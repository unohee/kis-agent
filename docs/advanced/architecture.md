# 아키텍처 개요

## 모듈 구조

```
kis_agent/
├── core/                 # 핵심 인프라
│   ├── agent.py          # Agent — 통합 진입점
│   ├── client.py         # KISClient — HTTP 통신
│   ├── config.py         # KISConfig — 설정 관리
│   ├── auth.py           # 인증/토큰 관리
│   ├── cache.py          # TTLCache — 지능형 캐싱
│   ├── rate_limiter.py   # RateLimiter — 요청 제한
│   └── base_api.py       # BaseAPI — 모든 API 기본 클래스
│
├── stock/                # 국내주식 (StockAPI Facade)
│   ├── price_api.py      # 시세 조회 전담
│   ├── market_api.py     # 시장 정보 전담
│   └── investor_api.py   # 투자자 정보 전담
│
├── account/              # 계좌 (AccountAPI Facade)
│   ├── balance_query_api.py  # 잔고/자산 조회
│   ├── order_api.py      # 주문 실행
│   └── profit_api.py     # 체결/손익 조회
│
├── overseas/             # 해외주식 (OverseasStockAPI Facade)
│   ├── price_api.py      # 시세 조회
│   ├── account_api.py    # 계좌 조회
│   ├── order_api.py      # 주문
│   └── ranking_api.py    # 순위 조회
│
├── futures/              # 국내선물 (Futures Facade)
├── overseas_futures/     # 해외선물 (OverseasFutures Facade)
├── websocket/            # 실시간 데이터 (WSAgent)
├── cli/                  # CLI 인터페이스
├── responses/            # TypedDict 응답 모델 (150+개)
├── utils/                # 종목마스터, 유틸리티
└── program/              # 프로그램매매 API
```

## 설계 패턴

### Facade 패턴

각 도메인(주식, 해외, 선물, 계좌)은 Facade 패턴으로 복잡한 하위 API를 단순화합니다:

```
Agent (통합 진입점)
├── StockAPI Facade
│   ├── StockPriceAPI      (시세 62+ 메서드)
│   ├── StockMarketAPI     (시장정보)
│   └── StockInvestorAPI   (투자자)
├── AccountAPI Facade
│   ├── AccountBalanceQueryAPI
│   ├── AccountOrderAPI
│   └── AccountProfitAPI
├── OverseasStockAPI Facade
│   ├── OverseasPriceAPI
│   ├── OverseasAccountAPI
│   ├── OverseasOrderAPI
│   └── OverseasRankingAPI
├── Futures Facade
└── OverseasFutures Facade
```

`__getattr__`를 활용한 동적 위임으로, Facade에 명시적으로 정의되지 않은 메서드도 하위 API에서 자동으로 찾아 호출합니다.

### 캐싱 (TTLCache)

```python
# 기본 설정
TTLCache(default_ttl=5, max_size=1000)
```

- **기본 TTL**: 5초 (시세 데이터 실시간성 유지)
- **최대 크기**: 1000 항목
- **Thread-safe**: RLock 사용
- **자동 정리**: 만료 항목 자동 제거
- **캐시 적중률**: 80-95%
- **캐시 적중 응답**: < 50ms

### Rate Limiter

전역 싱글턴으로 모든 API 호출이 공유합니다:

```python
RateLimiter(
    requests_per_second=18,    # 공식 20, 안전 마진 적용
    requests_per_minute=900,   # 공식 1000, 안전 마진 적용
    min_interval_ms=55,        # 최소 요청 간격
    burst_size=10,             # 순간 처리량
    enable_adaptive=True,      # 적응형 백오프
)
```

**적응형 Rate Limiting**: 에러 발생 시 자동으로 요청 속도를 줄이고, 성공 시 점진적으로 복구합니다.

```python
# Rate Limiter 상태 조회
status = agent.get_rate_limiter_status()

# 런타임 설정 변경
agent.set_rate_limits(requests_per_second=15, requests_per_minute=800)

# 초기화
agent.reset_rate_limiter()

# 적응형 활성화/비활성화
agent.enable_adaptive_rate_limiting(True)
```

## 응답 타입 (TypedDict)

`kis_agent/responses/` 패키지에 150개 이상의 TypedDict가 정의되어 있어 IDE 자동완성과 타입 검사를 지원합니다:

