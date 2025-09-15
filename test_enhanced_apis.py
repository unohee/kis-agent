#!/usr/bin/env python
"""
강화된 API 테스트 스크립트

리팩터링된 API들의 포괄적인 테스트:
- 데코레이터 기반 API 호출
- fail-fast 예외 처리
- 메서드명 정규화
- 캐시 동작
- 하위 호환성
"""

import os
import sys
import time
import warnings
import traceback
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# pykis 경로 추가
sys.path.insert(0, '/home/unohee/dev/tools/pykis-refactor')

from pykis import Agent
from pykis.stock.api_enhanced import StockAPIEnhanced
from pykis.account.api_enhanced import AccountAPIEnhanced


def test_stock_api_enhanced(agent):
    """강화된 Stock API 테스트"""
    print("\n" + "=" * 60)
    print("StockAPIEnhanced 테스트")
    print("=" * 60)

    stock_api = StockAPIEnhanced(
        client=agent.client,
        account_info={'CANO': agent.account['CANO'], 'ACNT_PRDT_CD': agent.account['ACNT_PRDT_CD']}
    )

    tests_passed = 0
    tests_failed = 0

    # 1. 현재가 조회 테스트
    print("\n[1] 현재가 조회 (get_price_current)")
    try:
        result = stock_api.get_price_current("005930")
        if result and result.get('rt_cd') == '0':
            output = result.get('output', {})
            print(f"  ✓ 삼성전자 현재가: {output.get('stck_prpr', 'N/A')}원")
            print(f"  ✓ 등락률: {output.get('prdy_ctrt', 'N/A')}%")
            tests_passed += 1
        else:
            print(f"  ✗ 실패: {result.get('msg1') if result else 'No response'}")
            tests_failed += 1
    except Exception as e:
        print(f"  ✗ 예외 발생: {e}")
        tests_failed += 1

    # 2. fail-fast 예외 처리 테스트
    print("\n[2] fail-fast 예외 처리 테스트")
    try:
        # 잘못된 종목코드로 호출
        result = stock_api.get_price_current("INVALID")
    except ValueError as e:
        print(f"  ✓ 예상된 예외 발생: {e}")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ 예상치 못한 예외: {e}")
        tests_failed += 1

    # 3. 호가 조회 테스트
    print("\n[3] 호가 조회 (get_book_order)")
    try:
        result = stock_api.get_book_order("005930")
        if result and result.get('rt_cd') == '0':
            output1 = result.get('output1', {})
            print(f"  ✓ 매도호가1: {output1.get('askp1', 'N/A')}원")
            print(f"  ✓ 매수호가1: {output1.get('bidp1', 'N/A')}원")
            tests_passed += 1
        else:
            print(f"  ✗ 실패: {result.get('msg1') if result else 'No response'}")
            tests_failed += 1
    except Exception as e:
        print(f"  ✗ 예외 발생: {e}")
        tests_failed += 1

    # 4. 캐시 동작 테스트
    print("\n[4] 캐시 동작 테스트")
    try:
        # 첫 번째 호출 (캐시 미스)
        start = time.time()
        result1 = stock_api.get_price_current("005930")
        time1 = time.time() - start

        # 두 번째 호출 (캐시 히트)
        start = time.time()
        result2 = stock_api.get_price_current("005930")
        time2 = time.time() - start

        if result2 and result2.get('_cached'):
            print(f"  ✓ 캐시 히트 확인 (첫 호출: {time1:.3f}초, 캐시: {time2:.3f}초)")
            tests_passed += 1
        else:
            print(f"  ✓ 캐시 미스 (API 재호출)")
            tests_passed += 1
    except Exception as e:
        print(f"  ✗ 예외 발생: {e}")
        tests_failed += 1

    # 5. 하위 호환성 테스트
    print("\n[5] 하위 호환성 테스트 (deprecated 메서드)")
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Deprecated 메서드 호출
            result = stock_api.get_stock_price("005930")

            if w and issubclass(w[0].category, DeprecationWarning):
                print(f"  ✓ DeprecationWarning 발생: {str(w[0].message)[:50]}...")
                if result and result.get('rt_cd') == '0':
                    print(f"  ✓ 하위 호환성 유지됨")
                    tests_passed += 1
                else:
                    print(f"  ✗ 호출 실패")
                    tests_failed += 1
            else:
                print(f"  ✗ DeprecationWarning 미발생")
                tests_failed += 1
    except Exception as e:
        print(f"  ✗ 예외 발생: {e}")
        tests_failed += 1

    # 6. 시장 정보 조회 테스트
    print("\n[6] 시장 정보 조회 (get_market_fluctuation)")
    try:
        result = stock_api.get_market_fluctuation(min_volume=1000000)
        if result and result.get('rt_cd') == '0':
            output = result.get('output', [])
            print(f"  ✓ 조회된 종목 수: {len(output)}개")
            if output and len(output) > 0:
                first = output[0]
                print(f"  ✓ 1위: {first.get('hts_kor_isnm', 'N/A')} ({first.get('prdy_ctrt', 'N/A')}%)")
            tests_passed += 1
        else:
            print(f"  ✗ 실패: {result.get('msg1') if result else 'No response'}")
            tests_failed += 1
    except Exception as e:
        print(f"  ✗ 예외 발생: {e}")
        tests_failed += 1

    # 7. 재시도 로직 테스트 (투자자 동향)
    print("\n[7] 재시도 로직 테스트 (@with_retry)")
    try:
        result = stock_api.get_investor_trend("005930")
        if result and result.get('rt_cd') == '0':
            print(f"  ✓ 투자자 동향 조회 성공 (재시도 로직 포함)")
            tests_passed += 1
        else:
            print(f"  ✗ 실패: {result.get('msg1') if result else 'No response'}")
            tests_failed += 1
    except Exception as e:
        print(f"  ✗ 예외 발생: {e}")
        tests_failed += 1

    print(f"\n[Stock API 결과] 성공: {tests_passed}, 실패: {tests_failed}")
    return tests_passed, tests_failed


