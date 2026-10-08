"""Overseas stock APIs added in Phase 3 (A5) against the official KIS contract.

Read APIs run against a MagicMock client and assert endpoint, TR_ID, HTTP method
and the complete params dict. The four daytime order paths are captured at the
HTTP layer (see test_overseas_order_spec.py): method, empty query string, final
TR_ID header, complete JSON body and paper-mode behaviour.
Sources: KIS workbook (2025-12-12) and open-trading-api examples_llm/overseas_stock.
"""

import contextlib
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import pytz

from kis_agent.core.client import KISClient
from kis_agent.core.config import KISConfig
from kis_agent.core.tr_mapping import PaperTradingNotSupportedError
from kis_agent.overseas.account_api import OverseasAccountAPI
from kis_agent.overseas.api_facade import OverseasStockAPI
from kis_agent.overseas.order_api import OverseasOrderAPI
from kis_agent.overseas.price_api import OverseasPriceAPI

ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
PRICE = "/uapi/overseas-price/v1/quotations/"
TRADING = "/uapi/overseas-stock/v1/trading/"

# 2026-10-08 14:00 KST
NOW = datetime(2026, 10, 8, 5, 0, tzinfo=pytz.utc)
TODAY, PLUS_30, MINUS_30 = "20261008", "20261107", "20260908"


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr("kis_agent.overseas._compat._utc_now", lambda: NOW)


def _api(cls, *responses):
    client = MagicMock()
    if responses:
        client.make_request.side_effect = list(responses)
    else:
        client.make_request.return_value = {"rt_cd": "0"}
    return cls(client, dict(ACCOUNT), enable_cache=False, _from_agent=True), client


# ---------------------------------------------------------------------------
# single-request GET APIs
# ---------------------------------------------------------------------------
def _search_params(**overrides):
    keys = ["PRICECUR", "RATE", "VALX", "SHAR", "VOLUME", "AMT", "EPS", "PER"]
    params = {"AUTH": "", "EXCD": "NAS"}
    for key in keys:
        params.update({f"CO_YN_{key}": "", f"CO_ST_{key}": "", f"CO_EN_{key}": ""})
    params["KEYB"] = ""
    params.update(overrides)
    return params


