"""
조건검색식 종목 조회 테스트
"""

import os

import pytest

from kis_agent import Agent

if not os.getenv("RUN_LIVE_TESTS"):
    pytest.skip("실제 API 테스트 건너뜀", allow_module_level=True)


@pytest.mark.requires_credentials
def test_condition_stocks():
    """조건검색식 종목 조회 테스트"""
    agent = Agent(
        app_key=os.getenv("KIS_APP_KEY", ""),
        app_secret=os.getenv("KIS_APP_SECRET", ""),
        account_no=os.getenv("KIS_ACCOUNT_NO", ""),
        account_code=os.getenv("KIS_ACCOUNT_CODE", ""),
    )

    # 조건검색식 목록 조회
    conditions = agent.get_condition_list()
    assert conditions is not None, "조건검색식 목록 조회 실패"

    if conditions and len(conditions) > 0:
        # 첫 번째 조건검색식으로 ���목 조회
        first_condition = conditions[0]
        stocks = agent.get_condition_stocks(first_condition["condition_name"])
        assert stocks is not None, "조건검색식 종목 조회 실패"
