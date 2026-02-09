"""
Futures API 패키지 - 선물옵션 관련 API 모음

Facade 패턴을 적용하여 단일 책임 원칙(SRP) 준수:
- Futures: Facade 패턴으로 통합 인터페이스 제공
- FuturesPriceAPI: 시세 조회 전담 (11개 메서드)
- FuturesAccountAPI: 계좌/잔고 조회 전담 (6개 메서드)
- FuturesOrderAPI: 주문/체결 조회 전담 (6개 메서드)
- FuturesCodeGenerator: 종목코드 자동 생성
"""

from typing import Any, Dict, Literal, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient
from .account_api import FuturesAccountAPI
from .code_generator import (
    FuturesCodeGenerator,
    generate_call_option,
    generate_current_futures,
    generate_next_futures,
    generate_put_option,
)
from .historical import FuturesContractCode, FuturesHistoricalAPI
from .order_api import FuturesOrderAPI
from .price_api import FuturesPriceAPI


class Futures(BaseAPI):
    """
    선물옵션 API 통합 Facade 클래스

    하위 시스템들을 통합하여 간단한 인터페이스를 제공합니다.
    국내 선물옵션 거래를 위한 모든 기능을 포함합니다.

    Attributes:
        price (FuturesPriceAPI): 시세 조회 API (11개 메서드)
        account_api (FuturesAccountAPI): 계좌/잔고 조회 API (6개 메서드)
        order (FuturesOrderAPI): 주문/체결 조회 API (6개 메서드)
        code (FuturesCodeGenerator): 종목코드 생성기

    Example:
        >>> from pykis import Agent
        >>>
        >>> agent = Agent(
        ...     app_key="...",
        ...     app_secret="...",
        ...     account_no="12345678",
        ...     account_code="03"  # 선물옵션 계좌
        ... )
        >>>
        >>> # 종목코드 자동 생성 - 현재 월물
        >>> code = agent.futures.code.generate_futures_code()
        >>> print(code)  # '101S03' (2026년 1월 → 3월물)
        >>>
        >>> # 시세 조회 (종목코드 직접 입력)
        >>> price = agent.futures.get_price("101S12")
        >>> print(price['output']['fuop_prpr'])
        >>>
        >>> # 시세 조회 (자동 생성)
        >>> price = agent.futures.get_current_futures_price()  # 현재 월물 자동
        >>> print(price['output']['fuop_prpr'])
        >>>
        >>> # 옵션 종목코드 생성
        >>> call_code = agent.futures.code.generate_option_code("CALL", 340.0)
        >>> print(call_code)  # '201SC340'
        >>>
        >>> # ATM 옵션 조회 (현재가 기반)
        >>> current_price = 340.25
        >>> atm_codes = agent.futures.code.generate_atm_option_codes(current_price)
        >>> print(atm_codes)
        >>> # {'atm_strike': 340.0, 'call': [...], 'put': [...]}
        >>>
        >>> # 매수 주문 (시장가)
        >>> result = agent.futures.order.order(
        ...     code="101S12",
        ...     order_type="02",  # 매수
        ...     qty="1",
        ...     price="0"  # 시장가
        ... )
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
        Futures API Facade 초기화

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

        # 하위 API 초기화 - Agent를 통해 생성된 경우 하위 API도 _from_agent=True로 초기화
        self.price = FuturesPriceAPI(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )
        self.account_api = FuturesAccountAPI(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )
        self.order = FuturesOrderAPI(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

        # 종목코드 생성기
        self.code = FuturesCodeGenerator

        # 과거 데이터 조회 API
        self.historical = FuturesHistoricalAPI(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

    # ===== 시세 관련 메서드 (FuturesPriceAPI 위임) =====

    def get_price(self, code: str) -> Optional[Dict]:
        """
        선물옵션 현재가 시세 조회

        Delegate to: FuturesPriceAPI.get_price()

        Args:
            code: 선물옵션 종목코드

        Returns:
            FuturesPriceResponse: 현재가 정보

        Example:
            >>> price = agent.futures.get_price("101S12")
            >>> print(price['output']['fuop_prpr'])
        """
        return self.price.get_price(code)

    def get_orderbook(self, code: str) -> Optional[Dict]:
        """
        선물옵션 호가 조회

        Delegate to: FuturesPriceAPI.get_orderbook()

        Args:
            code: 선물옵션 종목코드

        Returns:
            FuturesOrderbookResponse: 호가 정보

        Example:
            >>> orderbook = agent.futures.get_orderbook("101S12")
            >>> print(orderbook['output1']['askp1'])
        """
        return self.price.get_orderbook(code)

    def inquire_daily_fuopchartprice(
        self,
        code: str,
        start_date: str = "",
        end_date: str = "",
        period: str = "D",
    ) -> Optional[Dict]:
        """선물옵션 일별차트 조회. Delegate to: FuturesPriceAPI"""
        return self.price.inquire_daily_fuopchartprice(
            code, start_date, end_date, period
        )

    def inquire_time_fuopchartprice(
        self, code: str, hour: str = "153000", tick_range: str = "1"
    ) -> Optional[Dict]:
        """선물옵션 분봉차트 조회. Delegate to: FuturesPriceAPI"""
        return self.price.inquire_time_fuopchartprice(code, hour, tick_range)

    def display_board_callput(
        self,
        expiry: str,
        strike_base: str = "",
    ) -> Optional[Dict]:
        """옵션 콜/풋 전광판 조회. Delegate to: FuturesPriceAPI"""
        return self.price.display_board_callput(expiry, strike_base)

    def display_board_futures(self) -> Optional[Dict]:
        """선물 전광판 조회. Delegate to: FuturesPriceAPI"""
        return self.price.display_board_futures()

    # ===== 자주 사용하는 계좌 메서드도 직접 노출 (선택적) =====

    def inquire_balance(self) -> Optional[Dict]:
        """
        선물옵션 잔고 조회

        Delegate to: FuturesAccountAPI.inquire_balance()

        Example:
            >>> balance = agent.futures.inquire_balance()
            >>> # 또는
            >>> balance = agent.futures.account_api.inquire_balance()
        """
        return self.account_api.inquire_balance()

    def inquire_deposit(self) -> Optional[Dict]:
        """
        선물옵션 예수금 조회

        Delegate to: FuturesAccountAPI.inquire_deposit()

        Example:
            >>> deposit = agent.futures.inquire_deposit()
        """
        return self.account_api.inquire_deposit()

    # ===== 종목코드 자동 생성 편의 메서드 =====

    def get_current_futures_price(self) -> Optional[Dict]:
        """
        현재 월물 선물 현재가 조회 (종목코드 자동 생성)

        Returns:
            FuturesPriceResponse: 현재가 정보

        Example:
            >>> # 종목코드 입력 불필요 - 자동으로 현재 월물 조회
            >>> price = agent.futures.get_current_futures_price()
            >>> print(price['output']['fuop_prpr'])
        """
        code = generate_current_futures()
        return self.price.get_price(code)

    def get_next_futures_price(self) -> Optional[Dict]:
        """
        차근월물 선물 현재가 조회 (종목코드 자동 생성)

        Returns:
            FuturesPriceResponse: 현재가 정보

        Example:
            >>> price = agent.futures.get_next_futures_price()
            >>> print(price['output']['fuop_prpr'])
        """
        code = generate_next_futures()
        return self.price.get_price(code)

    def get_current_futures_orderbook(self) -> Optional[Dict]:
        """
        현재 월물 선물 호가 조회 (종목코드 자동 생성)

        Returns:
            FuturesOrderbookResponse: 호가 정보

        Example:
            >>> orderbook = agent.futures.get_current_futures_orderbook()
            >>> print(orderbook['output1']['askp1'])
        """
        code = generate_current_futures()
        return self.price.get_orderbook(code)

    def get_option_price(
        self,
        option_type: Literal["CALL", "PUT"],
        strike_price: float,
        expiry_month: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        옵션 현재가 조회 (종목코드 자동 생성)

        Args:
            option_type: 옵션 타입 ("CALL" 또는 "PUT")
            strike_price: 행사가
            expiry_month: 만기월 (없으면 현재 월물)

        Returns:
            FuturesPriceResponse: 현재가 정보

        Example:
            >>> # 현재 월물 콜옵션 340.0 현재가 조회
            >>> price = agent.futures.get_option_price("CALL", 340.0)
            >>> print(price['output']['fuop_prpr'])
            >>>
            >>> # 6월물 풋옵션 342.5 현재가 조회
            >>> price = agent.futures.get_option_price("PUT", 342.5, expiry_month=6)
            >>> print(price['output']['fuop_prpr'])
        """
        code = self.code.generate_option_code(
            option_type, strike_price, expiry_month=expiry_month
        )
        return self.price.get_price(code)

    def get_call_option_price(
        self, strike_price: float, expiry_month: Optional[int] = None
    ) -> Optional[Dict]:
        """
        콜옵션 현재가 조회 (종목코드 자동 생성)

        Args:
            strike_price: 행사가
            expiry_month: 만기월 (없으면 현재 월물)

        Returns:
            FuturesPriceResponse: 현재가 정보

        Example:
            >>> price = agent.futures.get_call_option_price(340.0)
            >>> print(price['output']['fuop_prpr'])
        """
        return self.get_option_price("CALL", strike_price, expiry_month)

    def get_put_option_price(
        self, strike_price: float, expiry_month: Optional[int] = None
    ) -> Optional[Dict]:
        """
        풋옵션 현재가 조회 (종목코드 자동 생성)

        Args:
            strike_price: 행사가
            expiry_month: 만기월 (없으면 현재 월물)

        Returns:
            FuturesPriceResponse: 현재가 정보

        Example:
            >>> price = agent.futures.get_put_option_price(340.0)
            >>> print(price['output']['fuop_prpr'])
        """
        return self.get_option_price("PUT", strike_price, expiry_month)

    def get_current_futures_chart(
        self, start_date: str = "", end_date: str = "", period: str = "D"
    ) -> Optional[Dict]:
        """
        현재 월물 선물 차트 조회 (종목코드 자동 생성)

        Args:
            start_date: 조회 시작일자 (YYYYMMDD)
            end_date: 조회 종료일자 (YYYYMMDD)
            period: 기간 구분 (D:일, W:주, M:월)

        Returns:
            차트 데이터

        Example:
            >>> # 현재 월물 일봉 차트
            >>> chart = agent.futures.get_current_futures_chart("20260101", "20260131")
            >>> for candle in chart['output']:
            ...     print(f"{candle['stck_bsop_date']}: {candle['fuop_prpr']}")
        """
        code = generate_current_futures()
        return self.price.inquire_daily_fuopchartprice(
            code, start_date, end_date, period
        )

    def order_current_futures(
        self, order_type: str, qty: str, price: str = "0", order_cond: str = "0"
    ) -> Optional[Dict]:
        """
        현재 월물 선물 주문 (종목코드 자동 생성)

        Args:
            order_type: 주문 구분 (01:매도, 02:매수)
            qty: 주문 수량
            price: 주문 단가 (0:시장가)
            order_cond: 주문 조건 (0:없음, 1:IOC, 2:FOK)

        Returns:
            FuturesOrderResponse: 주문 응답

        Example:
            >>> # 현재 월물 시장가 매수 1계약
            >>> result = agent.futures.order_current_futures("02", "1", "0")
            >>> print(f"주문번호: {result['output']['odno']}")
        """
        code = generate_current_futures()
        return self.order.order(code, order_type, qty, price, order_cond)

    def order_option(
        self,
        option_type: Literal["CALL", "PUT"],
        strike_price: float,
        order_type: str,
        qty: str,
        price: str = "0",
        expiry_month: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        옵션 주문 (종목코드 자동 생성)

        Args:
            option_type: 옵션 타입 ("CALL" 또는 "PUT")
            strike_price: 행사가
            order_type: 주문 구분 (01:매도, 02:매수)
            qty: 주문 수량
            price: 주문 단가 (0:시장가)
            expiry_month: 만기월 (없으면 현재 월물)

        Returns:
            FuturesOrderResponse: 주문 응답

        Example:
            >>> # 콜옵션 340.0 시장가 매수 1계약
            >>> result = agent.futures.order_option("CALL", 340.0, "02", "1", "0")
            >>> print(f"주문번호: {result['output']['odno']}")
        """
        code = self.code.generate_option_code(
            option_type, strike_price, expiry_month=expiry_month
        )
        return self.order.order(code, order_type, qty, price)

    # ===== 과거 데이터 조회 메서드 =====

    def get_historical_minute_bars(
        self,
        start_date: str,
        end_date: str = "",
        interval: str = "1",
        max_bars: int = 1000,
    ) -> list:
        """
        과거 선물 분봉 데이터 조회 (월물 자동 전환)

        Args:
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD, 기본값: 오늘)
            interval: 분봉 간격 (1:1분, 3:3분, 5:5분, 10:10분, 30:30분, 60:60분)
            max_bars: 최대 조회 건수 (기본값: 1000)

        Returns:
            분봉 데이터 리스트 (시간 오름차순)

        Example:
            >>> # 2025년 1월 한 달간 1분봉 데이터
            >>> bars = agent.futures.get_historical_minute_bars(
            ...     "20250101", "20250131", interval="1", max_bars=5000
            ... )
            >>> for bar in bars[:5]:
            ...     print(f"{bar['date']} {bar['time']}: {bar['close']}")
        """
        return self.historical.get_minute_bars(
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            max_bars=max_bars,
        )

    def get_contract_minute_bars(
        self,
        code: str,
        start_date: str,
        end_date: str = "",
        interval: str = "1",
        max_bars: int = 1000,
    ) -> list:
        """
        특정 월물의 분봉 데이터 조회

        Args:
            code: 종목코드 (예: "1016C" = 2026년 3월물)
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            interval: 분봉 간격
            max_bars: 최대 조회 건수

        Returns:
            분봉 데이터 리스트

        Example:
            >>> # 2026년 3월물 데이터 조회
            >>> bars = agent.futures.get_contract_minute_bars(
            ...     "1016C", "20260101", "20260131"
            ... )
        """
        return self.historical.get_contract_history(
            code=code,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            max_bars=max_bars,
        )


# __all__ 정의
__all__ = [
    "Futures",  # 메인 Facade
    "FuturesPriceAPI",  # 시세 전담
    "FuturesAccountAPI",  # 계좌 전담
    "FuturesOrderAPI",  # 주문 전담
    "FuturesCodeGenerator",  # 종목코드 생성기
    "FuturesContractCode",  # 월물 코드 생성기 (과거 데이터용)
    "FuturesHistoricalAPI",  # 과거 데이터 조회
    "generate_current_futures",  # 현재 월물 코드
    "generate_next_futures",  # 차근월물 코드
    "generate_call_option",  # 콜옵션 코드
    "generate_put_option",  # 풋옵션 코드
]
