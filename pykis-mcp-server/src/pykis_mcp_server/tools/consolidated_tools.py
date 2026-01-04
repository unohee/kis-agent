"""Consolidated MCP Tools for PyKIS

110개 개별 도구를 18개 통합 도구로 압축하여 LLM의 도구 선택 효율성을 향상시킵니다.
각 도구는 query_type 또는 action 파라미터로 세부 기능을 선택합니다.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from ..errors import InvalidParameterError, validate_api_response
from ..server import get_agent, server


# =============================================================================
# 1. stock_quote - 주식 시세/호가/체결 통합 조회
# =============================================================================
@server.tool()
async def stock_quote(
    code: str,
    query_type: str = "price",
    market: str = "J",
    hour: str = "",
) -> Dict[str, Any]:
    """주식 시세/호가/체결 통합 조회

    Args:
        code: 종목코드 6자리 (예: "005930")
        query_type: 조회 유형
            - price: 현재가 간단 조회
            - detail: 현재가 상세 조회
            - detail2: 현재가 상세 조회 2 (추가 필드)
            - orderbook: 호가 10단계 조회
            - execution: 체결 정보 조회
            - time_execution: 시간별 체결 조회 (hour 필요)
        market: 시장구분 (J=주식, ETF, ETN)
        hour: 시간 (HHMMSS, time_execution 시 사용, 기본값: 155900)

    Returns:
        Dict: 조회 유형에 따른 시세/호가/체결 정보
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    valid_types = [
        "price",
        "detail",
        "detail2",
        "orderbook",
        "execution",
        "time_execution",
    ]
    if query_type not in valid_types:
        raise InvalidParameterError("query_type", f"유효한 값: {valid_types}")

    agent = get_agent()

    if query_type == "price":
        result = agent.get_stock_price(code)
        return validate_api_response(result, "현재가 조회")
    elif query_type == "detail":
        result = agent.inquire_price(code, market)
        return validate_api_response(result, "현재가 상세 조회")
    elif query_type == "detail2":
        result = agent.inquire_price_2(code, market)
        return validate_api_response(result, "현재가 상세 조회 2")
    elif query_type == "orderbook":
        result = agent.get_orderbook_raw(code)
        return validate_api_response(result, "호가 조회")
    elif query_type == "execution":
        result = agent.inquire_ccnl(code, market)
        return validate_api_response(result, "체결 정보 조회")
    elif query_type == "time_execution":
        hour = hour or "155900"
        result = agent.inquire_time_itemconclusion(code, hour)
        return validate_api_response(result, "시간별 체결 조회")


