# 실시간 WebSocket API

WebSocket을 통해 실시간 체결, 호가, 지수 데이터를 수신합니다.

## 빠른 시작

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

## 구독 유형

| 유형 | 설명 |
|:---|:---|
| `STOCK_TRADE` | 주식 체결 데이터 |
| `INDEX` | 지수 데이터 (KOSPI, KOSDAQ 등) |
| `PROGRAM_TRADE` | 프로그램 매매 |
| `ASK_BID` | 호가 데이터 |

## WSAgent 직접 사용

더 세밀한 제어가 필요한 경우 `WSAgent`를 직접 사용합니다:

```python
from kis_agent.websocket.ws_agent import WSAgent, SubscriptionType

async def advanced_websocket():
    approval_key = client.get_ws_approval_key()
    ws_agent = WSAgent(approval_key)

    # 핸들러 함수
    def handle_trade(data, metadata):
        if isinstance(data, list) and len(data) >= 3:
            code, time, price = data[0], data[1], float(data[2])
            print(f"체결: {code} {price:,}원 @ {time}")

    # 구독 추가
    ws_agent.subscribe(SubscriptionType.STOCK_TRADE, "005930", handle_trade)
    ws_agent.subscribe(SubscriptionType.INDEX, "0001")           # KOSPI
    ws_agent.subscribe(SubscriptionType.PROGRAM_TRADE, "005930")

    await ws_agent.connect()

asyncio.run(advanced_websocket())
```

## WSAgent 생성자 옵션

| 파라미터 | 기본값 | 설명 |
|:---|:---|:---|
| `approval_key` | (필수) | 웹소켓 승인키 |
| `url` | `ws://ops.koreainvestment.com:21000` | 서버 URL |
| `ping_interval` | `30` | ping 전송 간격 (초) |
| `ping_timeout` | `30` | ping 응답 대기 시간 (초) |
| `auto_reconnect` | `True` | 자동 재연결 여부 |

## 야간 선물 실시간 데이터

v1.6.0부터 KRX 야간 선물/옵션 실시간 WebSocket이 지원됩니다.

## 안정성

- 무한 재연결 루프 방지 — 백오프 및 실패 횟수 제한 적용
- ping/pong 기반 연결 상태 모니터링
- 자동 재구독 (재연결 시)
