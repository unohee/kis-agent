import unittest
from unittest.mock import patch, MagicMock
from pykis.core.client import KISClient
from pykis.account.api import AccountAPI


class TestNewAccountAPI(unittest.TestCase):
    """AccountAPI 클래스의 새로운 메서드 테스트"""

    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        cls.client = KISClient()
        cls.account_info = {
            "CANO": "12345678",
            "ACNT_PRDT_CD": "01"
        }
        cls.api = AccountAPI(cls.client, cls.account_info)
        cls.test_code = "005930"

    @patch('pykis.core.client.KISClient.make_request')
    def test_order_credit(self, mock_request):
        """신용 주문 테스트"""
        mock_request.return_value = {"rt_cd": "0"}
        result = self.api.order_credit(self.test_code, 10, 60000, "00")
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_order_rvsecncl(self, mock_request):
        """정정/취소 주문 테스트"""
        mock_request.return_value = {"rt_cd": "0"}
        result = self.api.order_rvsecncl("12345", 10, 60000, "00", "02")
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_inquire_psbl_rvsecncl(self, mock_request):
        """정정/취소 가능 주문 조회 테스트"""
        mock_request.return_value = {"rt_cd": "0"}
        result = self.api.inquire_psbl_rvsecncl()
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_order_resv(self, mock_request):
        """예약 주문 테스트"""
        mock_request.return_value = {"rt_cd": "0"}
        result = self.api.order_resv(self.test_code, 10, 60000, "00")
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_order_resv_rvsecncl(self, mock_request):
        """예약 주문 정정/취소 테스트"""
        mock_request.return_value = {"rt_cd": "0"}
        result = self.api.order_resv_rvsecncl(12345, 10, 60000, "00")
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_order_resv_ccnl(self, mock_request):
        """예약 주문 조회 테스트"""
        mock_request.return_value = {"rt_cd": "0"}
        result = self.api.order_resv_ccnl()
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")


if __name__ == "__main__":
    unittest.main()
