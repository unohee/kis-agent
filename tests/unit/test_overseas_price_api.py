"""
OverseasPriceAPI 모듈 테스트

해외주식 시세 조회 API 테스트
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest

from kis_agent.core.client import KISClient
from kis_agent.overseas.price_api import OverseasPriceAPI


class TestOverseasPriceAPIInit(unittest.TestCase):
    """OverseasPriceAPI 초기화 테스트"""

    def test_init_with_client(self):
        """클라이언트로 초기화"""
        mock_client = Mock(spec=KISClient)
        api = OverseasPriceAPI(client=mock_client, _from_agent=True)

        self.assertEqual(api.client, mock_client)
        self.assertIsNone(api.account)

    def test_init_with_account_info(self):
        """계좌 정보와 함께 초기화"""
        mock_client = Mock(spec=KISClient)
        account_info = {"account_no": "12345", "account_code": "01"}

        api = OverseasPriceAPI(
            client=mock_client, account_info=account_info, _from_agent=True
        )

        self.assertEqual(api.account, account_info)

    def test_exchange_codes_constant(self):
        """EXCHANGE_CODES 상수 확인"""
        mock_client = Mock(spec=KISClient)
        api = OverseasPriceAPI(client=mock_client, _from_agent=True)

        expected_codes = ["NAS", "NYS", "AMS", "HKS", "TSE", "SHS", "SZS", "HSX", "HNX"]
        for code in expected_codes:
            self.assertIn(code, api.EXCHANGE_CODES)


class TestOverseasPriceAPIGetPrice(unittest.TestCase):
    """OverseasPriceAPI.get_price() 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        # make_request 메서드 추가
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(
            client=self.mock_client, enable_cache=False, _from_agent=True
        )

    def test_get_price_success(self):
        """현재가 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg_cd": "0000",
            "output": {
                "rsym": "DNASAAPL",
                "last": "185.50",
                "diff": "2.50",
                "rate": "1.37",
                "tvol": "45000000",
            },
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_price("NAS", "AAPL")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once()
        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["EXCD"], "NAS")
        self.assertEqual(call_kwargs["params"]["SYMB"], "AAPL")

    def test_get_price_invalid_exchange(self):
        """유효하지 않은 거래소 코드"""
        with self.assertRaises(ValueError) as context:
            self.api.get_price("XXX", "AAPL")

        self.assertIn("유효하지 않은 거래소 코드", str(context.exception))
        self.assertIn("XXX", str(context.exception))
        self.mock_client.make_request.assert_not_called()


class TestOverseasPriceAPIGetPriceInvalidSymbol(unittest.TestCase):
    """OverseasPriceAPI - 잘못된 종목코드 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(
            client=self.mock_client, enable_cache=False, _from_agent=True
        )

    def test_get_price_invalid_symbol_returns_error(self):
        """존재하지 않는 종목코드 조회 시 API 에러 응답"""
        error_response = {
            "rt_cd": "1",
            "msg_cd": "MCA00000",
            "msg1": "종목코드를 확인하세요",
        }
        self.mock_client.make_request.return_value = error_response

        result = self.api.get_price("NAS", "INVALIDCODE")

        self.assertEqual(result["rt_cd"], "1")
        self.mock_client.make_request.assert_called_once()

    def test_get_price_empty_symbol(self):
        """빈 종목코드 조회"""
        error_response = {
            "rt_cd": "1",
            "msg_cd": "MCA00000",
            "msg1": "종목코드를 입력하세요",
        }
        self.mock_client.make_request.return_value = error_response

        result = self.api.get_price("NAS", "")

        self.assertEqual(result["rt_cd"], "1")


