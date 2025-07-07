# pykis

한국투자증권 API를 Python으로 쉽게 사용할 수 있는 래퍼 라이브러리입니다.

## 설치 방법

```bash
pip install pykis
```

## 기본 사용법

```python
from pykis import Agent

# .env 파일에 설정된 정보를 바탕으로 Agent 인스턴스 생성
agent = Agent()

# 계좌 잔고 조회
balance = agent.get_account_balance()

# 현재가 조회
price = agent.get_stock_price("005930")  # 삼성전자

# 분봉 데이터 조회
minute_data = agent.get_minute_price("005930", "093000")  # 9시 30분 데이터

# 조건검색 결과 조회 (통일된 방식)
condition_stocks = agent.get_condition_stocks("unohee", 0, "N")

# 휴장일 정보 조회 (새로 추가됨)
holiday_info = agent.get_holiday_info()
is_holiday = agent.is_holiday("20241225")  # 크리스마스 휴장일 여부
```

## 주요 기능

- **계좌 관리**: 잔고 조회, 주문 가능 금액, 총 자산 조회, 신용 주문, 주문 정정/취소, 예약 주문
- **주식 시세**: 국내/해외 주식 현재가, 일별/분봉 시세, 호가 정보
- **시장 분석**: 체결강도 순위, 등락률 순위, 거래량 순위, 투자자별 매매 동향
- **재무 정보**: 손익계산서, 재무비율, 성장성/안정성 지표
- **프로그램 매매**: 종목별/시장별 프로그램 매매 추이 및 독립 분석 도구
- **조건검색**: 조건검색식 종목 조회 (통일된 API 방식)
- **휴장일 정보**: 휴장일 조회 및 특정 날짜 휴장일 여부 확인
- **실시간 데이터**: 웹소켓을 통한 실시간 시세, 지수, 프로그램매매, 호가 데이터 구독

## 🌟 웹소켓 실시간 데이터 (v0.1.20)

### 새로운 웹소켓 기능들
```python
from pykis import Agent

agent = Agent()

# 향상된 웹소켓 클라이언트 생성
ws_client = agent.websocket(
    stock_codes=["005930", "000660"],  # 구독할 종목들
    enable_index=True,                 # 📊 지수 실시간 구독 (코스피, 코스닥, 코스피200)
    enable_program_trading=True,       # 🔄 프로그램매매 실시간 구독
    enable_ask_bid=False              # 📈 호가 실시간 구독 (선택적)
)

# 실시간 데이터 수신 시작
await ws_client.connect()
```

### 지원하는 실시간 데이터
- **📊 실시간 지수**: KOSPI, KOSDAQ, KOSPI200 지수값, 등락률, 전일대비
- **📈 실시간 체결**: 종목별 체결가, 거래량, 체결강도 등
- **🔄 실시간 프로그램매매**: 매도량, 매수량, 순매수량, 순매수대금
- **📊 실시간 호가**: 10단계 호가 정보 (선택적 구독)

### 주요 특징
- **선택적 구독**: 필요한 데이터만 선택하여 구독 가능
- **자동 승인키 발급**: 웹소켓 연결 전 자동으로 승인키 발급
- **실시간 데이터 저장**: 받은 데이터를 자동으로 저장하여 분석 가능
- **기술적 지표 계산**: RSI, MACD 등 실시간 계산

## 최신 업데이트 (v0.1.20) ⭐ 신규

### ✨ 새로운 기능 (v0.1.22)
- **📚 메서드 탐색 및 사용법 도구 추가**: Agent에서 사용 가능한 모든 메서드를 쉽게 확인할 수 있는 기능 추가
  - `get_all_methods()`: 37개의 모든 메서드를 6개 카테고리별로 정리하여 반환
  - `search_methods(keyword)`: 키워드로 메서드 검색 (메서드명이나 설명에서 검색)
  - `show_method_usage(method_name)`: 특정 메서드의 상세 사용법 출력
- **🔧 pytest 테스트 시스템 완전 복구**: 127/128개 테스트 통과 (99.2% 성공률)
  - 토큰 관리 시스템 안정화 및 환경설정 경로 안정화
  - 테스트 실행 시간 90% 단축 (5분 → 30초)

