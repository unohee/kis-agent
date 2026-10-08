"""Overseas stock orders against the official KIS contract.

Every request is captured at the HTTP layer (after TR_ID paper conversion), and
the test asserts the HTTP method, that nothing goes out as a query string, the
final TR_ID header and the *complete* JSON body. Sources: KIS workbook sheets
v1_해외주식-001 (주문), -002 (예약주문접수), -003 (정정취소), -004 (예약주문접수취소)
and open-trading-api examples_llm/overseas_stock/order*.
"""

import warnings
from types import SimpleNamespace

import pytest

from kis_agent.core.client import KISClient
from kis_agent.core.config import KISConfig
from kis_agent.overseas.order_api import OverseasOrderAPI

ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}


class _Response:
    status_code = 200
    text = '{"rt_cd":"0","output":{}}'
    headers = {}

    def json(self):
        return {"rt_cd": "0", "output": {}}


@pytest.fixture
def wire(monkeypatch):
    """Return a factory building an OverseasOrderAPI whose HTTP calls are captured."""

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
            lambda: SimpleNamespace(my_token="token", my_app=config.APP_KEY, my_sec=config.APP_SECRET),
        )
        sent = []

        def transport(method, url, **kwargs):
            sent.append({"method": method, "url": url, **kwargs})
            return _Response()

        monkeypatch.setattr("kis_agent.core.client.httpx.request", transport)
        api = OverseasOrderAPI(client=client, account_info=dict(ACCOUNT), enable_cache=False, _from_agent=True)
        return api, sent

    return _build


def _one(sent, path):
    assert len(sent) == 1
    req = sent[0]
    assert req["method"] == "POST"
    assert req["params"] is None
    assert req["url"].endswith(path)
    return req["headers"]["tr_id"], req["json"]


EXCHANGES = {
    # alias: (order code, buy TR, sell TR, cancel TR, modify TR or None)
    "NAS": ("NASD", "TTTT1002U", "TTTT1006U", "TTTT1004U", "TTTT1004U"),
    "NYSE": ("NYSE", "TTTT1002U", "TTTT1006U", "TTTT1004U", "TTTT1004U"),
    "AMS": ("AMEX", "TTTT1002U", "TTTT1006U", "TTTT1004U", "TTTT1004U"),
    "HKS": ("SEHK", "TTTS1002U", "TTTS1001U", "TTTS1003U", "TTTS1003U"),
    "SHS": ("SHAA", "TTTS0202U", "TTTS1005U", "TTTS0302U", None),
    "SZS": ("SZAA", "TTTS0305U", "TTTS0304U", "TTTS0306U", None),
    "TSE": ("TKSE", "TTTS0308U", "TTTS0307U", "TTTS0309U", "TTTS0309U"),
    "HNX": ("HASE", "TTTS0311U", "TTTS0310U", "TTTS0312U", None),
    "HSX": ("VNSE", "TTTS0311U", "TTTS0310U", "TTTS0312U", None),
}


@pytest.mark.parametrize("alias", sorted(EXCHANGES))
def test_buy_selects_tr_per_exchange(wire, alias):
    code, buy_tr, *_ = EXCHANGES[alias]
    api, sent = wire()
    api.buy_order(alias, "abc", 3, 12.5, ord_dvsn="32")
    tr_id, body = _one(sent, "/uapi/overseas-stock/v1/trading/order")
    assert tr_id == buy_tr
    assert body == {
        **ACCOUNT,
        "OVRS_EXCG_CD": code,
        "PDNO": "ABC",
        "ORD_QTY": "3",
        "OVRS_ORD_UNPR": "12.5",
        "ORD_DVSN": "32",
        "ORD_SVR_DVSN_CD": "0",
    }


