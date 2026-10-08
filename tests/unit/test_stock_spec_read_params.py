"""Domestic quote/analysis requests against the official KIS contract.

Each test asserts endpoint, TR_ID and the complete params dict for the
methods fixed by the 2026-10-08 spec audit (workbook
한국투자증권_오픈API_전체문서_20251212 and open-trading-api examples_llm).
"""

from unittest.mock import MagicMock, patch

import pytest

from kis_agent.core.agent import Agent
from kis_agent.core.client import API_ENDPOINTS
from kis_agent.program.trade import ProgramTradeAPI
from kis_agent.stock.condition import ConditionAPI
from kis_agent.stock.investor import InvestorPositionAnalyzer
from kis_agent.stock.investor_api import StockInvestorAPI
from kis_agent.stock.market_api import StockMarketAPI
from kis_agent.stock.price_api import StockPriceAPI

OK = {"rt_cd": "0", "msg1": "ok", "output": []}


def _api(cls):
    client = MagicMock()
    client.make_request.return_value = dict(OK)
    if cls is ConditionAPI:
        return cls(client), client
    return cls(client, {"CANO": "1", "ACNT_PRDT_CD": "01"}, enable_cache=False, _from_agent=True), client


def _sent(client):
    kwargs = client.make_request.call_args.kwargs
    return kwargs["endpoint"], kwargs["tr_id"], kwargs["params"]


class TestMarketRankingsRouteToRankingApis:
    def test_market_fluctuation_uses_fluctuation_rank(self):
        api, client = _api(StockMarketAPI)
        assert api.get_market_fluctuation() == OK
        endpoint, tr_id, params = _sent(client)
        assert (endpoint, tr_id) == (API_ENDPOINTS["FLUCTUATION"], "FHPST01700000")
        assert params == {
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20170",
            "fid_input_iscd": "0000",
            "fid_rank_sort_cls_code": "0",
            "fid_input_cnt_1": "50",
            "fid_prc_cls_code": "0",
            "fid_input_price_1": "0",
            "fid_input_price_2": "1000000",
            "fid_vol_cnt": "100000",
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
            "fid_div_cls_code": "0",
            "fid_rsfl_rate1": "-30",
            "fid_rsfl_rate2": "30",
        }

    def test_market_rankings_uses_volume_rank(self):
        api, client = _api(StockMarketAPI)
        api.get_market_rankings(volume=7000000, market="NX")
        endpoint, tr_id, params = _sent(client)
        assert (endpoint, tr_id) == (API_ENDPOINTS["VOLUME_RANK"], "FHPST01710000")
        assert params == {
            "FID_COND_MRKT_DIV_CODE": "NX",
            "FID_COND_SCR_DIV_CODE": "20171",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "111111111",
            "FID_TRGT_EXLS_CLS_CODE": "0000000000",
            "FID_INPUT_PRICE_1": "0",
            "FID_INPUT_PRICE_2": "1000000",
            "FID_VOL_CNT": "7000000",
            "FID_INPUT_DATE_1": "",
        }

    @pytest.mark.parametrize("volume,expected", [(0, ""), (1000000, "1000000")])
    def test_volume_power_uses_volume_power_rank(self, volume, expected):
        api, client = _api(StockMarketAPI)
        api.get_volume_power(volume=volume)
        endpoint, tr_id, params = _sent(client)
        assert (endpoint, tr_id) == (API_ENDPOINTS["VOLUME_POWER"], "FHPST01680000")
        assert params == {
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20168",
            "fid_input_iscd": "0000",
            "fid_div_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": expected,
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
        }


