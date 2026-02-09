"""
Futures Response Types - 선물옵션 관련 응답 타입 정의

국내선물옵션 API 응답 구조
"""

from typing import List, TypedDict

from .common import BaseResponse

# ============================================================
# 1. inquire_price() - 선물옵션 현재가 조회
# ============================================================


class FuturesPriceOutput(TypedDict, total=False):
    """선물옵션 현재가 조회 output 필드"""

    # 기본 가격 정보
    fuop_prpr: str  # 선물옵션 현재가 (Future/Option Present Price)
    prdy_vrss: str  # 전일 대비 (Previous Day Versus)
    prdy_vrss_sign: str  # 전일 대비 부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)
    prdy_ctrt: str  # 전일 대비율 (Previous Day Change Rate) %
    fuop_oprc: str  # 선물옵션 시가 (Future/Option Opening Price)
    fuop_hgpr: str  # 선물옵션 최고가 (Future/Option High Price)
    fuop_lwpr: str  # 선물옵션 최저가 (Future/Option Low Price)
    fuop_sdpr: str  # 선물옵션 기준가 (Future/Option Standard Price)

    # 거래량/미결제 정보
    acml_vol: str  # 누적 거래량 (Accumulated Volume)
    acml_tr_pbmn: str  # 누적 거래대금 (Accumulated Trade Price By Million)
    optn_open_intr_vol: str  # 옵션 미결제 약정량 (Option Open Interest Volume)
    fuop_open_intr_vol: str  # 선물 미결제 약정량

    # 종목 정보
    hts_kor_isnm: str  # HTS 한글 종목명 (HTS Korean Issue Name)
    item_code: str  # 종목코드
    fuop_kind_code: str  # 선물옵션 종류 코드 (F:선물, C:콜옵션, P:풋옵션)
    bstp_nmix_prpr: str  # 업종 지수 현재가
    bstp_nmix_prdy_vrss: str  # 업종 지수 전일대비

    # 이론가/내재변동성 (옵션)
    optn_theo_pric: str  # 옵션 이론가격 (Option Theoretical Price)
    impl_vola: str  # 내재변동성 (Implied Volatility)
    optn_delta: str  # 옵션 델타 (Option Delta)
    optn_gamma: str  # 옵션 감마 (Option Gamma)
    optn_theta: str  # 옵션 세타 (Option Theta)
    optn_vega: str  # 옵션 베가 (Option Vega)

    # 추가 정보
    lstn_avrg_pric: str  # 상장 평균가
    mrkt_warn_cls_code: str  # 시장경고구분코드
    sbst_pric: str  # 대용가격 (Substitute Price)


class FuturesPriceResponse(BaseResponse):
    """선물옵션 현재가 조회 응답"""

    output: FuturesPriceOutput


# ============================================================
# 2. inquire_asking_price() - 선물옵션 호가 조회
# ============================================================


class FuturesOrderbookOutput1(TypedDict, total=False):
    """선물옵션 호가 응답 - 매도호가"""

    askp1: str  # 매도호가1 (Ask Price 1)
    askp_rsqn1: str  # 매도호가잔량1 (Ask Price Residual Quantity 1)
    askp2: str  # 매도호가2
    askp_rsqn2: str  # 매도호가잔량2
    askp3: str  # 매도호가3
    askp_rsqn3: str  # 매도호가잔량3
    askp4: str  # 매도호가4
    askp_rsqn4: str  # 매도호가잔량4
    askp5: str  # 매도호가5
    askp_rsqn5: str  # 매도호가잔량5
    askp6: str  # 매도호가6
    askp_rsqn6: str  # 매도호가잔량6
    askp7: str  # 매도호가7
    askp_rsqn7: str  # 매도호가잔량7
    askp8: str  # 매도호가8
    askp_rsqn8: str  # 매도호가잔량8
    askp9: str  # 매도호가9
    askp_rsqn9: str  # 매도호가잔량9
    askp10: str  # 매도호가10
    askp_rsqn10: str  # 매도호가잔량10
    total_askp_rsqn: str  # 총 매도호가잔량