@pytest.mark.parametrize("alias", sorted(EXCHANGES))
def test_sell_selects_tr_per_exchange(wire, alias):
    code, _, sell_tr, *_ = EXCHANGES[alias]
    api, sent = wire()
    api.sell_order(alias, "abc", 3, 0, ord_dvsn="33")
    tr_id, body = _one(sent, "/uapi/overseas-stock/v1/trading/order")
    assert tr_id == sell_tr
    assert body == {
        **ACCOUNT,
        "OVRS_EXCG_CD": code,
        "PDNO": "ABC",
        "ORD_QTY": "3",
        "OVRS_ORD_UNPR": "0",
        "SLL_TYPE": "00",
        "ORD_DVSN": "33",
        "ORD_SVR_DVSN_CD": "0",
    }


@pytest.mark.parametrize("alias", sorted(EXCHANGES))
def test_cancel_selects_tr_per_exchange(wire, alias):
    code, _, _, cancel_tr, _ = EXCHANGES[alias]
    api, sent = wire()
    api.cancel_order(alias, "abc", "0001234", 7)
    tr_id, body = _one(sent, "/uapi/overseas-stock/v1/trading/order-rvsecncl")
    assert tr_id == cancel_tr
    assert body == {
        **ACCOUNT,
        "OVRS_EXCG_CD": code,
        "PDNO": "ABC",
        "ORGN_ODNO": "0001234",
        "RVSE_CNCL_DVSN_CD": "02",
        "ORD_QTY": "7",
        "OVRS_ORD_UNPR": "0",
        "ORD_SVR_DVSN_CD": "0",
    }


@pytest.mark.parametrize("alias", sorted(EXCHANGES))
def test_modify_selects_tr_or_refuses_cancel_only_markets(wire, alias):
    code, _, _, _, modify_tr = EXCHANGES[alias]
    api, sent = wire()
    if modify_tr is None:
        with pytest.raises(ValueError, match="정정"):
            api.modify_order(alias, "abc", "0001234", 7, 9.75)
        assert sent == []
        return
    api.modify_order(alias, "abc", "0001234", 7, 9.75)
    tr_id, body = _one(sent, "/uapi/overseas-stock/v1/trading/order-rvsecncl")
    assert tr_id == modify_tr
    assert body == {
        **ACCOUNT,
        "OVRS_EXCG_CD": code,
        "PDNO": "ABC",
        "ORGN_ODNO": "0001234",
        "RVSE_CNCL_DVSN_CD": "01",
        "ORD_QTY": "7",
        "OVRS_ORD_UNPR": "9.75",
        "ORD_SVR_DVSN_CD": "0",
    }


def test_amend_cancel_ord_dvsn_is_ignored_with_a_warning(wire):
    api, sent = wire()
    with pytest.warns(DeprecationWarning, match="ord_dvsn"):
        api.modify_order("NASD", "AAPL", "1", 1, 1.0, ord_dvsn="34")
    with pytest.warns(DeprecationWarning, match="ord_dvsn"):
        api.cancel_order("NASD", "AAPL", "1", 1, ord_dvsn="34")
    assert all("ORD_DVSN" not in r["json"] for r in sent)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        api.cancel_order("NASD", "AAPL", "1", 1)


@pytest.mark.parametrize("side,tr", [("02", "TTTT3014U"), ("01", "TTTT3016U")])
def test_us_reservation(wire, side, tr):
    api, sent = wire()
    api.reserve_order("NAS", "tsla", side, 1, 900, ord_dvsn="36")
    tr_id, body = _one(sent, "/uapi/overseas-stock/v1/trading/order-resv")
    assert tr_id == tr
    assert body == {
        **ACCOUNT,
        "PDNO": "TSLA",
        "OVRS_EXCG_CD": "NASD",
        "FT_ORD_QTY": "1",
        "FT_ORD_UNPR3": "900",
        "ORD_SVR_DVSN_CD": "0",
        "ORD_DVSN": "36",
    }


