"""
강화된 Stock API - 데코레이터 기반 리팩터링

기존 StockAPI를 데코레이터 패턴으로 리팩터링하고
fail-fast 예외 처리를 적용한 버전
"""

from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta
from ..core.base_api import BaseAPI
from ..core.decorators import api_endpoint, deprecated, with_retry
from ..core.client import API_ENDPOINTS

logger = logging.getLogger(__name__)


class StockAPIEnhanced(BaseAPI):
    """주식 관련 API - 데코레이터 기반 강화 버전"""

    # ========== 가격 조회 API ==========

    @api_endpoint('INQUIRE_PRICE', 'FHKST01010100')
    def get_price_current(self, code: str) -> Dict[str, Any]:
        """
        현재가 조회

        Args:
            code: 종목코드 (6자리)

        Returns:
            현재가 정보를 담은 딕셔너리

        Raises:
            ValueError: 잘못된 종목코드
            Exception: API 호출 실패 (fail-fast)
        """
        if not code or len(code) != 6:
            raise ValueError(f"잘못된 종목코드: {code}")

        return {"FID_INPUT_ISCD": code}

    @api_endpoint('INQUIRE_DAILY_ITEMCHARTPRICE', 'FHKST01010400')
    def get_price_daily(self, code: str, period: str = "D", org_adj_prc: str = "1") -> Dict[str, Any]:
        """
        일별 시세 조회

        Args:
            code: 종목코드 (6자리)
            period: 기간구분 (D: 일, W: 주, M: 월, Y: 년)
            org_adj_prc: 수정주가구분 (0: 미사용, 1: 사용)

        Raises:
            ValueError: 잘못된 파라미터
            Exception: API 호출 실패 (fail-fast)
        """
        if not code or len(code) != 6:
            raise ValueError(f"잘못된 종목코드: {code}")
        if period not in ["D", "W", "M", "Y"]:
            raise ValueError(f"잘못된 기간구분: {period}")

        return {
            "fid_input_iscd": code,
            "fid_period_div_code": period,
            "fid_org_adj_prc": org_adj_prc
        }

    @api_endpoint('INQUIRE_TIME_ITEMCONCLUSION', 'FHKST01010300')
    def get_price_minute(self, code: str, hour: str = "153000") -> Dict[str, Any]:
        """
        분봉 데이터 조회

        Args:
            code: 종목코드 (6자리)
            hour: 조회시간 (HHMMSS 형식)

        Raises:
            ValueError: 잘못된 파라미터
            Exception: API 호출 실패 (fail-fast)
        """
        if not code or len(code) != 6:
            raise ValueError(f"잘못된 종목코드: {code}")
        if not hour or len(hour) != 6:
            raise ValueError(f"잘못된 시간 형식: {hour}")

        return {
            "FID_INPUT_ISCD": code,
            "FID_INPUT_HOUR_1": hour
        }

    @api_endpoint('INQUIRE_TIME_DAILYCHARTPRICE', 'FHKST03010230')
    def get_price_intraday(self, code: str, date: str, hour: str = "153000") -> Dict[str, Any]:
        """
        일중 분봉 조회

        Args:
            code: 종목코드 (6자리)
            date: 조회일자 (YYYYMMDD)
            hour: 조회시간 (HHMMSS)

        Raises:
            ValueError: 잘못된 파라미터
            Exception: API 호출 실패 (fail-fast)
        """
        if not code or len(code) != 6:
            raise ValueError(f"잘못된 종목코드: {code}")
        if not date or len(date) != 8:
            raise ValueError(f"잘못된 날짜 형식: {date}")

        return {
            "fid_input_iscd": code,
            "fid_input_date_1": date,
            "fid_input_hour_1": hour,
            "fid_pw_data_inq_yn": "Y"
        }

    # ========== 호가/거래량 조회 API ==========

    @api_endpoint('INQUIRE_ASKING_PRICE_EXP_CCN', 'FHKST01010200')
    def get_book_order(self, code: str) -> Dict[str, Any]:
        """
        호가 정보 조회

        Args:
            code: 종목코드 (6자리)

        Raises:
            ValueError: 잘못된 종목코드
            Exception: API 호출 실패 (fail-fast)
        """
        if not code or len(code) != 6:
            raise ValueError(f"잘못된 종목코드: {code}")

        return {"fid_input_iscd": code}

    @api_endpoint('VOLUME_POWER', 'FHPST01680000')
    def get_book_volume_power(self, volume: int = 0) -> Dict[str, Any]:
        """
        체결강도 조회

        Args:
            volume: 최소 거래량 기준

        Returns:
            체결강도 순위 정보
        """
        params = {
            "FID_COND_SCR_DIV_CODE": "20176",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "1",
            "FID_TRGT_EXLS_CLS_CODE": "1",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
            "FID_INPUT_DATE_1": "",
        }

        if volume > 0:
            params["FID_VOL_CNT"] = str(volume)

        return params

    # ========== 투자자/회원사 조회 API ==========

    @api_endpoint('INQUIRE_INVESTOR', 'FHKST01010900')
    @with_retry(max_retries=3, delay=0.5)
    def get_investor_trend(self, ticker: str) -> Dict[str, Any]:
        """
        투자자별 매매동향 조회

        Args:
            ticker: 종목코드 (6자리)

        Raises:
            ValueError: 잘못된 종목코드
            Exception: API 호출 실패 (fail-fast, 3회 재시도)
        """
        if not ticker or len(ticker) != 6:
            raise ValueError(f"잘못된 종목코드: {ticker}")

        return {"FID_INPUT_ISCD": ticker}

    @api_endpoint('INQUIRE_MEMBER', 'FHKST01010600')
    @with_retry(max_retries=3, delay=0.5)
    def get_member_trend(self, ticker: str) -> Dict[str, Any]:
        """
        회원사별 매매동향 조회

        Args:
            ticker: 종목코드 (6자리)

        Raises:
            ValueError: 잘못된 종목코드
            Exception: API 호출 실패 (fail-fast, 3회 재시도)
        """
        if not ticker or len(ticker) != 6:
            raise ValueError(f"잘못된 종목코드: {ticker}")

        return {"FID_INPUT_ISCD": ticker}

    # ========== 시장 정보 조회 API ==========

    @api_endpoint('FLUCTUATION', 'FHPST01700000')
    def get_market_fluctuation(self, min_volume: int = 3000000) -> Dict[str, Any]:
        """
        등락률 순위 조회

        Args:
            min_volume: 최소 거래량 기준 (기본: 3백만)

        Returns:
            등락률 순위 정보
        """
        return {
            "fid_cond_scr_div_code": "20170",
            "fid_input_iscd": "0000",
            "fid_rank_sort_cls_code": "0",
            "fid_input_cnt_1": "0",
            "fid_prc_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": str(min_volume),
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
            "fid_div_cls_code": "0",
            "fid_rsfl_rate1": "",
            "fid_rsfl_rate2": ""
        }

    @api_endpoint('VOLUME_RANK', 'FHPST01710000')
    def get_market_volume_rank(self, min_volume: int = 5000000) -> Dict[str, Any]:
        """
        거래량 순위 조회

        Args:
            min_volume: 최소 거래량 기준 (기본: 5백만)

        Returns:
            거래량 순위 정보
        """
        return {
            "FID_COND_SCR_DIV_CODE": "20171",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "111111111",
            "FID_TRGT_EXLS_CLS_CODE": "000000",
            "FID_INPUT_CNT_1": "0",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": str(min_volume),
            "FID_INPUT_DATE_1": "",
        }

    @api_endpoint('MARKET_CAP', 'FHPST01740000')
    def get_market_cap_rank(self, count: int = 30) -> Dict[str, Any]:
        """
        시가총액 순위 조회

        Args:
            count: 조회할 종목 수 (기본: 30)

        Returns:
            시가총액 순위 정보
        """
        return {
            "FID_COND_SCR_DIV_CODE": "20174",
            "FID_INPUT_ISCD": "0002",
            "FID_DIV_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "111111111",
            "FID_TRGT_EXLS_CLS_CODE": "0000000",
            "FID_INPUT_CNT_1": str(count),
            "FID_INPUT_DATE_1": "",
        }

    # ========== 종목 정보 조회 API ==========

    @api_endpoint('SEARCH_STOCK_INFO', 'CTPF1002R')
    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """
        종목 기본 정보 조회

        Args:
            ticker: 종목코드 (6자리)

        Raises:
            ValueError: 잘못된 종목코드
            Exception: API 호출 실패 (fail-fast)
        """
        if not ticker or len(ticker) != 6:
            raise ValueError(f"잘못된 종목코드: {ticker}")

        return {
            "PDNO": ticker,
            "PRDT_TYPE_CD": "300"
        }

    # ========== 프로그램 매매 조회 API ==========

    @api_endpoint('PROGRAM_TRADE_BY_STOCK_DAILY', 'FHPPG04650200')
    def get_program_trade_stock(self, code: str, date: str = None) -> Dict[str, Any]:
        """
        종목별 프로그램매매 추이

        Args:
            code: 종목코드 (6자리)
            date: 조회일자 (YYYYMMDD, 미지정시 오늘)

        Raises:
            ValueError: 잘못된 파라미터
            Exception: API 호출 실패 (fail-fast)
        """
        if not code or len(code) != 6:
            raise ValueError(f"잘못된 종목코드: {code}")

        if not date:
            date = datetime.now().strftime("%Y%m%d")
        elif len(date) != 8:
            raise ValueError(f"잘못된 날짜 형식: {date}")

        return {
            "fid_input_iscd": code,
            "fid_input_date_1": date,
            "fid_input_date_2": date
        }

    @api_endpoint('COMP_PROGRAM_TRADE_DAILY', 'FHPPG04600000')
    def get_program_trade_market(self, market_code: str = "1", date: str = None) -> Dict[str, Any]:
        """
        프로그램매매 종합현황

        Args:
            market_code: 시장구분 (1: KOSPI, 2: KOSDAQ)
            date: 조회일자 (YYYYMMDD, 미지정시 오늘)

        Returns:
            프로그램매매 종합 정보
        """
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        elif len(date) != 8:
            raise ValueError(f"잘못된 날짜 형식: {date}")

        return {
            "fid_input_date_1": date,
            "fid_input_date_2": date,
            "fid_rank_sort_cls_code": market_code
        }

    # ========== 시간외 거래 API ==========

    @api_endpoint('OVERTIME_CONCLUSION', 'FHKST01010300')
    def get_overtime_price(self, code: str) -> Dict[str, Any]:
        """
        시간외 단일가 조회

        Args:
            code: 종목코드 (6자리)

        Raises:
            ValueError: 잘못된 종목코드
            Exception: API 호출 실패 (fail-fast)
        """
        if not code or len(code) != 6:
            raise ValueError(f"잘못된 종목코드: {code}")

        return {
            "FID_INPUT_ISCD": code,
            "FID_INPUT_HOUR_1": "180000"  # 시간외 단일가는 18시
        }

    # ========== 하위 호환성을 위한 Alias 메서드 ==========

    @deprecated(alternative="get_price_current")
    def get_stock_price(self, code: str) -> Optional[Dict]:
        """Deprecated: Use get_price_current() instead"""
        return self.get_price_current(code)

    @deprecated(alternative="get_price_daily")
    def get_daily_price(self, code: str, period: str = "D", org_adj_prc: str = "1") -> Optional[Dict]:
        """Deprecated: Use get_price_daily() instead"""
        return self.get_price_daily(code, period, org_adj_prc)

    @deprecated(alternative="get_price_minute")
    def get_minute_price(self, code: str, hour: str = "153000") -> Optional[Dict]:
        """Deprecated: Use get_price_minute() instead"""
        return self.get_price_minute(code, hour)

    @deprecated(alternative="get_book_order")
    def get_orderbook(self, code: str) -> Optional[Dict]:
        """Deprecated: Use get_book_order() instead"""
        return self.get_book_order(code)

    @deprecated(alternative="get_investor_trend")
    def get_stock_investor(self, ticker: str) -> Optional[Dict]:
        """Deprecated: Use get_investor_trend() instead"""
        return self.get_investor_trend(ticker)

    @deprecated(alternative="get_member_trend")
    def get_stock_member(self, ticker: str) -> Optional[Dict]:
        """Deprecated: Use get_member_trend() instead"""
        return self.get_member_trend(ticker)

    # ========== 유틸리티 메서드 ==========

    def get_kospi200_futures_code(self, today: Optional[datetime] = None) -> str:
        """
        현재 거래되는 KOSPI200 선물 종목코드 반환

        Args:
            today: 기준 날짜 (미지정시 오늘)

        Returns:
            KOSPI200 선물 종목코드 (예: "101W09")
        """
        if today is None:
            today = datetime.now()

        def get_second_thursday(year: int, month: int) -> datetime:
            """해당 월의 두 번째 목요일 계산"""
            first_day = datetime(year, month, 1)
            days_until_first_thursday = (3 - first_day.weekday()) % 7
            first_thursday = first_day + timedelta(days=days_until_first_thursday)
            return first_thursday + timedelta(days=7)

        expiry_months = [3, 6, 9, 12]
        current_year = today.year
        current_month = today.month

        # 현재 월이 만기월인지 확인
        if current_month in expiry_months:
            expiry_date = get_second_thursday(current_year, current_month)
            expiry_datetime = expiry_date.replace(hour=15, minute=30, second=0)

            if today <= expiry_datetime:
                return f"101W{current_month:02d}"

        # 다음 만기월 찾기
        for month in expiry_months:
            if month > current_month:
                return f"101W{month:02d}"

        # 12월 이후는 다음해 3월물
        return f"101W03"