# =============================================================================
# 2. stock_chart - 주식 차트 데이터 통합 조회
# =============================================================================
@server.tool()
async def stock_chart(
    code: str,
    timeframe: str = "daily",
    date: str = "",
    period: str = "D",
    start_date: str = "",
    end_date: str = "",
    hour: str = "153000",
) -> Dict[str, Any]:
    """주식 차트 데이터 통합 조회

    Args:
        code: 종목코드 6자리
        timeframe: 차트 유형
            - minute: 분봉 데이터 (date가 있으면 특정일, 없으면 당일)
            - daily: 일봉 데이터
            - daily_30: 최근 30일 일봉
            - weekly: 주봉 데이터
            - monthly: 월봉 데이터
        date: 조회 기준일 (YYYYMMDD, minute에서 특정일 조회 시)
        period: 기간구분 (D=일, W=주, M=월)
        start_date: 시작일자 (YYYYMMDD)
        end_date: 종료일자 (YYYYMMDD)
        hour: 시각 (HHMMSS, 분봉 조회 시)

    Returns:
        Dict: 차트 데이터 (timeframe에 따라 다름)
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    valid_timeframes = ["minute", "daily", "daily_30", "weekly", "monthly"]
    if timeframe not in valid_timeframes:
        raise InvalidParameterError("timeframe", f"유효한 값: {valid_timeframes}")

    agent = get_agent()

    if timeframe == "minute":
        if date:
            # 특정일 분봉
            result = agent.get_daily_minute_price(code, date, hour)
            return validate_api_response(result, f"분봉 조회 ({date})")
        else:
            # 당일 분봉
            result = agent.get_intraday_price(code)
            return validate_api_response(result, "당일 분봉 조회")
    elif timeframe == "daily":
        result = agent.inquire_daily_itemchartprice(code, start_date, end_date)
        return validate_api_response(result, "일봉 데이터 조회")
    elif timeframe == "daily_30":
        result = agent.inquire_daily_price(code, period)
        return validate_api_response(result, "최근 30일 조회")
    elif timeframe == "weekly":
        result = agent.inquire_daily_price(code, "W")
        return validate_api_response(result, "주봉 데이터 조회")
    elif timeframe == "monthly":
        result = agent.inquire_daily_price(code, "M")
        return validate_api_response(result, "월봉 데이터 조회")


# =============================================================================
# 3. index_data - 지수 데이터 통합 조회
# =============================================================================
@server.tool()
async def index_data(
    index_code: str = "0001",
    data_type: str = "current",
    category: str = "0001",
    time_code: str = "093000",
) -> Dict[str, Any]:
    """지수 데이터 통합 조회

    Args:
        index_code: 지수 코드 (0001=KOSPI, 1001=KOSDAQ)
        data_type: 조회 유형
            - current: 현재 지수
            - daily: 일봉 데이터
            - tick: 틱 데이터
            - time: 시간별 데이터
            - minute: 분봉 데이터
            - category: 업종별 지수
        category: 업종코드 (category 유형에서 사용)
        time_code: 시간코드 (HHMMSS, minute에서 사용)

    Returns:
        Dict: 지수 데이터
    """
    valid_types = ["current", "daily", "tick", "time", "minute", "category"]
    if data_type not in valid_types:
        raise InvalidParameterError("data_type", f"유효한 값: {valid_types}")

    agent = get_agent()

    if data_type == "current":
        result = agent.inquire_index_price(index_code)
        return validate_api_response(result, "지수 현재가 조회")
    elif data_type == "daily":
        result = agent.get_index_daily_price(index_code)
        return validate_api_response(result, "지수 일봉 조회")
    elif data_type == "tick":
        result = agent.inquire_index_tickprice(index_code)
        return validate_api_response(result, "지수 틱 조회")
    elif data_type == "time":
        result = agent.inquire_index_timeprice(index_code)
        return validate_api_response(result, "지수 시간별 조회")
    elif data_type == "minute":
        result = agent.get_index_minute_data(index_code, time_code)
        return validate_api_response(result, "지수 분봉 조회")
    elif data_type == "category":
        result = agent.inquire_index_category_price(category=category)
        return validate_api_response(result, "업종별 지수 조회")


# =============================================================================
# 4. market_ranking - 시장 순위 통합 조회
# =============================================================================
@server.tool()
async def market_ranking(
    ranking_type: str = "volume",
    market: str = "0",
    sign: str = "0",
    volume: int = 5000000,
) -> Dict[str, Any]:
    """시장 순위 통합 조회

    Args:
        ranking_type: 순위 유형
            - volume: 거래량 순위
            - gainers: 상승률 순위
            - losers: 하락률 순위 (sign=3으로 fluctuation 호출)
            - fluctuation: 등락률 순위 (sign으로 방향 지정)
            - volume_power: 체결강도 순위
            - market_status: 시장 전체 등락 현황
        market: 시장 구분 (0=전체, 1=KOSPI, 2=KOSDAQ, ALL/KOSPI/KOSDAQ)
        sign: 등락 구분 (0=전체, 1=상승, 2=보합, 3=하락)
        volume: 최소 거래량 필터

    Returns:
        Dict: 시장 순위 데이터
    """
    valid_types = [
        "volume",
        "gainers",
        "losers",
        "fluctuation",
        "volume_power",
        "market_status",
    ]
    if ranking_type not in valid_types:
        raise InvalidParameterError("ranking_type", f"유효한 값: {valid_types}")

    agent = get_agent()
    market_api = agent.stock_api.market_api

    # 시장 코드 매핑 (MCP 파라미터 → API 파라미터)
    market_name_map = {
        "0": "ALL",
        "1": "KOSPI",
        "2": "KOSDAQ",
        "ALL": "ALL",
        "KOSPI": "KOSPI",
        "KOSDAQ": "KOSDAQ",
    }
    market_name = market_name_map.get(market, "ALL")

    # input_iscd 매핑
    market_iscd_map = {"ALL": "0000", "KOSPI": "0001", "KOSDAQ": "1001"}
    input_iscd = market_iscd_map.get(market_name, "0000")

    if ranking_type == "volume":
        # 거래량 순위: FHPST01710000
        # price_api.volume_rank() 사용 (UPPERCASE 파라미터 필요)
        price_api = agent.stock_api.price_api
        result = price_api.volume_rank(
            market="J",
            screen_code="20171",
            stock_code=input_iscd,
            div_cls="0",
            sort_cls="0",  # 평균거래량순
            target_cls="111111111",
            exclude_cls="0000000000",
            price_from="",
            price_to="",
            volume=str(volume),
            date="",
        )
        return validate_api_response(result, "거래량 순위 조회")

    elif ranking_type in ["gainers", "losers", "fluctuation"]:
        # 등락률 순위: FHPST01700000
        # sign 매핑: 1=상승 → rate_min=0, 3=하락 → rate_max=0
        rate_min = "-30"
        rate_max = "30"
        if ranking_type == "gainers" or sign == "1":
            rate_min = "0"  # 상승만
        elif ranking_type == "losers" or sign == "3":
            rate_max = "0"  # 하락만

        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20170",
            "fid_input_iscd": input_iscd,
            "fid_rank_sort_cls_code": "0",
            "fid_input_cnt_1": "50",
            "fid_prc_cls_code": "0",
            "fid_input_price_1": "0",
            "fid_input_price_2": "1000000",
            "fid_vol_cnt": str(volume),
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
            "fid_div_cls_code": "0",
            "fid_rsfl_rate1": rate_min,
            "fid_rsfl_rate2": rate_max,
        }
        result = market_api._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/fluctuation",
            tr_id="FHPST01700000",
            params=params,
        )
        operation = {
            "gainers": "상승률 순위 조회",
            "losers": "하락률 순위 조회",
            "fluctuation": "등락률 순위 조회",
        }
        return validate_api_response(
            result, operation.get(ranking_type, "등락률 순위 조회")
        )

    elif ranking_type == "volume_power":
        # 체결강도 순위: FHPST01680000
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20168",
            "fid_input_iscd": input_iscd,
            "fid_div_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "",
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
        }
        result = market_api._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/volume-power",
            tr_id="FHPST01680000",
            params=params,
        )
        return validate_api_response(result, "체결강도 순위 조회")

    elif ranking_type == "market_status":
        result = agent.get_market_fluctuation()
        return validate_api_response(result, "시장 등락 현황 조회")


# =============================================================================
# 5. investor_flow - 투자자 매매동향 통합 조회
# =============================================================================
@server.tool()
async def investor_flow(
    query_type: str,
    code: str = "",
    market: str = "0",
    start_date: str = "",
    end_date: str = "",
    investor_type: str = "1000",
) -> Dict[str, Any]:
    """투자자 매매동향 통합 조회

    Args:
        query_type: 조회 유형
            - stock: 종목별 투자자 동향
            - market_daily: 시장별 일별 동향
            - market_time: 시장별 시간대별 동향
            - foreign_trend: 외국인 매수 추세
            - foreign_estimate: 외국인 매매 추정
            - foreign_trading: 외국인 매매 추세
            - stock_daily: 종목별 일별 투자자 동향
            - investor_estimate: 투자자별 추정 동향
            - program_today: 당일 투자자 프로그램 매매
        code: 종목코드 (stock, foreign 관련 유형에서 필요)
        market: 시장 구분 (0=전체, 1=KOSPI, 2=KOSDAQ)
        start_date: 시작일자 (YYYYMMDD)
        end_date: 종료일자 (YYYYMMDD)
        investor_type: 투자자구분 (1000=개인, 9000=외국인 등)

    Returns:
        Dict: 투자자 매매동향 데이터
    """
    valid_types = [
        "stock",
        "market_daily",
        "market_time",
        "foreign_trend",
        "foreign_estimate",
        "foreign_trading",
        "stock_daily",
        "investor_estimate",
        "program_today",
    ]
    if query_type not in valid_types:
        raise InvalidParameterError("query_type", f"유효한 값: {valid_types}")

    agent = get_agent()

    if query_type == "stock":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        result = agent.get_stock_investor(code)
        return validate_api_response(result, "종목별 투자자 동향 조회")
    elif query_type == "market_daily":
        result = agent.get_investor_daily_by_market()
        return validate_api_response(result, "시장별 일별 투자자 동향 조회")
    elif query_type == "market_time":
        result = agent.get_investor_time_by_market()
        return validate_api_response(result, "시장별 시간대별 투자자 동향 조회")
    elif query_type == "foreign_trend":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        result = agent.get_frgnmem_pchs_trend(code)
        return validate_api_response(result, "외국인 매수 추세 조회")
    elif query_type == "foreign_estimate":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        result = agent.get_frgnmem_trade_estimate(code)
        return validate_api_response(result, "외국인 매매 추정 조회")
    elif query_type == "foreign_trading":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        result = agent.get_frgnmem_trade_trend(code)
        return validate_api_response(result, "외국인 매매 추세 조회")
    elif query_type == "stock_daily":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        result = agent.get_investor_trade_by_stock_daily(code, start_date, end_date)
        return validate_api_response(result, "종목별 일별 투자자 동향 조회")
    elif query_type == "investor_estimate":
        result = agent.get_investor_trend_estimate(market, investor_type)
        return validate_api_response(result, "투자자별 추정 동향 조회")
    elif query_type == "program_today":
        result = agent.get_investor_program_trade_today(market)
        return validate_api_response(result, "당일 투자자 프로그램 매매 조회")


# =============================================================================
# 6. broker_trading - 증권사 매매동향 통합 조회
# =============================================================================
@server.tool()
async def broker_trading(
    code: str,
    query_type: str = "current",
    start_date: str = "",
    end_date: str = "",
) -> Dict[str, Any]:
    """증권사 매매동향 통합 조회

    Args:
        code: 종목코드 6자리
        query_type: 조회 유형
            - current: 현재 증권사별 매매
            - period: 기간별 증권사 거래
            - info: 회원사 정보
        start_date: 시작일자 (YYYYMMDD, period에서 사용)
        end_date: 종료일자 (YYYYMMDD, period에서 사용)

    Returns:
        Dict: 증권사 매매동향 데이터
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    valid_types = ["current", "period", "info"]
    if query_type not in valid_types:
        raise InvalidParameterError("query_type", f"유효한 값: {valid_types}")

    agent = get_agent()

    if query_type == "current":
        result = agent.get_stock_member(code)
        return validate_api_response(result, "증권사별 매매 조회")
    elif query_type == "period":
        if not start_date or not end_date:
            raise InvalidParameterError(
                "start_date/end_date", "기간 조회 시 시작/종료일이 필요합니다"
            )
        result = agent.get_member_transaction(code, start_date, end_date)
        return validate_api_response(result, "기간별 증권사 거래 조회")
    elif query_type == "info":
        result = agent.get_member(code)
        return validate_api_response(result, "회원사 정보 조회")


