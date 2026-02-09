"""
Overseas Futures Response Types - 해외선물옵션 API 응답 타입 정의

해외선물옵션 API 응답 구조 (19개 API)
- 시세 8개: 현재가, 호가, 분봉, 일간체결추이, 상품정보
- 계좌 9개: 잔고, 예수금, 증거금, 주문가능, 주문내역, 체결내역, 기간손익
- 주문 2개: 주문, 정정취소
"""

from typing import List, TypedDict

from .common import BaseResponse

# ============================================================
# 1. get_price() - 해외선물 현재가 조회
# ============================================================


class OverseasFuturesPriceOutput(TypedDict, total=False):
    """해외선물 현재가 조회 output 필드"""

    # 기본 가격 정보
    rsym: str  # 실시간 종목코드
    exch_cd: str  # 거래소코드 (CME, EUREX 등)
    srs_cd: str  # 시리즈코드 (종목코드)
    curr: str  # 통화코드
    zdiv: str  # 소수점자리수

    # 현재가 정보
    last: str  # 현재가
    base: str  # 기준가
    sign: str  # 전일대비부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)
    diff: str  # 전일대비
    rate: str  # 등락률

    # OHLV 정보
    open: str  # 시가
    high: str  # 고가
    low: str  # 저가
    tvol: str  # 거래량
    tamt: str  # 거래대금

    # 호가 정보
    bprc: str  # 매수호가
    aprc: str  # 매도호가
    bqty: str  # 매수호가잔량
    aqty: str  # 매도호가잔량

    # 미결제
    oi: str  # 미결제약정


class OverseasFuturesPriceResponse(BaseResponse):
    """해외선물 현재가 조회 응답"""

    output: OverseasFuturesPriceOutput


# ============================================================
# 2. get_option_price() - 해외옵션 현재가 조회
# ============================================================


class OverseasOptionPriceOutput(TypedDict, total=False):
    """해외옵션 현재가 조회 output 필드"""

    rsym: str  # 실시간 종목코드
    exch_cd: str  # 거래소코드
    srs_cd: str  # 시리즈코드
    curr: str  # 통화코드
    zdiv: str  # 소수점자리수

    # 현재가 정보
    last: str  # 현재가
    base: str  # 기준가
    sign: str  # 전일대비부호
    diff: str  # 전일대비
    rate: str  # 등락률

    # OHLV
    open: str  # 시가
    high: str  # 고가
    low: str  # 저가
    tvol: str  # 거래량
    tamt: str  # 거래대금

    # 그릭스
    theo_pric: str  # 이론가
    iv: str  # 내재변동성
    delta: str  # 델타
    gamma: str  # 감마
    theta: str  # 세타
    vega: str  # 베가


class OverseasOptionPriceResponse(BaseResponse):
    """해외옵션 현재가 조회 응답"""

    output: OverseasOptionPriceOutput


# ============================================================
# 3. get_futures_orderbook() - 해외선물 호가 조회
# ============================================================


class OverseasFuturesOrderbookOutput1(TypedDict, total=False):
    """해외선물 호가 응답 - 매도호가"""

    askp1: str  # 매도호가1
    askp_rsqn1: str  # 매도호가잔량1
    askp2: str
    askp_rsqn2: str
    askp3: str
    askp_rsqn3: str
    askp4: str
    askp_rsqn4: str
    askp5: str
    askp_rsqn5: str
    total_askp_rsqn: str  # 총 매도호가잔량


class OverseasFuturesOrderbookOutput2(TypedDict, total=False):
    """해외선물 호가 응답 - 매수호가"""

    bidp1: str  # 매수호가1
    bidp_rsqn1: str  # 매수호가잔량1
    bidp2: str
    bidp_rsqn2: str
    bidp3: str
    bidp_rsqn3: str
    bidp4: str
    bidp_rsqn4: str
    bidp5: str
    bidp_rsqn5: str
    total_bidp_rsqn: str  # 총 매수호가잔량


class OverseasFuturesOrderbookResponse(BaseResponse):
    """해외선물 호가 조회 응답"""

    output1: OverseasFuturesOrderbookOutput1  # 매도호가
    output2: OverseasFuturesOrderbookOutput2  # 매수호가


# ============================================================
# 4. get_minute_chart() - 해외선물 분봉 조회
# ============================================================


