# 선물/옵션 API

## 국내 선물옵션

`agent.futures` 네임스페이스를 통해 접근합니다. `Futures` Facade가 `FuturesPriceAPI`, `FuturesAccountAPI`, `FuturesOrderAPI`, `FuturesCodeGenerator`, `FuturesHistoricalAPI`에 위임합니다.

### 시세 조회

```python
# 현재가 (market: "F"=주간선물, "O"=옵션, "CM"=야간)
price = agent.futures.get_price("101S03")
price_night = agent.futures.get_price("101W09", market="CM")

# 호가
orderbook = agent.futures.get_orderbook("101S03")

# 일봉차트
chart = agent.futures.inquire_daily_fuopchartprice(
    "101S03", start_date="20260101", end_date="20260331", period="D"
)

# 분봉차트
minute = agent.futures.inquire_time_fuopchartprice("101S03", tick_range="1")

# 옵션 콜/풋 전광판
callput = agent.futures.display_board_callput(expiry="202603")

# 선물 전광판
board = agent.futures.display_board_futures()
```

### 종목코드 자동 생성

종목코드를 직접 입력하지 않아도 자동으로 현재 월물을 찾아줍니다:

```python
# 현재 근월물 시세 (futures_master 기반)
price = agent.futures.get_current_futures_price()
price = agent.futures.get_current_futures_price(market="CM")  # 야간

# 차근월물 시세
next_price = agent.futures.get_next_futures_price()

# 근월물 호가
orderbook = agent.futures.get_current_futures_orderbook()

# 근월물 차트
chart = agent.futures.get_current_futures_chart("20260101", "20260331")
```

### 옵션

```python
# 옵션 현재가 (종목코드 자동 생성)
call = agent.futures.get_option_price("CALL", 340.0)
put = agent.futures.get_option_price("PUT", 342.5, expiry_month=6)

# 편의 메서드
call = agent.futures.get_call_option_price(340.0)
put = agent.futures.get_put_option_price(340.0)

# 종목코드 생성기 직접 사용
from kis_agent.futures import FuturesCodeGenerator
code = FuturesCodeGenerator.generate_futures_code()       # 현재 월물
code = FuturesCodeGenerator.generate_option_code("CALL", 340.0)
atm = FuturesCodeGenerator.generate_atm_option_codes(340.25)  # ATM 옵션
```

### 계좌/잔고

```python
balance = agent.futures.inquire_balance()      # 잔고
deposit = agent.futures.inquire_deposit()      # 예수금
```

### 야간 선물옵션

```python
ngt_balance = agent.futures.inquire_ngt_balance()           # 야간 잔고
ngt_ccnl = agent.futures.inquire_ngt_ccnl()                 # 야간 체결내역
psbl = agent.futures.inquire_psbl_ngt_order("101W09")       # 야간 주문 가능 수량
```

### 주문

```python
# 직접 주문
result = agent.futures.order.order(
    code="101S03", order_type="02", qty="1", price="0"  # 시장가 매수
)

# 현재 월물 주문 (종목코드 자동)
result = agent.futures.order_current_futures("02", "1", "0")

# 옵션 주문 (종목코드 자동)
result = agent.futures.order_option("CALL", 340.0, "02", "1", "0")
```

**주문구분:** `01`=매도, `02`=매수  
**주문조건:** `0`=없음, `1`=IOC, `2`=FOK

### 과거 데이터 조회

월물 전환을 자동으로 처리하여 연속 분봉 데이터를 조회합니다:

```python
# 과거 분봉 (월물 자동 전환)
bars = agent.futures.get_historical_minute_bars(
    start_date="20250101", end_date="20250131",
    interval="1", max_bars=5000
)

# 특정 월물 분봉
bars = agent.futures.get_contract_minute_bars(
    code="1016C", start_date="20260101", end_date="20260131"
)
```

---

## 해외 선물옵션

`agent.overseas_futures` 네임스페이스를 통해 접근합니다.

**지원 거래소:** CME, EUREX, COMEX, NYMEX, ICE

### 시세 조회

```python
# 선물 현재가
price = agent.overseas_futures.get_price("CNHU24")

# 옵션 현재가 (그릭스 포함)
opt = agent.overseas_futures.get_option_price("...")

# 분봉
minute = agent.overseas_futures.get_minute_chart("CNHU24", "CME")

# 체결추이 (일간)
daily = agent.overseas_futures.get_daily_trend("CNHU24", "CME")

# 선물 호가
orderbook = agent.overseas_futures.get_futures_orderbook("CNHU24")

# 옵션 호가
opt_ob = agent.overseas_futures.get_option_orderbook("...")

# 상품 기본정보
info = agent.overseas_futures.get_futures_info(["CNHU24", "ESH5"])
opt_info = agent.overseas_futures.get_option_info(["..."])
```

### 계좌/잔고

```python
# 잔고 (fuop_dvsn: "00"=전체, "01"=선물, "02"=옵션)
balance = agent.overseas_futures.get_balance()

# 예수금
deposit = agent.overseas_futures.get_deposit(crcy_cd="TUS")

# 증거금 상세
margin = agent.overseas_futures.get_margin_detail()

# 주문가능 조회
amount = agent.overseas_futures.get_order_amount("CNHU24", "02", "100.00")

# 당일 주문내역
today = agent.overseas_futures.get_today_orders()

# 일별 주문내역
orders = agent.overseas_futures.get_daily_orders("20260101", "20260331")

# 일별 체결내역
exec = agent.overseas_futures.get_daily_executions("20260101", "20260331")

# 기간 손익
profit = agent.overseas_futures.get_period_profit("20260101", "20260331")

# 기간 거래내역
tx = agent.overseas_futures.get_period_transactions("20260101", "20260331")
```

### 주문

```python
# 매수
result = agent.overseas_futures.order.buy(code="CNHU24", qty="1", price="100.00")

# 매도
result = agent.overseas_futures.order.sell(code="CNHU24", qty="1", price="105.00")
```

## API 메서드 요약

### 국내 선물옵션 (agent.futures)

| 메서드 | 설명 |
|:---|:---|
| `get_price(code, market)` | 현재가 |
| `get_orderbook(code, market)` | 호가 |
| `inquire_daily_fuopchartprice(...)` | 일봉 |
| `inquire_time_fuopchartprice(...)` | 분봉 |
| `display_board_callput(expiry)` | 옵션 전광판 |
| `display_board_futures()` | 선물 전광판 |
| `get_current_futures_price(market)` | 근월물 시세 (자동) |
| `get_option_price(type, strike)` | 옵션 시세 (자동) |
| `inquire_balance()` | 잔고 |
| `inquire_deposit()` | 예수금 |
| `inquire_ngt_balance()` | 야간 잔고 |
| `order_current_futures(...)` | 근월물 주문 (자동) |
| `get_historical_minute_bars(...)` | 과거 분봉 (월물 자동전환) |

### 해외 선물옵션 (agent.overseas_futures)

| 메서드 | 설명 |
|:---|:---|
| `get_price(srs_cd)` | 선물 현재가 |
| `get_option_price(srs_cd)` | 옵션 현재가 |
| `get_futures_orderbook(srs_cd)` | 선물 호가 |
| `get_balance(fuop_dvsn)` | 잔고 |
| `get_deposit(crcy_cd)` | 예수금 |
| `get_period_profit(from_dt, to_dt)` | 기간 손익 |
