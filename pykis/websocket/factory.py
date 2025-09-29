"""
WebSocket 클라이언트 팩토리 모듈 (Factory Pattern)

다양한 설정의 WebSocket 클라이언트를 생성합니다.
"""

import logging
from enum import Enum
from typing import List

from .connection import ConnectionManager
from .data_processor import DataProcessor
from .event_manager import EventManager
from .message_handlers import MessageHandlerRegistry
from .refactored_client import RefactoredWebSocketClient

logger = logging.getLogger(__name__)


class ClientType(Enum):
    """클라이언트 타입"""

    BASIC = "basic"  # 기본 클라이언트
    REALTIME = "realtime"  # 실시간 트레이딩용
    MONITORING = "monitoring"  # 모니터링용
    BACKTEST = "backtest"  # 백테스트용


class WebSocketClientFactory:
    """
    WebSocket 클라이언트 팩토리

    다양한 설정과 타입의 WebSocket 클라이언트를 생성합니다.
    """

    @staticmethod
    def create_client(
        client_type: ClientType, approval_key: str, **kwargs
    ) -> RefactoredWebSocketClient:
        """
        클라이언트 생성

        Args:
            client_type: 클라이언트 타입
            approval_key: WebSocket 승인키
            **kwargs: 추가 설정

        Returns:
            RefactoredWebSocketClient: 생성된 클라이언트
        """
        if client_type == ClientType.BASIC:
            return WebSocketClientFactory._create_basic_client(approval_key, **kwargs)
        elif client_type == ClientType.REALTIME:
            return WebSocketClientFactory._create_realtime_client(
                approval_key, **kwargs
            )
        elif client_type == ClientType.MONITORING:
            return WebSocketClientFactory._create_monitoring_client(
                approval_key, **kwargs
            )
        elif client_type == ClientType.BACKTEST:
            return WebSocketClientFactory._create_backtest_client(
                approval_key, **kwargs
            )
        else:
            raise ValueError(f"지원하지 않는 클라이언트 타입: {client_type}")

    @staticmethod
    def _create_basic_client(approval_key: str, **kwargs) -> RefactoredWebSocketClient:
        """
        기본 클라이언트 생성

        최소한의 기능만 포함된 가벼운 클라이언트입니다.
        """
        connection = ConnectionManager(
            url=kwargs.get("url", "ws://ops.koreainvestment.com:21000"),
            auto_reconnect=False,
        )

        processor = DataProcessor()
        event_manager = EventManager(async_mode=True)
        handler_registry = MessageHandlerRegistry()

        return RefactoredWebSocketClient(
            approval_key=approval_key,
            connection_manager=connection,
            data_processor=processor,
            event_manager=event_manager,
            handler_registry=handler_registry,
            enable_logging=False,
            enable_metrics=False,
        )

    @staticmethod
    def _create_realtime_client(
        approval_key: str, **kwargs
    ) -> RefactoredWebSocketClient:
        """
        실시간 트레이딩 클라이언트 생성

        자동 재연결, 로깅, 메트릭 수집이 활성화된 클라이언트입니다.
        """
        connection = ConnectionManager(
            url=kwargs.get("url", "ws://ops.koreainvestment.com:21000"),
            auto_reconnect=True,
            ping_interval=20,
            ping_timeout=10,
        )

        processor = DataProcessor()
        event_manager = EventManager(async_mode=True)
        handler_registry = MessageHandlerRegistry()

        client = RefactoredWebSocketClient(
            approval_key=approval_key,
            connection_manager=connection,
            data_processor=processor,
            event_manager=event_manager,
            handler_registry=handler_registry,
            enable_logging=True,
            enable_metrics=True,
        )

        # 실시간 트레이딩용 설정
        if "stock_codes" in kwargs:
            for code in kwargs["stock_codes"]:
                client.add_stock_subscription(code)

        if kwargs.get("enable_orderbook", False):
            client.enable_orderbook_subscription()

        if kwargs.get("enable_program_trading", False):
            client.enable_program_trading_subscription()

        return client

    @staticmethod
    def _create_monitoring_client(
        approval_key: str, **kwargs
    ) -> RefactoredWebSocketClient:
        """
        모니터링 클라이언트 생성

        시장 전반을 모니터링하기 위한 클라이언트입니다.
        """
        connection = ConnectionManager(
            url=kwargs.get("url", "ws://ops.koreainvestment.com:21000"),
            auto_reconnect=True,
            ping_interval=30,
            ping_timeout=30,
        )

        processor = DataProcessor()
        event_manager = EventManager(async_mode=True)
        handler_registry = MessageHandlerRegistry()

        client = RefactoredWebSocketClient(
            approval_key=approval_key,
            connection_manager=connection,
            data_processor=processor,
            event_manager=event_manager,
            handler_registry=handler_registry,
            enable_logging=True,
            enable_metrics=True,
        )

        # 모니터링용 설정
        client.enable_index_subscription()  # 지수 구독
        client.enable_program_trading_subscription()  # 프로그램매매 구독

        # 주요 종목들 구독
        major_stocks = kwargs.get("major_stocks", ["005930", "000660", "035420"])
        for code in major_stocks:
            client.add_stock_subscription(code)

        return client

    @staticmethod
    def _create_backtest_client(
        approval_key: str, **kwargs
    ) -> RefactoredWebSocketClient:
        """
        백테스트 클라이언트 생성

        백테스트용으로 데이터만 수집하는 클라이언트입니다.
        """
        connection = ConnectionManager(
            url=kwargs.get("url", "ws://ops.koreainvestment.com:21000"),
            auto_reconnect=False,  # 백테스트는 재연결 불필요
        )

        processor = DataProcessor()
        event_manager = EventManager(async_mode=False)  # 동기 모드
        handler_registry = MessageHandlerRegistry()

        return RefactoredWebSocketClient(
            approval_key=approval_key,
            connection_manager=connection,
            data_processor=processor,
            event_manager=event_manager,
            handler_registry=handler_registry,
            enable_logging=True,
            enable_metrics=False,  # 메트릭 불필요
            data_recording=True,  # 데이터 기록 활성화
        )


