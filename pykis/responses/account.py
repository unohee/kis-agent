"""
Account Response Types - 계좌 관련 응답 타입 정의

계좌 잔고, 매수가능금액, 체결내역 등 Account API 응답 구조
"""

from typing import List, TypedDict

from .common import BaseResponse

# ============================================================
# get_account_balance() - 계좌 잔고 조회
# ============================================================


class AccountBalanceOutput1Item(TypedDict, total=False):
    """계좌 잔고 개별 보유 종목 정보"""

    pdno: str  # 상품번호 (종목코드, Product Number)
    prdt_name: str  # 상품명 (Product Name)
    trad_dvsn_name: str  # 매매구분명 (Trade Division Name)
    bfdy_buy_qty: str  # 전일매수수량 (Before Day Buy Quantity)
    bfdy_sll_qty: str  # 전일매도수량 (Before Day Sell Quantity)
    thdt_buyqty: str  # 금일매수수량 (Today Buy Quantity)
    thdt_sll_qty: str  # 금일매도수량 (Today Sell Quantity)
    hldg_qty: str  # 보유수량 (Holding Quantity)
    ord_psbl_qty: str  # 주문가능수량 (Order Possible Quantity)
    pchs_avg_pric: str  # 매입평균가격 (Purchase Average Price)
    pchs_amt: str  # 매입금액 (Purchase Amount)
    prpr: str  # 현재가 (Present Price)
    evlu_amt: str  # 평가금액 (Evaluation Amount)
    evlu_pfls_amt: str  # 평가손익금액 (Evaluation Profit/Loss Amount)
    evlu_pfls_rt: str  # 평가손익률 (Evaluation Profit/Loss Rate) %
    evlu_erng_rt: str  # 평가수익률 (Evaluation Earning Rate) %
    loan_dt: str  # 대출일자 (Loan Date, YYYYMMDD)
    loan_amt: str  # 대출금액 (Loan Amount)
    stln_slng_chgs: str  # 대주매각대금 (Stock Lending Selling Charges)
    expd_dt: str  # 만기일자 (Expiration Date, YYYYMMDD)
    fltt_rt: str  # 등락율 (Fluctuation Rate) %
    bfdy_cprs_icdc: str  # 전일대비증감 (Before Day Comparison Increase/Decrease)
    item_mgna_rt_name: str  # 종목증거금율명 (Item Margin Rate Name)
    grta_rt_name: str  # 보증금율명 (Guarantee Rate Name)
    sbst_pric: str  # 대용가격 (Substitute Price)
    stck_loan_unpr: str  # 주식대출단가 (Stock Loan Unit Price)


class AccountBalanceOutput2(TypedDict, total=False):
    """계좌 잔고 요약 정보"""

    dnca_tot_amt: str  # 예수금총액 (Deposit and Cash Total Amount)
    nxdy_excc_amt: str  # 익일정산금액 (Next Day Execution Cash Amount)
    prvs_rcdl_excc_amt: str  # 가수도정산금액 (Previous Record Execution Cash Amount)
    cma_evlu_amt: str  # CMA평가금액 (CMA Evaluation Amount)
    bfdy_buy_amt: str  # 전일매수금액
    thdt_buy_amt: str  # 금일매수금액
    nxdy_auto_rdpt_amt: str  # 익일자동상환금액
    bfdy_sll_amt: str  # 전일매도금액
    thdt_sll_amt: str  # 금일매도금액
    d2_auto_rdpt_amt: str  # D+2자동상환금액
    bfdy_tlex_amt: str  # 전일제비용금액
    thdt_tlex_amt: str  # 금일제비용금액
    tot_loan_amt: str  # 총대출금액 (Total Loan Amount)
    scts_evlu_amt: str  # 유가평가금액 (Securities Evaluation Amount)
    tot_evlu_amt: str  # 총평가금액 (Total Evaluation Amount)
    nass_amt: str  # 순자산금액 (Net Asset Amount)
    fncg_gld_auto_rdpt_yn: (
        str  # 융자금자동상환여부 (Financing Gold Auto Repayment Yes/No)
    )
    pchs_amt_smtl_amt: str  # 매입금액합계금액 (Purchase Amount Sum Total Amount)
    evlu_amt_smtl_amt: str  # 평가금액합계금액 (Evaluation Amount Sum Total Amount)
    evlu_pfls_smtl_amt: (
        str  # 평가손익합계금액 (Evaluation Profit/Loss Sum Total Amount)
    )
    tot_stln_slng_chgs: str  # 총대주매각대금 (Total Stock Lending Selling Charges)
    bfdy_tot_asst_evlu_amt: (
        str  # 전일총자산평가금액 (Before Day Total Asset Evaluation Amount)
    )
    asst_icdc_amt: str  # 자산증감액 (Asset Increase/Decrease Amount)
    asst_icdc_erng_rt: str  # 자산증감수익률 (Asset Increase/Decrease Earning Rate) %


