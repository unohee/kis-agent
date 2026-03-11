"""
PyKIS 예외 처리 시스템 포괄적 단위 테스트

INT-377: core/exceptions.py 커버리지 개선
생성일: 2026-01-04
"""

import logging

import pytest

from kis_agent.core.exceptions import (
    APIException,
    AuthenticationException,
    ConfigurationException,
    DataProcessingException,
    ExceptionHandler,
    NetworkException,
    OrderException,
    PyKISException,
    RateLimitException,
    ValidationException,
    WebSocketException,
    api_method,
    ensure_not_none,
    ensure_type,
    handle_exceptions,
    safe_execute,
)


class TestExceptionHierarchy:
    """예외 클래스 계층 구조 테스트"""

    def test_all_exceptions_inherit_from_pykis_exception(self):
        """모든 예외가 PyKISException을 상속"""
        exceptions = [
            APIException,
            AuthenticationException,
            ValidationException,
            NetworkException,
            DataProcessingException,
            ConfigurationException,
            RateLimitException,
            WebSocketException,
            OrderException,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, PyKISException)
            assert issubclass(exc_class, Exception)

    def test_exception_instantiation(self):
        """각 예외 클래스 인스턴스화"""
        msg = "테스트 에러 메시지"

        exc = PyKISException(msg)
        assert str(exc) == msg

        exc = APIException(msg)
        assert str(exc) == msg

        exc = AuthenticationException(msg)
        assert str(exc) == msg

        exc = ValidationException(msg)
        assert str(exc) == msg

        exc = NetworkException(msg)
        assert str(exc) == msg

        exc = DataProcessingException(msg)
        assert str(exc) == msg

        exc = ConfigurationException(msg)
        assert str(exc) == msg

        exc = RateLimitException(msg)
        assert str(exc) == msg

        exc = WebSocketException(msg)
        assert str(exc) == msg

        exc = OrderException(msg)
        assert str(exc) == msg


class TestExceptionHandler:
    """ExceptionHandler 믹스인 클래스 테스트"""

    def test_init_with_default_logger(self):
        """기본 로거 이름으로 초기화"""

        class TestHandler(ExceptionHandler):
            pass

        handler = TestHandler()
        assert handler._exception_logger.name == "TestHandler"

    def test_init_with_custom_logger(self):
        """커스텀 로거 이름으로 초기화"""

        class TestHandler(ExceptionHandler):
            def __init__(self):
                super().__init__(logger_name="CustomLogger")

        handler = TestHandler()
        assert handler._exception_logger.name == "CustomLogger"

    def test_handle_exception_reraise_pykis_exception(self):
        """PyKISException은 그대로 재발생 (L206-207)"""

        class TestHandler(ExceptionHandler):
            def trigger(self):
                try:
                    raise APIException("원본 예외")
                except Exception as e:
                    self._handle_exception(e, "테스트 컨텍스트", reraise=True)

        handler = TestHandler()
        with pytest.raises(APIException) as exc_info:
            handler.trigger()
        assert "원본 예외" in str(exc_info.value)

    def test_handle_exception_wrap_generic_exception(self):
        """일반 예외는 APIException으로 래핑 (L208)"""

        class TestHandler(ExceptionHandler):
            def trigger(self):
                try:
                    raise ValueError("일반 예외")
                except Exception as e:
                    self._handle_exception(e, "테스트", reraise=True)

        handler = TestHandler()
        with pytest.raises(APIException):
            handler.trigger()

    def test_handle_exception_no_reraise(self):
        """reraise=False면 default_return 반환 (L209-210)"""

        class TestHandler(ExceptionHandler):
            def trigger(self):
                try:
                    raise ValueError("에러")
                except Exception as e:
                    return self._handle_exception(
                        e, "테스트", reraise=False, default_return={"status": "failed"}
                    )

        handler = TestHandler()
        result = handler.trigger()
        assert result == {"status": "failed"}

    def test_log_warning_with_exception(self, caplog):
        """_log_warning 예외 포함 (L214-215)"""

        class TestHandler(ExceptionHandler):
            pass

        handler = TestHandler()
        with caplog.at_level(logging.WARNING):
            handler._log_warning("경고 메시지", ValueError("원인"))

        assert "경고 메시지" in caplog.text
        assert "원인" in caplog.text

    def test_log_warning_without_exception(self, caplog):
        """_log_warning 예외 없이 (L216-217)"""

        class TestHandler(ExceptionHandler):
            pass

        handler = TestHandler()
        with caplog.at_level(logging.WARNING):
            handler._log_warning("단순 경고")

        assert "단순 경고" in caplog.text

    def test_log_debug(self, caplog):
        """_log_debug (L220-221)"""

        class TestHandler(ExceptionHandler):
            pass

        handler = TestHandler()
        with caplog.at_level(logging.DEBUG):
            handler._log_debug("디버그 메시지")

        assert "디버그 메시지" in caplog.text

    def test_log_info(self, caplog):
        """_log_info (L223-225)"""

        class TestHandler(ExceptionHandler):
            pass

        handler = TestHandler()
        with caplog.at_level(logging.INFO):
            handler._log_info("정보 메시지")

        assert "정보 메시지" in caplog.text


