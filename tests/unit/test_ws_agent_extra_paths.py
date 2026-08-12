"""WSAgent의 메시지·구독 상태 전이 회귀 테스트."""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from websockets.exceptions import ConnectionClosed

import kis_agent.websocket.ws_agent as module
from kis_agent.websocket.ws_agent import WSAgent
from kis_agent.websocket.ws_types import Subscription, SubscriptionType


@pytest.fixture
def agent():
    return WSAgent("approval", url="ws://example", auto_reconnect=False)


def test_market_close_session_windows(monkeypatch):
    class SeoulDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 1, 6, 16, 30, tzinfo=tz)

    monkeypatch.setattr(module, "datetime", SeoulDateTime)
    assert not module._is_after_market_close()

    class NightDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 1, 6, 21, 0, tzinfo=tz)

    monkeypatch.setattr(module, "datetime", NightDateTime)
    assert module._is_after_market_close()
    assert not module._is_after_market_close(has_night_session=True)

    class WeekendDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 1, 4, 10, 0, tzinfo=tz)

    monkeypatch.setattr(module, "datetime", WeekendDateTime)
    assert module._is_after_market_close()


def test_constructor_and_approval_key_guards(agent):
    with pytest.raises(ValueError, match="approval_key"):
        WSAgent("")
    agent.update_approval_key("")
    agent.connected = True
    agent.update_approval_key("new-approval")
    assert agent.approval_key == "new-approval"


def test_subscription_response_and_parse_fallbacks(agent):
    assert not agent._handle_subscription_response({"header": {}, "body": {}})
    assert not agent._handle_subscription_response({"header": {"tr_id": "H0STCNT0"}, "body": {"msg1": "ok"}})
    event = asyncio.Event()
    agent._pending_subscriptions["H0STCNT0_005930"] = event
    assert agent._handle_subscription_response({"header": {"tr_id": "H0STCNT0", "tr_key": "005930"}, "body": {"msg1": "SUBSCRIBE SUCCESS"}})
    assert event.is_set() and agent._subscription_results["H0STCNT0_005930"]
    assert agent._handle_subscription_response({"header": {"tr_id": "H0STCNT0", "tr_key": "005930"}, "body": {"msg1": "UNSUBSCRIBE SUCCESS"}})
    assert agent._parse_message("") == (None, None, None)
    assert agent._parse_message("0|too-short") == (None, None, None)
    agent._pending_subscriptions.clear()
    assert agent._handle_subscription_response({"header": {"tr_id": "H0STCNT0", "tr_key": "005930"}, "body": {"msg1": "UNSUBSCRIBE SUCCESS"}})
    assert not agent._handle_subscription_response({"header": {"tr_id": "H0STCNT0", "tr_key": "005930"}, "body": {"msg1": "unknown"}})


def test_encrypted_parse_and_aes_decryption(agent):
    agent.aes_keys["H0STCNI0"] = ("key", "iv")
    agent._decrypt_aes = MagicMock(return_value="005930^filled")
    assert agent._parse_message("1|H0STCNI0|1|cipher") == (
        "H0STCNI0",
        "005930",
        ["005930", "filled"],
    )

    cipher = MagicMock()
    cipher.decrypt.return_value = b"padded"
    with patch("Crypto.Cipher.AES.new", return_value=cipher), patch.object(
        module, "b64decode", return_value=b"cipher"
    ), patch("Crypto.Util.Padding.unpad", return_value=b"plain"):
        assert WSAgent._decrypt_aes(agent, "key", "iv", "cipher") == "plain"


@pytest.mark.asyncio
async def test_subscribe_all_disconnect_failure_and_exception(agent):
    subs = [Subscription(SubscriptionType.STOCK_TRADE, key) for key in ("1", "2")]
    agent.subscriptions = {f"H0STCNT0_{sub.key}": sub for sub in subs}
    assert await agent._subscribe_all() == {"success": [], "failed": ["H0STCNT0_1", "H0STCNT0_2"]}

    agent.ws = MagicMock(close_code=None)
    agent._send_subscription = AsyncMock(side_effect=[False, RuntimeError("offline")])
    result = await agent._subscribe_all()
    assert result["failed"] == ["H0STCNT0_1", "H0STCNT0_2"]

    many = [Subscription(SubscriptionType.STOCK_TRADE, str(index)) for index in range(10)]
    agent.subscriptions = {f"H0STCNT0_{sub.key}": sub for sub in many}
    agent._send_subscription = AsyncMock(return_value=True)
    result = await agent._subscribe_all()
    assert len(result["success"]) == 10


@pytest.mark.asyncio
async def test_unsubscription_error_and_message_handlers(agent):
    agent.ws = AsyncMock()
    agent.ws.send.side_effect = RuntimeError("closed")
    await agent._send_unsubscription(Subscription(SubscriptionType.STOCK_TRADE, "005930"))

    received = []
    agent.set_default_handler(lambda data, meta: received.append((data, meta)))
    await agent._handle_message("not-a-protocol-message")
    await agent._handle_message(json.dumps({"header": {"tr_id": "UNKNOWN", "tr_key": "x"}, "body": {}}))
    assert received and received[-1][1]["tr_id"] == "UNKNOWN"

    await agent._handle_message(json.dumps({"header": {"tr_id": "H0STCNT0", "tr_key": "x"}, "body": {"msg1": "SUBSCRIBE SUCCESS"}}))
    await agent._handle_message("{invalid")


@pytest.mark.asyncio
async def test_known_message_runs_type_and_default_handlers(agent):
    type_handler = AsyncMock()
    default_handler = AsyncMock()
    agent.register_handler(SubscriptionType.STOCK_TRADE, type_handler)
    agent.set_default_handler(default_handler)
    await agent._handle_message("0|H0STCNT0|0|005930^value")
    type_handler.assert_awaited_once()
    default_handler.assert_awaited_once()

    agent._parse_message = MagicMock(side_effect=RuntimeError("parse"))
    before = agent.stats["errors"]
    await agent._handle_message("message")
    assert agent.stats["errors"] == before + 1


@pytest.mark.asyncio
async def test_handler_cancellation_propagates(agent):
    async def cancelled(_data, _metadata):
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await agent._call_handler(cancelled, {}, {})


@pytest.mark.asyncio
async def test_subscription_retry_wait_and_connection_closed(agent, monkeypatch):
    subscription = Subscription(SubscriptionType.STOCK_TRADE, "005930")
    agent.ws = MagicMock(close_code=None)
    agent.ws.send = AsyncMock(side_effect=RuntimeError("offline"))
    sleep = AsyncMock()
    monkeypatch.setattr(module.asyncio, "sleep", sleep)
    assert not await agent._send_subscription(subscription, max_retries=2)
    sleep.assert_awaited_once_with(0.5)

    agent.ws.send = AsyncMock(side_effect=ConnectionClosed(None, None))
    assert not await agent._send_subscription(subscription, max_retries=1)


@pytest.mark.asyncio
async def test_connection_guards_and_disconnect(agent, monkeypatch):
    assert agent._ws_closed()
    agent.ws = MagicMock(close_code=1000)
    assert agent._ws_closed()
    agent.ws = AsyncMock()
    monkeypatch.setattr(module, "_is_after_market_close", lambda **kwargs: True)
    agent.auto_reconnect = True
    await agent.connect()
    assert not agent.auto_reconnect

    agent.auto_reconnect = True
    task = agent._track_task(asyncio.create_task(asyncio.sleep(10)))
    await agent.disconnect()
    assert agent.ws is None and task.cancelled()
