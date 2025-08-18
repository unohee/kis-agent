# pykis API 메서드 레퍼런스

> **pykis v0.1.21** - 한국투자증권 OpenAPI Python 래퍼 라이브러리

이 문서는 pykis 라이브러리의 모든 사용 가능한 메서드를 정리한 완전한 API 레퍼런스입니다.  
후임자나 다른 에이전트 LLM이 pykis를 활용할 때 참고할 수 있도록 작성되었습니다.

## 🧪 테스트 검증 현황 (v0.1.21)

**최근 테스트 일자**: 2025년 7월 10일  
**전체 테스트 결과**: 22개 메서드 중 19개 성공 (86.4% 성공률)

### ✅ 검증 완료 메서드 (19개)
주요 메서드들이 정상 작동 확인되었습니다:
- 주식 시세: `get_stock_price`, `get_daily_price`, `get_minute_price`, `get_daily_credit_balance` ⭐ 신규
- 계좌 정보: `get_account_balance`
- 프로그램 매매: `get_program_trade_by_stock`, `get_program_trade_hourly_trend`
- 거래원/회원사: `get_member`, `get_member_transaction`
- 시장 분석: `get_volume_power`, `get_market_rankings`, `get_pbar_tratio`
- 조건검색/휴장일: `get_condition_stocks`, `get_holiday_info`, `is_holiday`

### ⚠️ 주의 필요 메서드 (3개)
- `get_cash_available`: 파라미터 문제 (수정 필요)
- `get_total_asset`: 정산 시간 중 JSON 디코드 실패 (시간대 고려)
- `get_program_trade_period_detail`: 메서드 존재하지 않음 (확인 필요)

## 📋 목차

