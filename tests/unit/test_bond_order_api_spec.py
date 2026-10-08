"""Bond orders and account queries against the official KIS contract.

Orders are captured at the HTTP layer (HTTP method, absent query string, final
TR_ID header, complete JSON body). Sources: KIS workbook sheets for
domestic-bond/v1/trading/* and open-trading-api examples_llm/domestic_bond/*.
Bonds are not served on the paper-trading host.
"""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from kis_agent.bond import BondAPI, BondOrderAPI
from kis_agent.core.client import KISClient
from kis_agent.core.config import KISConfig
from kis_agent.core.exceptions import APIException
from kis_agent.core.tr_mapping import PaperTradingNotSupportedError

ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
BASE = "/uapi/domestic-bond/v1/trading/"
CODE = "KR6095572D81"


class _Response:
    status_code = 200
    text = '{"rt_cd":"0","output":{}}'
    headers = {}

    def json(self):
        return {"rt_cd": "0", "output": {}}


@pytest.fixture
def wire(monkeypatch):
    """Return a factory building a BondOrderAPI whose HTTP calls are captured."""

    def _build(paper=False):
        monkeypatch.setenv("KIS_APP_KEY", "app-key")
        monkeypatch.setenv("KIS_APP_SECRET", "app-secret")
        monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")
        monkeypatch.delenv("KIS_BASE_URL", raising=False)
        if paper:
            monkeypatch.setenv("KIS_PAPER", "1")
        else:
            monkeypatch.delenv("KIS_PAPER", raising=False)
        config = KISConfig.from_env()
        client = KISClient(config=config, enable_rate_limiter=False, _defer_token=True)
        client.token = "token"
        monkeypatch.setattr(client, "_check_and_refresh_token", lambda: None)
        monkeypatch.setattr(
            "kis_agent.core.client.getTREnv",
            lambda: SimpleNamespace(
                my_token="token", my_app=config.APP_KEY, my_sec=config.APP_SECRET
            ),
        )
        sent = []

        def transport(method, url, **kwargs):
            sent.append({"method": method, "url": url, **kwargs})
            return _Response()

        monkeypatch.setattr("kis_agent.core.client.httpx.request", transport)
        api = BondOrderAPI(
            client=client,
            account_info=dict(ACCOUNT),
            enable_cache=False,
            _from_agent=True,
        )
        return api, sent

    return _build


def _one(sent, path):
    assert len(sent) == 1
    req = sent[0]
    assert req["method"] == "POST"
    assert req["params"] is None
    assert req["url"].endswith(BASE + path)
    return req["headers"]["tr_id"], req["json"]


# ---------------------------------------------------------------------- buy


def test_buy_defaults(wire):
    api, sent = wire()
    api.buy_bond(CODE, 10, 10460)
    tr_id, body = _one(sent, "buy")
    assert tr_id == "TTTC0952U"
    assert body == {
        **ACCOUNT,
        "PDNO": CODE,
        "ORD_QTY2": "10",
        "BOND_ORD_UNPR": "10460",
        "SAMT_MKET_PTCI_YN": "N",
        "BOND_RTL_MKET_YN": "N",
        "IDCR_STFNO": "",
        "MGCO_APTM_ODNO": "",
        "ORD_SVR_DVSN_CD": "0",
        "CTAC_TLNO": "",
    }