class AccountBalanceResponse(BaseResponse):
    """계좌 잔고 조회 응답"""

    output1: List[AccountBalanceOutput1Item]
    output2: AccountBalanceOutput2


# ============================================================
# get_possible_order_amount() - 매수가능금액 조회
# ============================================================


class PossibleOrderOutput(TypedDict, total=False):
    """매수가능금액 조회 output 필드"""

    dnca_tot_amt: str  # 예수금총액 (Deposit and Cash Total Amount)
    nxdy_excc_amt: str  # 익일정산금액 (Next Day Execution Cash Amount)
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
    pchs_amt_smtl_amt: str  # 매입금액합계금액
    evlu_amt_smtl_amt: str  # 평가금액합계금액
    evlu_pfls_smtl_amt: str  # 평가손익합계금액
    ord_psbl_cash: str  # 주문가능현금 (Order Possible Cash)
    ord_psbl_sbst: str  # 주문가능대용 (Order Possible Substitute)
    ruse_psbl_amt: str  # 재사용가능금액 (Reuse Possible Amount)
    fund_rpch_chgs: str  # 펀드환매대금 (Fund Repurchase Charges)
    psbl_qty_calc_unpr: (
        str  # 가능수량계산단가 (Possible Quantity Calculation Unit Price)
    )
    nrcvb_buy_amt: str  # 미수매수금액 (Non-Receivable Buy Amount)
    nrcvb_buy_qty: str  # 미수매수수량 (Non-Receivable Buy Quantity)
    max_buy_amt: str  # 최대매수금액 (Maximum Buy Amount)
    max_buy_qty: str  # 최대매수수량 (Maximum Buy Quantity)
    cma_evlu_amt_icld_yn: str  # CMA평가금액포함여부
    ovrs_icld_yn: str  # 해외포함여부


class PossibleOrderResponse(BaseResponse):
    """매수가능금액 조회 응답"""

    output: PossibleOrderOutput


# ============================================================
# inquire_daily_ccld() - 일별주문체결조회
# ============================================================


class InquireDailyCcldOutput1Item(TypedDict, total=False):
    """일별 주문체결 개별 항목"""

    ord_dt: str  # 주문일자 (Order Date, YYYYMMDD)
    ord_gno_brno: str  # 주문채번지점번호 (Order General Number Branch Number)
    odno: str  # 주문번호 (Order Number)
    orgn_odno: str  # 원주문번호 (Original Order Number)
    ord_dvsn_name: str  # 주문구분명 (Order Division Name)
    sll_buy_dvsn_cd: str  # 매도매수구분코드 (Sell/Buy Division Code, 01:매도, 02:매수)
    sll_buy_dvsn_cd_name: str  # 매도매수구분코드명
    pdno: str  # 상품번호 (종목코드)
    prdt_name: str  # 상품명
    ord_qty: str  # 주문수량 (Order Quantity)
    ord_unpr: str  # 주문단가 (Order Unit Price)
    ord_tmd: str  # 주문시각 (Order Time, HHMMSS)
    tot_ccld_qty: str  # 총체결수량 (Total Concluded Quantity)
    avg_prvs: str  # 평균가 (Average Price)
    cncl_yn: str  # 취소여부 (Cancel Yes/No, Y/N)
    tot_ccld_amt: str  # 총체결금액 (Total Concluded Amount)
    loan_dt: str  # 대출일자 (Loan Date, YYYYMMDD)
    ord_dvsn_cd: str  # 주문구분코드 (Order Division Code)
    cncl_cfrm_qty: str  # 취소확인수량 (Cancel Confirm Quantity)
    rmn_qty: str  # 잔여수량 (Remaining Quantity)
    rjct_qty: str  # 거부수량 (Reject Quantity)
    ccld_cndt_name: str  # 체결조건명 (Concluded Condition Name)
    infm_tmd: str  # 통보시각 (Inform Time, HHMMSS)
    ctac_tlno: str  # 연락전화번호 (Contact Telephone Number)
    prdt_type_cd: str  # 상품유형코드
    excg_dvsn_cd: str  # 거래소구분코드 (Exchange Division Code)


