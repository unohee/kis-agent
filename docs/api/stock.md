# 국내 주식 API

`agent.stock_api` 또는 `agent` 직접 호출로 접근합니다. 내부적으로 `StockAPI` Facade가 `StockPriceAPI`, `StockMarketAPI`, `StockInvestorAPI`에 위임합니다.

## 시세 조회

### 현재가

```python
price = agent.get_stock_price("005930")
# market 파라미터: "J"=KRX(기본), "NX"=NXT, "UN"=통합
price_nxt = agent.get_stock_price("005930", market="NX")
```

### 일별 시세 (최근 30건)

```python
daily = agent.stock_api.inquire_daily_price("005930", period="D", org_adj_prc="1")
```

### 기간별 시세 (날짜 범위 지정)

```python
daily = agent.inquire_daily_itemchartprice(
    "005930", start_date="20250101", end_date="20251231", period="D"
)
```

### 장기 데이터 (100건 제한 자동 우회)

```python
result = agent.get_daily_price_all(
    code="005930", start_date="20200102", end_date="20201230",
    period="D", org_adj_prc="1"
)
print(f"총 {len(result['output2'])}건, API 호출 {result['_pagination_info']['total_calls']}회")
```

### 분봉 데이터

```python
# 당일 전체 분봉
intraday = agent.stock_api.get_intraday_price("005930")

# 특정일 전체 분봉 (내부 페이지네이션)
minute = agent.stock_api.get_daily_minute_price("005930", "20250610")
```

### 호가 조회

```python
orderbook = agent.get_orderbook("005930")
orderbook_raw = agent.stock_api.get_orderbook_raw("005930")  # 원시 데이터
```

### 체결 데이터

```python
ccnl = agent.stock_api.inquire_ccnl("005930")           # 최근 30건 체결
ccnl = agent.stock_api.get_stock_ccnl("005930")         # 체결 조회
time_ccnl = agent.stock_api.inquire_time_itemconclusion("005930")  # 시간대별 체결
```

### 복수종목 현재가

```python
prices = agent.stock_api.intstock_multprice("005930,000660,035420")
```

### 시세 추가 정보

```python
price2 = agent.stock_api.inquire_price("005930")     # 시세 (추가 정보)
price3 = agent.stock_api.inquire_price_2("005930")   # 시세2
```

## 지수 조회

```python
# 업종 현재 지수
index = agent.stock_api.inquire_index_timeprice("0001")   # KOSPI
index = agent.stock_api.inquire_index_timeprice("1001")   # KOSDAQ

# 업종 분봉/일봉 차트
chart = agent.stock_api.get_time_index_chart_price("0001", "4")  # KOSPI 10분봉(=일봉 30일)

# 업종 분봉 데이터
minute = agent.stock_api.get_index_minute_data("0001", "120")

# 업종 틱 데이터
tick = agent.stock_api.inquire_index_tickprice("0001")

# 업종별 전체시세
cat = agent.stock_api.inquire_index_category_price("0001")
```

## 시장 정보

```python
# 시장 변동성
fluct = agent.stock_api.get_market_fluctuation()

# 거래량 기준 순위
rank = agent.stock_api.get_market_rankings(volume=5000000)

# 체결강도 순위
power = agent.stock_api.get_volume_power()

# 종목 기본정보
info = agent.stock_api.get_stock_info("005930")

# 종목 기본정보 (상세)
info = agent.stock_api.search_stock_info("005930")

# 시가총액 조회
mktcap = agent.stock_api.market_value("005930")

# 거래시간 조회
time = agent.stock_api.market_time()

# 휴장일 확인
is_hol = agent.stock_api.is_holiday("20260410")
holiday = agent.stock_api.get_holiday_info("20260401")
```

## 순위 조회

```python
# 등락률 순위
fluct = agent.stock_api.fluctuation()
rank = agent.stock_api.get_fluctuation_rank()

# 거래량 순위
vol = agent.stock_api.volume_rank()
vol2 = agent.stock_api.get_volume_rank()

# 체결강도 순위
power = agent.stock_api.get_volume_power_rank()

# 시가총액 순위
cap = agent.stock_api.market_cap()

# 이격도 순위
disp = agent.stock_api.disparity()

# 공매도 상위
short = agent.stock_api.short_sale()

# 배당률 순위
div = agent.stock_api.dividend_rate()

# 외국인/기관 종합
fi = agent.stock_api.foreign_institution_total()
```

