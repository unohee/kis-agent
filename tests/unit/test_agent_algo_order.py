"""Agent 파사드의 TWAP/VWAP 위임 테스트."""

from unittest.mock import patch

import pytest

from kis_agent.core.agent import Agent


class TestTwapDelegation:
    def test_arguments_are_forwarded_to_run_twap(self):
        with patch("kis_agent.execution.run_twap") as mock_run:
            mock_run.return_value = "result"
            agent = Agent.__new__(Agent)  # 인증 없이 파사드만 검증
            out = agent.twap_order(
                "005930",
                "buy",
                1000,
                duration_minutes=45,
                slices=9,
                order_type="00",
                price=70000,
                exchange="NXT",
                limit_price=71000,
                on_price_breach="abort",
                max_consecutive_failures=5,
                dry_run=True,
                restrict_to_session=False,
            )

        assert out == "result"
        kwargs = mock_run.call_args.kwargs
        assert mock_run.call_args.args[0] is agent
        assert kwargs["code"] == "005930"
        assert kwargs["side"] == "buy"
        assert kwargs["quantity"] == 1000
        assert kwargs["duration_minutes"] == 45
        assert kwargs["slices"] == 9
        assert kwargs["order_type"] == "00"
        assert kwargs["price"] == 70000
        assert kwargs["exchange"] == "NXT"
        assert kwargs["limit_price"] == 71000
        assert kwargs["on_price_breach"] == "abort"
        assert kwargs["max_consecutive_failures"] == 5
        assert kwargs["dry_run"] is True
        assert kwargs["restrict_to_session"] is False

    def test_defaults_match_the_documented_contract(self):
        with patch("kis_agent.execution.run_twap") as mock_run:
            agent = Agent.__new__(Agent)
            agent.twap_order("005930", "buy", 100)
        kwargs = mock_run.call_args.kwargs
        assert kwargs["duration_minutes"] == 30
        assert kwargs["slices"] == 6
        assert kwargs["order_type"] == "03"
        assert kwargs["exchange"] == "KRX"
        assert kwargs["restrict_to_session"] is True
        assert kwargs["dry_run"] is False


class TestVwapDelegation:
    def test_arguments_are_forwarded_to_run_vwap(self):
        with patch("kis_agent.execution.run_vwap") as mock_run:
            mock_run.return_value = "result"
            agent = Agent.__new__(Agent)
            out = agent.vwap_order(
                "005930", "sell", 500, duration_minutes=120, slices=12, profile_days=20
            )
        assert out == "result"
        kwargs = mock_run.call_args.kwargs
        assert kwargs["side"] == "sell"
        assert kwargs["quantity"] == 500
        assert kwargs["duration_minutes"] == 120
        assert kwargs["slices"] == 12
        assert kwargs["profile_days"] == 20

    def test_defaults_match_the_documented_contract(self):
        with patch("kis_agent.execution.run_vwap") as mock_run:
            agent = Agent.__new__(Agent)
            agent.vwap_order("005930", "buy", 100)
        kwargs = mock_run.call_args.kwargs
        assert kwargs["duration_minutes"] == 60
        assert kwargs["slices"] == 6
        assert kwargs["profile_days"] == 5


class TestFacadeSurface:
    @pytest.mark.parametrize("name", ["twap_order", "vwap_order"])
    def test_methods_are_real_attributes_not_getattr_fallbacks(self, name):
        # __getattr__ 위임이 아니라 실제 정의된 메서드여야 introspection이 동작한다.
        assert name in vars(Agent)
        assert Agent.__dict__[name].__doc__


class TestCreditDelegation:
    def test_credit_arguments_are_forwarded(self):
        with patch("kis_agent.execution.run_twap") as mock_run:
            agent = Agent.__new__(Agent)
            agent.twap_order(
                "005930",
                "buy",
                100,
                funding="credit",
                credit_type="22",
                loan_dt="20260821",
                credit_fallback_to_cash=True,
            )
        kwargs = mock_run.call_args.kwargs
        assert kwargs["funding"] == "credit"
        assert kwargs["credit_type"] == "22"
        assert kwargs["loan_dt"] == "20260821"
        assert kwargs["credit_fallback_to_cash"] is True

    @pytest.mark.parametrize("method", ["twap_order", "vwap_order"])
    def test_funding_defaults_to_cash_with_no_fallback(self, method):
        target = "run_twap" if method == "twap_order" else "run_vwap"
        with patch(f"kis_agent.execution.{target}") as mock_run:
            agent = Agent.__new__(Agent)
            getattr(agent, method)("005930", "buy", 100)
        kwargs = mock_run.call_args.kwargs
        assert kwargs["funding"] == "cash"
        assert kwargs["credit_type"] is None
        assert kwargs["credit_fallback_to_cash"] is False