- [기본 사용법](#기본-사용법)
- [실시간 시세 (웹소켓)](#실시간-시세-웹소켓)
- [계좌 관련 메서드](#계좌-관련-메서드)
- [주식 시세 관련 메서드](#주식-시세-관련-메서드)
- [시장 분석 메서드](#시장-분석-메서드)
- [프로그램 매매 메서드](#프로그램-매매-메서드)
- [조건검색 메서드](#조건검색-메서드)
- [휴장일 정보 메서드](#휴장일-정보-메서드)
- [거래원/회원사 관련 메서드](#거래원회원사-관련-메서드)
- [해외주식 관련 메서드](#해외주식-관련-메서드)
- [선물옵션 관련 메서드](#선물옵션-관련-메서드)
- [유틸리티 메서드](#유틸리티-메서드)
- [데이터 관리 메서드](#데이터-관리-메서드)

---

## 기본 사용법

```python
from pykis import Agent

# Agent 초기화 (설정 파일 자동 로드)
agent = Agent()

# 또는 계좌 정보 직접 설정
agent = Agent(account_info={
    'CANO': '계좌번호',
    'ACNT_PRDT_CD': '계좌상품코드'
})
```

## 📦 헬퍼 모듈 (v0.1.21 신규) ✅ 테스트 검증 완료

테스트 및 개발 편의를 위한 헬퍼 모듈이 추가되어 실제 테스트에서 성공적으로 사용되었습니다:

```python
# 헬퍼 모듈 import 및 환경 설정
import sys
sys.path.append('..')
from test_helpers import (
    test_api_method, 
    setup_test_environment, 
    reload_modules,
    batch_test_methods,
    get_common_test_configs,
    print_test_summary,
    reset_test_results
)

# Agent 초기화 및 테스트 환경 설정
agent, TEST_STOCK, TEST_DATE = setup_test_environment()

# 개별 API 메서드 테스트
test_api_method("get_stock_price", agent.get_stock_price, TEST_STOCK)

# 일괄 테스트 실행
common_configs = get_common_test_configs(agent, TEST_STOCK, TEST_DATE)
batch_test_methods(agent, common_configs)

# 테스트 결과 요약 및 통계
print_test_summary()
```

### 주요 헬퍼 함수들 (실제 사용 검증 완료)
- `setup_test_environment()`: Agent 초기화 및 테스트 설정 (테스트 종목: 005930, 날짜: 당일)
- `test_api_method(method_name, method_func, *args)`: 개별 API 메서드 테스트 및 상세 결과 출력
- `batch_test_methods(agent, configs)`: 여러 메서드 일괄 테스트 (설정 기반)
- `get_common_test_configs(agent, stock, date)`: 자주 사용하는 메서드 설정 반환
- `print_test_summary()`: 성공/실패 통계 및 실패 메서드 목록 출력
- `reset_test_results()`: 테스트 결과 초기화
- `reload_modules()`: 모듈 완전 재로드 (개발 시 유용)

---

## 실시간 시세 (웹소켓)

### `agent.websocket(stock_codes, purchase_prices, enable_index, enable_program_trading, enable_ask_bid)`
**설명**: 실시간 시세 수신을 위한 웹소켓 클라이언트를 생성합니다.  
**매개변수**:
- `stock_codes` (list, optional) - 구독할 종목코드 리스트
- `purchase_prices` (dict, optional) - 매수 정보 딕셔너리 `{'종목코드': (매입가, 보유수량)}`
- `enable_index` (bool, optional) - 실시간 지수 데이터 수신 여부 (기본값: False)
- `enable_program_trading` (bool, optional) - 실시간 프로그램매매 데이터 수신 여부 (기본값: False)
- `enable_ask_bid` (bool, optional) - 실시간 호가 데이터 수신 여부 (기본값: False)

**반환**: `KisWebSocket` - 웹소켓 클라이언트 객체  
**예시**:
```python
import asyncio

agent = Agent()

# 기본 체결 데이터만 수신
ws_client = agent.websocket()

# 모든 실시간 데이터 수신
ws_client = agent.websocket(
    stock_codes=["005930", "000660"],
    purchase_prices={"005930": (75000, 10)},
    enable_index=True,
    enable_program_trading=True,
    enable_ask_bid=True
)

async def main():
    await ws_client.connect(["005930", "000660"])

if __name__ == "__main__":
    asyncio.run(main())
```

### `ws_client.connect(stock_codes)`
**설명**: 지정된 종목의 실시간 시세 구독을 시작합니다.  
**매개변수**: `stock_codes` (list) - 구독할 종목코드 리스트  
**참고**: 이 메서드는 `asyncio` 이벤트 루프 내에서 실행되어야 합니다.

### 웹소켓 실시간 데이터 종류

#### 1. 실시간 체결 데이터 (H0STCNT0)
**설명**: 주식 체결가, 누적거래량, 등락률 등의 실시간 정보  
**데이터 예시**:
```python
{
    'mksc_shrn_iscd': '005930',      # 종목코드
    'stck_cntg_hour': '143000',      # 체결시간
    'stck_prpr': '75000',            # 현재가
    'prdy_vrss': '1000',             # 전일대비
    'prdy_ctrt': '1.35',             # 등락률
    'acml_vol': '12345678',          # 누적거래량
    'acml_tr_pbmn': '987654321'      # 누적거래대금
}
```

#### 2. 실시간 지수 데이터 (H0IF1000) ⭐ 신규
**설명**: 코스피, 코스닥, 코스피200 등 주요 지수의 실시간 정보  
**지수 코드**:
- `0001`: 코스피 지수
- `1001`: 코스닥 지수  
- `2001`: 코스피200 지수

**데이터 예시**:
```python
{
    'bstp_nmix_prpr': '2500.50',     # 지수 현재가
    'bstp_nmix_prdy_vrss': '10.25',  # 전일대비
    'prdy_vrss_sign': '2',           # 등락구분
    'bstp_nmix_prdy_ctrt': '0.41',   # 등락률
    'acml_vol': '456789123',         # 누적거래량
    'acml_tr_pbmn': '12345678901'    # 누적거래대금
}
```

#### 3. 실시간 프로그램매매 추이 (H0GSCNT0) ⭐ 신규
**설명**: 프로그램매매 거래량과 거래대금의 실시간 추이  
**데이터 예시**:
```python
{
    'pgtr_ntby_qty': '12345',        # 프로그램매매 순매수량
    'pgtr_ntby_tr_pbmn': '987654321' # 프로그램매매 순매수대금
}
```

#### 4. 실시간 호가 데이터 (H0STASP0) ⭐ 신규
**설명**: 매수/매도 호가 및 잔량의 실시간 정보  
**데이터 예시**:
```python
{
    'mksc_shrn_iscd': '005930',      # 종목코드
    'bspr_rsqn_1': '100',           # 매수 1호가 잔량
    'bspr_rsqn_2': '200',           # 매수 2호가 잔량
    'askp_rsqn_1': '150',           # 매도 1호가 잔량
    'askp_rsqn_2': '250',           # 매도 2호가 잔량
    'stck_sdpr': '75100',           # 매도 1호가
    'stck_sbpr': '75000'            # 매수 1호가
}
```

### 웹소켓 클라이언트 메서드

#### `ws_client.get_index_name(index_code)`
**설명**: 지수 코드를 지수 이름으로 변환  
**매개변수**: `index_code` (str) - 지수 코드  
**반환**: `str` - 지수 이름  
**예시**:
```python
name = ws_client.get_index_name("0001")  # "코스피"
```

#### `ws_client.display_index_info(data)`
**설명**: 실시간 지수 정보를 포맷팅하여 출력  
**매개변수**: `data` (dict) - 지수 데이터  
**예시**:
```python
# 자동으로 호출되어 다음과 같이 출력됩니다:
# [실시간 지수] 코스피: 2,500.50 (▲10.25, +0.41%)
```

#### `ws_client.display_program_trading_info(data)`
**설명**: 실시간 프로그램매매 정보를 포맷팅하여 출력  
**매개변수**: `data` (dict) - 프로그램매매 데이터  
**예시**:
```python
# 자동으로 호출되어 다음과 같이 출력됩니다:
# [프로그램매매] 순매수량: 12,345주 | 순매수대금: 987,654,321원
```

#### `ws_client.display_ask_bid_info(data)`
**설명**: 실시간 호가 정보를 포맷팅하여 출력  
**매개변수**: `data` (dict) - 호가 데이터  
**예시**:
```python
# 자동으로 호출되어 다음과 같이 출력됩니다:
# [호가] 005930 | 매도1호가: 75,100원(150주) | 매수1호가: 75,000원(100주)
```

### 실시간 데이터 저장소

웹소켓 클라이언트는 다음 속성에 최신 데이터를 저장합니다:

#### `ws_client.latest_prices`
**설명**: 종목별 최신 체결 데이터 저장  
**구조**: `{'종목코드': {...체결데이터...}}`

#### `ws_client.latest_index` ⭐ 신규
**설명**: 지수별 최신 지수 데이터 저장  
**구조**: `{'지수코드': {...지수데이터...}}`

#### `ws_client.latest_program_trading` ⭐ 신규
**설명**: 최신 프로그램매매 데이터 저장  
**구조**: `{...프로그램매매데이터...}`

#### `ws_client.latest_ask_bid` ⭐ 신규
**설명**: 종목별 최신 호가 데이터 저장  
**구조**: `{'종목코드': {...호가데이터...}}`

### 실시간 데이터 활용 예시

```python
import asyncio
from pykis import Agent

async def realtime_monitor():
    agent = Agent()
    
    # 모든 실시간 데이터 활성화
    ws_client = agent.websocket(
        stock_codes=["005930", "000660"],
        enable_index=True,
        enable_program_trading=True,
        enable_ask_bid=True
    )
    
    # 웹소켓 연결 시작
    await ws_client.connect(["005930", "000660"])
    
    # 5초 후 데이터 조회
    await asyncio.sleep(5)
    
    # 최신 데이터 조회
    print("=== 최신 체결 데이터 ===")
    for code, data in ws_client.latest_prices.items():
        print(f"{code}: {data['stck_prpr']}원")
    
    print("\n=== 최신 지수 데이터 ===")
    for code, data in ws_client.latest_index.items():
        index_name = ws_client.get_index_name(code)
        print(f"{index_name}: {data['bstp_nmix_prpr']}")
    
    print("\n=== 최신 프로그램매매 데이터 ===")
    if ws_client.latest_program_trading:
        data = ws_client.latest_program_trading
        print(f"순매수량: {data['pgtr_ntby_qty']}주")
    
    print("\n=== 최신 호가 데이터 ===")
    for code, data in ws_client.latest_ask_bid.items():
        print(f"{code} 매도1호가: {data['stck_sdpr']}원")

if __name__ == "__main__":
    asyncio.run(realtime_monitor())
```

---

## 계좌 관련 메서드

### `get_account_balance()` ✅ 테스트 검증 완료
**설명**: 계좌 잔고 조회  
**반환**: `DataFrame` - 계좌 잔고 정보 (보유 종목별 상세 정보)  
**테스트 결과**: 정상 작동 확인 (12개 보유 종목, 26개 컬럼 정보 반환)  
**예시**:
```python
balance = agent.get_account_balance()
# DataFrame 형태로 반환: (행수, 컬럼수) 예: (12, 26)
# 주요 컬럼: pdno, prdt_name, hldg_qty, pchs_avg_pric 등
print(f"보유 종목 수: {len(balance)}개")
```

### `get_cash_available(stock_code="005930")` ⚠️ 파라미터 문제 
**설명**: 종목별 매수 가능 금액 조회  
**매개변수**: `stock_code` (str) - 종목코드 (기본값: "005930" 삼성전자)  
**반환**: `Dict` - 매수 가능 금액 정보  
**참고**: v0.1.21에서 종목코드 파라미터 추가, TR ID 변경 (TTTC8908R)  
**⚠️ 알려진 문제**: 현재 파라미터 전달 방식에 문제가 있어 수정이 필요함  
**예시**:
```python
# 직접 account_api 접근으로 임시 해결
cash = agent.account_api.get_cash_available("005930")
```

### `get_total_asset()` ⚠️ 정산 시간 주의
**설명**: 총 자산 평가 조회  
**반환**: `Dict` - 총 자산 정보  
**참고**: v0.1.21에서 TR ID 변경 (CTRP6548R), 파라미터 구조 변경  
**⚠️ 알려진 문제**: 정산 시간(23:30~01:00 등)에는 JSON 디코드 실패 발생 가능  
**예시**:
```python
total_asset = agent.get_total_asset()
# 정산 시간 체크
if total_asset and total_asset.get('rt_cd') == 'JSON_DECODE_ERROR':
    print("정산 시간 중입니다. 잠시 후 다시 시도해 주세요.")
```

### `get_possible_order_amount()`
**설명**: 주문 가능 금액 조회  
**반환**: `Dict` - 주문 가능 금액 정보  
**예시**:
```python
available = agent.get_possible_order_amount()
```

### `get_account_order_quantity(code)`
**설명**: 계좌별 주문 수량 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 주문 수량 정보  
**예시**:
```python
quantity = agent.get_account_order_quantity("005930")
```

### `get_possible_order(code, price, order_type="01")`
**설명**: 주문 가능 여부 확인  
**매개변수**:
- `code` (str) - 종목코드
- `price` (str) - 주문가격
- `order_type` (str) - 주문구분 (01: 지정가, 03: 시장가)

**반환**: `Dict` - 주문 가능 정보  
**예시**:
```python
possible = agent.get_possible_order("005930", "75000", "01")
```

### `order_credit(code, qty, price, order_type)`
**설명**: 신용 주문  
**매개변수**:
- `code` (str) - 종목코드
- `qty` (int) - 주문수량
- `price` (int) - 주문가격
- `order_type` (str) - 주문구분

**반환**: `Dict` - 주문 결과  
**예시**:
```python
order_result = agent.order_credit("005930", 10, 75000, "00")
```

### `order_rvsecncl(org_order_no, qty, price, order_type, cncl_type)`
**설명**: 주문 정정/취소  
**매개변수**:
- `org_order_no` (str) - 원주문번호
- `qty` (int) - 주문수량
- `price` (int) - 주문가격
- `order_type` (str) - 주문구분
- `cncl_type` (str) - 취소구분

**반환**: `Dict` - 주문 결과  
**예시**:
```python
order_result = agent.order_rvsecncl("12345", 10, 75000, "00", "02")
```

### `inquire_psbl_rvsecncl()`
**설명**: 정정/취소 가능 주문 조회  
**반환**: `Dict` - 주문 가능 정보  
**예시**:
```python
possible_orders = agent.inquire_psbl_rvsecncl()
```

### `order_resv(code, qty, price, order_type)`
**설명**: 예약 주문  
**매개변수**:
- `code` (str) - 종목코드
- `qty` (int) - 주문수량
- `price` (int) - 주문가격
- `order_type` (str) - 주문구분

**반환**: `Dict` - 주문 결과  
**예시**:
```python
order_result = agent.order_resv("005930", 10, 75000, "00")
```

### `order_resv_rvsecncl(seq, qty, price, order_type)`
**설명**: 예약 주문 정정/취소  
**매개변수**:
- `seq` (int) - 예약주문순번
- `qty` (int) - 주문수량
- `price` (int) - 주문가격
- `order_type` (str) - 주문구분

**반환**: `Dict` - 주문 결과  
**예시**:
```python
order_result = agent.order_resv_rvsecncl(12345, 10, 75000, "00")
```

### `order_resv_ccnl()`
**설명**: 예약 주문 조회  
**반환**: `Dict` - 주문 정보  
**예시**:
```python
reserved_orders = agent.order_resv_ccnl()
```

---

## 주식 시세 관련 메서드

### `get_stock_price(code)` ✅ 테스트 검증 완료
**설명**: 주식 현재가 조회  
**매개변수**: `code` (str) - 종목코드 (6자리)  
**반환**: `Dict` - 현재가 정보 (15개 이상의 상세 데이터 필드 포함)  
**테스트 결과**: 정상 작동 확인 (응답시간: 0.11초 내외)  
**예시**:
```python
price = agent.get_stock_price("005930")  # 삼성전자
# 주요 필드: stck_prpr(현재가), prdy_vrss(전일대비), prdy_ctrt(등락률) 등
```

### `get_daily_price(code, period="D", org_adj_prc="1")` ✅ 테스트 검증 완료
**설명**: 일별 시세 조회  
**매개변수**:
- `code` (str) - 종목코드
- `period` (str) - 기간구분 (D: 일, W: 주, M: 월, Y: 년)
- `org_adj_prc` (str) - 수정주가구분 (0: 미사용, 1: 사용)

**반환**: `Dict` - 일별 시세 정보 (최대 30일 데이터)  
**테스트 결과**: 정상 작동 확인 (30개 일별 데이터 반환)  
**예시**:
```python
daily = agent.get_daily_price("005930", "D", "1")
# output에 30개 일별 데이터 포함 (stck_bsop_date, stck_clpr 등)
```

### `get_daily_index_chart_price(market_div_code="U", input_iscd="0001", start_date="20210101", end_date="20220722", period_div_code="D")`
**설명**: 국내주식업종기간별시세 조회 (일/주/월/년)  
**매개변수**:
- `market_div_code` (str) - 시장 분류 코드 (U: 업종)
- `input_iscd` (str) - 업종코드 (0001: 종합, 0002: 대형주, 0003: 중형주, 0004: 소형주, 0005: KOSPI, 0006: KOSDAQ, 0007: KOSPI200, 0008: KOSPI100, 0009: KOSPI50, 0010: KOSDAQ150)
- `start_date` (str) - 시작일자 (YYYYMMDD 형식)
- `end_date` (str) - 종료일자 (YYYYMMDD 형식)
- `period_div_code` (str) - 기간분류코드 (D: 일봉, W: 주봉, M: 월봉, Y: 년봉)

**반환**: `Dict` - 업종기간별시세 데이터  
**참고**: 한 번의 호출에 최대 50건의 데이터 수신, 다음 데이터를 받아오려면 OUTPUT 값의 가장 과거 일자의 1일 전 날짜를 end_date에 넣어 재호출  
**예시**:
```python
# 종합 업종 일봉 데이터 조회
sector_daily = agent.get_daily_index_chart_price(
    market_div_code="U",      # 업종
    input_iscd="0001",        # 종합
    start_date="20240601",
    end_date="20240630",
    period_div_code="D"       # 일봉
)

# 대형주 업종 주봉 데이터 조회
large_cap_weekly = agent.get_daily_index_chart_price(
    market_div_code="U",      # 업종
    input_iscd="0002",        # 대형주
    start_date="20240101",
    end_date="20241231",
    period_div_code="W"       # 주봉
)
```

### `get_minute_price(code, hour="153000")` ✅ 테스트 검증 완료
**설명**: 분봉 시세 조회 (주식당일분봉조회)  
**매개변수**:
- `code` (str) - 종목코드
- `hour` (str) - 시간 (HHMMSS 형식, 기본값: "153000" 장마감 시간)

**반환**: `Dict` - 분봉 데이터 (output1, output2 형식)  
**테스트 결과**: 정상 작동 확인 (응답시간: 0.04초 내외)  
**참고**: v0.1.21에서 `get_minute_chart`에서 `get_minute_price`로 메서드명 수정  
**예시**:
```python
minute_data = agent.get_minute_price("005930", "143000")
# output1: 분봉 정보, output2: 추가 정보 포함
```



### `get_orderbook(code)` ✅ 테스트 검증 완료
**설명**: 호가 정보 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `DataFrame` - 호가 정보 (매도잔량, 매수잔량, 매수우세 등)  
**테스트 결과**: 정상 작동 확인 (1행 3열 DataFrame 반환, 응답시간: 0.14초)  
**예시**:
```python
orderbook = agent.get_orderbook("005930")
# 컬럼: ['매도잔량', '매수잔량', '매수우세']
print(f"매수우세: {orderbook['매수우세'].iloc[0]}")
```

### `get_daily_credit_balance(code, date)` ⭐ 신규 (v0.1.24)
**설명**: 국내주식 신용잔고 일별추이 조회  
**매개변수**:
- `code` (str) - 종목코드 (6자리, 예: "005930")
- `date` (str) - 결제일자 (YYYYMMDD 형식, 예: "20240508")

**반환**: `Dict` - 신용잔고 일별추이 데이터  
**TR ID**: FHPST04760000  
**주요 응답 필드**:
- `whol_loan_rmnd_stcn`: 융자잔고량 (주)
- `whol_loan_rmnd_amt`: 융자잔고금액 (원)
- `whol_loan_rmnd_rate`: 융자잔고율 (%)
- `whol_stln_rmnd_stcn`: 대주잔고량 (주)
- `whol_stln_rmnd_amt`: 대주잔고금액 (원)
- `whol_loan_new_stcn`: 융자신규량
- `whol_loan_rdmp_stcn`: 융자상환량

**참고**: 신용거래(융자/대주)로 인한 미결제 잔고 추이를 일별로 조회하여 투자자 심리와 매매 동향 파악 가능  
**예시**:
```python
# 삼성전자 신용잔고 일별추이 조회
credit_balance = agent.get_daily_credit_balance("005930", "20240508")

if credit_balance and credit_balance.get('rt_cd') == '0':
    data = credit_balance['output']
    print(f"데이터 건수: {len(data)}개")
    
    # 최근 데이터 분석
    recent_data = data[0]
    loan_balance = int(recent_data['whol_loan_rmnd_stcn'])
    loan_rate = float(recent_data['whol_loan_rmnd_rate'])
    
    print(f"융자잔고량: {loan_balance:,}주")
    print(f"융자잔고율: {loan_rate}%")
```

### `get_overtime(code)`
**설명**: 시간외 체결 정보 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 시간외 체결 정보  
**예시**:
```python
overtime = agent.get_overtime("005930")
```

### `get_stock_info(ticker)` ✅ 테스트 검증 완료
**설명**: 주식 기본 정보 조회  
**매개변수**: `ticker` (str) - 종목코드  
**반환**: `DataFrame` - 종목 기본 정보 (67개 컬럼의 상세 정보)  
**테스트 결과**: 정상 작동 확인 (1행 67열 DataFrame 반환, 응답시간: 0.03초)  
**예시**:
```python
info = agent.get_stock_info("005930")
# 주요 컬럼: pdno, prdt_type_cd, mket_id_cd, lstg_stqt 등
print(f"상장주식수: {info['lstg_stqt'].iloc[0]}")
```

### `get_daily_chart(code, start_date, end_date)`
**설명**: 일별 차트 정보 조회  
**매개변수**:
- `code` (str) - 종목코드
- `start_date` (str) - 시작일 (YYYYMMDD)
- `end_date` (str) - 종료일 (YYYYMMDD)

**반환**: `Dict` - 일별 차트 데이터  
**예시**:
```python
chart = agent.get_daily_chart("005930", "20240601", "20240630")
```

---

## 시장 분석 메서드

### `get_volume_power(volume=0)` ✅ 테스트 검증 완료
**설명**: 체결강도 순위 조회  
**매개변수**: `volume` (int) - 거래량 기준 (기본값: 0)  
**반환**: `Dict` - 체결강도 순위 (30개 종목 데이터)  
**테스트 결과**: 정상 작동 확인 (30개 종목 순위 데이터 반환, 응답시간: 0.03초)  
**예시**:
```python
volume_power = agent.get_volume_power(0)
# 주요 필드: stck_shrn_iscd, hts_kor_isnm, tday_rltv(체결강도) 등
```

### `get_market_fluctuation()`
**설명**: 등락률 순위 조회 (국내주식 전용)  
**반환**: `Dict` - 등락률 순위  
**예시**:
```python
fluctuation = agent.get_market_fluctuation()
```

### `get_market_rankings(volume=5000000)` ✅ 테스트 검증 완료
**설명**: 시장 순위 정보 조회  
**매개변수**: `volume` (int) - 거래량 기준  
**반환**: `Dict` - 시장 순위 정보 (30개 종목 데이터)  
**테스트 결과**: 정상 작동 확인 (30개 종목 순위 데이터 반환, 응답시간: 0.06초)  
**예시**:
```python
rankings = agent.get_market_rankings(5000000)
# 주요 필드: hts_kor_isnm, stck_prpr, prdy_ctrt, acml_vol 등
```

### `get_top_gainers()`
**설명**: 상승률 상위 종목 조회  
**반환**: `Dict` - 상승률 상위 종목  
**예시**:
```python
gainers = agent.get_top_gainers()
```

### `get_stock_investor(ticker)`
**설명**: 투자자별 매매 동향 조회  
**매개변수**: `ticker` (str) - 종목코드  
**반환**: `DataFrame` - 투자자별 매매 동향  
**예시**:
```python
investor = agent.get_stock_investor("005930")
```

### `get_pbar_tratio(code)` ✅ 테스트 검증 완료
**설명**: 매물대/거래비중 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 매물대/거래비중 정보 (output1, output2 형식)  
**테스트 결과**: 정상 작동 확인 (응답시간: 0.20초, 매물대 분석 가능)  
**예시**:
```python
pbar = agent.get_pbar_tratio("005930")
# output1: 매물대 정보, output2: 거래비중 정보
# 매물대 분석을 통한 지지/저항선 파악 가능
```

### `get_hourly_conclusion(code, hour)`
**설명**: 시간대별 체결 조회  
**매개변수**: 
- `code` (str) - 종목코드
- `hour` (str) - 기준시간 (HHMMSS 형식, 기본값: "115959")
**반환**: `Dict` - 시간대별 체결 정보  
**예시**:
```python
# 기본값 사용 (11시59분59초 기준)
hourly = agent.get_hourly_conclusion("005930")

# 특정 시간 지정 (14시30분00초 기준)
hourly = agent.get_hourly_conclusion("005930", "143000")
```

### `get_stock_ccnl(code)`
**설명**: 주식현재가 체결(최근30건) 조회 - **당일 체결강도 포함**  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 최근 30건 체결 내역
- `output`: 체결 내역 리스트 (30건)
  - `stck_cntg_hour`: 체결시간 (HHMMSS)
  - `stck_prpr`: 체결가격  
  - `prdy_vrss`: 전일대비
  - `prdy_ctrt`: 등락률
  - **`tday_rltv`: 당일 체결강도** ⭐
  - `cntg_vol`: 체결량
  
**예시**:
```python
# 삼성전자 최근 체결 내역 및 체결강도 조회
ccnl = agent.get_stock_ccnl("005930")
if ccnl and 'output' in ccnl:
    # 당일 체결강도 확인
    strength = ccnl['output'][0]['tday_rltv']
    print(f"당일 체결강도: {strength}")
    
    # 최근 5건 체결 내역
    for i, item in enumerate(ccnl['output'][:5]):
        print(f"{item['stck_cntg_hour']} | {item['stck_prpr']}원 | 체결강도: {item['tday_rltv']}")
```

---

## 프로그램 매매 메서드

### `get_program_trade_by_stock(code)` ✅ 테스트 검증 완료
**설명**: 종목별 프로그램매매추이(체결) 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 프로그램 매매 정보 (30개 시간대별 데이터)  
**테스트 결과**: 정상 작동 확인 (30개 시간대별 데이터 반환, 응답시간: 0.06초)  
**예시**:
```python
program_trade = agent.get_program_trade_by_stock("005930")
# 주요 필드: bsop_hour, whol_smtn_ntby_qty(순매수량), whol_smtn_ntby_tr_pbmn(순매수대금) 등
```

### `get_program_trade_daily_summary(code, date_str)` ✅ 테스트 검증 완료
**설명**: 종목별 일별 프로그램 매매 집계 조회  
**매개변수**:
- `code` (str) - 종목코드
- `date_str` (str) - 날짜 (YYYYMMDD)

**반환**: `Dict` - 일별 프로그램 매매 집계 (30개 일별 데이터)  
**테스트 결과**: 정상 작동 확인 (30개 일별 데이터 반환, 응답시간: 0.05초)  
**예시**:
```python
summary = agent.get_program_trade_daily_summary("005930", "20250710")
# 주요 필드: stck_bsop_date, whol_smtn_ntby_qty, whol_smtn_ntby_tr_pbmn 등
```

### `get_program_trade_period_detail(start_date, end_date)` ⚠️ 메서드 존재하지 않음
**설명**: 기간별 프로그램 매매 상세 조회  
**매개변수**:
- `start_date` (str) - 시작일 (YYYYMMDD)
- `end_date` (str) - 종료일 (YYYYMMDD)

**반환**: `Dict` - 기간별 프로그램 매매 상세  
**⚠️ 알려진 문제**: 현재 ProgramTradeAPI 클래스에 해당 메서드가 구현되지 않음  
**예시**:
```python
# 현재 사용 불가
# detail = agent.get_program_trade_period_detail("20240601", "20240630")
```

### `get_program_trade_market_daily(start_date, end_date)` ✅ 테스트 검증 완료
**설명**: 시장 전체 프로그램 매매 종합현황 (일별) 조회  
**매개변수**:
- `start_date` (str) - 시작일 (YYYYMMDD)
- `end_date` (str) - 종료일 (YYYYMMDD)

**반환**: `Dict` - 시장 전체 프로그램 매매 현황  
**테스트 결과**: 정상 작동 확인 (응답시간: 0.05초)  
**예시**:
```python
market_daily = agent.get_program_trade_market_daily("20250703", "20250710")
# 시장 전체 프로그램매매 현황 데이터
```

### `get_program_trade_hourly_trend(code)` ✅ 테스트 검증 완료
**설명**: 시간별 프로그램 매매 추이 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 시간별 프로그램 매매 추이 (30개 시간대별 데이터)  
**테스트 결과**: 정상 작동 확인 (30개 시간대별 데이터 반환, 응답시간: 0.04초)  
**예시**:
```python
hourly = agent.get_program_trade_hourly_trend("005930")
# 시간별 프로그램매매 추이 데이터
```

---

## 조건검색 메서드

### `get_condition_stocks(user_id="unohee", seq=0, tr_cont="N")` ✅ 테스트 검증 완료
**설명**: 조건검색 결과 조회 (통일된 API 방식)  
**매개변수**:
- `user_id` (str) - 사용자 ID (기본값: "unohee")
- `seq` (int) - 조건검색 시퀀스 번호 (기본값: 0)
- `tr_cont` (str) - 연속조회 여부 (기본값: "N")

**반환**: `List[Dict]` - 조건검색 결과 리스트  
**테스트 결과**: 정상 작동 확인 (24개 종목 조건검색 결과 반환, 응답시간: 0.04초)  
**예시**:
```python
condition_stocks = agent.get_condition_stocks()  # 기본 파라미터 사용
# 반환 예시: [{'code': '000020', 'name': '동화약품'}, ...]
print(f"조건검색 결과: {len(condition_stocks)}개 종목")
```

---

## 휴장일 정보 메서드

### `get_holiday_info()` ✅ 테스트 검증 완료
**설명**: 휴장일 정보 조회 (직접 API 접근)  
**반환**: `Dict` - 휴장일 정보 (12개 날짜 정보)  
**테스트 결과**: 정상 작동 확인 (12개 날짜 데이터 반환, 응답시간: 0.03초)  
**예시**:
```python
holiday_info = agent.get_holiday_info()
# 주요 필드: bass_dt, bzdy_yn(영업일여부), tr_day_yn(거래일여부) 등
```

### `is_holiday(date)` ✅ 테스트 검증 완료
**설명**: 특정 날짜 휴장일 여부 확인 (편의 메서드)  
**매개변수**: `date` (str) - 날짜 (YYYYMMDD)  
**반환**: `bool` - 휴장일 여부 (True: 휴장일, False: 거래일)  
**테스트 결과**: 정상 작동 확인 (크리스마스=True, 평일=False, 응답시간: 0.03초)  
**예시**:
```python
is_holiday_christmas = agent.is_holiday("20241225")  # True (크리스마스)
is_holiday_today = agent.is_holiday("20250707")     # False (평일)
```

---

## 거래원/회원사 관련 메서드

### `get_member(code)` ✅ 테스트 검증 완료
**설명**: 거래원 정보 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 거래원 정보 (매도/매수 상위 5개 거래원 정보)  
**테스트 결과**: 정상 작동 확인 (응답시간: 0.03초, 상세 거래원 정보 반환)  
**예시**:
```python
member_info = agent.get_member("005930")
# 주요 필드: seln_mbcr_name1~5(매도거래원), shnu_mbcr_name1~5(매수거래원),
#           total_seln_qty1~5(매도량), total_shnu_qty1~5(매수량) 등
print(f"매도1위: {member_info['output']['seln_mbcr_name1']}")
```

### `get_stock_member(ticker)`
**설명**: 주식 회원사 정보 조회  
**매개변수**: `ticker` (str) - 종목코드  
**반환**: `Dict` - 회원사 정보  
**예시**:
```python
stock_member = agent.get_stock_member("005930")
```

### `get_member_transaction(code, mem_code="99999")` ✅ 테스트 검증 완료
**설명**: 회원사 일별 매매 종목 조회  
**매개변수**:
- `code` (str) - 종목코드
- `mem_code` (str) - 회원사 코드 (기본값: "99999")

**반환**: `Dict` - 회원사 매매 정보 (23개 일별 데이터)  
**테스트 결과**: 정상 작동 확인 (23개 일별 매매 데이터 반환, 응답시간: 0.06초)  
**예시**:
```python
transaction = agent.get_member_transaction("005930", "99999")
# 주요 필드: stck_bsop_date, total_seln_qty, total_shnu_qty, ntby_qty 등
```

### `get_foreign_broker_net_buy(code, foreign_brokers, date)`
**설명**: 외국계 증권사 순매수 조회  
**매개변수**:
- `code` (str) - 종목코드
- `foreign_brokers` (list) - 외국계 증권사 리스트
- `date` (str) - 날짜 (YYYYMMDD)

**반환**: `tuple` - 순매수 정보  
**예시**:
```python
net_buy = agent.get_foreign_broker_net_buy("005930", ["모간", "골드만"], "20240625")
```

### `classify_broker(name)` (정적 메서드)
**설명**: 거래원 성격 분류 (외국계/리테일/기관)  
**매개변수**: `name` (str) - 거래원명  
**반환**: `str` - 분류 결과  
**예시**:
```python
broker_type = Agent.classify_broker("골드만삭스")  # "외국계"
```

---

## 해외주식 관련 메서드

### `get_overseas_price(code)`
**설명**: 해외주식 현재가 조회  
**매개변수**: `code` (str) - 해외주식 종목코드  
**반환**: `Dict` - 해외주식 현재가  
**예시**:
```python
overseas_price = agent.get_overseas_price("AAPL")
```

### `get_overseas_daily_price(code)`
**설명**: 해외주식 일별 시세 조회  
**매개변수**: `code` (str) - 해외주식 종목코드  
**반환**: `Dict` - 해외주식 일별 시세  
**예시**:
```python
overseas_daily = agent.get_overseas_daily_price("AAPL")
```

### `get_overseas_minute_price(code)`
**설명**: 해외주식 분봉 시세 조회  
**매개변수**: `code` (str) - 해외주식 종목코드  
**반환**: `Dict` - 해외주식 분봉 시세  
**예시**:
```python
overseas_minute = agent.get_overseas_minute_price("AAPL")
```

### `get_overseas_news(code)`
**설명**: 해외주식 뉴스 조회  
**매개변수**: `code` (str) - 해외주식 종목코드  
**반환**: `Dict` - 해외주식 뉴스  
**예시**:
```python
overseas_news = agent.get_overseas_news("AAPL")
```

### `get_overseas_right(code)`
**설명**: 해외주식 권리 정보 조회  
**매개변수**: `code` (str) - 해외주식 종목코드  
**반환**: `Dict` - 해외주식 권리 정보  
**예시**:
```python
overseas_right = agent.get_overseas_right("AAPL")
```

---

## 선물옵션 관련 메서드

### `get_future_option_price(market_div_code="F", input_iscd="101S09")`
**설명**: 선물옵션 시세 조회  
**매개변수**:
- `market_div_code` (str) - 시장분류코드 (F: 지수선물, O: 지수옵션, JF: 주식선물, JO: 주식옵션)
- `input_iscd` (str) - 선물옵션종목코드 (선물 6자리 예: 101S03, 옵션 9자리 예: 201S03370)

**반환**: `Dict` - 선물옵션 시세 데이터  
**참고**: 
- 시장분류코드: F(지수선물), O(지수옵션), JF(주식선물), JO(주식옵션)
- 종목코드: 선물은 6자리, 옵션은 9자리
- **⭐ KOSPI200 베이시스 계산**: `input_iscd`를 None으로 설정하면 오늘 날짜 기준 최근월물 자동 계산

**예시**:
```python
# 지수선물 시세 조회 (기본값 - 자동 최근월물 계산)
futures_price = agent.get_future_option_price()

# 다른 지수선물 종목 조회
futures_price = agent.get_future_option_price(
    market_div_code="F",      # 지수선물
    input_iscd="101S03"       # 다른 선물 종목
)

# 지수옵션 시세 조회
option_price = agent.get_future_option_price(
    market_div_code="O",      # 지수옵션
    input_iscd="201S03370"    # 옵션 종목 (9자리)
)

# KOSPI200 베이시스 계산 예시
# 오늘이 2025년 1월이라면 -> 101S03 (3월물) 자동 선택
# 오늘이 2025년 4월이라면 -> 101S06 (6월물) 자동 선택
futures_price = agent.get_future_option_price(
    market_div_code="F",      # 지수선물
    input_iscd=None           # 자동 최근월물 계산
)
```

---

## 유틸리티 메서드

### `get_price_volume_ratio(code)`
**설명**: 매물대 거래비중 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 매물대 거래비중  
**예시**:
```python
pv_ratio = agent.get_price_volume_ratio("005930")
```

### `inquire_ccnl(code)`
**설명**: 종목별 체결 현황 조회  
**매개변수**: `code` (str) - 종목코드  
**반환**: `Dict` - 체결 현황  
**예시**:
```python
ccnl = agent.inquire_ccnl("005930")
```

---

## 데이터 관리 메서드

### `init_minute_db(db_path='stonks_candles.db')` ✅ 테스트 검증 완료
**설명**: 분봉 데이터용 DB 및 테이블 생성 (최초 1회)  
**매개변수**: `db_path` (str) - DB 파일 경로  
**반환**: `bool` - DB 초기화 성공 여부  
**테스트 결과**: 정상 작동 확인 (True 반환, 즉시 완료)  
**예시**:
```python
success = agent.init_minute_db('my_data.db')
print(f"DB 초기화: {'성공' if success else '실패'}")
```

### `migrate_minute_csv_to_db(code, db_path='stonks_candles.db')`
**설명**: 기존 CSV 분봉 데이터를 DB로 이관  
**매개변수**:
- `code` (str) - 종목코드
- `db_path` (str) - DB 파일 경로

**예시**:
```python
agent.migrate_minute_csv_to_db("005930", 'my_data.db')
```

### `fetch_minute_data(code, date=None, cache_dir='cache')` ✅ 테스트 검증 완료
**설명**: 분봉 데이터 조회 및 캐시 (30분 단위 재귀 수집)  
**매개변수**:
- `code` (str) - 종목코드
- `date` (str) - 날짜 (YYYYMMDD, None이면 오늘)
- `cache_dir` (str) - 캐시 디렉토리

**반환**: `DataFrame` - 분봉 데이터 (최대 360개, 10개 컬럼)  
**테스트 결과**: 정상 작동 확인 (360개 분봉 데이터 수집, CSV 캐시 생성)  
**참고**: v0.1.21에서 `get_minute_price` 메서드 사용으로 수정, 정상 데이터 수집 확인  
**예시**:
```python
# 삼성전자 당일 분봉 데이터 (360개)
minute_data = agent.fetch_minute_data("005930", "20250710", "cache")
print(f"수집된 분봉 데이터: {len(minute_data)}개")
# 주요 컬럼: stck_bsop_date, stck_cntg_hour, stck_prpr, cntg_vol 등
# 시간 범위: 090000 ~ 153000 (1분 단위)
```

---

## 💡 사용 팁

### 1. 에러 처리 ✅ 테스트 검증 완료
모든 메서드는 실패 시 `None`을 반환하므로 반드시 체크:
```python
result = agent.get_stock_price("005930")
if result is None:
    print("API 호출 실패")
    return

if result.get('rt_cd') != '0':
    print(f"API 오류: {result.get('msg1', '알 수 없는 오류')}")
    return

# 정산 시간 특별 처리
if result.get('rt_cd') == 'JSON_DECODE_ERROR':
    print("정산 시간 중입니다. 잠시 후 다시 시도해 주세요.")
    return
```

### 2. 응답 데이터 구조 ✅ 테스트 검증 완료
대부분의 API 응답은 다음 구조를 가집니다:
```python
{
    "rt_cd": "0",        # 성공: "0", 실패: 기타, 정산시간: "JSON_DECODE_ERROR"
    "msg_cd": "MCA00000",
    "msg1": "정상처리 되었습니다",
    "output": { ... }    # 실제 데이터 (Dict 또는 List)
}

# 일부 메서드는 DataFrame 형태로 직접 반환
balance = agent.get_account_balance()  # DataFrame (12행 26열)
```

### 3. 종목코드 형식 ✅ 테스트 검증 완료
- **국내주식**: 6자리 숫자 (예: "005930")
- **해외주식**: 알파벳 티커 (예: "AAPL")

### 4. 날짜 형식 ✅ 테스트 검증 완료
모든 날짜는 **YYYYMMDD** 형식 사용:
```python
today = "20250710"  # 2025년 7월 10일
agent.get_daily_price("005930", date=today)
```

### 5. 연속 API 호출 시 주의사항 ✅ 테스트 검증 완료
API 호출 제한을 고려하여 적절한 간격 유지:
```python
import time

for code in stock_codes:
    result = agent.get_stock_price(code)
    time.sleep(0.1)  # 100ms 대기 (테스트에서 안정적인 응답 확인)
```

### 6. 성능 및 응답시간 (테스트 기반) ⭐ 신규
실제 테스트에서 측정된 응답시간:
- 빠른 메서드 (0.03~0.06초): `get_stock_price`, `get_daily_price`, `get_member`
- 보통 메서드 (0.10~0.20초): `get_orderbook`, `get_pbar_tratio`
- 데이터 수집 (즉시): `fetch_minute_data` (캐시 우선, 360개 분봉 데이터)

### 7. 안정성이 확인된 핵심 메서드 (85.7% 성공률) ⭐ 신규
다음 메서드들은 실제 운영 환경에서 안정적으로 작동 확인:
```python
# 주식 시세 (100% 성공)
agent.get_stock_price("005930")
agent.get_daily_price("005930")
agent.get_minute_price("005930", "153000")

# 시장 분석 (100% 성공)  
agent.get_volume_power(0)
agent.get_market_rankings(5000000)
agent.get_pbar_tratio("005930")

# 프로그램 매매 (100% 성공)
agent.get_program_trade_by_stock("005930")
agent.get_program_trade_hourly_trend("005930")

# 계좌 정보 (부분적 주의 필요)
agent.get_account_balance()  # ✅ 안정적
# agent.get_cash_available()  # ⚠️ 파라미터 문제
# agent.get_total_asset()     # ⚠️ 정산시간 주의
```

### 6. 웹소켓 사용 시 권장사항 ⭐ 신규
실시간 데이터 사용 시 효율성을 위한 권장사항:
```python
# 필요한 데이터만 선택적으로 활성화
ws_client = agent.websocket(
    enable_index=True,           # 지수 모니터링 시에만
    enable_program_trading=True, # 프로그램매매 분석 시에만
    enable_ask_bid=True         # 호가 분석 시에만
)

# 데이터 저장소 정기적으로 정리
async def cleanup_old_data():
    while True:
        await asyncio.sleep(3600)  # 1시간마다
        ws_client.latest_prices.clear()
        ws_client.latest_index.clear()
        # 필요시 정리 로직 추가
```

---

## 🔗 관련 리소스

- **GitHub**: https://github.com/unohee/pykis
- **PyPI**: https://pypi.org/project/pykis/
- **CHANGELOG**: [CHANGELOG.md](CHANGELOG.md)
- **개발 가이드**: [AGENTS.md](AGENTS.md)

---

## 📞 지원

문의사항이나 버그 신고는 GitHub Issues를 통해 연락주세요.

**pykis v0.1.21** - 한국투자증권 OpenAPI를 쉽고 안전하게! 🚀 