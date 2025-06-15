# pykis

한국투자증권 API를 Python으로 쉽게 사용할 수 있는 래퍼 라이브러리입니다.

## 설치 방법

```bash
pip install pykis
```

## 기본 사용법

```python
from pykis import Agent

# Agent 인스턴스 생성
agent = Agent()

# 계좌 잔고 조회
balance = agent.get_balance()

# 현재가 조회
price = agent.get_stock_price("005930")  # 삼성전자

# 분봉 데이터 조회
minute_data = agent.get_minute_chart("005930", "093000")  # 9시 30분 데이터
```

## 주요 기능

- 계좌 잔고 조회
- 주식 시세 조회
  - 국내주식: 현재가, 일별시세, 호가정보
  - 해외주식: 기간별시세, 뉴스, 권리정보
  - 채권: 기간별시세
- 시장 분석
  - 거래량/등락률/수익률 순위
  - 체결강도 랭킹(거래량 파워)
  - 투자자별 매매 동향
  - 증권사별 투자의견
- 재무정보
  - 손익계산서
  - 재무비율
  - 성장성/안정성 지표
- 프로그램 매매 정보 조회
- 조건검색식 종목 조회
- 실시간 시세 조회

## API 메서드 목록

### 계좌 관련
- `get_balance()`: 계좌 잔고 조회
- `get_possible_order(code, price)`: 주문 가능 수량 조회
- `order_stock_cash(code, price, quantity, order_type)`: 현금 주식 주문
- `cancel_order(order_id)`: 주문 취소
- `get_order_history()`: 주문 내역 조회

### 국내주식 관련
- `get_stock_price(code)`: 현재가 조회
- `get_daily_price(code)`: 일별 시세 조회
- `get_orderbook(code)`: 호가 정보 조회
- `get_minute_chart(code, time)`: 특정 시간 분봉 데이터 조회
- `fetch_minute_data(code, date, cache_dir)`: 당일 전체 분봉 데이터 조회 (캐시 활용)
- `get_minute_price(code)`: 분봉 시세 정보 조회
- `get_stock_income(code)`: 손익계산서 조회
- `get_stock_financial(code)`: 재무비율 조회
- `get_price_volume_ratio(code)`: 매물대 거래비중 조회
- `get_stock_info(ticker)`: 주식 기본 정보 조회
- `get_stock_basic(code)`: 주식 기본 정보 조회
- `get_stock_investor(ticker)`: 투자자별 매매 동향 조회
- `get_foreign_broker_net_buy(code, foreign_brokers, date)`: 외국계 증권사 순매수 조회
- `get_pbar_tratio(code)`: 시간대별 체결강도 조회
- `get_time_conclusion(code, hour)`: 시간별 체결 정보 조회
- `get_overtime_conclusion(code)`: 시간외 체결 정보 조회
- `get_daily_chart(code, start_date, end_date)`: 일별 차트 정보 조회
- `get_expected_closing_price(code)`: 예상 종가 정보 조회

### 해외주식 관련
- `get_overseas_price(code)`: 해외주식 현재가 조회
- `get_overseas_daily_price(code)`: 해외주식 일별 시세 조회
- `get_overseas_minute_price(code)`: 해외주식 분봉 시세 조회
- `get_overseas_news(code)`: 해외주식 뉴스 조회
- `get_overseas_right(code)`: 해외주식 권리 정보 조회

### 시장 분석
- `get_market_fluctuation()`: 시장 변동성 정보 조회
- `get_market_rankings(volume)`: 시장 순위 정보 조회
- `get_volume_power(volume)`: 거래량 파워 정보 조회
- `get_volume_power_ranking()`: 거래량 파워 순위 조회
- `get_index_chart(code)`: 지수 차트 정보 조회

### 프로그램 매매
- `get_program_trade_trend(code)`: 프로그램 매매 추이 조회
- `get_program_trade_hourly_trend(code)`: 시간별 프로그램 매매 추이 조회

### 조건검색
- `get_condition_stocks(condition_code)`: 조건검색 결과 조회
- `get_top_gainers(limit)`: 상승률 상위 종목 조회
- `get_top_losers(limit)`: 하락률 상위 종목 조회
- `get_top_volume(limit)`: 거래량 상위 종목 조회

### 회원사/거래원 관련
- `get_stock_member(ticker)`: 주식 회원사 정보 조회
- `get_member_transaction(code, mem_code)`: 회원사 일별 매매 종목 조회
- `get_member(code)`: 거래원 정보 조회

### 유틸리티
- `is_holiday(date)`: 휴장일 여부 확인
- `get_holiday_info()`: 휴장일 정보 조회
- `init_minute_db(db_path)`: 분봉 데이터 DB 초기화
- `migrate_minute_csv_to_db(code, db_path)`: CSV 분봉 데이터 DB 이관

## 사용 예시

```python
from pykis import Agent

# Agent 초기화
agent = Agent(account_info={
    'CANO': '계좌번호',
    'ACNT_PRDT_CD': '계좌상품코드'
})

# 주식 가격 조회
price = agent.get_stock_price("005930")  # 삼성전자

# 계좌 잔고 조회
balance = agent.get_balance()

# 해외주식 시세 조회
overseas_price = agent.get_overseas_price("AAPL")  # 애플

# 시장 순위 조회
volume_rank = agent.get_volume_power_ranking()  # 거래량 파워 순위
price_rank = agent.get_price_rank()    # 등락률 순위
power_rank = agent.get_volume_power_ranking()  # 체결강도 랭킹(거래량 파워)

# 재무정보 조회
income = agent.get_stock_income("005930")  # 손익계산서
financial = agent.get_stock_financial("005930")  # 재무비율
```

## 개발 환경 설정

1. 저장소 클론
```bash
git clone https://github.com/your-username/kis-agent.git
cd kis-agent
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
- `credit/kis_devlp.yaml` 파일에 API 인증 정보를 설정합니다.

## 테스트 실행

```bash
pytest tests/
```

## 주의사항
- API 호출 시 실제 주문이 발생할 수 있으므로 테스트 시 주의
- 인증 정보는 반드시 안전하게 관리
- API 호출 제한에 주의
- 에러 발생 시 로그 확인 필수
- 국내주식 엔드포인트는 실제 테스트 결과 대부분 정상 동작함 (일부 미지원/폐지 API 및 파라미터 오류 등은 실제 서비스 상태에 따라 다를 수 있음)