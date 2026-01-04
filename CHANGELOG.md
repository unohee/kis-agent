# Changelog

모든 주목할 만한 변경사항이 이 파일에 문서화됩니다.

## [1.4.0] - 2026-01-04

### 🚀 주요 변경사항

#### MCP 도구 통합 (110+ → 18개)

MCP 서버의 110개 이상의 개별 도구를 **18개의 통합 도구**로 재구성했습니다. 이를 통해:
- AI 에이전트의 도구 선택 정확도 향상 (도구 수 86% 감소)
- 파라미터 기반 유연한 쿼리 지원
- 일관된 응답 형식 (rt_cd, msg1, output 구조)

**통합된 18개 도구:**

| 도구 | 설명 | 지원 쿼리 |
|-----|------|----------|
| `stock_quote` | 주식 시세/호가/체결 조회 | price, detail, orderbook, execution |
| `stock_chart` | 차트 데이터 조회 | minute, daily, weekly, monthly |
| `index_data` | 지수 데이터 조회 | current, daily, tick, time, minute |
| `market_ranking` | 시장 순위 조회 | volume, gainers, losers, fluctuation |
| `investor_flow` | 투자자 매매동향 | stock, market_daily, foreign_trend |
| `broker_trading` | 증권사 매매동향 | current, period, info |
| `program_trading` | 프로그램 매매 | stock, daily_summary, market, hourly |
| `account_query` | 계좌 정보 조회 | balance, order_ability, trades, profit_loss |
| `order_execute` | 주문 실행 | buy, sell |
| `order_manage` | 주문 관리 | modify, cancel, reserve |
| `stock_info` | 종목 정보 | basic, detail, financial, vi_status |
| `overtime_trading` | 시간외 거래 | current, daily, orderbook |
| `derivatives` | 파생상품 조회 | futures_code, futures_price, elw |
| `interest_stocks` | 관심종목/조건검색 | condition, groups, stocks |
| `rate_limiter` | Rate Limiter 관리 | status, reset, set_limits |
| `method_discovery` | 메서드 탐색 | search, list_all, usage |
| `utility` | 유틸리티 기능 | holiday_info, is_holiday, credit_balance |
| `data_management` | 데이터 관리 | fetch_minute, support_resistance, init_db |

#### LOC 게이트 준수 (모든 파일 < 1500줄)

CI/CD 파이프라인에 LOC (Lines of Code) 게이트를 추가하여 코드 품질을 보장합니다:
- 모든 소스 파일 1500줄 미만 유지
- 대형 파일 자동 분할 권장
- 커밋 시 자동 검증

**분할된 주요 파일:**
- `account/api.py` (2,019줄) → `balance_api.py`, `order_api.py`, `profit_api.py`, `credit_api.py`
- `stock/api_facade.py` (1,600줄) → 위임 패턴으로 최적화

### 🐛 버그 수정

#### MCP 도구 버그 수정 (3건)

1. **rate_limiter 도구**
   - 문제: Agent 메서드들이 API 응답 형식(rt_cd, msg1)이 아닌 Dict/None 반환
   - 수정: validate_api_response 대신 직접 응답 형식 생성

2. **method_discovery 도구**
   - 문제: get_all_methods()는 list, show_method_usage()는 None 반환
   - 수정: 직접 응답 형식 생성 및 메서드 정보 조회 방식 개선

3. **utility/holiday_info**
   - 문제: api_facade.get_holiday_info()에 date 파라미터 누락
   - 수정: market_api.get_holiday_info(date) 시그니처와 일치하도록 수정

4. **market_ranking volume 파라미터**
   - 문제: volume 필터링 미적용
   - 수정: 거래량 필터 정상 작동

### 🔧 개선사항

#### 에러 메시지 개선
- API 응답 에러 시 msg1이 비어있으면 rt_cd/msg_cd 표시
- 디버깅 용이성 향상

#### CI/CD 개선
- LOC 게이트 자동 검증 추가
- Pre-commit hook에 LOC 검사 통합
- 의존성 분석 도구 추가

### 📊 통계
- **MCP 도구**: 110+ → 18개 (86% 감소)
- **테스트**: 232개 통과 (52% 커버리지)
- **LOC 준수**: 모든 파일 < 1500줄

### ⚠️ 마이그레이션 안내

기존 MCP 도구를 사용하던 경우 `docs/MIGRATION_v1.4.0.md` 참조.

---

## [1.3.6] - 2025-12-18

### 🐛 버그 수정

#### StockPriceAPI에 누락된 재무/기본정보 메서드 추가

신형 facade 구조(`StockPriceAPI`)에서 누락되었던 재무정보 및 기본정보 조회 메서드를 추가했습니다.

**추가된 메서드 (3개):**

1. **`get_stock_financial(code)`** - 분기별 재무비율 조회
   - 최근 30개 분기 재무지표 반환
   - ROE, EPS, BPS, 영업이익률, 순이익률, 유보율, 부채비율 등 10개 필드
   - TR_ID: `FHKST66430300`
   ```python
   financial = agent.get_stock_financial("005930")
   latest = financial['output'][0]  # 최신 분기
   print(f"ROE: {latest['roe_val']}%, EPS: {latest['eps']}원")
   ```

2. **`get_stock_basic(code)`** - 종목 기본정보 조회
   - 상장주식수, 시가총액, 액면가 등 67개 필드
   - TR_ID: `CTPF1002R`
   ```python
   basic = agent.get_stock_basic("005930")
   print(f"시가총액: {basic['output']['hts_avls']}")
   ```

3. **`get_stock_member(ticker)`** - 회원사 정보 조회
   - 증권사별 매매 동향
   - TR_ID: `FHKST01010600`
   - `get_member()` 별칭 함께 제공
   ```python
   member = agent.get_stock_member("005930")
   ```

**변경 이유:**
- legacy `api.py`에만 존재하던 메서드가 신형 facade 구조에서 누락
- `Agent` → `StockAPI` facade → `StockPriceAPI` delegation 체인에서 `AttributeError` 발생
- `__getattr__` delegation을 통해 자동으로 모든 메서드 접근 가능

**관련 이슈:** [링크 추가 예정]

## [1.3.5] - 2025-12-12

### 🆕 신규 기능

#### NXT(대체거래시스템) WebSocket 실시간 구독 지원

한국거래소 대체거래시스템(NXT) 실시간 데이터 구독 기능을 추가했습니다.

**추가된 구독 타입 (6개):**

| 타입 | TR_ID | 설명 |
|------|-------|------|
| `STOCK_TRADE_NXT` | H0NXCNT0 | NXT 실시간 체결가 |
| `STOCK_ASK_BID_NXT` | H0NXASP0 | NXT 실시간 호가 |
| `STOCK_EXPECTED_NXT` | H0NXANC0 | NXT 실시간 예상체결 |
| `PROGRAM_TRADE_NXT` | H0NXPGM0 | NXT 프로그램매매 |
| `MARKET_OPERATION_NXT` | H0NXMKO0 | NXT 장운영정보 |
| `MEMBER_TRADE_NXT` | H0NXMBC0 | NXT 회원사매매 |

