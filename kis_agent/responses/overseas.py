"""
Overseas Stock Response Types - 해외주식 응답 타입 정의

해외주식 시세 조회, 호가, 분봉 등 Overseas Stock API 응답 구조

지원 거래소:
- 미국: NAS (NASDAQ), NYS (NYSE), AMS (AMEX)
- 아시아: HKS (홍콩), TSE (도쿄), SHS (상해), SZS (심천), HSX (호치민), HNX (하노이)
"""

from typing import List, TypedDict

from .common import BaseResponse

# ============================================================
# get_price() - 해외주식 현재체결가 조회 (HHDFS00000300)
# ============================================================


class OverseasPriceOutput(TypedDict, total=False):
    """해외주식 현재체결가 output 필드"""

    rsym: str  # 실시간조회종목코드 (Real-time Symbol)
    zdiv: str  # 소수점자리수 (Decimal Digit)
    base: str  # 전일종가 (Base Price - Previous Close)
    pvol: str  # 전일거래량 (Previous Volume)
    last: str  # 현재가 (Last Price)
    sign: str  # 대비부호 (Sign: 1=상한, 2=상승, 3=보합, 4=하한, 5=하락)
    diff: str  # 전일대비 (Difference from Previous)
    rate: str  # 등락률 (Rate of Change) %
    tvol: str  # 거래량 (Trade Volume)
    tamt: str  # 거래대금 (Trade Amount)
    ordy: str  # 매수가능여부 (Orderable Yes/No)


class OverseasPriceResponse(BaseResponse, total=False):
    """해외주식 현재체결가 응답"""

    output: OverseasPriceOutput


# ============================================================
# get_price_detail() - 해외주식 현재가 상세 조회 (HHDFS76200200)
# ============================================================


class OverseasPriceDetailOutput(TypedDict, total=False):
    """해외주식 현재가 상세 output 필드"""

    rsym: str  # 실시간조회종목코드
    zdiv: str  # 소수점자리수
    base: str  # 전일종가
    pvol: str  # 전일거래량
    last: str  # 현재가
    sign: str  # 대비부호
    diff: str  # 전일대비
    rate: str  # 등락률
    tvol: str  # 거래량
    tamt: str  # 거래대금
    h52p: str  # 52주최고가 (52-week High Price)
    l52p: str  # 52주최저가 (52-week Low Price)
    perx: str  # PER (Price Earning Ratio)
    pbrx: str  # PBR (Price Book Ratio)
    epsx: str  # EPS (Earning Per Share)
    bpsx: str  # BPS (Book value Per Share)
    shar: str  # 상장주수 (Shares Outstanding)
    mcap: str  # 시가총액 (Market Cap)
    tomv: str  # 거래대금 (백만) (Trade Amount in Million)
    t_xprc: str  # 원화환산가격 (KRW Converted Price)
    t_rate: str  # 원화환율 (Exchange Rate)
    e_icod: str  # 업종코드 (Industry Code)


class OverseasPriceDetailResponse(BaseResponse, total=False):
    """해외주식 현재가 상세 응답"""

    output: OverseasPriceDetailOutput


# ============================================================
# get_daily_price() - 해외주식 기간별 시세 조회 (HHDFS76240000)
# ============================================================


class OverseasDailyPriceOutput1(TypedDict, total=False):
    """해외주식 기간별 시세 output1 - 종목 기본 정보"""

    rsym: str  # 실시간조회종목코드
    zdiv: str  # 소수점자리수
    nrec: str  # 레코드갯수 (Number of Records)


class OverseasDailyPriceOutput2(TypedDict, total=False):
    """해외주식 기간별 시세 output2 - 일별 시세"""

    xymd: str  # 일자 (YYYYMMDD) (Year Month Day)
    clos: str  # 종가 (Close Price)
    sign: str  # 대비부호
    diff: str  # 전일대비
    rate: str  # 등락률
    open: str  # 시가 (Open Price)
    high: str  # 고가 (High Price)
    low: str  # 저가 (Low Price)
    tvol: str  # 거래량
    tamt: str  # 거래대금
    pbid: str  # 매수호가 (Bid Price)
    vbid: str  # 매수잔량 (Bid Volume)
    pask: str  # 매도호가 (Ask Price)
    vask: str  # 매도잔량 (Ask Volume)


