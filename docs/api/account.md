# 계좌 관리 API

## 잔고 조회

```python
balance = agent.get_account_balance()
print(f"보유 종목 수: {len(balance['output1'])}개")
```

## 주문 가능 금액

```python
buyable = agent.inquire_order_psbl("005930", "70000")
print(f"주문가능수량: {buyable['output']['max_buy_qty']}")
```

## 신용 주문 가능 조회

```python
credit = agent.inquire_credit_order_psbl("005930", "70000")
```

## 거래 내역

### Python API

```python
trades = agent.get_trades()
```

### CLI

```bash
kis trades                          # 당일 체결내역
kis trades --from 7d --pretty       # 최근 7일
kis trades --from 30d --sell        # 최근 30일 매도만
kis trades --from 3m --profit       # 기간별 실현손익
```

## API 메서드 요약

| 메서드 | 설명 |
|:---|:---|
| `get_account_balance()` | 계좌 잔고 |
| `inquire_order_psbl()` | 현금 주문 가능 수량 |
| `inquire_credit_order_psbl()` | 신용 주문 가능 수량 |
| `inquire_psbl_rvsecncl()` | 정정/취소 가능 조회 |
