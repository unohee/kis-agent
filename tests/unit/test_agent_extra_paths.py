"""Agent의 경량 위임 및 백그라운드 사전 로드 실패 경로 테스트."""

from unittest.mock import MagicMock, patch

import kis_agent.core.agent as agent_module


def _agent_with_apis():
    agent = object.__new__(agent_module.Agent)
    agent.stock_api = object()
    agent.market_api = type("Market", (), {"market_only": "market"})()
    agent.account_api = object()
    agent.program_api = object()
    agent.investor_api = type("Investor", (), {"investor_only": "investor"})()
    agent.interest_api = object()
    return agent


def test_properties_and_getattr_delegate_to_remaining_apis():
    agent = _agent_with_apis()
    agent.overseas_api = "overseas"

    assert agent.overseas == "overseas"
    assert agent.market_only == "market"
    assert agent.investor_only == "investor"
    with patch.object(agent_module, "get_sector_code_by_market", return_value="sectors") as get_codes:
        assert agent.get_sector_code_by_market("all") == "sectors"
    get_codes.assert_called_once_with(market="all")


def test_preload_master_failure_is_logged_without_blocking():
    agent = object.__new__(agent_module.Agent)
    agent.logger = MagicMock()

    class ImmediateThread:
        def __init__(self, target, daemon):
            self.target = target
            assert daemon is True

        def start(self):
            self.target()

    with patch.object(agent_module, "_load_stock_master", side_effect=RuntimeError("offline")), patch(
        "threading.Thread", ImmediateThread
    ):
        agent._preload_masters()

    agent.logger.warning.assert_called_once()