class OverseasFuturesMinuteChartRow(TypedDict, total=False):
    """해외선물 분봉 차트 행"""

    bsop_date: str  # 영업일자 (YYYYMMDD)
    bsop_time: str  # 영업시간 (HHMMSS)
    open: str  # 시가
    high: str  # 고가
    low: str  # 저가
    last: str  # 종가 (현재가)
    tvol: str  # 거래량
    tamt: str  # 거래대금


class OverseasFuturesMinuteChartOutput1(TypedDict, total=False):
    """해외선물 분봉 조회 메타 정보"""

    index_key: str  # 다음 조회 키


class OverseasFuturesMinuteChartResponse(BaseResponse):
    """해외선물 분봉 조회 응답"""

    output1: OverseasFuturesMinuteChartOutput1
    output2: List[OverseasFuturesMinuteChartRow]


# ============================================================
# 5. get_daily_trend() - 해외선물 체결추이(일간)
# ============================================================


class OverseasFuturesDailyTrendRow(TypedDict, total=False):
    """해외선물 일간 체결추이 행"""

    bsop_date: str  # 영업일자
    open: str  # 시가
    high: str  # 고가
    low: str  # 저가
    last: str  # 종가
    sign: str  # 전일대비부호
    diff: str  # 전일대비
    rate: str  # 등락률
    tvol: str  # 거래량
    oi: str  # 미결제약정


class OverseasFuturesDailyTrendResponse(BaseResponse):
    """해외선물 체결추이(일간) 응답"""

    output1: dict  # 메타 정보
    output2: List[OverseasFuturesDailyTrendRow]


# ============================================================
# 6. get_futures_info() - 해외선물 상품기본정보
# ============================================================


class OverseasFuturesInfoOutput(TypedDict, total=False):
    """해외선물 상품기본정보 출력"""

    srs_cd: str  # 종목코드
    prdt_nm: str  # 상품명
    prdt_eng_nm: str  # 상품영문명
    exch_cd: str  # 거래소코드
    curr: str  # 통화코드
    zdiv: str  # 소수점자리수
    tick_sz: str  # 틱사이즈
    tick_val: str  # 틱가치
    ctrt_sz: str  # 계약크기
    lstg_date: str  # 상장일
    expr_date: str  # 만기일
    trdn_strt_time: str  # 거래시작시간
    trdn_end_time: str  # 거래종료시간


class OverseasFuturesInfoResponse(BaseResponse):
    """해외선물 상품기본정보 응답"""

    output: List[OverseasFuturesInfoOutput]


# ============================================================
# 7. get_balance() - 해외선물옵션 미결제내역(잔고) 조회
# ============================================================


class OverseasFuturesBalanceOutput(TypedDict, total=False):
    """해외선물옵션 잔고 조회 output 필드"""

    srs_cd: str  # 종목코드
    prdt_nm: str  # 상품명
    exch_cd: str  # 거래소코드
    fuop_dvsn: str  # 선물옵션구분 (01:선물, 02:옵션)
    sll_buy_dvsn_cd: str  # 매도매수구분코드 (01:매도, 02:매수)

    # 수량
    unsttl_qty: str  # 미결제수량 (Unsettled Quantity)
    ord_psbl_qty: str  # 주문가능수량

    # 가격
    avg_pchs_pric: str  # 평균매입가 (Average Purchase Price)
    now_pric: str  # 현재가
    evlu_amt: str  # 평가금액
    evlu_pfls_amt: str  # 평가손익금액
    evlu_pfls_rate: str  # 평가손익률


class OverseasFuturesBalanceResponse(BaseResponse):
    """해외선물옵션 잔고 조회 응답"""

    output: List[OverseasFuturesBalanceOutput]


# ============================================================
# 8. get_deposit() - 해외선물옵션 예수금 조회
# ============================================================


class OverseasFuturesDepositOutput(TypedDict, total=False):
    """해외선물옵션 예수금 조회 output 필드"""

    crcy_cd: str  # 통화코드
    dps_amt: str  # 예수금액 (Deposit Amount)
    ustl_pfls_amt: str  # 미결제손익금액
    tot_evlu_amt: str  # 총평가금액
    wdrw_psbl_amt: str  # 출금가능금액
    mrgn_amt: str  # 증거금액
    mrgn_rate: str  # 증거금률
    add_mrgn_amt: str  # 추가증거금액


class OverseasFuturesDepositResponse(BaseResponse):
    """해외선물옵션 예수금 조회 응답"""

    output: OverseasFuturesDepositOutput