class TestApiMethodDecorator:
    """@api_method 데코레이터 테스트"""

    def test_api_method_success(self):
        """정상 실행 시 결과 반환"""

        class TestAPI(ExceptionHandler):
            @api_method("테스트 API")
            def success_method(self):
                return {"result": "success"}

        api = TestAPI()
        result = api.success_method()
        assert result == {"result": "success"}

    def test_api_method_reraise_true(self):
        """reraise=True 시 예외 재발생"""

        class TestAPI(ExceptionHandler):
            @api_method("테스트 API", reraise=True)
            def failing_method(self):
                raise ValueError("실패")

        api = TestAPI()
        with pytest.raises(APIException):
            api.failing_method()

    def test_api_method_reraise_false(self):
        """reraise=False 시 default_return 반환"""

        class TestAPI(ExceptionHandler):
            @api_method("테스트 API", reraise=False, default_return=None)
            def failing_method(self):
                raise ValueError("실패")

        api = TestAPI()
        result = api.failing_method()
        assert result is None

    def test_api_method_without_exception_handler(self, caplog):
        """ExceptionHandler 상속 없이 사용 (L283-291)"""

        class PlainClass:
            @api_method("Plain API", reraise=True)
            def method(self):
                raise ValueError("에러")

        obj = PlainClass()
        with caplog.at_level(logging.ERROR), pytest.raises(APIException):
            obj.method()

        assert "Plain API" in caplog.text

    def test_api_method_without_handler_no_reraise(self, caplog):
        """ExceptionHandler 없이 reraise=False (L291)"""

        class PlainClass:
            @api_method("Plain API", reraise=False, default_return="default")
            def method(self):
                raise ValueError("에러")

        obj = PlainClass()
        with caplog.at_level(logging.ERROR):
            result = obj.method()

        assert result == "default"


class TestHandleExceptionsDecorator:
    """@handle_exceptions 데코레이터 테스트 (L298-346)"""

    def test_handle_exceptions_success(self):
        """정상 실행 시 결과 반환"""

        class TestAPI(ExceptionHandler):
            @handle_exceptions(context="테스트")
            def method(self):
                return "success"

        api = TestAPI()
        assert api.method() == "success"

    def test_handle_exceptions_with_handler(self):
        """ExceptionHandler 상속 클래스에서 예외 처리 (L328-334)"""

        class TestAPI(ExceptionHandler):
            @handle_exceptions(context="테스트")
            def method(self):
                raise ValueError("에러")

        api = TestAPI()
        with pytest.raises(APIException):
            api.method()

    def test_handle_exceptions_without_handler(self, caplog):
        """ExceptionHandler 없이 예외 처리 (L335-342)"""

        @handle_exceptions(context="함수 테스트")
        def standalone_function():
            raise ValueError("에러")

        with caplog.at_level(logging.ERROR), pytest.raises(ValueError):
            standalone_function()

        assert "함수 테스트" in caplog.text

    def test_handle_exceptions_reraise_as(self):
        """reraise_as로 예외 타입 변환 (L340-341)"""

        @handle_exceptions(context="변환 테스트", reraise_as=ValidationException)
        def function_with_reraise():
            raise ValueError("원본")

        with pytest.raises(ValidationException):
            function_with_reraise()

    def test_handle_exceptions_default_context(self):
        """context=None이면 함수명 사용 (L325)"""

        @handle_exceptions()  # context 없음
        def my_function():
            raise ValueError("에러")

        with pytest.raises(ValueError):
            my_function()


