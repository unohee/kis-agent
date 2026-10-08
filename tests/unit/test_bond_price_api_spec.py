"""Bond quotation APIs against the official KIS contract.

Sources: KIS workbook sheets for domestic-bond/v1/quotations/* and
open-trading-api examples_llm/domestic_bond/*. Bonds are not served on the
paper-trading host.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from kis_agent.bond import BondAPI, BondPriceAPI
from kis_agent.core.tr_mapping import PaperTradingNotSupportedError

ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
BASE = "/uapi/domestic-bond/v1/quotations/"


def _api():
    client = MagicMock()
    client.make_request.return_value = {"rt_cd": "0", "output": {}}
    return (
        BondPriceAPI(client, dict(ACCOUNT), enable_cache=False, _from_agent=True),
        client,
    )


def _sent(client, idx=-1):
    return client.make_request.call_args_list[idx].kwargs


QUOTES = [
    ("get_bond_asking_price", "inquire-asking-price", "FHKBJ773401C0"),
    ("get_bond_price", "inquire-price", "FHKBJ773400C0"),
    ("get_bond_ccnl", "inquire-ccnl", "FHKBJ773403C0"),
    ("get_bond_daily_price", "inquire-daily-price", "FHKBJ773404C0"),
    ("get_bond_daily_chart", "inquire-daily-itemchartprice", "FHKBJ773701C0"),
]


@pytest.mark.parametrize("name,path,tr_id", QUOTES)
def test_quote_requests(name, path, tr_id):
    api, client = _api()
    getattr(api, name)("KR2033022D33")
    assert _sent(client) == {
        "endpoint": BASE + path,
        "tr_id": tr_id,
        "params": {"FID_COND_MRKT_DIV_CODE": "B", "FID_INPUT_ISCD": "KR2033022D33"},
        "method": "GET",
    }
    getattr(api, name)("KR2033022D33", market="X")
    assert _sent(client)["params"]["FID_COND_MRKT_DIV_CODE"] == "X"


@pytest.mark.parametrize(
    "name,path,tr_id",
    [
        ("get_bond_issue_info", "issue-info", "CTPF1101R"),
        ("get_bond_info", "search-bond-info", "CTPF1114R"),
    ],
)
def test_reference_requests(name, path, tr_id):
    api, client = _api()
    getattr(api, name)("KR6449111CB8")
    assert _sent(client) == {
        "endpoint": BASE + path,
        "tr_id": tr_id,
        "params": {"PDNO": "KR6449111CB8", "PRDT_TYPE_CD": "302"},
        "method": "GET",
    }
    getattr(api, name)("KR6449111CB8", prdt_type_cd="300")
    assert _sent(client)["params"]["PRDT_TYPE_CD"] == "300"


def test_avg_unit_defaults_to_today():
    api, client = _api()
    api.get_bond_avg_unit()
    today = datetime.now().strftime("%Y%m%d")
    assert _sent(client) == {
        "endpoint": BASE + "avg-unit",
        "tr_id": "CTPF2005R",
        "params": {
            "INQR_STRT_DT": today,
            "INQR_END_DT": today,
            "PDNO": "",
            "PRDT_TYPE_CD": "302",
            "VRFC_KIND_CD": "00",
            "CTX_AREA_NK30": "",
            "CTX_AREA_FK100": "",
        },
        "method": "GET",
    }


def test_avg_unit_explicit_arguments_and_pagination():
    api, client = _api()
    pages = [
        {
            "rt_cd": "0",
            "_tr_cont": "M",
            "ctx_area_nk30": "N1",
            "ctx_area_fk100": "F1",
            "output1": [{"a": 1}],
            "output2": [{"b": 1}],
            "output3": [{"c": 1}],
        },
        {
            "rt_cd": "0",
            "_tr_cont": "D",
            "ctx_area_nk30": "",
            "ctx_area_fk100": "",
            "output1": [{"a": 2}],
            "output2": [{"b": 2}],
            "output3": [{"c": 2}],
        },
    ]
    seen = []

    def fake(**kwargs):
        seen.append(
            {**kwargs, "params": dict(kwargs["params"])}
        )  # _paginate reuses its params dict
        return pages[len(seen) - 1]

    client.make_request.side_effect = fake
    res = api.get_bond_avg_unit(
        "20260101", "20260131", "KR2033022D33", "302", "00", max_pages=3
    )
    assert [r["a"] for r in res["output1"]] == [1, 2]
    assert [r["b"] for r in res["output2"]] == [1, 2]
    assert [r["c"] for r in res["output3"]] == [1, 2]
    first, second = seen
    assert first["params"] == {
        "INQR_STRT_DT": "20260101",
        "INQR_END_DT": "20260131",
        "PDNO": "KR2033022D33",
        "PRDT_TYPE_CD": "302",
        "VRFC_KIND_CD": "00",
        "CTX_AREA_NK30": "",
        "CTX_AREA_FK100": "",
    }
    assert second["params"]["CTX_AREA_NK30"] == "N1"
    assert second["params"]["CTX_AREA_FK100"] == "F1"
    assert second["headers"] == {"tr_cont": "N"}
    assert second["tr_id"] == "CTPF2005R"


def test_facade_reachability():
    client = MagicMock()
    client.make_request.return_value = {"rt_cd": "0"}
    bond = BondAPI(client, dict(ACCOUNT), enable_cache=False, _from_agent=True)
    bond.get_bond_price("KR2033022D33")
    bond.get_bond_info("KR6449111CB8")
    assert [c.kwargs["tr_id"] for c in client.make_request.call_args_list] == [
        "FHKBJ773400C0",
        "CTPF1114R",
    ]


PAPER_CALLS = [
    ("get_bond_asking_price", ("KR2033022D33",)),
    ("get_bond_price", ("KR2033022D33",)),
    ("get_bond_ccnl", ("KR2033022D33",)),
    ("get_bond_daily_price", ("KR2033022D33",)),
    ("get_bond_daily_chart", ("KR2033022D33",)),
    ("get_bond_avg_unit", ()),
    ("get_bond_issue_info", ("KR6449111CB8",)),
    ("get_bond_info", ("KR6449111CB8",)),
]


@pytest.fixture
def paper_api(monkeypatch):
    from types import SimpleNamespace

    from kis_agent.core.client import KISClient
    from kis_agent.core.config import KISConfig

    monkeypatch.setenv("KIS_APP_KEY", "app-key")
    monkeypatch.setenv("KIS_APP_SECRET", "app-secret")
    monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")
    monkeypatch.delenv("KIS_BASE_URL", raising=False)
    monkeypatch.setenv("KIS_PAPER", "1")
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
    monkeypatch.setattr(
        "kis_agent.core.client.httpx.request", lambda *a, **k: sent.append((a, k))
    )
    return (
        BondPriceAPI(
            client=client,
            account_info=dict(ACCOUNT),
            enable_cache=False,
            _from_agent=True,
        ),
        sent,
    )


@pytest.mark.parametrize("name,args", PAPER_CALLS)
def test_paper_trading_is_refused_before_any_request(paper_api, name, args):
    api, sent = paper_api
    with pytest.raises(PaperTradingNotSupportedError):
        getattr(api, name)(*args)
    assert sent == []
