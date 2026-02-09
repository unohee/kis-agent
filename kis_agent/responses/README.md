# PyKIS Response Types

한국투자증권 OpenAPI 응답 구조를 TypedDict로 정의한 타입 힌팅 전용 패키지입니다.

## 개요

이 패키지는 **순수 타입 힌팅 용도**로, 런타임 동작에는 영향을 주지 않습니다. IDE 자동완성과 타입 체커(mypy, pyright 등)를 통한 개발 생산성 향상을 목표로 합니다.

## 디렉토리 구조

```
pykis/responses/
├── __init__.py      # 패키지 진입점 및 전체 export
├── common.py        # BaseResponse 등 공통 응답 구조
├── stock.py         # 주식 시세, 호가, 분봉 등 Stock API 응답
├── account.py       # 계좌 잔고, 체결내역 등 Account API 응답
├── order.py         # 주문 실행, 정정/취소 등 Order API 응답
└── README.md        # 이 문서
```

## 지원하는 API

### Stock API (stock.py)
- `StockPriceResponse` - get_stock_price() 주식 현재가 조회
- `DailyPriceResponse` - get_daily_price() 일별 시세 조회
- `OrderbookResponse` - get_orderbook() 호가 정보 조회
- `MinutePriceResponse` - get_minute_price() 분봉 시세 조회
- `StockInvestorResponse` - get_stock_investor() 투자자 매매 동향
- `InquireTimeItemconclusionResponse` - inquire_time_itemconclusion() 시간대별 체결
- `InquireCcnlResponse` - inquire_ccnl() 주식 체결 조회
- `SearchStockInfoResponse` - search_stock_info() 주식 기본정보 조회

### Account API (account.py)
- `AccountBalanceResponse` - get_account_balance() 계좌 잔고 조회
- `PossibleOrderResponse` - get_possible_order_amount() 매수가능금액 조회
- `InquireDailyCcldResponse` - inquire_daily_ccld() 일별 주문체결 조회
- `InquirePsblSellResponse` - inquire_psbl_sell() 매도가능수량 조회
- `GetTotalAssetResponse` - get_total_asset() 총자산평가 조회
- `InquireBalanceRlzPlResponse` - inquire_balance_rlz_pl() 잔고실현손익 조회

### Order API (order.py)
- `OrderCashResponse` - order_cash() 현금 주문 (매수/매도)
- `OrderCreditBuyResponse` - order_credit_buy() 신용 매수 주문
- `OrderCreditSellResponse` - order_credit_sell() 신용 매도 주문
- `OrderRvsecnclResponse` - order_rvsecncl() 주문 정정/취소
- `InquirePsblRvsecnclResponse` - inquire_psbl_rvsecncl() 정정취소가능주문 조회
- `OrderResvResponse` - order_resv() 예약 주문
- `OrderResvRvsecnclResponse` - order_resv_rvsecncl() 예약주문 정정/취소
- `OrderResvCcnlResponse` - order_resv_ccnl() 예약주문 조회

## 사용 예시

### 1. 기존 API 함수에 타입 힌트 추가

```python
from typing import Optional
from kis_agent.responses.stock import StockPriceResponse

def get_stock_price(code: str) -> Optional[StockPriceResponse]:
    """주식 현재가 조회 (타입 힌트 포함)"""
    return self._make_request_dict(
        endpoint=API_ENDPOINTS["INQUIRE_PRICE"],
        tr_id="FHKST01010100",
        params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
    )
```

### 2. 응답 필드 자동완성 활용

```python
from kis_agent.responses.stock import StockPriceResponse

def analyze_stock_price(response: StockPriceResponse) -> None:
    """
    IDE가 자동으로 사용 가능한 필드를 제안합니다:
    - response["rt_cd"]
    - response["output"]["stck_prpr"]
    - response["output"]["prdy_vrss"]
    - response["output"]["acml_vol"]
    등등...
    """
    if response["rt_cd"] == "0":
        output = response["output"]
        current_price = output["stck_prpr"]  # ✅ 자동완성 지원
        change = output["prdy_vrss"]         # ✅ 자동완성 지원
        print(f"현재가: {current_price}, 전일대비: {change}")
```