# =============================================================================
# 7. program_trading - 프로그램 매매 통합 조회
# =============================================================================
@server.tool()
async def program_trading(
    query_type: str,
    code: str = "",
    date: str = "",
    start_date: str = "",
    end_date: str = "",
) -> Dict[str, Any]:
    """프로그램 매매 통합 조회

    Args:
        query_type: 조회 유형
            - stock: 종목별 프로그램 매매
            - daily_summary: 일별 요약
            - market: 시장 전체 일별
            - hourly: 시간대별 추세
            - period: 기간별 상세
        code: 종목코드 (stock, daily_summary, hourly, period에서 사용)
        date: 기준일자 (YYYYMMDD)
        start_date: 시작일자 (YYYYMMDD, market/period에서 사용)
        end_date: 종료일자 (YYYYMMDD, market/period에서 사용)

    Returns:
        Dict: 프로그램 매매 데이터
    """
    valid_types = ["stock", "daily_summary", "market", "hourly", "period"]
    if query_type not in valid_types:
        raise InvalidParameterError("query_type", f"유효한 값: {valid_types}")

    agent = get_agent()

    if query_type == "stock":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        result = agent.get_program_trade_by_stock(code, date or None)
        return validate_api_response(result, "종목별 프로그램 매매 조회")
    elif query_type == "daily_summary":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        result = agent.get_program_trade_daily_summary(code, date)
        return validate_api_response(result, "프로그램 매매 일별 요약 조회")
    elif query_type == "market":
        if not start_date or not end_date:
            raise InvalidParameterError(
                "start_date/end_date", "시장 조회 시 기간이 필요합니다"
            )
        result = agent.get_program_trade_market_daily(start_date, end_date)
        return validate_api_response(result, "시장 프로그램 매매 조회")
    elif query_type == "hourly":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        result = agent.get_program_trade_hourly_trend(code)
        return validate_api_response(result, "시간대별 프로그램 매매 추세 조회")
    elif query_type == "period":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        if not start_date or not end_date:
            raise InvalidParameterError(
                "start_date/end_date", "기간 조회 시 시작/종료일이 필요합니다"
            )
        result = agent.get_program_trade_period_detail(code, start_date, end_date)
        return validate_api_response(result, "기간별 프로그램 매매 상세 조회")


