# Futures 모듈 아키텍처 설계

**작성일**: 2026-01-19
**버전**: v1.0
**관련 이슈**: [INT-506](https://linear.app/intrect/issue/INT-506)

---

## 1. 개요

pykis에 국내/해외 선물옵션 거래 기능을 통합하기 위한 아키텍처 설계 문서입니다.

### 설계 목표
- 기존 `pykis/stock/` 구조와 일관성 유지
- Facade 패턴 적용으로 단순하고 직관적인 인터페이스 제공
- 단일 책임 원칙(SRP) 준수로 유지보수성 향상
- TypedDict 응답 모델로 타입 안전성 보장
- 한국어 docstring으로 API 필드명 1:1 매칭

---

## 2. 모듈 구조

### 2.1 디렉토리 구조

```
pykis/
├── futures/                       # 국내선물옵션 모듈 (신규)
│   ├── __init__.py               # Facade 패턴 통합
│   ├── price_api.py              # 시세 조회 API (11개 메서드)
│   ├── account_api.py            # 계좌/잔고 조회 API (6개 메서드)
│   └── order_api.py              # 주문/체결 조회 API (6개 메서드)
│
├── overseas_futures/              # 해외선물옵션 모듈 (신규)
│   ├── __init__.py               # Facade 패턴 통합
│   ├── price_api.py              # 시세 조회 API
│   ├── account_api.py            # 계좌 조회 API
│   └── order_api.py              # 주문 API
│
├── responses/
│   ├── futures.py                # 국내선물옵션 TypedDict (신규)
│   └── overseas_futures.py       # 해외선물옵션 TypedDict (신규)
│
└── core/
    ├── agent.py                  # Agent.futures 속성 추가
    └── client.py                 # API_ENDPOINTS 확장
```

### 2.2 Facade 패턴 적용

기존 `StockAPI` 구조를 참고하여 Facade 설계:

```python
# pykis/futures/__init__.py

from .price_api import FuturesPriceAPI
from .account_api import FuturesAccountAPI
from .order_api import FuturesOrderAPI

class Futures(BaseAPI):
    """
    국내선물옵션 API 통합 Facade

    Attributes:
        price: 시세 조회 API (FuturesPriceAPI)
        account: 계좌/잔고 조회 API (FuturesAccountAPI)
        order: 주문/체결 조회 API (FuturesOrderAPI)
    """

    def __init__(self, client, account_info=None, _from_agent=False):
        super().__init__(client, account_info, _from_agent=_from_agent)

        # 하위 API 초기화
        self.price = FuturesPriceAPI(client, account_info, _from_agent=_from_agent)
        self.account = FuturesAccountAPI(client, account_info, _from_agent=_from_agent)
        self.order = FuturesOrderAPI(client, account_info, _from_agent=_from_agent)

    # Delegation 메서드 (선택적으로 직접 접근 제공)
    def get_price(self, code: str) -> Optional[Dict]:
        """선물옵션 현재가 조회"""
        return self.price.get_price(code)

    def get_orderbook(self, code: str) -> Optional[Dict]:
        """선물옵션 호가 조회"""
        return self.price.get_orderbook(code)

    # ... 기타 자주 사용하는 메서드들
```

---

## 3. API 분류 및 메서드 설계

### 3.1 국내선물옵션 (23개 API)

#### A. FuturesPriceAPI (시세 조회, 11개)

| 메서드명 | TR_ID | Endpoint | 설명 |
|---------|-------|----------|------|
| `display_board_callput()` | FHPIF05030100 | `/domestic-futureoption/v1/quotations/display-board-callput` | 옵션 콜/풋 전광판 |
| `display_board_futures()` | FHPIF05030200 | `/domestic-futureoption/v1/quotations/display-board-futures` | 선물 전광판 |
| `display_board_option_list()` | FHPIF05030300 | `/domestic-futureoption/v1/quotations/display-board-option-list` | 옵션 목록 |
| `display_board_top()` | FHPIF05020000 | `/domestic-futureoption/v1/quotations/display-board-top` | 상위 종목 |
| `exp_price_trend()` | FHMIF12060000 | `/domestic-futureoption/v1/quotations/exp-price-trend` | 예상 가격 추이 |
| `get_price()` | FHMIF10000000 | `/domestic-futureoption/v1/quotations/inquire-price` | 현재가 조회 |
| `get_orderbook()` | FHMIF10010000 | `/domestic-futureoption/v1/quotations/inquire-asking-price` | 호가 조회 |
| `inquire_daily_fuopchartprice()` | FHMIF10050200 | `/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice` | 일별 차트 |
| `inquire_time_fuopchartprice()` | FHMIF10050300 | `/domestic-futureoption/v1/quotations/inquire-time-fuopchartprice` | 시간별 차트 |
| `inquire_daily_amount_fee()` | FHMIF12070000 | `/domestic-futureoption/v1/quotations/inquire-daily-amount-fee` | 일별 거래량/수수료 |
| `inquire_ccnl_bstime()` | FHMIF10020000 | `/domestic-futureoption/v1/quotations/inquire-ccnl-bstime` | 시간대별 체결 |

#### B. FuturesAccountAPI (계좌/잔고, 6개)

| 메서드명 | TR_ID | Endpoint | 설명 |
|---------|-------|----------|------|
| `inquire_balance()` | CTFO6118R | `/domestic-futureoption/v1/trading/inquire-balance` | 잔고 조회 |
| `inquire_balance_settlement_pl()` | CTFO6119R | `/domestic-futureoption/v1/trading/inquire-balance-settlement-pl` | 청산손익 조회 |
| `inquire_balance_valuation_pl()` | CTFO6120R | `/domestic-futureoption/v1/trading/inquire-balance-valuation-pl` | 평가손익 조회 |
| `inquire_deposit()` | CTFO6122R | `/domestic-futureoption/v1/trading/inquire-deposit` | 예수금 조회 |
| `inquire_ngt_balance()` | CTFM6118R | `/domestic-futureoption/v1/trading/inquire-ngt-balance` | 야간 잔고 조회 |
| `ngt_margin_detail()` | CTFM6123R | `/domestic-futureoption/v1/trading/ngt-margin-detail` | 야간 증거금 상세 |

#### C. FuturesOrderAPI (주문/체결, 6개)

| 메서드명 | TR_ID | Endpoint | 설명 |
|---------|-------|----------|------|
| `inquire_ccnl()` | CTFO6121R | `/domestic-futureoption/v1/trading/inquire-ccnl` | 체결 내역 |
| `inquire_ngt_ccnl()` | CTFM6121R | `/domestic-futureoption/v1/trading/inquire-ngt-ccnl` | 야간 체결 |
| `inquire_psbl_order()` | CTFO6124R | `/domestic-futureoption/v1/trading/inquire-psbl-order` | 주문 가능 수량 |
| `inquire_psbl_ngt_order()` | CTFM6124R | `/domestic-futureoption/v1/trading/inquire-psbl-ngt-order` | 야간 주문 가능 |
| `order()` | CTFC0010U/CTFC0011U | `/domestic-futureoption/v1/trading/order` | 주문 실행 |
| `order_rvsecncl()` | CTFC0020U/CTFC0021U | `/domestic-futureoption/v1/trading/order-rvsecncl` | 정정/취소 |

### 3.2 해외선물옵션 (31개 API)

구조는 국내와 유사하지만 endpoint와 TR_ID가 다름:

```python
# pykis/overseas_futures/__init__.py

class OverseasFutures(BaseAPI):
    """
    해외선물옵션 API 통합 Facade
    """

    def __init__(self, client, account_info=None, _from_agent=False):
        super().__init__(client, account_info, _from_agent=_from_agent)

        self.price = OverseasFuturesPriceAPI(...)
        self.account = OverseasFuturesAccountAPI(...)
        self.order = OverseasFuturesOrderAPI(...)
```

**주요 메서드** (31개 전체 목록은 Linear 이슈 참조):
- 시세: `inquire_price()`, `inquire_asking_price()`, 차트 API 등
- 계좌: `inquire_deposit()`, `inquire_psamount()`, `inquire_ccld()` 등
- 주문: 주문/정정/취소, 미체결 조회 등

---

## 4. Agent 통합

### 4.1 Agent 클래스 확장

```python
# pykis/core/agent.py

from ..futures import Futures
from ..overseas_futures import OverseasFutures

class Agent(...):
    def __init__(self, ...):
        # ... 기존 초기화 ...

        # 선물옵션 API 초기화
        self._futures: Optional[Futures] = None
        self._overseas_futures: Optional[OverseasFutures] = None

    @property
    def futures(self) -> Futures:
        """
        국내선물옵션 API

        Example:
            >>> price = agent.futures.get_price("101S12")  # KOSPI200 선물
            >>> balance = agent.futures.account.inquire_balance()
        """
        if self._futures is None:
            self._futures = Futures(
                self.client, self.account_info, _from_agent=True
            )
        return self._futures

    @property
    def overseas_futures(self) -> OverseasFutures:
        """
        해외선물옵션 API

        Example:
            >>> price = agent.overseas_futures.get_price("ESZ4")  # S&P500 선물
        """
        if self._overseas_futures is None:
            self._overseas_futures = OverseasFutures(
                self.client, self.account_info, _from_agent=True
            )
        return self._overseas_futures
```

### 4.2 사용 예시

```python
from pykis import Agent

agent = Agent(
    app_key="...",
    app_secret="...",
    account_no="12345678",
    account_code="03"  # 선물옵션 계좌
)

# 국내선물옵션 시세 조회
price = agent.futures.get_price("101S12")  # KOSPI200 선물
print(price['output']['fuop_prpr'])  # 선물옵션 현재가

# 호가 조회
orderbook = agent.futures.get_orderbook("201S12")  # KOSPI200 옵션
print(orderbook['output1'])

# 잔고 조회
balance = agent.futures.account.inquire_balance()
print(balance['output'])

# 주문 실행
result = agent.futures.order.order(
    code="101S12",
    order_type="01",  # 매수
    qty="1",
    price="340.50"
)

# 해외선물옵션
overseas_price = agent.overseas_futures.get_price("ESZ4")
```

---

## 5. TypedDict 응답 모델 설계

### 5.1 국내선물옵션 응답

```python
# pykis/responses/futures.py

from typing import TypedDict, List, Optional

class FuturesPriceOutput(TypedDict):
    """선물옵션 현재가 응답 (output)"""
    fuop_prpr: str  # 선물옵션 현재가
    prdy_vrss: str  # 전일 대비
    prdy_ctrt: str  # 전일 대비율
    acml_vol: str   # 누적 거래량
    # ... 추가 필드 (open-trading-api 샘플 참조)

class FuturesPriceResponse(TypedDict):
    """선물옵션 현재가 조회 응답"""
    rt_cd: str      # 응답코드
    msg_cd: str     # 메시지코드
    msg1: str       # 메시지
    output: FuturesPriceOutput

class FuturesOrderbookOutput1(TypedDict):
    """선물옵션 호가 응답 (매도호가)"""
    askp1: str      # 매도호가1
    askp_rsqn1: str # 매도호가잔량1
    # ...

class FuturesOrderbookOutput2(TypedDict):
    """선물옵션 호가 응답 (매수호가)"""
    bidp1: str      # 매수호가1
    bidp_rsqn1: str # 매수호가잔량1
    # ...

class FuturesOrderbookResponse(TypedDict):
    """선물옵션 호가 조회 응답"""
    rt_cd: str
    msg_cd: str
    msg1: str
    output1: FuturesOrderbookOutput1
    output2: FuturesOrderbookOutput2

# ... 기타 응답 모델 (23개 API 각각)
```

### 5.2 해외선물옵션 응답

```python
# pykis/responses/overseas_futures.py

class OverseasFuturesPriceOutput(TypedDict):
    """해외선물옵션 현재가 응답"""
    # 필드명은 API 문서 기준으로 정의
    # ...
```

---

## 6. API Endpoints 확장

### 6.1 client.py 수정

```python
# pykis/core/client.py

API_ENDPOINTS = {
    # ... 기존 endpoint ...

    # === 국내선물옵션 시세 ===
    "FUTURES_DISPLAY_BOARD_CALLPUT": "/uapi/domestic-futureoption/v1/quotations/display-board-callput",
    "FUTURES_DISPLAY_BOARD_FUTURES": "/uapi/domestic-futureoption/v1/quotations/display-board-futures",
    "FUTURES_DISPLAY_BOARD_OPTION_LIST": "/uapi/domestic-futureoption/v1/quotations/display-board-option-list",
    "FUTURES_DISPLAY_BOARD_TOP": "/uapi/domestic-futureoption/v1/quotations/display-board-top",
    "FUTURES_EXP_PRICE_TREND": "/uapi/domestic-futureoption/v1/quotations/exp-price-trend",
    "FUTURES_INQUIRE_PRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-price",
    "FUTURES_INQUIRE_ASKING_PRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-asking-price",
    "FUTURES_INQUIRE_DAILY_FUOPCHARTPRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-daily-fuopchartprice",
    "FUTURES_INQUIRE_TIME_FUOPCHARTPRICE": "/uapi/domestic-futureoption/v1/quotations/inquire-time-fuopchartprice",
    "FUTURES_INQUIRE_DAILY_AMOUNT_FEE": "/uapi/domestic-futureoption/v1/quotations/inquire-daily-amount-fee",
    "FUTURES_INQUIRE_CCNL_BSTIME": "/uapi/domestic-futureoption/v1/quotations/inquire-ccnl-bstime",

    # === 국내선물옵션 계좌/잔고 ===
    "FUTURES_INQUIRE_BALANCE": "/uapi/domestic-futureoption/v1/trading/inquire-balance",
    "FUTURES_INQUIRE_BALANCE_SETTLEMENT_PL": "/uapi/domestic-futureoption/v1/trading/inquire-balance-settlement-pl",
    "FUTURES_INQUIRE_BALANCE_VALUATION_PL": "/uapi/domestic-futureoption/v1/trading/inquire-balance-valuation-pl",
    "FUTURES_INQUIRE_DEPOSIT": "/uapi/domestic-futureoption/v1/trading/inquire-deposit",
    "FUTURES_INQUIRE_NGT_BALANCE": "/uapi/domestic-futureoption/v1/trading/inquire-ngt-balance",
    "FUTURES_NGT_MARGIN_DETAIL": "/uapi/domestic-futureoption/v1/trading/ngt-margin-detail",

    # === 국내선물옵션 주문/체결 ===
    "FUTURES_INQUIRE_CCNL": "/uapi/domestic-futureoption/v1/trading/inquire-ccnl",
    "FUTURES_INQUIRE_NGT_CCNL": "/uapi/domestic-futureoption/v1/trading/inquire-ngt-ccnl",
    "FUTURES_INQUIRE_PSBL_ORDER": "/uapi/domestic-futureoption/v1/trading/inquire-psbl-order",
    "FUTURES_INQUIRE_PSBL_NGT_ORDER": "/uapi/domestic-futureoption/v1/trading/inquire-psbl-ngt-order",
    "FUTURES_ORDER": "/uapi/domestic-futureoption/v1/trading/order",
    "FUTURES_ORDER_RVSECNCL": "/uapi/domestic-futureoption/v1/trading/order-rvsecncl",

    # === 해외선물옵션 ===
    "OVERSEAS_FUTURES_INQUIRE_PRICE": "/uapi/overseas-futureoption/v1/quotations/inquire-price",
    # ... 31개 전체 (별도 문서 참조)
}
```

---

## 7. 구현 우선순위

### Phase 1: 국내선물옵션 (Week 1-2)
1. ✅ 아키텍처 설계 완료
2. API endpoint 정의 (`client.py` 수정)
3. `FuturesPriceAPI` 구현 (11개 메서드)
4. `FuturesAccountAPI` 구현 (6개 메서드)
5. `FuturesOrderAPI` 구현 (6개 메서드)
6. `Futures` Facade 통합
7. TypedDict 응답 모델 정의
8. Agent 통합 (`agent.futures` 속성)
9. 한국어 docstring 작성

### Phase 2: 해외선물옵션 (Week 3)
1. `OverseasFuturesPriceAPI` 구현
2. `OverseasFuturesAccountAPI` 구현
3. `OverseasFuturesOrderAPI` 구현
4. `OverseasFutures` Facade 통합
5. TypedDict 응답 모델 정의
6. Agent 통합 (`agent.overseas_futures`)

### Phase 3: 테스트 & 문서화 (Week 4)
1. 단위 테스트 (mock 기반)
2. 통합 테스트 (선택적, 실제 계좌 필요)
3. CHANGELOG.md 업데이트
4. README.md 예제 추가
5. API 레퍼런스 문서

---

## 8. 기술 요구사항

### 8.1 코딩 표준
- ✅ TypedDict 응답 모델 필수
- ✅ 한국어 docstring (API 필드명 1:1 매칭)
- ✅ Facade 패턴 준수
- ✅ BaseAPI 상속으로 캐싱/Rate Limiting 자동 적용
- ✅ `_make_request_dict()` 메서드 사용

### 8.2 성능 최적화
- Rate Limiting: 기존 RateLimiter 활용 (18 RPS / 900 RPM)
- 캐싱: TTL 5초 기본 (시세 데이터)
- 멀티스레드 안전성 보장

### 8.3 테스트 커버리지
- 목표: 60%+
- 우선순위: `futures/price_api.py` > `futures/account_api.py` > `futures/order_api.py`

---

## 9. 참고 자료

- **open-trading-api**: `/home/unohee/dev/tools/pykis/open-trading-api/`
- **샘플 코드**:
  - `examples_user/domestic_futureoption/domestic_futureoption_functions.py`
  - `examples_user/overseas_futureoption/overseas_futureoption_functions.py`
- **API 문서**: `한국투자증권_오픈API_전체문서_20251212_030000.xlsx`
- **기존 구조 참고**: `pykis/stock/` 모듈

---

## 10. 변경 이력

- **2026-01-19**: v1.0 초안 작성 (아키텍처 설계 완료)
