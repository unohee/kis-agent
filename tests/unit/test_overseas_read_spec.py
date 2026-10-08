"""Overseas read-only APIs against the official KIS contract.

Every request is captured at the HTTP layer (after the TR_ID paper conversion) and
the test asserts the endpoint, the final TR_ID header and the *complete* query
dict. Sources: KIS workbook (2025-12-12) sheets for the endpoints below and
open-trading-api examples_llm/overseas_stock/<name>. Where the sample was changed
after the workbook (price_fluct MINX) the sample wins; see the ranking tests.
"""

import warnings
from datetime import datetime
from types import SimpleNamespace

import pytest
import pytz

from kis_agent.core.client import KISClient
from kis_agent.core.config import KISConfig
from kis_agent.core.tr_mapping import PaperTradingNotSupportedError
from kis_agent.overseas.account_api import OverseasAccountAPI
from kis_agent.overseas.api_facade import OverseasStockAPI
from kis_agent.overseas.price_api import OverseasPriceAPI
from kis_agent.overseas.ranking_api import OverseasRankingAPI

ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

# 2026-10-08 01:30 KST = 2026-10-07 12:30 New York: the two local dates differ.
NOW_SPLIT = datetime(2026, 10, 7, 16, 30, tzinfo=pytz.utc)
# 2026-10-08 14:00 KST = 2026-10-08 01:00 New York: same local date.
NOW_SAME = datetime(2026, 10, 8, 5, 0, tzinfo=pytz.utc)


class _Response:
    status_code = 200
    text = '{"rt_cd":"0","output":{}}'
    headers = {}

    def json(self):
        return {"rt_cd": "0", "output": {}}


@pytest.fixture
def wire(monkeypatch):
    """Return a factory building an API whose HTTP calls are captured."""

    def _build(api_cls, paper=False, account=True):
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
        api = api_cls(
            client=client,
            account_info=dict(ACCOUNT) if account else None,
            enable_cache=False,
            _from_agent=True,
        )
        return api, sent

    return _build


def _one(sent, path):
    assert len(sent) == 1
    req = sent[0]
    assert req["method"] == "GET"
    assert req["url"].endswith(path)
    return req["headers"]["tr_id"], req["params"]


@pytest.fixture
def now(monkeypatch):
    def _set(value):
        monkeypatch.setattr("kis_agent.overseas.account_api._utc_now", lambda: value)

    return _set


# ---------------------------------------------------------------------------
# account_api.get_order_history  (inquire-ccnl)
# ---------------------------------------------------------------------------
CCNL_PATH = "/uapi/overseas-stock/v1/trading/inquire-ccnl"


def test_order_history_default_real(wire, now):
    now(NOW_SPLIT)
    api, sent = wire(OverseasAccountAPI)
    api.get_order_history()
    tr_id, params = _one(sent, CCNL_PATH)
    assert tr_id == "TTTS3035R"
    assert params == {
        **ACCOUNT,
        "PDNO": "%",
        "ORD_STRT_DT": "20261007",
        "ORD_END_DT": "20261008",
        "SLL_BUY_DVSN": "00",
        "CCLD_NCCS_DVSN": "00",
        "OVRS_EXCG_CD": "%",
        "SORT_SQN": "DS",
        "ORD_DT": "",
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "CTX_AREA_NK200": "",
        "CTX_AREA_FK200": "",
    }


def test_order_history_same_local_date(wire, now):
    now(NOW_SAME)
    api, sent = wire(OverseasAccountAPI)
    api.get_order_history()
    _, params = _one(sent, CCNL_PATH)
    assert params["ORD_STRT_DT"] == params["ORD_END_DT"] == "20261008"


def test_order_history_default_paper_sends_blank_filters(wire, now):
    now(NOW_SPLIT)
    api, sent = wire(OverseasAccountAPI, paper=True)
    api.get_order_history()
    tr_id, params = _one(sent, CCNL_PATH)
    assert tr_id == "VTTS3035R"
    assert params["PDNO"] == ""
    assert params["OVRS_EXCG_CD"] == ""
    assert params["SLL_BUY_DVSN"] == params["CCLD_NCCS_DVSN"] == "00"


