"""
Simple TTL Cache for PyKIS
짧은 시간 동안만 캐시하여 중복 요청을 방지합니다.
"""

import time
import hashlib
import json
from typing import Any, Optional, Dict, Callable
from functools import wraps
import threading


class TTLCache:
    """
    Thread-safe TTL (Time To Live) Cache
    
    짧은 시간 동안 API 응답을 캐시하여 중복 요청을 방지합니다.
    기본 TTL: 5초 (시세 데이터의 실시간성 유지)
    """
    
    def __init__(self, default_ttl: int = 5, max_size: int = 1000):
        """
        TTL 캐시 초기화
        
        Args:
            default_ttl: 기본 캐시 유효 시간 (초)
            max_size: 최대 캐시 항목 수
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cache: Dict[str, tuple[Any, float]] = {}  # key: (value, expiry_time)
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        
    def _make_key(self, *args, **kwargs) -> str:
        """캐시 키 생성"""
        # 모든 인자를 문자열로 변환하여 해시
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if time.time() < expiry:
                    self.hits += 1
                    return value
                else:
                    # 만료된 항목 제거
                    del self.cache[key]
            
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """캐시에 값 저장"""
        with self.lock:
            # 캐시 크기 제한 확인
            if len(self.cache) >= self.max_size:
                # 만료된 항목 먼저 제거
                self._cleanup()
                
                # 여전히 크기 초과면 가장 오래된 항목 제거
                if len(self.cache) >= self.max_size:
                    # FIFO 방식으로 제거 (간단한 구현)
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
            
            ttl = ttl if ttl is not None else self.default_ttl
            expiry_time = time.time() + ttl
            self.cache[key] = (value, expiry_time)
    
    def _cleanup(self) -> None:
        """만료된 항목 정리 (lock 내부에서 호출)"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if expiry <= current_time
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def clear(self) -> None:
        """캐시 전체 삭제"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.1f}%",
                "default_ttl": self.default_ttl
            }
    
    def cached(self, ttl: Optional[int] = None):
        """
        함수 데코레이터 - 함수 결과를 캐시
        
        사용 예:
            @cache.cached(ttl=10)
            def get_stock_price(code):
                return api.get_price(code)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 캐시 키 생성 (함수명 포함)
                cache_key = f"{func.__name__}:{self._make_key(*args, **kwargs)}"
                
                # 캐시 확인
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 함수 실행 및 캐시 저장
                result = func(*args, **kwargs)
                if result is not None:  # None이 아닌 경우만 캐시
                    self.set(cache_key, result, ttl)
                
                return result
            
            # 캐시 통계 접근 메서드 추가
            wrapper.cache_stats = self.get_stats
            wrapper.cache_clear = self.clear
            
            return wrapper
        return decorator


class APICache(TTLCache):
    """
    API 전용 캐시 - 특정 API 엔드포인트별로 다른 TTL 설정
    """
    
    # API별 기본 TTL 설정 (초) - 데이터 변동성 기준
    DEFAULT_TTLS = {
        # === 실시간 시세 (10초 이하) ===
        "inquire-price": 10,              # 현재가 - 10초 (실시간 변동)
        "inquire-asking-price": 10,       # 호가 - 10초 (실시간 변동)
        "inquire-time-itemconclusion": 5, # 체결 - 5초 (매우 빈번한 변동)
        "inquire-ccnl": 5,                # 체결내역 - 5초
        
        # === 분/시간 단위 데이터 (30초) ===
        "inquire-investor": 30,           # 투자자 동향 - 30초 (분 단위 집계)
        "inquire-member": 30,             # 거래원 - 30초 (분 단위 변동)
        "inquire-program": 30,            # 프로그램 매매 - 30초
        "inquire-minutechart": 30,        # 분봉 - 30초
        
        # === 일 단위 데이터 (60초) ===
        "inquire-daily-itemchartprice": 60,  # 일봉 - 60초 (장중 고/저/종가 변동)
        "inquire-daily-indexchartprice": 60, # 지수 일봉 - 60초
        "inquire-daily-program": 60,         # 일별 프로그램 - 60초
        "volume-rank": 60,                    # 거래량 순위 - 60초
        
        # === 계좌/잔고 정보 (60-120초) ===
        "inquire-balance": 60,            # 잔고 - 60초 (주문 시에만 변동)
        "inquire-psbl-order": 30,         # 주문가능금액 - 30초 (시세 연동)
        "inquire-account": 120,           # 계좌정보 - 120초
        "inquire-profit": 60,             # 수익률 - 60초
        
        # === 정적 정보 (300초 이상) ===
        "inquire-stock-info": 300,        # 종목 기본정보 - 300초 (5분)
        "inquire-holiday": 86400,         # 휴장일 - 86400초 (1일)
        "inquire-product": 300,           # 상품정보 - 300초
        "inquire-condition": 300,         # 조건검색 - 300초
        "search": 300,                    # 종목검색 - 300초
        
        # === 주문 관련 (캐시 안함) ===
        "order": 0,                        # 주문 - 캐시 안함
        "modify": 0,                       # 정정 - 캐시 안함
        "cancel": 0,                       # 취소 - 캐시 안함
        "order-cash": 0,                   # 현금주문 - 캐시 안함
        "order-credit": 0,                 # 신용주문 - 캐시 안함
    }
    
    def __init__(self, default_ttl: int = 5, max_size: int = 1000):
        super().__init__(default_ttl, max_size)
        
    def get_ttl_for_endpoint(self, endpoint: str) -> int:
        """엔드포인트별 적절한 TTL 반환"""
        # 엔드포인트를 소문자로 변환하여 비교
        endpoint_lower = endpoint.lower()
        
        # 엔드포인트에서 API 타입 추출
        for api_type, ttl in self.DEFAULT_TTLS.items():
            # API 타입도 소문자로 변환하여 비교
            if api_type.lower() in endpoint_lower:
                return ttl
        
        return self.default_ttl
    
    def cache_api_call(self, endpoint: str, tr_id: str, params: Dict):
        """
        API 호출 결과를 캐시하는 데코레이터
        
        엔드포인트별로 적절한 TTL을 자동 적용합니다.
        """
        ttl = self.get_ttl_for_endpoint(endpoint)
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 캐시 키 생성 (endpoint, tr_id, params 조합)
                cache_data = {
                    "endpoint": endpoint,
                    "tr_id": tr_id,
                    "params": params
                }
                cache_key = self._make_key(cache_data)
                
                # 캐시 확인
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    # 캐시 히트 시 rt_cd에 캐시 표시 추가
                    if isinstance(cached_value, dict):
                        cached_value["_cached"] = True
                        cached_value["_cache_hit_time"] = time.time()
                    return cached_value
                
                # 실제 API 호출
                result = func(*args, **kwargs)
                
                # 성공한 응답만 캐시 (rt_cd == "0")
                if result and isinstance(result, dict) and result.get("rt_cd") == "0":
                    self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator