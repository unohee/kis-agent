"""
캐시 TTL 설정 검증 테스트
시간 민감성에 따른 TTL 값이 적절한지 확인
"""

import time
from pykis.core.cache import APICache


def test_cache_ttl_configuration():
    """각 API 엔드포인트의 TTL 설정 확인"""
    cache = APICache()
    
    # 실시간 시세 확인 (10초 이하)
    ttl = cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-price")
    assert ttl == 10, f"Expected 10, got {ttl}"
    
    ttl = cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-asking-price")
    assert ttl == 10, f"Expected 10, got {ttl}"
    
    ttl = cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-time-itemconclusion")
    assert ttl == 5, f"Expected 5, got {ttl}"
    
    # 분/시간 단위 데이터 (30초)
    assert cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-investor") == 30
    assert cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-member") == 30
    assert cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-program") == 30
    
    # 일 단위 데이터 (60초)
    assert cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice") == 60
    assert cache.get_ttl_for_endpoint("/uapi/volume-rank") == 60
    
    # 계좌/잔고 정보 (60-120초)
    assert cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/inquire-balance") == 60
    assert cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/inquire-psbl-order") == 30
    assert cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/inquire-account") == 120
    
    # 정적 정보 (300초 이상)
    assert cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-stock-info") == 300
    assert cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-holiday") == 86400
    
    # 주문 관련 (캐시 안함)
    assert cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/order-cash") == 0
    assert cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/order-credit") == 0
    
    print("✅ 모든 TTL 설정이 시간 민감성에 맞게 구성됨")


def test_cache_expiry_behavior():
    """캐시 만료 동작 테스트"""
    cache = APICache(default_ttl=1)  # 1초 TTL
    
    # 데이터 저장
    cache.set("test_key", {"data": "test_value"}, ttl=1)
    
    # 즉시 조회 - 캐시 히트
    assert cache.get("test_key") is not None
    assert cache.hits == 1
    
    # 1.1초 후 조회 - 캐시 미스 (만료됨)
    time.sleep(1.1)
    assert cache.get("test_key") is None
    assert cache.misses == 1
    
    print("✅ 캐시 만료 동작 정상")


def test_cache_performance_with_different_ttls():
    """다양한 TTL에서의 캐시 성능 테스트"""
    cache = APICache()
    
    # 현재가 (10초 TTL)
    price_endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
    cache_key_price = cache._make_key({"endpoint": price_endpoint, "code": "005930"})
    cache.set(cache_key_price, {"price": 70000}, ttl=cache.get_ttl_for_endpoint(price_endpoint))
    
    # 종목 정보 (300초 TTL)
    info_endpoint = "/uapi/domestic-stock/v1/quotations/inquire-stock-info"
    cache_key_info = cache._make_key({"endpoint": info_endpoint, "code": "005930"})
    cache.set(cache_key_info, {"name": "삼성전자"}, ttl=cache.get_ttl_for_endpoint(info_endpoint))
    
    # 10초 후 - 현재가는 만료, 종목정보는 유지
    time.sleep(11)
    assert cache.get(cache_key_price) is None  # 만료됨
    assert cache.get(cache_key_info) is not None  # 아직 유효
    
    print("✅ TTL별 차등 만료 동작 정상")


def display_ttl_summary():
    """TTL 설정 요약 표시"""
    cache = APICache()
    
    print("\n📊 PyKIS 캐시 TTL 설정 요약")
    print("=" * 60)
    
    categories = [
        ("🔴 실시간 (5-10초)", ["price", "asking-price", "ccnl"]),
        ("🟡 준실시간 (30초)", ["investor", "member", "program", "minutechart"]),
        ("🟢 일단위 (60초)", ["daily", "volume-rank", "balance", "profit"]),
        ("🔵 정적 (120초+)", ["account", "stock-info", "holiday", "condition"]),
        ("⚫ 캐시안함 (0초)", ["order", "modify", "cancel"])
    ]
    
    for category_name, keywords in categories:
        print(f"\n{category_name}")
        for api_name, ttl in cache.DEFAULT_TTLS.items():
            for keyword in keywords:
                if keyword in api_name:
                    print(f"  - {api_name}: {ttl}초")
                    break
    
    print("\n" + "=" * 60)
    print(f"기본 TTL: {cache.default_ttl}초 (설정되지 않은 엔드포인트)")
    print(f"최대 캐시 크기: {cache.max_size}개 항목")


if __name__ == "__main__":
    test_cache_ttl_configuration()
    test_cache_expiry_behavior()
    # test_cache_performance_with_different_ttls()  # 시간이 걸리므로 주석 처리
    display_ttl_summary()