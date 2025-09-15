"""
리팩토링된 Stock API 클래스

데코레이터를 활용하여 보일러플레이트 코드를 제거하고
메서드명을 정규화한 버전
"""

from typing import Optional, Dict, Any
from ..core.base_api import BaseAPI
from ..core.decorators import api_endpoint, deprecated, cache_result, with_retry
from ..core.client import API_ENDPOINTS


class StockAPIRefactored(BaseAPI):
    """주식 관련 API (리팩토링 버전)"""

    # ========== 가격 관련 API ==========

    @api_endpoint('INQUIRE_PRICE', 'FHKST01010100')
    def get_price_current(self, code: str) -> Dict[str, Any]:
        """현재가 조회"""
        return {"FID_INPUT_ISCD": code}

    @api_endpoint('INQUIRE_DAILY_ITEMCHARTPRICE', 'FHKST01010400')
    def get_price_daily(self, code: str, period: str = "D", org_adj_prc: str = "1") -> Dict[str, Any]:
        """일별 시세 조회"""
        return {
            "fid_input_iscd": code,
            "fid_period_div_code": period,
            "fid_org_adj_prc": org_adj_prc
        }

    @api_endpoint('INQUIRE_TIME_ITEMCONCLUSION', 'FHKST01010300')
    def get_price_minute(self, code: str, hour: str = "153000") -> Dict[str, Any]:
        """분봉 데이터 조회"""
        return {
            "FID_INPUT_ISCD": code,
            "FID_INPUT_HOUR_1": hour
        }

    @api_endpoint('INQUIRE_TIME_DAILYCHARTPRICE', 'FHKST03010230')
    def get_price_daily_minute(self, code: str, date: str, hour: str = "153000") -> Dict[str, Any]:
        """특정일 분봉 데이터 조회"""
        return {
            "fid_input_iscd": code,
            "fid_input_date_1": date,
            "fid_input_hour_1": hour,
            "fid_pw_data_inq_yn": "Y"
        }

    # ========== 호가/거래량 관련 API ==========

    @api_endpoint('INQUIRE_ASKING_PRICE_EXP_CCN', 'FHKST01010200')
    def get_book_order(self, code: str) -> Dict[str, Any]:
        """호가 정보 조회"""
        return {"fid_input_iscd": code}

    @api_endpoint('VOLUME_POWER', 'FHPST01680000')
    def get_book_volume_power(self, volume: int = 0) -> Dict[str, Any]:
        """체결강도 조회"""
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

    # ========== 시장 정보 API ==========

    @api_endpoint('FLUCTUATION', 'FHPST01700000')
    def get_market_fluctuation(self) -> Dict[str, Any]:
        """등락률 순위 조회"""
        return {
            "fid_cond_scr_div_code": "20170",
            "fid_input_iscd": "0000",
            "fid_rank_sort_cls_code": "0",
            "fid_input_cnt_1": "0",
            "fid_prc_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "3000000",
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
            "fid_div_cls_code": "0",
            "fid_rsfl_rate1": "",
            "fid_rsfl_rate2": ""
        }

    @api_endpoint('VOLUME_RANK', 'FHPST01710000')
    def get_market_volume_rank(self, volume: int = 5000000) -> Dict[str, Any]:
        """거래량 순위 조회"""
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
            "FID_VOL_CNT": str(volume),
            "FID_INPUT_DATE_1": "",
        }

    @api_endpoint('MARKET_CAP', 'FHPST01740000')
    def get_market_cap_rank(self) -> Dict[str, Any]:
        """시가총액 상위 조회"""
        return {
            "FID_COND_SCR_DIV_CODE": "20174",
            "FID_INPUT_ISCD": "0002",
            "FID_DIV_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "111111111",
            "FID_TRGT_EXLS_CLS_CODE": "0000000",
            "FID_INPUT_CNT_1": "30",
            "FID_INPUT_DATE_1": "",
        }

    # ========== 투자자/회원사 API ==========

    @api_endpoint('INQUIRE_INVESTOR', 'FHKST01010900')
    @with_retry(max_retries=3)
    def get_investor_trend(self, ticker: str) -> Dict[str, Any]:
        """투자자별 매매동향 조회"""
        return {"FID_INPUT_ISCD": ticker}

    @api_endpoint('INQUIRE_MEMBER', 'FHKST01010600')
    @with_retry(max_retries=3)
    def get_member_trend(self, ticker: str) -> Dict[str, Any]:
        """회원사별 매매동향 조회"""
        return {"FID_INPUT_ISCD": ticker}

    # ========== 종목 정보 API ==========

    @api_endpoint('SEARCH_STOCK_INFO', 'CTPF1002R')
    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """종목 기본 정보 조회"""
        return {
            "PDNO": ticker,
            "PRDT_TYPE_CD": "300"
        }

    @api_endpoint('INQUIRE_DAILY_PRICE', 'FHKST03010100')
    def get_stock_financial(self, code: str) -> Dict[str, Any]:
        """종목 재무 정보 조회"""
        return {"FID_INPUT_ISCD": code}

    # ========== 프로그램 매매 API ==========

    @api_endpoint('PROGRAM_TRADE_BY_STOCK_DAILY', 'FHPPG04650200')
    def get_program_trade_stock(self, code: str, date: str) -> Dict[str, Any]:
        """종목별 프로그램매매 추이"""
        return {
            "fid_input_iscd": code,
            "fid_input_date_1": date,
            "fid_input_date_2": date
        }

    @api_endpoint('COMP_PROGRAM_TRADE_DAILY', 'FHPPG04600000')
    def get_program_trade_market(self, market_code: str = "1", date: str = None) -> Dict[str, Any]:
        """프로그램매매 종합현황"""
        from datetime import datetime
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        return {
            "fid_input_date_1": date,
            "fid_input_date_2": date,
            "fid_rank_sort_cls_code": market_code
        }

    # ========== 하위 호환성을 위한 Alias ==========

    @deprecated(alternative="get_price_current")
    def get_stock_price(self, code: str) -> Optional[Dict]:
        """Deprecated: Use get_price_current() instead"""
        return self.get_price_current(code)

    @deprecated(alternative="get_price_daily")
    def get_daily_price(self, code: str, period: str = "D", org_adj_prc: str = "1") -> Optional[Dict]:
        """Deprecated: Use get_price_daily() instead"""
        return self.get_price_daily(code, period, org_adj_prc)

    @deprecated(alternative="get_book_order")
    def get_orderbook(self, code: str) -> Optional[Dict]:
        """Deprecated: Use get_book_order() instead"""
        return self.get_book_order(code)

    @deprecated(alternative="get_price_minute")
    def get_minute_price(self, code: str, hour: str = "153000") -> Optional[Dict]:
        """Deprecated: Use get_price_minute() instead"""
        return self.get_price_minute(code, hour)

    @deprecated(alternative="get_investor_trend")
    def get_stock_investor(self, ticker: str, **kwargs) -> Optional[Dict]:
        """Deprecated: Use get_investor_trend() instead"""
        return self.get_investor_trend(ticker)

    @deprecated(alternative="get_member_trend")
    def get_stock_member(self, ticker: str, **kwargs) -> Optional[Dict]:
        """Deprecated: Use get_member_trend() instead"""
        return self.get_member_trend(ticker)

    # 기존 get_market_rankings는 유지 (이름이 이미 적절함)
    def get_market_rankings(self, volume: int = 5000000) -> Optional[Dict[str, Any]]:
        """시장 순위 종합 조회 (거래량 기준)"""
        return self.get_market_volume_rank(volume)