### 3. 계좌 잔고 조회 예시

```python
from kis_agent.responses.account import AccountBalanceResponse

def get_holdings(response: AccountBalanceResponse) -> list:
    """보유 종목 리스트 추출"""
    if response["rt_cd"] == "0":
        holdings = []
        for item in response["output1"]:
            holdings.append({
                "종목코드": item["pdno"],              # ✅ 자동완성
                "종목명": item["prdt_name"],          # ✅ 자동완성
                "보유수량": item["hldg_qty"],         # ✅ 자동완성
                "평가손익": item["evlu_pfls_amt"],    # ✅ 자동완성
            })
        return holdings
    return []
```

### 4. 일별 체결내역 조회 예시

```python
from kis_agent.responses.account import InquireDailyCcldResponse

def analyze_trades(response: InquireDailyCcldResponse) -> None:
    """일별 체결내역 분석"""
    if response["rt_cd"] == "0":
        # output1: 개별 체결 내역
        for trade in response["output1"]:
            print(f"종목: {trade['prdt_name']}")     # ✅ 자동완성
            print(f"수량: {trade['tot_ccld_qty']}")  # ✅ 자동완성
            print(f"금액: {trade['tot_ccld_amt']}")  # ✅ 자동완성

        # output2: 요약 정보
        summary = response["output2"]
        print(f"총 체결수량: {summary['tot_ccld_qty']}")    # ✅ 자동완성
        print(f"총 체결금액: {summary['tot_ccld_amt']}")    # ✅ 자동완성
        print(f"추정 수수료: {summary['prsm_tlex_smtl']}")  # ✅ 자동완성
```

### 5. 주문 응답 처리 예시

```python
from kis_agent.responses.order import OrderCashResponse

def process_order_result(response: OrderCashResponse) -> str:
    """주문 결과 처리"""
    if response["rt_cd"] == "0":
        output = response["output"]
        order_no = output["ODNO"]     # ✅ 자동완성
        order_time = output["ORD_TMD"]  # ✅ 자동완성
        return f"주문 성공 - 주문번호: {order_no}, 시각: {order_time}"
    else:
        return f"주문 실패 - {response['msg1']}"
```

## 주의사항

### 1. TypedDict의 total=False

대부분의 TypedDict는 `total=False`로 정의되어 있어, 모든 필드가 선택적(Optional)입니다. 이는 API 응답에 특정 필드가 없을 수 있기 때문입니다.

```python
# ✅ 안전한 접근 방법
output = response.get("output", {})
price = output.get("stck_prpr", "0")

# ⚠️  위험한 접근 방법 (KeyError 발생 가능)
price = response["output"]["stck_prpr"]
```

### 2. 런타임 검증 없음

TypedDict는 **정적 타입 체커**에서만 동작하며, 런타임에서는 일반 dict와 동일합니다.

```python
# 타입 체커에서만 오류 감지
response: StockPriceResponse = {"invalid": "data"}  # ❌ mypy 오류
# 하지만 런타임에서는 정상 실행됨
```

### 3. 실제 API 응답과의 일치 보장

이 타입 정의는 한국투자증권 API 문서와 실제 테스트 응답을 기반으로 작성되었으나, API 버전 업데이트에 따라 필드가 추가/변경/삭제될 수 있습니다.

## 타입 체커 설정

### mypy

`mypy.ini` 또는 `pyproject.toml`:

```ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### pyright

`pyrightconfig.json`:

```json
{
  "typeCheckingMode": "basic",
  "pythonVersion": "3.8"
}
```

## 기여 및 이슈

새로운 API 응답 타입 추가 또는 기존 타입 수정이 필요한 경우:

1. 실제 API 응답 구조 확인
2. 해당하는 모듈(stock.py, account.py, order.py)에 TypedDict 추가
3. `__init__.py`에서 export 추가
4. 이 README에 사용 예시 추가

## 버전

- **v1.2.0**: 초기 릴리스
  - Stock API 8개 응답 타입
  - Account API 6개 응답 타입
  - Order API 8개 응답 타입
  - 총 22개 응답 타입 지원
