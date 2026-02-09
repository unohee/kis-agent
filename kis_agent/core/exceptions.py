"""
PyKIS 통합 예외 처리 시스템

이 모듈은 PyKIS 전체에서 사용되는 통일된 예외 처리 시스템을 제공합니다.

주요 컴포넌트:
1. 예외 클래스 계층 (PyKISException 기반)
2. ExceptionHandler 믹스인 클래스
3. @api_method 데코레이터 (API 메서드 자동 예외 처리)
4. 유틸리티 함수들

사용 예시:
    from kis_agent.core.exceptions import APIException, api_method

    class MyAPI(ExceptionHandler):
        @api_method("주식 조회")
        def get_stock(self, code):
            return self.client.request(...)

        @api_method("주문 실행", reraise=True)
        def order(self, code, qty):
            return self.client.order(...)
"""

import logging
import sys
import traceback
from functools import wraps
from typing import Any, Callable, Optional, Type, Union

# =============================================================================
# PyKIS 전용 예외 클래스 계층
# =============================================================================


class PyKISException(Exception):
    """PyKIS 기본 예외 클래스

    모든 PyKIS 예외의 부모 클래스입니다.
    """

    pass


class APIException(PyKISException):
    """API 호출 관련 예외

    - HTTP 요청 실패
    - API 응답 오류 (rt_cd != "0")
    - 요청 타임아웃
    """

    pass


class AuthenticationException(PyKISException):
    """인증 관련 예외

    - 토큰 발급 실패
    - 토큰 만료
    - 인증 정보 오류
    """

    pass


class ValidationException(PyKISException):
    """데이터 검증 관련 예외

    - 필수 파라미터 누락
    - 잘못된 파라미터 형식
    - 범위 초과
    """

    pass


class NetworkException(PyKISException):
    """네트워크 관련 예외

    - 연결 실패
    - DNS 오류
    - SSL 오류
    """

    pass


class DataProcessingException(PyKISException):
    """데이터 처리 관련 예외

    - JSON 파싱 오류
    - 데이터 변환 오류
    - 필드 누락
    """

    pass


class ConfigurationException(PyKISException):
    """설정 관련 예외

    - 환경변수 누락
    - 설정 파일 오류
    - 잘못된 설정값
    """

    pass


class RateLimitException(PyKISException):
    """Rate Limit 관련 예외

    - API 호출 한도 초과
    - 요청 빈도 제한
    """

    pass


class WebSocketException(PyKISException):
    """WebSocket 관련 예외

    - 연결 실패
    - 메시지 수신 오류
    - 구독 실패
    """

    pass


class OrderException(PyKISException):
    """주문 관련 예외

    - 주문 실패
    - 잔고 부족
    - 주문 가능 시간 외
    """

    pass


# =============================================================================
# ExceptionHandler 믹스인 클래스
# =============================================================================


class ExceptionHandler:
    """
    통합 예외 처리 믹스인 클래스

    모든 PyKIS API 클래스는 이 클래스를 상속받아 일관된 예외 처리를 사용합니다.

    사용 예시:
        class AccountAPI(ExceptionHandler):
            def __init__(self, client):
                ExceptionHandler.__init__(self)
                self.client = client

            @api_method("계좌 잔고 조회")
            def get_balance(self):
                return self.client.request(...)
    """

    _exception_logger: logging.Logger

    def __init__(self, logger_name: Optional[str] = None):
        """
        Args:
            logger_name: 사용할 로거 이름. None이면 클래스 이름 사용
        """
        if logger_name is None:
            logger_name = self.__class__.__name__
        self._exception_logger = logging.getLogger(logger_name)

    def _handle_exception(
        self,
        exception: Exception,
        context: str,
        reraise: bool = True,
        default_return: Any = None,
    ) -> Any:
        """
        예외 처리 핵심 메서드

        Args:
            exception: 발생한 예외
            context: 예외 발생 컨텍스트 설명
            reraise: True면 예외 재발생, False면 default_return 반환
            default_return: reraise=False일 때 반환할 기본값

        Returns:
            reraise=False일 때 default_return

        Raises:
            reraise=True일 때 APIException으로 래핑된 예외
        """
        # 에러 메시지 구성
        error_msg = f"[{context}] {exception.__class__.__name__}: {str(exception)}"

        # 로깅 (exc_info=True로 traceback 자동 포함)
        self._exception_logger.error(error_msg, exc_info=True)

        if reraise:
            # PyKIS 예외는 그대로, 그 외는 APIException으로 래핑
            if isinstance(exception, PyKISException):
                raise
            raise APIException(error_msg) from exception
        else:
            return default_return

    def _log_warning(self, message: str, exception: Optional[Exception] = None) -> None:
        """경고 로깅 (예외는 발생시키지 않음)"""
        if exception:
            self._exception_logger.warning(f"{message}: {exception}")
        else:
            self._exception_logger.warning(message)

    def _log_debug(self, message: str) -> None:
        """디버그 로깅"""
        self._exception_logger.debug(message)

    def _log_info(self, message: str) -> None:
        """정보 로깅"""
        self._exception_logger.info(message)