class FuturesOrderbookOutput2(TypedDict, total=False):
    """선물옵션 호가 응답 - 매수호가"""

    bidp1: str  # 매수호가1 (Bid Price 1)
    bidp_rsqn1: str  # 매수호가잔량1 (Bid Price Residual Quantity 1)
    bidp2: str  # 매수호가2
    bidp_rsqn2: str  # 매수호가잔량2
    bidp3: str  # 매수호가3
    bidp_rsqn3: str  # 매수호가잔량3
    bidp4: str  # 매수호가4
    bidp_rsqn4: str  # 매수호가잔량4
    bidp5: str  # 매수호가5
    bidp_rsqn5: str  # 매수호가잔량5
    bidp6: str  # 매수호가6
    bidp_rsqn6: str  # 매수호가잔량6
    bidp7: str  # 매수호가7
    bidp_rsqn7: str  # 매수호가잔량7
    bidp8: str  # 매수호가8
    bidp_rsqn8: str  # 매수호가잔량8
    bidp9: str  # 매수호가9
    bidp_rsqn9: str  # 매수호가잔량9
    bidp10: str  # 매수호가10
    bidp_rsqn10: str  # 매수호가잔량10
    total_bidp_rsqn: str  # 총 매수호가잔량


class FuturesOrderbookResponse(BaseResponse):
    """선물옵션 호가 조회 응답"""

    output1: FuturesOrderbookOutput1  # 매도호가
    output2: FuturesOrderbookOutput2  # 매수호가


# ============================================================
# 3. inquire_balance() - 선물옵션 잔고 조회
# ============================================================


class FuturesBalanceOutput(TypedDict, total=False):
    """선물옵션 잔고 조회 output 필드"""

    fuop_item_code: str  # 선물옵션 종목코드
    item_name: str  # 종목명
    futs_optn_kind_code: str  # 선물옵션종류코드 (F:선물, C:콜, P:풋)
    bstp_code: str  # 업종코드

    # 잔고 수량
    ord_psbl_qty: str  # 주문가능수량 (Order Possible Quantity)
    sll_buy_dvsn_cd: str  # 매도매수구분코드 (1:매도, 2:매수)
    bfdy_cprs_icdc: str  # 전일대비증감수량

    # 가격 정보
    avg_pric: str  # 평균가 (Average Price)
    prsnt_pric: str  # 현재가 (Present Price)
    fnoat_plamt: str  # 평가손익금액 (Floating Profit/Loss Amount)
    erng_rate: str  # 수익률 (Earning Rate) %

    # 청산/평가 정보
    lqd_amt: str  # 청산금액 (Liquidation Amount)
    lqd_psbl_qty: str  # 청산가능수량
    evlu_amt: str  # 평가금액 (Evaluation Amount)
    evlu_pfls_amt: str  # 평가손익금액

    # 증거금 정보
    dpsi_reqr_amt: str  # 예탁금필요금액 (Deposit Requirement Amount)
    maint_mrgn: str  # 유지증거금 (Maintenance Margin)
    ord_mrgn: str  # 주문증거금 (Order Margin)


class FuturesBalanceResponse(BaseResponse):
    """선물옵션 잔고 조회 응답"""

    output: List[FuturesBalanceOutput]  # 잔고 리스트


# ============================================================
# 4. inquire_daily_fuopchartprice() - 선물옵션 일별차트
# ============================================================


class FuturesDailyChartRow(TypedDict, total=False):
    """선물옵션 일별차트 행"""

    stck_bsop_date: str  # 주식영업일자 (YYYYMMDD)
    fuop_oprc: str  # 선물옵션 시가
    fuop_hgpr: str  # 선물옵션 최고가
    fuop_lwpr: str  # 선물옵션 최저가
    fuop_clpr: str  # 선물옵션 종가 (Close Price)
    acml_vol: str  # 누적거래량
    prdy_vrss: str  # 전일대비
    prdy_vrss_sign: str  # 전일대비부호
    prdy_ctrt: str  # 전일대비율
    optn_open_intr_vol: str  # 옵션미결제약정량


class FuturesDailyChartResponse(BaseResponse):
    """선물옵션 일별차트 조회 응답"""

    output: List[FuturesDailyChartRow]


# ============================================================
# 5. inquire_time_fuopchartprice() - 선물옵션 분봉차트
# ============================================================


class FuturesTimeChartRow(TypedDict, total=False):
    """선물옵션 분봉차트 행"""

    stck_cntg_hour: str  # 주식체결시간 (HHMMSS)
    fuop_oprc: str  # 선물옵션 시가
    fuop_hgpr: str  # 선물옵션 최고가
    fuop_lwpr: str  # 선물옵션 최저가
    fuop_prpr: str  # 선물옵션 현재가
    cntg_vol: str  # 체결거래량
    acml_vol: str  # 누적거래량