**편의 메서드:**
```python
# 단일 종목 NXT 구독 (다양한 옵션)
ws_agent.subscribe_stock_nxt(
    "005930",
    with_orderbook=True,    # 호가 포함
    with_expected=True,     # 예상체결 포함
    with_program=True,      # 프로그램매매 포함
    with_member=True,       # 회원사매매 포함
)

# 복수 종목 NXT 구독
ws_agent.subscribe_stocks_nxt(["005930", "035420", "000660"])

# NXT 장운영정보 구독
ws_agent.subscribe_market_operation_nxt()

# NXT 전용 구독 해제
ws_agent.unsubscribe_stock_nxt("005930")
```

**KRX/NXT 동시 구독:**
```python
# KRX (기존)
ws_agent.subscribe_stock("005930")

# NXT (신규)
ws_agent.subscribe_stock_nxt("005930")

# 두 구독이 독립적으로 공존 가능
```

**파서 지원:**
- `MARKET_OPERATION_NXT_FIELDS`: 11개 필드 정의
- `PROGRAM_TRADE_NXT_FIELDS`: 11개 필드 정의
- 모든 NXT 타입에 대한 `RealtimeDataParser.parse()` 지원

**단위 테스트:**
- 27개 테스트 추가 (`tests/unit/test_ws_agent_nxt.py`)
- 구독 타입, 구독/해제 메서드, 파서 검증

### 🔧 개선사항

#### PROGRAM_TRADE TR_ID 수정
- 기존: `H0GSCNT0` (잘못된 값)
- 수정: `H0STPGM0` (올바른 KRX 프로그램매매 TR_ID)

#### SubscriptionType enum 확장
- 새로운 타입 추가: `STOCK_EXPECTED`, `INDEX_EXPECTED`, `MEMBER_TRADE`
- docstring 상세화: 모든 구독 타입에 대한 설명 추가

### 🐛 버그 수정

#### websockets.exceptions import 안정화
- `websockets.exceptions.ConnectionClosed` 접근 시 일부 환경에서 `AttributeError` 발생하는 문제 수정
- 명시적 import로 변경: `from websockets.exceptions import ConnectionClosed`

#### 구식 주문 TR ID 업데이트
`account/api.py`의 구식 TR ID를 신규 TR ID로 업데이트:

| 주문 유형 | 구식 TR | 신규 TR |
|----------|--------|--------|
| 현금 매도 | TTTC0801U | TTTC0011U |
| 현금 매수 | TTTC0802U | TTTC0012U |
| 정정/취소 | TTTC0803U | TTTC0013U |

---

## [1.3.4] - 2025-12-11

### 🐛 버그 수정

#### 분봉 조회 API 엔드포인트 수정

`price_api.py`의 분봉 조회 메서드들이 잘못된 엔드포인트/TR ID를 사용하던 문제 수정:

| 메서드 | 수정 전 | 수정 후 |
|--------|---------|---------|
| `get_minute_price` | TR: `FHKST01010300` | TR: `FHKST03010200` |
| `get_daily_minute_price` | `INQUIRE_TIME_ITEMCHARTPRICE` | `INQUIRE_TIME_DAILYCHARTPRICE` |
| `get_daily_minute_price` | TR: `FHKST01010300` | TR: `FHKST03010230` |

**수정 내용:**
- `get_minute_price()`: 주식당일분봉조회 API로 올바르게 연결
  - 엔드포인트: `/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice`
  - TR ID: `FHKST03010200`
- `get_daily_minute_price()`: 일별분봉시세조회 API로 올바르게 연결
  - 엔드포인트: `/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice`
  - TR ID: `FHKST03010230`

---

## [1.3.3] - 2025-12-10

### 🆕 신규 기능

#### 국내 지수 일자별 시세 조회 API 추가
- `get_index_daily_price()` 메서드를 `StockPriceAPI`에 추가
- KOSPI, KOSDAQ, KOSPI200 등 주요 지수의 일별/주별/월별 시세 조회 지원
- 베타 계산 및 시장 상관관계 분석에 활용 가능

**사용 예시:**
```python
# KOSPI 일별 시세 조회
result = agent.stock.get_index_daily_price("0001")

# KOSDAQ 특정 일자까지 시세
result = agent.stock.get_index_daily_price("1001", "20251210")

# KOSPI200 월별 시세
result = agent.stock.get_index_daily_price("2001", period="M")
```

**지수 코드:**
- `0001`: KOSPI
- `1001`: KOSDAQ
- `2001`: KOSPI200

**TR ID:** FHPUP02120000

### ⚠️ Deprecation

#### 레거시 WebSocket 클라이언트 Deprecated
- `pykis/websocket/client.py` (KISWebSocketClient) - deprecated
- `pykis/websocket/enhanced_client.py` (EnhancedKISWebSocketClient) - deprecated
- **권장**: `WSAgent` 사용 (`pykis/websocket/ws_agent.py`)

```python
# 기존 (deprecated)
from pykis.websocket import KISWebSocketClient

# 권장 (신규)
ws_client = agent.websocket(stock_codes=["005930"])
```

---

## [1.3.2] - 2025-12-08

### 🔧 WebSocket 안정성 대폭 개선

#### 🐛 Critical Bug Fix: 구독 교착 상태 해결

**문제 상황**
- 대량 종목(40개+) 구독 시 구독 응답 타임아웃 발생
- 첫 구독 요청 후 10초 내에 연결 종료
- 재연결 시도해도 동일 패턴 반복

**원인 분석**
- `connect()` 메서드의 **교착 상태(deadlock)** 아키텍처 결함:
  1. 웹소켓 연결 후 `_subscribe_all()` 호출 (블로킹)
  2. `_subscribe_all()` 내에서 `asyncio.Event().wait()`으로 응답 대기
  3. 응답은 메시지 수신 루프에서 처리되어야 함
  4. 수신 루프는 `_subscribe_all()` 완료 후에야 시작 → **영원히 타임아웃**

**해결 방법**
- 메시지 수신 루프를 별도 `asyncio.Task`로 **먼저 시작**
- 구독 요청과 메시지 수신이 **병렬로 실행**되도록 아키텍처 개선
- 새로운 `_receive_loop()` 메서드 추가

```python
# 수정 전 (교착 상태)
await self._subscribe_all()  # 블로킹
while True:  # 수신 루프 (도달 불가)
    data = await websocket.recv()

# 수정 후 (병렬 실행)
receive_task = asyncio.create_task(self._receive_loop(websocket))
await asyncio.sleep(0.1)
await self._subscribe_all()  # 응답 수신 가능
await receive_task
```

#### ✅ 테스트 결과
- **40개 종목 구독**: 성공 40개, 실패 0개
- **총 구독 시간**: ~12초 (안정적)
- **단위 테스트**: 65 passed, 6 skipped, 0 failed

#### 📁 수정된 파일
- `pykis/websocket/ws_agent.py` (라인 642-767)
  - `_receive_loop()` 메서드 추가
  - `connect()` 메서드 병렬 실행 구조로 리팩토링

