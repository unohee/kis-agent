"""
Stock Market API - 시장 정보 및 순위 조회 전용 모듈

시장 전체 정보와 종목 순위 분석 기능을 담당
- 시장 변동성 정보
- 거래량/체결강도 순위
- 종목 기본 정보
"""

from typing import Optional, Dict, Any
import pandas as pd
from ..core.client import KISClient, API_ENDPOINTS
from ..core.base_api import BaseAPI


class StockMarketAPI(BaseAPI):
    """주식 시장 정보 조회 전용 API 클래스"""

    def get_market_fluctuation(self) -> Optional[Dict[str, Any]]:
        """시장 변동성 정보 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_ASKING_PRICE_EXP_CCN'],
            tr_id="FHKST01010600",
            params={"FID_COND_MRKT_DIV_CODE": "J"}
        )

    def get_market_rankings(self, volume: int = 5000000) -> Optional[Dict[str, Any]]:
        """거래량 기준 종목 순위 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['FHKST01010900'],
            tr_id="FHKST01010900",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": "20171",
                "FID_INPUT_ISCD": "0000",
                "FID_RANK_SORT_CLS_CODE": "0",
                "FID_INPUT_CNT_1": "50",
                "FID_PRC_CLS_CODE": "1",
                "FID_INPUT_PRICE_1": "",
                "FID_INPUT_PRICE_2": "",
                "FID_VOL_CNT": str(volume)
            }
        )

    def get_volume_power(self, volume: int = 0) -> Optional[pd.DataFrame]:
        """체결강도 순위 조회"""
        return self._make_request_with_conversion(
            endpoint=API_ENDPOINTS['HTS_CURRENT_PRICE'],
            tr_id="FHKST01010900",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": "20171",
                "FID_INPUT_ISCD": "0000",
                "FID_RANK_SORT_CLS_CODE": "0",
                "FID_INPUT_CNT_1": "50",
                "FID_PRC_CLS_CODE": "1",
                "FID_INPUT_PRICE_1": "",
                "FID_INPUT_PRICE_2": "",
                "FID_VOL_CNT": str(volume)
            },
            field_type='volume_power'
        )

    def get_stock_info(self, ticker: str) -> Optional[pd.DataFrame]:
        """종목 기본 정보 조회"""
        return self._make_request_with_conversion(
            endpoint=API_ENDPOINTS['INQUIRE_PRICE'],
            tr_id="FHKST01010100",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ticker},
            field_type='stock_price'
        )