class WebSocketClientBuilder:
    """
    WebSocket 클라이언트 빌더

    Fluent Interface 패턴을 사용하여 클라이언트를 구성합니다.
    """

    def __init__(self, approval_key: str):
        """
        Builder 초기화

        Args:
            approval_key: WebSocket 승인키
        """
        self.approval_key = approval_key
        self.url = "ws://ops.koreainvestment.com:21000"
        self.auto_reconnect = True
        self.ping_interval = 30
        self.ping_timeout = 30
        self.stock_codes: List[str] = []
        self.enable_index = False
        self.enable_orderbook = False
        self.enable_program = False
        self.enable_logging = True
        self.enable_metrics = True

    def with_url(self, url: str) -> "WebSocketClientBuilder":
        """URL 설정"""
        self.url = url
        return self

    def with_auto_reconnect(self, enabled: bool) -> "WebSocketClientBuilder":
        """자동 재연결 설정"""
        self.auto_reconnect = enabled
        return self

    def with_ping_settings(
        self, interval: int, timeout: int
    ) -> "WebSocketClientBuilder":
        """Ping 설정"""
        self.ping_interval = interval
        self.ping_timeout = timeout
        return self

    def add_stock(self, code: str) -> "WebSocketClientBuilder":
        """종목 추가"""
        if code not in self.stock_codes:
            self.stock_codes.append(code)
        return self

    def add_stocks(self, codes: List[str]) -> "WebSocketClientBuilder":
        """여러 종목 추가"""
        for code in codes:
            self.add_stock(code)
        return self

    def with_index_subscription(self) -> "WebSocketClientBuilder":
        """지수 구독 활성화"""
        self.enable_index = True
        return self

    def with_orderbook_subscription(self) -> "WebSocketClientBuilder":
        """호가 구독 활성화"""
        self.enable_orderbook = True
        return self

    def with_program_trading_subscription(self) -> "WebSocketClientBuilder":
        """프로그램매매 구독 활성화"""
        self.enable_program = True
        return self

    def with_logging(self, enabled: bool) -> "WebSocketClientBuilder":
        """로깅 설정"""
        self.enable_logging = enabled
        return self

    def with_metrics(self, enabled: bool) -> "WebSocketClientBuilder":
        """메트릭 설정"""
        self.enable_metrics = enabled
        return self

    def build(self) -> RefactoredWebSocketClient:
        """클라이언트 빌드"""
        connection = ConnectionManager(
            url=self.url,
            auto_reconnect=self.auto_reconnect,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
        )

        processor = DataProcessor()
        event_manager = EventManager(async_mode=True)
        handler_registry = MessageHandlerRegistry()

        client = RefactoredWebSocketClient(
            approval_key=self.approval_key,
            connection_manager=connection,
            data_processor=processor,
            event_manager=event_manager,
            handler_registry=handler_registry,
            enable_logging=self.enable_logging,
            enable_metrics=self.enable_metrics,
        )

        # 구독 설정
        for code in self.stock_codes:
            client.add_stock_subscription(code)

        if self.enable_index:
            client.enable_index_subscription()

        if self.enable_orderbook:
            client.enable_orderbook_subscription()

        if self.enable_program:
            client.enable_program_trading_subscription()

        return client
