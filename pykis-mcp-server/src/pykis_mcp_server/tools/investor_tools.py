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


@server.tool()
async def get_frgnmem_pchs_trend(stock_code: str) -> Dict[str, Any]:
    """외국인 매수 추세 조회

    Args:
        stock_code: 종목코드 6자리

    Returns:
        Dict: 외국인 매수 추세 데이터
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_frgnmem_pchs_trend(stock_code)
    return validate_api_response(result, "외국인 매수 추세 조회")


@server.tool()
async def get_frgnmem_trade_estimate(
    stock_code: str, cls_code: str = "0"
) -> Dict[str, Any]:
    """외국인 매매 추정 조회

    Args:
        stock_code: 종목코드 6자리
        cls_code: 분류코드 (0=전체)

    Returns:
        Dict: 외국인 매매 추정 데이터
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_frgnmem_trade_estimate(stock_code, cls_code)
    return validate_api_response(result, "외국인 매매 추정 조회")


@server.tool()
async def get_frgnmem_trade_trend(
    stock_code: str, cls_code: str = "0", period: str = "D"
) -> Dict[str, Any]:
    """외국인 매매 추세 조회

    Args:
        stock_code: 종목코드 6자리
        cls_code: 분류코드 (0=전체)
        period: 기간구분 (D=일별)

    Returns:
        Dict: 외국인 매매 추세 데이터
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_frgnmem_trade_trend(stock_code, cls_code, period)
    return validate_api_response(result, "외국인 매매 추세 조회")


@server.tool()
async def get_investor_trade_by_stock_daily(
    stock_code: str, start_date: str = "", end_date: str = ""
) -> Dict[str, Any]:
    """종목별 투자자 일별 매매동향 조회

    Args:
        stock_code: 종목코드 6자리
        start_date: 시작일자 (YYYYMMDD)
        end_date: 종료일자 (YYYYMMDD)

    Returns:
        Dict: 투자자별 일별 매매동향
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")
    agent = get_agent()
    result = agent.get_investor_trade_by_stock_daily(stock_code, start_date, end_date)
    return validate_api_response(result, "투자자 일별 매매동향 조회")


@server.tool()
async def get_investor_trend_estimate(
    market: str = "0", investor: str = "1000"
) -> Dict[str, Any]:
    """투자자별 추정 동향 조회

    Args:
        market: 시장구분 (0=전체, 1=KOSPI, 2=KOSDAQ)
        investor: 투자자구분 (1000=개인, 9000=외국인 등)

    Returns:
        Dict: 투자자별 추정 동향
    """
    agent = get_agent()
    result = agent.get_investor_trend_estimate(market, investor)
    return validate_api_response(result, "투자자 추정 동향 조회")


@server.tool()
async def get_investor_program_trade_today(
    market: str = "0"
) -> Dict[str, Any]:
    """당일 투자자 프로그램 매매 조회

    Args:
        market: 시장구분 (0=전체, 1=KOSPI, 2=KOSDAQ)

    Returns:
        Dict: 당일 투자자 프로그램 매매 데이터
    """
    agent = get_agent()
    result = agent.get_investor_program_trade_today(market)
    return validate_api_response(result, "당일 투자자 프로그램 매매 조회")


@server.tool()
async def analyze_broker_accumulation(
    broker_name: str,
    days: int = 7,
    top_n: int = 10
) -> Dict[str, Any]:
    """특정 증권사의 기간별 매집 종목 분석

    지정된 증권사가 최근 N일간 가장 많이 순매수한 종목을 분석합니다.
    주요 거래량 상위 종목을 대상으로 분석합니다.

    Args:
        broker_name: 증권사명 (예: "모건스탠리", "JP모건", "골드만삭스")
        days: 분석 기간 (기본값: 7일)
        top_n: 상위 N개 종목 반환 (기본값: 10)

    Returns:
        Dict: 매집 분석 결과
            - broker: 증권사명
            - period: 분석 기간
            - top_accumulated: 순매수 상위 종목 리스트
                - code: 종목코드
                - name: 종목명
                - net_buy_volume: 순매수량
                - net_buy_amount: 순매수금액
            - analysis_date: 분석 일시
    """
    from datetime import datetime, timedelta

    agent = get_agent()

    # 분석 기간 계산
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    # 거래량 상위 종목 조회 (분석 대상)
    top_volume = agent.get_volume_rank("0", "0", "0")
    if not top_volume or top_volume.get("rt_cd") != "0":
        return {
            "success": False,
            "message": "거래량 상위 종목 조회 실패",
            "error_code": "VOLUME_RANK_FAILED"
        }

    # 상위 50개 종목에 대해 증권사별 거래 분석
    accumulation_data = []
    stocks = top_volume.get("output", [])[:50]

    for stock in stocks:
        code = stock.get("mksc_shrn_iscd", stock.get("stck_shrn_iscd", ""))
        name = stock.get("hts_kor_isnm", "")

        if not code or len(code) != 6:
            continue

        try:
            # 증권사별 기간 거래 조회
            member_data = agent.get_member_transaction(code, start_str, end_str)
            if not member_data or member_data.get("rt_cd") != "0":
                continue

            # 지정 증권사 찾기
            for member in member_data.get("output", []):
                member_name = member.get("mbcr_name", "")
                if broker_name.lower() in member_name.lower():
                    net_buy = int(member.get("ntby_qty", 0))
                    net_amount = int(member.get("ntby_tr_pbmn", 0))

                    if net_buy > 0:  # 순매수인 경우만
                        accumulation_data.append({
                            "code": code,
                            "name": name,
                            "net_buy_volume": net_buy,
                            "net_buy_amount": net_amount,
                            "broker_detail": member_name
                        })
                    break
        except Exception:
            continue

    # 순매수량 기준 정렬
    accumulation_data.sort(key=lambda x: x["net_buy_volume"], reverse=True)

    return {
        "success": True,
        "broker": broker_name,
        "period": f"{start_str} ~ {end_str}",
        "days": days,
        "analyzed_stocks": len(stocks),
        "top_accumulated": accumulation_data[:top_n],
        "analysis_date": datetime.now().isoformat()
    }
