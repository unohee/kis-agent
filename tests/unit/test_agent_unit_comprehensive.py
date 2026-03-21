"""
Agent 클래스 포괄적 단위 테스트

INT-380: core/agent.py 커버리지 개선 (32% → 70%)
생성일: 2026-01-04
수정일: 2026-02-06 - mock 패치 경로 수정 (read_token 제거)
"""

import logging
import sys
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest

# agent 모듈을 명시적으로 import
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


def patch_all_apis(agent_module, mocks=None):
    """Agent 생성에 필요한 모든 API를 패치하는 컨텍스트 매니저 스택을 반환합니다.

    Args:
        agent_module: kis_agent.core.agent 모듈
        mocks: 특정 API에 대한 mock 객체를 지정하는 딕셔너리 (선택사항)
               예: {"StockAPI": mock_stock_api}

    Returns:
        ExitStack: 모든 패치가 적용된 컨텍스트 매니저 스택
    """
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


class TestAgentInit:
    """Agent 초기화 테스트"""

    def test_init_missing_required_params(self):
        """필수 매개변수 누락 시 ValueError 발생 (L151-166)"""
        agent_module = get_agent_module()

        with pytest.raises(ValueError) as exc_info:
            agent_module.Agent(
                app_key="", app_secret="", account_no="", account_code=""
            )

        assert "필수 매개변수가 누락되었습니다" in str(exc_info.value)

    def test_init_missing_app_key_only(self):
        """app_key만 누락"""
        agent_module = get_agent_module()

        with pytest.raises(ValueError):
            agent_module.Agent(
                app_key="",
                app_secret="secret",
                account_no="12345678",
                account_code="01",
            )

    def test_init_with_all_params(self):
        """모든 필수 매개변수 제공 시 정상 초기화 (L147-231)"""
        agent_module = get_agent_module()

        with patch.object(agent_module, "KISConfig"), patch.object(
            agent_module, "KISClient"
        ) as mock_client_class:
            mock_client = MockKISClient()
            mock_client_class.return_value = mock_client

            with patch_all_apis(agent_module):
                agent = agent_module.Agent(
                    app_key="TEST_KEY",
                    app_secret="TEST_SECRET",
                    account_no="12345678",
                    account_code="01",
                )

                assert agent.account_info["CANO"] == "12345678"
                assert agent.account_info["ACNT_PRDT_CD"] == "01"
                assert agent.my_acct == agent.account_info

    def test_init_with_custom_client(self):
        """커스텀 client 전달 시 사용"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()

        with patch_all_apis(agent_module):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
            )

            assert agent.client == mock_client

    def test_init_with_custom_account_info(self):
        """커스텀 account_info 전달"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()
        custom_account_info = {"CANO": "CUSTOM", "ACNT_PRDT_CD": "99"}

        with patch_all_apis(agent_module):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
                account_info=custom_account_info,
            )

            assert agent.account_info == custom_account_info

    def test_init_with_rate_limiter_disabled(self):
        """Rate Limiter 비활성화"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()

        with patch_all_apis(agent_module):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
                enable_rate_limiter=False,
            )

            assert agent.rate_limiter is None

    def test_init_with_custom_rate_limiter(self):
        """커스텀 Rate Limiter 전달 (L172-174)"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()
        mock_rate_limiter = MagicMock()

        with patch_all_apis(agent_module):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
                enable_rate_limiter=True,
                rate_limiter=mock_rate_limiter,
            )

            assert agent.rate_limiter == mock_rate_limiter

    def test_init_with_rate_limiter_config(self):
        """Rate Limiter 설정 전달 (L186-190)"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()
        custom_config = {"requests_per_second": 10, "requests_per_minute": 500}

        with patch.object(agent_module, "get_global_rate_limiter") as mock_get_limiter:
            mock_limiter = MagicMock()
            mock_get_limiter.return_value = mock_limiter

            with patch_all_apis(agent_module):
                agent = agent_module.Agent(
                    app_key="KEY",
                    app_secret="SECRET",
                    account_no="12345",
                    account_code="01",
                    client=mock_client,
                    rate_limiter_config=custom_config,
                )

                # get_global_rate_limiter가 custom_config로 호출됨
                mock_get_limiter.assert_called_once()
                call_kwargs = mock_get_limiter.call_args[1]
                assert call_kwargs["requests_per_second"] == 10
                assert call_kwargs["requests_per_minute"] == 500


class TestWebsocket:
    """websocket 메서드 테스트 (L276-306)"""

    def test_websocket_creates_kis_websocket(self):
        """websocket() 메서드가 KisWebSocket 인스턴스 반환"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()
        mock_ws = MagicMock()

        with patch.object(agent_module, "KisWebSocket") as mock_ws_class:
            mock_ws_class.return_value = mock_ws

            with patch_all_apis(agent_module):
                agent = agent_module.Agent(
                    app_key="KEY",
                    app_secret="SECRET",
                    account_no="12345",
                    account_code="01",
                    client=mock_client,
                )

                ws = agent.websocket(
                    stock_codes=["005930", "035420"],
                    enable_index=True,
                    enable_program_trading=True,
                    enable_ask_bid=False,
                )

                assert ws == mock_ws
                mock_ws_class.assert_called_once()


