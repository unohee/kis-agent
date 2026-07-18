"""Deprecated EnhancedWebSocketClient의 데이터 변환 회귀 테스트."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from kis_agent.websocket.enhanced_client import EnhancedWebSocketClient


def _client(tmp_path):
    client = object.__new__(EnhancedWebSocketClient)
    client.stock_codes = ["005930"]
    client.enable_ask_bid = client.enable_program_trading = client.enable_index = True
    client.stock_api = MagicMock()
    client.ws_agent = MagicMock()
    client.ws_agent.connect = AsyncMock()
    client.ws_agent.disconnect = AsyncMock()
    client.ws_agent.get_stats.return_value = {}
    client.ws_agent.subscriptions = []
    client.market_data = {"stocks": {}, "ask_bid": {}, "index": {}, "program": {}}
    client.stock_info = {"005930": "삼성전자"}
    client.callbacks = {key: [] for key in ("on_trade", "on_ask_bid", "on_index", "on_program")}
    client.data_log_file = str(tmp_path / "market.jsonl")
    return client


@pytest.mark.asyncio
async def test_subscription_fetch_handlers_summary_and_lifecycle(tmp_path):
    client = _client(tmp_path)
    client.stock_api.get_stock_info.return_value = __import__("pandas").DataFrame({"prdt_name": ["삼성전자"]})
    await client._init_subscriptions()
    assert client.ws_agent.subscribe.call_count == 6

    client._handle_stock_trade(["005930", "090000", "70000", "x", "1", "0.1"] + ["0"] * 13, {})
    client._handle_stock_ask_bid(["005930", "x", "x"] + ["1"] * 40, {})
    client._handle_index(["0001", "2500", "1", "0.1"] + ["0"] * 6, {})
    client._handle_program_trade(["005930", "090000", "1", "2", "3", "4", "2", "2"] + ["0"] * 3, {})
    assert client.get_market_summary()["stocks"]["005930"]["price"] == 70000.0
    assert client.get_stats()["active_stocks"] == 1
    await client.start()
    await client.stop()
    assert client.ws_agent.connect.await_count == 1
    assert client.ws_agent.disconnect.await_count == 1


@pytest.mark.asyncio
async def test_enhanced_client_callback_exception_and_dynamic_stock_paths(tmp_path):
    client = _client(tmp_path)
    client.stock_api.get_stock_info.side_effect = RuntimeError("offline")
    await client._fetch_stock_info()
    assert client.stock_info["005930"] == "005930"

    for event in client.callbacks:
        client.callbacks[event].append(lambda _data: (_ for _ in ()).throw(RuntimeError("callback")))
    client._handle_stock_trade(["005930", "090000", "bad"] + ["0"] * 16, {})
    client._handle_stock_ask_bid(["005930", "x", "x"] + ["bad"] * 40, {})
    client._handle_index(["0001", "bad"] + ["0"] * 8, {})
    client._handle_program_trade(["005930", "090000", "bad"] + ["0"] * 8, {})

    callbacks = []
    client.callbacks["on_ask_bid"] = [lambda data: callbacks.append(data["code"])]
    client.callbacks["on_program"] = [lambda data: callbacks.append(data["code"])]
    client._handle_stock_ask_bid(["005930", "x", "x"] + ["1"] * 40, {})
    client._handle_program_trade(["005930", "090000", "1", "2", "3", "4", "2", "2"] + ["0"] * 3, {})
    assert callbacks == ["005930", "005930"]

    client.add_stock("000660")
    assert "000660" in client.stock_codes
    client.market_data["stocks"]["000660"] = {}
    client.remove_stock("000660")
    assert "000660" not in client.stock_codes
    client.stock_api.get_stock_info.side_effect = None
    client.stock_api.get_stock_info.return_value = __import__("pandas").DataFrame({"prdt_name": ["SK하이닉스"]})
    client.add_stock("000661")
    assert client.stock_info["000661"] == "SK하이닉스"
    client.data_log_file = str(tmp_path)
    client._log_data("trade", {})
