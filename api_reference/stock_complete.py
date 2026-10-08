"""
Stock Response Types - 주식 관련 응답 타입 정의 (완전판)

주식 시세 조회, 호가, 분봉 등 Stock API 응답 구조
examples_llm의 COLUMN_MAPPING 정보를 기반으로 완전히 문서화됨
"""

from typing import TypedDict

from .common import BaseResponse

# ============================================================
# get_comp_program_trade_daily() - None
# ============================================================


class CompProgramTradeDailyOutput(TypedDict, total=False):
    """None 필드"""

    stck_bsop_date: str  # 주식 영업 일자
    nabt_entm_seln_tr_pbmn: str  # 비차익 위탁 매도 거래 대금
    nabt_onsl_seln_vol: str  # 비차익 자기 매도 거래량
    whol_onsl_seln_tr_pbmn: str  # 전체 자기 매도 거래 대금
    arbt_smtn_shnu_vol: str  # 차익 합계 매수2 거래량
    nabt_smtn_shnu_tr_pbmn: str  # 비차익 합계 매수2 거래 대금
    arbt_entm_ntby_qty: str  # 차익 위탁 순매수 수량
    nabt_entm_ntby_tr_pbmn: str  # 비차익 위탁 순매수 거래 대금
    arbt_entm_seln_vol: str  # 차익 위탁 매도 거래량
    nabt_entm_seln_vol_rate: str  # 비차익 위탁 매도 거래량 비율
    nabt_onsl_seln_vol_rate: str  # 전체 자기 매도 거래량 비율
    whol_onsl_seln_tr_pbmn_rate: str  # 전체 자기 매도 거래 대금 비율
    arbt_smtm_shun_vol_rate: str  # 차익 합계 매수 거래량 비율
    nabt_smtm_shun_tr_pbmn_rate: str  # 비차익 합계 매수 거래대금 비율
    arbt_entm_ntby_qty_rate: str  # 차익 위탁 순매수 수량 비율
    nabt_entm_ntby_tr_pbmn_rate: str  # 비차익 위탁 순매수 거래 대금
    arbt_entm_seln_vol_rate: str  # 차익 위탁 매도 거래량 비율
    nabt_entm_seln_tr_pbmn_rate: str  # 비차익 위탁 매도 거래 대금 비
    nabt_onsl_seln_tr_pbmn: str  # 비차익 자기 매도 거래 대금
    whol_smtn_seln_vol: str  # 전체 합계 매도 거래량
    arbt_smtn_shnu_tr_pbmn: str  # 차익 합계 매수2 거래 대금
    whol_entm_shnu_vol: str  # 전체 위탁 매수2 거래량
    arbt_entm_ntby_tr_pbmn: str  # 차익 위탁 순매수 거래 대금
    nabt_onsl_ntby_qty: str  # 비차익 자기 순매수 수량
    arbt_entm_seln_tr_pbmn: str  # 차익 위탁 매도 거래 대금
    whol_seln_vol_rate: str  # 전체 매도 거래량 비율
    whol_entm_shnu_vol_rate: str  # 전체 위탁 매수 거래량 비율
    whol_entm_seln_tr_pbmn: str  # 전체 위탁 매도 거래 대금
    nabt_smtm_seln_vol: str  # 비차익 합계 매도 거래량
    arbt_entm_shnu_vol: str  # 차익 위탁 매수2 거래량
    nabt_entm_shnu_tr_pbmn: str  # 비차익 위탁 매수2 거래 대금
    whol_onsl_shnu_vol: str  # 전체 자기 매수2 거래량
    arbt_onsl_ntby_tr_pbmn: str  # 차익 자기 순매수 거래 대금
    nabt_smtn_ntby_qty: str  # 비차익 합계 순매수 수량
    arbt_onsl_seln_vol: str  # 차익 자기 매도 거래량
    whol_entm_ntby_qty: str  # 전체 위탁 순매수 수량
    nabt_onsl_ntby_tr_pbmn: str  # 비차익 자기 순매수 거래 대금
    arbt_onsl_seln_tr_pbmn: str  # 차익 자기 매도 거래 대금
    nabt_smtm_seln_tr_pbmn_rate: str  # 비차익 합계 매도 거래대금 비율
    arbt_entm_shnu_vol_rate: str  # 차익 위탁 매수 거래량 비율
    nabt_entm_shnu_tr_pbmn_rate: str  # 비차익 위탁 매수 거래 대금 비
    whol_onsl_shnu_tr_pbmn: str  # 전체 자기 매수2 거래 대금
    arbt_onsl_ntby_tr_pbmn_rate: str  # 차익 자기 순매수 거래 대금 비
    nabt_smtm_ntby_qty_rate: str  # 비차익 합계 순매수 수량 비율
    arbt_onsl_seln_vol_rate: str  # 차익 자기 매도 거래량 비율
    whol_entm_seln_vol: str  # 전체 위탁 매도 거래량
    arbt_entm_shnu_tr_pbmn: str  # 차익 위탁 매수2 거래 대금
    nabt_onsl_shnu_vol: str  # 비차익 자기 매수2 거래량
    whol_smtn_shnu_vol: str  # 전체 합계 매수2 거래량
    arbt_smtn_ntby_tr_pbmn: str  # 차익 합계 순매수 거래 대금
    arbt_smtn_seln_vol: str  # 차익 합계 매도 거래량
    whol_entm_seln_tr_pbmn_rate: str  # 전체 위탁 매도 거래 대금 비율
    arbt_onsl_shnu_vol_rate: str  # 차익 자기 매수 거래량 비율
    nabt_smtm_shun_vol_rate: str  # 비차익 합계 매수 거래량 비율
    whol_shun_tr_pbmn_rate: str  # 전체 매수 거래대금 비율
    nabt_entm_ntby_qty_rate: str  # 비차익 위탁 순매수 수량 비율
    arbt_smtm_seln_tr_pbmn_rate: str  # 차익 합계 매도 거래대금 비율
    arbt_onsl_shnu_vol: str  # 차익 자기 매수2 거래량
    nabt_onsl_shnu_tr_pbmn: str  # 비차익 자기 매수2 거래 대금
    nabt_smtn_shnu_vol: str  # 비차익 합계 매수2 거래량
    whol_smtn_shnu_tr_pbmn: str  # 전체 합계 매수2 거래 대금
    arbt_smtm_ntby_qty: str  # 차익 합계 순매수 수량
    nabt_smtn_ntby_tr_pbmn: str  # 비차익 합계 순매수 거래 대금
    arbt_smtn_seln_tr_pbmn: str  # 차익 합계 매도 거래 대금
    arbt_onsl_shnu_tr_pbmn_rate: str  # 차익 자기 매수 거래 대금 비율
    whol_shun_vol_rate: str  # 전체 매수 거래량 비율
    arbt_smtm_ntby_tr_pbmn_rate: str  # 차익 합계 순매수 거래대금 비율
    whol_entm_ntby_qty_rate: str  # 전체 위탁 순매수 수량 비율


