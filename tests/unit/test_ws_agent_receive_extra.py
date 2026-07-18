"""WSAgent 수신 루프의 정상·ping·오류 종료 경로 테스트."""

from unittest.mock import AsyncMock, MagicMock

import pytest

import kis_agent.websocket.ws_agent as module
from kis_agent.websocket.ws_agent import WSAgent


@pytest.mark.asyncio
async def test_receive_loop_handles_message_and_stops_disconnected():
    agent = WSAgent("approval", auto_reconnect=False)
    agent.connected = True
    websocket = type("Socket", (), {"recv": AsyncMock(return_value="message")})()

    async def handled(_data):
        agent.connected = False

    agent._handle_message = handled
    assert await agent._receive_loop(websocket) == "disconnected"


@pytest.mark.asyncio
async def test_receive_loop_ping_success_and_generic_error():
    agent = WSAgent("approval", auto_reconnect=False)
    agent.connected = True
    agent.ping_interval = 0.01
    agent.ping_timeout = 0.01

    async def timeout_recv(_self):
        raise TimeoutError

    async def ping(_self):
        agent.connected = False
        future = __import__("asyncio").get_running_loop().create_future()
        future.set_result(None)
        return future

    websocket = type("Socket", (), {"recv": timeout_recv, "ping": ping})()
    assert await agent._receive_loop(websocket) == "disconnected"

    agent.connected = True
    websocket.recv = AsyncMock(side_effect=RuntimeError("bad socket"))
    assert await agent._receive_loop(websocket) == "error"


@pytest.mark.asyncio
async def test_connect_fatal_auth_error_cleans_state(monkeypatch):
    agent = WSAgent("approval", url="ws://example", auto_reconnect=True, client=None)

    class FailingConnection:
        async def __aenter__(self):
            raise RuntimeError("403 forbidden")

        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr(module, "_is_after_market_close", lambda **_kwargs: False)
    monkeypatch.setattr(module.websockets, "connect", lambda *_args, **_kwargs: FailingConnection())
    await agent.connect()
    assert not agent.auto_reconnect
    assert not agent.connected and agent.ws is None


@pytest.mark.asyncio
async def test_connect_subscribes_then_stops_on_normal_disconnect(monkeypatch):
    agent = WSAgent("approval", url="ws://example", auto_reconnect=True)
    websocket = AsyncMock()

    class Connection:
        async def __aenter__(self):
            return websocket

        async def __aexit__(self, *_args):
            return False

    async def receive_loop(_websocket):
        return "disconnected"

    monkeypatch.setattr(module, "_is_after_market_close", lambda **_kwargs: False)
    monkeypatch.setattr(module.websockets, "connect", lambda *_args, **_kwargs: Connection())
    monkeypatch.setattr(module.asyncio, "sleep", AsyncMock())
    agent._receive_loop = receive_loop
    agent._subscribe_all = AsyncMock(return_value={})

    await agent.connect()

    agent._subscribe_all.assert_awaited_once()
    assert not agent.connected and agent.ws is None
    assert agent.auto_reconnect


@pytest.mark.asyncio
async def test_receive_loop_stops_after_repeated_ping_timeouts(monkeypatch):
    agent = WSAgent("approval", auto_reconnect=False)
    agent.connected = True
    agent.ping_interval = 0.001
    agent.ping_timeout = 0.001

    async def timeout_recv(_self):
        raise TimeoutError

    async def ping(_self):
        return __import__("asyncio").get_running_loop().create_future()

    websocket = type("Socket", (), {"recv": timeout_recv, "ping": ping})()
    monkeypatch.setattr(module.asyncio, "sleep", AsyncMock())
    assert await agent._receive_loop(websocket) == "ping_failed"


@pytest.mark.asyncio
async def test_receive_loop_reports_cancelled_and_connection_closed():
    agent = WSAgent("approval", auto_reconnect=False)
    agent.connected = True
    websocket = type("Socket", (), {"recv": AsyncMock(side_effect=__import__("asyncio").CancelledError())})()
    assert await agent._receive_loop(websocket) == "cancelled"

    from websockets.exceptions import ConnectionClosed

    agent.connected = True
    websocket.recv = AsyncMock(side_effect=ConnectionClosed(None, None))
    assert await agent._receive_loop(websocket) == "connection_closed"


@pytest.mark.asyncio
async def test_receive_loop_stops_after_repeated_ping_errors(monkeypatch):
    agent = WSAgent("approval", auto_reconnect=False)
    agent.connected = True
    agent.ping_interval = 0.001
    agent.ping_timeout = 0.001

    async def timeout_recv(_self):
        raise TimeoutError

    async def broken_ping(_self):
        raise RuntimeError("ping")

    websocket = type("Socket", (), {"recv": timeout_recv, "ping": broken_ping})()
    monkeypatch.setattr(module.asyncio, "sleep", AsyncMock())
    assert await agent._receive_loop(websocket) == "ping_failed"


