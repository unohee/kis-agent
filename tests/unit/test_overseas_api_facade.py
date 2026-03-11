"""
Overseas Stock API Facade 모듈 테스트

해외주식 API 통합 Facade Pattern 테스트
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest

from kis_agent.core.client import KISClient
from kis_agent.overseas.api_facade import OverseasStockAPI


class TestOverseasStockAPIFacade(unittest.TestCase):
    """OverseasStockAPI Facade 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"account_no": "12345", "account_code": "01"}

        with patch("kis_agent.overseas.api_facade.OverseasPriceAPI"):
            self.api = OverseasStockAPI(
                client=self.mock_client,
                account_info=self.account_info,
                enable_cache=False,
                _from_agent=True,
            )

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.api.client, self.mock_client)
        self.assertEqual(self.api.account, self.account_info)
        self.assertIsNotNone(self.api.price_api)

    def test_init_without_account_info(self):
        """계좌 정보 없이 초기화"""
        with patch("kis_agent.overseas.api_facade.OverseasPriceAPI"):
            api = OverseasStockAPI(client=self.mock_client, _from_agent=True)
            self.assertEqual(api.client, self.mock_client)
            self.assertIsNone(api.account)

    def test_exchanges_constant(self):
        """EXCHANGES 상수 확인"""
        expected_exchanges = [
            "NAS",
            "NYS",
            "AMS",
            "HKS",
            "TSE",
            "SHS",
            "SZS",
            "HSX",
            "HNX",
        ]
        for exchange in expected_exchanges:
            self.assertIn(exchange, self.api.EXCHANGES)
            self.assertIn("name", self.api.EXCHANGES[exchange])
            self.assertIn("country", self.api.EXCHANGES[exchange])
            self.assertIn("currency", self.api.EXCHANGES[exchange])


class TestOverseasStockAPIDelegation(unittest.TestCase):
    """OverseasStockAPI 위임 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"account_no": "12345", "account_code": "01"}

        with patch("kis_agent.overseas.api_facade.OverseasPriceAPI"):
            self.api = OverseasStockAPI(
                client=self.mock_client,
                account_info=self.account_info,
                enable_cache=False,
                _from_agent=True,
            )

    def test_get_price_delegation(self):
        """get_price 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"last": "185.50"}}
        self.api.price_api.get_price = Mock(return_value=expected_result)

        result = self.api.get_price("NAS", "AAPL")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_price.assert_called_once_with("NAS", "AAPL")

    def test_get_price_detail_delegation(self):
        """get_price_detail 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"last": "185.50", "perx": "28.5"}}
        self.api.price_api.get_price_detail = Mock(return_value=expected_result)

        result = self.api.get_price_detail("NAS", "TSLA")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_price_detail.assert_called_once_with("NAS", "TSLA")

    def test_get_daily_price_delegation(self):
        """get_daily_price 메서드 위임 테스트"""
        expected_result = {
            "rt_cd": "0",
            "output1": {},
            "output2": [{"xymd": "20231215"}],
        }
        self.api.price_api.get_daily_price = Mock(return_value=expected_result)

        result = self.api.get_daily_price("NAS", "NVDA", gubn="0", bymd="", modp="0")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_daily_price.assert_called_once_with(
            "NAS", "NVDA", "0", "", "0"
        )

    def test_get_minute_price_delegation(self):
        """get_minute_price 메서드 위임 테스트"""
        expected_result = {
            "rt_cd": "0",
            "output1": {},
            "output2": [{"tymd": "20231215"}],
        }
        self.api.price_api.get_minute_price = Mock(return_value=expected_result)

        result = self.api.get_minute_price(
            "NAS", "AAPL", nmin="5", pinc="0", nrec="100"
        )

        self.assertEqual(result, expected_result)
        self.api.price_api.get_minute_price.assert_called_once_with(
            "NAS", "AAPL", "5", "0", "100"
        )

    def test_get_orderbook_delegation(self):
        """get_orderbook 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output1": {}, "output2": {"pask1": "186.00"}}
        self.api.price_api.get_orderbook = Mock(return_value=expected_result)

        result = self.api.get_orderbook("NAS", "AAPL")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_orderbook.assert_called_once_with("NAS", "AAPL")

    def test_get_stock_info_delegation(self):
        """get_stock_info 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": {"prdt_name": "APPLE INC"}}
        self.api.price_api.get_stock_info = Mock(return_value=expected_result)

        result = self.api.get_stock_info("512", "NAS.AAPL")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_stock_info.assert_called_once_with("512", "NAS.AAPL")

    def test_get_ccnl_delegation(self):
        """get_ccnl 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output1": {}, "output2": [{"last": "185.50"}]}
        self.api.price_api.get_ccnl = Mock(return_value=expected_result)

        result = self.api.get_ccnl("NAS", "AAPL")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_ccnl.assert_called_once_with("NAS", "AAPL")

    def test_get_holiday_delegation(self):
        """get_holiday 메서드 위임 테스트"""
        expected_result = {"rt_cd": "0", "output": [{"hldy_dt": "20231225"}]}
        self.api.price_api.get_holiday = Mock(return_value=expected_result)

        result = self.api.get_holiday("20231201")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_holiday.assert_called_once_with("20231201")

    def test_get_news_title_delegation(self):
        """get_news_title 메서드 위임 테스트"""
        expected_result = {
            "rt_cd": "0",
            "output": [{"news_titl": "Apple announces..."}],
        }
        self.api.price_api.get_news_title = Mock(return_value=expected_result)

        result = self.api.get_news_title(excd="NAS", symb="AAPL", nrec="10")

        self.assertEqual(result, expected_result)
        self.api.price_api.get_news_title.assert_called_once_with(
            excd="NAS", symb="AAPL", nrec="10"
        )


