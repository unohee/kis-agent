# MCP Tool Consolidation Design

## 개요

기존 110개 MCP 도구를 22개로 통합하여 LLM의 도구 선택 효율성을 향상시킵니다.

## 통합 원칙

1. **기능적 그룹핑**: 유사 기능 도구를 `query_type` 파라미터로 통합
2. **높은 가치 도구 유지**: 복합 분석 도구는 개별 유지
3. **중복 제거**: 동일/유사 기능 도구 제거
4. **명확한 네이밍**: 통합 도구 이름에 기능 범위 명시

---

## 통합 도구 설계 (22개)

### 1. stock_quote (기존 7개 → 1개)

**통합 대상:**
- get_stock_price, inquire_price, inquire_price_2
- get_orderbook_raw, inquire_ccnl, get_stock_ccnl
- inquire_time_itemconclusion

```python
@server.tool()
async def stock_quote(
    code: str,
    query_type: str = "price",  # price, detail, orderbook, execution, time_execution
    market: str = "J",
    hour: str = ""
) -> Dict[str, Any]:
    """주식 시세/호가/체결 통합 조회

    query_type:
    - price: 현재가 간단 조회
    - detail: 현재가 상세 조회
    - orderbook: 호가 10단계 조회
    - execution: 체결 정보 조회
    - time_execution: 시간별 체결 조회
    """
```

### 2. stock_chart (기존 6개 → 1개)

**통합 대상:**
- get_daily_price, inquire_daily_price
- get_intraday_price, get_minute_price
- get_daily_minute_price, inquire_minute_price

```python
@server.tool()
async def stock_chart(
    code: str,
    timeframe: str = "daily",  # minute, daily, weekly, monthly
    date: str = "",
    period: str = "D",
    count: int = 30
) -> Dict[str, Any]:
    """주식 차트 데이터 통합 조회

    timeframe:
    - minute: 분봉 (당일 또는 특정일)
    - daily: 일봉
    - weekly: 주봉
    - monthly: 월봉
    """
```

### 3. index_data (기존 6개 → 1개)

**통합 대상:**
- get_index_daily_price, inquire_index_price
- inquire_index_category_price, inquire_index_tickprice
- inquire_index_timeprice, get_index_minute_data

```python
@server.tool()
async def index_data(
    index_code: str = "0001",  # 0001=KOSPI, 1001=KOSDAQ
    data_type: str = "current",  # current, daily, tick, time, minute, category
    category: str = ""
) -> Dict[str, Any]:
    """지수 데이터 통합 조회

    data_type:
    - current: 현재 지수
    - daily: 일봉 데이터
    - tick: 틱 데이터
    - time: 시간별 데이터
    - minute: 분봉 데이터
    - category: 업종별 지수
    """
```

### 4. market_ranking (기존 7개 → 1개)

**통합 대상:**
- get_volume_power, get_top_gainers, get_market_fluctuation
- get_market_rankings, get_fluctuation_rank
- get_volume_rank, get_volume_power_rank

```python
@server.tool()
async def market_ranking(
    ranking_type: str = "volume",  # volume, gainers, losers, fluctuation, volume_power, market_status
    market: str = "0",  # 0=전체, 1=KOSPI, 2=KOSDAQ
    sign: str = "0",  # 0=전체, 1=상승, 2=보합, 3=하락
    top_n: int = 50
) -> Dict[str, Any]:
    """시장 순위 통합 조회

    ranking_type:
    - volume: 거래량 순위
    - gainers: 상승률 순위
    - losers: 하락률 순위
    - fluctuation: 등락률 순위
    - volume_power: 체결강도 순위
    - market_status: 시장 전체 등락 현황
    """
```

### 5. investor_flow (기존 10개 → 1개)

**통합 대상:**
- get_stock_investor, get_investor_daily_by_market
- get_investor_time_by_market, get_foreign_broker_net_buy
- get_frgnmem_pchs_trend, get_frgnmem_trade_estimate
- get_frgnmem_trade_trend, get_investor_trade_by_stock_daily
- get_investor_trend_estimate, get_investor_program_trade_today