class OverseasDailyPriceResponse(BaseResponse, total=False):
    """해외주식 기간별 시세 응답"""

    output1: OverseasDailyPriceOutput1
    output2: List[OverseasDailyPriceOutput2]


# ============================================================
# get_minute_price() - 해외주식 분봉 조회 (HHDFS76950200)
# ============================================================


class OverseasMinutePriceOutput1(TypedDict, total=False):
    """해외주식 분봉 output1 - 종목 기본 정보"""

    rsym: str  # 실시간조회종목코드
    zdiv: str  # 소수점자리수


class OverseasMinutePriceOutput2(TypedDict, total=False):
    """해외주식 분봉 output2 - 분봉 데이터"""

    tymd: str  # 일자 (YYYYMMDD)
    xhms: str  # 시간 (HHMMSS) (Hour Minute Second)
    open: str  # 시가
    high: str  # 고가
    low: str  # 저가
    last: str  # 종가
    evol: str  # 거래량 (Executed Volume)
    eamt: str  # 거래대금 (Executed Amount)


class OverseasMinutePriceResponse(BaseResponse, total=False):
    """해외주식 분봉 응답"""

    output1: OverseasMinutePriceOutput1
    output2: List[OverseasMinutePriceOutput2]


# ============================================================
# get_orderbook() - 해외주식 10호가 조회 (HHDFS76200100)
# ============================================================


class OverseasOrderbookOutput1(TypedDict, total=False):
    """해외주식 10호가 output1 - 종목 기본 정보"""

    rsym: str  # 실시간조회종목코드
    zdiv: str  # 소수점자리수


class OverseasOrderbookOutput2(TypedDict, total=False):
    """해외주식 10호가 output2 - 호가 데이터"""

    # 매도호가 (Ask Price) 1~10
    pask1: str
    pask2: str
    pask3: str
    pask4: str
    pask5: str
    pask6: str
    pask7: str
    pask8: str
    pask9: str
    pask10: str

    # 매도잔량 (Ask Volume) 1~10
    vask1: str
    vask2: str
    vask3: str
    vask4: str
    vask5: str
    vask6: str
    vask7: str
    vask8: str
    vask9: str
    vask10: str

    # 매수호가 (Bid Price) 1~10
    pbid1: str
    pbid2: str
    pbid3: str
    pbid4: str
    pbid5: str
    pbid6: str
    pbid7: str
    pbid8: str
    pbid9: str
    pbid10: str

    # 매수잔량 (Bid Volume) 1~10
    vbid1: str
    vbid2: str
    vbid3: str
    vbid4: str
    vbid5: str
    vbid6: str
    vbid7: str
    vbid8: str
    vbid9: str
    vbid10: str

    # 거래 정보
    tamt: str  # 거래대금
    tvol: str  # 거래량


class OverseasOrderbookResponse(BaseResponse, total=False):
    """해외주식 10호가 응답"""

    output1: OverseasOrderbookOutput1
    output2: OverseasOrderbookOutput2


# ============================================================
# get_stock_info() - 해외주식 상품기본정보 조회 (CTPF1702R)
# ============================================================


class OverseasStockInfoOutput(TypedDict, total=False):
    """해외주식 상품기본정보 output 필드"""

    pdno: str  # 상품번호 (Product Number)
    prdt_name: str  # 상품명 (Product Name)
    prdt_eng_name: str  # 상품영문명 (Product English Name)
    natn_cd: str  # 국가코드 (Nation Code)
    tr_mket_name: str  # 거래시장명 (Trade Market Name)
    sctg_name: str  # 업종명 (Sector Category Name)
    lstg_stck_num: str  # 상장주식수 (Listed Stock Number)
    crcy_cd: str  # 통화코드 (Currency Code: USD, HKD, CNY, JPY, VND)
    lstg_dt: str  # 상장일 (Listing Date)


