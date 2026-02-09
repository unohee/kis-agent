"""
WebSocket 연결 관리 모듈

WebSocket 연결의 생명주기를 관리하는 모듈입니다.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

import websockets

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket 연결 관리자

    WebSocket 연결의 생성, 유지, 재연결을 담당합니다.

    Attributes:
        url: WebSocket 서버 URL
        ping_interval: Ping 전송 간격 (초)
        ping_timeout: Ping 응답 대기 시간 (초)
        auto_reconnect: 자동 재연결 여부
    """

    def __init__(
        self,
        url: str = "ws://ops.koreainvestment.com:21000",
        ping_interval: int = 30,
        ping_timeout: int = 30,
        auto_reconnect: bool = True,
    ):
        """
        ConnectionManager 초기화

        Args:
            url: WebSocket 서버 URL
            ping_interval: Ping 전송 간격 (초)
            ping_timeout: Ping 응답 대기 시간 (초)
            auto_reconnect: 자동 재연결 여부
        """
        self.url = url
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.auto_reconnect = auto_reconnect

        self.ws = None
        self.connected = False
        self.last_recv_time = datetime.now()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

    async def connect(self):
        """
        WebSocket 서버에 연결

        Returns:
            WebSocket 객체

        Raises:
            websockets.exceptions.WebSocketException: 연결 실패
        """
        logger.info(f"WebSocket 연결 시작: {self.url}")

        self.ws = await websockets.connect(
            self.url, ping_interval=self.ping_interval, ping_timeout=self.ping_timeout
        )

        self.connected = True
        self.reconnect_attempts = 0
        self.last_recv_time = datetime.now()

        logger.info("WebSocket 연결 성공")
        return self.ws

    async def disconnect(self):
        """WebSocket 연결 종료"""
        if self.ws and not self.ws.closed:
            await self.ws.close()
            logger.info("WebSocket 연결 종료")

        self.connected = False
        self.ws = None

    async def send(self, message: str):
        """
        메시지 전송

        Args:
            message: 전송할 메시지

        Raises:
            RuntimeError: WebSocket이 연결되지 않은 경우
            websockets.exceptions.ConnectionClosed: 연결이 닫힌 경우
        """
        if not self.ws:
            raise RuntimeError("WebSocket이 연결되지 않았습니다")

        if self.ws.closed:
            raise websockets.exceptions.ConnectionClosed(
                None, None, "WebSocket 연결이 닫혔습니다"
            )

        await self.ws.send(message)

    async def recv(self) -> Any:
        """
        메시지 수신

        Returns:
            수신된 메시지

        Raises:
            RuntimeError: WebSocket이 연결되지 않은 경우
            websockets.exceptions.ConnectionClosed: 연결이 닫힌 경우
        """
        if not self.ws:
            raise RuntimeError("WebSocket이 연결되지 않았습니다")

        if self.ws.closed:
            raise websockets.exceptions.ConnectionClosed(
                None, None, "WebSocket 연결이 닫혔습니다"
            )

        message = await self.ws.recv()
        self.last_recv_time = datetime.now()
        return message

    async def reconnect(self):
        """
        재연결 시도

        Returns:
            WebSocket 객체 (성공 시)
            None: 재연결 실패

        Raises:
            RuntimeError: 최대 재연결 시도 횟수 초과
        """
        if not self.auto_reconnect:
            raise RuntimeError("자동 재연결이 비활성화되었습니다")

        if self.reconnect_attempts >= self.max_reconnect_attempts:
            raise RuntimeError(
                f"최대 재연결 시도 횟수({self.max_reconnect_attempts}) 초과"
            )

        self.reconnect_attempts += 1
        logger.info(
            f"재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts}"
        )

        # 이전 연결 정리
        await self.disconnect()

        # 재연결 대기 (지수 백오프)
        wait_time = min(2**self.reconnect_attempts, 60)
        await asyncio.sleep(wait_time)

        # 재연결 시도
        return await self.connect()

    def is_alive(self) -> bool:
        """
        연결 상태 확인

        Returns:
            bool: 연결 상태
        """
        return self.connected and self.ws is not None and not self.ws.closed

    def get_stats(self) -> Dict[str, Any]:
        """
        연결 통계 반환

        Returns:
            Dict[str, Any]: 연결 통계 정보
        """
        return {
            "connected": self.connected,
            "url": self.url,
            "last_recv_time": (
                self.last_recv_time.isoformat() if self.last_recv_time else None
            ),
            "reconnect_attempts": self.reconnect_attempts,
            "websocket_closed": self.ws.closed if self.ws else True,
        }
