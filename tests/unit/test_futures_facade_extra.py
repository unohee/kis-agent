"""Futures facade의 자동 코드·야간·과거/VKOSPI 편의 메서드 테스트."""

from unittest.mock import MagicMock, patch

from kis_agent.futures import Futures


def _facade():
    facade = Futures(MagicMock(), {"CANO": "1", "ACNT_PRDT_CD": "03"}, enable_cache=False)
    facade.price = MagicMock()
    facade.account_api = MagicMock()
    facade.order = MagicMock()
    facade.historical = MagicMock()
    facade.code = MagicMock()
    return facade


def test_night_and_current_master_convenience_methods():
    facade = _facade()
    facade.inquire_ngt_balance()
    facade.inquire_ngt_ccnl("20250101", "20250102")
    facade.inquire_psbl_ngt_order("101S03")
    facade.price.get_price.return_value = "price"
    facade.price.get_orderbook.return_value = "book"
    with patch("kis_agent.futures._get_current_master", return_value=None):
        assert facade.get_current_futures_price() is None
        assert facade.get_current_futures_orderbook() is None
    with patch("kis_agent.futures._get_current_master", return_value={"code": "101S03"}):
        assert facade.get_current_futures_price("CM") == "price"
        assert facade.get_current_futures_orderbook("CM") == "book"
    with patch("kis_agent.utils.futures_master.get_futures_by_month_type", return_value=[]):
        assert facade.get_next_futures_price() is None
    with patch("kis_agent.utils.futures_master.get_futures_by_month_type", return_value=[{"code": "101M06"}]):
        assert facade.get_next_futures_price("CM") == "price"


def test_option_order_chart_history_and_vkospi_helpers():
    facade = _facade()
    facade.code.generate_option_code.return_value = "201S340"
    facade.price.get_price.return_value = "option"
    assert facade.get_option_price("CALL", 340.0, 3) == "option"
    assert facade.get_call_option_price(340.0) == "option"
    assert facade.get_put_option_price(340.0) == "option"
    with patch("kis_agent.futures.generate_current_futures", return_value="101S03"):
        facade.get_current_futures_chart("20250101", "20250102", "W")
        facade.order_current_futures("02", "1", "0", "1")
    facade.order_option("PUT", 340.0, "01", "1", "2", 6)
    facade.get_historical_minute_bars("20250101", "20250102", "5", 2)
    facade.get_contract_minute_bars("101S03", "20250101", "20250102", "5", 2)
    facade.price.display_board_callput.side_effect = [None, {}]
    assert facade.get_vkospi() is None
    facade.price.display_board_callput.side_effect = [{"output": 1}, {"output": 2}]
    with patch("kis_agent.futures.VKOSPICalculator") as calculator:
        calculator.return_value.calculate.return_value = "vkospi"
        assert facade.get_vkospi("202501", "202502") == "vkospi"
