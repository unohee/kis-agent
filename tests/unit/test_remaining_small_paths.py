"""작은 예외 및 기본값 경로 회귀 테스트."""

import builtins
import importlib
import logging
from datetime import datetime
from unittest.mock import MagicMock

import pytest

import kis_agent.cli.schema as schema_module
import kis_agent.cli_bridge as bridge
import kis_agent.stock as stock_module
from kis_agent.account.api import AccountAPI
from kis_agent.core.base_exception_handler import exception_handler
from kis_agent.core.response_processor import DataFrameResponseProcessor
from kis_agent.futures.account_api import FuturesAccountAPI
from kis_agent.futures.order_api import FuturesOrderAPI
from kis_agent.overseas.price_api import OverseasPriceAPI


def test_dataframe_processor_rejects_non_tabular_output():
    processor = DataFrameResponseProcessor(lambda df, response: df, lambda df, field_type: df)
    assert processor.process({"rt_cd": "0", "output": "not-tabular"}) is None


def test_plain_object_exception_handler_warns_and_returns_default(caplog):
    class Plain:
        @exception_handler(reraise=False, default_return="fallback", log_level="warning", exceptions=ValueError)
        def fail(self):
            raise ValueError("bad")

    with caplog.at_level(logging.WARNING):
        assert Plain().fail() == "fallback"
    assert "fail 실행 실패" in caplog.text


def test_futures_account_defaults_without_account_or_base_url():
    api = object.__new__(FuturesAccountAPI)
    api.account = None
    api.client = object()
    assert api._get_account_no() == ""
    assert api._is_virtual() is False


def test_futures_order_defaults_without_account_or_base_url():
    api = object.__new__(FuturesOrderAPI)
    api.account = None
    api.client = object()
    assert api._get_account_no() == ""
    assert api._get_account_code() == "03"
    assert api._is_virtual() is False


def test_cli_bridge_after_market_close_notice(monkeypatch):
    evening = datetime(2025, 1, 6, 17, 0, 0)
    monkeypatch.setattr(
        bridge, "datetime", MagicMock(now=MagicMock(return_value=evening))
    )
    bridge._market_status.update(
        {"checked": False, "notice": None, "last_business_day": None}
    )
    agent = MagicMock()
    agent.stock_api.is_holiday.return_value = False

    bridge.check_market_status(agent)

    assert bridge._market_status["last_business_day"] == "20250106"
    assert "장 마감 후" in bridge._market_status["notice"]


def test_cli_bridge_falls_back_to_previous_weekday_when_holiday_api_fails(
    monkeypatch,
):
    tuesday = datetime(2025, 1, 7, 12, 0, 0)
    monkeypatch.setattr(
        bridge, "datetime", MagicMock(now=MagicMock(return_value=tuesday))
    )
    bridge._market_status.update(
        {"checked": False, "notice": None, "last_business_day": None}
    )
    agent = MagicMock()
    agent.stock_api.is_holiday.side_effect = [True, RuntimeError("offline")]

    bridge.check_market_status(agent)

    assert bridge._market_status["last_business_day"] == "20250106"
    assert "공휴일 미확인" in bridge._market_status["notice"]


def test_schema_includes_type_level_doc_comment(monkeypatch):
    monkeypatch.setattr(
        schema_module,
        "SCHEMA_SDL",
        '"""설명"""\ntype Documented {\n  value: String\n}\n',
    )
    assert schema_module.get_schema("Documented").startswith('"""설명"""')


def test_overseas_industry_theme_builds_expected_request():
    api = object.__new__(OverseasPriceAPI)
    api._make_request_dict = MagicMock(return_value={"rt_cd": "0"})

    result = api.get_industry_theme("nas", "aapl", "1", "Y")

    assert result == {"rt_cd": "0"}
    assert api._make_request_dict.call_args.kwargs["params"] == {
        "AUTH": "",
        "EXCD": "NAS",
        "SYMB": "AAPL",
        "ISCD_COND": "1",
        "CO_YN": "Y",
    }


def test_account_facade_remaining_delegations_and_attribute_errors():
    api = object.__new__(AccountAPI)
    api._balance_api = MagicMock()
    api._order_api = MagicMock()
    api._profit_api = MagicMock()
    api._delegate_methods = {"delegated": api._balance_api}
    api._balance_api.delegated = "value"

    assert api.delegated == "value"
    with pytest.raises(AttributeError):
        _ = api._private_missing
    with pytest.raises(AttributeError):
        _ = api.public_missing

    assert api.inquire_balance_rlz_pl() is api._balance_api.inquire_balance_rlz_pl.return_value
    assert api.inquire_psbl_sell("005930") is api._balance_api.inquire_psbl_sell.return_value
    assert api.inquire_intgr_margin() is api._balance_api.inquire_intgr_margin.return_value
    assert api.inquire_psbl_order(1000, "005930", "00") is api._balance_api.inquire_psbl_order.return_value
    assert api.inquire_credit_psamount("005930") is api._balance_api.inquire_credit_psamount.return_value
    assert api.order_cash("005930", 1, 1000, "buy") is api._order_api.order_cash.return_value
    assert api.order_cash_sor("005930", 1, "buy") is api._order_api.order_cash_sor.return_value
    assert api.order_credit_buy("005930", 1, 1000) is api._order_api.order_credit_buy.return_value
    assert api.order_credit_sell("005930", 1, 1000) is api._order_api.order_credit_sell.return_value
    assert api.inquire_period_rights("20250101", "20250131") is api._profit_api.inquire_period_rights.return_value


def test_stock_package_falls_back_when_legacy_api_import_fails(monkeypatch):
    original_import = builtins.__import__

    def fail_legacy_import(name, globals=None, locals=None, fromlist=(), level=0):
        if (
            level == 1
            and name == "api"
            and globals
            and globals.get("__package__") == "kis_agent.stock"
        ):
            raise ImportError("legacy API unavailable")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fail_legacy_import)
    try:
        reloaded = importlib.reload(stock_module)
        assert reloaded.LegacyStockAPI is None
        assert reloaded.get_kospi200_futures_code is None
    finally:
        monkeypatch.setattr(builtins, "__import__", original_import)
        importlib.reload(stock_module)
