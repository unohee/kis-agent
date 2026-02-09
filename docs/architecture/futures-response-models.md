# Futures Response TypedDict 모델 설계

**작성일**: 2026-01-19
**관련 이슈**: [INT-506](https://linear.app/intrect/issue/INT-506)

---

## 1. 개요

선물옵션 API 응답을 위한 TypedDict 모델 설계입니다. 기존 `pykis/responses/stock.py` 구조를 참고하여 일관성을 유지합니다.

### 설계 원칙
- ✅ 모든 응답은 `BaseResponse` 상속
- ✅ 필드명은 한국투자증권 API 응답 그대로 사용 (예: `fuop_prpr`, `prdy_vrss`)
- ✅ 한국어 주석으로 필드 설명 (API 필드명 1:1 매칭)
- ✅ `total=False` 옵션으로 선택적 필드 지원
- ✅ List 타입은 명시적으로 정의 (예: `output1: List[FuturesOrderbookRow]`)

---

## 2. 파일 구조

```
pykis/responses/
├── common.py                # BaseResponse (공통)
├── stock.py                 # 주식 응답 (기존)
├── futures.py               # 국내선물옵션 응답 (신규)
└── overseas_futures.py      # 해외선물옵션 응답 (신규)
```

---

## 3. 국내선물옵션 TypedDict (futures.py)

### 3.1 기본 응답 구조

```python
# pykis/responses/futures.py

from typing import List, TypedDict
from .common import BaseResponse

# ============================================================
# 1. inquire_price() - 선물옵션 현재가 조회
# ============================================================

class FuturesPriceOutput(TypedDict, total=False):
    """선물옵션 현재가 조회 output 필드"""

    # 기본 가격 정보
    fuop_prpr: str          # 선물옵션 현재가 (Future/Option Present Price)
    prdy_vrss: str          # 전일 대비 (Previous Day Versus)
    prdy_vrss_sign: str     # 전일 대비 부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)
    prdy_ctrt: str          # 전일 대비율 (Previous Day Change Rate) %
    fuop_oprc: str          # 선물옵션 시가 (Future/Option Opening Price)
    fuop_hgpr: str          # 선물옵션 최고가 (Future/Option High Price)
    fuop_lwpr: str          # 선물옵션 최저가 (Future/Option Low Price)
    fuop_sdpr: str          # 선물옵션 기준가 (Future/Option Standard Price)

    # 거래량/미결제 정보
    acml_vol: str           # 누적 거래량 (Accumulated Volume)
    acml_tr_pbmn: str       # 누적 거래대금 (Accumulated Trade Price By Million)
    optn_open_intr_vol: str # 옵션 미결제 약정량 (Option Open Interest Volume)
    fuop_open_intr_vol: str # 선물 미결제 약정량

    # 종목 정보
    hts_kor_isnm: str       # HTS 한글 종목명 (HTS Korean Issue Name)
    item_code: str          # 종목코드
    fuop_kind_code: str     # 선물옵션 종류 코드 (F:선물, C:콜옵션, P:풋옵션)
    bstp_nmix_prpr: str     # 업종 지수 현재가
    bstp_nmix_prdy_vrss: str  # 업종 지수 전일대비

    # 이론가/내재변동성 (옵션)
    optn_theo_pric: str     # 옵션 이론가격 (Option Theoretical Price)
    impl_vola: str          # 내재변동성 (Implied Volatility)
    optn_delta: str         # 옵션 델타 (Option Delta)
    optn_gamma: str         # 옵션 감마 (Option Gamma)
    optn_theta: str         # 옵션 세타 (Option Theta)
    optn_vega: str          # 옵션 베가 (Option Vega)

    # 추가 정보
    lstn_avrg_pric: str     # 상장 평균가
    mrkt_warn_cls_code: str # 시장경고구분코드
    sbst_pric: str          # 대용가격 (Substitute Price)

class FuturesPriceResponse(BaseResponse):
    """선물옵션 현재가 조회 응답"""
    output: FuturesPriceOutput


# ============================================================
# 2. inquire_asking_price() - 선물옵션 호가 조회
# ============================================================

class FuturesOrderbookOutput1(TypedDict, total=False):
    """선물옵션 호가 응답 - 매도호가"""
    askp1: str              # 매도호가1 (Ask Price 1)
    askp_rsqn1: str         # 매도호가잔량1 (Ask Price Residual Quantity 1)
    askp2: str              # 매도호가2
    askp_rsqn2: str         # 매도호가잔량2
    askp3: str              # 매도호가3
    askp_rsqn3: str         # 매도호가잔량3
    askp4: str              # 매도호가4
    askp_rsqn4: str         # 매도호가잔량4
    askp5: str              # 매도호가5
    askp_rsqn5: str         # 매도호가잔량5
    askp6: str              # 매도호가6
    askp_rsqn6: str         # 매도호가잔량6
    askp7: str              # 매도호가7
    askp_rsqn7: str         # 매도호가잔량7
    askp8: str              # 매도호가8
    askp_rsqn8: str         # 매도호가잔량8
    askp9: str              # 매도호가9
    askp_rsqn9: str         # 매도호가잔량9
    askp10: str             # 매도호가10
    askp_rsqn10: str        # 매도호가잔량10
    total_askp_rsqn: str    # 총 매도호가잔량

class FuturesOrderbookOutput2(TypedDict, total=False):
    """선물옵션 호가 응답 - 매수호가"""
    bidp1: str              # 매수호가1 (Bid Price 1)
    bidp_rsqn1: str         # 매수호가잔량1 (Bid Price Residual Quantity 1)
    bidp2: str              # 매수호가2
    bidp_rsqn2: str         # 매수호가잔량2
    bidp3: str              # 매수호가3
    bidp_rsqn3: str         # 매수호가잔량3
    bidp4: str              # 매수호가4
    bidp_rsqn4: str         # 매수호가잔량4
    bidp5: str              # 매수호가5
    bidp_rsqn5: str         # 매수호가잔량5
    bidp6: str              # 매수호가6
    bidp_rsqn6: str         # 매수호가잔량6
    bidp7: str              # 매수호가7
    bidp_rsqn7: str         # 매수호가잔량7
    bidp8: str              # 매수호가8
    bidp_rsqn8: str         # 매수호가잔량8
    bidp9: str              # 매수호가9
    bidp_rsqn9: str         # 매수호가잔량9
    bidp10: str             # 매수호가10
    bidp_rsqn10: str        # 매수호가잔량10
    total_bidp_rsqn: str    # 총 매수호가잔량

class FuturesOrderbookResponse(BaseResponse):
    """선물옵션 호가 조회 응답"""
    output1: FuturesOrderbookOutput1  # 매도호가
    output2: FuturesOrderbookOutput2  # 매수호가


# ============================================================
# 3. inquire_balance() - 선물옵션 잔고 조회
# ============================================================

class FuturesBalanceOutput(TypedDict, total=False):
    """선물옵션 잔고 조회 output 필드"""
    fuop_item_code: str     # 선물옵션 종목코드
    item_name: str          # 종목명
    futs_optn_kind_code: str  # 선물옵션종류코드 (F:선물, C:콜, P:풋)
    bstp_code: str          # 업종코드

    # 잔고 수량
    ord_psbl_qty: str       # 주문가능수량 (Order Possible Quantity)
    sll_buy_dvsn_cd: str    # 매도매수구분코드 (1:매도, 2:매수)
    bfdy_cprs_icdc: str     # 전일대비증감수량

    # 가격 정보
    avg_pric: str           # 평균가 (Average Price)
    prsnt_pric: str         # 현재가 (Present Price)
    fnoat_plamt: str        # 평가손익금액 (Floating Profit/Loss Amount)
    erng_rate: str          # 수익률 (Earning Rate) %

    # 청산/평가 정보
    lqd_amt: str            # 청산금액 (Liquidation Amount)
    lqd_psbl_qty: str       # 청산가능수량
    evlu_amt: str           # 평가금액 (Evaluation Amount)
    evlu_pfls_amt: str      # 평가손익금액

    # 증거금 정보
    dpsi_reqr_amt: str      # 예탁금필요금액 (Deposit Requirement Amount)
    maint_mrgn: str         # 유지증거금 (Maintenance Margin)
    ord_mrgn: str           # 주문증거금 (Order Margin)

class FuturesBalanceResponse(BaseResponse):
    """선물옵션 잔고 조회 응답"""
    output: List[FuturesBalanceOutput]  # 잔고 리스트


# ============================================================
# 4. inquire_daily_fuopchartprice() - 선물옵션 일별차트
# ============================================================

class FuturesDailyChartRow(TypedDict, total=False):
    """선물옵션 일별차트 행"""
    stck_bsop_date: str     # 주식영업일자 (YYYYMMDD)
    fuop_oprc: str          # 선물옵션 시가
    fuop_hgpr: str          # 선물옵션 최고가
    fuop_lwpr: str          # 선물옵션 최저가
    fuop_clpr: str          # 선물옵션 종가 (Close Price)
    acml_vol: str           # 누적거래량
    prdy_vrss: str          # 전일대비
    prdy_vrss_sign: str     # 전일대비부호
    prdy_ctrt: str          # 전일대비율
    optn_open_intr_vol: str # 옵션미결제약정량

class FuturesDailyChartResponse(BaseResponse):
    """선물옵션 일별차트 조회 응답"""
    output: List[FuturesDailyChartRow]


# ============================================================
# 5. order() - 선물옵션 주문
# ============================================================

class FuturesOrderOutput(TypedDict, total=False):
    """선물옵션 주문 응답 output"""
    odno: str               # 주문번호 (Order Number)
    ord_tmd: str            # 주문시각 (Order Time)
    ord_gno_brno: str       # 주문채번지점번호
    odno_brno: str          # 주문번호지점번호

class FuturesOrderResponse(BaseResponse):
    """선물옵션 주문 응답"""
    output: FuturesOrderOutput


# ============================================================
# 6. display_board_callput() - 옵션 콜/풋 전광판
# ============================================================

class DisplayBoardCallPutRow(TypedDict, total=False):
    """옵션 콜/풋 전광판 행"""
    item_code: str          # 종목코드
    item_name: str          # 종목명
    fuop_prpr: str          # 선물옵션 현재가
    prdy_vrss: str          # 전일대비
    prdy_ctrt: str          # 전일대비율
    acml_vol: str           # 누적거래량
    optn_theo_pric: str     # 옵션이론가
    impl_vola: str          # 내재변동성
    optn_delta: str         # 델타
    optn_gamma: str         # 감마

class DisplayBoardCallPutResponse(BaseResponse):
    """옵션 콜/풋 전광판 응답"""
    output1: List[DisplayBoardCallPutRow]  # 콜옵션 리스트
    output2: List[DisplayBoardCallPutRow]  # 풋옵션 리스트


# ============================================================
# __all__ 정의
# ============================================================

__all__ = [
    # 현재가/호가
    "FuturesPriceOutput",
    "FuturesPriceResponse",
    "FuturesOrderbookOutput1",
    "FuturesOrderbookOutput2",
    "FuturesOrderbookResponse",

    # 잔고/계좌
    "FuturesBalanceOutput",
    "FuturesBalanceResponse",

    # 차트
    "FuturesDailyChartRow",
    "FuturesDailyChartResponse",

    # 주문
    "FuturesOrderOutput",
    "FuturesOrderResponse",

    # 전광판
    "DisplayBoardCallPutRow",
    "DisplayBoardCallPutResponse",
]
```

---

## 4. 해외선물옵션 TypedDict (overseas_futures.py)

### 4.1 기본 응답 구조

```python
# pykis/responses/overseas_futures.py

from typing import List, TypedDict
from .common import BaseResponse

# ============================================================
# 1. inquire_price() - 해외선물옵션 현재가 조회
# ============================================================

class OverseasFuturesPriceOutput(TypedDict, total=False):
    """해외선물옵션 현재가 조회 output 필드"""

    # 기본 가격 정보
    last: str               # 현재가 (Last Price)
    diff: str               # 전일대비 (Difference)
    rate: str               # 등락률 (Rate) %
    open: str               # 시가 (Open Price)
    high: str               # 최고가 (High Price)
    low: str                # 최저가 (Low Price)
    volume: str             # 거래량 (Volume)

    # 미결제 정보
    open_interest: str      # 미결제약정 (Open Interest)
    settlement_price: str   # 정산가 (Settlement Price)

    # 종목 정보
    symb: str               # 심볼 (Symbol)
    name: str               # 종목명
    exch: str               # 거래소 (Exchange)
    tick_size: str          # 틱 사이즈
    contract_size: str      # 계약 크기

class OverseasFuturesPriceResponse(BaseResponse):
    """해외선물옵션 현재가 조회 응답"""
    output: OverseasFuturesPriceOutput


# ============================================================
# 2. inquire_deposit() - 해외선물옵션 예수금 조회
# ============================================================

class OverseasFuturesDepositOutput(TypedDict, total=False):
    """해외선물옵션 예수금 조회 output 필드"""
    ovrs_dps_amt: str       # 해외예수금액 (Overseas Deposit Amount)
    frcr_evlu_pfls_amt: str # 외화평가손익금액 (Foreign Currency Evaluation P/L)
    tot_evlu_pfls_amt: str  # 총평가손익금액
    frcr_buy_amt_smtl: str  # 외화매수금액합계
    ovrs_rlzt_pfls_amt: str # 해외실현손익금액
    nxdy_auto_rdpt_amt: str # 익일자동상환금액

class OverseasFuturesDepositResponse(BaseResponse):
    """해외선물옵션 예수금 조회 응답"""
    output: OverseasFuturesDepositOutput


# ============================================================
# __all__ 정의
# ============================================================

__all__ = [
    "OverseasFuturesPriceOutput",
    "OverseasFuturesPriceResponse",
    "OverseasFuturesDepositOutput",
    "OverseasFuturesDepositResponse",
]
```

---

## 5. 구현 가이드

### 5.1 필드명 추출 방법

1. **open-trading-api 샘플 코드 참조**
   - `examples_user/domestic_futureoption/domestic_futureoption_functions.py`
   - 함수 내 `params` 딕셔너리에서 요청 필드 확인
   - 응답 필드는 실제 API 호출로 확인 필요

2. **한국투자증권 공식 엑셀 문서**
   - `한국투자증권_오픈API_전체문서_20251212_030000.xlsx`
   - TR_ID별 입출력 필드 명세 확인

3. **실제 API 호출 테스트**
   - 개발 초기 단계에서 실제 API 호출 후 응답 구조 확인
   - `response.json()` 출력으로 전체 필드 파악

### 5.2 TypedDict 작성 우선순위

**Phase 1 (필수)**: 핵심 API 응답 모델
1. ✅ FuturesPriceResponse (현재가)
2. ✅ FuturesOrderbookResponse (호가)
3. ✅ FuturesBalanceResponse (잔고)
4. ✅ FuturesOrderResponse (주문)

**Phase 2 (중요)**: 차트/분봉 응답
5. FuturesDailyChartResponse (일별차트)
6. FuturesTimeChartResponse (분봉)

**Phase 3 (확장)**: 전광판/통계 응답
7. DisplayBoardCallPutResponse (옵션 전광판)
8. DisplayBoardFuturesResponse (선물 전광판)
9. ... (나머지 API 응답)

### 5.3 코딩 규칙

```python
# ✅ 좋은 예: total=False로 선택적 필드 지원
class FuturesPriceOutput(TypedDict, total=False):
    fuop_prpr: str  # 선물옵션 현재가
    prdy_vrss: str  # 전일 대비

# ✅ 좋은 예: List 타입 명시
class FuturesBalanceResponse(BaseResponse):
    output: List[FuturesBalanceOutput]

# ❌ 나쁜 예: 필드명 변경 (API와 불일치)
class FuturesPriceOutput(TypedDict):
    current_price: str  # ❌ fuop_prpr 사용해야 함

# ❌ 나쁜 예: 주석 누락
class FuturesPriceOutput(TypedDict):
    fuop_prpr: str  # ❌ 한국어 주석 필수
```

---

## 6. 테스트 방법

### 6.1 TypedDict 검증

```python
# tests/unit/responses/test_futures_response.py

from kis_agent.responses.futures import FuturesPriceResponse

def test_futures_price_response_structure():
    """선물옵션 현재가 응답 구조 검증"""
    response: FuturesPriceResponse = {
        "rt_cd": "0",
        "msg_cd": "MCA00000",
        "msg1": "정상 처리되었습니다.",
        "output": {
            "fuop_prpr": "340.50",
            "prdy_vrss": "1.50",
            "prdy_ctrt": "0.44",
            "acml_vol": "12345",
        }
    }

    assert response["rt_cd"] == "0"
    assert response["output"]["fuop_prpr"] == "340.50"
```

### 6.2 실제 API 응답 매칭 테스트

```python
@pytest.mark.integration
def test_futures_price_api_response():
    """실제 API 응답과 TypedDict 매칭 검증"""
    agent = Agent(...)
    response = agent.futures.get_price("101S12")

    # TypedDict 검증
    assert "output" in response
    assert "fuop_prpr" in response["output"]
    assert isinstance(response["output"]["fuop_prpr"], str)
```

---

## 7. 변경 이력

- **2026-01-19**: v1.0 초안 작성 (국내/해외 선물옵션 핵심 응답 모델 설계)