@pytest.mark.parametrize(
    "alias,code,prdt", [("HKS", "SEHK", "501"), ("TSE", "TKSE", "515"), ("SHS", "SHAA", "551"), ("HSX", "VNSE", "508")]
)
def test_asia_reservation(wire, alias, code, prdt):
    api, sent = wire()
    api.reserve_order(alias, "00700", "01", 100, 300)
    tr_id, body = _one(sent, "/uapi/overseas-stock/v1/trading/order-resv")
    assert tr_id == "TTTS3013U"
    assert body == {
        **ACCOUNT,
        "PDNO": "00700",
        "OVRS_EXCG_CD": code,
        "FT_ORD_QTY": "100",
        "FT_ORD_UNPR3": "300",
        "ORD_SVR_DVSN_CD": "0",
        "SLL_BUY_DVSN_CD": "01",
        "RVSE_CNCL_DVSN_CD": "00",
        "PRDT_TYPE_CD": prdt,
    }


def test_reservation_validation_and_ignored_end_date(wire):
    api, sent = wire()
    with pytest.raises(ValueError, match="sll_buy_dvsn_cd"):
        api.reserve_order("NASD", "AAPL", "buy", 1, 1)
    assert sent == []
    with pytest.warns(DeprecationWarning, match="rsvn_ord_end_dt"):
        api.reserve_order("NASD", "AAPL", "02", 1, 1, rsvn_ord_end_dt="20260131")
    assert "RSVN_ORD_END_DT" not in sent[0]["json"]


def test_modify_reservation_is_refused_without_sending(wire):
    api, sent = wire()
    with pytest.warns(DeprecationWarning), pytest.raises(NotImplementedError, match="cancel_reserve_order"):
        api.modify_reserve_order("001", 15, 175.0)
    assert sent == []


def test_cancel_us_reservation(wire):
    api, sent = wire()
    api.cancel_reserve_order("0030008244", "20260108")
    tr_id, body = _one(sent, "/uapi/overseas-stock/v1/trading/order-resv-ccnl")
    assert tr_id == "TTTT3017U"
    assert body == {**ACCOUNT, "RSVN_ORD_RCIT_DT": "20260108", "OVRS_RSVN_ODNO": "0030008244"}


def test_cancel_asia_reservation(wire):
    api, sent = wire()
    api.cancel_reserve_order("0000123", "20260108", "SEHK", "00700", 100, 300)
    tr_id, body = _one(sent, "/uapi/overseas-stock/v1/trading/order-resv")
    assert tr_id == "TTTS3013U"
    assert body == {
        **ACCOUNT,
        "PDNO": "00700",
        "OVRS_EXCG_CD": "SEHK",
        "FT_ORD_QTY": "100",
        "FT_ORD_UNPR3": "300",
        "RVSE_CNCL_DVSN_CD": "02",
        "PRDT_TYPE_CD": "501",
        "RSVN_ORD_RCIT_DT": "20260108",
        "OVRS_RSVN_ODNO": "0000123",
        "ORD_SVR_DVSN_CD": "0",
    }


def test_cancel_asia_reservation_requires_symbol_and_quantity(wire):
    api, sent = wire()
    with pytest.raises(ValueError, match="pdno"):
        api.cancel_reserve_order("0000123", "20260108", "TKSE")
    assert sent == []


@pytest.mark.parametrize(
    "call,expected",
    [
        (lambda a: a.buy_order("HKS", "00700", 1, 1), "VTTS1002U"),
        (lambda a: a.sell_order("TSE", "7203", 1, 1), "VTTS0307U"),
        (lambda a: a.cancel_order("TSE", "7203", "1", 1), "VTTS0309U"),
        (lambda a: a.reserve_order("NASD", "AAPL", "01", 1, 1), "VTTT3016U"),
        (lambda a: a.cancel_reserve_order("1", "20260108"), "VTTT3017U"),
    ],
)
def test_paper_mode_converts_every_selected_tr(wire, call, expected):
    api, sent = wire(paper=True)
    call(api)
    assert sent[0]["headers"]["tr_id"] == expected