class InquireDailyCcldOutput2(TypedDict, total=False):
    """일별 주문체결 요약 정보"""

    tot_ord_qty: str  # 총주문수량 (Total Order Quantity)
    tot_ccld_qty: str  # 총체결수량 (Total Concluded Quantity)
    tot_ccld_amt: str  # 총체결금액 (Total Concluded Amount)
    prsm_tlex_smtl: str  # 추정제비용합계 (Presumed Tax/Levy Sum Total) - 수수료+세금
    pchs_avg_pric: str  # 매입평균가격 (Purchase Average Price)

    # 페이지네이션 관련 (일부 API에서만 제공)
    page_count: int  # 조회한 페이지 수 (pagination 사용 시)
    total_count: int  # 전체 조회 건수 (pagination 사용 시)


class InquireDailyCcldResponse(BaseResponse):
    """일별 주문체결 조회 응답"""

    output1: List[InquireDailyCcldOutput1Item]
    output2: InquireDailyCcldOutput2


# ============================================================
# inquire_psbl_sell() - 매도가능수량 조회
# ============================================================


class InquirePsblSellOutput(TypedDict, total=False):
    """매도가능수량 조회 output 필드"""

    ord_psbl_qty: str  # 주문가능수량 (Order Possible Quantity)
    ord_psbl_frcs_amt: str  # 주문가능외화금액 (Order Possible Foreign Currency Amount)
    sbst_ord_psbl_qty: str  # 대용주문가능수량 (Substitute Order Possible Quantity)
    max_ord_psbl_qty: str  # 최대주문가능수량 (Maximum Order Possible Quantity)
    pchs_avg_pric: str  # 매입평균가격
    hldg_qty: str  # 보유수량 (Holding Quantity)
    ord_unpr: str  # 주문단가 (Order Unit Price)
    rsvn_ord_psbl_qty: str  # 예약주문가능수량 (Reservation Order Possible Quantity)


class InquirePsblSellResponse(BaseResponse):
    """매도가능수량 조회 응답"""

    output: InquirePsblSellOutput


# ============================================================
# get_total_asset() - 총자산평가 조회
# ============================================================


class GetTotalAssetOutput1(TypedDict, total=False):
    """총자산평가 계좌 요약 정보"""

    dnca_tot_amt: str  # 예수금총액
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
    tot_evlu_amt: str  # 총평가금액 (Total Evaluation Amount)
    nass_amt: str  # 순자산금액 (Net Asset Amount)
    fncg_gld_auto_rdpt_yn: str  # 융자금자동상환여부
    pchs_amt_smtl_amt: str  # 매입금액합계금액
    evlu_amt_smtl_amt: str  # 평가금액합계금액 (Evaluation Amount Sum Total Amount)
    evlu_pfls_smtl_amt: (
        str  # 평가손익합계금액 (Evaluation Profit/Loss Sum Total Amount)
    )
    tot_stln_slng_chgs: str  # 총대주매각대금
    bfdy_tot_asst_evlu_amt: str  # 전일총자산평가금액
    asst_icdc_amt: str  # 자산증감액 (Asset Increase/Decrease Amount)
    asst_icdc_erng_rt: str  # 자산증감수익률 (%)


