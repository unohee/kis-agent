"""
Overseas Futures API 패키지 - 해외선물옵션 관련 API 모음

Facade 패턴을 적용하여 단일 책임 원칙(SRP) 준수:
- OverseasFutures: Facade 패턴으로 통합 인터페이스 제공
- OverseasFuturesPriceAPI: 시세 조회 전담 (8개 메서드)
- OverseasFuturesAccountAPI: 계좌/잔고 조회 전담 (9개 메서드)
- OverseasFuturesOrderAPI: 주문 전담 (2개 메서드 + 편의 메서드)

지원 거래소:
- CME: Chicago Mercantile Exchange (E-mini S&P500, 나스닥100)
- EUREX: European Exchange (EURO STOXX 50)
- COMEX: Commodity Exchange (금, 은 선물)
- NYMEX: NY Mercantile Exchange (원유 선물)
- ICE: Intercontinental Exchange (달러 인덱스)
"""

from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient
from .account_api import OverseasFuturesAccountAPI
from .order_api import OverseasFuturesOrderAPI
from .price_api import OverseasFuturesPriceAPI


class OverseasFutures(BaseAPI):
    """
    해외선물옵션 API 통합 Facade 클래스

    하위 시스템들을 통합하여 간단한 인터페이스를 제공합니다.
    해외선물옵션 거래를 위한 모든 기능을 포함합니다 (19개 API).

    Attributes:
        price (OverseasFuturesPriceAPI): 시세 조회 API (8개 메서드)
        account_api (OverseasFuturesAccountAPI): 계좌/잔고 조회 API (9개 메서드)
        order (OverseasFuturesOrderAPI): 주문 API (2개 메서드 + 편의)

    Example:
        >>> from pykis import Agent
        >>>
        >>> agent = Agent(
        ...     app_key="...",
        ...     app_secret="...",
        ...     account_no="12345678",
        ...     account_code="03"  # 해외선물옵션 계좌
        ... )
        >>>
        >>> # 해외선물 현재가 조회
        >>> price = agent.overseas_futures.get_price("CNHU24")
        >>> print(f"현재가: {price['output']['last']}")
        >>>
        >>> # 해외선물 호가 조회
        >>> orderbook = agent.overseas_futures.get_futures_orderbook("CNHU24")
        >>> print(f"매수1호가: {orderbook['output2']['bidp1']}")
        >>>
        >>> # 잔고 조회
        >>> balance = agent.overseas_futures.get_balance()
        >>> for pos in balance['output']:
        ...     print(f"{pos['srs_cd']}: {pos['unsttl_qty']}계약")
        >>>
        >>> # 매수 주문
        >>> result = agent.overseas_futures.order.buy(
        ...     code="CNHU24",
        ...     qty="1",
        ...     price="100.00"
        ... )
        >>> print(f"주문번호: {result['output']['odno']}")
    """

    def __init__(
        self,
        client: KISClient,
        account_info: Optional[Dict[str, Any]] = None,
        enable_cache: bool = True,
        cache_config: Optional[Dict[str, Any]] = None,
        _from_agent: bool = False,
    ) -> None:
        """
        OverseasFutures API Facade 초기화

        Args:
            client (KISClient): API 통신 클라이언트
            account_info (dict, optional): 계좌 정보
            enable_cache (bool): 캐시 사용 여부 (기본: True)
            cache_config (dict, optional): 캐시 설정
            _from_agent (bool): Agent를 통해 생성되었는지 여부 (내부 사용)
        """
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

        # 하위 API 초기화
        self.price = OverseasFuturesPriceAPI(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )
        self.account_api = OverseasFuturesAccountAPI(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )
        self.order = OverseasFuturesOrderAPI(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

    # ===== 시세 관련 메서드 (OverseasFuturesPriceAPI 위임) =====

    def get_price(self, srs_cd: str) -> Optional[Dict]:
        """
        해외선물 현재가 조회

        Delegate to: OverseasFuturesPriceAPI.get_price()

        Args:
            srs_cd: 종목코드 (예: 'CNHU24')

        Returns:
            OverseasFuturesPriceResponse: 현재가 정보

        Example:
            >>> price = agent.overseas_futures.get_price("CNHU24")
            >>> print(f"현재가: {price['output']['last']}")
        """
        return self.price.get_price(srs_cd)

    def get_option_price(self, srs_cd: str) -> Optional[Dict]:
        """
        해외옵션 현재가 조회

        Delegate to: OverseasFuturesPriceAPI.get_option_price()

        Args:
            srs_cd: 옵션 종목코드

        Returns:
            OverseasOptionPriceResponse: 현재가 및 그릭스 정보
        """
        return self.price.get_option_price(srs_cd)

    def get_minute_chart(
        self,
        srs_cd: str,
        exch_cd: str,
        end_date: str = "",
        qry_cnt: str = "120",
        qry_gap: str = "1",
    ) -> Optional[Dict]:
        """해외선물 분봉 조회. Delegate to: OverseasFuturesPriceAPI"""
        return self.price.get_minute_chart(srs_cd, exch_cd, end_date, qry_cnt, qry_gap)

    def get_daily_trend(
        self,
        srs_cd: str,
        exch_cd: str,
        end_date: str = "",
        qry_cnt: str = "30",
    ) -> Optional[Dict]:
        """해외선물 체결추이(일간) 조회. Delegate to: OverseasFuturesPriceAPI"""
        return self.price.get_daily_trend(srs_cd, exch_cd, end_date, qry_cnt)

    def get_futures_orderbook(self, srs_cd: str) -> Optional[Dict]:
        """
        해외선물 호가 조회

        Delegate to: OverseasFuturesPriceAPI.get_futures_orderbook()

        Args:
            srs_cd: 종목코드

        Returns:
            OverseasFuturesOrderbookResponse: 호가 정보
        """
        return self.price.get_futures_orderbook(srs_cd)

    def get_option_orderbook(self, srs_cd: str) -> Optional[Dict]:
        """해외옵션 호가 조회. Delegate to: OverseasFuturesPriceAPI"""
        return self.price.get_option_orderbook(srs_cd)

    def get_futures_info(self, srs_codes: list) -> Optional[Dict]:
        """해외선물 상품기본정보 조회. Delegate to: OverseasFuturesPriceAPI"""
        return self.price.get_futures_info(srs_codes)

    def get_option_info(self, srs_codes: list) -> Optional[Dict]:
        """해외옵션 상품기본정보 조회. Delegate to: OverseasFuturesPriceAPI"""
        return self.price.get_option_info(srs_codes)

    # ===== 계좌/잔고 관련 메서드 (OverseasFuturesAccountAPI 위임) =====

    def get_balance(self, fuop_dvsn: str = "00") -> Optional[Dict]:
        """
        해외선물옵션 잔고 조회

        Delegate to: OverseasFuturesAccountAPI.get_balance()

        Args:
            fuop_dvsn: 선물옵션구분 (00:전체, 01:선물, 02:옵션)

        Returns:
            OverseasFuturesBalanceResponse: 잔고 정보

        Example:
            >>> balance = agent.overseas_futures.get_balance()
            >>> for pos in balance['output']:
            ...     print(f"{pos['srs_cd']}: {pos['unsttl_qty']}계약")
        """
        return self.account_api.get_balance(fuop_dvsn)

    def get_deposit(self, crcy_cd: str = "TUS", inqr_dt: str = "") -> Optional[Dict]:
        """
        해외선물옵션 예수금 조회

        Delegate to: OverseasFuturesAccountAPI.get_deposit()

        Args:
            crcy_cd: 통화코드 (TUS, TKR, USD, EUR 등)
            inqr_dt: 조회일자 (YYYYMMDD)

        Returns:
            OverseasFuturesDepositResponse: 예수금 정보

        Example:
            >>> deposit = agent.overseas_futures.get_deposit()
            >>> print(f"예수금: ${deposit['output']['dps_amt']}")
        """
        return self.account_api.get_deposit(crcy_cd, inqr_dt)

    def get_margin_detail(
        self, crcy_cd: str = "TUS", inqr_dt: str = ""
    ) -> Optional[Dict]:
        """해외선물옵션 증거금 상세. Delegate to: OverseasFuturesAccountAPI"""
        return self.account_api.get_margin_detail(crcy_cd, inqr_dt)

    def get_order_amount(
        self,
        ovrs_futr_fx_pdno: str,
        sll_buy_dvsn_cd: str,
        fm_ord_pric: str,
        ecis_rsvn_ord_yn: str = "N",
    ) -> Optional[Dict]:
        """해외선물옵션 주문가능 조회. Delegate to: OverseasFuturesAccountAPI"""
        return self.account_api.get_order_amount(
            ovrs_futr_fx_pdno, sll_buy_dvsn_cd, fm_ord_pric, ecis_rsvn_ord_yn
        )

    def get_today_orders(
        self,
        ccld_nccs_dvsn: str = "01",
        sll_buy_dvsn_cd: str = "%%",
        fuop_dvsn: str = "00",
    ) -> Optional[Dict]:
        """해외선물옵션 당일 주문내역. Delegate to: OverseasFuturesAccountAPI"""
        return self.account_api.get_today_orders(
            ccld_nccs_dvsn, sll_buy_dvsn_cd, fuop_dvsn
        )

    def get_daily_orders(
        self,
        strt_dt: str,
        end_dt: str,
        ccld_nccs_dvsn: str = "01",
        sll_buy_dvsn_cd: str = "%%",
        fuop_dvsn: str = "00",
        fm_pdgr_cd: str = "",
    ) -> Optional[Dict]:
        """해외선물옵션 일별 주문내역. Delegate to: OverseasFuturesAccountAPI"""
        return self.account_api.get_daily_orders(
            strt_dt, end_dt, ccld_nccs_dvsn, sll_buy_dvsn_cd, fuop_dvsn, fm_pdgr_cd
        )

    def get_daily_executions(
        self,
        strt_dt: str,
        end_dt: str,
        fuop_dvsn_cd: str = "00",
        sll_buy_dvsn_cd: str = "%%",
        crcy_cd: str = "%%%",
    ) -> Optional[Dict]:
        """해외선물옵션 일별 체결내역. Delegate to: OverseasFuturesAccountAPI"""
        return self.account_api.get_daily_executions(
            strt_dt, end_dt, fuop_dvsn_cd, sll_buy_dvsn_cd, crcy_cd
        )

    def get_period_profit(
        self,
        from_dt: str,
        to_dt: str,
        crcy_cd: str = "%%%",
        fuop_dvsn: str = "00",
        whol_trsl_yn: str = "N",
    ) -> Optional[Dict]:
        """해외선물옵션 기간 계좌손익. Delegate to: OverseasFuturesAccountAPI"""
        return self.account_api.get_period_profit(
            from_dt, to_dt, crcy_cd, fuop_dvsn, whol_trsl_yn
        )

    def get_period_transactions(
        self,
        from_dt: str,
        to_dt: str,
        acnt_tr_type_cd: str = "1",
        crcy_cd: str = "%%%",
    ) -> Optional[Dict]:
        """해외선물옵션 기간 거래내역. Delegate to: OverseasFuturesAccountAPI"""
        return self.account_api.get_period_transactions(
            from_dt, to_dt, acnt_tr_type_cd, crcy_cd
        )


# __all__ 정의
__all__ = [
    "OverseasFutures",  # 메인 Facade
    "OverseasFuturesPriceAPI",  # 시세 전담
    "OverseasFuturesAccountAPI",  # 계좌 전담
    "OverseasFuturesOrderAPI",  # 주문 전담
]
