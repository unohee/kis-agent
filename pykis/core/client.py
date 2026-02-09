import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests

from .auth import auth, getTREnv
from .config import KISConfig
from .rate_limiter import RateLimiter, get_global_rate_limiter

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

API_ENDPOINTS = {
    # === OAuth 인증 ===
    "TOKEN": "/oauth2/tokenP",
    "APPROVAL": "/oauth2/Approval",
    "REVOKE": "/oauth2/revokeP",
    "HASHKEY": "/uapi/hashkey",
    # === 국내주식 시세 ===
    "INQUIRE_PRICE": "/uapi/domestic-stock/v1/quotations/inquire-price",  # 주식현재가 시세 (TR: FHKST01010100)
    "INQUIRE_DAILY_PRICE": "/uapi/domestic-stock/v1/quotations/inquire-daily-price",  # ELW 당일급변종목 (TR: FHPEW02870000)
    "INQUIRE_TIME_ITEMCHARTPRICE": "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",  # 주식당일분봉조회(주식) (TR: FHKST03010200)
    "INQUIRE_TIME_DAILYCHARTPRICE": "/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice",  # 일별분봉시세조회 (TR: FHKST03010230)
    "INQUIRE_MEMBER": "/uapi/domestic-stock/v1/quotations/inquire-member",  # 주식현재가 회원사 (TR: FHKST01010600)
    "INQUIRE_INVESTOR": "/uapi/domestic-stock/v1/quotations/inquire-investor",  # 주식현재가 투자자 (TR: FHKST01010900)
    "INQUIRE_ASKING_PRICE_EXP_CCN": "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",  # 주식현재가 호가 예상체결 (TR: FHKST01010200)
    "INQUIRE_CCNL": "/uapi/domestic-stock/v1/quotations/inquire-ccnl",  # 주식현재가 체결(최근30건) (TR: FHKST01010300)
    "INQUIRE_DAILY_ITEMCHARTPRICE": "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",  # 국내주식기간별시세(일/주/월/년) (TR: FHKST03010100)
    "INQUIRE_DAILY_INDEXCHARTPRICE": "/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice",  # 국내주식업종기간별시세(일/주/월/년) (TR: FHKUP03500100)
    "INQUIRE_INDEX_DAILY_PRICE": "/uapi/domestic-stock/v1/quotations/inquire-index-daily-price",  # 국내업종 일자별지수 (TR: FHPUP02120000)
    "INQUIRE_DAILY_OVERTIMEPRICE": "/uapi/domestic-stock/v1/quotations/inquire-daily-overtimeprice",  # 주식현재가 시간외 일자별주가 (TR: FHPST02320000)
    "INQUIRE_TIME_ITEMCONCLUSION": "/uapi/domestic-stock/v1/quotations/inquire-time-itemconclusion",  # 주식현재가 당일시간대별체결 (TR: FHPST01060000)
    "INQUIRE_TIME_OVERTIMECONCLUSION": "/uapi/domestic-stock/v1/quotations/inquire-time-overtimeconclusion",  # 주식현재가 시간외 시간별체결 (TR: FHPST02310000)
    "INQUIRE_OVERTIME_ASKING_PRICE": "/uapi/domestic-stock/v1/quotations/inquire-overtime-asking-price",  # 국내주식 시간외호가 (TR: FHPST02300400)
    "INQUIRE_OVERTIME_PRICE": "/uapi/domestic-stock/v1/quotations/inquire-overtime-price",  # 국내주식 시간외현재가 (TR: FHPST02300000)
    "INQUIRE_PRICE_2": "/uapi/domestic-stock/v1/quotations/inquire-price-2",  # 주식현재가 시세2 (TR: FHPST01010000)
    "INQUIRE_ELW_PRICE": "/uapi/domestic-stock/v1/quotations/inquire-elw-price",  # ELW 현재가 조회 (TR: FHKEW15010000)
    "INQUIRE_INDEX_CATEGORY_PRICE": "/uapi/domestic-stock/v1/quotations/inquire-index-category-price",  # 업종별 지수 시세 (TR: FHKUP03500100)
    "INQUIRE_INDEX_TICKPRICE": "/uapi/domestic-stock/v1/quotations/inquire-index-tickprice",  # 지수 틱 시세 (TR: FHPUP02110100)
    "INQUIRE_INDEX_TIMEPRICE": "/uapi/domestic-stock/v1/quotations/inquire-index-timeprice",  # 지수 분/일봉 시세 (TR: FHKUP03500200)
    "INQUIRE_TIME_INDEXCHARTPRICE": "/uapi/domestic-stock/v1/quotations/inquire-time-indexchartprice",  # 지수 분봉 차트 (TR: FHKUP03500100)
    "DISPARITY": "/uapi/domestic-stock/v1/ranking/disparity",  # 국내주식 이격도 순위 (TR: FHPST01780000)
    "DIVIDEND_RATE": "/uapi/domestic-stock/v1/ranking/dividend-rate",  # 국내주식 배당률 상위 (TR: HHKDB13470100)
    "MARKET_TIME": "/uapi/domestic-stock/v1/quotations/market-time",  # 국내주식 시장영업시간 (TR: FHKST01550000)
    "MARKET_VALUE": "/uapi/domestic-stock/v1/quotations/market-value",  # 국내주식 종목별 시가총액 (TR: FHKST70300200)
    "PROFIT_ASSET_INDEX": "/uapi/domestic-stock/v1/quotations/profit-asset-index",  # 국내주식 자산/수익지수 (TR: FHKUP03500400)
    "INTSTOCK_MULTPRICE": "/uapi/domestic-stock/v1/quotations/intstock-multprice",  # 국내주식 복수종목 현재가 (TR: FHKST662300C0)
    # === 프로그램매매 ===
    "PROGRAM_TRADE_BY_STOCK_DAILY": "/uapi/domestic-stock/v1/quotations/program-trade-by-stock-daily",  # 종목별 프로그램매매추이(일별) (TR: FHPPG04650200)
    "PROGRAM_TRADE_BY_STOCK": "/uapi/domestic-stock/v1/quotations/program-trade-by-stock",  # 종목별프로그램매매추이(체결) (TR: FHPPG04650101)
    "COMP_PROGRAM_TRADE_DAILY": "/uapi/domestic-stock/v1/quotations/comp-program-trade-daily",  # 프로그램매매 종합현황(일별) (TR: FHPPG04600000)
    "COMP_PROGRAM_TRADE_TODAY": "/uapi/domestic-stock/v1/quotations/comp-program-trade-today",  # 프로그램매매 종합현황(시간) (TR: FHPPG04600100)
    "INVESTOR_PROGRAM_TRADE_TODAY": "/uapi/domestic-stock/v1/quotations/investor-program-trade-today",  # 프로그램매매 투자자매매동향(당일) (TR: HHPPG046600C0)
    # === 투자자별 ===
    "INQUIRE_INVESTOR_TIME_BY_MARKET": "/uapi/domestic-stock/v1/quotations/inquire-investor-time-by-market",  # 시장별 투자자매매동향(시세) (TR: FHPTJ04030000)
    "INQUIRE_INVESTOR_DAILY_BY_MARKET": "/uapi/domestic-stock/v1/quotations/inquire-investor-daily-by-market",  # 시장별 투자자매매동향(일별) (TR: FHPTJ04040000)
    "INQUIRE_MEMBER_DAILY": "/uapi/domestic-stock/v1/quotations/inquire-member-daily",  # 주식현재가 회원사 종목매매동향 (TR: FHPST04540000)
    "INVESTOR_TREND_ESTIMATE": "/uapi/domestic-stock/v1/quotations/investor-trend-estimate",  # 종목별 외인기관 추정가집계 (TR: HHPTJ04160200)
    "INVESTOR_TRADE_BY_STOCK_DAILY": "/uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily",  # 종목별 투자자매매동향(일별) (TR: FHPTJ04160001)
    "FOREIGN_INSTITUTION_TOTAL": "/uapi/domestic-stock/v1/quotations/foreign-institution-total",  # 국내기관_외국인 매매종목가집계 (TR: FHPTJ04400000)
    "FRGNMEM_PCHS_TREND": "/uapi/domestic-stock/v1/quotations/frgnmem-pchs-trend",  # 종목별 외국계 순매수추이 (TR: FHKST644400C0)
    "FRGNMEM_TRADE_ESTIMATE": "/uapi/domestic-stock/v1/quotations/frgnmem-trade-estimate",  # 외국계 매매종목 가집계 (TR: FHKST644100C0)
    "FRGNMEM_TRADE_TREND": "/uapi/domestic-stock/v1/quotations/frgnmem-trade-trend",  # 회원사 실시간 매매동향(틱) (TR: FHPST04320000)
    # === 거래/주문 ===
    "INQUIRE_BALANCE": "/uapi/domestic-stock/v1/trading/inquire-balance",  # 주식잔고조회 (TR: TTTC8434R)
    "INQUIRE_PSBL_ORDER": "/uapi/domestic-stock/v1/trading/inquire-psbl-order",  # 매수가능조회 (TR: TTTC8908R)
    "INQUIRE_PSBL_SELL": "/uapi/domestic-stock/v1/trading/inquire-psbl-sell",  # 매도가능수량조회 (TR: TTTC8408R)
    "INQUIRE_DAILY_CCLD": "/uapi/domestic-stock/v1/trading/inquire-daily-ccld",  # 주식일별주문체결조회 (TR: TTTC8001R)
    "INQUIRE_ACCOUNT_BALANCE": "/uapi/domestic-stock/v1/trading/inquire-account-balance",  # 투자계좌자산현황조회 (TR: CTRP6548R)
    "INQUIRE_BALANCE_RLZ_PL": "/uapi/domestic-stock/v1/trading/inquire-balance-rlz-pl",  # 주식잔고조회_실현손익 (TR: TTTC8494R)
    "INQUIRE_PERIOD_PROFIT": "/uapi/domestic-stock/v1/trading/inquire-period-profit",  # 기간별손익일별합산조회 (TR: TTTC8708R)
    "INQUIRE_PERIOD_TRADE_PROFIT": "/uapi/domestic-stock/v1/trading/inquire-period-trade-profit",  # 기간별매매손익현황조회 (TR: TTTC8715R)
    "ORDER_CASH": "/uapi/domestic-stock/v1/trading/order-cash",  # 주식주문(현금) (TR: 매수-TTTC0012U/매도-TTTC0011U, Mock: VTTC0012U/VTTC0011U)
    "ORDER_CREDIT": "/uapi/domestic-stock/v1/trading/order-credit",  # 주식주문(신용) (TR: 매수-TTTC0052U/매도-TTTC0051U, 실전만)
    "INQUIRE_CREDIT_PSAMOUNT": "/uapi/domestic-stock/v1/trading/inquire-credit-psamount",  # 신용매수가능조회 (TR: TTTC8909R)
    "INQUIRE_PSBL_RVSECNCL": "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl",  # 주식정정취소가능주문조회 (TR: TTTC8036R)
    "ORDER_RESV_CCNL": "/uapi/domestic-stock/v1/trading/order-resv-ccnl",  # 주식예약주문조회 (TR: CTSC0004R)
    # === 시장정보/순위 ===
    "VOLUME_RANK": "/uapi/domestic-stock/v1/quotations/volume-rank",  # 거래량순위 (TR: FHPST01710000)
    "FLUCTUATION": "/uapi/domestic-stock/v1/ranking/fluctuation",  # 국내주식 등락률 순위 (TR: FHPST01700000)
    "MARKET_CAP": "/uapi/domestic-stock/v1/ranking/market-cap",  # 국내주식 시가총액 상위 (TR: FHPST01740000)
    "VOLUME_POWER": "/uapi/domestic-stock/v1/ranking/volume-power",  # 국내주식 체결강도 상위 (TR: FHPST01680000)
    "AFTER_HOUR_BALANCE": "/uapi/domestic-stock/v1/ranking/after-hour-balance",  # 국내주식 시간외잔량 순위 (TR: FHPST01760000)
    "SHORT_SALE": "/uapi/domestic-stock/v1/ranking/short-sale",  # 국내주식 공매도 상위종목 (TR: FHPST04820000)
    "OVERTIME_FLUCTUATION": "/uapi/domestic-stock/v1/ranking/overtime-fluctuation",  # 국내주식 시간외등락율순위 (TR: FHPST02340000)
    "OVERTIME_VOLUME": "/uapi/domestic-stock/v1/ranking/overtime-volume",  # 국내주식 시간외거래량순위 (TR: FHPST02350000)
    # === 기타 시세정보 ===
    "SEARCH_STOCK_INFO": "/uapi/domestic-stock/v1/quotations/search-stock-info",  # 주식기본조회 (TR: CTPF1002R)
    "CHK_HOLIDAY": "/uapi/domestic-stock/v1/quotations/chk-holiday",  # 국내휴장일조회 (TR: CTCA0903R)
    "PBAR_TRATIO": "/uapi/domestic-stock/v1/quotations/pbar-tratio",  # 국내주식 매물대/거래비중 (TR: FHPST01130000)
    "CAPTURE_UPLOWPRICE": "/uapi/domestic-stock/v1/quotations/capture-uplowprice",  # 국내주식 상하한가 포착 (TR: FHKST130000C0)
    "EXP_CLOSING_PRICE": "/uapi/domestic-stock/v1/quotations/exp-closing-price",  # 국내주식 장마감 예상체결가 (TR: FHKST117300C0)
    "EXP_PRICE_TREND": "/uapi/domestic-stock/v1/quotations/exp-price-trend",  # 국내주식 예상체결가 추이 (TR: FHPST01810000)
    "EXP_INDEX_TREND": "/uapi/domestic-stock/v1/quotations/exp-index-trend",  # 국내주식 예상체결지수 추이 (TR: FHPST01840000)
    "INQUIRE_VI_STATUS": "/uapi/domestic-stock/v1/quotations/inquire-vi-status",  # 변동성완화장치(VI) 현황 (TR: FHPST01390000)
    "INQUIRE_DAILY_TRADE_VOLUME": "/uapi/domestic-stock/v1/quotations/inquire-daily-trade-volume",  # 종목별일별매수매도체결량 (TR: FHKST03010800)
    "NEWS_TITLE": "/uapi/domestic-stock/v1/quotations/news-title",  # 종합 시황/공시(제목) (TR: FHKST01011800)
    "DAILY_CREDIT_BALANCE": "/uapi/domestic-stock/v1/quotations/daily-credit-balance",  # 국내주식 신용잔고 일별추이 (TR: FHPST04760000)
    "DAILY_SHORT_SALE": "/uapi/domestic-stock/v1/quotations/daily-short-sale",  # 국내주식 공매도 일별추이 (TR: FHPST04830000)
    "MKTFUNDS": "/uapi/domestic-stock/v1/quotations/mktfunds",  # 국내 증시자금 종합 (TR: FHKST649100C0)
    # === 재무정보 ===
    "INCOME_STATEMENT": "/uapi/domestic-stock/v1/finance/income-statement",  # 국내주식 손익계산서 (TR: FHKST66430200)
    "BALANCE_SHEET": "/uapi/domestic-stock/v1/finance/balance-sheet",  # 국내주식 대차대조표 (TR: FHKST66430100)
    "FINANCIAL_RATIO": "/uapi/domestic-stock/v1/finance/financial-ratio",  # 국내주식 재무비율 (TR: FHKST66430300)
    "PROFIT_RATIO": "/uapi/domestic-stock/v1/finance/profit-ratio",  # 국내주식 수익성비율 (TR: FHKST66430400)
    "STABILITY_RATIO": "/uapi/domestic-stock/v1/finance/stability-ratio",  # 국내주식 안정성비율 (TR: FHKST66430600)
    "GROWTH_RATIO": "/uapi/domestic-stock/v1/finance/growth-ratio",  # 국내주식 성장성비율 (TR: FHKST66430800)
    "ESTIMATE_PERFORM": "/uapi/domestic-stock/v1/quotations/estimate-perform",  # 국내주식 종목추정실적 (TR: HHKST668300C0)
    "INVEST_OPINION": "/uapi/domestic-stock/v1/quotations/invest-opinion",  # 국내주식 종목투자의견 (TR: FHKST663300C0)
    "INVEST_OPBYSEC": "/uapi/domestic-stock/v1/quotations/invest-opbysec",  # 국내주식 증권사별 투자의견 (TR: FHKST663400C0)
    # === 해외주식 ===
    "OVERSEAS_PRICE": "/uapi/overseas-price/v1/quotations/price",  # 해외주식 현재체결가 (TR: HHDFS00000300)
    "OVERSEAS_PRICE_DETAIL": "/uapi/overseas-price/v1/quotations/price-detail",  # 해외주식 현재가상세 (TR: HHDFS76200200)
    "OVERSEAS_DAILYPRICE": "/uapi/overseas-price/v1/quotations/dailyprice",  # 해외주식 기간별시세 (TR: HHDFS76240000)
    "OVERSEAS_INQUIRE_ASKING_PRICE": "/uapi/overseas-price/v1/quotations/inquire-asking-price",  # 해외주식 현재가 10호가 (TR: HHDFS76200100)
    "OVERSEAS_SEARCH_INFO": "/uapi/overseas-price/v1/quotations/search-info",  # 해외주식 상품기본정보 (TR: CTPF1702R)
    "OVERSEAS_NEWS_TITLE": "/uapi/overseas-price/v1/quotations/news-title",  # 해외뉴스종합(제목) (TR: HHPSTH60100C1)
    "OVERSEAS_INQUIRE_TIME_ITEMCHARTPRICE": "/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice",  # 해외주식분봉조회 (TR: HHDFS76950200)
    "OVERSEAS_INQUIRE_DAILY_CHARTPRICE": "/uapi/overseas-price/v1/quotations/inquire-daily-chartprice",  # 해외주식 종목/지수/환율기간별시세 (TR: FHKST03030100)
    # === 해외주식 거래 ===
    "OVERSEAS_INQUIRE_BALANCE": "/uapi/overseas-stock/v1/trading/inquire-balance",  # 해외주식 잔고 (TR: TTTS3012R)
    "OVERSEAS_INQUIRE_CCNL": "/uapi/overseas-stock/v1/trading/inquire-ccnl",  # 해외주식 주문체결내역 (TR: TTTS3035R)
    "OVERSEAS_INQUIRE_PSAMOUNT": "/uapi/overseas-stock/v1/trading/inquire-psamount",  # 해외주식 매수가능금액조회 (TR: TTTS3007R)
    # === 국내선물옵션 시세 (11개) ===
    "FUTURES_DISPLAY_BOARD_CALLPUT": "/uapi/domestic-futureoption/v1/quotations/display-board-callput",  # 옵션 콜/풋 전광판 (TR: FHPIF05030100)
    "FUTURES_DISPLAY_BOARD_FUTURES": "/uapi/domestic-futureoption/v1/quotations/display-board-futures",  # 선물 전광판 (TR: FHPIF05030200)
    "FUTURES_DISPLAY_BOARD_OPTION_LIST": "/uapi/domestic-futureoption/v1/quotations/display-board-option-list",  # 옵션 목록 (TR: FHPIO056104C0)
    "FUTURES_DISPLAY_BOARD_TOP": "/uapi/domestic-futureoption/v1/quotations/display-board-top",  # 상위 종목 (TR: FHPIF05030000)
    "FUTURES_EXP_PRICE_TREND": "/uapi/domestic-futureoption/v1/quotations/exp-price-trend",  # 예상 가격 추이 (TR: FHPIF05110100)
    "FUTURES_INQUIRE_PRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-price",  # 현재가 조회 (TR: FHMIF10000000)
    "FUTURES_INQUIRE_ASKING_PRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-asking-price",  # 호가 조회 (TR: FHMIF10010000)
    "FUTURES_INQUIRE_DAILY_FUOPCHARTPRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice",  # 일별 차트 (TR: FHKIF03020100)
    "FUTURES_INQUIRE_TIME_FUOPCHARTPRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-time-fuopchartprice",  # 분봉 차트 (TR: FHKIF03020200)
    "FUTURES_INQUIRE_CCNL_BSTIME": "/uapi/domestic-futureoption/v1/trading/inquire-ccnl-bstime",  # 시간대별 체결 (TR: CTFO5139R)
    "FUTURES_INQUIRE_DAILY_AMOUNT_FEE": "/uapi/domestic-futureoption/v1/trading/inquire-daily-amount-fee",  # 일별 거래량/수수료 (TR: CTFO6119R)
    # === 국내선물옵션 계좌/잔고 (6개) ===
    "FUTURES_INQUIRE_BALANCE": "/uapi/domestic-futureoption/v1/trading/inquire-balance",  # 잔고 조회 (TR: CTFO6118R/VTFO6118R)
    "FUTURES_INQUIRE_BALANCE_SETTLEMENT_PL": "/uapi/domestic-futureoption/v1/trading/inquire-balance-settlement-pl",  # 청산손익 (TR: CTFO6117R)
    "FUTURES_INQUIRE_BALANCE_VALUATION_PL": "/uapi/domestic-futureoption/v1/trading/inquire-balance-valuation-pl",  # 평가손익 (TR: CTFO6159R)
    "FUTURES_INQUIRE_DEPOSIT": "/uapi/domestic-futureoption/v1/trading/inquire-deposit",  # 예수금 (TR: CTRP6550R)
    "FUTURES_INQUIRE_NGT_BALANCE": "/uapi/domestic-futureoption/v1/trading/inquire-ngt-balance",  # 야간 잔고 (TR: CTFN6118R)
    "FUTURES_NGT_MARGIN_DETAIL": "/uapi/domestic-futureoption/v1/trading/ngt-margin-detail",  # 야간 증거금 (TR: CTFN7107R)
    # === 국내선물옵션 주문/체결 (6개) ===
    "FUTURES_INQUIRE_CCNL": "/uapi/domestic-futureoption/v1/trading/inquire-ccnl",  # 체결 내역 (TR: TTTO5201R/VTTO5201R)
    "FUTURES_INQUIRE_NGT_CCNL": "/uapi/domestic-futureoption/v1/trading/inquire-ngt-ccnl",  # 야간 체결 (TR: STTN5201R)
    "FUTURES_INQUIRE_PSBL_ORDER": "/uapi/domestic-futureoption/v1/trading/inquire-psbl-order",  # 주문 가능 수량 (TR: TTTO5105R/VTTO5105R)
    "FUTURES_INQUIRE_PSBL_NGT_ORDER": "/uapi/domestic-futureoption/v1/trading/inquire-psbl-ngt-order",  # 야간 주문 가능 (TR: STTN5105R)
    "FUTURES_ORDER": "/uapi/domestic-futureoption/v1/trading/order",  # 주문 (TR: TTTO1101U/TTTO1102U)
    "FUTURES_ORDER_RVSECNCL": "/uapi/domestic-futureoption/v1/trading/order-rvsecncl",  # 정정/취소 (TR: TTTO1103U/TTTO1104U)
    # === 레거시 (하위 호환성) ===
    "FUTUREOPTION_INQUIRE_PRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-price",  # → FUTURES_INQUIRE_PRICE
    "FUTUREOPTION_INQUIRE_ASKING_PRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-asking-price",  # → FUTURES_INQUIRE_ASKING_PRICE
    "FUTUREOPTION_INQUIRE_BALANCE": "/uapi/domestic-futureoption/v1/trading/inquire-balance",  # → FUTURES_INQUIRE_BALANCE
    "INQUIRE_INDEX_PRICE": "/uapi/domestic-futureoption/v1/quotations/underlying-price",  # KOSPI 200 지수 (TR: FHMIF10100000)
    "INQUIRE_FUTURES_PRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-price",  # → FUTURES_INQUIRE_PRICE
    # === ETF/ETN ===
    "ETF_INQUIRE_PRICE": "/uapi/etfetn/v1/quotations/inquire-price",  # ETF/ETN현재가 (TR: FHPST02400000)
    "ETF_NAV_COMPARISON_TREND": "/uapi/etfetn/v1/quotations/nav-comparison-trend",  # NAV 비교추이(종목) (TR: FHPST02440000)
    # === 채권 ===
    "BOND_INQUIRE_PRICE": "/uapi/domestic-bond/v1/quotations/inquire-price",  # 장내채권현재가(시세) (TR: FHKBJ773400C0)
    "BOND_INQUIRE_BALANCE": "/uapi/domestic-bond/v1/trading/inquire-balance",  # 장내채권 잔고조회 (TR: CTSC8407R)
    # === 조건검색 ===
    "CONDITIONED_STOCK": "/uapi/domestic-stock/v1/quotations/psearch-result",
    # === 관심종목 ===
    "INTEREST_GROUP_LIST": "/uapi/domestic-stock/v1/quotations/intstock-grouplist",  # 관심종목 그룹 조회
    "INTEREST_STOCK_LIST": "/uapi/domestic-stock/v1/quotations/intstock-stocklist-by-group",  # 관심종목 그룹별 종목 조회
    # === 해외선물옵션 시세 (8개) ===
    "OVRS_FUTR_INQUIRE_PRICE": "/uapi/overseas-futureoption/v1/quotations/inquire-price",  # 해외선물종목현재가
    "OVRS_FUTR_OPT_PRICE": "/uapi/overseas-futureoption/v1/quotations/opt-price",  # 해외옵션종목현재가
    "OVRS_FUTR_MINUTE_CHART": "/uapi/overseas-futureoption/v1/quotations/inquire-time-futurechartprice",  # 해외선물 분봉조회
    "OVRS_FUTR_DAILY_CCNL": "/uapi/overseas-futureoption/v1/quotations/daily-ccnl",  # 해외선물 체결추이(일간)
    "OVRS_FUTR_ASKING_PRICE": "/uapi/overseas-futureoption/v1/quotations/inquire-asking-price",  # 해외선물 호가
    "OVRS_FUTR_OPT_ASKING_PRICE": "/uapi/overseas-futureoption/v1/quotations/opt-asking-price",  # 해외옵션 호가
    "OVRS_FUTR_CONTRACT_DETAIL": "/uapi/overseas-futureoption/v1/quotations/search-contract-detail",  # 해외선물 상품기본정보
    "OVRS_FUTR_OPT_DETAIL": "/uapi/overseas-futureoption/v1/quotations/search-opt-detail",  # 해외옵션 상품기본정보
    # === 해외선물옵션 계좌 (9개) ===
    "OVRS_FUTR_BALANCE": "/uapi/overseas-futureoption/v1/trading/inquire-unpd",  # 미결제내역조회(잔고)
    "OVRS_FUTR_DEPOSIT": "/uapi/overseas-futureoption/v1/trading/inquire-deposit",  # 예수금현황
    "OVRS_FUTR_MARGIN": "/uapi/overseas-futureoption/v1/trading/margin-detail",  # 증거금상세
    "OVRS_FUTR_PSAMOUNT": "/uapi/overseas-futureoption/v1/trading/inquire-psamount",  # 주문가능조회
    "OVRS_FUTR_TODAY_CCLD": "/uapi/overseas-futureoption/v1/trading/inquire-ccld",  # 당일주문내역조회
    "OVRS_FUTR_DAILY_ORDER": "/uapi/overseas-futureoption/v1/trading/inquire-daily-order",  # 일별 주문내역
    "OVRS_FUTR_DAILY_CCLD": "/uapi/overseas-futureoption/v1/trading/inquire-daily-ccld",  # 일별 체결내역
    "OVRS_FUTR_PERIOD_CCLD": "/uapi/overseas-futureoption/v1/trading/inquire-period-ccld",  # 기간계좌손익
    "OVRS_FUTR_PERIOD_TRANS": "/uapi/overseas-futureoption/v1/trading/inquire-period-trans",  # 기간계좌거래내역
    # === 해외선물옵션 주문 (2개) ===
    "OVRS_FUTR_ORDER": "/uapi/overseas-futureoption/v1/trading/order",  # 해외선물옵션 주문
    "OVRS_FUTR_ORDER_RVSECNCL": "/uapi/overseas-futureoption/v1/trading/order-rvsecncl",  # 정정취소주문
}