def test_buy_explicit_arguments_and_normalisation(wire):
    api, sent = wire()
    api.buy_bond(f" {CODE.lower()} ", "3", Decimal("10460.50"), "Y", "Y", "01012345678")
    _, body = _one(sent, "buy")
    assert body["PDNO"] == CODE
    assert body["ORD_QTY2"] == "3"
    assert body["BOND_ORD_UNPR"] == "10460.50"
    assert body["SAMT_MKET_PTCI_YN"] == "Y"
    assert body["BOND_RTL_MKET_YN"] == "Y"
    assert body["CTAC_TLNO"] == "01012345678"


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"code": ""}, "종목코드"),
        ({"code": None}, "종목코드"),
        ({"code": "KR123"}, "종목코드"),
        ({"quantity": 0}, "주문수량"),
        ({"quantity": -1}, "주문수량"),
        ({"quantity": 1.5}, "주문수량"),
        ({"quantity": True}, "주문수량"),
        ({"quantity": "abc"}, "주문수량"),
        ({"quantity": None}, "주문수량"),
        ({"price": 0}, "주문단가"),
        ({"price": -5}, "주문단가"),
        ({"price": "abc"}, "주문단가"),
        ({"price": float("nan")}, "주문단가"),
        ({"price": float("inf")}, "주문단가"),
        ({"price": True}, "주문단가"),
        ({"price": None}, "주문단가"),
        ({"samt_mket_ptci_yn": "y"}, "samt_mket_ptci_yn"),
        ({"bond_rtl_mket_yn": ""}, "bond_rtl_mket_yn"),
    ],
)
def test_buy_validation_sends_nothing(wire, kwargs, match):
    api, sent = wire()
    args = {"code": CODE, "quantity": 1, "price": 10000, **kwargs}
    with pytest.raises(ValueError, match=match):
        api.buy_bond(**args)
    assert sent == []


# --------------------------------------------------------------------- sell


def test_sell_defaults(wire):
    api, sent = wire()
    api.sell_bond(CODE, 1, 10000.0)
    tr_id, body = _one(sent, "sell")
    assert tr_id == "TTTC0958U"
    assert body == {
        **ACCOUNT,
        "ORD_DVSN": "01",
        "PDNO": CODE,
        "ORD_QTY2": "1",
        "BOND_ORD_UNPR": "10000.0",
        "SPRX_YN": "N",
        "BUY_DT": "",
        "BUY_SEQ": "",
        "SAMT_MKET_PTCI_YN": "N",
        "SLL_AGCO_OPPS_SLL_YN": "N",
        "BOND_RTL_MKET_YN": "N",
        "MGCO_APTM_ODNO": "",
        "ORD_SVR_DVSN_CD": "0",
        "CTAC_TLNO": "",
    }


@pytest.mark.parametrize(
    "ord_dvsn,buy_date,buy_seq,expected_seq",
    [
        ("02", "20260105", "", "0"),
        ("02", "20260105", "0", "0"),
        ("03", "20260105", "7", "7"),
    ],
)
def test_sell_by_date_and_by_price(wire, ord_dvsn, buy_date, buy_seq, expected_seq):
    api, sent = wire()
    api.sell_bond(CODE, 2, 9990, ord_dvsn, buy_date, buy_seq, "Y", "Y", "Y", "010")
    tr_id, body = _one(sent, "sell")
    assert tr_id == "TTTC0958U"
    assert body["ORD_DVSN"] == ord_dvsn
    assert body["BUY_DT"] == buy_date
    assert body["BUY_SEQ"] == expected_seq
    assert body["SPRX_YN"] == "Y"
    assert body["SAMT_MKET_PTCI_YN"] == "Y"
    assert body["BOND_RTL_MKET_YN"] == "Y"
    assert body["SLL_AGCO_OPPS_SLL_YN"] == "N"
    assert body["CTAC_TLNO"] == "010"


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"ord_dvsn": "04"}, "ord_dvsn"),
        ({"ord_dvsn": "01", "buy_date": "20260105"}, "비워야"),
        ({"ord_dvsn": "01", "buy_seq": "1"}, "비워야"),
        ({"ord_dvsn": "02"}, "YYYYMMDD"),
        ({"ord_dvsn": "02", "buy_date": "2026-01-05"}, "YYYYMMDD"),
        ({"ord_dvsn": "02", "buy_date": "20260105", "buy_seq": "3"}, "'0'"),
        ({"ord_dvsn": "03", "buy_date": "20260105"}, "buy_seq"),
        ({"ord_dvsn": "03", "buy_date": "20260105", "buy_seq": "x"}, "buy_seq"),
        ({"ord_dvsn": "03"}, "YYYYMMDD"),
        ({"code": "bad"}, "종목코드"),
        ({"quantity": 0}, "주문수량"),
        ({"price": 0}, "주문단가"),
        ({"sprx_yn": "X"}, "sprx_yn"),
        ({"samt_mket_ptci_yn": "X"}, "samt_mket_ptci_yn"),
        ({"bond_rtl_mket_yn": "X"}, "bond_rtl_mket_yn"),
    ],
)
def test_sell_validation_sends_nothing(wire, kwargs, match):
    api, sent = wire()
    args = {"code": CODE, "quantity": 1, "price": 10000, **kwargs}
    with pytest.raises(ValueError, match=match):
        api.sell_bond(**args)
    assert sent == []


