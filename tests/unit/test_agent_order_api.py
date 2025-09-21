"""
Agent 클래스의 새로 추가된 주문 관련 메서드들에 대한 단위 테스트
"""

import pytest
from unittest.mock import Mock, patch
from pykis.core.agent import Agent


class TestAgentOrderAPI:
    """Agent 클래스 주문 관련 메서드 테스트"""

    @pytest.fixture
    def mock_agent(self):
        """Mock Agent 생성"""
        with patch("pykis.core.agent.KISClient"), patch("pykis.core.agent.auth"), patch(
            "pykis.core.agent.read_token"
        ):

            agent = Agent(
                app_key="test_key",
                app_secret="test_secret",
                account_no="12345678",
                account_code="01",
            )

            # Mock stock_api 생성
            agent.stock_api = Mock()
            return agent

    def test_order_stock_cash_success(self, mock_agent):
        """Agent를 통한 현금 주문 성공 테스트"""
        # Given
        expected_response = {
            "rt_cd": "0",
            "msg1": "주문이 정상적으로 접수되었습니다.",
            "output": {"odno": "0000117057"},
        }
        mock_agent.stock_api.order_cash.return_value = expected_response

        # When
        result = mock_agent.order_stock_cash(
            ord_dv="buy", pdno="005930", ord_dvsn="00", ord_qty="1", ord_unpr="70000"
        )

        # Then
        assert result == expected_response
        mock_agent.stock_api.order_cash.assert_called_once_with(
            ord_dv="buy",
            pdno="005930",
            ord_dvsn="00",
            ord_qty="1",
            ord_unpr="70000",
            excg_id_dvsn_cd="KRX",
            sll_type="",
            cndt_pric="",
        )

    def test_order_stock_cash_with_options(self, mock_agent):
        """Agent를 통한 현금 주문 옵션 파라미터 테스트"""
        # Given
        expected_response = {"rt_cd": "0", "msg1": "성공"}
        mock_agent.stock_api.order_cash.return_value = expected_response

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
        mock_agent.stock_api.order_cash.assert_called_once_with(
            ord_dv="sell",
            pdno="005930",
            ord_dvsn="01",
            ord_qty="5",
            ord_unpr="0",
            excg_id_dvsn_cd="SOR",
            sll_type="01",
            cndt_pric="69000",
        )

    def test_order_stock_credit_success(self, mock_agent):
        """Agent를 통한 신용 주문 성공 테스트"""
        # Given
        expected_response = {
            "rt_cd": "0",
            "msg1": "신용주문이 정상적으로 접수되었습니다.",
            "output": {"odno": "0000117058"},
        }
        mock_agent.stock_api.order_credit.return_value = expected_response

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
        mock_agent.stock_api.order_credit.assert_called_once_with(
            ord_dv="buy",
            pdno="005930",
            crdt_type="21",
            loan_dt="20250911",
            ord_dvsn="00",
            ord_qty="1",
            ord_unpr="70000",
            excg_id_dvsn_cd="KRX",
            sll_type="",
            rsvn_ord_yn="N",
            emgc_ord_yn="",
            cndt_pric="",
        )

    def test_inquire_order_psbl_success(self, mock_agent):
        """Agent를 통한 매수가능조회 성공 테스트"""
        # Given
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "ord_psbl_cash": "1000000",
                "max_buy_qty": "14",
                "ord_psbl_qty": "14",
            },
        }
        mock_agent.stock_api.inquire_psbl_order.return_value = expected_response

        # When
        result = mock_agent.inquire_order_psbl("005930", "70000")

        # Then
        assert result == expected_response
        mock_agent.stock_api.inquire_psbl_order.assert_called_once_with(
            pdno="005930",
            ord_unpr="70000",
            ord_dvsn="00",
            cma_evlu_amt_icld_yn="Y",
            ovrs_icld_yn="Y",
        )

    def test_inquire_order_psbl_with_options(self, mock_agent):
        """Agent를 통한 매수가능조회 옵션 파라미터 테스트"""
        # Given
        expected_response = {"rt_cd": "0", "msg1": "성공"}
        mock_agent.stock_api.inquire_psbl_order.return_value = expected_response

        # When
        result = mock_agent.inquire_order_psbl(
            pdno="005930",
            ord_unpr="70000",
            ord_dvsn="01",
            cma_evlu_amt_icld_yn="N",
            ovrs_icld_yn="N",
        )

        # Then
        mock_agent.stock_api.inquire_psbl_order.assert_called_once_with(
            pdno="005930",
            ord_unpr="70000",
            ord_dvsn="01",
            cma_evlu_amt_icld_yn="N",
            ovrs_icld_yn="N",
        )

    def test_inquire_credit_order_psbl_success(self, mock_agent):
        """Agent를 통한 신용매수가능조회 성공 테스트"""
        # Given
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "crdt_buy_psbl_amt": "2000000",
                "max_buy_qty": "28",
                "crdt_psbl_qty": "28",
            },
        }
        mock_agent.stock_api.inquire_credit_psamount.return_value = expected_response

        # When
        result = mock_agent.inquire_credit_order_psbl("005930", "70000")

        # Then
        assert result == expected_response
        mock_agent.stock_api.inquire_credit_psamount.assert_called_once_with(
            pdno="005930",
            ord_unpr="70000",
            ord_dvsn="00",
            crdt_type="21",
            cma_evlu_amt_icld_yn="N",
            ovrs_icld_yn="N",
        )

    def test_inquire_credit_order_psbl_with_options(self, mock_agent):
        """Agent를 통한 신용매수가능조회 옵션 파라미터 테스트"""
        # Given
        expected_response = {"rt_cd": "0", "msg1": "성공"}
        mock_agent.stock_api.inquire_credit_psamount.return_value = expected_response

        # When
        result = mock_agent.inquire_credit_order_psbl(
            pdno="005930", ord_unpr="70000", ord_dvsn="01", crdt_type="23"
        )

        # Then
        mock_agent.stock_api.inquire_credit_psamount.assert_called_once_with(
            pdno="005930",
            ord_unpr="70000",
            ord_dvsn="01",
            crdt_type="23",
            cma_evlu_amt_icld_yn="N",
            ovrs_icld_yn="N",
        )

    def test_stock_api_error_propagation(self, mock_agent):
        """StockAPI 에러가 Agent로 전파되는지 테스트"""
        # Given
        mock_agent.stock_api.order_cash.side_effect = ValueError("Test error")

        # When & Then
        with pytest.raises(ValueError, match="Test error"):
            mock_agent.order_stock_cash("buy", "005930", "00", "1", "70000")

    def test_agent_method_delegation(self, mock_agent):
        """Agent 메서드가 StockAPI로 올바르게 위임되는지 테스트"""
        # Given
        methods_to_test = [
            ("order_stock_cash", "order_cash"),
            ("order_stock_credit", "order_credit"),
            ("inquire_order_psbl", "inquire_psbl_order"),
            ("inquire_credit_order_psbl", "inquire_credit_psamount"),
        ]

        for agent_method, stock_api_method in methods_to_test:
            # When
            agent_func = getattr(mock_agent, agent_method)
            stock_api_func = getattr(mock_agent.stock_api, stock_api_method)

            # Then
            assert callable(agent_func), f"{agent_method} should be callable"
            assert hasattr(
                mock_agent.stock_api, stock_api_method
            ), f"stock_api should have {stock_api_method}"
