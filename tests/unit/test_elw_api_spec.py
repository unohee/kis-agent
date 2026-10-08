"""ELW 시세/순위 APIs send exactly the fields the official KIS spec defines.

Each case pins the COMPLETE request (endpoint, tr_id, method, params) against the
workbook "Required" column ([국내주식] ELW 시세, 국내주식-166 .. -186).
"""

import inspect
import re
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import kis_agent.elw.price_api as price_module
import kis_agent.elw.ranking_api as ranking_module
from kis_agent.core.tr_mapping import PaperTradingNotSupportedError, resolve_tr_id
from kis_agent.elw import ElwAPI, ElwPriceAPI, ElwRankingAPI

Q = "/uapi/elw/v1/quotations/"
R = "/uapi/elw/v1/ranking/"


def _client():
    client = MagicMock()
    client.is_real = True
    client.make_request.return_value = {"rt_cd": "0", "output": [], "output1": []}
    return client


def _api(cls, client):
    return cls(
        client,
        {"CANO": "12345678", "ACNT_PRDT_CD": "01"},
        enable_cache=False,
        _from_agent=True,
    )


def _sent(client):
    return client.make_request.call_args.kwargs


def _today():
    return date.today().strftime("%Y%m%d")


def _plus7():
    return (date.today() + timedelta(days=7)).strftime("%Y%m%d")


TREND_PARAMS = {"FID_COND_MRKT_DIV_CODE": "W", "FID_INPUT_ISCD": "58J297"}
MINUTE_PARAMS = {**TREND_PARAMS, "FID_HOUR_CLS_CODE": "60", "FID_PW_DATA_INCU_YN": "N"}

COND_SEARCH_PARAMS = {
    "FID_COND_MRKT_DIV_CODE": "W",
    "FID_COND_SCR_DIV_CODE": "11510",
    "FID_RANK_SORT_CLS_CODE": "0",
    "FID_INPUT_CNT_1": "1",
    "FID_INPUT_ISCD": "00000",
    "FID_MRKT_CLS_CODE": "A",
    "FID_INPUT_DATE_1": "0",
    "FID_INPUT_DATE_2": "0",
    "FID_ETC_CLS_CODE": "0",
    "FID_DIV_CLS_CODE": "0",
    **dict.fromkeys(["FID_RANK_SORT_CLS_CODE_2", "FID_INPUT_CNT_2", "FID_RANK_SORT_CLS_CODE_3", "FID_INPUT_CNT_3", "FID_TRGT_CLS_CODE", "FID_UNAS_INPUT_ISCD", "FID_INPUT_ISCD_2", "FID_INPUT_RMNN_DYNU_1", "FID_INPUT_RMNN_DYNU_2", "FID_PRPR_CNT1", "FID_PRPR_CNT2", "FID_RSFL_RATE1", "FID_RSFL_RATE2", "FID_VOL1", "FID_VOL2", "FID_APLY_RANG_PRC_1", "FID_APLY_RANG_PRC_2", "FID_LVRG_VAL1", "FID_LVRG_VAL2", "FID_VOL3", "FID_VOL4", "FID_INTS_VLTL1", "FID_INTS_VLTL2", "FID_PRMM_VAL1", "FID_PRMM_VAL2", "FID_GEAR1", "FID_GEAR2", "FID_PRLS_QRYR_RATE1", "FID_PRLS_QRYR_RATE2", "FID_DELTA1", "FID_DELTA2", "FID_ACPR1", "FID_ACPR2", "FID_STCK_CNVR_RATE1", "FID_STCK_CNVR_RATE2", "FID_PRIT1", "FID_PRIT2", "FID_CFP1", "FID_CFP2", "FID_INPUT_NMIX_PRICE_1", "FID_INPUT_NMIX_PRICE_2", "FID_EGEA_VAL1", "FID_EGEA_VAL2", "FID_INPUT_DVDN_ERT", "FID_INPUT_HIST_VLTL", "FID_THETA1", "FID_THETA2"], ""),
}