def test_order_history_paper_normalises_percent(wire, now):
    now(NOW_SPLIT)
    api, sent = wire(OverseasAccountAPI, paper=True)
    api.get_order_history(ovrs_excg_cd="%", pdno="%")
    _, params = _one(sent, CCNL_PATH)
    assert params["PDNO"] == "" and params["OVRS_EXCG_CD"] == ""


def test_order_history_explicit_arguments(wire, now):
    now(NOW_SPLIT)
    api, sent = wire(OverseasAccountAPI)
    api.get_order_history(
        "NASD",
        "AS",
        "fk",
        "nk",
        pdno="aapl",
        ord_strt_dt="20260101",
        ord_end_dt="20260131",
        sll_buy_dvsn="02",
        ccld_nccs_dvsn="01",
    )
    _, params = _one(sent, CCNL_PATH)
    assert params == {
        **ACCOUNT,
        "PDNO": "AAPL",
        "ORD_STRT_DT": "20260101",
        "ORD_END_DT": "20260131",
        "SLL_BUY_DVSN": "02",
        "CCLD_NCCS_DVSN": "01",
        "OVRS_EXCG_CD": "NASD",
        "SORT_SQN": "AS",
        "ORD_DT": "",
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "CTX_AREA_NK200": "nk",
        "CTX_AREA_FK200": "fk",
    }


# ---------------------------------------------------------------------------
# account_api.get_reserve_order_list  (order-resv-list)
# ---------------------------------------------------------------------------
RESV_PATH = "/uapi/overseas-stock/v1/trading/order-resv-list"


def test_reserve_list_default_us(wire, now):
    now(NOW_SPLIT)
    api, sent = wire(OverseasAccountAPI)
    api.get_reserve_order_list()
    tr_id, params = _one(sent, RESV_PATH)
    assert tr_id == "TTTT3039R"
    assert params == {
        **ACCOUNT,
        "INQR_STRT_DT": "20261001",
        "INQR_END_DT": "20261008",
        "INQR_DVSN_CD": "00",
        "OVRS_EXCG_CD": "",
        "PRDT_TYPE_CD": "",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": "",
    }


@pytest.mark.parametrize(
    "exchange,expected_tr",
    [
        ("NASD", "TTTT3039R"),
        ("nyse", "TTTT3039R"),
        ("AMEX", "TTTT3039R"),
        ("SEHK", "TTTS3014R"),
        ("SHAA", "TTTS3014R"),
        ("SZAA", "TTTS3014R"),
        ("TKSE", "TTTS3014R"),
        ("HASE", "TTTS3014R"),
        ("VNSE", "TTTS3014R"),
    ],
)
def test_reserve_list_selects_tr_by_exchange(wire, now, exchange, expected_tr):
    now(NOW_SAME)
    api, sent = wire(OverseasAccountAPI)
    api.get_reserve_order_list(exchange, prdt_type_cd="501")
    tr_id, params = _one(sent, RESV_PATH)
    assert tr_id == expected_tr
    assert params["OVRS_EXCG_CD"] == exchange.upper()
    assert params["PRDT_TYPE_CD"] == "501"


def test_reserve_list_explicit_arguments_asia(wire, now):
    now(NOW_SPLIT)
    api, sent = wire(OverseasAccountAPI)
    api.get_reserve_order_list(
        ctx_area_fk200="fk",
        ctx_area_nk200="nk",
        inqr_strt_dt="20260101",
        inqr_end_dt="20260131",
        inqr_dvsn_cd="02",
        nat_dv="asia",
    )
    tr_id, params = _one(sent, RESV_PATH)
    assert tr_id == "TTTS3014R"
    assert params == {
        **ACCOUNT,
        "INQR_STRT_DT": "20260101",
        "INQR_END_DT": "20260131",
        "INQR_DVSN_CD": "02",
        "OVRS_EXCG_CD": "",
        "PRDT_TYPE_CD": "",
        "CTX_AREA_FK200": "fk",
        "CTX_AREA_NK200": "nk",
    }


