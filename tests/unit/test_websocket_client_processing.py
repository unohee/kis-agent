"""레거시 WebSocket 클라이언트의 순수 메시지·지표 처리 회귀 테스트."""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from kis_agent.websocket.client import KisWebSocket


def _ws(tmp_path):
    ws = object.__new__(KisWebSocket)
    ws.client = MagicMock()
    ws.approval_key = "approval"
    ws.stock_codes = ["005930"]
    ws.trade_history = {"005930": []}
    ws.latest_trade = {"005930": None}
    ws.latest_ask_bid = {}
    ws.latest_index = {}
    ws.latest_index_expected = {}
    ws.latest_program_trading = {}
    ws.latest_expected_stock = {}
    ws.prev_indicators = {"005930": (None, None)}
    ws.subscribed_stocks = {"005930"}
    ws.stock_names = {"005930": "삼성전자"}
    ws.open_prices = {}
    ws.purchase_prices = {}
    ws.trade_log_file = str(tmp_path / "trade.jsonl")
    ws.enable_ask_bid = ws.enable_index = ws.enable_program_trading = True
    ws.enable_expected_index = ws.enable_expected_stock = True
    return ws


def test_constructor_initializes_all_runtime_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = MagicMock()
    with patch("kis_agent.websocket.client.StockAPI") as stock_api, pytest.deprecated_call():
        ws = KisWebSocket(
            client,
            {"account": "123"},
            stock_codes=["005930"],
            purchase_prices={"005930": (70000, 1)},
            enable_ask_bid=True,
            enable_expected_index=True,
            enable_expected_stock=True,
        )

    stock_api.assert_called_once_with(client=client, account_info={"account": "123"})
    assert ws.stock_codes == ["005930"]
    assert ws.latest_trade == {"005930": None}
    assert ws.trade_history == {"005930": []}
    assert ws.purchase_prices["005930"] == (70000, 1)
    assert ws.subscribed_stocks == {"005930"}
    assert ws.enable_ask_bid and ws.enable_expected_index and ws.enable_expected_stock
    assert ws.ping_interval == 30 and ws.max_ping_retries == 3


