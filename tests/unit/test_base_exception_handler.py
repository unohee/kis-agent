"""
Base Exception Handler 모듈 테스트

일관된 예외 처리를 위한 베이스 클래스와 데코레이터를 테스트합니다.
"""

import unittest
import logging
from unittest.mock import Mock, patch, MagicMock
import pytest
from io import StringIO

from pykis.core.base_exception_handler import (
    BaseExceptionHandler,
    exception_handler,
    safe_execute,
    SafeDict,
)


class TestBaseExceptionHandler(unittest.TestCase):
    """BaseExceptionHandler 테스트"""

    def setUp(self):
        self.handler = BaseExceptionHandler()

    def test_init_default_logger(self):
        """기본 로거 초기화"""
        self.assertEqual(self.handler.logger.name, "BaseExceptionHandler")

    def test_init_custom_logger(self):
        """커스텀 로거 초기화"""
        handler = BaseExceptionHandler("CustomLogger")
        self.assertEqual(handler.logger.name, "CustomLogger")

    @patch("pykis.core.base_exception_handler.logging.getLogger")
    def test_log_error_with_exception(self, mock_get_logger):
        """예외와 함께 에러 로깅"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        handler = BaseExceptionHandler()
        test_exception = ValueError("Test error")

        handler.log_error("Test message", test_exception)

        mock_logger.error.assert_called_once_with(
            "Test message: Test error", exc_info=True
        )

    @patch("pykis.core.base_exception_handler.logging.getLogger")
    def test_log_error_without_exception(self, mock_get_logger):
        """예외 없이 에러 로깅"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        handler = BaseExceptionHandler()

        handler.log_error("Test message")

        mock_logger.error.assert_called_once_with("Test message", exc_info=True)

    @patch("pykis.core.base_exception_handler.logging.getLogger")
    def test_log_error_no_traceback(self, mock_get_logger):
        """traceback 없이 에러 로깅"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        handler = BaseExceptionHandler()

        handler.log_error("Test message", include_traceback=False)

        mock_logger.error.assert_called_once_with("Test message")

    @patch("pykis.core.base_exception_handler.logging.getLogger")
    def test_log_warning_with_exception(self, mock_get_logger):
        """예외와 함께 경고 로깅"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        handler = BaseExceptionHandler()
        test_exception = ValueError("Test warning")

        handler.log_warning("Warning message", test_exception)

        mock_logger.warning.assert_called_once_with("Warning message: Test warning")

    @patch("pykis.core.base_exception_handler.logging.getLogger")
    def test_handle_exception_reraise_true(self, mock_get_logger):
        """예외 재발생 처리"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        handler = BaseExceptionHandler()
        test_exception = ValueError("Test error")

        with self.assertRaises(ValueError):
            handler.handle_exception("Test message", test_exception, reraise=True)

        mock_logger.error.assert_called_once()

    @patch("pykis.core.base_exception_handler.logging.getLogger")
    def test_handle_exception_reraise_false(self, mock_get_logger):
        """예외 재발생하지 않고 기본값 반환"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        handler = BaseExceptionHandler()
        test_exception = ValueError("Test error")

        result = handler.handle_exception(
            "Test message", test_exception, reraise=False, default_return="default"
        )

        self.assertEqual(result, "default")
        mock_logger.error.assert_called_once()

    @patch("pykis.core.base_exception_handler.logging.getLogger")
    def test_handle_exception_different_log_levels(self, mock_get_logger):
        """다양한 로그 레벨 테스트"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        handler = BaseExceptionHandler()
        test_exception = ValueError("Test error")

        # Warning 레벨
        handler.handle_exception(
            "Warning message", test_exception, reraise=False, log_level="warning"
        )
        mock_logger.warning.assert_called()

        # Info 레벨
        handler.handle_exception(
            "Info message", test_exception, reraise=False, log_level="info"
        )
        mock_logger.info.assert_called()


class TestExceptionHandlerDecorator(unittest.TestCase):
    """exception_handler 데코레이터 테스트"""

    def test_decorator_with_base_exception_handler(self):
        """BaseExceptionHandler를 상속받은 클래스에서 데코레이터 사용"""

        class TestClass(BaseExceptionHandler):
            @exception_handler(
                message="테스트 실행 실패", reraise=False, default_return="error"
            )
            def test_method(self):
                raise ValueError("Test error")

        instance = TestClass()
        result = instance.test_method()

        self.assertEqual(result, "error")

    def test_decorator_without_base_exception_handler(self):
        """BaseExceptionHandler를 상속받지 않은 클래스에서 데코레이터 사용"""

        class TestClass:
            @exception_handler(
                message="테스트 실행 실패", reraise=False, default_return="error"
            )
            def test_method(self):
                raise ValueError("Test error")

        instance = TestClass()
        result = instance.test_method()

        self.assertEqual(result, "error")

    def test_decorator_with_reraise_true(self):
        """reraise=True인 경우 예외 재발생"""

        class TestClass:
            @exception_handler(message="테스트 실행 실패", reraise=True)
            def test_method(self):
                raise ValueError("Test error")

        instance = TestClass()

        with self.assertRaises(ValueError):
            instance.test_method()

    def test_decorator_with_specific_exception(self):
        """특정 예외만 처리"""

        class TestClass:
            @exception_handler(
                message="ValueError만 처리",
                reraise=False,
                default_return="handled",
                exceptions=ValueError,
            )
            def test_method(self, raise_type="value"):
                if raise_type == "value":
                    raise ValueError("Value error")
                else:
                    raise TypeError("Type error")

        instance = TestClass()

        # ValueError는 처리됨
        result = instance.test_method("value")
        self.assertEqual(result, "handled")

        # TypeError는 처리되지 않음
        with self.assertRaises(TypeError):
            instance.test_method("type")

    def test_decorator_with_default_message(self):
        """기본 메시지 사용"""

        class TestClass:
            @exception_handler(reraise=False, default_return="default")
            def test_method_name(self):
                raise ValueError("Test error")

        instance = TestClass()
        result = instance.test_method_name()

        self.assertEqual(result, "default")

    def test_decorator_with_tuple_exceptions(self):
        """여러 예외 타입을 튜플로 지정"""

        class TestClass:
            @exception_handler(
                reraise=False,
                default_return="handled",
                exceptions=(ValueError, TypeError),
            )
            def test_method(self, error_type):
                if error_type == "value":
                    raise ValueError("Value error")
                elif error_type == "type":
                    raise TypeError("Type error")
                else:
                    raise RuntimeError("Runtime error")

        instance = TestClass()

        # ValueError 처리됨
        self.assertEqual(instance.test_method("value"), "handled")

        # TypeError 처리됨
        self.assertEqual(instance.test_method("type"), "handled")

        # RuntimeError는 처리되지 않음
        with self.assertRaises(RuntimeError):
            instance.test_method("runtime")


class TestSafeExecute(unittest.TestCase):
    """safe_execute 함수 테스트"""

    def test_safe_execute_success(self):
        """정상 실행"""

        def test_func(x, y):
            return x + y

        result = safe_execute(test_func, 1, 2)
        self.assertEqual(result, 3)

    def test_safe_execute_with_kwargs(self):
        """키워드 인자와 함께 실행"""

        def test_func(x, y, z=10):
            return x + y + z

        result = safe_execute(test_func, 1, 2, z=5)
        self.assertEqual(result, 8)

    @patch("pykis.core.base_exception_handler.logging.getLogger")
    def test_safe_execute_exception_reraise(self, mock_get_logger):
        """예외 발생 시 재발생"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        def test_func():
            raise ValueError("Test error")

        with self.assertRaises(ValueError):
            safe_execute(test_func, reraise=True)

        mock_logger.error.assert_called_once()

    @patch("pykis.core.base_exception_handler.logging.getLogger")
    def test_safe_execute_exception_no_reraise(self, mock_get_logger):
        """예외 발생 시 기본값 반환"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        def test_func():
            raise ValueError("Test error")

        result = safe_execute(test_func, reraise=False, default_return="default")

        self.assertEqual(result, "default")
        mock_logger.error.assert_called_once()

    def test_safe_execute_with_custom_logger(self):
        """커스텀 로거 사용"""
        custom_logger = Mock()

        def test_func():
            raise ValueError("Test error")

        result = safe_execute(
            test_func, logger=custom_logger, reraise=False, default_return="default"
        )

        self.assertEqual(result, "default")
        custom_logger.error.assert_called_once()


class TestSafeDict(unittest.TestCase):
    """SafeDict 클래스 테스트"""

    def setUp(self):
        self.safe_dict = SafeDict({"a": 1, "b": 2}, logger_name="TestSafeDict")

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.safe_dict["a"], 1)
        self.assertEqual(self.safe_dict["b"], 2)
        self.assertEqual(self.safe_dict.logger.name, "TestSafeDict")

    def test_getitem_existing_key(self):
        """존재하는 키 조회"""
        result = self.safe_dict["a"]
        self.assertEqual(result, 1)

    @patch("pykis.core.base_exception_handler.logging.getLogger")
    def test_getitem_missing_key(self, mock_get_logger):
        """존재하지 않는 키 조회"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        safe_dict = SafeDict({"a": 1})

        with self.assertRaises(KeyError):
            _ = safe_dict["missing"]

        mock_logger.warning.assert_called_once()

    def test_safe_get_existing_key(self):
        """safe_get으로 존재하는 키 조회"""
        result = self.safe_dict.safe_get("a")
        self.assertEqual(result, 1)

    def test_safe_get_missing_key_with_default(self):
        """safe_get으로 존재하지 않는 키 조회 (기본값 있음)"""
        result = self.safe_dict.safe_get("missing", "default")
        self.assertEqual(result, "default")

    def test_safe_get_missing_key_no_default(self):
        """safe_get으로 존재하지 않는 키 조회 (기본값 없음)"""
        result = self.safe_dict.safe_get("missing")
        self.assertIsNone(result)

    @patch("pykis.core.base_exception_handler.logging.getLogger")
    def test_safe_get_no_logging(self, mock_get_logger):
        """safe_get에서 로깅 비활성화"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        safe_dict = SafeDict({"a": 1})
        result = safe_dict.safe_get("missing", "default", log_missing=False)

        self.assertEqual(result, "default")
        mock_logger.debug.assert_not_called()

    @patch("pykis.core.base_exception_handler.logging.getLogger")
    def test_safe_get_with_logging(self, mock_get_logger):
        """safe_get에서 로깅 활성화"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        safe_dict = SafeDict({"a": 1})
        result = safe_dict.safe_get("missing", "default", log_missing=True)

        self.assertEqual(result, "default")
        mock_logger.debug.assert_called_once()


if __name__ == "__main__":
    unittest.main()
