"""
TTLCache 및 APICache 포괄적 단위 테스트

INT-376: core/cache.py 커버리지 개선
생성일: 2026-01-04
"""

import threading
import time

import pytest

from pykis.core.cache import APICache, TTLCache


class TestTTLCacheBasic:
    """TTLCache 기본 기능 테스트"""

    def test_init_default_values(self):
        """기본 초기화 값 확인"""
        cache = TTLCache()
        assert cache.default_ttl == 5
        assert cache.max_size == 1000
        assert cache.hits == 0
        assert cache.misses == 0
        assert len(cache.cache) == 0

    def test_init_custom_values(self):
        """커스텀 초기화 값 확인"""
        cache = TTLCache(default_ttl=10, max_size=500)
        assert cache.default_ttl == 10
        assert cache.max_size == 500

    def test_set_and_get_basic(self):
        """기본 set/get 동작"""
        cache = TTLCache(default_ttl=60)
        cache.set("key1", "value1")
        result = cache.get("key1")
        assert result == "value1"
        assert cache.hits == 1

    def test_get_missing_key(self):
        """존재하지 않는 키 조회"""
        cache = TTLCache()
        result = cache.get("nonexistent")
        assert result is None
        assert cache.misses == 1

    def test_get_expired_key_removes_entry(self):
        """만료된 키 조회 시 항목 제거 (L53)"""
        cache = TTLCache(default_ttl=1)
        cache.set("expire_test", "value", ttl=0.1)

        # 즉시 조회 - 성공
        assert cache.get("expire_test") == "value"

        # 만료 후 조회 - None 반환 및 항목 삭제
        time.sleep(0.15)
        result = cache.get("expire_test")
        assert result is None
        assert "expire_test" not in cache.cache

    def test_set_with_custom_ttl(self):
        """커스텀 TTL로 설정"""
        cache = TTLCache(default_ttl=60)
        cache.set("short_ttl", "value", ttl=1)

        # 즉시 조회
        assert cache.get("short_ttl") == "value"

        # 만료 후 조회
        time.sleep(1.1)
        assert cache.get("short_ttl") is None


class TestTTLCacheSizeManagement:
    """TTLCache 크기 관리 테스트 (L62-70)"""

    def test_cleanup_removes_expired_entries(self):
        """_cleanup() 만료 항목 정리 (L78-83)"""
        cache = TTLCache(default_ttl=60, max_size=10)

        # 만료되는 항목 추가
        cache.set("expired1", "val", ttl=0.1)
        cache.set("expired2", "val", ttl=0.1)
        cache.set("valid", "val", ttl=60)

        time.sleep(0.15)

        # cleanup 실행 (set에서 max_size 도달 시 호출됨)
        with cache.lock:
            cache._cleanup()

        # 만료된 항목은 제거되고 유효한 항목만 남음
        assert "expired1" not in cache.cache
        assert "expired2" not in cache.cache
        assert "valid" in cache.cache

    def test_max_size_triggers_cleanup(self):
        """max_size 도달 시 cleanup 호출 (L62-64)"""
        cache = TTLCache(default_ttl=0.1, max_size=3)

        # 3개 항목으로 max_size 도달
        cache.set("key1", "val1")
        cache.set("key2", "val2")
        cache.set("key3", "val3")

        # 만료 대기
        time.sleep(0.15)

        # 새 항목 추가 시 cleanup 발동
        cache.set("key4", "val4")

        # 만료된 항목은 정리됨
        assert len(cache.cache) <= cache.max_size

    def test_fifo_removal_when_full(self):
        """캐시가 가득 찼을 때 FIFO 방식 제거 (L67-70)"""
        cache = TTLCache(default_ttl=60, max_size=3)

        cache.set("first", "val1")
        cache.set("second", "val2")
        cache.set("third", "val3")

        # max_size 도달 상태에서 새 항목 추가
        cache.set("fourth", "val4")

        # 첫 번째 항목(FIFO)이 제거됨
        assert "first" not in cache.cache
        assert "fourth" in cache.cache
        assert len(cache.cache) == 3


class TestTTLCacheClear:
    """TTLCache clear 메서드 테스트 (L85-90)"""

    def test_clear_removes_all_entries(self):
        """clear() 모든 항목 제거"""
        cache = TTLCache()
        cache.set("key1", "val1")
        cache.set("key2", "val2")
        cache.hits = 5
        cache.misses = 3

        cache.clear()

        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0


class TestTTLCacheStats:
    """TTLCache 통계 테스트 (L92-105)"""

    def test_get_stats_empty_cache(self):
        """빈 캐시 통계"""
        cache = TTLCache(default_ttl=10, max_size=500)
        stats = cache.get_stats()

        assert stats["size"] == 0
        assert stats["max_size"] == 500
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == "0.0%"
        assert stats["default_ttl"] == 10

    def test_get_stats_with_data(self):
        """데이터가 있는 캐시 통계"""
        cache = TTLCache()
        cache.set("key1", "val1")
        cache.set("key2", "val2")

        # 2 hits + 1 miss
        cache.get("key1")
        cache.get("key2")
        cache.get("nonexistent")

        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == "66.7%"


