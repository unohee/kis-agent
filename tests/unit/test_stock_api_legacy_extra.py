"""레거시 StockAPI의 위임 실패 및 폐기 API 회귀 테스트."""

import pytest

from kis_agent.stock.api import StockAPI


def _api():
    api = object.__new__(StockAPI)
    api._price_api = object()
    api._market_api = object()
    api._investor_api = object()
    return api


def test_legacy_api_getattr_error_paths_and_deprecated_orders():
    api = _api()
    api._market_api = type("MarketAPI", (), {"lookup": "delegated"})()

    with pytest.raises(AttributeError, match="_private"):
        _ = api._private
    assert api.lookup == "delegated"
    with pytest.raises(AttributeError, match="legacy class"):
        _ = api.not_supported
    with pytest.raises(DeprecationWarning):
        api.order_cash("005930", 1)
    with pytest.raises(DeprecationWarning):
        api.order_credit("005930", 1)