# 글로벌 rate limit 변수들 제거됨 - 인스턴스별 관리로 변경


class KISClient:
    """
    한국투자증권 OpenAPI 클라이언트

    이 클래스는 한국투자증권 OpenAPI와의 통신을 담당합니다.
    API 요청, 토큰 관리, 요청 제한 관리 등의 기능을 제공합니다.

    Attributes:
        config (KISConfig): API 설정 정보
        token (str): API 인증 토큰
        base_url (str): API 기본 URL
        verbose (bool): 상세 로깅 여부

    Example:
        >>> client = KISClient()
        >>> response = client.make_request('/uapi/domestic-stock/v1/quotations/inquire-price', 'FHKST01010100', {'FID_COND_MRKT_DIV_CODE': 'UN', 'FID_INPUT_ISCD': '005930'})
    """

    def __init__(
        self,
        svr: str = "prod",
        config=None,
        verbose: bool = False,
        enable_rate_limiter: bool = True,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        """
        KISClient를 초기화합니다.

        Args:
            svr (str): 서버 환경 ('prod' 또는 'dev')
            config (KISConfig, optional): API 설정 정보
            verbose (bool): 상세 로깅 여부
            enable_rate_limiter (bool): Rate Limiter 사용 여부
            rate_limiter (RateLimiter, optional): 커스텀 Rate Limiter 인스턴스

        Raises:
            Exception: 인증 실패 시 발생
        """
        if isinstance(svr, KISConfig):
            self.config = svr
            svr = "prod"
        else:
            self.config = config
        self.verbose = verbose
        self.token: Optional[str] = None
        self.token_expired: Optional[str] = None  # 토큰 만료 시간 저장
        self.svr = svr  # 서버 환경 저장
        self.last_api_call_time = time.monotonic()
        self.last_request_time = 0.0
        self.min_interval = 0.05  # 50ms
        self.rate_limit_lock = threading.Lock()  # 인스턴스별 rate limit lock
        self.token_refresh_lock = threading.Lock()  # 토큰 재생성 동기화용 락

        # Rate Limiter 설정 (2025.09.21 실측 기반)
        # 공식 스펙: 초당 20회 / 분당 1000회
        # 안정 운영: 초당 18회 / 분당 900회 (실측 기반 권장)
        # 전역 싱글턴 사용: 모든 KISClient/Agent가 동일한 Rate Limiter 공유
        self.enable_rate_limiter = enable_rate_limiter
        if enable_rate_limiter:
            # 명시적으로 전달된 rate_limiter가 있으면 사용, 없으면 전역 싱글턴 사용
            self.rate_limiter = rate_limiter or get_global_rate_limiter(
                requests_per_second=18,  # 실측 기반 안정 한계
                requests_per_minute=900,  # 실측 기반 안정 한계
                min_interval_ms=55,  # 최소 55ms 간격 (18 RPS 기준)
                burst_size=10,  # 순간 처리량 허용
                enable_adaptive=True,
            )
        else:
            self.rate_limiter = None

        # 초기 토큰 발급 또는 기존 토큰 재사용
        self._initialize_token()

        # is_real 속성 설정 (실전투자 여부 판단)
        # 실전투자: https://openapi.koreainvestment.com:9443
        # 모의투자: https://openapivts.koreainvestment.com:29443
        self.is_real = "openapivts" not in getattr(self, "base_url", "")

    def _initialize_token(self) -> None:
        """초기 토큰 발급 또는 기존 토큰 재사용 (Thread-Safe)"""
        with self.token_refresh_lock:
            try:
                # 토큰이 이미 유효한 경우 재발급하지 않음 (중복 방지)
                if self.token and self.token_expired:
                    try:
                        exp_dt = (
                            datetime.strptime(self.token_expired, "%Y-%m-%d %H:%M:%S")
                            if isinstance(self.token_expired, str)
                            else self.token_expired
                        )
                        now_dt = datetime.now()
                        # 5분 이상 남았으면 재발급하지 않음
                        if exp_dt > now_dt + timedelta(minutes=5):
                            logger.debug("토큰이 아직 유효합니다. 재발급하지 않습니다.")
                            return
                    except Exception as e:
                        logger.warning(f"토큰 만료 시간 파싱 실패, 재발급 진행: {e}")

                logger.info("토큰 발급을 시작합니다...")
                if self.config is None:
                    # config가 없으면 환경 변수로 토큰 발급
                    token_data = auth(svr=self.svr)
                    if token_data:
                        self.token = token_data.get("access_token")
                        self.token_expired = token_data.get(
                            "access_token_token_expired"
                        )
                        logger.info(f"토큰 발급 완료 (만료: {self.token_expired})")
                    self.base_url = os.getenv(
                        "KIS_BASE_URL", "https://openapi.koreainvestment.com:9443"
                    )
                else:
                    # config가 있으면 config로 토큰 발급
                    token_data = auth(config=self.config, svr=self.svr)
                    if token_data:
                        self.token = token_data.get("access_token")
                        self.token_expired = token_data.get(
                            "access_token_token_expired"
                        )
                        logger.info(f"토큰 발급 완료 (만료: {self.token_expired})")
                    self.base_url = self.config.BASE_URL
            except Exception as e:
                logger.error(f"인증 실패: {e}", exc_info=True)
                raise

    def _check_and_refresh_token(self) -> None:
        """토큰 만료 체크 및 자동 갱신"""
        if self.token_expired:
            try:
                # 토큰 만료 시간 파싱
                exp_dt = (
                    datetime.strptime(self.token_expired, "%Y-%m-%d %H:%M:%S")
                    if isinstance(self.token_expired, str)
                    else self.token_expired
                )

                # 현재 시간
                now_dt = datetime.now()

                # 토큰이 만료되었거나 5분 이내 만료 예정이면 갱신
                if exp_dt <= now_dt + timedelta(minutes=5):
                    # logger.info("토큰이 만료되었거나 곧 만료됩니다. 자동 갱신을 시작합니다.")
                    self._initialize_token()
            except Exception as e:
                logger.warning(f"토큰 만료 체크 중 오류 발생, 토큰 재발급 시도: {e}")
                self._initialize_token()

    def _enforce_rate_limit(self, priority: int = 0) -> None:
        """
        API 요청 제한을 관리합니다 (인스턴스별).

        Args:
            priority: 요청 우선순위 (0=일반, 1=중요, 2=긴급)
        """
        if self.enable_rate_limiter and self.rate_limiter:
            # 새로운 Rate Limiter 사용
            wait_time = self.rate_limiter.acquire(priority)
            if wait_time > 0 and self.verbose:
                logger.debug(f"Rate limiter 대기: {wait_time:.3f}초")
        else:
            # 기존 방식 유지 (하위 호환성)
            with self.rate_limit_lock:
                now = time.monotonic()
                elapsed = now - self.last_api_call_time
                if elapsed < self.min_interval:
                    time.sleep(self.min_interval - elapsed)
                self.last_api_call_time = time.monotonic()
                self.last_request_time = self.last_api_call_time

    def _get_base_headers(self, tr_id: str) -> Dict[str, str]:
        """
        기본 HTTP 헤더를 생성합니다.

        Args:
            tr_id (str): API 트랜잭션 ID

        Returns:
            Dict[str, str]: HTTP 헤더
        """
        return {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.token}",
            "appKey": getTREnv().my_app,
            "appSecret": getTREnv().my_sec,
            "tr_id": tr_id,
            "custtype": "P",
        }

    def make_request(
        self,
        endpoint: str,
        tr_id: str,
        params: Dict[str, Any],
        method: str = "GET",
        retries: int = 2,  # [변경 이유] 테스트 속도 향상을 위해 재시도 횟수를 5회 → 2회로 단축
        headers: Dict[str, str] = None,
        priority: int = 0,  # 요청 우선순위 (0=일반, 1=중요, 2=긴급)
    ) -> Optional[Dict[str, Any]]:
        """
        API 요청을 보내고 응답을 처리합니다.

        Args:
            endpoint (str): API 엔드포인트 URL
            tr_id (str): API 트랜잭션 ID
            params (Dict[str, Any]): API 요청 파라미터
            method (str): HTTP 메서드 (기본값: 'GET')
            retries (int): 재시도 횟수 (기본값: 5)
            headers (Dict[str, str], optional): 추가 HTTP 헤더

        Returns:
            Optional[Dict[str, Any]]: API 응답 데이터

        Raises:
            Exception: API 요청 실패 시 발생
        """
        # 요청 전 토큰 만료 체크 및 자동 갱신
        self._check_and_refresh_token()

        url = f"{self.base_url}{endpoint}"

        # getTREnv()를 사용하여 올바른 헤더 설정
        env = getTREnv()
        headers = headers or {}
        headers["authorization"] = env.my_token
        headers["content-type"] = "application/json"
        headers["appkey"] = env.my_app
        headers["appsecret"] = env.my_sec
        headers["tr_id"] = tr_id
        headers["custtype"] = "P"  # 개인 고객 (필수: 주문 API에서 요구됨)

        if self.verbose:
            logger.debug(f"요청 URL: {url}")
            logger.debug(f"요청 헤더: {headers}")
            logger.debug(f"요청 파라미터: {params}")

        last_exception = None

        for attempt in range(retries):
            self._enforce_rate_limit(priority)
            response = None
            data = None
            try:
                if self.verbose:
                    logger.info(f"[API] ({method}) {tr_id} 시도 {attempt+1}/{retries}")

                response = requests.request(
                    method.upper(),
                    url,
                    headers=headers,
                    params=params if method.upper() == "GET" else None,
                    json=params if method.upper() != "GET" else None,
                    timeout=15,
                )

                try:
                    data = response.json()
                except json.JSONDecodeError:
                    logger.error(
                        f"[{tr_id}] JSON 디코드 실패 (시도 {attempt+1}/{retries})"
                    )
                    logger.error(
                        f"[{tr_id}] 원시 응답 텍스트: {response.text[:500]}..."
                    )
                    logger.error(f"[{tr_id}] 응답 상태 코드: {response.status_code}")
                    logger.error(f"[{tr_id}] 응답 헤더: {dict(response.headers)}")
                    return {
                        "rt_cd": "JSON_DECODE_ERROR",
                        "msg1": "JSON 디코드 실패",
                        "raw_text": response.text,
                        "status_code": response.status_code,
                        "error_type": "JSONDecodeError",
                    }

                rt_cd = data.get("rt_cd")
                if rt_cd is None:
                    logger.error(f"[{tr_id}] rt_cd 값이 없음: {data}")
                    return {
                        "rt_cd": "NO_RT_CD",
                        "msg1": "응답에 rt_cd 값이 없음",
                        "raw_data": data,
                        "status_code": response.status_code,
                        "error_type": "NoRtCd",
                    }

                if response.status_code == 200 and rt_cd == "0":
                    if self.verbose and tr_id != "TTTC8434R":
                        logger.info(f"[API] 응답: {data}")
                    # 성공 시 Rate Limiter에 보고
                    if self.enable_rate_limiter and self.rate_limiter:
                        self.rate_limiter.report_success()
                    return data
                else:
                    if response.status_code == 200 and rt_cd != "0":
                        api_msg = data.get("msg1", "")
                        api_code = data.get("rt_cd")
                        logger.warning(
                            f"[{tr_id}] API 오류 응답 (시도 {attempt+1}/{retries}): {api_msg} (code: {api_code})"
                        )

                        # 유량 제한 에러 체크
                        # 토큰 만료 에러 체크
                        is_token_expired = (
                            isinstance(api_code, str)
                            and api_code
                            in ["EGW00123", "EGW00124"]  # 토큰 만료 에러 코드
                        ) or (
                            isinstance(api_msg, str)
                            and ("토큰" in api_msg and "만료" in api_msg)
                        )

                        if is_token_expired:
                            logger.warning(f"[{tr_id}] 토큰 만료 감지. 재발급 시도...")
                            self._initialize_token()
                            # 헤더 업데이트
                            env = getTREnv()
                            headers["authorization"] = env.my_token
                            if attempt < retries - 1:
                                continue  # 토큰 갱신 후 재시도

                        is_rate_limit_error = (
                            isinstance(api_code, str)
                            and (
                                api_code == "1"
                                or api_code in ["EGW00201", "EGW00202", "EGW00203"]
                            )
                            and isinstance(api_msg, str)
                            and (
                                "초당 거래건수를 초과" in api_msg
                                or "유량 제한" in api_msg
                            )
                        )

                        if is_rate_limit_error:
                            # Rate Limiter에 에러 보고
                            if self.enable_rate_limiter and self.rate_limiter:
                                self.rate_limiter.report_error(api_code)

                            if attempt < retries - 1:
                                logger.warning(
                                    f"[{tr_id}] API 유량 제한 감지 (code: {api_code}). 0.5초 대기 후 재시도... ({attempt+1}/{retries})"
                                )
                                time.sleep(
                                    0.5
                                )  # [변경 이유] 테스트 속도 향상을 위해 대기 시간을 1초 → 0.5초로 단축
                            else:
                                logger.error(
                                    f"[{tr_id}] API 유량 제한 최종 실패 (재시도 소진)."
                                )
                                return data
                        else:
                            return {
                                "rt_cd": api_code,
                                "msg1": api_msg,
                                "raw_data": data,
                                "status_code": response.status_code,
                                "error_type": "ApiError",
                            }
                    elif response.status_code != 200:
                        http_error_msg = (
                            data.get("msg1", response.text)
                            if data and isinstance(data, dict)
                            else response.text
                        )
                        http_error_code_from_json = (
                            data.get("rt_cd")
                            if data and isinstance(data, dict)
                            else None
                        )
                        log_entry = f"[{tr_id}] HTTP 오류 응답 (시도 {attempt+1}/{retries}): Status {response.status_code}, Message: {http_error_msg}"
                        if http_error_code_from_json:
                            log_entry += (
                                f" (API Code in JSON: {http_error_code_from_json})"
                            )
                        logger.warning(log_entry)
                        if attempt < retries - 1:
                            time.sleep(
                                0.2
                            )  # [변경 이유] 테스트 속도 향상을 위해 HTTP 오류 시 대기 시간을 단축
                            continue
                        else:
                            logger.error(
                                f"[{tr_id}] HTTP 오류 최종 실패 (재시도 소진)."
                            )
                            return (
                                data
                                if data
                                else {
                                    "rt_cd": str(response.status_code),
                                    "msg1": response.text,
                                    "error_type": "HTTPErrorFinal",
                                }
                            )
                    else:
                        logger.error(
                            f"[{tr_id}] 로직 오류: 예상치 못한 HTTP/API 상태 (시도 {attempt+1}/{retries}). 응답: {data}. HTTP Status: {response.status_code if response else 'N/A'}"
                        )
                        return data
            except requests.exceptions.RequestException as e:
                logger.error(f"[{tr_id}] 요청 실패 (시도 {attempt+1}/{retries}): {e}")
                last_exception = e
                if attempt < retries - 1:
                    time.sleep(
                        0.2
                    )  # [변경 이유] 테스트 속도 향상을 위해 요청 실패 시 대기 시간을 단축
                    continue
                else:
                    logger.error(
                        f"[{tr_id}] 요청 최종 실패 (재시도 소진): {last_exception}"
                    )
                    raise last_exception

        logger.error(
            f"[{tr_id}] 최종 실패 후 루프 외부 도달: {last_exception if last_exception else '알 수 없는 오류'}"
        )
        if last_exception:
            raise last_exception
        raise Exception("Unknown error after retries")

    def refresh_token(self) -> None:
        """
        API 토큰을 갱신합니다. (Thread-Safe)

        Raises:
            Exception: 토큰 갱신 실패 시 발생
        """
        with self.token_refresh_lock:
            try:
                logger.info("토큰 갱신을 시작합니다...")
                response = requests.post(
                    f"{self.base_url}/oauth2/tokenP",
                    json={
                        "grant_type": "client_credentials",
                        "appkey": self.config.APP_KEY,
                        "appsecret": self.config.APP_SECRET,
                    },
                    headers={"content-type": "application/json"},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")
                    self.token_expired = data.get("access_token_token_expired")

                    if not self.token:
                        raise Exception("토큰 갱신 실패: access_token이 없습니다.")

                    logger.info(f"토큰 갱신 완료 (만료: {self.token_expired})")
                else:
                    raise Exception(f"토큰 갱신 실패: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"토큰 갱신 실패: {e}")
                raise

    def get_kospi200_index(
        self, futures_month: str = "202409"
    ) -> Optional[Dict[str, Any]]:
        """
        KOSPI200 지수 조회

        Args:
            futures_month (str): 선물 만료월 (YYYYMM 형식)

        Returns:
            Dict[str, Any]: KOSPI200 지수 정보
        """
        endpoint = API_ENDPOINTS["INQUIRE_INDEX_PRICE"]
        params = {
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": f"101{futures_month[-2:]}000",
        }
        return self.make_request(endpoint, "FHMIF10100000", params)

    def get_ws_approval_key(self) -> Optional[str]:
        """
        웹소켓 접속을 위한 승인키를 가져옵니다.

        Returns:
            str: 웹소켓 승인키
        """
        url = f"{self.base_url}/oauth2/Approval"

        payload = {
            "grant_type": "client_credentials",
            "appkey": self.config.app_key if self.config else os.getenv("KIS_APP_KEY"),
            "secretkey": (
                self.config.app_secret if self.config else os.getenv("KIS_APP_SECRET")
            ),
        }

        headers = {"content-type": "application/json"}

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                approval_key = response.json().get("approval_key")
                if not approval_key:
                    logger.error("응답에서 approval_key를 추출하지 못했습니다.")
                    return None
                logger.info(f"웹소켓 승인키 발급 완료: {approval_key[:10]}...")
                return approval_key
            else:
                logger.error(
                    f"웹소켓 승인키 요청 실패: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"웹소켓 승인키 요청 중 오류 발생: {e}")
            return None


__all__ = ["KISClient", "API_ENDPOINTS"]
