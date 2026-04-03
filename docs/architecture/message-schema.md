# JSON 메시지 형식 스키마

kis-agent CLI Bridge의 표준 JSON 메시지 형식(request/response)을 정의합니다.

## 개요

- **목적**: Node.js와 Python 간 JSON 기반 subprocess 통신의 일관성 있는 메시지 형식 제공
- **구현**: `kis_agent.message_schema` 모듈의 dataclass 기반 구조
- **검증**: `CliMessageValidator` 클래스로 타입 및 구조 검증

## Request 메시지 형식

### 구조

```python
@dataclass
class CliRequest:
    method: str                         # 필수: "domain.method" 형식
    args: Dict[str, Any] = field(...)  # 선택: 메서드 인자 (기본값: {})
    timeout: int = 30                   # 선택: 타임아웃 (초, 기본값: 30)
    id: Optional[str] = None            # 선택: 요청 ID (자동 생성)
```

### 예시

#### 최소 필드

```json
{
  "method": "stock_api.get_stock_price"
}
```

#### 모든 필드

```json
{
  "id": "req-a1b2c3d4",
  "method": "stock_api.get_stock_price",
  "args": {
    "code": "005930"
  },
  "timeout": 60
}
```

### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `method` | `str` | ✓ | "domain.method" 형식 메서드 경로. domain과 method는 유효한 Python 식별자여야 함 |
| `args` | `Dict[str, Any]` | ✗ | 메서드에 전달할 키워드 인자 (기본값: `{}`) |
| `timeout` | `int` | ✗ | 메서드 실행 타임아웃 (초). 양수만 허용 (기본값: 30) |
| `id` | `str` \| `null` | ✗ | 요청 ID. 지정하지 않으면 자동 생성 (형식: `req-{8자리 hex}`) |

### 검증 규칙

```python
# 유효한 요청
CliMessageValidator.validate_request({
    "method": "stock_api.get_stock_price",
    "args": {"code": "005930"},
    "timeout": 60
})  # → (True, None)

# 유효하지 않은 요청
CliMessageValidator.validate_request({
    "method": "invalid_method"  # "." 누락
})  # → (False, "Invalid 'method' format: ...")
```

## Response 메시지 형식

### 성공 응답 (Status: ok)

#### 구조

```python
@dataclass
class CliResponseSuccess:
    id: str                    # 요청 ID와 동일
    result: Any                # API 실행 결과
    status: ResponseStatus     # "ok" 고정
    notice: Optional[str]      # 선택: 시장 상태 공지
```

#### 예시

```json
{
  "id": "req-a1b2c3d4",
  "result": {
    "stck_prpr": "50000",
    "prdy_vrss": "+500"
  },
  "status": "ok",
  "_notice": "장 마감 후 — 데이터는 금일 종가 기준"
}
```

#### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | `str` | ✓ | 요청의 `id`와 동일 |
| `result` | `Any` | ✓ | API 메서드의 반환값 (Dict, DataFrame, list 등) |
| `status` | `str` | ✓ | `"ok"` (고정) |
| `_notice` | `str` | ✗ | 한투 시장 상태 공지 (휴장, 장시간, 시간외 등) |

### 에러 응답 (Status: error / timeout)

#### 구조

```python
@dataclass
class CliResponseError:
    id: Optional[str]          # 요청 ID (요청 파싱 실패 시 null)
    error: str                 # 에러 메시지
    code: str                  # 예외 클래스명
    status: ResponseStatus     # "error" 또는 "timeout"
```

#### 예시 — 일반 에러

```json
{
  "id": "req-a1b2c3d4",
  "error": "stock_api has no method 'get_invalid_price'",
  "code": "AttributeError",
  "status": "error"
}
```

#### 예시 — 타임아웃

```json
{
  "id": "req-a1b2c3d4",
  "error": "Request execution timed out after 60 seconds",
  "code": "TimeoutError",
  "status": "timeout"
}
```

