"""
Stock Response Types - 주식 관련 응답 타입 정의

주식 시세 조회, 호가, 분봉 등 Stock API 응답 구조
"""

from typing import List, TypedDict

from .common import BaseResponse

# ============================================================
# get_stock_price() - 주식 현재가 조회
# ============================================================


class StockPriceOutput(TypedDict, total=False):
    """주식 현재가 조회 output 필드 (82 필드)"""

    # 기본 가격 정보
    stck_prpr: str  # 주식 현재가 (Stock Present Price)
    prdy_vrss: str  # 전일 대비 (Previous Day Versus)
    prdy_vrss_sign: str  # 전일 대비 부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)
    prdy_ctrt: str  # 전일 대비율 (Previous Day Change Rate) %
    stck_oprc: str  # 주식 시가 (Stock Opening Price)
    stck_hgpr: str  # 주식 최고가 (Stock High Price)
    stck_lwpr: str  # 주식 최저가 (Stock Low Price)
    stck_mxpr: str  # 주식 상한가 (Stock Max Price)
    stck_llam: str  # 주식 하한가 (Stock Lower Limit Amount)
    stck_sdpr: str  # 주식 기준가 (Stock Standard Price)

    # 거래량/거래대금
    acml_vol: str  # 누적 거래량 (Accumulated Volume)
    acml_tr_pbmn: str  # 누적 거래대금 (Accumulated Trade Price By Million)
    prdy_vrss_vol_rate: str  # 전일 대비 거래량 비율

    # 종목 정보
    hts_kor_isnm: str  # HTS 한글 종목명 (HTS Korean Issue Name)
    bstp_kor_isnm: str  # 업종 한글 종목명
    stck_shrn_iscd: str  # 주식 단축 종목코드

    # 가중 평균 및 호가
    wghn_avrg_stck_prc: str  # 가중 평균 주식 가격 (Weighted Average Stock Price)

    # 외국인/기관 정보
    hts_frgn_ehrt: str  # HTS 외국인 소진율 (HTS Foreign Exhaustion Rate)
    frgn_ntby_qty: str  # 외국인 순매수 수량 (Foreign Net Buy Quantity)
    frgn_hldn_qty: str  # 외국인 보유 수량
    pgtr_ntby_qty: str  # 프로그램 순매수 수량 (Program Trade Net Buy Quantity)

    # 피벗 지표
    pvt_scnd_dmrs_prc: str  # 피벗 2차 디저항 가격
    pvt_frst_dmrs_prc: str  # 피벗 1차 디저항 가격
    pvt_pont_val: str  # 피벗 포인트 값
    pvt_frst_dmsp_prc: str  # 피벗 1차 디지지 가격
    pvt_scnd_dmsp_prc: str  # 피벗 2차 디지지 가격
    dmrs_val: str  # 디저항 값
    dmsp_val: str  # 디지지 값

    # 자본/액면/호가단위
    cpfn: str  # 자본금 (Capital Fund)
    cpfn_cnnm: str  # 자본금 통화명
    rstc_wdth_prc: str  # 제한폭 가격 (Restriction Width Price)
    stck_fcam: str  # 주식 액면가 (Stock Face Amount)
    fcam_cnnm: str  # 액면가 통화명
    stck_sspr: str  # 주식 대용가 (Stock Substitute Price)
    aspr_unit: str  # 호가단위 (Asking Price Unit)
    hts_deal_qty_unit_val: str  # HTS 매매 수량 단위 값

    # 시가총액/상장주수
    lstn_stcn: str  # 상장 주수 (Listed Stock Count)
    hts_avls: str  # HTS 시가총액 (HTS Market Capitalization)

    # 재무지표
    per: str  # PER (Price Earning Ratio)
    pbr: str  # PBR (Price Book-value Ratio)
    eps: str  # EPS (Earning Per Share)
    bps: str  # BPS (Book-value Per Share)
    stac_month: str  # 결산 월 (Settlement Month)
    vol_tnrt: str  # 거래량 회전율 (Volume Turnover Rate)

    # 최고가/최저가 기록
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
    w52_hgpr_vrss_prpr_ctrt: str  # 52주일 최고가 대비 현재가 대비율
    w52_hgpr_date: str  # 52주일 최고가 일자
    w52_lwpr: str  # 52주일 최저가
    w52_lwpr_vrss_prpr_ctrt: str  # 52주일 최저가 대비 현재가 대비율
    w52_lwpr_date: str  # 52주일 최저가 일자

    # 융자/대주/공매도
    whol_loan_rmnd_rate: str  # 전체 융자 잔고 비율
    itewhol_loan_rmnd_ratem_name: str  # 전체 융자 잔고 비율명
    ssts_yn: str  # 공매도가능여부
    last_ssts_cntg_qty: str  # 최종 공매도 체결 수량

    # 시장/종목 상태
    iscd_stat_cls_code: str  # 종목 상태 구분 코드
    marg_rate: str  # 증거금 비율
    grmn_rate_cls_code: str  # 보증금 비율 구분 코드
    rprs_mrkt_kor_name: str  # 대표 시장 한글 명
    new_hgpr_lwpr_cls_code: str  # 신 고가 저가 구분 코드
    temp_stop_yn: str  # 임시 정지 여부
    oprc_rang_cont_yn: str  # 시가 범위 연장 여부
    clpr_rang_cont_yn: str  # 종가 범위 연장 여부
    crdt_able_yn: str  # 신용 가능 여부
    elw_pblc_yn: str  # ELW 발행 여부
    vi_cls_code: str  # VI적용구분코드
    ovtm_vi_cls_code: str  # 시간외단일가VI적용구분코드
    invt_caful_yn: str  # 투자유의여부
    mrkt_warn_cls_code: str  # 시장경고코드
    short_over_yn: str  # 단기과열여부
    sltr_yn: str  # 정리매매여부
    mang_issu_cls_code: str  # 관리종목여부
    apprch_rate: str  # 접근도


