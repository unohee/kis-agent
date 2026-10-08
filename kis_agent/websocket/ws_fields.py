"""Official realtime (WebSocket) column layouts, keyed by TR_ID.

Generated from the KIS OpenAPI workbook (2025-12-12) and the open-trading-api
samples by ``scripts/spec_conformance`` rules: the workbook wins, except where a
sample committed after the workbook only appends columns (e.g. market_cls_code).
Futures/options feeds are not listed (out of scope).

Each value is the space-separated, lower-cased column list in frame order.
Verify with ``python scripts/spec_conformance/check.py``.
"""

from typing import Dict, Tuple

_LAYOUTS: Dict[str, str] = {
    # workbook:채권지수 실시간체결가
    "H0BICNT0": (
        "nmix_id stnd_date1 trnm_hour totl_ernn_nmix_oprc totl_ernn_nmix_hgpr "
        "totl_ernn_nmix_lwpr totl_ernn_nmix prdy_totl_ernn_nmix "
        "totl_ernn_nmix_prdy_vrss totl_ernn_nmix_prdy_vrss_sign "
        "totl_ernn_nmix_prdy_ctrt clen_prc_nmix mrkt_prc_nmix bond_call_rnvs_nmix "
        "bond_zero_rnvs_nmix bond_futs_thpr bond_avrg_drtn_val bond_avrg_cnvx_val "
        "bond_avrg_ytm_val bond_avrg_frdl_ytm_val"
    ),
    # workbook:일반채권 실시간호가
    "H0BJASP0": (
        "stnd_iscd stck_cntg_hour askp_ert1 bidp_ert1 askp1 bidp1 askp_rsqn1 "
        "bidp_rsqn1 askp_ert2 bidp_ert2 askp2 bidp2 askp_rsqn2 bidp_rsqn2 askp_ert3 "
        "bidp_ert3 askp3 bidp3 askp_rsqn3 bidp_rsqn3 askp_ert4 bidp_ert4 askp4 "
        "bidp4 askp_rsqn4 bidp_rsqn4 askp_ert5 bidp_ert5 askp5 bidp5 askp_rsqn52 "
        "bidp_rsqn53 total_askp_rsqn total_bidp_rsqn"
    ),
    # workbook:일반채권 실시간체결가
    "H0BJCNT0": (
        "stnd_iscd bond_isnm stck_cntg_hour prdy_vrss_sign prdy_vrss prdy_ctrt "
        "stck_prpr cntg_vol stck_oprc stck_hgpr stck_lwpr stck_prdy_clpr "
        "bond_cntg_ert oprc_ert hgpr_ert lwpr_ert acml_vol prdy_vol "
        "cntg_type_cls_code"
    ),
    # workbook:ELW 실시간예상체결
    "H0EWANC0": (
        "mksc_shrn_iscd stck_cntg_hour stck_prpr prdy_vrss_sign prdy_vrss prdy_ctrt "
        "wghn_avrg_stck_prc stck_oprc stck_hgpr stck_lwpr askp1 bidp1 cntg_vol "
        "acml_vol acml_tr_pbmn seln_cntg_csnu shnu_cntg_csnu ntby_cntg_csnu cttr "
        "seln_cntg_smtn shnu_cntg_smtn cntg_cls_code shnu_rate "
        "prdy_vol_vrss_acml_vol_rate oprc_hour oprc_vrss_prpr_sign oprc_vrss_prpr "
        "hgpr_hour hgpr_vrss_prpr_sign hgpr_vrss_prpr lwpr_hour lwpr_vrss_prpr_sign "
        "lwpr_vrss_prpr bsop_date new_mkop_cls_code trht_yn askp_rsqn1 bidp_rsqn1 "
        "total_askp_rsqn total_bidp_rsqn tmvl_val prit prmm_val gear prls_qryr_rate "
        "invl_val prmm_rate cfp lvrg_val delta gama vega theta rho hts_ints_vltl "
        "hts_thpr vol_tnrt lp_hvol lp_hldn_rate"
    ),
    # workbook:ELW 실시간호가
    "H0EWASP0": (
        "mksc_shrn_iscd bsop_hour hour_cls_code askp1 askp2 askp3 askp4 askp5 askp6 "
        "askp7 askp8 askp9 askp10 bidp1 bidp2 bidp3 bidp4 bidp5 bidp6 bidp7 bidp8 "
        "bidp9 bidp10 askp_rsqn1 askp_rsqn2 askp_rsqn3 askp_rsqn4 askp_rsqn5 "
        "askp_rsqn6 askp_rsqn7 askp_rsqn8 askp_rsqn9 askp_rsqn10 bidp_rsqn1 "
        "bidp_rsqn2 bidp_rsqn3 bidp_rsqn4 bidp_rsqn5 bidp_rsqn6 bidp_rsqn7 "
        "bidp_rsqn8 bidp_rsqn9 bidp_rsqn10 total_askp_rsqn total_bidp_rsqn "
        "antc_cnpr antc_cnqn antc_cntg_vrss_sign antc_cntg_vrss antc_cntg_prdy_ctrt "
        "lp_askp_rsqn1 lp_askp_rsqn2 lp_askp_rsqn3 lp_bidp_rsqn4 lp_askp_rsqn4 "
        "lp_bidp_rsqn5 lp_askp_rsqn5 lp_bidp_rsqn6 lp_askp_rsqn6 lp_bidp_rsqn7 "
        "lp_askp_rsqn7 lp_askp_rsqn8 lp_bidp_rsqn8 lp_askp_rsqn9 lp_bidp_rsqn9 "
        "lp_askp_rsqn10 lp_bidp_rsqn10 lp_bidp_rsqn1 lp_total_askp_rsqn "
        "lp_bidp_rsqn2 lp_total_bidp_rsqn lp_bidp_rsqn3 antc_vol"
    ),
    # workbook:ELW 실시간체결가
    "H0EWCNT0": (
        "mksc_shrn_iscd stck_cntg_hour stck_prpr prdy_vrss_sign prdy_vrss prdy_ctrt "
        "wghn_avrg_stck_prc stck_oprc stck_hgpr stck_lwpr askp1 bidp1 cntg_vol "
        "acml_vol acml_tr_pbmn seln_cntg_csnu shnu_cntg_csnu ntby_cntg_csnu cttr "
        "seln_cntg_smtn shnu_cntg_smtn cntg_cls_code shnu_rate "
        "prdy_vol_vrss_acml_vol_rate oprc_hour oprc_vrss_prpr_sign oprc_vrss_prpr "
        "hgpr_hour hgpr_vrss_prpr_sign hgpr_vrss_prpr lwpr_hour lwpr_vrss_prpr_sign "
        "lwpr_vrss_prpr bsop_date new_mkop_cls_code trht_yn askp_rsqn1 bidp_rsqn1 "
        "total_askp_rsqn total_bidp_rsqn tmvl_val prit prmm_val gear prls_qryr_rate "
        "invl_val prmm_rate cfp lvrg_val delta gama vega theta rho hts_ints_vltl "
        "hts_thpr vol_tnrt prdy_smns_hour_acml_vol prdy_smns_hour_acml_vol_rate "
        "apprch_rate lp_hvol lp_hldn_rate lp_ntby_qty"
    ),
    # examples_llm/overseas_stock/ccnl_notice/ccnl_notice.py
    "H0GSCNI0": (
        "cust_id acnt_no oder_no ooder_no seln_byov_cls rctf_cls oder_kind2 "
        "stck_shrn_iscd cntg_qty cntg_unpr stck_cntg_hour rfus_yn cntg_yn acpt_yn "
        "brnc_no oder_qty acnt_name cntg_isnm oder_cond debt_gb debt_date start_tm "
        "end_tm tm_div_tp cntg_unpr12"
    ),
    # examples_llm/overseas_stock/ccnl_notice/ccnl_notice.py
    "H0GSCNI9": (
        "cust_id acnt_no oder_no ooder_no seln_byov_cls rctf_cls oder_kind2 "
        "stck_shrn_iscd cntg_qty cntg_unpr stck_cntg_hour rfus_yn cntg_yn acpt_yn "
        "brnc_no oder_qty acnt_name cntg_isnm oder_cond debt_gb debt_date start_tm "
        "end_tm tm_div_tp cntg_unpr12"
    ),
    # workbook:국내주식 실시간예상체결 (NXT)
    "H0NXANC0": (
        "mksc_shrn_iscd stck_cntg_hour stck_prpr prdy_vrss_sign prdy_vrss prdy_ctrt "
        "wghn_avrg_stck_prc stck_oprc stck_hgpr stck_lwpr askp1 bidp1 cntg_vol "
        "acml_vol acml_tr_pbmn seln_cntg_csnu shnu_cntg_csnu ntby_cntg_csnu cttr "
        "seln_cntg_smtn shnu_cntg_smtn cntg_cls_code shnu_rate "
        "prdy_vol_vrss_acml_vol_rate oprc_hour oprc_vrss_prpr_sign oprc_vrss_prpr "
        "hgpr_hour hgpr_vrss_prpr_sign hgpr_vrss_prpr lwpr_hour lwpr_vrss_prpr_sign "
        "lwpr_vrss_prpr bsop_date new_mkop_cls_code trht_yn askp_rsqn1 bidp_rsqn1 "
        "total_askp_rsqn total_bidp_rsqn vol_tnrt prdy_smns_hour_acml_vol "
        "prdy_smns_hour_acml_vol_rate hour_cls_code mrkt_trtm_cls_code vi_stnd_prc"
    ),
    # workbook:국내주식 실시간호가 (NXT)
    "H0NXASP0": (
        "mksc_shrn_iscd bsop_hour hour_cls_code askp1 askp2 askp3 askp4 askp5 askp6 "
        "askp7 askp8 askp9 askp10 bidp1 bidp2 bidp3 bidp4 bidp5 bidp6 bidp7 bidp8 "
        "bidp9 bidp10 askp_rsqn1 askp_rsqn2 askp_rsqn3 askp_rsqn4 askp_rsqn5 "
        "askp_rsqn6 askp_rsqn7 askp_rsqn8 askp_rsqn9 askp_rsqn10 bidp_rsqn1 "
        "bidp_rsqn2 bidp_rsqn3 bidp_rsqn4 bidp_rsqn5 bidp_rsqn6 bidp_rsqn7 "
        "bidp_rsqn8 bidp_rsqn9 bidp_rsqn10 total_askp_rsqn total_bidp_rsqn "
        "ovtm_total_askp_rsqn ovtm_total_bidp_rsqn antc_cnpr antc_cnqn antc_vol "
        "antc_cntg_vrss antc_cntg_vrss_sign antc_cntg_prdy_ctrt acml_vol "
        "total_askp_rsqn_icdc total_bidp_rsqn_icdc ovtm_total_askp_icdc "
        "ovtm_total_bidp_icdc stck_deal_cls_code kmid_prc kmid_total_rsqn "
        "kmid_cls_code nmid_prc nmid_total_rsqn nmid_cls_code"
    ),
    # examples_llm/domestic_stock/ccnl_nxt/ccnl_nxt.py
    "H0NXCNT0": (
        "mksc_shrn_iscd stck_cntg_hour stck_prpr prdy_vrss_sign prdy_vrss prdy_ctrt "
        "wghn_avrg_stck_prc stck_oprc stck_hgpr stck_lwpr askp1 bidp1 cntg_vol "
        "acml_vol acml_tr_pbmn seln_cntg_csnu shnu_cntg_csnu ntby_cntg_csnu cttr "
        "seln_cntg_smtn shnu_cntg_smtn cntg_cls_code shnu_rate "
        "prdy_vol_vrss_acml_vol_rate oprc_hour oprc_vrss_prpr_sign oprc_vrss_prpr "
        "hgpr_hour hgpr_vrss_prpr_sign hgpr_vrss_prpr lwpr_hour lwpr_vrss_prpr_sign "
        "lwpr_vrss_prpr bsop_date new_mkop_cls_code trht_yn askp_rsqn1 bidp_rsqn1 "
        "total_askp_rsqn total_bidp_rsqn vol_tnrt prdy_smns_hour_acml_vol "
        "prdy_smns_hour_acml_vol_rate hour_cls_code mrkt_trtm_cls_code vi_stnd_prc "
        "market_cls_code"
    ),
    # workbook:국내주식 실시간회원사 (NXT)
    "H0NXMBC0": (
        "mksc_shrn_iscd seln2_mbcr_name1 seln2_mbcr_name2 seln2_mbcr_name3 "
        "seln2_mbcr_name4 seln2_mbcr_name5 byov_mbcr_name1 byov_mbcr_name2 "
        "byov_mbcr_name3 byov_mbcr_name4 byov_mbcr_name5 total_seln_qty1 "
        "total_seln_qty2 total_seln_qty3 total_seln_qty4 total_seln_qty5 "
        "total_shnu_qty1 total_shnu_qty2 total_shnu_qty3 total_shnu_qty4 "
        "total_shnu_qty5 seln_mbcr_glob_yn_1 seln_mbcr_glob_yn_2 "
        "seln_mbcr_glob_yn_3 seln_mbcr_glob_yn_4 seln_mbcr_glob_yn_5 "
        "shnu_mbcr_glob_yn_1 shnu_mbcr_glob_yn_2 shnu_mbcr_glob_yn_3 "
        "shnu_mbcr_glob_yn_4 shnu_mbcr_glob_yn_5 seln_mbcr_no1 seln_mbcr_no2 "
        "seln_mbcr_no3 seln_mbcr_no4 seln_mbcr_no5 shnu_mbcr_no1 shnu_mbcr_no2 "
        "shnu_mbcr_no3 shnu_mbcr_no4 shnu_mbcr_no5 seln_mbcr_rlim1 seln_mbcr_rlim2 "
        "seln_mbcr_rlim3 seln_mbcr_rlim4 seln_mbcr_rlim5 shnu_mbcr_rlim1 "
        "shnu_mbcr_rlim2 shnu_mbcr_rlim3 shnu_mbcr_rlim4 shnu_mbcr_rlim5 "
        "seln_qty_icdc1 seln_qty_icdc2 seln_qty_icdc3 seln_qty_icdc4 seln_qty_icdc5 "
        "shnu_qty_icdc1 shnu_qty_icdc2 shnu_qty_icdc3 shnu_qty_icdc4 shnu_qty_icdc5 "
        "glob_total_seln_qty glob_total_shnu_qty glob_total_seln_qty_icdc "
        "glob_total_shnu_qty_icdc glob_ntby_qty glob_seln_rlim glob_shnu_rlim "
        "seln2_mbcr_eng_name1 seln2_mbcr_eng_name2 seln2_mbcr_eng_name3 "
        "seln2_mbcr_eng_name4 seln2_mbcr_eng_name5 byov_mbcr_eng_name1 "
        "byov_mbcr_eng_name2 byov_mbcr_eng_name3 byov_mbcr_eng_name4 "
        "byov_mbcr_eng_name5"
    ),
    # workbook:국내주식 장운영정보 (NXT)
    "H0NXMKO0": (
        "mksc_shrn_iscd trht_yn tr_susp_reas_cntt mkop_cls_code antc_mkop_cls_code "
        "mrkt_trtm_cls_code divi_app_cls_code iscd_stat_cls_code vi_cls_code "
        "ovtm_vi_cls_code exch_cls_code"
    ),
    # workbook:국내주식 실시간프로그램매매 (NXT)
    "H0NXPGM0": (
        "mksc_shrn_iscd stck_cntg_hour seln_cnqn seln_tr_pbmn shnu_cnqn "
        "shnu_tr_pbmn ntby_cnqn ntby_tr_pbmn seln_rsqn shnu_rsqn whol_ntby_qty"
    ),
    # workbook:국내주식 실시간예상체결 (KRX)
    "H0STANC0": (
        "mksc_shrn_iscd stck_cntg_hour stck_prpr prdy_vrss_sign prdy_vrss prdy_ctrt "
        "wghn_avrg_stck_prc stck_oprc stck_hgpr stck_lwpr askp1 bidp1 cntg_vol "
        "acml_vol acml_tr_pbmn seln_cntg_csnu shnu_cntg_csnu ntby_cntg_csnu cttr "
        "seln_cntg_smtn shnu_cntg_smtn cntg_cls_code shnu_rate "
        "prdy_vol_vrss_acml_vol_rate oprc_hour oprc_vrss_prpr_sign oprc_vrss_prpr "
        "hgpr_hour hgpr_vrss_prpr_sign hgpr_vrss_prpr lwpr_hour lwpr_vrss_prpr_sign "
        "lwpr_vrss_prpr bsop_date new_mkop_cls_code trht_yn askp_rsqn1 bidp_rsqn1 "
        "total_askp_rsqn total_bidp_rsqn vol_tnrt prdy_smns_hour_acml_vol "
        "prdy_smns_hour_acml_vol_rate hour_cls_code mrkt_trtm_cls_code"
    ),
    # examples_llm/domestic_stock/asking_price_krx/asking_price_krx.py
    "H0STASP0": (
        "mksc_shrn_iscd bsop_hour hour_cls_code askp1 askp2 askp3 askp4 askp5 askp6 "
        "askp7 askp8 askp9 askp10 bidp1 bidp2 bidp3 bidp4 bidp5 bidp6 bidp7 bidp8 "
        "bidp9 bidp10 askp_rsqn1 askp_rsqn2 askp_rsqn3 askp_rsqn4 askp_rsqn5 "
        "askp_rsqn6 askp_rsqn7 askp_rsqn8 askp_rsqn9 askp_rsqn10 bidp_rsqn1 "
        "bidp_rsqn2 bidp_rsqn3 bidp_rsqn4 bidp_rsqn5 bidp_rsqn6 bidp_rsqn7 "
        "bidp_rsqn8 bidp_rsqn9 bidp_rsqn10 total_askp_rsqn total_bidp_rsqn "
        "ovtm_total_askp_rsqn ovtm_total_bidp_rsqn antc_cnpr antc_cnqn antc_vol "
        "antc_cntg_vrss antc_cntg_vrss_sign antc_cntg_prdy_ctrt acml_vol "
        "total_askp_rsqn_icdc total_bidp_rsqn_icdc ovtm_total_askp_icdc "
        "ovtm_total_bidp_icdc stck_deal_cls_code mid_prc midp_total_rsqn "
        "midp_cls_code market_cls_code"
    ),
    # workbook:국내주식 실시간체결통보
    "H0STCNI0": (
        "cust_id acnt_no oder_no ooder_no seln_byov_cls rctf_cls oder_kind "
        "oder_cond stck_shrn_iscd cntg_qty cntg_unpr stck_cntg_hour rfus_yn cntg_yn "
        "acpt_yn brnc_no oder_qty acnt_name ord_cond_prc ord_exg_gb popup_yn filler "
        "crdt_cls crdt_loan_date cntg_isnm40 oder_prc"
    ),
    # workbook:국내주식 실시간체결통보
    "H0STCNI9": (
        "cust_id acnt_no oder_no ooder_no seln_byov_cls rctf_cls oder_kind "
        "oder_cond stck_shrn_iscd cntg_qty cntg_unpr stck_cntg_hour rfus_yn cntg_yn "
        "acpt_yn brnc_no oder_qty acnt_name ord_cond_prc ord_exg_gb popup_yn filler "
        "crdt_cls crdt_loan_date cntg_isnm40 oder_prc"
    ),
    # examples_llm/domestic_stock/ccnl_krx/ccnl_krx.py
    "H0STCNT0": (
        "mksc_shrn_iscd stck_cntg_hour stck_prpr prdy_vrss_sign prdy_vrss prdy_ctrt "
        "wghn_avrg_stck_prc stck_oprc stck_hgpr stck_lwpr askp1 bidp1 cntg_vol "
        "acml_vol acml_tr_pbmn seln_cntg_csnu shnu_cntg_csnu ntby_cntg_csnu cttr "
        "seln_cntg_smtn shnu_cntg_smtn ccld_dvsn shnu_rate "
        "prdy_vol_vrss_acml_vol_rate oprc_hour oprc_vrss_prpr_sign oprc_vrss_prpr "
        "hgpr_hour hgpr_vrss_prpr_sign hgpr_vrss_prpr lwpr_hour lwpr_vrss_prpr_sign "
        "lwpr_vrss_prpr bsop_date new_mkop_cls_code trht_yn askp_rsqn1 bidp_rsqn1 "
        "total_askp_rsqn total_bidp_rsqn vol_tnrt prdy_smns_hour_acml_vol "
        "prdy_smns_hour_acml_vol_rate hour_cls_code mrkt_trtm_cls_code vi_stnd_prc "
        "market_cls_code"
    ),
    # workbook:국내주식 실시간회원사 (KRX)
    "H0STMBC0": (
        "mksc_shrn_iscd seln2_mbcr_name1 seln2_mbcr_name2 seln2_mbcr_name3 "
        "seln2_mbcr_name4 seln2_mbcr_name5 byov_mbcr_name1 byov_mbcr_name2 "
        "byov_mbcr_name3 byov_mbcr_name4 byov_mbcr_name5 total_seln_qty1 "
        "total_seln_qty2 total_seln_qty3 total_seln_qty4 total_seln_qty5 "
        "total_shnu_qty1 total_shnu_qty2 total_shnu_qty3 total_shnu_qty4 "
        "total_shnu_qty5 seln_mbcr_glob_yn_1 seln_mbcr_glob_yn_2 "
        "seln_mbcr_glob_yn_3 seln_mbcr_glob_yn_4 seln_mbcr_glob_yn_5 "
        "shnu_mbcr_glob_yn_1 shnu_mbcr_glob_yn_2 shnu_mbcr_glob_yn_3 "
        "shnu_mbcr_glob_yn_4 shnu_mbcr_glob_yn_5 seln_mbcr_no1 seln_mbcr_no2 "
        "seln_mbcr_no3 seln_mbcr_no4 seln_mbcr_no5 shnu_mbcr_no1 shnu_mbcr_no2 "
        "shnu_mbcr_no3 shnu_mbcr_no4 shnu_mbcr_no5 seln_mbcr_rlim1 seln_mbcr_rlim2 "
        "seln_mbcr_rlim3 seln_mbcr_rlim4 seln_mbcr_rlim5 shnu_mbcr_rlim1 "
        "shnu_mbcr_rlim2 shnu_mbcr_rlim3 shnu_mbcr_rlim4 shnu_mbcr_rlim5 "
        "seln_qty_icdc1 seln_qty_icdc2 seln_qty_icdc3 seln_qty_icdc4 seln_qty_icdc5 "
        "shnu_qty_icdc1 shnu_qty_icdc2 shnu_qty_icdc3 shnu_qty_icdc4 shnu_qty_icdc5 "
        "glob_total_seln_qty glob_total_shnu_qty glob_total_seln_qty_icdc "
        "glob_total_shnu_qty_icdc glob_ntby_qty glob_seln_rlim glob_shnu_rlim "
        "seln2_mbcr_eng_name1 seln2_mbcr_eng_name2 seln2_mbcr_eng_name3 "
        "seln2_mbcr_eng_name4 seln2_mbcr_eng_name5 byov_mbcr_eng_name1 "
        "byov_mbcr_eng_name2 byov_mbcr_eng_name3 byov_mbcr_eng_name4 "
        "byov_mbcr_eng_name5"
    ),
    # workbook:국내주식 장운영정보 (KRX)
    "H0STMKO0": (
        "mksc_shrn_iscd trht_yn tr_susp_reas_cntt mkop_cls_code antc_mkop_cls_code "
        "mrkt_trtm_cls_code divi_app_cls_code iscd_stat_cls_code vi_cls_code "
        "ovtm_vi_cls_code exch_cls_code"
    ),
    # workbook:국내ETF NAV추이
    "H0STNAV0": (
        "mksc_shrn_iscd nav nav_prdy_vrss_sign nav_prdy_vrss nav_prdy_ctrt oprc_nav "
        "hprc_nav lprc_nav"
    ),
    # workbook:국내주식 시간외 실시간호가 (KRX)
    "H0STOAA0": (
        "mksc_shrn_iscd bsop_hour hour_cls_code askp1 askp2 askp3 askp4 askp5 askp6 "
        "askp7 askp8 askp9 bidp1 bidp2 bidp3 bidp4 bidp5 bidp6 bidp7 bidp8 bidp9 "
        "askp_rsqn1 askp_rsqn2 askp_rsqn3 askp_rsqn4 askp_rsqn5 askp_rsqn6 "
        "askp_rsqn7 askp_rsqn8 askp_rsqn9 bidp_rsqn1 bidp_rsqn2 bidp_rsqn3 "
        "bidp_rsqn4 bidp_rsqn5 bidp_rsqn6 bidp_rsqn7 bidp_rsqn8 bidp_rsqn9 "
        "total_askp_rsqn total_bidp_rsqn ovtm_total_askp_rsqn ovtm_total_bidp_rsqn "
        "antc_cnpr antc_cnqn antc_vol antc_cntg_vrss antc_cntg_vrss_sign "
        "antc_cntg_prdy_ctrt acml_vol total_askp_rsqn_icdc total_bidp_rsqn_icdc "
        "ovtm_total_askp_icdc ovtm_total_bidp_icdc"
    ),
    # workbook:국내주식 시간외 실시간예상체결 (KRX)
    "H0STOAC0": (
        "mksc_shrn_iscd stck_cntg_hour stck_prpr prdy_vrss_sign prdy_vrss prdy_ctrt "
        "wghn_avrg_stck_prc stck_oprc stck_hgpr stck_lwpr askp1 bidp1 cntg_vol "
        "acml_vol acml_tr_pbmn seln_cntg_csnu shnu_cntg_csnu ntby_cntg_csnu cttr "
        "seln_cntg_smtn shnu_cntg_smtn cntg_cls_code shnu_rate "
        "prdy_vol_vrss_acml_vol_rate oprc_hour oprc_vrss_prpr_sign oprc_vrss_prpr "
        "hgpr_hour hgpr_vrss_prpr_sign hgpr_vrss_prpr lwpr_hour lwpr_vrss_prpr_sign "
        "lwpr_vrss_prpr bsop_date new_mkop_cls_code trht_yn askp_rsqn1 bidp_rsqn1 "
        "total_askp_rsqn total_bidp_rsqn vol_tnrt prdy_smns_hour_acml_vol "
        "prdy_smns_hour_acml_vol_rate"
    ),
    # workbook:국내주식 시간외 실시간체결가 (KRX)
    "H0STOUP0": (
        "mksc_shrn_iscd stck_cntg_hour stck_prpr prdy_vrss_sign prdy_vrss prdy_ctrt "
        "wghn_avrg_stck_prc stck_oprc stck_hgpr stck_lwpr askp1 bidp1 cntg_vol "
        "acml_vol acml_tr_pbmn seln_cntg_csnu shnu_cntg_csnu ntby_cntg_csnu cttr "
        "seln_cntg_smtn shnu_cntg_smtn cntg_cls_code shnu_rate "
        "prdy_vol_vrss_acml_vol_rate oprc_hour oprc_vrss_prpr_sign oprc_vrss_prpr "
        "hgpr_hour hgpr_vrss_prpr_sign hgpr_vrss_prpr lwpr_hour lwpr_vrss_prpr_sign "
        "lwpr_vrss_prpr bsop_date new_mkop_cls_code trht_yn askp_rsqn1 bidp_rsqn1 "
        "total_askp_rsqn total_bidp_rsqn vol_tnrt prdy_smns_hour_acml_vol "
        "prdy_smns_hour_acml_vol_rate"
    ),
    # workbook:국내주식 실시간프로그램매매 (KRX)
    "H0STPGM0": (
        "mksc_shrn_iscd stck_cntg_hour seln_cnqn seln_tr_pbmn shnu_cnqn "
        "shnu_tr_pbmn ntby_cnqn ntby_tr_pbmn seln_rsqn shnu_rsqn whol_ntby_qty"
    ),
    # workbook:국내주식 실시간예상체결 (통합)
    "H0UNANC0": (
        "mksc_shrn_iscd stck_cntg_hour stck_prpr prdy_vrss_sign prdy_vrss prdy_ctrt "
        "wghn_avrg_stck_prc stck_oprc stck_hgpr stck_lwpr askp1 bidp1 cntg_vol "
        "acml_vol acml_tr_pbmn seln_cntg_csnu shnu_cntg_csnu ntby_cntg_csnu cttr "
        "seln_cntg_smtn shnu_cntg_smtn cntg_cls_code shnu_rate "
        "prdy_vol_vrss_acml_vol_rate oprc_hour oprc_vrss_prpr_sign oprc_vrss_prpr "
        "hgpr_hour hgpr_vrss_prpr_sign hgpr_vrss_prpr lwpr_hour lwpr_vrss_prpr_sign "
        "lwpr_vrss_prpr bsop_date new_mkop_cls_code trht_yn askp_rsqn1 bidp_rsqn1 "
        "total_askp_rsqn total_bidp_rsqn vol_tnrt prdy_smns_hour_acml_vol "
        "prdy_smns_hour_acml_vol_rate hour_cls_code mrkt_trtm_cls_code vi_stnd_prc"
    ),
    # examples_llm/domestic_stock/asking_price_total/asking_price_total.py
    "H0UNASP0": (
        "mksc_shrn_iscd bsop_hour hour_cls_code askp1 askp2 askp3 askp4 askp5 askp6 "
        "askp7 askp8 askp9 askp10 bidp1 bidp2 bidp3 bidp4 bidp5 bidp6 bidp7 bidp8 "
        "bidp9 bidp10 askp_rsqn1 askp_rsqn2 askp_rsqn3 askp_rsqn4 askp_rsqn5 "
        "askp_rsqn6 askp_rsqn7 askp_rsqn8 askp_rsqn9 askp_rsqn10 bidp_rsqn1 "
        "bidp_rsqn2 bidp_rsqn3 bidp_rsqn4 bidp_rsqn5 bidp_rsqn6 bidp_rsqn7 "
        "bidp_rsqn8 bidp_rsqn9 bidp_rsqn10 total_askp_rsqn total_bidp_rsqn "
        "ovtm_total_askp_rsqn ovtm_total_bidp_rsqn antc_cnpr antc_cnqn antc_vol "
        "antc_cntg_vrss antc_cntg_vrss_sign antc_cntg_prdy_ctrt acml_vol "
        "total_askp_rsqn_icdc total_bidp_rsqn_icdc ovtm_total_askp_icdc "
        "ovtm_total_bidp_icdc stck_deal_cls_code kmid_prc kmid_total_rsqn "
        "kmid_cls_code nmid_prc nmid_total_rsqn nmid_cls_code antc_exch_cls_code"
    ),
    # examples_llm/domestic_stock/ccnl_total/ccnl_total.py
    "H0UNCNT0": (
        "mksc_shrn_iscd stck_cntg_hour stck_prpr prdy_vrss_sign prdy_vrss prdy_ctrt "
        "wghn_avrg_stck_prc stck_oprc stck_hgpr stck_lwpr askp1 bidp1 cntg_vol "
        "acml_vol acml_tr_pbmn seln_cntg_csnu shnu_cntg_csnu ntby_cntg_csnu cttr "
        "seln_cntg_smtn shnu_cntg_smtn cntg_cls_code shnu_rate "
        "prdy_vol_vrss_acml_vol_rate oprc_hour oprc_vrss_prpr_sign oprc_vrss_prpr "
        "hgpr_hour hgpr_vrss_prpr_sign hgpr_vrss_prpr lwpr_hour lwpr_vrss_prpr_sign "
        "lwpr_vrss_prpr bsop_date new_mkop_cls_code trht_yn askp_rsqn1 bidp_rsqn1 "
        "total_askp_rsqn total_bidp_rsqn vol_tnrt prdy_smns_hour_acml_vol "
        "prdy_smns_hour_acml_vol_rate hour_cls_code mrkt_trtm_cls_code vi_stnd_prc "
        "market_cls_code"
    ),
    # workbook:국내주식 실시간회원사 (통합)
    "H0UNMBC0": (
        "mksc_shrn_iscd seln2_mbcr_name1 seln2_mbcr_name2 seln2_mbcr_name3 "
        "seln2_mbcr_name4 seln2_mbcr_name5 byov_mbcr_name1 byov_mbcr_name2 "
        "byov_mbcr_name3 byov_mbcr_name4 byov_mbcr_name5 total_seln_qty1 "
        "total_seln_qty2 total_seln_qty3 total_seln_qty4 total_seln_qty5 "
        "total_shnu_qty1 total_shnu_qty2 total_shnu_qty3 total_shnu_qty4 "
        "total_shnu_qty5 seln_mbcr_glob_yn_1 seln_mbcr_glob_yn_2 "
        "seln_mbcr_glob_yn_3 seln_mbcr_glob_yn_4 seln_mbcr_glob_yn_5 "
        "shnu_mbcr_glob_yn_1 shnu_mbcr_glob_yn_2 shnu_mbcr_glob_yn_3 "
        "shnu_mbcr_glob_yn_4 shnu_mbcr_glob_yn_5 seln_mbcr_no1 seln_mbcr_no2 "
        "seln_mbcr_no3 seln_mbcr_no4 seln_mbcr_no5 shnu_mbcr_no1 shnu_mbcr_no2 "
        "shnu_mbcr_no3 shnu_mbcr_no4 shnu_mbcr_no5 seln_mbcr_rlim1 seln_mbcr_rlim2 "
        "seln_mbcr_rlim3 seln_mbcr_rlim4 seln_mbcr_rlim5 shnu_mbcr_rlim1 "
        "shnu_mbcr_rlim2 shnu_mbcr_rlim3 shnu_mbcr_rlim4 shnu_mbcr_rlim5 "
        "seln_qty_icdc1 seln_qty_icdc2 seln_qty_icdc3 seln_qty_icdc4 seln_qty_icdc5 "
        "shnu_qty_icdc1 shnu_qty_icdc2 shnu_qty_icdc3 shnu_qty_icdc4 shnu_qty_icdc5 "
        "glob_total_seln_qty glob_total_shnu_qty glob_total_seln_qty_icdc "
        "glob_total_shnu_qty_icdc glob_ntby_qty glob_seln_rlim glob_shnu_rlim "
        "seln2_mbcr_eng_name1 seln2_mbcr_eng_name2 seln2_mbcr_eng_name3 "
        "seln2_mbcr_eng_name4 seln2_mbcr_eng_name5 byov_mbcr_eng_name1 "
        "byov_mbcr_eng_name2 byov_mbcr_eng_name3 byov_mbcr_eng_name4 "
        "byov_mbcr_eng_name5"
    ),
    # workbook:국내주식 장운영정보 (통합)
    "H0UNMKO0": (
        "trht_yn tr_susp_reas_cntt mkop_cls_code antc_mkop_cls_code "
        "mrkt_trtm_cls_code divi_app_cls_code iscd_stat_cls_code vi_cls_code "
        "ovtm_vi_cls_code exch_cls_code"
    ),
    # workbook:국내주식 실시간프로그램매매 (통합)
    "H0UNPGM0": (
        "mksc_shrn_iscd stck_cntg_hour seln_cnqn seln_tr_pbmn shnu_cnqn "
        "shnu_tr_pbmn ntby_cnqn ntby_tr_pbmn seln_rsqn shnu_rsqn whol_ntby_qty"
    ),
    # workbook:국내지수 실시간예상체결
    "H0UPANC0": (
        "bstp_cls_code bsop_hour prpr_nmix prdy_vrss_sign bstp_nmix_prdy_vrss "
        "acml_vol acml_tr_pbmn pcas_vol pcas_tr_pbmn prdy_ctrt oprc_nmix nmix_hgpr "
        "nmix_lwpr oprc_vrss_nmix_prpr oprc_vrss_nmix_sign hgpr_vrss_nmix_prpr "
        "hgpr_vrss_nmix_sign lwpr_vrss_nmix_prpr lwpr_vrss_nmix_sign "
        "prdy_clpr_vrss_oprc_rate prdy_clpr_vrss_hgpr_rate prdy_clpr_vrss_lwpr_rate "
        "uplm_issu_cnt ascn_issu_cnt stnr_issu_cnt down_issu_cnt lslm_issu_cnt "
        "qtqt_ascn_issu_cnt qtqt_down_issu_cnt tick_vrss"
    ),
    # workbook:국내지수 실시간체결
    "H0UPCNT0": (
        "bstp_cls_code bsop_hour prpr_nmix prdy_vrss_sign bstp_nmix_prdy_vrss "
        "acml_vol acml_tr_pbmn pcas_vol pcas_tr_pbmn prdy_ctrt oprc_nmix nmix_hgpr "
        "nmix_lwpr oprc_vrss_nmix_prpr oprc_vrss_nmix_sign hgpr_vrss_nmix_prpr "
        "hgpr_vrss_nmix_sign lwpr_vrss_nmix_prpr lwpr_vrss_nmix_sign "
        "prdy_clpr_vrss_oprc_rate prdy_clpr_vrss_hgpr_rate prdy_clpr_vrss_lwpr_rate "
        "uplm_issu_cnt ascn_issu_cnt stnr_issu_cnt down_issu_cnt lslm_issu_cnt "
        "qtqt_ascn_issu_cnt qtqt_down_issu_cnt tick_vrss"
    ),
    # workbook:국내지수 실시간프로그램매매
    "H0UPPGM0": (
        "bstp_cls_code bsop_hour arbt_seln_entm_cnqn arbt_seln_onsl_cnqn "
        "arbt_shnu_entm_cnqn arbt_shnu_onsl_cnqn nabt_seln_entm_cnqn "
        "nabt_seln_onsl_cnqn nabt_shnu_entm_cnqn nabt_shnu_onsl_cnqn "
        "arbt_seln_entm_cntg_amt arbt_seln_onsl_cntg_amt arbt_shnu_entm_cntg_amt "
        "arbt_shnu_onsl_cntg_amt nabt_seln_entm_cntg_amt nabt_seln_onsl_cntg_amt "
        "nabt_shnu_entm_cntg_amt nabt_shnu_onsl_cntg_amt arbt_smtn_seln_vol "
        "arbt_smtm_seln_vol_rate arbt_smtn_seln_tr_pbmn arbt_smtm_seln_tr_pbmn_rate "
        "arbt_smtn_shnu_vol arbt_smtm_shnu_vol_rate arbt_smtn_shnu_tr_pbmn "
        "arbt_smtm_shnu_tr_pbmn_rate arbt_smtn_ntby_qty arbt_smtm_ntby_qty_rate "
        "arbt_smtn_ntby_tr_pbmn arbt_smtm_ntby_tr_pbmn_rate nabt_smtn_seln_vol "
        "nabt_smtm_seln_vol_rate nabt_smtn_seln_tr_pbmn nabt_smtm_seln_tr_pbmn_rate "
        "nabt_smtn_shnu_vol nabt_smtm_shnu_vol_rate nabt_smtn_shnu_tr_pbmn "
        "nabt_smtm_shnu_tr_pbmn_rate nabt_smtn_ntby_qty nabt_smtm_ntby_qty_rate "
        "nabt_smtn_ntby_tr_pbmn nabt_smtm_ntby_tr_pbmn_rate whol_entm_seln_vol "
        "entm_seln_vol_rate whol_entm_seln_tr_pbmn entm_seln_tr_pbmn_rate "
        "whol_entm_shnu_vol entm_shnu_vol_rate whol_entm_shnu_tr_pbmn "
        "entm_shnu_tr_pbmn_rate whol_entm_ntby_qt entm_ntby_qty_rat "
        "whol_entm_ntby_tr_pbmn entm_ntby_tr_pbmn_rate whol_onsl_seln_vol "
        "onsl_seln_vol_rate whol_onsl_seln_tr_pbmn onsl_seln_tr_pbmn_rate "
        "whol_onsl_shnu_vol onsl_shnu_vol_rate whol_onsl_shnu_tr_pbmn "
        "onsl_shnu_tr_pbmn_rate whol_onsl_ntby_qty onsl_ntby_qty_rate "
        "whol_onsl_ntby_tr_pbmn onsl_ntby_tr_pbmn_rate total_seln_qty "
        "whol_seln_vol_rate total_seln_tr_pbmn whol_seln_tr_pbmn_rate "
        "shnu_cntg_smtn whol_shun_vol_rate total_shnu_tr_pbmn "
        "whol_shun_tr_pbmn_rate whol_ntby_qty whol_smtm_ntby_qty_rate "
        "whol_ntby_tr_pbmn whol_ntby_tr_pbmn_rate arbt_entm_ntby_qty "
        "arbt_entm_ntby_tr_pbmn arbt_onsl_ntby_qty arbt_onsl_ntby_tr_pbmn "
        "nabt_entm_ntby_qty nabt_entm_ntby_tr_pbmn nabt_onsl_ntby_qty "
        "nabt_onsl_ntby_tr_pbmn acml_vol acml_tr_pbmn"
    ),
    # workbook:해외주식 실시간호가
    "HDFSASP0": (
        "rsym symb zdiv xymd xhms kymd khms bvol avol bdvl advl pbid1 pask1 vbid1 "
        "vask1 dbid1 dask1 pbid2 pask2 vbid2 vask2 dbid2 dask2 pbid3 pask3 vbid3 "
        "vask3 dbid3 dask3 pbid3 pask3 vbid3 vask3 dbid3 dask3 pbid4 pask4 vbid4 "
        "vask4 dbid4 dask4 pbid5 pask5 vbid5 vask5 dbid5 dask5 pbid6 pask6 vbid6 "
        "vask6 dbid6 dask6 pbid7 pask7 vbid7 vask7 dbid7 dask7 pbid8 pask8 vbid8 "
        "vask8 dbid8 dask8 pbid9 pask9 vbid9 vask9 dbid9 dask9 pbid10 pask10 vbid10 "
        "vask10 dbid10 dask10"
    ),
    # workbook:해외주식 지연호가(아시아)
    "HDFSASP1": (
        "rsym symb zdiv xymd xhms kymd khms bvol avol bdvl advl pbid1 pask1 vbid1 "
        "vask1 dbid1 dask1"
    ),
    # workbook:해외주식 실시간지연체결가
    "HDFSCNT0": (
        "rsym symb zdiv tymd xymd xhms kymd khms open high low last sign diff rate "
        "pbid pask vbid vask evol tvol tamt bivl asvl strn mtyp"
    ),
}


FIELDS: Dict[str, Tuple[str, ...]] = {
    tr_id: tuple(layout.split()) for tr_id, layout in _LAYOUTS.items()
}


def fields_for(tr_id: str) -> Tuple[str, ...]:
    """Column names for ``tr_id`` (empty tuple when the layout is unknown)."""
    return FIELDS.get(tr_id, ())