class OverseasStockInfoResponse(BaseResponse, total=False):
    """해외주식 상품기본정보 응답"""

    output: OverseasStockInfoOutput


# ============================================================
# get_ccnl() - 해외주식 체결정보 조회 (HHDFS76200300)
# ============================================================


class OverseasCcnlOutput1(TypedDict, total=False):
    """해외주식 체결정보 output1 - 종목 기본 정보"""

    rsym: str  # 실시간조회종목코드
    zdiv: str  # 소수점자리수


class OverseasCcnlOutput2(TypedDict, total=False):
    """해외주식 체결정보 output2 - 체결 내역"""

    tymd: str  # 일자 (YYYYMMDD)
    xhms: str  # 체결시각 (HHMMSS)
    last: str  # 체결가
    diff: str  # 전일대비
    sign: str  # 대비부호
    tvol: str  # 거래량
    tamt: str  # 거래대금


class OverseasCcnlResponse(BaseResponse, total=False):
    """해외주식 체결정보 응답"""

    output1: OverseasCcnlOutput1
    output2: List[OverseasCcnlOutput2]


# ============================================================
# get_holiday() - 해외거래소 휴장일 조회 (CTOS5011R)
# ============================================================


class OverseasHolidayOutput(TypedDict, total=False):
    """해외거래소 휴장일 output 필드"""

    trad_dt: str  # 거래일자 (Trade Date)
    gubn: str  # 구분
    natn_cd: str  # 국가코드 (Nation Code)
    natn_name: str  # 국가명 (Nation Name)
    hldy_dt: str  # 휴장일 (Holiday Date)
    hldy_nm: str  # 휴장일명 (Holiday Name)


class OverseasHolidayResponse(BaseResponse, total=False):
    """해외거래소 휴장일 응답"""

    output: List[OverseasHolidayOutput]


# ============================================================
# get_news_title() - 해외뉴스종합(제목) 조회 (HHPSTH60100C1)
# ============================================================


class OverseasNewsOutput(TypedDict, total=False):
    """해외뉴스종합 output 필드"""

    data_dt: str  # 등록일자 (Data Date)
    data_tm: str  # 등록시간 (Data Time)
    news_sn: str  # 뉴스순번 (News Serial Number)
    natn_cd: str  # 국가코드 (Nation Code)
    news_gb: str  # 뉴스구분 (News Category)
    news_titl: str  # 뉴스제목 (News Title)


class OverseasNewsResponse(BaseResponse, total=False):
    """해외뉴스종합 응답"""

    output: List[OverseasNewsOutput]


# ============================================================
# get_industry_theme() - 해외주식 업종/테마 조회 (HHDFS76370000)
# ============================================================


class OverseasIndustryThemeOutput1(TypedDict, total=False):
    """해외주식 업종/테마 output1 - 요약 정보"""

    rsym: str  # 실시간조회종목코드
    zdiv: str  # 소수점자리수


class OverseasIndustryThemeOutput2(TypedDict, total=False):
    """해외주식 업종/테마 output2 - 상세 리스트"""

    pass  # API 문서에 따라 추후 상세 정의


class OverseasIndustryThemeResponse(BaseResponse, total=False):
    """해외주식 업종/테마 응답"""

    output1: OverseasIndustryThemeOutput1
    output2: List[OverseasIndustryThemeOutput2]


# ============================================================
# get_balance() - 해외주식 잔고 조회 (TTTS3012R)
# ============================================================


