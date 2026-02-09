"""Stock price and market data MCP tools"""

from datetime import datetime
from typing import Any, Dict, Optional

from ..errors import InvalidParameterError, validate_api_response
from ..server import get_agent, server


@server.tool()
async def get_stock_price(code: str) -> Dict[str, Any]:
    """주식 현재가 조회

    Args:
        code: 종목코드 6자리 (예: "005930" - 삼성전자)

    Returns:
        Dict: 현재가 정보
            - output.stck_prpr: 주식 현재가
            - output.prdy_vrss: 전일 대비
            - output.prdy_ctrt: 전일 대비율
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_stock_price(code)
    return validate_api_response(result, "주식 현재가 조회")


@server.tool()
async def get_daily_price(
    stock_code: str, start_date: str = "", end_date: str = ""
) -> Dict[str, Any]:
    """국내주식 기간별 시세 조회 (일봉 데이터)

    Args:
        stock_code: 종목코드 6자리
        start_date: 시작일자 (YYYYMMDD, 선택)
        end_date: 종료일자 (YYYYMMDD, 선택)

    Returns:
        Dict: 일봉 데이터 (최대 100건)
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.inquire_daily_itemchartprice(stock_code, start_date, end_date)
    return validate_api_response(result, "일봉 데이터 조회")


@server.tool()
async def inquire_daily_price(
    stock_code: str, period: str = "D", org_adj_prc: str = "1"
) -> Dict[str, Any]:
    """주식현재가 일자별 조회 (최근 30일/주/월)

    Args:
        stock_code: 종목코드 6자리
        period: 기간구분 (D=일봉, W=주봉, M=월봉)
        org_adj_prc: 수정주가 적용 (0=미반영, 1=반영)

    Returns:
        Dict: 최근 30건 시세 데이터
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.inquire_daily_price(stock_code, period, org_adj_prc)
    return validate_api_response(result, "일자별 시세 조회")


@server.tool()
async def get_intraday_price(stock_code: str) -> Dict[str, Any]:
    """주식 당일 분봉 데이터 조회 (전체)

    Args:
        stock_code: 종목코드 6자리

    Returns:
        Dict: 당일 전체 분봉 데이터
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_intraday_price(stock_code)
    return validate_api_response(result, "당일 분봉 조회")


@server.tool()
async def inquire_price(stock_code: str, market: str = "J") -> Dict[str, Any]:
    """주식 현재가 상세 조회

    Args:
        stock_code: 종목코드 6자리
        market: 시장구분 (J=주식, ETF, ETN)

    Returns:
        Dict: 현재가 상세 정보
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.inquire_price(stock_code, market)
    return validate_api_response(result, "현재가 상세 조회")


@server.tool()
async def inquire_price_2(stock_code: str, market: str = "J") -> Dict[str, Any]:
    """주식 현재가 상세 조회 2

    Args:
        stock_code: 종목코드 6자리
        market: 시장구분 (J=주식)

    Returns:
        Dict: 현재가 상세 정보 (추가 필드)
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.inquire_price_2(stock_code, market)
    return validate_api_response(result, "현재가 상세 조회 2")


@server.tool()
async def inquire_ccnl(stock_code: str, market: str = "J") -> Dict[str, Any]:
    """주식 체결 정보 조회

    Args:
        stock_code: 종목코드 6자리
        market: 시장구분 (J=주식)

    Returns:
        Dict: 체결 정보
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.inquire_ccnl(stock_code, market)
    return validate_api_response(result, "체결 정보 조회")


@server.tool()
async def get_stock_ccnl(stock_code: str, market: str = "J") -> Dict[str, Any]:
    """주식 체결 조회

    Args:
        stock_code: 종목코드 6자리
        market: 시장구분 (J=주식)

    Returns:
        Dict: 주식 체결 데이터
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_stock_ccnl(stock_code, market)
    return validate_api_response(result, "주식 체결 조회")