# ------------------------------------------------------------ modify / cancel


def test_modify_partial_quantity(wire):
    api, sent = wire()
    api.modify_cancel_bond_order("modify", CODE, "0000015402", 2, 10460)
    tr_id, body = _one(sent, "order-rvsecncl")
    assert tr_id == "TTTC0953U"
    assert body == {
        **ACCOUNT,
        "PDNO": CODE,
        "ORGN_ODNO": "0000015402",
        "ORD_QTY2": "2",
        "BOND_ORD_UNPR": "10460",
        "QTY_ALL_ORD_YN": "N",
        "RVSE_CNCL_DVSN_CD": "01",
        "MGCO_APTM_ODNO": "",
        "ORD_SVR_DVSN_CD": "0",
        "CTAC_TLNO": "",
    }


def test_modify_all_remaining(wire):
    api, sent = wire()
    api.modify_cancel_bond_order(
        "modify",
        CODE,
        "0000015402",
        price="10461.5",
        all_remaining=True,
        contact_phone="010",
    )
    _, body = _one(sent, "order-rvsecncl")
    assert body["ORD_QTY2"] == "0"
    assert body["BOND_ORD_UNPR"] == "10461.5"
    assert body["QTY_ALL_ORD_YN"] == "Y"
    assert body["RVSE_CNCL_DVSN_CD"] == "01"
    assert body["CTAC_TLNO"] == "010"


def test_cancel_partial_sends_zero_price(wire):
    api, sent = wire()
    api.modify_cancel_bond_order("cancel", CODE, 15402, quantity=4, price=999)
    tr_id, body = _one(sent, "order-rvsecncl")
    assert tr_id == "TTTC0953U"
    assert body["RVSE_CNCL_DVSN_CD"] == "02"
    assert body["ORGN_ODNO"] == "15402"
    assert body["ORD_QTY2"] == "4"
    assert body["BOND_ORD_UNPR"] == "0"
    assert body["QTY_ALL_ORD_YN"] == "N"


def test_cancel_all_remaining(wire):
    api, sent = wire()
    api.modify_cancel_bond_order("cancel", CODE, "0000015402", all_remaining=True)
    _, body = _one(sent, "order-rvsecncl")
    assert body["RVSE_CNCL_DVSN_CD"] == "02"
    assert body["ORD_QTY2"] == "0"
    assert body["QTY_ALL_ORD_YN"] == "Y"


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"action": "amend"}, "action"),
        ({"action": "01"}, "action"),
        ({"orgn_odno": ""}, "원주문번호"),
        ({"orgn_odno": None}, "원주문번호"),
        ({"code": "bad"}, "종목코드"),
        ({"all_remaining": "Y"}, "all_remaining"),
        ({"all_remaining": True, "quantity": 1}, "all_remaining"),
        ({"quantity": None}, "quantity를 지정"),
        ({"quantity": 0}, "주문수량"),
        ({"price": None}, "price가 필요"),
        ({"price": 0}, "주문단가"),
    ],
)
def test_modify_cancel_validation_sends_nothing(wire, kwargs, match):
    api, sent = wire()
    args = {
        "action": "modify",
        "code": CODE,
        "orgn_odno": "1",
        "quantity": 1,
        "price": 10000,
        **kwargs,
    }
    with pytest.raises(ValueError, match=match):
        api.modify_cancel_bond_order(**args)
    assert sent == []