# =============================================================================
# 예외 처리 데코레이터
# =============================================================================


def api_method(
    context: str,
    reraise: bool = True,
    default_return: Any = None,
    exceptions: Union[Type[Exception], tuple] = Exception,
) -> Callable:
    """
    API 메서드 자동 예외 처리 데코레이터

    모든 예외를 캐치하여 로깅하고, reraise 설정에 따라 처리합니다.
    ExceptionHandler를 상속받은 클래스의 메서드에서 사용합니다.

    Args:
        context: 에러 컨텍스트 설명 (예: "계좌 잔고 조회", "주문 실행")
        reraise: True면 예외 재발생 (기본값), False면 default_return 반환
        default_return: reraise=False일 때 반환할 기본값 (기본: None)
        exceptions: 캐치할 예외 타입들 (기본: Exception)

    Note:
        - 기본값 reraise=True로 예외가 조용히 무시되지 않습니다.
        - 예외를 suppress하려면 명시적으로 reraise=False를 지정하세요.
        - reraise=False 사용 시 호출자는 반드시 None 체크를 해야 합니다.

    Example:
        class AccountAPI(ExceptionHandler):
            # 기본: 예외 발생 시 APIException으로 래핑되어 재발생
            @api_method("계좌 잔고 조회")
            def get_balance(self):
                return self.client.request(...)

            # 명시적으로 예외 suppress (호출자가 None 체크 필요)
            @api_method("종목 조회", reraise=False, default_return={})
            def get_stock(self, code):
                return self.client.get(...)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                return func(self, *args, **kwargs)
            except exceptions as e:
                # ExceptionHandler 상속 클래스인 경우
                if hasattr(self, "_handle_exception"):
                    return self._handle_exception(
                        exception=e,
                        context=context,
                        reraise=reraise,
                        default_return=default_return,
                    )
                else:
                    # ExceptionHandler를 상속받지 않은 경우 기본 로깅
                    logger = logging.getLogger(self.__class__.__name__)
                    error_msg = f"[{context}] {e.__class__.__name__}: {str(e)}"
                    logger.error(error_msg, exc_info=True)

                    if reraise:
                        raise APIException(error_msg) from e
                    return default_return

        return wrapper

    return decorator


def handle_exceptions(
    context: Optional[str] = None,
    reraise_as: Optional[Type[PyKISException]] = None,
    exceptions_to_catch: Union[Type[Exception], tuple] = Exception,
) -> Callable:
    """
    예외 처리 데코레이터 (레거시 호환용)

    새 코드에서는 @api_method 사용을 권장합니다.

    Args:
        context: 에러 컨텍스트 설명 (None이면 함수명 사용)
        reraise_as: 다른 예외 타입으로 변환
        exceptions_to_catch: 캐치할 예외 타입들

    Example:
        @handle_exceptions(context="주식 정보 조회", reraise_as=APIException)
        def get_stock_info(self, code):
            return self.api.get_info(code)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except exceptions_to_catch as e:
                error_context = context or func.__name__

                # self가 첫 번째 인자인 경우 (메서드)
                if args and hasattr(args[0], "_handle_exception"):
                    return args[0]._handle_exception(
                        exception=e,
                        context=error_context,
                        reraise=True,
                        default_return=None,
                    )
                else:
                    # 일반 함수인 경우
                    error_msg = f"[{error_context}] {e.__class__.__name__}: {str(e)}"
                    logging.error(error_msg, exc_info=True)

                    if reraise_as:
                        raise reraise_as(error_msg) from e
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
        error_context = (
            context or f"{func.__name__ if hasattr(func, '__name__') else 'unknown'}"
        )

        exc_type, exc_value, exc_tb = sys.exc_info()
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        tb_text = "".join(tb_lines)

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
    "PyKISException",
    "APIException",
    "AuthenticationException",
    "ValidationException",
    "NetworkException",
    "DataProcessingException",
    "ConfigurationException",
    "RateLimitException",
    "WebSocketException",
    "OrderException",
    # 핸들러 클래스
    "ExceptionHandler",
    # 데코레이터 및 유틸리티
    "api_method",
    "handle_exceptions",
    "safe_execute",
    "ensure_not_none",
    "ensure_type",
]