# =============================================================================
# 8. account_query - 계좌 정보 통합 조회
# =============================================================================
@server.tool()
async def account_query(
    query_type: str,
    code: str = "",
    price: str = "",
    start_date: str = "",
    end_date: str = "",
    date: str = "",
) -> Dict[str, Any]:
    """계좌 정보 통합 조회

    Args:
        query_type: 조회 유형
            - balance: 계좌 잔고
            - order_ability: 주문 가능 금액/수량 (code, price 필요)
            - order_quantity: 계좌별 주문 가능 수량 (code 필요)
            - trades: 일자별 체결 내역 (date 선택)
            - profit_loss: 평가/실현 손익
            - sell_quantity: 매도 가능 수량
            - period_profit: 기간별 매매 손익 (start_date, end_date 필요)
            - margin: 증거금
            - credit: 신용 거래 가능 (code, price 필요)
            - rights: 기간별 권리 (start_date, end_date 필요)
            - total: 총자산
        code: 종목코드 (order_ability, order_quantity, credit에서 사용)
        price: 주문 가격 (order_ability, credit에서 사용)
        start_date: 시작일자 (YYYYMMDD)
        end_date: 종료일자 (YYYYMMDD)
        date: 조회일자 (YYYYMMDD, trades에서 사용)

    Returns:
        Dict: 계좌 정보
    """
    valid_types = [
        "balance",
        "order_ability",
        "order_quantity",
        "trades",
        "profit_loss",
        "sell_quantity",
        "period_profit",
        "margin",
        "credit",
        "rights",
        "total",
    ]
    if query_type not in valid_types:
        raise InvalidParameterError("query_type", f"유효한 값: {valid_types}")

    agent = get_agent()

    if query_type == "balance":
        result = agent.get_account_balance()
        return validate_api_response(result, "계좌 잔고 조회")
    elif query_type == "order_ability":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        if not price:
            raise InvalidParameterError("price", "주문 가격이 필요합니다")
        result = agent.get_possible_order_amount(code, price)
        return validate_api_response(result, "주문 가능 금액 조회")
    elif query_type == "order_quantity":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        result = agent.get_account_order_quantity(code)
        return validate_api_response(result, "주문 가능 수량 조회")
    elif query_type == "trades":
        result = agent.inquire_daily_ccld(date)
        return validate_api_response(result, "체결 내역 조회")
    elif query_type == "profit_loss":
        result = agent.inquire_balance_rlz_pl()
        return validate_api_response(result, "평가/실현 손익 조회")
    elif query_type == "sell_quantity":
        result = agent.inquire_psbl_sell()
        return validate_api_response(result, "매도 가능 수량 조회")
    elif query_type == "period_profit":
        if not start_date or not end_date:
            raise InvalidParameterError("start_date/end_date", "기간이 필요합니다")
        result = agent.inquire_period_trade_profit(start_date, end_date)
        return validate_api_response(result, "기간별 매매 손익 조회")
    elif query_type == "margin":
        result = agent.inquire_intgr_margin()
        return validate_api_response(result, "증거금 조회")
    elif query_type == "credit":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        if not price:
            raise InvalidParameterError("price", "주문 가격이 필요합니다")
        result = agent.inquire_credit_psamount(code, price)
        return validate_api_response(result, "신용 거래 가능 조회")
    elif query_type == "rights":
        if not start_date or not end_date:
            raise InvalidParameterError("start_date/end_date", "기간이 필요합니다")
        result = agent.inquire_period_rights(start_date, end_date)
        return validate_api_response(result, "기간별 권리 조회")
    elif query_type == "total":
        result = agent.get_total_asset()
        return validate_api_response(result, "총자산 조회")


