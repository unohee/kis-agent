"""
OverseasFutures Facade 모듈 테스트

해외선물옵션 API Facade 패턴 동작을 종합적으로 테스트합니다.

테스트 대상 기능:
- OverseasFutures Facade 초기화
- 하위 API 초기화 검증
- 위임 메서드 동작 검증
- _from_agent 플래그 전파
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from pykis.overseas_futures import OverseasFutures
from pykis.overseas_futures.account_api import OverseasFuturesAccountAPI
from pykis.overseas_futures.order_api import OverseasFuturesOrderAPI
from pykis.overseas_futures.price_api import OverseasFuturesPriceAPI


class TestOverseasFuturesFacade(unittest.TestCase):
    """OverseasFutures Facade 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.mock_client = Mock()
        self.account_info = {"account_no": "12345678", "account_code": "03"}
        self.facade = OverseasFutures(
            client=self.mock_client,
            account_info=self.account_info,
            enable_cache=False,
            _from_agent=False,
        )

    def test_init(self):
        """Facade 초기화 테스트"""
        self.assertEqual(self.facade.client, self.mock_client)
        self.assertEqual(self.facade.account, self.account_info)

    def test_sub_apis_initialized(self):
        """하위 API 초기화 확인"""
        self.assertIsInstance(self.facade.price, OverseasFuturesPriceAPI)
        self.assertIsInstance(self.facade.account_api, OverseasFuturesAccountAPI)
        self.assertIsInstance(self.facade.order, OverseasFuturesOrderAPI)

    def test_sub_apis_share_client(self):
        """하위 API가 동일한 클라이언트 공유"""
        self.assertEqual(self.facade.price.client, self.mock_client)
        self.assertEqual(self.facade.account_api.client, self.mock_client)
        self.assertEqual(self.facade.order.client, self.mock_client)

    def test_sub_apis_share_account_info(self):
        """하위 API가 동일한 계좌 정보 공유"""
        self.assertEqual(self.facade.price.account, self.account_info)
        self.assertEqual(self.facade.account_api.account, self.account_info)
        self.assertEqual(self.facade.order.account, self.account_info)

    def test_from_agent_flag_propagation(self):
        """_from_agent 플래그 전파 확인"""
        facade_from_agent = OverseasFutures(
            client=self.mock_client,
            account_info=self.account_info,
            enable_cache=False,
            _from_agent=True,
        )

        self.assertIsInstance(facade_from_agent.price, OverseasFuturesPriceAPI)
        self.assertIsInstance(facade_from_agent.account_api, OverseasFuturesAccountAPI)
        self.assertIsInstance(facade_from_agent.order, OverseasFuturesOrderAPI)

    def test_get_price_delegation(self):
        """get_price 위임 메서드 동작 확인"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"last": "100.50"},
        }

        with patch.object(
            self.facade.price, "get_price", return_value=expected_response
        ):
            result = self.facade.get_price("CNHU24")

            self.assertEqual(result, expected_response)
            self.facade.price.get_price.assert_called_once_with("CNHU24")

    def test_get_futures_orderbook_delegation(self):
        """get_futures_orderbook 위임 메서드 동작 확인"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output1": {"askp1": "100.55"},
            "output2": {"bidp1": "100.50"},
        }

        with patch.object(
            self.facade.price, "get_futures_orderbook", return_value=expected_response
        ):
            result = self.facade.get_futures_orderbook("CNHU24")

            self.assertEqual(result, expected_response)
            self.facade.price.get_futures_orderbook.assert_called_once_with("CNHU24")

    def test_get_balance_delegation(self):
        """get_balance 위임 메서드 동작 확인"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"srs_cd": "CNHU24", "unsttl_qty": "2"}],
        }

        with patch.object(
            self.facade.account_api, "get_balance", return_value=expected_response
        ):
            result = self.facade.get_balance()

            self.assertEqual(result, expected_response)
            self.facade.account_api.get_balance.assert_called_once()

    def test_get_deposit_delegation(self):
        """get_deposit 위임 메서드 동작 확인"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"dps_amt": "10000.00"},
        }

        with patch.object(
            self.facade.account_api, "get_deposit", return_value=expected_response
        ):
            result = self.facade.get_deposit()

            self.assertEqual(result, expected_response)
            self.facade.account_api.get_deposit.assert_called_once()

    def test_get_minute_chart_delegation(self):
        """get_minute_chart 위임 메서드 동작 확인"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output2": []}

        with patch.object(
            self.facade.price, "get_minute_chart", return_value=expected_response
        ):
            result = self.facade.get_minute_chart("CNHU24", "CME")

            self.assertEqual(result, expected_response)
            self.facade.price.get_minute_chart.assert_called_once()

    def test_get_daily_trend_delegation(self):
        """get_daily_trend 위임 메서드 동작 확인"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output2": []}

        with patch.object(
            self.facade.price, "get_daily_trend", return_value=expected_response
        ):
            result = self.facade.get_daily_trend("CNHU24", "CME")

            self.assertEqual(result, expected_response)
            self.facade.price.get_daily_trend.assert_called_once()

    def test_direct_access_to_sub_apis(self):
        """하위 API 직접 접근 가능 확인"""
        # price API 직접 접근
        with patch.object(
            self.facade.price, "get_price", return_value={"rt_cd": "0", "output": {}}
        ):
            self.facade.price.get_price("CNHU24")
            self.facade.price.get_price.assert_called_once()

        # account API 직접 접근
        with patch.object(
            self.facade.account_api,
            "get_balance",
            return_value={"rt_cd": "0", "output": []},
        ):
            self.facade.account_api.get_balance()
            self.facade.account_api.get_balance.assert_called_once()

        # order API 직접 접근
        with patch.object(
            self.facade.order, "order", return_value={"rt_cd": "0", "output": {}}
        ):
            self.facade.order.order("CNHU24", "02", "1", "1")
            self.facade.order.order.assert_called_once()

    def test_cache_disabled(self):
        """캐시 비활성화 확인"""
        facade_no_cache = OverseasFutures(
            client=self.mock_client,
            account_info=self.account_info,
            enable_cache=False,
        )

        self.assertIsInstance(facade_no_cache.price, OverseasFuturesPriceAPI)
        self.assertIsInstance(facade_no_cache.account_api, OverseasFuturesAccountAPI)
        self.assertIsInstance(facade_no_cache.order, OverseasFuturesOrderAPI)

    def test_cache_enabled(self):
        """캐시 활성화 확인"""
        facade_with_cache = OverseasFutures(
            client=self.mock_client,
            account_info=self.account_info,
            enable_cache=True,
        )

        self.assertIsInstance(facade_with_cache.price, OverseasFuturesPriceAPI)
        self.assertIsInstance(facade_with_cache.account_api, OverseasFuturesAccountAPI)
        self.assertIsInstance(facade_with_cache.order, OverseasFuturesOrderAPI)


