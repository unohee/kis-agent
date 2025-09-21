# PyKIS WebSocket 실시간 데이터 수신 가이드

## 목차
1. [개요](#개요)
2. [인증 과정](#인증-과정)
3. [WebSocket 연결](#websocket-연결)
4. [데이터 구독](#데이터-구독)
5. [실시간 데이터 처리](#실시간-데이터-처리)
6. [전체 구현 예제](#전체-구현-예제)
7. [트러블슈팅](#트러블슈팅)

---

## 개요

PyKIS WebSocket 클라이언트는 한국투자증권의 실시간 시세 데이터를 수신할 수 있는 기능을 제공합니다.

### 주요 기능
- **실시간 체결 정보**: 주식 거래 체결 데이터
- **실시간 호가 정보**: 10단계 매수/매도 호가
- **실시간 지수 정보**: KOSPI, KOSDAQ, KOSPI200 등
- **프로그램매매 정보**: 프로그램 매매 동향

### WebSocket 서버 정보
- **URL**: `ws://ops.koreainvestment.com:21000`
- **프로토콜**: WebSocket
- **인증 방식**: REST API를 통한 승인키 발급 후 사용

---

## 인증 과정

### 1단계: Agent 초기화
```python
from pykis import Agent
from dotenv import load_dotenv
import os

# 환경변수 로드
load_dotenv()

# Agent 생성 (REST API 클라이언트)
agent = Agent(
    app_key=os.getenv('APP_KEY'),
    app_secret=os.getenv('APP_SECRET'),
    account_no=os.getenv('ACC_NO'),
    account_code="01"
)
```

### 2단계: WebSocket 승인키 발급
```python
# WebSocket 클라이언트 생성
ws = agent.websocket(
    stock_codes=["005930", "000660"],  # 구독할 종목
    enable_index=True,                  # 지수 실시간 활성화
    enable_program_trading=True,        # 프로그램매매 활성화
    enable_ask_bid=False                # 호가 실시간 비활성화
)

# 승인키 발급 (REST API 호출)
approval_key = ws.get_approval()
print(f"승인키: {approval_key}")
```

### 승인키 발급 내부 과정
1. REST API 엔드포인트: `/oauth2/Approval`
2. 요청 본문:
```json
{
    "grant_type": "client_credentials",
    "appkey": "YOUR_APP_KEY",
    "secretkey": "YOUR_APP_SECRET"
}
```
3. 응답:
```json
{
    "approval_key": "f9ab9f20-33e3-4e9c-af60-...",
    "approval_desc": "승인 성공"
}
```

---

## WebSocket 연결

### 연결 설정
```python
import websockets
import asyncio

async def connect_websocket():
    # WebSocket 서버 연결
    url = "ws://ops.koreainvestment.com:21000"

    async with websockets.connect(
        url,
        ping_interval=30,  # 30초마다 ping
        ping_timeout=30     # 30초 timeout
    ) as websocket:
        print("WebSocket 연결 성공")
        # 구독 및 데이터 수신 로직
```

### 연결 유지
- **Ping/Pong**: 30초 간격으로 자동 처리
- **재연결**: 연결 끊김 시 자동 재연결 로직 구현 필요

---

## 데이터 구독

### 구독 요청 형식

모든 구독 요청은 다음 JSON 형식을 따릅니다:

```json
{
    "header": {
        "approval_key": "승인키",
        "custtype": "P",           // P: 개인, B: 법인
        "tr_type": "1",            // 1: 구독, 2: 구독해제
        "content-type": "utf-8"
    },
    "body": {
        "input": {
            "tr_id": "TR_ID",      // 트랜잭션 ID
            "tr_key": "종목코드"    // 종목코드 또는 지수코드
        }
    }
}
```

### 주요 TR_ID 종류

| TR_ID | 설명 | tr_key 예시 |
|-------|------|------------|
| H0STCNT0 | 실시간 체결 | 005930 (삼성전자) |
| H0STASP0 | 실시간 호가 | 005930 |
| H0IF1000 | 실시간 지수 | 0001 (KOSPI) |
| H0GSCNT0 | 프로그램매매 | 005930 |

### 구독 요청 예제

#### 1. 실시간 체결 구독
```python
async def subscribe_trade(websocket, approval_key, stock_code):
    subscribe_data = {
        "header": {
            "approval_key": approval_key,
            "custtype": "P",
            "tr_type": "1",
            "content-type": "utf-8"
        },
        "body": {
            "input": {
                "tr_id": "H0STCNT0",
                "tr_key": stock_code  # "005930"
            }
        }
    }
    await websocket.send(json.dumps(subscribe_data))
    print(f"{stock_code} 체결정보 구독 완료")
```

#### 2. 지수 구독
```python
async def subscribe_index(websocket, approval_key):
    index_codes = {
        "0001": "KOSPI",
        "1001": "KOSDAQ",
        "2001": "KOSPI200"
    }

    for code, name in index_codes.items():
        subscribe_data = {
            "header": {
                "approval_key": approval_key,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "H0IF1000",
                    "tr_key": code
                }
            }
        }
        await websocket.send(json.dumps(subscribe_data))
        print(f"{name} 지수 구독 완료")
        await asyncio.sleep(0.1)  # 요청 간 딜레이
```

#### 3. 호가 구독
```python
async def subscribe_orderbook(websocket, approval_key, stock_code):
    subscribe_data = {
        "header": {
            "approval_key": approval_key,
            "custtype": "P",
            "tr_type": "1",
            "content-type": "utf-8"
        },
        "body": {
            "input": {
                "tr_id": "H0STASP0",
                "tr_key": stock_code
            }
        }
    }
    await websocket.send(json.dumps(subscribe_data))
    print(f"{stock_code} 호가 구독 완료")
```

---

## 실시간 데이터 처리

### 수신 데이터 형식

WebSocket으로 수신되는 데이터는 파이프(|)로 구분된 문자열입니다:

```
암호화여부|TR_ID|연속구분|데이터
```

- **암호화여부**: 0 (평문) / 1 (AES 암호화)
- **TR_ID**: 데이터 종류 식별자
- **연속구분**: 0 (단건) / 1 (연속)
- **데이터**: 캐럿(^)으로 구분된 필드들

### 데이터 파싱 예제

#### 체결 데이터 (H0STCNT0)
```python
def parse_trade_data(data):
    """실시간 체결 데이터 파싱"""
    parts = data.split('|')
    if len(parts) < 4:
        return None

    tr_id = parts[1]
    body_data = parts[3]

    if tr_id == 'H0STCNT0':
        fields = body_data.split('^')
        return {
            'type': '체결',
            'code': fields[0],           # 종목코드
            'time': fields[1],           # 체결시간
            'price': fields[2],          # 현재가
            'change': fields[3],         # 전일대비
            'change_rate': fields[4],   # 등락률
            'volume': fields[9],         # 체결량
            'total_volume': fields[10]  # 누적거래량
        }
    return None
```

#### 지수 데이터 (H0IF1000)
```python
def parse_index_data(data):
    """실시간 지수 데이터 파싱"""
    parts = data.split('|')
    if len(parts) < 4:
        return None

    tr_id = parts[1]
    body_data = parts[3]

    if tr_id == 'H0IF1000':
        fields = body_data.split('^')
        return {
            'type': '지수',
            'code': fields[0],       # 지수코드
            'time': fields[1],       # 시간
            'value': fields[2],      # 지수값
            'change': fields[3],     # 전일대비
            'change_rate': fields[4] # 등락률
        }
    return None
```

### 암호화된 데이터 처리

일부 데이터는 AES 암호화되어 전송됩니다:

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

def decrypt_data(encrypted_data, aes_key, aes_iv):
    """AES 복호화"""
    cipher = AES.new(aes_key, AES.MODE_CBC, aes_iv)
    decrypted = cipher.decrypt(b64decode(encrypted_data))
    return unpad(decrypted, AES.block_size).decode('utf-8')

def parse_websocket_data(data, aes_key=None, aes_iv=None):
    """WebSocket 데이터 파싱 (암호화 처리 포함)"""
    parts = data.split('|')

    if parts[0] == '1' and aes_key and aes_iv:
        # 암호화된 데이터
        body_data = decrypt_data(parts[3], aes_key, aes_iv)
    else:
        # 평문 데이터
        body_data = parts[3] if len(parts) > 3 else ""

    return {
        'encrypted': parts[0] == '1',
        'tr_id': parts[1],
        'body': body_data
    }
```

---

## 전체 구현 예제

### 기본 실시간 모니터링

```python
from pykis import Agent
import asyncio
import json
import websockets
from datetime import datetime

async def realtime_monitoring():
    """실시간 시세 모니터링"""

    # 1. Agent 초기화
    agent = Agent(
        app_key="YOUR_APP_KEY",
        app_secret="YOUR_APP_SECRET",
        account_no="YOUR_ACCOUNT",
        account_code="01"
    )

    # 2. WebSocket 클라이언트 생성
    ws_client = agent.websocket(
        stock_codes=["005930", "000660"],  # 삼성전자, SK하이닉스
        enable_index=True,
        enable_program_trading=True,
        enable_ask_bid=False
    )

    # 3. 승인키 발급
    approval_key = ws_client.get_approval()

    # 4. WebSocket 연결 및 구독
    url = "ws://ops.koreainvestment.com:21000"

    async with websockets.connect(url, ping_interval=30) as websocket:
        print("WebSocket 연결 성공")

        # 5. 종목 구독
        for stock_code in ["005930", "000660"]:
            subscribe_data = {
                "header": {
                    "approval_key": approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "H0STCNT0",
                        "tr_key": stock_code
                    }
                }
            }
            await websocket.send(json.dumps(subscribe_data))
            print(f"{stock_code} 구독 완료")
            await asyncio.sleep(0.1)

        # 6. 데이터 수신 루프
        while True:
            try:
                data = await asyncio.wait_for(websocket.recv(), timeout=30)

                # PINGPONG 필터
                if 'PINGPONG' in data:
                    continue

                # 데이터 파싱
                if data[0] in ['0', '1']:  # 실시간 데이터
                    parsed = parse_realtime_data(data)
                    if parsed:
                        process_realtime_data(parsed)

            except asyncio.TimeoutError:
                print("Timeout - 연결 유지 중...")
                continue
            except Exception as e:
                print(f"오류: {e}")
                break

def parse_realtime_data(data):
    """실시간 데이터 파싱"""
    parts = data.split('|')
    if len(parts) < 4:
        return None

    tr_id = parts[1]
    body = parts[3]

    if tr_id == 'H0STCNT0':  # 체결
        fields = body.split('^')
        return {
            'type': '체결',
            'code': fields[0],
            'price': fields[2],
            'volume': fields[9],
            'time': datetime.now()
        }

    return None

def process_realtime_data(data):
    """실시간 데이터 처리"""
    if data['type'] == '체결':
        print(f"[{data['time'].strftime('%H:%M:%S')}] "
              f"{data['code']}: {data['price']}원 ({data['volume']}주)")

# 실행
if __name__ == "__main__":
    asyncio.run(realtime_monitoring())
```

### PyKIS 내장 WebSocket 사용

가장 간단한 방법은 PyKIS 내장 기능을 사용하는 것입니다:

```python
from pykis import Agent

# Agent 초기화
agent = Agent(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    account_no="YOUR_ACCOUNT",
    account_code="01"
)

# WebSocket 생성 및 설정
ws = agent.websocket(
    stock_codes=["005930", "000660", "035720"],
    purchase_prices={
        "005930": (70000, 100),   # 매수가, 수량
        "000660": (150000, 50),
        "035720": (50000, 20)
    },
    enable_index=True,
    enable_program_trading=True,
    enable_ask_bid=True
)

# 실시간 모니터링 시작
ws.run()  # 블로킹 호출 - Ctrl+C로 종료
```

---

## 트러블슈팅

### 1. 승인키 발급 실패

**문제**: `approval_key를 답에서 추출하지 못했습니다.`

**해결방법**:
- APP_KEY와 APP_SECRET이 올바른지 확인
- 실전/모의 구분 확인
- API 사용 권한 확인

### 2. WebSocket 연결 실패

**문제**: 연결이 자주 끊어짐

**해결방법**:
```python
# 자동 재연결 로직
while True:
    try:
        async with websockets.connect(url) as ws:
            # 구독 및 처리
            pass
    except Exception as e:
        print(f"재연결 중... {e}")
        await asyncio.sleep(5)
```

### 3. 데이터 수신 안 됨

**문제**: 구독 후 데이터가 오지 않음

**체크리스트**:
- 장 운영시간 확인 (09:00 ~ 15:30)
- 종목코드 정확성 확인
- 구독 성공 메시지 확인
- TR_ID가 올바른지 확인

### 4. 암호화 데이터 처리

**문제**: 일부 데이터가 깨져서 표시됨

**해결방법**:
```python
# AES 키 설정 (필요시)
if ws.aes_key and ws.aes_iv:
    # 암호화된 데이터 처리
    decrypted = decrypt_data(encrypted_part, ws.aes_key, ws.aes_iv)
```

### 5. Rate Limit

**문제**: 너무 많은 구독 요청

**해결방법**:
```python
# 구독 요청 간 딜레이 추가
for stock in stock_codes:
    await subscribe(stock)
    await asyncio.sleep(0.1)  # 100ms 딜레이
```

---

## 테스트 결과

실제 테스트 결과 (2025-09-17):

```
============================================================
PyKIS WebSocket 기능 테스트
============================================================
1. 인증키 발급: ✓ 성공
2. WebSocket 연결: ✓ 성공
3. 실시간 수신: ✓ 준비됨
============================================================

[실시간 데이터 샘플]
- 삼성전자(005930) 체결: 77,350원 ~ 77,400원
- 총 수신 메시지: 86개 (30초)
- 유효 데이터: 84개
```

---

## 참고 자료

- [한국투자증권 OpenAPI 문서](https://apiportal.koreainvestment.com)
- [WebSocket Protocol RFC 6455](https://datatracker.ietf.org/doc/html/rfc6455)
- [PyKIS GitHub Repository](https://github.com/your-repo/pykis)

---

*마지막 업데이트: 2025-09-17*