class CompProgramTradeDailyResponse(BaseResponse):
    """None 응답"""

    output: CompProgramTradeDailyOutput


# ============================================================
# get_daily_ccld() - 주식일별주문체결조회
# ============================================================


class DailyCcldOutput(TypedDict, total=False):
    """주식일별주문체결조회 필드"""

    ord_dt: str  # 주문일자
    ord_gno_brno: str  # 주문채번지점번호
    odno: str  # 주문번호
    orgn_odno: str  # 원주문번호
    ord_dvsn_name: str  # 주문구분명
    sll_buy_dvsn_cd: str  # 매도매수구분코드
    sll_buy_dvsn_cd_name: str  # 매도매수구분코드명
    pdno: str  # 상품번호
    prdt_name: str  # 상품명
    ord_qty: str  # 주문수량
    ord_unpr: str  # 주문단가
    ord_tmd: str  # 주문시각
    tot_ccld_qty: str  # 총체결수량
    avg_prvs: str  # 평균가
    cncl_yn: str  # 취소여부
    tot_ccld_amt: str  # 매입평균가격
    loan_dt: str  # 대출일자
    ordr_empno: str  # 주문자사번
    ord_dvsn_cd: str  # 주문구분코드
    cnc_cfrm_qty: str  # 취소확인수량
    rmn_qty: str  # 잔여수량
    rjct_qty: str  # 거부수량
    ccld_cndt_name: str  # 체결조건명
    inqr_ip_addr: str  # 조회IP주소
    cpbc_ordp_ord_rcit_dvsn_cd: str  # 전산주문표주문접수구분코드
    cpbc_ordp_infm_mthd_dvsn_cd: str  # 전산주문표통보방법구분코드
    infm_tmd: str  # 통보시각
    ctac_tlno: str  # 연락전화번호
    prdt_type_cd: str  # 상품유형코드
    excg_dvsn_cd: str  # 거래소구분코드
    cpbc_ordp_mtrl_dvsn_cd: str  # 전산주문표자료구분코드
    ord_orgno: str  # 주문조직번호
    rsvn_ord_end_dt: str  # 예약주문종료일자
    excg_id_dvsn_Cd: str  # 거래소ID구분코드
    stpm_cndt_pric: str  # 스톱지정가조건가격
    stpm_efct_occr_dtmd: str  # 스톱지정가효력발생상세시각
    tot_ord_qty: str  # 총주문수량
    prsm_tlex_smtl: str  # 총체결금액
    pchs_avg_pric: str  # 추정제비용합계


class DailyCcldResponse(BaseResponse):
    """주식일별주문체결조회 응답"""

    output1: DailyCcldOutput


# ============================================================
# get_daily_credit_balance() - None
# ============================================================


class DailyCreditBalanceOutput(TypedDict, total=False):
    """None 필드"""

    deal_date: str  # 매매 일자
    stck_prpr: str  # 주식 현재가
    prdy_vrss_sign: str  # 전일 대비 부호
    prdy_vrss: str  # 전일 대비
    prdy_ctrt: str  # 전일 대비율
    acml_vol: str  # 누적 거래량
    stlm_date: str  # 결제 일자
    whol_loan_new_stcn: str  # 전체 융자 신규 주수
    whol_loan_rdmp_stcn: str  # 전체 융자 상환 주수
    whol_loan_rmnd_stcn: str  # 전체 융자 잔고 주수
    whol_loan_new_amt: str  # 전체 융자 신규 금액
    whol_loan_rdmp_amt: str  # 전체 융자 상환 금액
    whol_loan_rmnd_amt: str  # 전체 융자 잔고 금액
    whol_loan_rmnd_rate: str  # 전체 융자 잔고 비율
    whol_loan_gvrt: str  # 전체 융자 공여율
    whol_stln_new_stcn: str  # 전체 대주 신규 주수
    whol_stln_rdmp_stcn: str  # 전체 대주 상환 주수
    whol_stln_rmnd_stcn: str  # 전체 대주 잔고 주수
    whol_stln_new_amt: str  # 전체 대주 신규 금액
    whol_stln_rdmp_amt: str  # 전체 대주 상환 금액
    whol_stln_rmnd_amt: str  # 전체 대주 잔고 금액
    whol_stln_rmnd_rate: str  # 전체 대주 잔고 비율
    whol_stln_gvrt: str  # 전체 대주 공여율
    stck_oprc: str  # 주식 시가2
    stck_hgpr: str  # 주식 최고가
    stck_lwpr: str  # 주식 최저가


class DailyCreditBalanceResponse(BaseResponse):
    """None 응답"""

    output: DailyCreditBalanceOutput


# ============================================================
# get_daily_price() - 주식현재가 일자별
# ============================================================


class DailyPriceOutput(TypedDict, total=False):
    """주식현재가 일자별 필드"""

    stck_bsop_date: str  # 주식 영업 일자
    stck_oprc: str  # 주식 시가2
    stck_hgpr: str  # 주식 최고가
    stck_lwpr: str  # 주식 최저가
    stck_clpr: str  # 주식 종가
    acml_vol: str  # 누적 거래량
    prdy_vrss_vol_rate: str  # 전일 대비 거래량 비율
    prdy_vrss: str  # 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    prdy_ctrt: str  # 전일 대비율
    hts_frgn_ehrt: str  # HTS 외국인 소진율
    frgn_ntby_qty: str  # 외국인 순매수 수량
    flng_cls_code: str  # 락 구분 코드
    acml_prtt_rate: str  # 누적 분할 비율


class DailyPriceResponse(BaseResponse):
    """주식현재가 일자별 응답"""

    output: DailyPriceOutput


# ============================================================
# get_daily_short_sale() - None
# ============================================================


class DailyShortSaleOutput(TypedDict, total=False):
    """None 필드"""

    stck_prpr: str  # 주식 현재가
    prdy_vrss: str  # 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    prdy_ctrt: str  # 전일 대비율
    acml_vol: str  # 누적 거래량
    prdy_vol: str  # 전일 거래량
    stck_bsop_date: str  # 주식 영업 일자
    stck_clpr: str  # 주식 종가
    stnd_vol_smtn: str  # 기준 거래량 합계
    ssts_cntg_qty: str  # 공매도 체결 수량
    ssts_vol_rlim: str  # 공매도 거래량 비중
    acml_ssts_cntg_qty: str  # 누적 공매도 체결 수량
    acml_ssts_cntg_qty_rlim: str  # 누적 공매도 체결 수량 비중
    acml_tr_pbmn: str  # 누적 거래 대금
    stnd_tr_pbmn_smtn: str  # 기준 거래대금 합계
    ssts_tr_pbmn: str  # 공매도 거래 대금
    ssts_tr_pbmn_rlim: str  # 공매도 거래대금 비중
    acml_ssts_tr_pbmn: str  # 누적 공매도 거래 대금
    acml_ssts_tr_pbmn_rlim: str  # 누적 공매도 거래 대금 비중
    stck_oprc: str  # 주식 시가2
    stck_hgpr: str  # 주식 최고가
    stck_lwpr: str  # 주식 최저가
    avrg_prc: str  # 평균가격


