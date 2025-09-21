"""
Base exception handler for consistent error handling across PyKIS.

이 모듈은 PyKIS 전체에서 일관된 예외 처리를 위한 베이스 클래스를 제공합니다.
"""

import logging
import traceback
from typing import Optional, Any, Callable, Union, Type, Dict
from functools import wraps
import sys


class BaseExceptionHandler:
    """
    예외 처리를 위한 베이스 클래스

    모든 PyKIS 클래스는 이 클래스를 상속받아 일관된 예외 처리를 사용할 수 있습니다.
    """

    def __init__(self, logger_name: Optional[str] = None):
        """
        Args:
            logger_name: 사용할 로거 이름. None이면 클래스 이름 사용
        """
        if logger_name is None:
            logger_name = self.__class__.__name__
        self.logger = logging.getLogger(logger_name)

    def log_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        include_traceback: bool = True,
    ) -> None:
        """
        에러 로깅 (traceback 포함)

        Args:
            message: 로그 메시지
            exception: 예외 객체
            include_traceback: traceback 포함 여부
        """
        if exception:
            full_message = f"{message}: {exception}"
        else:
            full_message = message

        if include_traceback:
            self.logger.error(full_message, exc_info=True)
        else:
            self.logger.error(full_message)

    def log_warning(self, message: str, exception: Optional[Exception] = None) -> None:
        """
        경고 로깅

        Args:
            message: 로그 메시지
            exception: 예외 객체
        """
        if exception:
            full_message = f"{message}: {exception}"
        else:
            full_message = message
        self.logger.warning(full_message)

    def handle_exception(
        self,
        message: str,
        exception: Exception,
        reraise: bool = True,
        default_return: Any = None,
        log_level: str = "error",
    ) -> Any:
        """
        통합 예외 처리 메서드

        Args:
            message: 로그 메시지
            exception: 처리할 예외
            reraise: 예외를 다시 발생시킬지 여부
            default_return: reraise=False일 때 반환할 기본값
            log_level: 로그 레벨 ("error", "warning", "info")

        Returns:
            reraise=False일 때 default_return 값

        Raises:
            exception: reraise=True일 때 원본 예외
        """
        full_message = f"{message}: {exception}"

        if log_level == "error":
            self.logger.error(full_message, exc_info=True)
        elif log_level == "warning":
            self.logger.warning(full_message, exc_info=True)
        elif log_level == "info":
            self.logger.info(full_message, exc_info=True)

        if reraise:
            raise exception
        else:
            return default_return


def exception_handler(
    message: str = None,
    reraise: bool = True,
    default_return: Any = None,
    log_level: str = "error",
    exceptions: Union[Type[Exception], tuple] = Exception,
):
    """
    메서드 데코레이터: 자동 예외 처리

    Args:
        message: 로그 메시지 (None이면 함수명 사용)
        reraise: 예외를 다시 발생시킬지 여부
        default_return: reraise=False일 때 반환할 기본값
        log_level: 로그 레벨
        exceptions: 처리할 예외 타입(들)

    Example:
        @exception_handler(message="주식 정보 조회 실패", reraise=False, default_return={})
        def get_stock_info(self, code):
            return self.api.get_info(code)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except exceptions as e:
                # BaseExceptionHandler를 상속받지 않은 경우 기본 로깅
                if not hasattr(self, "handle_exception"):
                    logger = logging.getLogger(self.__class__.__name__)
                    error_message = message or f"{func.__name__} 실행 실패"
                    full_message = f"{error_message}: {e}"

                    if log_level == "error":
                        logger.error(full_message, exc_info=True)
                    elif log_level == "warning":
                        logger.warning(full_message, exc_info=True)

                    if reraise:
                        raise
                    return default_return
                else:
                    # BaseExceptionHandler 메서드 사용
                    error_message = message or f"{func.__name__} 실행 실패"
                    return self.handle_exception(
                        message=error_message,
                        exception=e,
                        reraise=reraise,
                        default_return=default_return,
                        log_level=log_level,
                    )

        return wrapper

    return decorator


def safe_execute(
    func: Callable,
    *args,
    logger: Optional[logging.Logger] = None,
    error_message: str = "작업 실행 실패",
    reraise: bool = True,
    default_return: Any = None,
    **kwargs,
) -> Any:
    """
    안전한 함수 실행 (독립 함수용)

    Args:
        func: 실행할 함수
        *args: 함수 인자
        logger: 사용할 로거
        error_message: 에러 메시지
        reraise: 예외를 다시 발생시킬지 여부
        default_return: reraise=False일 때 반환할 기본값
        **kwargs: 함수 키워드 인자

    Returns:
        함수 실행 결과 또는 default_return

    Example:
        result = safe_execute(
            api_call,
            param1, param2,
            logger=my_logger,
            error_message="API 호출 실패",
            reraise=False,
            default_return={}
        )
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        return func(*args, **kwargs)
    except Exception as e:
        full_message = f"{error_message}: {e}"
        logger.error(full_message, exc_info=True)

        if reraise:
            raise
        return default_return


class SafeDict(dict):
    """
    안전한 딕셔너리 - 키 에러 시 로깅하고 기본값 반환
    """

    def __init__(self, *args, logger_name: str = "SafeDict", **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(logger_name)

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError as e:
            self.logger.warning(f"키 '{key}'를 찾을 수 없습니다", exc_info=True)
            raise

    def safe_get(self, key, default=None, log_missing: bool = True):
        """
        안전한 get - 키가 없어도 로깅만 하고 기본값 반환
        """
        try:
            return self[key]
        except KeyError:
            if log_missing:
                self.logger.debug(f"키 '{key}' 없음, 기본값 '{default}' 반환")
            return default


__all__ = ["BaseExceptionHandler", "exception_handler", "safe_execute", "SafeDict"]
