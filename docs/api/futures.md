# 선물/옵션 API

선물옵션 기능은 `agent.futures` 및 `agent.overseas_futures` 네임스페이스를 통해 접근합니다.

## 국내 선물

### 시세 조회

```python
price = agent.futures.get_price("101S03")
```

### 주문

```python
# 매수
result = agent.futures.buy_order(code="101S03", qty=1, price=350.00)

# 매도
result = agent.futures.sell_order(code="101S03", qty=1, price=355.00)
```

### 잔고 조회

```python
balance = agent.futures.get_balance()
```

## 해외 선물

```python
price = agent.overseas_futures.get_price(excd="CME", symb="ESH5")
```

## 야간 세션

v1.6.0부터 야간 세션 REST 엔드포인트에 `market` 파라미터(CM/EU)가 지원됩니다.
`futures_master` 기반으로 종목코드가 자동 해석됩니다.

## CLI

```bash
kis futures 101S03                  # 국내 선물 시세
kis futures CLM26 --overseas        # 해외 선물 시세
```

## API 메서드 요약

| 메서드 | 설명 |
|:---|:---|
| `futures.get_price()` | 국내 선물 시세 |
| `futures.get_balance()` | 선물 잔고 |
| `futures.buy_order()` | 선물 매수 |
| `futures.sell_order()` | 선물 매도 |
| `overseas_futures.get_price()` | 해외 선물 시세 |
