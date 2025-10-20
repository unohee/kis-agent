"""Account management MCP tools"""
from typing import Any, Dict
from mcp.server import Server

from ..server import get_agent, server
from ..errors import validate_api_response, InvalidParameterError


@server.tool()
async def get_account_balance() -> Dict[str, Any]:
    """계좌 잔고 조회

    Returns:
        Dict: 계좌 잔고 정보
            - output1: 보유 종목 리스트
            - output2: 계좌 요약 정보 (총 자산, 예수금 등)
    """
    agent = get_agent()
    result = agent.get_account_balance()
    return validate_api_response(result, "계좌 잔고 조회")


@server.tool()
async def get_possible_order_amount(code: str, price: str) -> Dict[str, Any]:
    """주문 가능 금액/수량 조회

    Args:
        code: 종목코드 6자리
        price: 주문 가격

    Returns:
        Dict: 주문 가능 수량 정보
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    if not price:
        raise InvalidParameterError("price", "주문 가격이 필요합니다")

    agent = get_agent()
    result = agent.get_possible_order_amount(code, price)
    return validate_api_response(result, "주문 가능 금액/수량 조회")


@server.tool()
async def get_account_order_quantity(code: str) -> Dict[str, Any]:
    """계좌별 주문 가능 수량 조회

    Args:
        code: 종목코드 6자리

    Returns:
        Dict: 주문 가능 수량 정보
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_account_order_quantity(code)
    return validate_api_response(result, "계좌별 주문 가능 수량 조회")


@server.tool()
async def inquire_daily_ccld(date: str = "") -> Dict[str, Any]:
    """일자별 체결 내역 조회

    Args:
        date: 조회 날짜 (YYYYMMDD, 선택, 기본값: 당일)

    Returns:
        Dict: 일자별 체결 내역
    """
    agent = get_agent()
    result = agent.inquire_daily_ccld(date)
    return validate_api_response(result, "일자별 체결 내역 조회")


@server.tool()
async def inquire_balance_rlz_pl() -> Dict[str, Any]:
    """잔고 평가 및 실현 손익 조회

    Returns:
        Dict: 평가 손익 및 실현 손익 정보
    """
    agent = get_agent()
    result = agent.inquire_balance_rlz_pl()
    return validate_api_response(result, "잔고 평가 및 실현 손익 조회")


@server.tool()
async def inquire_psbl_sell() -> Dict[str, Any]:
    """매도 가능 수량 조회

    Returns:
        Dict: 보유 종목별 매도 가능 수량
    """
    agent = get_agent()
    result = agent.inquire_psbl_sell()
    return validate_api_response(result, "매도 가능 수량 조회")


@server.tool()
async def inquire_period_trade_profit(
    start_date: str, end_date: str
) -> Dict[str, Any]:
    """기간별 매매 손익 조회

    Args:
        start_date: 시작일 (YYYYMMDD)
        end_date: 종료일 (YYYYMMDD)

    Returns:
        Dict: 기간별 매매 손익 정보
    """
    if not start_date or len(start_date) != 8:
        raise InvalidParameterError("start_date", "시작일은 YYYYMMDD 형식이어야 합니다")
    if not end_date or len(end_date) != 8:
        raise InvalidParameterError("end_date", "종료일은 YYYYMMDD 형식이어야 합니다")

    agent = get_agent()
    result = agent.inquire_period_trade_profit(start_date, end_date)
    return validate_api_response(result, "기간별 매매 손익 조회")


@server.tool()
async def inquire_intgr_margin() -> Dict[str, Any]:
    """증거금 조회

    Returns:
        Dict: 증거금 정보
    """
    agent = get_agent()
    result = agent.inquire_intgr_margin()
    return validate_api_response(result, "증거금 조회")


@server.tool()
async def inquire_credit_psamount(code: str, price: str) -> Dict[str, Any]:
    """신용 거래 가능 금액 조회

    Args:
        code: 종목코드 6자리
        price: 주문 가격

    Returns:
        Dict: 신용 거래 가능 금액
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    if not price:
        raise InvalidParameterError("price", "주문 가격이 필요합니다")

    agent = get_agent()
    result = agent.inquire_credit_psamount(code, price)
    return validate_api_response(result, "신용 거래 가능 금액 조회")


@server.tool()
async def inquire_period_rights(start_date: str, end_date: str) -> Dict[str, Any]:
    """기간별 권리 조회

    Args:
        start_date: 시작일 (YYYYMMDD)
        end_date: 종료일 (YYYYMMDD)

    Returns:
        Dict: 기간별 권리 정보
    """
    if not start_date or len(start_date) != 8:
        raise InvalidParameterError("start_date", "시작일은 YYYYMMDD 형식이어야 합니다")
    if not end_date or len(end_date) != 8:
        raise InvalidParameterError("end_date", "종료일은 YYYYMMDD 형식이어야 합니다")

    agent = get_agent()
    result = agent.inquire_period_rights(start_date, end_date)
    return validate_api_response(result, "기간별 권리 조회")
