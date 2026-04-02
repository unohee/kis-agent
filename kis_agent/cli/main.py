#!/usr/bin/env python3
"""kis CLI 진입점 — pip install kis-agent 후 kis 명령으로 실행.

사용법:
    kis price 005930
    kis price 005930 --daily --days 5
    kis balance --holdings
    kis orderbook 005930
    kis overseas NAS AAPL
    kis overseas NAS AAPL --detail
    kis futures 101S03
    kis query stock get_stock_price code=005930
    kis schema [type]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

from kis_agent.cli.field_map import (
    ACCOUNT_BALANCE,
    DAILY_PRICE,
    DAILY_PROFIT,
    FUTURES_PRICE,
    HOLDING,
    ORDERBOOK_FIELDS,
    OVERSEAS_DAILY,
    OVERSEAS_FUTURES_PRICE,
    OVERSEAS_OPTION_PRICE,
    OVERSEAS_PRICE,
    OVERSEAS_PRICE_DETAIL,
    PENDING_ORDER,
    PERIOD_PROFIT,
    STOCK_PRICE,
    TRADE_EXECUTION,
    TRADE_SUMMARY,
    remap,
)
from kis_agent.cli.schema import get_schema
from kis_agent.utils.stock_master import resolve_code
from kis_agent.utils.stock_master import search as search_stocks


def _create_agent():
    """환경변수에서 인증 정보를 로드하여 Agent 생성 + 영업일 확인."""
    import logging

    from dotenv import load_dotenv

    # CLI에서는 WARNING 이상만 stderr로 출력 (토큰/Rate Limiter 로그 숨김)
    logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stderr)
    logging.getLogger("kis_agent").setLevel(logging.WARNING)

    # .env 파일 탐색
    for p in [
        ".env",
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
        ),
    ]:
        if os.path.exists(p):
            load_dotenv(p)
            break

    from kis_agent import Agent

    agent = Agent(
        app_key=os.environ["KIS_APP_KEY"],
        app_secret=os.environ.get("KIS_APP_SECRET", os.environ.get("KIS_SECRET", "")),
        account_no=os.environ["KIS_ACCOUNT_NO"],
        account_code=os.environ.get("KIS_ACCOUNT_CODE", "01"),
        base_url=os.environ.get(
            "KIS_BASE_URL", "https://openapi.koreainvestment.com:9443"
        ),
    )

    # Agent 생성 시 한 번만 영업일 확인 (공휴일 포함)
    _check_market_status(agent)

    return agent


# 영업일 캐시 — Agent 생성 시 한 번 조회 후 세션 내 재사용
_market_status = {
    "checked": False,
    "is_holiday": None,  # True/False/None
    "last_business_day": None,  # YYYYMMDD
    "notice": None,  # 안내 메시지
}


def _check_market_status(agent):
    """한투 API로 오늘이 영업일인지 확인하고 캐싱. Agent 생성 직후 1회 호출."""
    if _market_status["checked"]:
        return

    today = datetime.now()
    today_str = today.strftime("%Y%m%d")

    # 한투 API is_holiday 호출 (주말 + 공휴일 모두 확인)
    try:
        holiday = agent.stock_api.is_holiday(today_str)
    except Exception:
        # API 실패 시 주말만 체크
        holiday = today.weekday() >= 5

    _market_status["is_holiday"] = holiday
    _market_status["checked"] = True

    if holiday:
        # 직전 영업일 탐색 (최대 10일)
        for i in range(1, 11):
            prev = today - timedelta(days=i)
            prev_str = prev.strftime("%Y%m%d")
            try:
                prev_holiday = agent.stock_api.is_holiday(prev_str)
                if prev_holiday is False:
                    _market_status["last_business_day"] = prev_str
                    bday = prev.strftime("%Y-%m-%d %a")
                    _market_status["notice"] = (
                        f"휴장일 — 데이터는 직전 영업일({bday}) 기준"
                    )
                    break
            except Exception:
                # API 실패 시 주말만 건너뛰기
                if prev.weekday() < 5:
                    _market_status["last_business_day"] = prev_str
                    bday = prev.strftime("%Y-%m-%d %a")
                    _market_status["notice"] = (
                        f"휴장일 — 데이터는 직전 영업일({bday}) 기준 (공휴일 미확인)"
                    )
                    break
    else:
        _market_status["last_business_day"] = today_str
        hour = today.hour
        if hour < 9:
            _market_status["notice"] = "장 시작 전 — 데이터는 전일 종가 기준"
        elif hour >= 16:
            _market_status["notice"] = "장 마감 후 — 데이터는 금일 종가 기준"


def _out(data, pretty=False):
    """JSON 출력. 휴장일/장외 시간이면 notice 필드 추가."""
    notice = _market_status.get("notice")
    if notice and isinstance(data, dict) and "data" in data:
        data["_notice"] = notice
    indent = 2 if pretty else None
    print(json.dumps(data, ensure_ascii=False, indent=indent, default=str))


def _resolve(code_or_name: str) -> str:
    """종목코드 또는 종목명을 종목코드(6자리)로 변환. 실패 시 원본 반환."""
    resolved = resolve_code(code_or_name)
    if resolved:
        return resolved
    return code_or_name


def _get_name(agent, code: str):
    """국내 종목명 조회."""
    try:
        data = agent.stock_api.search_stock_info(code=code)
        if data and data.get("output"):
            o = data["output"]
            return o.get("prdt_abrv_name") or o.get("prdt_name")
    except Exception:
        pass
    return None


# 해외 거래소코드 → 상품유형코드 매핑 (get_stock_info용)
_OVERSEAS_EXCD_TO_PRDT_TYPE = {
    "NAS": "512", "NYS": "512", "AMS": "512",  # 미국
    "HKS": "513",  # 홍콩
    "SHS": "514",  # 중국 상해A
    "SZS": "515",  # 중국 심천A
    "TSE": "516",  # 일본
    "HNX": "517", "HSX": "517",  # 베트남
}


def _get_overseas_name(agent, excd: str, symb: str):
    """해외 종목명 조회."""
    try:
        prdt_type_cd = _OVERSEAS_EXCD_TO_PRDT_TYPE.get(excd, "512")
        pdno = f"{excd}.{symb}"
        data = agent.overseas_api.get_stock_info(
            prdt_type_cd=prdt_type_cd, pdno=pdno
        )
        if data and data.get("output"):
            o = data["output"]
            return o.get("prdt_name") or o.get("prdt_eng_name")
    except Exception:
        pass
    return None


# ============================================================
# 명령 핸들러
# ============================================================


def cmd_price(args):
    """국내 주식 현재가 조회. --daily로 일별 시세 포함."""
    agent = _create_agent()
    code = _resolve(args.code)

    result = {"stock": {"code": code}}

    # 종목명
    name = _get_name(agent, code)
    if name:
        result["stock"]["name"] = name

    # 현재가
    data = agent.stock_api.get_stock_price(code=code)
    if data and data.get("output"):
        result["stock"]["price"] = remap(data["output"], STOCK_PRICE)

    # 일별 시세
    if args.daily:
        daily_data = agent.stock_api.inquire_daily_price(code=code, period=args.period)
        if daily_data and daily_data.get("output"):
            items = [remap(item, DAILY_PRICE) for item in daily_data["output"]]
            result["stock"]["daily"] = items[: args.days] if args.days else items

    _out({"data": result}, args.pretty)


def cmd_balance(args):
    """계좌 잔고 조회. --holdings로 보유종목 상세 포함."""
    agent = _create_agent()
    data = agent.account_api.get_account_balance()
    if not data:
        _out({"error": "Failed to fetch balance"})
        return

    result = {"account": {}}

    # 잔고 요약
    if data.get("output2"):
        o2 = data["output2"]
        if isinstance(o2, list):
            o2 = o2[0] if o2 else {}
        result["account"]["balance"] = remap(o2, ACCOUNT_BALANCE)

    # 보유종목
    if args.holdings and data.get("output1"):
        result["account"]["holdings"] = [remap(h, HOLDING) for h in data["output1"]]

    _out({"data": result}, args.pretty)


def cmd_orderbook(args):
    """호가(매수/매도 10호가) 조회."""
    agent = _create_agent()
    code = _resolve(args.code)

    result = {"stock": {"code": code}}
    name = _get_name(agent, code)
    if name:
        result["stock"]["name"] = name

    data = agent.stock_api.get_orderbook(code=code)
    if data and data.get("output"):
        o = data["output"]
        asks = []
        bids = []
        for i in range(1, 11):
            ap, av = o.get(f"askp{i}"), o.get(f"askp_rsqn{i}")
            bp, bv = o.get(f"bidp{i}"), o.get(f"bidp_rsqn{i}")
            if ap:
                asks.append({"price": ap, "volume": av})
            if bp:
                bids.append({"price": bp, "volume": bv})

        result["stock"]["orderbook"] = {
            "asks": asks,
            "bids": bids,
            **remap(o, ORDERBOOK_FIELDS),
        }

    _out({"data": result}, args.pretty)


def cmd_overseas(args):
    """해외주식 시세 조회. --detail로 PER/PBR/시총 등 상세."""
    agent = _create_agent()
    excd, symb = args.excd.upper(), args.symb.upper()

    result = {"overseas": {"exchange": excd, "symbol": symb}}

    # 종목명
    name = _get_overseas_name(agent, excd, symb)
    if name:
        result["overseas"]["name"] = name

    if args.detail:
        data = agent.overseas_api.get_price_detail(excd=excd, symb=symb)
        if data and data.get("output"):
            result["overseas"]["priceDetail"] = remap(
                data["output"], OVERSEAS_PRICE_DETAIL
            )
    else:
        data = agent.overseas_api.get_price(excd=excd, symb=symb)
        if data and data.get("output"):
            result["overseas"]["price"] = remap(data["output"], OVERSEAS_PRICE)

    if args.daily:
        daily_data = agent.overseas_api.get_daily_price(excd=excd, symb=symb)
        if daily_data and daily_data.get("output2"):
            items = [remap(item, OVERSEAS_DAILY) for item in daily_data["output2"]]
            result["overseas"]["daily"] = items[: args.days] if args.days else items

    _out({"data": result}, args.pretty)


def cmd_futures(args):
    """선물옵션 시세 조회. --overseas로 해외선물, --option으로 해외옵션, --night로 야간."""
    agent = _create_agent()
    code = args.code

    # 야간 선물옵션 모드
    if args.night:
        return _cmd_futures_night(agent, args, code)

    if args.overseas or args.option:
        # 해외선물/옵션
        result = {"overseasFutures": {"code": code}}
        if args.option:
            data = agent.overseas_futures_api.get_option_price(srs_cd=code)
            field_map = OVERSEAS_OPTION_PRICE
        else:
            data = agent.overseas_futures_api.get_price(srs_cd=code)
            field_map = OVERSEAS_FUTURES_PRICE

        if data and data.get("rt_cd") == "1":
            result["overseasFutures"]["error"] = data.get("msg1", "API error")
        elif data and data.get("output"):
            result["overseasFutures"]["price"] = remap(data["output"], field_map)

        if args.orderbook and not args.option:
            ob = agent.overseas_futures_api.get_futures_orderbook(srs_cd=code)
            if ob and ob.get("output1") and ob.get("output2"):
                o1, o2 = ob["output1"], ob["output2"]
                asks = [
                    {"price": o1.get(f"askp{i}"), "volume": o1.get(f"askp_rsqn{i}")}
                    for i in range(1, 6)
                    if o1.get(f"askp{i}")
                ]
                bids = [
                    {"price": o2.get(f"bidp{i}"), "volume": o2.get(f"bidp_rsqn{i}")}
                    for i in range(1, 6)
                    if o2.get(f"bidp{i}")
                ]
                result["overseasFutures"]["orderbook"] = {"asks": asks, "bids": bids}
    else:
        # 국내선물
        result = {"futures": {"code": code}}
        data = agent.futures_api.get_price(code=code)
        if data and data.get("output"):
            mapped = remap(data["output"], FUTURES_PRICE)
            name = mapped.pop("name", None)
            if name:
                result["futures"]["name"] = name
            result["futures"]["price"] = mapped

    _out({"data": result}, args.pretty)


def _cmd_futures_night(agent, args, code):
    """야간 선물옵션 조회."""
    result = {"nightFutures": {"code": code}}

    # --balance: 야간 잔고
    if args.balance:
        data = agent.futures_api.inquire_ngt_balance()
        if data and data.get("output"):
            items = data["output"] if isinstance(data["output"], list) else [data["output"]]
            result["nightFutures"]["balance"] = items
        else:
            result["nightFutures"]["balance"] = []
        _out({"data": result}, args.pretty)
        return

    # --ccnl: 야간 체결내역
    if args.ccnl:
        data = agent.futures_api.inquire_ngt_ccnl()
        if data and data.get("output"):
            items = data["output"] if isinstance(data["output"], list) else [data["output"]]
            result["nightFutures"]["executions"] = items
        else:
            result["nightFutures"]["executions"] = []
        _out({"data": result}, args.pretty)
        return

    # 기본: 야간선물 시세 (기존 inquire-price에 야간 종목코드 사용)
    data = agent.futures_api.get_price(code=code)
    if data and data.get("output"):
        mapped = remap(data["output"], FUTURES_PRICE)
        name = mapped.pop("name", None)
        if name:
            result["nightFutures"]["name"] = name
        result["nightFutures"]["price"] = mapped
    elif data and data.get("rt_cd") != "0":
        result["nightFutures"]["error"] = data.get("msg1", "조회 실패")

    _out({"data": result}, args.pretty)


def _parse_date(s: str) -> str:
    """날짜 문자열을 YYYYMMDD로 변환.

    지원 형식:
        today          → 오늘
        7d, 30d, 3m, 1y → N일/월/년 전 (과거 상대날짜)
        2026-03-01     → 절대날짜
        20260301       → 절대날짜
    """
    if not s:
        return datetime.now().strftime("%Y%m%d")
    s = s.strip().lower()
    if s == "today":
        return datetime.now().strftime("%Y%m%d")
    # 상대 날짜: 7d, 30d, 3m, 1y (과거 기준)
    if len(s) >= 2 and s[-1] in ("d", "m", "y"):
        digits = s[:-1].lstrip("-")  # -7d도 7d도 동일 처리
        unit = s[-1]
        try:
            n = int(digits)
        except ValueError:
            pass
        else:
            today = datetime.now()
            if unit == "d":
                return (today - timedelta(days=n)).strftime("%Y%m%d")
            elif unit == "m":
                return (today - timedelta(days=n * 30)).strftime("%Y%m%d")
            elif unit == "y":
                return (today - timedelta(days=n * 365)).strftime("%Y%m%d")
    # YYYY-MM-DD 또는 YYYYMMDD
    cleaned = s.replace("-", "").replace("/", "").replace(".", "")
    if len(cleaned) == 8 and cleaned.isdigit():
        return cleaned
    return s


def _fmt_date(yyyymmdd: str) -> str:
    """YYYYMMDD → YYYY-MM-DD"""
    if len(yyyymmdd) == 8:
        return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"
    return yyyymmdd


def _fmt_time(hhmmss: str) -> str:
    """HHMMSS → HH:MM:SS"""
    if len(hhmmss) == 6:
        return f"{hhmmss[:2]}:{hhmmss[2:4]}:{hhmmss[4:]}"
    return hhmmss


def _fmt_number(s: str) -> str:
    """숫자에 천단위 콤마. 소수점이 있으면 보존."""
    if not s:
        return "0"
    try:
        if "." in s:
            f = float(s)
            if f == int(f):
                return f"{int(f):,}"
            return f"{f:,.2f}"
        return f"{int(s):,}"
    except (ValueError, TypeError):
        return s


def cmd_trades(args):
    """거래내역 조회 — 체결내역, 기간별 손익."""
    agent = _create_agent()

    start = _parse_date(args.start)
    end = _parse_date(args.end) if args.end else datetime.now().strftime("%Y%m%d")

    # 매수/매도 필터
    sll_buy = "00"  # 전체
    if args.buy:
        sll_buy = "02"
    elif args.sell:
        sll_buy = "01"

    stock_filter = args.stock or ""

    # 기간별 손익 모드
    if args.profit:
        return _cmd_trades_profit(agent, args, start, end, stock_filter)

    # 체결내역 조회 (pagination으로 전체 조회)
    data = agent.account_api.inquire_daily_ccld(
        start_date=start,
        end_date=end,
        pdno=stock_filter,
        ord_dvsn_cd=sll_buy,
        pagination=True,
        ccld_dvsn="01" if args.filled else "00",
    )

    if not data or data.get("rt_cd") != "0":
        _out({"error": "거래내역 조회 실패", "detail": data.get("msg1") if data else None})
        return

    items = data.get("output1", [])
    summary = data.get("output2", {})

    if not items:
        _out({"data": {
            "trades": {"period": f"{_fmt_date(start)} ~ {_fmt_date(end)}", "count": 0, "items": []},
        }}, args.pretty)
        return

    # 필드 매핑 + 포맷팅
    mapped = []
    for item in items:
        m = remap(item, TRADE_EXECUTION)
        m["date"] = _fmt_date(m.get("date", ""))
        m["time"] = _fmt_time(m.get("time", ""))
        m["orderQty"] = _fmt_number(m.get("orderQty", ""))
        m["orderPrice"] = _fmt_number(m.get("orderPrice", ""))
        m["filledQty"] = _fmt_number(m.get("filledQty", ""))
        m["avgPrice"] = _fmt_number(m.get("avgPrice", ""))
        m["filledAmount"] = _fmt_number(m.get("filledAmount", ""))
        if m.get("remainQty"):
            m["remainQty"] = _fmt_number(m["remainQty"])
        # 체결건만 필터 (--filled 아닐 때도 체결수량 0인 건 정리)
        if args.filled and m.get("filledQty") == "0":
            continue
        mapped.append(m)

    # 요약 매핑
    mapped_summary = remap(summary, TRADE_SUMMARY)
    for k in ["totalOrderQty", "totalFilledQty", "totalFilledAmount", "totalFees"]:
        if k in mapped_summary:
            mapped_summary[k] = _fmt_number(mapped_summary[k])

    if "page_count" in summary:
        mapped_summary["pages"] = summary["page_count"]
    if "total_count" in summary:
        mapped_summary["totalCount"] = summary["total_count"]

    result = {
        "trades": {
            "period": f"{_fmt_date(start)} ~ {_fmt_date(end)}",
            "count": len(mapped),
            "summary": mapped_summary,
            "items": mapped[:args.limit] if args.limit else mapped,
        }
    }

    _out({"data": result}, args.pretty)


def _cmd_trades_profit(agent, args, start, end, stock_filter):
    """기간별 손익 조회."""
    if args.daily_profit:
        # 일별 손익 합산
        data = agent.account_api.get_period_profit(
            start_date=start,
            end_date=end,
        )
        if not data or data.get("rt_cd") != "0":
            _out({"error": "기간별 손익 조회 실패", "detail": data.get("msg1") if data else None})
            return

        items = data.get("output1", [])
        mapped = []
        for item in items:
            m = remap(item, DAILY_PROFIT)
            m["date"] = _fmt_date(m.get("date", ""))
            for k in ["realizedPL", "sellAmount", "buyAmount", "totalFees"]:
                if k in m:
                    m[k] = _fmt_number(m[k])
            if m.get("realizedPLRate"):
                m["realizedPLRate"] = f"{m['realizedPLRate']}%"
            mapped.append(m)

        result = {
            "dailyProfit": {
                "period": f"{_fmt_date(start)} ~ {_fmt_date(end)}",
                "count": len(mapped),
                "items": mapped,
            }
        }
        _out({"data": result}, args.pretty)
        return

    # 종목별 실현손익
    data = agent.account_api.get_period_trade_profit(
        start_date=start,
        end_date=end,
        pdno=stock_filter,
    )

    if not data or data.get("rt_cd") != "0":
        _out({"error": "기간별 손익 조회 실패", "detail": data.get("msg1") if data else None})
        return

    items = data.get("output1", [])
    summary = data.get("output2", {})

    mapped = []
    for item in items:
        m = remap(item, PERIOD_PROFIT)
        for k in ["buyQty", "buyAmount", "sellQty", "sellAmount", "realizedPL", "totalFees"]:
            if k in m:
                m[k] = _fmt_number(m[k])
        if m.get("realizedPLRate"):
            m["realizedPLRate"] = f"{m['realizedPLRate']}%"
        mapped.append(m)

    # output2 요약
    profit_summary = {}
    for k in ["tot_sll_amt", "tot_buy_amt", "tot_rlzt_pfls", "tot_prsm_tlex_smtl"]:
        v = summary.get(k)
        if v:
            label = {
                "tot_sll_amt": "totalSellAmount",
                "tot_buy_amt": "totalBuyAmount",
                "tot_rlzt_pfls": "totalRealizedPL",
                "tot_prsm_tlex_smtl": "totalFees",
            }.get(k, k)
            profit_summary[label] = _fmt_number(v)
    if summary.get("tot_rlzt_erng_rt"):
        profit_summary["totalRealizedPLRate"] = f"{summary['tot_rlzt_erng_rt']}%"

    result = {
        "profit": {
            "period": f"{_fmt_date(start)} ~ {_fmt_date(end)}",
            "count": len(mapped),
            "summary": profit_summary,
            "items": mapped,
        }
    }

    _out({"data": result}, args.pretty)


# ============================================================
# 주문 타입 매핑
# ============================================================

# 국내주식 주문구분 코드
_DOMESTIC_ORDER_TYPES = {
    "limit": "00",       # 지정가
    "market": "01",      # 시장가
    "cond": "02",        # 조건부지정가
    "best": "03",        # 최유리지정가
    "pre": "05",         # 장전시간외
    "after": "06",       # 장후시간외
    "ioc": "11",         # IOC지정가
    "fok": "12",         # FOK지정가
}

# 해외주식 주문구분 코드
_OVERSEAS_ORDER_TYPES = {
    "limit": "00",       # 지정가
    "moo": "31",         # MOO (매도만)
    "loo": "32",         # LOO
    "moc": "33",         # MOC (매도만)
    "loc": "34",         # LOC
}

# 해외주식 거래소 매핑 (조회용 → 주문용)
_OVERSEAS_EXCG_MAP = {
    "NAS": "NASD", "NYS": "NYSE", "AMS": "AMEX",
    "HKS": "SEHK", "SHS": "SHAA", "SZS": "SZAA",
    "TSE": "TKSE", "HNX": "HASE", "HSX": "VNSE",
    # 주문용 코드 직접 입력도 허용
    "NASD": "NASD", "NYSE": "NYSE", "AMEX": "AMEX",
    "SEHK": "SEHK", "SHAA": "SHAA", "SZAA": "SZAA",
    "TKSE": "TKSE", "HASE": "HASE", "VNSE": "VNSE",
}


def _confirm_order(action: str, details: dict) -> bool:
    """주문 실행 전 확인. --yes 없으면 stderr로 확인 프롬프트."""
    import sys

    info_lines = [f"  {k}: {v}" for k, v in details.items() if v]
    msg = f"\n{'='*50}\n  [{action}]\n{'='*50}\n"
    msg += "\n".join(info_lines)
    msg += f"\n{'='*50}\n"
    sys.stderr.write(msg)
    sys.stderr.write("  실행하시겠습니까? (y/N): ")
    sys.stderr.flush()
    try:
        answer = input().strip().lower()
    except EOFError:
        return False
    return answer in ("y", "yes")


def cmd_order(args):
    """주문 실행 — 매수/매도/취소/정정/미체결 조회."""
    action = args.action

    if action == "list":
        return _cmd_order_list(args)
    elif action in ("buy", "sell"):
        return _cmd_order_execute(args)
    elif action == "cancel":
        return _cmd_order_cancel(args)
    elif action == "modify":
        return _cmd_order_modify(args)
    else:
        _out({"error": f"Unknown action: {action}. Use: buy, sell, cancel, modify, list"})
        sys.exit(1)


def _cmd_order_list(args):
    """미체결 주문 목록 조회."""
    agent = _create_agent()

    if args.overseas:
        # 해외주식 미체결
        excd = _OVERSEAS_EXCG_MAP.get(args.overseas.upper(), args.overseas.upper())
        data = agent.overseas_api.get_nccs_orders(ovrs_excg_cd=excd)
    else:
        # 국내주식 미체결
        data = agent.account_api.inquire_psbl_rvsecncl()

    if not data:
        _out({"error": "미체결 주문 조회 실패"})
        return

    items = data.get("output", data.get("output1", []))
    if not items:
        _out({"data": {"orders": {"count": 0, "items": []}}}, args.pretty)
        return

    mapped = []
    for item in items:
        m = remap(item, PENDING_ORDER)
        if m.get("date"):
            m["date"] = _fmt_date(m["date"])
        if m.get("time"):
            m["time"] = _fmt_time(m["time"])
        for k in ["orderQty", "orderPrice", "filledQty", "remainQty"]:
            if k in m:
                m[k] = _fmt_number(m[k])
        mapped.append(m)

    _out({"data": {"orders": {"count": len(mapped), "items": mapped}}}, args.pretty)


def _cmd_order_execute(args):
    """매수/매도 주문 실행."""
    agent = _create_agent()
    is_buy = args.action == "buy"
    code = args.code

    if args.overseas:
        return _cmd_order_overseas(agent, args, is_buy)

    # 국내주식 주문
    order_type = _DOMESTIC_ORDER_TYPES.get(args.type, args.type)
    qty = args.qty
    price = args.price if args.price else 0

    # 시장가/최유리 계열은 가격 0
    if order_type in ("01", "03", "05", "06"):
        price = 0

    # 종목명 조회
    name = _get_name(agent, code)
    side_label = "매수" if is_buy else "매도"
    type_label = {v: k for k, v in _DOMESTIC_ORDER_TYPES.items()}.get(order_type, order_type)

    details = {
        "종목": f"{code} ({name})" if name else code,
        "구분": side_label,
        "주문유형": type_label,
        "수량": f"{qty:,}주",
        "가격": f"{price:,}원" if price else "시장가",
        "거래소": args.exchange.upper(),
    }

    if not args.yes and not _confirm_order(f"국내주식 {side_label}", details):
        _out({"cancelled": True, "message": "주문이 취소되었습니다"})
        return

    try:
        buy_sell = "BUY" if is_buy else "SELL"
        result = agent.account_api.order_cash(
            pdno=code,
            qty=qty,
            price=price,
            buy_sell=buy_sell,
            order_type=order_type,
            exchange=args.exchange.upper(),
        )

        if not result:
            _out({"error": "주문 실패: 응답 없음"})
            return

        if result.get("rt_cd") != "0":
            _out({"error": result.get("msg1", "주문 실패"), "code": result.get("msg_cd")})
            return

        output = result.get("output", {})
        _out({"data": {
            "order": {
                "status": "accepted",
                "orderNo": output.get("odno", ""),
                "time": _fmt_time(output.get("ord_tmd", "")),
                "side": side_label,
                "code": code,
                "name": name,
                "qty": qty,
                "price": price if price else "시장가",
                "type": type_label,
            }
        }}, args.pretty)

    except Exception as e:
        _out({"error": str(e), "code": type(e).__name__})
        sys.exit(1)


def _cmd_order_overseas(agent, args, is_buy):
    """해외주식 주문 실행."""
    excd = _OVERSEAS_EXCG_MAP.get(args.overseas.upper(), args.overseas.upper())
    code = args.code.upper()
    order_type = _OVERSEAS_ORDER_TYPES.get(args.type, args.type)
    qty = args.qty
    price = args.price if args.price else 0

    side_label = "매수" if is_buy else "매도"
    type_label = {v: k for k, v in _OVERSEAS_ORDER_TYPES.items()}.get(order_type, order_type)

    # MOO/MOC는 매도만 가능
    if is_buy and order_type in ("31", "33"):
        _out({"error": f"{type_label} 주문은 매도만 가능합니다"})
        return

    details = {
        "거래소": excd,
        "종목": code,
        "구분": side_label,
        "주문유형": type_label,
        "수량": f"{qty:,}주",
        "가격": f"{price}" if price else "시장가",
    }

    if not args.yes and not _confirm_order(f"해외주식 {side_label}", details):
        _out({"cancelled": True, "message": "주문이 취소되었습니다"})
        return

    try:
        if is_buy:
            result = agent.overseas_api.buy_order(
                ovrs_excg_cd=excd, pdno=code, qty=qty,
                price=price, ord_dvsn=order_type,
            )
        else:
            result = agent.overseas_api.sell_order(
                ovrs_excg_cd=excd, pdno=code, qty=qty,
                price=price, ord_dvsn=order_type,
            )

        if not result:
            _out({"error": "주문 실패: 응답 없음"})
            return

        if result.get("rt_cd") != "0":
            _out({"error": result.get("msg1", "주문 실패"), "code": result.get("msg_cd")})
            return

        output = result.get("output", {})
        _out({"data": {
            "order": {
                "status": "accepted",
                "orderNo": output.get("odno", ""),
                "time": _fmt_time(output.get("ord_tmd", "")),
                "side": side_label,
                "exchange": excd,
                "code": code,
                "qty": qty,
                "price": price if price else "시장가",
                "type": type_label,
            }
        }}, args.pretty)

    except Exception as e:
        _out({"error": str(e), "code": type(e).__name__})
        sys.exit(1)


def _cmd_order_cancel(args):
    """주문 취소."""
    agent = _create_agent()
    order_no = args.order_no

    if args.overseas:
        excd = _OVERSEAS_EXCG_MAP.get(args.overseas.upper(), args.overseas.upper())
        code = args.code.upper() if args.code else ""

        details = {"거래소": excd, "종목": code, "주문번호": order_no}
        if not args.yes and not _confirm_order("해외주식 주문 취소", details):
            _out({"cancelled": True, "message": "취소가 중단되었습니다"})
            return

        try:
            result = agent.overseas_api.cancel_order(
                ovrs_excg_cd=excd, pdno=code,
                orgn_odno=order_no, qty=args.qty or 0,
            )
        except Exception as e:
            _out({"error": str(e), "code": type(e).__name__})
            return
    else:
        details = {"주문번호": order_no, "수량": f"{args.qty}주" if args.qty else "전량"}
        if not args.yes and not _confirm_order("주문 취소", details):
            _out({"cancelled": True, "message": "취소가 중단되었습니다"})
            return

        try:
            result = agent.account_api.order_rvsecncl(
                org_order_no=order_no,
                qty=args.qty or 0,
                price=0,
                order_type="01",
                cncl_type="취소",
            )
        except Exception as e:
            _out({"error": str(e), "code": type(e).__name__})
            return

    if not result:
        _out({"error": "취소 실패: 응답 없음"})
        return

    if result.get("rt_cd") != "0":
        _out({"error": result.get("msg1", "취소 실패"), "code": result.get("msg_cd")})
        return

    output = result.get("output", {})
    _out({"data": {
        "cancel": {
            "status": "accepted",
            "orderNo": output.get("odno", ""),
            "origOrderNo": order_no,
        }
    }}, args.pretty)


def _cmd_order_modify(args):
    """주문 정정."""
    agent = _create_agent()
    order_no = args.order_no
    price = args.price or 0
    qty = args.qty or 0
    order_type = _DOMESTIC_ORDER_TYPES.get(args.type, args.type)

    if args.overseas:
        excd = _OVERSEAS_EXCG_MAP.get(args.overseas.upper(), args.overseas.upper())
        code = args.code.upper() if args.code else ""

        details = {
            "거래소": excd, "종목": code, "주문번호": order_no,
            "변경가격": f"{price}" if price else "-",
            "변경수량": f"{qty}주" if qty else "-",
        }
        if not args.yes and not _confirm_order("해외주식 주문 정정", details):
            _out({"cancelled": True, "message": "정정이 중단되었습니다"})
            return

        try:
            result = agent.overseas_api.modify_order(
                ovrs_excg_cd=excd, pdno=code,
                orgn_odno=order_no, qty=qty, price=price,
            )
        except Exception as e:
            _out({"error": str(e), "code": type(e).__name__})
            return
    else:
        details = {
            "주문번호": order_no,
            "변경가격": f"{price:,}원" if price else "-",
            "변경수량": f"{qty:,}주" if qty else "-",
            "주문유형": args.type,
        }
        if not args.yes and not _confirm_order("주문 정정", details):
            _out({"cancelled": True, "message": "정정이 중단되었습니다"})
            return

        try:
            result = agent.account_api.order_rvsecncl(
                org_order_no=order_no,
                qty=qty,
                price=price,
                order_type=order_type,
                cncl_type="정정",
            )
        except Exception as e:
            _out({"error": str(e), "code": type(e).__name__})
            return

    if not result:
        _out({"error": "정정 실패: 응답 없음"})
        return

    if result.get("rt_cd") != "0":
        _out({"error": result.get("msg1", "정정 실패"), "code": result.get("msg_cd")})
        return

    output = result.get("output", {})
    _out({"data": {
        "modify": {
            "status": "accepted",
            "orderNo": output.get("odno", ""),
            "origOrderNo": order_no,
        }
    }}, args.pretty)


def cmd_query(args):
    """API 직접 호출 — kis query <domain> <method> [key=value ...]"""
    agent = _create_agent()
    domain = args.domain
    method = args.method

    # key=value 인자 파싱
    kwargs = {}
    for kv in args.args:
        if "=" in kv:
            k, v = kv.split("=", 1)
            kwargs[k] = v

    # 도메인별 API 객체 선택
    targets = {
        "stock": agent.stock_api,
        "account": agent.account_api,
        "overseas": agent.overseas_api,
        "futures": agent.futures_api,
        "overseas_futures": agent.overseas_futures_api,
        "agent": agent,
    }
    target = targets.get(domain)
    if not target:
        _out(
            {
                "error": f"Unknown domain: {domain}. Available: {', '.join(targets.keys())}"
            }
        )
        sys.exit(1)

    fn = getattr(target, method, None)
    if not fn:
        methods = [
            m
            for m in dir(target)
            if not m.startswith("_") and callable(getattr(target, m, None))
        ]
        _out({"error": f"Unknown method: {domain}.{method}", "available": methods})
        sys.exit(1)

    try:
        result = fn(**kwargs)
        _out({"data": result}, args.pretty)
    except Exception as e:
        _out({"error": str(e), "code": type(e).__name__})
        sys.exit(1)


def cmd_search(args):
    """종목 검색 (종목코드 또는 종목명)."""
    query = args.query
    limit = args.limit

    results = search_stocks(query, limit=limit)
    if not results:
        _out({"data": {"search": {"query": query, "results": [], "count": 0}}})
        return

    _out({
        "data": {
            "search": {
                "query": query,
                "count": len(results),
                "results": results,
            }
        }
    }, args.pretty)


def cmd_schema(args):
    """스키마 출력."""
    type_name = args.type
    if args.json:
        # JSON으로 타입 목록 출력
        import re

        types = re.findall(r"^(type|enum|input)\s+(\w+)", get_schema(), re.MULTILINE)
        type_list = [{"kind": kind, "name": name} for kind, name in types]
        _out({"types": type_list}, pretty=True)
    else:
        print(get_schema(type_name))


# ============================================================
# CLI 파서
# ============================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kis",
        description="kis-agent CLI — LLM-friendly 한국투자증권 API",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.2.0")
    sub = parser.add_subparsers(dest="command", help="명령")

    # price
    p = sub.add_parser("price", help="주식 현재가 조회")
    p.add_argument("code", help="종목코드 또는 종목명 (예: 005930, 삼성전자)")
    p.add_argument("--daily", action="store_true", help="일별 시세 포함")
    p.add_argument("--period", default="D", help="기간 (D:일, W:주, M:월)")
    p.add_argument("--days", type=int, default=30, help="일수 (기본 30)")
    p.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # balance
    p = sub.add_parser("balance", help="계좌 잔고 조회")
    p.add_argument("--holdings", action="store_true", help="보유종목 상세")
    p.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # orderbook
    p = sub.add_parser("orderbook", help="호가 조회")
    p.add_argument("code", help="종목코드 또는 종목명")
    p.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # overseas
    p = sub.add_parser("overseas", help="해외주식 시세 조회")
    p.add_argument("excd", help="거래소 (NAS, NYS, AMS, TSE, HKS)")
    p.add_argument("symb", help="종목 심볼 (AAPL, TSLA)")
    p.add_argument("--detail", action="store_true", help="PER/PBR/시총 등 상세")
    p.add_argument("--daily", action="store_true", help="일별 시세 포함")
    p.add_argument("--days", type=int, default=30, help="일수 (기본 30)")
    p.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # futures
    p = sub.add_parser("futures", help="선물옵션 시세 조회 (국내/해외/야간)")
    p.add_argument("code", help="종목코드 (국내: 101S03, 야간: 101W09, 해외: CLM26)")
    p.add_argument(
        "--overseas", action="store_true", help="해외선물 (CME, NYMEX, EUREX 등)"
    )
    p.add_argument("--option", action="store_true", help="해외옵션 (그릭스 포함)")
    p.add_argument("--orderbook", action="store_true", help="호가 포함 (해외선물)")
    p.add_argument("--night", action="store_true", help="야간선물 모드 (18:00~05:00)")
    p.add_argument("--balance", action="store_true", help="잔고 조회 (--night와 함께)")
    p.add_argument("--ccnl", action="store_true", help="체결내역 조회 (--night와 함께)")
    p.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # trades (거래내역)
    p = sub.add_parser("trades", help="거래내역/체결/손익 조회")
    p.add_argument("--from", dest="start", default="today", help="시작일 (today, 7d, 30d, 3m, 2026-03-01)")
    p.add_argument("--to", dest="end", default="", help="종료일 (기본: 오늘)")
    p.add_argument("--buy", action="store_true", help="매수만")
    p.add_argument("--sell", action="store_true", help="매도만")
    p.add_argument("--stock", default="", help="종목코드 필터 (예: 005930)")
    p.add_argument("--filled", action="store_true", help="체결 완료건만")
    p.add_argument("--limit", type=int, default=0, help="최대 건수 (0=전체)")
    p.add_argument("--profit", action="store_true", help="기간별 실현손익 모드")
    p.add_argument("--daily-profit", action="store_true", help="일별 손익 합산 (--profit과 함께)")
    p.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # order (주문)
    p = sub.add_parser("order", help="주문 실행 (매수/매도/취소/정정/미체결)")
    order_sub = p.add_subparsers(dest="action", help="주문 액션")

    # order buy
    ob = order_sub.add_parser("buy", help="매수 주문")
    ob.add_argument("code", help="종목코드 (국내: 005930, 해외: AAPL)")
    ob.add_argument("--qty", type=int, required=True, help="주문수량")
    ob.add_argument("--price", type=float, default=0, help="주문가격 (0=시장가)")
    ob.add_argument("--type", default="limit", help="주문유형 (limit, market, best, ioc, fok, pre, after, loo, loc)")
    ob.add_argument("--exchange", default="KRX", help="거래소 (KRX, NXT, SOR)")
    ob.add_argument("--overseas", default="", help="해외거래소 (NAS, NYS, AMS, HKS, TSE)")
    ob.add_argument("--yes", action="store_true", help="확인 없이 즉시 실행")
    ob.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # order sell
    os_ = order_sub.add_parser("sell", help="매도 주문")
    os_.add_argument("code", help="종목코드")
    os_.add_argument("--qty", type=int, required=True, help="주문수량")
    os_.add_argument("--price", type=float, default=0, help="주문가격 (0=시장가)")
    os_.add_argument("--type", default="limit", help="주문유형 (limit, market, best, moo, moc, loo, loc)")
    os_.add_argument("--exchange", default="KRX", help="거래소 (KRX, NXT, SOR)")
    os_.add_argument("--overseas", default="", help="해외거래소")
    os_.add_argument("--yes", action="store_true", help="확인 없이 즉시 실행")
    os_.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # order cancel
    oc = order_sub.add_parser("cancel", help="주문 취소")
    oc.add_argument("order_no", help="주문번호")
    oc.add_argument("--code", default="", help="종목코드 (해외주식 필수)")
    oc.add_argument("--qty", type=int, default=0, help="취소수량 (0=전량)")
    oc.add_argument("--overseas", default="", help="해외거래소")
    oc.add_argument("--yes", action="store_true", help="확인 없이 즉시 실행")
    oc.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # order modify
    om = order_sub.add_parser("modify", help="주문 정정")
    om.add_argument("order_no", help="주문번호")
    om.add_argument("--code", default="", help="종목코드 (해외주식 필수)")
    om.add_argument("--qty", type=int, default=0, help="변경수량")
    om.add_argument("--price", type=float, default=0, help="변경가격")
    om.add_argument("--type", default="limit", help="주문유형")
    om.add_argument("--overseas", default="", help="해외거래소")
    om.add_argument("--yes", action="store_true", help="확인 없이 즉시 실행")
    om.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # order list
    ol = order_sub.add_parser("list", help="미체결 주문 조회")
    ol.add_argument("--overseas", default="", help="해외거래소 (지정 시 해외 미체결)")
    ol.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # search (종목 검색)
    p = sub.add_parser("search", help="종목 검색 (코드 또는 이름)")
    p.add_argument("query", help="검색어 (종목코드 또는 종목명, 예: 삼성, 005930, 카카오)")
    p.add_argument("--limit", type=int, default=20, help="최대 결과 수 (기본 20)")
    p.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # query (API 직접 호출)
    p = sub.add_parser(
        "query", help="API 직접 호출 (kis query stock get_stock_price code=005930)"
    )
    p.add_argument("domain", help="도메인 (stock, account, overseas, futures, agent)")
    p.add_argument("method", help="메서드명")
    p.add_argument("args", nargs="*", help="인자 (key=value)")
    p.add_argument("--pretty", action="store_true", help="사람 읽기용 포맷")

    # schema
    p = sub.add_parser("schema", help="스키마 출력 (LLM introspection)")
    p.add_argument("type", nargs="?", help="특정 타입만 (예: Stock, Account)")
    p.add_argument("--json", action="store_true", help="JSON 형식")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    handlers = {
        "price": cmd_price,
        "balance": cmd_balance,
        "orderbook": cmd_orderbook,
        "overseas": cmd_overseas,
        "futures": cmd_futures,
        "trades": cmd_trades,
        "order": cmd_order,
        "search": cmd_search,
        "query": cmd_query,
        "schema": cmd_schema,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
