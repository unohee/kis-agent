# PyKIS 통합 예외 처리 시스템 마이그레이션 가이드

## 개요

이 문서는 PyKIS의 모든 모듈을 새로운 통합 예외 처리 시스템으로 마이그레이션하는 방법을 설명합니다.

### 핵심 원칙
1. **절대 예외를 먹지 마세요** - 예외는 반드시 traceback과 함께 raise
2. **구체적인 예외 사용** - `Exception` 대신 구체적 예외 타입 사용
3. **명시적 실패** - None 반환 대신 예외 발생
4. **완전한 추적** - 모든 예외는 traceback 포함하여 로깅

## 현재 상태 분석 결과

```
- 이슈가 있는 파일: 20개
- 전체 이슈: 196개
  - GENERIC_EXCEPTION: 100건
  - NO_RAISE_AFTER_LOG: 52건
  - SWALLOW_EXCEPTION: 44건
```

## 마이그레이션 단계별 가이드

### 1단계: 새 예외 모듈 import

```python
# 기존 코드
import logging

# 변경 후
import logging
from ..core.exceptions import (
    ExceptionHandler,
    APIException,
    ValidationException,
    NetworkException,
    handle_exceptions,
    ensure_not_none,
    ensure_type
)
```

### 2단계: 클래스에 ExceptionHandler 상속 추가

```python
# 기존 코드
class StockAPI(BaseAPI):
    def __init__(self, client, account):
        BaseAPI.__init__(self, client)

# 변경 후
class StockAPI(BaseAPI, ExceptionHandler):
    def __init__(self, client, account):
        BaseAPI.__init__(self, client)
        ExceptionHandler.__init__(self, "pykis.stock.StockAPI")
```

### 3단계: 예외 처리 패턴 변경

#### 패턴 1: 광범위한 except를 구체화

```python
# 기존 코드 (❌ 나쁨)
try:
    response = self.api_call()
except Exception as e:
    logging.error(f"API 호출 실패: {e}")
    return None

# 변경 후 (✅ 좋음)
try:
    response = self.api_call()
except NetworkException as e:
    self._handle_exception(e, "API 호출 실패", reraise_as=APIException)
except ValidationException as e:
    self._handle_exception(e, "입력 검증 실패")
```

#### 패턴 2: 예외를 먹지 말고 raise

```python
# 기존 코드 (❌ 나쁨)
try:
    data = process_data()
except Exception as e:
    logging.error(f"처리 실패: {e}")
    return None  # 예외를 먹음!

# 변경 후 (✅ 좋음)
try:
    data = process_data()
except Exception as e:
    self._handle_exception(e, "데이터 처리 실패")
    # 예외가 자동으로 raise됨
```

#### 패턴 3: 데코레이터 사용

```python
# 기존 코드
def get_stock_price(self, code):
    try:
        response = self.api_call(code)
        return response
    except Exception as e:
        logging.error(f"주식 가격 조회 실패: {e}")
        return None

# 변경 후 (✅ 좋음)
@handle_exceptions(context="주식 가격 조회", reraise_as=APIException)
def get_stock_price(self, code):
    ensure_not_none(code, "종목코드")
    ensure_type(code, str, "종목코드")

    response = self.api_call(code)
    return response
```

### 4단계: 입력 검증 추가

```python
# 기존 코드
def process_order(self, order_id, quantity):
    # 검증 없이 바로 처리
    return self.execute_order(order_id, quantity)

# 변경 후
def process_order(self, order_id, quantity):
    # 명시적 검증
    ensure_not_none(order_id, "주문 ID")
    ensure_type(order_id, str, "주문 ID")
    ensure_not_none(quantity, "수량")
    ensure_type(quantity, int, "수량")

    if quantity <= 0:
        raise ValidationException(f"수량은 0보다 커야 합니다: {quantity}")

    return self.execute_order(order_id, quantity)
```

## 예외 타입 선택 가이드

| 상황 | 사용할 예외 | 예시 |
|------|------------|------|
| API 호출 실패 | `APIException` | API 응답 오류, timeout |
| 인증 실패 | `AuthenticationException` | 토큰 만료, 잘못된 인증정보 |
| 입력 검증 실패 | `ValidationException` | 잘못된 파라미터, 형식 오류 |
| 네트워크 오류 | `NetworkException` | 연결 실패, DNS 오류 |
| 데이터 처리 오류 | `DataProcessingException` | 파싱 실패, 변환 오류 |
| 설정 오류 | `ConfigurationException` | 필수 설정 누락 |
| Rate Limit | `RateLimitException` | API 호출 제한 초과 |
| WebSocket | `WebSocketException` | WebSocket 연결/통신 오류 |

