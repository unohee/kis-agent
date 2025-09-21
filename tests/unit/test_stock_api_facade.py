"""
Stock API Facade 모듈 테스트

Facade Pattern이 적용된 주식 API 통합 인터페이스를 테스트합니다.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest

from pykis.stock.api_facade import StockAPI, StockAPIFacade
from pykis.core.client import KISClient


class TestStockAPIFacade(unittest.TestCase):
    """StockAPI Facade 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"account_no": "12345", "account_code": "01"}

        with patch("pykis.stock.api_facade.StockPriceAPI"), patch(
            "pykis.stock.api_facade.StockMarketAPI"
        ), patch("pykis.stock.api_facade.StockInvestorAPI"):

            self.api = StockAPI(
                client=self.mock_client,
                account_info=self.account_info,
                enable_cache=False,
            )

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.api.client, self.mock_client)
        self.assertEqual(self.api.account, self.account_info)

        # 하위 시스템이 생성되었는지 확인
        self.assertIsNotNone(self.api.price_api)
        self.assertIsNotNone(self.api.market_api)
        self.assertIsNotNone(self.api.investor_api)

    def test_init_without_account_info(self):
        """계좌 정보 없이 초기화"""
        with patch("pykis.stock.api_facade.StockPriceAPI"), patch(
            "pykis.stock.api_facade.StockMarketAPI"
        ), patch("pykis.stock.api_facade.StockInvestorAPI"):

            api = StockAPI(client=self.mock_client)
            self.assertEqual(api.client, self.mock_client)
            self.assertIsNone(api.account)

    def test_get_stock_price_delegation(self):
        """get_stock_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"stck_prpr": "70000"}}
        self.api.price_api.get_stock_price = Mock(return_value=expected_result)

        result = self.api.get_stock_price("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_stock_price.assert_called_once_with("005930")

    def test_get_daily_price_delegation(self):
        """get_daily_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_bsop_date": "20231215"}]}
        self.api.price_api.get_daily_price = Mock(return_value=expected_result)

        result = self.api.get_daily_price("005930", period="W", org_adj_prc="0")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_daily_price.assert_called_once_with("005930", "W", "0")

    def test_get_daily_price_default_params(self):
        """get_daily_price 기본 파라미터 테스트"""
        expected_result = {"rt_cd": "0", "output": []}
        self.api.price_api.get_daily_price = Mock(return_value=expected_result)

        result = self.api.get_daily_price("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_daily_price.assert_called_once_with("005930", "D", "1")

    def test_get_orderbook_delegation(self):
        """get_orderbook 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"askp1": "70100"}}
        self.api.price_api.get_orderbook = Mock(return_value=expected_result)

        result = self.api.get_orderbook("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_orderbook.assert_called_once_with("005930")

    def test_get_orderbook_raw_delegation(self):
        """get_orderbook_raw 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"raw": "data"}}
        self.api.price_api.get_orderbook_raw = Mock(return_value=expected_result)

        result = self.api.get_orderbook_raw("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_orderbook_raw.assert_called_once_with("005930")

    def test_get_minute_price_delegation(self):
        """get_minute_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_cntg_hour": "153000"}]}
        self.api.price_api.get_minute_price = Mock(return_value=expected_result)

        result = self.api.get_minute_price("005930", hour="120000")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_minute_price.assert_called_once_with("005930", "120000")

    def test_get_minute_price_default_hour(self):
        """get_minute_price 기본 시간 테스트"""
        expected_result = {"rt_cd": "0", "output": []}
        self.api.price_api.get_minute_price = Mock(return_value=expected_result)

        result = self.api.get_minute_price("005930")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_minute_price.assert_called_once_with("005930", "153000")

    def test_get_daily_minute_price_delegation(self):
        """get_daily_minute_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"stck_bsop_date": "20231215"}]}
        self.api.price_api.get_daily_minute_price = Mock(return_value=expected_result)

        result = self.api.get_daily_minute_price("005930", "20231215", hour="090000")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_daily_minute_price.assert_called_once_with(
            "005930", "20231215", "090000"
        )

    def test_get_daily_minute_price_default_hour(self):
        """get_daily_minute_price 기본 시간 테스트"""
        expected_result = {"rt_cd": "0", "output": []}
        self.api.price_api.get_daily_minute_price = Mock(return_value=expected_result)

        result = self.api.get_daily_minute_price("005930", "20231215")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_daily_minute_price.assert_called_once_with(
            "005930", "20231215", "153000"
        )

    def test_get_market_fluctuation_delegation(self):
        """get_market_fluctuation 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"market_data": "test"}}
        self.api.market_api.get_market_fluctuation = Mock(return_value=expected_result)

        result = self.api.get_market_fluctuation()

        self.assertEqual(result, expected_result)
        self.api.market_api.get_market_fluctuation.assert_called_once()

    def test_get_market_rankings_delegation(self):
        """get_market_rankings 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"rank": 1}]}
        self.api.market_api.get_market_rankings = Mock(return_value=expected_result)

        result = self.api.get_market_rankings(volume=10000000)

        self.assertEqual(result, expected_result)
        self.api.market_api.get_market_rankings.assert_called_once_with(10000000)

    def test_get_market_rankings_default_volume(self):
        """get_market_rankings 기본 거래량 테스트"""
        expected_result = {"rt_cd": "0", "output": []}
        self.api.market_api.get_market_rankings = Mock(return_value=expected_result)

        result = self.api.get_market_rankings()

        self.assertEqual(result, expected_result)
        self.api.market_api.get_market_rankings.assert_called_once_with(5000000)

    def test_get_volume_power_delegation(self):
        """get_volume_power 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"code": "005930"}]}
        self.api.market_api.get_volume_power = Mock(return_value=expected_result)

        result = self.api.get_volume_power(volume=1000000)

        self.assertEqual(result, expected_result)
        self.api.market_api.get_volume_power.assert_called_once_with(1000000)

    def test_get_volume_power_default_volume(self):
        """get_volume_power 기본 거래량 테스트"""
        expected_result = {"rt_cd": "0", "output": []}
        self.api.market_api.get_volume_power = Mock(return_value=expected_result)

        result = self.api.get_volume_power()

        self.assertEqual(result, expected_result)
        self.api.market_api.get_volume_power.assert_called_once_with(0)

    def test_get_stock_info_delegation(self):
        """get_stock_info 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"name": "삼성전자"}}
        self.api.market_api.get_stock_info = Mock(return_value=expected_result)

        result = self.api.get_stock_info("005930")

        self.assertEqual(result, expected_result)
        self.api.market_api.get_stock_info.assert_called_once_with("005930")

    def test_get_stock_investor_delegation(self):
        """get_stock_investor 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"investor_data": "test"}}
        self.api.investor_api.get_stock_investor = Mock(return_value=expected_result)

        result = self.api.get_stock_investor(
            ticker="005930", retries=5, force_refresh=True
        )

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_stock_investor.assert_called_once_with(
            "005930", 5, True
        )

    def test_get_stock_investor_default_params(self):
        """get_stock_investor 기본 파라미터 테스트"""
        expected_result = {"rt_cd": "0", "output": {}}
        self.api.investor_api.get_stock_investor = Mock(return_value=expected_result)

        result = self.api.get_stock_investor()

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_stock_investor.assert_called_once_with("", 10, False)

    def test_get_stock_member_delegation(self):
        """get_stock_member 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"member_data": "test"}}
        self.api.investor_api.get_stock_member = Mock(return_value=expected_result)

        result = self.api.get_stock_member("005930", retries=5)

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_stock_member.assert_called_once_with("005930", 5)

    def test_get_stock_member_default_retries(self):
        """get_stock_member 기본 재시도 횟수 테스트"""
        expected_result = {"rt_cd": "0", "output": {}}
        self.api.investor_api.get_stock_member = Mock(return_value=expected_result)

        result = self.api.get_stock_member("005930")

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_stock_member.assert_called_once_with("005930", 10)

    def test_get_member_transaction_delegation(self):
        """get_member_transaction 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"transaction_data": "test"}}
        self.api.investor_api.get_member_transaction = Mock(
            return_value=expected_result
        )

        result = self.api.get_member_transaction("005930", "001")

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_member_transaction.assert_called_once_with(
            "005930", "001"
        )

    def test_get_frgnmem_pchs_trend_delegation(self):
        """get_frgnmem_pchs_trend 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"trend_data": "test"}}
        self.api.investor_api.get_frgnmem_pchs_trend = Mock(
            return_value=expected_result
        )

        result = self.api.get_frgnmem_pchs_trend("005930", "20231215")

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_frgnmem_pchs_trend.assert_called_once_with(
            "005930", "20231215"
        )

    def test_get_foreign_broker_net_buy_delegation(self):
        """get_foreign_broker_net_buy 메서드 위임 테스트"""
        expected_result = ("broker_data", {"net_buy": 1000})
        self.api.investor_api.get_foreign_broker_net_buy = Mock(
            return_value=expected_result
        )

        foreign_brokers = ["morgan", "goldman"]
        result = self.api.get_foreign_broker_net_buy(
            "005930", foreign_brokers, "20231215"
        )

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_foreign_broker_net_buy.assert_called_once_with(
            "005930", foreign_brokers, "20231215"
        )

    def test_get_foreign_broker_net_buy_default_params(self):
        """get_foreign_broker_net_buy 기본 파라미터 테스트"""
        expected_result = ("data", {})
        self.api.investor_api.get_foreign_broker_net_buy = Mock(
            return_value=expected_result
        )

        result = self.api.get_foreign_broker_net_buy("005930")

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_foreign_broker_net_buy.assert_called_once_with(
            "005930", None, None
        )

    def test_facade_pattern_integration(self):
        """Facade 패턴 통합 테스트"""
        # 각 하위 시스템의 응답 설정
        price_response = {"rt_cd": "0", "output": {"stck_prpr": "70000"}}
        market_response = {"rt_cd": "0", "output": {"market_data": "test"}}
        investor_response = {"rt_cd": "0", "output": {"investor_data": "test"}}

        self.api.price_api.get_stock_price = Mock(return_value=price_response)
        self.api.market_api.get_market_fluctuation = Mock(return_value=market_response)
        self.api.investor_api.get_stock_investor = Mock(return_value=investor_response)

        # 각 하위 시스템 호출
        price_result = self.api.get_stock_price("005930")
        market_result = self.api.get_market_fluctuation()
        investor_result = self.api.get_stock_investor("005930")

        # 결과 검증
        self.assertEqual(price_result, price_response)
        self.assertEqual(market_result, market_response)
        self.assertEqual(investor_result, investor_response)

        # 각 하위 시스템이 호출되었는지 확인
        self.api.price_api.get_stock_price.assert_called_once()
        self.api.market_api.get_market_fluctuation.assert_called_once()
        self.api.investor_api.get_stock_investor.assert_called_once()

    def test_stock_api_facade_alias(self):
        """StockAPIFacade 별칭 테스트"""
        self.assertIs(StockAPIFacade, StockAPI)


if __name__ == "__main__":
    unittest.main()
