"""
Stock API Facade - 주식 관련 API 통합 인터페이스

Facade Pattern을 적용하여 복잡한 하위 시스템을 단순화
- StockPriceAPI: 시세 정보
- StockMarketAPI: 시장 정보  
- StockInvestorAPI: 투자자 정보
- 기존 StockAPI와 동일한 인터페이스 유지 (하위 호환성)
"""

from typing import Any, Dict, List, Optional, Tuple

from ..core.base_api import BaseAPI
from ..core.client import KISClient
from .investor_api import StockInvestorAPI
from .market_api import StockMarketAPI
from .price_api import StockPriceAPI


class StockAPI(BaseAPI):
    """
    주식 관련 API 통합 Facade 클래스

    하위 시스템들을 통합하여 기존 인터페이스와 호환성을 유지하면서
    내부적으로는 책임 분산된 구조를 제공합니다.

    Attributes:
        price_api (StockPriceAPI): 시세 조회 전담 API
        market_api (StockMarketAPI): 시장 정보 전담 API
        investor_api (StockInvestorAPI): 투자자 정보 전담 API
    """

    def __init__(
        self, client: KISClient, account_info=None, enable_cache=True, cache_config=None
    ):
        """
        StockAPI Facade 초기화

        Args:
            client (KISClient): API 통신 클라이언트
            account_info (dict, optional): 계좌 정보
        """
        super().__init__(client, account_info, enable_cache, cache_config)

        # 하위 시스템 초기화
        self.price_api = StockPriceAPI(client, account_info)
        self.market_api = StockMarketAPI(client, account_info)
        self.investor_api = StockInvestorAPI(client, account_info)

    # ===== 시세 관련 메서드 (StockPriceAPI 위임) =====

    def get_stock_price(self, code: str) -> Optional[Dict]:
        """주식 현재가 조회"""
        return self.price_api.get_stock_price(code)

    def get_daily_price(
        self, code: str, period: str = "D", org_adj_prc: str = "1"
    ) -> Optional[Dict]:
        """일별 시세 조회"""
        return self.price_api.get_daily_price(code, period, org_adj_prc)

    def get_orderbook(self, code: str) -> Optional[Dict]:
        """주식 호가 정보 조회"""
        return self.price_api.get_orderbook(code)

    def get_orderbook_raw(self, code: str) -> Optional[Dict]:
        """호가 정보 원시 데이터 조회"""
        return self.price_api.get_orderbook_raw(code)

    def get_minute_price(self, code: str, hour: str = "153000") -> Optional[Dict]:
        """분봉 시세 조회"""
        return self.price_api.get_minute_price(code, hour)

    def get_daily_minute_price(
        self, code: str, date: str, hour: str = "153000"
    ) -> Optional[Dict]:
        """특정일 분봉 시세 조회"""
        return self.price_api.get_daily_minute_price(code, date, hour)

    # ===== 시장 정보 관련 메서드 (StockMarketAPI 위임) =====

    def get_market_fluctuation(self) -> Optional[Dict[str, Any]]:
        """시장 변동성 정보 조회"""
        return self.market_api.get_market_fluctuation()

    def get_market_rankings(self, volume: int = 5000000) -> Optional[Dict[str, Any]]:
        """거래량 기준 종목 순위 조회"""
        return self.market_api.get_market_rankings(volume)

    def get_volume_power(self, volume: int = 0) -> Optional[Dict]:
        """체결강도 순위 조회"""
        return self.market_api.get_volume_power(volume)

    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """종목 기본 정보 조회"""
        return self.market_api.get_stock_info(ticker)

    # ===== 투자자 정보 관련 메서드 (StockInvestorAPI 위임) =====

    def get_stock_investor(
        self, ticker: str = "", retries: int = 10, force_refresh: bool = False
    ) -> Optional[Dict]:
        """투자자별 매매동향 조회 (원시 dict 반환)

        Note:
            - [변경 이유] StockInvestorAPI.get_stock_investor가 dict를 반환하므로 Facade도 일관성을 위해 dict로 타입을 맞춤
        """
        return self.investor_api.get_stock_investor(ticker, retries, force_refresh)

    def get_stock_member(self, ticker: str, retries: int = 10) -> Optional[Dict]:
        """거래원별 매매 정보 조회"""
        return self.investor_api.get_stock_member(ticker, retries)

    def get_member_transaction(
        self, code: str, mem_code: str
    ) -> Optional[Dict[str, Any]]:
        """특정 거래원의 매매 내역 조회"""
        return self.investor_api.get_member_transaction(code, mem_code)

    def get_frgnmem_pchs_trend(self, code: str) -> Optional[Dict[str, Any]]:
        """외국인 매수 추이 조회"""
        return self.investor_api.get_frgnmem_pchs_trend(code)

    def get_foreign_broker_net_buy(
        self, code: str, foreign_brokers=None, date: str = None
    ) -> Optional[tuple]:
        """외국계 증권사 순매수 집계"""
        return self.investor_api.get_foreign_broker_net_buy(code, foreign_brokers, date)

    def get_index_minute_data(
        self,
        fid_input_iscd: str = "0001",
        fid_input_hour_1: str = "120",
        fid_cond_mrkt_div_code: str = "U",
        fid_pw_data_incu_yn: str = "Y",
        fid_etc_cls_code: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        업종 분봉 조회

        Args:
            fid_input_iscd (str): 종목코드 (0001: 종합, 1001: 코스닥종합)
            fid_input_hour_1 (str): 입력 시간(초) - 조회 시간 범위
            fid_cond_mrkt_div_code (str): 시장 분류 코드 (U: 업종)
            fid_pw_data_incu_yn (str): 과거 데이터 포함 여부 (Y/N)
            fid_etc_cls_code (str): 기타 구분 코드

        Returns:
            Dict containing:
                - output1: 업종 현재가 정보
                - output2: 분봉 데이터 리스트
        """
        return self.price_api.get_index_minute_data(
            fid_input_iscd,
            fid_input_hour_1,
            fid_cond_mrkt_div_code,
            fid_pw_data_incu_yn,
            fid_etc_cls_code,
        )

    def get_index_timeprice(
        self,
        fid_input_iscd: str = "1029",
        fid_input_hour_1: str = "600",
        fid_cond_mrkt_div_code: str = "U",
    ) -> Optional[Dict[str, Any]]:
        """
        국내업종 시간별 지수 조회 (기본값: KOSPI200)

        Args:
            fid_input_iscd (str): 종목코드 (기본값 "1029": KOSPI200, "1001": KOSPI, "2001": KOSDAQ)
            fid_input_hour_1 (str): 입력 시간(초) - 조회 시간 범위 (기본값 "600": 10분봉)
            fid_cond_mrkt_div_code (str): 시장 분류 코드 (기본값 "U": 업종)

        Returns:
            Dict containing:
                - output1: 업종 현재가 정보
                - output2: 시간별 지수 데이터 리스트
        """
        return self.price_api.get_index_timeprice(
            fid_input_iscd,
            fid_input_hour_1,
            fid_cond_mrkt_div_code,
        )


# 하위 호환성을 위한 별칭
StockAPIFacade = StockAPI
