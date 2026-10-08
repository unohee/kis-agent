"""Account read APIs send exactly the fields the official KIS spec defines.

Each test pins the COMPLETE request (endpoint, tr_id, params) against the
workbook "Required" column so a drifting key shows up as a test failure.
"""

from unittest.mock import MagicMock

import pytest

from kis_agent.account.api import AccountAPI
from kis_agent.account.balance_query_api import AccountBalanceQueryAPI
from kis_agent.account.profit_api import AccountProfitAPI
from kis_agent.core.tr_mapping import PaperTradingNotSupportedError

ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
BASE = "/uapi/domestic-stock/v1/trading/"


def _client(is_real=True):
    client = MagicMock()
    client.is_real = is_real
    client.make_request.return_value = {"rt_cd": "0", "output": {}, "output1": []}
    return client


def _balance(client):
    return AccountBalanceQueryAPI(client, ACCOUNT, enable_cache=False, _from_agent=True)


def _profit(client):
    return AccountProfitAPI(client, ACCOUNT, enable_cache=False, _from_agent=True)


def _sent(client, index=-1):
    return client.make_request.call_args_list[index].kwargs


# ----- balance query -----


def test_account_order_quantity_is_the_sellable_quantity():
    client = _client()
    _balance(client).get_account_order_quantity("005930")
    assert _sent(client) == {
        "endpoint": BASE + "inquire-psbl-sell",
        "tr_id": "TTTC8408R",
        "params": {"CANO": "12345678", "ACNT_PRDT_CD": "01", "PDNO": "005930"},
        "method": "GET",
    }

def test_psbl_sell_sends_only_spec_fields():
    client = _client()
    _balance(client).inquire_psbl_sell("005930")
    assert _sent(client) == {
        "endpoint": BASE + "inquire-psbl-sell",
        "tr_id": "TTTC8408R",
        "params": {"CANO": "12345678", "ACNT_PRDT_CD": "01", "PDNO": "005930"},
        "method": "GET",
    }


def test_intgr_margin_sends_required_fields_with_sample_defaults():
    client = _client()
    _balance(client).inquire_intgr_margin()
    assert _sent(client) == {
        "endpoint": BASE + "intgr-margin",
        "tr_id": "TTTC0869R",
        "params": {
            "CANO": "12345678",
            "ACNT_PRDT_CD": "01",
            "CMA_EVLU_AMT_ICLD_YN": "N",
            "WCRC_FRCR_DVSN_CD": "01",
            "FWEX_CTRT_FRCR_DVSN_CD": "01",
        },
        "method": "GET",
    }


def test_intgr_margin_overrides_flow_through_the_facade():
    client = _client()
    AccountAPI(client, ACCOUNT, enable_cache=False).inquire_intgr_margin(
        cma_evlu_amt_icld_yn="Y",
        wcrc_frcr_dvsn_cd="02",
        fwex_ctrt_frcr_dvsn_cd="02",
    )
    assert _sent(client)["params"] == {
        "CANO": "12345678",
        "ACNT_PRDT_CD": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "WCRC_FRCR_DVSN_CD": "02",
        "FWEX_CTRT_FRCR_DVSN_CD": "02",
    }


def test_credit_psamount_sends_only_spec_fields():
    client = _client()
    _balance(client).inquire_credit_psamount("005930")
    assert _sent(client) == {
        "endpoint": BASE + "inquire-credit-psamount",
        "tr_id": "TTTC8909R",
        "params": {
            "CANO": "12345678",
            "ACNT_PRDT_CD": "01",
            "PDNO": "005930",
            "ORD_UNPR": "0",
            "ORD_DVSN": "00",
            "CRDT_TYPE": "21",
            "CMA_EVLU_AMT_ICLD_YN": "Y",
            "OVRS_ICLD_YN": "N",
        },
        "method": "GET",
    }


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.get_account_order_quantity("005930"),
        lambda api: api.inquire_psbl_sell("005930"),
        lambda api: api.inquire_intgr_margin(),
        lambda api: api.inquire_credit_psamount("005930"),
    ],
)
def test_balance_queries_do_not_swallow_paper_trading_error(call):
    client = _client(is_real=False)
    client.make_request.side_effect = PaperTradingNotSupportedError("TTTC0000R")
    with pytest.raises(PaperTradingNotSupportedError):
        call(_balance(client))


# ----- profit -----


