"""Investor & program trading MCP tools"""
from typing import Any, Dict
from ..server import get_agent, server
from ..errors import validate_api_response, InvalidParameterError


@server.tool()
async def get_stock_investor(code: str) -> Dict[str, Any]:
    """종목별 투자자 매매동향"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_stock_investor(code)
    return validate_api_response(result, "투자자 매매동향 조회")


@server.tool()
async def get_investor_daily_by_market(
    fid_cond_mrkt_div_code: str = "U",
    fid_input_iscd: str = "0001",
    fid_input_date_1: str = "",
    fid_input_iscd_1: str = "KSP",
    fid_input_date_2: str = "",
    fid_input_iscd_2: str = "0001",
) -> Dict[str, Any]:
    """시장별 투자자 일별 매매동향"""
    agent = get_agent()
    result = agent.get_investor_daily_by_market(
        fid_cond_mrkt_div_code,
        fid_input_iscd,
        fid_input_date_1,
        fid_input_iscd_1,
        fid_input_date_2,
        fid_input_iscd_2,
    )
    return validate_api_response(result, "시장별 투자자 일별 동향 조회")


@server.tool()
async def get_investor_time_by_market(
    fid_input_iscd: str = "999", fid_input_iscd_2: str = "S001"
) -> Dict[str, Any]:
    """시장별 투자자 시간대별 매매동향"""
    agent = get_agent()
    result = agent.get_investor_time_by_market(fid_input_iscd, fid_input_iscd_2)
    return validate_api_response(result, "시장별 투자자 시간대별 동향 조회")


@server.tool()
async def get_foreign_broker_net_buy(
    code: str, foreign_brokers: list, date: str
) -> Dict[str, Any]:
    """외국인/기관 순매수 조회"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_foreign_broker_net_buy(code, foreign_brokers, date)
    return {"success": True, "data": result}


@server.tool()
async def get_stock_member(code: str) -> Dict[str, Any]:
    """증권사별 매매동향"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_stock_member(code)
    return validate_api_response(result, "증권사별 매매동향 조회")


@server.tool()
async def get_member_transaction(code: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """증권사 기간별 거래"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_member_transaction(code, start_date, end_date)
    return validate_api_response(result, "증권사 기간별 거래 조회")


@server.tool()
async def get_program_trade_by_stock(code: str, date: str = "") -> Dict[str, Any]:
    """종목별 프로그램 매매"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_program_trade_by_stock(code, date)
    return validate_api_response(result, "프로그램 매매 조회")


@server.tool()
async def get_program_trade_daily_summary(code: str, date: str = "") -> Dict[str, Any]:
    """프로그램 매매 일별 요약"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_program_trade_daily_summary(code, date)
    return validate_api_response(result, "프로그램 매매 일별 요약 조회")


@server.tool()
async def get_program_trade_market_daily(start_date: str, end_date: str) -> Dict[str, Any]:
    """시장 프로그램 매매"""
    agent = get_agent()
    result = agent.get_program_trade_market_daily(start_date, end_date)
    return validate_api_response(result, "시장 프로그램 매매 조회")


@server.tool()
async def get_program_trade_hourly_trend(code: str = "") -> Dict[str, Any]:
    """프로그램 매매 시간대별 추세"""
    agent = get_agent()
    result = agent.get_program_trade_hourly_trend(code)
    return validate_api_response(result, "프로그램 매매 시간대별 추세 조회")


@server.tool()
async def get_program_trade_period_detail(
    code: str, start_date: str, end_date: str
) -> Dict[str, Any]:
    """프로그램 매매 기간 상세"""
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_program_trade_period_detail(code, start_date, end_date)
    return validate_api_response(result, "프로그램 매매 기간 상세 조회")
