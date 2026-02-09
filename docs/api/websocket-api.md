# PyKIS 웹소켓 API 문서

##  API 개요
PyKIS 웹소켓 모듈의 공개 API 인터페이스를 정의합니다.

**테스트 커버리지:** 64%  
**최신 업데이트:** 2025-08-22

## 🏗️ 클래스 참조

### WSAgent

다중 구독을 관리하는 핵심 웹소켓 에이전트입니다.

#### 초기화
```python
WSAgent(
    approval_key: str,
    url: str = 'ws://ops.koreainvestment.com:21000',
    ping_interval: int = 30,
    ping_timeout: int = 30,
    auto_reconnect: bool = True
)
```

**매개변수:**
- `approval_key`: 웹소켓 승인키 (필수)
- `url`: 웹소켓 서버 URL (기본값: `ws://ops.koreainvestment.com:21000`)
- `ping_interval`: ping 전송 간격 (초, 기본값: 30)
- `ping_timeout`: ping 응답 대기 시간 (초, 기본값: 30)
- `auto_reconnect`: 자동 재연결 여부 (기본값: True)

**사용 예시:**
```python
from pykis import Agent

# Agent를 통한 간편한 접근 (추천)
agent = Agent(env_path=".env")
ws_client = agent.websocket(
    stock_codes=["005930", "035420"],
    enable_index=True,
    enable_program_trading=True
)

# 직접 생성
from pykis.websocket.ws_agent import WSAgent
ws_agent = WSAgent(approval_key="your_approval_key")
```

#### 메서드

##### subscribe()
```python
subscribe(
    sub_type: SubscriptionType,
    key: str,
    handler: Optional[Callable] = None,
    **metadata
) -> str
```

새로운 구독을 추가합니다.

**매개변수:**
- `sub_type`: 구독 타입 (SubscriptionType 열거형)
- `key`: 종목코드 또는 지수코드
- `handler`: 개별 핸들러 함수 (선택사항)
- `**metadata`: 추가 메타데이터

**반환값:** 구독 ID (문자열)

**예제:**
```python
# 삼성전자 체결 데이터 구독
sub_id = agent.subscribe(
    SubscriptionType.STOCK_TRADE, 
    "005930",
    handler=my_handler,
    company="삼성전자"
)
```

##### unsubscribe()
```python
unsubscribe(sub_id: str) -> None
```

기존 구독을 해제합니다.

**매개변수:**
- `sub_id`: 구독 ID

**예제:**
```python
agent.unsubscribe("H0STCNT0_005930")
```

##### register_handler()
```python
register_handler(
    sub_type: SubscriptionType,
    handler: Callable
) -> None
```

구독 타입별 공통 핸들러를 등록합니다.

**매개변수:**
- `sub_type`: 구독 타입
- `handler`: 핸들러 함수 `(data, metadata) -> None`

**예제:**
```python
def handle_all_trades(data, metadata):
    print(f"체결: {data}")

agent.register_handler(
    SubscriptionType.STOCK_TRADE,
    handle_all_trades
)
```

##### connect()
```python
async connect() -> None
```

웹소켓 서버에 연결하고 메시지 수신을 시작합니다.

**예제:**
```python
await agent.connect()
```

##### disconnect()
```python
async disconnect() -> None
```

웹소켓 연결을 종료합니다.

##### get_stats()
```python
get_stats() -> Dict[str, Any]
```

통계 정보를 반환합니다.

**반환값:**
```python
{
    'messages_received': int,
    'messages_processed': int,
    'errors': int,
    'reconnects': int,
    'last_message_time': Optional[datetime]
}
```

---

### EnhancedWebSocketClient

WSAgent를 기반으로 한 고수준 웹소켓 클라이언트입니다.

