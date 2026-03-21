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
    OVERSEAS_PRICE,
    OVERSEAS_PRICE_DETAIL,
    STOCK_PRICE,
    remap,
)
from kis_agent.cli.schema import get_schema


def _create_agent():
    """환경변수에서 인증 정보를 로드하여 Agent 생성."""
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

    return Agent(
        app_key=os.environ["KIS_APP_KEY"],
        app_secret=os.environ.get("KIS_APP_SECRET", os.environ.get("KIS_SECRET", "")),
        account_no=os.environ["KIS_ACCOUNT_NO"],
        account_code=os.environ.get("KIS_ACCOUNT_CODE", "01"),
        base_url=os.environ.get(
            "KIS_BASE_URL", "https://openapi.koreainvestment.com:9443"
        ),
    )


def _last_business_day():
    """가장 최근 영업일 반환. 주말이면 직전 금요일로 폴백."""
    today = datetime.now()
    wd = today.weekday()  # 0=월 ... 6=일
    if wd == 5:  # 토요일
        return today - timedelta(days=1)
    elif wd == 6:  # 일요일
        return today - timedelta(days=2)
    return today


def _market_notice():
    """주말/장외 시간이면 안내 메시지 반환."""
    today = datetime.now()
    wd = today.weekday()
    if wd >= 5:
        bday = _last_business_day()
        return f"주말 — 데이터는 직전 영업일({bday.strftime('%Y-%m-%d %a')}) 기준"
    hour = today.hour
    if hour < 9:
        return "장 시작 전 — 데이터는 전일 종가 기준"
    if hour >= 16:
        return "장 마감 후 — 데이터는 금일 종가 기준"
    return None


def _out(data, pretty=False):
    """JSON 출력. 주말/장외 시간이면 notice 필드 추가."""
    notice = _market_notice()
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
    """국내 선물옵션 시세 조회."""
    agent = _create_agent()
    code = args.code

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
    p = sub.add_parser("futures", help="선물옵션 시세 조회")
    p.add_argument("code", help="선물옵션 종목코드")
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