GET_CASES = [
    pytest.param(
        OverseasPriceAPI,
        "get_inquire_search",
        ("nas",),
        {},
        PRICE + "inquire-search",
        "HHDFS76410000",
        _search_params(),
        id="search-default",
    ),
    pytest.param(
        OverseasPriceAPI,
        "get_inquire_search",
        ("TSE",),
        {
            "price": (10, 50.5),
            "rate": (3, 20),
            "market_cap": (1, 2),
            "shares": (3, 4),
            "volume": (1000, 9000),
            "amount": (5, 6),
            "eps": (0.5, 9),
            "per": (1, 30),
            "keyb": "k",
        },
        PRICE + "inquire-search",
        "HHDFS76410000",
        _search_params(
            EXCD="TSE",
            CO_YN_PRICECUR="1",
            CO_ST_PRICECUR="10",
            CO_EN_PRICECUR="50.5",
            CO_YN_RATE="1",
            CO_ST_RATE="3",
            CO_EN_RATE="20",
            CO_YN_VALX="1",
            CO_ST_VALX="1",
            CO_EN_VALX="2",
            CO_YN_SHAR="1",
            CO_ST_SHAR="3",
            CO_EN_SHAR="4",
            CO_YN_VOLUME="1",
            CO_ST_VOLUME="1000",
            CO_EN_VOLUME="9000",
            CO_YN_AMT="1",
            CO_ST_AMT="5",
            CO_EN_AMT="6",
            CO_YN_EPS="1",
            CO_ST_EPS="0.5",
            CO_EN_EPS="9",
            CO_YN_PER="1",
            CO_ST_PER="1",
            CO_EN_PER="30",
            KEYB="k",
        ),
        id="search-all-conditions",
    ),
    pytest.param(
        OverseasPriceAPI,
        "get_inquire_time_indexchartprice",
        ("SPX",),
        {},
        PRICE + "inquire-time-indexchartprice",
        "FHKST03030200",
        {
            "FID_COND_MRKT_DIV_CODE": "N",
            "FID_INPUT_ISCD": "SPX",
            "FID_HOUR_CLS_CODE": "0",
            "FID_PW_DATA_INCU_YN": "Y",
        },
        id="index-minute-default",
    ),
    pytest.param(
        OverseasPriceAPI,
        "get_inquire_time_indexchartprice",
        ("USDKRW",),
        {"market": "X", "hour_cls_code": "1", "past_data": "N"},
        PRICE + "inquire-time-indexchartprice",
        "FHKST03030200",
        {
            "FID_COND_MRKT_DIV_CODE": "X",
            "FID_INPUT_ISCD": "USDKRW",
            "FID_HOUR_CLS_CODE": "1",
            "FID_PW_DATA_INCU_YN": "N",
        },
        id="index-minute-args",
    ),
    pytest.param(
        OverseasPriceAPI,
        "get_industry_price",
        ("nas",),
        {},
        PRICE + "industry-price",
        "HHDFS76370100",
        {"AUTH": "", "EXCD": "NAS"},
        id="industry-price",
    ),
    pytest.param(
        OverseasPriceAPI,
        "get_inquire_daily_chartprice",
        (".DJI",),
        {},
        PRICE + "inquire-daily-chartprice",
        "FHKST03030100",
        {
            "FID_COND_MRKT_DIV_CODE": "N",
            "FID_INPUT_ISCD": ".DJI",
            "FID_INPUT_DATE_1": MINUS_30,
            "FID_INPUT_DATE_2": TODAY,
            "FID_PERIOD_DIV_CODE": "D",
        },
        id="daily-chart-default",
    ),
    pytest.param(
        OverseasPriceAPI,
        "get_inquire_daily_chartprice",
        (".DJI", "20240101", "20240331"),
        {"market": "I", "period": "W"},
        PRICE + "inquire-daily-chartprice",
        "FHKST03030100",
        {
            "FID_COND_MRKT_DIV_CODE": "I",
            "FID_INPUT_ISCD": ".DJI",
            "FID_INPUT_DATE_1": "20240101",
            "FID_INPUT_DATE_2": "20240331",
            "FID_PERIOD_DIV_CODE": "W",
        },
        id="daily-chart-args",
    ),
    pytest.param(
        OverseasPriceAPI,
        "get_inquire_daily_chartprice",
        (".DJI",),
        {"end_date": "20240331"},
        PRICE + "inquire-daily-chartprice",
        "FHKST03030100",
        {
            "FID_COND_MRKT_DIV_CODE": "N",
            "FID_INPUT_ISCD": ".DJI",
            "FID_INPUT_DATE_1": "20240301",
            "FID_INPUT_DATE_2": "20240331",
            "FID_PERIOD_DIV_CODE": "D",
        },
        id="daily-chart-start-follows-end",
    ),
    pytest.param(
        OverseasPriceAPI,
        "get_brknews_title",
        (),
        {},
        PRICE + "brknews-title",
        "FHKST01011801",
        {
            "FID_NEWS_OFER_ENTP_CODE": "0",
            "FID_COND_MRKT_CLS_CODE": "",
            "FID_INPUT_ISCD": "",
            "FID_TITL_CNTT": "",
            "FID_INPUT_DATE_1": "",
            "FID_INPUT_HOUR_1": "",
            "FID_RANK_SORT_CLS_CODE": "",
            "FID_INPUT_SRNO": "",
            "FID_COND_SCR_DIV_CODE": "11801",
        },
        id="brknews-default",
    ),
    pytest.param(
        OverseasPriceAPI,
        "get_brknews_title",
        ("1",),
        {},
        PRICE + "brknews-title",
        "FHKST01011801",
        {
            "FID_NEWS_OFER_ENTP_CODE": "1",
            "FID_COND_MRKT_CLS_CODE": "",
            "FID_INPUT_ISCD": "",
            "FID_TITL_CNTT": "",
            "FID_INPUT_DATE_1": "",
            "FID_INPUT_HOUR_1": "",
            "FID_RANK_SORT_CLS_CODE": "",
            "FID_INPUT_SRNO": "",
            "FID_COND_SCR_DIV_CODE": "11801",
        },
        id="brknews-provider",
    ),
    pytest.param(
        OverseasPriceAPI,
        "get_rights_by_ice",
        ("us", "nvdl"),
        {},
        PRICE + "rights-by-ice",
        "HHDFS78330900",
        {"NCOD": "US", "SYMB": "NVDL", "ST_YMD": "", "ED_YMD": ""},
        id="rights-by-ice-default",
    ),
    pytest.param(
        OverseasPriceAPI,
        "get_rights_by_ice",
        ("HK", "00700"),
        {"st_ymd": "20240101", "ed_ymd": "20240514"},
        PRICE + "rights-by-ice",
        "HHDFS78330900",
        {"NCOD": "HK", "SYMB": "00700", "ST_YMD": "20240101", "ED_YMD": "20240514"},
        id="rights-by-ice-range",
    ),
    pytest.param(
        OverseasAccountAPI,
        "get_inquire_paymt_stdr_balance",
        (),
        {},
        TRADING + "inquire-paymt-stdr-balance",
        "CTRP6010R",
        {
            **ACCOUNT,
            "BASS_DT": TODAY,
            "WCRC_FRCR_DVSN_CD": "02",
            "INQR_DVSN_CD": "00",
        },
        id="paymt-balance-default",
    ),
    pytest.param(
        OverseasAccountAPI,
        "get_inquire_paymt_stdr_balance",
        ("20230630", "01", "02"),
        {},
        TRADING + "inquire-paymt-stdr-balance",
        "CTRP6010R",
        {
            **ACCOUNT,
            "BASS_DT": "20230630",
            "WCRC_FRCR_DVSN_CD": "01",
            "INQR_DVSN_CD": "02",
        },
        id="paymt-balance-args",
    ),
]