class OverseasBalanceOutput1Item(TypedDict, total=False):
    """해외주식 잔고 output1 - 보유종목 항목"""

    ovrs_pdno: str  # 해외종목번호 (Overseas Product Number)
    ovrs_item_name: str  # 해외종목명 (Overseas Item Name)
    frcr_evlu_pfls_amt: str  # 외화평가손익금액 (Foreign Currency Eval P/L Amount)
    evlu_pfls_rt: str  # 평가손익율 (Eval P/L Rate)
    pchs_avg_pric: str  # 매입평균가격 (Purchase Average Price)
    ovrs_cblc_qty: str  # 해외잔고수량 (Overseas Balance Quantity)
    ord_psbl_qty: str  # 주문가능수량 (Order Possible Quantity)
    frcr_pchs_amt1: str  # 외화매입금액 (Foreign Currency Purchase Amount)
    ovrs_stck_evlu_amt: str  # 해외주식평가금액 (Overseas Stock Eval Amount)
    now_pric2: str  # 현재가격 (Current Price)
    tr_crcy_cd: str  # 거래통화코드 (Trade Currency Code)
    ovrs_excg_cd: str  # 해외거래소코드 (Overseas Exchange Code)


class OverseasBalanceOutput2(TypedDict, total=False):
    """해외주식 잔고 output2 - 요약 정보"""

    tot_evlu_pfls_amt: str  # 총평가손익금액 (Total Eval P/L Amount)
    tot_pftrt: str  # 총수익률 (Total Profit Rate)
    frcr_buy_amt_smtl1: str  # 외화매수금액합계 (Foreign Currency Buy Amount Sum)
    ovrs_rlzt_pfls_amt: str  # 해외실현손익금액 (Overseas Realized P/L Amount)
    ovrs_tot_pfls: str  # 해외총손익 (Overseas Total P/L)
    tot_evlu_amt: str  # 총평가금액 (Total Eval Amount)


class OverseasBalanceResponse(BaseResponse, total=False):
    """해외주식 잔고 응답"""

    output1: List[OverseasBalanceOutput1Item]
    output2: OverseasBalanceOutput2


# ============================================================
# get_order_history() - 해외주식 주문체결내역 조회 (TTTS3035R)
# ============================================================


class OverseasOrderHistoryOutput(TypedDict, total=False):
    """해외주식 주문체결내역 output 항목"""

    ord_dt: str  # 주문일자 (Order Date)
    ord_gno_brno: str  # 주문채번지점번호 (Order Generation Branch Number)
    odno: str  # 주문번호 (Order Number)
    orgn_odno: str  # 원주문번호 (Original Order Number)
    sll_buy_dvsn_cd: str  # 매도매수구분코드 (Sell/Buy Division Code)
    sll_buy_dvsn_cd_name: str  # 매도매수구분명 (Sell/Buy Division Name)
    rvse_cncl_dvsn: str  # 정정취소구분 (Revise/Cancel Division)
    pdno: str  # 상품번호 (Product Number)
    prdt_name: str  # 상품명 (Product Name)
    ft_ord_qty: str  # FT주문수량 (FT Order Quantity)
    ft_ord_unpr3: str  # FT주문단가 (FT Order Unit Price)
    ft_ccld_qty: str  # FT체결수량 (FT Concluded Quantity)
    ft_ccld_unpr3: str  # FT체결단가 (FT Concluded Unit Price)
    nccs_qty: str  # 미체결수량 (Non-Concluded Quantity)
    ord_tmd: str  # 주문시각 (Order Time)
    tr_crcy_cd: str  # 거래통화코드 (Trade Currency Code)
    ovrs_excg_cd: str  # 해외거래소코드 (Overseas Exchange Code)


class OverseasOrderHistoryResponse(BaseResponse, total=False):
    """해외주식 주문체결내역 응답"""

    output: List[OverseasOrderHistoryOutput]


# ============================================================
# get_unfilled_orders() - 해외주식 미체결내역 조회 (TTTS3018R)
# ============================================================


