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
- **실시간 데이터**: 실시간 시세 조회

## 최신 업데이트 (v0.1.9)

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
- `get_possible_order_amount(code, price)`: ���문 가능 수량 조회
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