# =============================================================================
# 9. order_execute - 주문 실행 통합
# =============================================================================
@server.tool()
async def order_execute(
    action: str,
    code: str,
    quantity: str,
    price: str = "0",
    order_type: str = "00",
    credit: bool = False,
    credit_type: str = "21",
    loan_date: str = "",
) -> Dict[str, Any]:
    """주문 실행 통합

    Args:
        action: 주문 유형 (buy=매수, sell=매도)
        code: 종목코드 6자리
        quantity: 주문 수량
        price: 주문 가격 (시장가: "0")
        order_type: 주문 유형 ("00"=지정가, "01"=시장가, "03"=최유리가)
        credit: 신용 거래 여부 (True/False)
        credit_type: 신용 유형 ("21"=자기융자, "22"=유통융자)
        loan_date: 대출일자 (YYYYMMDD, 신용 매도 시 필수)

    Returns:
        Dict: 주문 결과
    """
    if action not in ["buy", "sell"]:
        raise InvalidParameterError("action", "'buy' 또는 'sell'이어야 합니다")
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()

    if credit:
        # 신용 거래
        if action == "buy":
            result = agent.order_credit_buy(
                code, credit_type, quantity, price, order_type
            )
            return validate_api_response(result, "신용 매수 주문")
        else:
            if not loan_date:
                raise InvalidParameterError(
                    "loan_date", "신용 매도 시 대출일자가 필요합니다"
                )
            result = agent.order_credit_sell(
                code, loan_date, quantity, price, order_type
            )
            return validate_api_response(result, "신용 매도 주문")
    else:
        # 현금 거래
        if order_type == "01" and price == "0":
            # 시장가 주문 (SOR)
            result = agent.order_cash_sor(code, quantity) if action == "buy" else None
            if result is None:
                # 시장가 매도는 order_cash 사용
                result = agent.order_stock_cash(
                    action, code, order_type, quantity, price
                )
            return validate_api_response(result, f"시장가 {action} 주문")
        else:
            result = agent.order_stock_cash(action, code, order_type, quantity, price)
            return validate_api_response(result, f"현금 {action} 주문")


# =============================================================================
# 10. order_manage - 주문 관리 통합 (정정/취소/예약)
# =============================================================================
@server.tool()
async def order_manage(
    action: str,
    order_no: str = "",
    code: str = "",
    quantity: str = "",
    price: str = "",
    order_type: str = "00",
    seq: str = "",
) -> Dict[str, Any]:
    """주문 관리 통합 (정정/취소/예약)

    Args:
        action: 관리 유형
            - modify: 주문 정정 (order_no, quantity, price 필요)
            - cancel: 주문 취소 (order_no, quantity 필요)
            - reserve: 예약 주문 (code, quantity, price 필요)
            - reserve_modify: 예약 정정/취소 (seq, quantity, price 필요)
            - reserve_cancel_all: 예약 전체 취소
            - list_pending: 정정/취소 가능 목록 조회
        order_no: 원주문번호 (modify, cancel에서 사용)
        code: 종목코드 (reserve에서 사용)
        quantity: 수량
        price: 가격
        order_type: 주문 유형 ("00"=지정가, "01"=시장가)
        seq: 예약 주문 일련번호 (reserve_modify에서 사용)

    Returns:
        Dict: 주문 관리 결과
    """
    valid_actions = [
        "modify",
        "cancel",
        "reserve",
        "reserve_modify",
        "reserve_cancel_all",
        "list_pending",
    ]
    if action not in valid_actions:
        raise InvalidParameterError("action", f"유효한 값: {valid_actions}")

    agent = get_agent()

    if action == "modify":
        if not order_no:
            raise InvalidParameterError("order_no", "원주문번호가 필요합니다")
        result = agent.order_rvsecncl(order_no, quantity, price, order_type, "01")
        return validate_api_response(result, "주문 정정")
    elif action == "cancel":
        if not order_no:
            raise InvalidParameterError("order_no", "원주문번호가 필요합니다")
        result = agent.order_rvsecncl(order_no, quantity, price, order_type, "02")
        return validate_api_response(result, "주문 취소")
    elif action == "reserve":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        result = agent.order_resv(code, quantity, price, order_type)
        return validate_api_response(result, "예약 주문")
    elif action == "reserve_modify":
        if not seq:
            raise InvalidParameterError("seq", "예약 주문 일련번호가 필요합니다")
        result = agent.order_resv_rvsecncl(seq, quantity, price, order_type)
        return validate_api_response(result, "예약 주문 정정/취소")
    elif action == "reserve_cancel_all":
        result = agent.order_resv_ccnl()
        return validate_api_response(result, "예약 주문 전체 취소")
    elif action == "list_pending":
        result = agent.inquire_psbl_rvsecncl()
        return validate_api_response(result, "정정/취소 가능 목록 조회")