class TestGetConditionStocks:
    """get_condition_stocks 테스트 (L333-353)"""

    def test_get_condition_stocks_success(self):
        """조건검색 결과 조회 성공"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()
        mock_result = [{"stock_code": "005930"}, {"stock_code": "035420"}]

        with patch_all_apis(agent_module):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
            )

            # ConditionAPI를 모의
            with patch("kis_agent.stock.condition.ConditionAPI") as mock_condition:
                mock_condition_instance = MagicMock()
                mock_condition_instance.get_condition_stocks.return_value = mock_result
                mock_condition.return_value = mock_condition_instance

                result = agent.get_condition_stocks(user_id="test", seq=1)
                assert result == mock_result

    def test_get_condition_stocks_failure(self, caplog):
        """조건검색 결과 조회 실패 시 None 반환"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()

        with patch_all_apis(agent_module):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
            )

            # ConditionAPI에서 예외 발생
            with patch("kis_agent.stock.condition.ConditionAPI") as mock_condition:
                mock_condition.side_effect = Exception("API 오류")

                with caplog.at_level(logging.ERROR):
                    result = agent.get_condition_stocks()

                assert result is None


class TestGetTopGainers:
    """get_top_gainers 테스트 (L355-376)"""

    def test_get_top_gainers_success(self):
        """상승률 상위 종목 조회 성공"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()
        mock_result = [{"hts_kor_isnm": "삼성전자", "prdy_ctrt": "5.0"}]

        mock_stock_api = MagicMock()
        mock_stock_api.get_market_fluctuation.return_value = mock_result

        with patch_all_apis(agent_module, {"StockAPI": mock_stock_api}):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
            )

            result = agent.get_top_gainers()
            assert result == mock_result

    def test_get_top_gainers_failure(self, caplog):
        """상승률 상위 종목 조회 실패 시 빈 리스트 반환"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()

        mock_stock_api = MagicMock()
        mock_stock_api.get_market_fluctuation.side_effect = Exception("API 오류")

        with patch_all_apis(agent_module, {"StockAPI": mock_stock_api}):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
            )

            with caplog.at_level(logging.ERROR):
                result = agent.get_top_gainers()

            assert result == []


class TestOrderStockCash:
    """order_stock_cash 테스트 (L380-467)"""

    def test_order_stock_cash_buy(self):
        """현금 매수 주문"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()
        mock_order_result = {"rt_cd": "0", "output": {"ODNO": "12345"}}

        mock_account_api = MagicMock()
        mock_account_api.order_cash.return_value = mock_order_result

        with patch_all_apis(agent_module, {"AccountAPI": mock_account_api}):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
            )

            result = agent.order_stock_cash(
                ord_dv="buy",
                pdno="005930",
                ord_dvsn="00",
                ord_qty="1",
                ord_unpr="70000",
            )

            assert result == mock_order_result
            mock_account_api.order_cash.assert_called_once_with(
                pdno="005930",
                qty=1,
                price=70000,
                buy_sell="BUY",
                order_type="00",
                exchange="KRX",
            )

    def test_order_stock_cash_sell(self):
        """현금 매도 주문"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()
        mock_order_result = {"rt_cd": "0", "output": {"ODNO": "12346"}}

        mock_account_api = MagicMock()
        mock_account_api.order_cash.return_value = mock_order_result

        with patch_all_apis(agent_module, {"AccountAPI": mock_account_api}):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
            )

            result = agent.order_stock_cash(
                ord_dv="SELL",  # 대문자도 허용
                pdno="035720",
                ord_dvsn="01",
                ord_qty="10",
                ord_unpr="0",
            )

            assert result == mock_order_result
            mock_account_api.order_cash.assert_called_once_with(
                pdno="035720",
                qty=10,
                price=0,
                buy_sell="SELL",
                order_type="01",
                exchange="KRX",
            )


