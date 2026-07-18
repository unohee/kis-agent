"""CLI 공개 조회 명령의 출력 형식과 분기 회귀 테스트."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import kis_agent.cli.main as cli


def _args(**values):
    values.setdefault("pretty", False)
    return SimpleNamespace(**values)


def _agent():
    agent = MagicMock()
    agent.stock_api.search_stock_info.return_value = {"output": {"prdt_abrv_name": "삼성"}}
    agent.stock_api.get_stock_price.return_value = {"output": {"stck_prpr": "70000"}}
    agent.stock_api.inquire_daily_price.return_value = {"output": [{"stck_clpr": "70000"}]}
    agent.stock_api.get_orderbook.return_value = {"output": {"askp1": "70100", "askp_rsqn1": "3", "bidp1": "70000", "bidp_rsqn1": "4"}}
    agent.account_api.get_account_balance.return_value = {"output1": [{"pdno": "005930"}], "output2": [{"dnca_tot_amt": "10"}]}
    agent.overseas_api.get_stock_info.return_value = {"output": {"prdt_name": "Apple"}}
    agent.overseas_api.get_price.return_value = {"output": {"last": "10"}}
    agent.overseas_api.get_price_detail.return_value = {"output": {"last": "10"}}
    agent.overseas_api.get_daily_price.return_value = {"output2": [{"clos": "10"}]}
    agent.futures_api.get_price.return_value = {"output": {"prdt_name": "선물", "futs_prpr": "1"}}
    agent.overseas_futures_api.get_price.return_value = {"output": {"last": "1"}}
    agent.overseas_futures_api.get_option_price.return_value = {"output": {"last": "1"}}
    agent.overseas_futures_api.get_futures_orderbook.return_value = {"output1": {"askp1": "2", "askp_rsqn1": "3"}, "output2": {"bidp1": "1", "bidp_rsqn1": "4"}}
    return agent


def test_format_resolution_and_market_status(monkeypatch, capsys):
    assert cli._fmt_date("20250102") == "2025-01-02"
    assert cli._fmt_time("093001") == "09:30:01"
    assert cli._fmt_number("1000") == "1,000"
    assert cli._fmt_number("1.5") == "1.50"
    assert cli._fmt_number("bad") == "bad"
    monkeypatch.setattr(cli, "resolve_code", lambda _: "005930")
    assert cli._resolve("삼성") == "005930"
    monkeypatch.setattr(cli, "resolve_code", lambda _: None)
    assert cli._resolve("unknown") == "unknown"
    cli._market_status["notice"] = "notice"
    cli._out({"data": {}}, False)
    assert "notice" in capsys.readouterr().out


def test_read_commands_emit_mapped_shapes(monkeypatch):
    agent, output = _agent(), []
    monkeypatch.setattr(cli, "_create_agent", lambda: agent)
    monkeypatch.setattr(cli, "_resolve", lambda code: code)
    monkeypatch.setattr(cli, "_out", lambda value, pretty=False: output.append(value))

    cli.cmd_price(_args(code="005930", daily=True, period="D", days=1))
    assert output.pop()["data"]["stock"]["code"] == "005930"
    cli.cmd_balance(_args(holdings=True))
    assert "balance" in output.pop()["data"]["account"]
    cli.cmd_orderbook(_args(code="005930"))
    assert output.pop()["data"]["stock"]["orderbook"]["asks"]
    cli.cmd_overseas(_args(excd="nas", symb="aapl", detail=False, daily=True, days=1))
    assert output.pop()["data"]["overseas"]["symbol"] == "AAPL"
    cli.cmd_overseas(_args(excd="nas", symb="aapl", detail=True, daily=False, days=None))
    assert "priceDetail" in output.pop()["data"]["overseas"]
    cli.cmd_futures(_args(code="101S03", night=False, overseas=False, option=False, orderbook=False))
    assert "futures" in output.pop()["data"]
    cli.cmd_futures(_args(code="ES", night=False, overseas=True, option=False, orderbook=True))
    assert output.pop()["data"]["overseasFutures"]["orderbook"]["bids"]
    cli.cmd_futures(_args(code="OPT", night=False, overseas=False, option=True, orderbook=False))
    assert "price" in output.pop()["data"]["overseasFutures"]


def test_night_futures_and_name_error_paths(monkeypatch):
    agent, output = _agent(), []
    monkeypatch.setattr(cli, "_out", lambda value, pretty=False: output.append(value))
    agent.futures_api.inquire_ngt_balance.return_value = None
    agent.futures_api.inquire_ngt_ccnl.return_value = None
    cli._cmd_futures_night(agent, _args(balance=True, ccnl=False), "101S03")
    assert output.pop()["data"]["nightFutures"]["balance"] == []
    cli._cmd_futures_night(agent, _args(balance=False, ccnl=True), "101S03")
    assert output.pop()["data"]["nightFutures"]["executions"] == []
    cli._cmd_futures_night(agent, _args(balance=False, ccnl=False), "101S03")
    assert "price" in output.pop()["data"]["nightFutures"]
    agent.stock_api.search_stock_info.side_effect = RuntimeError("offline")
    agent.overseas_api.get_stock_info.side_effect = RuntimeError("offline")
    assert cli._get_name(agent, "005930") is None
    assert cli._get_overseas_name(agent, "NAS", "AAPL") is None


def test_parser_query_search_schema_and_main_dispatch(monkeypatch, capsys):
    parser = cli.build_parser()
    assert parser.parse_args(["price", "005930"]).command == "price"
    assert parser.parse_args(["order", "buy", "005930", "--qty", "1"]).action == "buy"

    agent, output = _agent(), []
    monkeypatch.setattr(cli, "_create_agent", lambda: agent)
    monkeypatch.setattr(cli, "_out", lambda value, pretty=False: output.append(value))
    cli.cmd_query(_args(domain="stock", method="get_stock_price", args=["code=005930"], pretty=False))
    assert output.pop()["data"] == agent.stock_api.get_stock_price.return_value
    monkeypatch.setattr(cli, "search_stocks", lambda query, limit: [{"code": query}])
    cli.cmd_search(_args(query="삼성", limit=1, pretty=False))
    assert output.pop()["data"]["search"]["count"] == 1
    monkeypatch.setattr(cli, "get_schema", lambda type_name=None: "type Stock { code: String }")
    cli.cmd_schema(_args(type=None, json=True))
    assert output.pop()["types"][0]["name"] == "Stock"
    cli.cmd_schema(_args(type="Stock", json=False))
    assert "type Stock" in capsys.readouterr().out

    called = []
    monkeypatch.setattr(cli, "build_parser", lambda: SimpleNamespace(parse_args=lambda: SimpleNamespace(command="search")))
    monkeypatch.setattr(cli, "cmd_search", lambda args: called.append(args.command))
    cli.main()
    assert called == ["search"]

    monkeypatch.setattr(cli, "build_parser", lambda: SimpleNamespace(parse_args=lambda: SimpleNamespace(command=None), print_help=lambda: called.append("help")))
    with pytest.raises(SystemExit):
        cli.main()
    assert "help" in called


def test_cli_guard_and_error_paths(monkeypatch):
    output = []
    monkeypatch.setattr(cli, "_out", lambda value, pretty=False: output.append(value))
    monkeypatch.setattr("builtins.input", lambda: (_ for _ in ()).throw(EOFError))
    assert not cli._confirm_order("매수", {"종목": "005930"})

    with pytest.raises(SystemExit):
        cli.cmd_order(_args(action="unexpected"))
    assert "Unknown action" in output.pop()["error"]

    agent = _agent()
    monkeypatch.setattr(cli, "_create_agent", lambda: agent)
    with pytest.raises(SystemExit):
        cli.cmd_query(_args(domain="invalid", method="x", args=[], pretty=False))
    assert "Unknown domain" in output.pop()["error"]

    agent.stock_api = SimpleNamespace()
    with pytest.raises(SystemExit):
        cli.cmd_query(_args(domain="stock", method="missing", args=[], pretty=False))
    assert "Unknown method" in output.pop()["error"]

    agent.stock_api = MagicMock()
    agent.stock_api.get_stock_price.side_effect = RuntimeError("offline")
    with pytest.raises(SystemExit):
        cli.cmd_query(_args(domain="stock", method="get_stock_price", args=[], pretty=False))
    assert output.pop()["code"] == "RuntimeError"

    monkeypatch.setattr(cli, "search_stocks", lambda *_args, **_kwargs: [])
    cli.cmd_search(_args(query="없음", limit=1, pretty=False))
    assert output.pop()["data"]["search"]["count"] == 0


def test_check_market_status_caches_holiday_and_fallback(monkeypatch):
    class MondayMorning(cli.datetime):
        @classmethod
        def now(cls):
            return cls(2025, 1, 6, 8, 0)

    monkeypatch.setattr(cli, "datetime", MondayMorning)
    cli._market_status.update(checked=False, is_holiday=None, last_business_day=None, notice=None)
    agent = _agent()
    agent.stock_api.is_holiday.return_value = False
    cli._check_market_status(agent)
    assert cli._market_status["last_business_day"] == "20250106"
    assert "장 시작 전" in cli._market_status["notice"]

    cli._market_status.update(checked=False, is_holiday=None, last_business_day=None, notice=None)
    agent.stock_api.is_holiday.side_effect = [True, RuntimeError("offline")]
    cli._check_market_status(agent)
    assert cli._market_status["last_business_day"] == "20250103"
    assert "공휴일 미확인" in cli._market_status["notice"]


def test_order_cancel_and_modify_success_and_failure(monkeypatch):
    agent, output = _agent(), []
    monkeypatch.setattr(cli, "_create_agent", lambda: agent)
    monkeypatch.setattr(cli, "_out", lambda value, pretty=False: output.append(value))
    agent.account_api.order_rvsecncl.return_value = {"rt_cd": "0", "output": {"odno": "new"}}
    cli._cmd_order_cancel(_args(order_no="old", overseas=None, code=None, qty=1, yes=True))
    assert output.pop()["data"]["cancel"]["orderNo"] == "new"
    cli._cmd_order_modify(_args(order_no="old", overseas=None, code=None, qty=1, price=100, type="limit", yes=True))
    assert output.pop()["data"]["modify"]["origOrderNo"] == "old"
    agent.account_api.order_rvsecncl.return_value = None
    cli._cmd_order_cancel(_args(order_no="old", overseas=None, code=None, qty=0, yes=True))
    assert "error" in output.pop()


def test_overseas_order_cancel_and_modify(monkeypatch):
    agent, output = _agent(), []
    monkeypatch.setattr(cli, "_create_agent", lambda: agent)
    monkeypatch.setattr(cli, "_out", lambda value, pretty=False: output.append(value))
    agent.overseas_api.cancel_order.return_value = {"rt_cd": "0", "output": {"odno": "new"}}
    agent.overseas_api.modify_order.return_value = {"rt_cd": "0", "output": {"odno": "mod"}}
    cli._cmd_order_cancel(_args(order_no="old", overseas="nas", code="aapl", qty=1, yes=True))
    assert output.pop()["data"]["cancel"]["orderNo"] == "new"
    cli._cmd_order_modify(_args(order_no="old", overseas="nas", code="aapl", qty=1, price=10, type="limit", yes=True))
    assert output.pop()["data"]["modify"]["orderNo"] == "mod"
