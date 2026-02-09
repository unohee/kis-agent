# PyKIS

한국투자증권 OpenAPI Python 래퍼 - Korea Investment & Securities Trading API Client

## 주요 특징

- **고성능**: 지능형 캐싱으로 API 호출 80-95% 감소
- **안정성**: 실측 기반 Rate Limiting (18 RPS / 900 RPM)
- **실시간**: WebSocket을 통한 실시간 데이터 스트리밍
- **국내시장**: KOSPI, KOSDAQ, NXT(넥스트) 시장 완벽 지원
- **해외시장**: 미국, 일본, 중국, 홍콩, 베트남 9개 거래소 지원
- **선물옵션**: 국내/해외 선물옵션 거래 지원
- **타입 안정성**: 96개 TypedDict 응답 모델, 100% 타입힌팅
- **명확한 문서**: 한국투자증권 API 공식 문서와 용어 일치

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 설치

```bash
pip install pykis
```

WebSocket 지원이 필요한 경우:

```bash
pip install pykis[websocket]
```

## 사전 준비

1. [한국투자증권 API 포털](https://apiportal.koreainvestment.com)에서 API 신청
2. APP_KEY와 APP_SECRET 발급
3. 계좌번호(CANO)와 계좌상품코드(ACNT_PRDT_CD) 확인

## 빠른 시작

```python
from pykis import Agent
import os

# 환경변수에서 API 키 로드
agent = Agent(
    app_key=os.environ.get('KIS_APP_KEY'),
    app_secret=os.environ.get('KIS_APP_SECRET'),
    account_no=os.environ.get('KIS_ACCOUNT_NO'),
    account_code=os.environ.get('KIS_ACCOUNT_CODE', '01'),
)

# 주식 현재가 조회
price = agent.get_stock_price("005930")  # 삼성전자
print(f"현재가: {price['output']['stck_prpr']}원")

# 계좌 잔고 조회
balance = agent.get_account_balance()

# 일봉 데이터 조회
daily = agent.inquire_daily_itemchartprice(
    "005930",
    start_date="20250101",
    end_date="20251231"
)
```

## 국내 주식 거래

```python
# 현금 매수 (지정가)
result = agent.order_stock_cash("buy", "005930", "00", "1", "70000")

# 현금 매수 (시장가)
result = agent.order_stock_cash("buy", "005930", "03", "1", "0")

# 신용 매수
from datetime import datetime
today = datetime.now().strftime("%Y%m%d")
result = agent.order_stock_credit("buy", "009470", "21", "00", "1", "12000", loan_dt=today)

# 주문 가능 수량 조회
inquiry = agent.inquire_order_psbl("005930", "70000")
print(f"주문가능수량: {inquiry['output']['max_buy_qty']}")

# 주문 정정/취소
result = agent.order_rvsecncl(org_order_no, qty, price, order_type, cncl_type)
```

## 해외 주식 거래

```python
# 해외주식 시세 조회
apple = agent.overseas.get_price(excd="NAS", symb="AAPL")
print(f"AAPL 현재가: ${apple['output']['last']}")

# 차트 데이터 조회
tesla_daily = agent.overseas.get_daily_price(excd="NAS", symb="TSLA", start="20240101")
tesla_minute = agent.overseas.get_minute_price(excd="NYS", symb="TSLA", interval=5)

# 해외주식 잔고 조회
balance = agent.overseas.get_balance()

# 매수 주문
result = agent.overseas.buy_order(
    excd="NAS",      # 거래소: NASDAQ
    symb="AAPL",     # 종목: Apple
    qty="10",        # 수량
    price="150.00"   # 가격
)

# 매도 주문
result = agent.overseas.sell_order(excd="NYS", symb="MSFT", qty="20", price="350.00")

# 주문 정정/취소
modify_result = agent.overseas.modify_order(excd="NAS", order_no="...", qty="15", price="155.00")
cancel_result = agent.overseas.cancel_order(excd="NAS", order_no="...")
```

**지원 거래소:**
- 미국: NAS (NASDAQ), NYS (NYSE), AMS (AMEX)
- 일본: TSE (도쿄증권거래소)
- 중국: SHS (상해), SZS (심천)
- 홍콩: HKS (홍콩거래소)
- 베트남: HSX (호치민), HNX (하노이)

## 선물/옵션 거래

```python
# 국내 선물 시세 조회
futures_price = agent.futures.get_price("101S03")  # KOSPI200 선물

# 국내 선물 주문
result = agent.futures.buy_order(code="101S03", qty=1, price=350.00)
result = agent.futures.sell_order(code="101S03", qty=1, price=351.00)

# 해외 선물 시세 조회
overseas_futures = agent.overseas_futures.get_price(excd="CME", symb="ESH5")

# 선물 계좌 잔고
futures_balance = agent.futures.get_balance()
```

## 실시간 데이터 (WebSocket)

```python
# WebSocket 클라이언트 생성
ws_client = agent.websocket(
    stock_codes=["005930", "035420"],  # 삼성전자, NAVER
    enable_index=True,                 # 지수 구독
    enable_program_trading=True,       # 프로그램 매매
    enable_ask_bid=True                # 호가 구독
)

# 실행
import asyncio
asyncio.run(ws_client.start())
```

## 분석 기능

```python
# 투자자별 매매동향
investor_trend = agent.get_stock_investor("005930")

# 프로그램 매매 동향
program_trade = agent.get_program_trade_by_stock("005930", "20250101")

# 증권사별 매매동향
member_trade = agent.get_stock_member("005930")

# 지지/저항선 분석
support_resistance = agent.calculate_support_resistance("005930")

# 휴장일 확인
is_holiday = agent.is_holiday("20250101")
```

## 장기 데이터 조회

API의 100건 제한을 자동으로 우회하여 전체 기간 데이터 수집:

```python
result = agent.get_daily_price_all(
    code="005930",
    start_date="20200102",
    end_date="20201230",
    period="D",
    org_adj_prc="1"
)
print(f"총 {len(result['output2'])}건 수집")  # 248건 (100건 제한 우회!)
print(f"API 호출: {result['_pagination_info']['total_calls']}회")
```

## 거래 보고서 생성

```python
from pykis.utils.trading_report import generate_trading_report

report_path = generate_trading_report(
    client=agent.client,
    account_info={'CANO': 'your_account', 'ACNT_PRDT_CD': '01'},
    start_date='20250101',
    end_date='20250131',
    output_path='trading_history.xlsx',
    tickers=['005930', '035420'],
    only_executed=True
)
```

## 성능 최적화

- **캐시 적중률**: 80-95% (API 호출 대폭 감소)
- **Rate Limiting**: 18 RPS / 900 RPM (실측 안정 기준)
- **응답 시간**: 평균 50ms 이하 (캐시 적중 시)
- **동시 연결**: 멀티스레드 안전성 보장

## 한국어 Docstring

PyKIS는 의도적으로 한국어 docstring을 사용합니다:

1. **API 공식 문서와 용어 일치**: 필드명 `stck_prpr`(주식현재가)를 한국어 그대로 사용
2. **디버깅 효율성**: API 에러 메시지가 한글이므로 즉시 매칭 가능
3. **주 사용자층 최적화**: 한국투자증권 API는 국내 전용

## 개발 환경 설정

```bash
# 개발 의존성 설치
pip install -e ".[dev]"

# 코드 린팅 및 포맷팅
ruff check pykis tests
ruff format pykis tests

# 타입 체크
mypy pykis

# 테스트 실행
pytest tests/ -v --cov=pykis
```

## API 메서드 목록

### 계좌
- `get_account_balance()`: 계좌 잔고 조회
- `inquire_order_psbl()`: 주문 가능 수량 조회
- `inquire_credit_order_psbl()`: 신용 주문 가능 수량 조회

### 주문
- `order_stock_cash()`: 현금 주문 (매수/매도)
- `order_stock_credit()`: 신용 주문
- `order_rvsecncl()`: 주문 정정/취소
- `inquire_psbl_rvsecncl()`: 정정/취소 가능 조회

### 시세
- `get_stock_price()`: 주식 현재가
- `get_daily_price()`: 일봉 데이터
- `get_minute_price()`: 분봉 데이터
- `get_orderbook()`: 호가 조회
- `fetch_minute_data()`: 전체 분봉 데이터 (4시간)

### 분석
- `get_stock_investor()`: 투자자별 매매동향
- `get_stock_member()`: 증권사별 매매동향
- `get_program_trade_by_stock()`: 프로그램 매매
- `calculate_support_resistance()`: 지지/저항선

### 해외주식 (agent.overseas.*)
- `get_price()`: 해외주식 현재가
- `get_daily_price()`: 해외주식 일봉
- `get_balance()`: 해외주식 잔고
- `buy_order()` / `sell_order()`: 매수/매도 주문
- `modify_order()` / `cancel_order()`: 주문 정정/취소

### 선물옵션 (agent.futures.*)
- `get_price()`: 선물 시세
- `get_balance()`: 선물 계좌 잔고
- `buy_order()` / `sell_order()`: 선물 주문

## 라이센스

MIT License

## 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다.

## 링크

- [한국투자증권 API 포털](https://apiportal.koreainvestment.com)
- [GitHub Issues](https://github.com/unohee/pykis/issues)
