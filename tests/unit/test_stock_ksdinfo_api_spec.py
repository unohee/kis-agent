from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from kis_agent.stock import ksdinfo_api as mod
from kis_agent.stock.api_facade import StockAPI
from kis_agent.stock.ksdinfo_api import StockKsdInfoAPI

OK = {"rt_cd": "0", "msg1": "ok", "output": []}
ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}


def _api(cls):
    client = MagicMock()
    client.make_request.return_value = dict(OK)
    return cls(client, ACCOUNT, enable_cache=False, _from_agent=True), client


def _sent(client):
    kwargs = client.make_request.call_args.kwargs
    return kwargs["endpoint"], kwargs["tr_id"], kwargs["method"], kwargs["params"]


@pytest.fixture(autouse=True)
def _freeze(monkeypatch):
    monkeypatch.setattr(mod, "_today", lambda: date(2026, 10, 8))


# (method, url slug, tr_id, output key, method-specific params at defaults)
CASES = [
    ("get_ksd_bonus_issue", "bonus-issue", "HHKDB669101C0", "output1", {}),
    ("get_ksd_cap_dcrs", "cap-dcrs", "HHKDB669106C0", "output1", {}),
    (
        "get_ksd_dividend",
        "dividend",
        "HHKDB669102C0",
        "output1",
        {"GB1": "0", "HIGH_GB": ""},
    ),
    ("get_ksd_forfeit", "forfeit", "HHKDB669109C0", "output1", {}),
    ("get_ksd_list_info", "list-info", "HHKDB669107C0", "output1", {}),
    ("get_ksd_mand_deposit", "mand-deposit", "HHKDB669110C0", "output1", {}),
    ("get_ksd_merger_split", "merger-split", "HHKDB669104C0", "output1", {}),
    ("get_ksd_paidin_capin", "paidin-capin", "HHKDB669100C0", "output", {"GB1": "1"}),
    ("get_ksd_pub_offer", "pub-offer", "HHKDB669108C0", "output1", {}),
    ("get_ksd_purreq", "purreq", "HHKDB669103C0", "output1", {}),
    ("get_ksd_rev_split", "rev-split", "HHKDB669105C0", "output1", {"MARKET_GB": "0"}),
    ("get_ksd_sharehld_meet", "sharehld-meet", "HHKDB669111C0", "output1", {}),
]
BASE = {"CTS": "", "F_DT": "20261008", "T_DT": "20261107", "SHT_CD": ""}


def _expected(extra, **overrides):
    params = {**BASE, **extra}
    params.update(overrides)
    return params


@pytest.mark.parametrize("name,slug,tr_id,out_key,extra", CASES)
class TestKsdInfo:
    def test_defaults(self, name, slug, tr_id, out_key, extra):
        api, client = _api(StockKsdInfoAPI)
        assert getattr(api, name)()["rt_cd"] == "0"
        endpoint, tr, method, params = _sent(client)
        assert (endpoint, tr, method) == (
            "/uapi/domestic-stock/v1/ksdinfo/" + slug,
            tr_id,
            "GET",
        )
        assert params == _expected(extra)

    def test_explicit_window_and_code(self, name, slug, tr_id, out_key, extra):
        api, client = _api(StockKsdInfoAPI)
        getattr(api, name)("20230101", "20231231", "005930")
        assert _sent(client)[3] == _expected(
            extra, F_DT="20230101", T_DT="20231231", SHT_CD="005930"
        )

    def test_cts_pagination(self, name, slug, tr_id, out_key, extra):
        api, client = _api(StockKsdInfoAPI)
        client.make_request.side_effect = [
            {
                "rt_cd": "0",
                "msg1": "ok",
                out_key: [{"sht_cd": "A"}],
                "cts": "NEXT",
                "_tr_cont": "M",
            },
            {
                "rt_cd": "0",
                "msg1": "ok",
                out_key: [{"sht_cd": "B"}],
                "cts": "",
                "_tr_cont": "D",
            },
        ]
        res = getattr(api, name)()
        assert [r["sht_cd"] for r in res[out_key]] == ["A", "B"]
        assert res["_pagination"] == {"pages": 2, "truncated": False, "error": None}
        assert client.make_request.call_args_list[1].kwargs["params"]["CTS"] == "NEXT"


def test_dividend_kind_and_high_dividend_blank():
    api, client = _api(StockKsdInfoAPI)
    api.get_ksd_dividend(kind="1")
    assert _sent(client)[3]["GB1"] == "1"
    assert _sent(client)[3]["HIGH_GB"] == ""


def test_paidin_capin_kind():
    api, client = _api(StockKsdInfoAPI)
    api.get_ksd_paidin_capin(kind="2")
    assert _sent(client)[3]["GB1"] == "2"


def test_rev_split_market():
    api, client = _api(StockKsdInfoAPI)
    api.get_ksd_rev_split(market="2")
    assert _sent(client)[3]["MARKET_GB"] == "2"


def test_max_pages_caps_requests():
    api, client = _api(StockKsdInfoAPI)
    client.make_request.return_value = {
        "rt_cd": "0",
        "msg1": "ok",
        "output1": [],
        "cts": "X",
        "_tr_cont": "M",
    }
    res = api.get_ksd_dividend(max_pages=2)
    assert client.make_request.call_count == 2
    assert res["_pagination"]["truncated"] is True


def test_default_window_uses_real_clock_when_not_frozen(monkeypatch):
    monkeypatch.undo()
    assert mod._today() == date.today()


def test_reachable_through_facade():
    client = MagicMock()
    client.make_request.return_value = dict(OK)
    stock = StockAPI(client, ACCOUNT, _from_agent=True)
    stock.get_ksd_dividend("20260101", "20261231")
    assert client.make_request.call_args.kwargs["tr_id"] == "HHKDB669102C0"