# =============================================================================
# 11. stock_info - 종목 정보 통합 조회
# =============================================================================
@server.tool()
async def stock_info(
    code: str,
    info_type: str = "basic",
) -> Dict[str, Any]:
    """종목 정보 통합 조회

    Args:
        code: 종목코드 6자리 (vi_status에서는 공백 가능 - 전체 조회)
        info_type: 정보 유형
            - basic: 기본 정보
            - detail: 상세 정보
            - financial: 재무 정보
            - buy_sell_ratio: 매수/매도 비율
            - expected_execution: 호가 예상 체결
            - vi_status: VI 발동 상태 (code 공백 시 전체)

    Returns:
        Dict: 종목 정보
    """
    valid_types = [
        "basic",
        "detail",
        "financial",
        "buy_sell_ratio",
        "expected_execution",
        "vi_status",
    ]
    if info_type not in valid_types:
        raise InvalidParameterError("info_type", f"유효한 값: {valid_types}")

    if info_type != "vi_status" and (not code or len(code) != 6):
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()

    if info_type == "basic":
        result = agent.get_stock_info(code)
        return validate_api_response(result, "종목 기본 정보 조회")
    elif info_type == "detail":
        result = agent.get_stock_basic(code)
        return validate_api_response(result, "종목 상세 정보 조회")
    elif info_type == "financial":
        result = agent.get_stock_financial(code)
        return validate_api_response(result, "종목 재무 정보 조회")
    elif info_type == "buy_sell_ratio":
        result = agent.get_pbar_tratio(code)
        return validate_api_response(result, "매수/매도 비율 조회")
    elif info_type == "expected_execution":
        result = agent.get_asking_price_exp_ccn(code)
        return validate_api_response(result, "호가 예상 체결 조회")
    elif info_type == "vi_status":
        result = agent.inquire_vi_status(code)
        return validate_api_response(result, "VI 발동 상태 조회")


