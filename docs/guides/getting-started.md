# PyKIS 시작하기

PyKIS는 한국투자증권 OpenAPI를 위한 Python SDK입니다. 이 가이드는 PyKIS를 처음 사용하는 개발자를 위한 시작 가이드입니다.

## 📋 사전 준비

### 1. 한국투자증권 OpenAPI 가입
1. [한국투자증권 OpenAPI 포털](https://apiportal.koreainvestment.com/)에서 회원가입
2. API 서비스 신청 및 승인
3. 앱 등록 후 **App Key**와 **App Secret** 발급
4. 계좌 번호 확인

### 2. Python 환경 설정
- **Python 3.8 이상** 필수
- 가상환경 사용 권장

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

## 🚀 설치

### 기본 설치
```bash
pip install pykis
```

### 개발 버전 설치 (최신 기능)
```bash
git clone https://github.com/your-repo/pykis.git
cd pykis
pip install -e .
```

## ⚙️ 환경 설정

### 1. 환경변수 설정
`.env` 파일을 생성하여 API 인증 정보를 설정합니다:

```bash
# .env 파일
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
KIS_ACCOUNT_NUMBER=12345678-01
```

### 2. 설정 파일 확인
환경변수가 올바르게 설정되었는지 확인:

```python
import os
from dotenv import load_dotenv

load_dotenv()

print("App Key:", os.getenv('KIS_APP_KEY')[:10] + "...")
print("Account:", os.getenv('KIS_ACCOUNT_NUMBER'))
```

## 🔑 기본 인증

### KISClient 초기화
```python
from pykis.core.client import KISClient

# 클라이언트 생성
client = KISClient(
    app_key=os.getenv('KIS_APP_KEY'),
    app_secret=os.getenv('KIS_APP_SECRET'),
    account_number=os.getenv('KIS_ACCOUNT_NUMBER'),
    is_real=True  # 실전투자: True, 모의투자: False
)

# 연결 테스트
print("인증 토큰:", client.get_access_token()[:20] + "...")
```

## 📊 REST API 사용

### 주식 정보 조회
```python
from pykis.stock.api import StockAPI

# 계좌 정보 설정
account_info = {
    'CANO': os.getenv('KIS_ACCOUNT_NUMBER').split('-')[0],
    'ACNT_PRDT_CD': os.getenv('KIS_ACCOUNT_NUMBER').split('-')[1]
}

# 주식 API 초기화
stock_api = StockAPI(client=client, account_info=account_info)

# 삼성전자 현재가 조회
price_data = stock_api.get_stock_price("005930")
print(f"삼성전자 현재가: {price_data['output']['stck_prpr']}원")

# 일일 가격 데이터 조회
daily_data = stock_api.get_daily_price("005930")
print(f"일일 데이터 건수: {len(daily_data)}개")
```

### 계좌 정보 조회
```python
from pykis.account.api import AccountAPI

# 계좌 API 초기화
account_api = AccountAPI(client=client, account_info=account_info)

# 잔고 조회
balance = account_api.get_account_balance()
print(f"보유 종목 수: {len(balance['output1'])}개")

# 주문 가능 금액 조회
buyable = account_api.get_buyable_amount("005930", "76000")
print(f"주문 가능 수량: {buyable['output']['ord_psbl_qty']}주")
```

## ⚡ 실시간 웹소켓 사용

### 기본 실시간 데이터 수신
```python
import asyncio
from pykis.websocket import EnhancedWebSocketClient

async def websocket_example():
    # 웹소켓 클라이언트 생성
    ws_client = EnhancedWebSocketClient(
        client=client,
        account_info=account_info,
        stock_codes=["005930", "000660"],  # 삼성전자, SK하이닉스
        enable_index=True,      # 지수 데이터 수신
        enable_ask_bid=True     # 호가 데이터 수신
    )
    
    # 콜백 함수 정의
    def on_trade(data):
        print(f"[체결] {data['name']}: {data['price']:,}원 ({data['change_rate']:+.2f}%)")
    
    def on_index(data):
        print(f"[지수] {data['name']}: {data['value']:,.2f} ({data['change_rate']:+.2f}%)")
    
    # 콜백 등록
    ws_client.register_callback('on_trade', on_trade)
    ws_client.register_callback('on_index', on_index)
    
    # 웹소켓 시작 (무한 루프)
    await ws_client.start()

# 실행
asyncio.run(websocket_example())
```

### 고급 웹소켓 사용 (WSAgent)
```python
from pykis.websocket import WSAgent, SubscriptionType

async def advanced_websocket():
    # WSAgent 직접 사용
    approval_key = client.get_ws_approval_key()
    agent = WSAgent(approval_key)
    
    # 핸들러 함수
    def handle_trade(data, metadata):
        if isinstance(data, list) and len(data) >= 3:
            code, time, price = data[0], data[1], float(data[2])
            print(f"체결: {code} {price:,}원 @ {time}")
    
    # 다양한 구독 추가
    agent.subscribe(SubscriptionType.STOCK_TRADE, "005930", handle_trade)
    agent.subscribe(SubscriptionType.INDEX, "0001")  # KOSPI
    agent.subscribe(SubscriptionType.PROGRAM_TRADE, "005930")
    
    # 연결 시작
    await agent.connect()

asyncio.run(advanced_websocket())
```

## 📈 주문 실행

### 현금 매수 주문
```python
# 시장가 매수
buy_order = account_api.order_stock_cash(
    ticker="005930",           # 삼성전자
    price="0",                 # 시장가 (0)
    quantity="10",             # 10주
    order_type="01"            # 매수
)

print(f"주문 결과: {buy_order.get('msg1', 'Unknown')}")
print(f"주문번호: {buy_order.get('output', {}).get('ODNO', 'N/A')}")
```

### 지정가 매도 주문
```python
# 지정가 매도
sell_order = account_api.order_stock_cash(
    ticker="005930",
    price="78000",             # 지정가 78,000원
    quantity="5",              # 5주
    order_type="02"            # 매도
)
```

## 🔍 실전 예제

### 간단한 자동매매 봇
```python
import asyncio
from datetime import datetime

class SimpleBot:
    def __init__(self, client, account_info):
        self.client = client
        self.account_info = account_info
        self.account_api = AccountAPI(client=client, account_info=account_info)
        self.positions = {}
        
    def on_trade_data(self, data):
        code = data['code']
        price = data['price']
        change_rate = data['change_rate']
        
        # 단순한 전략: 2% 하락 시 매수, 3% 상승 시 매도
        if change_rate <= -2.0 and code not in self.positions:
            self.buy_stock(code, price)
        elif change_rate >= 3.0 and code in self.positions:
            self.sell_stock(code, price)
            
    def buy_stock(self, code, price):
        try:
            # 10만원어치 매수
            qty = min(100000 // price, 100)  # 최대 100주
            order = self.account_api.order_stock_cash(
                ticker=code,
                price="0",  # 시장가
                quantity=str(qty),
                order_type="01"
            )
            if order.get('rt_cd') == '0':  # 성공
                self.positions[code] = {'qty': qty, 'avg_price': price}
                print(f"✅ 매수 성공: {code} {qty}주 @ {price:,}원")
        except Exception as e:
            print(f"❌ 매수 실패: {e}")
            
    def sell_stock(self, code, price):
        if code not in self.positions:
            return
        try:
            qty = self.positions[code]['qty']
            order = self.account_api.order_stock_cash(
                ticker=code,
                price="0",  # 시장가
                quantity=str(qty),
                order_type="02"
            )
            if order.get('rt_cd') == '0':  # 성공
                profit = (price - self.positions[code]['avg_price']) * qty
                print(f"✅ 매도 성공: {code} {qty}주 @ {price:,}원 (수익: {profit:,.0f}원)")
                del self.positions[code]
        except Exception as e:
            print(f"❌ 매도 실패: {e}")

# 봇 실행
async def run_bot():
    bot = SimpleBot(client, account_info)
    
    ws_client = EnhancedWebSocketClient(
        client=client,
        account_info=account_info,
        stock_codes=["005930", "000660", "035420"],  # 관심종목
        enable_index=False
    )
    
    ws_client.register_callback('on_trade', bot.on_trade_data)
    await ws_client.start()

# 주의: 실제 돈이 투자됩니다!
# asyncio.run(run_bot())
```

## ⚠️ 주의사항

### 1. 보안
- **API 키를 코드에 직접 작성하지 마세요**
- 환경변수나 안전한 설정 파일 사용
- `.env` 파일을 버전 관리에 포함하지 마세요

### 2. API 제한
- **요청 빈도 제한**: 초당 5회, 분당 200회
- **동시 연결 제한**: 웹소켓 연결은 계정당 제한
- **시장 시간**: 주식 시장 개장 시간에만 실시간 데이터 제공

### 3. 에러 처리
```python
try:
    result = stock_api.get_stock_price("005930")
    if result.get('rt_cd') != '0':
        print(f"API 오류: {result.get('msg1')}")
except Exception as e:
    print(f"네트워크 오류: {e}")
```

## 🆘 문제 해결

### 자주 발생하는 오류

#### 1. 인증 실패
```
Error: Invalid token
```
**해결방법**: API 키와 Secret을 다시 확인하고, 토큰을 갱신하세요.

#### 2. 계좌 권한 오류
```
Error: 40310000 - 모의투자 미신청
```
**해결방법**: OpenAPI 포털에서 모의투자 또는 실전투자 서비스를 신청하세요.

#### 3. 웹소켓 연결 실패
```
Error: Websocket connection failed
```
**해결방법**: 
- 네트워크 상태 확인
- approval_key 유효성 확인
- 시장 개장 시간 확인

### 디버깅 팁

#### 로깅 활성화
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('pykis')
logger.setLevel(logging.DEBUG)
```

#### API 응답 확인
```python
response = stock_api.get_stock_price("005930")
print("Full response:", response)
```

## 📚 더 알아보기

- **[API 문서](../api/websocket-api.md)**: 완전한 API 레퍼런스
- **[아키텍처 문서](../architecture/websocket-architecture.md)**: 시스템 구조 이해
- **[예제 코드](../../examples/)**: 더 많은 실전 예제
- **[공식 문서](https://apiportal.koreainvestment.com/)**: 한국투자증권 공식 API 문서

## 💡 다음 단계

1. **실전 예제 실행**: `examples/` 디렉토리의 예제 코드 실행
2. **자신만의 전략 개발**: 기술적 지표와 조건을 활용한 자동매매 전략 구현
3. **모니터링 시스템 구축**: 실시간 수익률 추적 및 알림 시스템 개발
4. **리스크 관리**: 손절매, 분산투자 등 리스크 관리 로직 추가