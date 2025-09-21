"""
 TTL   
   TTL   
"""

import time
from pykis.core.cache import APICache


def test_cache_ttl_configuration():
    """API  TTL"""
    cache = APICache()

    #    (10 )
    ttl = cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-price")
    assert ttl == 10, f"Expected 10, got {ttl}"

    ttl = cache.get_ttl_for_endpoint(
        "/uapi/domestic-stock/v1/quotations/inquire-asking-price"
    )
    assert ttl == 10, f"Expected 10, got {ttl}"

    ttl = cache.get_ttl_for_endpoint(
        "/uapi/domestic-stock/v1/quotations/inquire-time-itemconclusion"
    )
    assert ttl == 5, f"Expected 5, got {ttl}"

    # /   (30)
    assert (
        cache.get_ttl_for_endpoint(
            "/uapi/domestic-stock/v1/quotations/inquire-investor"
        )
        == 30
    )
    assert (
        cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-member")
        == 30
    )
    assert (
        cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/quotations/inquire-program")
        == 30
    )

    #    (60)
    assert (
        cache.get_ttl_for_endpoint(
            "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        )
        == 60
    )
    assert cache.get_ttl_for_endpoint("/uapi/volume-rank") == 60

    # /  (60-120)
    assert (
        cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/inquire-balance")
        == 60
    )
    assert (
        cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/inquire-psbl-order")
        == 30
    )
    assert (
        cache.get_ttl_for_endpoint("/uapi/domestic-stock/v1/trading/inquire-account")
        == 120
    )

    #   (300 )
    assert (
        cache.get_ttl_for_endpoint(
            "/uapi/domestic-stock/v1/quotations/inquire-stock-info"
        )
        == 300
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


def test_cache_performance_with_different_ttls():
    """TTL"""
    cache = APICache()

    #  (10 TTL)
    price_endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
    cache_key_price = cache._make_key({"endpoint": price_endpoint, "code": "005930"})
    cache.set(
        cache_key_price,
        {"price": 70000},
        ttl=cache.get_ttl_for_endpoint(price_endpoint),
    )

    #   (300 TTL)
    info_endpoint = "/uapi/domestic-stock/v1/quotations/inquire-stock-info"
    cache_key_info = cache._make_key({"endpoint": info_endpoint, "code": "005930"})
    cache.set(
        cache_key_info, {"name": ""}, ttl=cache.get_ttl_for_endpoint(info_endpoint)
    )

    # 10  -  ,
    time.sleep(11)
    assert cache.get(cache_key_price) is None  #
    assert cache.get(cache_key_info) is not None  #

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
    # test_cache_performance_with_different_ttls()  #
    display_ttl_summary()