class GetTotalAssetOutput2(TypedDict, total=False):
    """총자산평가 상세 정보"""

    tot_dncl_amt: str  # 총예수금액 (Total Deposit and Cash Amount)
    nxdy_excc_amt: str  # 익일정산금액
    tlex_amt: str  # 제비용금액 (Tax/Levy Amount)
    rlzt_pfls: str  # 실현손익 (Realized Profit/Loss)
    unrlzt_pfls: str  # 미실현손익 (Unrealized Profit/Loss)


class GetTotalAssetResponse(BaseResponse):
    """총자산평가 조회 응답"""

    output1: GetTotalAssetOutput1
    output2: GetTotalAssetOutput2


# ============================================================
# inquire_balance_rlz_pl() - 잔고실현손익 조회
# ============================================================


class InquireBalanceRlzPlOutput1Item(TypedDict, total=False):
    """잔고실현손익 개별 종목 정보"""

    pdno: str  # 상품번호 (종목코드)
    prdt_name: str  # 상품명
    hldg_qty: str  # 보유수량
    pchs_avg_pric: str  # 매입평균가격
    pchs_amt: str  # 매입금액
    prpr: str  # 현재가
    evlu_amt: str  # 평가금액
    evlu_pfls_amt: str  # 평가손익금액
    evlu_pfls_rt: str  # 평가손익률 (%)
    evlu_erng_rt: str  # 평가수익률 (%)
    rlzt_pfls: str  # 실현손익 (Realized Profit/Loss)
    rlzt_pfls_rt: str  # 실현손익률 (Realized Profit/Loss Rate) %
    rlzt_erng_rt: str  # 실현수익률
    real_evlu_pfls: str  # 실평가손익
    real_evlu_pfls_erng_rt: str  # 실평가손익수익률
    ord_psbl_qty: str  # 주문가능수량


class InquireBalanceRlzPlResponse(BaseResponse):
    """잔고실현손익 조회 응답"""

    output1: List[InquireBalanceRlzPlOutput1Item]


# ============================================================
# inquire_period_trade_profit() - 기간별매매손익현황조회
# ============================================================


class InquirePeriodTradeProfitOutput1Item(TypedDict, total=False):
    """기간별매매손익 개별 항목"""

    trad_dt: str  # 매매일자 (Trade Date)
    pdno: str  # 상품번호 (종목코드)
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


class InquirePeriodTradeProfitOutput2(TypedDict, total=False):
    """기간별매매손익 요약 정보"""

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


class InquirePeriodTradeProfitResponse(BaseResponse):
    """기간별매매손익현황조회 응답"""

    output1: List[InquirePeriodTradeProfitOutput1Item]
    output2: InquirePeriodTradeProfitOutput2


# ============================================================
# inquire_period_profit() - 기간별손익일별합산조회 (TTTC8708R)
# ============================================================


class InquirePeriodProfitOutput1Item(TypedDict, total=False):
    """기간별손익일별합산 개별 항목 (일별 손익)"""

    trad_dt: str  # 거래일자 (Trade Date, YYYYMMDD)
    sll_amt: str  # 매도금액 (Sell Amount)
    buy_amt: str  # 매수금액 (Buy Amount)
    rlzt_pfls: str  # 실현손익 (Realized Profit/Loss)
    fee_smtl: str  # 수수료합계 (Fee Sum Total)
    tltx_smtl: str  # 제세금합계 (Tax/Levy Sum Total)
    tot_rlzt_pfls: str  # 총실현손익 (Total Realized Profit/Loss)


class InquirePeriodProfitOutput2(TypedDict, total=False):
    """기간별손익일별합산 요약 정보"""

    tot_sll_amt: str  # 총매도금액 (Total Sell Amount)
    tot_buy_amt: str  # 총매수금액 (Total Buy Amount)
    tot_rlzt_pfls: str  # 총실현손익 (Total Realized Profit/Loss)
    tot_fee: str  # 총수수료 (Total Fee)
    tot_tltx: str  # 총제세금 (Total Tax/Levy)


class InquirePeriodProfitResponse(BaseResponse):
    """기간별손익일별합산조회 응답"""

    output1: List[InquirePeriodProfitOutput1Item]
    output2: InquirePeriodProfitOutput2