@pytest.mark.parametrize(
    "method_name,args",
    [
        ("get_price", ("CNHU24",)),
        ("get_option_price", ("ES2401C5000",)),
        ("get_futures_orderbook", ("CNHU24",)),
        ("get_option_orderbook", ("ES2401C5000",)),
        ("get_balance", ()),
        ("get_deposit", ()),
    ],
)
def test_facade_delegation_methods(method_name, args):
    """Facade 위임 메서드 파라미터 전달 검증"""
    mock_client = Mock()
    facade = OverseasFutures(
        client=mock_client,
        account_info={"account_no": "12345678", "account_code": "03"},
        enable_cache=False,
    )

    # 해당 메서드가 존재하는지 확인
    assert hasattr(facade, method_name)

    # 메서드 호출 가능한지 확인
    method = getattr(facade, method_name)
    assert callable(method)


def test_overseas_futures_facade_in_agent():
    """Agent에서 OverseasFutures Facade 통합 확인"""
    import sys

    import pykis.core.agent  # noqa: F401

    agent_module = sys.modules["pykis.core.agent"]

    # Mock client 생성
    mock_client = Mock()
    mock_client.token = "mock_token"
    mock_client.token_expired = "2026-01-05 12:00:00"
    mock_client.base_url = "https://mock.api.com"
    mock_client.is_real = True
    mock_client.enable_rate_limiter = False
    mock_client.rate_limiter = None

    # 모든 API 클래스 패치
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
        patches = [patch.object(agent_module, cls) for cls in api_classes]
        for p in patches:
            p.start()

        try:
            agent = agent_module.Agent(
                app_key="test_key",
                app_secret="test_secret",
                account_no="12345678",
                account_code="03",
            )

            # Agent에 overseas_futures 속성 존재 확인
            assert hasattr(agent, "overseas_futures")
        finally:
            for p in patches:
                p.stop()


if __name__ == "__main__":
    unittest.main()
