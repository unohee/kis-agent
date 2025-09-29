"""
Stock Price API - 주식 시세 조회 전용 모듈

단일 책임 원칙(SRP)에 따라 StockAPI에서 시세 관련 기능만 분리
- 현재가 조회
- 일별/분봉 시세
- 호가 정보
"""

from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS, KISClient


class StockPriceAPI(BaseAPI):
    """주식 시세 조회 전용 API 클래스"""

    def get_stock_price(self, code: str) -> Optional[Dict]:
        """주식 현재가 조회"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_PRICE"],
            tr_id="FHKST01010100",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
        )

    def get_daily_price(
        self, code: str, period: str = "D", org_adj_prc: str = "1"
    ) -> Optional[Dict]:
        """
        일별 시세 조회

        Args:
            code: 종목코드 (6자리)
            period: 기간구분 (D: 일, W: 주, M: 월, Y: 년)
            org_adj_prc: 수정주가구분 (0: 수정주가 미사용, 1: 수정주가 사용)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_DAILY_ITEMCHARTPRICE"],
            tr_id="FHKST01010400",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_period_div_code": period,
                "fid_org_adj_prc": org_adj_prc,
            },
        )

    def get_orderbook(self, code: str) -> Optional[Dict]:
        """주식 호가 정보 조회"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_ASKING_PRICE_EXP_CCN"],
            tr_id="FHKST01010200",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
        )

    def get_orderbook_raw(self, code: str) -> Optional[Dict]:
        """호가 정보 원시 데이터 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_ASKING_PRICE_EXP_CCN"],
            tr_id="FHKST01010200",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
        )

    def get_minute_price(self, code: str, hour: str = "153000") -> Optional[Dict]:
        """분봉 시세 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_TIME_ITEMCHARTPRICE"],
            tr_id="FHKST01010300",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": hour,
            },
        )

    def get_daily_minute_price(
        self, code: str, date: str, hour: str = "153000"
    ) -> Optional[Dict]:
        """특정일 분봉 시세 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_TIME_ITEMCHARTPRICE"],
            tr_id="FHKST01010300",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": date,
                "FID_INPUT_HOUR_1": hour,
            },
        )
