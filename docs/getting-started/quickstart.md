# 빠른 시작

## Agent 초기화

모든 기능은 `Agent` 객체를 통해 접근합니다:

```python
from kis_agent import Agent
import os

agent = Agent(
    app_key=os.environ['KIS_APP_KEY'],
    app_secret=os.environ['KIS_APP_SECRET'],
    account_no=os.environ['KIS_ACCOUNT_NO'],
    account_code=os.environ.get('KIS_ACCOUNT_CODE', '01'),
)
```

## 주식 시세 조회

```python
# 현재가
price = agent.get_stock_price("005930")
print(f"삼성전자 현재가: {price['output']['stck_prpr']}원")

# 일봉 데이터
daily = agent.inquire_daily_itemchartprice(
    "005930",
    start_date="20250101",
    end_date="20251231"
)
```

## 계좌 조회

```python
# 잔고
balance = agent.get_account_balance()

# 주문 가능 수량
inquiry = agent.inquire_order_psbl("005930", "70000")
print(f"주문가능수량: {inquiry['output']['max_buy_qty']}")
```

## 주문 실행

```python
# 시장가 매수
result = agent.order_stock_cash("buy", "005930", "03", "1", "0")

# 지정가 매수
result = agent.order_stock_cash("buy", "005930", "00", "1", "70000")

# 주문 정정/취소
result = agent.order_rvsecncl(org_order_no, qty, price, order_type, cncl_type)
```

!!! danger "실전투자 주의"
    `is_real=True`로 설정된 경우 실제 돈이 투자됩니다. 모의투자에서 충분히 테스트하세요.

## 실시간 데이터

```python
import asyncio

ws_client = agent.websocket(
    stock_codes=["005930", "035420"],
    enable_index=True,
    enable_program_trading=True,
    enable_ask_bid=True
)

asyncio.run(ws_client.start())
```

## 다음 단계

더 자세한 내용은 각 섹션을 참고하세요:

- [CLI 사용법](../cli/usage.md) — 터미널에서 시세 조회, 잔고 확인
- [국내 주식 API](../api/stock.md) — 시세, 차트, 분석 기능
- [해외 주식 API](../api/overseas.md) — 미국, 일본 등 9개 거래소
- [선물/옵션 API](../api/futures.md) — 국내/해외 선물옵션
- [실시간 WebSocket](../api/websocket.md) — 실시간 체결, 호가, 지수