### 이전 기능 (v0.1.20-21)
- **🌟 웹소켓 실시간 지수 구독 기능 (H0IF1000)**: 코스피, 코스닥, 코스피200 실시간 지수 데이터 구독 지원
- **🔄 웹소켓 실시간 프로그램매매 구독 기능 (H0GSCNT0)**: 종목별 실시간 프로그램매매 추이 데이터 구독 지원
- **📊 웹소켓 실시간 호가 구독 기능 개선 (H0STASP0)**: 10단계 호가 실시간 업데이트 지원
- **⚡ Agent 웹소켓 인터페이스 개선**: `enable_index`, `enable_program_trading`, `enable_ask_bid` 파라미터 추가

### 🔧 개선됨
- **웹소켓 클라이언트 메시지 처리 로직 개선**: 새로운 TR ID 처리 로직 추가
- **KISClient 웹소켓 승인키 발급 기능 추가**: `get_ws_approval_key()` 메서드 추가
- **테스트 커버리지 향상**: 웹소켓 클라이언트 12% → 25%

## 이전 업데이트 (v0.1.19)

### ✨ 새로운 기능
- **웹소켓 모듈 통합**: `KIS_WS.py`를 `pykis.websocket` 서브모듈로 통합하고 `Agent`에서 쉽게 접근할 수 있도록 `websocket()` 메서드를 추가했습니다.
- **문서 업데이트**: 웹소켓 통합에 맞춰 `README.md`, `PYKIS_API_METHODS.md` 등 관련 문서를 모두 업데이트했습니다.

## 이전 업데이트 (v0.1.18)

### ✅ 테스트 시스템 100% 통과 달성
- **전체 테스트 결과**: 121개 통과, 2개 스킵, 1개 xfail (예상된 실패)
- **PyKIS 노트북 핵심 기능 100% 통과**: 모든 주요 API 메서드 정상 작동 확인
  - `get_stock_price`, `get_daily_price`, `get_minute_price` 등 8개 핵심 API 테스트 성공
  - Agent 클래스 초기화 및 메서드 접근성 확인
  - 실시간 API 호출 및 응답 검증 완료

### 🔧 개선됨
- **테스트 안정성 강화**: CI/CD 환경에서 외부 의존성 문제 해결
- **설정 클래스 로직 개선**: `KISConfig` 클래스의 부분적 인자 제공 시에도 올바른 검증 수행
- **전체 테스트 커버리지 61% 유지**: 핵심 기능의 안정성 보장

## 이전 업데이트 (v0.1.16)

### ✨ 새로운 기능
- **📊 KOSPI200 지수 베이시스 계산 기능**: 선물옵션 API에 자동 최근월물 계산 기능 추가
  - `get_kospi200_futures_code` 함수: 두 번째 주 목요일 만기 규칙을 적용하여 다음 만기월(3,6,9,12월) 중 가장 가까운 미래 월물 자동 계산
  - `get_future_option_price` 메서드 개선: 별도 파라미터 없이 호출해도 최신 KOSPI200 선물 시세 자동 조회
  - 기존 수동 종목코드 지정 방식에서 자동 계산 방식으로 편의성 대폭 향상

### 🔧 개선됨
- **선물옵션 시세 조회 편의성 향상**: KOSPI200 베이시스 계산 자동화로 사용자 편의성 증대
- **문서 업데이트**: PYKIS_API_METHODS.md에 새로운 기능 설명 및 사용 예시 추가

## 이전 업데이트 (v0.1.15)

### ✨ 새로운 기능
- **📊 선물옵션 시세 API 추가**: 지수선물, 지수옵션, 주식선물, 주식옵션 시세 조회 기능 구현
  - `get_future_option_price` 메서드: 다양한 선물옵션 종목의 시세 조회 지원
  - 시장분류코드별 조회: F(지수선물), O(지수옵션), JF(주식선물), JO(주식옵션)
  - 종목코드 형식: 선물 6자리(예: 101S03), 옵션 9자리(예: 201S03370)

## 이전 업데이트 (v0.1.14)

### ✨ 새로운 기능
- **📈 업종 시세 API 추가**: 국내주식업종기간별시세 조회 기능 구현
  - `get_daily_index_chart_price` 메서드: 종합, 대형주, 중형주, 소형주, KOSPI, KOSDAQ 등 업종별 시세 조회
  - 기간별 조회 지원: 일봉, 주봉, 월봉, 년봉
  - 최대 50건 데이터 수신, 연속 조회를 위한 날짜 범위 설정 가능