```python
@server.tool()
async def investor_flow(
    query_type: str,  # stock, market_daily, market_time, foreign_trend, institutional
    code: str = "",
    market: str = "0",
    start_date: str = "",
    end_date: str = "",
    investor_type: str = "1000"  # 1000=개인, 9000=외국인
) -> Dict[str, Any]:
    """투자자 매매동향 통합 조회

    query_type:
    - stock: 종목별 투자자 동향
    - market_daily: 시장별 일별 동향
    - market_time: 시장별 시간대별 동향
    - foreign_trend: 외국인 매수 추세
    - institutional: 기관 동향
    - stock_daily: 종목별 일별 투자자 동향
    """
```

### 6. broker_trading (기존 3개 → 1개)

**통합 대상:**
- get_stock_member, get_member_transaction, get_member

```python
@server.tool()
async def broker_trading(
    code: str,
    query_type: str = "current",  # current, period, info
    start_date: str = "",
    end_date: str = ""
) -> Dict[str, Any]:
    """증권사 매매동향 통합 조회

    query_type:
    - current: 현재 증권사별 매매
    - period: 기간별 증권사 거래
    - info: 회원사 정보
    """
```

### 7. program_trading (기존 5개 → 1개)

**통합 대상:**
- get_program_trade_by_stock, get_program_trade_daily_summary
- get_program_trade_market_daily, get_program_trade_hourly_trend
- get_program_trade_period_detail

```python
@server.tool()
async def program_trading(
    query_type: str,  # stock, daily_summary, market, hourly, period
    code: str = "",
    start_date: str = "",
    end_date: str = ""
) -> Dict[str, Any]:
    """프로그램 매매 통합 조회

    query_type:
    - stock: 종목별 프로그램 매매
    - daily_summary: 일별 요약
    - market: 시장 전체 일별
    - hourly: 시간대별 추세
    - period: 기간별 상세
    """
```

### 8. account_query (기존 11개 → 1개)

**통합 대상:**
- get_account_balance, get_possible_order_amount
- get_account_order_quantity, inquire_daily_ccld
- inquire_balance_rlz_pl, inquire_psbl_sell
- inquire_period_trade_profit, inquire_intgr_margin
- inquire_credit_psamount, inquire_period_rights
- get_total_asset

```python
@server.tool()
async def account_query(
    query_type: str,  # balance, positions, order_ability, trades, profit_loss, margin, total, credit, rights
    code: str = "",
    price: str = "",
    start_date: str = "",
    end_date: str = ""
) -> Dict[str, Any]:
    """계좌 정보 통합 조회

    query_type:
    - balance: 계좌 잔고
    - positions: 보유 종목
    - order_ability: 주문 가능 금액/수량
    - trades: 체결 내역
    - profit_loss: 평가/실현 손익
    - margin: 증거금
    - total: 총자산
    - credit: 신용 거래 가능
    - rights: 권리 정보
    """
```

### 9. order_execute (기존 6개 → 1개)

**통합 대상:**
- order_stock_cash, order_stock_credit
- order_cash, order_cash_sor
- order_credit_buy, order_credit_sell

```python
@server.tool()
async def order_execute(
    action: str,  # buy, sell
    code: str,
    quantity: str,
    price: str = "0",
    order_type: str = "00",  # 00=지정가, 01=시장가
    credit: bool = False,
    credit_type: str = "21",  # 21=자기융자, 22=유통융자
    loan_date: str = ""
) -> Dict[str, Any]:
    """주문 실행 통합

    action: buy(매수), sell(매도)
    credit: True면 신용 주문
    """
```

### 10. order_manage (기존 5개 → 1개)

**통합 대상:**
- order_rvsecncl, order_resv
- order_resv_rvsecncl, order_resv_ccnl
- inquire_psbl_rvsecncl

