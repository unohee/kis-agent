"""Order execution MCP tools"""

from typing import Any, Dict

from ..errors import InvalidParameterError, validate_api_response
from ..server import get_agent, server


@server.tool()
async def order_stock_cash(
    ord_dv: str, pdno: str, ord_dvsn: str, ord_qty: str, ord_unpr: str
) -> Dict[str, Any]:
    """현금 주문 (매수/매도)

    Args:
        ord_dv: 주문 구분 ("buy" 또는 "sell")
        pdno: 종목코드 6자리
        ord_dvsn: 주문 유형 ("00":지정가, "01":시장가, "03":최유리가)
        ord_qty: 주문 수량
        ord_unpr: 주문 단가 (시장가: "0")

    Returns:
        Dict: 주문 결과
    """
    if ord_dv not in ["buy", "sell"]:
        raise InvalidParameterError("ord_dv", "'buy' 또는 'sell'이어야 합니다")
    if not pdno or len(pdno) != 6:
        raise InvalidParameterError("pdno", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.order_stock_cash(ord_dv, pdno, ord_dvsn, ord_qty, ord_unpr)
    return validate_api_response(result, "현금 주문")


@server.tool()
async def order_stock_credit(
    ord_dv: str,
    pdno: str,
    crdt_type: str,
    ord_dvsn: str,
    ord_qty: str,
    ord_unpr: str,
    loan_dt: str = "",
) -> Dict[str, Any]:
    """신용 주문 (매수/매도)

    Args:
        ord_dv: 주문 구분 ("buy" 또는 "sell")
        pdno: 종목코드 6자리
        crdt_type: 신용 유형 ("21":자기융자, "22":유통융자)
        ord_dvsn: 주문 유형 ("00":지정가, "01":시장가)
        ord_qty: 주문 수량
        ord_unpr: 주문 단가
        loan_dt: 대출일자 (YYYYMMDD, 매도 시 필수)

    Returns:
        Dict: 주문 결과
    """
    if ord_dv not in ["buy", "sell"]:
        raise InvalidParameterError("ord_dv", "'buy' 또는 'sell'이어야 합니다")
    if not pdno or len(pdno) != 6:
        raise InvalidParameterError("pdno", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.order_stock_credit(
        ord_dv, pdno, crdt_type, ord_dvsn, ord_qty, ord_unpr, loan_dt
    )
    return validate_api_response(result, "신용 주문")


@server.tool()
async def order_cash(
    code: str, qty: str, price: str, order_type: str
) -> Dict[str, Any]:
    """현금 매수

    Args:
        code: 종목코드 6자리
        qty: 주문 수량
        price: 주문 가격
        order_type: 주문 유형 ("00":지정가, "01":시장가)

    Returns:
        Dict: 주문 결과
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.order_cash(code, qty, price, order_type)
    return validate_api_response(result, "현금 매수")


@server.tool()
async def order_cash_sor(code: str, qty: str) -> Dict[str, Any]:
    """시장가 매수

    Args:
        code: 종목코드 6자리
        qty: 주문 수량

    Returns:
        Dict: 주문 결과
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.order_cash_sor(code, qty)
    return validate_api_response(result, "시장가 매수")


@server.tool()
async def order_credit_buy(
    code: str, crdt_type: str, qty: str, price: str, order_type: str
) -> Dict[str, Any]:
    """신용 매수

    Args:
        code: 종목코드 6자리
        crdt_type: 신용 유형 ("21":자기융자, "22":유통융자)
        qty: 주문 수량
        price: 주문 가격
        order_type: 주문 유형

    Returns:
        Dict: 주문 결과
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.order_credit_buy(code, crdt_type, qty, price, order_type)
    return validate_api_response(result, "신용 매수")


@server.tool()
async def order_credit_sell(
    code: str, loan_dt: str, qty: str, price: str, order_type: str
) -> Dict[str, Any]:
    """신용 매도

    Args:
        code: 종목코드 6자리
        loan_dt: 대출일자 (YYYYMMDD)
        qty: 주문 수량
        price: 주문 가격
        order_type: 주문 유형

    Returns:
        Dict: 주문 결과
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.order_credit_sell(code, loan_dt, qty, price, order_type)
    return validate_api_response(result, "신용 매도")


@server.tool()
async def order_rvsecncl(
    org_order_no: str, qty: str, price: str, order_type: str, cncl_type: str
) -> Dict[str, Any]:
    """주문 정정/취소

    Args:
        org_order_no: 원주문번호
        qty: 정정/취소 수량
        price: 정정 가격
        order_type: 주문 유형
        cncl_type: 취소 유형 ("01":정정, "02":취소)

    Returns:
        Dict: 정정/취소 결과
    """
    agent = get_agent()
    result = agent.order_rvsecncl(org_order_no, qty, price, order_type, cncl_type)
    return validate_api_response(result, "주문 정정/취소")


@server.tool()
async def order_resv(
    code: str, qty: str, price: str, order_type: str
) -> Dict[str, Any]:
    """예약 주문

    Args:
        code: 종목코드 6자리
        qty: 주문 수량
        price: 주문 가격
        order_type: 주문 유형

    Returns:
        Dict: 예약 주문 결과
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.order_resv(code, qty, price, order_type)
    return validate_api_response(result, "예약 주문")


@server.tool()
async def order_resv_rvsecncl(
    seq: str, qty: str, price: str, order_type: str
) -> Dict[str, Any]:
    """예약 주문 정정/취소

    Args:
        seq: 예약 주문 일련번호
        qty: 정정/취소 수량
        price: 정정 가격
        order_type: 주문 유형

    Returns:
        Dict: 예약 정정/취소 결과
    """
    agent = get_agent()
    result = agent.order_resv_rvsecncl(seq, qty, price, order_type)
    return validate_api_response(result, "예약 주문 정정/취소")


@server.tool()
async def order_resv_ccnl() -> Dict[str, Any]:
    """예약 주문 전체 취소

    Returns:
        Dict: 전체 취소 결과
    """
    agent = get_agent()
    result = agent.order_resv_ccnl()
    return validate_api_response(result, "예약 주문 전체 취소")
