"""
캐싱 로직 통합 테스트
실제 API 호출과 캐싱 동작을 검증합니다.
"""

import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from pykis.core.cache import APICache, TTLCache
from pykis.core.base_api import BaseAPI


class TestCacheIntegration:
    """캐시 통합 테스트"""

    def test_ttl_cache_basic_operations(self):
        """TTLCache 기본 동작 테스트"""
        cache = TTLCache(default_ttl=2, max_size=10)

        # 저장 및 조회
        cache.set("key1", {"data": "value1"})
        result = cache.get("key1")
        assert result == {"data": "value1"}
        assert cache.hits == 1

        # 존재하지 않는 키 조회
        result = cache.get("nonexistent")
        assert result is None
        assert cache.misses == 1

        # TTL 만료 테스트
        cache.set("key2", {"data": "value2"}, ttl=1)
        assert cache.get("key2") is not None
        time.sleep(1.1)
        assert cache.get("key2") is None

    def test_api_cache_ttl_by_endpoint(self):
        """엔드포인트별 TTL 설정 테스트"""
        cache = APICache()

        # 시세 데이터는 10초 TTL
        price_ttl = cache.get_ttl_for_endpoint(
            "/uapi/domestic-stock/v1/quotations/inquire-price"
        )
        assert price_ttl == 10, f"시세 데이터 TTL은 10초여야 합니다. 실제: {price_ttl}"

        # 체결 데이터는 5초 TTL
        ccnl_ttl = cache.get_ttl_for_endpoint(
            "/uapi/domestic-stock/v1/quotations/inquire-ccnl"
        )
        assert ccnl_ttl == 5, f"체결 데이터 TTL은 5초여야 합니다. 실제: {ccnl_ttl}"

        # 일봉 데이터는 60초 TTL
        daily_ttl = cache.get_ttl_for_endpoint(
            "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        )
        assert daily_ttl == 60, f"일봉 데이터 TTL은 60초여야 합니다. 실제: {daily_ttl}"

        # 종목 정보는 300초 TTL
        info_ttl = cache.get_ttl_for_endpoint(
            "/uapi/domestic-stock/v1/quotations/inquire-stock-info"
        )
        assert info_ttl == 300, f"종목 정보 TTL은 300초여야 합니다. 실제: {info_ttl}"

        # 주문은 캐시하지 않음 (0초)
        order_ttl = cache.get_ttl_for_endpoint(
            "/uapi/domestic-stock/v1/trading/order-cash"
        )
        assert order_ttl == 0, f"주문은 캐시하지 않아야 합니다. TTL: {order_ttl}"

    def test_cache_hit_miss_statistics(self):
        """캐시 히트/미스 통계 테스트"""
        cache = TTLCache(default_ttl=10)

        # 초기 상태
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

        # 캐시 미스
        cache.get("key1")
        stats = cache.get_stats()
        assert stats["misses"] == 1

        # 캐시 히트
        cache.set("key1", "value1")
        cache.get("key1")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["hit_rate"] == "50.0%"

    def test_cache_size_limit(self):
        """캐시 크기 제한 테스트"""
        cache = TTLCache(default_ttl=10, max_size=3)

        # 최대 크기까지 저장
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        assert len(cache.cache) == 3

        # 크기 초과 시 오래된 항목 제거
        cache.set("key4", "value4")
        assert len(cache.cache) == 3
        # key1이 제거되고 key2, key3, key4가 남아있어야 함
        assert cache.get("key1") is None
        assert cache.get("key4") is not None

    def test_cache_decorator(self):
        """캐시 데코레이터 테스트"""
        cache = TTLCache(default_ttl=2)
        call_count = 0

        @cache.cached(ttl=2)
        def expensive_function(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"

        # 첫 호출 - 함수 실행
        result1 = expensive_function("test")
        assert result1 == "result_test"
        assert call_count == 1

        # 두 번째 호출 - 캐시에서 반환
        result2 = expensive_function("test")
        assert result2 == "result_test"
        assert call_count == 1  # 함수가 다시 실행되지 않음

        # 다른 파라미터 - 함수 실행
        result3 = expensive_function("other")
        assert result3 == "result_other"
        assert call_count == 2

    @patch("pykis.core.base_api.APIRequestManager")
    def test_base_api_cache_integration(self, mock_request_manager):
        """BaseAPI의 캐시 통합 테스트"""
        # Mock 클라이언트 설정
        mock_client = Mock()
        mock_client.make_request = Mock(
            return_value={"rt_cd": "0", "msg1": "성공", "output": [{"price": 70000}]}
        )

        # BaseAPI 인스턴스 생성 (캐시 활성화)
        api = BaseAPI(
            client=mock_client, enable_cache=True, cache_config={"default_ttl": 2}
        )

        # 첫 번째 요청 - API 호출 (캐시 TTL을 명시적으로 2초로 설정)
        result1 = api._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={"code": "005930"},
            cache_ttl=2,
        )
        assert result1["rt_cd"] == "0"
        assert mock_client.make_request.call_count == 1

        # 두 번째 요청 - 캐시에서 반환 (동일한 TTL 설정 유지)
        result2 = api._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={"code": "005930"},
            cache_ttl=2,
        )
        assert result2["rt_cd"] == "0"
        assert result2.get("_cached") == True  # 캐시 플래그 확인
        assert mock_client.make_request.call_count == 1  # API가 다시 호출되지 않음

        # TTL 만료 후 요청 (2초 + 여유시간)
        time.sleep(2.1)
        result3 = api._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={"code": "005930"},
            cache_ttl=2,
        )
        assert mock_client.make_request.call_count == 2  # API가 다시 호출됨

    def test_cache_with_different_ttls(self):
        """다양한 TTL 설정 동시 테스트"""
        cache = APICache()

        # 서로 다른 TTL로 데이터 저장
        cache.set("price_key", {"price": 70000}, ttl=1)  # 1초
        cache.set("info_key", {"name": "삼성전자"}, ttl=5)  # 5초

        # 즉시 조회 - 모두 캐시에 있음 (히트: 2)
        assert cache.get("price_key") is not None
        assert cache.get("info_key") is not None

        # 1.5초 후 - price는 만료, info는 유지 (히트: 1, 미스: 1)
        time.sleep(1.5)
        assert cache.get("price_key") is None
        assert cache.get("info_key") is not None

        # 통계 확인 - 총 히트: 3 (price_key 1번, info_key 2번), 미스: 1 (price_key 만료)
        stats = cache.get_stats()
        assert stats["hits"] == 3  # info_key 2번 + price_key 1번 히트
        assert stats["misses"] == 1  # price_key 1번 미스

    def test_cache_clear(self):
        """캐시 초기화 테스트"""
        cache = TTLCache()

        # 데이터 저장
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert len(cache.cache) == 2

        # 캐시 초기화
        cache.clear()
        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0

    def test_concurrent_cache_access(self):
        """동시성 테스트 (thread-safe 확인)"""
        import threading

        cache = TTLCache(default_ttl=10)
        results = []

        def access_cache(thread_id):
            for i in range(10):
                cache.set(f"key_{thread_id}_{i}", f"value_{thread_id}_{i}")
                value = cache.get(f"key_{thread_id}_{i}")
                results.append((thread_id, i, value))

        # 여러 스레드에서 동시 접근
        threads = []
        for i in range(5):
            t = threading.Thread(target=access_cache, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 모든 작업이 정상적으로 완료되었는지 확인
        assert len(results) == 50  # 5 스레드 * 10 작업

        # 각 스레드의 데이터가 올바르게 저장/조회되었는지 확인
        for thread_id, i, value in results:
            assert value == f"value_{thread_id}_{i}"


class TestCacheTTLVerification:
    """캐시 TTL 설정 검증"""

    def test_realtime_data_ttl(self):
        """실시간 데이터 TTL 검증 (10초 이하)"""
        cache = APICache()

        realtime_endpoints = [
            ("/uapi/domestic-stock/v1/quotations/inquire-price", 10),
            ("/uapi/domestic-stock/v1/quotations/inquire-asking-price", 10),
            ("/uapi/domestic-stock/v1/quotations/inquire-time-itemconclusion", 5),
            ("/uapi/domestic-stock/v1/quotations/inquire-ccnl", 5),
        ]

        for endpoint, expected_ttl in realtime_endpoints:
            ttl = cache.get_ttl_for_endpoint(endpoint)
            assert (
                ttl == expected_ttl
            ), f"{endpoint}의 TTL은 {expected_ttl}초여야 합니다. 실제: {ttl}"
            assert ttl <= 10, f"실시간 데이터 TTL은 10초 이하여야 합니다: {endpoint}"

    def test_minute_data_ttl(self):
        """분/시간 단위 데이터 TTL 검증 (30초)"""
        cache = APICache()

        minute_endpoints = [
            "/uapi/domestic-stock/v1/quotations/inquire-investor",
            "/uapi/domestic-stock/v1/quotations/inquire-member",
            "/uapi/domestic-stock/v1/quotations/inquire-program",
            "/uapi/domestic-stock/v1/quotations/inquire-minutechart",
        ]

        for endpoint in minute_endpoints:
            ttl = cache.get_ttl_for_endpoint(endpoint)
            assert ttl == 30, f"{endpoint}의 TTL은 30초여야 합니다. 실제: {ttl}"

    def test_daily_data_ttl(self):
        """일 단위 데이터 TTL 검증 (60초)"""
        cache = APICache()

        daily_endpoints = [
            "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            "/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice",
            "/uapi/domestic-stock/v1/quotations/inquire-daily-program",
            "/uapi/volume-rank",
        ]

        for endpoint in daily_endpoints:
            ttl = cache.get_ttl_for_endpoint(endpoint)
            assert ttl == 60, f"{endpoint}의 TTL은 60초여야 합니다. 실제: {ttl}"

    def test_account_data_ttl(self):
        """계좌/잔고 데이터 TTL 검증"""
        cache = APICache()

        account_endpoints = [
            ("/uapi/domestic-stock/v1/trading/inquire-balance", 60),
            ("/uapi/domestic-stock/v1/trading/inquire-psbl-order", 30),
            ("/uapi/domestic-stock/v1/trading/inquire-account", 120),
            ("/uapi/domestic-stock/v1/trading/inquire-profit", 60),
        ]

        for endpoint, expected_ttl in account_endpoints:
            ttl = cache.get_ttl_for_endpoint(endpoint)
            assert (
                ttl == expected_ttl
            ), f"{endpoint}의 TTL은 {expected_ttl}초여야 합니다. 실제: {ttl}"

    def test_static_data_ttl(self):
        """정적 데이터 TTL 검증 (300초 이상)"""
        cache = APICache()

        static_endpoints = [
            ("/uapi/domestic-stock/v1/quotations/inquire-stock-info", 300),
            ("/uapi/domestic-stock/v1/quotations/inquire-holiday", 86400),
            ("/uapi/domestic-stock/v1/quotations/inquire-product", 300),
            ("/uapi/domestic-stock/v1/quotations/inquire-condition", 300),
        ]

        for endpoint, expected_ttl in static_endpoints:
            ttl = cache.get_ttl_for_endpoint(endpoint)
            assert (
                ttl == expected_ttl
            ), f"{endpoint}의 TTL은 {expected_ttl}초여야 합니다. 실제: {ttl}"
            assert ttl >= 300, f"정적 데이터 TTL은 300초 이상이어야 합니다: {endpoint}"

    def test_order_no_cache(self):
        """주문 관련 API는 캐시하지 않음 검증"""
        cache = APICache()

        order_endpoints = [
            "/uapi/domestic-stock/v1/trading/order",
            "/uapi/domestic-stock/v1/trading/order-cash",
            "/uapi/domestic-stock/v1/trading/order-credit",
            "/uapi/domestic-stock/v1/trading/modify",
            "/uapi/domestic-stock/v1/trading/cancel",
        ]

        for endpoint in order_endpoints:
            ttl = cache.get_ttl_for_endpoint(endpoint)
            assert (
                ttl == 0
            ), f"주문 API는 캐시하지 않아야 합니다 (TTL=0): {endpoint}, 실제 TTL: {ttl}"

    def test_default_ttl_for_unknown_endpoint(self):
        """알 수 없는 엔드포인트는 기본 TTL 사용"""
        cache = APICache(default_ttl=5)

        unknown_endpoint = "/uapi/unknown/endpoint"
        ttl = cache.get_ttl_for_endpoint(unknown_endpoint)
        assert (
            ttl == 5
        ), f"알 수 없는 엔드포인트는 기본 TTL을 사용해야 합니다. 실제: {ttl}"


if __name__ == "__main__":
    # pytest 실행
    pytest.main([__file__, "-v", "--tb=short"])
