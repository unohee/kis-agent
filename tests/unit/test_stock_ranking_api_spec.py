"""Domestic ranking APIs (ranking/*) against the official KIS contract.

Every method is asserted against the official KIS contract (workbook
한국투자증권_오픈API_전체문서_20251212 and open-trading-api examples_llm): endpoint,
TR_ID, HTTP method and the COMPLETE params dict, once with defaults and once with
every keyword argument overridden (proving each argument lands on its own key).
"""

from unittest.mock import MagicMock

import pytest

from kis_agent.stock import ranking_api as ranking_module
from kis_agent.stock.api_facade import StockAPI
from kis_agent.stock.ranking_api import StockRankingAPI

OK = {"rt_cd": "0", "msg1": "ok", "output": []}
ACCOUNT = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
TODAY = "20261008"

CASES = [
    {
        "method": "get_after_hour_balance_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/after-hour-balance",
        "tr_id": "FHPST01760000",
        "default_call": {},
        "default_params": {
            "fid_input_price_1": "",
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20176",
            "fid_rank_sort_cls_code": "1",
            "fid_div_cls_code": "0",
            "fid_input_iscd": "0000",
            "fid_trgt_exls_cls_code": "0",
            "fid_trgt_cls_code": "0",
            "fid_vol_cnt": "",
            "fid_input_price_2": "",
        },
        "override_call": {
            "sort": "v_sort",
            "market": "v_market",
            "index_code": "v_index_code",
            "div_cls": "v_div_cls",
            "target_cls": "v_target_cls",
            "exclude_cls": "v_exclude_cls",
            "price_min": "v_price_min",
            "price_max": "v_price_max",
            "min_volume": "v_min_volume",
        },
        "override_params": {
            "fid_input_price_1": "v_price_min",
            "fid_cond_mrkt_div_code": "v_market",
            "fid_cond_scr_div_code": "20176",
            "fid_rank_sort_cls_code": "v_sort",
            "fid_div_cls_code": "v_div_cls",
            "fid_input_iscd": "v_index_code",
            "fid_trgt_exls_cls_code": "v_exclude_cls",
            "fid_trgt_cls_code": "v_target_cls",
            "fid_vol_cnt": "v_min_volume",
            "fid_input_price_2": "v_price_max",
        },
    },
    {
        "method": "get_bulk_trans_num_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/bulk-trans-num",
        "tr_id": "FHKST190900C0",
        "default_call": {},
        "default_params": {
            "fid_aply_rang_prc_2": "",
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "11909",
            "fid_input_iscd": "0000",
            "fid_rank_sort_cls_code": "0",
            "fid_div_cls_code": "0",
            "fid_input_price_1": "",
            "fid_aply_rang_prc_1": "",
            "fid_input_iscd_2": "",
            "fid_trgt_exls_cls_code": "0",
            "fid_trgt_cls_code": "0",
            "fid_vol_cnt": "",
        },
        "override_call": {
            "sort": "v_sort",
            "market": "v_market",
            "index_code": "v_index_code",
            "div_cls": "v_div_cls",
            "stock_code": "v_stock_code",
            "amount_min": "v_amount_min",
            "price_min": "v_price_min",
            "price_max": "v_price_max",
            "target_cls": "v_target_cls",
            "exclude_cls": "v_exclude_cls",
            "min_volume": "v_min_volume",
        },
        "override_params": {
            "fid_aply_rang_prc_2": "v_price_max",
            "fid_cond_mrkt_div_code": "v_market",
            "fid_cond_scr_div_code": "11909",
            "fid_input_iscd": "v_index_code",
            "fid_rank_sort_cls_code": "v_sort",
            "fid_div_cls_code": "v_div_cls",
            "fid_input_price_1": "v_amount_min",
            "fid_aply_rang_prc_1": "v_price_min",
            "fid_input_iscd_2": "v_stock_code",
            "fid_trgt_exls_cls_code": "v_exclude_cls",
            "fid_trgt_cls_code": "v_target_cls",
            "fid_vol_cnt": "v_min_volume",
        },
    },
    {
        "method": "get_credit_balance_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/credit-balance",
        "tr_id": "FHKST17010000",
        "default_call": {},
        "default_params": {
            "FID_COND_SCR_DIV_CODE": "11701",
            "FID_INPUT_ISCD": "0000",
            "FID_OPTION": "2",
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_RANK_SORT_CLS_CODE": "0",
        },
        "override_call": {
            "sort": "v_sort",
            "period": "v_period",
            "market": "v_market",
            "index_code": "v_index_code",
        },
        "override_params": {
            "FID_COND_SCR_DIV_CODE": "11701",
            "FID_INPUT_ISCD": "v_index_code",
            "FID_OPTION": "v_period",
            "FID_COND_MRKT_DIV_CODE": "v_market",
            "FID_RANK_SORT_CLS_CODE": "v_sort",
        },
    },
    {
        "method": "get_exp_trans_updown_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/exp-trans-updown",
        "tr_id": "FHPST01820000",
        "default_call": {},
        "default_params": {
            "fid_rank_sort_cls_code": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20182",
            "fid_input_iscd": "0000",
            "fid_div_cls_code": "0",
            "fid_aply_rang_prc_1": "",
            "fid_vol_cnt": "",
            "fid_pbmn": "",
            "fid_blng_cls_code": "0",
            "fid_mkop_cls_code": "0",
        },
        "override_call": {
            "sort": "v_sort",
            "market": "v_market",
            "index_code": "v_index_code",
            "div_cls": "v_div_cls",
            "price_min": "v_price_min",
            "min_volume": "v_min_volume",
            "min_amount": "v_min_amount",
            "belong_cls": "v_belong_cls",
            "session": "v_session",
        },
        "override_params": {
            "fid_rank_sort_cls_code": "v_sort",
            "fid_cond_mrkt_div_code": "v_market",
            "fid_cond_scr_div_code": "20182",
            "fid_input_iscd": "v_index_code",
            "fid_div_cls_code": "v_div_cls",
            "fid_aply_rang_prc_1": "v_price_min",
            "fid_vol_cnt": "v_min_volume",
            "fid_pbmn": "v_min_amount",
            "fid_blng_cls_code": "v_belong_cls",
            "fid_mkop_cls_code": "v_session",
        },
    },
    {
        "method": "get_finance_ratio_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/finance-ratio",
        "tr_id": "FHPST01750000",
        "default_call": {},
        "default_params": {
            "fid_trgt_cls_code": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20175",
            "fid_input_iscd": "0000",
            "fid_div_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "",
            "fid_input_option_1": "2025",
            "fid_input_option_2": "3",
            "fid_rank_sort_cls_code": "7",
            "fid_blng_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
        },
        "override_call": {
            "sort": "v_sort",
            "fiscal_year": "v_fiscal_year",
            "fiscal_period": "v_fiscal_period",
            "market": "v_market",
            "index_code": "v_index_code",
            "div_cls": "v_div_cls",
            "target_cls": "v_target_cls",
            "exclude_cls": "v_exclude_cls",
            "price_min": "v_price_min",
            "price_max": "v_price_max",
            "min_volume": "v_min_volume",
            "belong_cls": "v_belong_cls",
        },
        "override_params": {
            "fid_trgt_cls_code": "v_target_cls",
            "fid_cond_mrkt_div_code": "v_market",
            "fid_cond_scr_div_code": "20175",
            "fid_input_iscd": "v_index_code",
            "fid_div_cls_code": "v_div_cls",
            "fid_input_price_1": "v_price_min",
            "fid_input_price_2": "v_price_max",
            "fid_vol_cnt": "v_min_volume",
            "fid_input_option_1": "v_fiscal_year",
            "fid_input_option_2": "v_fiscal_period",
            "fid_rank_sort_cls_code": "v_sort",
            "fid_blng_cls_code": "v_belong_cls",
            "fid_trgt_exls_cls_code": "v_exclude_cls",
        },
    },
    {
        "method": "get_hts_top_view_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/hts-top-view",
        "tr_id": "HHMCM000100C0",
        "default_call": {},
        "default_params": {},
        "override_call": {},
        "override_params": {},
    },
    {
        "method": "get_market_value_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/market-value",
        "tr_id": "FHPST01790000",
        "default_call": {},
        "default_params": {
            "fid_trgt_cls_code": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20179",
            "fid_input_iscd": "0000",
            "fid_div_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "",
            "fid_input_option_1": "2025",
            "fid_input_option_2": "0",
            "fid_rank_sort_cls_code": "23",
            "fid_blng_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
        },
        "override_call": {
            "sort": "v_sort",
            "fiscal_year": "v_fiscal_year",
            "fiscal_period": "v_fiscal_period",
            "market": "v_market",
            "index_code": "v_index_code",
            "div_cls": "v_div_cls",
            "target_cls": "v_target_cls",
            "exclude_cls": "v_exclude_cls",
            "price_min": "v_price_min",
            "price_max": "v_price_max",
            "min_volume": "v_min_volume",
            "belong_cls": "v_belong_cls",
        },
        "override_params": {
            "fid_trgt_cls_code": "v_target_cls",
            "fid_cond_mrkt_div_code": "v_market",
            "fid_cond_scr_div_code": "20179",
            "fid_input_iscd": "v_index_code",
            "fid_div_cls_code": "v_div_cls",
            "fid_input_price_1": "v_price_min",
            "fid_input_price_2": "v_price_max",
            "fid_vol_cnt": "v_min_volume",
            "fid_input_option_1": "v_fiscal_year",
            "fid_input_option_2": "v_fiscal_period",
            "fid_rank_sort_cls_code": "v_sort",
            "fid_blng_cls_code": "v_belong_cls",
            "fid_trgt_exls_cls_code": "v_exclude_cls",
        },
    },
    {
        "method": "get_near_new_highlow_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/near-new-highlow",
        "tr_id": "FHPST01870000",
        "default_call": {},
        "default_params": {
            "fid_aply_rang_vol": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20187",
            "fid_div_cls_code": "0",
            "fid_input_cnt_1": "0",
            "fid_input_cnt_2": "100",
            "fid_prc_cls_code": "0",
            "fid_input_iscd": "0000",
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
            "fid_aply_rang_prc_1": "",
            "fid_aply_rang_prc_2": "",
        },
        "override_call": {
            "price_cls": "v_price_cls",
            "market": "v_market",
            "index_code": "v_index_code",
            "div_cls": "v_div_cls",
            "gap_min": "v_gap_min",
            "gap_max": "v_gap_max",
            "min_volume": "v_min_volume",
            "target_cls": "v_target_cls",
            "exclude_cls": "v_exclude_cls",
            "price_min": "v_price_min",
            "price_max": "v_price_max",
        },
        "override_params": {
            "fid_aply_rang_vol": "v_min_volume",
            "fid_cond_mrkt_div_code": "v_market",
            "fid_cond_scr_div_code": "20187",
            "fid_div_cls_code": "v_div_cls",
            "fid_input_cnt_1": "v_gap_min",
            "fid_input_cnt_2": "v_gap_max",
            "fid_prc_cls_code": "v_price_cls",
            "fid_input_iscd": "v_index_code",
            "fid_trgt_cls_code": "v_target_cls",
            "fid_trgt_exls_cls_code": "v_exclude_cls",
            "fid_aply_rang_prc_1": "v_price_min",
            "fid_aply_rang_prc_2": "v_price_max",
        },
    },
    {
        "method": "get_overtime_exp_trans_fluct_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/overtime-exp-trans-fluct",
        "tr_id": "FHKST11860000",
        "default_call": {},
        "default_params": {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "11186",
            "FID_INPUT_ISCD": "0000",
            "FID_RANK_SORT_CLS_CODE": "0",
            "FID_DIV_CLS_CODE": "0",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_INPUT_VOL_1": "",
        },
        "override_call": {
            "sort": "v_sort",
            "market": "v_market",
            "index_code": "v_index_code",
            "div_cls": "v_div_cls",
            "price_min": "v_price_min",
            "min_volume": "v_min_volume",
        },
        "override_params": {
            "FID_COND_MRKT_DIV_CODE": "v_market",
            "FID_COND_SCR_DIV_CODE": "11186",
            "FID_INPUT_ISCD": "v_index_code",
            "FID_RANK_SORT_CLS_CODE": "v_sort",
            "FID_DIV_CLS_CODE": "v_div_cls",
            "FID_INPUT_PRICE_1": "v_price_min",
            "FID_INPUT_PRICE_2": "",
            "FID_INPUT_VOL_1": "v_min_volume",
        },
    },
    {
        "method": "get_overtime_fluctuation_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/overtime-fluctuation",
        "tr_id": "FHPST02340000",
        "default_call": {},
        "default_params": {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_MRKT_CLS_CODE": "",
            "FID_COND_SCR_DIV_CODE": "20234",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": "2",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
            "FID_TRGT_CLS_CODE": "",
            "FID_TRGT_EXLS_CLS_CODE": "",
        },
        "override_call": {
            "div_cls": "v_div_cls",
            "market": "v_market",
            "index_code": "v_index_code",
            "price_min": "v_price_min",
            "price_max": "v_price_max",
            "min_volume": "v_min_volume",
        },
        "override_params": {
            "FID_COND_MRKT_DIV_CODE": "v_market",
            "FID_MRKT_CLS_CODE": "",
            "FID_COND_SCR_DIV_CODE": "20234",
            "FID_INPUT_ISCD": "v_index_code",
            "FID_DIV_CLS_CODE": "v_div_cls",
            "FID_INPUT_PRICE_1": "v_price_min",
            "FID_INPUT_PRICE_2": "v_price_max",
            "FID_VOL_CNT": "v_min_volume",
            "FID_TRGT_CLS_CODE": "",
            "FID_TRGT_EXLS_CLS_CODE": "",
        },
    },
    {
        "method": "get_overtime_volume_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/overtime-volume",
        "tr_id": "FHPST02350000",
        "default_call": {},
        "default_params": {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "20235",
            "FID_INPUT_ISCD": "0000",
            "FID_RANK_SORT_CLS_CODE": "2",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
            "FID_TRGT_CLS_CODE": "",
            "FID_TRGT_EXLS_CLS_CODE": "",
        },
        "override_call": {
            "sort": "v_sort",
            "market": "v_market",
            "index_code": "v_index_code",
            "price_min": "v_price_min",
            "price_max": "v_price_max",
            "min_volume": "v_min_volume",
        },
        "override_params": {
            "FID_COND_MRKT_DIV_CODE": "v_market",
            "FID_COND_SCR_DIV_CODE": "20235",
            "FID_INPUT_ISCD": "v_index_code",
            "FID_RANK_SORT_CLS_CODE": "v_sort",
            "FID_INPUT_PRICE_1": "v_price_min",
            "FID_INPUT_PRICE_2": "v_price_max",
            "FID_VOL_CNT": "v_min_volume",
            "FID_TRGT_CLS_CODE": "",
            "FID_TRGT_EXLS_CLS_CODE": "",
        },
    },
    {
        "method": "get_prefer_disparate_ratio_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/prefer-disparate-ratio",
        "tr_id": "FHPST01770000",
        "default_call": {},
        "default_params": {
            "fid_vol_cnt": "",
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20177",
            "fid_div_cls_code": "0",
            "fid_input_iscd": "0000",
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
        },
        "override_call": {
            "market": "v_market",
            "index_code": "v_index_code",
            "div_cls": "v_div_cls",
            "target_cls": "v_target_cls",
            "exclude_cls": "v_exclude_cls",
            "price_min": "v_price_min",
            "price_max": "v_price_max",
            "min_volume": "v_min_volume",
        },
        "override_params": {
            "fid_vol_cnt": "v_min_volume",
            "fid_cond_mrkt_div_code": "v_market",
            "fid_cond_scr_div_code": "20177",
            "fid_div_cls_code": "v_div_cls",
            "fid_input_iscd": "v_index_code",
            "fid_trgt_cls_code": "v_target_cls",
            "fid_trgt_exls_cls_code": "v_exclude_cls",
            "fid_input_price_1": "v_price_min",
            "fid_input_price_2": "v_price_max",
        },
    },
    {
        "method": "get_profit_asset_index_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/profit-asset-index",
        "tr_id": "FHPST01730000",
        "default_call": {},
        "default_params": {
            "fid_cond_mrkt_div_code": "J",
            "fid_trgt_cls_code": "0",
            "fid_cond_scr_div_code": "20173",
            "fid_input_iscd": "0000",
            "fid_div_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "",
            "fid_input_option_1": "2025",
            "fid_input_option_2": "0",
            "fid_rank_sort_cls_code": "0",
            "fid_blng_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
        },
        "override_call": {
            "sort": "v_sort",
            "fiscal_year": "v_fiscal_year",
            "fiscal_period": "v_fiscal_period",
            "market": "v_market",
            "index_code": "v_index_code",
            "div_cls": "v_div_cls",
            "target_cls": "v_target_cls",
            "exclude_cls": "v_exclude_cls",
            "price_min": "v_price_min",
            "price_max": "v_price_max",
            "min_volume": "v_min_volume",
            "belong_cls": "v_belong_cls",
        },
        "override_params": {
            "fid_cond_mrkt_div_code": "v_market",
            "fid_trgt_cls_code": "v_target_cls",
            "fid_cond_scr_div_code": "20173",
            "fid_input_iscd": "v_index_code",
            "fid_div_cls_code": "v_div_cls",
            "fid_input_price_1": "v_price_min",
            "fid_input_price_2": "v_price_max",
            "fid_vol_cnt": "v_min_volume",
            "fid_input_option_1": "v_fiscal_year",
            "fid_input_option_2": "v_fiscal_period",
            "fid_rank_sort_cls_code": "v_sort",
            "fid_blng_cls_code": "v_belong_cls",
            "fid_trgt_exls_cls_code": "v_exclude_cls",
        },
    },
    {
        "method": "get_quote_balance_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/quote-balance",
        "tr_id": "FHPST01720000",
        "default_call": {},
        "default_params": {
            "fid_vol_cnt": "",
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20172",
            "fid_input_iscd": "0000",
            "fid_rank_sort_cls_code": "0",
            "fid_div_cls_code": "0",
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
        },
        "override_call": {
            "sort": "v_sort",
            "market": "v_market",
            "index_code": "v_index_code",
            "div_cls": "v_div_cls",
            "target_cls": "v_target_cls",
            "exclude_cls": "v_exclude_cls",
            "price_min": "v_price_min",
            "price_max": "v_price_max",
            "min_volume": "v_min_volume",
        },
        "override_params": {
            "fid_vol_cnt": "v_min_volume",
            "fid_cond_mrkt_div_code": "v_market",
            "fid_cond_scr_div_code": "20172",
            "fid_input_iscd": "v_index_code",
            "fid_rank_sort_cls_code": "v_sort",
            "fid_div_cls_code": "v_div_cls",
            "fid_trgt_cls_code": "v_target_cls",
            "fid_trgt_exls_cls_code": "v_exclude_cls",
            "fid_input_price_1": "v_price_min",
            "fid_input_price_2": "v_price_max",
        },
    },
    {
        "method": "get_top_interest_stock_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/top-interest-stock",
        "tr_id": "FHPST01800000",
        "default_call": {},
        "default_params": {
            "fid_input_iscd_2": "000000",
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20180",
            "fid_input_iscd": "0000",
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "",
            "fid_div_cls_code": "0",
            "fid_input_cnt_1": "1",
        },
        "override_call": {
            "market": "v_market",
            "index_code": "v_index_code",
            "div_cls": "v_div_cls",
            "target_cls": "v_target_cls",
            "exclude_cls": "v_exclude_cls",
            "price_min": "v_price_min",
            "price_max": "v_price_max",
            "min_volume": "v_min_volume",
            "start_rank": "v_start_rank",
        },
        "override_params": {
            "fid_input_iscd_2": "000000",
            "fid_cond_mrkt_div_code": "v_market",
            "fid_cond_scr_div_code": "20180",
            "fid_input_iscd": "v_index_code",
            "fid_trgt_cls_code": "v_target_cls",
            "fid_trgt_exls_cls_code": "v_exclude_cls",
            "fid_input_price_1": "v_price_min",
            "fid_input_price_2": "v_price_max",
            "fid_vol_cnt": "v_min_volume",
            "fid_div_cls_code": "v_div_cls",
            "fid_input_cnt_1": "v_start_rank",
        },
    },
    {
        "method": "get_traded_by_company_rank",
        "endpoint": "/uapi/domestic-stock/v1/ranking/traded-by-company",
        "tr_id": "FHPST01860000",
        "default_call": {},
        "default_params": {
            "fid_trgt_exls_cls_code": "0",
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20186",
            "fid_div_cls_code": "0",
            "fid_rank_sort_cls_code": "1",
            "fid_input_date_1": "20261008",
            "fid_input_date_2": "20261008",
            "fid_input_iscd": "0000",
            "fid_trgt_cls_code": "0",
            "fid_aply_rang_vol": "0",
            "fid_aply_rang_prc_2": "",
            "fid_aply_rang_prc_1": "",
        },
        "override_call": {
            "sort": "v_sort",
            "start_date": "v_start_date",
            "end_date": "v_end_date",
            "market": "v_market",
            "index_code": "v_index_code",
            "div_cls": "v_div_cls",
            "target_cls": "v_target_cls",
            "exclude_cls": "v_exclude_cls",
            "min_volume": "v_min_volume",
            "price_min": "v_price_min",
            "price_max": "v_price_max",
        },
        "override_params": {
            "fid_trgt_exls_cls_code": "v_exclude_cls",
            "fid_cond_mrkt_div_code": "v_market",
            "fid_cond_scr_div_code": "20186",
            "fid_div_cls_code": "v_div_cls",
            "fid_rank_sort_cls_code": "v_sort",
            "fid_input_date_1": "v_start_date",
            "fid_input_date_2": "v_end_date",
            "fid_input_iscd": "v_index_code",
            "fid_trgt_cls_code": "v_target_cls",
            "fid_aply_rang_vol": "v_min_volume",
            "fid_aply_rang_prc_2": "v_price_max",
            "fid_aply_rang_prc_1": "v_price_min",
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
    monkeypatch.setattr(ranking_module, "_today", lambda: TODAY)
    api, client = _api(StockRankingAPI)
    assert getattr(api, case["method"])(**case["default_call"]) == OK
    assert _sent(client) == {
        "endpoint": case["endpoint"],
        "tr_id": case["tr_id"],
        "params": case["default_params"],
        "method": "GET",
    }


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_every_argument_reaches_its_own_key(case, monkeypatch):
    monkeypatch.setattr(ranking_module, "_today", lambda: TODAY)
    api, client = _api(StockRankingAPI)
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

    source = inspect.getsource(getattr(StockRankingAPI, case["method"]))
    assert f'tr_id="{case["tr_id"]}"' in source
    assert case["endpoint"] in source


def test_fiscal_year_defaults_to_last_year_and_dates_to_today(monkeypatch):
    monkeypatch.setattr(ranking_module, "_today", lambda: "20270105")
    api, client = _api(StockRankingAPI)
    api.get_finance_ratio_rank()
    assert _sent(client)["params"]["fid_input_option_1"] == "2026"
    client.make_request.reset_mock()
    api.get_traded_by_company_rank()
    params = _sent(client)["params"]
    assert (params["fid_input_date_1"], params["fid_input_date_2"]) == (
        "20270105",
        "20270105",
    )


def test_today_helper_is_yyyymmdd():
    assert len(ranking_module._today()) == 8 and ranking_module._today().isdigit()


def test_hts_top_view_sends_no_params():
    api, client = _api(StockRankingAPI)
    api.get_hts_top_view_rank()
    assert _sent(client)["params"] == {}


def test_ranking_methods_are_reachable_through_the_stock_facade():
    client = MagicMock()
    client.make_request.return_value = dict(OK)
    stock = StockAPI(client, _from_agent=True)
    assert stock.get_quote_balance_rank(sort="2", index_code="0001") == OK
    assert _sent(client)["tr_id"] == "FHPST01720000"
    client.make_request.reset_mock()
    stock.get_overtime_volume_rank()
    assert _sent(client)["endpoint"].endswith("/ranking/overtime-volume")
    client.make_request.reset_mock()
    stock.get_hts_top_view_rank()
    assert _sent(client)["tr_id"] == "HHMCM000100C0"


def test_ranking_calls_are_cached_per_parameter_set_by_default():
    client = MagicMock()
    client.make_request.return_value = dict(OK)
    api = StockRankingAPI(client, dict(ACCOUNT), enable_cache=True, _from_agent=True)
    api.get_quote_balance_rank()
    api.get_quote_balance_rank()
    assert client.make_request.call_count == 1
    api.get_quote_balance_rank(sort="1")
    assert client.make_request.call_count == 2


def test_paper_trading_error_propagates():
    from kis_agent.core.tr_mapping import PaperTradingNotSupportedError

    client = MagicMock()
    client.make_request.side_effect = PaperTradingNotSupportedError("FHPST01720000")
    api = StockRankingAPI(client, dict(ACCOUNT), enable_cache=False, _from_agent=True)
    with pytest.raises(PaperTradingNotSupportedError):
        api.get_quote_balance_rank()
