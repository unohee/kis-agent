"""한투 API 필드명 → LLM-friendly 이름 매핑.

한투 API는 stck_prpr 같은 축약 필드명을 씁니다.
LLM이 의미를 파악할 수 있도록 영문 이름으로 변환합니다.
"""

# 국내 주식 현재가
STOCK_PRICE = {
    "stck_prpr": "currentPrice",
    "prdy_vrss": "change",
    "prdy_vrss_sign": "changeSign",
    "prdy_ctrt": "changeRate",
    "stck_oprc": "open",
    "stck_hgpr": "high",
    "stck_lwpr": "low",
    "stck_mxpr": "upperLimit",
    "stck_llam": "lowerLimit",
    "stck_sdpr": "basePrice",
    "acml_vol": "volume",
    "acml_tr_pbmn": "tradingValue",
    "per": "per",
    "pbr": "pbr",
    "eps": "eps",
    "bps": "bps",
    "hts_avls": "marketCap",
    "lstn_stcn": "listedShares",
    "hts_frgn_ehrt": "foreignHoldingRate",
    "frgn_ntby_qty": "foreignNetBuy",
    "w52_hgpr": "week52High",
    "w52_lwpr": "week52Low",
    "vol_tnrt": "volumeTurnover",
}

# 일별 시세
DAILY_PRICE = {
    "stck_bsop_date": "date",
    "stck_clpr": "close",
    "stck_oprc": "open",
    "stck_hgpr": "high",
    "stck_lwpr": "low",
    "acml_vol": "volume",
    "acml_tr_pbmn": "tradingValue",
    "prdy_ctrt": "changeRate",
    "prdy_vrss_sign": "changeSign",
    "prdy_vrss": "change",
}

# 호가
ORDERBOOK_FIELDS = {
    "total_askp_rsqn": "totalAskVolume",
    "total_bidp_rsqn": "totalBidVolume",
    "antc_cnpr": "expectedPrice",
    "antc_cnqn": "expectedVolume",
}

# 계좌 잔고 요약 (output2)
ACCOUNT_BALANCE = {
    "dnca_tot_amt": "depositTotal",
    "scts_evlu_amt": "stockEvalAmount",
    "tot_evlu_amt": "totalEvalAmount",
    "nass_amt": "netAssetAmount",
    "pchs_amt_smtl_amt": "totalPurchaseAmount",
    "evlu_amt_smtl_amt": "totalEvalAmountSum",
    "evlu_pfls_smtl_amt": "totalProfitLoss",
    "asst_icdc_amt": "assetChange",
    "asst_icdc_erng_rt": "assetChangeRate",
}

# 보유종목 (output1)
HOLDING = {
    "pdno": "code",
    "prdt_name": "name",
    "hldg_qty": "quantity",
    "pchs_avg_pric": "avgPrice",
    "pchs_amt": "purchaseAmount",
    "prpr": "currentPrice",
    "evlu_amt": "evalAmount",
    "evlu_pfls_amt": "profitLoss",
    "evlu_pfls_rt": "profitRate",
    "ord_psbl_qty": "sellableQty",
}

# 해외주식 현재가
OVERSEAS_PRICE = {
    "last": "currentPrice",
    "base": "prevClose",
    "pvol": "prevVolume",
    "sign": "sign",
    "diff": "change",
    "rate": "changeRate",
    "tvol": "volume",
    "tamt": "tradingValue",
}

# 해외주식 현재가 상세
OVERSEAS_PRICE_DETAIL = {
    "last": "currentPrice",
    "diff": "change",
    "rate": "changeRate",
    "h52p": "high52w",
    "l52p": "low52w",
    "perx": "per",
    "pbrx": "pbr",
    "epsx": "eps",
    "bpsx": "bps",
    "mcap": "marketCap",
    "shar": "shares",
    "tvol": "volume",
}

# 해외주식 일별
OVERSEAS_DAILY = {
    "xymd": "date",
    "clos": "close",
    "open": "open",
    "high": "high",
    "low": "low",
    "tvol": "volume",
    "rate": "changeRate",
}