# ============================================================
# 9. get_margin_detail() - 해외선물옵션 증거금상세
# ============================================================


class OverseasFuturesMarginOutput(TypedDict, total=False):
    """해외선물옵션 증거금상세 output 필드"""

    crcy_cd: str  # 통화코드
    tot_mrgn_amt: str  # 총증거금액
    init_mrgn_amt: str  # 개시증거금액
    maint_mrgn_amt: str  # 유지증거금액
    add_mrgn_amt: str  # 추가증거금액
    optn_prem_amt: str  # 옵션프리미엄금액
    ord_mrgn_amt: str  # 주문증거금액


class OverseasFuturesMarginResponse(BaseResponse):
    """해외선물옵션 증거금상세 응답"""

    output: OverseasFuturesMarginOutput


# ============================================================
# 10. get_order_amount() - 해외선물옵션 주문가능조회
# ============================================================


class OverseasFuturesOrderAmountOutput(TypedDict, total=False):
    """해외선물옵션 주문가능조회 output 필드"""

    ord_psbl_qty: str  # 주문가능수량
    new_ord_mrgn_amt: str  # 신규주문증거금액
    crcy_cd: str  # 통화코드


class OverseasFuturesOrderAmountResponse(BaseResponse):
    """해외선물옵션 주문가능조회 응답"""

    output: OverseasFuturesOrderAmountOutput


# ============================================================
# 11. get_today_orders() - 해외선물옵션 당일주문내역
# ============================================================


class OverseasFuturesTodayOrderRow(TypedDict, total=False):
    """해외선물옵션 당일주문내역 행"""

    ord_dt: str  # 주문일자
    ord_tmd: str  # 주문시각
    odno: str  # 주문번호
    orgn_odno: str  # 원주문번호
    srs_cd: str  # 종목코드
    prdt_nm: str  # 상품명
    sll_buy_dvsn_cd: str  # 매도매수구분코드
    ord_qty: str  # 주문수량
    ord_pric: str  # 주문가격
    ccld_qty: str  # 체결수량
    ccld_pric: str  # 체결가격
    rmn_qty: str  # 잔여수량
    ord_stat: str  # 주문상태


class OverseasFuturesTodayOrderResponse(BaseResponse):
    """해외선물옵션 당일주문내역 응답"""

    output: List[OverseasFuturesTodayOrderRow]


# ============================================================
# 12. get_daily_orders() - 해외선물옵션 일별 주문내역
# ============================================================


class OverseasFuturesDailyOrderRow(TypedDict, total=False):
    """해외선물옵션 일별 주문내역 행"""

    ord_dt: str  # 주문일자
    odno: str  # 주문번호
    srs_cd: str  # 종목코드
    prdt_nm: str  # 상품명
    sll_buy_dvsn_cd: str  # 매도매수구분코드
    ord_qty: str  # 주문수량
    ord_pric: str  # 주문가격
    ccld_qty: str  # 체결수량
    ccld_pric: str  # 체결가격
    ord_stat: str  # 주문상태


class OverseasFuturesDailyOrderResponse(BaseResponse):
    """해외선물옵션 일별 주문내역 응답"""

    output: List[OverseasFuturesDailyOrderRow]


# ============================================================
# 13. get_daily_executions() - 해외선물옵션 일별 체결내역
# ============================================================


class OverseasFuturesDailyExecutionRow(TypedDict, total=False):
    """해외선물옵션 일별 체결내역 행"""

    ccld_dt: str  # 체결일자
    ccld_tmd: str  # 체결시각
    odno: str  # 주문번호
    srs_cd: str  # 종목코드
    prdt_nm: str  # 상품명
    sll_buy_dvsn_cd: str  # 매도매수구분코드
    ccld_qty: str  # 체결수량
    ccld_pric: str  # 체결가격
    ccld_amt: str  # 체결금액
    fee_amt: str  # 수수료금액


class OverseasFuturesDailyExecutionResponse(BaseResponse):
    """해외선물옵션 일별 체결내역 응답"""

    output: List[OverseasFuturesDailyExecutionRow]
    output1: dict  # 합계 정보


# ============================================================
# 14. get_period_profit() - 해외선물옵션 기간계좌손익
# ============================================================


class OverseasFuturesPeriodProfitRow(TypedDict, total=False):
    """해외선물옵션 기간계좌손익 행"""

    bsop_date: str  # 영업일자
    crcy_cd: str  # 통화코드
    rlzt_pfls_amt: str  # 실현손익금액
    fee_amt: str  # 수수료금액
    net_pfls_amt: str  # 순손익금액


