"""Extra index APIs (예상체결지수, 전체지수, 현재지수, 금리 종합) against the KIS contract.

Every method is asserted against the official KIS contract (workbook
한국투자증권_오픈API_전체문서_20251212 and open-trading-api examples_llm): endpoint,
TR_ID, HTTP method and the COMPLETE params dict, once with defaults and once with
every keyword argument overridden (proving each argument lands on its own key).
"""

from unittest.mock import MagicMock

import pytest

from kis_agent.stock.api_facade import StockAPI
from kis_agent.stock.index_api import StockIndexAPI

OK = {"rt_cd": "0", "msg1": "ok", "output": []}
ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
TODAY = "20261008"

CASES = [
    {
        "method": "get_exp_index_trend",
        "endpoint": "/uapi/domestic-stock/v1/quotations/exp-index-trend",
        "tr_id": "FHPST01840000",
        "default_call": {},
        "default_params": {
            "FID_MKOP_CLS_CODE": "1",
            "FID_INPUT_HOUR_1": "600",
            "FID_INPUT_ISCD": "0001",
            "FID_COND_MRKT_DIV_CODE": "U",
        },
        "override_call": {
            "index_code": "v_index_code",
            "session": "v_session",
            "interval": "v_interval",
            "market": "v_market",
        },
        "override_params": {
            "FID_MKOP_CLS_CODE": "v_session",
            "FID_INPUT_HOUR_1": "v_interval",
            "FID_INPUT_ISCD": "v_index_code",
            "FID_COND_MRKT_DIV_CODE": "v_market",
        },
    },
    {
        "method": "get_exp_total_index",
        "endpoint": "/uapi/domestic-stock/v1/quotations/exp-total-index",
        "tr_id": "FHKUP11750000",
        "default_call": {},
        "default_params": {
            "fid_mrkt_cls_code": "0",
            "fid_cond_mrkt_div_code": "U",
            "fid_cond_scr_div_code": "11175",
            "fid_input_iscd": "0000",
            "fid_mkop_cls_code": "1",
        },
        "override_call": {
            "market_cls": "v_market_cls",
            "index_code": "v_index_code",
            "session": "v_session",
            "market": "v_market",
        },
        "override_params": {
            "fid_mrkt_cls_code": "v_market_cls",
            "fid_cond_mrkt_div_code": "v_market",
            "fid_cond_scr_div_code": "11175",
            "fid_input_iscd": "v_index_code",
            "fid_mkop_cls_code": "v_session",
        },
    },
    {
        "method": "get_index_price",
        "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-index-price",
        "tr_id": "FHPUP02100000",
        "default_call": {},
        "default_params": {"FID_COND_MRKT_DIV_CODE": "U", "FID_INPUT_ISCD": "0001"},
        "override_call": {"index_code": "v_index_code", "market": "v_market"},
        "override_params": {
            "FID_COND_MRKT_DIV_CODE": "v_market",
            "FID_INPUT_ISCD": "v_index_code",
        },
    },
    {
        "method": "get_comp_interest",
        "endpoint": "/uapi/domestic-stock/v1/quotations/comp-interest",
        "tr_id": "FHPST07020000",
        "default_call": {},
        "default_params": {
            "FID_COND_MRKT_DIV_CODE": "I",
            "FID_COND_SCR_DIV_CODE": "20702",
            "FID_DIV_CLS_CODE": "1",
            "FID_DIV_CLS_CODE1": "",
        },
        "override_call": {"div_cls": "v_div_cls", "div_cls1": "v_div_cls1"},
        "override_params": {
            "FID_COND_MRKT_DIV_CODE": "I",
            "FID_COND_SCR_DIV_CODE": "20702",
            "FID_DIV_CLS_CODE": "v_div_cls",
            "FID_DIV_CLS_CODE1": "v_div_cls1",
        },
    },
]


def _api(cls):
    client = MagicMock()
    client.make_request.return_value = dict(OK)
    return cls(client, dict(ACCOUNT), enable_cache=False, _from_agent=True), client


def _sent(client):
    assert client.make_request.call_count == 1
    return client.make_request.call_args.kwargs


IDS = [c["method"] for c in CASES]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_defaults_match_the_contract(case, monkeypatch):
    del monkeypatch
    api, client = _api(StockIndexAPI)
    assert getattr(api, case["method"])(**case["default_call"]) == OK
    assert _sent(client) == {
        "endpoint": case["endpoint"],
        "tr_id": case["tr_id"],
        "params": case["default_params"],
        "method": "GET",
    }


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_every_argument_reaches_its_own_key(case, monkeypatch):
    del monkeypatch
    api, client = _api(StockIndexAPI)
    getattr(api, case["method"])(**case["override_call"])
    assert _sent(client) == {
        "endpoint": case["endpoint"],
        "tr_id": case["tr_id"],
        "params": case["override_params"],
        "method": "GET",
    }


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_literal_tr_id_in_source(case):
    import inspect

    source = inspect.getsource(getattr(StockIndexAPI, case["method"]))
    assert f'tr_id="{case["tr_id"]}"' in source
    assert case["endpoint"] in source


def test_index_methods_are_reachable_through_the_stock_facade():
    client = MagicMock()
    client.make_request.return_value = dict(OK)
    stock = StockAPI(client, _from_agent=True)
    assert stock.get_index_price("1001") == OK
    kwargs = _sent(client)
    assert kwargs["tr_id"] == "FHPUP02100000"
    assert kwargs["params"] == {"FID_COND_MRKT_DIV_CODE": "U", "FID_INPUT_ISCD": "1001"}


def test_deprecated_inquire_index_price_still_redirects_to_timeprice():
    api, client = _api(StockIndexAPI)
    with pytest.warns(DeprecationWarning):
        api.inquire_index_price("0001")
    assert _sent(client)["tr_id"] == "FHPUP02110200"
