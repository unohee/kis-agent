"""Deprecated WebSocket factory/builder의 구성 계약 테스트."""

from unittest.mock import MagicMock, patch

import pytest

from kis_agent.websocket.factory import ClientType, WebSocketClientBuilder, WebSocketClientFactory


@pytest.fixture
def factory_mocks():
    with patch("kis_agent.websocket.factory.ConnectionManager") as connection, patch(
        "kis_agent.websocket.factory.RefactoredWebSocketClient"
    ) as client:
        client.return_value = MagicMock()
        yield connection, client


def test_factory_builds_every_client_type(factory_mocks):
    connection, client = factory_mocks
    basic = WebSocketClientFactory.create_client(ClientType.BASIC, "key", url="ws://basic")
    connection.assert_called_with(url="ws://basic", auto_reconnect=False)
    assert basic is client.return_value

    realtime = WebSocketClientFactory.create_client(
        ClientType.REALTIME, "key", stock_codes=["005930"], enable_orderbook=True, enable_program_trading=True
    )
    realtime.add_stock_subscription.assert_called_once_with("005930")
    realtime.enable_orderbook_subscription.assert_called_once()
    realtime.enable_program_trading_subscription.assert_called_once()
    realtime.reset_mock()

    monitoring = WebSocketClientFactory.create_client(ClientType.MONITORING, "key", major_stocks=["000660"])
    monitoring.enable_index_subscription.assert_called_once()
    monitoring.enable_program_trading_subscription.assert_called_once()
    monitoring.add_stock_subscription.assert_called_once_with("000660")

    WebSocketClientFactory.create_client(ClientType.BACKTEST, "key")
    assert client.call_args.kwargs["data_recording"] is True
    with pytest.raises(ValueError, match="지원하지 않는"):
        WebSocketClientFactory.create_client("bad", "key")


def test_builder_fluent_options_build_expected_client(factory_mocks):
    connection, client = factory_mocks
    built = (
        WebSocketClientBuilder("key")
        .with_url("ws://custom")
        .with_auto_reconnect(False)
        .with_ping_settings(1, 2)
        .add_stock("005930")
        .add_stocks(["005930", "000660"])
        .with_index_subscription()
        .with_orderbook_subscription()
        .with_program_trading_subscription()
        .with_logging(False)
        .with_metrics(False)
        .build()
    )
    connection.assert_called_once_with(url="ws://custom", auto_reconnect=False, ping_interval=1, ping_timeout=2)
    assert built is client.return_value
    assert built.add_stock_subscription.call_args_list[0].args == ("005930",)
    assert built.add_stock_subscription.call_args_list[1].args == ("000660",)
    built.enable_index_subscription.assert_called_once()
    built.enable_orderbook_subscription.assert_called_once()
    built.enable_program_trading_subscription.assert_called_once()
    assert client.call_args.kwargs["enable_logging"] is False
    assert client.call_args.kwargs["enable_metrics"] is False