## 이전 업데이트 (v0.1.13)

### ✨ 새로운 기능
- **📊 체결 관련 API 확장**: 시간대별 체결 조회 및 당일 체결강도 직접 조회 기능 추가
  - `get_hourly_conclusion` 메서드: 시간대별 체결 조회 기능
  - `get_stock_ccnl` 메서드: 주식현재가 체결(최근30건) 조회 - **당일 체결강도 직접 제공**
  - 체결강도 순위권에 없는 종목도 체결강도를 즉시 확인할 수 있어 매매 전략 수립에 유용

## 이전 업데이트 (v0.1.9)

### ✨ 새로운 기능
- **계좌 API 확장**: `pykis.account.api`에 신용 주문, 주문 정정/취소, 예약 주문 등 Postman 컬렉션에 명시된 모든 계좌 관련 API를 구현했습니다.
- **신규 계좌 API 테스트**: 새로 추가된 계좌 API 메서드에 대한 단위 테스트를 추가하여 안정성을 검증했습니다.

### 🔧 개선됨
- **테스트 스크립트 정리**: 모든 테스트 파일에서 불필요한 `print`문과 로깅 호출을 제거하여 테스트 코드의 가독성과 명확성을 높였습니다.

## 이전 업데이트 (v0.1.8)

### 🗑️ 제거됨
- `pykis/program/api.py`: 더 이상 사용되지 않는 deprecated 파일 제거.

## API 메서드 목록

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

### 국내주식 관련
- `get_stock_price(code)`: 현재가 조회
- `get_daily_price(code)`: 일별 시세 조회
- `get_orderbook(code)`: 호가 정보 조회
- `get_minute_price(code, time)`: 특정 시간 분봉 데이터 조회
- `fetch_minute_data(code, date, cache_dir)`: 당일 전체 분봉 데이터 조회 (캐시 활용)
- `get_stock_income(code)`: 손익계산서 조회
- `get_stock_financial(code)`: 재무비율 조회
- `get_price_volume_ratio(code)`: 매물대 거래비중 조회
- `get_stock_info(ticker)`: 주식 기본 정보 조회
- `get_stock_basic(code)`: 주식 기본 정보 조회
- `get_stock_investor(ticker)`: 투자자별 매매 동향 조회
- `get_foreign_broker_net_buy(code, foreign_brokers, date)`: 외국계 증권사 순매수 조회
- `get_pbar_tratio(code)`: 매물대/거래비중 조회
- `get_hourly_conclusion(code, hour)`: 시간대별 체결 조회
- `get_stock_ccnl(code)`: 주식현재가 체결(최근30건) 조회 - 당일 체결강도 포함
- `get_overtime(code)`: 시간외 체결 정보 조회
- `get_daily_chart(code, start_date, end_date)`: 일별 차트 정보 조회

### 해외주식 관련
- `get_overseas_price(code)`: 해외주식 현재가 조회
- `get_overseas_daily_price(code)`: 해외주식 일별 시세 조회
- `get_overseas_minute_price(code)`: 해외주식 분봉 시세 조회
- `get_overseas_news(code)`: 해외주식 뉴스 조회
- `get_overseas_right(code)`: 해외주식 권리 정보 조회

### 시장 분석
- `get_market_fluctuation()`: 등락률 순위 조회 (국내주식 전용)
- `get_market_rankings(volume)`: 시장 순위 정보 조회
- `get_volume_power()`: 체결강도 순위 조회 (올바른 API 적용)
- `get_top_gainers()`: 상승률 상위 종목 조회
- `get_top_losers()`: 하락률 상위 종목 조회
- `get_top_volume()`: 거래량 상위 종목 조회

### 프로그램 매매
- `get_program_trade_by_stock(code, date)`: 종목별 프로그램매매추이(체결) 조회
- `get_program_trade_daily_summary(code, date)`: 종목별 일별 프로그램 매매 집계 조회
- `get_program_trade_market_daily(start_date, end_date)`: 시장 전체 프로그램 매매 현황 조회
- `get_program_trade_period_detail(start_date, end_date)`: 기간별 프로그램 매매 상세 조회