@pytest.mark.parametrize("cls,name,args,kwargs,endpoint,tr_id,params", GET_CASES)
def test_get_request_matches_spec(cls, name, args, kwargs, endpoint, tr_id, params):
    api, client = _api(cls)
    assert getattr(api, name)(*args, **kwargs) == {"rt_cd": "0"}
    client.make_request.assert_called_once_with(
        endpoint=endpoint, tr_id=tr_id, params=params, method="GET"
    )


@pytest.mark.parametrize("name", ["get_inquire_search", "get_industry_price"])
def test_exchange_is_validated_before_sending(name):
    api, client = _api(OverseasPriceAPI)
    with pytest.raises(ValueError, match="거래소"):
        getattr(api, name)("XXX")
    client.make_request.assert_not_called()


# ---------------------------------------------------------------------------
# paginated GET APIs
# ---------------------------------------------------------------------------
def _page(cursor, tr_cont, **body):
    return {"rt_cd": "0", "msg1": "ok", "_tr_cont": tr_cont, **cursor, **body}


def _two_pages(
    cls, name, args, kwargs, cursor_fields, list_key, endpoint, tr_id, first, second
):
    cur1 = dict(zip(cursor_fields, ("f1", "n1")))
    cur2 = dict(zip(cursor_fields, ("f2", "n2")))
    pages = iter(
        [
            _page(cur1, "M", **{list_key: [{"row": 1}]}),
            _page(cur2, "D", **{list_key: [{"row": 2}]}),
        ]
    )
    calls = []

    def fake(**kw):
        # _paginate reuses one params dict between pages, so snapshot every call.
        calls.append({**kw, "params": dict(kw["params"])})
        return next(pages)

    client = MagicMock()
    client.make_request.side_effect = fake
    api = cls(client, dict(ACCOUNT), enable_cache=False, _from_agent=True)
    out = getattr(api, name)(*args, **kwargs)
    assert out[list_key] == [{"row": 1}, {"row": 2}]
    assert out["_pagination"] == {"pages": 2, "truncated": False, "error": None}
    assert calls == [
        {"endpoint": endpoint, "tr_id": tr_id, "params": first, "method": "GET"},
        {
            "endpoint": endpoint,
            "tr_id": tr_id,
            "params": second,
            "method": "GET",
            "headers": {"tr_cont": "N"},
        },
    ]