## 실제 마이그레이션 예시

### Before: pykis/stock/api.py

```python
def get_stock_member(self, ticker: str, retries: int = 10) -> Optional[Dict]:
    for attempt in range(retries):
        try:
            response = self.client.make_request(...)
            if response and response.get("rt_cd") == "0":
                return response
            else:
                return None
        except Exception as e:
            logging.error(f"주식 회원사 조회 실패: {e}")
            if attempt < retries - 1:
                continue
            return None
```

### After: 개선된 버전

```python
@handle_exceptions(context="주식 회원사 정보 조회")
def get_stock_member(self, ticker: str, retries: int = 10) -> Dict:
    ensure_not_none(ticker, "종목코드")
    ensure_type(ticker, str, "종목코드")

    last_exception = None

    for attempt in range(retries):
        try:
            response = self.client.make_request(...)

            if not response:
                raise APIException(f"API 응답이 없습니다: {ticker}")

            if response.get("rt_cd") != "0":
                error_msg = response.get("msg1", "알 수 없는 오류")
                raise APIException(f"API 오류: {error_msg}")

            return response

        except (NetworkException, APIException) as e:
            last_exception = e
            self._log_warning(f"재시도 {attempt+1}/{retries}: {e}")

            if attempt < retries - 1:
                continue

    # 모든 재시도 실패
    raise APIException(
        f"{retries}회 재시도 후에도 실패: {ticker}"
    ) from last_exception
```

## 테스트 방법

```python
# tests/test_exception_handling.py
import pytest
from pykis.core.exceptions import APIException, ValidationException
from pykis.stock.api_improved import StockAPI

def test_invalid_input_raises_validation_exception():
    """잘못된 입력은 ValidationException 발생"""
    api = StockAPI(mock_client, mock_account)

    with pytest.raises(ValidationException, match="종목코드는 6자리"):
        api.get_stock_price("123")  # 3자리만

def test_api_failure_raises_api_exception():
    """API 실패 시 APIException 발생"""
    api = StockAPI(mock_client, mock_account)
    mock_client.make_request.side_effect = NetworkException("연결 실패")

    with pytest.raises(APIException, match="API 호출 실패"):
        api.get_stock_price("005930")

def test_exception_includes_traceback(caplog):
    """예외 발생 시 전체 traceback 로깅 확인"""
    api = StockAPI(mock_client, mock_account)

    with pytest.raises(APIException):
        api.get_invalid_method()

    # 로그에 traceback이 포함되었는지 확인
    assert "Traceback" in caplog.text
```

## 마이그레이션 체크리스트

- [ ] `pykis/core/exceptions.py` 파일 생성
- [ ] 각 모듈에 ExceptionHandler import 추가
- [ ] 클래스에 ExceptionHandler 상속 추가
- [ ] `except Exception`을 구체적 예외로 변경
- [ ] `return None`을 예외 raise로 변경
- [ ] logging만 하고 raise 안하는 부분 수정
- [ ] 입력 검증 코드 추가
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 실행

## 주의사항

1. **점진적 마이그레이션**: 한번에 모든 파일을 변경하지 마세요. 모듈 단위로 진행하세요.
2. **하위 호환성**: 기존 API 사용자를 위해 변경사항을 문서화하세요.
3. **테스트 우선**: 마이그레이션 전 테스트를 작성하여 동작을 검증하세요.
4. **로깅 레벨**: 개발 환경에서는 DEBUG, 프로덕션에서는 ERROR 레벨 사용

## 문제 해결

### Q: 기존 코드가 None을 기대하는 경우?
A: 호출부를 try-except로 감싸서 명시적으로 처리:
```python
try:
    result = api.get_data()
except APIException:
    result = None  # 명시적으로 None 처리
```

### Q: 여러 예외를 동시에 처리하려면?
A: 튜플로 여러 예외 타입 지정:
```python
except (APIException, ValidationException, NetworkException) as e:
    self._handle_exception(e, "복합 오류")
```

## 지원 및 문의

문제 발생 시 다음을 확인하세요:
1. `exception_migration_report.txt` - 현재 이슈 목록
2. `pykis/stock/api_improved.py` - 완전히 마이그레이션된 예시
3. `tests/test_exception_handling.py` - 테스트 예시