class TestSafeExecute:
    """safe_execute 함수 테스트 (L349-380)"""

    def test_safe_execute_success(self):
        """정상 실행 시 결과 반환"""

        def add(a, b):
            return a + b

        result = safe_execute(add, 1, 2)
        assert result == 3

    def test_safe_execute_with_kwargs(self):
        """키워드 인자 전달"""

        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = safe_execute(greet, "World", greeting="Hi")
        assert result == "Hi, World!"

    def test_safe_execute_exception(self, caplog):
        """예외 발생 시 로깅 후 재발생 (L369-380)"""

        def failing():
            raise RuntimeError("실행 실패")

        with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError):
            safe_execute(failing, context="테스트 컨텍스트")

        assert "테스트 컨텍스트" in caplog.text
        assert "실행 실패" in caplog.text

    def test_safe_execute_without_context(self, caplog):
        """context 없으면 함수명 사용 (L370-372)"""

        def my_failing_func():
            raise ValueError("에러")

        with caplog.at_level(logging.ERROR), pytest.raises(ValueError):
            safe_execute(my_failing_func)

        assert "my_failing_func" in caplog.text

    def test_safe_execute_lambda(self, caplog):
        """람다 함수 (이름 없는 함수) 처리"""

        with caplog.at_level(logging.ERROR), pytest.raises(ZeroDivisionError):
            safe_execute(lambda: 1 / 0)


class TestEnsureNotNone:
    """ensure_not_none 함수 테스트 (L383-399)"""

    def test_ensure_not_none_valid(self):
        """유효한 값은 그대로 반환"""
        assert ensure_not_none("value", "test") == "value"
        assert ensure_not_none(0, "number") == 0
        assert ensure_not_none([], "list") == []
        assert ensure_not_none(False, "bool") is False

    def test_ensure_not_none_raises(self):
        """None이면 ValidationException 발생 (L397-398)"""
        with pytest.raises(ValidationException) as exc_info:
            ensure_not_none(None, "필수값")

        assert "필수값" in str(exc_info.value)
        assert "None" in str(exc_info.value)


class TestEnsureType:
    """ensure_type 함수 테스트 (L402-422)"""

    def test_ensure_type_valid(self):
        """올바른 타입은 그대로 반환"""
        assert ensure_type("hello", str, "text") == "hello"
        assert ensure_type(42, int, "number") == 42
        assert ensure_type([1, 2], list, "items") == [1, 2]
        assert ensure_type({"a": 1}, dict, "data") == {"a": 1}

    def test_ensure_type_raises(self):
        """타입 불일치 시 ValidationException 발생 (L417-421)"""
        with pytest.raises(ValidationException) as exc_info:
            ensure_type("not_a_number", int, "숫자값")

        error_msg = str(exc_info.value)
        assert "숫자값" in error_msg
        assert "int" in error_msg
        assert "str" in error_msg

    def test_ensure_type_subclass(self):
        """서브클래스도 통과"""

        class MyList(list):
            pass

        my_list = MyList([1, 2, 3])
        assert ensure_type(my_list, list, "items") == my_list


class TestExceptionChaining:
    """예외 체이닝 테스트"""

    def test_exception_chaining_preserved(self):
        """원본 예외가 __cause__로 보존됨"""

        class TestAPI(ExceptionHandler):
            @api_method("체이닝 테스트")
            def method(self):
                raise ValueError("원본 에러")

        api = TestAPI()
        with pytest.raises(APIException) as exc_info:
            api.method()

        # 원본 예외가 __cause__로 연결됨
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