@server.tool()
async def inquire_time_itemconclusion(
    stock_code: str, hour: str = "155900"
) -> Dict[str, Any]:
    """주식 시간별 체결 조회

    Args:
        stock_code: 종목코드 6자리
        hour: 시간 (HHMMSS, 기본값: 155900)

    Returns:
        Dict: 시간별 체결 데이터
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.inquire_time_itemconclusion(stock_code, hour)
    return validate_api_response(result, "시간별 체결 조회")


@server.tool()
async def get_minute_price(code: str, time_code: str = "093000") -> Dict[str, Any]:
    """[DEPRECATED] 분봉 데이터 조회 - get_intraday_price 또는 get_daily_minute_price 사용 권장

    .. deprecated::
        이 도구는 deprecated 되었습니다.
        - 당일 전체 분봉: get_intraday_price(code)
        - 과거 특정일 분봉: get_daily_minute_price(code, date, hour)

    Args:
        code: 종목코드 6자리
        time_code: 시간코드 (HHMMSS) - 무시됨, 당일 전체 분봉으로 포워딩

    Returns:
        Dict: 당일 전체 분봉 데이터 (get_intraday_price로 포워딩)
    """
    import warnings

    warnings.warn(
        "get_minute_price()는 deprecated 되었습니다. "
        "당일 전체 분봉은 get_intraday_price(), "
        "과거 특정일 분봉은 get_daily_minute_price()를 사용하세요.",
        DeprecationWarning,
        stacklevel=2,
    )

    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    # deprecated: get_intraday_price로 포워딩
    result = agent.get_intraday_price(code)
    return validate_api_response(
        result, "당일 분봉 조회 (deprecated → get_intraday_price)"
    )


@server.tool()
async def get_daily_minute_price(code: str, date: str) -> Dict[str, Any]:
    """특정일 전체 분봉 데이터 조회 (내부 페이지네이션)

    Args:
        code: 종목코드 6자리
        date: 날짜 (YYYYMMDD)

    Returns:
        Dict: 하루 전체 분봉 데이터 (~390건)
            - output1: 종목 기본정보
            - output2: 분봉 리스트 (09:00~15:30)
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    if not date or len(date) != 8:
        raise InvalidParameterError("date", "날짜는 YYYYMMDD 형식이어야 합니다")

    agent = get_agent()
    result = agent.get_daily_minute_price(code, date)
    return validate_api_response(result, "특정일 전체 분봉 조회")


@server.tool()
async def inquire_minute_price(code: str, date: Optional[str] = None) -> Dict[str, Any]:
    """분봉시세조회 - 하루 전체 분봉 데이터 조회

    지정된 날짜의 전체 분봉 데이터를 조회합니다 (09:00~15:30).
    내부적으로 페이지네이션하여 하루 전체 데이터를 수집합니다.

    Args:
        code: 종목코드 6자리 (예: "005930")
        date: 날짜 (YYYYMMDD, 선택). 미입력 시 오늘 날짜 사용

    Returns:
        Dict: 하루 전체 분봉 데이터 (~390건)
            - output1: 종목 기본정보
            - output2: 분봉 리스트
                - output2[].stck_bsop_date: 영업일자
                - output2[].stck_cntg_hour: 체결시각
                - output2[].stck_prpr: 현재가
                - output2[].cntg_vol: 체결거래량
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    # date가 없으면 오늘 날짜 사용
    if not date:
        date = datetime.now().strftime("%Y%m%d")

    if len(date) != 8:
        raise InvalidParameterError("date", "날짜는 YYYYMMDD 형식이어야 합니다")

    agent = get_agent()
    result = agent.get_daily_minute_price(code, date)
    return validate_api_response(result, "분봉시세조회")


@server.tool()
async def get_orderbook_raw(code: str) -> Dict[str, Any]:
    """호가 조회

    Args:
        code: 종목코드 6자리

    Returns:
        Dict: 호가 정보 (매수/매도 호가 10단계)
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_orderbook_raw(code)
    return validate_api_response(result, "호가 조회")


@server.tool()
async def fetch_minute_data(
    code: str, date: str = "", cache_dir: str = "minute_data"
) -> Dict[str, Any]:
    """4일간 분봉 데이터 수집

    Args:
        code: 종목코드 6자리
        date: 기준 날짜 (YYYYMMDD, 선택)
        cache_dir: 캐시 디렉토리 경로

    Returns:
        Dict: 수집된 분봉 데이터 정보
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.fetch_minute_data(code, date, cache_dir)
    return {"success": True, "data": result}


@server.tool()
async def calculate_support_resistance(code: str, date: str = "") -> Dict[str, Any]:
    """지지/저항선 계산

    Args:
        code: 종목코드 6자리
        date: 기준 날짜 (YYYYMMDD, 선택)

    Returns:
        Dict: 지지선, 저항선, VWAP, 거래량 프로파일
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.calculate_support_resistance(code, date)
    return {"success": True, "data": result}


@server.tool()
async def get_index_daily_price(index_code: str = "0001") -> Dict[str, Any]:
    """지수 일봉 데이터 조회

    Args:
        index_code: 지수 코드 (0001=KOSPI, 1001=KOSDAQ)

    Returns:
        Dict: 지수 일봉 데이터
    """
    agent = get_agent()
    result = agent.get_index_daily_price(index_code)
    return validate_api_response(result, "지수 일봉 조회")