#### 초기화
```python
EnhancedWebSocketClient(
    client: KISClient,
    account_info: dict,
    stock_codes: List[str] = None,
    enable_index: bool = True,
    enable_program_trading: bool = False,
    enable_ask_bid: bool = False,
    enable_futures: bool = False,
    enable_options: bool = False
)
```

**매개변수:**
- `client`: KIS API 클라이언트 인스턴스
- `account_info`: 계좌 정보 딕셔너리
- `stock_codes`: 구독할 종목코드 리스트
- `enable_*`: 각종 데이터 타입 구독 활성화 플래그

#### 메서드

##### add_stock()
```python
add_stock(code: str) -> None
```

실시간으로 종목을 추가합니다.

**예제:**
```python
client.add_stock("000660")  # SK하이닉스 추가
```

##### remove_stock()
```python
remove_stock(code: str) -> None
```

종목을 제거합니다.

##### get_current_price()
```python
get_current_price(code: str) -> Optional[float]
```

종목의 현재가를 조회합니다.

##### get_market_summary()
```python
get_market_summary() -> Dict[str, Any]
```

시장 요약 정보를 반환합니다.

**반환값:**
```python
{
    'stocks': {
        '005930': {
            'name': '삼성전자',
            'price': 75000.0,
            'change_rate': -1.23,
            'volume': 1000000,
            'strength': 102.5
        }
    },
    'indices': {
        'KOSPI': {
            'value': 2650.5,
            'change_rate': 0.45
        }
    },
    'timestamp': datetime(2024, 8, 22, 10, 30, 0)
}
```

##### register_callback()
```python
register_callback(event_type: str, callback: Callable) -> None
```

이벤트 콜백을 등록합니다.

**이벤트 타입:**
- `'on_trade'`: 체결 데이터 수신
- `'on_ask_bid'`: 호가 데이터 수신
- `'on_index'`: 지수 데이터 수신
- `'on_program'`: 프로그램매매 데이터 수신

**예제:**
```python
def on_trade_event(data):
    print(f"체결: {data['name']} {data['price']}")

client.register_callback('on_trade', on_trade_event)
```

---

### SubscriptionType

구독 가능한 데이터 타입을 정의하는 열거형입니다.

```python
class SubscriptionType(Enum):
    STOCK_TRADE = "H0STCNT0"        # 국내주식 체결
    STOCK_ASK_BID = "H0STASP0"      # 국내주식 호가
    STOCK_NOTICE = "H0STCNI0"       # 국내주식 체결통보
    STOCK_NOTICE_AH = "H0STCNI9"    # 국내주식 시간외체결통보
    INDEX = "H0IF1000"              # 지수
    PROGRAM_TRADE = "H0GSCNT0"      # 프로그램매매
    FUTURES_TRADE = "H0CFCNT0"      # 선물 체결
    FUTURES_ASK_BID = "H0CFASP0"    # 선물 호가
    OPTION_TRADE = "H0OPCNT0"       # 옵션 체결
    OPTION_ASK_BID = "H0OPASP0"     # 옵션 호가
    OVERSEAS_STOCK = "HDFSCNT0"     # 해외주식 체결
    OVERSEAS_FUTURES = "HDFFF020"   # 해외선물 체결
```

##  데이터 구조

### 주식 체결 데이터
```python
{
    'code': '005930',
    'name': '삼성전자',
    'time': '093000',
    'price': 75000.0,
    'change': -1000.0,
    'change_rate': -1.32,
    'volume': 100,
    'amount': 7500000.0,
    'strength': 102.5,
    'timestamp': datetime(2024, 8, 22, 9, 30, 0)
}
```

### 호가 데이터
```python
{
    'code': '005930',
    'name': '삼성전자',
    'time': datetime(2024, 8, 22, 9, 30, 0),
    'sell_prices': [75100, 75200, 75300, ...],  # 매도호가 1~10
    'buy_prices': [75000, 74900, 74800, ...],   # 매수호가 1~10
    'sell_qty': [100, 200, 150, ...],           # 매도호가잔량
    'buy_qty': [50, 300, 100, ...]              # 매수호가잔량
}
```