---

### 🔒 인증 시스템 개선

#### 토큰 격리 버그 수정
- SHA256 해싱을 사용한 토큰 격리 버그 해결
- 다중 계정 사용 시 토큰 충돌 문제 해결

#### 23시간 메모리 캐시 추가
- 인증 토큰에 23시간 메모리 캐시 적용
- API 호출 횟수 대폭 감소

---

### 🆕 신규 기능

#### 신용 주문 자동 대출일자 설정
- 자기융자(credit_type=22) 주문 시 `loan_dt`를 오늘 날짜로 자동 설정
- 수동 입력 오류 방지

#### DirectAPIUsageWarning 제거
- `_from_agent` 플래그 전달로 불필요한 경고 메시지 제거

#### 업종 코드 문서화 및 유틸리티 추가
- KOSPI/KOSDAQ 전체 업종 코드를 docstring에 추가
- `pykis/utils/sector_codes.py` - 업종 코드 MST 파일 다운로드/파싱 유틸리티

**KOSPI 업종 코드 (일부):**
- `0001`: 종합(KOSPI)
- `0002`: 대형주
- `0003`: 중형주
- `0004`: 소형주

**KOSDAQ 업종 코드 (일부):**
- `1001`: 종합(KOSDAQ)
- `2001`: 코스닥 대형주
- `2002`: 코스닥 중형주

### 🐛 버그 수정

#### 주문 API account_api 사용 수정
- `order_stock_cash()`, `order_stock_credit()` 메서드가 올바르게 `account_api`를 사용하도록 수정

---

### 🤖 MCP 서버 (pykis-mcp-server)

#### FastMCP 프레임워크 마이그레이션
- 기존 MCP 구현을 FastMCP 프레임워크로 전면 재작성
- 더 안정적이고 효율적인 서버 구조

#### 58개 MCP 도구 구현
- PyKIS의 모든 주요 API 엔드포인트를 MCP 도구로 노출
- 시세 조회, 주문, 계좌 조회, 투자자 동향 등 전 기능 지원

#### 도구 오케스트레이션 시스템
- `get_tool_registry()` - 사용 가능한 도구 목록 및 관계 조회
- `plan_query_execution()` - 자연어 쿼리 분석 및 실행 계획 생성
- `suggest_tool_combination()` - 목표 달성을 위한 도구 조합 제안

#### 4개 복합 분석 도구 추가
- `analyze_broker_accumulation()` - 특정 증권사 기간별 매집 종목 분석
- `analyze_foreign_institutional_flow()` - 외국인/기관 동시 순매수 종목 분석
- `detect_volume_spike()` - 거래량 급등 종목 탐지
- `find_price_momentum()` - 가격 모멘텀 종목 탐색

#### 분봉 조회 도구 개선
- `inquire_minute_price()` - 일별분봉시세조회 우선 사용하도록 개선

---

## [1.3.1] - 2025-10-30

### 📚 API 응답 타입 완전 문서화

#### 🎯 주요 개선사항

**1. TypedDict 응답 모델 완전 문서화**
- **334개 API 엔드포인트** 응답 구조 추출 (`open-trading-api/examples_llm/` 분석)
- **106개 필드 추가** (기존 57개 → 163개 필드)
  - `StockPriceOutput`: 39 → **82 fields** (+43)
  - `DailyPriceItem`: 13 → **18 fields** (+5)
  - `StockInvestorOutput`: 13 → **27 fields** (+14)
  - `MinutePriceItem`: 8 → **14 fields** (+6)
  - `InquireBalanceRlzPlOutput`: 12 → **15 fields** (+3)
  - **NEW** `InquirePeriodTradeProfitOutput`: **35 fields** (신규 추가)

**2. 메서드 Docstring 완전 개선**
- **6개 주요 API** 메서드에 상세 응답 필드 문서 추가:
  - `get_stock_price()` - 주식 현재가 조회 (82개 필드 문서화)
  - `get_daily_price()` - 일별 시세 조회
  - `get_stock_investor()` - 투자자 매매 동향
  - `get_minute_price()` - 분봉 시세 조회
  - `inquire_balance_rlz_pl()` - 잔고 평가 및 실현 손익
  - `inquire_period_trade_profit()` - 기간별 매매 손익 (신규)

**3. 자동화 도구 개발**
- `extract_response_mappings.py` - 334개 예제 파일에서 COLUMN_MAPPING 추출
- `generate_complete_typeddict.py` - 완전한 TypedDict 모델 자동 생성
- `response_mappings.json` - 모든 API 응답 필드 매핑 (334 APIs, 288 categories)

**4. 개발자 경험 향상**
- IDE 자동완성 지원 강화 (163개 응답 필드)
- 타입 안전성 향상 (모든 필드에 한글 설명 포함)
- API 문서 접근성 개선 (docstring에 주요 필드 포함)

#### 📁 수정된 파일 (6개, +442줄)
- `pykis/responses/stock.py` - 향상된 stock 응답 타입
- `pykis/responses/account.py` - 향상된 account 응답 타입 + 신규 API
- `pykis/responses/__init__.py` - 새로운 응답 타입 export
- `pykis/stock/price_api.py` - 향상된 docstrings
- `pykis/stock/investor_api.py` - 향상된 docstrings
- `pykis/account/api.py` - 향상된 docstrings

#### 🐛 버그 수정
- `price_api.py:991` - 미사용 `retries` 파라미터 경고 해결 (`_retries`로 변경)

#### ✅ 검증 완료
- ✅ 248개 unit tests 통과 (breaking changes 없음)
- ✅ TypedDict `total=False` 일관성 유지
- ✅ 한국어 문서화 철학 유지 (API 필드명 1:1 매핑)

## [1.3.0] - 2025-10-24

### 🎯 파사드 패턴 완성 및 API 안정성 개선

#### 🔧 주요 수정사항

**1. 404 에러 API 처리**
- `inquire_index_price()` - 원본 KIS API 엔드포인트가 404를 반환하는 문제 해결
  - `inquire_index_timeprice()`로 내부 리다이렉트
  - **DeprecationWarning** 추가 (v2.0에서 제거 예정)
  - TODO 주석 명시

**2. TR_ID 수정**
- `get_index_timeprice()` - TR_ID를 `FHPUP02110200`로 수정
  - POSTMAN 테스트로 정상 작동 확인
  - KOSPI/KOSDAQ 시간별 지수 조회 정상화

**3. StockAPI Facade 완성 (31개 메서드 추가)**

Price API (21개):
- `inquire_index_price()`, `inquire_index_tickprice()`, `inquire_index_timeprice()`
- `inquire_index_category_price()`, `inquire_daily_overtimeprice()`, `inquire_elw_price()`
- `inquire_overtime_asking_price()`, `inquire_overtime_price()`, `inquire_vi_status()`
- `get_intraday_price()`, `get_stock_ccnl()`, `daily_credit_balance()`
- `disparity()`, `dividend_rate()`, `fluctuation()`, `foreign_institution_total()`
- `intstock_multprice()`, `market_cap()`, `market_time()`, `market_value()`
- `news_title()`, `profit_asset_index()`, `search_stock_info()`, `short_sale()`, `volume_rank()`

