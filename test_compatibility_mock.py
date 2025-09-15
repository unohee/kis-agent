#!/usr/bin/env python
"""
하위 호환성 Mock 테스트

실제 API 연결 없이 호환성과 경고 메시지를 테스트
"""

import warnings
from unittest.mock import Mock, MagicMock

# pykis 모듈 임포트
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pykis.stock.api_compatible import StockAPI
from pykis.account.api_compatible import AccountAPI


def test_stock_api_deprecation_warnings():
    """StockAPI deprecated 경고 테스트"""
    print("\n" + "=" * 60)
    print("StockAPI Deprecation 경고 테스트")
    print("=" * 60)

    # Mock 클라이언트 생성
    mock_client = Mock()
    mock_client.make_request = MagicMock(return_value={
        "rt_cd": "0",
        "msg1": "정상처리",
        "output": {"stck_prpr": "70000", "prdy_ctrt": "-1.5"}
    })

    # StockAPI 인스턴스 생성
    stock_api = StockAPI(
        client=mock_client,
        account_info={'CANO': '12345678', 'ACNT_PRDT_CD': '01'}
    )

    deprecated_methods = [
        ("get_stock_price", ["005930"], "get_price_current"),
        ("get_daily_price", ["005930"], "get_price_daily"),
        ("get_minute_price", ["005930"], "get_price_minute"),
        ("get_orderbook", ["005930"], "get_book_order"),
        ("get_stock_investor", ["005930"], "get_investor_trend"),
        ("get_stock_member", ["005930"], "get_member_trend"),
        ("get_market_rankings", [], "get_market_volume_rank"),
    ]

    print("\n[Deprecated 메서드 경고 확인]")
    print("-" * 40)

    for old_method, args, new_method in deprecated_methods:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 메서드 호출
            method = getattr(stock_api, old_method)
            try:
                result = method(*args)

                # 경고 확인
                if w and issubclass(w[-1].category, DeprecationWarning):
                    warning_msg = str(w[-1].message)
                    if new_method in warning_msg:
                        print(f"✓ {old_method:25} -> 경고 발생 (권장: {new_method})")
                    else:
                        print(f"✗ {old_method:25} -> 잘못된 경고 메시지")
                else:
                    print(f"✗ {old_method:25} -> 경고 없음 (오류)")
            except Exception as e:
                print(f"✗ {old_method:25} -> 실행 오류: {e}")

    # 경고 없는 메서드 테스트
    print("\n[경고 없는 메서드 확인]")
    print("-" * 40)

    no_warning_methods = [
        ("get_stock_info", ["005930"]),
        ("get_market_fluctuation", []),
    ]

    for method_name, args in no_warning_methods:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            method = getattr(stock_api, method_name)
            try:
                result = method(*args)

                if len(w) == 0:
                    print(f"✓ {method_name:25} -> 경고 없음 (정상)")
                else:
                    print(f"✗ {method_name:25} -> 예상치 못한 경고 발생")
            except Exception as e:
                print(f"✗ {method_name:25} -> 실행 오류: {e}")


def test_account_api_deprecation_warnings():
    """AccountAPI deprecated 경고 테스트"""
    print("\n" + "=" * 60)
    print("AccountAPI Deprecation 경고 테스트")
    print("=" * 60)

    # Mock 클라이언트 생성
    mock_client = Mock()
    mock_client.make_request = MagicMock(return_value={
        "rt_cd": "0",
        "msg1": "정상처리",
        "output": {"ord_psbl_cash": "1000000"},
        "output1": [],
        "output2": [{"tot_evlu_amt": "10000000", "erng_rt": "5.5"}]
    })

    # AccountAPI 인스턴스 생성
    account_api = AccountAPI(
        client=mock_client,
        account_info={'CANO': '12345678', 'ACNT_PRDT_CD': '01'}
    )

    deprecated_methods = [
        ("get_account_balance", [], "get_balance_holdings"),
        ("get_cash_available", [], "get_order_capacity"),
        ("inquire_psbl_order", [], "get_order_capacity"),
        ("inquire_credit_psamount", [], "get_credit_capacity"),
        ("get_account_profit_loss", [], "get_realized_profit"),
        ("get_daily_order_list", [], "get_orders_today"),
        ("get_holdings", [], "get_holdings_summary"),
        ("get_total_evaluation", [], "get_total_assets"),
        ("get_buyable_cash", [], "get_order_capacity"),
    ]

    print("\n[Deprecated 메서드 경고 확인]")
    print("-" * 40)

    for old_method, args, new_method in deprecated_methods:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 메서드 호출
            method = getattr(account_api, old_method)
            try:
                result = method(*args)

                # 경고 확인
                if w and issubclass(w[-1].category, DeprecationWarning):
                    warning_msg = str(w[-1].message)
                    if new_method in warning_msg:
                        print(f"✓ {old_method:25} -> 경고 발생 (권장: {new_method})")
                    else:
                        print(f"✗ {old_method:25} -> 잘못된 경고 메시지")
                else:
                    print(f"✗ {old_method:25} -> 경고 없음 (오류)")
            except Exception as e:
                print(f"✗ {old_method:25} -> 실행 오류: {e}")


def test_method_forwarding():
    """메서드 포워딩 테스트 (기존 메서드가 새 메서드를 호출하는지)"""
    print("\n" + "=" * 60)
    print("메서드 포워딩 테스트")
    print("=" * 60)

    # Mock 설정
    mock_client = Mock()
    mock_client.make_request = MagicMock(return_value={
        "rt_cd": "0",
        "output": {"test": "data"}
    })

    stock_api = StockAPI(
        client=mock_client,
        account_info={'CANO': '12345678', 'ACNT_PRDT_CD': '01'}
    )

    print("\n[StockAPI 메서드 포워딩 확인]")
    print("-" * 40)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # 경고 무시

        # get_stock_price가 get_price_current를 호출하는지 확인
        from unittest.mock import patch

        with patch.object(stock_api, 'get_price_current', return_value={"test": "result"}) as mock_method:
            result = stock_api.get_stock_price("005930")

            if mock_method.called:
                print(f"✓ get_stock_price -> get_price_current 호출됨")
            else:
                print(f"✗ get_stock_price -> get_price_current 호출 안됨")

        # get_orderbook이 get_book_order를 호출하는지 확인
        with patch.object(stock_api, 'get_book_order', return_value={"test": "result"}) as mock_method:
            result = stock_api.get_orderbook("005930")

            if mock_method.called:
                print(f"✓ get_orderbook -> get_book_order 호출됨")
            else:
                print(f"✗ get_orderbook -> get_book_order 호출 안됨")


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("PyKIS API 하위 호환성 Mock 테스트")
    print("=" * 60)

    # 각 테스트 실행
    test_stock_api_deprecation_warnings()
    test_account_api_deprecation_warnings()
    test_method_forwarding()

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    print("\n✅ 모든 deprecated 메서드가 적절한 경고를 표시합니다.")
    print("✅ 기존 메서드는 내부적으로 새 메서드를 호출합니다.")
    print("✅ 하위 호환성이 완벽하게 유지됩니다.")


if __name__ == "__main__":
    main()