class OverseasUnfilledOrderOutput(TypedDict, total=False):
    """해외주식 미체결내역 output 항목"""

    ord_dt: str  # 주문일자 (Order Date)
    ord_gno_brno: str  # 주문채번지점번호 (Order Generation Branch Number)
    odno: str  # 주문번호 (Order Number)
    orgn_odno: str  # 원주문번호 (Original Order Number)
    pdno: str  # 상품번호 (Product Number)
    prdt_name: str  # 상품명 (Product Name)
    sll_buy_dvsn_cd: str  # 매도매수구분코드 (Sell/Buy Division Code)
    ft_ord_qty: str  # FT주문수량 (FT Order Quantity)
    ft_ord_unpr3: str  # FT주문단가 (FT Order Unit Price)
    ft_ccld_qty: str  # FT체결수량 (FT Concluded Quantity)
    nccs_qty: str  # 미체결수량 (Non-Concluded Quantity)
    ord_tmd: str  # 주문시각 (Order Time)
    ovrs_excg_cd: str  # 해외거래소코드 (Overseas Exchange Code)
    tr_crcy_cd: str  # 거래통화코드 (Trade Currency Code)


class OverseasUnfilledOrderResponse(BaseResponse, total=False):
    """해외주식 미체결내역 응답"""

    output: List[OverseasUnfilledOrderOutput]


# ============================================================
# get_buyable_amount() - 해외주식 매수가능금액 조회 (TTTS3007R)
# ============================================================


class OverseasBuyableAmountOutput(TypedDict, total=False):
    """해외주식 매수가능금액 output 필드"""

    ovrs_ord_psbl_amt: str  # 해외주문가능금액 (Overseas Order Possible Amount)
    frcr_ord_psbl_amt1: str  # 외화주문가능금액 (Foreign Currency Order Possible Amount)
    max_ord_psbl_qty: str  # 최대주문가능수량 (Max Order Possible Quantity)
    echm_af_ord_psbl_amt: (
        str  # 환전후주문가능금액 (Exchange After Order Possible Amount)
    )
    ord_psbl_frcr_amt: str  # 주문가능외화금액 (Order Possible Foreign Currency Amount)
    ovrs_excg_cd: str  # 해외거래소코드 (Overseas Exchange Code)
    tr_crcy_cd: str  # 거래통화코드 (Trade Currency Code)


class OverseasBuyableAmountResponse(BaseResponse, total=False):
    """해외주식 매수가능금액 응답"""

    output: OverseasBuyableAmountOutput


# ============================================================
# get_present_balance() - 해외주식 체결기준현재잔고 조회 (CTRP6504R)
# ============================================================


class OverseasPresentBalanceOutput1Item(TypedDict, total=False):
    """해외주식 체결기준현재잔고 output1 - 보유종목 항목"""

    cano: str  # 계좌번호 (Account Number)
    acnt_prdt_cd: str  # 계좌상품코드 (Account Product Code)
    prdt_name: str  # 상품명 (Product Name)
    frcr_pchs_amt: str  # 외화매입금액 (Foreign Currency Purchase Amount)
    ovrs_cblc_qty: str  # 해외잔고수량 (Overseas Balance Quantity)
    pchs_avg_pric: str  # 매입평균가격 (Purchase Average Price)
    frcr_evlu_amt: str  # 외화평가금액 (Foreign Currency Eval Amount)
    evlu_pfls_amt: str  # 평가손익금액 (Eval P/L Amount)
    evlu_pfls_rt: str  # 평가손익율 (Eval P/L Rate)


class OverseasPresentBalanceOutput2(TypedDict, total=False):
    """해외주식 체결기준현재잔고 output2 - 요약 정보"""

    frcr_pchs_amt_smtl: str  # 외화매입금액합계 (Foreign Currency Purchase Amount Sum)
    frcr_evlu_amt_smtl: str  # 외화평가금액합계 (Foreign Currency Eval Amount Sum)
    evlu_pfls_amt_smtl: str  # 평가손익금액합계 (Eval P/L Amount Sum)


class OverseasPresentBalanceResponse(BaseResponse, total=False):
    """해외주식 체결기준현재잔고 응답"""

    output1: List[OverseasPresentBalanceOutput1Item]
    output2: OverseasPresentBalanceOutput2


# ============================================================
# get_period_profit() - 해외주식 기간손익 조회 (TTTS3039R)
# ============================================================