class DailyShortSaleResponse(BaseResponse):
    """None 응답"""

    output1: DailyShortSaleOutput


# ============================================================
# get_elw_price() - ELW 현재가 시세
# ============================================================


class ElwPriceOutput(TypedDict, total=False):
    """ELW 현재가 시세 필드"""

    elw_shrn_iscd: str  # ELW 단축 종목코드
    hts_kor_isnm: str  # HTS 한글 종목명
    elw_prpr: str  # ELW 현재가
    prdy_vrss: str  # 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    prdy_ctrt: str  # 전일 대비율
    acml_vol: str  # 누적 거래량
    prdy_vrss_vol_rate: str  # 전일 대비 거래량 비율
    unas_shrn_iscd: str  # 기초자산 단축 종목코드
    unas_isnm: str  # 기초자산 종목명
    unas_prpr: str  # 기초자산 현재가
    unas_prdy_vrss: str  # 기초자산 전일 대비
    unas_prdy_vrss_sign: str  # 기초자산 전일 대비 부호
    unas_prdy_ctrt: str  # 기초자산 전일 대비율
    bidp: str  # 매수호가
    askp: str  # 매도호가
    acml_tr_pbmn: str  # 누적 거래 대금
    vol_tnrt: str  # 거래량 회전율
    elw_oprc: str  # ELW 시가2
    elw_hgpr: str  # ELW 최고가
    elw_lwpr: str  # ELW 최저가
    stck_prdy_clpr: str  # 주식 전일 종가
    hts_thpr: str  # HTS 이론가
    dprt: str  # 괴리율
    atm_cls_name: str  # ATM구분명
    hts_ints_vltl: str  # HTS 내재 변동성
    acpr: str  # 행사가
    pvt_scnd_dmrs_prc: str  # 피벗 2차 디저항 가격
    pvt_frst_dmrs_prc: str  # 피벗 1차 디저항 가격
    pvt_pont_val: str  # 피벗 포인트 값
    pvt_frst_dmsp_prc: str  # 피벗 1차 디지지 가격
    pvt_scnd_dmsp_prc: str  # 피벗 2차 디지지 가격
    dmsp_val: str  # 디지지 값
    dmrs_val: str  # 디저항 값
    elw_sdpr: str  # ELW 기준가
    apprch_rate: str  # 접근도
    tick_conv_prc: str  # 틱환산가
    invt_epmd_cntt: str  # 투자 유의 내용


class ElwPriceResponse(BaseResponse):
    """ELW 현재가 시세 응답"""

    output: ElwPriceOutput


# ============================================================
# get_index_category_price() - 국내업종 구분별전체시세
# ============================================================


class IndexCategoryPriceOutput(TypedDict, total=False):
    """국내업종 구분별전체시세 필드"""

    bstp_nmix_prpr: str  # 업종 지수 현재가
    bstp_nmix_prdy_vrss: str  # 업종 지수 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    bstp_nmix_prdy_ctrt: str  # 업종 지수 전일 대비율
    acml_vol: str  # 누적 거래량
    acml_tr_pbmn: str  # 누적 거래 대금
    bstp_nmix_oprc: str  # 업종 지수 시가2
    bstp_nmix_hgpr: str  # 업종 지수 최고가
    bstp_nmix_lwpr: str  # 업종 지수 최저가
    prdy_vol: str  # 전일 거래량
    ascn_issu_cnt: str  # 상승 종목 수
    down_issu_cnt: str  # 하락 종목 수
    stnr_issu_cnt: str  # 보합 종목 수
    uplm_issu_cnt: str  # 상한 종목 수
    lslm_issu_cnt: str  # 하한 종목 수
    prdy_tr_pbmn: str  # 전일 거래 대금
    dryy_bstp_nmix_hgpr_date: str  # 연중업종지수최고가일자
    dryy_bstp_nmix_hgpr: str  # 연중업종지수최고가
    dryy_bstp_nmix_lwpr: str  # 연중업종지수최저가
    dryy_bstp_nmix_lwpr_date: str  # 연중업종지수최저가일자
    bstp_cls_code: str  # 업종 구분 코드
    hts_kor_isnm: str  # HTS 한글 종목명
    acml_vol_rlim: str  # 누적 거래량 비중
    acml_tr_pbmn_rlim: str  # 누적 거래 대금 비중


class IndexCategoryPriceResponse(BaseResponse):
    """국내업종 구분별전체시세 응답"""

    output1: IndexCategoryPriceOutput


# ============================================================
# get_index_daily_price() - 국내업종 일자별지수
# ============================================================


class IndexDailyPriceOutput(TypedDict, total=False):
    """국내업종 일자별지수 필드"""

    bstp_nmix_prpr: str  # 업종 지수 현재가
    bstp_nmix_prdy_vrss: str  # 업종 지수 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    bstp_nmix_prdy_ctrt: str  # 업종 지수 전일 대비율
    acml_vol: str  # 누적 거래량
    acml_tr_pbmn: str  # 누적 거래 대금
    bstp_nmix_oprc: str  # 업종 지수 시가2
    bstp_nmix_hgpr: str  # 업종 지수 최고가
    bstp_nmix_lwpr: str  # 업종 지수 최저가
    prdy_vol: str  # 전일 거래량
    ascn_issu_cnt: str  # 상승 종목 수
    down_issu_cnt: str  # 하락 종목 수
    stnr_issu_cnt: str  # 보합 종목 수
    uplm_issu_cnt: str  # 상한 종목 수
    lslm_issu_cnt: str  # 하한 종목 수
    prdy_tr_pbmn: str  # 전일 거래 대금
    dryy_bstp_nmix_hgpr_date: str  # 연중업종지수최고가일자
    dryy_bstp_nmix_hgpr: str  # 연중업종지수최고가
    dryy_bstp_nmix_lwpr: str  # 연중업종지수최저가
    dryy_bstp_nmix_lwpr_date: str  # 연중업종지수최저가일자
    stck_bsop_date: str  # 주식 영업 일자
    acml_vol_rlim: str  # 누적 거래량 비중
    invt_new_psdg: str  # 투자 신 심리도
    d20_dsrt: str  # 20일 이격도


class IndexDailyPriceResponse(BaseResponse):
    """국내업종 일자별지수 응답"""

    output1: IndexDailyPriceOutput


# ============================================================
# get_index_price() - 국내업종 현재지수
# ============================================================