```python
from kis_agent.responses import (
    StockPriceResponse,
    AccountBalanceResponse,
    OverseasPriceResponse,
    # ... 150+ 타입
)
```

**모듈별 응답 타입:**

| 모듈 | 설명 |
|:---|:---|
| `responses/common.py` | BaseResponse 기본 구조 |
| `responses/stock.py` | 주식 시세/체결 응답 |
| `responses/account.py` | 계좌/잔고 응답 |
| `responses/order.py` | 주문 응답 |
| `responses/overseas.py` | 해외주식 응답 (40+ 타입) |
| `responses/futures.py` | 선물옵션 응답 |
| `responses/overseas_futures.py` | 해외선물 응답 |

## 종목 마스터

`kis_agent/utils/` 패키지에서 종목 마스터 데이터를 관리합니다:

```python
from kis_agent.utils import (
    search_futures,          # 선물 검색
    get_current_futures,     # 현재 월물 조회
    resolve_futures_code,    # 코드 변환
    get_sector_codes,        # 섹터 코드
    SECTOR_CODES,            # 섹터 코드 상수
)

from kis_agent.utils.stock_master import (
    resolve_code,            # 종목명 → 코드 변환
    search,                  # 종목 검색
)
```

### 자동 다운로드 및 캐싱

`Agent()`를 생성하면 `__init__` 마지막에 `_preload_masters()`가 자동 호출되어, **백그라운드 스레드**에서 주식 + 선물옵션 마스터 파일을 다운로드합니다.

- 캐시가 오늘 날짜면 즉시 반환 (수 ms)
- 캐시가 없거나 오래됐으면 백그라운드에서 다운로드
- 다운로드 실패해도 Agent 초기화를 블로킹하지 않음 (경고 로그만 출력)

수동 관리가 필요 없습니다.

#### 주식 마스터 (`stock_master.py`)

KOSPI/KOSDAQ 전종목 코드+이름을 관리합니다.

- **다운로드 소스**: `https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip`, `kosdaq_code.mst.zip`
- **캐시 경로**: `~/.kis_agent/master/stocks.csv`
- **갱신 주기**: 하루 1회 (날짜 기준, 첫 호출 시 자동 다운로드)
- **캐시 계층**: 메모리 캐시 → 파일 캐시 → 다운로드
- **폴백**: 다운로드 실패 시 만료된 파일 캐시 사용

```python
from kis_agent.utils.stock_master import load_stocks, search, resolve_code

# 전종목 로드 (자동 다운로드+캐싱)
stocks = load_stocks()                  # [{"code": "005930", "name": "삼성전자", "market": "코스피"}, ...]
stocks = load_stocks(force_refresh=True)  # 강제 재다운로드

# 종목 검색 (정확→접두사→부분 매칭 순)
results = search("삼성", limit=10)

# 종목명 → 코드 변환
code = resolve_code("삼성전자")  # "005930"
code = resolve_code("005930")    # "005930" (6자리는 그대로 반환)
```

#### 선물옵션 마스터 (`futures_master.py`)

지수/상품 선물옵션 전종목을 관리합니다.

- **다운로드 소스**: `fo_idx_code_mts.mst.zip` (지수선물옵션), `fo_com_code.mst.zip` (상품선물옵션)
- **캐시 경로**: `~/.kis_agent/master/futures.csv`
- **갱신 주기**: 하루 1회 (동일 메커니즘)
- **분류 코드**: 지수선물, 지수콜/풋옵션, 미니선물, 위클리옵션, 코스닥150 등 17종
- **월물 구분**: 연결선물, 최근월물, 차근월물, 차차근월물

```python
from kis_agent.utils.futures_master import (
    load_futures, search_futures, get_current_futures, resolve_futures_code
)

# 전종목 로드
futures = load_futures()

# 선물 검색
results = search_futures("KOSPI200")

# 현재 근월물 조회
current = get_current_futures("kospi200")  # {"code": "101S06", "name": "F 202606", ...}

# 단축코드 해석
info = resolve_futures_code("101S06")
```

#### CLI에서의 활용

CLI에서 종목명으로 입력하면 내부적으로 `resolve_code()`를 호출하여 자동 변환합니다:

```bash
kis price 삼성전자        # → resolve_code("삼성전자") → "005930"
kis search 카카오         # → search("카카오")
kis futures 101S06       # → futures_master에서 종목명 자동 조회
```
