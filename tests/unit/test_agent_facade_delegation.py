"""
Agent Facade Delegation 테스트

수정일: 2026-02-06 - Agent mock 패턴 수정 (read_token/auth 제거)
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

import pykis.core.agent  # noqa: F401
from pykis.core.client import API_ENDPOINTS, KISClient


def get_agent_module():
    """agent 모듈을 sys.modules에서 가져옵니다."""
    return sys.modules["pykis.core.agent"]


class MockKISClient:
    """테스트용 Mock KISClient"""

    def __init__(self):
        self.token = "mock_token"
        self.token_expired = "2026-01-05 12:00:00"
        self.base_url = "https://mock.api.com"
        self.is_real = True
        self.enable_rate_limiter = False
        self.rate_limiter = None
        self._requests = []

    def make_request(
        self,
        endpoint: str,
        tr_id: str,
        params: dict,
        retries: int = 0,
        method: str = "GET",
    ):
        self._requests.append({"endpoint": endpoint, "tr_id": tr_id, "params": params})
        return {"rt_cd": "0", "msg1": "OK", "output": {}}


@pytest.fixture
def mock_agent():
    """Agent 인스턴스를 생성하는 fixture"""
    agent_module = get_agent_module()

    mock_client = MockKISClient()

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

    with patch.object(agent_module, "KISConfig"), patch.object(
        agent_module, "KISClient", return_value=mock_client
    ):
        # API 클래스들 패치
        patches = []
        for api_name in api_classes:
            p = patch.object(agent_module, api_name)
            patches.append(p)
            p.start()

        try:
            agent = agent_module.Agent(
                app_key="k",
                app_secret="s",
                account_no="12345678",
                account_code="01",
                base_url="https://openapivts.koreainvestment.com:29443",
            )
            # 테스트용으로 client 속성 교체
            agent._mock_client = mock_client
            yield agent
        finally:
            for p in patches:
                p.stop()


def test_agent_inquire_price_delegates_to_price_api(mock_agent):
    """Agent.inquire_price가 price_api로 위임되는지 확인"""
    expected_result = {"rt_cd": "0", "msg1": "OK", "output": {"stck_prpr": "70000"}}

    # stock_api.inquire_price mock
    mock_agent.stock_api.inquire_price = MagicMock(return_value=expected_result)

    resp = mock_agent.inquire_price("005930")

    assert resp is not None
    assert resp.get("rt_cd") == "0"
    # Agent는 __getattr__를 통해 stock_api로 위임, 코드 파라미터만 전달됨
    mock_agent.stock_api.inquire_price.assert_called_once_with("005930")


def test_agent_inquire_ccnl_delegates_to_price_api(mock_agent):
    """Agent.inquire_ccnl가 price_api로 위임되는지 확인"""
    expected_result = {"rt_cd": "0", "msg1": "OK", "output": []}

    # stock_api.inquire_ccnl mock
    mock_agent.stock_api.inquire_ccnl = MagicMock(return_value=expected_result)

    resp = mock_agent.inquire_ccnl("005930")

    assert resp is not None
    assert resp.get("rt_cd") == "0"
    mock_agent.stock_api.inquire_ccnl.assert_called_once_with("005930")