def test_reserve_list_nat_dv_us_overrides_blank_exchange(wire, now):
    now(NOW_SAME)
    api, sent = wire(OverseasAccountAPI)
    api.get_reserve_order_list(nat_dv="us")
    tr_id, _ = _one(sent, RESV_PATH)
    assert tr_id == "TTTT3039R"


def test_reserve_list_start_date_follows_given_end_date(wire, now):
    now(NOW_SAME)
    api, sent = wire(OverseasAccountAPI)
    api.get_reserve_order_list(inqr_end_dt="20260310")
    _, params = _one(sent, RESV_PATH)
    assert params["INQR_STRT_DT"] == "20260303"
    assert params["INQR_END_DT"] == "20260310"


def test_reserve_list_rejects_unknown_market(wire):
    api, sent = wire(OverseasAccountAPI)
    with pytest.raises(ValueError, match="nat_dv"):
        api.get_reserve_order_list(nat_dv="eu")
    assert not sent


def test_reserve_list_sort_sqn_is_ignored_with_warning(wire, now):
    now(NOW_SAME)
    api, sent = wire(OverseasAccountAPI)
    with pytest.warns(DeprecationWarning, match="sort_sqn") as rec:
        api.get_reserve_order_list(sort_sqn="AS")
    assert rec[0].filename == __file__
    _, params = _one(sent, RESV_PATH)
    assert "SORT_SQN" not in params


def test_reserve_list_not_supported_on_paper(wire):
    api, sent = wire(OverseasAccountAPI, paper=True)
    with pytest.raises(PaperTradingNotSupportedError):
        api.get_reserve_order_list()
    assert not sent


# ---------------------------------------------------------------------------
# account_api.get_foreign_margin  (foreign-margin)
# ---------------------------------------------------------------------------
def test_foreign_margin_sends_only_the_account(wire):
    api, sent = wire(OverseasAccountAPI)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        api.get_foreign_margin()
    tr_id, params = _one(sent, "/uapi/overseas-stock/v1/trading/foreign-margin")
    assert tr_id == "TTTC2101R"
    assert params == ACCOUNT


def test_foreign_margin_currency_is_ignored_with_warning(wire):
    api, sent = wire(OverseasAccountAPI)
    with pytest.warns(DeprecationWarning, match="crcy_cd") as rec:
        api.get_foreign_margin("USD")
    assert rec[0].filename == __file__
    _, params = _one(sent, "/uapi/overseas-stock/v1/trading/foreign-margin")
    assert params == ACCOUNT


# ---------------------------------------------------------------------------
# price_api
# ---------------------------------------------------------------------------
PRICE = "/uapi/overseas-price/v1/quotations/"