Market API (6개):
- `get_holiday_info()`, `is_holiday()`, `get_pbar_tratio()`
- `get_fluctuation_rank()`, `get_volume_power_rank()`, `get_volume_rank()`

**4. Agent 클래스 완성 (13개 메서드 추가)**

Price API (5개):
- `get_orderbook()` - 호가 정보 조회
- `inquire_price()` - 시세 조회 (추가 정보 포함)
- `get_stock_ccnl()` - 체결 조회
- `get_intraday_price()` - 당일 분봉 전체 데이터
- `get_index_minute_data()` - 업종 분봉 조회

Market API (7개):
- `get_market_fluctuation()` - 시장 변동성 정보
- `get_market_rankings()` - 거래량 기준 종목 순위
- `get_stock_info()` - 종목 기본 정보
- `get_fluctuation_rank()` - 등락률 순위
- `get_volume_power_rank()` - 체결강도 순위
- `get_volume_rank()` - 거래량 순위
- `get_pbar_tratio()` - PBR/PER 비율 순위

Investor API (1개):
- `get_frgnmem_pchs_trend()` - 외국인 매수 추이

### 📊 통계
- **StockAPI Facade**: 58개 메서드 (완성)
- **Agent Stock API**: 90개 메서드 (완성)
- **파사드 패턴**: 100% 구현 완료

### 🏗️ 아키텍처 개선
- Agent → StockAPI Facade → (StockPriceAPI | StockMarketAPI | StockInvestorAPI) 계층 구조 완성
- 모든 하위 API 메서드가 Facade와 Agent를 통해 접근 가능
- `__getattr__()` 동적 위임으로 향후 추가 메서드 자동 지원

### 🐛 버그 수정
- 404 에러 발생하는 `inquire_index_price()` 대체 메서드 제공
- `get_index_timeprice()` TR_ID 오류 수정
- StockAPI Facade에서 누락된 31개 메서드 추가
- Agent에서 누락된 13개 Stock API 메서드 추가

### ⚠️ Deprecation 경고
- `inquire_index_price()` - v2.0에서 제거 예정
  - 대안: `inquire_index_timeprice()` 또는 `get_index_timeprice()` 사용

---

## [1.2.0] - 2025-10-10

### 🚀 신규 API 추가 (31개)

#### 고우선순위 API (8개)
- **시간별 체결 조회**: `inquire_time_itemconclusion()` - 특정 시간 이후 체결 내역 조회
- **실시간 체결 조회**: `inquire_ccnl()` - 30건 체결 데이터 (체결강도 포함)
- **주식현재가 시세2**: `inquire_price_2()` - 상세 시세 정보
- **종목 기본정보**: `search_stock_info()` - 종목명, 시가총액, 상장주식수 등
- **뉴스 제목 조회**: `news_title()` - 종목 관련 뉴스
- **등락률 순위**: `fluctuation()` - 시장 등락률 상위 종목
- **거래량 순위**: `volume_rank()` - 거래량 상위 종목
- **시가총액 순위**: `market_cap()` - 시가총액 상위 종목

#### 중우선순위 API (5개)
- **외국인/기관 종합**: `foreign_institution_total()` - 매매동향 종합
- **신용잔고**: `daily_credit_balance()` - 일별 신용잔고 추이
- **공매도**: `short_sale()` - 공매도 상위 종목
- **ELW 현재가**: `inquire_elw_price()` - ELW 시세 조회
- **VI 발동 현황**: `inquire_vi_status()` - 변동성 완화장치 발동 현황

#### 시세조회 API (13개)
- **시간외 주가**: `inquire_daily_overtimeprice()`, `inquire_overtime_price()`, `inquire_overtime_asking_price()`
- **업종 지수**: `inquire_index_category_price()`, `inquire_index_tickprice()`, `inquire_index_timeprice()`
- **순위/지표**: `disparity()`, `dividend_rate()`, `profit_asset_index()`
- **복수종목**: `intstock_multprice()` - 한 번에 여러 종목 조회
- **서버 미지원 API**: `inquire_index_price()`, `market_time()`, `market_value()` - NotImplementedError 발생 및 대안 API 안내

#### 투자자동향 API (5개)
- **외국계 가집계**: `get_frgnmem_trade_estimate()` - 외국계 매매종목 가집계
- **회원사 동향**: `get_frgnmem_trade_trend()` - 실시간 매매동향
- **프로그램매매**: `get_investor_program_trade_today()` - 투자자별 프로그램매매
- **종목별 동향**: `get_investor_trade_by_stock_daily()` - 종목별 투자자 매매동향
- **추정가집계**: `get_investor_trend_estimate()` - 외국인/기관 추정가집계

### 🛠️ 시스템 개선
- **StockInvestorAPI 모듈 신규 생성**: 투자자 동향 API 분리 (`pykis/stock/investor_api.py`)
- **Agent 클래스 통합**: 모든 신규 API를 Agent에서 직접 호출 가능
- **명확한 에러 처리**: 서버 미지원 API는 NotImplementedError 발생 + 대안 API 제시
- **통합 테스트**: 실제 API 호출 테스트 20개 (100% 성공)

### 📋 테스트
- **유닛 테스트**: 31개 메서드 시그니처 검증 (100%)
- **통합 테스트**: 20개 실제 API 호출 테스트 (100%)
- **테스트 파일**:
  - `testing/test_all_new_apis_251010.py` - 메서드 존재 여부 검증
  - `tests/test_new_apis_integration_251010.py` - 실제 API 호출 검증

### 📊 API 통계
- **구현 완료**: 28개 API (실제 서버 지원)
- **서버 미지원**: 3개 API (명확한 에러 메시지 + 대안 제시)
- **성공률**: 100% (서버 미지원 API는 예상된 동작)

### 🔧 기술 부채 해소
- **보일러플레이트 자동화**: Task agent를 활용한 반복 작업 자동화
- **코드 품질**: 일관된 BaseAPI 패턴 적용
- **문서화**: 모든 메서드에 docstring 포함

## [1.1.0+] - 2025-09-21

### 🚀 성능 최적화
- **Rate Limiter 최적화**: 실측 기반으로 기본값 조정 (18 RPS / 900 RPM)
- **CI/CD 최적화**: Python 버전 테스트를 3개로 축소 (3.8/3.11/3.12)
- **캐시 성능**: 80-95% API 호출 감소 확인

### 🛠️ 시스템 개선
- **예외 처리 강화**: 통합 예외 처리 시스템 구축 (`pykis/core/exceptions.py`)
- **문서화 개선**: 모든 docstring 업데이트 및 README 전면 개선
- **테스트 안정성**: 232개 테스트 통과율 100% 달성

### 🔧 개발 환경
- **GitHub Actions**: CI/CD 파이프라인 최적화 및 보안 스캔 추가
- **보안 강화**: CodeQL 및 Trivy 보안 검사 통합
- **의존성 관리**: Dependabot 제거로 PR 노이즈 감소
- **코드 품질**: Black, isort, flake8, mypy 자동화