# (api class, method, args, kwargs, endpoint, tr_id, complete params)
CASES = [
    (
        ElwPriceAPI,
        "get_elw_compare_stocks",
        ("005930",),
        {},
        Q + "compare-stocks",
        "FHKEW151701C0",
        {"FID_COND_SCR_DIV_CODE": "11517", "FID_INPUT_ISCD": "005930"},
    ),
    (
        ElwPriceAPI,
        "get_elw_cond_search",
        (),
        {},
        Q + "cond-search",
        "FHKEW15100000",
        COND_SEARCH_PARAMS,
    ),
    (
        ElwPriceAPI,
        "get_elw_cond_search",
        (),
        {
            "rank_sort_cls_code": "10",
            "input_cnt_1": "2",
            "issuer_code": "00003",
            "market_cls_code": "CO",
            "listing_period": "2",
            "maturity_period": "4",
            "strike_cls_code": "1",
            "div_cls_code": "2",
            "filters": {"FID_DELTA1": "0.3", "FID_UNAS_INPUT_ISCD": "005930"},
        },
        Q + "cond-search",
        "FHKEW15100000",
        {
            **COND_SEARCH_PARAMS,
            "FID_RANK_SORT_CLS_CODE": "10",
            "FID_INPUT_CNT_1": "2",
            "FID_INPUT_ISCD": "00003",
            "FID_MRKT_CLS_CODE": "CO",
            "FID_INPUT_DATE_1": "2",
            "FID_INPUT_DATE_2": "4",
            "FID_ETC_CLS_CODE": "1",
            "FID_DIV_CLS_CODE": "2",
            "FID_DELTA1": "0.3",
            "FID_UNAS_INPUT_ISCD": "005930",
        },
    ),
    (
        ElwPriceAPI,
        "get_elw_expiration_stocks",
        (),
        {},
        Q + "expiration-stocks",
        "FHKEW154700C0",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "11547",
            "FID_INPUT_DATE_1": _today(),
            "FID_INPUT_DATE_2": _plus7(),
            "FID_DIV_CLS_CODE": "2",
            "FID_ETC_CLS_CODE": "",
            "FID_UNAS_INPUT_ISCD": "000000",
            "FID_INPUT_ISCD_2": "00000",
            "FID_BLNG_CLS_CODE": "0",
            "FID_INPUT_OPTION_1": "",
        },
    ),
    (
        ElwPriceAPI,
        "get_elw_expiration_stocks",
        ("20260401", "20260410"),
        {
            "call_put": "0",
            "underlying": "005930",
            "issuer": "00017",
            "settle_type": "2",
        },
        Q + "expiration-stocks",
        "FHKEW154700C0",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "11547",
            "FID_INPUT_DATE_1": "20260401",
            "FID_INPUT_DATE_2": "20260410",
            "FID_DIV_CLS_CODE": "0",
            "FID_ETC_CLS_CODE": "",
            "FID_UNAS_INPUT_ISCD": "005930",
            "FID_INPUT_ISCD_2": "00017",
            "FID_BLNG_CLS_CODE": "2",
            "FID_INPUT_OPTION_1": "",
        },
    ),
    (
        ElwPriceAPI,
        "get_elw_newly_listed",
        (),
        {},
        Q + "newly-listed",
        "FHKEW154800C0",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "11548",
            "FID_DIV_CLS_CODE": "02",
            "FID_UNAS_INPUT_ISCD": "000000",
            "FID_INPUT_ISCD_2": "00003",
            "FID_INPUT_DATE_1": _today(),
            "FID_BLNC_CLS_CODE": "0",
        },
    ),
    (
        ElwPriceAPI,
        "get_elw_newly_listed",
        ("20260401",),
        {"call_put": "00", "underlying": "2001", "issuer": "00005", "settle_type": "1"},
        Q + "newly-listed",
        "FHKEW154800C0",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "11548",
            "FID_DIV_CLS_CODE": "00",
            "FID_UNAS_INPUT_ISCD": "2001",
            "FID_INPUT_ISCD_2": "00005",
            "FID_INPUT_DATE_1": "20260401",
            "FID_BLNC_CLS_CODE": "1",
        },
    ),
    (
        ElwPriceAPI,
        "get_elw_udrl_asset_list",
        (),
        {},
        Q + "udrl-asset-list",
        "FHKEW154100C0",
        {
            "FID_COND_SCR_DIV_CODE": "11541",
            "FID_RANK_SORT_CLS_CODE": "0",
            "FID_INPUT_ISCD": "00000",
        },
    ),
    (
        ElwPriceAPI,
        "get_elw_udrl_asset_list",
        ("3",),
        {"issuer": "00017"},
        Q + "udrl-asset-list",
        "FHKEW154100C0",
        {
            "FID_COND_SCR_DIV_CODE": "11541",
            "FID_RANK_SORT_CLS_CODE": "3",
            "FID_INPUT_ISCD": "00017",
        },
    ),
    (
        ElwPriceAPI,
        "get_elw_udrl_asset_price",
        ("005930",),
        {},
        Q + "udrl-asset-price",
        "FHKEW154101C0",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "11541",
            "FID_MRKT_CLS_CODE": "A",
            "FID_INPUT_ISCD": "00000",
            "FID_UNAS_INPUT_ISCD": "005930",
            "FID_VOL_CNT": "",
            "FID_TRGT_EXLS_CLS_CODE": "0",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_INPUT_VOL_1": "",
            "FID_INPUT_VOL_2": "",
            "FID_INPUT_RMNN_DYNU_1": "",
            "FID_INPUT_RMNN_DYNU_2": "",
            "FID_OPTION": "0",
            "FID_INPUT_OPTION_1": "",
            "FID_INPUT_OPTION_2": "",
        },
    ),
    (
        ElwPriceAPI,
        "get_elw_udrl_asset_price",
        ("005930",),
        {
            "market_cls_code": "C",
            "issuer": "00003",
            "prev_volume": "1000",
            "exclude_untradable": "1",
            "price_min": "100",
            "price_max": "5000",
            "volume_min": "10",
            "volume_max": "500",
            "remain_days_min": "30",
            "remain_days_max": "90",
            "option_status": "1",
        },
        Q + "udrl-asset-price",
        "FHKEW154101C0",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "11541",
            "FID_MRKT_CLS_CODE": "C",
            "FID_INPUT_ISCD": "00003",
            "FID_UNAS_INPUT_ISCD": "005930",
            "FID_VOL_CNT": "1000",
            "FID_TRGT_EXLS_CLS_CODE": "1",
            "FID_INPUT_PRICE_1": "100",
            "FID_INPUT_PRICE_2": "5000",
            "FID_INPUT_VOL_1": "10",
            "FID_INPUT_VOL_2": "500",
            "FID_INPUT_RMNN_DYNU_1": "30",
            "FID_INPUT_RMNN_DYNU_2": "90",
            "FID_OPTION": "1",
            "FID_INPUT_OPTION_1": "",
            "FID_INPUT_OPTION_2": "",
        },
    ),
    # --- (market, code) trend APIs ---
    *[
        (ElwPriceAPI, name, ("58J297",), {}, Q + path, tr_id, TREND_PARAMS)
        for name, path, tr_id in [
            ("get_elw_indicator_trend_ccnl", "indicator-trend-ccnl", "FHPEW02740100"),
            ("get_elw_indicator_trend_daily", "indicator-trend-daily", "FHPEW02740200"),
            ("get_elw_lp_trade_trend", "lp-trade-trend", "FHPEW03760000"),
            (
                "get_elw_sensitivity_trend_ccnl",
                "sensitivity-trend-ccnl",
                "FHPEW02830100",
            ),
            (
                "get_elw_sensitivity_trend_daily",
                "sensitivity-trend-daily",
                "FHPEW02830200",
            ),
            ("get_elw_volatility_trend_ccnl", "volatility-trend-ccnl", "FHPEW02840100"),
            (
                "get_elw_volatility_trend_daily",
                "volatility-trend-daily",
                "FHPEW02840200",
            ),
            ("get_elw_volatility_trend_tick", "volatility-trend-tick", "FHPEW02840400"),
        ]
    ],
    # --- minute trend APIs ---
    *[
        (ElwPriceAPI, name, ("58J297",), kwargs, Q + path, tr_id, params)
        for name, path, tr_id in [
            (
                "get_elw_indicator_trend_minute",
                "indicator-trend-minute",
                "FHPEW02740300",
            ),
            (
                "get_elw_volatility_trend_minute",
                "volatility-trend-minute",
                "FHPEW02840300",
            ),
        ]
        for kwargs, params in [
            ({}, MINUTE_PARAMS),
            (
                {"hour_cls_code": "300", "include_past": "Y"},
                {
                    **MINUTE_PARAMS,
                    "FID_HOUR_CLS_CODE": "300",
                    "FID_PW_DATA_INCU_YN": "Y",
                },
            ),
        ]
    ],
    # --- ranking ---
    (
        ElwRankingAPI,
        "get_elw_indicator_rank",
        (),
        {},
        R + "indicator",
        "FHPEW02790000",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "20279",
            "FID_UNAS_INPUT_ISCD": "000000",
            "FID_INPUT_ISCD": "00000",
            "FID_DIV_CLS_CODE": "0",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_INPUT_VOL_1": "",
            "FID_INPUT_VOL_2": "",
            "FID_RANK_SORT_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
        },
    ),
    (
        ElwRankingAPI,
        "get_elw_indicator_rank",
        ("1",),
        {
            "underlying": "005930",
            "issuer": "00003",
            "call_put": "1",
            "price_min": "1000",
            "price_max": "5000",
            "volume_min": "100",
            "volume_max": "1000",
            "settle_type": "2",
        },
        R + "indicator",
        "FHPEW02790000",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "20279",
            "FID_UNAS_INPUT_ISCD": "005930",
            "FID_INPUT_ISCD": "00003",
            "FID_DIV_CLS_CODE": "1",
            "FID_INPUT_PRICE_1": "1000",
            "FID_INPUT_PRICE_2": "5000",
            "FID_INPUT_VOL_1": "100",
            "FID_INPUT_VOL_2": "1000",
            "FID_RANK_SORT_CLS_CODE": "1",
            "FID_BLNG_CLS_CODE": "2",
        },
    ),
    (
        ElwRankingAPI,
        "get_elw_quick_change_rank",
        (),
        {},
        R + "quick-change",
        "FHPEW02870000",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "20287",
            "FID_UNAS_INPUT_ISCD": "000000",
            "FID_INPUT_ISCD": "00000",
            "FID_MRKT_CLS_CODE": "A",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_INPUT_VOL_1": "",
            "FID_INPUT_VOL_2": "",
            "FID_HOUR_CLS_CODE": "1",
            "FID_INPUT_HOUR_1": "",
            "FID_INPUT_HOUR_2": "",
            "FID_RANK_SORT_CLS_CODE": "1",
            "FID_BLNG_CLS_CODE": "0",
        },
    ),
    (
        ElwRankingAPI,
        "get_elw_quick_change_rank",
        ("3", "2"),
        {
            "input_hour_1": "10",
            "input_hour_2": "30",
            "underlying": "2001",
            "issuer": "00017",
            "price_min": "100",
            "price_max": "900",
            "volume_min": "5",
            "volume_max": "50",
            "settle_type": "1",
        },
        R + "quick-change",
        "FHPEW02870000",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "20287",
            "FID_UNAS_INPUT_ISCD": "2001",
            "FID_INPUT_ISCD": "00017",
            "FID_MRKT_CLS_CODE": "A",
            "FID_INPUT_PRICE_1": "100",
            "FID_INPUT_PRICE_2": "900",
            "FID_INPUT_VOL_1": "5",
            "FID_INPUT_VOL_2": "50",
            "FID_HOUR_CLS_CODE": "2",
            "FID_INPUT_HOUR_1": "10",
            "FID_INPUT_HOUR_2": "30",
            "FID_RANK_SORT_CLS_CODE": "3",
            "FID_BLNG_CLS_CODE": "1",
        },
    ),
    (
        ElwRankingAPI,
        "get_elw_sensitivity_rank",
        (),
        {},
        R + "sensitivity",
        "FHPEW02850000",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "20285",
            "FID_UNAS_INPUT_ISCD": "000000",
            "FID_INPUT_ISCD": "00000",
            "FID_DIV_CLS_CODE": "0",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_INPUT_VOL_1": "",
            "FID_INPUT_VOL_2": "",
            "FID_RANK_SORT_CLS_CODE": "0",
            "FID_INPUT_RMNN_DYNU_1": "",
            "FID_INPUT_DATE_1": "",
            "FID_BLNG_CLS_CODE": "0",
        },
    ),
    (
        ElwRankingAPI,
        "get_elw_sensitivity_rank",
        ("1",),
        {
            "underlying": "3003",
            "issuer": "00005",
            "call_put": "2",
            "price_min": "1",
            "price_max": "2",
            "volume_min": "3",
            "volume_max": "4",
            "remain_days_min": "5",
            "base_date": "20260401",
            "settle_type": "2",
        },
        R + "sensitivity",
        "FHPEW02850000",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "20285",
            "FID_UNAS_INPUT_ISCD": "3003",
            "FID_INPUT_ISCD": "00005",
            "FID_DIV_CLS_CODE": "2",
            "FID_INPUT_PRICE_1": "1",
            "FID_INPUT_PRICE_2": "2",
            "FID_INPUT_VOL_1": "3",
            "FID_INPUT_VOL_2": "4",
            "FID_RANK_SORT_CLS_CODE": "1",
            "FID_INPUT_RMNN_DYNU_1": "5",
            "FID_INPUT_DATE_1": "20260401",
            "FID_BLNG_CLS_CODE": "2",
        },
    ),
    (
        ElwRankingAPI,
        "get_elw_updown_rate_rank",
        (),
        {},
        R + "updown-rate",
        "FHPEW02770000",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "20277",
            "FID_UNAS_INPUT_ISCD": "000000",
            "FID_INPUT_ISCD": "00000",
            "FID_INPUT_RMNN_DYNU_1": "0",
            "FID_DIV_CLS_CODE": "0",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_INPUT_VOL_1": "",
            "FID_INPUT_VOL_2": "",
            "FID_INPUT_DATE_1": "",
            "FID_RANK_SORT_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_INPUT_DATE_2": "",
        },
    ),
    (
        ElwRankingAPI,
        "get_elw_updown_rate_rank",
        ("1", "3"),
        {"underlying": "005930", "issuer": "00003", "call_put": "2"},
        R + "updown-rate",
        "FHPEW02770000",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "20277",
            "FID_UNAS_INPUT_ISCD": "005930",
            "FID_INPUT_ISCD": "00003",
            "FID_INPUT_RMNN_DYNU_1": "3",
            "FID_DIV_CLS_CODE": "2",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_INPUT_VOL_1": "",
            "FID_INPUT_VOL_2": "",
            "FID_INPUT_DATE_1": "",
            "FID_RANK_SORT_CLS_CODE": "1",
            "FID_BLNG_CLS_CODE": "0",
            "FID_INPUT_DATE_2": "",
        },
    ),
    (
        ElwRankingAPI,
        "get_elw_volume_rank",
        (),
        {},
        R + "volume-rank",
        "FHPEW02780000",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "20278",
            "FID_UNAS_INPUT_ISCD": "000000",
            "FID_INPUT_ISCD": "00000",
            "FID_INPUT_RMNN_DYNU_1": "",
            "FID_DIV_CLS_CODE": "0",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_INPUT_VOL_1": "",
            "FID_INPUT_VOL_2": "",
            "FID_INPUT_DATE_1": "",
            "FID_RANK_SORT_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_INPUT_ISCD_2": "0000",
            "FID_INPUT_DATE_2": "",
        },
    ),
    (
        ElwRankingAPI,
        "get_elw_volume_rank",
        ("3",),
        {
            "underlying": "2001",
            "issuer": "00017",
            "call_put": "1",
            "remain_days": "30",
            "price_min": "10",
            "price_max": "20",
            "volume_min": "30",
            "volume_max": "40",
            "base_date": "20260401",
            "lp_issuer": "00003",
        },
        R + "volume-rank",
        "FHPEW02780000",
        {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "20278",
            "FID_UNAS_INPUT_ISCD": "2001",
            "FID_INPUT_ISCD": "00017",
            "FID_INPUT_RMNN_DYNU_1": "30",
            "FID_DIV_CLS_CODE": "1",
            "FID_INPUT_PRICE_1": "10",
            "FID_INPUT_PRICE_2": "20",
            "FID_INPUT_VOL_1": "30",
            "FID_INPUT_VOL_2": "40",
            "FID_INPUT_DATE_1": "20260401",
            "FID_RANK_SORT_CLS_CODE": "3",
            "FID_BLNG_CLS_CODE": "0",
            "FID_INPUT_ISCD_2": "00003",
            "FID_INPUT_DATE_2": "",
        },
    ),
]