def test_cancel_still_requires_quantity_choice(wire):
    api, sent = wire()
    with pytest.raises(ValueError, match="quantity를 지정"):
        api.modify_cancel_bond_order("cancel", CODE, "1")
    assert sent == []


def test_orders_are_not_retried_on_http_error(wire, monkeypatch):
    api, sent = wire()

    def boom(method, url, **kwargs):
        sent.append(1)
        raise RuntimeError("network down")

    monkeypatch.setattr("kis_agent.core.client.httpx.request", boom)
    with pytest.raises(APIException):
        api.buy_bond(CODE, 1, 10000)
    assert len(sent) == 1


# ------------------------------------------------------------------ queries


def _qapi():
    client = MagicMock()
    client.make_request.return_value = {"rt_cd": "0", "output": []}
    return (
        BondOrderAPI(client, dict(ACCOUNT), enable_cache=False, _from_agent=True),
        client,
    )


def _paged(api, client, call, pages):
    """Run ``call`` against scripted pages; return (result, per-request snapshots)."""
    seen = []

    def fake(**kwargs):
        seen.append(
            {**kwargs, "params": dict(kwargs["params"])}
        )  # _paginate reuses its params dict
        return pages[len(seen) - 1]

    client.make_request.side_effect = fake
    return call(), seen


def test_psbl_rvsecncl_defaults_and_pagination():
    api, client = _qapi()
    today = datetime.now().strftime("%Y%m%d")
    api.get_bond_psbl_rvsecncl()
    assert client.make_request.call_args.kwargs == {
        "endpoint": BASE + "inquire-psbl-rvsecncl",
        "tr_id": "CTSC8035R",
        "params": {
            **ACCOUNT,
            "ORD_DT": today,
            "ODNO": "",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        },
        "method": "GET",
    }
    pages = [
        {
            "rt_cd": "0",
            "_tr_cont": "M",
            "ctx_area_fk200": "F",
            "ctx_area_nk200": "N",
            "output": [{"odno": "1"}],
        },
        {
            "rt_cd": "0",
            "_tr_cont": "D",
            "ctx_area_fk200": "",
            "ctx_area_nk200": "",
            "output": [{"odno": "2"}],
        },
    ]
    res, seen = _paged(
        api,
        client,
        lambda: api.get_bond_psbl_rvsecncl("20260105", "0001", max_pages=2),
        pages,
    )
    assert [r["odno"] for r in res["output"]] == ["1", "2"]
    assert seen[0]["params"] == {
        **ACCOUNT,
        "ORD_DT": "20260105",
        "ODNO": "0001",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": "",
    }
    assert seen[1]["params"]["CTX_AREA_FK200"] == "F"
    assert seen[1]["params"]["CTX_AREA_NK200"] == "N"
    assert seen[1]["headers"] == {"tr_cont": "N"}


def test_daily_ccld_defaults_and_pagination():
    api, client = _qapi()
    today = datetime.now().strftime("%Y%m%d")
    api.get_bond_daily_ccld()
    assert client.make_request.call_args.kwargs == {
        "endpoint": BASE + "inquire-daily-ccld",
        "tr_id": "CTSC8013R",
        "params": {
            **ACCOUNT,
            "INQR_STRT_DT": today,
            "INQR_END_DT": today,
            "SLL_BUY_DVSN_CD": "%",
            "SORT_SQN_DVSN": "01",
            "PDNO": "",
            "NCCS_YN": "N",
            "CTX_AREA_NK200": "",
            "CTX_AREA_FK200": "",
        },
        "method": "GET",
    }
    pages = [
        {
            "rt_cd": "0",
            "_tr_cont": "F",
            "ctx_area_fk200": "F",
            "ctx_area_nk200": "N",
            "output1": {"sum": 1},
            "output2": [{"odno": "1"}],
        },
        {
            "rt_cd": "0",
            "_tr_cont": "E",
            "ctx_area_fk200": "",
            "ctx_area_nk200": "",
            "output1": {"sum": 2},
            "output2": [{"odno": "2"}],
        },
    ]
    res, seen = _paged(
        api,
        client,
        lambda: api.get_bond_daily_ccld(
            "20260101", "20260105", "02", "02", CODE, "Y", max_pages=2
        ),
        pages,
    )
    assert [r["odno"] for r in res["output2"]] == ["1", "2"]
    assert seen[0]["params"] == {
        **ACCOUNT,
        "INQR_STRT_DT": "20260101",
        "INQR_END_DT": "20260105",
        "SLL_BUY_DVSN_CD": "02",
        "SORT_SQN_DVSN": "02",
        "PDNO": CODE,
        "NCCS_YN": "Y",
        "CTX_AREA_NK200": "",
        "CTX_AREA_FK200": "",
    }
    assert seen[1]["params"]["CTX_AREA_NK200"] == "N"
    assert seen[1]["params"]["CTX_AREA_FK200"] == "F"


