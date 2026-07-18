"""Overseas facade의 미노출 위임 메서드 회귀 테스트."""

from unittest.mock import MagicMock

from kis_agent.overseas.api_facade import OverseasStockAPI
from kis_agent.overseas_futures import OverseasFutures


def test_remaining_account_order_and_ranking_delegations():
    api = object.__new__(OverseasStockAPI)
    api.price_api = MagicMock()
    api.account_api = MagicMock()
    api.order_api = MagicMock()
    api.ranking_api = MagicMock()
    api.get_industry_theme("NAS", "AAPL")
    api.search_symbol("NAS", "AAPL")
    api.get_balance("NAS")
    api.get_order_history("NAS")
    api.get_unfilled_orders("NAS")
    api.get_buyable_amount("NAS")
    api.get_present_balance()
    api.get_period_profit()
    api.get_reserve_order_list()
    api.get_foreign_margin("USD")
    api.buy_order("NAS", "AAPL", 1, 1.0)
    api.sell_order("NAS", "AAPL", 1, 1.0)
    api.modify_order("NAS", "AAPL", "1", 1, 1.0)
    api.cancel_order("NAS", "AAPL", "1", 1)
    api.reserve_order("NAS", "AAPL", "02", 1, 1.0)
    api.modify_reserve_order("1", 1, 1.0)
    api.cancel_reserve_order("1")
    api.trade_volume_ranking("NAS")
    api.trade_amount_ranking("NAS")
    api.trade_growth_ranking("NAS")
    api.trade_turnover_ranking("NAS")
    api.market_cap_ranking("NAS")
    api.price_change_ranking("NAS")
    api.price_fluctuation_ranking("NAS")
    api.new_high_low_ranking("NAS")
    api.volume_power_ranking("NAS")
    api.volume_surge_ranking("NAS")
    assert api.account_api.get_balance.called and api.order_api.buy_order.called and api.ranking_api.volume_surge_ranking.called


def test_remaining_overseas_futures_delegations():
    api = object.__new__(OverseasFutures)
    api.price = MagicMock()
    api.account_api = MagicMock()

    api.get_option_price("OPT")
    api.get_option_orderbook("OPT")
    api.get_futures_info(["ES"])
    api.get_option_info(["OPT"])
    api.get_margin_detail("USD", "20250101")
    api.get_order_amount("ES", "02", "100", "Y")
    api.get_today_orders()
    api.get_daily_orders("20250101", "20250131")
    api.get_daily_executions("20250101", "20250131")
    api.get_period_profit("20250101", "20250131")
    api.get_period_transactions("20250101", "20250131")

    api.price.get_option_price.assert_called_once_with("OPT")
    api.price.get_option_orderbook.assert_called_once_with("OPT")
    api.price.get_futures_info.assert_called_once_with(["ES"])
    api.price.get_option_info.assert_called_once_with(["OPT"])
    api.account_api.get_margin_detail.assert_called_once_with("USD", "20250101")
    api.account_api.get_order_amount.assert_called_once_with("ES", "02", "100", "Y")
    api.account_api.get_today_orders.assert_called_once_with("01", "%%", "00")
    api.account_api.get_daily_orders.assert_called_once_with(
        "20250101", "20250131", "01", "%%", "00", ""
    )
    api.account_api.get_daily_executions.assert_called_once_with(
        "20250101", "20250131", "00", "%%", "%%%"
    )
    api.account_api.get_period_profit.assert_called_once_with(
        "20250101", "20250131", "%%%", "00", "N"
    )
    api.account_api.get_period_transactions.assert_called_once_with(
        "20250101", "20250131", "1", "%%%"
    )
