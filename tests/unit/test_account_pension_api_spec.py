"""퇴직연금 계좌 APIs send exactly the fields the official KIS spec defines.

Sources: workbook [국내주식] 주문/계좌 sheets 국내주식-032 .. -036 and
open-trading-api examples_llm/domestic_stock/pension_*.
"""

from unittest.mock import MagicMock

import pytest

from kis_agent.account.api import AccountAPI
from kis_agent.account.pension_api import AccountPensionAPI
from kis_agent.core.tr_mapping import PaperTradingNotSupportedError, resolve_tr_id

ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "29"}
BASE = "/uapi/domestic-stock/v1/trading/pension/"
CURSOR_BLANK = {"CTX_AREA_FK100": "", "CTX_AREA_NK100": ""}


def _client(response=None):
    client = MagicMock()
    client.is_real = True
    client.make_request.return_value = response or {
        "rt_cd": "0",
        "output": {},
        "output1": [],
    }
    return client


def _api(client):
    return AccountPensionAPI(client, ACCOUNT, enable_cache=False, _from_agent=True)


def _sent(client, index=-1):
    return client.make_request.call_args_list[index].kwargs


def _expected(endpoint, tr_id, **params):
    return {
        "endpoint": BASE + endpoint,
        "tr_id": tr_id,
        "params": {"CANO": "12345678", "ACNT_PRDT_CD": "29", **params},
        "method": "GET",
    }


def test_deposit_sends_spec_fields():
    client = _client()
    _api(client).get_pension_deposit()
    assert _sent(client) == _expected("inquire-deposit", "TTTC0506R", ACCA_DVSN_CD="00")


def test_deposit_accepts_reserve_division():
    client = _client()
    _api(client).get_pension_deposit("01")
    assert _sent(client)["params"]["ACCA_DVSN_CD"] == "01"


def test_psbl_order_defaults_to_market_order():
    client = _client()
    _api(client).get_pension_psbl_order("069500")
    assert _sent(client) == _expected(
        "inquire-psbl-order",
        "TTTC0503R",
        PDNO="069500",
        ACCA_DVSN_CD="00",
        CMA_EVLU_AMT_ICLD_YN="Y",
        ORD_DVSN="01",
        ORD_UNPR="0",
    )


def test_psbl_order_limit_price_and_overrides():
    client = _client()
    _api(client).get_pension_psbl_order(
        "069500", 30800, "00", acca_dvsn_cd="01", cma_evlu_amt_icld_yn="N"
    )
    assert _sent(client) == _expected(
        "inquire-psbl-order",
        "TTTC0503R",
        PDNO="069500",
        ACCA_DVSN_CD="01",
        CMA_EVLU_AMT_ICLD_YN="N",
        ORD_DVSN="00",
        ORD_UNPR="30800",
    )


def test_daily_ccld_defaults_use_the_krx_only_tr():
    client = _client()
    _api(client).get_pension_daily_ccld()
    assert _sent(client) == _expected(
        "inquire-daily-ccld",
        "TTTC2201R",
        USER_DVSN_CD="%%",
        SLL_BUY_DVSN_CD="00",
        CCLD_NCCS_DVSN="%%",
        INQR_DVSN_3="00",
        **CURSOR_BLANK,
    )


def test_daily_ccld_include_nxt_selects_the_nxt_sor_tr():
    client = _client()
    _api(client).get_pension_daily_ccld("02", "02", "00", "%%", include_nxt=True)
    assert _sent(client) == _expected(
        "inquire-daily-ccld",
        "TTTC2210R",
        USER_DVSN_CD="%%",
        SLL_BUY_DVSN_CD="02",
        CCLD_NCCS_DVSN="02",
        INQR_DVSN_3="00",
        **CURSOR_BLANK,
    )


def test_present_balance_sends_spec_fields():
    client = _client()
    _api(client).get_pension_present_balance()
    assert _sent(client) == _expected(
        "inquire-present-balance", "TTTC2202R", USER_DVSN_CD="00", **CURSOR_BLANK
    )