## [1.1.0] - 2025-01-12

###   
- **  API  **: /     
  - `order_stock_cash()`:  /  (, ,  )
  - `order_stock_credit()`:  /  (, ,  , )
  - `inquire_order_psbl()`:   / 
  - `inquire_credit_order_psbl()`:   / 

###     
- **TR ID **:   OpenAPI  
  - :  TTTC0012U,  TTTC0011U (: VTTC0012U, VTTC0011U)
  - :  TTTC0052U,  TTTC0051U
- **Rate Limiter **: 10 req/sec, 100ms   
- **  **:      
- ** Docstring**: NumPy      
- **  **:     

###   
- **246  **:   68  
- **52%  **: 8% 
- **  **: 
  - StockAPI    (13 )
  - Agent    (9 )
  - /   
  -      

###   
- **README.md**:   API   
- **  **: ,     
- ** **:     

###   
- **  **:     
- **  **:     
- ** **: ,     

## [1.0.0] - 2025-01-03 

###   :     

###  Breaking Changes
- **API   **:  `inquire_daily_ccld`  DataFrame  Dict    (pykis   )
- **  **: `pagination: bool = False`  / 

###   
- **  **: 
  - CTX_AREA_FK100/NK100    100  
  -  10,000   (100 × 100)
  -       
  -      
  
- **   **: 
  - `OrderExecutionItem`:    (27 )
  - `OrderExecutionSummary`:   
  - `OrderExecutionResponse`:  API  
  -  : `is_buy`, `is_sell`, `is_executed`, `execution_rate` 

- **   **:
  -    
  - NumPy   
  -   

###   
- ** **: Dict    
- ****:       
- ****:       
- ****:  ,       

###   
- **  **:  100 →  10,000  
- ** **:     
- ** **: (ord_dt, odno, pdno)    

###   
```python
#   ( )
result = agent.inquire_daily_ccld(start_date="20250101", end_date="20250131")

#  ()
result = agent.inquire_daily_ccld(
    start_date="20250101", 
    end_date="20250131",
    pagination=True,
    max_pages=50,
    page_callback=lambda page, data, ctx: print(f" {page}: {len(data)}")
)

#   
from pykis.account.models import OrderExecutionResponse
response = OrderExecutionResponse.from_api_response(result)
buy_orders = response.get_buy_orders()
executed_orders = response.get_executed_orders()
```

###   
- **94.4%  **:    
- **zero  **:   `pagination=False`   
- ** **:      

   pykis **   **    .

---

## [0.1.22] - 2025-08-27

###  NXT()   
- **  **:  API KOSPI/KOSDAQ/NXT  
  - `FID_COND_MRKT_DIV_CODE`  "J" "J" 
  - 29   (7  + 2  )
  -  KOSPI/KOSDAQ  100%  
  - NXT      

###         
- ** **: 232   (54 )
- ** **: 52%  (8% )
- **  **: 
  - `test_dataframe_helper.py`: DataFrame   16  (100% )
  - `test_investor_db.py`:  DB  16  (75% )
  - `test_websocket_client_basic.py`: WebSocket    15 

###   
- **Stock API **: `api.py`, `investor_api.py`, `price_api.py`, `market_api.py`, `condition.py`
- **Core **: `client.py` (  )
- **Program **: `trade.py` ( )
- ** **: `test_client.py`, `test_program_trade.py`

###    (2025-08-27 )
- **   **: API   J/UN   
- **investor_api.py**: / API J   (UN   )
  - `get_stock_investor()`, `get_stock_member()`, `get_member_transaction()` 
- ** API**:  / API UN   (NXT  )

###   
- **README.md**: NXT   ,  
- **NXT_SUPPORT_CHANGES.md**:   

## [0.1.21] - 2025-08-22

###   
- **  Excel  **:   Excel     
  - ** **: YYYYMMDD  / 
  - ** **:     
  - **  **:      
  - **  **:    
  - **98%  **:    

- **    **:    
  - **178   **: 2 , 1  
  - **Agent   **: env_path  
  - **   **:    
  - ** API  **: BaseAPI  

###  
- ** **: .env     
  - Agent  env_path  
  -      
- **  **: BaseAPI   account   
- **  **:       
- **  **:     

###    
- ** **: 44%
- **  **:
  - `trading_report.py`: 98% 
  - `program/trade.py`: 95%
  - `core/config.py`: 88%
  - `websocket/ws_agent.py`: 64%

###   
```python
#    Agent 
from pykis import Agent
agent = Agent(env_path=".env")  # env_path 

#  Excel 
from pykis.utils.trading_report import generate_trading_report
report_path = generate_trading_report(
    client=agent.client,
    account_info={'CANO': 'your_account', 'ACNT_PRDT_CD': '01'},
    start_date='20250101',
    end_date='20250131',
    output_path='trading_history.xlsx'
)

# 200   ( )
futures_price = agent.get_future_option_price()  # 9(101W09)
```

## [0.1.26] - 2025-01-08

### 
- **    API **
  - **/  API**:
    - `inquire_daily_ccld`:  (TTTC0081R)
    - `order_cash`: () - / (TTTC0011U/TTTC0012U)
    - `order_rvsecncl`: () (TTTC0013U)
    - `inquire_psbl_rvsecncl`:  (TTTC0084R)
  
  - **/  API**:
    - `inquire_period_trade_profit`:  (TTTC8715R)
    - `inquire_balance_rlz_pl`: _ (TTTC8494R)
  
  - **/  API**:
    - `inquire_psbl_sell`:  (TTTC8408R)
  
  - **  API**:
    - `order_resv`:  (CTSC0008U)
    - `order_resv_ccnl`:  (CTSC0004R)
    - `order_resv_rvsecncl`:  (CTSC0009U/CTSC0013U)
  
  - **  API**:
    - `inquire_credit_psamount`:  (TTTC8909R)
    - `order_credit_buy`: () (TTTC0052U)
    - `order_credit_sell`: () (TTTC0051U)
  
  - **/  API**:
    - `inquire_intgr_margin`:   (TTTC0869R)
    - `inquire_period_rights`:  (CTRGA011R)

### 
- **AccountAPI   **: 15     
- **Agent Facade  **:   API Agent    
- ** **:       

### 
- `testing/test_account_apis_250108.py`:   API    

=======
>>>>>>> a49c093ae6bced46934b90424a2ff3dac213c4ba
## [0.1.25] - 2025-07-15

### 
- **  API **
  - **`get_daily_minute_price(code, date, hour)`  **:
    -       ( 120)
    - TR ID: FHKST03010230 
    -        
    -  1    
  - **API  **: `INQUIRE_TIME_DAILYCHARTPRICE`
  - **StockAPI  Agent  **

### 
- **    **
  - **`fetch_minute_data`   **:
    -  30   →  4   
    -    (~480)  
    - 4  09:00, 11:00, 13:00, 15:30  
  - **   **:
    -  :   +    
    -  :   
  - **  **: `is_holiday` API    
  - **  **:    ,    

