"""
리팩토링된 WebSocket 클라이언트 (레거시)

.. deprecated:: 1.3.0
    이 모듈은 더 이상 유지보수되지 않습니다.
    대신 :class:`WSAgent` 또는 :class:`WSAgentWithStore`를 사용하세요.

마이그레이션 예시::

    # 기존 코드 (deprecated)
    from kis_agent.websocket import RefactoredWebSocketClient
    client = RefactoredWebSocketClient(
        approval_key=key,
        connection_manager=conn,
        data_processor=proc,
        event_manager=events,
        handler_registry=registry
    )
    await client.connect()

    # 새로운 코드 (권장)
    from kis_agent.websocket import WSAgent
    ws = WSAgent(approval_key=key)
    ws.subscribe_stock("005930")
    await ws.connect()

책임이 분리되고 디자인 패턴이 적용된 깔끔한 WebSocket 클라이언트입니다.
"""

import json
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from .connection import ConnectionManager
from .data_processor import DataProcessor
from .event_manager import EventManager, EventType
from .message_handlers import MessageHandlerRegistry

logger = logging.getLogger(__name__)


class RefactoredWebSocketClient:
    """
    리팩토링된 WebSocket 클라이언트

    .. deprecated:: 1.3.0
        이 클래스는 더 이상 유지보수되지 않습니다.
        대신 :class:`WSAgent` 또는 :class:`WSAgentWithStore`를 사용하세요.

    Single Responsibility Principle에 따라 책임이 분리되고,
    디자인 패턴이 적용된 깔끔한 구조를 가진 WebSocket 클라이언트입니다.

    See Also:
        :class:`WSAgent`: 권장되는 대체 클래스
        :class:`WSAgentWithStore`: 데이터 저장소가 포함된 에이전트

    Attributes:
        approval_key: WebSocket 승인키
        connection_manager: 연결 관리자
        data_processor: 데이터 처리기
        event_manager: 이벤트 관리자
        handler_registry: 메시지 핸들러 레지스트리
    """

    def __init__(
        self,
        approval_key: str,
        connection_manager: ConnectionManager,
        data_processor: DataProcessor,
        event_manager: EventManager,
        handler_registry: MessageHandlerRegistry,
        enable_logging: bool = True,
        enable_metrics: bool = True,
        data_recording: bool = False,
    ):
        """
        RefactoredWebSocketClient 초기화

        Args:
            approval_key: WebSocket 승인키
            connection_manager: 연결 관리자
            data_processor: 데이터 처리기
            event_manager: 이벤트 관리자
            handler_registry: 메시지 핸들러 레지스트리
            enable_logging: 로깅 활성화 여부
            enable_metrics: 메트릭 수집 활성화 여부
            data_recording: 데이터 기록 활성화 여부
        """
        warnings.warn(
            "RefactoredWebSocketClient는 deprecated되었습니다. "
            "WSAgent 또는 WSAgentWithStore를 사용하세요. "
            "마이그레이션 가이드: from kis_agent.websocket import WSAgent",
            DeprecationWarning,
            stacklevel=2,
        )
        self.approval_key = approval_key
        self.connection_manager = connection_manager
        self.data_processor = data_processor
        self.event_manager = event_manager
        self.handler_registry = handler_registry

        self.enable_logging = enable_logging
        self.enable_metrics = enable_metrics
        self.data_recording = data_recording

        # 구독 관리
        self.subscriptions: Set[str] = set()
        self.stock_subscriptions: Set[str] = set()

        # 메트릭
        self.metrics = {
            "messages_received": 0,
            "messages_processed": 0,
            "errors": 0,
            "start_time": None,
            "last_message_time": None,
        }

        # 데이터 기록 설정
        if data_recording:
            self._setup_data_recording()

        # 이벤트 핸들러 등록
        self._setup_event_handlers()

    def _setup_data_recording(self):
        """데이터 기록 설정"""
        log_dir = Path("logs/websocket")
        log_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d")
        self.data_log_file = log_dir / f"data_{date_str}.jsonl"

    def _setup_event_handlers(self):
        """기본 이벤트 핸들러 설정"""
        self.event_manager.subscribe(
            EventType.CONNECTION_OPENED, self._on_connection_opened
        )

        self.event_manager.subscribe(
            EventType.CONNECTION_CLOSED, self._on_connection_closed
        )

        self.event_manager.subscribe(EventType.ERROR, self._on_error)

    async def connect(self):
        """
        WebSocket 서버에 연결

        Raises:
            websockets.exceptions.WebSocketException: 연결 실패
        """
        logger.info("WebSocket 연결 시작")

        await self.connection_manager.connect()

        if self.enable_metrics:
            self.metrics["start_time"] = datetime.now()

        self.event_manager.emit(
            EventType.CONNECTION_OPENED, {"timestamp": datetime.now()}
        )

    async def disconnect(self):
        """WebSocket 연결 종료"""
        logger.info("WebSocket 연결 종료")

        await self.connection_manager.disconnect()

        self.event_manager.emit(
            EventType.CONNECTION_CLOSED, {"timestamp": datetime.now()}
        )

    async def subscribe_stock(self, code: str, with_orderbook: bool = False):
        """
        종목 구독

        Args:
            code: 종목 코드
            with_orderbook: 호가 데이터도 구독할지 여부

        Raises:
            RuntimeError: 연결되지 않은 상태에서 구독 시도
        """
        if not self.connection_manager.is_alive():
            raise RuntimeError("WebSocket이 연결되지 않았습니다")

        # 체결 데이터 구독
        trade_message = {
            "header": {
                "approval_key": self.approval_key,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8",
            },
            "body": {"input": {"tr_id": "H0STCNT0", "tr_key": code}},
        }

        await self.connection_manager.send(json.dumps(trade_message))
        self.stock_subscriptions.add(code)

        logger.info(f"종목 구독: {code}")

        # 호가 데이터 구독 (선택적)
        if with_orderbook:
            orderbook_message = {
                "header": {
                    "approval_key": self.approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8",
                },
                "body": {"input": {"tr_id": "H0STASP0", "tr_key": code}},
            }

            await self.connection_manager.send(json.dumps(orderbook_message))
            logger.info(f"호가 구독: {code}")

    async def unsubscribe_stock(self, code: str):
        """
        종목 구독 해제

        Args:
            code: 종목 코드

        Raises:
            RuntimeError: 연결되지 않은 상태에서 구독 해제 시도
        """
        if not self.connection_manager.is_alive():
            raise RuntimeError("WebSocket이 연결되지 않았습니다")

        message = {
            "header": {
                "approval_key": self.approval_key,
                "custtype": "P",
                "tr_type": "2",  # 구독 해제
                "content-type": "utf-8",
            },
            "body": {"input": {"tr_id": "H0STCNT0", "tr_key": code}},
        }

        await self.connection_manager.send(json.dumps(message))
        self.stock_subscriptions.discard(code)

        logger.info(f"종목 구독 해제: {code}")

    async def subscribe_index(self, codes: Optional[List[str]] = None):
        """
        지수 구독

        Args:
            codes: 지수 코드 리스트 (기본값: KOSPI, KOSDAQ, KOSPI200)

        Raises:
            RuntimeError: 연결되지 않은 상태에서 구독 시도
        """
        if not self.connection_manager.is_alive():
            raise RuntimeError("WebSocket이 연결되지 않았습니다")

        if codes is None:
            codes = ["0001", "1001", "2001"]  # KOSPI, KOSDAQ, KOSPI200

        for code in codes:
            message = {
                "header": {
                    "approval_key": self.approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8",
                },
                "body": {"input": {"tr_id": "H0IF1000", "tr_key": code}},
            }

            await self.connection_manager.send(json.dumps(message))
            logger.info(f"지수 구독: {code}")

    async def run(self):
        """
        메인 실행 루프

        메시지를 수신하고 처리하는 메인 루프입니다.

        Raises:
            Exception: 메시지 처리 중 발생한 모든 예외
        """
        logger.info("WebSocket 클라이언트 실행 시작")

        while self.connection_manager.is_alive():
            # 메시지 수신
            raw_message = await self.connection_manager.recv()

            if self.enable_metrics:
                self.metrics["messages_received"] += 1
                self.metrics["last_message_time"] = datetime.now()

            # 메시지 처리
            processed_message = self.data_processor.process_message(raw_message)

            # 핸들러 실행
            result = self.handler_registry.process(processed_message)

            if result:
                # 이벤트 발생
                if result["type"] == "trade":
                    self.event_manager.emit(EventType.TRADE_UPDATE, result)
                elif result["type"] == "orderbook":
                    self.event_manager.emit(EventType.ORDERBOOK_UPDATE, result)
                elif result["type"] == "index":
                    self.event_manager.emit(EventType.INDEX_UPDATE, result)
                elif result["type"] == "program_trading":
                    self.event_manager.emit(EventType.PROGRAM_TRADING_UPDATE, result)

                # 데이터 기록
                if self.data_recording:
                    self._record_data(result)

                if self.enable_metrics:
                    self.metrics["messages_processed"] += 1

    def _record_data(self, data: Dict[str, Any]):
        """
        데이터 기록

        Args:
            data: 기록할 데이터
        """
        if not hasattr(self, "data_log_file"):
            return

        with open(self.data_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def _on_connection_opened(self, event):
        """연결 열림 이벤트 핸들러"""
        logger.info(f"연결 열림: {event.timestamp}")

    def _on_connection_closed(self, event):
        """연결 닫힘 이벤트 핸들러"""
        logger.info(f"연결 닫힘: {event.timestamp}")

    def _on_error(self, event):
        """
        에러 이벤트 핸들러

        에러를 로깅하고 다시 발생시킵니다.
        """
        logger.error(f"에러 발생: {event.data}")

        if self.enable_metrics:
            self.metrics["errors"] += 1

        # 에러를 다시 발생시켜 상위로 전파
        raise RuntimeError(f"WebSocket 에러: {event.data}")

    def add_stock_subscription(self, code: str):
        """종목 구독 추가 (빌더 패턴용)"""
        self.stock_subscriptions.add(code)

    def enable_index_subscription(self):
        """지수 구독 활성화 (빌더 패턴용)"""
        self.subscriptions.add("index")

    def enable_orderbook_subscription(self):
        """호가 구독 활성화 (빌더 패턴용)"""
        self.subscriptions.add("orderbook")

    def enable_program_trading_subscription(self):
        """프로그램매매 구독 활성화 (빌더 패턴용)"""
        self.subscriptions.add("program_trading")

    def register_callback(self, event_type: EventType, callback: Callable):
        """
        콜백 등록

        Args:
            event_type: 이벤트 타입
            callback: 콜백 함수
        """
        self.event_manager.subscribe(event_type, callback)

    def get_metrics(self) -> Dict[str, Any]:
        """
        메트릭 조회

        Returns:
            Dict[str, Any]: 수집된 메트릭
        """
        if not self.enable_metrics:
            return {}

        metrics = self.metrics.copy()

        # 실행 시간 계산
        if metrics["start_time"]:
            uptime = datetime.now() - metrics["start_time"]
            metrics["uptime_seconds"] = uptime.total_seconds()

        # 연결 상태 추가
        metrics["connection_status"] = self.connection_manager.get_stats()

        return metrics

    def get_latest_data(self, code: str) -> Optional[Dict[str, Any]]:
        """
        최신 데이터 조회

        Args:
            code: 종목 코드

        Returns:
            Optional[Dict[str, Any]]: 최신 데이터
        """
        return self.data_processor.latest_data.get(code)

    def get_indicators(self, code: str) -> Dict[str, Any]:
        """
        기술 지표 조회

        Args:
            code: 종목 코드

        Returns:
            Dict[str, Any]: 계산된 기술 지표
        """
        return self.data_processor.calculate_indicators(code)