class OverseasPeriodProfitOutput1Item(TypedDict, total=False):
    """해외주식 기간손익 output1 - 종목별 손익 항목"""

    ovrs_pdno: str  # 해외상품번호 (Overseas Product Number)
    ovrs_item_name: str  # 해외종목명 (Overseas Item Name)
    frcr_sll_amt_smtl: str  # 외화매도금액합계 (Foreign Currency Sell Amount Sum)
    frcr_buy_amt_smtl: str  # 외화매수금액합계 (Foreign Currency Buy Amount Sum)
    ovrs_rlzt_pfls_amt: str  # 해외실현손익금액 (Overseas Realized P/L Amount)
    pftrt: str  # 수익률 (Profit Rate)
    sll_qty: str  # 매도수량 (Sell Quantity)
    buy_qty: str  # 매수수량 (Buy Quantity)
    tr_crcy_cd: str  # 거래통화코드 (Trade Currency Code)


class OverseasPeriodProfitOutput2(TypedDict, total=False):
    """해외주식 기간손익 output2 - 요약 정보"""

    frcr_sll_amt_smtl: str  # 외화매도금액합계 (Foreign Currency Sell Amount Sum)
    frcr_buy_amt_smtl: str  # 외화매수금액합계 (Foreign Currency Buy Amount Sum)
    ovrs_rlzt_pfls_amt: str  # 해외실현손익금액 (Overseas Realized P/L Amount)


class OverseasPeriodProfitResponse(BaseResponse, total=False):
    """해외주식 기간손익 응답"""

    output1: List[OverseasPeriodProfitOutput1Item]
    output2: OverseasPeriodProfitOutput2


# ============================================================
# get_reserve_order_list() - 해외주식 예약주문내역 조회 (TTTT3039R)
# ============================================================


class OverseasReserveOrderOutput(TypedDict, total=False):
    """해외주식 예약주문내역 output 항목"""

    rsvn_ord_seq: str  # 예약주문순번 (Reserve Order Sequence)
    rsvn_ord_dt: str  # 예약주문일자 (Reserve Order Date)
    rsvn_ord_rcit_dt: str  # 예약주문접수일자 (Reserve Order Receipt Date)
    ord_dvsn_cd: str  # 주문구분코드 (Order Division Code)
    sll_buy_dvsn_cd: str  # 매도매수구분코드 (Sell/Buy Division Code)
    pdno: str  # 상품번호 (Product Number)
    prdt_name: str  # 상품명 (Product Name)
    rsvn_ord_qty: str  # 예약주문수량 (Reserve Order Quantity)
    rsvn_ord_pric: str  # 예약주문가격 (Reserve Order Price)
    rsvn_ord_rcit_pric: str  # 예약주문접수가격 (Reserve Order Receipt Price)
    rsvn_ord_stat_cd: str  # 예약주문상태코드 (Reserve Order Status Code)
    ovrs_excg_cd: str  # 해외거래소코드 (Overseas Exchange Code)
    tr_crcy_cd: str  # 거래통화코드 (Trade Currency Code)


class OverseasReserveOrderResponse(BaseResponse, total=False):
    """해외주식 예약주문내역 응답"""

    output: List[OverseasReserveOrderOutput]


# ============================================================
# get_foreign_margin() - 해외주식 외화증거금 조회 (TTTC2101R)
# ============================================================


class OverseasForeignMarginOutput(TypedDict, total=False):
    """해외주식 외화증거금 output 항목"""

    crcy_cd: str  # 통화코드 (Currency Code)
    crcy_cd_name: str  # 통화코드명 (Currency Code Name)
    frst_bltn_exrt: str  # 최초고시환율 (First Bulletin Exchange Rate)
    frcr_dncl_amt: str  # 외화예수금액 (Foreign Currency Deposit Amount)
    frcr_evlu_amt: str  # 외화평가금액 (Foreign Currency Eval Amount)
    frcr_use_psbl_amt: str  # 외화사용가능금액 (Foreign Currency Usable Amount)
    frcr_ord_psbl_amt: str  # 외화주문가능금액 (Foreign Currency Order Possible Amount)


