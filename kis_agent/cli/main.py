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
    FUTURES_PRICE,
    HOLDING,
    ORDERBOOK_FIELDS,
    OVERSEAS_DAILY,
    OVERSEAS_FUTURES_PRICE,
    OVERSEAS_OPTION_PRICE,
    OVERSEAS_PRICE,
    OVERSEAS_PRICE_DETAIL,
    STOCK_PRICE,
    remap,
)
from kis_agent.cli.schema import get_schema


def _create_agent():
    """환경변수에서 인증 정보를 로드하여 Agent 생성 + 영업일 확인."""
    from dotenv import load_dotenv

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


def _get_name(agent, code: str):
    """종목명 조회."""
    try:
        data = agent.stock_api.search_stock_info(code=code)
        if data and data.get("output"):
            o = data["output"]
            return o.get("prdt_abrv_name") or o.get("prdt_name")
    except Exception:
        pass
    return None


# ============================================================
# 명령 핸들러
# ============================================================


def cmd_price(args):
    """국내 주식 현재가 조회. --daily로 일별 시세 포함."""
    agent = _create_agent()
    code = args.code

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
    code = args.code

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
    """선물옵션 시세 조회. --overseas로 해외선물, --option으로 해외옵션."""
    agent = _create_agent()
    code = args.code

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
    p.add_argument("code", help="종목코드 (예: 005930)")
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
    p.add_argument("code", help="종목코드")
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
    p = sub.add_parser("futures", help="선물옵션 시세 조회 (국내/해외)")
    p.add_argument("code", help="종목코드 (국내: 101S03, 해외: CLM26, ESM26)")
    p.add_argument(
        "--overseas", action="store_true", help="해외선물 (CME, NYMEX, EUREX 등)"
    )
    p.add_argument("--option", action="store_true", help="해외옵션 (그릭스 포함)")
    p.add_argument("--orderbook", action="store_true", help="호가 포함 (해외선물)")
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
