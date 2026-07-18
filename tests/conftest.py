"""
테스트 설정을 관리하는 모듈입니다.
"""

import os
import sys
from contextlib import ExitStack
from unittest.mock import patch

import pytest

# 저장소 체크아웃에서 직접 실행할 때도 패키지를 임포트할 수 있게 루트를 먼저 추가합니다.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from kis_agent import Agent
from kis_agent.core.config import KISConfig


def pytest_collection_modifyitems(config, items):
    """자격증명이 없는 로컬 실행에서 실계좌 테스트를 안전하게 제외한다."""
    required_credentials = ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_NO")
    if all(os.getenv(name) for name in required_credentials):
        return

    skip_credentials = pytest.mark.skip(
        reason="KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NO 자격증명이 필요합니다"
    )
    for item in items:
        if item.get_closest_marker("requires_credentials"):
            item.add_marker(skip_credentials)


@pytest.fixture
def account_info():
    """테스트용 계좌 정보를 반환합니다."""
    config = KISConfig()
    return {"CANO": config.account_stock, "ACNT_PRDT_CD": config.account_product}


@pytest.fixture
def test_stock_code():
    """테스트용 종목 코드를 반환합니다."""
    return "005930"  # 삼성전자


@pytest.fixture
def patch_all_apis():
    """Agent 생성에 필요한 모든 API를 패치하는 fixture.

    Agent 클래스의 종합적인 단위 테스트를 위해 모든 API 의존성을 Mock으로 대체합니다.
    이 fixture는 test_agent_unit_comprehensive.py에서 추출되어 전역 fixture로 승격되었습니다.

    Args:
        agent_module: kis_agent.core.agent 모듈
        mocks: 특정 API에 대한 mock 객체를 지정하는 딕셔너리 (선택사항)
               예: {"StockAPI": mock_stock_api}

    Returns:
        function: patch_all_apis 함수
    """

    def _patch_all_apis(agent_module, mocks=None):
        """Agent 생성에 필요한 모든 API를 패치하는 컨텍스트 매니저 스택을 반환합니다."""
        if mocks is None:
            mocks = {}

        stack = ExitStack()

        api_classes = [
            "AccountAPI",
            "StockAPI",
            "StockInvestorAPI",
            "ProgramTradeAPI",
            "StockMarketAPI",
            "InterestStockAPI",
            "OverseasStockAPI",
            "Futures",
            "OverseasFutures",
        ]

        for api_name in api_classes:
            if api_name in mocks:
                mock_obj = stack.enter_context(patch.object(agent_module, api_name))
                mock_obj.return_value = mocks[api_name]
            else:
                stack.enter_context(patch.object(agent_module, api_name))

        return stack

    return _patch_all_apis