@pytest.mark.asyncio
async def test_disconnect_cancels_background_tasks_and_exposes_state():
    agent = WSAgent("approval", auto_reconnect=True)
    agent.connected = True
    agent.active_subscriptions.add("H0STCNT0:005930")
    agent.ws = type("Socket", (), {"close": AsyncMock()})()
    task = __import__("asyncio").create_task(__import__("asyncio").sleep(60))
    agent._background_tasks.add(task)

    await agent.disconnect()

    agent.ws = None
    assert task.cancelled()
    assert not agent.is_connected()
    assert agent.get_active_subscriptions() == ["H0STCNT0:005930"]
    assert isinstance(agent.get_stats(), dict)


@pytest.mark.asyncio
async def test_subscription_send_rejects_closed_socket_and_unsubscribes():
    agent = WSAgent("approval", auto_reconnect=False)
    sub_id = agent.subscribe(module.SubscriptionType.STOCK_TRADE, "005930")
    subscription = agent.subscriptions[sub_id]
    assert await agent._send_subscription(subscription, max_retries=1) is False

    agent.ws = type("Socket", (), {"send": AsyncMock()})()
    agent.active_subscriptions.add(sub_id)
    await agent._send_unsubscription(subscription)
    payload = __import__("json").loads(agent.ws.send.await_args.args[0])
    assert payload["header"]["tr_type"] == "2"
    assert sub_id not in agent.active_subscriptions


@pytest.mark.asyncio
async def test_subscribe_async_handles_disconnected_duplicate_and_failed_send():
    agent = WSAgent("approval", auto_reconnect=False)
    sub_type = module.SubscriptionType.STOCK_TRADE

    sub_id, success = await agent.subscribe_async(sub_type, "005930")
    assert success is False and sub_id in agent.subscriptions

    duplicate_id, duplicate_success = await agent.subscribe_async(sub_type, "005930")
    assert (duplicate_id, duplicate_success) == (sub_id, True)

    agent.connected = True
    agent.ws = type("Socket", (), {})()
    agent._ws_closed = lambda: False
    agent._send_subscription = AsyncMock(return_value=False)
    failed_id, failed_success = await agent.subscribe_async(sub_type, "000660")
    assert failed_success is False
    assert failed_id not in agent.subscriptions


@pytest.mark.asyncio
async def test_connect_cancels_slow_subscriptions_after_receive_loop_exits(monkeypatch):
    agent = WSAgent(
        "approval", url="ws://example", auto_reconnect=True, max_reconnect_attempts=1
    )
    cancelled = False

    class Connection:
        async def __aenter__(self):
            return AsyncMock()

        async def __aexit__(self, *_args):
            return False

    async def receive_loop(_websocket):
        return "connection_closed"

    async def slow_subscribe_all():
        nonlocal cancelled
        try:
            await __import__("asyncio").sleep(60)
        except __import__("asyncio").CancelledError:
            cancelled = True
            raise

    monkeypatch.setattr(module, "_is_after_market_close", lambda **_kwargs: False)
    monkeypatch.setattr(module.websockets, "connect", lambda *_args, **_kwargs: Connection())
    agent._receive_loop = receive_loop
    agent._subscribe_all = slow_subscribe_all

    await agent.connect()

    assert cancelled
    assert not agent.auto_reconnect
    assert agent.stats["reconnects"] == 0


@pytest.mark.asyncio
async def test_connect_refreshes_approval_key_after_fatal_error(monkeypatch):
    client = type("Client", (), {"get_ws_approval_key": lambda *_args, **_kwargs: "fresh-key"})()
    agent = WSAgent(
        "stale-key", url="ws://example", auto_reconnect=True, max_reconnect_attempts=1, client=client
    )

    class FailingConnection:
        async def __aenter__(self):
            raise RuntimeError("403 forbidden")

        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr(module, "_is_after_market_close", lambda **_kwargs: False)
    monkeypatch.setattr(module.websockets, "connect", lambda *_args, **_kwargs: FailingConnection())

    await agent.connect()

    assert agent.approval_key == "fresh-key"
    assert not agent.auto_reconnect
    assert agent.stats["reconnects"] == 0


@pytest.mark.asyncio
async def test_connect_waits_for_receive_loop_after_subscriptions_finish(monkeypatch):
    agent = WSAgent("approval", url="ws://example", auto_reconnect=True)
    ready = __import__("asyncio").Event()

    class Connection:
        async def __aenter__(self):
            return AsyncMock()

        async def __aexit__(self, *_args):
            return False

    async def subscribe_all():
        ready.set()
        return {}

    async def receive_loop(_websocket):
        await ready.wait()
        await __import__("asyncio").sleep(0.01)
        return "cancelled"

    monkeypatch.setattr(module, "_is_after_market_close", lambda **_kwargs: False)
    monkeypatch.setattr(
        module.websockets, "connect", lambda *_args, **_kwargs: Connection()
    )
    agent._subscribe_all = subscribe_all
    agent._receive_loop = receive_loop

    await agent.connect()

    assert not agent.connected