class OverseasForeignMarginResponse(BaseResponse, total=False):
    """해외주식 외화증거금 응답"""

    output: List[OverseasForeignMarginOutput]


# ============================================================
# buy_order() / sell_order() - 해외주식 매수/매도주문 (TTTT1002U/TTTT1006U)
# ============================================================


class OverseasOrderOutput(TypedDict, total=False):
    """해외주식 매수/매도 주문 output 필드"""

    odno: str  # 주문번호 (Order Number)
    ord_tmd: str  # 주문시각 (Order Time)


class OverseasOrderResponse(BaseResponse, total=False):
    """해외주식 매수/매도 주문 응답"""

    output: OverseasOrderOutput


# ============================================================
# modify_order() - 해외주식 정정주문 (TTTT1004U)
# ============================================================


class OverseasModifyOrderOutput(TypedDict, total=False):
    """해외주식 정정주문 output 필드"""

    odno: str  # 신규주문번호 (New Order Number)
    ord_tmd: str  # 정정시각 (Order Time)


class OverseasModifyOrderResponse(BaseResponse, total=False):
    """해외주식 정정주문 응답"""

    output: OverseasModifyOrderOutput


# ============================================================
# cancel_order() - 해외주식 취소주문 (TTTT1003U)
# ============================================================


class OverseasCancelOrderOutput(TypedDict, total=False):
    """해외주식 취소주문 output 필드"""

    odno: str  # 취소주문번호 (Cancel Order Number)
    ord_tmd: str  # 취소시각 (Order Time)


class OverseasCancelOrderResponse(BaseResponse, total=False):
    """해외주식 취소주문 응답"""

    output: OverseasCancelOrderOutput


# ============================================================
# reserve_order() - 해외주식 예약주문 (TTTS6036U)
# ============================================================


class OverseasReserveOrderCreateOutput(TypedDict, total=False):
    """해외주식 예약주문 등록 output 필드"""

    rsvn_ord_seq: str  # 예약주문순번 (Reserve Order Sequence)


class OverseasReserveOrderCreateResponse(BaseResponse, total=False):
    """해외주식 예약주문 등록 응답"""

    output: OverseasReserveOrderCreateOutput


# ============================================================
# modify_reserve_order() - 해외주식 예약주문 정정 (TTTS6037U)
# ============================================================


class OverseasReserveOrderModifyOutput(TypedDict, total=False):
    """해외주식 예약주문 정정 output 필드"""

    rsvn_ord_seq: str  # 예약주문순번 (Reserve Order Sequence)


class OverseasReserveOrderModifyResponse(BaseResponse, total=False):
    """해외주식 예약주문 정정 응답"""

    output: OverseasReserveOrderModifyOutput


# ============================================================
# cancel_reserve_order() - 해외주식 예약주문 취소 (TTTS6038U)
# ============================================================


class OverseasReserveOrderCancelOutput(TypedDict, total=False):
    """해외주식 예약주문 취소 output 필드"""

    rsvn_ord_seq: str  # 취소된 예약주문순번 (Cancelled Reserve Order Sequence)


class OverseasReserveOrderCancelResponse(BaseResponse, total=False):
    """해외주식 예약주문 취소 응답"""

    output: OverseasReserveOrderCancelOutput


# ============================================================
# 순위 API 응답 타입 (Ranking API Response Types)
# ============================================================


class OverseasRankingOutput1(TypedDict, total=False):
    """해외주식 순위 output1 (요약 정보)"""

    nrec: str  # 조회건수 (Number of Records)


