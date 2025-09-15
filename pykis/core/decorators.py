"""
API 엔드포인트 데코레이터

보일러플레이트 코드를 줄이기 위한 데코레이터 모음
"""

from functools import wraps
from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


def api_endpoint(endpoint_key: str, tr_id: str, method: str = 'GET'):
    """
    API 엔드포인트 호출을 위한 데코레이터

    Args:
        endpoint_key: API_ENDPOINTS 딕셔너리의 키
        tr_id: 거래 ID
        method: HTTP 메서드 (GET/POST)

    Example:
        @api_endpoint('INQUIRE_PRICE', 'FHKST01010100')
        def get_price_current(self, code: str):
            return {"FID_INPUT_ISCD": code}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 함수 실행하여 파라미터 얻기
            params = func(self, *args, **kwargs)

            # None 반환 시 빈 딕셔너리로 처리
            if params is None:
                params = {}

            # 기본 파라미터 추가 (시장 코드 등)
            if hasattr(self, '_add_default_params'):
                params = self._add_default_params(params)

            # API 호출
            from ..core.client import API_ENDPOINTS
            endpoint = API_ENDPOINTS.get(endpoint_key)
            if not endpoint:
                raise ValueError(f"Unknown endpoint: {endpoint_key}")

            # 캐시 체크 (GET 요청만)
            if method == 'GET' and hasattr(self, 'cache') and self.cache:
                cache_key = f"{endpoint_key}:{tr_id}:{str(params)}"
                cached = self.cache.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached

            # API 요청
            if hasattr(self, '_make_request_dict'):
                result = self._make_request_dict(
                    endpoint=endpoint,
                    tr_id=tr_id,
                    params=params
                )
            else:
                # BaseAPI가 아닌 경우 직접 호출
                result = self.client.make_request(
                    endpoint=endpoint,
                    tr_id=tr_id,
                    params=params,
                    method=method
                )

            # 캐시 저장 (성공 시에만)
            if method == 'GET' and hasattr(self, 'cache') and self.cache:
                if result and result.get('rt_cd') == '0':
                    self.cache.set(cache_key, result)

            return result

        # 메타데이터 추가
        wrapper._api_endpoint = endpoint_key
        wrapper._tr_id = tr_id
        wrapper._method = method

        return wrapper
    return decorator


def with_retry(max_retries: int = 3, delay: float = 1.0):
    """
    재시도 로직을 추가하는 데코레이터

    Args:
        max_retries: 최대 재시도 횟수
        delay: 재시도 간격 (초)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time

            last_error = None
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    if result is not None:
                        return result
                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay)

            if last_error:
                raise last_error
            return None

        return wrapper
    return decorator


def validate_params(**validators):
    """
    파라미터 검증 데코레이터

    Args:
        **validators: 파라미터명과 검증 함수 매핑

    Example:
        @validate_params(
            code=lambda x: len(x) == 6,
            price=lambda x: x.isdigit()
        )
        def order_stock(self, code, price):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 함수 시그니처에서 파라미터 이름 추출
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(self, *args, **kwargs)
            bound.apply_defaults()

            # 검증 수행
            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not validator(value):
                        raise ValueError(f"Invalid parameter {param_name}: {value}")

            return func(self, *args, **kwargs)

        return wrapper
    return decorator


def deprecated(message: str = None, alternative: str = None):
    """
    Deprecated 메서드 표시 데코레이터

    Args:
        message: 사용자 정의 메시지
        alternative: 대체 메서드명
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import warnings

            msg = f"{func.__name__} is deprecated"
            if message:
                msg += f": {message}"
            if alternative:
                msg += f". Use {alternative} instead"

            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper
    return decorator


def cache_result(ttl: int = 60):
    """
    결과 캐싱 데코레이터

    Args:
        ttl: Time To Live (초)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # 캐시 확인
            if hasattr(self, 'cache') and self.cache:
                cached = self.cache.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached

            # 함수 실행
            result = func(self, *args, **kwargs)

            # 캐시 저장
            if hasattr(self, 'cache') and self.cache and result is not None:
                self.cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator