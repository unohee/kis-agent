# pykis API 메서드 레퍼런스

> **pykis v0.1.8** - 한국투자증권 OpenAPI Python 래퍼 라이브러리

이 문서는 pykis 라이브러리의 모든 사용 가능한 메서드를 정리한 완전한 API 레퍼런스입니다.  
후임자나 다른 에이전트 LLM이 pykis를 활용할 때 참고할 수 있도록 작성되었습니다.

## 📋 목차

- [기본 사용법](#기본-사용법)
- [계좌 관련 메서드](#계좌-관련-메서드)
- [주식 시세 관련 메서드](#주식-시세-관련-메서드)
- [시장 분석 메서드](#시장-분석-메서드)
- [프로그램 매매 메서드](#프로그램-매매-메서드)
- [조건검색 메서드](#조건검색-메서드)
- [휴장일 정보 메서드](#휴장일-정보-메서드)
- [거래원/회원사 관련 메서드](#거래원회원사-관련-메서드)
- [해외주식 관련 메서드](#해외주식-관련-메서드)
- [유틸리티 메서드](#유틸리티-메서드)
- [데이터 관리 메서드](#데이터-관리-메서드)

---

## 기본 사용법

```python
from pykis import Agent

# Agent 초기화 (설정 파일 자동 로드)
agent = Agent()

# 또는 계좌 정보 직접 설정
agent = Agent(account_info={
    'CANO': '계좌번호',
    'ACNT_PRDT_CD': '계좌상품코드'
})
```

---

## 계좌 관련 메서드

### `get_account_balance()`
**설명**: 계좌 잔고 조회  
**반환**: `Dict` - 계좌 잔고 정보  
**예시**:
```python
balance = agent.get_account_balance()
```

### `get_possible_order_amount()`
**설명**: 주문 가능 금액 조회  
**반환**: `Dict` - 주문 가능 금액 정보  
**예시**:
```python
available = agent.get_possible_order_amount()
```

### `get_account_order_quantity(code)`
**설명**: 계좌별 주문 수량 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 주문 수량 정보  
**예시**:
```python
quantity = agent.get_account_order_quantity("005930")
```

### `get_possible_order(code, price, order_type="01")`
**설명**: 주문 가능 여부 확인  
**매개변수**:
- `code` (str) - 종목코드
- `price` (str) - 주문가격
- `order_type` (str) - 주문구분 (01: 지정가, 03: 시장가)

**반환**: `Dict` - 주문 가능 정보  
**예시**:
```python
possible = agent.get_possible_order("005930", "75000", "01")
```

### `order_credit(code, qty, price, order_type)`
**설���**: 신용 주문  
**매개변수**:
- `code` (str) - 종목코드
- `qty` (int) - 주문수량
- `price` (int) - 주문가격
- `order_type` (str) - 주문구분

**반환**: `Dict` - 주문 결과  
**예시**:
```python
order_result = agent.order_credit("005930", 10, 75000, "00")
```

### `order_rvsecncl(org_order_no, qty, price, order_type, cncl_type)`
**설명**: 주문 정정/취소  
**매개변수**:
- `org_order_no` (str) - 원주문번호
- `qty` (int) - 주문수량
- `price` (int) - 주문가격
- `order_type` (str) - 주문구분
- `cncl_type` (str) - 취소구분

**반환**: `Dict` - 주문 결과  
**예시**:
```python
order_result = agent.order_rvsecncl("12345", 10, 75000, "00", "02")
```

### `inquire_psbl_rvsecncl()`
**설명**: 정정/취소 가능 주문 조회  
**반환**: `Dict` - 주문 가능 정보  
**예시**:
```python
possible_orders = agent.inquire_psbl_rvsecncl()
```

### `order_resv(code, qty, price, order_type)`
**설명**: 예약 주문  
**매개변수**:
- `code` (str) - 종목코드
- `qty` (int) - 주문수량
- `price` (int) - 주문가격
- `order_type` (str) - 주문구분

**반환**: `Dict` - 주문 결과  
**예시**:
```python
order_result = agent.order_resv("005930", 10, 75000, "00")
```

### `order_resv_rvsecncl(seq, qty, price, order_type)`
**설명**: 예약 주문 정정/취소  
**매개변수**:
- `seq` (int) - 예약주문순번
- `qty` (int) - 주문수량
- `price` (int) - 주문가격
- `order_type` (str) - 주문구분

**반환**: `Dict` - 주문 결과  
**예시**:
```python
order_result = agent.order_resv_rvsecncl(12345, 10, 75000, "00")
```

### `order_resv_ccnl()`
**설명**: 예약 주문 조회  
**반환**: `Dict` - 주문 정보  
**예시**:
```python
reserved_orders = agent.order_resv_ccnl()
```

---

## 주식 시세 관련 메서드

### `get_stock_price(code)`
**설명**: 주식 현재가 조회  
**매개변수**: `code` (str) - 종목코드 (6자리)  
**반환**: `Dict` - 현재가 정보  
**예시**:
```python
price = agent.get_stock_price("005930")  # 삼성전자
```

### `get_daily_price(code, period="D", org_adj_prc="1")`
**설명**: 일별 시세 조회  
**매개변수**:
- `code` (str) - 종목코드
- `period` (str) - 기간구분 (D: 일, W: 주, M: 월, Y: 년)
- `org_adj_prc` (str) - 수정주가구분 (0: 미사용, 1: 사용)

**반환**: `Dict` - 일별 시세 정보  
**예시**:
```python
daily = agent.get_daily_price("005930", "D", "1")
```

### `get_minute_price(code, hour="153000")`
**설명**: 분봉 시세 조회  
**매개변수**:
- `code` (str) - 종목코드
- `hour` (str) - 시간 (HHMMSS 형식)

**반환**: `Dict` - 분봉 데이터  
**예시**:
```python
minute_data = agent.get_minute_price("005930", "143000")
```

### `get_minute_chart(code, time)`
**설명**: 분봉 차트 조회  
**매개변수**:
- `code` (str) - 종목코드
- `time` (str) - 시간 (HHMMSS)

**반환**: `Dict` - 분봉 차트 데이터  
**예시**:
```python
chart = agent.get_minute_chart("005930", "143000")
```

### `get_orderbook(code)`
**설명**: 호가 정보 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `DataFrame` - 호가 정보  
**예시**:
```python
orderbook = agent.get_orderbook("005930")
```

### `get_overtime(code)`
**설명**: 시간외 체결 정보 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 시간외 체결 정보  
**예시**:
```python
overtime = agent.get_overtime("005930")
```

### `get_stock_info(ticker)`
**설명**: 주식 기본 정보 조회  
**매개변수**: `ticker` (str) - 종목코드  
**반환**: `DataFrame` - 종목 기본 정보  
**예시**:
```python
info = agent.get_stock_info("005930")
```

### `get_daily_chart(code, start_date, end_date)`
**설명**: 일별 차트 정보 조회  
**매개변수**:
- `code` (str) - 종목코드
- `start_date` (str) - 시작일 (YYYYMMDD)
- `end_date` (str) - 종료일 (YYYYMMDD)

**반환**: `Dict` - 일별 차트 데이터  
**예시**:
```python
chart = agent.get_daily_chart("005930", "20240601", "20240630")
```

---

## 시장 분석 메서드

### `get_volume_power(volume=0)`
**설명**: 체결강도 순위 조회  
**매개변수**: `volume` (int) - 거래량 기준 (기본값: 0)  
**반환**: `Dict` - 체결강도 순위  
**예시**:
```python
volume_power = agent.get_volume_power(1000000)
```

### `get_market_fluctuation()`
**설명**: 등락률 순위 조회 (국내주식 전용)  
**반환**: `Dict` - 등락률 순위  
**예시**:
```python
fluctuation = agent.get_market_fluctuation()
```

### `get_market_rankings(volume=5000000)`
**설명**: 시장 순위 정보 조회  
**매개변수**: `volume` (int) - 거래량 기준  
**반환**: `Dict` - 시장 순위 정보  
**예시**:
```python
rankings = agent.get_market_rankings(5000000)
```

### `get_top_gainers()`
**설명**: 상승률 상위 종목 조회  
**반환**: `Dict` - 상승률 상위 종목  
**예시**:
```python
gainers = agent.get_top_gainers()
```

### `get_stock_investor(ticker)`
**설명**: 투자자별 매매 동향 조회  
**매개변수**: `ticker` (str) - 종목코드  
**반환**: `DataFrame` - 투자자별 매매 동향  
**예시**:
```python
investor = agent.get_stock_investor("005930")
```

### `get_pbar_tratio(code)`
**설명**: 매물대/거래비중 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 매물대/거래비중 정보  
**예시**:
```python
pbar = agent.get_pbar_tratio("005930")
```

### `get_hourly_conclusion(code, hour)`
**설명**: 시간대별 체결 조회  
**매개변수**: 
- `code` (str) - 종목코드
- `hour` (str) - 기준시간 (HHMMSS 형식, 기본값: "115959")
**반환**: `Dict` - 시간대별 체결 정보  
**예시**:
```python
# 기본값 사용 (11시59분59초 기준)
hourly = agent.get_hourly_conclusion("005930")

# 특정 시간 지정 (14시30분00초 기준)
hourly = agent.get_hourly_conclusion("005930", "143000")
```

---

## 프로그램 매매 메서드

### `get_program_trade_by_stock(code)`
**설명**: 종목별 프로그램매매추이(체결) 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 프로그램 매매 정보  
**예시**:
```python
program_trade = agent.get_program_trade_by_stock("005930")
```

### `get_program_trade_daily_summary(code, date_str)`
**설명**: 종목별 일별 프로그램 매매 집계 조회  
**매개변수**:
- `code` (str) - 종목코드
- `date_str` (str) - 날짜 (YYYYMMDD)

**반환**: `Dict` - 일별 프로그램 매매 집계  
**예시**:
```python
summary = agent.get_program_trade_daily_summary("005930", "20240625")
```

### `get_program_trade_period_detail(start_date, end_date)`
**설명**: 기간별 프로그램 매매 상세 조회  
**매개변수**:
- `start_date` (str) - 시작일 (YYYYMMDD)
- `end_date` (str) - 종료일 (YYYYMMDD)

**반환**: `Dict` - 기간별 프로그램 매매 상세  
**예시**:
```python
detail = agent.get_program_trade_period_detail("20240601", "20240630")
```

### `get_program_trade_market_daily(start_date, end_date)`
**설명**: 시장 전체 프로그램 매매 종합현황 (일별) 조회  
**매개변수**:
- `start_date` (str) - 시작일 (YYYYMMDD)
- `end_date` (str) - 종료일 (YYYYMMDD)

**반환**: `Dict` - 시장 전체 프로그램 매매 현황  
**예시**:
```python
market_daily = agent.get_program_trade_market_daily("20240601", "20240630")
```

### `get_program_trade_hourly_trend(code)`
**설명**: 시간별 프로그램 매매 추이 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 시간별 프로그램 매매 추이  
**예시**:
```python
hourly = agent.get_program_trade_hourly_trend("005930")
```

---

## 조건검색 메서드

### `get_condition_stocks(user_id="unohee", seq=0, tr_cont="N")`
**설명**: 조건검색 결과 조회 (통일된 API 방식)  
**매개변수**:
- `user_id` (str) - 사용자 ID (기본값: "unohee")
- `seq` (int) - 조건검색 시퀀스 번호 (기본값: 0)
- `tr_cont` (str) - 연속조회 여부 (기본값: "N")

**반환**: `List[Dict]` - 조건검색 결과 리스트  
**예시**:
```python
condition_stocks = agent.get_condition_stocks("unohee", 0, "N")
```

---

## 휴장일 정보 메서드

### `get_holiday_info()`
**설명**: 휴장일 정보 조회 (직접 API 접근)  
**반환**: `Dict` - 휴장일 정보  
**예시**:
```python
holiday_info = agent.get_holiday_info()
```

### `is_holiday(date)`
**설명**: 특정 날짜 휴장일 여부 확인 (편의 메서드)  
**매개변수**: `date` (str) - 날짜 (YYYYMMDD)  
**반환**: `bool` - 휴장일 여부 (True: 휴장일, False: 거래일)  
**예시**:
```python
is_holiday_today = agent.is_holiday("20241225")  # 크리스마스
```

---

## 거래원/회원사 관련 메서드

### `get_member(code)`
**설명**: 거래원 정보 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 거래원 정보  
**예시**:
```python
member_info = agent.get_member("005930")
```

### `get_stock_member(ticker)`
**설명**: 주식 회원사 정보 조회  
**매개변수**: `ticker` (str) - 종목코드  
**반환**: `Dict` - 회원사 정보  
**예시**:
```python
stock_member = agent.get_stock_member("005930")
```

### `get_member_transaction(code, mem_code="99999")`
**설명**: 회원사 일별 매매 종목 조회  
**매개변수**:
- `code` (str) - 종목코드
- `mem_code` (str) - 회원사 코드 (기본값: "99999")

**반환**: `Dict` - 회원사 매매 정보  
**예시**:
```python
transaction = agent.get_member_transaction("005930", "99999")
```

### `get_foreign_broker_net_buy(code, foreign_brokers, date)`
**설명**: 외국계 증권사 순매수 조회  
**매개변수**:
- `code` (str) - 종목코드
- `foreign_brokers` (list) - 외국계 증권사 리스트
- `date` (str) - 날짜 (YYYYMMDD)

**반환**: `tuple` - 순매수 정보  
**예시**:
```python
net_buy = agent.get_foreign_broker_net_buy("005930", ["모간", "골드만"], "20240625")
```

### `classify_broker(name)` (정적 메서드)
**설명**: 거래원 성격 분류 (외국계/리테일/기관)  
**매개변수**: `name` (str) - 거래원명  
**반환**: `str` - 분류 결과  
**예시**:
```python
broker_type = Agent.classify_broker("골드만삭스")  # "외국계"
```

---

## 해외주식 관련 메서드

### `get_overseas_price(code)`
**설명**: 해외주식 현재가 조회  
**매개변수**: `code` (str) - 해외주식 종목코드  
**반환**: `Dict` - 해외주식 현재가  
**예시**:
```python
overseas_price = agent.get_overseas_price("AAPL")
```

### `get_overseas_daily_price(code)`
**설명**: 해외주식 일별 시세 조회  
**매개변수**: `code` (str) - 해외주식 종목코드  
**반환**: `Dict` - 해외주식 일별 시세  
**예시**:
```python
overseas_daily = agent.get_overseas_daily_price("AAPL")
```

### `get_overseas_minute_price(code)`
**설명**: 해외주식 분봉 시세 조회  
**매개변수**: `code` (str) - 해외주식 종목코드  
**반환**: `Dict` - 해외주식 분봉 시세  
**예시**:
```python
overseas_minute = agent.get_overseas_minute_price("AAPL")
```

### `get_overseas_news(code)`
**설명**: 해외주식 뉴스 조회  
**매개변수**: `code` (str) - 해외주식 종목코드  
**반환**: `Dict` - 해외주식 뉴스  
**예시**:
```python
overseas_news = agent.get_overseas_news("AAPL")
```

### `get_overseas_right(code)`
**설명**: 해외주식 권리 정보 조회  
**매개변수**: `code` (str) - 해외주식 종목코드  
**반환**: `Dict` - 해외주식 권리 정보  
**예시**:
```python
overseas_right = agent.get_overseas_right("AAPL")
```

---

## 유틸리티 메서드

### `get_price_volume_ratio(code)`
**설명**: 매물대 거래비중 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 매물대 거래비중  
**예시**:
```python
pv_ratio = agent.get_price_volume_ratio("005930")
```

### `inquire_ccnl(code)`
**설명**: 종목별 체결 현황 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 체결 현황  
**예시**:
```python
ccnl = agent.inquire_ccnl("005930")
```

---

## 데이터 관리 메서드

### `init_minute_db(db_path='stonks_candles.db')`
**설명**: 분봉 데이터용 DB 및 테이블 생성 (최초 1회)  
**매개변수**: `db_path` (str) - DB 파일 경로  
**예시**:
```python
agent.init_minute_db('my_data.db')
```

### `migrate_minute_csv_to_db(code, db_path='stonks_candles.db')`
**설명**: 기존 CSV 분봉 데이터를 DB로 이관  
**매개변수**:
- `code` (str) - 종목코드
- `db_path` (str) - DB 파일 경로

**예시**:
```python
agent.migrate_minute_csv_to_db("005930", 'my_data.db')
```

### `fetch_minute_data(code, date=None, cache_dir='cache')`
**설명**: 분봉 데이터 조회 및 캐시  
**매개변수**:
- `code` (str) - 종목코드
- `date` (str) - 날짜 (YYYYMMDD, None이면 오늘)
- `cache_dir` (str) - 캐시 디렉토리

**반환**: `DataFrame` - 분봉 데이터  
**예시**:
```python
minute_data = agent.fetch_minute_data("005930", "20240625", "cache")
```

---

## 💡 사용 팁

### 1. 에러 처리
모든 메서드는 실패 시 `None`을 반환하므로 반드시 체크:
```python
result = agent.get_stock_price("005930")
if result is None:
    print("API 호출 실패")
    return

if result.get('rt_cd') != '0':
    print(f"API 오류: {result.get('msg1', '알 수 없는 오류')}")
    return
```

### 2. 응답 데이터 구조
대부분의 API 응답은 다음 구조를 가집니다:
```python
{
    "rt_cd": "0",        # 성공: "0", 실패: 기타
    "msg_cd": "MCA00000",
    "msg1": "정상처리 되었습니다",
    "output": { ... }    # 실제 데이터
}
```

### 3. 종목코드 형식
- **국내주식**: 6자리 숫자 (예: "005930")
- **해외주식**: 알파벳 티커 (예: "AAPL")

### 4. 날짜 형식
모든 날짜는 **YYYYMMDD** 형식 사용:
```python
today = "20240625"
agent.get_daily_price("005930", date=today)
```

### 5. 연속 API 호출 시 주의사항
API 호출 제한을 고려하여 적절한 간격 유지:
```python
import time

for code in stock_codes:
    result = agent.get_stock_price(code)
    time.sleep(0.1)  # 100ms 대기
```

---

## 🔗 관련 리소스

- **GitHub**: https://github.com/unohee/pykis
- **PyPI**: https://pypi.org/project/pykis/
- **CHANGELOG**: [CHANGELOG.md](CHANGELOG.md)
- **개발 가이드**: [AGENTS.md](AGENTS.md)

---

## 📞 지원

문의사항이나 버그 신고는 GitHub Issues를 통해 연락주세요.

**pykis v0.1.8** - 한국투자증권 OpenAPI를 쉽고 안전하게! 🚀 