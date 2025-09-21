"""
PyKIS 통합 예외 처리 시스템

이 모듈은 PyKIS 전체에서 사용되는 통일된 예외 처리 시스템을 제공합니다.
모든 예외는 반드시 traceback과 함께 로깅되고 raise되어야 합니다.
"""

import sys
import logging
import traceback
from typing import Optional, Any, Type, Union
from functools import wraps


# PyKIS 전용 예외 클래스들
class PyKISException(Exception):
    """PyKIS 기본 예외 클래스"""
    pass


class APIException(PyKISException):
    """API 호출 관련 예외"""
    pass


class AuthenticationException(PyKISException):
    """인증 관련 예외"""
    pass


class ValidationException(PyKISException):
    """데이터 검증 관련 예외"""
    pass


class NetworkException(PyKISException):
    """네트워크 관련 예외"""
    pass


class DataProcessingException(PyKISException):
    """데이터 처리 관련 예외"""
    pass


class ConfigurationException(PyKISException):
    """설정 관련 예외"""
    pass


class RateLimitException(PyKISException):
    """Rate Limit 관련 예외"""
    pass


class WebSocketException(PyKISException):
    """WebSocket 관련 예외"""
    pass


class ExceptionHandler:
    """
    통합 예외 처리 클래스

    모든 PyKIS 클래스는 이 클래스를 상속받아 일관된 예외 처리를 사용해야 합니다.
    예외는 절대 먹지 않고 반드시 traceback과 함께 raise합니다.
    """

    def __init__(self, logger_name: Optional[str] = None):
        """
        Args:
            logger_name: 사용할 로거 이름. None이면 클래스 이름 사용
        """
        if logger_name is None:
            logger_name = f"pykis.{self.__class__.__module__}.{self.__class__.__name__}"
        self._exception_logger = logging.getLogger(logger_name)

    def _handle_exception(self,
                         exception: Exception,
                         context: str,
                         reraise_as: Optional[Type[PyKISException]] = None) -> None:
        """
        예외 처리 핵심 메서드

        Args:
            exception: 발생한 예외
            context: 예외 발생 컨텍스트 설명
            reraise_as: 다른 예외 타입으로 변환하여 raise (None이면 원본 예외 raise)

        Raises:
            원본 예외 또는 변환된 예외를 반드시 raise
        """
        # 전체 traceback 정보 캡처
        exc_type, exc_value, exc_tb = sys.exc_info()
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        tb_text = ''.join(tb_lines)

        # 에러 메시지 구성
        error_msg = f"[{context}] {exception.__class__.__name__}: {str(exception)}"

        # 로깅 (전체 traceback 포함)
        self._exception_logger.error(f"{error_msg}\n{tb_text}")

        # 예외 재발생 (변환 또는 원본)
        if reraise_as:
            raise reraise_as(f"{error_msg}\n원본 예외: {exception}") from exception
        else:
            raise  # 원본 예외를 그대로 raise

    def _log_warning(self, message: str, exception: Optional[Exception] = None) -> None:
        """경고 로깅 (예외는 발생시키지 않음)"""
        if exception:
            self._exception_logger.warning(f"{message}: {exception}")
        else:
            self._exception_logger.warning(message)

    def _log_debug(self, message: str) -> None:
        """디버그 로깅"""
        self._exception_logger.debug(message)


def handle_exceptions(context: str = None,
                     reraise_as: Type[PyKISException] = None,
                     exceptions_to_catch: Union[Type[Exception], tuple] = Exception):
    """
    예외 처리 데코레이터

    Args:
        context: 에러 컨텍스트 설명 (None이면 함수명 사용)
        reraise_as: 다른 예외 타입으로 변환
        exceptions_to_catch: 캐치할 예외 타입들

    Example:
        @handle_exceptions(context="주식 정보 조회", reraise_as=APIException)
        def get_stock_info(self, code):
            return self.api.get_info(code)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions_to_catch as e:
                # self가 첫 번째 인자인 경우 (메서드)
                if args and hasattr(args[0], '_handle_exception'):
                    error_context = context or f"{func.__name__}"
                    args[0]._handle_exception(e, error_context, reraise_as)
                else:
                    # 일반 함수인 경우
                    error_context = context or f"{func.__name__}"
                    exc_type, exc_value, exc_tb = sys.exc_info()
                    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
                    tb_text = ''.join(tb_lines)

                    error_msg = f"[{error_context}] {e.__class__.__name__}: {str(e)}"
                    logging.error(f"{error_msg}\n{tb_text}")

                    if reraise_as:
                        raise reraise_as(f"{error_msg}\n원본 예외: {e}") from e
                    else:
                        raise
        return wrapper
    return decorator


def safe_execute(func, *args, context: str = None, **kwargs) -> Any:
    """
    안전한 함수 실행 (독립 함수용)

    모든 예외를 캐치하여 로깅하고 다시 raise합니다.

    Args:
        func: 실행할 함수
        *args: 함수 인자
        context: 실행 컨텍스트 설명
        **kwargs: 함수 키워드 인자

    Returns:
        함수 실행 결과

    Raises:
        함수 실행 중 발생한 모든 예외
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_context = context or f"{func.__name__ if hasattr(func, '__name__') else 'unknown'}"

        exc_type, exc_value, exc_tb = sys.exc_info()
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        tb_text = ''.join(tb_lines)

        error_msg = f"[{error_context}] {e.__class__.__name__}: {str(e)}"
        logging.error(f"{error_msg}\n{tb_text}")
        raise


def ensure_not_none(value: Any, name: str) -> Any:
    """
    값이 None이 아님을 보장

    Args:
        value: 확인할 값
        name: 값의 이름 (에러 메시지용)

    Returns:
        None이 아닌 값

    Raises:
        ValidationException: 값이 None인 경우
    """
    if value is None:
        raise ValidationException(f"{name}은(는) None일 수 없습니다")
    return value


def ensure_type(value: Any, expected_type: type, name: str) -> Any:
    """
    값의 타입을 확인

    Args:
        value: 확인할 값
        expected_type: 기대하는 타입
        name: 값의 이름 (에러 메시지용)

    Returns:
        타입이 확인된 값

    Raises:
        ValidationException: 타입이 맞지 않는 경우
    """
    if not isinstance(value, expected_type):
        raise ValidationException(
            f"{name}은(는) {expected_type.__name__} 타입이어야 하지만 "
            f"{type(value).__name__} 타입입니다"
        )
    return value


__all__ = [
    # 예외 클래스들
    'PyKISException',
    'APIException',
    'AuthenticationException',
    'ValidationException',
    'NetworkException',
    'DataProcessingException',
    'ConfigurationException',
    'RateLimitException',
    'WebSocketException',

    # 핸들러 클래스
    'ExceptionHandler',

    # 데코레이터 및 유틸리티
    'handle_exceptions',
    'safe_execute',
    'ensure_not_none',
    'ensure_type',
]