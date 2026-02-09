"""
프로그램매매 정보 조회 테스트
"""

import os

import pytest

from pykis import Agent

if not os.getenv("RUN_LIVE_TESTS"):
    pytest.skip("실제 API 테스트 건너뜀", allow_module_level=True)


@pytest.mark.requires_credentials
def test_program_trade_info(test_stock_code):
    """프로그램매매 정보 조회 테스트"""
    print("\n[프로그램매매 정보 조회 테스트]")
    agent = Agent(
        app_key=os.getenv("KIS_APP_KEY", ""),
        app_secret=os.getenv("KIS_APP_SECRET", ""),
        account_no=os.getenv("KIS_ACCOUNT_NO", ""),
        account_code=os.getenv("KIS_ACCOUNT_CODE", ""),
    )

    # 프로그램매매 정보 조회
    ref_date = "20250516"
    result = agent.get_program_trade_summary(test_stock_code, ref_date=ref_date)
    assert result is not None, "프로그램매매 정보 조회 실패"

    # 결과 출력
    print(f"프로그램매매 정보 ({test_stock_code}, {ref_date}):")
    print(result)


@pytest.mark.requires_credentials
def test_program_trade_hourly_trend(test_stock_code):
    """시간별 프로그램 매매 추이 조회 테스트"""
    print("\n[시간별 프로그램 매맨 추이 조회 테스트]")
    agent = Agent(
        app_key=os.getenv("KIS_APP_KEY", ""),
        app_secret=os.getenv("KIS_APP_SECRET", ""),
        account_no=os.getenv("KIS_ACCOUNT_NO", ""),
        account_code=os.getenv("KIS_ACCOUNT_CODE", ""),
    )

    # 시간별 프로그램 매매 추이 조회
    result = agent.get_program_trade_hourly_trend(test_stock_code)
    assert result is not None, "시간별 프로그램 매매 추이 조회 실패"

    # 결과 출력
    print(f"시간별 프로그램 매매 추이 ({test_stock_code}):")
    print(result)