def test_period_rights_default_and_cursor():
    base = {
        "RGHT_TYPE_CD": "%%",
        "INQR_DVSN_CD": "02",
        "INQR_STRT_DT": TODAY,
        "INQR_END_DT": PLUS_30,
        "PDNO": "",
        "PRDT_TYPE_CD": "",
    }
    _two_pages(
        OverseasPriceAPI,
        "get_period_rights",
        (),
        {},
        ("ctx_area_fk50", "ctx_area_nk50"),
        "output",
        PRICE + "period-rights",
        "CTRGT011R",
        {**base, "CTX_AREA_NK50": "", "CTX_AREA_FK50": ""},
        {**base, "CTX_AREA_NK50": "n1", "CTX_AREA_FK50": "f1"},
    )


def test_period_rights_arguments():
    api, client = _api(OverseasPriceAPI)
    api.get_period_rights(
        "03", "04", "20240417", "20240517", "AAPL", "512", max_pages=1
    )
    assert client.make_request.call_args.kwargs["params"] == {
        "RGHT_TYPE_CD": "03",
        "INQR_DVSN_CD": "04",
        "INQR_STRT_DT": "20240417",
        "INQR_END_DT": "20240517",
        "PDNO": "AAPL",
        "PRDT_TYPE_CD": "512",
        "CTX_AREA_NK50": "",
        "CTX_AREA_FK50": "",
    }


def test_colable_by_company_default_and_cursor():
    base = {
        "PDNO": "AMD",
        "PRDT_TYPE_CD": "",
        "INQR_STRT_DT": "",
        "INQR_END_DT": "",
        "INQR_DVSN": "",
        "NATN_CD": "840",
        "INQR_SQN_DVSN": "01",
        "RT_DVSN_CD": "",
        "RT": "",
        "LOAN_PSBL_YN": "",
    }
    _two_pages(
        OverseasPriceAPI,
        "get_colable_by_company",
        ("AMD",),
        {},
        ("ctx_area_fk100", "ctx_area_nk100"),
        "output1",
        PRICE + "colable-by-company",
        "CTLN4050R",
        {**base, "CTX_AREA_FK100": "", "CTX_AREA_NK100": ""},
        {**base, "CTX_AREA_FK100": "f1", "CTX_AREA_NK100": "n1"},
    )


def test_colable_by_company_arguments():
    api, client = _api(OverseasPriceAPI)
    api.get_colable_by_company("0700", "344", "02", max_pages=1)
    params = client.make_request.call_args.kwargs["params"]
    assert (params["PDNO"], params["NATN_CD"], params["INQR_SQN_DVSN"]) == (
        "0700",
        "344",
        "02",
    )


def test_algo_ordno_default_and_cursor():
    base = {
        "CANO": "12345678",
        "ACNO_PRDT_CD": "01",
        "TRAD_DT": TODAY,
    }
    _two_pages(
        OverseasAccountAPI,
        "get_algo_ordno",
        (),
        {},
        ("ctx_area_fk200", "ctx_area_nk200"),
        "output",
        TRADING + "algo-ordno",
        "TTTS6058R",
        {**base, "CTX_AREA_NK200": "", "CTX_AREA_FK200": ""},
        {**base, "CTX_AREA_NK200": "n1", "CTX_AREA_FK200": "f1"},
    )


def test_algo_ordno_explicit_date():
    api, client = _api(OverseasAccountAPI)
    api.get_algo_ordno("20250619", max_pages=1)
    assert client.make_request.call_args.kwargs["params"] == {
        "CANO": "12345678",
        "ACNO_PRDT_CD": "01",
        "TRAD_DT": "20250619",
        "CTX_AREA_NK200": "",
        "CTX_AREA_FK200": "",
    }


def test_inquire_algo_ccnl_default_and_cursor():
    base = {
        **ACCOUNT,
        "ORD_DT": TODAY,
        "ORD_GNO_BRNO": "",
        "ODNO": "0030012345",
        "TTLZ_ICLD_YN": "",
    }
    _two_pages(
        OverseasAccountAPI,
        "get_inquire_algo_ccnl",
        ("0030012345",),
        {},
        ("ctx_area_fk200", "ctx_area_nk200"),
        "output",
        TRADING + "inquire-algo-ccnl",
        "TTTS6059R",
        {**base, "CTX_AREA_NK200": "", "CTX_AREA_FK200": ""},
        {**base, "CTX_AREA_NK200": "n1", "CTX_AREA_FK200": "f1"},
    )