### 
- **    **
  - **`calculate_support_resistance(code, date)`  **:
    -    /  
    -     (Volume Profile)
    -     (R1~R3, S1~S3)
    - VWAP (   ) 
    -    (0-100) 
  - **5   **:
    -    
    -    / 
    -      
    -      
    -   /  

### 
- **    **
  - **`examples/minute_candle_crawler.py` **:
    -   /  
    -      
    - 4     
    - `{}_candles.db` SQLite   
    -      
    -      
  - **  **:
    -  →   
    -     
    -     DB 
    -     

### 
- **    **:
  - (005930) 2024 12 20 361   
  -   +   722 (361+361)  
  -   0.00   
- **   **:
  -  5,  5  
  - VWAP     
  -     
  -     

###  
- **README.md **:
  -      
  -     
  -       
- **  **:
  - `get_daily_minute_price`  
  - `calculate_support_resistance`  
  -     

### 
- **   300% **: 30   → 4  
- **   **:        
- **   **:      
- **  **:    +     

## [0.1.24] - 2025-01-21

### 
- **     **
  - **`get_daily_credit_balance(code, date)`  **:
    -  (/)    
    - TR ID: FHPST04760000 
    - , ,     
    - ,   
    -  /   
  - **StockAPI  Agent  **:
    - `pykis/stock/api.py` StockAPI  
    - `pykis/core/agent.py` Agent  
    -    API  

### 
- **  API  **:
  - (005930)    
  - 30     
  -   0 () 
  -  0.13%,  842    

###  
- **PYKIS_API_METHODS.md **:
  -      
  -     (19/22  , 86.4%)
  -       
- **README.md **:
  -   " "  
  - API   `get_daily_credit_balance` 
- **CHANGELOG.md **:
  -      

### 
- **   **: /       
- **API  **: Postman    API  
- ** **:         

## [0.1.23] - 2025-07-10

### 
- **         **
  - **`fetch_minute_data`    **:
    - (09:00~15:30): 5  
    - : 30  
    -       
  - **   **:
    - : `{code}_minute_data.csv`
    - : `{code}_minute_data_{YYYYMMDD}.csv`
    -     
  - **  **:
    -       
    - API       
    -      

### 
- **     **
  - **`examples/portfolio_realtime_monitor.py`  **:
    -        
    -     
    - VWAP(  ) 60   
    - VWAP     
    -    
    -   5  
  - **`examples/README_portfolio_monitor.md`  **:
    -      
    -      
    -       
    -   (RSI, MACD,   )
  - **`examples/test_portfolio_monitor.py`  **:
    - Agent ,  ,    
    -  , VWAP ,    
    -       

### 
- **    **
  - **StockPosition  **:
    -  : , , , 
    -  : , , VWAP, 
    - : / ,  
    -  : ,   
  - **  **:
    - VWAP  -   
    -       
    -     

###  
- **  **:
  ```python
  #       
  balance = self.agent.get_account_balance()
  for position in balance['output1']:
      if int(position.get('hldg_qty', 0)) > 0:
          self.positions[code] = StockPosition(...)
  ```
- **VWAP  **:
  ```python
  # 60   VWAP 
  total_value = sum(price * volume for price, volume in valid_data)
  total_volume = sum(volume for _, volume in valid_data)
  vwap = total_value / total_volume
  ```
- ** **:
  ```
      
                  VWAP        
      75,000   70,000  +7.14%  74,500  +0.67%   +2.5%   1,234
  ```

### 
- **   **:
  -   : API   (420)
  -   :    ( )
  -       
- **   **:
  - 6      
  - Agent ,  ,    
  - VWAP        

### 
- ** **:        
- ** **:       
- **  **: VWAP     
- ** **:        
- ****:        

## [0.1.22] - 2025-07-07

### 
- ** pytest    **
  - **   **: 
    -         
    - `tests/test_token.py` /      
    -    `pykis/core/credit/KIS_Token.json` 
  - **  **:
    - `pykis/core/auth.py`, `pykis/core/config.py`   `.env`   
    -       `.env`  
    - `load_dotenv(dotenv_path=os.path.join(ROOT_DIR, '.env'), override=True)` 
  - **   **:
    - HTTP   5 → 2 
    -   1 → 0.5     
    - API        

### 
- **   99.2%  **
  - **  **: 127 , 2 , 1 xfail ( )
  - ** **:    5 → 30 90% 
  - ** **:         
  - **  **: `tests/websocket/test_client.py` → `test_websocket_client.py` 

###    
- **   **:
  ```python
  #       
  backup_path = token_tmp + '.backup'
  if os.path.exists(token_tmp):
      shutil.copy2(token_tmp, backup_path)
  
  #       
  finally:
      if os.path.exists(backup_path):
          shutil.copy2(backup_path, token_tmp)
          os.remove(backup_path)
  ```
- **  **:
  ```python
  #    .env    
  ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
  load_dotenv(dotenv_path=os.path.join(ROOT_DIR, '.env'), override=True)
  ```

### 
- **        **
- **   128   127  **
- **CI/CD     **

## [0.1.21] - 2025-07-07

### 
- **  API     **
  - **`get_cash_available` API **: 
    - TR ID : `TTTC8901R` → `TTTC8908R` ()
    -   : `PDNO`     
    - : "005930" ()
  - **`get_total_asset` API **:
    - TR ID : `TTTC8522R` → `CTRP6548R` ()
    -   : `INQR_DVSN_1`, `BSPR_BF_DT_APLY_YN` 
    -  404   JSON     

- **   **
  - **`fetch_minute_data`  **: 
    -   `get_minute_chart`  `get_minute_price` 
    -      360     
  - **   **:  `get_minute_chart`  `get_minute_price` 

- **   **
  - **`pykis/websocket/client.py`   **:
    - 1245-1246 `if self.enable_ask_bid:`    
    - PyKIS  import      

### 
- **   100%  **
  - **  **: 127 , 2 , 1 xfail ( )
  - ** API   **: 
    - ""  → "_"  
    -  API     
    -  AccountAPI  16 
  - **API  **: 404 , JSON     API  

### 
- **   **
  - **`examples/test_helpers.py`  **:
    - `test_api_method`: API      
    - `setup_test_environment`: Agent       
    - `batch_test_methods`:    
    - `print_test_summary`:   
    - `reset_test_results`:   
    - `get_common_test_configs`:     
  - **  **:       

- **   v2.0  **
  - **Cell 1**:   import    
  - **Cell 2**:     ,     
  - **Cell 5**:    (  )
  - **Cell 6**:     ( )
  - **Cell 7**:      
  - **Cell 0**:  "v2.0 -    " 

### 
- ** RTX_ENV   **
  -     
  - PyKIS Agent  import/ 
  - API  100%  
  -      

### 
- **API **:        (360 )
- **API **:  API   404   
- ** **:      
- ** **:       
- ** **:       

## [0.1.20] - 2025-07-07