class TestOrderStockCredit:
    """order_stock_credit 테스트 (L469-549)"""

    def test_order_stock_credit_buy(self):
        """신용 매수 주문"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()
        mock_order_result = {"rt_cd": "0", "output": {"ODNO": "99999"}}

        mock_account_api = MagicMock()
        mock_account_api.order_credit_buy.return_value = mock_order_result

        with patch_all_apis(agent_module, {"AccountAPI": mock_account_api}):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
            )

            result = agent.order_stock_credit(
                ord_dv="buy",
                pdno="005930",
                crdt_type="21",
                ord_dvsn="00",
                ord_qty="1",
                ord_unpr="70000",
            )

            assert result == mock_order_result
            mock_account_api.order_credit_buy.assert_called_once()

    def test_order_stock_credit_sell(self):
        """신용 매도 주문"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()
        mock_order_result = {"rt_cd": "0", "output": {"ODNO": "88888"}}

        mock_account_api = MagicMock()
        mock_account_api.order_credit_sell.return_value = mock_order_result

        with patch_all_apis(agent_module, {"AccountAPI": mock_account_api}):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
            )

            result = agent.order_stock_credit(
                ord_dv="sell",
                pdno="005930",
                crdt_type="25",
                ord_dvsn="01",
                ord_qty="1",
                ord_unpr="0",
            )

            assert result == mock_order_result
            mock_account_api.order_credit_sell.assert_called_once()


class TestRateLimiterMethods:
    """Rate Limiter 관리 메서드 테스트 (L555-649)"""

    def _create_agent_with_rate_limiter(self, agent_module, mock_rate_limiter=None):
        """테스트용 Agent 생성 헬퍼"""
        mock_client = MockKISClient()

        with patch_all_apis(agent_module):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
                enable_rate_limiter=mock_rate_limiter is not None,
                rate_limiter=mock_rate_limiter,
            )
            return agent

    def test_get_rate_limiter_status_with_limiter(self):
        """Rate Limiter 상태 조회 (활성화된 경우)"""
        agent_module = get_agent_module()

        mock_rate_limiter = MagicMock()
        mock_rate_limiter.get_current_rate.return_value = {
            "requests_per_second": 5,
            "throttled_count": 0,
        }

        agent = self._create_agent_with_rate_limiter(agent_module, mock_rate_limiter)
        status = agent.get_rate_limiter_status()

        assert status["requests_per_second"] == 5
        mock_rate_limiter.get_current_rate.assert_called_once()

    def test_get_rate_limiter_status_without_limiter(self):
        """Rate Limiter 상태 조회 (비활성화된 경우)"""
        agent_module = get_agent_module()

        agent = self._create_agent_with_rate_limiter(agent_module, None)
        status = agent.get_rate_limiter_status()

        assert status is None

    def test_set_rate_limits_with_limiter(self, caplog):
        """Rate Limiter 제한 값 변경 (L581-614)"""
        agent_module = get_agent_module()

        mock_rate_limiter = MagicMock()

        agent = self._create_agent_with_rate_limiter(agent_module, mock_rate_limiter)

        with caplog.at_level(logging.INFO):
            agent.set_rate_limits(
                requests_per_second=10, requests_per_minute=500, min_interval_ms=100
            )

        mock_rate_limiter.set_limits.assert_called_once_with(
            requests_per_second=10, requests_per_minute=500, min_interval_ms=100
        )

    def test_set_rate_limits_without_limiter(self, caplog):
        """Rate Limiter 비활성 시 경고 로그"""
        agent_module = get_agent_module()

        agent = self._create_agent_with_rate_limiter(agent_module, None)

        with caplog.at_level(logging.WARNING):
            agent.set_rate_limits(requests_per_second=10)

        assert "비활성화 상태" in caplog.text

    def test_reset_rate_limiter_with_limiter(self, caplog):
        """Rate Limiter 초기화 (L616-631)"""
        agent_module = get_agent_module()

        mock_rate_limiter = MagicMock()

        agent = self._create_agent_with_rate_limiter(agent_module, mock_rate_limiter)

        with caplog.at_level(logging.INFO):
            agent.reset_rate_limiter()

        mock_rate_limiter.reset.assert_called_once()
        assert "초기화 완료" in caplog.text

    def test_reset_rate_limiter_without_limiter(self, caplog):
        """Rate Limiter 비활성 시 경고"""
        agent_module = get_agent_module()

        agent = self._create_agent_with_rate_limiter(agent_module, None)

        with caplog.at_level(logging.WARNING):
            agent.reset_rate_limiter()

        assert "비활성화 상태" in caplog.text

    def test_enable_adaptive_rate_limiting(self, caplog):
        """적응형 속도 조절 활성화/비활성화 (L633-649)"""
        agent_module = get_agent_module()

        mock_rate_limiter = MagicMock()
        mock_rate_limiter.enable_adaptive = False

        agent = self._create_agent_with_rate_limiter(agent_module, mock_rate_limiter)

        with caplog.at_level(logging.INFO):
            agent.enable_adaptive_rate_limiting(True)

        assert mock_rate_limiter.enable_adaptive is True
        assert "활성화" in caplog.text

        with caplog.at_level(logging.INFO):
            agent.enable_adaptive_rate_limiting(False)

        assert mock_rate_limiter.enable_adaptive is False