def test_balance_sends_spec_fields():
    client = _client()
    _api(client).get_pension_balance()
    assert _sent(client) == _expected(
        "inquire-balance",
        "TTTC2208R",
        ACCA_DVSN_CD="00",
        INQR_DVSN="00",
        **CURSOR_BLANK,
    )


def test_balance_overrides():
    client = _client()
    _api(client).get_pension_balance("01", "01")
    assert _sent(client)["params"] == {
        "CANO": "12345678",
        "ACNT_PRDT_CD": "29",
        "ACCA_DVSN_CD": "01",
        "INQR_DVSN": "01",
        **CURSOR_BLANK,
    }


def _page(key, rows, tr_cont, fk, nk):
    return {
        "rt_cd": "0",
        "msg1": "ok",
        key: rows,
        "ctx_area_fk100": fk,
        "ctx_area_nk100": nk,
        "_tr_cont": tr_cont,
    }


@pytest.mark.parametrize(
    "method, key, endpoint, tr_id",
    [
        ("get_pension_daily_ccld", "output", "inquire-daily-ccld", "TTTC2201R"),
        (
            "get_pension_present_balance",
            "output1",
            "inquire-present-balance",
            "TTTC2202R",
        ),
        ("get_pension_balance", "output1", "inquire-balance", "TTTC2208R"),
    ],
)
def test_cursor_apis_follow_continuation_and_merge(method, key, endpoint, tr_id):
    client = MagicMock()
    client.is_real = True
    client.make_request.side_effect = [
        _page(key, [{"pdno": "A"}], "M", "fk-1", "nk-1"),
        _page(key, [{"pdno": "B"}], "D", "", ""),
    ]
    result = getattr(_api(client), method)()
    assert result[key] == [{"pdno": "A"}, {"pdno": "B"}]
    assert result["_pagination"] == {"pages": 2, "truncated": False, "error": None}
    second = _sent(client, 1)
    assert second["endpoint"] == BASE + endpoint
    assert second["tr_id"] == tr_id
    assert second["headers"] == {"tr_cont": "N"}
    assert second["params"]["CTX_AREA_FK100"] == "fk-1"
    assert second["params"]["CTX_AREA_NK100"] == "nk-1"


def test_max_pages_limits_the_walk():
    client = MagicMock()
    client.is_real = True
    client.make_request.side_effect = [
        _page("output1", [1], "M", "f1", "n1"),
        _page("output1", [2], "M", "f2", "n2"),
    ]
    result = _api(client).get_pension_balance(max_pages=2)
    assert client.make_request.call_count == 2
    assert result["_pagination"]["truncated"] is True


def test_pension_methods_reach_the_account_facade():
    client = _client()
    account = AccountAPI(client, ACCOUNT, enable_cache=False, _from_agent=True)
    account.get_pension_deposit()
    assert _sent(client)["tr_id"] == "TTTC0506R"
    account.get_pension_daily_ccld(include_nxt=True)
    assert _sent(client)["tr_id"] == "TTTC2210R"
    account.get_pension_psbl_order("069500", 1000, "00")
    assert _sent(client)["params"]["ORD_UNPR"] == "1000"


def test_existing_irp_routing_is_untouched():
    """AccountBalanceQueryAPI still routes IRP (29) get_account_balance to the pension URL."""
    client = _client()
    AccountAPI(
        client, ACCOUNT, enable_cache=False, _from_agent=True
    ).get_account_balance()
    assert _sent(client)["endpoint"] == BASE + "inquire-balance"
    assert _sent(client)["tr_id"] == "TTTC2208R"


@pytest.mark.parametrize(
    "tr_id",
    ["TTTC0506R", "TTTC2201R", "TTTC2210R", "TTTC0503R", "TTTC2202R", "TTTC2208R"],
)
def test_pension_tr_ids_are_unsupported_on_paper(tr_id):
    with pytest.raises(PaperTradingNotSupportedError):
        resolve_tr_id(tr_id, is_real=False)
