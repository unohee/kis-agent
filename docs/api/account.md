# 계좌 관리 API

`agent.account_api` 또는 `agent` 직접 호출로 접근합니다. 내부적으로 `AccountAPI` Facade가 `AccountBalanceQueryAPI`, `AccountOrderAPI`, `AccountProfitAPI`에 위임합니다.

## 잔고/자산 조회

```python
# 계좌 잔고 (output1=보유종목, output2=요약)
balance = agent.account_api.get_account_balance()

# 종목별 매수가능금액
cash = agent.account_api.get_cash_available("005930")

# 총자산
total = agent.account_api.get_total_asset()

# 종목별 주문가능수량
qty = agent.account_api.get_account_order_quantity("005930")

# 주문가능금액
amount = agent.account_api.get_possible_order_amount()

# 실현손익
rlz = agent.account_api.inquire_balance_rlz_pl()

# 매도가능수량
sell = agent.account_api.inquire_psbl_sell("005930")

# 통합증거금 현황
margin = agent.account_api.inquire_intgr_margin()

# 매수가능 조회
psbl = agent.account_api.inquire_psbl_order(price=70000, pdno="005930")

# 신용매수가능 조회
credit = agent.account_api.inquire_credit_psamount("005930")
```

## 주문

### 현금 주문

```python
# 주식주문(현금)
result = agent.account_api.order_cash(
    pdno="005930", qty=10, price=70000,
    buy_sell="BUY", order_type="00",  # 지정가
    exchange="KRX"  # KRX, NXT, SOR
)

# SOR 최유리지정가 주문
result = agent.account_api.order_cash_sor(
    pdno="005930", qty=10, buy_sell="BUY"
)
```

**주문유형 코드:**

| 코드 | 설명 |
|:---|:---|
| `00` | 지정가 |
| `01` | 시장가 |
| `02` | 조건부지정가 |
| `03` | 최유리지정가 |
| `05` | 장전시간외 |
| `06` | 장후시간외 |
| `11` | IOC지정가 |
| `12` | FOK지정가 |

### 신용 주문

```python
# 신용매수 (credit_type: "21"=융자, "61"=대주)
result = agent.account_api.order_credit_buy(
    pdno="005930", qty=10, price=70000,
    credit_type="21"
)

# 신용매도
result = agent.account_api.order_credit_sell(
    pdno="005930", qty=10, price=78000,
    credit_type="11"
)

# 신용주문 (범용)
result = agent.account_api.order_credit("005930", 10, 70000, "00")
```

### 주문 정정/취소

```python
# 정정/취소
result = agent.account_api.order_rvsecncl(
    org_order_no="0001234567", qty=10, price=72000,
    order_type="00", cncl_type="정정"  # 또는 "취소"
)

# 정정/취소 가능 주문 조회
orders = agent.account_api.inquire_psbl_rvsecncl()
```

### 예약 주문

```python
# 예약주문 등록
result = agent.account_api.order_resv("005930", 10, 70000, "00")

# 예약주문 정정/취소
result = agent.account_api.order_resv_rvsecncl(seq=1, qty=10, price=72000, order_type="00")

# 예약주문 내역 조회
orders = agent.account_api.order_resv_ccnl()
```

## 체결/손익 조회

```python
# 일별 주문체결 조회 (페이지네이션 자동)
trades = agent.account_api.inquire_daily_ccld(
    start_date="20260101", end_date="20260331",
    pagination=True,    # 자동 페이지네이션
    ccld_dvsn="01",     # 체결건만
)

# 기간별 실현손익 (종목별)
profit = agent.account_api.inquire_period_trade_profit(
    start_date="20260101", end_date="20260331"
)
# Dict 반환 버전
profit = agent.account_api.get_period_trade_profit("20260101", "20260331")

# 기간별 손익 일별합산
daily = agent.account_api.inquire_period_profit(
    start_date="20260101", end_date="20260331"
)
# Dict 반환 버전
daily = agent.account_api.get_period_profit("20260101", "20260331")

# 기간별 권리현황
rights = agent.account_api.inquire_period_rights("20260101", "20260331")
```

## API 메서드 요약

### 잔고/자산

| 메서드 | 설명 |
|:---|:---|
| `get_account_balance()` | 계좌 잔고 |
| `get_cash_available(code)` | 종목별 매수가능금액 |
| `get_total_asset()` | 총자산 |
| `get_account_order_quantity(code)` | 주문가능수량 |
| `get_possible_order_amount()` | 주문가능금액 |
| `inquire_balance_rlz_pl()` | 실현손익 |
| `inquire_psbl_sell(pdno)` | 매도가능수량 |
| `inquire_intgr_margin()` | 통합증거금 |
| `inquire_psbl_order(price)` | 매수가능 |
| `inquire_credit_psamount(pdno)` | 신용매수가능 |

### 주문

| 메서드 | 설명 |
|:---|:---|
| `order_cash(pdno, qty, price, buy_sell)` | 현금 주문 |
| `order_cash_sor(pdno, qty, buy_sell)` | SOR 주문 |
| `order_credit_buy(pdno, qty, price)` | 신용 매수 |
| `order_credit_sell(pdno, qty, price)` | 신용 매도 |
| `order_rvsecncl(org_order_no, ...)` | 정정/취소 |
| `inquire_psbl_rvsecncl()` | 정정/취소 가능 |
| `order_resv(code, qty, price)` | 예약주문 |

### 체결/손익

| 메서드 | 설명 |
|:---|:---|
| `inquire_daily_ccld(...)` | 일별 주문체결 |
| `inquire_period_trade_profit(...)` | 기간별 실현손익 |
| `get_period_trade_profit(...)` | 기간별 실현손익 (Dict) |
| `inquire_period_profit(...)` | 기간별 손익 일별합산 |
| `get_period_profit(...)` | 기간별 손익 (Dict) |
| `inquire_period_rights(...)` | 기간별 권리현황 |
