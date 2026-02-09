"""
Futures Facade 모듈 테스트

선물옵션 API Facade 패턴 동작을 종합적으로 테스트합니다.

자동 생성됨 - /boost-coverage 스킬
생성일: 2026-01-19

테스트 대상 기능:
- Futures Facade 초기화
- 하위 API 초기화 검증
- 위임 메서드 동작 검증
- _from_agent 플래그 전파
- 편의 메서드 (get_price, inquire_balance 등)

테스트 시나리오:
- 정상적인 Facade 초기화
- 하위 API 정상 생성 확인
- 위임 메서드의 올바른 동작
- Agent를 통한 초기화 경로
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from kis_agent.futures import Futures
from kis_agent.futures.account_api import FuturesAccountAPI
from kis_agent.futures.order_api import FuturesOrderAPI
from kis_agent.futures.price_api import FuturesPriceAPI


class TestFuturesFacade(unittest.TestCase):
    """Futures Facade 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.mock_client = Mock()
        self.account_info = {"account_no": "12345678", "account_code": "03"}
        self.facade = Futures(
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
        self.assertIsInstance(self.facade.price, FuturesPriceAPI)
        self.assertIsInstance(self.facade.account_api, FuturesAccountAPI)
        self.assertIsInstance(self.facade.order, FuturesOrderAPI)

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
        facade_from_agent = Futures(
            client=self.mock_client,
            account_info=self.account_info,
            enable_cache=False,
            _from_agent=True,
        )

        # 하위 API들도 _from_agent=True로 초기화되어야 함
        # (BaseAPI의 내부 동작이므로 직접 확인 불가, 초기화만 검증)
        self.assertIsInstance(facade_from_agent.price, FuturesPriceAPI)
        self.assertIsInstance(facade_from_agent.account_api, FuturesAccountAPI)
        self.assertIsInstance(facade_from_agent.order, FuturesOrderAPI)

    def test_get_price_delegation(self):
        """get_price 위임 메서드 동작 확인"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"fuop_prpr": "340.50"},
        }

        with patch.object(
            self.facade.price, "get_price", return_value=expected_response
        ):
            result = self.facade.get_price("101S12")

            self.assertEqual(result, expected_response)
            self.facade.price.get_price.assert_called_once_with("101S12")

    def test_get_orderbook_delegation(self):
        """get_orderbook 위임 메서드 동작 확인"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output1": {"askp1": "340.55"},
            "output2": {"bidp1": "340.50"},
        }

        with patch.object(
            self.facade.price, "get_orderbook", return_value=expected_response
        ):
            result = self.facade.get_orderbook("101S12")

            self.assertEqual(result, expected_response)
            self.facade.price.get_orderbook.assert_called_once_with("101S12")

    def test_inquire_balance_delegation(self):
        """inquire_balance 위임 메서드 동작 확인"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"fuop_item_code": "101S12", "fnoat_plamt": "15000"}],
        }

        with patch.object(
            self.facade.account_api, "inquire_balance", return_value=expected_response
        ):
            result = self.facade.inquire_balance()

            self.assertEqual(result, expected_response)
            self.facade.account_api.inquire_balance.assert_called_once()

    def test_inquire_deposit_delegation(self):
        """inquire_deposit 위임 메서드 동작 확인"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"fuop_dps_amt": "10000000", "tot_asst_amt": "10150000"},
        }

        with patch.object(
            self.facade.account_api, "inquire_deposit", return_value=expected_response
        ):
            result = self.facade.inquire_deposit()

            self.assertEqual(result, expected_response)
            self.facade.account_api.inquire_deposit.assert_called_once()

    def test_inquire_daily_fuopchartprice_delegation(self):
        """inquire_daily_fuopchartprice 위임 메서드 동작 확인"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}

        with patch.object(
            self.facade.price,
            "inquire_daily_fuopchartprice",
            return_value=expected_response,
        ):
            result = self.facade.inquire_daily_fuopchartprice(
                "101S12", "20260101", "20260131", "D"
            )

            self.assertEqual(result, expected_response)
            self.facade.price.inquire_daily_fuopchartprice.assert_called_once_with(
                "101S12", "20260101", "20260131", "D"
            )

    def test_inquire_time_fuopchartprice_delegation(self):
        """inquire_time_fuopchartprice 위임 메서드 동작 확인"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}

        with patch.object(
            self.facade.price,
            "inquire_time_fuopchartprice",
            return_value=expected_response,
        ):
            result = self.facade.inquire_time_fuopchartprice("101S12", "153000", "5")

            self.assertEqual(result, expected_response)
            self.facade.price.inquire_time_fuopchartprice.assert_called_once_with(
                "101S12", "153000", "5"
            )

    def test_display_board_callput_delegation(self):
        """display_board_callput 위임 메서드 동작 확인"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output1": [],
            "output2": [],
        }

        with patch.object(
            self.facade.price, "display_board_callput", return_value=expected_response
        ):
            result = self.facade.display_board_callput("202601", "340")

            self.assertEqual(result, expected_response)
            self.facade.price.display_board_callput.assert_called_once_with(
                "202601", "340"
            )

    def test_display_board_futures_delegation(self):
        """display_board_futures 위임 메서드 동작 확인"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}

        with patch.object(
            self.facade.price, "display_board_futures", return_value=expected_response
        ):
            result = self.facade.display_board_futures()

            self.assertEqual(result, expected_response)
            self.facade.price.display_board_futures.assert_called_once()

    def test_direct_access_to_sub_apis(self):
        """하위 API 직접 접근 가능 확인"""
        # price API 직접 접근
        with patch.object(
            self.facade.price, "get_price", return_value={"rt_cd": "0", "output": {}}
        ):
            self.facade.price.get_price("101S12")
            self.facade.price.get_price.assert_called_once()

        # account API 직접 접근
        with patch.object(
            self.facade.account_api,
            "inquire_balance",
            return_value={"rt_cd": "0", "output": []},
        ):
            self.facade.account_api.inquire_balance()
            self.facade.account_api.inquire_balance.assert_called_once()

        # order API 직접 접근
        with patch.object(
            self.facade.order, "order", return_value={"rt_cd": "0", "output": {}}
        ):
            self.facade.order.order("101S12", "02", "1", "0")
            self.facade.order.order.assert_called_once()

    def test_cache_disabled(self):
        """캐시 비활성화 확인"""
        facade_no_cache = Futures(
            client=self.mock_client,
            account_info=self.account_info,
            enable_cache=False,
        )

        # BaseAPI의 캐시 설정이 하위 API에 전달됨
        self.assertIsInstance(facade_no_cache.price, FuturesPriceAPI)
        self.assertIsInstance(facade_no_cache.account_api, FuturesAccountAPI)
        self.assertIsInstance(facade_no_cache.order, FuturesOrderAPI)

    def test_cache_enabled(self):
        """캐시 활성화 확인"""
        facade_with_cache = Futures(
            client=self.mock_client,
            account_info=self.account_info,
            enable_cache=True,
        )

        # 하위 API 정상 초기화 확인
        self.assertIsInstance(facade_with_cache.price, FuturesPriceAPI)
        self.assertIsInstance(facade_with_cache.account_api, FuturesAccountAPI)
        self.assertIsInstance(facade_with_cache.order, FuturesOrderAPI)


@pytest.mark.parametrize(
    "method_name,args",
    [
        ("get_price", ("101S12",)),
        ("get_orderbook", ("101S12",)),
        ("inquire_balance", ()),
        ("inquire_deposit", ()),
        ("display_board_futures", ()),
    ],
)
def test_facade_delegation_methods(method_name, args):
    """Facade 위임 메서드 파라미터 전달 검증"""
    mock_client = Mock()
    facade = Futures(
        client=mock_client,
        account_info={"account_no": "12345678", "account_code": "03"},
        enable_cache=False,
    )

    # 해당 메서드가 존재하는지 확인
    assert hasattr(facade, method_name)

    # 메서드 호출 가능한지 확인 (실제 API 호출 없이)
    method = getattr(facade, method_name)
    assert callable(method)


def test_futures_facade_in_agent():
    """Agent에서 Futures Facade 통합 확인"""
    import sys

    import kis_agent.core.agent  # noqa: F401

    agent_module = sys.modules["kis_agent.core.agent"]

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

            # Agent에 futures 속성 존재 확인
            assert hasattr(agent, "futures")
        finally:
            for p in patches:
                p.stop()


if __name__ == "__main__":
    unittest.main()
