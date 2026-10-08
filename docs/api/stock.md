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

## 공식 API 확장 (2.0.0)

2.0.0에서 공식 문서의 국내주식 API를 모두 래핑했습니다. 아래 메서드는 `agent.stock`에서 바로 호출합니다 (`StockAPI`가 메뉴별 하위 API로 자동 위임). 모의투자 지원 여부는 API마다 다르며, 미지원 API를 모의투자에서 호출하면 `PaperTradingNotSupportedError`가 발생합니다.

### 순위분석

| 메서드 | 설명 |
|:---|:---|
| `agent.stock.get_after_hour_balance_rank()` | 국내주식 시간외잔량 순위 [v1_국내주식-093] |
| `agent.stock.get_bulk_trans_num_rank()` | 국내주식 대량체결건수 상위 [국내주식-107] |
| `agent.stock.get_credit_balance_rank()` | 국내주식 신용잔고 상위 [국내주식-109] |
| `agent.stock.get_exp_trans_updown_rank()` | 국내주식 예상체결 상승/하락상위 [v1_국내주식-103] |
| `agent.stock.get_finance_ratio_rank()` | 국내주식 재무비율 순위 [v1_국내주식-092] |
| `agent.stock.get_hts_top_view_rank()` | HTS조회상위20종목 [국내주식-214] |
| `agent.stock.get_market_value_rank()` | 국내주식 시장가치 순위 [v1_국내주식-096] |
| `agent.stock.get_near_new_highlow_rank()` | 국내주식 신고/신저근접종목 상위 [v1_국내주식-105] |
| `agent.stock.get_overtime_exp_trans_fluct_rank()` | 국내주식 시간외예상체결등락률 [국내주식-140] |
| `agent.stock.get_overtime_fluctuation_rank()` | 국내주식 시간외등락율순위 [국내주식-138] |
| `agent.stock.get_overtime_volume_rank()` | 국내주식 시간외거래량순위 [국내주식-139] |
| `agent.stock.get_prefer_disparate_ratio_rank()` | 국내주식 우선주/괴리율 상위 [v1_국내주식-094] |
| `agent.stock.get_profit_asset_index_rank()` | 국내주식 수익자산지표 순위 [v1_국내주식-090] |
| `agent.stock.get_quote_balance_rank()` | 국내주식 호가잔량 순위 [국내주식-089] |
| `agent.stock.get_top_interest_stock_rank()` | 국내주식 관심종목등록 상위 [v1_국내주식-102] |
| `agent.stock.get_traded_by_company_rank()` | 국내주식 당사매매종목 상위 [v1_국내주식-104] |

### 시세분석

| 메서드 | 설명 |
|:---|:---|
| `agent.stock.get_capture_uplowprice()` | 국내주식 상하한가 포착 [국내주식-190] |
| `agent.stock.get_daily_loan_trans()` | 종목별 일별 대차거래추이 [국내주식-135] |
| `agent.stock.get_daily_short_sale(code)` | 국내주식 공매도 일별추이 [국내주식-134] |
| `agent.stock.get_daily_trade_volume(code)` | 종목별일별매수매도체결량 [v1_국내주식-056] |
| `agent.stock.get_exp_price_trend(code)` | 국내주식 예상체결가 추이 [국내주식-118] |
| `agent.stock.get_investor_time_by_market()` | 시장별 투자자매매동향(시세) [v1_국내주식-074] |
| `agent.stock.get_mktfunds()` | 국내 증시자금 종합 [국내주식-193] |
| `agent.stock.get_tradprt_byamt(code)` | 국내주식 체결금액별 매매비중 [국내주식-192] |

### 종목정보·재무

| 메서드 | 설명 |
|:---|:---|
| `agent.stock.get_balance_sheet(code)` | 국내주식 대차대조표 [v1_국내주식-078] |
| `agent.stock.get_credit_by_company()` | 국내주식 당사 신용가능종목 [국내주식-111] |
| `agent.stock.get_estimate_perform(code)` | 국내주식 종목추정실적 [국내주식-187] |
| `agent.stock.get_growth_ratio(code)` | 국내주식 성장성비율 [v1_국내주식-085] |
| `agent.stock.get_income_statement(code)` | 국내주식 손익계산서 [v1_국내주식-079] |
| `agent.stock.get_invest_opinion(code)` | 국내주식 종목투자의견 [국내주식-188] |
| `agent.stock.get_invest_opinion_by_sec(member_code)` | 국내주식 증권사별 투자의견 [국내주식-189] |
| `agent.stock.get_lendable_by_company()` | 당사 대주가능 종목 [국내주식-195] |
| `agent.stock.get_other_major_ratios(code)` | 국내주식 기타주요비율 [v1_국내주식-082] |
| `agent.stock.get_profit_ratio(code)` | 국내주식 수익성비율 [v1_국내주식-081] |
| `agent.stock.get_search_info(code)` | 상품기본조회 [v1_국내주식-029] |
| `agent.stock.get_stability_ratio(code)` | 국내주식 안정성비율 [v1_국내주식-083] |

### 예탁원 일정

| 메서드 | 설명 |
|:---|:---|
| `agent.stock.get_ksd_bonus_issue()` | 예탁원정보(무상증자일정) [국내주식-144] |
| `agent.stock.get_ksd_cap_dcrs()` | 예탁원정보(자본감소일정) [국내주식-149] |
| `agent.stock.get_ksd_dividend()` | 예탁원정보(배당일정) [국내주식-145] |
| `agent.stock.get_ksd_forfeit()` | 예탁원정보(실권주일정) [국내주식-152] |
| `agent.stock.get_ksd_list_info()` | 예탁원정보(상장정보일정) [국내주식-150] |
| `agent.stock.get_ksd_mand_deposit()` | 예탁원정보(의무예치일정) [국내주식-153] |
| `agent.stock.get_ksd_merger_split()` | 예탁원정보(합병/분할일정) [국내주식-147] |
| `agent.stock.get_ksd_paidin_capin()` | 예탁원정보(유상증자일정) [국내주식-143] |
| `agent.stock.get_ksd_pub_offer()` | 예탁원정보(공모주청약일정) [국내주식-151] |
| `agent.stock.get_ksd_purreq()` | 예탁원정보(주식매수청구일정) [국내주식-146] |
| `agent.stock.get_ksd_rev_split()` | 예탁원정보(액면교체일정) [국내주식-148] |
| `agent.stock.get_ksd_sharehld_meet()` | 예탁원정보(주주총회일정) [국내주식-154] |

### 분봉·시간외

| 메서드 | 설명 |
|:---|:---|
| `agent.stock.get_exp_closing_price()` | 국내주식 장마감 예상체결가 [국내주식-120] |
| `agent.stock.get_overtime_conclusion_by_time(code)` | 주식현재가 시간외시간별체결 [v1_국내주식-025] |
| `agent.stock.get_today_minute_chart(code)` | 주식당일분봉조회 [v1_국내주식-022] |

업종 현재지수(`get_index_price`), 예상체결 지수(`get_exp_index_trend`, `get_exp_total_index`), 금리 종합(`get_comp_interest`), 프로그램매매 종합현황(`get_comp_program_trade_today`)도 추가됐습니다. ETF/ETN은 [ETF/ETN API](etf.md)를 보세요.