class OverseasFuturesPeriodProfitOutput2(TypedDict, total=False):
    """해외선물옵션 기간계좌손익 합계"""

    tot_rlzt_pfls_amt: str  # 총실현손익금액
    tot_fee_amt: str  # 총수수료금액
    tot_net_pfls_amt: str  # 총순손익금액


class OverseasFuturesPeriodProfitResponse(BaseResponse):
    """해외선물옵션 기간계좌손익 응답"""

    output1: List[OverseasFuturesPeriodProfitRow]
    output2: OverseasFuturesPeriodProfitOutput2


# ============================================================
# 15. get_period_transactions() - 해외선물옵션 기간계좌거래내역
# ============================================================


class OverseasFuturesPeriodTransRow(TypedDict, total=False):
    """해외선물옵션 기간계좌거래내역 행"""

    trns_dt: str  # 거래일자
    trns_type: str  # 거래유형
    crcy_cd: str  # 통화코드
    trns_amt: str  # 거래금액
    bal_amt: str  # 잔액


class OverseasFuturesPeriodTransResponse(BaseResponse):
    """해외선물옵션 기간계좌거래내역 응답"""

    output: List[OverseasFuturesPeriodTransRow]


# ============================================================
# 16. order() - 해외선물옵션 주문
# ============================================================


class OverseasFuturesOrderOutput(TypedDict, total=False):
    """해외선물옵션 주문 응답 output"""

    odno: str  # 주문번호
    ord_dt: str  # 주문일자
    ord_tmd: str  # 주문시각


class OverseasFuturesOrderResponse(BaseResponse):
    """해외선물옵션 주문 응답"""

    output: OverseasFuturesOrderOutput


# ============================================================
# 17. modify_cancel() - 해외선물옵션 정정취소주문
# ============================================================


class OverseasFuturesModifyCancelOutput(TypedDict, total=False):
    """해외선물옵션 정정취소주문 응답 output"""

    odno: str  # 주문번호
    orgn_odno: str  # 원주문번호
    ord_dt: str  # 주문일자
    ord_tmd: str  # 주문시각


class OverseasFuturesModifyCancelResponse(BaseResponse):
    """해외선물옵션 정정취소주문 응답"""

    output: OverseasFuturesModifyCancelOutput


# ============================================================
# __all__ 정의
# ============================================================

__all__ = [
    # 현재가/호가
    "OverseasFuturesPriceOutput",
    "OverseasFuturesPriceResponse",
    "OverseasOptionPriceOutput",
    "OverseasOptionPriceResponse",
    "OverseasFuturesOrderbookOutput1",
    "OverseasFuturesOrderbookOutput2",
    "OverseasFuturesOrderbookResponse",
    # 차트/추이
    "OverseasFuturesMinuteChartRow",
    "OverseasFuturesMinuteChartResponse",
    "OverseasFuturesDailyTrendRow",
    "OverseasFuturesDailyTrendResponse",
    # 상품정보
    "OverseasFuturesInfoOutput",
    "OverseasFuturesInfoResponse",
    # 잔고/계좌
    "OverseasFuturesBalanceOutput",
    "OverseasFuturesBalanceResponse",
    "OverseasFuturesDepositOutput",
    "OverseasFuturesDepositResponse",
    "OverseasFuturesMarginOutput",
    "OverseasFuturesMarginResponse",
    "OverseasFuturesOrderAmountOutput",
    "OverseasFuturesOrderAmountResponse",
    # 주문/체결내역
    "OverseasFuturesTodayOrderRow",
    "OverseasFuturesTodayOrderResponse",
    "OverseasFuturesDailyOrderRow",
    "OverseasFuturesDailyOrderResponse",
    "OverseasFuturesDailyExecutionRow",
    "OverseasFuturesDailyExecutionResponse",
    # 기간손익/거래내역
    "OverseasFuturesPeriodProfitRow",
    "OverseasFuturesPeriodProfitResponse",
    "OverseasFuturesPeriodTransRow",
    "OverseasFuturesPeriodTransResponse",
    # 주문
    "OverseasFuturesOrderOutput",
    "OverseasFuturesOrderResponse",
    "OverseasFuturesModifyCancelOutput",
    "OverseasFuturesModifyCancelResponse",
]
