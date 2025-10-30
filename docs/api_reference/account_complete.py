"""
Account Response Types - 계좌 관련 응답 타입 정의 (완전판)

계좌 잔고, 주문 가능 수량, 체결 내역 등 Account API 응답 구조
examples_llm의 COLUMN_MAPPING 정보를 기반으로 완전히 문서화됨
"""

from typing import List, TypedDict

from .common import BaseResponse


# ============================================================
# get_account_balance() - 주식잔고조회
# ============================================================


class AccountBalanceOutput(TypedDict, total=False):
    """주식잔고조회 필드"""

    pdno: str  # 상품번호
    prdt_name: str  # 상품명
    trad_dvsn_name: str  # 매매구분명
    bfdy_buy_qty: str  # 전일매수수량
    bfdy_sll_qty: str  # 전일매도수량
    thdt_buyqty: str  # 금일매수수량
    thdt_sll_qty: str  # 금일매도수량
    hldg_qty: str  # 보유수량
    ord_psbl_qty: str  # 주문가능수량
    pchs_avg_pric: str  # 매입평균가격
    pchs_amt: str  # 매입금액
    prpr: str  # 현재가
    evlu_amt: str  # 평가금액
    evlu_pfls_amt: str  # 평가손익금액
    evlu_pfls_rt: str  # 평가손익율
    evlu_erng_rt: str  # 평가수익율
    loan_dt: str  # 대출일자
    loan_amt: str  # 대출금액
    stln_slng_chgs: str  # 대주매각대금
    expd_dt: str  # 만기일자
    fltt_rt: str  # 등락율
    bfdy_cprs_icdc: str  # 전일대비증감
    item_mgna_rt_name: str  # 종목증거금율명
    grta_rt_name: str  # 보증금율명
    sbst_pric: str  # 대용가격
    stck_loan_unpr: str  # 주식대출단가
    dnca_tot_amt: str  # 예수금총금액
    nxdy_excc_amt: str  # 익일정산금액
    prvs_rcdl_excc_amt: str  # 가수도정산금액
    cma_evlu_amt: str  # CMA평가금액
    bfdy_buy_amt: str  # 전일매수금액
    thdt_buy_amt: str  # 금일매수금액
    nxdy_auto_rdpt_amt: str  # 익일자동상환금액
    bfdy_sll_amt: str  # 전일매도금액
    thdt_sll_amt: str  # 금일매도금액
    d2_auto_rdpt_amt: str  # D+2자동상환금액
    bfdy_tlex_amt: str  # 전일제비용금액
    thdt_tlex_amt: str  # 금일제비용금액
    tot_loan_amt: str  # 총대출금액
    scts_evlu_amt: str  # 유가평가금액
    tot_evlu_amt: str  # 총평가금액
    nass_amt: str  # 순자산금액
    fncg_gld_auto_rdpt_yn: str  # 융자금자동상환여부
    pchs_amt_smtl_amt: str  # 매입금액합계금액
    evlu_amt_smtl_amt: str  # 평가금액합계금액
    evlu_pfls_smtl_amt: str  # 평가손익합계금액
    tot_stln_slng_chgs: str  # 총대주매각대금
    bfdy_tot_asst_evlu_amt: str  # 전일총자산평가금액
    asst_icdc_amt: str  # 자산증감액
    asst_icdc_erng_rt: str  # 자산증감수익율


class AccountBalanceResponse(BaseResponse):
    """주식잔고조회 응답"""

    output1: AccountBalanceOutput



# ============================================================
# get_account_balance_rlz_pl() - 주식잔고조회_실현손익
# ============================================================