@server.tool()
async def inquire_index_price(index_code: str = "0001") -> Dict[str, Any]:
    """지수 현재가 조회

    Args:
        index_code: 지수 코드 (0001=KOSPI, 1001=KOSDAQ)

    Returns:
        Dict: 지수 현재가 정보
    """
    agent = get_agent()
    result = agent.inquire_index_price(index_code)
    return validate_api_response(result, "지수 현재가 조회")


@server.tool()
async def inquire_index_category_price(
    market: str = "U", category: str = "0001"
) -> Dict[str, Any]:
    """업종별 지수 조회

    Args:
        market: 시장구분 (U=업종)
        category: 업종코드

    Returns:
        Dict: 업종별 지수 정보
    """
    agent = get_agent()
    result = agent.inquire_index_category_price(market, category)
    return validate_api_response(result, "업종별 지수 조회")


@server.tool()
async def inquire_index_tickprice(index_code: str = "0001") -> Dict[str, Any]:
    """지수 틱 데이터 조회

    Args:
        index_code: 지수 코드 (0001=KOSPI, 1001=KOSDAQ)

    Returns:
        Dict: 지수 틱 데이터
    """
    agent = get_agent()
    result = agent.inquire_index_tickprice(index_code)
    return validate_api_response(result, "지수 틱 조회")


@server.tool()
async def inquire_index_timeprice(index_code: str = "0001") -> Dict[str, Any]:
    """지수 시간별 데이터 조회

    Args:
        index_code: 지수 코드 (0001=KOSPI, 1001=KOSDAQ)

    Returns:
        Dict: 지수 시간별 데이터
    """
    agent = get_agent()
    result = agent.inquire_index_timeprice(index_code)
    return validate_api_response(result, "지수 시간별 조회")


@server.tool()
async def get_index_minute_data(
    index_code: str = "0001", time_code: str = "093000"
) -> Dict[str, Any]:
    """지수 분봉 데이터 조회

    Args:
        index_code: 지수 코드 (0001=KOSPI, 1001=KOSDAQ)
        time_code: 시간코드 (HHMMSS)

    Returns:
        Dict: 지수 분봉 데이터
    """
    agent = get_agent()
    result = agent.get_index_minute_data(index_code, time_code)
    return validate_api_response(result, "지수 분봉 조회")


@server.tool()
async def inquire_elw_price(stock_code: str) -> Dict[str, Any]:
    """ELW 시세 조회

    Args:
        stock_code: ELW 종목코드 6자리

    Returns:
        Dict: ELW 시세 정보
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.inquire_elw_price(stock_code)
    return validate_api_response(result, "ELW 시세 조회")


@server.tool()
async def get_volume_power(volume: int = 0) -> Dict[str, Any]:
    """거래량 순위 조회

    Args:
        volume: 최소 거래량 (기본값: 0)

    Returns:
        Dict: 거래량 순위 종목 리스트
    """
    agent = get_agent()
    result = agent.get_volume_power(volume)
    return validate_api_response(result, "거래량 순위 조회")


@server.tool()
async def get_top_gainers(market: str = "ALL") -> Dict[str, Any]:
    """등락률 순위 조회

    Args:
        market: 시장 구분 (ALL, KOSPI, KOSDAQ, NXT)

    Returns:
        Dict: 등락률 상위 종목 리스트
    """
    agent = get_agent()
    result = agent.get_top_gainers(market)
    return validate_api_response(result, "등락률 순위 조회")


@server.tool()
async def get_market_fluctuation() -> Dict[str, Any]:
    """시장 등락 현황 조회

    Returns:
        Dict: 시장 전체 등락 현황
    """
    agent = get_agent()
    result = agent.get_market_fluctuation()
    return validate_api_response(result, "시장 등락 현황 조회")


@server.tool()
async def get_market_rankings(volume: int = 5000000) -> Dict[str, Any]:
    """시장 순위 조회

    Args:
        volume: 최소 거래량 (기본값: 5000000)

    Returns:
        Dict: 시장 순위 정보
    """
    agent = get_agent()
    result = agent.get_market_rankings(volume)
    return validate_api_response(result, "시장 순위 조회")


@server.tool()
async def get_fluctuation_rank(
    market: str = "0", sign: str = "0", cls_code: str = "0"
) -> Dict[str, Any]:
    """등락률 순위 상세 조회

    Args:
        market: 시장구분 (0=전체, 1=KOSPI, 2=KOSDAQ)
        sign: 등락구분 (0=전체, 1=상승, 2=보합, 3=하락)
        cls_code: 분류코드

    Returns:
        Dict: 등락률 순위 종목 리스트
    """
    agent = get_agent()
    result = agent.get_fluctuation_rank(market, sign, cls_code)
    return validate_api_response(result, "등락률 순위 상세 조회")


@server.tool()
async def get_volume_rank(
    market: str = "0", sign: str = "0", cls_code: str = "0"
) -> Dict[str, Any]:
    """거래량 순위 조회

    Args:
        market: 시장구분 (0=전체, 1=KOSPI, 2=KOSDAQ)
        sign: 등락구분 (0=전체, 1=상승, 2=보합, 3=하락)
        cls_code: 분류코드

    Returns:
        Dict: 거래량 순위 종목 리스트
    """
    agent = get_agent()
    result = agent.get_volume_rank(market, sign, cls_code)
    return validate_api_response(result, "거래량 순위 조회")


@server.tool()
async def get_volume_power_rank(
    market: str = "0", sign: str = "0", cls_code: str = "0"
) -> Dict[str, Any]:
    """체결강도 순위 조회

    Args:
        market: 시장구분 (0=전체, 1=KOSPI, 2=KOSDAQ)
        sign: 등락구분 (0=전체, 1=상승, 2=보합, 3=하락)
        cls_code: 분류코드

    Returns:
        Dict: 체결강도 순위 종목 리스트
    """
    agent = get_agent()
    result = agent.get_volume_power_rank(market, sign, cls_code)
    return validate_api_response(result, "체결강도 순위 조회")


@server.tool()
async def inquire_daily_overtimeprice(
    stock_code: str, period: str = "D"
) -> Dict[str, Any]:
    """시간외 일별 시세 조회

    Args:
        stock_code: 종목코드 6자리
        period: 기간구분 (D=일봉)

    Returns:
        Dict: 시간외 일별 시세 데이터
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.inquire_daily_overtimeprice(stock_code, period)
    return validate_api_response(result, "시간외 일별 시세 조회")


