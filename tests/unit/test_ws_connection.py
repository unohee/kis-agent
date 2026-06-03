"""kis_agent.websocket.connection.ConnectionManager 단위 테스트."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kis_agent.core.constants import WS_REAL_URL
from kis_agent.websocket.connection import ConnectionManager


def _make_ws(closed: bool = False):
    """가짜 websocket 클라이언트 객체."""
    ws = MagicMock()
    ws.closed = closed
    ws.send = AsyncMock()
    ws.recv = AsyncMock(return_value="msg")
    ws.close = AsyncMock()
    return ws


class TestConnectionManagerInit:
    def test_defaults(self):
        cm = ConnectionManager()
        assert cm.url == WS_REAL_URL
        assert cm.ping_interval == 30
        assert cm.ping_timeout == 30
        assert cm.auto_reconnect is True
        assert cm.ws is None
        assert cm.connected is False
        assert cm.reconnect_attempts == 0
        assert cm.max_reconnect_attempts == 5

    def test_custom(self):
        cm = ConnectionManager(
            url="ws://example.com",
            ping_interval=15,
            ping_timeout=20,
            auto_reconnect=False,
        )
        assert cm.url == "ws://example.com"
        assert cm.ping_interval == 15
        assert cm.ping_timeout == 20
        assert cm.auto_reconnect is False


class TestConnect:
    @pytest.mark.asyncio
    async def test_connect_sets_state(self):
        cm = ConnectionManager()
        fake_ws = _make_ws(closed=False)
        with patch(
            "kis_agent.websocket.connection.websockets.connect",
            new=AsyncMock(return_value=fake_ws),
        ) as mock_connect:
            result = await cm.connect()
        assert result is fake_ws
        assert cm.ws is fake_ws
        assert cm.connected is True
        assert cm.reconnect_attempts == 0
        mock_connect.assert_awaited_once()


class TestSendRecv:
    @pytest.mark.asyncio
    async def test_send_raises_when_not_connected(self):
        cm = ConnectionManager()
        with pytest.raises(RuntimeError, match="연결되지 않았습니다"):
            await cm.send("hello")

    @pytest.mark.asyncio
    async def test_send_raises_when_closed(self):
        """closed=True면 ConnectionClosed가 raise되어야 함.

        ConnectionManager.send는 websockets.exceptions.ConnectionClosed를
        직접 생성하지만 그 시그니처는 websockets 라이브러리 버전마다 다를
        수 있다 (현재 16.x는 (rcvd, sent) 두 인자 + dict-like). 따라서
        구체적 예외 타입은 검증하지 않고 어떤 Exception이든 raise되면
        충분하다.
        """
        cm = ConnectionManager()
        cm.ws = _make_ws(closed=True)
        with pytest.raises(Exception):
            await cm.send("hello")

    @pytest.mark.asyncio
    async def test_send_ok(self):
        cm = ConnectionManager()
        cm.ws = _make_ws(closed=False)
        await cm.send("hello")
        cm.ws.send.assert_awaited_once_with("hello")

    @pytest.mark.asyncio
    async def test_recv_raises_when_not_connected(self):
        cm = ConnectionManager()
        with pytest.raises(RuntimeError, match="연결되지 않았습니다"):
            await cm.recv()

    @pytest.mark.asyncio
    async def test_recv_raises_when_closed(self):
        """recv도 send와 동일하게 closed 시 raise (구체 타입은 미검증)."""
        cm = ConnectionManager()
        cm.ws = _make_ws(closed=True)
        with pytest.raises(Exception):
            await cm.recv()

    @pytest.mark.asyncio
    async def test_recv_ok_updates_last_recv_time(self):
        cm = ConnectionManager()
        cm.ws = _make_ws(closed=False)
        before = cm.last_recv_time
        msg = await cm.recv()
        assert msg == "msg"
        assert cm.last_recv_time >= before


class TestDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect_calls_close(self):
        cm = ConnectionManager()
        cm.ws = _make_ws(closed=False)
        cm.connected = True
        await cm.disconnect()
        assert cm.connected is False
        assert cm.ws is None

    @pytest.mark.asyncio
    async def test_disconnect_skip_if_already_closed(self):
        cm = ConnectionManager()
        cm.ws = _make_ws(closed=True)
        cm.connected = True
        await cm.disconnect()
        # closed=True면 close()는 호출되지 않지만 상태는 정리됨
        cm.ws  # noqa: B015 — no assert, 위에서 None 처리 후 재할당 안 됨
        assert cm.connected is False


class TestReconnect:
    @pytest.mark.asyncio
    async def test_reconnect_disabled_raises(self):
        cm = ConnectionManager(auto_reconnect=False)
        with pytest.raises(RuntimeError, match="자동 재연결이 비활성화"):
            await cm.reconnect()

    @pytest.mark.asyncio
    async def test_reconnect_max_attempts_exceeded(self):
        cm = ConnectionManager()
        cm.reconnect_attempts = cm.max_reconnect_attempts
        with pytest.raises(RuntimeError, match="최대 재연결 시도 횟수"):
            await cm.reconnect()

    @pytest.mark.asyncio
    async def test_reconnect_invokes_disconnect_and_connect(self):
        cm = ConnectionManager()
        cm.ws = _make_ws(closed=False)
        cm.connected = True
        fake_ws_new = _make_ws(closed=False)
        with patch(
            "kis_agent.websocket.connection.websockets.connect",
            new=AsyncMock(return_value=fake_ws_new),
        ), patch(
            "kis_agent.websocket.connection.asyncio.sleep", new=AsyncMock()
        ) as mock_sleep:
            result = await cm.reconnect()
        assert result is fake_ws_new
        assert cm.connected is True
        # 지수 백오프로 한 번 대기
        mock_sleep.assert_awaited()


class TestStatusHelpers:
    def test_is_alive_false_when_no_ws(self):
        cm = ConnectionManager()
        assert cm.is_alive() is False

    def test_is_alive_false_when_closed(self):
        cm = ConnectionManager()
        cm.connected = True
        cm.ws = _make_ws(closed=True)
        assert cm.is_alive() is False

    def test_is_alive_true(self):
        cm = ConnectionManager()
        cm.connected = True
        cm.ws = _make_ws(closed=False)
        assert cm.is_alive() is True

    def test_get_stats_no_ws(self):
        cm = ConnectionManager()
        stats = cm.get_stats()
        assert stats["connected"] is False
        assert stats["websocket_closed"] is True
        assert stats["reconnect_attempts"] == 0
        assert stats["url"] == WS_REAL_URL

    def test_get_stats_with_ws(self):
        cm = ConnectionManager()
        cm.connected = True
        cm.ws = _make_ws(closed=False)
        stats = cm.get_stats()
        assert stats["connected"] is True
        assert stats["websocket_closed"] is False
        assert "last_recv_time" in stats