class IndexPriceOutput(TypedDict, total=False):
    """국내업종 현재지수 필드"""

    bstp_nmix_prpr: str  # 업종 지수 현재가
    bstp_nmix_prdy_vrss: str  # 업종 지수 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    bstp_nmix_prdy_ctrt: str  # 업종 지수 전일 대비율
    acml_vol: str  # 누적 거래량
    prdy_vol: str  # 전일 거래량
    acml_tr_pbmn: str  # 누적 거래 대금
    prdy_tr_pbmn: str  # 전일 거래 대금
    bstp_nmix_oprc: str  # 업종 지수 시가2
    prdy_nmix_vrss_nmix_oprc: str  # 전일 지수 대비 지수 시가2
    oprc_vrss_prpr_sign: str  # 시가2 대비 현재가 부호
    bstp_nmix_oprc_prdy_ctrt: str  # 업종 지수 시가2 전일 대비율
    bstp_nmix_hgpr: str  # 업종 지수 최고가
    prdy_nmix_vrss_nmix_hgpr: str  # 전일 지수 대비 지수 최고가
    hgpr_vrss_prpr_sign: str  # 최고가 대비 현재가 부호
    bstp_nmix_hgpr_prdy_ctrt: str  # 업종 지수 최고가 전일 대비율
    bstp_nmix_lwpr: str  # 업종 지수 최저가
    prdy_clpr_vrss_lwpr: str  # 전일 종가 대비 최저가
    lwpr_vrss_prpr_sign: str  # 최저가 대비 현재가 부호
    prdy_clpr_vrss_lwpr_rate: str  # 전일 종가 대비 최저가 비율
    ascn_issu_cnt: str  # 상승 종목 수
    uplm_issu_cnt: str  # 상한 종목 수
    stnr_issu_cnt: str  # 보합 종목 수
    down_issu_cnt: str  # 하락 종목 수
    lslm_issu_cnt: str  # 하한 종목 수
    dryy_bstp_nmix_hgpr: str  # 연중업종지수최고가
    dryy_hgpr_vrss_prpr_rate: str  # 연중 최고가 대비 현재가 비율
    dryy_bstp_nmix_hgpr_date: str  # 연중업종지수최고가일자
    dryy_bstp_nmix_lwpr: str  # 연중업종지수최저가
    dryy_lwpr_vrss_prpr_rate: str  # 연중 최저가 대비 현재가 비율
    dryy_bstp_nmix_lwpr_date: str  # 연중업종지수최저가일자
    total_askp_rsqn: str  # 총 매도호가 잔량
    total_bidp_rsqn: str  # 총 매수호가 잔량
    seln_rsqn_rate: str  # 매도 잔량 비율
    shnu_rsqn_rate: str  # 매수2 잔량 비율
    ntby_rsqn: str  # 순매수 잔량


class IndexPriceResponse(BaseResponse):
    """국내업종 현재지수 응답"""

    output: IndexPriceOutput


# ============================================================
# get_investor_daily_by_market() - None
# ============================================================


class InvestorDailyByMarketOutput(TypedDict, total=False):
    """None 필드"""

    stck_bsop_date: str  # 주식 영업 일자
    bstp_nmix_prpr: str  # 업종 지수 현재가
    bstp_nmix_prdy_vrss: str  # 업종 지수 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    bstp_nmix_prdy_ctrt: str  # 업종 지수 전일 대비율
    bstp_nmix_oprc: str  # 업종 지수 시가2
    bstp_nmix_hgpr: str  # 업종 지수 최고가
    bstp_nmix_lwpr: str  # 업종 지수 최저가
    stck_prdy_clpr: str  # 주식 전일 종가
    frgn_ntby_qty: str  # 외국인 순매수 수량
    frgn_reg_ntby_qty: str  # 외국인 등록 순매수 수량
    frgn_nreg_ntby_qty: str  # 외국인 비등록 순매수 수량
    prsn_ntby_qty: str  # 개인 순매수 수량
    orgn_ntby_qty: str  # 기관계 순매수 수량
    scrt_ntby_qty: str  # 증권 순매수 수량
    ivtr_ntby_qty: str  # 투자신탁 순매수 수량
    pe_fund_ntby_vol: str  # 사모 펀드 순매수 거래량
    bank_ntby_qty: str  # 은행 순매수 수량
    insu_ntby_qty: str  # 보험 순매수 수량
    mrbn_ntby_qty: str  # 종금 순매수 수량
    fund_ntby_qty: str  # 기금 순매수 수량
    etc_ntby_qty: str  # 기타 순매수 수량
    etc_orgt_ntby_vol: str  # 기타 단체 순매수 거래량
    etc_corp_ntby_vol: str  # 기타 법인 순매수 거래량
    frgn_ntby_tr_pbmn: str  # 외국인 순매수 거래 대금
    frgn_reg_ntby_pbmn: str  # 외국인 등록 순매수 대금
    frgn_nreg_ntby_pbmn: str  # 외국인 비등록 순매수 대금
    prsn_ntby_tr_pbmn: str  # 개인 순매수 거래 대금
    orgn_ntby_tr_pbmn: str  # 기관계 순매수 거래 대금
    scrt_ntby_tr_pbmn: str  # 증권 순매수 거래 대금
    ivtr_ntby_tr_pbmn: str  # 투자신탁 순매수 거래 대금
    pe_fund_ntby_tr_pbmn: str  # 사모 펀드 순매수 거래 대금
    bank_ntby_tr_pbmn: str  # 은행 순매수 거래 대금
    insu_ntby_tr_pbmn: str  # 보험 순매수 거래 대금
    mrbn_ntby_tr_pbmn: str  # 종금 순매수 거래 대금
    fund_ntby_tr_pbmn: str  # 기금 순매수 거래 대금
    etc_ntby_tr_pbmn: str  # 기타 순매수 거래 대금
    etc_orgt_ntby_tr_pbmn: str  # 기타 단체 순매수 거래 대금
    etc_corp_ntby_tr_pbmn: str  # 기타 법인 순매수 거래 대금


class InvestorDailyByMarketResponse(BaseResponse):
    """None 응답"""

    output: InvestorDailyByMarketOutput


# ============================================================
# get_investor_time_by_market() - 시장별 투자자매매동향(시세)
# ============================================================