def _ccld_params(**overrides):
    params = {
        "CANO": "12345678",
        "ACNT_PRDT_CD": "01",
        "INQR_STRT_DT": "20990101",
        "INQR_END_DT": "20990131",
        "SLL_BUY_DVSN_CD": "00",
        "INQR_DVSN": "00",
        "PDNO": "",
        "CCLD_DVSN": "00",
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "INQR_DVSN_3": "00",
        "INQR_DVSN_1": "",
        "EXCG_ID_DVSN_CD": "ALL",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }
    params.update(overrides)
    return params


def test_daily_ccld_single_request_defaults_to_all_exchanges_on_real():
    client = _client(is_real=True)
    _profit(client).inquire_daily_ccld("20990101", "20990131")
    assert _sent(client) == {
        "endpoint": BASE + "inquire-daily-ccld",
        "tr_id": "TTTC0081R",
        "params": _ccld_params(),
        "method": "GET",
    }


def test_daily_ccld_defaults_to_krx_on_paper_trading():
    client = _client(is_real=False)
    _profit(client).inquire_daily_ccld("20990101", "20990131")
    assert _sent(client)["params"] == _ccld_params(EXCG_ID_DVSN_CD="KRX")


def test_daily_ccld_explicit_exchange_wins():
    client = _client()
    _profit(client).inquire_daily_ccld("20990101", "20990131", excg_id_dvsn_cd="NXT")
    assert _sent(client)["params"] == _ccld_params(EXCG_ID_DVSN_CD="NXT")


def test_daily_ccld_pagination_sends_exchange_on_every_page_via_facade():
    client = _client()
    page = [{"ord_dt": "20990101", "odno": str(i), "pdno": "005930"} for i in range(100)]
    client.make_request.side_effect = [
        {
            "rt_cd": "0",
            "msg1": "조회가 계속됩니다",
            "output1": page,
            "ctx_area_fk100": "fk",
            "ctx_area_nk100": "nk",
        },
        {"rt_cd": "0", "msg1": "완료", "output1": []},
    ]
    AccountAPI(client, ACCOUNT, enable_cache=False).inquire_daily_ccld(
        "20990101", "20990131", pagination=True, excg_id_dvsn_cd="SOR"
    )
    first, second = client.make_request.call_args_list
    expected = _ccld_params(
        EXCG_ID_DVSN_CD="SOR",
        CCLD_DVSN="00",
        INQR_DVSN="01",
    )
    assert first.kwargs["endpoint"] == BASE + "inquire-daily-ccld"
    assert first.kwargs["tr_id"] == "TTTC0081R"
    assert first.kwargs["params"] == expected
    assert second.kwargs["params"] == {
        **expected,
        "CTX_AREA_FK100": "fk",
        "CTX_AREA_NK100": "nk",
    }


def test_daily_ccld_pagination_default_exchange_follows_environment():
    for is_real, expected in ((True, "ALL"), (False, "KRX")):
        client = _client(is_real=is_real)
        _profit(client)._inquire_daily_ccld_pagination("20990101", "20990131")
        assert _sent(client)["params"]["EXCG_ID_DVSN_CD"] == expected


def test_period_rights_sends_the_official_parameter_set():
    client = _client()
    _profit(client).inquire_period_rights("20250101", "20250131")
    assert _sent(client) == {
        "endpoint": BASE + "period-rights",
        "tr_id": "CTRGA011R",
        "params": {
            "INQR_DVSN": "03",
            "CUST_RNCNO25": "",
            "HMID": "",
            "CANO": "12345678",
            "ACNT_PRDT_CD": "01",
            "INQR_STRT_DT": "20250101",
            "INQR_END_DT": "20250131",
            "RGHT_TYPE_CD": "",
            "PDNO": "",
            "PRDT_TYPE_CD": "",
            "CTX_AREA_NK100": "",
            "CTX_AREA_FK100": "",
        },
        "method": "GET",
    }


def test_period_rights_optional_filters_flow_through_the_facade():
    client = _client()
    AccountAPI(client, ACCOUNT, enable_cache=False).inquire_period_rights(
        "20250101",
        "20250131",
        pdno="005930",
        rght_type_cd="01",
        prdt_type_cd="300",
        inqr_dvsn="03",
    )
    params = _sent(client)["params"]
    assert params["PDNO"] == "005930"
    assert params["RGHT_TYPE_CD"] == "01"
    assert params["PRDT_TYPE_CD"] == "300"


def test_period_rights_does_not_swallow_paper_trading_error():
    client = _client(is_real=False)
    client.make_request.side_effect = PaperTradingNotSupportedError("CTRGA011R")
    with pytest.raises(PaperTradingNotSupportedError):
        _profit(client).inquire_period_rights("20250101", "20250131")
