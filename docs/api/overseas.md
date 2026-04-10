# 해외 주식 API

해외 주식 기능은 `agent.overseas` 네임스페이스를 통해 접근합니다.

## 지원 거래소

| 코드 | 거래소 | 국가 |
|:---|:---|:---|
| `NAS` | NASDAQ | 미국 |
| `NYS` | NYSE | 미국 |
| `AMS` | AMEX | 미국 |
| `TSE` | 도쿄증권거래소 | 일본 |
| `SHS` | 상해증권거래소 | 중국 |
| `SZS` | 심천증권거래소 | 중국 |
| `HKS` | 홍콩증권거래소 | 홍콩 |
| `HSX` | 호치민증권거래소 | 베트남 |
| `HNX` | 하노이증권거래소 | 베트남 |

## 시세 조회

```python
# 현재가
apple = agent.overseas.get_price(excd="NAS", symb="AAPL")
print(f"AAPL 현재가: ${apple['output']['last']}")

# 일봉
tesla_daily = agent.overseas.get_daily_price(excd="NAS", symb="TSLA")

# 분봉
tesla_minute = agent.overseas.get_minute_price(excd="NYS", symb="TSLA", interval=5)
```

## 주문

```python
# 매수
result = agent.overseas.buy_order(excd="NAS", symb="AAPL", qty="10", price="150.00")

# 매도
result = agent.overseas.sell_order(excd="NYS", symb="MSFT", qty="20", price="350.00")

# 정정
agent.overseas.modify_order(excd="NAS", order_no="...", qty="15", price="155.00")

# 취소
agent.overseas.cancel_order(excd="NAS", order_no="...")
```

## 잔고 조회

```python
balance = agent.overseas.get_balance()
```

## CLI

```bash
kis overseas NAS AAPL               # AAPL 시세
kis overseas NAS AAPL --detail      # PER/PBR/시총 포함
```

## API 메서드 요약

| 메서드 | 설명 |
|:---|:---|
| `overseas.get_price()` | 현재가 조회 |
| `overseas.get_daily_price()` | 일봉 조회 |
| `overseas.get_minute_price()` | 분봉 조회 |
| `overseas.get_balance()` | 해외주식 잔고 |
| `overseas.buy_order()` | 매수 주문 |
| `overseas.sell_order()` | 매도 주문 |
| `overseas.modify_order()` | 주문 정정 |
| `overseas.cancel_order()` | 주문 취소 |