@pytest.mark.asyncio
async def test_connect_sends_enabled_subscriptions_and_stops_on_event(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.url = "ws://example"
    ws.ping_interval = ws.ping_timeout = 1
    ws.enable_index = ws.enable_ask_bid = ws.enable_program_trading = True
    ws.enable_expected_index = ws.enable_expected_stock = True
    for method in (
        "get_approval",
        "load_historical_data",
        "fetch_stock_names",
        "fetch_open_prices",
        "load_initial_balance",
        "display_balance_info",
    ):
        monkeypatch.setattr(ws, method, MagicMock())

    stop_event = asyncio.Event()

    async def recv(_self):
        stop_event.set()
        return "PINGPONG"

    socket = type("Socket", (), {"send": AsyncMock(), "recv": recv})()

    class Connection:
        async def __aenter__(self):
            return socket

        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr(
        "kis_agent.websocket.client.websockets.connect",
        lambda *_args, **_kwargs: Connection(),
    )
    sleep_calls = 0

    async def set_stop(_seconds):
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls >= 7:
            stop_event.set()

    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", set_stop)

    await ws.connect(stop_event=stop_event)

    tr_ids = {json.loads(call.args[0])["body"]["input"]["tr_id"] for call in socket.send.await_args_list}
    assert {
        "H0IF1000",
        "H0UPANC0",
        "H0STCNT0",
        "H0STASP0",
        "H0GSCNT0",
        "H0UNANC0",
    } <= tr_ids


@pytest.mark.asyncio
async def test_connect_receives_trade_message_during_market_session(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.url = "ws://example"
    ws.ping_interval = ws.ping_timeout = 1
    ws.enable_index = ws.enable_ask_bid = ws.enable_program_trading = False
    ws.enable_expected_index = ws.enable_expected_stock = False
    for method in (
        "get_approval",
        "load_historical_data",
        "fetch_stock_names",
        "fetch_open_prices",
        "load_initial_balance",
        "display_balance_info",
    ):
        monkeypatch.setattr(ws, method, MagicMock())
    ws.handle_message = MagicMock()
    stop_event = asyncio.Event()

    class MarketDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 1, 6, 10, 0, tzinfo=tz)

    async def recv(_self):
        stop_event.set()
        return "0|H0STCNT0|001|005930^093000^70000"

    socket = type("Socket", (), {"send": AsyncMock(), "recv": recv})()

    class Connection:
        async def __aenter__(self):
            return socket

        async def __aexit__(self, *_args):
            return False

    import datetime as datetime_module

    monkeypatch.setattr(datetime_module, "datetime", MarketDateTime)
    monkeypatch.setattr(
        "kis_agent.websocket.client.websockets.connect",
        lambda *_args, **_kwargs: Connection(),
    )
    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", AsyncMock())

    await ws.connect(stop_event=stop_event)

    ws.handle_message.assert_called_once_with("0|H0STCNT0|001|005930^093000^70000")


@pytest.mark.asyncio
async def test_connect_pings_after_receive_timeout(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.url = "ws://example"
    ws.ping_interval = ws.ping_timeout = 1
    ws.stock_codes = []
    ws.enable_index = ws.enable_ask_bid = ws.enable_program_trading = False
    ws.enable_expected_index = ws.enable_expected_stock = False
    for method in (
        "get_approval",
        "load_historical_data",
        "fetch_stock_names",
        "fetch_open_prices",
        "load_initial_balance",
        "display_balance_info",
    ):
        monkeypatch.setattr(ws, method, MagicMock())
    stop_event = asyncio.Event()

    class MarketDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 1, 6, 10, 0, tzinfo=tz)

    async def recv(_self):
        raise asyncio.TimeoutError

    pings = 0

    async def ping(_self):
        nonlocal pings
        pings += 1
        stop_event.set()
        future = asyncio.get_running_loop().create_future()
        future.set_result(None)
        return future

    socket = type("Socket", (), {"send": AsyncMock(), "recv": recv, "ping": ping})()

    class Connection:
        async def __aenter__(self):
            return socket

        async def __aexit__(self, *_args):
            return False

    import datetime as datetime_module

    monkeypatch.setattr(datetime_module, "datetime", MarketDateTime)
    monkeypatch.setattr(
        "kis_agent.websocket.client.websockets.connect",
        lambda *_args, **_kwargs: Connection(),
    )
    await ws.connect(stop_event=stop_event)
    assert stop_event.is_set() and pings == 1


@pytest.mark.asyncio
async def test_connect_reconnects_after_connection_error(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.url = "ws://example"
    ws.ping_interval = ws.ping_timeout = 1
    ws.stock_codes = []
    ws.enable_index = ws.enable_ask_bid = ws.enable_program_trading = False
    ws.enable_expected_index = ws.enable_expected_stock = False
    for method in (
        "get_approval",
        "load_historical_data",
        "fetch_stock_names",
        "fetch_open_prices",
        "load_initial_balance",
        "display_balance_info",
    ):
        monkeypatch.setattr(ws, method, MagicMock())
    stop_event = asyncio.Event()

    async def stop_sleep(_seconds):
        stop_event.set()

    class BrokenConnection:
        async def __aenter__(self):
            raise RuntimeError("offline")

        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr(
        "kis_agent.websocket.client.websockets.connect",
        lambda *_args, **_kwargs: BrokenConnection(),
    )
    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", stop_sleep)
    await ws.connect(stop_event=stop_event)
    assert stop_event.is_set()


@pytest.mark.asyncio
async def test_connect_reconnects_after_ping_error(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.url = "ws://example"
    ws.ping_interval = ws.ping_timeout = 1
    ws.max_ping_retries = 1
    ws.stock_codes = []
    ws.enable_index = ws.enable_ask_bid = ws.enable_program_trading = False
    ws.enable_expected_index = ws.enable_expected_stock = False
    for method in (
        "get_approval",
        "load_historical_data",
        "fetch_stock_names",
        "fetch_open_prices",
        "load_initial_balance",
        "display_balance_info",
    ):
        monkeypatch.setattr(ws, method, MagicMock())
    stop_event = asyncio.Event()

    class MarketDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 1, 6, 10, 0, tzinfo=tz)

    async def recv(_self):
        raise asyncio.TimeoutError

    async def ping(_self):
        raise RuntimeError("ping failed")

    socket = type("Socket", (), {"send": AsyncMock(), "recv": recv, "ping": ping})()

    class Connection:
        async def __aenter__(self):
            return socket

        async def __aexit__(self, *_args):
            return False

    async def stop_sleep(_seconds):
        stop_event.set()

    import datetime as datetime_module

    monkeypatch.setattr(datetime_module, "datetime", MarketDateTime)
    monkeypatch.setattr(
        "kis_agent.websocket.client.websockets.connect",
        lambda *_args, **_kwargs: Connection(),
    )
    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", stop_sleep)
    await ws.connect(stop_event=stop_event)
    assert stop_event.is_set()


@pytest.mark.asyncio
async def test_poll_final_price_unsubscribes_and_updates_close(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.stock_api = MagicMock()
    ws.stock_api.get_stock_price.return_value = {"stck_prpr": "71000"}
    ws.unsubscribe_all = MagicMock()

    class AfterCloseDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 1, 6, 15, 21, tzinfo=tz)

    async def cancel_after_update(_seconds):
        raise asyncio.CancelledError

    import datetime as datetime_module

    monkeypatch.setattr(datetime_module, "datetime", AfterCloseDateTime)
    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", cancel_after_update)
    with pytest.raises(asyncio.CancelledError):
        await ws.poll_final_price()

    ws.unsubscribe_all.assert_called_once()
    assert "71000.0" in ws.latest_trade["005930"]


def test_format_approval_history_and_indicators(tmp_path):
    ws = _ws(tmp_path)
    assert ws.format_price("12345") == "12,345"
    assert ws.format_price("1.5") == "1.5"
    assert ws.format_price("bad") == "bad"
    ws.client.get_ws_approval_key.return_value = "approved"
    assert ws.get_approval() == "approved"
    ws.client.get_ws_approval_key.return_value = None
    with pytest.raises(ValueError, match="approval_key"):
        ws.get_approval()

    start = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(minutes=30)
    for index in range(30):
        ws.update_trade_history("005930", start + timedelta(minutes=index), 100 + index, 90 + index)
    assert len(Path(ws.trade_log_file).read_text().splitlines()) == 30
    assert ws.compute_RSI("005930") == 100
    assert ws.compute_MACD("005930") is not None
    assert len(ws.compute_candles("005930", interval_minutes=5)) == 6
    assert ws.compute_RSI_candles("005930") == 100
    assert ws.compute_MACD_candles("005930") is not None
    assert ws.compute_MACD_oscillator_candles("005930", span_long=3, signal_span=2) is not None
    assert ws.compute_ATR("005930", period=2) >= 0
    assert ws.compute_trade_strength_candle("005930")
    assert ws.compute_RSI("missing") is None
    assert ws.compute_MACD("missing") is None
    assert ws.compute_ATR("missing") is None


def test_handle_all_realtime_and_json_message_types(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    monkeypatch.setattr(ws, "update_price_and_indicators", MagicMock())
    monkeypatch.setattr(ws, "display_ask_bid_info", MagicMock())
    monkeypatch.setattr(ws, "display_index_info", MagicMock())
    monkeypatch.setattr(ws, "display_program_trading_info", MagicMock())

    fields = ["005930", "093000", "70000"] + ["0"] * 15 + ["99"]
    ws.handle_message("0|H0STCNT0|001|" + "^".join(fields))
    assert ws.latest_trade["005930"] and ws.trade_history["005930"]
    ws.handle_message("0|H0STASP0|001|005930^" + "^".join(["1"] * 50))
    assert "005930" in ws.latest_ask_bid
    ws.handle_message("0|H0IF1000|001|0001^2500^1^0.1^0^0^0^0^0^0")
    assert "KOSPI" in ws.latest_index
    ws.handle_message("0|H0UPANC0|001|2001^x^x")
    ws.handle_message("0|H0GSCNT0|001|005930^" + "^".join(["1"] * 10))
    ws.handle_message("0|H0UNANC0|001|005930^x")
    assert ws.latest_index_expected and ws.latest_program_trading and ws.latest_expected_stock
    ws.handle_message("0|H0STCNI0|001|000660^x")
    assert "000660" in ws.stock_codes

    ws.handle_message(json.dumps({"header": {"tr_id": "PINGPONG", "tr_key": "x"}, "body": {}}))
    ws.handle_message(
        json.dumps(
            {
                "header": {"tr_id": "x", "tr_key": "x"},
                "body": {"msg1": "SUBSCRIBE SUCCESS"},
            }
        )
    )
    ws.handle_message(
        json.dumps(
            {
                "header": {"tr_id": "H0STCNI9", "tr_key": "x"},
                "body": {"output": {"key": "key", "iv": "iv"}},
            }
        )
    )
    assert (ws.aes_key, ws.aes_iv) == ("key", "iv")


@pytest.mark.asyncio
async def test_notice_subscription_and_malformed_trade_are_isolated(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.ws = type("Socket", (), {"send": AsyncMock()})()
    monkeypatch.setattr(ws, "update_price_and_indicators", MagicMock())
    ws.handle_message("0|H0STCNT0|001|005930^bad-time^not-price")
    ws.handle_message("0|H0STCNI0|001|000660^x")
    await asyncio.sleep(0)
    assert ws.ws.send.await_count == 1
    assert "000660" in ws.subscribed_stocks


def test_trade_format_and_summary(tmp_path):
    ws = _ws(tmp_path)
    ws.latest_trade["005930"] = "005930^093000^71000^x^100^0.2^x^x^x^x^x^x^100^x^100000000^x^x^x^99"
    ws.purchase_prices["005930"] = (70000, 2)
    ws.open_prices["005930"] = 70000
    ws.compute_RSI_candles = MagicMock(return_value=50.0)
    ws.compute_MACD_candles = MagicMock(return_value=10.0)
    ws.compute_ATR = MagicMock(return_value=3.0)
    ws.compute_candles = MagicMock(return_value=[(datetime.now(), 1, 1, 1, 71000)] * 20)
    assert "체결가" in ws.format_trade_string(ws.latest_trade["005930"])
    assert ws.trade_summary()["005930"][7] == 142000.0


def test_trade_summary_handles_empty_invalid_and_long_candle_history(tmp_path):
    ws = _ws(tmp_path)
    ws.stock_codes = ["005930", "000660"]
    ws.latest_trade["005930"] = "005930^093000^not-a-price"
    ws.latest_trade["000660"] = None
    ws.purchase_prices["005930"] = (100, 1)
    ws.compute_RSI_candles = MagicMock(return_value=None)
    ws.compute_MACD_candles = MagicMock(return_value=None)
    ws.compute_ATR = MagicMock(return_value=None)
    candles = [(datetime.now(), 1, 1, 1, price) for price in range(120)]
    ws.compute_candles = MagicMock(return_value=candles)

    summary = ws.trade_summary()

    assert summary["005930"][2] is None
    assert summary["005930"][13] is not None and summary["005930"][14] is not None
    assert summary["000660"][2] is None


def test_should_exit_on_all_profit_taking_signals(tmp_path):
    ws = _ws(tmp_path)
    ws.latest_trade["005930"] = "005930^093000^110^x"
    ws.purchase_prices["005930"] = (100, 1)
    ws.prev_indicators["005930"] = (70.0, None)
    ws.compute_RSI_candles = MagicMock(return_value=60.0)
    ws.compute_trade_strength_candle = MagicMock(return_value=[(None, 100), (None, 90), (None, 80)])
    ws.compute_ATR = MagicMock(return_value=0.5)

    assert ws.should_exit("005930") is True


def test_should_exit_false_for_missing_trade_low_profit_and_missing_purchase(tmp_path):
    ws = _ws(tmp_path)
    assert ws.should_exit("005930") is False
    ws.latest_trade["005930"] = "005930^093000^101^x"
    ws.purchase_prices["005930"] = (100, 1)
    assert ws.should_exit("005930") is False
    ws.purchase_prices.clear()
    assert ws.should_exit("005930") is False


@pytest.mark.asyncio
async def test_historical_names_open_prices_and_unsubscribe(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.stock_api = MagicMock()
    ws.stock_api.inquire_daily_price.return_value = pd.DataFrame(
        {
            "stck_bsop_date": ["20250101", "bad"],
            "stck_cntg_hour": ["090000", "090000"],
            "stck_clpr": ["100", "200"],
        }
    )
    ws.load_historical_data()
    assert len(ws.trade_history["005930"]) == 1
    ws.stock_api.get_stock_info.return_value = pd.DataFrame({"prdt_name": ["삼성전자"]})
    ws.fetch_stock_names()
    assert ws.stock_names["005930"] == "삼성전자"
    ws.stock_api.get_stock_price.return_value = {"output": {"stck_oprc": "70000"}}
    ws.fetch_open_prices()
    assert ws.open_prices["005930"] == 70000.0
    ws.ws = MagicMock(send=AsyncMock())
    ws.unsubscribe_all()
    await asyncio.sleep(0)
    assert ws.ws.send.called
    ws.ws = None
    ws.unsubscribe_all()


@pytest.mark.asyncio
async def test_update_holdings_loop_reconciles_subscriptions_once(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.auth = MagicMock()
    ws.stock_codes = ["005930"]
    ws.purchase_prices = {"005930": (70000.0, 1)}
    ws.ws = type("Socket", (), {"send": AsyncMock()})()
    ws.load_historical_data_for_stock = MagicMock()
    ws.fetch_stock_names = MagicMock()

    class AccountAPI:
        def __init__(self, **_kwargs):
            pass

        def get_account_balance(self):
            return {"output1": [{"pdno": "000660", "pchs_avg_pric": "100", "hldg_qty": "2"}]}

    monkeypatch.setattr("kis_agent.account.api.AccountAPI", AccountAPI)

    async def stop_after_iteration(_seconds):
        raise asyncio.CancelledError

    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", stop_after_iteration)
    with pytest.raises(asyncio.CancelledError):
        await ws.update_holdings_loop()

    assert ws.stock_codes == ["000660"]
    assert ws.purchase_prices == {"000660": (100.0, 2)}
    sent_ids = [json.loads(call.args[0])["body"]["input"]["tr_id"] for call in ws.ws.send.await_args_list]
    assert sent_ids == ["H0STCNT0", "H0STCNT0_UNSUB"]


def test_update_price_and_balance_display_paths(tmp_path, monkeypatch, capsys):
    ws = _ws(tmp_path)
    ws.account_info = {"account": "123"}
    ws.balance_info = pd.DataFrame(
        [
            {
                "pdno": "005930",
                "prdt_name": "삼성",
                "hldg_qty": "1",
                "pchs_avg_pric": "70000",
                "prpr": "71000",
                "evlu_amt": "71000",
                "evlu_pfls_amt": "1000",
                "evlu_pfls_rt": "1.4",
            },
            {
                "pdno": "000660",
                "prdt_name": "SK",
                "hldg_qty": "0",
                "pchs_avg_pric": "1",
                "prpr": "1",
                "evlu_amt": "0",
                "evlu_pfls_amt": "0",
                "evlu_pfls_rt": "0",
            },
        ]
    )
    ws.initial_cash_balance = 500
    ws.last_balance_check = datetime.now()
    ws.compute_RSI_candles = MagicMock(return_value=None)
    ws.compute_MACD_candles = MagicMock(return_value=None)
    monkeypatch.setattr("kis_agent.websocket.client.os.system", lambda *_args: 0)
    ws.update_price_and_indicators()
    assert "총 자산" in capsys.readouterr().out

    ws.balance_info = None
    ws.load_initial_balance = MagicMock(return_value=False)
    ws.display_balance_info()
    ws.load_initial_balance.assert_called_once()


@pytest.mark.asyncio
async def test_exit_and_monitor_loops_have_controlled_exit_paths(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.execute_exit_orders = MagicMock()

    async def cancel_sleep(_seconds):
        raise asyncio.CancelledError

    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", cancel_sleep)
    with pytest.raises(asyncio.CancelledError):
        await ws.exit_watch_loop()
    ws.execute_exit_orders.assert_called_once()

    ws.ws = type("Socket", (), {"close": AsyncMock()})()
    monkeypatch.setitem(sys.modules, "msvcrt", None)
    monkeypatch.setattr("kis_agent.websocket.client.select.select", lambda *_args: ([sys.stdin], [], []))
    monkeypatch.setattr(sys.stdin, "read", lambda _size: "")
    with pytest.raises(SystemExit):
        await ws.monitor_exit()
    ws.ws.close.assert_awaited_once()

    monkeypatch.setitem(sys.modules, "msvcrt", None)
    await ws.monitor_esc()

    windows_ws = _ws(tmp_path)
    windows_ws.ws = type("Socket", (), {"close": AsyncMock()})()
    fake_msvcrt = type(
        "Msvcrt",
        (),
        {"kbhit": staticmethod(lambda: True), "getch": staticmethod(lambda: b"\x1b")},
    )()
    monkeypatch.setitem(sys.modules, "msvcrt", fake_msvcrt)
    with pytest.raises(SystemExit):
        await windows_ws.monitor_esc()
    windows_ws.ws.close.assert_awaited_once()


def test_balance_loader_and_active_check(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.account_info = {"account": "123"}

    class AccountAPI:
        def __init__(self, **_kwargs):
            pass

        def get_account_balance(self):
            return {
                "output1": [{"pdno": "005930"}],
                "output2": [{"dnca_tot_amt": "1234"}],
            }

    monkeypatch.setattr("kis_agent.account.api.AccountAPI", AccountAPI)
    assert ws.load_initial_balance()
    assert ws.initial_cash_balance == 1234
    ws.last_ws_recv_time = datetime.now()
    assert ws.is_ws_active()
    ws.last_ws_recv_time = datetime.now() - timedelta(seconds=61)
    assert not ws.is_ws_active()


def test_single_stock_history_and_open_price_error_paths(tmp_path):
    ws = _ws(tmp_path)
    ws.stock_api = MagicMock()
    ws.stock_api.inquire_daily_price.return_value = pd.DataFrame(
        {
            "stck_bsop_date": ["20250101"],
            "stck_cntg_hour": ["090000"],
            "stck_clpr": ["100"],
        }
    )
    ws.load_historical_data_for_stock("005930")
    assert ws.trade_history["005930"][0][1] == 100.0
    ws.stock_api.get_stock_price.side_effect = RuntimeError("offline")
    ws.fetch_open_prices()


def test_websocket_display_helpers_and_trade_log_failure(tmp_path, monkeypatch, capsys):
    ws = _ws(tmp_path)
    assert ws.get_index_name("0001") == "KOSPI"
    assert ws.get_index_name("unknown") == "INDEX_unknown"
    ws.print_program_trade_summary(1, "^".join(["1"] * 11))
    ws.print_domestic_hoga("005930^" + "^".join(["1"] * 55))
    assert "프로그램매매" in capsys.readouterr().out
    ws.trade_log_file = str(tmp_path)
    ws.update_trade_history("005930", datetime.now(), 1)


def test_realtime_display_helpers(tmp_path, capsys):
    ws = _ws(tmp_path)
    ws.display_ask_bid_info("005930", "^".join(["1"] * 50))
    ws.display_index_info("KOSPI", ["0001", "2500", "1", "0.1"] + ["0"] * 6)
    ws.display_program_trading_info("005930", "^".join(["1"] * 11))
    output = capsys.readouterr().out
    assert "호가" in output and "KOSPI" in output and "프로그램매매" in output


def test_indicator_edge_cases_and_trade_summary_display(tmp_path, capsys):
    ws = _ws(tmp_path)
    start = datetime.now().replace(second=0, microsecond=0) - timedelta(minutes=30)
    for index in range(30):
        ws.trade_history["005930"].append((start + timedelta(minutes=index), 130 - index, None))

    assert ws.compute_RSI("005930") == 0
    assert ws.compute_MACD_candles("005930", span_long=40) is None
    assert ws.compute_MACD_oscillator_candles("005930", span_long=26, signal_span=9) is None
    assert ws.compute_trade_strength_candle("005930") == []


def test_indicator_loss_intervals_and_display_error_paths(tmp_path):
    ws = _ws(tmp_path)
    start = datetime.now().replace(second=0, microsecond=0) - timedelta(minutes=30)
    ws.trade_history["005930"] = [(start + timedelta(minutes=index), 130 - index, 100 - index) for index in range(30)]
    assert ws.compute_RSI_candles("005930") == 0
    assert ws.compute_trade_strength_candle("005930", interval_minutes=5)

    with pytest.raises(AttributeError):
        ws.display_ask_bid_info("005930", None)
    with pytest.raises(TypeError):
        ws.display_index_info("KOSPI", None)
    ws.display_program_trading_info("005930", None)


def test_notice_crypto_wrapper_delegates_to_decryptor(tmp_path, capsys):
    ws = _ws(tmp_path)
    ws.aes_cbc_base64_dec = MagicMock(return_value="decoded")
    assert ws.stocksigningnotice("cipher", "key", "iv") is None
    ws.aes_cbc_base64_dec.assert_called_once_with("key", "iv", "cipher")

    ws.latest_trade["005930"] = "005930^093000^not-a-number"
    assert "파싱 실패" in ws.format_trade_string(ws.latest_trade["005930"])
    ws.compute_RSI_candles = MagicMock(return_value=None)
    ws.compute_MACD_candles = MagicMock(return_value=None)
    ws.compute_ATR = MagicMock(return_value=None)
    ws.display_trade_summary()
    assert "N/A" in capsys.readouterr().out


def test_history_name_and_open_price_error_branches(tmp_path):
    ws = _ws(tmp_path)
    ws.stock_api = MagicMock()
    ws.stock_api.inquire_daily_price.side_effect = RuntimeError("offline")
    ws.load_historical_data()
    ws.load_historical_data_for_stock("005930")
    ws.stock_names.clear()
    ws.stock_api.get_stock_info.side_effect = RuntimeError("offline")
    ws.fetch_stock_names()
    assert ws.stock_names == {}


def test_balance_display_uses_websocket_and_fallback_prices(tmp_path, monkeypatch, capsys):
    ws = _ws(tmp_path)
    ws.balance_info = pd.DataFrame(
        [
            {
                "pdno": "005930",
                "prdt_name": "삼성전자",
                "hldg_qty": "2",
                "pchs_avg_pric": "70000",
                "prpr": "71000",
                "evlu_amt": "142000",
                "evlu_pfls_amt": "2000",
                "evlu_pfls_rt": "1.43",
            },
            {
                "pdno": "000660",
                "prdt_name": "SK하이닉스",
                "hldg_qty": "1",
                "pchs_avg_pric": "100000",
                "prpr": "101000",
                "evlu_amt": "101000",
                "evlu_pfls_amt": "1000",
                "evlu_pfls_rt": "1.0",
            },
            {
                "pdno": "000000",
                "prdt_name": "제외",
                "hldg_qty": "0",
                "pchs_avg_pric": "1",
                "prpr": "1",
                "evlu_amt": "0",
                "evlu_pfls_amt": "0",
                "evlu_pfls_rt": "0",
            },
        ]
    )
    ws.last_balance_check = datetime.now()
    ws.initial_cash_balance = 50_000
    ws.latest_trade["005930"] = "005930^093000^72000"
    ws.compute_RSI_candles = MagicMock(return_value=55.0)
    ws.compute_MACD_candles = MagicMock(return_value=None)
    monkeypatch.setattr("kis_agent.websocket.client.os.system", lambda *_: 0)

    ws.update_price_and_indicators()

    output = capsys.readouterr().out
    assert "삼성전자" in output and "SK하이닉스" in output
    assert "총 자산: 295,000원" in output


def test_execute_exit_orders_submits_market_order_and_skips_zero_quantity(tmp_path):
    ws = _ws(tmp_path)
    ws.account_info = {"account": "123"}
    ws.purchase_prices = {"005930": (70000, 2)}
    ws.should_exit = MagicMock(return_value=True)
    with patch("kis_agent.account.api.AccountAPI") as account_api:
        account_api.return_value.order_stock_cash.return_value = {"msg1": "ok"}
        ws.execute_exit_orders()

    account_api.return_value.order_stock_cash.assert_called_once_with(ticker="005930", price="0", quantity="2", order_type="01")
    ws.purchase_prices["005930"] = (70000, 0)
    with patch("kis_agent.account.api.AccountAPI") as account_api:
        ws.execute_exit_orders()
    account_api.return_value.order_stock_cash.assert_not_called()


def test_remaining_small_state_and_indicator_paths(tmp_path, monkeypatch, capsys):
    ws = _ws(tmp_path)
    with patch("kis_agent.websocket.client.os.system") as system:
        ws.clear_console()
    system.assert_called_once()

    class BadPrice:
        def replace(self, *_args):
            raise ValueError("bad")

    assert ws.format_price(BadPrice()) is not None
    for index in range(1002):
        ws.update_trade_history("000660", datetime.now(), index)
    assert len(ws.trade_history["000660"]) == 1000
    assert ws.compute_MACD_oscillator_candles("missing") is None
    assert ws.compute_trade_strength_candle("missing") == []

    ws.display_live_trade("005930", "formatted")
    assert "formatted" in capsys.readouterr().out
    ws.balance_info = pd.DataFrame()
    ws.update_price_and_indicators = MagicMock()
    ws.display_balance_info()
    ws.update_price_and_indicators.assert_called_once()


def test_trade_summary_bad_purchase_and_should_exit_tail_paths(tmp_path):
    ws = _ws(tmp_path)
    ws.latest_trade["005930"] = "005930^093000^110"
    ws.purchase_prices["005930"] = (100,)
    ws.compute_RSI_candles = MagicMock(return_value=None)
    ws.compute_MACD_candles = MagicMock(return_value=None)
    ws.compute_ATR = MagicMock(return_value=None)
    ws.compute_candles = MagicMock(return_value=[])
    assert ws.trade_summary()["005930"][5] is None

    ws.purchase_prices["005930"] = (100, 1)
    ws.prev_indicators["005930"] = (50, None)
    ws.compute_RSI_candles.return_value = 60
    ws.compute_trade_strength_candle = MagicMock(return_value=[])
    assert not ws.should_exit("005930")
    assert ws.prev_indicators["005930"] == (60, None)
    ws.purchase_prices["005930"] = (0, 1)
    assert not ws.should_exit("005930")


def test_malformed_trade_name_fallback_and_null_history_row(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.update_price_and_indicators = MagicMock()
    fields = ["005930", "bad-time", "not-price"] + ["0"] * 16
    ws.handle_message("0|H0STCNT0|001|" + "^".join(fields))
    ws.stock_names.clear()
    ws.stock_api = MagicMock()
    ws.stock_api.get_stock_info.return_value = pd.DataFrame({"prdt_name": ["삼성전자"]})
    ws.fetch_stock_names()
    assert ws.stock_names["005930"] == "삼성전자"

    ws.stock_api.inquire_daily_price.return_value = pd.DataFrame(
        {
            "stck_bsop_date": ["bad"],
            "stck_cntg_hour": ["bad"],
            "stck_clpr": ["100"],
        }
    )
    ws.load_historical_data_for_stock("005930")


def test_aes_decrypt_exit_order_exception_and_empty_balance(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    cipher = MagicMock()
    cipher.decrypt.return_value = b"padded"
    with patch("Crypto.Cipher.AES.new", return_value=cipher), patch(
        "kis_agent.websocket.client.b64decode", return_value=b"cipher"
    ), patch("Crypto.Util.Padding.unpad", return_value=b"plain"):
        assert ws.aes_cbc_base64_dec("key", "iv", "cipher") == "plain"

    ws.account_info = {}
    ws.should_exit = MagicMock(return_value=True)
    ws.purchase_prices["005930"] = (100, 1)
    with patch("kis_agent.account.api.AccountAPI") as account_api:
        account_api.return_value.order_stock_cash.side_effect = RuntimeError("offline")
        ws.execute_exit_orders()

    class AccountAPI:
        def __init__(self, **_kwargs):
            pass

        def get_account_balance(self):
            return {"output1": []}

    monkeypatch.setattr("kis_agent.account.api.AccountAPI", AccountAPI)
    assert not ws.load_initial_balance()
    ws.balance_info = None
    ws.update_price_and_indicators()


@pytest.mark.asyncio
async def test_holding_poll_and_final_price_error_paths(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.account_info = {}
    ws.auth = MagicMock()

    class BrokenAccountAPI:
        def __init__(self, **_kwargs):
            pass

        def get_account_balance(self):
            raise RuntimeError("offline")

    monkeypatch.setattr("kis_agent.account.api.AccountAPI", BrokenAccountAPI)

    async def cancel_sleep(_seconds):
        raise asyncio.CancelledError

    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", cancel_sleep)
    with pytest.raises(asyncio.CancelledError):
        await ws.update_holdings_loop()

    ws.stock_api = MagicMock()
    ws.stock_api.get_stock_price.side_effect = RuntimeError("offline")

    class AfterCloseDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 1, 6, 15, 21, tzinfo=tz)

    import datetime as datetime_module

    monkeypatch.setattr(datetime_module, "datetime", AfterCloseDateTime)
    with pytest.raises(asyncio.CancelledError):
        await ws.poll_final_price()


@pytest.mark.asyncio
async def test_poll_final_price_market_session_and_monitor_sleep_paths(tmp_path, monkeypatch):
    ws = _ws(tmp_path)

    class MarketDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 1, 6, 10, 0, tzinfo=tz)

    import datetime as datetime_module

    monkeypatch.setattr(datetime_module, "datetime", MarketDateTime)

    async def cancel_sleep(_seconds):
        raise asyncio.CancelledError

    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", cancel_sleep)
    with pytest.raises(asyncio.CancelledError):
        await ws.poll_final_price()

    fake_msvcrt = type(
        "Msvcrt",
        (),
        {"kbhit": staticmethod(lambda: False), "getch": staticmethod(lambda: b"")},
    )()
    monkeypatch.setitem(sys.modules, "msvcrt", fake_msvcrt)
    with pytest.raises(asyncio.CancelledError):
        await ws.monitor_esc()

    monkeypatch.setitem(sys.modules, "msvcrt", None)
    monkeypatch.setattr("kis_agent.websocket.client.select.select", lambda *_args: ([], [], []))
    with pytest.raises(asyncio.CancelledError):
        await ws.monitor_exit()


@pytest.mark.asyncio
async def test_monitor_exit_windows_escape(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.ws = type("Socket", (), {"close": AsyncMock()})()
    fake_msvcrt = type(
        "Msvcrt",
        (),
        {
            "kbhit": staticmethod(lambda: True),
            "getch": staticmethod(lambda: b"\x1b"),
        },
    )()
    monkeypatch.setitem(sys.modules, "msvcrt", fake_msvcrt)
    with pytest.raises(SystemExit):
        await ws.monitor_exit()
    ws.ws.close.assert_awaited_once()

    waiting_msvcrt = type(
        "Msvcrt",
        (),
        {
            "kbhit": staticmethod(lambda: False),
            "getch": staticmethod(lambda: b""),
        },
    )()
    monkeypatch.setitem(sys.modules, "msvcrt", waiting_msvcrt)

    async def cancel_sleep(_seconds):
        raise asyncio.CancelledError

    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", cancel_sleep)
    with pytest.raises(asyncio.CancelledError):
        await ws.monitor_exit()


@pytest.mark.asyncio
async def test_exit_watch_loop_isolates_execution_error(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.execute_exit_orders = MagicMock(side_effect=RuntimeError("offline"))

    async def cancel_sleep(_seconds):
        raise asyncio.CancelledError

    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", cancel_sleep)
    with pytest.raises(asyncio.CancelledError):
        await ws.exit_watch_loop()


def test_balance_refresh_updates_holdings_cash_and_timestamp(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    ws.account_info = {}
    empty_holding = {
        "pdno": "005930",
        "prdt_name": "삼성전자",
        "hldg_qty": "0",
        "pchs_avg_pric": "0",
        "prpr": "0",
        "evlu_amt": "0",
        "evlu_pfls_amt": "0",
        "evlu_pfls_rt": "0",
    }
    ws.balance_info = pd.DataFrame([empty_holding])
    ws.last_balance_check = datetime.now() - timedelta(minutes=2)
    ws.initial_cash_balance = None

    class AccountAPI:
        def __init__(self, **_kwargs):
            pass

        def get_account_balance(self):
            return {
                "output1": [empty_holding],
                "output2": [{"dnca_tot_amt": "1234"}],
            }

    monkeypatch.setattr("kis_agent.account.api.AccountAPI", AccountAPI)
    monkeypatch.setattr("kis_agent.websocket.client.os.system", lambda *_args: 0)
    ws.compute_RSI_candles = MagicMock(return_value=None)
    ws.compute_MACD_candles = MagicMock(return_value=None)
    ws.update_price_and_indicators()
    assert ws.initial_cash_balance == 1234


def _prepare_connect_ws(ws, monkeypatch):
    ws.url = "ws://example"
    ws.ping_interval = ws.ping_timeout = 0.001
    ws.max_ping_retries = 2
    ws.stock_codes = []
    ws.enable_index = ws.enable_ask_bid = ws.enable_program_trading = False
    ws.enable_expected_index = ws.enable_expected_stock = False
    for method in (
        "get_approval",
        "load_historical_data",
        "fetch_stock_names",
        "fetch_open_prices",
        "load_initial_balance",
        "display_balance_info",
    ):
        monkeypatch.setattr(ws, method, MagicMock())


@pytest.mark.asyncio
async def test_connect_ignores_pingpong_and_subscription_success(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    _prepare_connect_ws(ws, monkeypatch)
    stop_event = asyncio.Event()
    messages = iter(["PINGPONG", "SUBSCRIBE SUCCESS"])

    class MarketDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 1, 6, 10, 0, tzinfo=tz)

    async def recv(_self):
        message = next(messages)
        if message == "SUBSCRIBE SUCCESS":
            stop_event.set()
        return message

    socket = type("Socket", (), {"send": AsyncMock(), "recv": recv})()

    class Connection:
        async def __aenter__(self):
            return socket

        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr(
        "kis_agent.websocket.client.websockets.connect",
        lambda *_args, **_kwargs: Connection(),
    )
    import datetime as datetime_module

    monkeypatch.setattr(datetime_module, "datetime", MarketDateTime)
    await ws.connect(stop_event=stop_event)
    assert stop_event.is_set()


@pytest.mark.asyncio
async def test_connect_waits_after_market_close_until_morning(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    _prepare_connect_ws(ws, monkeypatch)
    stop_event = asyncio.Event()

    class SessionDateTime(datetime):
        calls = 0

        @classmethod
        def now(cls, tz=None):
            cls.calls += 1
            hour = 16 if cls.calls == 1 else 8
            return cls(2025, 1, 6, hour, 0, tzinfo=tz)

    async def recv(_self):
        stop_event.set()
        return "PINGPONG"

    socket = type("Socket", (), {"send": AsyncMock(), "recv": recv})()

    class Connection:
        async def __aenter__(self):
            return socket

        async def __aexit__(self, *_args):
            return False

    import datetime as datetime_module

    monkeypatch.setattr(datetime_module, "datetime", SessionDateTime)
    monkeypatch.setattr(
        "kis_agent.websocket.client.websockets.connect",
        lambda *_args, **_kwargs: Connection(),
    )
    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", AsyncMock())
    await ws.connect(stop_event=stop_event)
    assert SessionDateTime.calls >= 2


@pytest.mark.asyncio
@pytest.mark.parametrize("ping_error", [asyncio.TimeoutError(), RuntimeError("ping")])
async def test_connect_retries_ping_failure_below_limit(tmp_path, monkeypatch, ping_error):
    ws = _ws(tmp_path)
    _prepare_connect_ws(ws, monkeypatch)
    stop_event = asyncio.Event()

    class MarketDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 1, 6, 10, 0, tzinfo=tz)

    async def recv(_self):
        raise asyncio.TimeoutError

    async def ping(_self):
        raise ping_error

    socket = type("Socket", (), {"send": AsyncMock(), "recv": recv, "ping": ping})()

    class Connection:
        async def __aenter__(self):
            return socket

        async def __aexit__(self, *_args):
            return False

    async def stop_on_retry(seconds):
        if seconds == 1:
            stop_event.set()

    import datetime as datetime_module

    monkeypatch.setattr(datetime_module, "datetime", MarketDateTime)
    monkeypatch.setattr(
        "kis_agent.websocket.client.websockets.connect",
        lambda *_args, **_kwargs: Connection(),
    )
    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", stop_on_retry)
    await ws.connect(stop_event=stop_event)
    assert stop_event.is_set()


@pytest.mark.asyncio
async def test_connect_reconnects_after_ping_timeout_limit(tmp_path, monkeypatch):
    ws = _ws(tmp_path)
    _prepare_connect_ws(ws, monkeypatch)
    ws.max_ping_retries = 1
    stop_event = asyncio.Event()

    class MarketDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2025, 1, 6, 10, 0, tzinfo=tz)

    async def recv(_self):
        raise asyncio.TimeoutError

    async def ping(_self):
        return asyncio.get_running_loop().create_future()

    socket = type("Socket", (), {"send": AsyncMock(), "recv": recv, "ping": ping})()

    class Connection:
        async def __aenter__(self):
            return socket

        async def __aexit__(self, *_args):
            return False

    async def stop_reconnect(seconds):
        if seconds == 5:
            stop_event.set()

    import datetime as datetime_module

    monkeypatch.setattr(datetime_module, "datetime", MarketDateTime)
    monkeypatch.setattr(
        "kis_agent.websocket.client.websockets.connect",
        lambda *_args, **_kwargs: Connection(),
    )
    monkeypatch.setattr("kis_agent.websocket.client.asyncio.sleep", stop_reconnect)
    await ws.connect(stop_event=stop_event)
    assert stop_event.is_set()