class AccountBalanceRlzPlOutput(TypedDict, total=False):
    """주식잔고조회_실현손익 필드"""

    pdno: str  # 상품번호
    prdt_name: str  # 상품명
    trad_dvsn_name: str  # 매매구분명
    bfdy_buy_qty: str  # 전일매수수량
    bfdy_sll_qty: str  # 전일매도수량
    thdt_buyqty: str  # 금일매수수량
    thdt_sll_qty: str  # 금일매도수량
    hldg_qty: str  # 보유수량
    ord_psbl_qty: str  # 주문가능수량
    pchs_avg_pric: str  # 매입평균가격
    pchs_amt: str  # 매입금액
    prpr: str  # 현재가
    evlu_amt: str  # 평가금액
    evlu_pfls_amt: str  # 평가손익금액
    evlu_pfls_rt: str  # 평가손익율
    evlu_erng_rt: str  # 평가수익율
    loan_dt: str  # 대출일자
    loan_amt: str  # 대출금액
    stln_slng_chgs: str  # 대주매각대금
    expd_dt: str  # 만기일자
    stck_loan_unpr: str  # 주식대출단가
    bfdy_cprs_icdc: str  # 전일대비증감
    fltt_rt: str  # 등락율
    dnca_tot_amt: str  # 예수금총금액
    nxdy_excc_amt: str  # 익일정산금액
    prvs_rcdl_excc_amt: str  # 가수도정산금액
    cma_evlu_amt: str  # CMA평가금액
    bfdy_buy_amt: str  # 전일매수금액
    thdt_buy_amt: str  # 금일매수금액
    nxdy_auto_rdpt_amt: str  # 익일자동상환금액
    bfdy_sll_amt: str  # 전일매도금액
    thdt_sll_amt: str  # 금일매도금액
    d2_auto_rdpt_amt: str  # D+2자동상환금액
    bfdy_tlex_amt: str  # 전일제비용금액
    thdt_tlex_amt: str  # 금일제비용금액
    tot_loan_amt: str  # 총대출금액
    scts_evlu_amt: str  # 유가평가금액
    tot_evlu_amt: str  # 총평가금액
    nass_amt: str  # 순자산금액
    fncg_gld_auto_rdpt_yn: str  # 융자금자동상환여부
    pchs_amt_smtl_amt: str  # 매입금액합계금액
    evlu_amt_smtl_amt: str  # 평가금액합계금액
    evlu_pfls_smtl_amt: str  # 평가손익합계금액
    tot_stln_slng_chgs: str  # 총대주매각대금
    bfdy_tot_asst_evlu_amt: str  # 전일총자산평가금액
    asst_icdc_amt: str  # 자산증감액
    asst_icdc_erng_rt: str  # 자산증감수익율
    rlzt_pfls: str  # 실현손익
    rlzt_erng_rt: str  # 실현수익율
    real_evlu_pfls: str  # 실평가손익
    real_evlu_pfls_erng_rt: str  # 실평가손익수익율


class AccountBalanceRlzPlResponse(BaseResponse):
    """주식잔고조회_실현손익 응답"""

    output1: AccountBalanceRlzPlOutput



# ============================================================
# get_credit_balance() - None
# ============================================================


class CreditBalanceOutput(TypedDict, total=False):
    """None 필드"""

    bstp_cls_code: str  # 업종 구분 코드
    hts_kor_isnm: str  # HTS 한글 종목명
    stnd_date1: str  # 기준 일자1
    stnd_date2: str  # 기준 일자2
    mksc_shrn_iscd: str  # 유가증권 단축 종목코드
    stck_prpr: str  # 주식 현재가
    prdy_vrss: str  # 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    prdy_ctrt: str  # 전일 대비율
    acml_vol: str  # 누적 거래량
    whol_loan_rmnd_stcn: str  # 전체 융자 잔고 주수
    whol_loan_rmnd_amt: str  # 전체 융자 잔고 금액
    whol_loan_rmnd_rate: str  # 전체 융자 잔고 비율
    whol_stln_rmnd_stcn: str  # 전체 대주 잔고 주수
    whol_stln_rmnd_amt: str  # 전체 대주 잔고 금액
    whol_stln_rmnd_rate: str  # 전체 대주 잔고 비율
    nday_vrss_loan_rmnd_inrt: str  # N일 대비 융자 잔고 증가율
    nday_vrss_stln_rmnd_inrt: str  # N일 대비 대주 잔고 증가율