class InvestorTimeByMarketOutput(TypedDict, total=False):
    """시장별 투자자매매동향(시세) 필드"""

    frgn_seln_vol: str  # 외국인 매도 거래량
    frgn_shnu_vol: str  # 외국인 매수2 거래량
    frgn_ntby_qty: str  # 외국인 순매수 수량
    frgn_seln_tr_pbmn: str  # 외국인 매도 거래 대금
    frgn_shnu_tr_pbmn: str  # 외국인 매수2 거래 대금
    frgn_ntby_tr_pbmn: str  # 외국인 순매수 거래 대금
    prsn_seln_vol: str  # 개인 매도 거래량
    prsn_shnu_vol: str  # 개인 매수2 거래량
    prsn_ntby_qty: str  # 개인 순매수 수량
    prsn_seln_tr_pbmn: str  # 개인 매도 거래 대금
    prsn_shnu_tr_pbmn: str  # 개인 매수2 거래 대금
    prsn_ntby_tr_pbmn: str  # 개인 순매수 거래 대금
    orgn_seln_vol: str  # 기관계 매도 거래량
    orgn_shnu_vol: str  # 기관계 매수2 거래량
    orgn_ntby_qty: str  # 기관계 순매수 수량
    orgn_seln_tr_pbmn: str  # 기관계 매도 거래 대금
    orgn_shnu_tr_pbmn: str  # 기관계 매수2 거래 대금
    orgn_ntby_tr_pbmn: str  # 기관계 순매수 거래 대금
    scrt_seln_vol: str  # 증권 매도 거래량
    scrt_shnu_vol: str  # 증권 매수2 거래량
    scrt_ntby_qty: str  # 증권 순매수 수량
    scrt_seln_tr_pbmn: str  # 증권 매도 거래 대금
    scrt_shnu_tr_pbmn: str  # 증권 매수2 거래 대금
    scrt_ntby_tr_pbmn: str  # 증권 순매수 거래 대금
    ivtr_seln_vol: str  # 투자신탁 매도 거래량
    ivtr_shnu_vol: str  # 투자신탁 매수2 거래량
    ivtr_ntby_qty: str  # 투자신탁 순매수 수량
    ivtr_seln_tr_pbmn: str  # 투자신탁 매도 거래 대금
    ivtr_shnu_tr_pbmn: str  # 투자신탁 매수2 거래 대금
    ivtr_ntby_tr_pbmn: str  # 투자신탁 순매수 거래 대금
    pe_fund_seln_tr_pbmn: str  # 사모 펀드 매도 거래 대금
    pe_fund_seln_vol: str  # 사모 펀드 매도 거래량
    pe_fund_ntby_vol: str  # 사모 펀드 순매수 거래량
    pe_fund_shnu_tr_pbmn: str  # 사모 펀드 매수2 거래 대금
    pe_fund_shnu_vol: str  # 사모 펀드 매수2 거래량
    pe_fund_ntby_tr_pbmn: str  # 사모 펀드 순매수 거래 대금
    bank_seln_vol: str  # 은행 매도 거래량
    bank_shnu_vol: str  # 은행 매수2 거래량
    bank_ntby_qty: str  # 은행 순매수 수량
    bank_seln_tr_pbmn: str  # 은행 매도 거래 대금
    bank_shnu_tr_pbmn: str  # 은행 매수2 거래 대금
    bank_ntby_tr_pbmn: str  # 은행 순매수 거래 대금
    insu_seln_vol: str  # 보험 매도 거래량
    insu_shnu_vol: str  # 보험 매수2 거래량
    insu_ntby_qty: str  # 보험 순매수 수량
    insu_seln_tr_pbmn: str  # 보험 매도 거래 대금
    insu_shnu_tr_pbmn: str  # 보험 매수2 거래 대금
    insu_ntby_tr_pbmn: str  # 보험 순매수 거래 대금
    mrbn_seln_vol: str  # 종금 매도 거래량
    mrbn_shnu_vol: str  # 종금 매수2 거래량
    mrbn_ntby_qty: str  # 종금 순매수 수량
    mrbn_seln_tr_pbmn: str  # 종금 매도 거래 대금
    mrbn_shnu_tr_pbmn: str  # 종금 매수2 거래 대금
    mrbn_ntby_tr_pbmn: str  # 종금 순매수 거래 대금
    fund_seln_vol: str  # 기금 매도 거래량
    fund_shnu_vol: str  # 기금 매수2 거래량
    fund_ntby_qty: str  # 기금 순매수 수량
    fund_seln_tr_pbmn: str  # 기금 매도 거래 대금
    fund_shnu_tr_pbmn: str  # 기금 매수2 거래 대금
    fund_ntby_tr_pbmn: str  # 기금 순매수 거래 대금
    etc_orgt_seln_vol: str  # 기타 단체 매도 거래량
    etc_orgt_shnu_vol: str  # 기타 단체 매수2 거래량
    etc_orgt_ntby_vol: str  # 기타 단체 순매수 거래량
    etc_orgt_seln_tr_pbmn: str  # 기타 단체 매도 거래 대금
    etc_orgt_shnu_tr_pbmn: str  # 기타 단체 매수2 거래 대금
    etc_orgt_ntby_tr_pbmn: str  # 기타 단체 순매수 거래 대금
    etc_corp_seln_vol: str  # 기타 법인 매도 거래량
    etc_corp_shnu_vol: str  # 기타 법인 매수2 거래량
    etc_corp_ntby_vol: str  # 기타 법인 순매수 거래량
    etc_corp_seln_tr_pbmn: str  # 기타 법인 매도 거래 대금
    etc_corp_shnu_tr_pbmn: str  # 기타 법인 매수2 거래 대금
    etc_corp_ntby_tr_pbmn: str  # 기타 법인 순매수 거래 대금


class InvestorTimeByMarketResponse(BaseResponse):
    """시장별 투자자매매동향(시세) 응답"""

    output: InvestorTimeByMarketOutput


# ============================================================
# get_member_daily() - None
# ============================================================


class MemberDailyOutput(TypedDict, total=False):
    """None 필드"""

    stck_bsop_date: str  # 주식영업일자
    total_seln_qty: str  # 총매도수량
    total_shnu_qty: str  # 총매수2수량
    ntby_qty: str  # 순매수수량
    stck_prpr: str  # 주식현재가
    prdy_vrss: str  # 전일대비
    prdy_vrss_sign: str  # 전일대비부호
    prdy_ctrt: str  # 전일대비율
    acml_vol: str  # 누적거래량


class MemberDailyResponse(BaseResponse):
    """None 응답"""

    output: MemberDailyOutput


# ============================================================
# get_minute_price() - 주식당일분봉조회
# ============================================================


class MinutePriceOutput(TypedDict, total=False):
    """주식당일분봉조회 필드"""

    prdy_vrss: str  # 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    prdy_ctrt: str  # 전일 대비율
    stck_prdy_clpr: str  # 전일대비 종가
    acml_vol: str  # 누적 거래량
    acml_tr_pbmn: str  # 누적 거래대금
    hts_kor_isnm: str  # 한글 종목명
    stck_prpr: str  # 주식 현재가
    stck_bsop_date: str  # 주식 영업일자
    stck_cntg_hour: str  # 주식 체결시간
    stck_oprc: str  # 주식 시가
    stck_hgpr: str  # 주식 최고가
    stck_lwpr: str  # 주식 최저가
    cntg_vol: str  # 체결 거래량


class MinutePriceResponse(BaseResponse):
    """주식당일분봉조회 응답"""

    output1: MinutePriceOutput


# ============================================================
# get_orderbook() - None
# ============================================================


