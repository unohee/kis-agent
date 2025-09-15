"""
리팩토링된 API 테스트

데코레이터 기반 API와 기존 API 비교 테스트
"""

import os
import sys
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# pykis 경로 추가
sys.path.insert(0, '/home/unohee/dev/tools/pykis-refactor')

from pykis import Agent
from pykis.stock.api_refactored import StockAPIRefactored

def test_refactored_api():
    """리팩토링된 API 테스트"""

    # 환경변수 설정
    app_key = os.environ.get('APP_KEY')
    app_secret = os.environ.get('APP_SECRET')
    account_no = os.environ.get('CANO') or os.environ.get('ACC_NO')
    account_code = os.environ.get('ACNT_PRDT_CD') or os.environ.get('ACC_PRD') or '01'

    if not all([app_key, app_secret, account_no]):
        print("환경변수가 설정되지 않았습니다.")
        return

    print(f"계좌: {account_no[:4]}****-{account_code}\n")

    try:
        # Agent 생성
        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code
        )

        # 리팩토링된 API 인스턴스 생성
        refactored_api = StockAPIRefactored(
            client=agent.client,
            account_info={'CANO': account_no, 'ACNT_PRDT_CD': account_code}
        )

        print("=" * 50)
        print("리팩토링된 API 테스트")
        print("=" * 50)

        # 1. 현재가 조회 테스트
        print("\n[1] 현재가 조회 (get_price_current)")
        result = refactored_api.get_price_current("005930")
        if result and result.get('rt_cd') == '0':
            output = result.get('output', {})
            print(f"  삼성전자 현재가: {output.get('stck_prpr', 'N/A')}원")
            print(f"  등락률: {output.get('prdy_ctrt', 'N/A')}%")
        else:
            print(f"  실패: {result.get('msg1') if result else 'No response'}")

        # 2. 호가 조회 테스트
        print("\n[2] 호가 조회 (get_book_order)")
        result = refactored_api.get_book_order("005930")
        if result and result.get('rt_cd') == '0':
            output1 = result.get('output1', {})
            print(f"  매도호가1: {output1.get('askp1', 'N/A')}원")
            print(f"  매수호가1: {output1.get('bidp1', 'N/A')}원")
        else:
            print(f"  실패: {result.get('msg1') if result else 'No response'}")

        # 3. 시장 등락률 테스트
        print("\n[3] 등락률 순위 (get_market_fluctuation)")
        result = refactored_api.get_market_fluctuation()
        if result and result.get('rt_cd') == '0':
            output = result.get('output', [])
            print(f"  조회된 종목 수: {len(output)}개")
            if output and len(output) > 0:
                first = output[0]
                print(f"  1위: {first.get('hts_kor_isnm', 'N/A')} ({first.get('prdy_ctrt', 'N/A')}%)")
        else:
            print(f"  실패: {result.get('msg1') if result else 'No response'}")

        # 4. Deprecated 메서드 테스트
        print("\n[4] Deprecated 메서드 테스트 (하위 호환성)")
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 기존 메서드 호출
            result = refactored_api.get_stock_price("005930")

            # DeprecationWarning 확인
            if w and issubclass(w[0].category, DeprecationWarning):
                print(f"  경고 발생: {w[0].message}")

            if result and result.get('rt_cd') == '0':
                print("  하위 호환성 유지: 성공")
            else:
                print("  하위 호환성 실패")

        # 5. 기존 API와 비교
        print("\n[5] 기존 API vs 리팩토링 API 비교")

        # 기존 API
        original_result = agent.stock_api.get_stock_price("005930")

        # 리팩토링 API
        refactored_result = refactored_api.get_price_current("005930")

        if original_result and refactored_result:
            orig_price = original_result.get('output', {}).get('stck_prpr')
            ref_price = refactored_result.get('output', {}).get('stck_prpr')

            if orig_price == ref_price:
                print(f"  결과 일치: {orig_price}원")
            else:
                print(f"  결과 불일치! 기존: {orig_price}, 리팩토링: {ref_price}")
        else:
            print("  비교 실패")

        print("\n" + "=" * 50)
        print("테스트 완료!")
        print("=" * 50)

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_refactored_api()