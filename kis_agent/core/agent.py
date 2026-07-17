import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from ..account.api import AccountAPI
from ..futures import Futures
from ..overseas import OverseasStockAPI
from ..overseas_futures import OverseasFutures
from ..program.trade import ProgramTradeAPI
from ..stock import (
    StockAPI,  # [변경 이유] 레거시가 아닌 패키지 파사드 StockAPI 사용으로 중복/충돌 제거
    StockMarketAPI,
)
from ..stock.interest import InterestStockAPI
from ..stock.investor_api import StockInvestorAPI
from ..utils.futures_master import load_futures as _load_futures_master
from ..utils.sector_code import (
    SECTOR_CODES,
    get_sector_code_by_market,
    get_sector_codes,
)
from ..utils.stock_master import load_stocks as _load_stock_master
from ..websocket.client import KisWebSocket
from .base_exception_handler import BaseExceptionHandler, exception_handler
from .client import KISClient
from .config import KISConfig
from .constants import REAL_BASE_URL, resolve_environment  # noqa: F401
from .method_discovery import MethodDiscoveryMixin
from .rate_limiter import RateLimiter, get_global_rate_limiter
from .rate_limiter_mixin import RateLimiterControlMixin
from .technical_analysis import TechnicalAnalysisMixin


class Agent(
    TechnicalAnalysisMixin,
    MethodDiscoveryMixin,
    RateLimiterControlMixin,
    BaseExceptionHandler,
):
    """
    한국투자증권 API의 통합 인터페이스

    PyKIS의 핵심 클래스로 모든 API 기능을 통합된 인터페이스로 제공합니다.
    KOSPI, KOSDAQ, NXT 시장 지원과 고성능 캐싱, Rate Limiting, WebSocket 연결을 포함합니다.

    주요 기능:
    - 주식 시세 조회 (실시간/과거 데이터)
    - 계좌 정보 및 거래 기능
    - 프로그램 매매 분석
    - 실시간 WebSocket 데이터 스트리밍
    - 조건검색식 및 투자자 동향 분석
    - 선물/옵션 데이터 조회
    - Excel 거래 보고서 생성

    Performance Features:
    - 지능형 캐싱 시스템 (80-95% API 호출 감소)
    - 실측 기반 Rate Limiting (18 RPS / 900 RPM)
    - 자동 에러 복구 및 재시도 메커니즘
    - 멀티스레드 안전성 보장

    Example:
        >>> from kis_agent import Agent
        >>> agent = Agent(
        ...     app_key="YOUR_APP_KEY",
        ...     app_secret="YOUR_APP_SECRET",  # cxt-ignore: hardcoded_secret
        ...     account_no="12345678",
        ...     account_code="01"
        ... )
        >>>
        >>> # 주식 시세 조회 (캐싱 적용)
        >>> price = agent.get_stock_price("005930")  # 삼성전자
        >>>
        >>> # 실시간 WebSocket 연결
        >>> ws = agent.websocket(["005930", "035420"])
        >>>
        >>> # 거래 주문
        >>> result = agent.order_stock_cash("buy", "005930", "00", "1", "70000")
        >>>
        >>> # Excel 거래 보고서 생성
        >>> from kis_agent.utils.trading_report import generate_trading_report
        >>> report = generate_trading_report(agent.client, account_info, "20250101", "20250131")
    """

    # [변경 이유] 로거 미정의로 flake8 F821 경고 발생. 모듈 레벨 로거를 명시적으로 생성합니다.
    logger = logging.getLogger(__name__)

    @staticmethod
    def _validate_required(
        app_key: str, app_secret: str, account_no: str, account_code: str
    ) -> None:
        """Reject a half-configured Agent before it reaches the network.

        `__init__`과 `create_async`가 공유한다 — 두 경로가 같은 메시지를 내야
        사용자가 동기/비동기에 따라 다른 안내를 받지 않는다.

        Raises:
            ValueError: 필수 매개변수가 하나라도 비어 있는 경우.
        """
        if all([app_key, app_secret, account_no, account_code]):
            return
        raise ValueError(
            "필수 매개변수가 누락되었습니다.\n"
            "Agent를 생성할 때 다음 매개변수가 모두 필요합니다:\n"
            "  - app_key: 한국투자증권 API 앱 키\n"
            "  - app_secret: 한국투자증권 API 앱 시크릿\n"
            "  - account_no: 계좌번호\n"
            "  - account_code: 계좌 상품코드\n\n"
            "예시:\n"
            "  agent = Agent(\n"
            "      app_key='YOUR_APP_KEY',\n"
            "      app_secret='YOUR_APP_SECRET',\n"  # cxt-ignore: hardcoded_secret
            "      account_no='12345678',\n"
            "      account_code='01'\n"
            "  )"
        )

    @classmethod
    async def create_async(
        cls,
        app_key: str,
        app_secret: str,
        account_no: str,
        account_code: str,
        base_url: Optional[str] = None,
        paper: Optional[bool] = None,
        svr: str = "prod",
        verbose: bool = False,
        account_info: Optional[Dict] = None,
        enable_rate_limiter: bool = True,
        rate_limiter: Optional[RateLimiter] = None,
        rate_limiter_config: Optional[Dict[str, Any]] = None,
    ) -> "Agent":
        """Create an Agent without blocking the event loop on token issuance.

        `Agent(...)`는 생성자에서 동기 HTTP로 토큰을 발급한다. asyncio 앱에서는
        그 사이 이벤트 루프가 멈추므로, 토큰만 비동기로 받아 동일하게 초기화한
        Agent를 돌려준다. 인자와 동작은 `__init__`과 같다.

        Args:
            app_key: 한국투자증권 API 앱 키 (필수).
            app_secret: 한국투자증권 API 앱 시크릿 (필수).
            account_no: 계좌번호 (필수).
            account_code: 계좌 상품코드 (필수).
            base_url: API 베이스 URL. None이면 `paper`/환경변수로 결정.
            paper: 모의투자 사용 여부. `__init__`과 동일.
            svr: 인증 서버 구분 ('prod' 또는 'vps').
            verbose: 상세 로깅 여부.
            account_info: 계좌 정보. None이면 자동 설정.
            enable_rate_limiter: Rate Limiter 사용 여부.
            rate_limiter: 커스텀 Rate Limiter 인스턴스.
            rate_limiter_config: Rate Limiter 설정.

        Returns:
            토큰이 발급된 `Agent`.

        Raises:
            ValueError: 필수 매개변수 누락 또는 `paper`/`base_url` 모순.
            ImportError: aiohttp 미설치.
            RuntimeError: 토큰 발급 실패.

        Example:
            >>> agent = await Agent.create_async(
            ...     app_key="...", app_secret="...",
            ...     account_no="12345678", account_code="01",
            ... )
            >>> price = agent.get_stock_price("005930")
        """
        # 네트워크를 타기 전에 검증한다 (동기 경로와 동일한 메시지).
        cls._validate_required(app_key, app_secret, account_no, account_code)

        base_url, _ = resolve_environment(base_url=base_url, paper=paper)
        config = KISConfig(
            app_key=app_key,
            app_secret=app_secret,
            base_url=base_url,
            account_no=account_no,
            account_code=account_code,
        )

        # 토큰 발급만 비동기로. 완성된 client를 넘기면 __init__은 동기 인증을
        # 하지 않는다.
        client = await KISClient.create_async(
            svr=svr,
            config=config,
            verbose=verbose,
            enable_rate_limiter=enable_rate_limiter,
            rate_limiter=rate_limiter,
        )

        return cls(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code,
            base_url=base_url,
            client=client,
            account_info=account_info,
            enable_rate_limiter=enable_rate_limiter,
            rate_limiter=rate_limiter,
            rate_limiter_config=rate_limiter_config,
        )

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        account_no: str,
        account_code: str,
        base_url: Optional[str] = None,
        paper: Optional[bool] = None,
        client: Optional[KISClient] = None,
        account_info: Optional[Dict] = None,
        enable_rate_limiter: bool = True,
        rate_limiter: Optional[RateLimiter] = None,
        rate_limiter_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Agent를 초기화합니다.

        Args:
            app_key (str): 한국투자증권 API 앱 키 (필수)
            app_secret (str): 한국투자증권 API 앱 시크릿 (필수)
            account_no (str): 계좌번호 (필수)
            account_code (str): 계좌 상품코드 (필수)
            base_url (str, optional): API 베이스 URL. None이면 `paper` /
                `KIS_PAPER` / `KIS_BASE_URL` 로부터 결정된다 (기본: 실전투자).
                - 실전투자: "https://openapi.koreainvestment.com:9443"
                - 모의투자: "https://openapivts.koreainvestment.com:29443"
            paper (bool, optional): 모의투자 사용 여부. True면 모의투자 URL과
                모의투자 TR_ID가 자동 적용된다. None이면 `KIS_PAPER` 환경변수,
                그것도 없으면 `base_url` 모양으로 추론한다.
                `base_url`과 모순되면 ValueError.
            client (KISClient, optional): API 클라이언트. None이면 새로 생성
            account_info (Dict, optional): 계좌 정보. None이면 자동 설정
            enable_rate_limiter (bool): Rate Limiter 사용 여부 (기본값: True)
            rate_limiter (RateLimiter, optional): 커스텀 Rate Limiter 인스턴스
            rate_limiter_config (Dict, optional): Rate Limiter 설정
                - requests_per_second: 초당 최대 요청 수 (기본값: 18, 실측 안정값)
                - requests_per_minute: 분당 최대 요청 수 (기본값: 900, 실측 안정값)
                - min_interval_ms: 최소 간격(밀리초) (기본값: 50ms, 권장값)
                - burst_size: 버스트 크기 (기본값: 10, 안정성 우선)
                - enable_adaptive: 적응형 백오프 활성화 (기본값: True)

        Raises:
            ValueError: 필수 매개변수가 누락되었을 때
            RuntimeError: 토큰 발급이 실패했을 때

        Example:
            >>> # 실전투자 Agent 생성
            >>> agent = Agent(
            ...     app_key="YOUR_APP_KEY",
            ...     app_secret="YOUR_APP_SECRET",  # cxt-ignore: hardcoded_secret
            ...     account_no="12345678",
            ...     account_code="01"
            ... )
            >>>
            >>> # 모의투자 Agent 생성
            >>> agent = Agent(
            ...     app_key="YOUR_APP_KEY",
            ...     app_secret="YOUR_APP_SECRET",  # cxt-ignore: hardcoded_secret
            ...     account_no="12345678",
            ...     account_code="01",
            ...     paper=True
            ... )
            >>>
            >>> # Rate Limiter 비활성화
            >>> agent = Agent(
            ...     app_key="YOUR_APP_KEY",
            ...     app_secret="YOUR_APP_SECRET",  # cxt-ignore: hardcoded_secret
            ...     account_no="12345678",
            ...     account_code="01",
            ...     enable_rate_limiter=False
            ... )

        Note:
            API 키와 계좌 정보는 보안상 중요하므로 코드에 직접 하드코딩하지 마세요.
            환경변수나 별도의 설정 파일에서 로드하는 것을 권장합니다.
        """
        # BaseExceptionHandler 초기화
        super().__init__("Agent")

        # 필수 매개변수 검증
        self._validate_required(app_key, app_secret, account_no, account_code)

        # 실전/모의 환경 결정 (paper > KIS_PAPER > base_url 순으로 의도를 해석).
        # 모순 시 ValueError — 잘못된 환경으로 주문이 나가는 것보다 낫다.
        base_url, self.is_real = resolve_environment(base_url=base_url, paper=paper)
        if not self.is_real:
            self.logger.info("모의투자 모드로 실행합니다 (모의투자 TR_ID 자동 적용)")

        # Rate Limiter 설정 (전역 싱글턴 패턴)
        # 기본값은 kis_agent.core.rate_limiter의 DEFAULT_* 상수를 사용한다
        # (공식 20 RPS / 1000 RPM 대비 75% / 80% 안전 마진).
        # 사용자가 rate_limiter_config로 일부 키를 override할 수 있다.
        if enable_rate_limiter:
            if rate_limiter:
                self.rate_limiter = rate_limiter
            elif rate_limiter_config:
                # 사용자 override는 첫 호출에서만 적용됨 (싱글턴이므로)
                self.rate_limiter = get_global_rate_limiter(**rate_limiter_config)
            else:
                self.rate_limiter = get_global_rate_limiter()
        else:
            self.rate_limiter = None

        # 설정 객체 생성
        config = (
            KISConfig(
                app_key=app_key,
                app_secret=app_secret,
                base_url=base_url,
                account_no=account_no,
                account_code=account_code,
            )
            if not client
            else None
        )

        # 클라이언트 초기화 (KISClient._initialize_token에서 토큰 자동 관리)
        self.client = client or KISClient(
            config=config,
            enable_rate_limiter=enable_rate_limiter,
            rate_limiter=self.rate_limiter,
        )

        # 계좌 정보 설정
        if account_info is None:
            self.account_info = {
                "CANO": account_no,
                "ACNT_PRDT_CD": account_code,
            }
        else:
            self.account_info = account_info

        # [추가] STONKS 프로젝트 호환성을 위한 my_acct 속성
        self.my_acct = self.account_info

        # API 모듈 초기화
        self._init_apis()

    def _init_apis(self) -> None:
        """API 모듈들을 초기화합니다 (Agent를 통한 정상 경로)."""
        self.account_api = AccountAPI(self.client, self.account_info, _from_agent=True)
        self.stock_api = StockAPI(self.client, self.account_info, _from_agent=True)
        self.investor_api = StockInvestorAPI(
            self.client, self.account_info, _from_agent=True
        )
        self.program_api = ProgramTradeAPI(
            self.client, self.account_info, _from_agent=True
        )
        self.market_api = StockMarketAPI(
            self.client, self.account_info, _from_agent=True
        )
        self.interest_api = InterestStockAPI(
            self.client, self.account_info, _from_agent=True
        )
        self.overseas_api = OverseasStockAPI(
            self.client, self.account_info, _from_agent=True
        )
        self.futures_api = Futures(self.client, self.account_info, _from_agent=True)
        self.overseas_futures_api = OverseasFutures(
            self.client, self.account_info, _from_agent=True
        )

        # 종목 마스터 사전 로드 (캐시 있으면 즉시 반환, 없으면 백그라운드 다운로드)
        self._preload_masters()

    def _preload_masters(self) -> None:
        """종목 마스터 파일 사전 로드.

        캐시가 오늘 날짜면 즉시 반환 (수 ms).
        캐시가 없거나 오래됐으면 백그라운드 스레드에서 다운로드.
        실패해도 Agent 초기화를 블로킹하지 않음.
        """
        import threading

        def _load():
            try:
                stocks = _load_stock_master()
                futures = _load_futures_master()
                self.logger.info(
                    f"종목 마스터 로드 완료: 주식 {len(stocks)}개, 선물옵션 {len(futures)}개"
                )
            except Exception as e:
                self.logger.warning(f"종목 마스터 로드 실패 (무시): {e}")

        thread = threading.Thread(target=_load, daemon=True)
        thread.start()

    @property
    def overseas(self) -> OverseasStockAPI:
        """
        해외주식 API 파사드

        해외주식 거래에 필요한 모든 API를 통합된 인터페이스로 제공합니다.

        지원 거래소:
        - 미국: NAS (NASDAQ), NYS (NYSE), AMS (AMEX)
        - 아시아: HKS (홍콩), TSE (도쿄), SHS (상해), SZS (심천), HSX (호치민), HNX (하노이)

        Returns:
            OverseasStockAPI: 해외주식 API 파사드

        Example:
            >>> from kis_agent import Agent
            >>> agent = Agent(...)
            >>>
            >>> # 시세 조회
            >>> price = agent.overseas.get_price(excd="NAS", symb="AAPL")
            >>> print(f"AAPL: ${price['output']['last']}")
            >>>
            >>> # 일봉 조회
            >>> daily = agent.overseas.get_daily_price(excd="NAS", symb="TSLA")
            >>>
            >>> # 호가 조회
            >>> orderbook = agent.overseas.get_orderbook(excd="NYS", symb="MSFT")
        """
        return self.overseas_api

    @property
    def futures(self) -> Futures:
        """
        선물옵션 API 파사드

        국내 선물옵션 거래에 필요한 모든 API를 통합된 인터페이스로 제공합니다.

        지원 상품:
        - KOSPI200 선물/옵션
        - 기타 파생상품

        Returns:
            Futures: 선물옵션 API 파사드

        Example:
            >>> from kis_agent import Agent
            >>> agent = Agent(
            ...     app_key="...",
            ...     app_secret="...",
            ...     account_no="12345678",
            ...     account_code="03"  # 선물옵션 계좌
            ... )
            >>>
            >>> # 시세 조회
            >>> price = agent.futures.get_price("101S12")  # KOSPI200 선물
            >>> print(f"현재가: {price['output']['fuop_prpr']}")
            >>>
            >>> # 호가 조회
            >>> orderbook = agent.futures.get_orderbook("101S12")
            >>> print(f"매도호가1: {orderbook['output1']['askp1']}")
            >>>
            >>> # 잔고 조회
            >>> balance = agent.futures.inquire_balance()
            >>> for item in balance['output']:
            ...     print(f"{item['item_name']}: {item['fnoat_plamt']}원")
            >>>
            >>> # 주문 가능 수량 조회
            >>> psbl = agent.futures.order.inquire_psbl_order("101S12")
            >>> print(f"주문가능: {psbl['output']['ord_psbl_qty']}계약")
            >>>
            >>> # 매수 주문 (시장가)
            >>> result = agent.futures.order.order(
            ...     code="101S12",
            ...     order_type="02",  # 매수
            ...     qty="1",
            ...     price="0"  # 시장가
            ... )
        """
        return self.futures_api

    @property
    def overseas_futures(self) -> OverseasFutures:
        """
        해외선물옵션 API 파사드

        해외선물옵션 거래에 필요한 모든 API를 통합된 인터페이스로 제공합니다.

        지원 거래소:
        - CME: Chicago Mercantile Exchange (E-mini S&P500, 나스닥100)
        - EUREX: European Exchange (EURO STOXX 50)
        - COMEX: Commodity Exchange (금, 은 선물)
        - NYMEX: NY Mercantile Exchange (원유 선물)
        - ICE: Intercontinental Exchange (달러 인덱스)

        Returns:
            OverseasFutures: 해외선물옵션 API 파사드

        Example:
            >>> from kis_agent import Agent
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
        return self.overseas_futures_api

    def websocket(
        self,
        stock_codes: list = None,
        purchase_prices: dict = None,
        enable_index: bool = True,
        enable_program_trading: bool = True,
        enable_ask_bid: bool = False,
    ) -> KisWebSocket:
        """
        실시간 웹소켓 클라이언트를 생성합니다.

        Args:
            stock_codes (list, optional): 구독할 종목코드 리스트. Defaults to None.
            purchase_prices (dict, optional): 매수 정보 딕셔너리
                {'종목코드': (매입가격, 보유 수량)}. Defaults to None.
            enable_index (bool): 지수 실시간 데이터 구독 여부. Defaults to True.
            enable_program_trading (bool): 프로그램매매 실시간 데이터 구독 여부. Defaults to True.
            enable_ask_bid (bool): 호가 실시간 데이터 구독 여부. Defaults to False.

        Returns:
            KisWebSocket: 웹소켓 클라이언트 객체
        """
        return KisWebSocket(
            client=self.client,
            account_info=self.account_info,
            stock_codes=stock_codes,
            purchase_prices=purchase_prices,
            enable_index=enable_index,
            enable_program_trading=enable_program_trading,
            enable_ask_bid=enable_ask_bid,
        )

    # ============================================================================
    # 주식 시세 관련 메서드들 (StockAPI 위임)
    # ============================================================================

    # ============================================================================
    # 계좌 관련 메서드들 (AccountAPI 위임)
    # ============================================================================

    # ============================================================================
    # 프로그램 매매 관련 메서드들 (ProgramTradeAPI 위임)
    # ============================================================================

    # ===== 메서드 탐색 기능은 MethodDiscoveryMixin에서 상속 =====
    # get_all_methods, search_methods, show_method_usage, classify_broker
    # → pykis/core/method_discovery.py 참조

    @exception_handler(
        message="휴장일 정보 조회 실패", reraise=False, default_return=None
    )
    @exception_handler(message="휴장일 확인 실패", reraise=False, default_return=None)

    # ===== 기술 분석 메서드는 TechnicalAnalysisMixin에서 상속 =====
    # init_minute_db, migrate_minute_csv_to_db, fetch_minute_data,
    # calculate_support_resistance 등은 TechnicalAnalysisMixin 참조

    def get_condition_stocks(
        self, user_id: str = "unohee", seq: int = 0, tr_cont: str = "N"
    ) -> Optional[List[Dict[str, Any]]]:
        """조건검색 결과를 조회합니다.

        Args:
            user_id (str): 사용자 ID (기본값: "unohee")
            seq (int): 조건검색 시퀀스 번호 (기본값: 0)
            tr_cont (str): 연속조회 여부 (기본값: 'N')

        Returns:
            List[Dict]: 조건검색 결과 리스트, 실패 시 None
        """
        try:
            from ..stock.condition import ConditionAPI

            condition_api = ConditionAPI(self.client)
            return condition_api.get_condition_stocks(user_id, seq, tr_cont)
        except Exception as e:
            logging.error(f"조건검색 종목 조회 실패: {e}")
            return None

    def get_top_gainers(self) -> Optional[List[Dict[str, Any]]]:
        """
        상승률 상위 종목 조회

        국내주식 등락률 순위를 조회하여 상승률이 높은 종목 목록을 반환합니다.

        Returns:
            Optional[List[Dict[str, Any]]]: 상승률 상위 종목 리스트
                - 성공 시: 등락률 순위 정보 리스트
                - 실패 시: 빈 리스트

        Example:
            >>> agent = Agent(env_path=".env")
            >>> top_gainers = agent.get_top_gainers()
            >>> for stock in top_gainers[:5]:  # 상위 5개
            ...     print(f"{stock['hts_kor_isnm']}: {stock['prdy_ctrt']}%")
        """
        try:
            return self.stock_api.get_market_fluctuation()
        except Exception as e:
            logging.error(f"상승률 상위 종목 조회 실패: {e}")
            return []

    # ===== 새로 추가된 계좌 관련 API 메서드 (2025-01-08) =====

    def order_stock_cash(
        self,
        ord_dv: str,  # 매수매도구분 (buy:매수, sell:매도)
        pdno: str,  # 종목코드
        ord_dvsn: str,  # 주문구분
        ord_qty: str,  # 주문수량
        ord_unpr: str,  # 주문단가
        excg_id_dvsn_cd: str = "KRX",  # 거래소ID구분코드
        sll_type: str = "",  # 매도유형
        cndt_pric: str = "",  # 조건가격
    ) -> Optional[Dict[str, Any]]:
        """국내주식 현금 주문 (Cash order for domestic stocks)

        현금으로 국내 주식을 매수/매도합니다. 지정가, 시장가, 조건부지정가 등 다양한 주문 유형을 지원합니다.
        Places buy/sell orders for domestic stocks with cash. Supports various order types including limit, market, and conditional orders.

        Args:
            ord_dv: 매수매도구분 (Order type)
                    "buy": 매수 (Buy), "sell": 매도 (Sell)
            pdno: 종목코드 6자리 (Stock code, 6 digits)
                  예: "005930" (삼성전자), "035720" (카카오)
            ord_dvsn: 주문구분 (Order division)
                      - "00": 지정가 (Limit order)
                      - "01": 시장가 (Market order)
                      - "02": 조건부지정가 (Conditional limit)
                      - "03": 최유리지정가 (Best limit)
                      - "05": 장전시간외 (Pre-market)
                      - "06": 장후시간외 (After-hours)
                      - "11": IOC지정가 (IOC limit)
                      - "12": FOK지정가 (FOK limit)
            ord_qty: 주문수량 (Order quantity)
                     문자열 형식, 예: "1", "10"
            ord_unpr: 주문단가 (Order price)
                      시장가 주문 시 "0" (Use "0" for market orders)
            excg_id_dvsn_cd: 거래소ID구분코드 (Exchange ID)
                             기본값: "KRX" (한국거래소)
            sll_type: 매도유형 (Sell type, optional)
                      - "01": 일반매도 (Normal sell)
                      - "02": 임의매매 (Discretionary)
                      - "05": 대차매도 (Short sell)
            cndt_pric: 조건가격 (Conditional price, optional)
                       스탑주문 시 사용 (Used for stop orders)

        Returns:
            Optional[Dict[str, Any]]: 주문 결과 (Order result)
                - rt_cd: 응답코드 (Response code, "0" = success)
                - msg1: 응답메시지 (Response message)
                - output.KRX_FWDG_ORD_ORGNO: 주문조직번호 (Order org number)
                - output.ODNO: 주문번호 (Order number)
                - output.ORD_TMD: 주문시각 (Order time)
                - 실패 시 None 반환 (Returns None on failure)

        Raises:
            ValueError: 잘못된 주문 파라미터 입력 시
                       (If invalid order parameters provided)

        Examples:
            >>> agent = Agent(app_key="...", app_secret="...", account_no="...", account_code="...")
            >>>
            >>> # 예시 1: 삼성전자 1주 70,000원 지정가 매수
            >>> result = agent.order_stock_cash("buy", "005930", "00", "1", "70000")
            >>> if result and result['rt_cd'] == '0':
            ...     print(f"주문번호: {result['output']['ODNO']}")
            주문번호: 0000123456
            >>>
            >>> # 예시 2: 카카오 1주 시장가 매도
            >>> result = agent.order_stock_cash("sell", "035720", "01", "1", "0")
            >>>
            >>> # 예시 3: 최유리지정가로 빠른 매수 (추천)
            >>> result = agent.order_stock_cash("buy", "005930", "03", "1", "0")

        Note:
            - Rate Limiting: 18 RPS / 900 RPM
            - 캐싱 없음 (주문은 매번 새로 실행) (No caching for orders)
            - 주문 가능 시간: 08:00 ~ 15:30 (정규장) (Regular market hours)
            - 시간외 거래: 08:30 ~ 08:40, 15:40 ~ 16:00 (Extended hours)
        """
        # ord_dv를 buy_sell로 변환 ("buy" → "BUY", "sell" → "SELL")
        buy_sell = "BUY" if ord_dv.lower() == "buy" else "SELL"

        return self.account_api.order_cash(
            pdno=pdno,
            qty=int(ord_qty),
            price=int(ord_unpr),
            buy_sell=buy_sell,
            order_type=ord_dvsn,
            exchange=excg_id_dvsn_cd,
        )

    def order_stock_credit(
        self,
        ord_dv: str,  # 매수매도구분 (buy:매수, sell:매도)
        pdno: str,  # 종목코드
        crdt_type: str,  # 신용유형
        ord_dvsn: str,  # 주문구분
        ord_qty: str,  # 주문수량
        ord_unpr: str,  # 주문단가
        loan_dt: str = "",  # 대출일자 (기본값: 빈 문자열)
        excg_id_dvsn_cd: str = "KRX",  # 거래소ID구분코드
        sll_type: str = "",  # 매도유형
        rsvn_ord_yn: str = "N",  # 예약주문여부
        emgc_ord_yn: str = "",  # 비상주문여부
        cndt_pric: str = "",  # 조건가격
    ) -> Optional[Dict[str, Any]]:
        """
        국내주식주문(신용) API - StockAPI 기반

        StockAPI의 order_credit 메서드를 사용하여 신용매수/매도 주문을 실행합니다.
        (모의투자 미지원)

        Args:
            ord_dv (str): 매수매도구분 (buy:매수, sell:매도)
            pdno (str): 종목코드 (6자리)
            crdt_type (str): 신용유형
                - [매수] 21:자기융자신규, 23:유통융자신규, 26:유통대주상환, 28:자기대주상환
                - [매도] 22:유통대주신규, 24:자기대주신규, 25:자기융자상환, 27:유통융자상환
            ord_dvsn (str): 주문구분
                - 00:지정가, 01:시장가, 02:조건부지정가, 03:최유리지정가
                - 04:최우선지정가, 05:장전시간외, 06:장후시간외, 07:시간외단일가
            ord_qty (str): 주문수량
            ord_unpr (str): 주문단가
            loan_dt (str): 대출일자 (YYYYMMDD, 기본값: "")
                - 신용매수: 오늘날짜 권장
                - 신용매도: 매도할 종목의 대출일자
                - 빈 문자열 허용 (AccountAPI 호환성)
            excg_id_dvsn_cd (str): 거래소ID구분코드 (KRX:한국거래소)
            sll_type (str): 매도유형
            rsvn_ord_yn (str): 예약주문여부 (Y:예약주문, N:신용주문)
            emgc_ord_yn (str): 비상주문여부
            cndt_pric (str): 조건가격

        Returns:
            Optional[Dict[str, Any]]: 주문 결과 데이터
                - rt_cd: 응답코드 ("0": 성공)
                - msg1: 응답메시지
                - output: 주문 상세 정보

        Example:
            >>> # 삼성전자 1주 자기융자신규 매수
            >>> from datetime import datetime
            >>> today = datetime.now().strftime("%Y%m%d")
            >>> result = agent.order_stock_credit(
            ...     ord_dv="buy", pdno="005930", crdt_type="21",
            ...     ord_dvsn="00", ord_qty="1", ord_unpr="70000", loan_dt=today
            ... )

            >>> # 최유리지정가로 빠른 체결
            >>> result = agent.order_stock_credit(
            ...     ord_dv="buy", pdno="009470", crdt_type="21",
            ...     ord_dvsn="03", ord_qty="1", ord_unpr="0", loan_dt=today
            ... )
        """
        # ord_dv에 따라 적절한 신용주문 메서드 호출
        if ord_dv.lower() == "buy":
            return self.account_api.order_credit_buy(
                pdno=pdno,
                qty=int(ord_qty),
                price=int(ord_unpr),
                order_type=ord_dvsn,
                credit_type=crdt_type,
                exchange=excg_id_dvsn_cd,
            )
        else:
            return self.account_api.order_credit_sell(
                pdno=pdno,
                qty=int(ord_qty),
                price=int(ord_unpr),
                order_type=ord_dvsn,
                credit_type=crdt_type,
            )

    # ============================================================================
    # Rate Limiter 관리 메서드 (kis_agent.core.rate_limiter_mixin.RateLimiterControlMixin 상속)
    # ============================================================================

    # ============================================================================
    # 관심종목 관련 메서드
    # ============================================================================

    # ============================================================================
    # 업종코드 마스터 데이터 조회 (한투 서버에서 다운로드)
    # ============================================================================

    def get_sector_codes(
        self,
        as_dict: bool = False,
    ) -> pd.DataFrame | Dict[str, str]:
        """
        업종코드 마스터 데이터를 조회합니다.

        한국투자증권 서버에서 업종코드 MST 파일을 다운로드하고 파싱합니다.

        Args:
            as_dict (bool): True이면 {코드: 이름} Dict 반환, False면 DataFrame 반환

        Returns:
            pd.DataFrame | Dict[str, str]: 업종코드 데이터
                - DataFrame: columns = ['market_div', 'sector_code', 'full_code', 'sector_name']
                - Dict: {sector_code: sector_name}

        Example:
            >>> # DataFrame으로 조회
            >>> df = agent.get_sector_codes()
            >>> print(df.head())
               market_div sector_code full_code sector_name
            0           0        0001     00001          종합
            1           0        0002     00002         대형주
            ...

            >>> # Dict로 조회
            >>> codes = agent.get_sector_codes(as_dict=True)
            >>> print(codes['0001'])
            종합

        Note:
            - 시장구분 (market_div):
              - 0: 코스피
              - 1: 코스닥
              - 2: KOSPI200 관련
              - 3: KOSDAQ150 관련
              - 4: KRX 지수
              - 6, 7: 기타 지수
        """
        return get_sector_codes(as_dict=as_dict)

    def get_sector_code_by_market(
        self,
        market: str = "kospi",
    ) -> pd.DataFrame:
        """
        시장별 업종코드를 조회합니다.

        Args:
            market (str): 시장 구분
                - "kospi" 또는 "0": 코스피 업종
                - "kosdaq" 또는 "1": 코스닥 업종
                - "other" 또는 "2": 기타 지수 (KOSPI200 등)
                - "all": 전체

        Returns:
            pd.DataFrame: 해당 시장의 업종코드 DataFrame
                - columns = ['market_div', 'sector_code', 'full_code', 'sector_name']

        Example:
            >>> # 코스피 업종 조회
            >>> kospi_df = agent.get_sector_code_by_market("kospi")
            >>> print(kospi_df.head())

            >>> # 코스닥 업종 조회
            >>> kosdaq_df = agent.get_sector_code_by_market("kosdaq")

            >>> # 전체 조회
            >>> all_df = agent.get_sector_code_by_market("all")
        """
        return get_sector_code_by_market(market=market)

    @property
    def sector_codes_constants(self) -> Dict[str, str]:
        """
        주요 업종코드 상수를 반환합니다.

        자주 사용되는 업종코드를 상수로 제공합니다.

        Returns:
            Dict[str, str]: 업종코드 상수
                - KOSPI: 0001 (코스피 종합)
                - KOSPI_LARGE: 0002 (대형주)
                - KOSPI_MEDIUM: 0003 (중형주)
                - KOSPI_SMALL: 0004 (소형주)
                - KOSDAQ: 1001 (코스닥)
                - KOSDAQ_LARGE: 1002 (코스닥 대형주)
                - KOSDAQ_MEDIUM: 1003 (코스닥 중형주)
                - KOSDAQ_SMALL: 1004 (코스닥 소형주)
                - KOSPI200: 2001
                - KOSPI100: 2007
                - KOSPI50: 2008
                - KOSDAQ150: 3003 (KSQ150)
                - KRX100: 4001
                - KRX300: 4300

        Note:
            코스피 업종코드 (market_div=0):
                0001: 종합          0002: 대형주        0003: 중형주        0004: 소형주
                0005: 음식료·담배   0006: 섬유·의류     0007: 종이·목재     0008: 화학
                0009: 제약          0010: 비금속        0011: 금속          0012: 기계·장비
                0013: 전기·전자     0014: 의료·정밀기기 0015: 운송장비·부품 0016: 유통
                0017: 전기·가스     0018: 건설          0019: 운송·창고     0020: 통신
                0021: 금융          0024: 증권          0025: 보험          0026: 일반서비스
                0027: 제조          0028: 부동산        0029: IT 서비스     0030: 오락·문화
                0163: 고배당50      0164: 배당성장50    0165: 우선주        0195: 코스피 TR
                0241: 코스피 고배당 50 TR              0242: 코스피 배당성장 50 TR
                0244: 코스피200제외 코스피지수         0503: VKOSPI

            코스닥 업종코드 (market_div=1):
                1001: KOSDAQ        1002: 코스닥 대형주 1003: 코스닥 중형주 1004: 코스닥 소형주
                1006: 일반서비스    1009: 제조          1010: 건설          1011: 유통
                1013: 운송·창고     1014: 금융          1015: 오락·문화     1019: 음식료·담배
                1020: 섬유·의류     1021: 종이·목재     1022: 출판·매체복제 1023: 화학
                1024: 제약          1025: 비금속        1026: 금속          1027: 기계·장비
                1028: 전기·전자     1029: 의료·정밀기기 1030: 운송장비·부품 1031: 기타제조
                1032: 통신          1033: IT 서비스     1042: 우량기업      1043: 벤처기업
                1044: 중견기업      1045: 기술성장기업  1049: 코스닥 글로벌 1196: 코스닥 TR
                1331: 코스닥 150 거버넌스

        Example:
            >>> codes = agent.sector_codes_constants
            >>> print(codes["KOSPI"])  # '0001'
            >>> print(codes["KOSDAQ150"])  # '3003'
        """
        return SECTOR_CODES

    # ============================================================================
    # 하위 호환성을 위한 __getattr__ 메서드 (기존 코드와의 호환성)
    # ============================================================================

    def __getattr__(self, name: str):
        """API 모듈의 메서드를 위임 (하위 호환성)

        우선순위:
        1. StockAPI - 주식 관련 기본 API (최우선)
        2. StockMarketAPI - 시장 데이터 API
        3. AccountAPI / ProgramTradeAPI / StockInvestorAPI / InterestStockAPI

        `__init__`이 만드는 API 모듈은 전부 여기에 있어야 한다. 빠지면 그
        모듈의 메서드는 Agent를 통해 호출할 수 없고, 사용자에겐 "메서드가
        없다"로 보인다 (investor_api/interest_api가 실제로 그랬다).
        """
        # StockAPI를 최우선으로 확인 (메인 주식 API)
        if hasattr(self.stock_api, name):
            return getattr(self.stock_api, name)

        # StockMarketAPI 확인 (시장 데이터 관련 API)
        if hasattr(self.market_api, name):
            return getattr(self.market_api, name)

        # 나머지 API 모듈에서 메서드 찾기
        for api in (
            self.account_api,
            self.program_api,
            self.investor_api,
            self.interest_api,
        ):
            if hasattr(api, name):
                return getattr(api, name)

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


# Expose facade class for flat import
__all__ = ["Agent"]
