# PyKIS

한국투자증권 OpenAPI를 Python으로 쉽게 사용할 수 있는 래퍼 라이브러리입니다.

** NEW: NXT(넥스트레이드) 시장 지원!** - KOSPI/KOSDAQ과 함께 차세대 대체거래소 통합 지원

[![Tests](https://img.shields.io/badge/tests-232%20passed-brightgreen)](https://github.com/your-repo/pykis)
[![Coverage](https://img.shields.io/badge/coverage-52%25-orange)](https://github.com/your-repo/pykis)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![NXT](https://img.shields.io/badge/NXT-지원-green)](https://www.nextrade.co.kr/)

##  설치 방법

```bash
pip install pykis
```

##  API 키 발급

한국투자증권 개발자센터에서 API 키를 발급받으세요:
- [개발자센터](https://apiportal.koreainvestment.com)에서 회원가입 및 API 신청
- APP_KEY와 APP_SECRET 발급
- 계좌번호(CANO)와 상품코드(ACNT_PRDT_CD) 확인

##  기본 사용법

### API 키 직접 전달 방식 (권장)

```python
from pykis import Agent
import os

# 환경변수에서 API 키 로드 (보안 권장)
app_key = os.environ.get('KIS_APP_KEY')
app_secret = os.environ.get('KIS_APP_SECRET')
account_no = os.environ.get('KIS_ACCOUNT_NO')
account_code = os.environ.get('KIS_ACCOUNT_CODE', '01')

# Agent 인스턴스 생성 (실전투자)
agent = Agent(
    app_key=app_key,
    app_secret=app_secret,
    account_no=account_no,
    account_code=account_code,
    # base_url="https://openapi.koreainvestment.com:9443"  # 기본값 (실전)
)

# 모의투자 Agent 생성
agent_mock = Agent(
    app_key=app_key,
    app_secret=app_secret,
    account_no=account_no,
    account_code=account_code,
    base_url="https://openapivts.koreainvestment.com:29443"  # 모의투자
)
```

### 예외 처리

```python
try:
    agent = Agent(
        app_key=app_key,
        app_secret=app_secret,
        account_no=account_no,
        account_code=account_code
    )
except ValueError as e:
    print(f"필수 매개변수 누락: {e}")
except RuntimeError as e:
    print(f"토큰 발급 실패: {e}")
```

### .env 파일 사용 (호환성)

기존 코드와의 호환성을 위해 `.env` 파일도 여전히 지원합니다:

```bash
# .env 파일
APP_KEY=your_app_key_here
APP_SECRET=your_app_secret_here
KIS_BASE_URL=https://openapi.koreainvestment.com:9443
CANO=your_account_number
ACNT_PRDT_CD=01
```

```python
# .env 파일에서 로드
from dotenv import load_dotenv
import os

load_dotenv()

agent = Agent(
    app_key=os.getenv('APP_KEY'),
    app_secret=os.getenv('APP_SECRET'),
    account_no=os.getenv('CANO'),
    account_code=os.getenv('ACNT_PRDT_CD', '01')
)

#  계좌 정보 조회
balance = agent.get_account_balance()  # 계좌 잔고

# Note: get_cash_available과 get_total_asset 메서드가 없는 경우 대체 방법:
if balance and balance.get('rt_cd') == '0':
    # 전체 계좌 잔고 정보는 balance['output2']에 포함됨
    total_info = balance['output2'][0] if balance.get('output2') else None
    if total_info:
        total_asset = total_info.get('tot_evlu_amt')  # 총 평가금액
        available_cash = total_info.get('nass_amt')   # 순자산금액

#  주식 시세 조회 (KOSPI/KOSDAQ/NXT 통합 지원)
price = agent.get_stock_price("005930")      # 삼성전자 현재가 (KOSPI)
daily = agent.get_daily_price("035720")      # 카카오 일별시세 (KOSDAQ)
orderbook = agent.get_orderbook("NXT종목")   # NXT 시장 종목도 동일하게 조회 가능

#  분봉 데이터 조회
minute_data = agent.get_minute_price("005930", "093000")  # 특정 시간 분봉
daily_minute = agent.get_daily_minute_price("005930", "20250715", "153000")  # 과거일자 분봉

#  고효율 분봉 수집 (4번 호출로 전일 분봉 수집)
minute_data = agent.fetch_minute_data("005930", "20250715")  # 특정일
recent_data = agent.fetch_minute_data("005930")             # 최근 영업일

#  매물대 분석 (지지선/저항선, VWAP, 피벗)
support_resistance = agent.calculate_support_resistance("005930")

#  조건검색 & 투자자 정보
condition_stocks = agent.get_condition_stocks("user_id", 0, "N")
investor_trend = agent.get_stock_investor("005930")  # 투자자별 매매동향

#  휴장일 & 시장 정보
is_holiday = agent.is_holiday("20250101")  # 휴장일 여부
holiday_info = agent.get_holiday_info()    # 휴장일 목록

#  코스피200 선물 시세 (자동 최근월물)
futures_price = agent.get_future_option_price()  # 9월물(101W09) 자동 조회

#  거래내역 Excel 내보내기
from pykis.utils.trading_report import generate_trading_report
report_path = generate_trading_report(
    agent.client, 
    {'CANO': 'your_account', 'ACNT_PRDT_CD': '01'},
    '20250101', '20250131',
    output_path='trading_history.xlsx'
)
```

##  웹소켓 실시간 데이터

```python
# 웹소켓으로 실시간 시세 수신
ws_client = agent.websocket(
    stock_codes=["005930", "035420"],  # 삼성전자, 네이버
    enable_index=True,                 # 지수 데이터
    enable_program_trading=True,       # 프로그램매매 
    enable_ask_bid=True               # 호가 데이터
)

# 비동기 실행
import asyncio
asyncio.run(ws_client.start())
```

##  거래내역 Excel 내보내기

```python
from pykis.utils.trading_report import generate_trading_report

# 계좌 거래내역을 Excel로 내보내기
report_path = generate_trading_report(
    client=agent.client,
    account_info={'CANO': 'your_account', 'ACNT_PRDT_CD': '01'},
    start_date='20250101',
    end_date='20250131', 
    output_path='trading_history.xlsx',
    tickers=['005930', '035420'],  # 특정 종목만 (선택사항)
    only_executed=True             # 체결된 거래만
)
print(f"거래내역이 저장되었습니다: {report_path}")
```

##  분봉 데이터 크롤러

대량의 분봉 데이터를 SQLite에 저장하는 크롤러:

```bash
cd examples  
python minute_candle_crawler.py
```

### 기능
- **대화형 인터페이스**: 종목명/코드와 기간을 입력받아 자동 수집
- **영업일 자동 계산**: 휴장일 API를 활용한 정확한 영업일 계산
- **효율적 수집**: 4번 호출로 하루 전체 분봉 데이터 수집
- **SQLite 저장**: `{종목코드}_candles.db` 파일로 자동 저장
- **진행 상황 표시**: 실시간 수집 진행률 및 통계 제공

### 실행 예시
```
 분봉 데이터 크롤러
========================================
 종목명 또는 종목코드를 입력하세요: 삼성전자
 종목 확인: 삼성전자 (005930)

 수집 기간 설정
시작일 (YYYYMMDD): 20240101
종료일 (YYYYMMDD): 20240131

 수집 시작: 삼성전자(005930)
 기간: 20240101 ~ 20240131
 총 영업일: 22일
 저장 경로: 005930_candles.db
============================================================
[  1/22] 20240102 수집 중...  완료 (361건)
[  2/22] 20240103 수집 중...  완료 (361건)
...
============================================================
 수집 완료!
 성공: 22/22일 
 저장 위치: 005930_candles.db

 저장된 데이터 통계:
   총 분봉 개수: 7,942건
   수집된 날짜: 22일
   일평균 분봉: 361.0건
```

##  테스트 현황

-  **178개 테스트 통과** (2개 건너뜀, 1개 예상 실패)
-  **44% 코드 커버리지** 
-  **핵심 모듈 고커버리지**:
  - `trading_report.py`: 98%
  - `program/trade.py`: 95% 
  - `core/config.py`: 88%
  - `websocket/ws_agent.py`: 64%

```bash
# 테스트 실행
pytest tests/ -v --cov=pykis
```

##  주요 기능

### 계좌 관련
- `get_account_balance()`: 계좌 잔고 조회
- `get_cash_available()`: 주문 가능 현금 조회
- `get_total_asset()`: 총 자산 조회
- `get_possible_order_amount(code, price)`: 주문 가능 수량 조회
- `order_credit(code, qty, price, order_type)`: 신용 주문
- `order_rvsecncl(org_order_no, qty, price, order_type, cncl_type)`: 주문 정정/취소
- `inquire_psbl_rvsecncl()`: 정정/취소 가능 주문 조회
- `order_resv(code, qty, price, order_type)`: 예약 주문
- `order_resv_rvsecncl(seq, qty, price, order_type)`: 예약 주문 정정/취소
- `order_resv_ccnl()`: 예약 주문 조회

### 국내주식 관련 (KOSPI/KOSDAQ/NXT 통합 지원)
- `get_stock_price(code)`: 현재가 조회 
- `get_daily_price(code)`: 일별 시세 조회  
- `get_orderbook(code)`: 호가 정보 조회
- `get_minute_price(code, time)`: 특정 시간 분봉 데이터 조회
- `get_daily_minute_price(code, date, hour)`: 과거일자 분봉 데이터 조회 (최대 120건)
- `fetch_minute_data(code, date, cache_dir)`: 분봉 데이터 수집 (4번 호출로 효율적 수집)
- `calculate_support_resistance(code, date)`: 매물대 분석 (지지선/저항선, VWAP, 피벗)

### 선물옵션 관련  
- `get_future_option_price()`: 코스피200 선물 시세 (자동 최근월물)
- `get_futures_price(code)`: 특정 선물 시세 조회
- `get_kospi200_futures_code()`: 현재 활성 선물코드 계산

### 유틸리티
- `generate_trading_report()`: 거래내역 Excel 내보내기 

### 투자자 정보
- `get_stock_investor(ticker)`: 투자자별 매매 동향 조회
- `get_foreign_broker_net_buy(code, foreign_brokers, date)`: 외국계 증권사 순매수 조회
- `get_volume_power(code)`: 체결강도 조회
- `get_stock_ccnl(code)`: 주식현재가 체결(최근30건) 조회 - 당일 체결강도 포함

### 거래원 정보
- `get_stock_member(code)`: 거래원 정보 조회
- `get_member_transaction(code, start_date, end_date)`: 거래원별 거래 내역

### 조건검색
- `get_condition_stocks(user_id, seq, div_code)`: 조건검색 결과 조회

### 프로그램매매
- `get_program_trade_by_stock(code, date)`: 종목별 프로그램매매 추이
- `get_program_trade_daily_summary(code, date)`: 프로그램매매 일별 집계
- `get_program_trade_market_daily(start_date, end_date)`: 프로그램매매 종합현황

### 기타
- `get_holiday_info()`: 휴장일 정보 조회
- `is_holiday(date)`: 특정일 휴장일 여부 확인
- `get_daily_credit_balance(code, date)`: 국내주식 신용잔고 일별추이 조회

##  최신 업데이트 (v0.1.21)

###  새로운 기능
- ** 거래내역 Excel 내보내기**: 계좌 거래내역을 Excel 파일로 내보내는 유틸리티 추가
  - 기간별, 종목별 필터링 지원
  - 체결된 거래만 필터링 옵션
  - 98% 테스트 커버리지 달성
- ** 테스트 시스템 대폭 개선**: 178개 테스트 모두 통과 달성
  - Agent 초기화 시 env_path 매개변수 필수화로 보안 강화
  - 모든 테스트 파일에서 환경변수 경로 명시적 지정
  - 프로그램매매 API 테스트 안정화

###  개선됨
- **보안 강화**: .env 파일 경로를 명시적으로 지정하도록 개선
- **코드 품질**: BaseAPI 패턴 적용으로 account 속성 일관성 확보
- **문서 정리**: 한국투자증권 관련 설정만 유지하고 불필요한 설정 제거

## 이전 업데이트 (v0.1.20)

##  최신 업데이트 (v0.1.22)

###  NXT(넥스트레이드) 시장 지원 추가
- **통합 시장 지원**: 모든 API에서 KOSPI/KOSDAQ/NXT 동시 지원
  - `FID_COND_MRKT_DIV_CODE` 값을 "J"에서 "UN"으로 변경
  - 기존 KOSPI/KOSDAQ 종목 100% 호환성 보장
  - NXT 종목도 기존과 동일한 방식으로 조회 가능
- **영향받는 기능**: 현재가 조회, 일별/분봉 시세, 호가 정보, 투자자별 매매 동향, 조건 검색 등 모든 주식 관련 API

###  테스트 및 코드 품질 향상
- **테스트 확대**: 232개 테스트 통과 (기존 178개에서 54개 추가)
- **코드 커버리지**: 52%로 향상 (기존 44%에서 개선)
- **신규 테스트 모듈**: DataFrame 헬퍼, 투자자 DB, WebSocket 클라이언트 기본 기능 테스트 추가

###  이전 업데이트
- ** 웹소켓 멀티 구독 시스템**: 여러 종목을 동시에 구독할 수 있는 `WSAgent` 클래스 추가
  - 실시간 시세, 호가, 지수, 프로그램매매 데이터 동시 수신
  - 자동 연결 관리 및 오류 복구 기능
  - 유연한 구독 설정 및 콜백 시스템

###  개선됨
- **웹소켓 모듈 통합**: `KIS_WS.py`를 `pykis.websocket` 서브모듈로 통합
- **Agent 접근성**: `agent.websocket()` 메서드로 쉬운 웹소켓 접근

## 이전 업데이트 (v0.1.18)

###  테스트 시스템 100% 통과 달성
- **전체 테스트 결과**: 121개 통과, 2개 스킵, 1개 xfail (예상된 실패)
- **PyKIS 노트북 핵심 기능 100% 통과**: 모든 주요 API 메서드 정상 작동 확인

###  개선됨
- **테스트 안정성 강화**: CI/CD 환경에서 외부 의존성 문제 해결
- **설정 클래스 로직 개선**: `KISConfig` 클래스의 부분적 인자 제공 시에도 올바른 검증 수행

## 이전 업데이트 (v0.1.16)

###  새로운 기능
- ** KOSPI200 지수 베이시스 계산 기능**: 선물옵션 API에 자동 최근월물 계산 기능 추가
  - `get_kospi200_futures_code` 함수: 두 번째 주 목요일 만기 규칙을 적용하여 다음 만기월(3,6,9,12월) 중 가장 가까운 미래 월물 자동 계산
  - `get_future_option_price` 메서드 개선: 별도 파라미터 없이 호출해도 최신 KOSPI200 선물 시세 자동 조회

## 라이선스

MIT License

## 기여하기

이슈 리포트, 기능 요청, 풀 리퀘스트를 환영합니다!

## 지원

- 이슈 트래커: [GitHub Issues](https://github.com/your-repo/pykis/issues)
- 문서: [PyKIS 문서](https://your-docs-url.com)