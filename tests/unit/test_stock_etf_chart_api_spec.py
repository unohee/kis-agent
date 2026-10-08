from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from kis_agent.stock import chart_api as chart_mod
from kis_agent.stock import etf_api as etf_mod
from kis_agent.stock.api_facade import StockAPI
from kis_agent.stock.chart_api import StockChartAPI
from kis_agent.stock.etf_api import StockEtfAPI

OK = {"rt_cd": "0", "msg1": "ok", "output": []}
ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}


def _api(cls):
    client = MagicMock()
    client.make_request.return_value = dict(OK)
    return cls(client, ACCOUNT, enable_cache=False, _from_agent=True), client


def _sent(client):
    kwargs = client.make_request.call_args.kwargs
    return kwargs["endpoint"], kwargs["tr_id"], kwargs["method"], kwargs["params"]


ETF = "/uapi/etfetn/v1/quotations/"
QUO = "/uapi/domestic-stock/v1/quotations/"


@pytest.fixture(autouse=True)
def _freeze(monkeypatch):
    monkeypatch.setattr(etf_mod, "_today", lambda: date(2026, 10, 8))
    monkeypatch.setattr(chart_mod, "_now", lambda: datetime(2026, 10, 8, 10, 15, 30))


class TestEtf:
    def test_price(self):
        api, client = _api(StockEtfAPI)
        assert api.get_etf_price("069500") == OK
        assert _sent(client) == (
            ETF + "inquire-price",
            "FHPST02400000",
            "GET",
            {"fid_input_iscd": "069500", "fid_cond_mrkt_div_code": "J"},
        )

    def test_component_stock_price(self):
        api, client = _api(StockEtfAPI)
        api.get_etf_component_stock_price("069500")
        assert _sent(client) == (
            ETF + "inquire-component-stock-price",
            "FHKST121600C0",
            "GET",
            {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "069500",
                "FID_COND_SCR_DIV_CODE": "11216",
            },
        )

    def test_nav_comparison_trend(self):
        api, client = _api(StockEtfAPI)
        api.get_etf_nav_comparison_trend("069500")
        assert _sent(client) == (
            ETF + "nav-comparison-trend",
            "FHPST02440000",
            "GET",
            {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "069500"},
        )

    def test_nav_daily_default_and_explicit_window(self):
        api, client = _api(StockEtfAPI)
        api.get_etf_nav_comparison_daily_trend("069500")
        assert _sent(client) == (
            ETF + "nav-comparison-daily-trend",
            "FHPST02440200",
            "GET",
            {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": "069500",
                "fid_input_date_1": "20260908",
                "fid_input_date_2": "20261008",
            },
        )
        api.get_etf_nav_comparison_daily_trend("069500", "20240101", "20240220")
        params = _sent(client)[3]
        assert (params["fid_input_date_1"], params["fid_input_date_2"]) == (
            "20240101",
            "20240220",
        )

    def test_nav_time_trend(self):
        api, client = _api(StockEtfAPI)
        api.get_etf_nav_comparison_time_trend("069500")
        assert _sent(client) == (
            ETF + "nav-comparison-time-trend",
            "FHPST02440100",
            "GET",
            {
                "fid_hour_cls_code": "60",
                "fid_cond_mrkt_div_code": "E",
                "fid_input_iscd": "069500",
            },
        )
        api.get_etf_nav_comparison_time_trend("069500", 180)
        assert _sent(client)[3]["fid_hour_cls_code"] == "180"


class TestChart:
    def test_today_minute_chart_defaults_to_now(self):
        api, client = _api(StockChartAPI)
        api.get_today_minute_chart("005930")
        assert _sent(client) == (
            QUO + "inquire-time-itemchartprice",
            "FHKST03010200",
            "GET",
            {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930",
                "FID_INPUT_HOUR_1": "101530",
                "FID_PW_DATA_INCU_YN": "Y",
                "FID_ETC_CLS_CODE": "",
            },
        )

    def test_today_minute_chart_explicit(self):
        api, client = _api(StockChartAPI)
        api.get_today_minute_chart("005930", "093000", "N", "NX")
        params = _sent(client)[3]
        assert (
            params["FID_INPUT_HOUR_1"],
            params["FID_PW_DATA_INCU_YN"],
            params["FID_COND_MRKT_DIV_CODE"],
        ) == ("093000", "N", "NX")

    def test_exp_closing_price(self):
        api, client = _api(StockChartAPI)
        api.get_exp_closing_price()
        assert _sent(client) == (
            QUO + "exp-closing-price",
            "FHKST117300C0",
            "GET",
            {
                "FID_RANK_SORT_CLS_CODE": "0",
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": "11173",
                "FID_INPUT_ISCD": "0000",
                "FID_BLNG_CLS_CODE": "0",
            },
        )
        api.get_exp_closing_price(sort="1", scope="1001", belong="1")
        params = _sent(client)[3]
        assert (
            params["FID_RANK_SORT_CLS_CODE"],
            params["FID_INPUT_ISCD"],
            params["FID_BLNG_CLS_CODE"],
        ) == ("1", "1001", "1")

    def test_overtime_conclusion_by_time(self):
        api, client = _api(StockChartAPI)
        api.get_overtime_conclusion_by_time("005930")
        assert _sent(client) == (
            QUO + "inquire-time-overtimeconclusion",
            "FHPST02310000",
            "GET",
            {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930",
                "FID_HOUR_CLS_CODE": "1",
            },
        )

    def test_real_clock_helpers(self, monkeypatch):
        monkeypatch.undo()
        assert etf_mod._today() == date.today()
        assert isinstance(chart_mod._now(), datetime)


def test_reachable_through_facade():
    client = MagicMock()
    client.make_request.return_value = dict(OK)
    stock = StockAPI(client, ACCOUNT, _from_agent=True)
    stock.get_etf_price("069500")
    assert client.make_request.call_args.kwargs["tr_id"] == "FHPST02400000"
    stock.get_exp_closing_price()
    assert client.make_request.call_args.kwargs["tr_id"] == "FHKST117300C0"
