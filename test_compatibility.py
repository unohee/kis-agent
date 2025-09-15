#!/usr/bin/env python
"""
하위 호환성 테스트 스크립트

기존 메서드명을 사용하는 코드가 정상 작동하는지 확인
deprecated 경고가 제대로 표시되는지 검증
"""

import os
import sys
import warnings
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# pykis 경로 추가
sys.path.insert(0, '/home/unohee/dev/tools/pykis-refactor')

from pykis import Agent
from pykis.stock.api_compatible import StockAPI
from pykis.account.api_compatible import AccountAPI


def test_stock_api_compatibility():
    """StockAPI 하위 호환성 테스트"""
    print("\n" + "=" * 60)
    print("StockAPI 하위 호환성 테스트")
    print("=" * 60)

    # 환경변수 설정
    app_key = os.environ.get('APP_KEY')
    app_secret = os.environ.get('APP_SECRET')
    account_no = os.environ.get('CANO') or os.environ.get('ACC_NO')
    account_code = os.environ.get('ACNT_PRDT_CD') or os.environ.get('ACC_PRD') or '01'

    if not all([app_key, app_secret, account_no]):
        print("환경변수가 설정되지 않았습니다.")
        return

    try:
        # Agent 생성
        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code
        )

        # 호환성 StockAPI 생성
        stock_api = StockAPI(
            client=agent.client,
            account_info={'CANO': account_no, 'ACNT_PRDT_CD': account_code}
        )

        print("\n[기존 메서드명 테스트]")
        print("-" * 40)

        # 경고 캡처 설정
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 1. get_stock_price (기존) -> get_price_current (신규)
            print("\n1. get_stock_price('005930') 호출")
            result = stock_api.get_stock_price("005930")

            if w:
                print(f"   ⚠️ 경고: {w[-1].message}")

            if result and result.get('rt_cd') == '0':
                output = result.get('output', {})
                print(f"   ✓ 현재가: {output.get('stck_prpr', 'N/A')}원")
            else:
                print(f"   ✗ 실패: {result.get('msg1') if result else 'No response'}")

            # 2. get_daily_price (기존) -> get_price_daily (신규)
            print("\n2. get_daily_price('005930') 호출")
            result = stock_api.get_daily_price("005930")

            if w and len(w) > 1:
                print(f"   ⚠️ 경고: {w[-1].message}")

            if result:
                print(f"   ✓ 일별 시세 조회 성공")
            else:
                print(f"   ✗ 실패")

            # 3. get_orderbook (기존) -> get_book_order (신규)
            print("\n3. get_orderbook('005930') 호출")
            result = stock_api.get_orderbook("005930")

            if w and len(w) > 2:
                print(f"   ⚠️ 경고: {w[-1].message}")

            if result:
                print(f"   ✓ 호가 조회 성공")
            else:
                print(f"   ✗ 실패")

            # 4. get_stock_investor (기존) -> get_investor_trend (신규)
            print("\n4. get_stock_investor('005930') 호출")
            result = stock_api.get_stock_investor("005930")

            if w and len(w) > 3:
                print(f"   ⚠️ 경고: {w[-1].message}")

            if result:
                print(f"   ✓ 투자자 동향 조회 성공")
            else:
                print(f"   ✗ 실패")

            # 5. 경고 없는 메서드 테스트
            print("\n5. get_stock_info('005930') 호출 (경고 없음)")
            initial_warning_count = len(w)
            result = stock_api.get_stock_info("005930")

            if len(w) == initial_warning_count:
                print(f"   ✓ 경고 없음 (정상)")
            else:
                print(f"   ✗ 예상치 못한 경고 발생")

        print("\n[신규 메서드명 테스트]")
        print("-" * 40)

        # 경고 없이 신규 메서드 사용
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            print("\n1. get_price_current('005930') 호출 (신규)")
            result = stock_api.get_price_current("005930")

            if len(w) == 0:
                print(f"   ✓ 경고 없음 (정상)")
            else:
                print(f"   ✗ 예상치 못한 경고: {w[-1].message}")

            if result and result.get('rt_cd') == '0':
                output = result.get('output', {})
                print(f"   ✓ 현재가: {output.get('stck_prpr', 'N/A')}원")

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()


