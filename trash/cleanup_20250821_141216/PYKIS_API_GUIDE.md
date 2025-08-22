# PyKIS API 사용 가이드

## 개요
PyKIS는 한국투자증권 OpenAPI를 Python에서 쉽게 사용할 수 있도록 만든 라이브러리입니다.

## 설치 및 초기 설정

### 설치
```bash
pip install pykis
```

### 초기화
```python
from pykis import PyKIS

# 환경 변수 또는 직접 인증 정보 입력
kis = PyKIS(
    account_number="12345678",  # 계좌번호
    account_code="01",          # 계좌 상품코드
    app_key="YOUR_APP_KEY",     # 앱키 (옵션: 환경변수 KIS_APP_KEY)
    app_secret="YOUR_SECRET"    # 앱시크릿 (옵션: 환경변수 KIS_APP_SECRET)
)

# 또는 환경변수 사용 (.env 파일 지원)
kis = PyKIS()
```

## 주요 API 카테고리

### 1. 기본 시세 조회

#### 현재가 조회
```python
# 주식 현재가
price = kis.stock.get_stock_price("005930")  # 삼성전자

# 주식 현재가 시세2 (확장 정보)
price_detail = kis.stock.get_price_2("005930")

# 호가 및 예상체결
orderbook = kis.stock.get_asking_price_exp_ccn("005930")

# 체결 내역 (최근 30건)
trades = kis.stock.get_stock_ccnl("005930")
```

#### 차트 데이터
```python
# 일봉 데이터
daily = kis.stock.get_daily_price("005930", period="D")  # D:일, W:주, M:월, Y:년

# 분봉 데이터
minute = kis.stock.get_minute_price("005930", hour="153000")

# 당일 전체 분봉
full_minute = kis.stock.get_full_day_minute_price("005930", date="20240820")

# 시간별 차트 (30초/1분/3분/5분/10분/15분/30분/60분)
time_chart = kis.stock.get_time_daily_chart_price("005930", period_div="1")  # 1:1분봉
```

### 2. 투자자/회원사 동향

#### 투자자별 매매동향
```python
# 종목별 투자자 매매동향
investor = kis.stock.get_stock_investor("005930")

# 시장별 투자자 일별 매매동향
market_investor_daily = kis.stock.get_investor_daily_by_market("STK", "20240820")  # STK:전체, KSP:코스피, KSQ:코스닥

# 시장별 투자자 시간대별 매매동향
market_investor_time = kis.stock.get_investor_time_by_market("STK", time_div="1")  # 0:당일전체, 1:1분, 2:10분, 3:30분
```

#### 회원사 매매동향
```python
# 종목별 회원사 매매동향
member = kis.stock.get_stock_member("005930")

# 종목별 회원사 일별 매매동향
member_daily = kis.stock.get_member_daily("005930", "20240101", "20240131")
```

### 3. 프로그램매매

```python
# 종목별 프로그램매매 추이(체결)
program_trade = kis.stock.get_program_trade_by_stock("005930")

# 종목별 프로그램매매 추이(일별)
program_daily = kis.stock.get_program_trade_by_stock_daily("005930", "20240101", "20240131")

# 프로그램매매 종합현황(일별)
comp_program_daily = kis.stock.get_comp_program_trade_daily("J", "20240101", "20240131")  # J:거래소, Q:코스닥, JQ:KRX

# 프로그램매매 종합현황(당일/시간별)
comp_program_today = kis.stock.get_comp_program_trade_today("J", time_div="1")  # 0:당일전체, 1:1분, 2:10분, 3:30분

# 투자자별 프로그램매매 동향(당일)
investor_program = kis.stock.get_investor_program_trade_today("J")
```

### 4. 시간외 거래

```python
# 시간외 시세
overtime_price = kis.stock.get_overtime_price("005930")

# 시간외 호가
overtime_orderbook = kis.stock.get_overtime_asking_price("005930")

# 시간외 일자별 주가
overtime_daily = kis.stock.get_daily_overtimeprice("005930", "20240101", "20240131")

# 시간외 체결 조회
overtime_trades = kis.stock.get_time_overtime_conclusion("005930")
```

### 5. 지수 정보

```python
# 업종별 지수 시세
index_category = kis.stock.get_index_category_price("0001")

# 지수 일별 가격
index_daily = kis.stock.get_index_daily_price("0001", "20240101", "20240131")

# 지수 틱 시세
index_tick = kis.stock.get_index_tick_price("0001", hour="090000")

# 지수 분/일봉 시세
index_time = kis.stock.get_index_time_price("0001", time_div="1")  # 0:30초, 1:1분, 2:10분, 3:30분, D:일봉

# 지수 분봉 차트
index_chart = kis.stock.get_time_index_chart_price("0001", period_div="1")  # 1:1분, 2:3분, 3:5분...

# KOSPI200 지수
kospi200 = kis.stock.get_kospi200_index()

# KOSPI200 선물
futures = kis.stock.get_futures_price("101W12")  # 또는 자동: get_kospi200_futures_code()
```

### 6. 기타 시세 정보