class TestOverseasStockAPIUtilities(unittest.TestCase):
    """OverseasStockAPI 유틸리티 메서드 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)

        with patch("kis_agent.overseas.api_facade.OverseasPriceAPI"):
            self.api = OverseasStockAPI(
                client=self.mock_client,
                enable_cache=False,
                _from_agent=True,
            )

    def test_get_supported_exchanges(self):
        """지원 거래소 목록 조회"""
        exchanges = self.api.get_supported_exchanges()

        self.assertIsInstance(exchanges, dict)
        self.assertIn("NAS", exchanges)
        self.assertIn("NYS", exchanges)
        self.assertEqual(exchanges["NAS"]["name"], "NASDAQ")
        self.assertEqual(exchanges["NYS"]["country"], "미국")

    def test_is_valid_exchange_true(self):
        """유효한 거래소 코드"""
        self.assertTrue(self.api.is_valid_exchange("NAS"))
        self.assertTrue(self.api.is_valid_exchange("nas"))  # 대소문자 무관
        self.assertTrue(self.api.is_valid_exchange("NYS"))
        self.assertTrue(self.api.is_valid_exchange("HKS"))
        self.assertTrue(self.api.is_valid_exchange("TSE"))

    def test_is_valid_exchange_false(self):
        """유효하지 않은 거래소 코드"""
        self.assertFalse(self.api.is_valid_exchange("XXX"))
        self.assertFalse(self.api.is_valid_exchange("KRX"))  # 국내 거래소
        self.assertFalse(self.api.is_valid_exchange(""))

    def test_get_exchange_info(self):
        """거래소 정보 조회"""
        info = self.api.get_exchange_info("NAS")

        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "NASDAQ")
        self.assertEqual(info["country"], "미국")
        self.assertEqual(info["currency"], "USD")

    def test_get_exchange_info_case_insensitive(self):
        """거래소 정보 조회 (대소문자 무관)"""
        info = self.api.get_exchange_info("nas")

        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "NASDAQ")

    def test_get_exchange_info_invalid(self):
        """존재하지 않는 거래소"""
        info = self.api.get_exchange_info("XXX")

        self.assertIsNone(info)


class TestOverseasStockAPIDynamicDelegation(unittest.TestCase):
    """OverseasStockAPI __getattr__ 동적 위임 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)

        with patch("kis_agent.overseas.api_facade.OverseasPriceAPI") as MockPriceAPI:
            # spec을 설정하여 존재하지 않는 속성 접근 시 AttributeError 발생
            self.mock_price_api = Mock()
            MockPriceAPI.return_value = self.mock_price_api
            self.api = OverseasStockAPI(
                client=self.mock_client,
                enable_cache=False,
                _from_agent=True,
            )

    def test_getattr_delegates_to_price_api(self):
        """__getattr__가 price_api로 위임"""
        # price_api에 임의 메서드 추가
        self.mock_price_api.custom_method = Mock(return_value="custom_result")

        result = self.api.custom_method()

        self.assertEqual(result, "custom_result")
        self.mock_price_api.custom_method.assert_called_once()

    def test_getattr_raises_attribute_error_for_missing_attr(self):
        """price_api에 없는 속성은 AttributeError"""
        # Mock에 spec 설정하여 없는 속성 접근 시 AttributeError 발생하도록 함
        self.api.price_api = Mock(spec=[])  # 빈 spec - 아무 메서드도 없음

        with self.assertRaises(AttributeError) as context:
            _ = self.api.nonexistent_method

        self.assertIn("OverseasStockAPI", str(context.exception))
        self.assertIn("nonexistent_method", str(context.exception))


if __name__ == "__main__":
    unittest.main()