def test_account_api_compatibility():
    """AccountAPI 하위 호환성 테스트"""
    print("\n" + "=" * 60)
    print("AccountAPI 하위 호환성 테스트")
    print("=" * 60)

    # 환경변수 설정
    app_key = os.environ.get('APP_KEY')
    app_secret = os.environ.get('APP_SECRET')
    account_no = os.environ.get('CANO') or os.environ.get('ACC_NO')
    account_code = os.environ.get('ACNT_PRDT_CD') or os.environ.get('ACC_PRD') or '01'

    if not all([app_key, app_secret, account_no]):
        print("환경변수가 설정되지 않았습니다.")
        return

    try:
        # Agent 생성
        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code
        )

        # 호환성 AccountAPI 생성
        account_api = AccountAPI(
            client=agent.client,
            account_info={'CANO': account_no, 'ACNT_PRDT_CD': account_code}
        )

        print("\n[기존 메서드명 테스트]")
        print("-" * 40)

        # 경고 캡처 설정
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 1. get_account_balance (기존) -> get_balance_holdings (신규)
            print("\n1. get_account_balance() 호출")
            result = account_api.get_account_balance()

            if w:
                print(f"   ⚠️ 경고: {w[-1].message}")

            if result and result.get('rt_cd') == '0':
                print(f"   ✓ 잔고 조회 성공")
            else:
                print(f"   ✗ 실패: {result.get('msg1') if result else 'No response'}")

            # 2. get_cash_available (기존) -> get_order_capacity (신규)
            print("\n2. get_cash_available('005930') 호출")
            result = account_api.get_cash_available("005930")

            if w and len(w) > 1:
                print(f"   ⚠️ 경고: {w[-1].message}")

            if result:
                print(f"   ✓ 주문 가능 금액 조회 성공")
            else:
                print(f"   ✗ 실패")

            # 3. get_buyable_cash (편의 메서드)
            print("\n3. get_buyable_cash('005930') 호출")
            cash = account_api.get_buyable_cash("005930")

            if w and len(w) > 2:
                print(f"   ⚠️ 경고: {w[-1].message}")

            if cash is not None:
                print(f"   ✓ 매수 가능 현금: {cash:,}원")
            else:
                print(f"   ✗ 실패")

        print("\n[신규 메서드명 테스트]")
        print("-" * 40)

        # 경고 없이 신규 메서드 사용
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            print("\n1. get_balance_holdings() 호출 (신규)")
            result = account_api.get_balance_holdings()

            if len(w) == 0:
                print(f"   ✓ 경고 없음 (정상)")
            else:
                print(f"   ✗ 예상치 못한 경고: {w[-1].message}")

            if result and result.get('rt_cd') == '0':
                print(f"   ✓ 잔고 조회 성공")

            print("\n2. get_total_assets() 호출 (신규 유틸리티)")
            assets = account_api.get_total_assets()

            if assets:
                print(f"   ✓ 총자산: {assets.get('총자산', 0):,}원")
                print(f"   ✓ 수익률: {assets.get('수익률', 0):.2f}%")

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("PyKIS API 하위 호환성 테스트")
    print("=" * 60)
    print("\n이 테스트는 기존 메서드명을 사용하는 코드가")
    print("리팩터링 후에도 정상 작동하는지 확인합니다.")
    print("각 deprecated 메서드는 경고를 표시해야 합니다.")

    # StockAPI 테스트
    test_stock_api_compatibility()

    # AccountAPI 테스트
    test_account_api_compatibility()

    print("\n" + "=" * 60)
    print("하위 호환성 테스트 완료!")
    print("=" * 60)
    print("\n💡 권장사항:")
    print("- deprecated 경고가 표시된 메서드는 새 버전으로 교체하세요")
    print("- 예: get_stock_price() -> get_price_current()")
    print("- 예: get_account_balance() -> get_balance_holdings()")


if __name__ == "__main__":
    main()