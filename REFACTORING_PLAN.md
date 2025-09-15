# PyKIS API Refactoring Plan

## 목표
1. API 메서드 이름 정규화
2. 보일러플레이트 코드 제거
3. 일관된 패턴 적용
4. 비즈니스 로직 보존

## 메서드 명명 규칙

### 현재 패턴 분석
- `get_*`: 데이터 조회 (대부분)
- `fetch_*`: 데이터 수집
- `inquire_*`: 계좌/주문 관련 조회
- `order_*`: 주문 실행

### 정규화 방안
```python
# 1. 시세 조회: get_price_*
get_stock_price() -> get_price_current()
get_daily_price() -> get_price_daily()
get_minute_price() -> get_price_minute()
get_intraday_price() -> get_price_intraday()

# 2. 호가/거래량: get_book_*
get_orderbook() -> get_book_order()
get_volume_power() -> get_book_volume_power()

# 3. 시장 정보: get_market_*
get_market_fluctuation() -> get_market_fluctuation()  # 유지
get_market_rankings() -> get_market_rankings()  # 유지

# 4. 투자자/회원사: get_investor_*
get_stock_investor() -> get_investor_trend()
get_stock_member() -> get_member_trend()

# 5. 종목 정보: get_stock_*
get_stock_info() -> get_stock_info()  # 유지
get_stock_basic() -> get_stock_basic()  # 유지
get_stock_financial() -> get_stock_financial()  # 유지

# 6. 주문/계좌: inquire_* (유지)
inquire_psbl_order() -> inquire_order_capacity()
inquire_credit_psamount() -> inquire_credit_capacity()
```

## 보일러플레이트 패턴

### 현재 반복 패턴
```python
def get_something(self, params):
    return self._make_request_dict(
        endpoint=API_ENDPOINTS['ENDPOINT_NAME'],
        tr_id="TRANSACTION_ID",
        params={
            "key1": value1,
            "key2": value2
        }
    )
```

### 개선 방안
```python
# BaseAPI에 데코레이터 추가
@api_endpoint('ENDPOINT_NAME', 'TRANSACTION_ID')
def get_something(self, param1, param2):
    return {
        "key1": param1,
        "key2": param2
    }
```

## 구현 단계

### Phase 1: BaseAPI 개선
1. `@api_endpoint` 데코레이터 구현
2. 공통 파라미터 처리 로직 추가
3. 에러 처리 표준화

### Phase 2: StockAPI 메서드 정규화
1. 메서드명 변경 (alias 유지)
2. 파라미터 표준화
3. 반환 타입 일관성

### Phase 3: 테스트 업데이트
1. 새 메서드명 테스트
2. 하위 호환성 테스트
3. 성능 비교

## 하위 호환성 전략
```python
# 기존 메서드를 alias로 유지
def get_stock_price(self, code):
    """Deprecated: Use get_price_current() instead"""
    return self.get_price_current(code)
```

## 예상 효과
- 코드 라인 수: 약 30% 감소
- 가독성: 크게 향상
- 유지보수성: 패턴 통일로 개선
- 테스트 용이성: 데코레이터 단위 테스트 가능