class StockPriceResponse(BaseResponse):
    """주식 현재가 조회 응답"""

    output: StockPriceOutput


# ============================================================
# get_daily_price() - 일별 시세 조회
# ============================================================


class DailyPriceItem(TypedDict, total=False):
    """일별 시세 개별 항목"""

    stck_bsop_date: str  # 주식 영업 일자 (Stock Business Operation Date, YYYYMMDD)
    stck_clpr: str  # 주식 종가 (Stock Closing Price)
    stck_oprc: str  # 주식 시가 (Stock Opening Price)
    stck_hgpr: str  # 주식 최고가 (Stock High Price)
    stck_lwpr: str  # 주식 최저가 (Stock Low Price)
    acml_vol: str  # 누적 거래량 (Accumulated Volume)
    acml_tr_pbmn: str  # 누적 거래대금 (Accumulated Trade Price By Million)
    prdy_vrss_vol_rate: str  # 전일 대비 거래량 비율
    prdy_vrss_sign: str  # 전일 대비 부호 (Previous Day Versus Sign)
    prdy_vrss: str  # 전일 대비 (Previous Day Versus)
    prdy_ctrt: str  # 전일 대비율 (Previous Day Change Rate)
    hts_frgn_ehrt: str  # HTS 외국인 소진율
    frgn_ntby_qty: str  # 외국인 순매수 수량
    flng_cls_code: str  # 락 구분 코드 (Falling Class Code)
    acml_prtt_rate: str  # 누적 분할 비율
    prtt_rate: str  # 분할 비율 (Partition Rate)
    mod_yn: str  # 분할변경여부 (Modified Yes/No)
    revl_issu_reas: str  # 재평가 사유 (Revaluation Issue Reason)


class DailyPriceResponse(BaseResponse):
    """일별 시세 조회 응답"""

    output: List[DailyPriceItem]  # output2가 아닌 output으로 리스트 반환


# ============================================================
# get_orderbook() - 호가 정보 조회
# ============================================================


