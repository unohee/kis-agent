#!/usr/bin/env python3
"""관심종목 API 테스트 스크립트"""

import os
import sys

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pykis import Agent


def test_interest_stocks():
    """관심종목 API 테스트"""
    # 환경변수에서 계좌 정보 로드
    app_key = os.environ.get("KIS_APP_KEY")
    app_secret = os.environ.get("KIS_APP_SECRET")
    account_no = os.environ.get("KIS_ACCOUNT_NO")
    account_code = os.environ.get("KIS_ACCOUNT_CODE", "01")

    if not all([app_key, app_secret, account_no]):
        print("Error: 필수 환경변수가 설정되지 않았습니다.")
        print("다음 환경변수를 설정하세요:")
        print("  export KIS_APP_KEY='your_app_key'")
        print("  export KIS_APP_SECRET='your_app_secret'")
        print("  export KIS_ACCOUNT_NO='your_account_no'")
        print("  export KIS_ACCOUNT_CODE='01'  # 선택사항")
        return

    try:
        # Agent 인스턴스 생성
        print("\n=== Agent 초기화 중... ===")
        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code,
        )
        print("Agent 초기화 완료!\n")

        # 1. 관심종목 그룹 목록 조회
        print("\n=== 1. 관심종목 그룹 목록 조회 ===")
        user_id = "unohee"
        groups = agent.get_interest_group_list(user_id)

        if groups:
            print("✓ 관심종목 그룹 조회 성공!")
            print(f"응답 구조: {list(groups.keys())}")
            if "output" in groups:
                print(f"\n그룹 목록 ({len(groups['output'])}개):")
                for group in groups["output"]:
                    print(f"  - 그룹: {group}")
        else:
            print("✗ 관심종목 그룹 조회 실패")

        # 2. 관심종목 그룹별 종목 조회
        print("\n=== 2. 관심종목 그룹별 종목 조회 ===")
        inter_grp_code = "001"  # 첫 번째 그룹
        stocks = agent.get_interest_stock_list(user_id, inter_grp_code)

        if stocks:
            print("✓ 관심종목 종목 조회 성공!")
            print(f"응답 구조: {list(stocks.keys())}")

            if "output1" in stocks:
                print("\n그룹 정보:")
                print(f"  - {stocks['output1']}")

            if "output2" in stocks:
                stock_list = stocks["output2"]
                print(f"\n종목 목록 ({len(stock_list)}개):")
                for stock in stock_list[:10]:  # 처음 10개만 출력
                    name = stock.get("hts_kor_isnm", "N/A")
                    code = stock.get("jong_code", "N/A")
                    market = stock.get("fid_mrkt_cls_code", "N/A")
                    print(f"  - {name} ({code}) [{market}]")

                if len(stock_list) > 10:
                    print(f"  ... 외 {len(stock_list) - 10}개 종목")
        else:
            print("✗ 관심종목 종목 조회 실패")

        print("\n=== 테스트 완료 ===\n")

    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_interest_stocks()