def test_inquire_algo_ccnl_arguments_and_validation():
    api, client = _api(OverseasAccountAPI)
    api.get_inquire_algo_ccnl("0030012345", "20250619", "06010", "Y", max_pages=1)
    assert client.make_request.call_args.kwargs["params"] == {
        **ACCOUNT,
        "ORD_DT": "20250619",
        "ORD_GNO_BRNO": "06010",
        "ODNO": "0030012345",
        "TTLZ_ICLD_YN": "Y",
        "CTX_AREA_NK200": "",
        "CTX_AREA_FK200": "",
    }
    client.make_request.reset_mock()
    with pytest.raises(ValueError, match="odno"):
        api.get_inquire_algo_ccnl("")
    client.make_request.assert_not_called()


def test_inquire_period_trans_default_and_cursor():
    base = {
        **ACCOUNT,
        "ERLM_STRT_DT": MINUS_30,
        "ERLM_END_DT": TODAY,
        "OVRS_EXCG_CD": "",
        "PDNO": "",
        "SLL_BUY_DVSN_CD": "00",
        "LOAN_DVSN_CD": "",
    }
    _two_pages(
        OverseasAccountAPI,
        "get_inquire_period_trans",
        (),
        {},
        ("ctx_area_fk100", "ctx_area_nk100"),
        "output1",
        TRADING + "inquire-period-trans",
        "CTOS4001R",
        {**base, "CTX_AREA_FK100": "", "CTX_AREA_NK100": ""},
        {**base, "CTX_AREA_FK100": "f1", "CTX_AREA_NK100": "n1"},
    )


def test_inquire_period_trans_arguments():
    api, client = _api(OverseasAccountAPI)
    api.get_inquire_period_trans(
        "20240420", "20240520", "NASD", "aapl", "02", "01", max_pages=1
    )
    assert client.make_request.call_args.kwargs["params"] == {
        **ACCOUNT,
        "ERLM_STRT_DT": "20240420",
        "ERLM_END_DT": "20240520",
        "OVRS_EXCG_CD": "NASD",
        "PDNO": "AAPL",
        "SLL_BUY_DVSN_CD": "02",
        "LOAN_DVSN_CD": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }


def test_inquire_period_trans_start_follows_given_end():
    api, client = _api(OverseasAccountAPI)
    api.get_inquire_period_trans(erlm_end_dt="20240520", max_pages=1)
    params = client.make_request.call_args.kwargs["params"]
    assert (params["ERLM_STRT_DT"], params["ERLM_END_DT"]) == ("20240420", "20240520")


@pytest.mark.parametrize(
    "name,args",
    [
        ("get_algo_ordno", ()),
        ("get_inquire_algo_ccnl", ("1",)),
        ("get_inquire_paymt_stdr_balance", ()),
        ("get_inquire_period_trans", ()),
    ],
)
def test_account_queries_need_an_account(name, args):
    client = MagicMock()
    api = OverseasAccountAPI(client, None, enable_cache=False, _from_agent=True)
    with pytest.raises(ValueError, match="계좌"):
        getattr(api, name)(*args)
    client.make_request.assert_not_called()


# ---------------------------------------------------------------------------
# facade reachability and name uniqueness
# ---------------------------------------------------------------------------
def test_facade_reaches_new_methods():
    client = MagicMock()
    client.make_request.return_value = {"rt_cd": "0"}
    api = OverseasStockAPI(client, dict(ACCOUNT), enable_cache=False, _from_agent=True)
    api.get_industry_price("NAS")
    assert client.make_request.call_args.kwargs["tr_id"] == "HHDFS76370100"
    api.get_inquire_paymt_stdr_balance("20230630")
    assert client.make_request.call_args.kwargs["tr_id"] == "CTRP6010R"
    api.daytime_buy_order("NASD", "AAPL", 1, 1.5)
    assert client.make_request.call_args.kwargs["tr_id"] == "TTTS6036U"