@server.tool()
async def inquire_overtime_price(stock_code: str) -> Dict[str, Any]:
    """시간외 현재가 조회

    Args:
        stock_code: 종목코드 6자리

    Returns:
        Dict: 시간외 현재가 정보
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.inquire_overtime_price(stock_code)
    return validate_api_response(result, "시간외 현재가 조회")


@server.tool()
async def inquire_overtime_asking_price(stock_code: str) -> Dict[str, Any]:
    """시간외 호가 조회

    Args:
        stock_code: 종목코드 6자리

    Returns:
        Dict: 시간외 호가 정보
    """
    if not stock_code or len(stock_code) != 6:
        raise InvalidParameterError("stock_code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.inquire_overtime_asking_price(stock_code)
    return validate_api_response(result, "시간외 호가 조회")


@server.tool()
async def get_member(code: str) -> Dict[str, Any]:
    """회원사 정보 조회

    Args:
        code: 종목코드 6자리

    Returns:
        Dict: 회원사 정보
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_member(code)
    return validate_api_response(result, "회원사 정보 조회")


@server.tool()
async def init_minute_db(code: str, db_path: str = "") -> Dict[str, Any]:
    """분봉 데이터베이스 초기화

    Args:
        code: 종목코드 6자리
        db_path: 데이터베이스 경로 (선택)

    Returns:
        Dict: 초기화 결과
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    agent.init_minute_db(code, db_path)
    return {"success": True, "message": "분봉 DB 초기화 완료"}


@server.tool()
async def migrate_minute_csv_to_db(
    code: str, csv_dir: str, db_path: str = ""
) -> Dict[str, Any]:
    """CSV 데이터를 데이터베이스로 마이그레이션

    Args:
        code: 종목코드 6자리
        csv_dir: CSV 파일 디렉토리
        db_path: 데이터베이스 경로 (선택)

    Returns:
        Dict: 마이그레이션 결과
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.migrate_minute_csv_to_db(code, csv_dir, db_path)
    return {"success": True, "migrated_count": result}


@server.tool()
async def get_kospi200_futures_code() -> Dict[str, Any]:
    """KOSPI200 선물 종목코드 조회

    Returns:
        Dict: 현재 활성 선물 종목코드
    """
    from pykis.stock import get_kospi200_futures_code

    code = get_kospi200_futures_code()
    return {"success": True, "futures_code": code}


@server.tool()
async def get_future_option_price() -> Dict[str, Any]:
    """KOSPI200 선물옵션 가격 조회

    Returns:
        Dict: 선물옵션 가격 정보
    """
    agent = get_agent()
    result = agent.get_future_option_price()
    return validate_api_response(result, "선물옵션 가격 조회")
