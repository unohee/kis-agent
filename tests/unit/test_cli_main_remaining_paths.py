"""CLI의 실패 응답, 확인 취소, 예외 경로 회귀 테스트."""

import runpy
import sys
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import kis_agent
import kis_agent.cli.main as cli


def _args(**values):
    values.setdefault("pretty", False)
    return SimpleNamespace(**values)


def _agent():
    agent = MagicMock()
    agent.stock_api.search_stock_info.return_value = {"output": {"prdt_abrv_name": "삼성"}}
    return agent


def test_create_agent_loads_local_env_and_checks_market(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("KIS_APP_KEY=file\n", encoding="utf-8")
    monkeypatch.setenv("KIS_APP_KEY", "app")
    monkeypatch.setenv("KIS_APP_SECRET", "secret")
    monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_ACCOUNT_CODE", "01")
    agent = _agent()
    check = MagicMock()

    with patch("dotenv.load_dotenv") as load, patch.object(
        kis_agent, "Agent", return_value=agent
    ) as constructor, patch.object(cli, "_check_market_status", check):
        assert cli._create_agent() is agent

    load.assert_called_once_with(".env", override=False)
    constructor.assert_called_once_with(
        app_key="app",
        app_secret="secret",
        account_no="12345678",
        account_code="01",
    )
    check.assert_called_once_with(agent)


def test_market_status_cached_holiday_success_and_after_close(monkeypatch):
    agent = _agent()
    cli._market_status.update(checked=True, is_holiday=False, last_business_day=None, notice=None)
    cli._check_market_status(agent)
    agent.stock_api.is_holiday.assert_not_called()

    class Monday(datetime):
        @classmethod
        def now(cls):
            return cls(2025, 1, 6, 12, 0)

    monkeypatch.setattr(cli, "datetime", Monday)
    cli._market_status.update(checked=False, is_holiday=None, last_business_day=None, notice=None)
    agent.stock_api.is_holiday.side_effect = [True, False]
    cli._check_market_status(agent)
    assert "휴장일" in cli._market_status["notice"]

    class Evening(datetime):
        @classmethod
        def now(cls):
            return cls(2025, 1, 6, 17, 0)

    monkeypatch.setattr(cli, "datetime", Evening)
    cli._market_status.update(checked=False, is_holiday=None, last_business_day=None, notice=None)
    agent.stock_api.is_holiday.side_effect = None
    agent.stock_api.is_holiday.return_value = False
    cli._check_market_status(agent)
    assert "장 마감 후" in cli._market_status["notice"]

    cli._market_status.update(checked=False, is_holiday=None, last_business_day=None, notice=None)
    agent.stock_api.is_holiday.side_effect = RuntimeError("offline")
    cli._check_market_status(agent)
    assert cli._market_status["is_holiday"] is False


def test_read_command_error_paths_and_date_passthrough(monkeypatch):
    agent, output = _agent(), []
    monkeypatch.setattr(cli, "_create_agent", lambda: agent)
    monkeypatch.setattr(cli, "_out", lambda value, pretty=False: output.append(value))

    agent.account_api.get_account_balance.return_value = None
    cli.cmd_balance(_args(holdings=False))
    assert output.pop()["error"] == "Failed to fetch balance"

    agent.overseas_futures_api.get_price.return_value = {"rt_cd": "1", "msg1": "bad"}
    cli.cmd_futures(
        _args(code="ES", night=False, overseas=True, option=False, orderbook=False)
    )
    assert output.pop()["data"]["overseasFutures"]["error"] == "bad"
    assert cli._parse_date("2y").isdigit()
    assert cli._parse_date("day") == "day"


def _trade_args(**changes):
    values = {
        "start": "20250101",
        "end": "20250131",
        "buy": False,
        "sell": False,
        "stock": "",
        "filled": False,
        "limit": 0,
        "profit": False,
        "daily_profit": False,
        "pretty": False,
    }
    values.update(changes)
    return _args(**values)


def test_trade_empty_and_failure_responses(monkeypatch):
    agent, output = _agent(), []
    monkeypatch.setattr(cli, "_create_agent", lambda: agent)
    monkeypatch.setattr(cli, "_out", lambda value, pretty=False: output.append(value))

    agent.account_api.inquire_daily_ccld.return_value = None
    cli.cmd_trades(_trade_args())
    assert "error" in output.pop()
    agent.account_api.inquire_daily_ccld.return_value = {"rt_cd": "0", "output1": []}
    cli.cmd_trades(_trade_args())
    assert output.pop()["data"]["trades"]["count"] == 0
    agent.account_api.inquire_daily_ccld.return_value = {
        "rt_cd": "0",
        "output1": [{"tot_ccld_qty": "0"}],
    }
    cli.cmd_trades(_trade_args(filled=True))
    assert output.pop()["data"]["trades"]["items"] == []

    agent.account_api.get_period_profit.return_value = None
    cli.cmd_trades(_trade_args(profit=True, daily_profit=True))
    assert "error" in output.pop()
    agent.account_api.get_period_trade_profit.return_value = {"rt_cd": "1", "msg1": "bad"}
    cli.cmd_trades(_trade_args(profit=True))
    assert output.pop()["detail"] == "bad"


def test_order_list_overseas_and_failure(monkeypatch):
    agent, output = _agent(), []
    monkeypatch.setattr(cli, "_create_agent", lambda: agent)
    monkeypatch.setattr(cli, "_out", lambda value, pretty=False: output.append(value))
    agent.overseas_api.get_nccs_orders.return_value = None
    cli._cmd_order_list(_args(overseas="nas"))
    assert "error" in output.pop()
    agent.overseas_api.get_nccs_orders.return_value = {"output": []}
    cli._cmd_order_list(_args(overseas="nas"))
    assert output.pop()["data"]["orders"]["count"] == 0


def _execute_args(**changes):
    values = {
        "action": "buy",
        "code": "005930",
        "overseas": "",
        "type": "limit",
        "qty": 1,
        "price": 1000,
        "exchange": "krx",
        "yes": True,
        "pretty": False,
    }
    values.update(changes)
    return _args(**values)


def test_domestic_order_cancel_failure_api_error_and_exception(monkeypatch):
    agent, output = _agent(), []
    monkeypatch.setattr(cli, "_create_agent", lambda: agent)
    monkeypatch.setattr(cli, "_out", lambda value, pretty=False: output.append(value))
    monkeypatch.setattr(cli, "_confirm_order", lambda *_: False)
    cli._cmd_order_execute(_execute_args(yes=False))
    assert output.pop()["cancelled"]

    agent.account_api.order_cash.return_value = None
    cli._cmd_order_execute(_execute_args())
    assert "응답 없음" in output.pop()["error"]
    agent.account_api.order_cash.return_value = {"rt_cd": "1", "msg1": "rejected"}
    cli._cmd_order_execute(_execute_args())
    assert output.pop()["error"] == "rejected"
    agent.account_api.order_cash.side_effect = RuntimeError("offline")
    with pytest.raises(SystemExit):
        cli._cmd_order_execute(_execute_args())
    assert output.pop()["code"] == "RuntimeError"


def test_overseas_order_guard_cancel_failures_and_sell(monkeypatch):
    agent, output = _agent(), []
    monkeypatch.setattr(cli, "_out", lambda value, pretty=False: output.append(value))
    cli._cmd_order_overseas(agent, _execute_args(overseas="nas", type="moo"), True)
    assert "매도만" in output.pop()["error"]

    monkeypatch.setattr(cli, "_confirm_order", lambda *_: False)
    cli._cmd_order_overseas(
        agent, _execute_args(overseas="nas", type="limit", yes=False), True
    )
    assert output.pop()["cancelled"]

    agent.overseas_api.sell_order.return_value = None
    cli._cmd_order_overseas(
        agent, _execute_args(action="sell", overseas="nas"), False
    )
    assert "응답 없음" in output.pop()["error"]
    agent.overseas_api.sell_order.return_value = {"rt_cd": "1", "msg1": "bad"}
    cli._cmd_order_overseas(
        agent, _execute_args(action="sell", overseas="nas"), False
    )
    assert output.pop()["error"] == "bad"
    agent.overseas_api.sell_order.side_effect = RuntimeError("offline")
    with pytest.raises(SystemExit):
        cli._cmd_order_overseas(
            agent, _execute_args(action="sell", overseas="nas"), False
        )
    assert output.pop()["code"] == "RuntimeError"


def _change_args(**changes):
    values = {
        "order_no": "old",
        "overseas": "",
        "code": "005930",
        "qty": 1,
        "price": 1000,
        "type": "limit",
        "yes": True,
        "pretty": False,
    }
    values.update(changes)
    return _args(**values)


def test_cancel_and_modify_confirmation_exception_and_api_error(monkeypatch):
    agent, output = _agent(), []
    monkeypatch.setattr(cli, "_create_agent", lambda: agent)
    monkeypatch.setattr(cli, "_out", lambda value, pretty=False: output.append(value))
    monkeypatch.setattr(cli, "_confirm_order", lambda *_: False)
    cli._cmd_order_cancel(_change_args(yes=False))
    assert output.pop()["cancelled"]
    cli._cmd_order_cancel(_change_args(overseas="nas", yes=False))
    assert output.pop()["cancelled"]
    cli._cmd_order_modify(_change_args(yes=False))
    assert output.pop()["cancelled"]
    cli._cmd_order_modify(_change_args(overseas="nas", yes=False))
    assert output.pop()["cancelled"]

    agent.account_api.order_rvsecncl.side_effect = RuntimeError("domestic")
    cli._cmd_order_cancel(_change_args())
    assert output.pop()["code"] == "RuntimeError"
    cli._cmd_order_modify(_change_args())
    assert output.pop()["code"] == "RuntimeError"
    agent.overseas_api.cancel_order.side_effect = RuntimeError("overseas")
    agent.overseas_api.modify_order.side_effect = RuntimeError("overseas")
    cli._cmd_order_cancel(_change_args(overseas="nas"))
    assert output.pop()["code"] == "RuntimeError"
    cli._cmd_order_modify(_change_args(overseas="nas"))
    assert output.pop()["code"] == "RuntimeError"

    agent.account_api.order_rvsecncl.side_effect = None
    agent.account_api.order_rvsecncl.return_value = {"rt_cd": "1", "msg1": "bad"}
    cli._cmd_order_cancel(_change_args())
    assert output.pop()["error"] == "bad"
    cli._cmd_order_modify(_change_args())
    assert output.pop()["error"] == "bad"
    agent.account_api.order_rvsecncl.return_value = None
    cli._cmd_order_modify(_change_args())
    assert "응답 없음" in output.pop()["error"]


def test_main_unknown_command_and_module_entrypoint(monkeypatch, capsys):
    parser = SimpleNamespace(
        parse_args=lambda: SimpleNamespace(command="unknown"),
        print_help=MagicMock(),
    )
    monkeypatch.setattr(cli, "build_parser", lambda: parser)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    parser.print_help.assert_called_once()

    monkeypatch.setattr(sys, "argv", ["kis", "schema"])
    with patch("kis_agent.cli.schema.get_schema", return_value="type Stock {}"):
        runpy.run_path(cli.__file__, run_name="__main__")
    assert "type Stock" in capsys.readouterr().out