class FuturesTimeChartResponse(BaseResponse):
    """선물옵션 분봉차트 조회 응답"""

    output: List[FuturesTimeChartRow]


# ============================================================
# 6. order() - 선물옵션 주문
# ============================================================


class FuturesOrderOutput(TypedDict, total=False):
    """선물옵션 주문 응답 output"""

    odno: str  # 주문번호 (Order Number)
    ord_tmd: str  # 주문시각 (Order Time)
    ord_gno_brno: str  # 주문채번지점번호
    odno_brno: str  # 주문번호지점번호


class FuturesOrderResponse(BaseResponse):
    """선물옵션 주문 응답"""

    output: FuturesOrderOutput


# ============================================================
# 7. inquire_ccnl() - 선물옵션 체결내역
# ============================================================


class FuturesConclusionRow(TypedDict, total=False):
    """선물옵션 체결내역 행"""

    ord_dt: str  # 주문일자 (YYYYMMDD)
    ord_gno_brno: str  # 주문채번지점번호
    odno: str  # 주문번호
    orgn_odno: str  # 원주문번호
    fuop_item_code: str  # 선물옵션종목코드
    sll_buy_dvsn_cd: str  # 매도매수구분코드 (1:매도, 2:매수)
    ord_qty: str  # 주문수량
    ord_unpr: str  # 주문단가
    ccld_qty: str  # 체결수량
    ccld_unpr: str  # 체결단가
    ccld_amt: str  # 체결금액
    rmn_qty: str  # 잔여수량
    rjct_qty: str  # 거부수량
    ccld_cndt_name: str  # 체결조건명


class FuturesConclusionResponse(BaseResponse):
    """선물옵션 체결내역 조회 응답"""

    output: List[FuturesConclusionRow]


# ============================================================
# 8. display_board_callput() - 옵션 콜/풋 전광판
# ============================================================


class DisplayBoardCallPutRow(TypedDict, total=False):
    """옵션 콜/풋 전광판 행"""

    item_code: str  # 종목코드
    item_name: str  # 종목명
    fuop_prpr: str  # 선물옵션 현재가
    prdy_vrss: str  # 전일대비
    prdy_ctrt: str  # 전일대비율
    acml_vol: str  # 누적거래량
    optn_theo_pric: str  # 옵션이론가
    impl_vola: str  # 내재변동성
    optn_delta: str  # 델타
    optn_gamma: str  # 감마


class DisplayBoardCallPutResponse(BaseResponse):
    """옵션 콜/풋 전광판 응답"""

    output1: List[DisplayBoardCallPutRow]  # 콜옵션 리스트
    output2: List[DisplayBoardCallPutRow]  # 풋옵션 리스트


# ============================================================
# 9. inquire_deposit() - 선물옵션 예수금/총자산
# ============================================================


class FuturesDepositOutput(TypedDict, total=False):
    """선물옵션 예수금 조회 output"""

    fuop_dps_amt: str  # 선물옵션예수금액 (Futures/Options Deposit Amount)
    fuop_evlu_pfls_amt: str  # 선물옵션평가손익금액
    tot_evlu_amt: str  # 총평가금액
    tot_asst_amt: str  # 총자산금액 (Total Asset Amount)
    maint_mrgn_amt: str  # 유지증거금액 (Maintenance Margin Amount)
    addp_amt: str  # 추가증거금액
    nass_amt: str  # 순자산금액 (Net Asset Amount)


class FuturesDepositResponse(BaseResponse):
    """선물옵션 예수금 조회 응답"""

    output: FuturesDepositOutput


# ============================================================
# __all__ 정의
# ============================================================

__all__ = [
    # 현재가/호가
    "FuturesPriceOutput",
    "FuturesPriceResponse",
    "FuturesOrderbookOutput1",
    "FuturesOrderbookOutput2",
    "FuturesOrderbookResponse",
    # 잔고/계좌
    "FuturesBalanceOutput",
    "FuturesBalanceResponse",
    "FuturesDepositOutput",
    "FuturesDepositResponse",
    # 차트
    "FuturesDailyChartRow",
    "FuturesDailyChartResponse",
    "FuturesTimeChartRow",
    "FuturesTimeChartResponse",
    # 주문/체결
    "FuturesOrderOutput",
    "FuturesOrderResponse",
    "FuturesConclusionRow",
    "FuturesConclusionResponse",
    # 전광판
    "DisplayBoardCallPutRow",
    "DisplayBoardCallPutResponse",
]