class TestOverseasPriceAPIGetDailyPriceDateRange(unittest.TestCase):
    """OverseasPriceAPI.get_daily_price() 기간 조회 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(
            client=self.mock_client, enable_cache=False, _from_agent=True
        )

    def test_get_daily_price_date_range(self):
        """기간별 일봉 조회 (bymd 지정)"""
        expected_response = {
            "rt_cd": "0",
            "output1": {"rsym": "DNASAAPL", "zdiv": "2"},
            "output2": [
                {"xymd": "20231201", "clos": "190.00", "open": "189.00"},
                {"xymd": "20231130", "clos": "189.50", "open": "188.00"},
                {"xymd": "20231129", "clos": "188.00", "open": "187.50"},
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_daily_price("NAS", "AAPL", bymd="20231201")

        self.assertEqual(result["rt_cd"], "0")
        self.assertEqual(len(result["output2"]), 3)
        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["BYMD"], "20231201")
        self.assertEqual(call_kwargs["params"]["EXCD"], "NAS")
        self.assertEqual(call_kwargs["params"]["SYMB"], "AAPL")

    def test_get_daily_price_monthly(self):
        """월봉 조회"""
        expected_response = {"rt_cd": "0", "output1": {}, "output2": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_daily_price("NAS", "AAPL", gubn="2")

        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["GUBN"], "2")

    def test_get_daily_price_adjusted(self):
        """수정주가 반영 조회"""
        expected_response = {"rt_cd": "0", "output1": {}, "output2": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_daily_price("NAS", "AAPL", modp="1")

        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["MODP"], "1")


class TestOverseasPriceAPIGetPriceDetail(unittest.TestCase):
    """OverseasPriceAPI.get_price_detail() 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(
            client=self.mock_client, enable_cache=False, _from_agent=True
        )

    def test_get_price_detail_success(self):
        """현재가 상세 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "output": {
                "last": "185.50",
                "h52p": "200.00",
                "l52p": "150.00",
                "perx": "28.5",
                "epsx": "6.50",
            },
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_price_detail("NAS", "AAPL")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["EXCD"], "NAS")
        self.assertEqual(call_kwargs["params"]["SYMB"], "AAPL")

    def test_get_price_detail_invalid_exchange(self):
        """유효하지 않은 거래소 코드"""
        with self.assertRaises(ValueError) as context:
            self.api.get_price_detail("INVALID", "AAPL")

        self.assertIn("유효하지 않은 거래소 코드", str(context.exception))


class TestOverseasPriceAPIGetDailyPrice(unittest.TestCase):
    """OverseasPriceAPI.get_daily_price() 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(
            client=self.mock_client, enable_cache=False, _from_agent=True
        )

    def test_get_daily_price_success(self):
        """일봉 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "output1": {"rsym": "DNASAAPL", "zdiv": "2"},
            "output2": [
                {"xymd": "20231215", "clos": "185.50", "open": "183.00"},
                {"xymd": "20231214", "clos": "183.00", "open": "182.50"},
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_daily_price("NAS", "AAPL")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["EXCD"], "NAS")
        self.assertEqual(call_kwargs["params"]["SYMB"], "AAPL")
        self.assertEqual(call_kwargs["params"]["GUBN"], "0")  # 기본값: 일봉
        self.assertEqual(call_kwargs["params"]["MODP"], "0")  # 기본값: 수정주가 미반영

    def test_get_daily_price_weekly(self):
        """주봉 조회"""
        expected_response = {"rt_cd": "0", "output1": {}, "output2": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_daily_price("NAS", "TSLA", gubn="1")

        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["GUBN"], "1")

    def test_get_daily_price_with_date(self):
        """기준일자 지정 조회"""
        expected_response = {"rt_cd": "0", "output1": {}, "output2": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_daily_price("NAS", "NVDA", bymd="20231201")

        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["BYMD"], "20231201")


class TestOverseasPriceAPIGetMinutePrice(unittest.TestCase):
    """OverseasPriceAPI.get_minute_price() 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(
            client=self.mock_client, enable_cache=False, _from_agent=True
        )

    def test_get_minute_price_success(self):
        """분봉 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "output1": {"rsym": "DNASAAPL"},
            "output2": [
                {"tymd": "20231215", "xhms": "093000", "last": "185.50"},
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_minute_price("NAS", "AAPL")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["NMIN"], "1")  # 기본값: 1분봉
        self.assertEqual(call_kwargs["params"]["PINC"], "0")  # 기본값: 당일만
        self.assertEqual(call_kwargs["params"]["NREC"], "120")  # 기본값: 120건

    def test_get_minute_price_5min(self):
        """5분봉 조회"""
        expected_response = {"rt_cd": "0", "output1": {}, "output2": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_minute_price("NAS", "AAPL", nmin="5")

        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["NMIN"], "5")

    def test_get_minute_price_with_previous_day(self):
        """전일 포함 조회"""
        expected_response = {"rt_cd": "0", "output1": {}, "output2": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_minute_price("NAS", "TSLA", pinc="1")

        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["PINC"], "1")


class TestOverseasPriceAPIGetOrderbook(unittest.TestCase):
    """OverseasPriceAPI.get_orderbook() 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(
            client=self.mock_client, enable_cache=False, _from_agent=True
        )

    def test_get_orderbook_success(self):
        """호가 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "output1": {"rsym": "DNASAAPL"},
            "output2": {
                "pask1": "186.00",
                "vask1": "1000",
                "pbid1": "185.90",
                "vbid1": "800",
            },
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_orderbook("NAS", "AAPL")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["EXCD"], "NAS")
        self.assertEqual(call_kwargs["params"]["SYMB"], "AAPL")


class TestOverseasPriceAPIGetStockInfo(unittest.TestCase):
    """OverseasPriceAPI.get_stock_info() 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(
            client=self.mock_client, enable_cache=False, _from_agent=True
        )

    def test_get_stock_info_success(self):
        """상품정보 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "output": {
                "pdno": "NAS.AAPL",
                "prdt_name": "APPLE INC",
                "prdt_eng_name": "APPLE INC",
                "tr_mket_name": "NASDAQ",
                "crcy_cd": "USD",
            },
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_stock_info("512", "NAS.AAPL")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["PRDT_TYPE_CD"], "512")
        self.assertEqual(call_kwargs["params"]["PDNO"], "NAS.AAPL")


class TestOverseasPriceAPIGetCcnl(unittest.TestCase):
    """OverseasPriceAPI.get_ccnl() 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(
            client=self.mock_client, enable_cache=False, _from_agent=True
        )

    def test_get_ccnl_success(self):
        """체결정보 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "output1": {"rsym": "DNASAAPL"},
            "output2": [
                {"tymd": "20231215", "xhms": "093000", "last": "185.50", "tvol": "100"},
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_ccnl("NAS", "AAPL")

        self.assertEqual(result, expected_response)


class TestOverseasPriceAPIGetHoliday(unittest.TestCase):
    """OverseasPriceAPI.get_holiday() 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(
            client=self.mock_client, enable_cache=False, _from_agent=True
        )

    def test_get_holiday_success(self):
        """휴장일 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "output": [
                {"hldy_dt": "20231225", "hldy_nm": "Christmas Day", "natn_name": "USA"},
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_holiday("20231201")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["TRAD_DT"], "20231201")

    def test_get_holiday_no_date(self):
        """기준일자 없이 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_holiday()

        call_kwargs = self.mock_client.make_request.call_args[1]
        self.assertEqual(call_kwargs["params"]["TRAD_DT"], "")