class OverseasRankingOutput2Item(TypedDict, total=False):
    """해외주식 순위 output2 개별 항목 (종목별 순위 정보)"""

    # 공통 필드
    symb: str  # 종목코드 (Symbol)
    name: str  # 종목명 (Name)
    last: str  # 현재가 (Last Price)
    sign: str  # 대비부호 (Sign)
    diff: str  # 전일대비 (Difference)
    rate: str  # 등락률 (Rate) %
    tvol: str  # 거래량 (Trade Volume)
    tamt: str  # 거래대금 (Trade Amount)
    # 시가총액
    mcap: str  # 시가총액 (Market Cap)
    # 거래증가율
    grt: str  # 거래증가율 (Growth Rate)
    # 거래회전율
    turn: str  # 거래회전율 (Turnover)
    # 체결강도
    vpwr: str  # 체결강도 (Volume Power)
    # 급등락
    high: str  # 고가 (High)
    low: str  # 저가 (Low)
    open: str  # 시가 (Open)
    # 거래량급증
    surge_rate: str  # 급증률 (Surge Rate)


class OverseasRankingResponse(BaseResponse, total=False):
    """해외주식 순위 공통 응답"""

    output1: OverseasRankingOutput1
    output2: list  # List[OverseasRankingOutput2Item]


# ============================================================
# 타입 Export
# ============================================================

__all__ = [
    # 현재가
    "OverseasPriceOutput",
    "OverseasPriceResponse",
    # 현재가 상세
    "OverseasPriceDetailOutput",
    "OverseasPriceDetailResponse",
    # 기간별 시세 (일봉)
    "OverseasDailyPriceOutput1",
    "OverseasDailyPriceOutput2",
    "OverseasDailyPriceResponse",
    # 분봉
    "OverseasMinutePriceOutput1",
    "OverseasMinutePriceOutput2",
    "OverseasMinutePriceResponse",
    # 호가
    "OverseasOrderbookOutput1",
    "OverseasOrderbookOutput2",
    "OverseasOrderbookResponse",
    # 상품정보
    "OverseasStockInfoOutput",
    "OverseasStockInfoResponse",
    # 체결정보
    "OverseasCcnlOutput1",
    "OverseasCcnlOutput2",
    "OverseasCcnlResponse",
    # 휴장일
    "OverseasHolidayOutput",
    "OverseasHolidayResponse",
    # 뉴스
    "OverseasNewsOutput",
    "OverseasNewsResponse",
    # 업종/테마
    "OverseasIndustryThemeOutput1",
    "OverseasIndustryThemeOutput2",
    "OverseasIndustryThemeResponse",
    # 잔고
    "OverseasBalanceOutput1Item",
    "OverseasBalanceOutput2",
    "OverseasBalanceResponse",
    # 주문체결내역
    "OverseasOrderHistoryOutput",
    "OverseasOrderHistoryResponse",
    # 미체결내역
    "OverseasUnfilledOrderOutput",
    "OverseasUnfilledOrderResponse",
    # 매수가능금액
    "OverseasBuyableAmountOutput",
    "OverseasBuyableAmountResponse",
    # 체결기준현재잔고
    "OverseasPresentBalanceOutput1Item",
    "OverseasPresentBalanceOutput2",
    "OverseasPresentBalanceResponse",
    # 기간손익
    "OverseasPeriodProfitOutput1Item",
    "OverseasPeriodProfitOutput2",
    "OverseasPeriodProfitResponse",
    # 예약주문내역
    "OverseasReserveOrderOutput",
    "OverseasReserveOrderResponse",
    # 외화증거금
    "OverseasForeignMarginOutput",
    "OverseasForeignMarginResponse",
    # 매수/매도 주문
    "OverseasOrderOutput",
    "OverseasOrderResponse",
    # 정정주문
    "OverseasModifyOrderOutput",
    "OverseasModifyOrderResponse",
    # 취소주문
    "OverseasCancelOrderOutput",
    "OverseasCancelOrderResponse",
    # 예약주문 등록
    "OverseasReserveOrderCreateOutput",
    "OverseasReserveOrderCreateResponse",
    # 예약주문 정정
    "OverseasReserveOrderModifyOutput",
    "OverseasReserveOrderModifyResponse",
    # 예약주문 취소
    "OverseasReserveOrderCancelOutput",
    "OverseasReserveOrderCancelResponse",
    # 순위 API
    "OverseasRankingOutput1",
    "OverseasRankingOutput2Item",
    "OverseasRankingResponse",
]
