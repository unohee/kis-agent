import unittest
from unittest.mock import MagicMock

from pykis.account.api import AccountAPI
from pykis.core.client import KISClient


class TestNewAccountAPI(unittest.TestCase):
    """AccountAPI 클래스의 새로운 메서드 테스트"""

    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        cls.client = MagicMock(spec=KISClient)
        cls.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        cls.api = AccountAPI(cls.client, cls.account_info)
        cls.test_code = "005930"

    def test_order_credit(self):
        """신용 주문 테스트"""
        self.client.make_request.return_value = {"rt_cd": "0"}
        result = self.api.order_credit(self.test_code, 10, 60000, "00")
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    def test_order_rvsecncl(self):
        """정정/취소 주문 테스트"""
        self.client.make_request.return_value = {"rt_cd": "0"}
        result = self.api.order_rvsecncl("12345", 10, 60000, "00", "02")
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    def test_inquire_psbl_rvsecncl(self):
        """정정/취소 가능 주문 조회 테스트"""
        self.client.make_request.return_value = {"rt_cd": "0"}
        result = self.api.inquire_psbl_rvsecncl()
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    def test_order_resv(self):
        """예약 주문 테스트"""
        self.client.make_request.return_value = {"rt_cd": "0"}
        result = self.api.order_resv(self.test_code, 10, 60000, "00")
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    def test_order_resv_rvsecncl(self):
        """예약 주문 정정/취소 테스트"""
        self.client.make_request.return_value = {"rt_cd": "0"}
        result = self.api.order_resv_rvsecncl(12345, 10, 60000, "00")
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    def test_order_resv_ccnl(self):
        """예약 주문 조회 테스트"""
        self.client.make_request.return_value = {"rt_cd": "0"}
        result = self.api.order_resv_ccnl()
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")


if __name__ == "__main__":
    unittest.main()