# =============================================================================
# 12. overtime_trading - 시간외 거래 통합 조회
# =============================================================================
@server.tool()
async def overtime_trading(
    code: str,
    query_type: str = "current",
    period: str = "D",
) -> Dict[str, Any]:
    """시간외 거래 통합 조회

    Args:
        code: 종목코드 6자리
        query_type: 조회 유형
            - current: 현재가
            - daily: 일별 시세
            - orderbook: 호가

    Returns:
        Dict: 시간외 거래 정보
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    valid_types = ["current", "daily", "orderbook"]
    if query_type not in valid_types:
        raise InvalidParameterError("query_type", f"유효한 값: {valid_types}")

    agent = get_agent()

    if query_type == "current":
        result = agent.inquire_overtime_price(code)
        return validate_api_response(result, "시간외 현재가 조회")
    elif query_type == "daily":
        result = agent.inquire_daily_overtimeprice(code, period)
        return validate_api_response(result, "시간외 일별 시세 조회")
    elif query_type == "orderbook":
        result = agent.inquire_overtime_asking_price(code)
        return validate_api_response(result, "시간외 호가 조회")


# =============================================================================
# 13. derivatives - 파생상품 조회
# =============================================================================
@server.tool()
async def derivatives(
    product_type: str,
    code: str = "",
) -> Dict[str, Any]:
    """파생상품 조회

    Args:
        product_type: 상품 유형
            - futures_code: KOSPI200 선물 종목코드
            - futures_price: 선물옵션 가격
            - elw: ELW 시세 (code 필요)
        code: ELW 종목코드 (elw에서 사용)

    Returns:
        Dict: 파생상품 정보
    """
    valid_types = ["futures_code", "futures_price", "elw"]
    if product_type not in valid_types:
        raise InvalidParameterError("product_type", f"유효한 값: {valid_types}")

    agent = get_agent()

    if product_type == "futures_code":
        result = agent.get_kospi200_futures_code()
        return validate_api_response(result, "KOSPI200 선물 종목코드 조회")
    elif product_type == "futures_price":
        result = agent.get_future_option_price()
        return validate_api_response(result, "선물옵션 가격 조회")
    elif product_type == "elw":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "ELW 종목코드는 6자리여야 합니다")
        result = agent.inquire_elw_price(code)
        return validate_api_response(result, "ELW 시세 조회")


# =============================================================================
# 14. interest_stocks - 관심종목/조건검색 조회
# =============================================================================
@server.tool()
async def interest_stocks(
    query_type: str,
    user_id: str,
    group_code: str = "",
    seq: int = 0,
) -> Dict[str, Any]:
    """관심종목/조건검색 조회

    Args:
        query_type: 조회 유형
            - condition: 조건검색식 종목 (seq 필요)
            - groups: 관심종목 그룹 목록
            - stocks: 그룹별 종목 목록 (group_code 필요)
        user_id: 사용자 ID
        group_code: 관심종목 그룹 코드 (stocks에서 사용)
        seq: 조건식 순번 (condition에서 사용)

    Returns:
        Dict: 관심종목/조건검색 결과
    """
    valid_types = ["condition", "groups", "stocks"]
    if query_type not in valid_types:
        raise InvalidParameterError("query_type", f"유효한 값: {valid_types}")

    if not user_id:
        raise InvalidParameterError("user_id", "사용자 ID가 필요합니다")

    agent = get_agent()

    if query_type == "condition":
        result = agent.get_condition_stocks(user_id, seq)
        return validate_api_response(result, "조건검색식 종목 조회")
    elif query_type == "groups":
        result = agent.get_interest_group_list(user_id)
        return validate_api_response(result, "관심종목 그룹 목록 조회")
    elif query_type == "stocks":
        if not group_code:
            raise InvalidParameterError("group_code", "그룹 코드가 필요합니다")
        result = agent.get_interest_stock_list(user_id, group_code)
        return validate_api_response(result, "그룹별 종목 목록 조회")


# =============================================================================
# 15. utility - 유틸리티 기능 통합
# =============================================================================
@server.tool()
async def utility(
    action: str,
    date: str = "",
    code: str = "",
) -> Dict[str, Any]:
    """유틸리티 기능 통합

    Args:
        action: 기능 유형
            - holiday_info: 휴장일 정보 (date 선택)
            - is_holiday: 특정일 휴장 여부 (date 필요)
            - credit_balance: 신용잔고 일별추이 (code, date 필요)
        date: 날짜 (YYYYMMDD)
        code: 종목코드 (credit_balance에서 사용)

    Returns:
        Dict: 유틸리티 결과
    """
    valid_actions = ["holiday_info", "is_holiday", "credit_balance"]
    if action not in valid_actions:
        raise InvalidParameterError("action", f"유효한 값: {valid_actions}")

    agent = get_agent()

    if action == "holiday_info":
        result = agent.get_holiday_info(date)
        return validate_api_response(result, "휴장일 정보 조회")
    elif action == "is_holiday":
        if not date:
            raise InvalidParameterError("date", "날짜가 필요합니다")
        result = agent.is_holiday(date)
        return validate_api_response(result, "휴장 여부 확인")
    elif action == "credit_balance":
        if not code or len(code) != 6:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
        if not date:
            raise InvalidParameterError("date", "날짜가 필요합니다")
        result = agent.get_daily_credit_balance(code, date)
        return validate_api_response(result, "신용잔고 일별추이 조회")


# =============================================================================
# 16. data_management - 데이터 관리 통합
# =============================================================================
@server.tool()
async def data_management(
    action: str,
    code: str,
    date: str = "",
    cache_dir: str = "minute_data",
    csv_dir: str = "",
    db_path: str = "",
) -> Dict[str, Any]:
    """데이터 관리 통합

    Args:
        action: 기능 유형
            - fetch_minute: 4일간 분봉 수집
            - support_resistance: 지지/저항선 계산
            - init_db: 분봉 DB 초기화
            - migrate_csv: CSV → DB 마이그레이션
        code: 종목코드 6자리
        date: 기준 날짜 (YYYYMMDD)
        cache_dir: 캐시 디렉토리 (fetch_minute에서 사용)
        csv_dir: CSV 디렉토리 (migrate_csv에서 사용)
        db_path: DB 경로 (init_db, migrate_csv에서 사용)

    Returns:
        Dict: 데이터 관리 결과
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    valid_actions = ["fetch_minute", "support_resistance", "init_db", "migrate_csv"]
    if action not in valid_actions:
        raise InvalidParameterError("action", f"유효한 값: {valid_actions}")

    agent = get_agent()

    if action == "fetch_minute":
        result = agent.fetch_minute_data(code, date, cache_dir)
        return validate_api_response(result, "분봉 데이터 수집")
    elif action == "support_resistance":
        result = agent.calculate_support_resistance(code, date)
        return validate_api_response(result, "지지/저항선 계산")
    elif action == "init_db":
        result = agent.init_minute_db(code, db_path)
        return validate_api_response(result, "분봉 DB 초기화")
    elif action == "migrate_csv":
        if not csv_dir:
            raise InvalidParameterError("csv_dir", "CSV 디렉토리가 필요합니다")
        result = agent.migrate_minute_csv_to_db(code, csv_dir, db_path)
        return validate_api_response(result, "CSV → DB 마이그레이션")