### 
- **      (H0IF1000)**
  - **, , 200**     
  - , ,   
  - `enable_index=True`    
  -    : 0001(KOSPI), 1001(KOSDAQ), 2001(KOSPI200)

- **      (H0GSCNT0)**
  - **   **   
  - , , ,   
  - `enable_program_trading=True`    
  -     

- **       (H0STASP0)**
  - **10   **  (    )
  -  5    
  - `enable_ask_bid=False`     (: )

- ** Agent   **
  - `agent.websocket()`    :
    - `enable_index`:      (: True)
    - `enable_program_trading`:      (: True)
    - `enable_ask_bid`:      (: False)

### 
- **     **
  - `handle_message()`   TR ID   
  -        
  -       
  -         

- **      **
  -      (KOSPI, KOSDAQ, KOSPI200)
  -      ( )
  -      (  )

- **KISClient     **
  - `get_ws_approval_key()`  
  -    : `KIS_SECRET_KEY` → `KIS_APP_SECRET`
  -        

### 
- **  **:   12% → 25%
- **  **: 6    
- **   **: , ,     

###  
```python
#    
agent = Agent()
ws_client = agent.websocket(
    stock_codes=["005930"],
    enable_index=True,           #    (, , 200)
    enable_program_trading=True, #   
    enable_ask_bid=False         #    ()
)
await ws_client.connect()
```

## [0.1.19] - 2025-07-07

### 
- **  **: `KIS_WS.py` `pykis.websocket`   `Agent`     `websocket()`  .
- ** **:    `README.md`, `PYKIS_API_METHODS.md`     .

### 
- `pykis/websocket/client.py`:  `KIS_WS.py`  `pykis`    ,    .
- `pykis/__init__.py`: `KisWebSocket`  `pykis`  .

## [0.1.18] - 2025-06-29

### 
- **  100%  **
  - `pykis/core/config.py`: `KISConfig`  `__init__`   
    - `all()`  `any()`        
    -       
    - `tests/unit/test_config.py::TestKISConfig::test_validate_config_missing_values`  
  - **  : 121 , 2 , 1 xfail ( )**
  - **PyKIS    100% **:   API    
    - `get_stock_price`, `get_daily_price`, `get_minute_price`  8  API  
    - Agent      
    -  API     

### 
- **  **: CI/CD     
- **   **:       
- **   61% **:    

## [0.1.17] - 2025-07-06

### 
- **   **
  - `tests/unit/test_config.py`: `KISConfig`       ,     `.env`    .   CI/CD              .
  - `tests/integration/test_agent_comprehensive.py`: `test_is_holiday`     .         ,       .

## [0.1.16] - 2025-01-29

### 
- ** KOSPI200    **
  - **`get_kospi200_futures_code`  **:          
    -     (3,6,9,12)      
    - KOSPI200     (: 101S12, 201S03 )
    - `get_future_option_price`    
  - ** API **:      KOSPI200    
    - :     (`101S09` )
    - :      

### 
- **    **: KOSPI200   
- ** **: PYKIS_API_METHODS.md    

###  
```python
#   (  )
futures_price = agent.get_future_option_price(
    market_div_code="F",      # 
    input_iscd="101S09"       #   
)

#   (  )
futures_price = agent.get_future_option_price()  #   KOSPI200  
```

## [0.1.15] - 2025-01-29

### 
- **   API **
  - **`get_future_option_price`  **:    
    - API : `/uapi/domestic-futureoption/v1/quotations/inquire-price` (TR: FHMIF10000000)
    - , , ,    
    - : F(), O(), JF(), JO()
    - :  6(: 101S03),  9(: 201S03370)
    - : (F), (101S09)

- ** **:
  ```python
  #    ()
  futures_price = agent.get_future_option_price()
  
  #    
  futures_price = agent.get_future_option_price(
      market_div_code="F",      # 
      input_iscd="101S03"       #   
  )
  
  #   
  option_price = agent.get_future_option_price(
      market_div_code="O",      # 
      input_iscd="201S03370"    #   (9)
  )
  ```

- **  **: `examples/future_option_price_example.py` -     
- ** **: PYKIS_API_METHODS.md     

## [0.1.14] - 2025-01-29

### 
- **   API **
  - **`get_daily_index_chart_price`  **:   
    - API : `/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice` (TR: FHKUP03500100)
    -     (, , , , KOSPI, KOSDAQ )
    -    (, , , )
    -  50  ,       
    -  : 0001(), 0002(), 0003(), 0004(), 0005(KOSPI), 0006(KOSDAQ), 0007(KOSPI200), 0008(KOSPI100), 0009(KOSPI50), 0010(KOSDAQ150)

- ** **:
  ```python
  #     
  sector_daily = agent.get_daily_index_chart_price(
      market_div_code="U",      # 
      input_iscd="0001",        # 
      start_date="20240601",
      end_date="20240630",
      period_div_code="D"       # 
  )
  
  #     
  large_cap_weekly = agent.get_daily_index_chart_price(
      market_div_code="U",      # 
      input_iscd="0002",        # 
      start_date="20240101",
      end_date="20241231",
      period_div_code="W"       # 
  )
  ```

- **  **: `examples/daily_index_chart_price_example.py` -     
- ** **: PYKIS_API_METHODS.md  API  

## [0.1.13] - 2025-01-29

### 
- **   API **
  - **`get_hourly_conclusion`  **:    
    - API : `/uapi/domestic-stock/v1/quotations/inquire-time-itemconclusion` (TR: FHPST01060000)
    -    (HHMMSS , : "115959")
    -  :  , , ,   30  
  
  - ** `get_stock_ccnl`  **:  (30)  - **   **
    - API : `/uapi/domestic-stock/v1/quotations/inquire-ccnl` (TR: FHKST01010300)
    - ** **:  (`tday_rltv`)      
    -  `get_volume_power`      
    -  :  30 , , , ,  
    -           

- **Agent   **:    Agent     
  ```python
  #   
  hourly = agent.get_hourly_conclusion("005930", "143000")
  
  #    
  ccnl = agent.get_stock_ccnl("005930")
  strength = ccnl['output'][0]['tday_rltv']  # 123.50
  ```

### 
- **   **:      
- ** **: README.md, PYKIS_API_METHODS.md    

## [0.1.12] - 2025-06-29

### 
- **`get_pbar_tratio`  **
  - `get_pbar_tratio`  docstring, `tr_id`,   "/ "    .

## [0.1.11] - 2025-06-29

### 
- **  API   **
  - `Agent`   `get_program_trade_hourly_trend`  `ProgramTradeAPI`    .
  - `ProgramTradeAPI` `get_program_trade_hourly_trend`    `get_program_trade_by_stock`  .
  -       .

## [0.1.10] - 2025-06-29

### 
- **`is_holiday`   **: (, )    .   API          .

## [0.1.9] - 2025-06-29

### 
- **  **: `kis_devlp.yaml`    `.env`    .
  - `python-dotenv`   `.env`  API     .
  -   `pyyaml`   .

### 
- **`.env.example` **:       `.env.example`  .
- ** **: `.env`    `FileNotFoundError`     .