class OrderbookOutput(TypedDict, total=False):
    """None 필드"""

    rsym: str  # 실시간조회종목코드
    zdiv: str  # 소수점자리수
    curr: str  # 통화
    base: str  # 전일종가
    open: str  # 시가
    high: str  # 고가
    low: str  # 저가
    last: str  # 현재가
    dymd: str  # 호가일자
    dhms: str  # 호가시간
    bvol: str  # 매수호가총잔량
    avol: str  # 매도호가총잔량
    bdvl: str  # 매수호가총잔량대비
    advl: str  # 매도호가총잔량대비
    code: str  # 종목코드
    ropen: str  # 시가율
    rhigh: str  # 고가율
    rlow: str  # 저가율
    rclose: str  # 현재가율
    pbid1: str  # 매수호가가격1
    pask1: str  # 매도호가가격1
    vbid1: str  # 매수호가잔량1
    vask1: str  # 매도호가잔량1
    dbid1: str  # 매수호가대비1
    dask1: str  # 매도호가대비1
    vstm: str  # VCMStart시간
    vetm: str  # VCMEnd시간
    csbp: str  # CAS/VCM기준가
    cshi: str  # CAS/VCMHighprice
    cslo: str  # CAS/VCMLowprice
    iep: str  # IEP
    iev: str  # IEV


class OrderbookResponse(BaseResponse):
    """None 응답"""

    output1: OrderbookOutput


# ============================================================
# get_overtime_asking_price() - None
# ============================================================


class OvertimeAskingPriceOutput(TypedDict, total=False):
    """None 필드"""

    ovtm_untp_last_hour: str  # 시간외 단일가 최종 시간
    ovtm_untp_askp1: str  # 시간외 단일가 매도호가1
    ovtm_untp_askp2: str  # 시간외 단일가 매도호가2
    ovtm_untp_askp3: str  # 시간외 단일가 매도호가3
    ovtm_untp_askp4: str  # 시간외 단일가 매도호가4
    ovtm_untp_askp5: str  # 시간외 단일가 매도호가5
    ovtm_untp_askp6: str  # 시간외 단일가 매도호가6
    ovtm_untp_askp7: str  # 시간외 단일가 매도호가7
    ovtm_untp_askp8: str  # 시간외 단일가 매도호가8
    ovtm_untp_askp9: str  # 시간외 단일가 매도호가9
    ovtm_untp_askp10: str  # 시간외 단일가 매도호가10
    ovtm_untp_bidp1: str  # 시간외 단일가 매수호가1
    ovtm_untp_bidp2: str  # 시간외 단일가 매수호가2
    ovtm_untp_bidp3: str  # 시간외 단일가 매수호가3
    ovtm_untp_bidp4: str  # 시간외 단일가 매수호가4
    ovtm_untp_bidp5: str  # 시간외 단일가 매수호가5
    ovtm_untp_bidp6: str  # 시간외 단일가 매수호가6
    ovtm_untp_bidp7: str  # 시간외 단일가 매수호가7
    ovtm_untp_bidp8: str  # 시간외 단일가 매수호가8
    ovtm_untp_bidp9: str  # 시간외 단일가 매수호가9
    ovtm_untp_bidp10: str  # 시간외 단일가 매수호가10
    ovtm_untp_askp_icdc1: str  # 시간외 단일가 매도호가 증감1
    ovtm_untp_askp_icdc2: str  # 시간외 단일가 매도호가 증감2
    ovtm_untp_askp_icdc3: str  # 시간외 단일가 매도호가 증감3
    ovtm_untp_askp_icdc4: str  # 시간외 단일가 매도호가 증감4
    ovtm_untp_askp_icdc5: str  # 시간외 단일가 매도호가 증감5
    ovtm_untp_askp_icdc6: str  # 시간외 단일가 매도호가 증감6
    ovtm_untp_askp_icdc7: str  # 시간외 단일가 매도호가 증감7
    ovtm_untp_askp_icdc8: str  # 시간외 단일가 매도호가 증감8
    ovtm_untp_askp_icdc9: str  # 시간외 단일가 매도호가 증감9
    ovtm_untp_askp_icdc10: str  # 시간외 단일가 매도호가 증감10
    ovtm_untp_bidp_icdc1: str  # 시간외 단일가 매수호가 증감1
    ovtm_untp_bidp_icdc2: str  # 시간외 단일가 매수호가 증감2
    ovtm_untp_bidp_icdc3: str  # 시간외 단일가 매수호가 증감3
    ovtm_untp_bidp_icdc4: str  # 시간외 단일가 매수호가 증감4
    ovtm_untp_bidp_icdc5: str  # 시간외 단일가 매수호가 증감5
    ovtm_untp_bidp_icdc6: str  # 시간외 단일가 매수호가 증감6
    ovtm_untp_bidp_icdc7: str  # 시간외 단일가 매수호가 증감7
    ovtm_untp_bidp_icdc8: str  # 시간외 단일가 매수호가 증감8
    ovtm_untp_bidp_icdc9: str  # 시간외 단일가 매수호가 증감9
    ovtm_untp_bidp_icdc10: str  # 시간외 단일가 매수호가 증감10
    ovtm_untp_askp_rsqn1: str  # 시간외 단일가 매도호가 잔량1
    ovtm_untp_askp_rsqn2: str  # 시간외 단일가 매도호가 잔량2
    ovtm_untp_askp_rsqn3: str  # 시간외 단일가 매도호가 잔량3
    ovtm_untp_askp_rsqn4: str  # 시간외 단일가 매도호가 잔량4
    ovtm_untp_askp_rsqn5: str  # 시간외 단일가 매도호가 잔량5
    ovtm_untp_askp_rsqn6: str  # 시간외 단일가 매도호가 잔량6
    ovtm_untp_askp_rsqn7: str  # 시간외 단일가 매도호가 잔량7
    ovtm_untp_askp_rsqn8: str  # 시간외 단일가 매도호가 잔량8
    ovtm_untp_askp_rsqn9: str  # 시간외 단일가 매도호가 잔량9
    ovtm_untp_askp_rsqn10: str  # 시간외 단일가 매도호가 잔량10
    ovtm_untp_bidp_rsqn1: str  # 시간외 단일가 매수호가 잔량1
    ovtm_untp_bidp_rsqn: str  # 시간외 단일가 매수호가 잔량2
    ovtm_untp_bidp_rsqn3: str  # 시간외 단일가 매수호가 잔량3
    ovtm_untp_bidp_rsqn4: str  # 시간외 단일가 매수호가 잔량4
    ovtm_untp_bidp_rsqn5: str  # 시간외 단일가 매수호가 잔량5
    ovtm_untp_bidp_rsqn6: str  # 시간외 단일가 매수호가 잔량6
    ovtm_untp_bidp_rsqn7: str  # 시간외 단일가 매수호가 잔량7
    ovtm_untp_bidp_rsqn8: str  # 시간외 단일가 매수호가 잔량8
    ovtm_untp_bidp_rsqn9: str  # 시간외 단일가 매수호가 잔량9
    ovtm_untp_bidp_rsqn10: str  # 시간외 단일가 매수호가 잔량10
    ovtm_untp_total_askp_rsqn: str  # 시간외 단일가 총 매도호가 잔량
    ovtm_untp_total_bidp_rsqn: str  # 시간외 단일가 총 매수호가 잔량
    ovtm_untp_total_askp_rsqn_icdc: str  # 시간외 단일가 총 매도호가 잔량
    ovtm_untp_total_bidp_rsqn_icdc: str  # 시간외 단일가 총 매수호가 잔량
    ovtm_untp_ntby_bidp_rsqn: str  # 시간외 단일가 순매수 호가 잔량
    total_askp_rsqn: str  # 총 매도호가 잔량
    total_bidp_rsqn: str  # 총 매수호가 잔량
    total_askp_rsqn_icdc: str  # 총 매도호가 잔량 증감
    total_bidp_rsqn_icdc: str  # 총 매수호가 잔량 증감
    ovtm_total_askp_rsqn: str  # 시간외 총 매도호가 잔량
    ovtm_total_bidp_rsqn: str  # 시간외 총 매수호가 잔량
    ovtm_total_askp_icdc: str  # 시간외 총 매도호가 증감
    ovtm_total_bidp_icdc: str  # 시간외 총 매수호가 증감