class TestOverseasPriceAPIGetNewsTitle(unittest.TestCase):
    """OverseasPriceAPI.get_news_title() 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(
            client=self.mock_client, enable_cache=False, _from_agent=True
        )

    def test_get_news_title_success(self):
        """뉴스 제목 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "output": [
                {"news_titl": "Apple announces new product", "data_dt": "20231215"},
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_news_title(excd="NAS", symb="AAPL", nrec="10")

        self.assertEqual(result, expected_response)

    def test_get_news_title_all(self):
        """전체 뉴스 조회 (거래소/종목 지정 없이)"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_news_title()

        self.assertEqual(result, expected_response)


class TestOverseasPriceAPISearchSymbol(unittest.TestCase):
    """OverseasPriceAPI.search_symbol() 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(
            client=self.mock_client, enable_cache=False, _from_agent=True
        )

    def test_search_symbol_success(self):
        """종목 검색 성공"""
        expected_response = {
            "rt_cd": "0",
            "output": {"rsym": "DNASAAPL", "prdt_name": "APPLE INC"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.search_symbol("NAS", "AAPL")

        self.assertIsNotNone(result)

    def test_search_symbol_invalid_exchange(self):
        """유효하지 않은 거래소 - 기본값 사용"""
        # search_symbol은 유효하지 않은 거래소도 기본값(512)으로 처리
        # API 결과가 없으면 None 반환
        self.mock_client.make_request.return_value = {"rt_cd": "1", "msg_cd": "0001"}

        result = self.api.search_symbol("XXX", "AAPL")

        # 실패 응답이므로 None 반환
        self.assertIsNone(result)


class TestOverseasPriceAPIValidateExchange(unittest.TestCase):
    """OverseasPriceAPI._validate_exchange() 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.mock_client.make_request = Mock()
        self.api = OverseasPriceAPI(client=self.mock_client, _from_agent=True)

    def test_validate_exchange_valid_codes(self):
        """유효한 거래소 코드 검증"""
        valid_codes = ["NAS", "NYS", "AMS", "HKS", "TSE", "SHS", "SZS", "HSX", "HNX"]
        for code in valid_codes:
            self.assertTrue(self.api._validate_exchange(code))

    def test_validate_exchange_invalid_codes(self):
        """유효하지 않은 거래소 코드 검증"""
        invalid_codes = ["XXX", "KRX", "LON", "FRA"]
        for code in invalid_codes:
            with self.assertRaises(ValueError):
                self.api._validate_exchange(code)

    def test_validate_exchange_empty_string(self):
        """빈 문자열은 예외 발생"""
        with self.assertRaises(ValueError):
            self.api._validate_exchange("")

    def test_validate_exchange_case_insensitive(self):
        """대소문자 무관"""
        self.assertTrue(self.api._validate_exchange("nas"))
        self.assertTrue(self.api._validate_exchange("Nas"))
        self.assertTrue(self.api._validate_exchange("NAS"))


if __name__ == "__main__":
    unittest.main()
