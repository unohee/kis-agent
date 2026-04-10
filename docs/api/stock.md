# 국내 주식 API

## 시세 조회

### 현재가

```python
price = agent.get_stock_price("005930")
print(f"현재가: {price['output']['stck_prpr']}원")
```

### 일봉 데이터

```python
daily = agent.inquire_daily_itemchartprice(
    "005930",
    start_date="20250101",
    end_date="20251231"
)
```

### 장기 데이터 (100건 제한 자동 우회)

API의 100건 제한을 자동으로 우회하여 전체 기간 데이터를 수집합니다:

```python
result = agent.get_daily_price_all(
    code="005930",
    start_date="20200102",
    end_date="20201230",
    period="D",
    org_adj_prc="1"
)
print(f"총 {len(result['output2'])}건 수집")   # 248건
print(f"API 호출: {result['_pagination_info']['total_calls']}회")
```

### 분봉 데이터

```python
minute = agent.get_minute_price("005930")
```

### 호가 조회

```python
orderbook = agent.get_orderbook("005930")
```

## 주문

### 현금 매수/매도

```python
# 시장가 매수
result = agent.order_stock_cash("buy", "005930", "03", "1", "0")

# 지정가 매수
result = agent.order_stock_cash("buy", "005930", "00", "1", "70000")

# 지정가 매도
result = agent.order_stock_cash("sell", "005930", "00", "5", "78000")
```

**주문 유형 코드:**

| 코드 | 설명 |
|:---|:---|
| `00` | 지정가 |
| `03` | 시장가 |
| `05` | 조건부지정가 |
| `06` | 최유리지정가 |
| `07` | 최우선지정가 |

### 주문 정정/취소

```python
result = agent.order_rvsecncl(org_order_no, qty, price, order_type, cncl_type)
```

### 주문 가능 수량 조회

```python
inquiry = agent.inquire_order_psbl("005930", "70000")
print(f"주문가능수량: {inquiry['output']['max_buy_qty']}")
```

## 분석

### 투자자별 매매동향

```python
investor = agent.get_stock_investor("005930")
```

### 프로그램 매매

```python
program = agent.get_program_trade_by_stock("005930", "20250101")
```

### 증권사별 매매동향

```python
member = agent.get_stock_member("005930")
```

### 지지/저항선 계산

```python
sr = agent.calculate_support_resistance("005930")
```

## API 메서드 요약

| 메서드 | 설명 |
|:---|:---|
| `get_stock_price()` | 현재가 조회 |
| `get_daily_price()` | 일봉 조회 |
| `get_daily_price_all()` | 장기 일봉 (페이지네이션 자동) |
| `get_minute_price()` | 분봉 조회 |
| `get_orderbook()` | 호가 조회 |
| `order_stock_cash()` | 현금 매수/매도 |
| `order_stock_credit()` | 신용 매수/매도 |
| `order_rvsecncl()` | 주문 정정/취소 |
| `inquire_order_psbl()` | 주문 가능 수량 |
| `get_stock_investor()` | 투자자별 매매동향 |
| `get_stock_member()` | 증권사별 매매동향 |
| `get_program_trade_by_stock()` | 프로그램 매매 |
| `calculate_support_resistance()` | 지지/저항선 |
