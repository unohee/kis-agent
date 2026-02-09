"""
TTL
  TTL
"""

import time

import pytest

from kis_agent.core.cache import APICache


def test_cache_ttl_configuration():
    """API  TTL"""
    cache = APICache()

    # 실시간 시세 (10-30초)
    ttl = cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-price")
    assert ttl == 30, f"Expected 30, got {ttl}"  # 현재가: 30초

    ttl = cache.get_ttl_for_endpoint(
        "/uapi/domestic-stock/v1/quotations/inquire-asking-price"
    )
    assert ttl == 30, f"Expected 30, got {ttl}"  # 호가: 30초

    ttl = cache.get_ttl_for_endpoint(
        "/uapi/domestic-stock/v1/quotations/inquire-time-itemconclusion"
    )
    assert ttl == 10, f"Expected 10, got {ttl}"  # 체결: 10초

    # 분/시간 단위 데이터 (5-10분)
    assert (
        cache.get_ttl_for_endpoint(
            "/uapi/domestic-stock/v1/quotations/inquire-investor"
        )
        == 600  # 투자자 동향: 10분
    )
    assert (
        cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-member")
        == 600  # 거래원: 10분
    )
    assert (
        cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-program")
        == 600  # 프로그램 매매: 10분
    )

    # 일봉 데이터 (30분)
    assert (
        cache.get_ttl_for_endpoint(
            "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        )
        == 1800  # 일봉: 30분
    )
    assert cache.get_ttl_for_endpoint("/uapi/volume-rank") == 600  # 거래량 순위: 10분

    # 계좌/주문 데이터 (5-30분)
    assert (
        cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/inquire-balance")
        == 600  # 잔고: 10분
    )
    assert (
        cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/inquire-psbl-order")
        == 300  # 주문가능금액: 5분
    )
    assert (
        cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/inquire-account")
        == 1800  # 계좌정보: 30분
    )

    # 정적 정보 (1시간+)
    assert (
        cache.get_ttl_for_endpoint(
            "/uapi/domestic-stock/v1/quotations/inquire-stock-info"
        )
        == 3600  # 종목 기본정보: 1시간
    )
    assert (
        cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-holiday")
        == 86400
    )

    #   ( )
    assert cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/order-cash") == 0
    assert (
        cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/order-credit") == 0
    )

    print("  TTL     ")


def test_cache_expiry_behavior():
    """ """
    cache = APICache(default_ttl=1)  # 1 TTL

    #
    cache.set("test_key", {"data": "test_value"}, ttl=1)

    #   -
    assert cache.get("test_key") is not None
    assert cache.hits == 1

    # 1.1   -   ()
    time.sleep(1.1)
    assert cache.get("test_key") is None
    assert cache.misses == 1

    print("    ")


@pytest.mark.timeout(60)
def test_cache_performance_with_different_ttls():
    """TTL"""
    cache = APICache()

    # 시세 데이터 (30초 TTL)
    price_endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
    cache_key_price = cache._make_key({"endpoint": price_endpoint, "code": "005930"})
    cache.set(
        cache_key_price,
        {"price": 70000},
        ttl=cache.get_ttl_for_endpoint(price_endpoint),
    )

    # 종목 정보 (3600초 TTL)
    info_endpoint = "/uapi/domestic-stock/v1/quotations/inquire-stock-info"
    cache_key_info = cache._make_key({"endpoint": info_endpoint, "code": "005930"})
    cache.set(
        cache_key_info,
        {"name": "삼성전자"},
        ttl=cache.get_ttl_for_endpoint(info_endpoint),
    )

    # 31초 후 - 시세는 만료, 종목정보는 유효
    time.sleep(31)
    assert cache.get(cache_key_price) is None  # 만료됨
    assert cache.get(cache_key_info) is not None  # 유효

    print(" TTL    ")


def display_ttl_summary():
    """TTL"""
    cache = APICache()

    print("\n PyKIS  TTL  ")
    print("=" * 60)

    categories = [
        ("  (5-10)", ["price", "asking-price", "ccnl"]),
        ("🟡  (30)", ["investor", "member", "program", "minutechart"]),
        ("🟢  (60)", ["daily", "volume-rank", "balance", "profit"]),
        ("  (120+)", ["account", "stock-info", "holiday", "condition"]),
        ("  (0)", ["order", "modify", "cancel"]),
    ]

    for category_name, keywords in categories:
        print(f"\n{category_name}")
        for api_name, ttl in cache.DEFAULT_TTLS.items():
            for keyword in keywords:
                if keyword in api_name:
                    print(f"  - {api_name}: {ttl}")
                    break

    print("\n" + "=" * 60)
    print(f" TTL: {cache.default_ttl} (  )")
    print(f"  : {cache.max_size} ")


if __name__ == "__main__":
    test_cache_ttl_configuration()
    test_cache_expiry_behavior()
    display_ttl_summary()
