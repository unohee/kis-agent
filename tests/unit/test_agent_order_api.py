"""
Agent 클래스의 새로 추가된 주문 관련 메서드들에 대한 단위 테스트

수정일: 2026-02-06 - Agent mock 패턴 수정 (read_token/auth 제거)
"""

import sys
from unittest.mock import Mock, patch

import pytest

import kis_agent.core.agent  # noqa: F401


def get_agent_module():
    """agent 모듈을 sys.modules에서 가져옵니다."""
    return sys.modules["kis_agent.core.agent"]


class MockKISClient:
    """테스트용 Mock KISClient"""

    def __init__(self):
        self.token = "mock_token"
        self.token_expired = "2026-01-05 12:00:00"
        self.base_url = "https://mock.api.com"
        self.is_real = True
        self.enable_rate_limiter = False
        self.rate_limiter = None


class TestAgentOrderAPI:
    """Agent 클래스 주문 관련 메서드 테스트"""

    @pytest.fixture
    def mock_agent(self):
        """Mock Agent 생성"""
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
                    app_key="test_key",
                    app_secret="test_secret",
                    account_no="12345678",
                    account_code="01",
                )

                # Mock account_api와 stock_api 재설정
                agent.account_api = Mock()
                agent.stock_api = Mock()
                yield agent
            finally:
                for p in patches:
                    p.stop()

    def test_order_stock_cash_success(self, mock_agent):
        """Agent를 통한 현금 주문 성공 테스트"""
        # Given
        expected_response = {
            "rt_cd": "0",
            "msg1": "주문이 정상적으로 접수되었습니다.",
            "output": {"odno": "0000117057"},
        }
        mock_agent.account_api.order_cash.return_value = expected_response

        # When
        result = mock_agent.order_stock_cash(
            ord_dv="buy", pdno="005930", ord_dvsn="00", ord_qty="1", ord_unpr="70000"
        )

        # Then
        assert result == expected_response
        mock_agent.account_api.order_cash.assert_called_once_with(
            pdno="005930",
            qty=1,
            price=70000,
            buy_sell="BUY",
            order_type="00",
            exchange="KRX",
        )

    def test_order_stock_cash_with_options(self, mock_agent):
        """Agent를 통한 현금 주문 옵션 파라미터 테스트"""
        # Given
        expected_response = {"rt_cd": "0", "msg1": "성공"}
        mock_agent.account_api.order_cash.return_value = expected_response

        # When
        result = mock_agent.order_stock_cash(
            ord_dv="sell",
            pdno="005930",
            ord_dvsn="01",
            ord_qty="5",
            ord_unpr="0",
            excg_id_dvsn_cd="SOR",
            sll_type="01",
            cndt_pric="69000",
        )

        # Then
        mock_agent.account_api.order_cash.assert_called_once_with(
            pdno="005930",
            qty=5,
            price=0,
            buy_sell="SELL",
            order_type="01",
            exchange="SOR",
        )

    def test_order_stock_credit_success(self, mock_agent):
        """Agent를 통한 신용 주문 성공 테스트"""
        # Given
        expected_response = {
            "rt_cd": "0",
            "msg1": "신용주문이 정상적으로 접수되었습니다.",
            "output": {"odno": "0000117058"},
        }
        mock_agent.account_api.order_credit_buy.return_value = expected_response

        # When
        result = mock_agent.order_stock_credit(
            ord_dv="buy",
            pdno="005930",
            crdt_type="21",
            loan_dt="20250911",
            ord_dvsn="00",
            ord_qty="1",
            ord_unpr="70000",
        )

        # Then
        assert result == expected_response
        mock_agent.account_api.order_credit_buy.assert_called_once_with(
            pdno="005930",
            qty=1,
            price=70000,
            order_type="00",
            credit_type="21",
            exchange="KRX",
        )

    def test_stock_api_error_propagation(self, mock_agent):
        """AccountAPI 에러가 Agent로 전파되는지 테스트"""
        # Given
        mock_agent.account_api.order_cash.side_effect = ValueError("Test error")

        # When & Then
        with pytest.raises(ValueError, match="Test error"):
            mock_agent.order_stock_cash("buy", "005930", "00", "1", "70000")

    def test_agent_method_delegation(self, mock_agent):
        """Agent 메서드가 적절한 API로 위임되는지 테스트"""
        # Given - account_api로 위임되는 메서드들
        account_api_methods = [
            ("order_stock_cash", "order_cash"),
            ("order_stock_credit", "order_credit_buy"),
        ]
        # stock_api로 위임되는 메서드들
        stock_api_methods = [
            ("inquire_order_psbl", "inquire_psbl_order"),
            ("inquire_credit_order_psbl", "inquire_credit_psamount"),
        ]

        for agent_method, account_api_method in account_api_methods:
            # When
            agent_func = getattr(mock_agent, agent_method)
            # Then
            assert callable(agent_func), f"{agent_method} should be callable"
            assert hasattr(
                mock_agent.account_api, account_api_method
            ), f"account_api should have {account_api_method}"

        for agent_method, stock_api_method in stock_api_methods:
            # When
            agent_func = getattr(mock_agent, agent_method)
            # Then
            assert callable(agent_func), f"{agent_method} should be callable"
            assert hasattr(
                mock_agent.stock_api, stock_api_method
            ), f"stock_api should have {stock_api_method}"
