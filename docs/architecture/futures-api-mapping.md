# Futures API Endpoint & TR_ID 매핑

**작성일**: 2026-01-19
**관련 이슈**: [INT-506](https://linear.app/intrect/issue/INT-506)

---

## 1. 국내선물옵션 (Domestic Futures/Options) - 23개 API

### 1.1 시세 조회 API (11개) - FuturesPriceAPI

| 순번 | 메서드명 | TR_ID | Endpoint | 설명 | 비고 |
|-----|---------|-------|----------|------|------|
| 1 | `display_board_callput()` | FHPIF05030100 | `/uapi/domestic-futureoption/v1/quotations/display-board-callput` | 국내옵션전광판_콜풋 | output1, output2 각 100건 |
| 2 | `display_board_futures()` | FHPIF05030200 | `/uapi/domestic-futureoption/v1/quotations/display-board-futures` | 국내옵션전광판_선물 | 조회 시간 긴 API |
| 3 | `display_board_option_list()` | FHPIO056104C0 | `/uapi/domestic-futureoption/v1/quotations/display-board-option-list` | 국내옵션전광판_옵션목록 | 옵션 종목 리스트 |
| 4 | `display_board_top()` | FHPIF05030000 | `/uapi/domestic-futureoption/v1/quotations/display-board-top` | 국내옵션전광판_상위TOP | 상위 종목 랭킹 |
| 5 | `exp_price_trend()` | FHPIF05110100 | `/uapi/domestic-futureoption/v1/quotations/exp-price-trend` | 선물옵션 일중예상체결추이 | 실시간 예상 체결가 추이 |
| 6 | `inquire_price()` | FHMIF10000000 | `/uapi/domestic-futureoption/v1/quotations/inquire-price` | 선물옵션 현재가시세 | 핵심 시세 API |
| 7 | `inquire_asking_price()` | FHMIF10010000 | `/uapi/domestic-futureoption/v1/quotations/inquire-asking-price` | 선물옵션 현재가호가 | 10호가 정보 |
| 8 | `inquire_daily_fuopchartprice()` | FHKIF03020100 | `/uapi/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice` | 선물옵션 일별차트 | 일/주/월봉 |
| 9 | `inquire_time_fuopchartprice()` | FHKIF03020200 | `/uapi/domestic-futureoption/v1/quotations/inquire-time-fuopchartprice` | 선물옵션 분봉조회 | 1/3/5/10/30/60분봉 |
| 10 | `inquire_ccnl_bstime()` | CTFO5139R | `/uapi/domestic-futureoption/v1/trading/inquire-ccnl-bstime` | 선물옵션 시간대별체결 | 시간대별 체결 내역 |
| 11 | `inquire_daily_amount_fee()` | CTFO6119R | `/uapi/domestic-futureoption/v1/trading/inquire-daily-amount-fee` | 선물옵션 기간약정수수료일별 | 일별 거래량/수수료 |

### 1.2 계좌/잔고 조회 API (6개) - FuturesAccountAPI

| 순번 | 메서드명 | TR_ID | Endpoint | 설명 | 비고 |
|-----|---------|-------|----------|------|------|
| 12 | `inquire_balance()` | CTFO6118R (실전)<br>VTFO6118R (모의) | `/uapi/domestic-futureoption/v1/trading/inquire-balance` | 선물옵션 잔고현황 | 핵심 잔고 API |
| 13 | `inquire_balance_settlement_pl()` | CTFO6117R | `/uapi/domestic-futureoption/v1/trading/inquire-balance-settlement-pl` | 선물옵션 잔고청산손익 | 청산 손익 상세 |
| 14 | `inquire_balance_valuation_pl()` | CTFO6159R | `/uapi/domestic-futureoption/v1/trading/inquire-balance-valuation-pl` | 선물옵션 잔고평가손익내역 | 평가 손익 상세 |
| 15 | `inquire_deposit()` | CTRP6550R | `/uapi/domestic-futureoption/v1/trading/inquire-deposit` | 선물옵션 총자산현황 | 예수금 및 총자산 |
| 16 | `inquire_ngt_balance()` | CTFN6118R | `/uapi/domestic-futureoption/v1/trading/inquire-ngt-balance` | 야간 선물옵션 잔고현황 | 야간 거래 잔고 |
| 17 | `ngt_margin_detail()` | CTFN7107R | `/uapi/domestic-futureoption/v1/trading/ngt-margin-detail` | (야간)선물옵션 증거금 상세 | 야간 증거금 내역 |

### 1.3 주문/체결 조회 API (6개) - FuturesOrderAPI

| 순번 | 메서드명 | TR_ID | Endpoint | 설명 | 비고 |
|-----|---------|-------|----------|------|------|
| 18 | `inquire_ccnl()` | TTTO5201R (실전)<br>VTTO5201R (모의) | `/uapi/domestic-futureoption/v1/trading/inquire-ccnl` | 선물옵션 체결내역 | 당일 체결 내역 |
| 19 | `inquire_ngt_ccnl()` | STTN5201R | `/uapi/domestic-futureoption/v1/trading/inquire-ngt-ccnl` | 야간 선물옵션 체결내역 | 야간 거래 체결 |
| 20 | `inquire_psbl_order()` | TTTO5105R (실전)<br>VTTO5105R (모의) | `/uapi/domestic-futureoption/v1/trading/inquire-psbl-order` | 선물옵션 주문가능수량 | 주문 가능 수량 조회 |
| 21 | `inquire_psbl_ngt_order()` | STTN5105R | `/uapi/domestic-futureoption/v1/trading/inquire-psbl-ngt-order` | 야간 선물옵션 주문가능수량 | 야간 주문 가능 |
| 22 | `order()` | TTTO1101U (실전 매수)<br>TTTO1102U (실전 매도)<br>STTN1101U (야간 매수)<br>STTN1102U (야간 매도) | `/uapi/domestic-futureoption/v1/trading/order` | 선물옵션 주문 | 신규/청산 주문 |
| 23 | `order_rvsecncl()` | TTTO1103U (정정)<br>TTTO1104U (취소) | `/uapi/domestic-futureoption/v1/trading/order-rvsecncl` | 선물옵션 정정/취소 | 주문 정정/취소 |

---

## 2. 해외선물옵션 (Overseas Futures/Options) - 31개 API

### 2.1 시세 조회 API (14개) - OverseasFuturesPriceAPI

| 순번 | 메서드명 | TR_ID | Endpoint | 설명 | 비고 |
|-----|---------|-------|----------|------|------|
| 1 | `inquire_price()` | HHDFC552200C0 | `/uapi/overseas-futureoption/v1/quotations/inquire-price` | 해외선물옵션 현재가 | 핵심 시세 API |
| 2 | `inquire_asking_price()` | HHDFC552300C0 | `/uapi/overseas-futureoption/v1/quotations/inquire-asking-price` | 해외선물옵션 호가 | 호가 정보 |
| 3 | `inquire_time_futurechartprice()` | HHDFC55236000 | `/uapi/overseas-futureoption/v1/quotations/inquire-time-futurechartprice` | 해외선물 분봉차트 | 선물 분봉 |
| 4 | `inquire_time_optchartprice()` | HHDFO55237000 | `/uapi/overseas-futureoption/v1/quotations/inquire-time-optchartprice` | 해외옵션 분봉차트 | 옵션 분봉 |
| 5 | `asking_price()` | H0FOPRC0 (실시간) | WebSocket | 해외선물옵션 실시간호가 | 실시간 구독 |
| 6 | `ccnl()` | H0FUCNT0 (실시간) | WebSocket | 해외선물옵션 실시간체결 | 실시간 구독 |
| 7 | `ccnl_notice()` | H0STCNI0 (실시간) | WebSocket | 해외선물옵션 체결통보 | 실시간 알림 |
| 8 | `daily_ccnl()` | HHDFO55310000 | `/uapi/overseas-futureoption/v1/trading/daily-ccnl` | 해외선물옵션 일별체결 | 일별 체결 내역 |
| 9-14 | *(추가 시세 API 6개)* | - | - | *(상세 정의 필요)* | - |

### 2.2 계좌/주문 조회 API (10개) - OverseasFuturesAccountAPI

| 순번 | 메서드명 | TR_ID | Endpoint | 설명 | 비고 |
|-----|---------|-------|----------|------|------|
| 15 | `inquire_deposit()` | CTOS5011R | `/uapi/overseas-futureoption/v1/trading/inquire-deposit` | 해외선물옵션 예수금 | 예수금 조회 |
| 16 | `inquire_psamount()` | CTOS5002R | `/uapi/overseas-futureoption/v1/trading/inquire-psamount` | 해외선물옵션 매수가능금액 | 주문 가능 금액 |
| 17 | `inquire_ccld()` | CTOS5005R | `/uapi/overseas-futureoption/v1/trading/inquire-ccld` | 해외선물옵션 체결내역 | 당일 체결 |
| 18 | `inquire_daily_ccld()` | CTOS5006R | `/uapi/overseas-futureoption/v1/trading/inquire-daily-ccld` | 해외선물옵션 일별체결내역 | 기간별 체결 |
| 19 | `inquire_period_ccld()` | CTOS5007R | `/uapi/overseas-futureoption/v1/trading/inquire-period-ccld` | 해외선물옵션 기간별체결 | 기간 조회 |
| 20 | `inquire_daily_order()` | CTOS5010R | `/uapi/overseas-futureoption/v1/trading/inquire-daily-order` | 해외선물옵션 일별주문내역 | 일별 주문 |
| 21 | `inquire_period_trans()` | CTOS5008R | `/uapi/overseas-futureoption/v1/trading/inquire-period-trans` | 해외선물옵션 기간별거래내역 | 거래 내역 |
| 22 | `inquire_unpd()` | CTOS5004R | `/uapi/overseas-futureoption/v1/trading/inquire-unpd` | 해외선물옵션 미체결내역 | 미체결 조회 |
| 23 | `investor_unpd_trend()` | HHDFO55316100 | `/uapi/overseas-futureoption/v1/quotations/investor-unpd-trend` | 해외선물옵션 투자자별미체결 | 투자자 분류 |
| 24 | *(추가 계좌 API 1개)* | - | - | *(상세 정의 필요)* | - |

### 2.3 주문 실행 API (7개) - OverseasFuturesOrderAPI

| 순번 | 메서드명 | TR_ID | Endpoint | 설명 | 비고 |
|-----|---------|-------|----------|------|------|
| 25 | `order()` | CTOS5002U (매수)<br>CTOS5003U (매도) | `/uapi/overseas-futureoption/v1/trading/order` | 해외선물옵션 주문 | 신규 주문 |
| 26 | `order_rvsecncl()` | CTOS5004U (정정)<br>CTOS5005U (취소) | `/uapi/overseas-futureoption/v1/trading/order-rvsecncl` | 해외선물옵션 정정/취소 | 주문 수정 |
| 27-31 | *(추가 주문 API 5개)* | - | - | *(상세 정의 필요)* | - |

---

## 3. API Endpoints 확장 (client.py 추가)

### 3.1 국내선물옵션 (23개)

```python
# pykis/core/client.py

API_ENDPOINTS = {
    # ... 기존 endpoints ...

    # === 국내선물옵션 시세 ===
    "FUTURES_DISPLAY_BOARD_CALLPUT": "/uapi/domestic-futureoption/v1/quotations/display-board-callput",
    "FUTURES_DISPLAY_BOARD_FUTURES": "/uapi/domestic-futureoption/v1/quotations/display-board-futures",
    "FUTURES_DISPLAY_BOARD_OPTION_LIST": "/uapi/domestic-futureoption/v1/quotations/display-board-option-list",
    "FUTURES_DISPLAY_BOARD_TOP": "/uapi/domestic-futureoption/v1/quotations/display-board-top",
    "FUTURES_EXP_PRICE_TREND": "/uapi/domestic-futureoption/v1/quotations/exp-price-trend",
    "FUTURES_INQUIRE_PRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-price",
    "FUTURES_INQUIRE_ASKING_PRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-asking-price",
    "FUTURES_INQUIRE_DAILY_FUOPCHARTPRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice",
    "FUTURES_INQUIRE_TIME_FUOPCHARTPRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-time-fuopchartprice",
    "FUTURES_INQUIRE_CCNL_BSTIME": "/uapi/domestic-futureoption/v1/trading/inquire-ccnl-bstime",
    "FUTURES_INQUIRE_DAILY_AMOUNT_FEE": "/uapi/domestic-futureoption/v1/trading/inquire-daily-amount-fee",

    # === 국내선물옵션 계좌/잔고 ===
    "FUTURES_INQUIRE_BALANCE": "/uapi/domestic-futureoption/v1/trading/inquire-balance",
    "FUTURES_INQUIRE_BALANCE_SETTLEMENT_PL": "/uapi/domestic-futureoption/v1/trading/inquire-balance-settlement-pl",
    "FUTURES_INQUIRE_BALANCE_VALUATION_PL": "/uapi/domestic-futureoption/v1/trading/inquire-balance-valuation-pl",
    "FUTURES_INQUIRE_DEPOSIT": "/uapi/domestic-futureoption/v1/trading/inquire-deposit",
    "FUTURES_INQUIRE_NGT_BALANCE": "/uapi/domestic-futureoption/v1/trading/inquire-ngt-balance",
    "FUTURES_NGT_MARGIN_DETAIL": "/uapi/domestic-futureoption/v1/trading/ngt-margin-detail",

    # === 국내선물옵션 주문/체결 ===
    "FUTURES_INQUIRE_CCNL": "/uapi/domestic-futureoption/v1/trading/inquire-ccnl",
    "FUTURES_INQUIRE_NGT_CCNL": "/uapi/domestic-futureoption/v1/trading/inquire-ngt-ccnl",
    "FUTURES_INQUIRE_PSBL_ORDER": "/uapi/domestic-futureoption/v1/trading/inquire-psbl-order",
    "FUTURES_INQUIRE_PSBL_NGT_ORDER": "/uapi/domestic-futureoption/v1/trading/inquire-psbl-ngt-order",
    "FUTURES_ORDER": "/uapi/domestic-futureoption/v1/trading/order",
    "FUTURES_ORDER_RVSECNCL": "/uapi/domestic-futureoption/v1/trading/order-rvsecncl",

    # === 해외선물옵션 시세 ===
    "OVERSEAS_FUTURES_INQUIRE_PRICE": "/uapi/overseas-futureoption/v1/quotations/inquire-price",
    "OVERSEAS_FUTURES_INQUIRE_ASKING_PRICE": "/uapi/overseas-futureoption/v1/quotations/inquire-asking-price",
    "OVERSEAS_FUTURES_INQUIRE_TIME_FUTURECHARTPRICE": "/uapi/overseas-futureoption/v1/quotations/inquire-time-futurechartprice",
    "OVERSEAS_FUTURES_INQUIRE_TIME_OPTCHARTPRICE": "/uapi/overseas-futureoption/v1/quotations/inquire-time-optchartprice",
    "OVERSEAS_FUTURES_DAILY_CCNL": "/uapi/overseas-futureoption/v1/trading/daily-ccnl",

    # === 해외선물옵션 계좌/주문 ===
    "OVERSEAS_FUTURES_INQUIRE_DEPOSIT": "/uapi/overseas-futureoption/v1/trading/inquire-deposit",
    "OVERSEAS_FUTURES_INQUIRE_PSAMOUNT": "/uapi/overseas-futureoption/v1/trading/inquire-psamount",
    "OVERSEAS_FUTURES_INQUIRE_CCLD": "/uapi/overseas-futureoption/v1/trading/inquire-ccld",
    "OVERSEAS_FUTURES_INQUIRE_DAILY_CCLD": "/uapi/overseas-futureoption/v1/trading/inquire-daily-ccld",
    "OVERSEAS_FUTURES_INQUIRE_PERIOD_CCLD": "/uapi/overseas-futureoption/v1/trading/inquire-period-ccld",
    "OVERSEAS_FUTURES_INQUIRE_DAILY_ORDER": "/uapi/overseas-futureoption/v1/trading/inquire-daily-order",
    "OVERSEAS_FUTURES_INQUIRE_PERIOD_TRANS": "/uapi/overseas-futureoption/v1/trading/inquire-period-trans",
    "OVERSEAS_FUTURES_INQUIRE_UNPD": "/uapi/overseas-futureoption/v1/trading/inquire-unpd",
    "OVERSEAS_FUTURES_INVESTOR_UNPD_TREND": "/uapi/overseas-futureoption/v1/quotations/investor-unpd-trend",
    "OVERSEAS_FUTURES_ORDER": "/uapi/overseas-futureoption/v1/trading/order",
    "OVERSEAS_FUTURES_ORDER_RVSECNCL": "/uapi/overseas-futureoption/v1/trading/order-rvsecncl",
}
```

---

## 4. TR_ID 매핑 규칙

### 4.1 국내선물옵션 TR_ID 패턴

- **시세 조회**: `FHPIF*`, `FHMIF*`, `FHKIF*`
  - 예: `FHMIF10000000` (현재가), `FHKIF03020100` (일별차트)

- **계좌/잔고**: `CTFO*`, `CTRP*`, `CTFN*` (야간)
  - 실전: `CTFO6118R` (잔고)
  - 모의: `VTFO6118R` (잔고)
  - 야간: `CTFN6118R` (야간 잔고)

- **주문/체결**: `TTTO*` (당일), `STTN*` (야간)
  - 실전 주문: `TTTO1101U` (매수), `TTTO1102U` (매도)
  - 야간 주문: `STTN1101U` (매수), `STTN1102U` (매도)
  - 정정/취소: `TTTO1103U` (정정), `TTTO1104U` (취소)

### 4.2 해외선물옵션 TR_ID 패턴

- **시세 조회**: `HHDFC*` (선물), `HHDFO*` (옵션)
  - 예: `HHDFC552200C0` (현재가), `HHDFO55237000` (옵션 분봉)

- **계좌/주문**: `CTOS*`
  - 예: `CTOS5011R` (예수금), `CTOS5002U` (매수 주문)

---

## 5. 변경 이력

- **2026-01-19**: v1.0 초안 작성 (국내선물옵션 23개 API 매핑 완료)