def test_balance_defaults_and_pagination():
    api, client = _qapi()
    api.get_bond_balance()
    assert client.make_request.call_args.kwargs == {
        "endpoint": BASE + "inquire-balance",
        "tr_id": "CTSC8407R",
        "params": {
            **ACCOUNT,
            "INQR_CNDT": "00",
            "PDNO": "",
            "BUY_DT": "",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        },
        "method": "GET",
    }
    pages = [
        {
            "rt_cd": "0",
            "_tr_cont": "M",
            "ctx_area_fk200": "F",
            "ctx_area_nk200": "N",
            "output": [{"pdno": "A"}],
        },
        {
            "rt_cd": "0",
            "_tr_cont": "D",
            "ctx_area_fk200": "",
            "ctx_area_nk200": "",
            "output": [{"pdno": "B"}],
        },
    ]
    res, seen = _paged(
        api,
        client,
        lambda: api.get_bond_balance("01", CODE, "20260105", max_pages=2),
        pages,
    )
    assert [r["pdno"] for r in res["output"]] == ["A", "B"]
    assert seen[0]["params"] == {
        **ACCOUNT,
        "INQR_CNDT": "01",
        "PDNO": CODE,
        "BUY_DT": "20260105",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": "",
    }
    assert seen[1]["params"]["CTX_AREA_FK200"] == "F"
    assert seen[1]["params"]["CTX_AREA_NK200"] == "N"


def test_psbl_order_request():
    api, client = _qapi()
    api.get_bond_psbl_order("KR2033022D33", 1000)
    assert client.make_request.call_args.kwargs == {
        "endpoint": BASE + "inquire-psbl-order",
        "tr_id": "TTTC8910R",
        "params": {**ACCOUNT, "PDNO": "KR2033022D33", "BOND_ORD_UNPR": "1000"},
        "method": "GET",
    }


def test_facade_reachability():
    client = MagicMock()
    client.make_request.return_value = {"rt_cd": "0"}
    bond = BondAPI(client, dict(ACCOUNT), enable_cache=False, _from_agent=True)
    bond.buy_bond(CODE, 1, 10000)
    bond.get_bond_psbl_order(CODE, 10000)
    calls = client.make_request.call_args_list
    assert [c.kwargs["tr_id"] for c in calls] == ["TTTC0952U", "TTTC8910R"]
    assert [c.kwargs["method"] for c in calls] == ["POST", "GET"]


# -------------------------------------------------------------- paper mode


@pytest.mark.parametrize(
    "name,args",
    [
        ("buy_bond", (CODE, 1, 10000)),
        ("sell_bond", (CODE, 1, 10000)),
        ("modify_cancel_bond_order", ("cancel", CODE, "1", 1)),
        ("get_bond_psbl_rvsecncl", ()),
        ("get_bond_daily_ccld", ()),
        ("get_bond_balance", ()),
        ("get_bond_psbl_order", (CODE, 10000)),
    ],
)
def test_paper_trading_is_refused_before_any_request(wire, name, args):
    api, sent = wire(paper=True)
    with pytest.raises(PaperTradingNotSupportedError):
        getattr(api, name)(*args)
    assert sent == []