def test_new_method_names_are_unique_across_overseas_sub_apis():
    from kis_agent.overseas.ranking_api import OverseasRankingAPI

    seen = {}
    for cls in (
        OverseasPriceAPI,
        OverseasAccountAPI,
        OverseasOrderAPI,
        OverseasRankingAPI,
    ):
        for name in vars(cls):
            if name.startswith("_"):
                continue
            seen.setdefault(name, []).append(cls.__name__)
    assert {n: c for n, c in seen.items() if len(c) > 1} == {}


# ---------------------------------------------------------------------------
# daytime orders (real money): HTTP-layer capture
# ---------------------------------------------------------------------------
class _Response:
    status_code = 200
    text = '{"rt_cd":"0","output":{}}'
    headers = {}

    def json(self):
        return {"rt_cd": "0", "output": {}}


@pytest.fixture
def wire(monkeypatch):
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
        api = OverseasOrderAPI(
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
    assert req["url"].endswith(path)
    return req["headers"]["tr_id"], req["json"]


ORDER = "/uapi/overseas-stock/v1/trading/daytime-order"
RVSECNCL = "/uapi/overseas-stock/v1/trading/daytime-order-rvsecncl"


@pytest.mark.parametrize(
    "method,tr_id",
    [("daytime_buy_order", "TTTS6036U"), ("daytime_sell_order", "TTTS6037U")],
)
@pytest.mark.parametrize(
    "alias,code", [("NAS", "NASD"), ("nyse", "NYSE"), ("AMS", "AMEX"), ("AMEX", "AMEX")]
)
def test_daytime_order_body(wire, method, tr_id, alias, code):
    api, sent = wire()
    getattr(api, method)(alias, "aapl", 10, 185.5)
    sent_tr, body = _one(sent, ORDER)
    assert sent_tr == tr_id
    assert body == {
        **ACCOUNT,
        "OVRS_EXCG_CD": code,
        "PDNO": "AAPL",
        "ORD_QTY": "10",
        "OVRS_ORD_UNPR": "185.5",
        "CTAC_TLNO": "",
        "MGCO_APTM_ODNO": "",
        "ORD_SVR_DVSN_CD": "0",
        "ORD_DVSN": "00",
    }


def test_daytime_order_optional_fields(wire):
    api, sent = wire()
    api.daytime_buy_order("NASD", "AAPL", 1, 2, "01012345678", "000000000001")
    _, body = _one(sent, ORDER)
    assert body["CTAC_TLNO"] == "01012345678"
    assert body["MGCO_APTM_ODNO"] == "000000000001"
    assert body["OVRS_ORD_UNPR"] == "2"


def test_daytime_modify_body(wire):
    api, sent = wire()
    api.daytime_modify_order("nas", "aapl", "0001234", 5, 190.25, "010", "m1")
    tr_id, body = _one(sent, RVSECNCL)
    assert tr_id == "TTTS6038U"
    assert body == {
        **ACCOUNT,
        "OVRS_EXCG_CD": "NASD",
        "PDNO": "AAPL",
        "ORGN_ODNO": "0001234",
        "RVSE_CNCL_DVSN_CD": "01",
        "ORD_QTY": "5",
        "OVRS_ORD_UNPR": "190.25",
        "CTAC_TLNO": "010",
        "MGCO_APTM_ODNO": "m1",
        "ORD_SVR_DVSN_CD": "0",
    }


def test_daytime_cancel_body(wire):
    api, sent = wire()
    api.daytime_cancel_order("NYSE", "ko", "0001234", 5)
    tr_id, body = _one(sent, RVSECNCL)
    assert tr_id == "TTTS6038U"
    assert body == {
        **ACCOUNT,
        "OVRS_EXCG_CD": "NYSE",
        "PDNO": "KO",
        "ORGN_ODNO": "0001234",
        "RVSE_CNCL_DVSN_CD": "02",
        "ORD_QTY": "5",
        "OVRS_ORD_UNPR": "0",
        "CTAC_TLNO": "",
        "MGCO_APTM_ODNO": "",
        "ORD_SVR_DVSN_CD": "0",
    }


ORDER_CALLS = [
    ("daytime_buy_order", ("NASD", "AAPL", 1, 1.0)),
    ("daytime_sell_order", ("NASD", "AAPL", 1, 1.0)),
    ("daytime_modify_order", ("NASD", "AAPL", "0001", 1, 1.0)),
    ("daytime_cancel_order", ("NASD", "AAPL", "0001", 1)),
]


@pytest.mark.parametrize(
    "method,args,index,bad,match",
    [
        # exchange: US only, and known
        ("daytime_buy_order", ORDER_CALLS[0][1], 0, "SEHK", "미국"),
        ("daytime_sell_order", ORDER_CALLS[1][1], 0, "TKSE", "미국"),
        ("daytime_modify_order", ORDER_CALLS[2][1], 0, "SHAA", "미국"),
        ("daytime_cancel_order", ORDER_CALLS[3][1], 0, "VNSE", "미국"),
        ("daytime_buy_order", ORDER_CALLS[0][1], 0, "ZZZ", "거래소"),
        # quantity: positive int only
        ("daytime_buy_order", ORDER_CALLS[0][1], 2, 0, "qty"),
        ("daytime_sell_order", ORDER_CALLS[1][1], 2, -3, "qty"),
        ("daytime_buy_order", ORDER_CALLS[0][1], 2, 1.5, "qty"),
        ("daytime_buy_order", ORDER_CALLS[0][1], 2, "10", "qty"),
        ("daytime_buy_order", ORDER_CALLS[0][1], 2, True, "qty"),
        ("daytime_modify_order", ORDER_CALLS[2][1], 3, 0, "qty"),
        ("daytime_cancel_order", ORDER_CALLS[3][1], 3, 0, "qty"),
        # price: limit only, so strictly positive number
        ("daytime_buy_order", ORDER_CALLS[0][1], 3, 0, "지정가"),
        ("daytime_sell_order", ORDER_CALLS[1][1], 3, -1.0, "지정가"),
        ("daytime_modify_order", ORDER_CALLS[2][1], 4, 0, "지정가"),
        ("daytime_buy_order", ORDER_CALLS[0][1], 3, "1.0", "price"),
        ("daytime_buy_order", ORDER_CALLS[0][1], 3, True, "price"),
        # original order number
        ("daytime_modify_order", ORDER_CALLS[2][1], 2, "", "orgn_odno"),
        ("daytime_cancel_order", ORDER_CALLS[3][1], 2, "", "orgn_odno"),
    ],
)
def test_daytime_validation_sends_nothing(wire, method, args, index, bad, match):
    api, sent = wire()
    call = list(args)
    call[index] = bad
    with pytest.raises(ValueError, match=match):
        getattr(api, method)(*call)
    assert not sent


@pytest.mark.parametrize("method,args", ORDER_CALLS)
def test_daytime_orders_are_not_supported_on_paper(wire, method, args):
    api, sent = wire(paper=True)
    with pytest.raises(PaperTradingNotSupportedError):
        getattr(api, method)(*args)
    assert not sent


@pytest.mark.parametrize("method,args", ORDER_CALLS)
def test_daytime_orders_need_an_account(method, args):
    client = MagicMock()
    api = OverseasOrderAPI(client, None, enable_cache=False, _from_agent=True)
    with pytest.raises(ValueError, match="계좌"):
        getattr(api, method)(*args)
    client.make_request.assert_not_called()


def test_daytime_order_failure_is_not_retried(wire, monkeypatch):
    api, sent = wire()

    class _Error(_Response):
        status_code = 500
        text = "boom"

        def json(self):
            return {"rt_cd": "1", "msg1": "boom"}

    def transport(method, url, **kwargs):
        sent.append({"method": method, "url": url, **kwargs})
        return _Error()

    monkeypatch.setattr("kis_agent.core.client.httpx.request", transport)
    with contextlib.suppress(Exception):  # only the number of attempts matters here
        api.daytime_buy_order("NASD", "AAPL", 1, 1.0)
    assert len(sent) == 1


def test_kst_date_uses_the_real_clock_by_default(monkeypatch):
    from kis_agent.overseas import _compat

    monkeypatch.undo()
    today = _compat.kst_date()
    assert len(today) == 8 and today.isdigit()
    assert _compat.kst_date(1) > today
