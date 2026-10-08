from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from kis_agent.stock import finance_api as mod
from kis_agent.stock.api_facade import StockAPI
from kis_agent.stock.finance_api import StockFinanceAPI

OK = {"rt_cd": "0", "msg1": "ok", "output": []}
ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}


def _api(cls):
    client = MagicMock()
    client.make_request.return_value = dict(OK)
    return cls(client, ACCOUNT, enable_cache=False, _from_agent=True), client


def _sent(client):
    kwargs = client.make_request.call_args.kwargs
    return kwargs["endpoint"], kwargs["tr_id"], kwargs["method"], kwargs["params"]


FIN = "/uapi/domestic-stock/v1/finance/"
QUO = "/uapi/domestic-stock/v1/quotations/"


@pytest.fixture(autouse=True)
def _freeze(monkeypatch):
    monkeypatch.setattr(mod, "_today", lambda: date(2026, 10, 8))


STATEMENTS = [
    ("get_balance_sheet", "balance-sheet", "FHKST66430100", "FID_DIV_CLS_CODE"),
    ("get_income_statement", "income-statement", "FHKST66430200", "FID_DIV_CLS_CODE"),
    ("get_profit_ratio", "profit-ratio", "FHKST66430400", "FID_DIV_CLS_CODE"),
    (
        "get_other_major_ratios",
        "other-major-ratios",
        "FHKST66430500",
        "fid_div_cls_code",
    ),
    ("get_stability_ratio", "stability-ratio", "FHKST66430600", "fid_div_cls_code"),
    ("get_growth_ratio", "growth-ratio", "FHKST66430800", "fid_div_cls_code"),
]


@pytest.mark.parametrize("name,slug,tr_id,div_key", STATEMENTS)
class TestFinanceStatements:
    def test_defaults(self, name, slug, tr_id, div_key):
        api, client = _api(StockFinanceAPI)
        assert getattr(api, name)("000660") == OK
        endpoint, tr, method, params = _sent(client)
        assert (endpoint, tr, method) == (FIN + slug, tr_id, "GET")
        assert params == {
            div_key: "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": "000660",
        }

    def test_quarterly_override(self, name, slug, tr_id, div_key):
        api, client = _api(StockFinanceAPI)
        getattr(api, name)("005930", period="1", market="J")
        assert _sent(client)[3][div_key] == "1"


class TestQuotationInfo:
    def test_search_info(self):
        api, client = _api(StockFinanceAPI)
        api.get_search_info("000660")
        assert _sent(client) == (
            QUO + "search-info",
            "CTPF1604R",
            "GET",
            {"PDNO": "000660", "PRDT_TYPE_CD": "300"},
        )
        api.get_search_info("AAPL", product_type="512")
        assert _sent(client)[3] == {"PDNO": "AAPL", "PRDT_TYPE_CD": "512"}

    def test_invest_opinion_default_window(self):
        api, client = _api(StockFinanceAPI)
        api.get_invest_opinion("005930")
        assert _sent(client) == (
            QUO + "invest-opinion",
            "FHKST663300C0",
            "GET",
            {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": "16633",
                "FID_INPUT_ISCD": "005930",
                "FID_INPUT_DATE_1": "20260710",
                "FID_INPUT_DATE_2": "20261008",
            },
        )

    def test_invest_opinion_explicit_dates(self):
        api, client = _api(StockFinanceAPI)
        api.get_invest_opinion("005930", "20230101", "20231231", market="J")
        params = _sent(client)[3]
        assert (params["FID_INPUT_DATE_1"], params["FID_INPUT_DATE_2"]) == (
            "20230101",
            "20231231",
        )

    def test_invest_opinion_by_sec(self):
        api, client = _api(StockFinanceAPI)
        api.get_invest_opinion_by_sec("J04")
        assert _sent(client) == (
            QUO + "invest-opbysec",
            "FHKST663400C0",
            "GET",
            {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": "16634",
                "FID_INPUT_ISCD": "J04",
                "FID_DIV_CLS_CODE": "0",
                "FID_INPUT_DATE_1": "20260710",
                "FID_INPUT_DATE_2": "20261008",
            },
        )
        api.get_invest_opinion_by_sec("J04", "20230101", "20231231", opinion="1")
        params = _sent(client)[3]
        assert params["FID_DIV_CLS_CODE"] == "1"
        assert (params["FID_INPUT_DATE_1"], params["FID_INPUT_DATE_2"]) == (
            "20230101",
            "20231231",
        )

    def test_credit_by_company(self):
        api, client = _api(StockFinanceAPI)
        api.get_credit_by_company()
        assert _sent(client) == (
            QUO + "credit-by-company",
            "FHPST04770000",
            "GET",
            {
                "fid_rank_sort_cls_code": "0",
                "fid_slct_yn": "0",
                "fid_input_iscd": "0000",
                "fid_cond_scr_div_code": "20477",
                "fid_cond_mrkt_div_code": "J",
            },
        )
        api.get_credit_by_company("1", "1", "1001")
        params = _sent(client)[3]
        assert (
            params["fid_rank_sort_cls_code"],
            params["fid_slct_yn"],
            params["fid_input_iscd"],
        ) == ("1", "1", "1001")

    def test_estimate_perform(self):
        api, client = _api(StockFinanceAPI)
        api.get_estimate_perform("265520")
        assert _sent(client) == (
            QUO + "estimate-perform",
            "HHKST668300C0",
            "GET",
            {"SHT_CD": "265520"},
        )


class TestLendableByCompany:
    EXPECTED = {
        "EXCG_DVSN_CD": "00",
        "PDNO": "",
        "THCO_STLN_PSBL_YN": "Y",
        "INQR_DVSN_1": "0",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK100": "",
    }

    def test_single_page(self):
        api, client = _api(StockFinanceAPI)
        res = api.get_lendable_by_company()
        assert res["output"] == []
        assert _sent(client) == (
            QUO + "lendable-by-company",
            "CTSC2702R",
            "GET",
            self.EXPECTED,
        )

    def test_arguments(self):
        api, client = _api(StockFinanceAPI)
        api.get_lendable_by_company("02", "005930", "1")
        params = _sent(client)[3]
        assert (params["EXCG_DVSN_CD"], params["PDNO"], params["INQR_DVSN_1"]) == (
            "02",
            "005930",
            "1",
        )

    def test_multi_page_merges_and_sends_cursor(self):
        api, client = _api(StockFinanceAPI)
        client.make_request.side_effect = [
            {
                "rt_cd": "0",
                "msg1": "ok",
                "output1": [{"pdno": "A"}],
                "ctx_area_fk200": "FK",
                "ctx_area_nk100": "NK",
                "_tr_cont": "M",
            },
            {
                "rt_cd": "0",
                "msg1": "ok",
                "output1": [{"pdno": "B"}],
                "ctx_area_fk200": "",
                "ctx_area_nk100": "",
                "_tr_cont": "D",
            },
        ]
        res = api.get_lendable_by_company()
        assert [r["pdno"] for r in res["output1"]] == ["A", "B"]
        assert res["_pagination"]["pages"] == 2
        second = client.make_request.call_args_list[1].kwargs["params"]
        assert (second["CTX_AREA_FK200"], second["CTX_AREA_NK100"]) == ("FK", "NK")


def test_reachable_through_facade():
    client = MagicMock()
    client.make_request.return_value = dict(OK)
    stock = StockAPI(client, ACCOUNT, _from_agent=True)
    assert stock.get_balance_sheet("000660") == OK
    assert client.make_request.call_args.kwargs["tr_id"] == "FHKST66430100"
    stock.get_estimate_perform("265520")
    assert client.make_request.call_args.kwargs["tr_id"] == "HHKST668300C0"


def test_real_clock_helper(monkeypatch):
    monkeypatch.undo()
    assert mod._today() == date.today()
