"""리팩토링 WebSocket 클라이언트의 수명주기·구독·라우팅 테스트."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

import kis_agent.websocket.refactored_client as refactored_module
from kis_agent.websocket.event_manager import EventType
from kis_agent.websocket.refactored_client import RefactoredWebSocketClient


def _client(metrics=True, recording=False):
    connection = MagicMock()
    connection.connect = AsyncMock()
    connection.disconnect = AsyncMock()
    connection.send = AsyncMock()
    processor = MagicMock()
    events = MagicMock()
    registry = MagicMock()
    client = RefactoredWebSocketClient("key", connection, processor, events, registry, enable_metrics=metrics, data_recording=recording)
    return client, connection, processor, events, registry


@pytest.mark.asyncio
async def test_connection_and_subscription_lifecycle():
    client, connection, _, events, _ = _client()
    connection.is_alive.return_value = False
    with pytest.raises(RuntimeError):
        await client.subscribe_stock("005930")
    with pytest.raises(RuntimeError):
        await client.unsubscribe_stock("005930")
    with pytest.raises(RuntimeError):
        await client.subscribe_index()

    connection.is_alive.return_value = True
    await client.connect()
    await client.subscribe_stock("005930", with_orderbook=True)
    await client.unsubscribe_stock("005930")
    await client.subscribe_index(["0001"])
    await client.subscribe_index()
    await client.disconnect()
    payloads = [json.loads(call.args[0]) for call in connection.send.await_args_list]
    assert [payload["body"]["input"]["tr_id"] for payload in payloads] == ["H0STCNT0", "H0STASP0", "H0STCNT0", "H0IF1000", "H0IF1000", "H0IF1000", "H0IF1000"]
    assert client.metrics["start_time"] is not None
    assert events.emit.call_count == 2


@pytest.mark.asyncio
async def test_run_routes_messages_records_and_updates_metrics(tmp_path):
    client, connection, processor, events, registry = _client(recording=False)
    client.data_recording = True
    client.data_log_file = tmp_path / "data.jsonl"
    connection.is_alive.side_effect = [True, True, True, True, False]
    connection.recv = AsyncMock(side_effect=["trade", "book", "index", "program"])
    processor.process_message.side_effect = [{}, {}, {}, {}]
    registry.process.side_effect = [
        {"type": "trade", "code": "1"}, {"type": "orderbook"}, {"type": "index"}, {"type": "program_trading"}
    ]
    await client.run()
    emitted_types = [call.args[0] for call in events.emit.call_args_list]
    assert emitted_types == [EventType.TRADE_UPDATE, EventType.ORDERBOOK_UPDATE, EventType.INDEX_UPDATE, EventType.PROGRAM_TRADING_UPDATE]
    assert client.metrics["messages_received"] == client.metrics["messages_processed"] == 4
    assert len(client.data_log_file.read_text().splitlines()) == 4


def test_helpers_recording_callbacks_metrics_and_error(tmp_path):
    client, connection, processor, events, _ = _client()
    client._record_data({"x": 1})  # 기록 파일 없는 경우
    client.data_log_file = tmp_path / "data.jsonl"
    client._record_data({"x": 1})
    assert client.data_log_file.read_text().strip() == '{"x": 1}'
    client.add_stock_subscription("005930")
    client.enable_index_subscription()
    client.enable_orderbook_subscription()
    client.enable_program_trading_subscription()
    callback = MagicMock()
    client.register_callback(EventType.TRADE_UPDATE, callback)
    assert client.get_latest_data("005930") is processor.latest_data.get.return_value
    assert client.get_indicators("005930") is processor.calculate_indicators.return_value
    client.metrics["start_time"] = datetime.now()
    connection.get_stats.return_value = {"connected": True}
    assert client.get_metrics()["connection_status"] == {"connected": True}
    client._on_connection_opened(MagicMock(timestamp="now"))
    client._on_connection_closed(MagicMock(timestamp="now"))
    with pytest.raises(RuntimeError, match="boom"):
        client._on_error(MagicMock(data="boom"))
    assert client.metrics["errors"] == 1
    disabled, *_ = _client(metrics=False)
    assert disabled.get_metrics() == {}


@pytest.mark.asyncio
async def test_recording_setup_and_run_without_handler_result(tmp_path, monkeypatch):
    monkeypatch.setattr(refactored_module, "Path", lambda _: tmp_path)
    client, connection, processor, _, registry = _client(recording=True)
    assert client.data_log_file.parent == tmp_path
    connection.is_alive.side_effect = [True, False]
    connection.recv = AsyncMock(return_value="ignored")
    processor.process_message.return_value = {}
    registry.process.return_value = None
    await client.run()
    assert client.metrics["messages_received"] == 1
    assert client.metrics["messages_processed"] == 0