class TestAgentTopGainers:
    def _agent(self, response=None, error=None):
        agent = object.__new__(Agent)
        agent.stock_api = MagicMock()
        if error:
            agent.stock_api.get_market_fluctuation.side_effect = error
        else:
            agent.stock_api.get_market_fluctuation.return_value = response
        return agent

    def test_returns_the_ranking_rows(self):
        rows = [{"hts_kor_isnm": "A", "prdy_ctrt": "29.9"}]
        assert self._agent({"rt_cd": "0", "output": rows}).get_top_gainers() == rows

    @pytest.mark.parametrize("response", [None, {"rt_cd": "1"}, {"rt_cd": "0"}])
    def test_failure_or_empty_returns_empty_list(self, response):
        assert self._agent(response).get_top_gainers() == []

    def test_exception_returns_empty_list(self):
        assert self._agent(error=RuntimeError("x")).get_top_gainers() == []


class TestPriceApi:
    def test_market_time_is_the_futures_business_day_api(self):
        api, client = _api(StockPriceAPI)
        api.market_time("NX")
        endpoint, tr_id, params = _sent(client)
        assert (endpoint, tr_id, params) == (API_ENDPOINTS["MARKET_TIME"], "HHMCM000002C0", {})

    def test_market_value_comes_from_the_quote(self):
        api, client = _api(StockPriceAPI)
        api.market_value("005930", "UN")
        endpoint, tr_id, params = _sent(client)
        assert tr_id == "FHKST01010100"
        assert params == {"FID_COND_MRKT_DIV_CODE": "UN", "FID_INPUT_ISCD": "005930"}

    def test_profit_asset_index_is_refused(self):
        api, client = _api(StockPriceAPI)
        with pytest.warns(DeprecationWarning), pytest.raises(NotImplementedError, match="profit-asset-index"):
            api.profit_asset_index("0001")
        client.make_request.assert_not_called()

    @pytest.mark.parametrize("codes", ["005930, 000660", ["005930", "000660"]])
    def test_intstock_multprice_fills_numbered_slots(self, codes):
        api, client = _api(StockPriceAPI)
        api.intstock_multprice(codes, "UN")
        endpoint, tr_id, params = _sent(client)
        assert (endpoint, tr_id) == (API_ENDPOINTS["INTSTOCK_MULTPRICE"], "FHKST11300006")
        assert len(params) == 60
        assert params["FID_COND_MRKT_DIV_CODE_1"] == "UN"
        assert params["FID_INPUT_ISCD_1"] == "005930"
        assert params["FID_INPUT_ISCD_2"] == "000660"
        assert params["FID_COND_MRKT_DIV_CODE_3"] == "" and params["FID_INPUT_ISCD_30"] == ""

    @pytest.mark.parametrize("codes", ["", [], ",".join(str(i).zfill(6) for i in range(31))])
    def test_intstock_multprice_rejects_empty_or_too_many(self, codes):
        api, client = _api(StockPriceAPI)
        with pytest.raises(ValueError, match="1~30"):
            api.intstock_multprice(codes)
        client.make_request.assert_not_called()

    def test_minute_page_sends_only_spec_fields(self):
        api, client = _api(StockPriceAPI)
        api._fetch_minute_price_page("005930", "20261008", "130000", "J")
        _, tr_id, params = _sent(client)
        assert tr_id == "FHKST03010230"
        assert params == {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": "005930",
            "FID_INPUT_HOUR_1": "130000",
            "FID_PW_DATA_INCU_YN": "Y",
            "FID_INPUT_DATE_1": "20261008",
            "FID_FAKE_TICK_INCU_YN": "",
        }