# =============================================================================
# 17. rate_limiter - Rate Limiter 관리 통합
# =============================================================================
@server.tool()
async def rate_limiter(
    action: str,
    requests_per_second: Optional[int] = None,
    requests_per_minute: Optional[int] = None,
    min_interval_ms: Optional[int] = None,
    enable_adaptive: Optional[bool] = None,
) -> Dict[str, Any]:
    """Rate Limiter 관리 통합

    Args:
        action: 기능 유형
            - status: 현재 상태 조회
            - reset: 상태 초기화
            - set_limits: 제한 값 설정
            - set_adaptive: 적응형 활성화/비활성화
        requests_per_second: 초당 최대 요청 수 (set_limits에서 사용)
        requests_per_minute: 분당 최대 요청 수 (set_limits에서 사용)
        min_interval_ms: 최소 요청 간격 ms (set_limits에서 사용)
        enable_adaptive: 적응형 활성화 여부 (set_adaptive에서 사용)

    Returns:
        Dict: Rate Limiter 관리 결과
    """
    valid_actions = ["status", "reset", "set_limits", "set_adaptive"]
    if action not in valid_actions:
        raise InvalidParameterError("action", f"유효한 값: {valid_actions}")

    agent = get_agent()

    # Rate Limiter는 로컬 상태 관리이므로 API 검증 대신 직접 응답 생성
    if action == "status":
        status = agent.get_rate_limiter_status()
        if status is None:
            return {
                "rt_cd": "0",
                "msg1": "Rate Limiter가 비활성화 상태입니다",
                "output": {"enabled": False},
            }
        return {
            "rt_cd": "0",
            "msg1": "Rate Limiter 상태 조회 성공",
            "output": status,
        }
    elif action == "reset":
        agent.reset_rate_limiter()
        return {
            "rt_cd": "0",
            "msg1": "Rate Limiter 초기화 완료",
            "output": {"success": True},
        }
    elif action == "set_limits":
        agent.set_rate_limits(
            requests_per_second=requests_per_second,
            requests_per_minute=requests_per_minute,
            min_interval_ms=min_interval_ms,
        )
        return {
            "rt_cd": "0",
            "msg1": "Rate Limiter 제한 설정 완료",
            "output": {
                "requests_per_second": requests_per_second,
                "requests_per_minute": requests_per_minute,
                "min_interval_ms": min_interval_ms,
            },
        }
    elif action == "set_adaptive":
        if enable_adaptive is None:
            raise InvalidParameterError("enable_adaptive", "활성화 여부가 필요합니다")
        # Note: enable_adaptive_rate_limiting 메서드가 없다면 rate_limiter 직접 설정
        if hasattr(agent, "enable_adaptive_rate_limiting"):
            agent.enable_adaptive_rate_limiting(enable_adaptive)
        elif agent.rate_limiter:
            agent.rate_limiter.enable_adaptive = enable_adaptive
        return {
            "rt_cd": "0",
            "msg1": f"적응형 Rate Limiting {'활성화' if enable_adaptive else '비활성화'} 완료",
            "output": {"enable_adaptive": enable_adaptive},
        }


# =============================================================================
# 18. method_discovery - Agent 메서드 탐색 통합
# =============================================================================
@server.tool()
async def method_discovery(
    action: str,
    query: str = "",
    method_name: str = "",
) -> Dict[str, Any]:
    """Agent 메서드 탐색 통합

    Args:
        action: 기능 유형
            - search: 키워드로 메서드 검색 (query 필요)
            - list_all: 전체 메서드 목록
            - usage: 특정 메서드 사용법 (method_name 필요)
        query: 검색 키워드 (search에서 사용)
        method_name: 메서드 이름 (usage에서 사용)

    Returns:
        Dict: 메서드 탐색 결과
    """
    valid_actions = ["search", "list_all", "usage"]
    if action not in valid_actions:
        raise InvalidParameterError("action", f"유효한 값: {valid_actions}")

    agent = get_agent()

    # method_discovery는 로컬 메서드이므로 API 검증 대신 직접 응답 생성
    if action == "search":
        if not query:
            raise InvalidParameterError("query", "검색 키워드가 필요합니다")
        methods = agent.search_methods(query)
        return {
            "rt_cd": "0",
            "msg1": f"'{query}' 검색 결과: {len(methods)}개 메서드",
            "output": methods,
        }
    elif action == "list_all":
        methods = agent.get_all_methods(show_details=True)
        return {
            "rt_cd": "0",
            "msg1": f"전체 메서드: {len(methods)}개",
            "output": methods,
        }
    elif action == "usage":
        if not method_name:
            raise InvalidParameterError("method_name", "메서드 이름이 필요합니다")
        # show_method_usage는 print만 하므로, 직접 메서드 정보 조회
        methods = agent.get_all_methods(show_details=True)
        method_info = next((m for m in methods if m.get("name") == method_name), None)
        if method_info:
            return {
                "rt_cd": "0",
                "msg1": f"메서드 '{method_name}' 사용법 조회 성공",
                "output": method_info,
            }
        else:
            return {
                "rt_cd": "1",
                "msg1": f"메서드 '{method_name}'를 찾을 수 없습니다",
                "output": None,
            }