class OvertimeAskingPriceResponse(BaseResponse):
    """None 응답"""

    output: OvertimeAskingPriceOutput


# ============================================================
# get_overtime_price() - None
# ============================================================


class OvertimePriceOutput(TypedDict, total=False):
    """None 필드"""

    bstp_kor_isnm: str  # 업종 한글 종목명
    mang_issu_cls_name: str  # 관리 종목 구분 명
    ovtm_untp_prpr: str  # 시간외 단일가 현재가
    ovtm_untp_prdy_vrss: str  # 시간외 단일가 전일 대비
    ovtm_untp_prdy_vrss_sign: str  # 시간외 단일가 전일 대비 부호
    ovtm_untp_prdy_ctrt: str  # 시간외 단일가 전일 대비율
    ovtm_untp_vol: str  # 시간외 단일가 거래량
    ovtm_untp_tr_pbmn: str  # 시간외 단일가 거래 대금
    ovtm_untp_mxpr: str  # 시간외 단일가 상한가
    ovtm_untp_llam: str  # 시간외 단일가 하한가
    ovtm_untp_oprc: str  # 시간외 단일가 시가2
    ovtm_untp_hgpr: str  # 시간외 단일가 최고가
    ovtm_untp_lwpr: str  # 시간외 단일가 최저가
    marg_rate: str  # 증거금 비율
    ovtm_untp_antc_cnpr: str  # 시간외 단일가 예상 체결가
    ovtm_untp_antc_cntg_vrss: str  # 시간외 단일가 예상 체결 대비
    ovtm_untp_antc_cntg_vrss_sign: str  # 시간외 단일가 예상 체결 대비
    ovtm_untp_antc_cntg_ctrt: str  # 시간외 단일가 예상 체결 대비율
    ovtm_untp_antc_cnqn: str  # 시간외 단일가 예상 체결량
    crdt_able_yn: str  # 신용 가능 여부
    new_lstn_cls_name: str  # 신규 상장 구분 명
    sltr_yn: str  # 정리매매 여부
    mang_issu_yn: str  # 관리 종목 여부
    mrkt_warn_cls_code: str  # 시장 경고 구분 코드
    trht_yn: str  # 거래정지 여부
    vlnt_deal_cls_name: str  # 임의 매매 구분 명
    ovtm_untp_sdpr: str  # 시간외 단일가 기준가
    mrkt_warn_cls_name: str  # 시장 경구 구분 명
    revl_issu_reas_name: str  # 재평가 종목 사유 명
    insn_pbnt_yn: str  # 불성실 공시 여부
    flng_cls_name: str  # 락 구분 이름
    rprs_mrkt_kor_name: str  # 대표 시장 한글 명
    ovtm_vi_cls_code: str  # 시간외단일가VI적용구분코드
    bidp: str  # 매수호가
    askp: str  # 매도호가


class OvertimePriceResponse(BaseResponse):
    """None 응답"""

    output: OvertimePriceOutput


# ============================================================
# get_program_trade_by_stock() - 종목별 프로그램매매추이(체결)
# ============================================================


class ProgramTradeByStockOutput(TypedDict, total=False):
    """종목별 프로그램매매추이(체결) 필드"""

    bsop_hour: str  # 영업 시간
    stck_prpr: str  # 주식 현재가
    prdy_vrss: str  # 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    prdy_ctrt: str  # 전일 대비율
    acml_vol: str  # 누적 거래량
    whol_smtn_seln_vol: str  # 전체 합계 매도 거래량
    whol_smtn_shnu_vol: str  # 전체 합계 매수2 거래량
    whol_smtn_ntby_qty: str  # 전체 합계 순매수 수량
    whol_smtn_seln_tr_pbmn: str  # 전체 합계 매도 거래 대금
    whol_smtn_shnu_tr_pbmn: str  # 전체 합계 매수2 거래 대금
    whol_smtn_ntby_tr_pbmn: str  # 전체 합계 순매수 거래 대금
    whol_ntby_vol_icdc: str  # 전체 순매수 거래량 증감
    whol_ntby_tr_pbmn_icdc: str  # 전체 순매수 거래 대금 증감


class ProgramTradeByStockResponse(BaseResponse):
    """종목별 프로그램매매추이(체결) 응답"""

    output: ProgramTradeByStockOutput


# ============================================================
# get_program_trade_by_stock_daily() - None
# ============================================================


class ProgramTradeByStockDailyOutput(TypedDict, total=False):
    """None 필드"""

    stck_bsop_date: str  # 주식 영업 일자
    stck_clpr: str  # 주식 종가
    prdy_vrss: str  # 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    prdy_ctrt: str  # 전일 대비율
    acml_vol: str  # 누적 거래량
    acml_tr_pbmn: str  # 누적 거래 대금
    whol_smtn_seln_vol: str  # 전체 합계 매도 거래량
    whol_smtn_shnu_vol: str  # 전체 합계 매수2 거래량
    whol_smtn_ntby_qty: str  # 전체 합계 순매수 수량
    whol_smtn_seln_tr_pbmn: str  # 전체 합계 매도 거래 대금
    whol_smtn_shnu_tr_pbmn: str  # 전체 합계 매수2 거래 대금
    whol_smtn_ntby_tr_pbmn: str  # 전체 합계 순매수 거래 대금
    whol_ntby_vol_icdc: str  # 전체 순매수 거래량 증감
    whol_ntby_tr_pbmn_icdc2: str  # 전체 순매수 거래 대금 증감2


class ProgramTradeByStockDailyResponse(BaseResponse):
    """None 응답"""

    output: ProgramTradeByStockDailyOutput


# ============================================================
# get_stock_investor() - 주식현재가 투자자
# ============================================================


