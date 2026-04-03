"""메시지 스키마 검증 테스트.

kis_agent.message_schema의 요청/응답 메시지 포맷 검증을 테스트합니다.
"""

import pytest
from kis_agent.message_schema import (
    CliRequest,
    CliResponseSuccess,
    CliResponseError,
    ResponseStatus,
    CliMessageValidator,
)


class TestCliRequest:
    """CliRequest 데이터클래스 테스트."""

    def test_create_with_all_fields(self):
        """모든 필드가 있는 요청 생성."""
        req = CliRequest(
            method="stock_api.get_stock_price",
            args={"code": "005930"},
            timeout=60,
            id="req-custom-001"
        )
        assert req.method == "stock_api.get_stock_price"
        assert req.args == {"code": "005930"}
        assert req.timeout == 60
        assert req.id == "req-custom-001"

    def test_create_with_defaults(self):
        """기본값으로 요청 생성."""
        req = CliRequest(method="stock_api.get_stock_price")
        assert req.method == "stock_api.get_stock_price"
        assert req.args == {}
        assert req.timeout == 30000
        assert req.id is not None  # 자동 생성
        assert req.id.startswith("req-")

    def test_auto_generate_id(self):
        """ID 자동 생성 확인."""
        req1 = CliRequest(method="test.method")
        req2 = CliRequest(method="test.method")
        assert req1.id != req2.id

    def test_to_dict(self):
        """딕셔너리 변환."""
        req = CliRequest(
            method="stock_api.get_stock_price",
            args={"code": "005930"},
            timeout=60,
            id="req-001"
        )
        data = req.to_dict()
        assert data["method"] == "stock_api.get_stock_price"
        assert data["args"] == {"code": "005930"}
        assert data["timeout"] == 60
        assert data["id"] == "req-001"

    def test_from_dict(self):
        """딕셔너리에서 생성."""
        data = {
            "method": "stock_api.get_stock_price",
            "args": {"code": "005930"},
            "timeout": 60,
            "id": "req-001"
        }
        req = CliRequest.from_dict(data)
        assert req.method == "stock_api.get_stock_price"
        assert req.args == {"code": "005930"}
        assert req.timeout == 60
        assert req.id == "req-001"

    def test_from_dict_with_defaults(self):
        """기본값으로 딕셔너리에서 생성."""
        data = {"method": "test.method"}
        req = CliRequest.from_dict(data)
        assert req.method == "test.method"
        assert req.args == {}
        assert req.timeout == 30000
        assert req.id is not None  # __post_init__에서 자동 생성
        assert req.id.startswith("req-")


class TestCliResponseSuccess:
    """CliResponseSuccess 데이터클래스 테스트."""

    def test_create_with_all_fields(self):
        """모든 필드가 있는 성공 응답 생성."""
        resp = CliResponseSuccess(
            id="req-001",
            result={"price": 50000},
            status=ResponseStatus.OK,
            notice="시장 상태 알림"
        )
        assert resp.id == "req-001"
        assert resp.result == {"price": 50000}
        assert resp.status == ResponseStatus.OK
        assert resp.notice == "시장 상태 알림"

    def test_create_with_defaults(self):
        """기본값으로 성공 응답 생성."""
        resp = CliResponseSuccess(
            id="req-001",
            result={"price": 50000}
        )
        assert resp.id == "req-001"
        assert resp.result == {"price": 50000}
        assert resp.status == ResponseStatus.OK
        assert resp.notice is None

    def test_to_dict_with_notice(self):
        """공지가 있는 경우 딕셔너리 변환."""
        resp = CliResponseSuccess(
            id="req-001",
            result={"price": 50000},
            notice="시장 상태"
        )
        data = resp.to_dict()
        assert data["id"] == "req-001"
        assert data["result"] == {"price": 50000}
        assert data["status"] == "ok"
        assert data["_notice"] == "시장 상태"

    def test_to_dict_without_notice(self):
        """공지가 없는 경우 딕셔너리 변환."""
        resp = CliResponseSuccess(
            id="req-001",
            result={"price": 50000}
        )
        data = resp.to_dict()
        assert "_notice" not in data


class TestCliResponseError:
    """CliResponseError 데이터클래스 테스트."""

    def test_create_with_error_status(self):
        """에러 상태로 에러 응답 생성."""
        resp = CliResponseError(
            id="req-001",
            error="Invalid method",
            code="AttributeError",
            status=ResponseStatus.ERROR
        )
        assert resp.id == "req-001"
        assert resp.error == "Invalid method"
        assert resp.code == "AttributeError"
        assert resp.status == ResponseStatus.ERROR

    def test_create_with_timeout_status(self):
        """타임아웃 상태로 에러 응답 생성."""
        resp = CliResponseError(
            id="req-001",
            error="Request execution timed out",
            code="TimeoutError",
            status=ResponseStatus.TIMEOUT
        )
        assert resp.status == ResponseStatus.TIMEOUT

    def test_create_without_id(self):
        """요청 ID 없이 에러 응답 생성 (요청 실패 시)."""
        resp = CliResponseError(
            id=None,
            error="Invalid JSON",
            code="JSONDecodeError"
        )
        assert resp.id is None

    def test_to_dict(self):
        """딕셔너리 변환."""
        resp = CliResponseError(
            id="req-001",
            error="Invalid method",
            code="AttributeError"
        )
        data = resp.to_dict()
        assert data["id"] == "req-001"
        assert data["error"] == "Invalid method"
        assert data["code"] == "AttributeError"
        assert data["status"] == "error"


class TestCliMessageValidator:
    """CliMessageValidator 클래스 테스트."""

    class TestValidateRequest:
        """요청 메시지 검증 테스트."""

        def test_valid_request_minimal(self):
            """최소 필드만 있는 유효한 요청."""
            data = {"method": "stock_api.get_stock_price"}
            valid, error = CliMessageValidator.validate_request(data)
            assert valid
            assert error is None

        def test_valid_request_complete(self):
            """모든 필드가 있는 유효한 요청."""
            data = {
                "method": "stock_api.get_stock_price",
                "args": {"code": "005930"},
                "timeout": 60,
                "id": "req-001"
            }
            valid, error = CliMessageValidator.validate_request(data)
            assert valid
            assert error is None

        def test_invalid_missing_method(self):
            """method 필드 누락."""
            data = {"args": {}}
            valid, error = CliMessageValidator.validate_request(data)
            assert not valid
            assert "method" in error.lower()

        def test_invalid_method_not_string(self):
            """method가 문자열이 아님."""
            data = {"method": 123}
            valid, error = CliMessageValidator.validate_request(data)
            assert not valid

        def test_invalid_method_format_no_dot(self):
            """method 형식이 잘못됨 (점 없음)."""
            data = {"method": "get_stock_price"}
            valid, error = CliMessageValidator.validate_request(data)
            assert not valid
            assert "domain.method" in error

        def test_invalid_method_format_multiple_dots(self):
            """method 형식이 잘못됨 (점이 여러 개)."""
            data = {"method": "stock.api.get_stock_price"}
            valid, error = CliMessageValidator.validate_request(data)
            assert not valid

        def test_invalid_method_invalid_identifier(self):
            """method의 domain/method가 유효한 식별자가 아님."""
            data = {"method": "stock-api.get-price"}
            valid, error = CliMessageValidator.validate_request(data)
            assert not valid

        def test_invalid_args_not_dict(self):
            """args가 딕셔너리가 아님."""
            data = {
                "method": "stock_api.get_stock_price",
                "args": "invalid"
            }
            valid, error = CliMessageValidator.validate_request(data)
            assert not valid
            assert "args" in error

        def test_invalid_timeout_not_positive(self):
            """timeout이 양수가 아님."""
            data = {
                "method": "stock_api.get_stock_price",
                "timeout": 0
            }
            valid, error = CliMessageValidator.validate_request(data)
            assert not valid

        def test_invalid_timeout_not_int(self):
            """timeout이 정수가 아님."""
            data = {
                "method": "stock_api.get_stock_price",
                "timeout": "30"
            }
            valid, error = CliMessageValidator.validate_request(data)
            assert not valid

        def test_invalid_id_not_string(self):
            """id가 문자열이 아님."""
            data = {
                "method": "stock_api.get_stock_price",
                "id": 123
            }
            valid, error = CliMessageValidator.validate_request(data)
            assert not valid
            assert "id" in error

    class TestValidateResponseSuccess:
        """성공 응답 메시지 검증 테스트."""

        def test_valid_response(self):
            """유효한 성공 응답."""
            data = {
                "id": "req-001",
                "result": {"price": 50000},
                "status": "ok"
            }
            valid, error = CliMessageValidator.validate_response_success(data)
            assert valid
            assert error is None

        def test_valid_response_with_notice(self):
            """공지가 있는 유효한 응답."""
            data = {
                "id": "req-001",
                "result": {"price": 50000},
                "status": "ok",
                "_notice": "시장 상태"
            }
            valid, error = CliMessageValidator.validate_response_success(data)
            assert valid

        def test_invalid_missing_id(self):
            """id 필드 누락."""
            data = {
                "result": {"price": 50000},
                "status": "ok"
            }
            valid, error = CliMessageValidator.validate_response_success(data)
            assert not valid

        def test_invalid_missing_result(self):
            """result 필드 누락."""
            data = {
                "id": "req-001",
                "status": "ok"
            }
            valid, error = CliMessageValidator.validate_response_success(data)
            assert not valid

        def test_invalid_missing_status(self):
            """status 필드 누락."""
            data = {
                "id": "req-001",
                "result": {"price": 50000}
            }
            valid, error = CliMessageValidator.validate_response_success(data)
            assert not valid

        def test_invalid_wrong_status(self):
            """status가 'ok'가 아님."""
            data = {
                "id": "req-001",
                "result": {"price": 50000},
                "status": "error"
            }
            valid, error = CliMessageValidator.validate_response_success(data)
            assert not valid

        def test_invalid_notice_not_string(self):
            """_notice가 문자열이 아님."""
            data = {
                "id": "req-001",
                "result": {"price": 50000},
                "status": "ok",
                "_notice": 123
            }
            valid, error = CliMessageValidator.validate_response_success(data)
            assert not valid

    class TestValidateResponseError:
        """에러 응답 메시지 검증 테스트."""

        def test_valid_error_response(self):
            """유효한 에러 응답."""
            data = {
                "id": "req-001",
                "error": "Invalid method",
                "code": "AttributeError",
                "status": "error"
            }
            valid, error = CliMessageValidator.validate_response_error(data)
            assert valid
            assert error is None

        def test_valid_timeout_response(self):
            """유효한 타임아웃 응답."""
            data = {
                "id": "req-001",
                "error": "Request timed out",
                "code": "TimeoutError",
                "status": "timeout"
            }
            valid, error = CliMessageValidator.validate_response_error(data)
            assert valid

        def test_valid_response_without_id(self):
            """ID 없는 유효한 에러 응답."""
            data = {
                "id": None,
                "error": "Invalid JSON",
                "code": "JSONDecodeError",
                "status": "error"
            }
            valid, error = CliMessageValidator.validate_response_error(data)
            assert valid

        def test_invalid_missing_error(self):
            """error 필드 누락."""
            data = {
                "id": "req-001",
                "code": "AttributeError",
                "status": "error"
            }
            valid, error = CliMessageValidator.validate_response_error(data)
            assert not valid

        def test_invalid_missing_code(self):
            """code 필드 누락."""
            data = {
                "id": "req-001",
                "error": "Invalid method",
                "status": "error"
            }
            valid, error = CliMessageValidator.validate_response_error(data)
            assert not valid

        def test_invalid_status_ok(self):
            """status가 'ok'임 (에러 응답에서 불가)."""
            data = {
                "id": "req-001",
                "error": "Invalid method",
                "code": "AttributeError",
                "status": "ok"
            }
            valid, error = CliMessageValidator.validate_response_error(data)
            assert not valid

    class TestValidateResponse:
        """통합 응답 메시지 검증 테스트."""

        def test_valid_success_response(self):
            """유효한 성공 응답 검증."""
            data = {
                "id": "req-001",
                "result": {"price": 50000},
                "status": "ok"
            }
            valid, error = CliMessageValidator.validate_response(data)
            assert valid
            assert error is None

        def test_valid_error_response(self):
            """유효한 에러 응답 검증."""
            data = {
                "id": "req-001",
                "error": "Invalid method",
                "code": "AttributeError",
                "status": "error"
            }
            valid, error = CliMessageValidator.validate_response(data)
            assert valid

        def test_valid_timeout_response(self):
            """유효한 타임아웃 응답 검증."""
            data = {
                "id": "req-001",
                "error": "Request timed out",
                "code": "TimeoutError",
                "status": "timeout"
            }
            valid, error = CliMessageValidator.validate_response(data)
            assert valid

        def test_invalid_not_dict(self):
            """응답이 딕셔너리가 아님."""
            data = "not a dict"
            valid, error = CliMessageValidator.validate_response(data)
            assert not valid

        def test_invalid_missing_status(self):
            """status 필드 누락."""
            data = {
                "id": "req-001",
                "result": {"price": 50000}
            }
            valid, error = CliMessageValidator.validate_response(data)
            assert not valid

        def test_invalid_unknown_status(self):
            """알 수 없는 status."""
            data = {
                "id": "req-001",
                "status": "unknown"
            }
            valid, error = CliMessageValidator.validate_response(data)
            assert not valid