### 
- **YAML  **: `pykis/core/config.py`    YAML    .
- **`load_account_info` **: `pykis/stock/api.py`     `load_account_info`  .

## [0.1.8] - 2025-06-29

### 
- `pykis/program/api.py`:     deprecated  .

## [0.1.7] - 2025-06-29

### 
- **API    **
  -  API         .
  - `pykis/stock/program_trade.py`  deprecated  .
  - `pykis/stock/data.py`      .
- **  **
  -      .
  -     (`tests/unit/test_stock_data.py`, `tests/unit/test_stock_market.py`) .
- **`API_ENDPOINTS` **
  - `pykis/core/client.py` `API_ENDPOINTS` (alias)     .
- **Facade  **
  - `Agent`    API    .
  - `pykis/__init__.py`  `Agent`     Facade   .

### 
- **    **
  -     API   .
- ** **
  -           .

## [0.1.6] - 2025-06-28

### 
- **      **
  - `tests/test_agent_usage.py`: `get_market_rankings()` -> `get_price_rank()`, `get_stock_info()` -> `get_stock_opinion()`  . DataFrame    .
  - `tests/integration/test_agent_comprehensive.py`: `validate_api_response`  `output1`, `output2`    /   .
  - `tests/unit/test_auth.py`: `read_token`  `save_token`    mock  .
  - `tests/unit/test_client.py`: `test_make_request_daily_price` `tr_id` . `test_refresh_token` `requests.post` mock .
  - `tests/unit/test_program_trade.py`: `datetime` import       `pytest.raises` .

- **`pykis/core/agent.py` **
  - `StockMarketAPI` `Agent`   `__getattr__`    .

### 
- **    **
  -        .
  - mock     API  .

## [0.1.5] - 2025-06-26

### 
- **datetime import  **
  - `pykis/core/agent.py`: `import datetime` `from datetime import timedelta`  import  
  - `pykis/stock/api.py`: `import datetime` `from datetime import datetime` , `datetime.datetime.now()` → `datetime.now()` 
  - `pykis/stock/data.py`:  datetime import 
  -    import (`from datetime import datetime, timedelta`)  

- ** API        **
  -  API   : `FID_ETC_CLS_CODE=""` , `FID_COND_SCR_DIV_CODE` 
  - `get_minute_price`  API_ENDPOINTS  `MINUTE_CHART` → `MINUTE_PRICE` 
  - `fetch_minute_data`     : `output` → `output2`  
  -   "0900" → "090000" (HHMMSS) 
  - API       (`rt_cd == '0'`)
  -      : 8  240    

-  API   
  -    `condition.py`  (`tr_id="HHKST03900400"`)  
  - `pykis/stock/api.py` `get_condition_stocks`   `tr_id` 
  - `pykis/core/agent.py` `get_condition_stocks_dict`   `ConditionAPI` 
  - `examples/list_interest_groups.py` Agent   
  -    `user_id="unohee"`   
  - `rt_cd='1'` ("  ")    

-      
  - `StockAPI`  `get_holiday_info()`  `is_holiday()`  
  - Agent    :  API (`get_holiday_info`) +  (`is_holiday`)
  -     API    
  -    :        
  -   10     

### 
- **     **
  - `fetch_minute_data`  8 (09:00~15:30)    
  - SQLite DB      
  -  240     
  - : `stck_bsop_date`, `stck_cntg_hour`, `stck_prpr`, `stck_oprc`, `stck_hgpr`, `stck_lwpr`, `cntg_vol`, `acml_tr_pbmn`, `code`, `date`

- Facade   
  -  `ConditionAPI`    
  - Agent  `get_condition_stocks`  (`user_id`, `seq`, `tr_cont`) 
  -   Agent      API  
  -  Agent    

-   
  - `examples/pykis.ipynb`     
  -     API    (   )
  -      
  -      
  -      

### 
-  API  
  - `/uapi/domestic-stock/v1/quotations/chk-holiday`  
  - `tr_id="CTCA0903R"`    
  -  (`opnd_yn`)  
  -      

## [0.1.4] - 2024-06-22

### 
-   API   
  - `get_volume_power`     
  -  API   TR   (`/uapi/domestic-stock/v1/ranking/volume-power`, `FHPST01680000`)
  -  : " " → "" 
  -      (  API)

-   API 
  -        API 
  - `get_program_trade_daily_summary`:   
  - `get_program_trade_market_daily`:    API 
  -   

-   API 
  - `get_market_fluctuation`      API 
  - : `/uapi/domestic-stock/v1/ranking/fluctuation`, TR: `FHPST01700000`

-  API 
  -   
  - `client.py` `INQUIRE_PSBL_ORDER`  
  -   `get_total_evaluation`  

### 
-   
  - `get_pgm_trade`  `examples/program_trade_analysis.py` 
  - `ProgramTradeAnalyzer`    
  - API    

-    
  - `logger`   : `logger` → `logging` 
  -     : `get_condition_stocks_dict`  API  

- Strategy   
  - deprecated strategy  import    
  - `pykis/core/agent.py` strategy   
  - `tests/integration/test_strategy.py`  

### 
-    
  - 50      
  - , , ,  ,     
  -       
  -     

### 
-  `get_volume_power`  
-     API   
- Strategy      
-    API  

## [0.1.3] - 2024-06-19

### 
- ProgramTradeAPI     
  - `pykis/program/api.py`, `pykis/program/trade.py`, `pykis/stock/program_trade.py`   
  -  import `pykis.program.trade` 
  - deprecated    

### 
-  
  - `get_program_trade_summary` → `get_program_trade_by_stock` 
  -     
- `get_program_trade_by_stock`  API   
  - () API  
  -    

### 
- README.md 
  -      
  -       

## [0.1.2] - 2024-06-16

### 
-  `kis-agent` `pykis` 
-   
  - `src`  
  -   `pykis` 
-  
  - `KIS_Agent` → `Agent`
  - `KISClient` → `Client`

## [0.1.1] - 2024-06-15

### 
- Postman    
  - : , , ,  
  - :  ( ) API     
  - : , ,  
  - :  
  -  : //  

### 
-   
  -  API     
  -   
  -   
-     ,     ( / API           )

### 
- `market.py`  
  -  
  -    
  -   

### 
-  API   docstring 
  - , ,  
  -   
  -    

## [0.1.0] - 2025-06-11

### 
-  OpenAPI      
  - `core`: API , ,  
  - `account`:     
  - `stock`:     
  - `program`:    
  - `strategy`:    

### 
-      docstring 
  -  : , , ,  ,  
  -  : , ,  
  -  : , , , ,  

### 
- `program_trade.py`  
  - `get_program_trade_detail` → `get_program_trade_period_detail`
  - `get_program_trade_ratio` → `get_pgm_trade`

### 
- `scripts/convert_yaml_to_env.py`:    

### 
- API        
-     .gitignore 

### 
-   README.md  
- API     
-     

###  
- `program_trade.py`   `get_program_trade_summary`   
-  API     
-       