```python
@server.tool()
async def order_manage(
    action: str,  # modify, cancel, reserve, reserve_modify, reserve_cancel_all, list_pending
    order_no: str = "",
    code: str = "",
    quantity: str = "",
    price: str = "",
    order_type: str = "00"
) -> Dict[str, Any]:
    """주문 관리 통합 (정정/취소/예약)

    action:
    - modify: 주문 정정
    - cancel: 주문 취소
    - reserve: 예약 주문
    - reserve_modify: 예약 정정/취소
    - reserve_cancel_all: 예약 전체 취소
    - list_pending: 정정/취소 가능 목록
    """
```

### 11. stock_info (기존 6개 → 1개)

**통합 대상:**
- get_stock_info, get_stock_basic, get_stock_financial
- get_pbar_tratio, get_asking_price_exp_ccn, inquire_vi_status

```python
@server.tool()
async def stock_info(
    code: str,
    info_type: str = "basic"  # basic, detail, financial, buy_sell_ratio, expected_execution, vi_status
) -> Dict[str, Any]:
    """종목 정보 통합 조회

    info_type:
    - basic: 기본 정보
    - detail: 상세 정보
    - financial: 재무 정보
    - buy_sell_ratio: 매수/매도 비율
    - expected_execution: 호가 예상 체결
    - vi_status: VI 발동 상태
    """
```

### 12. overtime_trading (기존 3개 → 1개)

**통합 대상:**
- inquire_daily_overtimeprice, inquire_overtime_price
- inquire_overtime_asking_price

```python
@server.tool()
async def overtime_trading(
    code: str,
    query_type: str = "current"  # current, daily, orderbook
) -> Dict[str, Any]:
    """시간외 거래 통합 조회

    query_type:
    - current: 현재가
    - daily: 일별 시세
    - orderbook: 호가
    """
```

### 13. derivatives (기존 3개 → 1개)

**통합 대상:**
- get_kospi200_futures_code, get_future_option_price, inquire_elw_price

```python
@server.tool()
async def derivatives(
    product_type: str,  # futures_code, futures_price, elw
    code: str = ""
) -> Dict[str, Any]:
    """파생상품 조회

    product_type:
    - futures_code: KOSPI200 선물 종목코드
    - futures_price: 선물옵션 가격
    - elw: ELW 시세
    """
```

### 14. interest_stocks (기존 3개 → 1개)

**통합 대상:**
- get_condition_stocks, get_interest_group_list, get_interest_stock_list

```python
@server.tool()
async def interest_stocks(
    query_type: str,  # condition, groups, stocks
    user_id: str,
    group_code: str = "",
    seq: int = 0
) -> Dict[str, Any]:
    """관심종목/조건검색 조회

    query_type:
    - condition: 조건검색식 종목
    - groups: 관심종목 그룹 목록
    - stocks: 그룹별 종목 목록
    """
```

### 15. utility (기존 3개 → 1개)

**통합 대상:**
- get_holiday_info, is_holiday, get_daily_credit_balance

```python
@server.tool()
async def utility(
    action: str,  # holiday_info, is_holiday, credit_balance
    date: str = "",
    code: str = ""
) -> Dict[str, Any]:
    """유틸리티 기능 통합

    action:
    - holiday_info: 휴장일 정보
    - is_holiday: 특정일 휴장 여부
    - credit_balance: 신용잔고 일별추이
    """
```

### 16. data_management (기존 4개 → 1개)

**통합 대상:**
- fetch_minute_data, calculate_support_resistance
- init_minute_db, migrate_minute_csv_to_db

```python
@server.tool()
async def data_management(
    action: str,  # fetch_minute, support_resistance, init_db, migrate_csv
    code: str,
    date: str = "",
    cache_dir: str = "minute_data",
    csv_dir: str = "",
    db_path: str = ""
) -> Dict[str, Any]:
    """데이터 관리 통합

    action:
    - fetch_minute: 4일간 분봉 수집
    - support_resistance: 지지/저항선 계산
    - init_db: 분봉 DB 초기화
    - migrate_csv: CSV → DB 마이그레이션
    """
```