class TestSectorCodeMethods:
    """업종코드 관련 메서드 테스트 (L659-785)"""

    def test_get_sector_codes(self):
        """get_sector_codes 테스트 (L659-699)"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()

        with patch.object(agent_module, "get_sector_codes") as mock_get_codes:
            mock_get_codes.return_value = {"0001": "종합"}

            with patch_all_apis(agent_module):
                agent = agent_module.Agent(
                    app_key="KEY",
                    app_secret="SECRET",
                    account_no="12345",
                    account_code="01",
                    client=mock_client,
                )

                result = agent.get_sector_codes(as_dict=True)
                assert result == {"0001": "종합"}

    def test_sector_codes_constants(self):
        """sector_codes_constants 프로퍼티 테스트 (L732-785)"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()

        with patch_all_apis(agent_module):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
            )

            codes = agent.sector_codes_constants
            assert isinstance(codes, dict)
            # SECTOR_CODES가 반환됨
            assert codes == agent_module.SECTOR_CODES


class TestGetAttr:
    """__getattr__ 위임 테스트 (L791-814)"""

    def test_getattr_delegates_to_stock_api(self):
        """StockAPI로 위임"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()

        mock_stock_api = MagicMock()
        mock_stock_api.some_stock_method.return_value = "stock_result"

        with patch_all_apis(agent_module, {"StockAPI": mock_stock_api}):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
            )

            # stock_api에 있는 메서드 호출
            result = agent.some_stock_method()
            assert result == "stock_result"

    def test_getattr_raises_attribute_error(self):
        """존재하지 않는 속성 접근 시 AttributeError"""
        agent_module = get_agent_module()
        mock_client = MockKISClient()

        # spec을 지정하여 실제 API 클래스처럼 동작하도록 함
        # MagicMock은 모든 속성에 응답하므로, spec=[]로 빈 인터페이스 지정
        mocks = {
            "AccountAPI": MagicMock(spec=[]),
            "StockAPI": MagicMock(spec=[]),
            "StockInvestorAPI": MagicMock(spec=[]),
            "ProgramTradeAPI": MagicMock(spec=[]),
            "StockMarketAPI": MagicMock(spec=[]),
            "InterestStockAPI": MagicMock(spec=[]),
            "OverseasStockAPI": MagicMock(spec=[]),
            "Futures": MagicMock(spec=[]),
            "OverseasFutures": MagicMock(spec=[]),
        }

        with patch_all_apis(agent_module, mocks):
            agent = agent_module.Agent(
                app_key="KEY",
                app_secret="SECRET",
                account_no="12345",
                account_code="01",
                client=mock_client,
            )

            with pytest.raises(AttributeError) as exc_info:
                agent.nonexistent_method()

            assert "nonexistent_method" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