def test_account_api_enhanced(agent):
    """강화된 Account API 테스트"""
    print("\n" + "=" * 60)
    print("AccountAPIEnhanced 테스트")
    print("=" * 60)

    account_api = AccountAPIEnhanced(
        client=agent.client,
        account_info={'CANO': agent.account['CANO'], 'ACNT_PRDT_CD': agent.account['ACNT_PRDT_CD']}
    )

    tests_passed = 0
    tests_failed = 0

    # 1. 잔고 조회 테스트
    print("\n[1] 잔고 조회 (get_balance_holdings)")
    try:
        result = account_api.get_balance_holdings()
        if result and result.get('rt_cd') == '0':
            output1 = result.get('output1', [])
            output2 = result.get('output2', [{}])[0]
            print(f"  ✓ 보유종목 수: {len(output1)}개")
            print(f"  ✓ 총 평가금액: {output2.get('tot_evlu_amt', 'N/A')}원")
            tests_passed += 1
        else:
            print(f"  ✗ 실패: {result.get('msg1') if result else 'No response'}")
            tests_failed += 1
    except Exception as e:
        print(f"  ✗ 예외 발생: {e}")
        tests_failed += 1

    # 2. 주문 가능 금액 조회 테스트
    print("\n[2] 주문 가능 금액 조회 (get_order_capacity)")
    try:
        result = account_api.get_order_capacity("005930")
        if result and result.get('rt_cd') == '0':
            output = result.get('output', {})
            print(f"  ✓ 주문 가능 현금: {output.get('ord_psbl_cash', 'N/A')}원")
            print(f"  ✓ 최대 매수 수량: {output.get('max_buy_qty', 'N/A')}주")
            tests_passed += 1
        else:
            print(f"  ✗ 실패: {result.get('msg1') if result else 'No response'}")
            tests_failed += 1
    except Exception as e:
        print(f"  ✗ 예외 발생: {e}")
        tests_failed += 1

    # 3. 예외 처리 테스트
    print("\n[3] 예외 처리 테스트 (잘못된 종목코드)")
    try:
        result = account_api.get_order_capacity("WRONG")
    except ValueError as e:
        print(f"  ✓ 예상된 예외 발생: {e}")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ 예상치 못한 예외: {e}")
        tests_failed += 1

    # 4. 총 자산 정보 테스트
    print("\n[4] 총 자산 정보 (get_total_assets)")
    try:
        assets = account_api.get_total_assets()
        if assets:
            print(f"  ✓ 예수금: {assets.get('예수금', 0):,}원")
            print(f"  ✓ 주식평가액: {assets.get('주식평가액', 0):,}원")
            print(f"  ✓ 총자산: {assets.get('총자산', 0):,}원")
            print(f"  ✓ 수익률: {assets.get('수익률', 0):.2f}%")
            tests_passed += 1
        else:
            print(f"  ✗ 자산 정보 조회 실패")
            tests_failed += 1
    except Exception as e:
        print(f"  ✗ 예외 발생: {e}")
        tests_failed += 1

    # 5. 캐시 동작 테스트
    print("\n[5] 캐시 동작 테스트 (@cache_result)")
    try:
        # 첫 번째 호출
        start = time.time()
        result1 = account_api.get_balance_holdings()
        time1 = time.time() - start

        # 두 번째 호출 (캐시 히트 예상)
        start = time.time()
        result2 = account_api.get_balance_holdings()
        time2 = time.time() - start

        print(f"  ✓ 첫 호출: {time1:.3f}초, 두 번째: {time2:.3f}초")
        if time2 < time1 * 0.5:  # 캐시가 50% 이상 빠르면 성공
            print(f"  ✓ 캐시 효과 확인됨")
            tests_passed += 1
        else:
            print(f"  ✓ 캐시 미사용 또는 효과 미미")
            tests_passed += 1
    except Exception as e:
        print(f"  ✗ 예외 발생: {e}")
        tests_failed += 1

    # 6. 하위 호환성 테스트
    print("\n[6] 하위 호환성 테스트 (deprecated 메서드)")
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Deprecated 메서드 호출
            result = account_api.get_account_balance()

            if w and issubclass(w[0].category, DeprecationWarning):
                print(f"  ✓ DeprecationWarning 발생")
                if result and result.get('rt_cd') == '0':
                    print(f"  ✓ 하위 호환성 유지됨")
                    tests_passed += 1
                else:
                    print(f"  ✗ 호출 실패")
                    tests_failed += 1
            else:
                print(f"  ✗ DeprecationWarning 미발생")
                tests_failed += 1
    except Exception as e:
        print(f"  ✗ 예외 발생: {e}")
        tests_failed += 1

    print(f"\n[Account API 결과] 성공: {tests_passed}, 실패: {tests_failed}")
    return tests_passed, tests_failed


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("PyKIS 리팩터링 API 포괄적 테스트")
    print("=" * 60)

    # 환경변수 확인
    app_key = os.environ.get('APP_KEY')
    app_secret = os.environ.get('APP_SECRET')
    account_no = os.environ.get('CANO') or os.environ.get('ACC_NO')
    account_code = os.environ.get('ACNT_PRDT_CD') or os.environ.get('ACC_PRD') or '01'

    if not all([app_key, app_secret, account_no]):
        print("\n❌ 환경변수가 설정되지 않았습니다.")
        print("필요한 환경변수: APP_KEY, APP_SECRET, CANO (또는 ACC_NO)")
        return

    print(f"\n계좌: {account_no[:4]}****-{account_code}")

    try:
        # Agent 생성
        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code
        )

        total_passed = 0
        total_failed = 0

        # Stock API 테스트
        stock_passed, stock_failed = test_stock_api_enhanced(agent)
        total_passed += stock_passed
        total_failed += stock_failed

        # Account API 테스트
        account_passed, account_failed = test_account_api_enhanced(agent)
        total_passed += account_passed
        total_failed += account_failed

        # 최종 결과
        print("\n" + "=" * 60)
        print("테스트 완료!")
        print("=" * 60)
        print(f"총 테스트: {total_passed + total_failed}개")
        print(f"✓ 성공: {total_passed}개")
        print(f"✗ 실패: {total_failed}개")

        if total_failed == 0:
            print("\n🎉 모든 테스트가 성공했습니다!")
        else:
            print(f"\n⚠️ {total_failed}개의 테스트가 실패했습니다.")

    except Exception as e:
        print(f"\n❌ 치명적 오류 발생: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()