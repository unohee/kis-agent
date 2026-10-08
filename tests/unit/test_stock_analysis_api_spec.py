"""Domestic quote-analysis APIs (quotations/*) and program-trade today against the KIS contract.

Every method is asserted against the official KIS contract (workbook
한국투자증권_오픈API_전체문서_20251212 and open-trading-api examples_llm): endpoint,
TR_ID, HTTP method and the COMPLETE params dict, once with defaults and once with
every keyword argument overridden (proving each argument lands on its own key).
"""

from unittest.mock import MagicMock

import pytest

from kis_agent.program.trade import ProgramTradeAPI
from kis_agent.stock.analysis_api import StockAnalysisAPI
from kis_agent.stock.api_facade import StockAPI

OK = {"rt_cd": "0", "msg1": "ok", "output": []}
ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
TODAY = "20261008"

CASES = [
    {
        "method": "get_capture_uplowprice",
        "endpoint": "/uapi/domestic-stock/v1/quotations/capture-uplowprice",
        "tr_id": "FHKST130000C0",
        "default_call": {},
        "default_params": {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "11300",
            "FID_PRC_CLS_CODE": "0",
            "FID_DIV_CLS_CODE": "0",
            "FID_INPUT_ISCD": "0000",
            "FID_TRGT_CLS_CODE": "",
            "FID_TRGT_EXLS_CLS_CODE": "",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
        },
        "override_call": {
            "limit_type": "v_limit_type",
            "div_cls": "v_div_cls",
            "index_code": "v_index_code",
            "market": "v_market",
        },
        "override_params": {
            "FID_COND_MRKT_DIV_CODE": "v_market",
            "FID_COND_SCR_DIV_CODE": "11300",
            "FID_PRC_CLS_CODE": "v_limit_type",
            "FID_DIV_CLS_CODE": "v_div_cls",
            "FID_INPUT_ISCD": "v_index_code",
            "FID_TRGT_CLS_CODE": "",
            "FID_TRGT_EXLS_CLS_CODE": "",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
        },
    },
    {
        "method": "get_daily_loan_trans",
        "endpoint": "/uapi/domestic-stock/v1/quotations/daily-loan-trans",
        "tr_id": "HHPST074500C0",
        "default_call": {},
        "default_params": {
            "MRKT_DIV_CLS_CODE": "3",
            "MKSC_SHRN_ISCD": "",
            "START_DATE": "",
            "END_DATE": "",
            "CTS": "",
        },
        "override_call": {
            "code": "v_code",
            "division": "v_division",
            "start_date": "v_start_date",
            "end_date": "v_end_date",
            "cts": "v_cts",
        },
        "override_params": {
            "MRKT_DIV_CLS_CODE": "v_division",
            "MKSC_SHRN_ISCD": "v_code",
            "START_DATE": "v_start_date",
            "END_DATE": "v_end_date",
            "CTS": "v_cts",
        },
    },
    {
        "method": "get_daily_short_sale",
        "endpoint": "/uapi/domestic-stock/v1/quotations/daily-short-sale",
        "tr_id": "FHPST04830000",
        "default_call": {"code": "005930"},
        "default_params": {
            "FID_INPUT_DATE_2": "",
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": "005930",
            "FID_INPUT_DATE_1": "",
        },
        "override_call": {
            "code": "v_code",
            "market": "v_market",
            "start_date": "v_start_date",
            "end_date": "v_end_date",
        },
        "override_params": {
            "FID_INPUT_DATE_2": "v_end_date",
            "FID_COND_MRKT_DIV_CODE": "v_market",
            "FID_INPUT_ISCD": "v_code",
            "FID_INPUT_DATE_1": "v_start_date",
        },
    },
    {
        "method": "get_exp_price_trend",
        "endpoint": "/uapi/domestic-stock/v1/quotations/exp-price-trend",
        "tr_id": "FHPST01810000",
        "default_call": {"code": "005930"},
        "default_params": {
            "fid_mkop_cls_code": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": "005930",
        },
        "override_call": {
            "code": "v_code",
            "market": "v_market",
            "session": "v_session",
        },
        "override_params": {
            "fid_mkop_cls_code": "v_session",
            "fid_cond_mrkt_div_code": "v_market",
            "fid_input_iscd": "v_code",
        },
    },
    {
        "method": "get_daily_trade_volume",
        "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-daily-trade-volume",
        "tr_id": "FHKST03010800",
        "default_call": {"code": "005930"},
        "default_params": {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": "005930",
            "FID_INPUT_DATE_1": "",
            "FID_INPUT_DATE_2": "",
            "FID_PERIOD_DIV_CODE": "D",
        },
        "override_call": {
            "code": "v_code",
            "market": "v_market",
            "period": "v_period",
            "start_date": "v_start_date",
            "end_date": "v_end_date",
        },
        "override_params": {
            "FID_COND_MRKT_DIV_CODE": "v_market",
            "FID_INPUT_ISCD": "v_code",
            "FID_INPUT_DATE_1": "v_start_date",
            "FID_INPUT_DATE_2": "v_end_date",
            "FID_PERIOD_DIV_CODE": "v_period",
        },
    },
    {
        "method": "get_investor_time_by_market",
        "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-investor-time-by-market",
        "tr_id": "FHPTJ04030000",
        "default_call": {},
        "default_params": {"fid_input_iscd": "KSP", "fid_input_iscd_2": "0001"},
        "override_call": {"market": "v_market", "sector": "v_sector"},
        "override_params": {
            "fid_input_iscd": "v_market",
            "fid_input_iscd_2": "v_sector",
        },
    },
    {
        "method": "get_mktfunds",
        "endpoint": "/uapi/domestic-stock/v1/quotations/mktfunds",
        "tr_id": "FHKST649100C0",
        "default_call": {},
        "default_params": {"FID_INPUT_DATE_1": ""},
        "override_call": {"date": "v_date"},
        "override_params": {"FID_INPUT_DATE_1": "v_date"},
    },
    {
        "method": "get_tradprt_byamt",
        "endpoint": "/uapi/domestic-stock/v1/quotations/tradprt-byamt",
        "tr_id": "FHKST111900C0",
        "default_call": {"code": "005930"},
        "default_params": {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "11119",
            "FID_INPUT_ISCD": "005930",
        },
        "override_call": {"code": "v_code", "market": "v_market"},
        "override_params": {
            "FID_COND_MRKT_DIV_CODE": "v_market",
            "FID_COND_SCR_DIV_CODE": "11119",
            "FID_INPUT_ISCD": "v_code",
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
    api, client = _api(StockAnalysisAPI)
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
    api, client = _api(StockAnalysisAPI)
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

    source = inspect.getsource(getattr(StockAnalysisAPI, case["method"]))
    assert f'tr_id="{case["tr_id"]}"' in source
    assert case["endpoint"] in source


def test_analysis_methods_are_reachable_through_the_stock_facade():
    client = MagicMock()
    client.make_request.return_value = dict(OK)
    stock = StockAPI(client, _from_agent=True)
    assert stock.get_daily_short_sale("005930") == OK
    assert _sent(client)["tr_id"] == "FHPST04830000"
    client.make_request.reset_mock()
    stock.get_mktfunds()
    assert _sent(client)["endpoint"].endswith("/quotations/mktfunds")
    client.make_request.reset_mock()
    stock.get_investor_time_by_market()
    assert _sent(client)["tr_id"] == "FHPTJ04030000"


def test_daily_loan_trans_forwards_the_continuation_key_without_paging():
    api, client = _api(StockAnalysisAPI)
    api.get_daily_loan_trans("005930", cts="KEY1")
    assert _sent(client)["params"]["CTS"] == "KEY1"


PROGRAM_CASES = [
    {
        "method": "get_comp_program_trade_today",
        "endpoint": "/uapi/domestic-stock/v1/quotations/comp-program-trade-today",
        "tr_id": "FHPPG04600101",
        "default_call": {},
        "default_params": {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_MRKT_CLS_CODE": "K",
            "FID_SCTN_CLS_CODE": "",
            "FID_INPUT_ISCD": "",
            "FID_COND_MRKT_DIV_CODE1": "",
            "FID_INPUT_HOUR_1": "",
        },
        "override_call": {"market_cls": "v_market_cls", "market": "v_market"},
        "override_params": {
            "FID_COND_MRKT_DIV_CODE": "v_market",
            "FID_MRKT_CLS_CODE": "v_market_cls",
            "FID_SCTN_CLS_CODE": "",
            "FID_INPUT_ISCD": "",
            "FID_COND_MRKT_DIV_CODE1": "",
            "FID_INPUT_HOUR_1": "",
        },
    }
]


@pytest.mark.parametrize("case", PROGRAM_CASES, ids=["get_comp_program_trade_today"])
def test_program_trade_today_matches_the_contract(case):
    api, client = _api(ProgramTradeAPI)
    assert getattr(api, case["method"])(**case["default_call"]) == OK
    assert _sent(client) == {
        "endpoint": case["endpoint"],
        "tr_id": case["tr_id"],
        "params": case["default_params"],
        "method": "GET",
    }
    client.make_request.reset_mock()
    getattr(api, case["method"])(**case["override_call"])
    assert _sent(client)["params"] == case["override_params"]