## 투자자 정보

```python
# 투자자별 매매동향
investor = agent.stock_api.get_stock_investor("005930")

# 거래원별 매매
member = agent.stock_api.get_stock_member("005930")

# 특정 거래원 매매 내역
mem_tx = agent.stock_api.get_member_transaction("005930", "ABN001")

# 외국인 매수 추이
frgn = agent.stock_api.get_frgnmem_pchs_trend("005930")

# 외국계 증권사 순매수 집계
net_buy = agent.stock_api.get_foreign_broker_net_buy("005930")

# 외국계 매매종목 가집계
estimate = agent.stock_api.get_frgnmem_trade_estimate()

# 회원사 실시간 매매동향(틱)
trend = agent.stock_api.get_frgnmem_trade_trend()

# 프로그램매매 투자자동향 (당일)
pgm = agent.stock_api.get_investor_program_trade_today()

# 종목별 투자자매매동향 (일별)
daily = agent.stock_api.get_investor_trade_by_stock_daily(fid_input_iscd="005930")

# 종목별 외국인/기관 추정가집계
est = agent.stock_api.get_investor_trend_estimate("005930")
```

## 기타

```python
# 선물옵션 시세 (StockPriceAPI 내장)
fop = agent.stock_api.get_future_option_price("F")

# 시간외 체결
ot = agent.stock_api.inquire_daily_overtimeprice("005930")

# 시간외 호가
ot_ask = agent.stock_api.inquire_overtime_asking_price("005930")

# 시간외 현재가
ot_price = agent.stock_api.inquire_overtime_price("005930")

# ELW 시세
elw = agent.stock_api.inquire_elw_price("580001")

# VI 현황
vi = agent.stock_api.inquire_vi_status()

# 매물대/거래비중
pbar = agent.stock_api.get_pbar_tratio("005930")

# 일자별 신용잔고
credit = agent.stock_api.daily_credit_balance("005930")

# 뉴스 제목
news = agent.stock_api.news_title("005930")

# 업종 수익/자산 지수
pai = agent.stock_api.profit_asset_index("0001")
```

## API 메서드 요약

### 시세/차트

| 메서드 | 설명 |
|:---|:---|
| `get_stock_price(code, market)` | 현재가 |
| `inquire_daily_price(code, period)` | 일별 시세 (30건) |
| `inquire_daily_itemchartprice(...)` | 기간별 시세 |
| `get_daily_price_all(...)` | 장기 데이터 (100건 우회) |
| `get_intraday_price(code)` | 당일 전체 분봉 |
| `get_daily_minute_price(code, date)` | 특정일 분봉 |
| `get_orderbook(code)` | 호가 10호가 |
| `inquire_ccnl(code)` | 체결 (30건) |
| `intstock_multprice(codes)` | 복수종목 현재가 |

### 지수

| 메서드 | 설명 |
|:---|:---|
| `inquire_index_timeprice(index, market)` | 지수 분/일봉 |
| `get_time_index_chart_price(index, period)` | 지수 차트 |
| `get_index_minute_data(index)` | 업종 분봉 |
| `inquire_index_category_price(index)` | 업종별 전체시세 |

### 시장정보

| 메서드 | 설명 |
|:---|:---|
| `get_stock_info(ticker)` | 종목 기본정보 |
| `market_time()` | 거래시간 |
| `is_holiday(date)` | 휴장일 여부 |
| `market_value(code)` | 시가총액 |

### 순위

| 메서드 | 설명 |
|:---|:---|
| `fluctuation()` | 등락률 순위 |
| `volume_rank()` | 거래량 순위 |
| `market_cap()` | 시가총액 순위 |
| `disparity()` | 이격도 순위 |
| `short_sale()` | 공매도 상위 |
| `dividend_rate()` | 배당률 순위 |
| `foreign_institution_total()` | 외국인/기관 종합 |

### 투자자 정보

| 메서드 | 설명 |
|:---|:---|
| `get_stock_investor(ticker)` | 투자자별 매매동향 |
| `get_stock_member(ticker)` | 거래원별 매매 |
| `get_frgnmem_pchs_trend(code)` | 외국인 매수 추이 |
| `get_foreign_broker_net_buy(code)` | 외국계 순매수 |
| `get_investor_program_trade_today()` | 프로그램매매 동향 |
| `get_investor_trend_estimate(code)` | 외국인/기관 추정 |