```python
# ELW 현재가
elw = kis.stock.get_elw_price("58F282")

# 변동성완화장치(VI) 현황
vi_status = kis.stock.get_vi_status("005930", input_date="20240126")

# 일별 매수매도 체결량
trade_volume = kis.stock.get_daily_trade_volume("005930", "20240101", "20240131")

# 신용잔고 일별추이
credit_balance = kis.stock.get_daily_credit_balance("005930", "20240508")

# 종목 기본정보
stock_info = kis.stock.get_stock_info("005930")

# 휴장일 조회
holiday = kis.stock.get_holiday_info("20240101")
```

### 7. 계좌 관련

```python
# 잔고 조회
balance = kis.account.get_balance()

# 주문 가능 현금 조회
cash = kis.account.get_possible_order("005930", "50000", order_type="01")

# 실현손익 조회
profit = kis.account.get_balance_rlz_pl()

# 일별 주문체결 조회
orders = kis.account.get_daily_ccld()

# 계좌 자산현황
account_balance = kis.account.get_account_balance()
```

### 8. 주문 실행

```python
# 매수 주문
buy_result = kis.order.buy("005930", quantity=10, price=70000, order_type="00")  # 00:지정가

# 매도 주문
sell_result = kis.order.sell("005930", quantity=10, price=75000, order_type="00")

# 주문 취소
cancel_result = kis.order.cancel(order_no="0000000000")

# 주문 정정
modify_result = kis.order.modify(order_no="0000000000", price=71000)
```

## 유용한 헬퍼 메서드

### API 엔드포인트 목록 확인
```python
from pykis.core.client import API_ENDPOINTS

# 모든 API 엔드포인트 확인
for key, endpoint in API_ENDPOINTS.items():
    print(f"{key}: {endpoint}")

# 특정 패턴의 엔드포인트 찾기
inquire_apis = [k for k in API_ENDPOINTS.keys() if 'INQUIRE' in k]
program_apis = [k for k in API_ENDPOINTS.keys() if 'PROGRAM' in k]
```

### 사용 가능한 메서드 확인
```python
# StockAPI의 모든 메서드 확인
import inspect
from pykis.stock.api import StockAPI

methods = [m for m in dir(StockAPI) if not m.startswith('_') and callable(getattr(StockAPI, m))]
for method in methods:
    print(f"- {method}")
    
# 메서드 상세 정보 확인
help(kis.stock.get_stock_price)
```

### 자동 날짜 처리
```python
# 많은 메서드가 날짜를 자동으로 처리합니다
# end_date 미입력시: 오늘 날짜
# start_date 미입력시: end_date 기준 30일 전

# 예시
data = kis.stock.get_daily_price("005930")  # 최근 30일
data = kis.stock.get_daily_price("005930", start_date="20240101")  # 2024-01-01부터 오늘까지
```

## 데이터 처리 팁

### DataFrame 변환
```python
import pandas as pd

# API 응답을 DataFrame으로 변환
response = kis.stock.get_stock_investor("005930")
if response and response.get("output"):
    df = pd.DataFrame(response["output"])
    print(df.head())
```

### 에러 처리
```python
try:
    price = kis.stock.get_stock_price("005930")
    if price and price.get("rt_cd") == "0":
        # 성공
        output = price.get("output")
        print(f"현재가: {output.get('stck_prpr')}")
    else:
        # API 에러
        print(f"에러: {price.get('msg1')}")
except Exception as e:
    print(f"예외 발생: {e}")
```

## 주요 파라미터 참고

### 시장 구분 코드
- `J`: 주식/거래소/KRX
- `Q`: 코스닥
- `K`: 코스피
- `NX`: KONEX
- `UN`: 통합
- `STK`: 전체
- `KSP`: 코스피
- `KSQ`: 코스닥
- `JQ`: KRX (거래소+코스닥)

### 시간 구분 코드
- `0`: 전체/30초
- `1`: 1분
- `2`: 3분/10분
- `3`: 5분/30분
- `4`: 10분
- `5`: 15분
- `6`: 30분
- `7`: 60분
- `D`: 일봉
- `W`: 주봉
- `M`: 월봉
- `Y`: 년봉

### 주문 유형
- `00`: 지정가
- `01`: 시장가
- `02`: 조건부지정가
- `03`: 최유리지정가
- `04`: 최우선지정가
- `05`: 장전 시간외
- `06`: 장후 시간외
- `07`: 시간외 단일가

## 환경 변수 설정 (.env)

```bash
# .env 파일 예시
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
KIS_ACCOUNT_NUMBER=12345678
KIS_ACCOUNT_CODE=01
KIS_ENV=prod  # 또는 dev (모의투자)
```

## 주의사항

1. **API 호출 제한**: 초당 20회 제한이 있으므로 대량 호출시 주의
2. **토큰 관리**: 토큰은 자동으로 갱신되지만, 24시간 유효
3. **시장 운영시간**: 주식시장 운영시간(09:00-15:30) 외에는 일부 API 제한
4. **데이터 지연**: 실시간이 아닌 API는 약간의 지연이 있을 수 있음

## 문제 해결

### 인증 실패
```python
# 토큰 재발급
kis.client.issue_access_token()
```

### API 응답 코드 확인
- `rt_cd == "0"`: 성공
- `rt_cd != "0"`: 실패 (msg1에 에러 메시지)

## 추가 정보

- 한국투자증권 OpenAPI 문서: https://apiportal.koreainvestment.com
- PyKIS GitHub: https://github.com/koreainvestment/pykis