class TestInvestorApis:
    def test_member_transaction_uses_member_daily(self):
        api, client = _api(StockInvestorAPI)
        with patch("kis_agent.stock.investor_api.datetime") as dt:
            dt.now.return_value.strftime.return_value = "20261008"
            api.get_member_transaction("005930", "00036", "NX")
        endpoint, tr_id, params = _sent(client)
        assert (endpoint, tr_id) == (API_ENDPOINTS["INQUIRE_MEMBER_DAILY"], "FHPST04540000")
        assert params == {
            "FID_COND_MRKT_DIV_CODE": "NX",
            "FID_INPUT_ISCD": "005930",
            "FID_INPUT_ISCD_2": "00036",
            "FID_INPUT_DATE_1": "20261008",
            "FID_INPUT_DATE_2": "20261008",
            "FID_SCTN_CLS_CODE": "",
        }

    def test_member_transaction_date_range(self):
        api, client = _api(StockInvestorAPI)
        api.get_member_transaction("005930", "00036", start_date="20261001", end_date="20261008")
        _, _, params = _sent(client)
        assert (params["FID_INPUT_DATE_1"], params["FID_INPUT_DATE_2"]) == ("20261001", "20261008")

    def test_program_trade_today_sends_exchange(self):
        api, client = _api(StockInvestorAPI)
        api.get_investor_program_trade_today("4", "UN")
        _, tr_id, params = _sent(client)
        assert tr_id == "HHPPG046600C1"
        assert params == {"EXCH_DIV_CLS_CODE": "UN", "MRKT_DIV_CLS_CODE": "4"}

    @pytest.mark.parametrize("market,sector", [("KSP", "0001"), ("KSQ", "1001")])
    def test_daily_market_trends(self, market, sector):
        client = MagicMock()
        client.make_request.return_value = dict(OK)
        analyzer = InvestorPositionAnalyzer(client)
        analyzer.get_daily_market_trends("20261008", market)
        kwargs = client.make_request.call_args.kwargs
        assert kwargs["tr_id"] == "FHPTJ04040000"
        assert kwargs["params"] == {
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": sector,
            "FID_INPUT_DATE_1": "20261008",
            "FID_INPUT_ISCD_1": market,
            "FID_INPUT_DATE_2": "20261008",
            "FID_INPUT_ISCD_2": sector,
        }


class TestProgramTradeByStock:
    def test_without_date_uses_the_fill_api(self):
        api, client = _api(ProgramTradeAPI)
        api.get_program_trade_by_stock("005930")
        _, tr_id, params = _sent(client)
        assert tr_id == "FHPPG04650101"
        assert params == {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"}

    def test_with_date_uses_the_daily_api(self):
        api, client = _api(ProgramTradeAPI)
        api.get_program_trade_by_stock("005930", ref_date="20261007")
        _, tr_id, params = _sent(client)
        assert tr_id == "FHPPG04650201"
        assert params == {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": "005930",
            "FID_INPUT_DATE_1": "20261007",
        }


class TestConditionSearch:
    def test_list_uses_psearch_title(self):
        api, client = _api(ConditionAPI)
        api.get_condition_list("hts_user")
        endpoint, tr_id, params = _sent(client)
        assert endpoint.endswith("/quotations/psearch-title")
        assert (tr_id, params) == ("HHKST03900300", {"user_id": "hts_user"})

    def test_result_uses_psearch_result(self):
        api, client = _api(ConditionAPI)
        api.get_condition_result(3, "hts_user")
        endpoint, tr_id, params = _sent(client)
        assert endpoint == API_ENDPOINTS["CONDITIONED_STOCK"]
        assert (tr_id, params) == ("HHKST03900400", {"user_id": "hts_user", "seq": "3"})

    def test_user_id_is_required(self):
        api, client = _api(ConditionAPI)
        with pytest.raises(ValueError, match="user_id"):
            api.get_condition_list()
        with pytest.raises(ValueError, match="user_id"):
            api.get_condition_result("0")
        client.make_request.assert_not_called()

    def test_request_errors_return_none(self):
        api, client = _api(ConditionAPI)
        client.make_request.side_effect = RuntimeError("offline")
        assert api.get_condition_list("u") is None
        assert api.get_condition_result("0", "u") is None

    @pytest.mark.parametrize(
        "call", [lambda a: a.save_condition("n", {}), lambda a: a.delete_condition("1")]
    )
    def test_save_and_delete_are_refused(self, call):
        api, client = _api(ConditionAPI)
        with pytest.warns(DeprecationWarning), pytest.raises(NotImplementedError, match="HTS"):
            call(api)
        client.make_request.assert_not_called()