class TestTTLCacheDecorator:
    """TTLCache cached() 데코레이터 테스트 (L107-141)"""

    def test_cached_decorator_basic(self):
        """cached() 데코레이터 기본 동작"""
        cache = TTLCache(default_ttl=60)
        call_count = 0

        @cache.cached()
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # 첫 번째 호출 - 실제 함수 실행
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # 두 번째 호출 - 캐시에서 반환
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # 함수 재실행 안됨

        # 다른 인자 - 실제 함수 실행
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2

    def test_cached_decorator_with_custom_ttl(self):
        """cached() 데코레이터 커스텀 TTL"""
        cache = TTLCache()
        call_count = 0

        @cache.cached(ttl=0.1)
        def short_lived(x):
            nonlocal call_count
            call_count += 1
            return x

        # 첫 호출
        short_lived(1)
        assert call_count == 1

        # 캐시 히트
        short_lived(1)
        assert call_count == 1

        # TTL 만료 후
        time.sleep(0.15)
        short_lived(1)
        assert call_count == 2

    def test_cached_decorator_none_not_cached(self):
        """cached() 데코레이터 - None 반환은 캐시 안됨 (L130)"""
        cache = TTLCache()
        call_count = 0

        @cache.cached()
        def returns_none(x):
            nonlocal call_count
            call_count += 1
            return None if x < 0 else x

        # None 반환 - 캐시 안됨
        result = returns_none(-1)
        assert result is None
        assert call_count == 1

        # 다시 호출 - 캐시 미스로 재실행
        returns_none(-1)
        assert call_count == 2

    def test_cached_decorator_exposes_cache_methods(self):
        """cached() 데코레이터 - cache_stats, cache_clear 메서드 노출 (L136-137)"""
        cache = TTLCache()

        @cache.cached()
        def my_func(x):
            return x

        my_func(1)
        my_func(1)

        # cache_stats 접근
        stats = my_func.cache_stats()
        assert "hits" in stats

        # cache_clear 접근
        my_func.cache_clear()
        assert cache.hits == 0


class TestAPICacheDecorator:
    """APICache cache_api_call() 데코레이터 테스트 (L203-238)"""

    def test_cache_api_call_basic(self):
        """cache_api_call() 기본 동작"""
        cache = APICache()
        call_count = 0

        endpoint = "/test/endpoint"
        tr_id = "TR001"
        params = {"code": "005930"}

        @cache.cache_api_call(endpoint, tr_id, params)
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            return {"rt_cd": "0", "data": "success"}

        # 첫 호출
        result1 = mock_api_call()
        assert result1["rt_cd"] == "0"
        assert call_count == 1

        # 캐시 히트
        result2 = mock_api_call()
        assert result2["_cached"] is True
        assert "_cache_hit_time" in result2
        assert call_count == 1

    def test_cache_api_call_uses_endpoint_ttl(self):
        """cache_api_call() 엔드포인트별 TTL 적용"""
        cache = APICache()

        # 짧은 TTL 엔드포인트
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
        ttl = cache.get_ttl_for_endpoint(endpoint)
        assert ttl == 30  # inquire-price는 30초

        # 긴 TTL 엔드포인트
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-holiday"
        ttl = cache.get_ttl_for_endpoint(endpoint)
        assert ttl == 86400  # holiday는 1일

    def test_cache_api_call_only_caches_success(self):
        """cache_api_call() 성공 응답만 캐시 (L231)"""
        cache = APICache()
        call_count = 0

        @cache.cache_api_call("/test", "TR", {})
        def failing_api():
            nonlocal call_count
            call_count += 1
            return {"rt_cd": "1", "msg": "error"}  # 실패 응답

        # 첫 호출
        failing_api()
        assert call_count == 1

        # 실패 응답은 캐시 안됨 - 재호출
        failing_api()
        assert call_count == 2

    def test_cache_api_call_handles_non_dict_response(self):
        """cache_api_call() dict가 아닌 응답 처리"""
        cache = APICache()

        @cache.cache_api_call("/test", "TR", {})
        def returns_none():
            return None

        result = returns_none()
        assert result is None


class TestTTLCacheThreadSafety:
    """TTLCache 스레드 안전성 테스트"""

    def test_concurrent_set_get(self):
        """동시 set/get 동작"""
        cache = TTLCache(default_ttl=60, max_size=1000)
        errors = []

        def writer(thread_id):
            try:
                for i in range(100):
                    cache.set(f"thread_{thread_id}_{i}", f"value_{i}")
            except Exception as e:
                errors.append(e)

        def reader(thread_id):
            try:
                for i in range(100):
                    cache.get(f"thread_{thread_id}_{i}")
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(5):
            threads.append(threading.Thread(target=writer, args=(i,)))
            threads.append(threading.Thread(target=reader, args=(i,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestMakeKey:
    """_make_key() 해시 생성 테스트"""

    def test_make_key_consistency(self):
        """동일 인자에 대해 동일 키 생성"""
        cache = TTLCache()
        key1 = cache._make_key("arg1", "arg2", kwarg1="val1")
        key2 = cache._make_key("arg1", "arg2", kwarg1="val1")
        assert key1 == key2

    def test_make_key_different_args(self):
        """다른 인자에 대해 다른 키 생성"""
        cache = TTLCache()
        key1 = cache._make_key("arg1")
        key2 = cache._make_key("arg2")
        assert key1 != key2

    def test_make_key_kwargs_order_independent(self):
        """kwargs 순서와 무관하게 동일 키"""
        cache = TTLCache()
        key1 = cache._make_key(a=1, b=2)
        key2 = cache._make_key(b=2, a=1)
        assert key1 == key2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
