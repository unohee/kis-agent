"""
통합 예외 처리 시스템 테스트

새로운 예외 처리 시스템이 올바르게 작동하는지 검증합니다.
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch
import sys
import traceback

# 테스트 대상 import
from pykis.core.exceptions import (
    PyKISException,
    APIException,
    ValidationException,
    NetworkException,
    AuthenticationException,
    DataProcessingException,
    ExceptionHandler,
    handle_exceptions,
    ensure_not_none,
    ensure_type,
    safe_execute,
)


class TestExceptionTypes:
    """예외 타입 테스트"""

    def test_base_exception_inheritance(self):
        """모든 커스텀 예외가 PyKISException을 상속"""
        assert issubclass(APIException, PyKISException)
        assert issubclass(ValidationException, PyKISException)
        assert issubclass(NetworkException, PyKISException)
        assert issubclass(AuthenticationException, PyKISException)

    def test_exception_message(self):
        """예외 메시지가 올바르게 설정되는지 확인"""
        msg = "테스트 에러 메시지"
        e = APIException(msg)
        assert str(e) == msg


class TestExceptionHandler:
    """ExceptionHandler 클래스 테스트"""

    def test_handler_initialization(self):
        """핸들러 초기화 테스트"""
        handler = ExceptionHandler("test.module")
        assert handler._exception_logger.name == "test.module"

    def test_handler_without_name(self):
        """이름 없이 핸들러 초기화"""

        class TestClass(ExceptionHandler):
            pass

        obj = TestClass()
        assert "TestClass" in obj._exception_logger.name

    def test_handle_exception_with_raise(self, caplog):
        """예외 처리 및 재발생 테스트"""
        handler = ExceptionHandler("test")

        with pytest.raises(ValueError):
            try:
                raise ValueError("원본 에러")
            except ValueError as e:
                handler._handle_exception(e, "테스트 컨텍스트")

        # 로그에 traceback이 포함되었는지 확인
        assert "[테스트 컨텍스트]" in caplog.text
        assert "ValueError: 원본 에러" in caplog.text
        assert "Traceback" in caplog.text

    def test_handle_exception_with_reraise_as(self, caplog):
        """다른 예외 타입으로 변환하여 재발생"""
        handler = ExceptionHandler("test")

        with pytest.raises(APIException) as exc_info:
            try:
                raise ValueError("원본 에러")
            except ValueError as e:
                handler._handle_exception(e, "변환 테스트", reraise_as=APIException)

        # 새 예외가 원본 예외 정보를 포함하는지 확인
        assert "원본 에러" in str(exc_info.value)
        assert "변환 테스트" in str(exc_info.value)

    def test_log_warning(self, caplog):
        """경고 로깅 테스트"""
        handler = ExceptionHandler("test")
        handler._log_warning("경고 메시지", Exception("예외 정보"))

        assert "경고 메시지: 예외 정보" in caplog.text


class TestHandleExceptionsDecorator:
    """handle_exceptions 데코레이터 테스트"""

    def test_decorator_on_method(self, caplog):
        """메서드에 데코레이터 적용"""

        class TestAPI(ExceptionHandler):
            def __init__(self):
                super().__init__("TestAPI")

            @handle_exceptions(context="테스트 작업", reraise_as=APIException)
            def failing_method(self):
                raise ValueError("의도된 에러")

        api = TestAPI()

        with pytest.raises(APIException) as exc_info:
            api.failing_method()

        assert "테스트 작업" in str(exc_info.value)
        assert "ValueError" in str(exc_info.value)

    def test_decorator_on_function(self):
        """일반 함수에 데코레이터 적용"""

        @handle_exceptions(context="함수 테스트")
        def failing_function():
            raise RuntimeError("함수 에러")

        with pytest.raises(RuntimeError):
            failing_function()

    def test_decorator_with_specific_exceptions(self):
        """특정 예외만 캐치하는 데코레이터"""

        class TestAPI(ExceptionHandler):
            @handle_exceptions(context="특정 예외", exceptions_to_catch=ValueError)
            def method_with_specific_catch(self, error_type):
                if error_type == "value":
                    raise ValueError("값 에러")
                elif error_type == "runtime":
                    raise RuntimeError("런타임 에러")

        api = TestAPI()

        # ValueError는 캐치됨
        with pytest.raises(ValueError):
            api.method_with_specific_catch("value")

        # RuntimeError는 캐치 안됨 (그대로 통과)
        with pytest.raises(RuntimeError):
            api.method_with_specific_catch("runtime")


class TestValidationFunctions:
    """입력 검증 함수 테스트"""

    def test_ensure_not_none_valid(self):
        """None이 아닌 값 검증 성공"""
        result = ensure_not_none("valid", "테스트값")
        assert result == "valid"

    def test_ensure_not_none_invalid(self):
        """None 값 검증 실패"""
        with pytest.raises(ValidationException) as exc_info:
            ensure_not_none(None, "테스트값")

        assert "테스트값은(는) None일 수 없습니다" in str(exc_info.value)

    def test_ensure_type_valid(self):
        """올바른 타입 검증 성공"""
        result = ensure_type("문자열", str, "테스트값")
        assert result == "문자열"

        result = ensure_type(123, int, "숫자")
        assert result == 123

    def test_ensure_type_invalid(self):
        """잘못된 타입 검증 실패"""
        with pytest.raises(ValidationException) as exc_info:
            ensure_type(123, str, "문자열값")

        assert "문자열값은(는) str 타입이어야" in str(exc_info.value)
        assert "int 타입입니다" in str(exc_info.value)


class TestSafeExecute:
    """safe_execute 함수 테스트"""

    def test_safe_execute_success(self):
        """정상 실행"""

        def add(a, b):
            return a + b

        result = safe_execute(add, 1, 2)
        assert result == 3

    def test_safe_execute_with_exception(self, caplog):
        """예외 발생 시"""

        def failing_func():
            raise ValueError("실패")

        with pytest.raises(ValueError):
            safe_execute(failing_func, context="안전 실행 테스트")

        assert "안전 실행 테스트" in caplog.text
        assert "ValueError: 실패" in caplog.text


class TestIntegrationWithStockAPI:
    """StockAPI와의 통합 테스트"""

    @pytest.fixture
    def mock_client(self):
        """Mock KISClient"""
        client = Mock()
        client.make_request = MagicMock()
        return client

    @pytest.fixture
    def mock_account(self):
        """Mock 계좌 정보"""
        return {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    def test_stock_api_validation(self, mock_client, mock_account):
        """StockAPI 입력 검증 테스트"""
        from pykis.stock.api_improved import StockAPI

        api = StockAPI(mock_client, mock_account)

        # 잘못된 종목코드 길이 - APIException으로 변환됨
        with pytest.raises(APIException) as exc_info:
            api.get_stock_price("123")  # 3자리

        assert "종목코드는 6자리" in str(exc_info.value)

        # None 종목코드 - APIException으로 변환됨
        with pytest.raises(APIException) as exc_info:
            api.get_stock_price(None)

        assert "None일 수 없습니다" in str(exc_info.value)

    def test_stock_api_network_error(self, mock_client, mock_account, caplog):
        """네트워크 오류 처리 테스트"""
        from pykis.stock.api_improved import StockAPI

        api = StockAPI(mock_client, mock_account)

        # 네트워크 오류 시뮬레이션
        mock_client.make_request.side_effect = NetworkException("연결 실패")

        with pytest.raises(APIException) as exc_info:
            api.get_stock_price("005930")

        # 원본 네트워크 예외가 APIException으로 변환되었는지 확인
        assert "주식 현재가 조회" in str(exc_info.value)

        # 로그에 전체 traceback이 있는지 확인
        assert "Traceback" in caplog.text
        assert "NetworkException" in caplog.text

    def test_stock_api_response_validation(self, mock_client, mock_account):
        """API 응답 검증 테스트"""
        from pykis.stock.api_improved import StockAPI

        api = StockAPI(mock_client, mock_account)

        # 빈 응답
        mock_client.make_request.return_value = None

        with pytest.raises(APIException) as exc_info:
            api.get_stock_price("005930")

        assert "API 응답이 없습니다" in str(exc_info.value)

        # 오류 응답
        mock_client.make_request.return_value = {"rt_cd": "1", "msg1": "시스템 점검 중"}

        with pytest.raises(APIException) as exc_info:
            api.get_stock_price("005930")

        assert "API 오류 발생" in str(exc_info.value)
        assert "시스템 점검 중" in str(exc_info.value)


class TestExceptionChaining:
    """예외 체이닝 테스트"""

    def test_exception_chain_preserved(self):
        """예외 체인이 보존되는지 확인"""

        def inner_function():
            raise ValueError("내부 에러")

        def outer_function():
            try:
                inner_function()
            except ValueError as e:
                raise APIException("외부 에러") from e

        with pytest.raises(APIException) as exc_info:
            outer_function()

        # 예외 체인 확인
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)
        assert str(exc_info.value.__cause__) == "내부 에러"


class TestLoggingIntegration:
    """로깅 통합 테스트"""

    def test_full_traceback_in_logs(self, caplog):
        """로그에 전체 traceback이 포함되는지 확인"""
        caplog.set_level(logging.ERROR)

        class TestClass(ExceptionHandler):
            def failing_method(self):
                try:
                    self.nested_method()
                except Exception as e:
                    self._handle_exception(e, "최상위 메서드")

            def nested_method(self):
                self.deep_nested_method()

            def deep_nested_method(self):
                raise RuntimeError("깊은 곳의 에러")

        obj = TestClass()

        with pytest.raises(RuntimeError):
            obj.failing_method()

        # 전체 호출 스택이 로그에 있는지 확인
        assert "failing_method" in caplog.text
        assert "nested_method" in caplog.text
        assert "deep_nested_method" in caplog.text
        assert "깊은 곳의 에러" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