@pytest.mark.parametrize("cls, method, args, kwargs, endpoint, tr_id, params", CASES)
def test_elw_request_matches_spec(cls, method, args, kwargs, endpoint, tr_id, params):
    client = _client()
    result = getattr(_api(cls, client), method)(*args, **kwargs)
    assert result["rt_cd"] == "0"
    assert _sent(client) == {
        "endpoint": endpoint,
        "tr_id": tr_id,
        "params": params,
        "method": "GET",
    }


def test_every_elw_url_is_implemented_once():
    """All 21 official URLs are covered by the cases above (and by no duplicates)."""
    urls = {case[4] for case in CASES}
    assert len(urls) == 21
    assert {u for u in urls if u.startswith(Q)} and len(
        {u for u in urls if u.startswith(R)}
    ) == 5


def test_cond_search_rejects_unknown_filter_without_sending():
    client = _client()
    with pytest.raises(ValueError, match="FID_BOGUS"):
        _api(ElwPriceAPI, client).get_elw_cond_search(filters={"FID_BOGUS": "1"})
    client.make_request.assert_not_called()


def test_elw_methods_reach_the_elw_facade():
    client = _client()
    elw = ElwAPI(
        client,
        {"CANO": "12345678", "ACNT_PRDT_CD": "01"},
        enable_cache=False,
        _from_agent=True,
    )
    elw.get_elw_lp_trade_trend("52K577")
    assert _sent(client)["tr_id"] == "FHPEW03760000"
    assert _sent(client)["params"]["FID_INPUT_ISCD"] == "52K577"
    elw.get_elw_volume_rank("3")
    assert _sent(client)["endpoint"] == R + "volume-rank"
    assert _sent(client)["params"]["FID_RANK_SORT_CLS_CODE"] == "3"
    assert not hasattr(elw, "get_elw_does_not_exist")


def test_elw_apis_propagate_paper_mode_rejection():
    client = _client()
    client.make_request.side_effect = PaperTradingNotSupportedError("FHPEW02780000")
    with pytest.raises(PaperTradingNotSupportedError):
        _api(ElwRankingAPI, client).get_elw_volume_rank()


def test_all_elw_tr_ids_are_literal_keywords():
    """Every request names its tr_id as a literal tr_id= keyword (audited by the spec checker)."""
    for module in (price_module, ranking_module):
        source = Path(inspect.getsourcefile(module)).read_text()
        literals = re.findall(r'tr_id="(FH[A-Z0-9]+)"', source)
        assert len(literals) == len(set(literals))
        assert len(literals) == (16 if module is price_module else 5)


@pytest.mark.parametrize("tr_id", sorted({case[5] for case in CASES}))
def test_no_elw_tr_id_has_a_paper_counterpart(tr_id):
    """ELW is unsupported on paper, including LP매매추이 whose workbook paper cell is blank."""
    assert resolve_tr_id(tr_id, is_real=True) == tr_id
    with pytest.raises(PaperTradingNotSupportedError):
        resolve_tr_id(tr_id, is_real=False)