class StockInvestorOutput(TypedDict, total=False):
    """주식현재가 투자자 필드"""

    stck_bsop_date: str  # 주식 영업 일자
    stck_clpr: str  # 주식 종가
    prdy_vrss: str  # 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    prsn_ntby_qty: str  # 개인 순매수 수량
    frgn_ntby_qty: str  # 외국인 순매수 수량
    orgn_ntby_qty: str  # 기관계 순매수 수량
    prsn_ntby_tr_pbmn: str  # 개인 순매수 거래 대금
    frgn_ntby_tr_pbmn: str  # 외국인 순매수 거래 대금
    orgn_ntby_tr_pbmn: str  # 기관계 순매수 거래 대금
    prsn_shnu_vol: str  # 개인 매수2 거래량
    frgn_shnu_vol: str  # 외국인 매수2 거래량
    orgn_shnu_vol: str  # 기관계 매수2 거래량
    prsn_shnu_tr_pbmn: str  # 개인 매수2 거래 대금
    frgn_shnu_tr_pbmn: str  # 외국인 매수2 거래 대금
    orgn_shnu_tr_pbmn: str  # 기관계 매수2 거래 대금
    prsn_seln_vol: str  # 개인 매도 거래량
    frgn_seln_vol: str  # 외국인 매도 거래량
    orgn_seln_vol: str  # 기관계 매도 거래량
    prsn_seln_tr_pbmn: str  # 개인 매도 거래 대금
    frgn_seln_tr_pbmn: str  # 외국인 매도 거래 대금
    orgn_seln_tr_pbmn: str  # 기관계 매도 거래 대금


class StockInvestorResponse(BaseResponse):
    """주식현재가 투자자 응답"""

    output: StockInvestorOutput


# ============================================================
# get_stock_price() - 주식현재가 시세
# ============================================================


class StockPriceOutput(TypedDict, total=False):
    """주식현재가 시세 필드"""

    iscd_stat_cls_code: str  # 종목 상태 구분 코드
    marg_rate: str  # 증거금 비율
    rprs_mrkt_kor_name: str  # 대표 시장 한글 명
    new_hgpr_lwpr_cls_code: str  # 신 고가 저가 구분 코드
    bstp_kor_isnm: str  # 업종 한글 종목명
    temp_stop_yn: str  # 임시 정지 여부
    oprc_rang_cont_yn: str  # 시가 범위 연장 여부
    clpr_rang_cont_yn: str  # 종가 범위 연장 여부
    crdt_able_yn: str  # 신용 가능 여부
    grmn_rate_cls_code: str  # 보증금 비율 구분 코드
    elw_pblc_yn: str  # ELW 발행 여부
    stck_prpr: str  # 주식 현재가
    prdy_vrss: str  # 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    prdy_ctrt: str  # 전일 대비율
    acml_tr_pbmn: str  # 누적 거래 대금
    acml_vol: str  # 누적 거래량
    prdy_vrss_vol_rate: str  # 전일 대비 거래량 비율
    stck_oprc: str  # 주식 시가2
    stck_hgpr: str  # 주식 최고가
    stck_lwpr: str  # 주식 최저가
    stck_mxpr: str  # 주식 상한가
    stck_llam: str  # 주식 하한가
    stck_sdpr: str  # 주식 기준가
    wghn_avrg_stck_prc: str  # 가중 평균 주식 가격
    hts_frgn_ehrt: str  # HTS 외국인 소진율
    frgn_ntby_qty: str  # 외국인 순매수 수량
    pgtr_ntby_qty: str  # 프로그램매매 순매수 수량
    pvt_scnd_dmrs_prc: str  # 피벗 2차 디저항 가격
    pvt_frst_dmrs_prc: str  # 피벗 1차 디저항 가격
    pvt_pont_val: str  # 피벗 포인트 값
    pvt_frst_dmsp_prc: str  # 피벗 1차 디지지 가격
    pvt_scnd_dmsp_prc: str  # 피벗 2차 디지지 가격
    dmrs_val: str  # 디저항 값
    dmsp_val: str  # 디지지 값
    cpfn: str  # 자본금
    rstc_wdth_prc: str  # 제한 폭 가격
    stck_fcam: str  # 주식 액면가
    stck_sspr: str  # 주식 대용가
    aspr_unit: str  # 호가단위
    hts_deal_qty_unit_val: str  # HTS 매매 수량 단위 값
    lstn_stcn: str  # 상장 주수
    hts_avls: str  # HTS 시가총액
    per: str  # PER
    pbr: str  # PBR
    stac_month: str  # 결산 월
    vol_tnrt: str  # 거래량 회전율
    eps: str  # EPS
    bps: str  # BPS
    d250_hgpr: str  # 250일 최고가
    d250_hgpr_date: str  # 250일 최고가 일자
    d250_hgpr_vrss_prpr_rate: str  # 250일 최고가 대비 현재가 비율
    d250_lwpr: str  # 250일 최저가
    d250_lwpr_date: str  # 250일 최저가 일자
    d250_lwpr_vrss_prpr_rate: str  # 250일 최저가 대비 현재가 비율
    stck_dryy_hgpr: str  # 주식 연중 최고가
    dryy_hgpr_vrss_prpr_rate: str  # 연중 최고가 대비 현재가 비율
    dryy_hgpr_date: str  # 연중 최고가 일자
    stck_dryy_lwpr: str  # 주식 연중 최저가
    dryy_lwpr_vrss_prpr_rate: str  # 연중 최저가 대비 현재가 비율
    dryy_lwpr_date: str  # 연중 최저가 일자
    w52_hgpr: str  # 52주일 최고가
    w52_hgpr_vrss_prpr_ctrt: str  # 52주일 최고가 대비 현재가 대비
    w52_hgpr_date: str  # 52주일 최고가 일자
    w52_lwpr: str  # 52주일 최저가
    w52_lwpr_vrss_prpr_ctrt: str  # 52주일 최저가 대비 현재가 대비
    w52_lwpr_date: str  # 52주일 최저가 일자
    whol_loan_rmnd_rate: str  # 전체 융자 잔고 비율
    ssts_yn: str  # 공매도가능여부
    stck_shrn_iscd: str  # 주식 단축 종목코드
    fcam_cnnm: str  # 액면가 통화명
    cpfn_cnnm: str  # 자본금 통화명
    apprch_rate: str  # 접근도
    frgn_hldn_qty: str  # 외국인 보유 수량
    vi_cls_code: str  # VI적용구분코드
    ovtm_vi_cls_code: str  # 시간외단일가VI적용구분코드
    last_ssts_cntg_qty: str  # 최종 공매도 체결 수량
    invt_caful_yn: str  # 투자유의여부
    mrkt_warn_cls_code: str  # 시장경고코드
    short_over_yn: str  # 단기과열여부
    sltr_yn: str  # 정리매매여부
    mang_issu_cls_code: str  # 관리종목여부


class StockPriceResponse(BaseResponse):
    """주식현재가 시세 응답"""

    output: StockPriceOutput