### 조건검색 (v0.1.8에서 통일됨)
- `get_condition_stocks(user_id, seq, tr_cont)`: 조건검색 결과 조회 (통일된 API 방식)

### 휴장일 정보 (v0.1.8에서 새로 추가됨)
- `get_holiday_info()`: 휴장일 정보 조회 (직접 API 접근)
- `is_holiday(date)`: 특정 날짜 휴장일 여부 확인 (편의 메서드)

### 회원사/거래원 관련
- `get_stock_member(ticker)`: 주식 회원사 정보 조회
- `get_member_transaction(code, mem_code)`: 회원사 일별 매매 종목 조회
- `get_member(code)`: 거래원 정보 조회

### 유틸리티
- `init_minute_db(db_path)`: 분봉 데이터 DB 초기화
- `migrate_minute_csv_to_db(code, db_path)`: CSV 분봉 데이터 DB 이관
- `classify_broker(name)`: 거래원 분류 (정적 메서드)

## 사용 예시

```python
from pykis import Agent

# .env 파일을 통해 자동으로 인증 정보가 로드됩니다.
agent = Agent()

# 🆕 사용 가능한 모든 메서드 확인 (v0.1.22)
methods = agent.get_all_methods()
print(f"총 {methods['_summary']['total_methods']}개 메서드 사용 가능")

# 🆕 키워드로 메서드 검색
price_methods = agent.search_methods("price")
for method in price_methods:
    print(f"{method['name']}: {method['description']}")

# 🆕 특정 메서드 사용법 확인
agent.show_method_usage("get_stock_price")

# 주식 가격 조회
price = agent.get_stock_price("005930")  # 삼성전자

# 계좌 잔고 조회
balance = agent.get_account_balance()

# 해외주식 시세 조회
overseas_price = agent.get_overseas_price("AAPL")  # 애플

# 시장 순위 조회 (v0.1.4에서 개선됨)
volume_power = agent.get_volume_power()  # 체결강도 순위 (올바른 API)
fluctuation = agent.get_market_fluctuation()  # 등락률 순위 (국내주식 전용)

# 프로그램 매매 정보 조회 (v0.1.4에서 분리됨)
program_trade_stock = agent.get_program_trade_by_stock("005930")  # 종목별
program_trade_market = agent.get_program_trade_market_daily("20240601", "20240630")  # 시장 전체

# 재무정보 조회
income = agent.get_stock_income("005930")  # 손익계산서
financial = agent.get_stock_financial("005930")  # 재무비율

# 조건검색 (v0.1.8에서 통일된 방식)
condition_stocks = agent.get_condition_stocks("unohee", 0, "N")

# 휴장일 정보 (v0.1.8에서 새로 추가됨)
holiday_info = agent.get_holiday_info()  # 휴장일 정보 조회
is_xmas_holiday = agent.is_holiday("20241225")  # 크리스마스 휴장일 여부
is_today_holiday = agent.is_holiday("20240625")  # 오늘이 휴장일인지 확인
```

## 독립 분석 도구

v0.1.4부터 프로그램 매매 분석 기능이 독립적인 도구로 분리되었습니다:

```python
# examples/program_trade_analysis.py 사용
from examples.program_trade_analysis import ProgramTradeAnalyzer

analyzer = ProgramTradeAnalyzer()
analysis = analyzer.analyze_program_trade("005930", "20240622")
```

## 개발 환경 설정

1. 저장소 클론
```bash
git clone https://github.com/your-username/pykis.git
cd pykis
```

2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. API 인증 정보 설정
- `.env.example` 파일을 복사하여 `.env` 파일을 만들고, API 인증 정보를 설정합니다.

## 테스트 실행

```bash
# 전체 테스트
pytest tests/

# 종합 테스트 노트북 (50+ 메서드)
jupyter notebook examples/pykis.ipynb
```

## 주의사항
- API 호출 시 실제 주문이 발생할 수 있으므로 테스트 시 주의
- 인증 정보는 반드시 안전하게 관리
- API 호출 제한에 주의
- 에러 발생 시 로그 확인 필수
- 한국투자증권 OpenAPI 정책 변경에 따라 일부 기능이 영향받을 수 있음

## 라이선스
MIT License

## 기여하기
이슈 리포트나 풀 리퀘스트는 언제든지 환영합니다.