# 실시간 WebSocket API

WebSocket을 통해 실시간 체결, 호가, 지수, 선물옵션 데이터를 수신합니다.

## 빠른 시작

```python
import asyncio

ws_client = agent.websocket(
    codes=["005930", "035420"],
    include_orderbook=True,
    on_trade=lambda data: print(f"체결: {data}"),
    on_orderbook=lambda data: print(f"호가: {data}"),
)

asyncio.run(ws_client.start())
```

## SubscriptionType

모든 구독 타입은 `SubscriptionType` enum으로 정의됩니다:

### 국내주식 (KRX)

| 타입 | 코드 | 설명 |
|:---|:---|:---|
| `STOCK_TRADE` | `H0STCNT0` | 실시간 체결가 |
| `STOCK_ASK_BID` | `H0STASP0` | 실시간 호가 |
| `STOCK_EXPECTED` | `H0UNANC0` | 예상체결 |
| `STOCK_NOTICE` | `H0STCNI0` | 체결통보 |
| `STOCK_NOTICE_AH` | `H0STCNI9` | 시간외 체결통보 |

### 국내주식 (NXT)

| 타입 | 코드 | 설명 |
|:---|:---|:---|
| `STOCK_TRADE_NXT` | `H0NXCNT0` | 실시간 체결가 (NXT) |
| `STOCK_ASK_BID_NXT` | `H0NXASP0` | 실시간 호가 (NXT) |
| `STOCK_EXPECTED_NXT` | `H0NXANC0` | 예상체결 (NXT) |
| `PROGRAM_TRADE_NXT` | `H0NXPGM0` | 프로그램매매 (NXT) |
| `MARKET_OPERATION_NXT` | `H0NXMKO0` | 장운영정보 (NXT) |
| `MEMBER_TRADE_NXT` | `H0NXMBC0` | 회원사 (NXT) |

### 지수

| 타입 | 코드 | 설명 |
|:---|:---|:---|
| `INDEX` | `H0IF1000` | 지수 실시간 |
| `INDEX_EXPECTED` | `H0UPANC0` | 지수 예상체결 |

### 프로그램매매/회원사

| 타입 | 코드 | 설명 |
|:---|:---|:---|
| `PROGRAM_TRADE` | `H0STPGM0` | 프로그램매매 (KRX) |
| `MEMBER_TRADE` | `H0MBCNT0` | 회원사별 매매동향 |

### 선물/옵션 (주간)

| 타입 | 코드 | 설명 |
|:---|:---|:---|
| `FUTURES_TRADE` | `H0CFCNT0` | 선물 체결 |
| `FUTURES_ASK_BID` | `H0CFASP0` | 선물 호가 |
| `OPTION_TRADE` | `H0OPCNT0` | 옵션 체결 |
| `OPTION_ASK_BID` | `H0OPASP0` | 옵션 호가 |

### 야간 선물/옵션

| 타입 | 코드 | 설명 |
|:---|:---|:---|
| `NIGHT_FUTURES_TRADE` | `H0MFCNT0` | 야간선물 체결 |
| `NIGHT_FUTURES_ASK_BID` | `H0MFASP0` | 야간선물 호가 |
| `NIGHT_OPTION_TRADE` | `H0EUCNT0` | 야간옵션 체결 |
| `NIGHT_OPTION_ASK_BID` | `H0EUASP0` | 야간옵션 호가 |

### 해외

| 타입 | 코드 | 설명 |
|:---|:---|:---|
| `OVERSEAS_STOCK` | `HDFSCNT0` | 해외주식 체결 |
| `OVERSEAS_FUTURES` | `HDFFF020` | 해외선물 체결 |

## WSAgent 직접 사용

세밀한 제어가 필요한 경우:

```python
from kis_agent.websocket import WSAgent, SubscriptionType

async def advanced():
    approval_key = client.get_ws_approval_key()
    ws = WSAgent(approval_key)

    def handle_trade(data, metadata):
        code, time, price = data[0], data[1], float(data[2])
        print(f"체결: {code} {price:,}원 @ {time}")

    # 구독 추가
    ws.subscribe(SubscriptionType.STOCK_TRADE, "005930")
    ws.subscribe(SubscriptionType.INDEX, "0001")
    ws.subscribe(SubscriptionType.FUTURES_TRADE, "101S03")
    ws.subscribe(SubscriptionType.NIGHT_FUTURES_TRADE, "101W09")

    # 핸들러 등록
    ws.register_handler(SubscriptionType.STOCK_TRADE, handle_trade)
    ws.set_default_handler(lambda d, m: print(d))

    await ws.connect()

asyncio.run(advanced())
```

### 비동기 구독

```python
# 연결 이후 동적 구독/해제
sub_id = await ws.subscribe_async(SubscriptionType.STOCK_TRADE, "000660")
ws.unsubscribe(sub_id)
```

### 상태 조회

```python
ws.is_connected()              # 연결 여부
ws.get_active_subscriptions()  # 활성 구독 목록
ws.get_stats()                 # 수신 통계
```

## WSAgentWithStore

데이터 저장소가 내장된 버전으로, 구독 데이터를 자동으로 저장합니다:

```python
from kis_agent.websocket import WSAgentWithStore

ws = WSAgentWithStore(approval_key)
ws.subscribe_stocks(["005930", "000660"])
ws.subscribe_indices(["0001", "1001"])
ws.subscribe_futures(["101S03"])

await ws.connect()

# 저장된 데이터 접근
store = ws.get_store()
```

## WSAgent 생성자 옵션

| 파라미터 | 기본값 | 설명 |
|:---|:---|:---|
| `approval_key` | (필수) | 웹소켓 승인키 |
| `url` | `ws://ops.koreainvestment.com:21000` | 서버 URL |
| `ping_interval` | `30` | ping 전송 간격 (초) |
| `ping_timeout` | `30` | ping 응답 대기 시간 (초) |
| `auto_reconnect` | `True` | 자동 재연결 |
| `max_reconnect_attempts` | `10` | 최대 재연결 시도 횟수 |

## 안정성

- 무한 재연결 루프 방지 — 백오프 + 실패 횟수 제한 (기본 10회)
- ping/pong 기반 연결 상태 모니터링
- 자동 재구독 (재연결 시 기존 구독 복원)
- AES 복호화 자동 처리