### 17. rate_limiter (기존 4개 → 1개)

**통합 대상:**
- get_rate_limiter_status, reset_rate_limiter
- set_rate_limits, enable_adaptive_rate_limiting

```python
@server.tool()
async def rate_limiter(
    action: str,  # status, reset, set_limits, set_adaptive
    requests_per_second: int = None,
    requests_per_minute: int = None,
    min_interval_ms: int = None,
    enable_adaptive: bool = None
) -> Dict[str, Any]:
    """Rate Limiter 관리 통합

    action:
    - status: 현재 상태 조회
    - reset: 상태 초기화
    - set_limits: 제한 값 설정
    - set_adaptive: 적응형 활성화/비활성화
    """
```

### 18. method_discovery (기존 3개 → 1개)

**통합 대상:**
- search_methods, get_all_methods, show_method_usage

```python
@server.tool()
async def method_discovery(
    action: str,  # search, list_all, usage
    query: str = "",
    method_name: str = ""
) -> Dict[str, Any]:
    """Agent 메서드 탐색 통합

    action:
    - search: 키워드로 메서드 검색
    - list_all: 전체 메서드 목록
    - usage: 특정 메서드 사용법
    """
```

### 19-22. 복합 분석 도구 (개별 유지)

높은 가치의 복합 분석 도구는 개별 유지:

```python
# 19. analyze_broker_accumulation - 증권사 매집 분석
# 20. analyze_foreign_institutional_flow - 외국인/기관 동시 순매수
# 21. detect_volume_spike - 거래량 급등 탐지
# 22. find_price_momentum - 가격 모멘텀 탐색
```

### 추가: 오케스트레이션 도구 (개별 유지)

메타 도구로서 개별 유지:
- get_tool_registry
- plan_query_execution
- suggest_tool_combination

---

## 통합 전후 비교

| 카테고리 | 기존 | 통합 후 |
|----------|------|---------|
| 주식 시세/호가 | 7개 | 1개 (stock_quote) |
| 주식 차트 | 6개 | 1개 (stock_chart) |
| 지수 데이터 | 6개 | 1개 (index_data) |
| 시장 순위 | 7개 | 1개 (market_ranking) |
| 투자자 동향 | 10개 | 1개 (investor_flow) |
| 증권사 거래 | 3개 | 1개 (broker_trading) |
| 프로그램 매매 | 5개 | 1개 (program_trading) |
| 계좌 조회 | 11개 | 1개 (account_query) |
| 주문 실행 | 6개 | 1개 (order_execute) |
| 주문 관리 | 5개 | 1개 (order_manage) |
| 종목 정보 | 6개 | 1개 (stock_info) |
| 시간외 거래 | 3개 | 1개 (overtime_trading) |
| 파생상품 | 3개 | 1개 (derivatives) |
| 관심종목 | 3개 | 1개 (interest_stocks) |
| 유틸리티 | 3개 | 1개 (utility) |
| 데이터 관리 | 4개 | 1개 (data_management) |
| Rate Limiter | 4개 | 1개 (rate_limiter) |
| 메서드 탐색 | 3개 | 1개 (method_discovery) |
| 복합 분석 | 5개 | 4개 (개별 유지) |
| 오케스트레이션 | 3개 | 3개 (개별 유지) |
| **합계** | **~110개** | **~25개** |

---

## 구현 계획

### Phase 3.3: 통합 도구 구현

1. `consolidated_tools.py` 파일 생성
2. 각 통합 도구 구현 (query_type 분기 로직)
3. 기존 도구와의 호환성 유지 (deprecated 래퍼)

### Phase 3.4: 테스트

1. 각 통합 도구의 모든 query_type 테스트
2. 기존 도구와 결과 비교
3. LLM 도구 선택 효율성 검증

---

## 주의사항

1. **하위 호환성**: 기존 도구명은 deprecated 래퍼로 유지
2. **에러 처리**: 통합 도구 내 각 분기에서 적절한 에러 처리
3. **문서화**: 각 query_type에 대한 명확한 docstring
