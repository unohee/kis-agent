"""Stock price and market data MCP tools"""
from typing import Any, Dict
from mcp.server import Server

from ..server import get_agent, server
from ..errors import validate_api_response, InvalidParameterError


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
    code: str, start_date: str = "", end_date: str = ""
) -> Dict[str, Any]:
    """일봉 데이터 조회

    Args:
        code: 종목코드 6자리
        start_date: 시작일자 (YYYYMMDD, 선택)
        end_date: 종료일자 (YYYYMMDD, 선택)

    Returns:
        Dict: 일봉 데이터 (최대 100건)
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_daily_price(code, start_date, end_date)
    return validate_api_response(result, "일봉 데이터 조회")


@server.tool()
async def get_minute_price(code: str, time_code: str = "093000") -> Dict[str, Any]:
    """분봉 데이터 조회

    Args:
        code: 종목코드 6자리
        time_code: 시간코드 (HHMMSS, 기본값: 093000)

    Returns:
        Dict: 분봉 데이터
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

    agent = get_agent()
    result = agent.get_minute_price(code, time_code)
    return validate_api_response(result, "분봉 데이터 조회")


@server.tool()
async def get_daily_minute_price(
    code: str, date: str, hour: str = "153000"
) -> Dict[str, Any]:
    """특정일 분봉 데이터 조회

    Args:
        code: 종목코드 6자리
        date: 날짜 (YYYYMMDD)
        hour: 시각 (HHMMSS, 기본값: 153000)

    Returns:
        Dict: 분봉 데이터 (최대 120건)
    """
    if not code or len(code) != 6:
        raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")
    if not date or len(date) != 8:
        raise InvalidParameterError("date", "날짜는 YYYYMMDD 형식이어야 합니다")

    agent = get_agent()
    result = agent.get_daily_minute_price(code, date, hour)
    return validate_api_response(result, "특정일 분봉 데이터 조회")


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
async def calculate_support_resistance(
    code: str, date: str = ""
) -> Dict[str, Any]:
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
    from pykis.stock.api import get_kospi200_futures_code

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