class OrderbookOutput(TypedDict, total=False):
    """호가 정보 조회 output 필드"""

    # 매도 호가 (Ask Price) - 1~10호가
    askp1: str  # 매도호가1
    askp2: str
    askp3: str
    askp4: str
    askp5: str
    askp6: str
    askp7: str
    askp8: str
    askp9: str
    askp10: str

    # 매수 호가 (Bid Price) - 1~10호가
    bidp1: str  # 매수호가1
    bidp2: str
    bidp3: str
    bidp4: str
    bidp5: str
    bidp6: str
    bidp7: str
    bidp8: str
    bidp9: str
    bidp10: str

    # 매도 호가 잔량 (Ask Price Residual Quantity)
    askp_rsqn1: str  # 매도호가 잔량1
    askp_rsqn2: str
    askp_rsqn3: str
    askp_rsqn4: str
    askp_rsqn5: str
    askp_rsqn6: str
    askp_rsqn7: str
    askp_rsqn8: str
    askp_rsqn9: str
    askp_rsqn10: str

    # 매수 호가 잔량 (Bid Price Residual Quantity)
    bidp_rsqn1: str  # 매수호가 잔량1
    bidp_rsqn2: str
    bidp_rsqn3: str
    bidp_rsqn4: str
    bidp_rsqn5: str
    bidp_rsqn6: str
    bidp_rsqn7: str
    bidp_rsqn8: str
    bidp_rsqn9: str
    bidp_rsqn10: str

    # 총 호가 잔량
    total_askp_rsqn: str  # 총 매도호가 잔량 (Total Ask Price Residual Quantity)
    total_bidp_rsqn: str  # 총 매수호가 잔량 (Total Bid Price Residual Quantity)

    # 기타
    ovtm_total_askp_rsqn: str  # 시간외 총 매도호가 잔량
    ovtm_total_bidp_rsqn: str  # 시간외 총 매수호가 잔량
    antc_cnpr: str  # 예상 체결가 (Anticipated Conclusion Price)
    antc_cnqn: str  # 예상 체결량 (Anticipated Conclusion Quantity)
    antc_vol: str  # 예상 거래량 (Anticipated Volume)
    antc_cntg_vrss: str  # 예상 체결 대비 (Anticipated Conclusion Versus)
    antc_cntg_vrss_sign: str  # 예상 체결 대비 부호
    antc_cntg_prdy_ctrt: str  # 예상 체결 전일 대비율
    acml_vol: str  # 누적 거래량
    total_askp_rsqn_icdc: str  # 총 매도호가 잔량 증감
    total_bidp_rsqn_icdc: str  # 총 매수호가 잔량 증감
    ovtm_total_askp_icdc: str  # 시간외 총 매도호가 증감
    ovtm_total_bidp_icdc: str  # 시간외 총 매수호가 증감
    stck_prpr: str  # 주식 현재가


class OrderbookResponse(BaseResponse):
    """호가 정보 조회 응답"""

    output: OrderbookOutput


# ============================================================
# get_minute_price() - 분봉 시세 조회
# ============================================================


class MinutePriceItem(TypedDict, total=False):
    """분봉 시세 개별 항목"""

    stck_bsop_date: str  # 주식 영업 일자 (YYYYMMDD)
    stck_cntg_hour: str  # 주식 체결 시각 (HHMMSS)
    stck_prpr: str  # 주식 현재가 (Stock Present Price)
    stck_oprc: str  # 주식 시가 (Stock Opening Price)
    stck_hgpr: str  # 주식 최고가 (Stock High Price)
    stck_lwpr: str  # 주식 최저가 (Stock Low Price)
    cntg_vol: str  # 체결 거래량 (Conclusion Volume)
    acml_vol: str  # 누적 거래량
    acml_tr_pbmn: str  # 누적 거래대금 (Accumulated Trade Price By Million)
    prdy_vrss: str  # 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    prdy_ctrt: str  # 전일 대비율
    stck_prdy_clpr: str  # 주식 전일 종가
    hts_kor_isnm: str  # HTS 한글 종목명


class MinutePriceResponse(BaseResponse):
    """분봉 시세 조회 응답"""

    output: List[MinutePriceItem]


# ============================================================
# get_stock_investor() - 종목별 투자자 매매 동향
# ============================================================


class StockInvestorOutput(TypedDict, total=False):
    """투자자 매매 동향 output 필드"""

    stck_bsop_date: str  # 주식 영업 일자 (Stock Business Operation Date)
    stck_clpr: str  # 주식 종가 (Stock Closing Price)
    prdy_vrss: str  # 전일 대비 (Previous Day Versus)
    prdy_vrss_sign: str  # 전일 대비 부호
    prdy_ctrt: str  # 전일 대비율 (%)
    acml_vol: str  # 누적 거래량

    # 개인 (Individual)
    prsn_ntby_qty: str  # 개인 순매수 수량 (Person Net Buy Quantity)
    prsn_ntby_tr_pbmn: (
        str  # 개인 순매수 거래대금 (Person Net Buy Trade Price By Million)
    )
    prsn_shnu_vol: str  # 개인 매수 거래량
    prsn_shnu_tr_pbmn: str  # 개인 매수 거래대금
    prsn_seln_vol: str  # 개인 매도 거래량
    prsn_seln_tr_pbmn: str  # 개인 매도 거래대금

    # 외국인 (Foreigner)
    frgn_ntby_qty: str  # 외국인 순매수 수량 (Foreign Net Buy Quantity)
    frgn_ntby_tr_pbmn: str  # 외국인 순매수 거래대금
    frgn_shnu_vol: str  # 외국인 매수 거래량
    frgn_shnu_tr_pbmn: str  # 외국인 매수 거래대금
    frgn_seln_vol: str  # 외국인 매도 거래량
    frgn_seln_tr_pbmn: str  # 외국인 매도 거래대금

    # 기관계 (Institution)
    orgn_ntby_qty: str  # 기관 순매수 수량 (Organization Net Buy Quantity)
    orgn_ntby_tr_pbmn: str  # 기관 순매수 거래대금
    orgn_shnu_vol: str  # 기관계 매수 거래량
    orgn_shnu_tr_pbmn: str  # 기관계 매수 거래대금
    orgn_seln_vol: str  # 기관계 매도 거래량
    orgn_seln_tr_pbmn: str  # 기관계 매도 거래대금