### 지수 데이터
```python
{
    'code': '0001',
    'name': 'KOSPI',
    'value': 2650.5,
    'change': 12.3,
    'change_rate': 0.47,
    'timestamp': datetime(2024, 8, 22, 9, 30, 0)
}
```

### 프로그램매매 데이터
```python
{
    'code': '005930',
    'name': '삼성전자',
    'time': '093000',
    'sell_volume': 1000,
    'sell_amount': 75000000.0,
    'buy_volume': 1200,
    'buy_amount': 90000000.0,
    'net_volume': 200,
    'net_amount': 15000000.0,
    'timestamp': datetime(2024, 8, 22, 9, 30, 0)
}
```

##  사용 예제

### 기본 사용법
```python
import asyncio
from pykis.core.client import KISClient
from pykis.websocket import WSAgent, SubscriptionType

async def main():
    # 클라이언트 초기화
    client = KISClient(
        app_key="your_app_key",
        app_secret="your_app_secret",
        account_number="your_account"
    )
    
    # WSAgent 생성
    approval_key = client.get_ws_approval_key()
    agent = WSAgent(approval_key)
    
    # 핸들러 정의
    def handle_trade(data, metadata):
        if isinstance(data, list) and len(data) >= 3:
            code, time, price = data[0], data[1], float(data[2])
            print(f"체결: {code} {price:,}원")
    
    # 구독 추가
    agent.subscribe(
        SubscriptionType.STOCK_TRADE,
        "005930",
        handler=handle_trade
    )
    
    # 연결 시작
    await agent.connect()

if __name__ == "__main__":
    asyncio.run(main())
```

### 고급 사용법 (EnhancedWebSocketClient)
```python
import asyncio
from pykis.websocket import EnhancedWebSocketClient

async def main():
    # 클라이언트 생성
    client = EnhancedWebSocketClient(
        client=kis_client,
        account_info=account_info,
        stock_codes=["005930", "000660"],
        enable_index=True,
        enable_ask_bid=True
    )
    
    # 콜백 등록
    def on_trade(data):
        print(f"체결: {data['name']} {data['price']:,}원 ({data['change_rate']:+.2f}%)")
    
    def on_index(data):
        print(f"지수: {data['name']} {data['value']:,.2f} ({data['change_rate']:+.2f}%)")
    
    client.register_callback('on_trade', on_trade)
    client.register_callback('on_index', on_index)
    
    # 실행
    await client.start()

asyncio.run(main())
```

##  주의사항

1. **승인키 관리**: 승인키는 24시간 유효하며, 만료 시 재발급 필요
2. **연결 제한**: 동시 연결 수에 제한이 있을 수 있음
3. **메시지 처리**: 고빈도 메시지 처리 시 적절한 백프레셔 관리 필요
4. **에러 처리**: 네트워크 오류 및 인증 오류에 대한 적절한 처리 필요

##  설정 옵션

### 환경변수
```bash
KIS_APP_KEY=your_app_key
KIS_APP_SECRET=your_app_secret
KIS_ACCOUNT_NUMBER=your_account
```

### 로깅 설정
```python
import logging

# 웹소켓 모듈 전용 로거
ws_logger = logging.getLogger('pykis.websocket')
ws_logger.setLevel(logging.INFO)

# 핸들러 추가
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
ws_logger.addHandler(handler)
```

## 🐛 트러블슈팅

### 연결 실패
- 승인키 유효성 확인
- 네트워크 연결 상태 확인
- API 서버 상태 확인

### 메시지 수신 안됨
- 구독 요청 성공 여부 확인
- 시장 개장 시간 확인
- 종목코드 유효성 확인

### 성능 이슈
- 핸들러 처리 시간 최적화
- 불필요한 구독 제거
- 메모리 사용량 모니터링