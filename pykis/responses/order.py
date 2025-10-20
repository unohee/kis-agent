"""
Order Response Types - 주문 관련 응답 타입 정의

현금주문, 신용주문, 정정/취소 등 Order API 응답 구조
"""

from typing import List, TypedDict

from .common import BaseResponse


# ============================================================
# order_cash() - 현금 주문 (매수/매도)
# ============================================================


class OrderCashOutput(TypedDict, total=False):
    """현금 주문 output 필드"""

    KRX_FWDG_ORD_ORGNO: str  # KRX 주문조직번호 (KRX Forward Order Organization Number)
    ODNO: str  # 주문번호 (Order Number)
    ORD_TMD: str  # 주문시각 (Order Time, HHMMSS)


class OrderCashResponse(BaseResponse):
    """현금 주문 응답 (매수/매도)"""

    output: OrderCashOutput


# ============================================================
# order_credit_buy() - 신용 매수 주문
# ============================================================


class OrderCreditBuyOutput(TypedDict, total=False):
    """신용 매수 주문 output 필드"""

    KRX_FWDG_ORD_ORGNO: str  # KRX 주문조직번호
    ODNO: str  # 주문번호
    ORD_TMD: str  # 주문시각 (HHMMSS)
    LOAN_DT: str  # 대출일자 (Loan Date, YYYYMMDD)


class OrderCreditBuyResponse(BaseResponse):
    """신용 매수 주문 응답"""

    output: OrderCreditBuyOutput


# ============================================================
# order_credit_sell() - 신용 매도 주문
# ============================================================


class OrderCreditSellOutput(TypedDict, total=False):
    """신용 매도 주문 output 필드"""

    KRX_FWDG_ORD_ORGNO: str  # KRX 주문조직번호
    ODNO: str  # 주문번호
    ORD_TMD: str  # 주문시각 (HHMMSS)


class OrderCreditSellResponse(BaseResponse):
    """신용 매도 주문 응답"""

    output: OrderCreditSellOutput


# ============================================================
# order_rvsecncl() - 주문 정정/취소
# ============================================================


class OrderRvsecnclOutput(TypedDict, total=False):
    """주문 정정/취소 output 필드"""

    KRX_FWDG_ORD_ORGNO: str  # KRX 주문조직번호
    ODNO: str  # 주문번호
    ORD_TMD: str  # 주문시각 (HHMMSS)
    RVSE_CNCL_DVSN_CD: str  # 정정취소구분코드 (Revise/Cancel Division Code)


class OrderRvsecnclResponse(BaseResponse):
    """주문 정정/취소 응답"""

    output: OrderRvsecnclOutput


# ============================================================
# inquire_psbl_rvsecncl() - 정정취소가능주문 조회
# ============================================================


class InquirePsblRvsecnclItem(TypedDict, total=False):
    """정정취소가능 주문 개별 항목"""

    ord_dt: str  # 주문일자 (Order Date, YYYYMMDD)
    ord_gno_brno: str  # 주문채번지점번호
    odno: str  # 주문번호
    orgn_odno: str  # 원주문번호
    pdno: str  # 상품번호 (종목코드)
    prdt_name: str  # 상품명
    sll_buy_dvsn_cd: str  # 매도매수구분코드 (01:매도, 02:매수)
    sll_buy_dvsn_cd_name: str  # 매도매수구분코드명
    ord_qty: str  # 주문수량
    ord_unpr: str  # 주문단가
    ord_tmd: str  # 주문시각 (HHMMSS)
    tot_ccld_qty: str  # 총체결수량
    psbl_qty: str  # 가능수량 (Possible Quantity) - 정정/취소 가능 수량
    avg_prvs: str  # 평균가
    cncl_yn: str  # 취소여부 (Y/N)
    tot_ccld_amt: str  # 총체결금액
    rmn_qty: str  # 잔여수량 (Remaining Quantity)
    ord_dvsn_name: str  # 주문구분명


class InquirePsblRvsecnclResponse(BaseResponse):
    """정정취소가능주문 조회 응답"""

    output: List[InquirePsblRvsecnclItem]


# ============================================================
# order_resv() - 예약 주문
# ============================================================


class OrderResvOutput(TypedDict, total=False):
    """예약 주문 output 필드"""

    RSVN_ORD_SEQ: str  # 예약주문일련번호 (Reservation Order Sequence)
    ORD_TMD: str  # 주문시각 (HHMMSS)


class OrderResvResponse(BaseResponse):
    """예약 주문 응답"""

    output: OrderResvOutput


# ============================================================
# order_resv_rvsecncl() - 예약주문 정정/취소
# ============================================================


class OrderResvRvsecnclOutput(TypedDict, total=False):
    """예약주문 정정/취소 output 필드"""

    RSVN_ORD_SEQ: str  # 예약주문일련번호
    ORD_TMD: str  # 주문시각 (HHMMSS)
    RVSE_CNCL_DVSN_CD: str  # 정정취소구분코드


class OrderResvRvsecnclResponse(BaseResponse):
    """예약주문 정정/취소 응답"""

    output: OrderResvRvsecnclOutput


# ============================================================
# order_resv_ccnl() - 예약주문 조회
# ============================================================


class OrderResvCcnlItem(TypedDict, total=False):
    """예약주문 개별 항목"""

    rsvn_ord_seq: str  # 예약주문일련번호
    rsvn_ord_dt: str  # 예약주문일자 (YYYYMMDD)
    pdno: str  # 상품번호 (종목코드)
    prdt_name: str  # 상품명
    sll_buy_dvsn_cd: str  # 매도매수구분코드 (01:매도, 02:매수)
    sll_buy_dvsn_cd_name: str  # 매도매수구분코드명
    ord_qty: str  # 주문수량
    ord_unpr: str  # 주문단가
    ord_dvsn_cd: str  # 주문구분코드
    ord_dvsn_cd_name: str  # 주문구분코드명
    rsvn_ord_objt_dt: str  # 예약주문대상일자 (Reservation Order Object Date, YYYYMMDD)
    rsvn_ord_objt_tmd: str  # 예약주문대상시각 (Reservation Order Object Time, HHMMSS)
    prcs_yn: str  # 처리여부 (Process Yes/No, Y/N)
    cncl_yn: str  # 취소여부 (Y/N)


class OrderResvCcnlResponse(BaseResponse):
    """예약주문 조회 응답"""

    output: List[OrderResvCcnlItem]
