#!/usr/bin/env python3
"""
캐싱 로직 실제 동작 검증 테스트
시세 데이터는 10초, 다른 데이터는 컨텍스트별 TTL 적용 확인
"""

import time
import json
from unittest.mock import Mock, patch
from pykis.core.cache import APICache, TTLCache
from pykis.core.base_api import BaseAPI


def test_price_data_caching():
    """시세 데이터 10초 TTL 실제 동작 테스트"""
    cache = APICache()
    endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"

    # TTL 확인
    ttl = cache.get_ttl_for_endpoint(endpoint)
    assert ttl == 10, f"시세 데이터는 10초 TTL이어야 합니다. 실제: {ttl}"

    # 데이터 저장
    test_data = {
        "rt_cd": "0",
        "output": {"stck_prpr": "70000", "prdy_vrss": "1000", "prdy_ctrt": "1.45"},
    }

    cache_key = cache._make_key(
        {
            "endpoint": endpoint,
            "tr_id": "FHKST01010100",
            "params": {"FID_INPUT_ISCD": "005930"},
        }
    )

    cache.set(cache_key, test_data, ttl=ttl)

    # 즉시 조회 - 캐시 히트
    cached = cache.get(cache_key)
    assert cached is not None, "캐시된 데이터를 찾을 수 없습니다"

    # 5초 후 - 아직 유효
    time.sleep(5)
    cached = cache.get(cache_key)
    assert cached is not None, "5초 후에도 캐시가 유효해야 합니다"

    # 11초 후 - 만료됨
    time.sleep(6)
    cached = cache.get(cache_key)
    assert cached is None, "11초 후에는 캐시가 만료되어야 합니다"


def _get_test_cases():
    """테스트 케이스 데이터 생성"""
    return [
        {
            "name": "체결내역 (실시간)",
            "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-ccnl",
            "expected_ttl": 5,
            "data": {"rt_cd": "0", "output": [{"체결가": "70000"}]},
        },
        {
            "name": "투자자 동향 (준실시간)",
            "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-investor",
            "expected_ttl": 30,
            "data": {"rt_cd": "0", "output": {"개인": "매수"}},
        },
        {
            "name": "일봉 차트 (일단위)",
            "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            "expected_ttl": 60,
            "data": {"rt_cd": "0", "output": [{"종가": "70000"}]},
        },
        {
            "name": "종목 정보 (정적)",
            "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-stock-info",
            "expected_ttl": 300,
            "data": {"rt_cd": "0", "output": {"종목명": "삼성전자"}},
        },
    ]


def _store_test_data(cache, test_cases):
    """테스트 데이터를 캐시에 저장"""
    stored_keys = []
    for tc in test_cases:
        ttl = cache.get_ttl_for_endpoint(tc["endpoint"])
        assert ttl == tc["expected_ttl"], f"TTL 불일치: {ttl} != {tc['expected_ttl']}"

        cache_key = cache._make_key(
            {"endpoint": tc["endpoint"], "params": {"test": True}}
        )
        cache.set(cache_key, tc["data"], ttl=ttl)
        stored_keys.append((tc["name"], cache_key, ttl))
    return stored_keys


def _verify_ttl_expiry(cache, stored_keys):
    """TTL 만료 검증"""
    for name, key, ttl in stored_keys:
        cached = cache.get(key)
        if ttl <= 5:
            assert cached is None, f"{name}은(는) 만료되어야 합니다"
        else:
            assert cached is not None, f"{name}은(는) 유효해야 합니다"


def test_different_context_ttls():
    """다양한 컨텍스트별 TTL 동작 테스트"""
    cache = APICache()
    test_cases = _get_test_cases()
    stored_keys = _store_test_data(cache, test_cases)

    # 6초 후 체크 - 5초 TTL만 만료
    time.sleep(6)
    _verify_ttl_expiry(cache, stored_keys)


def test_cache_performance():
    """캐시 성능 측정 테스트"""

    cache = APICache()

    # 1000개 데이터 저장 시간 측정
    start_time = time.time()
    for i in range(1000):
        cache.set(f"key_{i}", {"data": f"value_{i}"}, ttl=60)
    write_time = time.time() - start_time

    # 1000개 데이터 읽기 시간 측정
    start_time = time.time()
    hits = 0
    for i in range(1000):
        if cache.get(f"key_{i}") is not None:
            hits += 1
    read_time = time.time() - start_time

    # 성능 검증
    assert write_time < 1.0, f"쓰기 성능이 느림: {write_time:.3f}초"
    assert read_time < 1.0, f"읽기 성능이 느림: {read_time:.3f}초"
    assert hits == 1000, f"히트율 문제: {hits}/1000"


def test_order_api_no_cache():
    """주문 API는 캐시하지 않음 검증"""

    cache = APICache()

    order_endpoints = [
        "/uapi/domestic-stock/v1/trading/order-cash",
        "/uapi/domestic-stock/v1/trading/order-credit",
        "/uapi/domestic-stock/v1/trading/modify",
        "/uapi/domestic-stock/v1/trading/cancel",
    ]

    for endpoint in order_endpoints:
        ttl = cache.get_ttl_for_endpoint(endpoint)
        assert ttl == 0, f"주문 API는 캐시하지 않아야 합니다: {endpoint}"

    # 실제로 캐시가 안 되는지 테스트
    endpoint = "/uapi/domestic-stock/v1/trading/order-cash"
    cache_key = cache._make_key({"endpoint": endpoint, "params": {"order": "buy"}})

    # TTL=0으로 저장 시도
    cache.set(cache_key, {"result": "주문 완료"}, ttl=0)

    # 즉시 조회 - 캐시되지 않음
    cached = cache.get(cache_key)
    assert cached is None, "TTL=0인 데이터는 캐시되지 않아야 합니다"


def test_cache_statistics_summary():
    """캐시 통계 요약"""

    cache = APICache()

    # TTL 그룹별 분류
    ttl_groups = {
        "실시간 (5-10초)": [],
        "준실시간 (30초)": [],
        "일단위 (60초)": [],
        "계좌정보 (60-120초)": [],
        "정적 (300초+)": [],
        "캐시안함 (0초)": [],
    }

    # 각 API별 TTL 분류
    for api_name, ttl in cache.DEFAULT_TTLS.items():
        if ttl == 0:
            ttl_groups["캐시안함 (0초)"].append(f"{api_name}: {ttl}초")
        elif ttl <= 10:
            ttl_groups["실시간 (5-10초)"].append(f"{api_name}: {ttl}초")
        elif ttl <= 30:
            ttl_groups["준실시간 (30초)"].append(f"{api_name}: {ttl}초")
        elif ttl <= 60:
            ttl_groups["일단위 (60초)"].append(f"{api_name}: {ttl}초")
        elif ttl <= 120:
            ttl_groups["계좌정보 (60-120초)"].append(f"{api_name}: {ttl}초")
        else:
            ttl_groups["정적 (300초+)"].append(f"{api_name}: {ttl}초")

    # 기본 검증
    assert len(ttl_groups["실시간 (5-10초)"]) > 0, "실시간 API가 없음"
    assert len(ttl_groups["캐시안함 (0초)"]) > 0, "캐시 비활성화 API가 없음"
    assert cache.default_ttl > 0, "기본 TTL이 0이면 안됨"


def main():
    """메인 테스트 실행"""
    test_price_data_caching()
    test_different_context_ttls()
    test_cache_performance()
    test_order_api_no_cache()
    test_cache_statistics_summary()


if __name__ == "__main__":
    main()
