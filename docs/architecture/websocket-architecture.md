# PyKIS 웹소켓 아키텍처 문서

##  문서 개요
- **작성일**: 2024-08-22
- **버전**: v1.0
- **작성자**: Heewon Oh
- **대상**: PyKIS 웹소켓 다중 구독 시스템

##  아키텍처 개요

PyKIS 웹소켓 모듈은 한국투자증권 OpenAPI의 실시간 데이터를 효율적으로 수신하고 관리하기 위한 다중 구독 시스템입니다.

### 핵심 설계 원칙
1. **모듈성**: 구독 타입별 독립적 처리
2. **확장성**: 새로운 구독 타입 쉽게 추가 가능
3. **안정성**: 자동 재연결 및 오류 복구
4. **유연성**: 다양한 핸들러 패턴 지원

## 🏗️ 시스템 컨텍스트 (C4 - Level 1)

```
┌─────────────────────────────────────────────────────┐
│                  PyKIS System                       │
│                                                     │
│  ┌──────────────┐    ┌──────────────────────────┐  │
│  │   REST API   │    │    WebSocket Module       │  │
│  │   Module     │    │   (Real-time Data)        │  │
│  └──────────────┘    └──────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                           │
                           │ WebSocket Protocol
                           │
┌─────────────────────────────────────────────────────┐
│           한국투자증권 OpenAPI Server                │
│                                                     │
│  • 실시간 주식 체결 데이터                          │
│  • 실시간 지수 데이터                               │
│  • 실시간 호가 데이터                               │
│  • 프로그램매매 데이터                              │
└─────────────────────────────────────────────────────┘
```

### 외부 시스템 의존성
- **한국투자증권 WebSocket Server**: `ws://ops.koreainvestment.com:21000`
- **인증 시스템**: REST API를 통한 approval_key 발급
- **AES 암호화**: 체결통보 메시지 복호화

##  컨테이너 아키텍처 (C4 - Level 2)

```
┌─────────────────────────────────────────────────────┐
│                PyKIS WebSocket Module                │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │   WSAgent    │  │ Enhanced     │  │  Legacy     ││
│  │   (Core)     │  │ Client       │  │  Client     ││
│  └──────────────┘  └──────────────┘  └─────────────┘│
│          │                  │                        │
│          │ uses             │ uses                   │
│          │                  │                        │
│  ┌──────────────────────────────────────────────────┐│
│  │           Subscription Management                 ││
│  │  • SubscriptionType (Enum)                       ││
│  │  • Subscription (DataClass)                      ││
│  └──────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
                           │
                           │ WebSocket Connection
                           │
┌─────────────────────────────────────────────────────┐
│                External Services                     │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                │
│  │   KIS API    │  │   Logging    │                │
│  │   Server     │  │   System     │                │
│  └──────────────┘  └──────────────┘                │
└─────────────────────────────────────────────────────┘
```

##  컴포넌트 아키텍처 (C4 - Level 3)

### WSAgent 컴포넌트

```
┌─────────────────────────────────────────────────────┐
│                    WSAgent                           │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │ Connection   │  │ Subscription │  │  Message    ││
│  │ Manager      │  │ Manager      │  │  Handler    ││
│  │              │  │              │  │             ││
│  │ • connect()  │  │ • subscribe()│  │ • parse()   ││
│  │ • reconnect()│  │ • unsubscr() │  │ • decrypt() ││
│  │ • ping/pong  │  │ • handlers   │  │ • route()   ││
│  └──────────────┘  └──────────────┘  └─────────────┘│
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                │
│  │   Statistics │  │   AES Crypto │                │
│  │   Tracker    │  │   Manager    │                │
│  │              │  │              │                │
│  │ • counters   │  │ • decrypt()  │                │
│  │ • timestamps │  │ • key store  │                │
│  └──────────────┘  └──────────────┘                │
└─────────────────────────────────────────────────────┘
```

### Enhanced Client 컴포넌트

```
┌─────────────────────────────────────────────────────┐
│              EnhancedWebSocketClient                 │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │  Market Data │  │   Callback   │  │   Stock     ││
│  │   Manager    │  │   System     │  │  Manager    ││
│  │              │  │              │  │             ││
│  │ • stocks{}   │  │ • on_trade   │  │ • add()     ││
│  │ • indices{}  │  │ • on_index   │  │ • remove()  ││
│  │ • ask_bid{}  │  │ • on_ask_bid │  │ • info{}    ││
│  └──────────────┘  └──────────────┘  └─────────────┘│
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                │
│  │    Logger    │  │   API Client │                │
│  │   Manager    │  │   Interface  │                │
│  │              │  │              │                │
│  │ • data logs  │  │ • stock_api  │                │
│  │ • JSONL      │  │ • account    │                │
│  └──────────────┘  └──────────────┘                │
└─────────────────────────────────────────────────────┘
```

##  데이터 아키텍처

### 구독 타입 정의

```python
class SubscriptionType(Enum):
    STOCK_TRADE = "H0STCNT0"        # 국내주식 체결
    STOCK_ASK_BID = "H0STASP0"      # 국내주식 호가
    INDEX = "H0IF1000"              # 지수
    PROGRAM_TRADE = "H0GSCNT0"      # 프로그램매매
    FUTURES_TRADE = "H0CFCNT0"      # 선물 체결
    OVERSEAS_STOCK = "HDFSCNT0"     # 해외주식 체결
```

