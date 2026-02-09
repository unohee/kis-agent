# PyKIS 거래내역 유틸리티 API 문서

##  API 개요
PyKIS 거래내역 Excel 내보내기 유틸리티의 공개 API 인터페이스를 정의합니다.

**테스트 커버리지:** 98%   
**최신 업데이트:** 2025-08-22

## 🏗️ 클래스 참조

### TradingReportGenerator

계좌 거래내역을 조회하고 Excel 파일로 내보내는 핵심 클래스입니다.

#### 초기화
```python
TradingReportGenerator(
    client: KISClient,
    account_info: Dict[str, str]
)
```

**매개변수:**
- `client`: KISClient 인스턴스 (필수)
- `account_info`: 계좌 정보 딕셔너리 (필수)
  - `CANO`: 계좌번호
  - `ACNT_PRDT_CD`: 계좌상품코드

**사용 예시:**
```python
from pykis import Agent
from pykis.utils.trading_report import TradingReportGenerator

agent = Agent(env_path=".env")
generator = TradingReportGenerator(
    client=agent.client,
    account_info={'CANO': 'your_account', 'ACNT_PRDT_CD': '01'}
)
```

#### 메서드

##### export_to_excel()
```python
export_to_excel(
    start_date: str,
    end_date: str,
    output_path: Optional[str] = None,
    tickers: Optional[List[str]] = None,
    only_executed: bool = True,
    separate_sheets: bool = False
) -> str
```

거래내역을 Excel 파일로 내보냅니다.

**매개변수:**
- `start_date`: 시작일 (YYYYMMDD 형식, 필수)
- `end_date`: 종료일 (YYYYMMDD 형식, 필수)
- `output_path`: 출력 파일 경로 (None이면 자동 생성)
- `tickers`: 조회할 종목 리스트 (None이면 전체)
- `only_executed`: True면 체결된 거래만 필터링
- `separate_sheets`: True면 종목별로 시트 분리

**반환값:** 생성된 Excel 파일 경로 (문자열)

**예외:**
- `ValueError`: 잘못된 날짜 형식
- `Exception`: API 조회 실패 시

**사용 예시:**
```python
# 기본 사용법
report_path = generator.export_to_excel('20250101', '20250131')

# 특정 종목만 필터링
report_path = generator.export_to_excel(
    '20250101', '20250131',
    tickers=['005930', '035420'],
    output_path='samsung_naver_trades.xlsx'
)

# 모든 거래 (체결/미체결 포함)
report_path = generator.export_to_excel(
    '20250101', '20250131',
    only_executed=False
)
```

##### get_trading_history()
```python
get_trading_history(
    start_date: str,
    end_date: str,
    tickers: Optional[List[str]] = None,
    only_executed: bool = True
) -> pd.DataFrame
```

거래내역을 DataFrame으로 조회합니다.

**매개변수:**
- `start_date`: 시작일 (YYYYMMDD 형식)
- `end_date`: 종료일 (YYYYMMDD 형식) 
- `tickers`: 조회할 종목 리스트 (선택사항)
- `only_executed`: 체결된 거래만 조회 여부

**반환값:** 거래내역 DataFrame

**DataFrame 컬럼:**
- `ord_dt`: 주문일자
- `ord_gno_brno`: 주문채번지점번호
- `odno`: 주문번호
- `orgn_odno`: 원주문번호
- `ord_dvsn_name`: 주문구분명
- `sll_buy_dvsn_cd_name`: 매도매수구분코드명
- `pdno`: 상품번호 (종목코드)
- `prdt_name`: 상품명 (종목명)
- `ord_qty`: 주문수량
- `ord_unpr`: 주문단가
- `ord_tmd`: 주문시각
- `tot_ccld_qty`: 총체결수량
- `avg_prvs`: 평균가
- `cncl_yn`: 취소여부
- `tot_ccld_amt`: 총체결금액
- `loan_dt`: 대출일자
- `ord_dvsn_cd`: 주문구분코드
- `sll_buy_dvsn_cd`: 매도매수구분코드

##  편의 함수

### generate_trading_report()
```python
generate_trading_report(
    client: KISClient,
    account_info: Dict[str, str],
    start_date: str,
    end_date: str,
    output_path: Optional[str] = None,
    tickers: Optional[List[str]] = None,
    only_executed: bool = True,
    separate_sheets: bool = False
) -> str
```

거래내역 Excel 생성을 위한 편의 함수입니다.

**매개변수:** `TradingReportGenerator.export_to_excel()`과 동일하며, `client`와 `account_info`가 추가됨

**반환값:** 생성된 Excel 파일 경로

**사용 예시:**
```python
from pykis import Agent
from pykis.utils.trading_report import generate_trading_report

agent = Agent(env_path=".env")

# 간단한 사용법
report_path = generate_trading_report(
    client=agent.client,
    account_info={'CANO': 'your_account', 'ACNT_PRDT_CD': '01'},
    start_date='20250101',
    end_date='20250131'
)

print(f"거래내역이 저장되었습니다: {report_path}")
```

##  Excel 출력 형식

생성되는 Excel 파일은 다음과 같은 구조를 갖습니다:

### 기본 시트 구조
- **Sheet명:** "거래내역"
- **헤더 스타일:** 파란색 배경, 굵은 글씨
- **데이터 정렬:** 주문일자 내림차순
- **컬럼 자동 조정:** 내용에 맞게 폭 자동 조정

### 종목별 시트 분리 (separate_sheets=True)
- 각 종목별로 별도 시트 생성
- **Sheet명:** "{종목코드}_{종목명}"
- 동일한 스타일 적용

### 필터링 결과 표시
파일명에 필터링 조건이 자동으로 포함됩니다:
- 기본: `trading_report_YYYYMMDD_YYYYMMDD.xlsx`
- 특정 종목: `trading_report_005930_035420_YYYYMMDD_YYYYMMDD.xlsx`
- 체결된 거래만: 파일명에 `_executed` 추가

## 🔒 보안 고려사항

- 계좌번호와 같은 민감한 정보는 Excel 파일에 직접 저장되지 않음
- API 호출 실패 시 빈 DataFrame 반환하여 안전한 오류 처리
- 로깅을 통한 오류 추적 가능

##  성능 특성

- **API 호출 최적화:** 날짜 범위별 배치 처리
- **메모리 효율성:** 대용량 거래내역도 스트리밍 방식으로 처리
- **오류 복구:** 네트워크 오류 시 자동 재시도 (AccountAPI 레벨)

##  테스트 커버리지

현재 98%의 높은 테스트 커버리지를 달성하고 있으며, 다음 시나리오들이 검증되었습니다:

-  정상적인 거래내역 조회 및 Excel 생성
-  특정 종목 필터링
-  체결된 거래만 필터링  
-  빈 거래내역 처리
-  API 오류 시 안전한 처리
-  잘못된 매개변수 처리
-  Excel 파일 생성 및 형식 검증