#### 예시 — 요청 파싱 실패 (id: null)

```json
{
  "id": null,
  "error": "Invalid JSON: Expecting value: line 1 column 1 (char 0)",
  "code": "JSONDecodeError",
  "status": "error"
}
```

#### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | `str` \| `null` | ✓ | 요청 ID. 요청 파싱 실패 시 `null` |
| `error` | `str` | ✓ | 에러 메시지 |
| `code` | `str` | ✓ | 예외 클래스명 (Python 클래스명 사용) |
| `status` | `str` | ✓ | `"error"` 또는 `"timeout"` |

### ResponseStatus 열거형

```python
class ResponseStatus(str, Enum):
    OK = "ok"           # 성공
    ERROR = "error"     # 에러 (타임아웃 제외)
    TIMEOUT = "timeout" # 타임아웃
```

## 검증 (CliMessageValidator)

### 요청 검증

```python
from kis_agent import CliMessageValidator

# 요청 검증
valid, error = CliMessageValidator.validate_request(request_dict)
if not valid:
    print(f"Invalid request: {error}")
```

### 응답 검증

```python
# 응답 검증 (성공/에러 자동 구분)
valid, error = CliMessageValidator.validate_response(response_dict)
if not valid:
    print(f"Invalid response: {error}")

# 또는 명시적 검증
valid, error = CliMessageValidator.validate_response_success(response_dict)
valid, error = CliMessageValidator.validate_response_error(response_dict)
```

### 검증 규칙

#### Request
- `method` 필수 (문자열)
- `method` 형식: `"domain.method"` (점 1개, 양쪽 모두 유효한 Python 식별자)
- `args` 선택 (딕셔너리)
- `timeout` 선택 (양의 정수)
- `id` 선택 (문자열)

#### Response Success
- `id` 필수 (문자열)
- `result` 필수 (모든 타입)
- `status` 필수 (`"ok"`)
- `_notice` 선택 (문자열)

#### Response Error
- `id` 필수 (`str` 또는 `null`)
- `error` 필수 (문자열)
- `code` 필수 (문자열)
- `status` 필수 (`"error"` 또는 `"timeout"`)

## 사용 예시

### Python에서 사용

```python
from kis_agent import CliRequest, CliResponseSuccess, CliMessageValidator

# 요청 생성
request = CliRequest(
    method="stock_api.get_stock_price",
    args={"code": "005930"},
    timeout=60
)

# 딕셔너리로 변환 (JSON 직렬화)
import json
request_json = json.dumps(request.to_dict())
print(request_json)
# {"id": "req-...", "method": "stock_api.get_stock_price", "args": {"code": "005930"}, "timeout": 60}

# 딕셔너리에서 생성
data = json.loads(request_json)
request = CliRequest.from_dict(data)

# 응답 생성
response = CliResponseSuccess(
    id=request.id,
    result={"stck_prpr": "50000"},
    notice="장 마감 후"
)

# 응답 검증
valid, error = CliMessageValidator.validate_response(response.to_dict())
assert valid, f"Invalid response: {error}"
```

### 호환성 (기존 cli_bridge.py)

cli_bridge.py는 여전히 기존 형식을 지원합니다:
- Request: `{method, params}` → 내부적으로 `{method, args}`로 변환
- Response: `{success, data}` → 내부적으로 `{status, result}`로 변환

새 코드는 새로운 스키마를 사용하는 것을 권장합니다.

## 변경 이력

| 버전 | 날짜 | 변경사항 |
|------|------|---------|
| 1.0 | 2026-03-24 | 초기 정의: CliRequest, CliResponseSuccess, CliResponseError, CliMessageValidator |

## 참고

- 구현: `kis_agent/message_schema.py`
- 테스트: `tests/unit/test_message_schema.py` (44개 테스트 케이스)
- CLI Bridge: `kis_agent/cli_bridge.py`