# 선물 현재가
FUTURES_PRICE = {
    "fuop_prpr": "currentPrice",
    "prdy_vrss": "change",
    "prdy_vrss_sign": "changeSign",
    "prdy_ctrt": "changeRate",
    "fuop_oprc": "open",
    "fuop_hgpr": "high",
    "fuop_lwpr": "low",
    "fuop_sdpr": "basePrice",
    "acml_vol": "volume",
    "acml_tr_pbmn": "tradingValue",
    "fuop_open_intr_vol": "openInterest",
    "impl_vola": "impliedVolatility",
    "optn_delta": "delta",
    "optn_gamma": "gamma",
    "optn_theta": "theta",
    "optn_vega": "vega",
    "optn_theo_pric": "theoreticalPrice",
    "hts_kor_isnm": "name",
}

# 해외선물 현재가
OVERSEAS_FUTURES_PRICE = {
    "last": "currentPrice",
    "base": "prevClose",
    "sign": "sign",
    "diff": "change",
    "rate": "changeRate",
    "open": "open",
    "high": "high",
    "low": "low",
    "tvol": "volume",
    "tamt": "tradingValue",
    "oi": "openInterest",
    "rsym": "symbol",
    "exch_cd": "exchange",
    "srs_cd": "seriesCode",
    "curr": "currency",
    "zdiv": "decimalPlaces",
    "bprc": "bidPrice",
    "aprc": "askPrice",
    "bqty": "bidQty",
    "aqty": "askQty",
}

# 해외옵션 현재가 (그릭스 포함)
OVERSEAS_OPTION_PRICE = {
    "last": "currentPrice",
    "base": "prevClose",
    "sign": "sign",
    "diff": "change",
    "rate": "changeRate",
    "open": "open",
    "high": "high",
    "low": "low",
    "tvol": "volume",
    "tamt": "tradingValue",
    "theo_pric": "theoreticalPrice",
    "iv": "impliedVolatility",
    "delta": "delta",
    "gamma": "gamma",
    "theta": "theta",
    "vega": "vega",
}

# 일별 주문체결 (output1)
TRADE_EXECUTION = {
    "ord_dt": "date",
    "ord_tmd": "time",
    "pdno": "code",
    "prdt_name": "name",
    "sll_buy_dvsn_cd_name": "side",
    "ord_dvsn_name": "orderType",
    "ord_qty": "orderQty",
    "ord_unpr": "orderPrice",
    "tot_ccld_qty": "filledQty",
    "avg_prvs": "avgPrice",
    "tot_ccld_amt": "filledAmount",
    "rmn_qty": "remainQty",
    "cncl_yn": "cancelled",
    "odno": "orderNo",
    "orgn_odno": "origOrderNo",
}

# 체결 요약 (output2)
TRADE_SUMMARY = {
    "tot_ord_qty": "totalOrderQty",
    "tot_ccld_qty": "totalFilledQty",
    "tot_ccld_amt": "totalFilledAmount",
    "prsm_tlex_smtl": "totalFees",
    "pchs_avg_pric": "avgPurchasePrice",
}

# 기간별 실현손익 (output1)
PERIOD_PROFIT = {
    "pdno": "code",
    "prdt_name": "name",
    "sll_buy_dvsn_cd_name": "side",
    "buy_qty": "buyQty",
    "buy_amt": "buyAmount",
    "sll_qty": "sellQty",
    "sll_amt": "sellAmount",
    "rlzt_pfls": "realizedPL",
    "rlzt_erng_rt": "realizedPLRate",
    "prsm_tlex_smtl": "totalFees",
}

# 기간별 손익 일별합산 (output1)
DAILY_PROFIT = {
    "bsop_dt": "date",
    "rlzt_pfls": "realizedPL",
    "rlzt_erng_rt": "realizedPLRate",
    "sll_amt": "sellAmount",
    "buy_amt": "buyAmount",
    "prsm_tlex_smtl": "totalFees",
}

# 종목정보
STOCK_INFO = {
    "prdt_abrv_name": "name",
    "prdt_name": "fullName",
    "prdt_eng_name": "engName",
}


def remap(data: dict, field_map: dict) -> dict:
    """필드명을 LLM-friendly 이름으로 변환."""
    return {field_map.get(k, k): v for k, v in data.items() if k in field_map}
