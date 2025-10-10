import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from ..account.api import AccountAPI
from ..program.trade import ProgramTradeAPI
from ..stock import StockMarketAPI
from ..stock.api import StockAPI
from ..stock.investor_api import StockInvestorAPI
from ..websocket.client import KisWebSocket
from .auth import auth, read_token
from .base_exception_handler import BaseExceptionHandler, exception_handler
from .client import KISClient
from .config import KISConfig
from .rate_limiter import RateLimiter


class Agent(BaseExceptionHandler):
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
        >>> from pykis import Agent
        >>> agent = Agent(
        ...     app_key="YOUR_APP_KEY",
        ...     app_secret="YOUR_APP_SECRET",
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
        >>> from pykis.utils.trading_report import generate_trading_report
        >>> report = generate_trading_report(agent.client, account_info, "20250101", "20250131")
    """

    # [변경 이유] 로거 미정의로 flake8 F821 경고 발생. 모듈 레벨 로거를 명시적으로 생성합니다.
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        account_no: str,
        account_code: str,
        base_url: str = "https://openapi.koreainvestment.com:9443",
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
            base_url (str): API 베이스 URL (기본값: 실전투자 URL)
                - 실전투자: "https://openapi.koreainvestment.com:9443"
                - 모의투자: "https://openapivts.koreainvestment.com:29443"
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
            ...     app_secret="YOUR_APP_SECRET",
            ...     account_no="12345678",
            ...     account_code="01"
            ... )
            >>>
            >>> # 모의투자 Agent 생성
            >>> agent = Agent(
            ...     app_key="YOUR_APP_KEY",
            ...     app_secret="YOUR_APP_SECRET",
            ...     account_no="12345678",
            ...     account_code="01",
            ...     base_url="https://openapivts.koreainvestment.com:29443"
            ... )
            >>>
            >>> # Rate Limiter 비활성화
            >>> agent = Agent(
            ...     app_key="YOUR_APP_KEY",
            ...     app_secret="YOUR_APP_SECRET",
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
        if not all([app_key, app_secret, account_no, account_code]):
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
                "      app_secret='YOUR_APP_SECRET',\n"
                "      account_no='12345678',\n"
                "      account_code='01'\n"
                "  )"
            )

        # Rate Limiter 설정
        if enable_rate_limiter:
            if rate_limiter:
                self.rate_limiter = rate_limiter
            else:
                # 기본값 또는 사용자 정의 설정 사용
                default_config = {
                    "requests_per_second": 10,  # 보수적 설정 (실제 제한보다 낮게)
                    "requests_per_minute": 500,  # 보수적 설정
                    "min_interval_ms": 100,  # 최소 100ms 간격
                    "burst_size": 5,  # 순간 처리량 제한
                    "enable_adaptive": True,
                }
                if rate_limiter_config:
                    default_config.update(rate_limiter_config)

                self.rate_limiter = RateLimiter(**default_config)
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

        # 클라이언트 초기화
        self.client = client or KISClient(
            config=config,
            enable_rate_limiter=enable_rate_limiter,
            rate_limiter=self.rate_limiter,
        )

        # 토큰 자동 검증 및 재발급
        self._ensure_valid_token(config)

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

    def _ensure_valid_token(self, config):
        """토큰 유효성 검증 및 자동 재발급"""
        try:
            # 기존 토큰 확인
            saved_token = read_token()

            if saved_token is None:
                # 토큰이 없거나 만료된 경우 새로 발급
                if not os.environ.get("PYKIS_SILENT"):
                    print(
                        "[Agent] 토큰이 없거나 만료되었습니다. 새 토큰을 발급받습니다."
                    )
                auth(config=config)
                if not os.environ.get("PYKIS_SILENT"):
                    print("[Agent] 토큰 발급이 완료되었습니다.")
            else:
                # 유효한 토큰이 있는 경우
                if not os.environ.get("PYKIS_SILENT"):
                    print("[Agent] 유효한 토큰이 확인되었습니다.")

        except Exception as e:
            # [변경 이유] 미정의 logger 사용 오류 수정 -> 클래스 로거 사용
            self.logger.error(f"[Agent] 토큰 검증/발급 중 오류 발생: {e}")
            # 토큰 발급 실패는 중요한 문제이므로 예외 재발생
            raise RuntimeError(f"토큰 자동 발급 실패: {e}")

    def _init_apis(self):
        """API 모듈들을 초기화합니다."""
        self.account_api = AccountAPI(self.client, self.account_info)
        self.stock_api = StockAPI(self.client, self.account_info)
        self.investor_api = StockInvestorAPI(self.client, self.account_info)
        self.program_api = ProgramTradeAPI(self.client, self.account_info)
        self.market_api = StockMarketAPI(self.client, self.account_info)

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

    def get_stock_price(self, code: str) -> Optional[Dict[str, Any]]:
        """
        주식 현재가 조회

        지정된 종목의 실시간 현재가와 시세 정보를 조회합니다.

        Args:
            code (str): 종목코드 (6자리, 예: "005930")

        Returns:
            Optional[Dict[str, Any]]: 현재가 시세 데이터
                - 성공 시: rt_cd와 함께 시세 정보 딕셔너리
                - 실패 시: None

        Example:
            >>> agent = Agent(env_path=".env")
            >>> result = agent.get_stock_price("005930")  # 삼성전자
            >>> if result and result.get('rt_cd') == '0':
            ...     price = result['output']['stck_prpr']
            ...     print(f"현재가: {price:,}원")
        """
        return self.stock_api.get_stock_price(code)

    def get_daily_price(
        self, code: str, period: str = "D", org_adj_prc: str = "1"
    ) -> Optional[Dict[str, Any]]:
        """
        일별 시세 조회 (Postman 검증된 방식)

        Args:
            code: 종목코드 (6자리)
            period: 기간구분 (D: 일, W: 주, M: 월, Y: 년)
            org_adj_prc: 수정주가구분 (0: 수정주가 미사용, 1: 수정주가 사용)
        """
        return self.stock_api.get_daily_price(code, period, org_adj_prc)

    def get_daily_credit_balance(
        self, code: str, date: str
    ) -> Optional[Dict[str, Any]]:
        """
        국내주식 신용잔고 일별추이 조회

        Args:
            code: 종목코드 (6자리, 예: "005930")
            date: 결제일자 (YYYYMMDD 형식, 예: "20240508")

        Returns:
            Dict: 신용잔고 일별추이 데이터 (성공 시), None (실패 시)
        """
        return self.stock_api.get_daily_credit_balance(code, date)

    def get_minute_price(
        self, code: str, hour: str = "153000"
    ) -> Optional[Dict[str, Any]]:
        """
        주식당일분봉조회 (Postman 검증된 방식)

        Args:
            code: 종목코드 (6자리)
            hour: 시간 (HHMMSS 형식, 기본값: 153000)
        """
        return self.stock_api.get_minute_price(code, hour)

    def get_daily_minute_price(
        self, code: str, date: str, hour: str = "153000"
    ) -> Optional[Dict[str, Any]]:
        """
        일별분봉시세조회 - 과거일자 분봉 데이터 조회

        Args:
            code (str): 종목코드 (6자리)
            date (str): 조회 날짜 (YYYYMMDD 형식)
            hour (str): 조회 시간 (HHMMSS 형식, 기본값: 153000)

        Returns:
            Dict: 일별분봉시세 데이터

        Note:
            - 실전계좌의 경우 한 번의 호출에 최대 120건까지 조회 가능
            - 과거 최대 1년까지의 분봉 데이터 조회 가능
            - 당사 서버에 보관된 데이터만 조회 가능
        """
        # [변경 이유] 한국투자증권 새로운 일별분봉시세조회 API 추가
        return self.stock_api.get_daily_minute_price(code, date, hour)

    def inquire_time_itemconclusion(
        self, code: str, hour: str = "153000", market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """
        주식현재가 당일시간대별체결 조회

        Args:
            code: 종목코드 (6자리)
            hour: 조회 시간 (HHMMSS, 기본값: 153000)
            market: 시장구분 (J:KRX, NX:NXT, UN:통합)

        Returns:
            시간대별 체결 데이터 (output1: 요약, output2: 시간별 체결 리스트)
        """
        return self.stock_api.inquire_time_itemconclusion(code, hour, market)

    def inquire_ccnl(
        self, code: str, market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """
        주식현재가 체결 조회 (최근 30건)

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT, UN:통합)

        Returns:
            최근 체결 데이터 (최대 30건)
        """
        return self.stock_api.inquire_ccnl(code, market)

    def inquire_price_2(
        self, code: str, market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """
        주식현재가 시세2 조회 (추가 정보 포함)

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT, UN:통합)

        Returns:
            주식현재가 시세2 데이터
        """
        return self.stock_api.inquire_price_2(code, market)

    def search_stock_info(
        self, code: str, product_type: str = "300"
    ) -> Optional[Dict[str, Any]]:
        """
        주식 기본정보 조회

        Args:
            code: 종목코드 (6자리, ETN의 경우 Q로 시작)
            product_type: 상품유형코드 (300:주식/ETF/ETN/ELW, 301:선물옵션, 302:채권, 306:ELS)

        Returns:
            주식 기본정보 (종목명, 업종, 상장일, 자본금 등)
        """
        return self.stock_api.search_stock_info(code, product_type)

    def news_title(
        self,
        code: str = "",
        news_provider: str = "2",
        market_cls: str = "00",
        title_content: str = "",
        date: str = "",
        hour: str = "000000",
        sort_code: str = "01",
        serial_no: str = "1",
    ) -> Optional[Dict[str, Any]]:
        """
        종합 시황/공시 뉴스 제목 조회

        Args:
            code: 종목코드 (공백: 전체)
            news_provider: 뉴스제공업체코드 (2:전체)
            market_cls: 시장구분코드 (00:전체)
            title_content: 제목내용 (검색어)
            date: 조회날짜 (YYYYMMDD, 공백: 당일)
            hour: 조회시간 (HHMMSS)
            sort_code: 정렬코드 (01:시간순)
            serial_no: 일련번호

        Returns:
            뉴스 제목 리스트
        """
        return self.stock_api.news_title(
            code, news_provider, market_cls, title_content, date, hour, sort_code, serial_no
        )

    def fluctuation(
        self,
        market: str = "J",
        screen_code: str = "20170",
        stock_code: str = "0000",
        sort_code: str = "0",
        count: str = "30",
        price_cls: str = "0",
        price_from: str = "",
        price_to: str = "",
        volume: str = "",
        target_cls: str = "0",
        exclude_cls: str = "0",
        div_cls: str = "0",
        rate_from: str = "",
        rate_to: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        등락률 순위 조회

        Args:
            market: 시장구분 (J:주식, W:ELW, Q:ETF)
            screen_code: 화면코드 (20170:등락률)
            stock_code: 종목코드 (0000:전체)
            sort_code: 정렬코드 (0:상승률순)
            count: 조회건수
            price_cls: 가격구분 (0:전체)
            price_from: 가격하한
            price_to: 가격상한
            volume: 거래량하한
            target_cls: 대상구분코드 (0:전체)
            exclude_cls: 제외구분코드 (0:없음)
            div_cls: 분류구분 (0:전체)
            rate_from: 등락률하한
            rate_to: 등락률상한

        Returns:
            등락률 순위 데이터
        """
        return self.stock_api.fluctuation(
            market, screen_code, stock_code, sort_code, count, price_cls,
            price_from, price_to, volume, target_cls, exclude_cls, div_cls,
            rate_from, rate_to
        )

    def volume_rank(
        self,
        market: str = "J",
        screen_code: str = "20171",
        stock_code: str = "0000",
        div_cls: str = "0",
        sort_cls: str = "0",
        target_cls: str = "111111111",
        exclude_cls: str = "0000000000",
        price_from: str = "",
        price_to: str = "",
        volume: str = "",
        date: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        거래량 순위 조회

        Args:
            market: 시장구분 (J:KRX, NX:NXT, UN:통합, W:ELW)
            screen_code: 화면코드 (20171:거래량)
            stock_code: 종목코드 (0000:전체)
            div_cls: 분류구분 (0:전체, 1:보통주, 2:우선주)
            sort_cls: 정렬구분 (0:평균거래량, 1:거래증가율, 2:평균거래회전율, 3:거래금액순, 4:평균거래금액회전율)
            target_cls: 대상구분코드 (9자리, 증거금비율)
            exclude_cls: 제외구분코드 (10자리, 투자위험/관리종목 등)
            price_from: 가격하한
            price_to: 가격상한
            volume: 거래량하한
            date: 조회날짜 (YYYYMMDD, 공백:당일)

        Returns:
            거래량 순위 데이터
        """
        return self.stock_api.volume_rank(
            market, screen_code, stock_code, div_cls, sort_cls, target_cls,
            exclude_cls, price_from, price_to, volume, date
        )

    def market_cap(
        self,
        market: str = "J",
        screen_code: str = "20174",
        stock_code: str = "0000",
        div_cls: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_from: str = "",
        price_to: str = "",
        volume: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        시가총액 순위 조회

        Args:
            market: 시장구분 (J:KRX, NX:NXT)
            screen_code: 화면코드 (20174:시가총액)
            stock_code: 종목코드 (0000:전체, 0001:거래소, 1001:코스닥, 2001:코스피200)
            div_cls: 분류구분 (0:전체, 1:보통주, 2:우선주)
            target_cls: 대상구분 (0:전체)
            exclude_cls: 제외구분 (0:전체)
            price_from: 가격하한
            price_to: 가격상한
            volume: 거래량하한

        Returns:
            시가총액 순위 데이터
        """
        return self.stock_api.market_cap(
            market, screen_code, stock_code, div_cls, target_cls, exclude_cls,
            price_from, price_to, volume
        )

    def inquire_daily_overtimeprice(
        self, code: str, market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """
        주식현재가 시간외 일자별주가 조회 (최근 30건)

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT, UN:통합)

        Returns:
            시간외 일자별주가 데이터 (output1: 요약, output2: 일자별 리스트)
        """
        return self.stock_api.inquire_daily_overtimeprice(code, market)

    def inquire_elw_price(self, code: str, market: str = "W") -> Optional[Dict[str, Any]]:
        """
        ELW 현재가 조회

        Args:
            code: ELW 종목코드
            market: 시장구분 (W:ELW)

        Returns:
            ELW 현재가 데이터
        """
        return self.stock_api.inquire_elw_price(code, market)

    def inquire_index_category_price(
        self,
        index_code: str,
        screen_code: str = "20214",
        market_cls: str = "K",
        belong_cls: str = "0",
        market: str = "U",
    ) -> Optional[Dict[str, Any]]:
        """
        국내업종 구분별 전체시세 조회

        Args:
            index_code: 업종코드 (0001:코스피, 1001:코스닥, 2001:코스피200)
            screen_code: 화면코드 (20214:고정값)
            market_cls: 시장구분코드 (K:거래소, Q:코스닥, K2:코스피200)
            belong_cls: 소속구분코드 (0:전업종, 1:기타구분, 2:자본금/벤처구분, 3:상업별/일반구분)
            market: 시장구분 (U:업종)

        Returns:
            업종별 전체시세 데이터 (output1: 요약, output2: 업종별 리스트)
        """
        return self.stock_api.inquire_index_category_price(
            index_code, screen_code, market_cls, belong_cls, market
        )

    def inquire_index_price(
        self, index_code: str, market: str = "U"
    ) -> Optional[Dict[str, Any]]:
        """
        국내업종 현재지수 조회

        Args:
            index_code: 업종코드 (0001:코스피, 1001:코스닥, 2001:코스피200)
            market: 시장구분 (U:업종)

        Returns:
            업종 현재지수 데이터
        """
        return self.stock_api.inquire_index_price(index_code, market)

    def inquire_index_tickprice(
        self, index_code: str, market: str = "U"
    ) -> Optional[Dict[str, Any]]:
        """
        국내업종 시간별지수(틱) 조회

        Args:
            index_code: 업종코드 (0001:거래소, 1001:코스닥, 2001:코스피200, 3003:KSQ150)
            market: 시장구분 (U:업종)

        Returns:
            시간별지수 틱 데이터
        """
        return self.stock_api.inquire_index_tickprice(index_code, market)

    def inquire_index_timeprice(
        self, index_code: str, market: str = "U", time_div: str = "0"
    ) -> Optional[Dict[str, Any]]:
        """
        국내업종 지수 분/일봉 시세 조회

        Args:
            index_code: 업종코드 (0001:코스피, 1001:코스닥, 2001:코스피200)
            market: 시장구분 (U:업종)
            time_div: 시간구분 (0:분봉, 1:일봉)

        Returns:
            지수 분/일봉 시세 데이터
        """
        return self.stock_api.inquire_index_timeprice(index_code, market, time_div)

    def inquire_overtime_asking_price(
        self, code: str, market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """
        국내주식 시간외호가 조회

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT)

        Returns:
            시간외호가 데이터
        """
        return self.stock_api.inquire_overtime_asking_price(code, market)

    def inquire_overtime_price(
        self, code: str, market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """
        국내주식 시간외현재가 조회

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT)

        Returns:
            시간외현재가 데이터
        """
        return self.stock_api.inquire_overtime_price(code, market)

    def disparity(
        self,
        market: str = "J",
        screen_code: str = "20178",
        div_cls: str = "0",
        sort_code: str = "0",
        hour_cls: str = "5",
        stock_code: str = "0000",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_from: str = "",
        volume: str = "",
        price_to: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        국내주식 이격도 순위 조회

        Args:
            market: 시장구분 (J:KRX, NX:NXT)
            screen_code: 화면코드 (20178:이격도)
            div_cls: 분류구분 (0:전체, 1:관리종목, 2:투자주의 등)
            sort_code: 정렬코드 (0:이격도상위순, 1:이격도하위순)
            hour_cls: 시간구분 (5:이격도5, 10:이격도10, 20:이격도20, 60:이격도60, 120:이격도120)
            stock_code: 종목코드 (0000:전체, 0001:거래소, 1001:코스닥, 2001:코스피200)
            target_cls: 대상구분 (0:전체)
            exclude_cls: 제외구분 (0:전체)
            price_from: 가격하한
            volume: 거래량하한
            price_to: 가격상한

        Returns:
            이격도 순위 데이터
        """
        return self.stock_api.disparity(
            market, screen_code, div_cls, sort_code, hour_cls, stock_code,
            target_cls, exclude_cls, price_from, volume, price_to
        )

    def dividend_rate(
        self,
        cts_area: str = " ",
        gb1: str = "1",
        upjong: str = "0001",
        gb2: str = "0",
        gb3: str = "1",
        f_dt: str = "",
        t_dt: str = "",
        gb4: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        국내주식 배당률 상위 조회

        Args:
            cts_area: 연속영역 (공백)
            gb1: 시장구분 (0:전체, 1:코스피, 2:코스피200, 3:코스닥)
            upjong: 업종구분 (0001:종합, 0002:대형주 등)
            gb2: 종목선택 (0:전체, 6:보통주, 7:우선주)
            gb3: 배당구분 (1:주식배당, 2:현금배당)
            f_dt: 기준일From (YYYYMMDD)
            t_dt: 기준일To (YYYYMMDD)
            gb4: 결산/중간배당 (0:전체, 1:결산배당, 2:중간배당)

        Returns:
            배당률 상위 데이터
        """
        return self.stock_api.dividend_rate(cts_area, gb1, upjong, gb2, gb3, f_dt, t_dt, gb4)

    def market_time(self) -> Optional[Dict[str, Any]]:
        """
        국내주식 시장영업시간 조회

        Returns:
            시장영업시간 데이터 (개장시간, 폐장시간, 휴장일 등)
        """
        return self.stock_api.market_time()

    def market_value(self, code: str, market: str = "J") -> Optional[Dict[str, Any]]:
        """
        국내주식 종목별 시가총액 조회

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT)

        Returns:
            종목별 시가총액 데이터
        """
        return self.stock_api.market_value(code, market)

    def profit_asset_index(
        self, index_code: str = "0001", market: str = "U"
    ) -> Optional[Dict[str, Any]]:
        """
        국내주식 자산/수익지수 조회

        Args:
            index_code: 지수코드 (0001:코스피, 1001:코스닥)
            market: 시장구분 (U:업종)

        Returns:
            자산/수익지수 데이터
        """
        return self.stock_api.profit_asset_index(index_code, market)

    def intstock_multprice(self, codes: str, market: str = "J") -> Optional[Dict[str, Any]]:
        """
        국내주식 복수종목 현재가 조회

        Args:
            codes: 종목코드 (복수 종목은 ','로 구분, 최대 50종목)
            market: 시장구분 (J:KRX, NX:NXT)

        Returns:
            복수종목 현재가 데이터
        """
        return self.stock_api.intstock_multprice(codes, market)

    def get_member(self, code: str) -> Optional[Dict[str, Any]]:
        """
        거래원별 매매 현황 조회

        특정 종목의 거래원별 매수/매도 현황을 조회합니다.

        Args:
            code (str): 종목코드 (6자리, 예: "005930")

        Returns:
            Optional[Dict[str, Any]]: 거래원별 매매 현황 데이터
                - 성공 시: rt_cd와 함께 거래원 정보 딕셔너리
                - 실패 시: None

        Example:
            >>> agent = Agent(env_path=".env")
            >>> result = agent.get_member("005930")
            >>> if result and result.get('rt_cd') == '0':
            ...     for member in result['output']:
            ...         print(f"거래원: {member['mbcr_name']}")
        """
        return self.stock_api.get_member(code)

    def get_foreign_broker_net_buy(
        self, code: str, foreign_brokers=None, date: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        외국계 증권사 순매수 현황 조회

        특정 종목에 대한 외국계 증권사들의 순매수 거래량을 조회합니다.

        Args:
            code (str): 종목코드 (6자리, 예: "005930")
            foreign_brokers (list, optional): 외국계 증권사 목록. None이면 기본 목록 사용.
            date (str, optional): 조회 날짜 (YYYYMMDD). None이면 당일.

        Returns:
            Optional[Dict[str, Any]]: 외국계 순매수 현황 데이터
                - 성공 시: 외국계 증권사별 순매수량 정보
                - 실패 시: None

        Example:
            >>> agent = Agent(env_path=".env")
            >>> result = agent.get_foreign_broker_net_buy("005930")
            >>> if result:
            ...     print(f"외국계 순매수량: {result['net_buy_volume']:,}주")
        """
        return self.stock_api.get_foreign_broker_net_buy(code, foreign_brokers, date)

    def get_program_trade_by_stock(self, code: str) -> Optional[Dict[str, Any]]:
        """
        종목별 프로그램매매 추이 조회

        특정 종목의 프로그램매매 체결 현황을 조회합니다.

        Args:
            code (str): 종목코드 (6자리, 예: "005930")

        Returns:
            Optional[Dict[str, Any]]: 프로그램매매 추이 데이터
                - 성공 시: rt_cd와 함께 프로그램매매 정보 딕셔너리
                - 실패 시: None

        Example:
            >>> agent = Agent(env_path=".env")
            >>> result = agent.get_program_trade_by_stock("005930")
            >>> if result and result.get('rt_cd') == '0':
            ...     print(f"프로그램매매 순매수량: {result['output']['pgtr_ntby_qty']}")
        """
        return self.program_api.get_program_trade_by_stock(code)

    def get_member_transaction(
        self, code: str, mem_code: str = "99999"
    ) -> Optional[Dict[str, Any]]:
        """
        회원사별 매매 정보 조회

        특정 종목의 회원사별 매수/매도 거래 정보를 조회합니다.

        Args:
            code (str): 종목코드 (6자리, 예: "005930")
            mem_code (str, optional): 회원사 코드. Defaults to "99999" (전체).

        Returns:
            Optional[Dict[str, Any]]: 회원사별 매매 정보 데이터
                - 성공 시: rt_cd와 함께 회원사 매매 정보 딕셔너리
                - 실패 시: None

        Example:
            >>> agent = Agent(env_path=".env")
            >>> result = agent.get_member_transaction("005930")
            >>> if result and result.get('rt_cd') == '0':
            ...     for member in result['output']:
            ...         print(f"회원사: {member['brkr_name']}")
        """
        return self.stock_api.get_member_transaction(code, mem_code)

    def get_volume_power(self, volume: int = 0) -> Optional[Dict[str, Any]]:
        """
        체결강도 순위 조회

        체결강도가 높은 종목들의 순위를 조회합니다.

        Args:
            volume (int, optional): 최소 거래량 조건. Defaults to 0.

        Returns:
            Optional[Dict[str, Any]]: 체결강도 순위 데이터
                - 성공 시: rt_cd와 함께 체결강도 순위 정보 딕셔너리
                - 실패 시: None

        Example:
            >>> agent = Agent(env_path=".env")
            >>> result = agent.get_volume_power(volume=1000000)  # 100만주 이상
            >>> if result and result.get('rt_cd') == '0':
            ...     for stock in result['output']:
            ...         print(f"종목: {stock['hts_kor_isnm']}, 체결강도: {stock['cttr_pwr']}")
        """
        return self.stock_api.get_volume_power(volume)

    def get_index_daily_price(
        self, index_code: str = "0001", end_date: str = None, period: str = "D"
    ) -> Optional[Dict[str, Any]]:
        """
        국내 지수 일자별 시세 조회

        Args:
            index_code (str): 지수코드 (0001:KOSPI, 1001:KOSDAQ, 2001:KOSPI200)
            end_date (str): 조회 종료일 (YYYYMMDD), None이면 오늘
            period (str): 기간 구분 (D:일별, W:주별, M:월별)

        Returns:
            Dict: 지수 일별 시세 데이터
        """
        return self.stock_api.get_index_daily_price(index_code, end_date, period)

    def get_orderbook_raw(self, code: str) -> Optional[Dict[str, Any]]:
        """
        주식 호가 조회 (원시 데이터)

        Args:
            code (str): 종목코드 (6자리)

        Returns:
            Dict: 호가 원시 데이터
        """
        return self.stock_api.get_orderbook_raw(code)

    def get_stock_member(self, code: str) -> Optional[Dict[str, Any]]:
        """
        주식 회원사(거래원) 정보 조회

        Args:
            code (str): 종목코드 (6자리)

        Returns:
            Dict: 회원사 매매 정보
        """
        return self.stock_api.get_stock_member(code)

    def get_stock_investor(self, code: str) -> Optional[Dict[str, Any]]:
        """
        주식 투자자별 매매동향 조회 (원시 데이터)

        Args:
            code (str): 종목코드 (6자리)

        Returns:
            Dict: 투자자별 매매 원시 데이터
        """
        return self.stock_api.get_stock_investor(code)

    def get_frgnmem_trade_estimate(
        self,
        fid_cond_mrkt_div_code: str = "J",
        fid_cond_scr_div_code: str = "16441",
        fid_input_iscd: str = "0000",
        fid_rank_sort_cls_code: str = "0",
        fid_rank_sort_cls_code_2: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        외국계 매매종목 가집계 조회

        Args:
            fid_cond_mrkt_div_code: 조건시장분류코드 (J: 주식)
            fid_cond_scr_div_code: 조건화면분류코드 (16441: 기본)
            fid_input_iscd: 입력종목코드 (0000: 전체, 1001: 코스피, 2001: 코스닥)
            fid_rank_sort_cls_code: 순위정렬구분코드 (0: 금액순, 1: 수량순)
            fid_rank_sort_cls_code_2: 순위정렬구분코드2 (0: 매수순, 1: 매도순)

        Returns:
            Optional[Dict[str, Any]]: 외국계 매매종목 가집계 데이터
        """
        return self.investor_api.get_frgnmem_trade_estimate(
            fid_cond_mrkt_div_code,
            fid_cond_scr_div_code,
            fid_input_iscd,
            fid_rank_sort_cls_code,
            fid_rank_sort_cls_code_2,
        )

    def get_frgnmem_trade_trend(
        self,
        fid_cond_scr_div_code: str = "20432",
        fid_cond_mrkt_div_code: str = "J",
        fid_input_iscd: str = "",
        fid_input_iscd_2: str = "99999",
        fid_mrkt_cls_code: str = "A",
        fid_vol_cnt: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        회원사 실시간 매매동향(틱) 조회

        Args:
            fid_cond_scr_div_code: 조건화면분류코드 (20432)
            fid_cond_mrkt_div_code: 조건시장분류코드 (J 고정)
            fid_input_iscd: 종목코드 (예: 005930)
            fid_input_iscd_2: 회원사코드 (99999: 전체)
            fid_mrkt_cls_code: 시장구분코드 (A: 전체, K: 코스피, Q: 코스닥)
            fid_vol_cnt: 거래량

        Returns:
            Optional[Dict[str, Any]]: 회원사 실시간 매매동향 데이터
        """
        return self.investor_api.get_frgnmem_trade_trend(
            fid_cond_scr_div_code,
            fid_cond_mrkt_div_code,
            fid_input_iscd,
            fid_input_iscd_2,
            fid_mrkt_cls_code,
            fid_vol_cnt,
        )

    def get_investor_program_trade_today(
        self, mrkt_div_cls_code: str = "1"
    ) -> Optional[Dict[str, Any]]:
        """
        프로그램매매 투자자매매동향(당일) 조회

        Args:
            mrkt_div_cls_code: 시장구분코드 (1: 코스피, 4: 코스닥)

        Returns:
            Optional[Dict[str, Any]]: 프로그램매매 투자자매매동향 데이터
        """
        return self.investor_api.get_investor_program_trade_today(mrkt_div_cls_code)

    def get_investor_trade_by_stock_daily(
        self,
        fid_cond_mrkt_div_code: str = "J",
        fid_input_iscd: str = "",
        fid_input_date_1: str = "",
        fid_org_adj_prc: str = "",
        fid_etc_cls_code: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        종목별 투자자매매동향(일별) 조회

        Args:
            fid_cond_mrkt_div_code: 조건시장분류코드 (J: KRX, NX: NXT, UN: 통합)
            fid_input_iscd: 종목코드 (6자리)
            fid_input_date_1: 조회날짜 (YYYYMMDD)
            fid_org_adj_prc: 수정주가원주가가격 (공란)
            fid_etc_cls_code: 기타구분코드 (공란)

        Returns:
            Optional[Dict[str, Any]]: 종목별 투자자매매동향 데이터
        """
        return self.investor_api.get_investor_trade_by_stock_daily(
            fid_cond_mrkt_div_code,
            fid_input_iscd,
            fid_input_date_1,
            fid_org_adj_prc,
            fid_etc_cls_code,
        )

    def get_investor_trend_estimate(
        self, mksc_shrn_iscd: str
    ) -> Optional[Dict[str, Any]]:
        """
        종목별 외국인/기관 추정가집계 조회

        장중에 증권사 직원이 집계한 외국인/기관 매매 추정치를 조회합니다.
        입력시간: 외국인 09:30, 11:20, 13:20, 14:30 / 기관종합 10:00, 11:20, 13:20, 14:30

        Args:
            mksc_shrn_iscd: 종목코드 (6자리)

        Returns:
            Optional[Dict[str, Any]]: 종목별 외국인/기관 추정가집계 데이터
        """
        return self.investor_api.get_investor_trend_estimate(mksc_shrn_iscd)

    def foreign_institution_total(
        self,
        market: str = "J",
        screen_code: str = "20449",
        stock_code: str = "0000",
        div_cls: str = "0",
        sort_cls: str = "0",
        etc_cls: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        외국인/기관 종합 매매동향 조회

        Args:
            market: 시장구분 (J:KRX, NX:NXT)
            screen_code: 화면코드 (20449:외국인/기관종합)
            stock_code: 종목코드 (0000:전체)
            div_cls: 분류구분 (0:전체, 1:보통주, 2:우선주)
            sort_cls: 정렬구분 (0:순매수상위, 1:순매도상위)
            etc_cls: 기타구분 (0:전체, 1:외국인, 2:기관계, 3:기타)

        Returns:
            Optional[Dict[str, Any]]: 외국인/기관 종합 매매동향 데이터
        """
        return self.stock_api.foreign_institution_total(
            market, screen_code, stock_code, div_cls, sort_cls, etc_cls
        )

    def daily_credit_balance(
        self, code: str, market: str = "J", screen_code: str = "20476", date: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        신용잔고 일별추이 조회

        Args:
            code: 종목코드 (6자리)
            market: 시장구분 (J:KRX, NX:NXT)
            screen_code: 화면코드 (20476:신용잔고)
            date: 조회날짜 (YYYYMMDD, 공백:당일)

        Returns:
            Optional[Dict[str, Any]]: 신용잔고 일별추이 데이터
        """
        return self.stock_api.daily_credit_balance(code, market, screen_code, date)

    def short_sale(
        self,
        market: str = "J",
        screen_code: str = "20482",
        stock_code: str = "0000",
        period: str = "0",
        count: str = "30",
        exclude_cls: str = "0",
        target_cls: str = "0",
        volume: str = "",
        price_from: str = "",
        price_to: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        공매도 상위종목 조회

        Args:
            market: 시장구분 (J:KRX, NX:NXT)
            screen_code: 화면코드 (20482:공매도)
            stock_code: 종목코드 (0000:전체)
            period: 조회구분 (0:일, 1:월)
            count: 조회일수/월수
            exclude_cls: 제외구분 (0:없음)
            target_cls: 대상구분 (0:전체)
            volume: 거래량하한
            price_from: 가격하한
            price_to: 가격상한

        Returns:
            Optional[Dict[str, Any]]: 공매도 상위종목 데이터
        """
        return self.stock_api.short_sale(
            market,
            screen_code,
            stock_code,
            period,
            count,
            exclude_cls,
            target_cls,
            volume,
            price_from,
            price_to,
        )

    def inquire_vi_status(
        self,
        div_cls: str = "0",
        screen_code: str = "20139",
        market: str = "0",
        stock_code: str = "",
        sort_cls: str = "0",
        date: str = "",
        target_cls: str = "0",
        exclude_cls: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        VI(변동성완화장치) 발동 현황 조회

        Args:
            div_cls: 분류구분 (0:전체, 1:정적, 2:동적)
            screen_code: 화면코드 (20139:VI발동현황)
            market: 시장구분 (0:전체, 1:KOSPI, 2:KOSDAQ)
            stock_code: 종목코드 (공백:전체)
            sort_cls: 정렬구분 (0:VI발동시간순)
            date: 조회날짜 (YYYYMMDD, 공백:당일)
            target_cls: 대상구분 (0:전체)
            exclude_cls: 제외구분 (0:없음)

        Returns:
            Optional[Dict[str, Any]]: VI 발동 현황 데이터
        """
        return self.stock_api.inquire_vi_status(
            div_cls,
            screen_code,
            market,
            stock_code,
            sort_cls,
            date,
            target_cls,
            exclude_cls,
        )

    # ============================================================================
    # 계좌 관련 메서드들 (AccountAPI 위임)
    # ============================================================================

    def get_account_balance(self) -> Optional[Dict[str, Any]]:
        """
        계좌 잔고 조회

        현재 계좌의 보유 종목, 평가손익, 총 자산 등의 잔고 정보를 조회합니다.

        Returns:
            Optional[Dict[str, Any]]: 계좌 잔고 정보 데이터
                - 성공 시: rt_cd와 함께 잔고 정보 딕셔너리
                - 실패 시: None

        Example:
            >>> agent = Agent(env_path=".env")
            >>> result = agent.get_account_balance()
            >>> if result and result.get('rt_cd') == '0':
            ...     total_asset = result['output2'][0]['tot_evlu_amt']
            ...     print(f"총 평가금액: {total_asset:,}원")
        """
        return self.account_api.get_account_balance()

    def get_possible_order_amount(
        self, code: str, price: str, order_type: str = "01"
    ) -> Optional[Dict[str, Any]]:
        """
        주문 가능 금액 조회

        특정 종목에 대한 매수/매도 가능 금액을 조회합니다.

        Args:
            code (str): 종목코드 (6자리, 예: "005930")
            price (str): 주문 단가
            order_type (str, optional): 주문 구분. Defaults to "01" (매수).

        Returns:
            Optional[Dict[str, Any]]: 주문 가능 금액 정보 데이터
                - 성공 시: rt_cd와 함께 주문 가능 정보 딕셔너리
                - 실패 시: None

        Example:
            >>> agent = Agent(env_path=".env")
            >>> result = agent.get_possible_order_amount("005930", "70000", "01")
            >>> if result and result.get('rt_cd') == '0':
            ...     max_qty = result['output']['ord_psbl_qty']
            ...     print(f"주문 가능 수량: {max_qty:,}주")
        """
        return self.stock_api.get_possible_order(code, price, order_type)

    def get_account_order_quantity(self, code: str) -> Optional[Dict[str, Any]]:
        """
        계좌별 주문 수량 조회

        특정 종목에 대한 계좌별 주문 가능 수량을 조회합니다.

        Args:
            code (str): 종목코드 (6자리, 예: "005930")

        Returns:
            Optional[Dict[str, Any]]: 계좌별 주문 수량 정보 데이터
                - 성공 시: rt_cd와 함께 주문 수량 정보 딕셔너리
                - 실패 시: None

        Example:
            >>> agent = Agent(env_path=".env")
            >>> result = agent.get_account_order_quantity("005930")
            >>> if result and result.get('rt_cd') == '0':
            ...     available_qty = result['output']['ord_psbl_qty']
            ...     print(f"주문 가능 수량: {available_qty:,}주")
        """
        return self.account_api.get_account_order_quantity(code)

    # ============================================================================
    # 프로그램 매매 관련 메서드들 (ProgramTradeAPI 위임)
    # ============================================================================

    def get_program_trade_hourly_trend(self, code: str) -> Optional[Dict[str, Any]]:
        """
        시간별 프로그램 매매 추이 조회

        특정 종목의 시간대별 프로그램 매매 동향을 조회합니다.

        Args:
            code (str): 종목코드 (6자리, 예: "005930")

        Returns:
            Optional[Dict[str, Any]]: 시간별 프로그램 매매 추이 데이터
        """
        return self.program_api.get_program_trade_hourly_trend(code)

    def get_program_trade_daily_summary(
        self, code: str, date_str: str
    ) -> Optional[Dict[str, Any]]:
        """
        종목별 일별 프로그램 매매 집계 조회

        특정 날짜의 특정 종목 프로그램 매매 집계를 조회합니다.

        Args:
            code (str): 종목코드 (6자리, 예: "005930")
            date_str (str): 조회 날짜 (YYYYMMDD 형식)

        Returns:
            Optional[Dict[str, Any]]: 일별 프로그램 매매 집계 데이터
        """
        return self.program_api.get_program_trade_daily_summary(code, date_str)

    def get_program_trade_period_detail(
        self, start_date: str, end_date: str
    ) -> Optional[Dict[str, Any]]:
        """
        기간별 프로그램 매매 상세 조회

        지정된 기간 동안의 프로그램 매매 상세 내역을 조회합니다.

        Args:
            start_date (str): 시작 날짜 (YYYYMMDD 형식)
            end_date (str): 종료 날짜 (YYYYMMDD 형식)

        Returns:
            Optional[Dict[str, Any]]: 기간별 프로그램 매매 상세 데이터
        """
        return self.program_api.get_program_trade_period_detail(start_date, end_date)

    def get_program_trade_market_daily(
        self, start_date: str, end_date: str
    ) -> Optional[Dict[str, Any]]:
        """
        시장 전체 프로그램 매매 종합현황 조회

        지정된 기간의 시장 전체 프로그램 매매 현황을 조회합니다.

        Args:
            start_date (str): 시작 날짜 (YYYYMMDD 형식)
            end_date (str): 종료 날짜 (YYYYMMDD 형식)

        Returns:
            Optional[Dict[str, Any]]: 시장 전체 프로그램 매매 현황 데이터
        """
        return self.program_api.get_program_trade_market_daily(start_date, end_date)

    # ============================================================================
    # 기타 유틸리티 메서드들
    # ============================================================================

    def get_all_methods(
        self, show_details: bool = False, category: str = None
    ) -> Dict[str, Any]:
        """
        Agent에서 사용 가능한 모든 메서드를 카테고리별로 정리하여 반환합니다.

        Args:
            show_details (bool): 각 메서드의 상세 설명 포함 여부 (기본값: False)
            category (str): 특정 카테고리만 보기 (기본값: None - 전체)
                가능한 값: 'stock', 'account', 'program', 'market', 'utility',
                'websocket'

        Returns:
            dict: 메서드 정보가 담긴 딕셔너리

        Example:
            >>> agent = Agent()
            >>> methods = agent.get_all_methods()
            >>> print(f"총 {len(sum(methods.values(), []))}개 메서드 사용 가능")
            >>>
            >>> # 주식 관련 메서드만 보기
            >>> stock_methods = agent.get_all_methods(category='stock')
            >>>
            >>> # 상세 설명 포함
            >>> detailed = agent.get_all_methods(show_details=True)
        """

        # 메서드 카테고리별 분류
        methods_info = {
            "stock": {
                "title": " 주식 시세 관련",
                "methods": [
                    ("get_stock_price", "현재가 조회", 'get_stock_price("005930")'),
                    (
                        "get_daily_price",
                        "일별/주별/월별 시세 조회",
                        'get_daily_price("005930", period="D")',
                    ),
                    (
                        "get_minute_price",
                        "분봉 시세 조회",
                        'get_minute_price("005930", hour="153000")',
                    ),
                    (
                        "get_daily_minute_price",
                        "일별분봉시세조회",
                        'get_daily_minute_price("005930", "20250715", "153000")',
                    ),
                    ("get_orderbook", "호가 정보 조회", 'get_orderbook("005930")'),
                    (
                        "get_stock_investor",
                        "투자자별 매매 동향",
                        'get_stock_investor("005930")',
                    ),
                    ("get_stock_info", "종목 기본 정보", 'get_stock_info("005930")'),
                    (
                        "get_stock_financial",
                        "종목 재무 정보",
                        'get_stock_financial("005930")',
                    ),
                    ("get_stock_basic", "종목 기초 정보", 'get_stock_basic("005930")'),
                    (
                        "get_foreign_broker_net_buy",
                        "외국계 브로커 순매수",
                        'get_foreign_broker_net_buy("005930")',
                    ),
                    ("get_member", "거래원 정보 조회", 'get_member("005930")'),
                    (
                        "get_member_transaction",
                        "회원사 매매 정보",
                        'get_member_transaction("005930")',
                    ),
                ],
            },
            "market": {
                "title": " 시장 정보 관련",
                "methods": [
                    ("get_volume_power", "체결강도 순위", "get_volume_power(0)"),
                    ("get_top_gainers", "상위 상승주", "get_top_gainers()"),
                    (
                        "get_market_fluctuation",
                        "시장 등락 현황",
                        "get_market_fluctuation()",
                    ),
                    (
                        "get_market_rankings",
                        "시장 순위 정보",
                        "get_market_rankings(volume=5000000)",
                    ),
                    ("get_kospi200_index", "KOSPI200 지수", "get_kospi200_index()"),
                    ("get_futures_price", "선물 시세", 'get_futures_price("101S12")'),
                    (
                        "get_future_option_price",
                        "선물옵션 시세",
                        "get_future_option_price()",
                    ),
                    (
                        "get_daily_index_chart_price",
                        "지수 차트",
                        'get_daily_index_chart_price("0001", "D")',
                    ),
                ],
            },
            "account": {
                "title": " 계좌 관련",
                "methods": [
                    ("get_account_balance", "계좌 잔고 조회", "get_account_balance()"),
                    (
                        "get_cash_available",
                        "매수 가능 금액",
                        'get_cash_available("005930")',
                    ),
                    ("get_total_asset", "계좌 총 자산", "get_total_asset()"),
                    (
                        "get_possible_order_amount",
                        "주문 가능 금액",
                        'get_possible_order_amount("005930", "60000")',
                    ),
                    (
                        "get_account_order_quantity",
                        "계좌별 주문 수량",
                        'get_account_order_quantity("005930")',
                    ),
                ],
            },
            "program": {
                "title": "프로그램 매매 관련",
                "methods": [
                    (
                        "get_program_trade_by_stock",
                        "종목별 프로그램매매 추이",
                        'get_program_trade_by_stock("005930")',
                    ),
                    (
                        "get_program_trade_hourly_trend",
                        "시간별 프로그램매매 추이",
                        'get_program_trade_hourly_trend("005930")',
                    ),
                    (
                        "get_program_trade_daily_summary",
                        "일별 프로그램매매 집계",
                        'get_program_trade_daily_summary("005930", "20250107")',
                    ),
                    (
                        "get_program_trade_period_detail",
                        "기간별 프로그램매매 상세",
                        'get_program_trade_period_detail("20250101", "20250107")',
                    ),
                    (
                        "get_program_trade_market_daily",
                        "시장 전체 프로그램매매",
                        'get_program_trade_market_daily("20250101", "20250107")',
                    ),
                ],
            },
            "utility": {
                "title": " 유틸리티",
                "methods": [
                    ("get_holiday_info", "휴장일 정보", "get_holiday_info()"),
                    ("is_holiday", "휴장일 여부 확인", 'is_holiday("20250107")'),
                    (
                        "fetch_minute_data",
                        "분봉 데이터 수집",
                        'fetch_minute_data("005930", "20250107")',
                    ),
                    (
                        "calculate_support_resistance",
                        "매물대 분석",
                        'calculate_support_resistance("005930")',
                    ),
                    ("get_condition_stocks", "조건검색 종목", "get_condition_stocks()"),
                    (
                        "init_minute_db",
                        "SQLite DB 초기화",
                        'init_minute_db("my_data.db")',
                    ),
                    (
                        "migrate_minute_csv_to_db",
                        "CSV→DB 마이그레이션",
                        'migrate_minute_csv_to_db("005930")',
                    ),
                    (
                        "classify_broker",
                        "거래원 성격 분류",
                        'classify_broker("모간스탠리")',
                    ),
                ],
            },
            "websocket": {
                "title": " 실시간 웹소켓",
                "methods": [
                    (
                        "websocket",
                        "실시간 웹소켓 클라이언트",
                        'websocket(["005930"], enable_index=True)',
                    ),
                ],
            },
        }

        # 특정 카테고리만 요청된 경우
        if category:
            if category not in methods_info:
                available_categories = list(methods_info.keys())
                return {
                    "error": f"유효하지 않은 카테고리: {category}",
                    "available_categories": available_categories,
                }
            methods_info = {category: methods_info[category]}

        # 결과 정리
        result = {}
        total_methods = 0

        for cat_key, cat_info in methods_info.items():
            if show_details:
                # 상세 정보 포함
                result[cat_key] = {
                    "title": cat_info["title"],
                    "count": len(cat_info["methods"]),
                    "methods": [
                        {
                            "name": method[0],
                            "description": method[1],
                            "example": method[2],
                        }
                        for method in cat_info["methods"]
                    ],
                }
            else:
                # 간단한 정보만
                result[cat_key] = {
                    "title": cat_info["title"],
                    "count": len(cat_info["methods"]),
                    "methods": [method[0] for method in cat_info["methods"]],
                }

            total_methods += len(cat_info["methods"])

        # 요약 정보 추가
        result["_summary"] = {
            "total_methods": total_methods,
            "total_categories": len(result) - 1,  # _summary 제외
            "usage_tip": (
                'agent.get_all_methods(show_details=True, category="stock") '
                "형태로 상세 정보를 확인할 수 있습니다."
            ),
        }

        return result

    def search_methods(self, keyword: str) -> List[Dict[str, Any]]:
        """
        키워드로 메서드를 검색합니다.

        Args:
            keyword (str): 검색할 키워드 (메서드명이나 설명에서 검색)

        Returns:
            list: 매칭되는 메서드 정보 리스트

        Example:
            >>> agent = Agent()
            >>> # "price"라는 키워드로 검색
            >>> results = agent.search_methods("price")
            >>> for method in results:
            ...     print(f"{method['name']}: {method['description']}")
        """
        all_methods = self.get_all_methods(show_details=True)
        results = []
        keyword_lower = keyword.lower()

        for category_key, category_info in all_methods.items():
            if category_key == "_summary":
                continue

            for method in category_info["methods"]:
                # 메서드명이나 설명에서 키워드 검색
                if (
                    keyword_lower in method["name"].lower()
                    or keyword_lower in method["description"].lower()
                ):
                    results.append(
                        {
                            "name": method["name"],
                            "description": method["description"],
                            "example": method["example"],
                            "category": category_info["title"],
                        }
                    )

        return results

    def show_method_usage(self, method_name: str) -> None:
        """
        특정 메서드의 사용법을 출력합니다.

        Args:
            method_name (str): 확인할 메서드명

        Example:
            >>> agent = Agent()
            >>> agent.show_method_usage("get_stock_price")
        """
        all_methods = self.get_all_methods(show_details=True)

        for category_key, category_info in all_methods.items():
            if category_key == "_summary":
                continue

            for method in category_info["methods"]:
                if method["name"] == method_name:
                    print(f" 메서드: {method['name']}")
                    print(f" 설명: {method['description']}")
                    print(f" 카테고리: {category_info['title']}")
                    print(f" 사용 예시: agent.{method['example']}")

                    # 실제 메서드가 있는지 확인하고 docstring 출력
                    if hasattr(self, method_name):
                        actual_method = getattr(self, method_name)
                        if hasattr(actual_method, "__doc__") and actual_method.__doc__:
                            print(" 상세 문서:")
                            print(f"    {actual_method.__doc__.strip()}")
                    return

        print(f" '{method_name}' 메서드를 찾을 수 없습니다.")
        print(" 사용 가능한 메서드 확인: agent.get_all_methods()")

    @staticmethod
    def classify_broker(name: str) -> str:
        """간단한 거래원 성격 분류기: 외국계 / 리테일 / 기관"""
        # Guard clause: if name is not a string, return "N/A"
        if not isinstance(name, str):
            return "N/A"
        foreign_brokers = [
            "모간",
            "CS",
            "맥쿼리",
            "골드만",
            "바클레이",
            "노무라",
            "UBS",
            "BOA",
            "BNP",
        ]
        retail_brokers = ["키움", "NH투자", "미래에셋", "삼성증권", "신한증권"]
        name = name.upper()

        if any(fb.upper() in name for fb in foreign_brokers):
            return "외국계"
        elif any(rb.upper() in name for rb in retail_brokers):
            return "리테일/국내기관"
        else:
            return "기타"

    @exception_handler(
        message="휴장일 정보 조회 실패", reraise=False, default_return=None
    )
    def get_holiday_info(self) -> Optional[Dict[str, Any]]:
        """휴장일 정보를 조회합니다.

        Returns:
            Dict: 휴장일 정보, 실패 시 None
        """
        return self.stock_api.get_holiday_info()

    @exception_handler(message="휴장일 확인 실패", reraise=False, default_return=None)
    def is_holiday(self, date: str) -> Optional[bool]:
        """주어진 날짜(YYYYMMDD)가 한국 주식 시장 휴장일인지 확인합니다.

        Args:
            date: YYYYMMDD 형식의 날짜 문자열

        Returns:
            bool: 휴장일이면 True, 거래일이면 False, 확인 불가면 None
        """
        return self.stock_api.is_holiday(date)

    def init_minute_db(self, db_path: str = "db/stonks_candles.db") -> bool:
        """분봉 데이터용 DB 및 테이블 생성 (최초 1회)"""
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS minute_data (
                    code TEXT,
                    date TEXT,
                    tm TEXT,
                    stck_cntg_hour TEXT,
                    stck_prpr REAL,
                    stck_oprc REAL,
                    stck_hgpr REAL,
                    stck_lwpr REAL,
                    cntg_vol INTEGER,
                    acml_tr_pbmn REAL,
                    stck_bsop_date TEXT,
                    PRIMARY KEY (code, date, stck_cntg_hour)
                )
            """
            )
            conn.close()
            return True
        except Exception as e:
            logging.error(f"분봉 DB 초기화 실패: {e}")
            return False

    def migrate_minute_csv_to_db(
        self, code: str, db_path: str = "db/stonks_candles.db"
    ) -> bool:
        """기존 csv 분봉 데이터를 DB로 이관 (한 번만)"""
        cache_dir = "cache"
        csv_file_path = os.path.join(cache_dir, f"{code}_minute_data.csv")
        if not os.path.exists(csv_file_path):
            logging.info(f"CSV 파일이 존재하지 않음: {csv_file_path}")
            return True  # 파일이 없는 것은 오류가 아님
        try:
            import pandas as pd  # 지역 import로 로딩 시간 단축

            df = pd.read_csv(csv_file_path)
            if df.empty:
                logging.info(f"CSV 파일이 비어있음: {csv_file_path}")
                return True  # 빈 파일도 오류가 아님
            # code, date 컬럼 추가
            today = datetime.now().strftime("%Y%m%d")
            df["code"] = code
            df["date"] = today
            # DB에 저장
            conn = sqlite3.connect(db_path)
            df.to_sql("minute_data", conn, if_exists="append", index=False)
            conn.close()
            # 이관 완료 후 csv 파일 삭제
            os.remove(csv_file_path)
            logging.info(f"CSV to DB 마이그레이션 완료: {code}")
            return True
        except Exception as e:
            logging.error(f"CSV to DB migration failed: {e}")
            return False

    def _get_last_business_day(self, date_str: str = None) -> str:
        """
        가장 최근 영업일 계산 (휴장일 제외)

        Args:
            date_str (str): 기준 날짜 (YYYYMMDD 형식, 없으면 오늘)

        Returns:
            str: 가장 최근 영업일 (YYYYMMDD 형식)
        """
        # [변경 이유] 영업일 계산을 위한 헬퍼 함수 추가
        import datetime

        current_date = (
            datetime.datetime.strptime(date_str, "%Y%m%d")
            if date_str
            else datetime.datetime.now()
        )

        # 최대 10일까지만 확인 (무한 루프 방지)
        for i in range(10):
            check_date = current_date - datetime.timedelta(days=i)
            check_date_str = check_date.strftime("%Y%m%d")

            # 주말 체크
            if check_date.weekday() >= 5:  # 토요일(5), 일요일(6)
                continue

            # 휴장일 체크
            try:
                is_holiday_result = self.is_holiday(check_date_str)
                if is_holiday_result is False:  # 영업일
                    return check_date_str
            except Exception:
                # API 호출 실패 시 주말만 제외하고 반환
                return check_date_str

        # 영업일을 찾지 못했을 경우 오늘 날짜 반환
        return current_date.strftime("%Y%m%d")

    def fetch_minute_data(
        self, code: str, date: Optional[str] = None, cache_dir: str = "cache"
    ) -> "pd.DataFrame":
        """
        분봉 데이터 수집 (4번 호출 방식으로 효율적 수집)

        Args:
            code (str): 종목코드
            date (str): 날짜 (YYYYMMDD 형식)
                      - None: 당일 또는 가장 최근 영업일 + 전일 분봉
                      - 특정 날짜: 해당 날짜의 분봉만 수집
            cache_dir (str): 캐시 디렉토리

        Returns:
            pandas.DataFrame: 분봉 데이터
        """
        # [변경 이유] 4번 호출 방식으로 변경하여 효율성 향상, 영업일 계산 추가
        import datetime
        import os

        import pandas as pd

        os.makedirs(cache_dir, exist_ok=True)
        now = datetime.datetime.now()

        # 날짜 결정 로직
        if date is None:
            # 인자가 없으면 최근 영업일 + 전일 분봉 수집
            today_str = now.strftime("%Y%m%d")
            last_business_day = self._get_last_business_day(today_str)

            # 현재 시간이 장 시작 전이면 전일 데이터만
            market_open_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if now < market_open_time:
                target_dates = [last_business_day]
                logging.info(
                    f"[{code}] 장 시작 전: 최근 영업일 분봉 수집 ({last_business_day})"
                )
            else:
                # 장 시작 후면 최근 영업일 + 전일 분봉
                prev_business_day = self._get_last_business_day(
                    (
                        datetime.datetime.strptime(last_business_day, "%Y%m%d")
                        - datetime.timedelta(days=1)
                    ).strftime("%Y%m%d")
                )
                target_dates = (
                    [last_business_day, prev_business_day]
                    if prev_business_day != last_business_day
                    else [last_business_day]
                )
                logging.info(f"[{code}] 최근 영업일 + 전일 분봉 수집 ({target_dates})")
        else:
            # 특정 날짜 지정
            target_dates = [date]
            logging.info(f"[{code}] 특정 날짜 분봉 수집 ({date})")

        all_data_frames = []

        for target_date in target_dates:
            csv_file_path = os.path.join(
                cache_dir, f"{code}_minute_data_{target_date}.csv"
            )

            # 캐시 확인
            cached_df = self._check_cache(csv_file_path, target_date, now)
            if cached_df is not None:
                logging.info(f"[{code}] 캐시된 분봉 데이터 사용 ({target_date})")
                all_data_frames.append(cached_df)
                continue

            # 새로 수집
            logging.info(f"[{code}] 분봉 데이터 API 수집 시작 ({target_date})")
            result = self.stock_api.get_intraday_price(code, target_date)

            if result and result.get("rt_cd") == "0":
                minute_data = result.get("output2", [])
                if minute_data:
                    df = pd.DataFrame(minute_data)
                    df["code"] = code
                    df["date"] = target_date

                    # 시간 포맷 정규화
                    if "stck_cntg_hour" in df.columns:
                        df["stck_cntg_hour"] = df["stck_cntg_hour"].apply(
                            lambda x: int(target_date + str(x).zfill(6)[-6:])
                        )

                    # CSV 저장
                    df.to_csv(csv_file_path, index=False)
                    logging.info(
                        f"[{code}] 분봉 데이터 수집 완료: {len(df)}건, CSV 저장됨 ({target_date})"
                    )

                    # DB 저장 시도
                    self._save_to_db(df, code, target_date)

                    all_data_frames.append(df)
                else:
                    logging.warning(f"[{code}] 분봉 데이터 없음 ({target_date})")
            else:
                logging.warning(f"[{code}] 분봉 데이터 수집 실패 ({target_date})")

        # 모든 데이터 합치기
        if all_data_frames:
            import pandas as pd  # 지역 import로 로딩 시간 단축

            combined_df = pd.concat(all_data_frames, ignore_index=True)
            # 시간 순서로 정렬 (최신 순)
            if "stck_cntg_hour" in combined_df.columns:
                combined_df = combined_df.sort_values("stck_cntg_hour", ascending=False)
            logging.info(f"[{code}] 전체 분봉 데이터 수집 완료: {len(combined_df)}건")
            return combined_df
        else:
            logging.warning(f"[{code}] 분봉 데이터 수집 실패: 모든 API 응답 없음")
            import pandas as pd  # 지역 import로 로딩 시간 단축
        return pd.DataFrame()

    def _check_cache(
        self, csv_file_path: str, target_date: str, now: "datetime.datetime"
    ) -> "pd.DataFrame":
        """
        캐시 파일 유효성 확인

        Args:
            csv_file_path (str): 캐시 파일 경로
            target_date (str): 대상 날짜
            now (datetime): 현재 시간

        Returns:
            pd.DataFrame: 유효한 캐시 데이터 또는 None
        """
        # [변경 이유] 캐시 확인 로직을 별도 함수로 분리하여 가독성 향상
        import datetime
        import os

        import pandas as pd

        if not os.path.exists(csv_file_path):
            return None

        try:
            # 파일 수정 시간 확인
            file_mtime = datetime.datetime.fromtimestamp(
                os.path.getmtime(csv_file_path)
            )

            # 과거 날짜는 캐시 유효
            target_datetime = datetime.datetime.strptime(target_date, "%Y%m%d")
            if target_datetime.date() < now.date():
                cached_df = pd.read_csv(csv_file_path)
                if not cached_df.empty:
                    return cached_df

            # 당일 데이터는 시간 기반 갱신
            market_open_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
            market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)

            if market_open_time <= now <= market_close_time:
                # 장중: 5분마다 갱신
                refresh_interval = datetime.timedelta(minutes=5)
            else:
                # 장외: 30분마다 갱신
                refresh_interval = datetime.timedelta(minutes=30)

            if now - file_mtime < refresh_interval:
                cached_df = pd.read_csv(csv_file_path)
                if not cached_df.empty:
                    return cached_df

        except Exception as e:
            logging.warning(f"캐시 파일 로드 실패: {e}")

        return None

    def _save_to_db(self, df: "pd.DataFrame", code: str, date: str):
        """
        DB에 분봉 데이터 저장

        Args:
            df (pd.DataFrame): 분봉 데이터
            code (str): 종목코드
            date (str): 날짜
        """
        # [변경 이유] DB 저장 로직을 별도 함수로 분리하여 가독성 향상
        try:
            import sqlite3

            db_path = "db/stonks_candles.db"
            conn = sqlite3.connect(db_path)
            # 기존 해당 날짜 데이터 삭제 후 새로 저장
            conn.execute(
                "DELETE FROM minute_data WHERE code = ? AND date = ?", (code, date)
            )
            df.to_sql("minute_data", conn, if_exists="append", index=False)
            conn.close()
            logging.info(f"[{code}] {date} 분봉 데이터 DB 저장 완료")
        except Exception as e:
            logging.warning(f"DB 저장 실패: {e}")

    def calculate_support_resistance(
        self, code: str, date: str = None, price_bins: int = 50
    ) -> dict:
        """
        매물대 분석 - 지지선과 저항선 계산

        Args:
            code (str): 종목코드
            date (str): 분석 날짜 (YYYYMMDD, None이면 최근 데이터)
            price_bins (int): 가격대 구간 수 (기본값: 50)

        Returns:
            dict: 매물대 분석 결과
        """
        # [변경 이유] 분봉 데이터를 활용한 매물대 분석 기능 추가
        import pandas as pd

        # 분봉 데이터 가져오기
        df = self.fetch_minute_data(code, date)

        if df.empty:
            logging.warning(f"[{code}] 분봉 데이터가 없어 매물대 계산 불가")
            return {}

        # 숫자형 변환
        numeric_columns = [
            "stck_oprc",
            "stck_hgpr",
            "stck_lwpr",
            "stck_prpr",
            "cntg_vol",
        ]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 기본 통계
        price_min = df["stck_lwpr"].min()
        price_max = df["stck_hgpr"].max()
        price_range = price_max - price_min

        # 1. 가격대별 거래량 분석
        volume_profile = self._calculate_volume_profile(df, price_bins)

        # 2. 피벗 포인트 계산
        pivot_points = self._calculate_pivot_points(df)

        # 3. VWAP 계산
        vwap = self._calculate_vwap(df)

        # 4. 지지/저항선 감지
        support_levels = self._detect_support_levels(df, volume_profile)
        resistance_levels = self._detect_resistance_levels(df, volume_profile)

        # 5. 매물대 강도 계산
        support_strength = self._calculate_level_strength(df, support_levels)
        resistance_strength = self._calculate_level_strength(df, resistance_levels)

        result = {
            "code": code,
            "analysis_date": date or df["date"].iloc[0],
            "price_range": {
                "min": float(price_min),
                "max": float(price_max),
                "range": float(price_range),
            },
            "volume_profile": volume_profile,
            "pivot_points": pivot_points,
            "vwap": float(vwap),
            "support_levels": [
                {"price": float(level), "strength": float(strength)}
                for level, strength in zip(support_levels, support_strength)
            ],
            "resistance_levels": [
                {"price": float(level), "strength": float(strength)}
                for level, strength in zip(resistance_levels, resistance_strength)
            ],
            "current_price": float(df["stck_prpr"].iloc[0]),
            "total_volume": int(df["cntg_vol"].sum()),
            "data_points": len(df),
        }

        logging.info(
            f"[{code}] 매물대 분석 완료: "
            f"지지선 {len(support_levels)}개, 저항선 {len(resistance_levels)}개"
        )
        return result

    def _calculate_volume_profile(self, df: "pd.DataFrame", bins: int = 50) -> list:
        """가격대별 거래량 분포 계산"""
        # [변경 이유] 매물대 분석을 위한 가격대별 거래량 분포 계산
        import numpy as np

        price_min = df["stck_lwpr"].min()
        price_max = df["stck_hgpr"].max()

        # 가격대 구간 생성
        price_bins = np.linspace(price_min, price_max, bins + 1)

        # 각 분봉에 대해 가격대별 거래량 분배
        volume_profile = np.zeros(bins)

        for _, row in df.iterrows():
            low, high = row["stck_lwpr"], row["stck_hgpr"]
            volume = row["cntg_vol"]

            # 해당 분봉의 가격 범위에 포함되는 구간들에 거래량 분배
            for i in range(bins):
                bin_low = price_bins[i]
                bin_high = price_bins[i + 1]

                # 겹치는 구간 계산
                overlap_low = max(low, bin_low)
                overlap_high = min(high, bin_high)

                if overlap_low < overlap_high:
                    # 겹치는 비율만큼 거래량 분배
                    overlap_ratio = (
                        (overlap_high - overlap_low) / (high - low) if high > low else 1
                    )
                    volume_profile[i] += volume * overlap_ratio

        # 결과 반환
        return [
            {
                "price": float((price_bins[i] + price_bins[i + 1]) / 2),
                "volume": float(volume_profile[i]),
            }
            for i in range(bins)
        ]

    def _calculate_pivot_points(self, df: "pd.DataFrame") -> dict:
        """피벗 포인트 계산"""
        # [변경 이유] 클래식 피벗 포인트 계산으로 지지/저항선 예측
        high = df["stck_hgpr"].max()
        low = df["stck_lwpr"].min()
        close = df["stck_prpr"].iloc[0]  # 최근 종가

        # 피벗 포인트 계산
        pivot = (high + low + close) / 3

        # 지지선과 저항선
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)

        return {
            "pivot": float(pivot),
            "resistance": {"r1": float(r1), "r2": float(r2), "r3": float(r3)},
            "support": {"s1": float(s1), "s2": float(s2), "s3": float(s3)},
        }

    def _calculate_vwap(self, df: "pd.DataFrame") -> float:
        """거래량 가중 평균 가격 계산"""
        # [변경 이유] VWAP 계산으로 공정가치 참조선 제공
        typical_price = (df["stck_hgpr"] + df["stck_lwpr"] + df["stck_prpr"]) / 3
        volume = df["cntg_vol"]

        vwap = (typical_price * volume).sum() / volume.sum()
        return vwap

    def _detect_support_levels(self, df: "pd.DataFrame", volume_profile: list) -> list:
        """지지선 감지"""
        # [변경 이유] 거래량이 많은 가격대에서 지지선 감지
        import numpy as np

        # 거래량 기준 상위 20% 구간에서 지지선 후보 추출
        volumes = [vp["volume"] for vp in volume_profile]
        volume_threshold = np.percentile(volumes, 80)

        support_candidates = []
        for vp in volume_profile:
            if vp["volume"] >= volume_threshold:
                # 해당 가격대에서 저가 터치 횟수 확인
                touch_count = len(
                    df[df["stck_lwpr"] <= vp["price"] * 1.002]
                )  # 0.2% 오차 허용
                if touch_count >= 2:  # 최소 2회 이상 터치
                    support_candidates.append(vp["price"])

        # 가격 순으로 정렬하여 상위 5개 반환
        return sorted(support_candidates)[:5]

    def _detect_resistance_levels(
        self, df: "pd.DataFrame", volume_profile: list
    ) -> list:
        """저항선 감지"""
        # [변경 이유] 거래량이 많은 가격대에서 저항선 감지
        import numpy as np

        # 거래량 기준 상위 20% 구간에서 저항선 후보 추출
        volumes = [vp["volume"] for vp in volume_profile]
        volume_threshold = np.percentile(volumes, 80)

        resistance_candidates = []
        for vp in volume_profile:
            if vp["volume"] >= volume_threshold:
                # 해당 가격대에서 고가 터치 횟수 확인
                touch_count = len(
                    df[df["stck_hgpr"] >= vp["price"] * 0.998]
                )  # 0.2% 오차 허용
                if touch_count >= 2:  # 최소 2회 이상 터치
                    resistance_candidates.append(vp["price"])

        # 가격 순으로 정렬하여 상위 5개 반환
        return sorted(resistance_candidates, reverse=True)[:5]

    def _calculate_level_strength(self, df: "pd.DataFrame", levels: list) -> list:
        """매물대 강도 계산"""
        # [변경 이유] 각 지지/저항선의 강도를 거래량과 터치 횟수로 계산
        strengths = []

        for level in levels:
            # 해당 가격대 근처(±0.5%) 거래량 합계
            price_range = level * 0.005
            nearby_volume = df[
                (df["stck_lwpr"] <= level + price_range)
                & (df["stck_hgpr"] >= level - price_range)
            ]["cntg_vol"].sum()

            # 터치 횟수 (고가 또는 저가가 해당 가격대 근처)
            touch_count = len(
                df[
                    (
                        (df["stck_hgpr"] >= level - price_range)
                        & (df["stck_hgpr"] <= level + price_range)
                    )
                    | (
                        (df["stck_lwpr"] >= level - price_range)
                        & (df["stck_lwpr"] <= level + price_range)
                    )
                ]
            )

            # 강도 = 거래량 가중치 * 터치 횟수
            strength = nearby_volume * touch_count
            strengths.append(strength)

        # 정규화 (0-100 스케일)
        if strengths:
            max_strength = max(strengths)
            strengths = [
                s / max_strength * 100 if max_strength > 0 else 0 for s in strengths
            ]

        return strengths

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

    def inquire_daily_ccld(
        self,
        start_date: str = "",
        end_date: str = "",
        pdno: str = "",
        ord_dvsn_cd: str = "00",
        pagination: bool = False,
        ccld_dvsn: str = "00",
        inqr_dvsn: str = "01",
        inqr_dvsn_3: str = "00",
        max_pages: int = 100,
        page_callback: Optional[
            Callable[[int, List[Dict[str, Any]], Dict[str, Any]], None]
        ] = None,
    ) -> Optional[Dict[str, Any]]:
        """주식일별주문체결조회

        특정 기간 동안의 주문 및 체결 내역을 조회합니다.

        Args:
            start_date: 조회시작일자 (YYYYMMDD). 기본값: 최근 30일
            end_date: 조회종료일자 (YYYYMMDD). 기본값: 오늘
            pdno: 종목코드 (6자리). 기본값: 전체
            ord_dvsn_cd: 주문구분코드. 기본값: "00"(전체)
            pagination: 연속조회 사용 여부. 기본값: False
            ccld_dvsn: 체결구분 ("00":전체, "01":체결, "02":미체결)
            inqr_dvsn: 조회구분/정렬 ("00":역순, "01":정순)
            inqr_dvsn_3: 조회구분3 ("00":전체, "01":현금, "02":신용)
            max_pages: 최대 페이지 수 (pagination=True일 때)
            page_callback: 페이지 콜백 함수 (pagination=True일 때)

        Returns:
            Optional[Dict[str, Any]]: 주문체결내역 (pagination=True) 또는 DataFrame (pagination=False)

        See Also:
            AccountAPI.inquire_daily_ccld: 상세 구현
        """
        return self.account_api.inquire_daily_ccld(
            start_date,
            end_date,
            pdno,
            ord_dvsn_cd,
            pagination,
            ccld_dvsn,
            inqr_dvsn,
            inqr_dvsn_3,
            max_pages,
            page_callback,
        )

    def inquire_period_trade_profit(
        self, start_date: str, end_date: str
    ) -> Optional[pd.DataFrame]:
        """기간별매매손익현황조회

        지정한 기간 동안의 실현 매매손익을 종목별로 조회합니다.

        Args:
            start_date: 조회시작일자 (YYYYMMDD 형식)
            end_date: 조회종료일자 (YYYYMMDD 형식)

        Returns:
            Optional[pd.DataFrame]: 기간별 매매손익 DataFrame

        See Also:
            AccountAPI.inquire_period_trade_profit: 상세 구현
        """
        return self.account_api.inquire_period_trade_profit(start_date, end_date)

    def inquire_balance_rlz_pl(self) -> Optional[pd.DataFrame]:
        """주식잔고조회_실현손익

        보유 종목의 평가손익과 실현손익 정보를 포함한 잔고를 조회합니다.

        Returns:
            Optional[pd.DataFrame]: 실현손익이 포함된 잔고 DataFrame

        See Also:
            AccountAPI.inquire_balance_rlz_pl: 상세 구현
        """
        return self.account_api.inquire_balance_rlz_pl()

    def inquire_psbl_sell(self, pdno: str) -> Optional[Dict[str, Any]]:
        """매도가능수량조회

        특정 종목의 매도 가능한 수량을 조회합니다.

        Args:
            pdno: 종목코드 (6자리)

        Returns:
            Optional[Dict[str, Any]]: 매도가능수량 정보

        See Also:
            AccountAPI.inquire_psbl_sell: 상세 구현
        """
        return self.account_api.inquire_psbl_sell(pdno)

    def order_cash(
        self,
        pdno: str,
        qty: int,
        price: int,
        buy_sell: str,
        order_type: str = "00",
        exchange: str = "KRX",
    ) -> Optional[Dict[str, Any]]:
        """주식주문(현금)

        현금으로 주식을 매수 또는 매도합니다. 실제 주문이 실행되므로 주의하세요.

        Args:
            pdno: 종목코드 (6자리)
            qty: 주문수량
            price: 주문단가 (시장가는 0)
            buy_sell: 매수매도구분 ("BUY" 또는 "SELL")
            order_type: 주문구분. 기본값: "00"(지정가)

        Returns:
            Optional[Dict[str, Any]]: 주문 응답

        Warning:
            실제 주문이 실행되므로 테스트 시 소액으로 진행하세요.

        See Also:
            AccountAPI.order_cash: 상세 구현
        """
        return self.account_api.order_cash(
            pdno, qty, price, buy_sell, order_type, exchange
        )

    def order_cash_sor(
        self, pdno: str, qty: int, buy_sell: str, order_type: str = "03"
    ) -> Optional[Dict[str, Any]]:
        """SOR 최유리지정가 주문

        Smart Order Routing으로 최적 가격에 주문합니다.
        KRX와 NXT 중 최적의 거래소를 자동 선택합니다.

        Args:
            pdno: 종목코드 (6자리)
            qty: 주문수량
            buy_sell: 매수매도구분 ("BUY" 또는 "SELL")
            order_type: 주문구분 (기본값: "03" 최유리지정가)

        Returns:
            Optional[Dict[str, Any]]: 주문 응답

        Example:
            >>> # SOR 최유리지정가 매수
            >>> agent.order_cash_sor("005930", 10, "BUY")
            >>>
            >>> # SOR 시장가 매도
            >>> agent.order_cash_sor("005930", 5, "SELL", "01")
        """
        return self.account_api.order_cash_sor(pdno, qty, buy_sell, order_type)

    def order_rvsecncl(
        self, org_order_no: str, qty: int, price: int, order_type: str, cncl_type: str
    ) -> Optional[Dict[str, Any]]:
        """주식주문(정정취소)

        미체결 주문을 정정하거나 취소합니다.

        Args:
            org_order_no: 원주문번호
            qty: 주문수량 (정정 시 새로운 수량, 취소 시 기존 수량)
            price: 주문단가 (정정 시 새로운 가격)
            order_type: 주문구분
            cncl_type: 정정취소구분 ("01": 정정, "02": 취소)

        Returns:
            Optional[Dict[str, Any]]: 정정취소 응답

        See Also:
            AccountAPI.order_rvsecncl: 상세 구현
        """
        return self.account_api.order_rvsecncl(
            org_order_no, qty, price, order_type, cncl_type
        )

    def order_resv(
        self, code: str, qty: int, price: int, order_type: str
    ) -> Optional[Dict[str, Any]]:
        """주식예약주문

        특정 조건에서 자동으로 실행될 예약주문을 등록합니다.

        Args:
            code: 종목코드 (6자리)
            qty: 주문수량
            price: 주문단가
            order_type: 주문구분

        Returns:
            Optional[Dict[str, Any]]: 예약주문 응답

        See Also:
            AccountAPI.order_resv: 상세 구현
        """
        return self.account_api.order_resv(code, qty, price, order_type)

    def order_resv_ccnl(self) -> Optional[Dict[str, Any]]:
        """주식예약주문조회

        등록된 예약주문 목록을 조회합니다.

        Returns:
            Optional[Dict[str, Any]]: 예약주문 목록

        See Also:
            AccountAPI.order_resv_ccnl: 상세 구현
        """
        return self.account_api.order_resv_ccnl()

    def order_resv_rvsecncl(
        self, seq: int, qty: int, price: int, order_type: str
    ) -> Optional[Dict[str, Any]]:
        """주식예약주문정정취소

        등록된 예약주문을 정정하거나 취소합니다.

        Args:
            seq: 예약주문순번
            qty: 주문수량
            price: 주문단가
            order_type: 주문구분

        Returns:
            Optional[Dict[str, Any]]: 예약주문 정정취소 응답

        See Also:
            AccountAPI.order_resv_rvsecncl: 상세 구현
        """
        return self.account_api.order_resv_rvsecncl(seq, qty, price, order_type)

    def inquire_credit_psamount(self, pdno: str) -> Optional[Dict[str, Any]]:
        """신용매수가능조회

        신용거래로 매수 가능한 금액과 수량을 조회합니다.

        Args:
            pdno: 종목코드 (6자리)

        Returns:
            Optional[Dict[str, Any]]: 신용매수가능 정보

        See Also:
            AccountAPI.inquire_credit_psamount: 상세 구현
        """
        return self.account_api.inquire_credit_psamount(pdno)

    def order_credit_buy(
        self,
        pdno: str,
        qty: int,
        price: int,
        order_type: str = "00",
        credit_type: str = "21",
    ) -> Optional[Dict[str, Any]]:
        """주식주문(신용매수)

        신용으로 주식을 매수합니다. 이자와 상환 의무가 발생합니다.

        Args:
            pdno: 종목코드 (6자리)
            qty: 주문수량
            price: 주문단가 (시장가는 0)
            order_type: 주문구분. 기본값: "00"(지정가)
            credit_type: 신용거래구분. 기본값: "21"(신용융자매수)

        Returns:
            Optional[Dict[str, Any]]: 주문 응답

        Warning:
            신용거래는 이자와 상환 의무가 발생하므로 신중하게 사용하세요.

        See Also:
            AccountAPI.order_credit_buy: 상세 구현
        """
        return self.account_api.order_credit_buy(
            pdno, qty, price, order_type, credit_type
        )

    def order_credit_sell(
        self,
        pdno: str,
        qty: int,
        price: int,
        order_type: str = "00",
        credit_type: str = "11",
    ) -> Optional[Dict[str, Any]]:
        """주식주문(신용매도)

        신용으로 매수한 주식을 매도하여 대출금을 상환합니다.

        Args:
            pdno: 종목코드 (6자리)
            qty: 주문수량
            price: 주문단가 (시장가는 0)
            order_type: 주문구분. 기본값: "00"(지정가)
            credit_type: 신용거래구분. 기본값: "11"(융자상환매도)

        Returns:
            Optional[Dict[str, Any]]: 주문 응답

        See Also:
            AccountAPI.order_credit_sell: 상세 구현
        """
        return self.account_api.order_credit_sell(
            pdno, qty, price, order_type, credit_type
        )

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
        """
        국내주식주문(현금) API - StockAPI 기반

        StockAPI의 order_cash 메서드를 사용하여 현금매수/매도 주문을 실행합니다.

        Args:
            ord_dv (str): 매수매도구분 (buy:매수, sell:매도)
            pdno (str): 종목코드 (6자리)
            ord_dvsn (str): 주문구분
                - 00:지정가, 01:시장가, 02:조건부지정가, 03:최유리지정가
                - 04:최우선지정가, 05:장전시간외, 06:장후시간외
                - 07:시간외단일가, 08:자기주식, 09:자기주식S-Option
                - 10:자기주식금전신탁, 11:IOC지정가, 12:FOK지정가
                - 13:IOC시장가, 14:FOK시장가, 15:IOC최유리, 16:FOK최유리
            ord_qty (str): 주문수량
            ord_unpr (str): 주문단가 (시장가는 "0")
            excg_id_dvsn_cd (str): 거래소ID구분코드 (KRX:한국거래소)
            sll_type (str): 매도유형 (01:일반매도, 02:임의매매, 05:대차매도)
            cndt_pric (str): 조건가격 (스탑지정가 주문 시 사용)

        Returns:
            Optional[Dict[str, Any]]: 주문 결과 데이터
                - rt_cd: 응답코드 ("0": 성공)
                - msg1: 응답메시지
                - output: 주문 상세 정보

        Example:
            >>> # 삼성전자 1주 70000원 지정가 매수
            >>> result = agent.order_stock_cash("buy", "005930", "00", "1", "70000")
            >>> print(result['msg1'])

            >>> # 삼성전자 1주 시장가 매도
            >>> result = agent.order_stock_cash("sell", "005930", "01", "1", "0")

            >>> # 최유리지정가로 빠른 매수 (추천)
            >>> result = agent.order_stock_cash("buy", "009470", "03", "1", "0")
        """
        return self.stock_api.order_cash(
            ord_dv=ord_dv,
            pdno=pdno,
            ord_dvsn=ord_dvsn,
            ord_qty=ord_qty,
            ord_unpr=ord_unpr,
            excg_id_dvsn_cd=excg_id_dvsn_cd,
            sll_type=sll_type,
            cndt_pric=cndt_pric,
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
        return self.stock_api.order_credit(
            ord_dv=ord_dv,
            pdno=pdno,
            crdt_type=crdt_type,
            loan_dt=loan_dt,
            ord_dvsn=ord_dvsn,
            ord_qty=ord_qty,
            ord_unpr=ord_unpr,
            excg_id_dvsn_cd=excg_id_dvsn_cd,
            sll_type=sll_type,
            rsvn_ord_yn=rsvn_ord_yn,
            emgc_ord_yn=emgc_ord_yn,
            cndt_pric=cndt_pric,
        )

    def inquire_order_psbl(
        self,
        pdno: str,  # 종목코드
        ord_unpr: str,  # 주문단가
        ord_dvsn: str = "00",  # 주문구분
        cma_evlu_amt_icld_yn: str = "Y",  # CMA평가금액포함여부
        ovrs_icld_yn: str = "Y",  # 해외포함여부
    ) -> Optional[Dict[str, Any]]:
        """
        매수가능조회 - StockAPI 기반

        StockAPI의 inquire_psbl_order 메서드를 사용하여 특정 종목의 매수 가능 수량과 금액을 조회합니다.

        Args:
            pdno (str): 종목코드 (6자리)
            ord_unpr (str): 주문단가
            ord_dvsn (str): 주문구분 (기본값: "00")
                - 00:지정가, 01:시장가, 02:조건부지정가, 03:최유리지정가
                - 04:최우선지정가, 05:장전시간외, 06:장후시간외
                - 07:시간외단일가, 08:자기주식, 09:자기주식S-Option
                - 10:자기주식금전신탁, 11:IOC지정가, 12:FOK지정가
                - 13:IOC시장가, 14:FOK시장가, 15:IOC최유리, 16:FOK최유리
            cma_evlu_amt_icld_yn (str): CMA평가금액포함여부 (Y:포함, N:미포함)
            ovrs_icld_yn (str): 해외포함여부 (Y:포함, N:미포함)

        Returns:
            Optional[Dict[str, Any]]: 매수가능 정보
                - rt_cd: 응답코드 ("0": 성공)
                - msg1: 응답메시지
                - output: 매수가능 상세 정보
                    - ord_psbl_cash: 주문가능현금
                    - max_buy_qty: 최대매수수량
                    - ord_psbl_qty: 주문가능수량

        Example:
            >>> # 삼성전자 70000원 지정가 매수가능 조회
            >>> result = agent.inquire_order_psbl("005930", "70000")
            >>> print(f"매수가능수량: {result['output']['max_buy_qty']}")
        """
        return self.stock_api.inquire_psbl_order(
            pdno=pdno,
            ord_unpr=ord_unpr,
            ord_dvsn=ord_dvsn,
            cma_evlu_amt_icld_yn=cma_evlu_amt_icld_yn,
            ovrs_icld_yn=ovrs_icld_yn,
        )

    def inquire_credit_order_psbl(
        self,
        pdno: str,  # 종목코드
        ord_unpr: str,  # 주문단가
        ord_dvsn: str = "00",  # 주문구분
        crdt_type: str = "21",  # 신용유형
        cma_evlu_amt_icld_yn: str = "N",  # CMA평가금액포함여부
        ovrs_icld_yn: str = "N",  # 해외포함여부
    ) -> Optional[Dict[str, Any]]:
        """
        신용매수가능조회 - StockAPI 기반

        StockAPI의 inquire_credit_psamount 메서드를 사용하여 특정 종목의 신용매수 가능 수량과 금액을 조회합니다.

        Args:
            pdno (str): 종목코드 (6자리)
            ord_unpr (str): 주문단가
            ord_dvsn (str): 주문구분 (기본값: "00")
                - 00:지정가, 01:시장가, 02:조건부지정가, 03:최유리지정가
                - 04:최우선지정가, 05:장전시간외, 06:장후시간외
                - 07:시간외단일가
            crdt_type (str): 신용유형 (기본값: "21")
                - 21:자기융자신규, 23:유통융자신규
                - 26:유통대주상환, 28:자기대주상환
            cma_evlu_amt_icld_yn (str): CMA평가금액포함여부 (기본값: "N")
                - Y:포함, N:불포함
            ovrs_icld_yn (str): 해외포함여부 (기본값: "N")
                - Y:포함, N:불포함

        Returns:
            Optional[Dict[str, Any]]: 신용매수가능 정보
                - rt_cd: 응답코드 ("0": 성공)
                - msg1: 응답메시지
                - output: 신용매수가능 상세 정보
                    - crdt_buy_psbl_amt: 신용매수가능금액
                    - max_buy_qty: 최대매수수량
                    - crdt_psbl_qty: 신용매수가능수량

        Example:
            >>> # 삼성전자 70000원 신용매수가능 조회
            >>> result = agent.inquire_credit_order_psbl("005930", "70000")
            >>> print(f"신용매수가능수량: {result['output']['max_buy_qty']}")
        """
        return self.stock_api.inquire_credit_psamount(
            pdno=pdno,
            ord_unpr=ord_unpr,
            ord_dvsn=ord_dvsn,
            crdt_type=crdt_type,
            cma_evlu_amt_icld_yn=cma_evlu_amt_icld_yn,
            ovrs_icld_yn=ovrs_icld_yn,
        )

    def inquire_intgr_margin(self) -> Optional[Dict[str, Any]]:
        """주식통합증거금 현황

        통합증거금 계좌의 증거금 현황을 조회합니다.

        Returns:
            Optional[Dict[str, Any]]: 통합증거금 현황 정보

        See Also:
            AccountAPI.inquire_intgr_margin: 상세 구현
        """
        return self.account_api.inquire_intgr_margin()

    def inquire_period_rights(
        self, start_date: str, end_date: str
    ) -> Optional[pd.DataFrame]:
        """기간별계좌권리현황조회

        특정 기간 동안의 배당, 증자 등 권리 현황을 조회합니다.

        Args:
            start_date: 조회시작일자 (YYYYMMDD 형식)
            end_date: 조회종료일자 (YYYYMMDD 형식)

        Returns:
            Optional[pd.DataFrame]: 기간별 권리현황 DataFrame

        See Also:
            AccountAPI.inquire_period_rights: 상세 구현
        """
        return self.account_api.inquire_period_rights(start_date, end_date)

    def inquire_psbl_rvsecncl(self) -> Optional[Dict[str, Any]]:
        """주식정정취소가능주문조회

        현재 정정하거나 취소할 수 있는 미체결 주문을 조회합니다.

        Returns:
            Optional[Dict[str, Any]]: 정정취소가능 주문 목록

        See Also:
            AccountAPI.inquire_psbl_rvsecncl: 상세 구현
        """
        return self.account_api.inquire_psbl_rvsecncl()

    # ============================================================================
    # Rate Limiter 관리 메서드
    # ============================================================================

    def get_rate_limiter_status(self) -> Optional[Dict[str, Any]]:
        """
        Rate Limiter 상태 조회

        Returns:
            Dict: Rate Limiter 상태 정보
                - requests_per_second: 현재 초당 요청 수
                - requests_per_minute: 현재 분당 요청 수
                - limit_per_second: 초당 제한
                - limit_per_minute: 분당 제한
                - backoff_multiplier: 백오프 배수
                - total_requests: 총 요청 수
                - throttled_count: 제한된 요청 수
                - avg_wait_time: 평균 대기 시간
            None: Rate Limiter가 비활성화된 경우

        Example:
            >>> status = agent.get_rate_limiter_status()
            >>> if status:
            ...     print(f"현재 요청률: {status['requests_per_second']}/초")
            ...     print(f"제한 도달 횟수: {status['throttled_count']}")
        """
        if self.rate_limiter:
            return self.rate_limiter.get_current_rate()
        return None

    def set_rate_limits(
        self,
        requests_per_second: Optional[int] = None,
        requests_per_minute: Optional[int] = None,
        min_interval_ms: Optional[int] = None,
    ):
        """
        Rate Limiter 제한 값 동적 변경

        Args:
            requests_per_second: 초당 최대 요청 수 (None이면 변경 안 함)
            requests_per_minute: 분당 최대 요청 수 (None이면 변경 안 함)
            min_interval_ms: 최소 간격 (밀리초) (None이면 변경 안 함)

        Example:
            >>> # 더 보수적인 설정으로 변경
            >>> agent.set_rate_limits(
            ...     requests_per_second=10,
            ...     requests_per_minute=500
            ... )
            >>>
            >>> # 최소 간격만 변경
            >>> agent.set_rate_limits(min_interval_ms=100)
        """
        if self.rate_limiter:
            self.rate_limiter.set_limits(
                requests_per_second=requests_per_second,
                requests_per_minute=requests_per_minute,
                min_interval_ms=min_interval_ms,
            )
            # [변경 이유] 불필요한 f-string 사용으로 F541 경고 발생 -> 리터럴 문자열로 변경
            logging.info("Rate limits 업데이트 완료")
        else:
            logging.warning("Rate Limiter가 비활성화 상태입니다")

    def reset_rate_limiter(self):
        """
        Rate Limiter 상태 초기화

        모든 요청 기록과 통계를 초기화합니다.
        백오프 배수도 1.0으로 리셋됩니다.

        Example:
            >>> agent.reset_rate_limiter()
            >>> print("Rate limiter 초기화 완료")
        """
        if self.rate_limiter:
            self.rate_limiter.reset()
            logging.info("Rate limiter 초기화 완료")
        else:
            logging.warning("Rate Limiter가 비활성화 상태입니다")

    def enable_adaptive_rate_limiting(self, enable: bool = True):
        """
        적응형 속도 조절 활성화/비활성화

        Args:
            enable: True면 활성화, False면 비활성화

        Example:
            >>> # 적응형 속도 조절 비활성화
            >>> agent.enable_adaptive_rate_limiting(False)
        """
        if self.rate_limiter:
            self.rate_limiter.enable_adaptive = enable
            status = "활성화" if enable else "비활성화"
            logging.info(f"적응형 속도 조절 {status}")
        else:
            logging.warning("Rate Limiter가 비활성화 상태입니다")

    # ============================================================================
    # 하위 호환성을 위한 __getattr__ 메서드 (기존 코드와의 호환성)
    # ============================================================================

    def __getattr__(self, name: str):
        """API 모듈의 메서드를 위임 (하위 호환성)

        우선순위:
        1. StockAPI - 주식 관련 기본 API (최우선)
        2. AccountAPI - 계좌 관련 API
        3. ProgramTradeAPI - 프로그램매매 관련 API
        """
        # StockAPI를 최우선으로 확인 (메인 주식 API)
        if hasattr(self.stock_api, name):
            return getattr(self.stock_api, name)

        # StockMarketAPI 확인 (시장 데이터 관련 API)
        if hasattr(self.market_api, name):
            return getattr(self.market_api, name)

        # 나머지 API 모듈에서 메서드 찾기
        for api in (self.account_api, self.program_api):
            if hasattr(api, name):
                return getattr(api, name)

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


# Expose facade class for flat import
__all__ = ["Agent"]
