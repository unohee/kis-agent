"""JSON 메시지 형식 스키마 정의 — Request/Response 구조.

kis-agent CLI Bridge의 JSON 메시지 형식을 명시적으로 정의합니다.
모든 요청/응답은 이 스키마를 따릅니다.

Request 형식:
{
    "id": "req-001",              # 요청 ID (선택, 비동기 처리용)
    "method": "stock_api.get_stock_price",  # domain.method 형식
    "args": {"code": "005930"},   # 메서드 인자
    "timeout": 30000              # 타임아웃 (밀리초, 기본값 30000)
}

Response 형식 (성공):
{
    "id": "req-001",              # 요청과 동일 ID
    "result": {...},              # 실제 결과 데이터
    "status": "ok",               # 상태 (ok, error, timeout)
    "_notice": "optional market status"  # 시장 상태 공지 (선택)
}

Response 형식 (오류):
{
    "id": "req-001",              # 요청과 동일 ID
    "error": "error message",     # 에러 메시지
    "code": "ErrorClassName",     # 에러 클래스명
    "status": "error"             # 상태 (error)
}
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Union
from uuid import uuid4


class ResponseStatus(str, Enum):
    """응답 상태 열거형."""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class CliRequest:
    """CLI Bridge JSON 요청 스키마.

    Attributes:
        method: "domain.method" 형식의 메서드 경로 (필수)
        args: 메서드에 전달할 키워드 인자 (기본값: 빈 dict)
        timeout: 타임아웃 (밀리초, 기본값: 30000)
        id: 요청 ID (선택, 자동 생성)
    """
    method: str
    args: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30000
    id: Optional[str] = None

    def __post_init__(self):
        """요청 초기화 후 ID가 없으면 자동 생성."""
        if self.id is None:
            self.id = f"req-{uuid4().hex[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        """데이터클래스를 딕셔너리로 변환."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CliRequest":
        """딕셔너리에서 CliRequest 객체 생성."""
        return cls(
            method=data.get("method"),
            args=data.get("args", {}),
            timeout=data.get("timeout", 30000),
            id=data.get("id")
        )


@dataclass
class CliResponseSuccess:
    """CLI Bridge JSON 성공 응답 스키마.

    Attributes:
        id: 요청 ID (응답과 일치)
        result: API 실행 결과 데이터
        status: 상태 ("ok")
        notice: 시장 상태 공지 (선택)
    """
    id: str
    result: Any
    status: ResponseStatus = ResponseStatus.OK
    notice: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """데이터클래스를 딕셔너리로 변환."""
        data = {
            "id": self.id,
            "result": self.result,
            "status": self.status.value,
        }
        if self.notice:
            data["_notice"] = self.notice
        return data


@dataclass
class CliResponseError:
    """CLI Bridge JSON 에러 응답 스키마.

    Attributes:
        id: 요청 ID (응답과 일치, 요청 실패 시 null 가능)
        error: 에러 메시지
        code: 에러 클래스명
        status: 상태 ("error" 또는 "timeout")
    """
    id: Optional[str]
    error: str
    code: str
    status: ResponseStatus = ResponseStatus.ERROR

    def to_dict(self) -> Dict[str, Any]:
        """데이터클래스를 딕셔너리로 변환."""
        return {
            "id": self.id,
            "error": self.error,
            "code": self.code,
            "status": self.status.value,
        }


# 타입 별칭: 모든 응답 타입
CliResponse = Union[CliResponseSuccess, CliResponseError]


class CliMessageValidator:
    """CLI 메시지 구조 검증 클래스."""

    @staticmethod
    def validate_request(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """요청 메시지 검증.

        Args:
            data: 검증할 요청 딕셔너리

        Returns:
            (유효 여부, 에러 메시지)
        """
        # 필수 필드: method
        if "method" not in data or not isinstance(data["method"], str):
            return False, "Missing or invalid 'method' field (string required)"

        method = data["method"]
        if "." not in method:
            return False, f"Invalid 'method' format: '{method}'. Use 'domain.method'"

        parts = method.split(".")
        if len(parts) != 2 or not all(part.isidentifier() for part in parts):
            return False, f"Invalid 'method' format: '{method}'. Both domain and method must be valid identifiers"

        # args 필드 검증
        if "args" in data:
            if not isinstance(data["args"], dict):
                return False, "'args' must be a dictionary"

        # timeout 필드 검증
        if "timeout" in data:
            if not isinstance(data["timeout"], int) or data["timeout"] <= 0:
                return False, "'timeout' must be a positive integer"

        # id 필드 검증 (선택)
        if "id" in data and data["id"] is not None:
            if not isinstance(data["id"], str):
                return False, "'id' must be a string"

        return True, None

    @staticmethod
    def validate_response_success(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """성공 응답 메시지 검증.

        Args:
            data: 검증할 응답 딕셔너리

        Returns:
            (유효 여부, 에러 메시지)
        """
        # 필수 필드: id, result, status
        if "id" not in data or not isinstance(data["id"], str):
            return False, "Missing or invalid 'id' field (string required)"

        if "result" not in data:
            return False, "Missing 'result' field"

        if "status" not in data or data["status"] not in ("ok", "error", "timeout"):
            return False, "Missing or invalid 'status' field"

        if data["status"] != "ok":
            return False, f"Success response must have status='ok', got '{data['status']}'"

        # notice 필드 검증 (선택)
        if "_notice" in data and data["_notice"] is not None:
            if not isinstance(data["_notice"], str):
                return False, "'_notice' must be a string"

        return True, None

    @staticmethod
    def validate_response_error(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """에러 응답 메시지 검증.

        Args:
            data: 검증할 응답 딕셔너리

        Returns:
            (유효 여부, 에러 메시지)
        """
        # 필수 필드: id, error, code, status
        if "id" not in data or (data["id"] is not None and not isinstance(data["id"], str)):
            return False, "'id' must be a string or null"

        if "error" not in data or not isinstance(data["error"], str):
            return False, "Missing or invalid 'error' field (string required)"

        if "code" not in data or not isinstance(data["code"], str):
            return False, "Missing or invalid 'code' field (string required)"

        if "status" not in data or data["status"] not in ("error", "timeout"):
            return False, "Missing or invalid 'status' field (must be 'error' or 'timeout')"

        return True, None

    @staticmethod
    def validate_response(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """응답 메시지 검증 (성공/에러 자동 구분).

        Args:
            data: 검증할 응답 딕셔너리

        Returns:
            (유효 여부, 에러 메시지)
        """
        if not isinstance(data, dict):
            return False, "Response must be a dictionary"

        # 기본 필드 확인
        if "status" not in data:
            return False, "Missing 'status' field"

        status = data.get("status")

        # 성공 응답
        if status == "ok":
            return CliMessageValidator.validate_response_success(data)

        # 에러 응답
        elif status in ("error", "timeout"):
            return CliMessageValidator.validate_response_error(data)

        else:
            return False, f"Invalid 'status': {status}. Must be 'ok', 'error', or 'timeout'"