class CreditBalanceResponse(BaseResponse):
    """None 응답"""

    output1: CreditBalanceOutput



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
# get_period_trade_profit() - 기간별매매손익현황조회
# ============================================================


class PeriodTradeProfitOutput(TypedDict, total=False):
    """기간별매매손익현황조회 필드"""

    trad_dt: str  # 매매일자
    pdno: str  # 상품번호
    prdt_name: str  # 상품명
    trad_dvsn_name: str  # 매매구분명
    loan_dt: str  # 대출일자
    hldg_qty: str  # 보유수량
    pchs_unpr: str  # 매입단가
    buy_qty: str  # 매수수량
    buy_amt: str  # 매수금액
    sll_pric: str  # 매도가격
    sll_qty: str  # 매도수량
    sll_amt: str  # 매도금액
    rlzt_pfls: str  # 실현손익
    pfls_rt: str  # 손익률
    fee: str  # 수수료
    tl_tax: str  # 제세금
    loan_int: str  # 대출이자
    sll_qty_smtl: str  # 매도수량합계
    sll_tr_amt_smtl: str  # 매도거래금액합계
    sll_fee_smtl: str  # 매도수수료합계
    sll_tltx_smtl: str  # 매도제세금합계
    sll_excc_amt_smtl: str  # 매도정산금액합계
    buyqty_smtl: str  # 매수수량합계
    buy_tr_amt_smtl: str  # 매수거래금액합계
    buy_fee_smtl: str  # 매수수수료합계
    buy_tax_smtl: str  # 매수제세금합계
    buy_excc_amt_smtl: str  # 매수정산금액합계
    tot_qty: str  # 총수량
    tot_tr_amt: str  # 총거래금액
    tot_fee: str  # 총수수료
    tot_tltx: str  # 총제세금
    tot_excc_amt: str  # 총정산금액
    tot_rlzt_pfls: str  # 총실현손익
    tot_pftrt: str  # 총수익률


class PeriodTradeProfitResponse(BaseResponse):
    """기간별매매손익현황조회 응답"""

    output1: PeriodTradeProfitOutput



# ============================================================
# get_psbl_order() - 매수가능조회
# ============================================================


class PsblOrderOutput(TypedDict, total=False):
    """매수가능조회 필드"""

    ord_psbl_cash: str  # 주문가능현금
    ord_psbl_sbst: str  # 주문가능대용
    ruse_psbl_amt: str  # 재사용가능금액
    fund_rpch_chgs: str  # 펀드환매대금
    psbl_qty_calc_unpr: str  # 가능수량계산단가
    nrcvb_buy_amt: str  # 미수없는매수금액
    nrcvb_buy_qty: str  # 미수없는매수수량
    max_buy_amt: str  # 최대매수금액
    max_buy_qty: str  # 최대매수수량
    cma_evlu_amt: str  # CMA평가금액
    ovrs_re_use_amt_wcrc: str  # 해외재사용금액원화
    ord_psbl_frcr_amt_wcrc: str  # 주문가능외화금액원화


class PsblOrderResponse(BaseResponse):
    """매수가능조회 응답"""

    output: PsblOrderOutput



# ============================================================
# get_psbl_sell() - None
# ============================================================


class PsblSellOutput(TypedDict, total=False):
    """None 필드"""

    pdno: str  # 상품번호
    buy_qty: str  # 매수수량
    sll_qty: str  # 매도수량
    cblc_qty: str  # 잔고수량
    nsvg_qty: str  # 비저축수량
    ord_psbl_qty: str  # 주문가능수량
    pchs_avg_pric: str  # 매입평균가격
    pchs_amt: str  # 매입금액
    now_pric: str  # 현재가
    evlu_amt: str  # 평가금액
    evlu_pfls_amt: str  # 평가손익금액
    evlu_pfls_rt: str  # 평가손익율


class PsblSellResponse(BaseResponse):
    """None 응답"""

    output: PsblSellOutput