### 데이터 흐름도

```
WebSocket Server → WSAgent → Message Parser → Handler Router
                                                    ↓
Subscription Handler ← Callback System ← Market Data Store
       ↓                      ↓                    ↓
   User Code            UI Display          Log Files
```

### 메시지 처리 파이프라인

```
Raw Message → Type Detection → AES Decryption (if needed) → 
Data Parsing → Subscription Matching → Handler Execution → 
Data Storage → Callback Notification
```

## 🔐 보안 아키텍처

### 인증 흐름
1. **Approval Key 발급**: REST API 호출
2. **WebSocket 연결**: approval_key 헤더 포함
3. **구독 요청**: 인증된 연결에서 구독 메시지 전송

### AES 암호화 처리
- **체결통보 메시지**: AES256-CBC 암호화
- **키 관리**: 웹소켓 연결 시 동적 키 수신
- **복호화**: Base64 디코딩 후 AES 복호화

##  성능 및 확장성

### 성능 특성
- **동시 구독**: 무제한 (메모리 허용 범위)
- **메시지 처리**: 비동기 파이프라인
- **재연결**: 지수 백오프 전략
- **메모리 사용**: 구독당 ~1KB

### 확장성 패턴
- **수평적 확장**: 다중 WSAgent 인스턴스
- **수직적 확장**: 핸들러 병렬 처리
- **타입별 분산**: 구독 타입별 전용 에이전트

##  배포 아키텍처

### 개발 환경
```python
# 단일 프로세스 개발
client = EnhancedWebSocketClient(...)
await client.start()
```

### 프로덕션 환경
```python
# 멀티 프로세스 배포
import asyncio
import multiprocessing

async def run_agent(stocks):
    agent = WSAgent(...)
    for stock in stocks:
        agent.subscribe(SubscriptionType.STOCK_TRADE, stock)
    await agent.connect()

# 프로세스풀로 부하 분산
if __name__ == "__main__":
    stock_groups = [stocks[i::4] for i in range(4)]  # 4개 프로세스
    processes = []
    for group in stock_groups:
        p = multiprocessing.Process(target=asyncio.run, args=(run_agent(group),))
        processes.append(p)
        p.start()
```

##  모니터링 및 관찰성

### 메트릭스
- `messages_received`: 수신 메시지 수
- `messages_processed`: 처리된 메시지 수
- `errors`: 에러 발생 횟수
- `reconnects`: 재연결 횟수
- `active_subscriptions`: 활성 구독 수

### 로깅 전략
```python
# 구조화된 로깅
{
    "timestamp": "2024-08-22T10:30:00Z",
    "level": "INFO",
    "component": "WSAgent",
    "event": "subscription_added",
    "subscription_id": "H0STCNT0_005930",
    "metadata": {"stock": "005930", "name": "삼성전자"}
}
```

### 헬스체크
- **연결 상태**: `is_connected()`
- **마지막 메시지 시간**: `last_message_time`
- **활성 구독 목록**: `get_active_subscriptions()`

##  아키텍처 결정 기록 (ADRs)

### ADR-001: WSAgent 중심 설계
**결정**: 단일 WSAgent가 다중 구독을 관리하는 중앙집중형 아키텍처 채택

**근거**:
- 연결 관리의 단순화
- 메시지 라우팅의 효율성
- 리소스 사용량 최적화

**대안**: 구독 타입별 독립 에이전트
**트레이드오프**: 단일 장애점 vs 관리 복잡성

### ADR-002: 콜백 기반 핸들러 시스템
**결정**: 개별/타입별/기본 핸들러의 3단계 콜백 시스템 구현

**근거**:
- 유연한 이벤트 처리
- 컴포넌트 간 느슨한 결합
- 확장 가능한 구조

**대안**: 옵저버 패턴, 이벤트 버스
**트레이드오프**: 단순성 vs 기능성

### ADR-003: 비동기 I/O 기반 구현
**결정**: asyncio 기반 완전 비동기 구현

**근거**:
- 높은 동시성
- 적은 리소스 사용
- Python 표준 라이브러리 활용

**대안**: 멀티스레딩, 멀티프로세싱
**트레이드오프**: 학습 곡선 vs 성능

##  향후 개선 계획

### 단기 (1-3개월)
- [ ] 메트릭스 수집 자동화
- [ ] 구독 상태 Dashboard 구축
- [ ] 에러 복구 전략 고도화

### 중기 (3-6개월)
- [ ] 분산 배포 지원
- [ ] 백프레셰 방지 시스템
- [ ] 실시간 설정 변경 지원

### 장기 (6개월 이상)
- [ ] 머신러닝 기반 이상 탐지
- [ ] 다중 거래소 지원 확장
- [ ] 클라우드 네이티브 배포

##  참고 자료

- [한국투자증권 OpenAPI 문서](https://apiportal.koreainvestment.com/)
- [WebSocket RFC 6455](https://tools.ietf.org/html/rfc6455)
- [Python asyncio 문서](https://docs.python.org/3/library/asyncio.html)
- [AES 암호화 표준](https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.197.pdf)