"""
이벤트 관리자 모듈 (Observer Pattern)

WebSocket 이벤트를 관리하고 구독자들에게 알림을 전송합니다.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class EventType(Enum):
    """이벤트 타입 정의"""

    CONNECTION_OPENED = "connection_opened"
    CONNECTION_CLOSED = "connection_closed"
    CONNECTION_ERROR = "connection_error"
    MESSAGE_RECEIVED = "message_received"
    TRADE_UPDATE = "trade_update"
    ORDERBOOK_UPDATE = "orderbook_update"
    INDEX_UPDATE = "index_update"
    PROGRAM_TRADING_UPDATE = "program_trading_update"
    SUBSCRIPTION_SUCCESS = "subscription_success"
    SUBSCRIPTION_FAILED = "subscription_failed"
    ERROR = "error"


class Event:
    """
    이벤트 객체

    Attributes:
        type: 이벤트 타입
        data: 이벤트 데이터
        timestamp: 이벤트 발생 시각
        source: 이벤트 발생 소스
    """

    def __init__(self, event_type: EventType, data: Any, source: Optional[str] = None):
        """
        Event 초기화

        Args:
            event_type: 이벤트 타입
            data: 이벤트 데이터
            source: 이벤트 발생 소스
        """
        self.type = event_type
        self.data = data
        self.timestamp = datetime.now()
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
        }


class EventManager:
    """
    이벤트 관리자 (Observer Pattern)

    이벤트 발생 시 등록된 리스너들에게 알림을 전송합니다.

    Attributes:
        listeners: 이벤트 타입별 리스너 목록
        async_mode: 비동기 실행 모드
        event_history: 이벤트 히스토리
    """

    def __init__(self, async_mode: bool = True):
        """
        EventManager 초기화

        Args:
            async_mode: 비동기 실행 모드
        """
        self.listeners: Dict[EventType, List[Callable]] = {}
        self.async_mode = async_mode
        self.event_history: List[Event] = []
        self.max_history = 1000

    def subscribe(self, event_type: EventType, callback: Callable):
        """
        이벤트 구독

        Args:
            event_type: 구독할 이벤트 타입
            callback: 이벤트 발생 시 실행할 콜백 함수
        """
        if event_type not in self.listeners:
            self.listeners[event_type] = []

        if callback not in self.listeners[event_type]:
            self.listeners[event_type].append(callback)
            logger.info(f"이벤트 구독: {event_type.value} -> {callback.__name__}")

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """
        이벤트 구독 해제

        Args:
            event_type: 구독 해제할 이벤트 타입
            callback: 제거할 콜백 함수
        """
        if event_type in self.listeners and callback in self.listeners[event_type]:
            self.listeners[event_type].remove(callback)
            logger.info(f"이벤트 구독 해제: {event_type.value} -> {callback.__name__}")

    async def emit_async(self, event: Event):
        """
        이벤트 발생 (비동기)

        Args:
            event: 발생시킬 이벤트
        """
        # 이벤트 히스토리에 추가
        self._add_to_history(event)

        # 해당 이벤트 타입의 리스너들 실행
        if event.type in self.listeners:
            tasks = []
            for callback in self.listeners[event.type]:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(self._call_async_listener(callback, event))
                else:
                    tasks.append(
                        asyncio.create_task(
                            asyncio.to_thread(self._call_sync_listener, callback, event)
                        )
                    )

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    def emit_sync(self, event: Event):
        """
        이벤트 발생 (동기)

        Args:
            event: 발생시킬 이벤트
        """
        # 이벤트 히스토리에 추가
        self._add_to_history(event)

        # 해당 이벤트 타입의 리스너들 실행
        if event.type in self.listeners:
            for callback in self.listeners[event.type]:
                self._call_sync_listener(callback, event)

    def emit(self, event_type: EventType, data: Any, source: Optional[str] = None):
        """
        이벤트 발생 (모드에 따라 자동 선택)

        Args:
            event_type: 이벤트 타입
            data: 이벤트 데이터
            source: 이벤트 소스
        """
        event = Event(event_type, data, source)

        if self.async_mode:
            # 비동기 모드에서는 태스크 생성
            asyncio.create_task(self.emit_async(event))
        else:
            # 동기 모드에서는 직접 실행
            self.emit_sync(event)

    async def _call_async_listener(self, callback: Callable, event: Event):
        """
        비동기 리스너 호출

        Args:
            callback: 비동기 콜백 함수
            event: 이벤트 객체
        """
        try:
            await callback(event)
        except Exception as e:
            logger.error(
                f"비동기 리스너 실행 중 오류: {callback.__name__}, "
                f"이벤트: {event.type.value}, 오류: {e}"
            )
            # 오류를 다시 발생시켜 상위로 전파
            raise

    def _call_sync_listener(self, callback: Callable, event: Event):
        """
        동기 리스너 호출

        Args:
            callback: 동기 콜백 함수
            event: 이벤트 객체
        """
        try:
            callback(event)
        except Exception as e:
            logger.error(
                f"동기 리스너 실행 중 오류: {callback.__name__}, "
                f"이벤트: {event.type.value}, 오류: {e}"
            )
            # 오류를 다시 발생시켜 상위로 전파
            raise

    def _add_to_history(self, event: Event):
        """
        이벤트 히스토리에 추가

        Args:
            event: 추가할 이벤트
        """
        self.event_history.append(event)

        # 최대 크기 유지
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history :]

    def get_history(
        self, event_type: Optional[EventType] = None, limit: int = 100
    ) -> List[Event]:
        """
        이벤트 히스토리 조회

        Args:
            event_type: 필터링할 이벤트 타입 (None이면 전체)
            limit: 최대 개수

        Returns:
            List[Event]: 이벤트 목록
        """
        history = self.event_history

        if event_type:
            history = [e for e in history if e.type == event_type]

        return history[-limit:]

    def clear_history(self):
        """이벤트 히스토리 초기화"""
        self.event_history.clear()

    def get_listener_count(self, event_type: Optional[EventType] = None) -> int:
        """
        리스너 개수 조회

        Args:
            event_type: 이벤트 타입 (None이면 전체)

        Returns:
            int: 리스너 개수
        """
        if event_type:
            return len(self.listeners.get(event_type, []))
        else:
            return sum(len(listeners) for listeners in self.listeners.values())

    def clear_listeners(self, event_type: Optional[EventType] = None):
        """
        리스너 초기화

        Args:
            event_type: 초기화할 이벤트 타입 (None이면 전체)
        """
        if event_type:
            self.listeners[event_type] = []
        else:
            self.listeners.clear()

        logger.info(f"리스너 초기화: {event_type.value if event_type else '전체'}")