@pytest.mark.asyncio
async def test_connect_fatal_refresh_exception_stops(monkeypatch):
    client = MagicMock()
    client.get_ws_approval_key.side_effect = RuntimeError("refresh")
    agent = WSAgent(
        "approval", url="ws://example", auto_reconnect=True, client=client
    )

    class FailingConnection:
        async def __aenter__(self):
            raise RuntimeError("403 forbidden")

        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr(module, "_is_after_market_close", lambda **_kwargs: False)
    monkeypatch.setattr(
        module.websockets, "connect", lambda *_args, **_kwargs: FailingConnection()
    )
    await agent.connect()
    assert not agent.auto_reconnect


@pytest.mark.asyncio
async def test_connect_cancels_pending_receive_task_during_setup_error(monkeypatch):
    agent = WSAgent(
        "approval",
        url="ws://example",
        auto_reconnect=True,
        max_reconnect_attempts=1,
    )
    receive_cancelled = False

    class Connection:
        async def __aenter__(self):
            return AsyncMock()

        async def __aexit__(self, *_args):
            return False

    async def receive_loop(_websocket):
        nonlocal receive_cancelled
        try:
            await __import__("asyncio").sleep(60)
        except __import__("asyncio").CancelledError:
            receive_cancelled = True
            raise

    original_sleep = module.asyncio.sleep

    async def setup_failure(seconds):
        if seconds == 0.1:
            raise RuntimeError("setup")
        await original_sleep(seconds)

    monkeypatch.setattr(module, "_is_after_market_close", lambda **_kwargs: False)
    monkeypatch.setattr(
        module.websockets, "connect", lambda *_args, **_kwargs: Connection()
    )
    monkeypatch.setattr(module.asyncio, "sleep", setup_failure)
    agent._receive_loop = receive_loop

    await agent.connect()

    assert not agent.connected and agent.ws is None


@pytest.mark.asyncio
async def test_connect_stops_reconnect_at_market_close(monkeypatch):
    agent = WSAgent("approval", url="ws://example", auto_reconnect=True)

    class FailingConnection:
        async def __aenter__(self):
            raise RuntimeError("offline")

        async def __aexit__(self, *_args):
            return False

    market_checks = iter([False, True])
    monkeypatch.setattr(
        module, "_is_after_market_close", lambda **_kwargs: next(market_checks)
    )
    monkeypatch.setattr(
        module.websockets, "connect", lambda *_args, **_kwargs: FailingConnection()
    )

    await agent.connect()

    assert not agent.auto_reconnect


@pytest.mark.asyncio
async def test_connect_applies_backoff_before_next_attempt(monkeypatch):
    agent = WSAgent(
        "approval",
        url="ws://example",
        auto_reconnect=True,
        max_reconnect_attempts=2,
    )

    class FailingConnection:
        async def __aenter__(self):
            raise RuntimeError("offline")

        async def __aexit__(self, *_args):
            return False

    sleep_calls = []

    async def stop_after_backoff(seconds):
        sleep_calls.append(seconds)
        agent.auto_reconnect = False

    monkeypatch.setattr(module, "_is_after_market_close", lambda **_kwargs: False)
    monkeypatch.setattr(
        module.websockets, "connect", lambda *_args, **_kwargs: FailingConnection()
    )
    monkeypatch.setattr(module.asyncio, "sleep", stop_after_backoff)

    await agent.connect()

    assert agent.stats["reconnects"] == 1
    assert sleep_calls == [5]


@pytest.mark.asyncio
async def test_sync_subscription_and_unsubscribe_manage_background_tasks():
    agent = WSAgent("approval", auto_reconnect=False)
    agent.connected = True
    agent.ws = type("Socket", (), {"close_code": None})()
    agent._send_subscription = AsyncMock(return_value=True)
    agent._send_unsubscription = AsyncMock()

    sub_id = agent.subscribe(module.SubscriptionType.STOCK_TRADE, "005930")
    await __import__("asyncio").sleep(0)
    agent._send_subscription.assert_awaited_once()

    agent.unsubscribe(sub_id)
    await __import__("asyncio").sleep(0)
    agent._send_unsubscription.assert_awaited_once()
    agent.unsubscribe("missing")

    cancelled = __import__("asyncio").create_task(__import__("asyncio").sleep(60))
    cancelled.cancel()
    with pytest.raises(__import__("asyncio").CancelledError):
        await cancelled
    agent._on_subscription_task_done(cancelled, "cancelled")


@pytest.mark.asyncio
async def test_send_subscription_records_rejected_response():
    agent = WSAgent("approval", auto_reconnect=False)
    subscription = module.Subscription(module.SubscriptionType.STOCK_TRADE, "005930")

    async def send(_self, _message):
        sub_id = "H0STCNT0_005930"
        agent._subscription_errors[sub_id] = "rejected"
        agent._pending_subscriptions[sub_id].set()

    agent.ws = type("Socket", (), {"close_code": None, "send": send})()
    assert not await agent._send_subscription(subscription, max_retries=1)
    assert not agent._pending_subscriptions