class StockInvestorResponse(BaseResponse):
    """투자자 매매 동향 조회 응답"""

    output: StockInvestorOutput


# ============================================================
# inquire_time_itemconclusion() - 당일시간대별체결 조회
# ============================================================


class InquireTimeItemconclusionOutput1(TypedDict, total=False):
    """시간대별 체결 요약 정보"""

    stck_prpr: str  # 주식 현재가
    prdy_vrss: str  # 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    prdy_ctrt: str  # 전일 대비율
    acml_vol: str  # 누적 거래량
    acml_tr_pbmn: str  # 누적 거래대금


class InquireTimeItemconclusionOutput2(TypedDict, total=False):
    """시간대별 체결 개별 항목"""

    stck_cntg_hour: str  # 주식 체결 시각 (HHMMSS)
    stck_prpr: str  # 주식 현재가
    cntg_vol: str  # 체결 거래량
    acml_vol: str  # 누적 거래량


class InquireTimeItemconclusionResponse(BaseResponse):
    """시간대별 체결 조회 응답"""

    output1: InquireTimeItemconclusionOutput1
    output2: List[InquireTimeItemconclusionOutput2]


# ============================================================
# inquire_ccnl() - 주식현재가 체결 조회
# ============================================================


class InquireCcnlItem(TypedDict, total=False):
    """체결 내역 개별 항목"""

    stck_cntg_hour: str  # 주식 체결 시각 (HHMMSS)
    stck_prpr: str  # 주식 현재가
    prdy_vrss: str  # 전일 대비
    prdy_vrss_sign: str  # 전일 대비 부호
    cntg_vol: str  # 체결 거래량
    tday_rltv: str  # 당일 체결강도 (Today Relative Strength)
    prdy_vol: str  # 전일 동시간 거래량


class InquireCcnlResponse(BaseResponse):
    """주식 체결 조회 응답 (최근 30건)"""

    output: List[InquireCcnlItem]


# ============================================================
# search_stock_info() - 주식 기본정보 조회
# ============================================================


class SearchStockInfoOutput(TypedDict, total=False):
    """주식 기본정보 output 필드"""

    pdno: str  # 상품번호 (종목코드, Product Number)
    prdt_type_cd: str  # 상품유형코드 (Product Type Code)
    prdt_name: str  # 상품명 (Product Name)
    prdt_name120: str  # 상품명120 (긴 상품명)
    prdt_abrv_name: str  # 상품약어명 (Product Abbreviation Name)
    prdt_eng_name: str  # 상품영문명 (Product English Name)
    prdt_eng_name120: str  # 상품영문명120
    prdt_eng_abrv_name: str  # 상품영문약어명
    std_pdno: str  # 표준상품번호 (Standard Product Number)
    shtn_pdno: str  # 단축상품번호 (Shortened Product Number)
    prdt_sale_stat_cd: str  # 상품판매상태코드 (Product Sale Status Code)
    prdt_risk_grad_cd: str  # 상품위험등급코드
    prdt_clsf_cd: str  # 상품분류코드
    prdt_clsf_name: str  # 상품분류명
    sale_strt_dt: str  # 판매시작일자 (YYYYMMDD)
    sale_end_dt: str  # 판매종료일자
    wrap_asst_type_cd: str  # 랩자산유형코드
    ivst_prdt_type_cd: str  # 투자상품유형코드
    ivst_prdt_type_cd_name: str  # 투자상품유형코드명
    frst_erlm_dt: str  # 최초등록일자 (First Enrollment Date)


class SearchStockInfoResponse(BaseResponse):
    """주식 기본정보 조회 응답"""

    output: SearchStockInfoOutput