def test_minute_price_first_page(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    api.get_minute_price("nas", "aapl")
    tr_id, params = _one(sent, PRICE + "inquire-time-itemchartprice")
    assert tr_id == "HHDFS76950200"
    assert params == {
        "AUTH": "",
        "EXCD": "NAS",
        "SYMB": "AAPL",
        "NMIN": "1",
        "PINC": "0",
        "NEXT": "",
        "NREC": "120",
        "FILL": "",
        "KEYB": "",
    }


def test_minute_price_next_page_derives_next_flag(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    api.get_minute_price(
        "NAS", "AAPL", nmin="5", pinc="1", nrec="60", keyb="20241014140100"
    )
    _, params = _one(sent, PRICE + "inquire-time-itemchartprice")
    assert params == {
        "AUTH": "",
        "EXCD": "NAS",
        "SYMB": "AAPL",
        "NMIN": "5",
        "PINC": "1",
        "NEXT": "1",
        "NREC": "60",
        "FILL": "",
        "KEYB": "20241014140100",
    }


def test_minute_price_explicit_next_flag_wins(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    api.get_minute_price("NAS", "AAPL", keyb="20241014140100", next_flag="")
    _, params = _one(sent, PRICE + "inquire-time-itemchartprice")
    assert params["NEXT"] == "" and params["KEYB"] == "20241014140100"


def test_ccnl_default_is_today(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    api.get_ccnl("nas", "aapl")
    tr_id, params = _one(sent, PRICE + "inquire-ccnl")
    assert tr_id == "HHDFS76200300"
    assert params == {
        "EXCD": "NAS",
        "AUTH": "",
        "KEYB": "",
        "TDAY": "1",
        "SYMB": "AAPL",
    }


def test_ccnl_previous_day_with_key(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    api.get_ccnl("NAS", "AAPL", tday="0", keyb="k")
    _, params = _one(sent, PRICE + "inquire-ccnl")
    assert params == {
        "EXCD": "NAS",
        "AUTH": "",
        "KEYB": "k",
        "TDAY": "0",
        "SYMB": "AAPL",
    }


NEWS_EMPTY = {
    "INFO_GB": "",
    "CLASS_CD": "",
    "NATION_CD": "",
    "EXCHANGE_CD": "",
    "SYMB": "",
    "DATA_DT": "",
    "DATA_TM": "",
    "CTS": "",
}


def test_news_title_default_sends_the_spec_fields_only(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        api.get_news_title()
    tr_id, params = _one(sent, PRICE + "news-title")
    assert tr_id == "HHPSTH60100C1"
    assert params == NEWS_EMPTY


def test_news_title_new_arguments(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        api.get_news_title(
            symb="aapl",
            info_gb="1",
            class_cd="2",
            nation_cd="US",
            exchange_cd="NAS",
            data_dt="20240502",
            data_tm="093500",
            cts="next",
        )
    _, params = _one(sent, PRICE + "news-title")
    assert params == {
        "INFO_GB": "1",
        "CLASS_CD": "2",
        "NATION_CD": "US",
        "EXCHANGE_CD": "NAS",
        "SYMB": "AAPL",
        "DATA_DT": "20240502",
        "DATA_TM": "093500",
        "CTS": "next",
    }


def test_news_title_renamed_arguments_still_work(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    with pytest.warns(DeprecationWarning) as rec:
        api.get_news_title("", "AAPL", "3", "20240502")
    messages = sorted(str(w.message) for w in rec)
    assert len(messages) == 2
    assert any("news_gb" in m and "info_gb" in m for m in messages)
    assert any("bymd" in m and "data_dt" in m for m in messages)
    assert all(w.filename == __file__ for w in rec)
    _, params = _one(sent, PRICE + "news-title")
    assert params == {
        **NEWS_EMPTY,
        "INFO_GB": "3",
        "SYMB": "AAPL",
        "DATA_DT": "20240502",
    }


def test_news_title_new_names_win_over_renamed_ones(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        api.get_news_title(
            news_gb="old", info_gb="new", bymd="20200101", data_dt="20240502"
        )
    _, params = _one(sent, PRICE + "news-title")
    assert params["INFO_GB"] == "new" and params["DATA_DT"] == "20240502"


def test_news_title_dropped_arguments_warn_and_are_not_sent(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    with pytest.warns(DeprecationWarning) as rec:
        api.get_news_title(excd="NAS", nrec="5", ctx_area_fk="fk", ctx_area_nk="nk")
    names = " ".join(str(w.message) for w in rec)
    for name in ("excd", "nrec", "ctx_area_fk", "ctx_area_nk"):
        assert name in names
    assert len(rec) == 4
    _, params = _one(sent, PRICE + "news-title")
    assert params == NEWS_EMPTY


def test_industry_theme_default(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        api.get_industry_theme("nas")
    tr_id, params = _one(sent, PRICE + "industry-theme")
    assert tr_id == "HHDFS76370000"
    assert params == {
        "KEYB": "",
        "AUTH": "",
        "EXCD": "NAS",
        "ICOD": "",
        "VOL_RANG": "0",
    }


def test_industry_theme_arguments(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    api.get_industry_theme("NYS", icod="010", vol_rang="3", keyb="k")
    _, params = _one(sent, PRICE + "industry-theme")
    assert params == {
        "KEYB": "k",
        "AUTH": "",
        "EXCD": "NYS",
        "ICOD": "010",
        "VOL_RANG": "3",
    }


def test_industry_theme_dropped_arguments_warn_and_are_not_sent(wire):
    api, sent = wire(OverseasPriceAPI, account=False)
    with pytest.warns(DeprecationWarning) as rec:
        api.get_industry_theme("NAS", "AAPL", iscd_cond="1", co_yn="Y")
    names = " ".join(str(w.message) for w in rec)
    for name in ("symb", "iscd_cond", "co_yn"):
        assert name in names
    assert len(rec) == 3
    _, params = _one(sent, PRICE + "industry-theme")
    assert set(params) == {"KEYB", "AUTH", "EXCD", "ICOD", "VOL_RANG"}


# ---------------------------------------------------------------------------
# ranking_api
# ---------------------------------------------------------------------------
RANK = "/uapi/overseas-stock/v1/ranking/"


def test_trade_volume_ranking_params(wire):
    api, sent = wire(OverseasRankingAPI, account=False)
    api.trade_volume_ranking("nas")
    tr_id, params = _one(sent, RANK + "trade-vol")
    assert tr_id == "HHDFS76310010"
    assert params == {
        "EXCD": "NAS",
        "NDAY": "0",
        "VOL_RANG": "0",
        "AUTH": "",
        "KEYB": "",
        "PRC1": "",
        "PRC2": "",
    }


def test_trade_volume_ranking_price_range(wire):
    api, sent = wire(OverseasRankingAPI, account=False)
    api.trade_volume_ranking("NYS", "3", "2", prc1="1", prc2="50")
    _, params = _one(sent, RANK + "trade-vol")
    assert params == {
        "EXCD": "NYS",
        "NDAY": "3",
        "VOL_RANG": "2",
        "AUTH": "",
        "KEYB": "",
        "PRC1": "1",
        "PRC2": "50",
    }


def test_trade_amount_ranking_params(wire):
    api, sent = wire(OverseasRankingAPI, account=False)
    api.trade_amount_ranking("nas")
    tr_id, params = _one(sent, RANK + "trade-pbmn")
    assert tr_id == "HHDFS76320010"
    assert params == {
        "EXCD": "NAS",
        "NDAY": "0",
        "VOL_RANG": "0",
        "AUTH": "",
        "KEYB": "",
        "PRC1": "",
        "PRC2": "",
    }


def test_trade_amount_ranking_price_range(wire):
    api, sent = wire(OverseasRankingAPI, account=False)
    api.trade_amount_ranking("NYS", "9", "6", prc1="5", prc2="10")
    _, params = _one(sent, RANK + "trade-pbmn")
    assert params == {
        "EXCD": "NYS",
        "NDAY": "9",
        "VOL_RANG": "6",
        "AUTH": "",
        "KEYB": "",
        "PRC1": "5",
        "PRC2": "10",
    }


def test_market_cap_ranking_has_no_nday(wire):
    api, sent = wire(OverseasRankingAPI, account=False)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        api.market_cap_ranking("nas", vol_rang="2")
    tr_id, params = _one(sent, RANK + "market-cap")
    assert tr_id == "HHDFS76350100"
    assert params == {"EXCD": "NAS", "VOL_RANG": "2", "AUTH": "", "KEYB": ""}


def test_market_cap_ranking_nday_warns_and_is_not_sent(wire):
    api, sent = wire(OverseasRankingAPI, account=False)
    with pytest.warns(DeprecationWarning, match="nday") as rec:
        api.market_cap_ranking("NAS", nday="3")
    assert rec[0].filename == __file__
    _, params = _one(sent, RANK + "market-cap")
    assert params == {"EXCD": "NAS", "VOL_RANG": "0", "AUTH": "", "KEYB": ""}


def test_price_fluctuation_ranking_sends_minx(wire):
    api, sent = wire(OverseasRankingAPI, account=False)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        api.price_fluctuation_ranking("nas")
    tr_id, params = _one(sent, RANK + "price-fluct")
    assert tr_id == "HHDFS76260000"
    # MINX (KIS sample fixed 2026-03-16), no NDAY, no MIXN.
    assert params == {
        "EXCD": "NAS",
        "GUBN": "0",
        "MINX": "0",
        "VOL_RANG": "0",
        "AUTH": "",
        "KEYB": "",
    }


def test_price_fluctuation_ranking_arguments(wire):
    api, sent = wire(OverseasRankingAPI, account=False)
    api.price_fluctuation_ranking("NAS", gubn="1", vol_rang="4", minx="7")
    _, params = _one(sent, RANK + "price-fluct")
    assert params == {
        "EXCD": "NAS",
        "GUBN": "1",
        "MINX": "7",
        "VOL_RANG": "4",
        "AUTH": "",
        "KEYB": "",
    }


def test_price_fluctuation_ranking_legacy_nday_becomes_minx(wire):
    api, sent = wire(OverseasRankingAPI, account=False)
    with pytest.warns(DeprecationWarning, match="nday.*minx") as rec:
        api.price_fluctuation_ranking("NAS", "5")
    assert rec[0].filename == __file__
    _, params = _one(sent, RANK + "price-fluct")
    assert params["MINX"] == "5"
    assert "NDAY" not in params


def test_price_fluctuation_ranking_minx_wins_over_nday(wire):
    api, sent = wire(OverseasRankingAPI, account=False)
    with pytest.warns(DeprecationWarning, match="nday") as rec:
        api.price_fluctuation_ranking("NAS", "5", minx="2")
    assert len(rec) == 1
    _, params = _one(sent, RANK + "price-fluct")
    assert params["MINX"] == "2"


def test_new_high_low_ranking_sends_gubn2(wire):
    api, sent = wire(OverseasRankingAPI, account=False)
    api.new_high_low_ranking("nas")
    tr_id, params = _one(sent, RANK + "new-highlow")
    assert tr_id == "HHDFS76300000"
    # NDAY stays: the workbook defines it (5일..1년); the sample's MINX is a copy-paste.
    assert params == {
        "EXCD": "NAS",
        "NDAY": "0",
        "GUBN": "1",
        "GUBN2": "0",
        "VOL_RANG": "0",
        "AUTH": "",
        "KEYB": "",
    }


def test_new_high_low_ranking_arguments(wire):
    api, sent = wire(OverseasRankingAPI, account=False)
    api.new_high_low_ranking("NYS", "6", "0", "3", gubn2="1")
    _, params = _one(sent, RANK + "new-highlow")
    assert params == {
        "EXCD": "NYS",
        "NDAY": "6",
        "GUBN": "0",
        "GUBN2": "1",
        "VOL_RANG": "3",
        "AUTH": "",
        "KEYB": "",
    }


@pytest.mark.parametrize(
    "method,args",
    [
        ("trade_volume_ranking", ("NAS",)),
        ("trade_amount_ranking", ("NAS",)),
        ("market_cap_ranking", ("NAS",)),
        ("price_fluctuation_ranking", ("NAS",)),
        ("new_high_low_ranking", ("NAS",)),
    ],
)
def test_ranking_does_not_swallow_paper_unsupported(wire, method, args):
    """모의투자 미지원 오류가 None으로 삼켜지면 호출부가 원인을 알 수 없다."""
    api, sent = wire(OverseasRankingAPI, paper=True, account=False)
    with pytest.raises(PaperTradingNotSupportedError):
        getattr(api, method)(*args)
    assert not sent


# ---------------------------------------------------------------------------
# facade forwarding
# ---------------------------------------------------------------------------
@pytest.fixture
def facade():
    from unittest.mock import MagicMock

    api = object.__new__(OverseasStockAPI)
    api.price_api = MagicMock()
    api.account_api = MagicMock()
    api.ranking_api = MagicMock()
    return api


def test_facade_forwards_new_price_arguments(facade):
    facade.get_minute_price("NAS", "AAPL", "5", "1", "60", keyb="k", next_flag="1")
    facade.price_api.get_minute_price.assert_called_once_with(
        "NAS", "AAPL", "5", "1", "60", keyb="k", next_flag="1"
    )
    facade.get_ccnl("NAS", "AAPL", tday="0", keyb="k")
    facade.price_api.get_ccnl.assert_called_once_with("NAS", "AAPL", tday="0", keyb="k")
    facade.get_news_title(
        symb="AAPL",
        info_gb="1",
        class_cd="2",
        nation_cd="US",
        exchange_cd="NAS",
        data_dt="20240502",
        data_tm="093500",
        cts="c",
    )
    facade.price_api.get_news_title.assert_called_once_with(
        excd="",
        symb="AAPL",
        nrec="20",
        info_gb="1",
        class_cd="2",
        nation_cd="US",
        exchange_cd="NAS",
        data_dt="20240502",
        data_tm="093500",
        cts="c",
    )
    facade.get_industry_theme("NAS", icod="010", vol_rang="2", keyb="k")
    facade.price_api.get_industry_theme.assert_called_once_with(
        "NAS", "", icod="010", vol_rang="2", keyb="k"
    )


def test_facade_forwards_new_account_arguments(facade):
    facade.get_order_history(
        "NASD",
        "AS",
        "fk",
        "nk",
        pdno="AAPL",
        ord_strt_dt="20260101",
        ord_end_dt="20260131",
        sll_buy_dvsn="02",
        ccld_nccs_dvsn="01",
    )
    facade.account_api.get_order_history.assert_called_once_with(
        "NASD",
        "AS",
        "fk",
        "nk",
        pdno="AAPL",
        ord_strt_dt="20260101",
        ord_end_dt="20260131",
        sll_buy_dvsn="02",
        ccld_nccs_dvsn="01",
    )
    facade.get_reserve_order_list(
        "SEHK",
        ctx_area_fk200="fk",
        ctx_area_nk200="nk",
        inqr_strt_dt="20260101",
        inqr_end_dt="20260131",
        inqr_dvsn_cd="01",
        prdt_type_cd="501",
        nat_dv="asia",
    )
    facade.account_api.get_reserve_order_list.assert_called_once_with(
        "SEHK",
        "DS",
        "fk",
        "nk",
        inqr_strt_dt="20260101",
        inqr_end_dt="20260131",
        inqr_dvsn_cd="01",
        prdt_type_cd="501",
        nat_dv="asia",
    )


def test_facade_forwards_new_ranking_arguments(facade):
    facade.trade_volume_ranking("NAS", prc1="1", prc2="9")
    facade.ranking_api.trade_volume_ranking.assert_called_once_with(
        "NAS", "0", "0", prc1="1", prc2="9"
    )
    facade.trade_amount_ranking("NAS", prc1="1", prc2="9")
    facade.ranking_api.trade_amount_ranking.assert_called_once_with(
        "NAS", "0", "0", prc1="1", prc2="9"
    )
    facade.price_fluctuation_ranking("NAS", gubn="1", minx="3")
    facade.ranking_api.price_fluctuation_ranking.assert_called_once_with(
        "NAS", "0", "1", "0", minx="3"
    )
    facade.new_high_low_ranking("NAS", gubn2="1")
    facade.ranking_api.new_high_low_ranking.assert_called_once_with(
        "NAS", "0", "1", "0", gubn2="1"
    )
