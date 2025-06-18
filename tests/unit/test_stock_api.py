import os
import unittest
from pykis.core.client import KISClient
from pykis.stock.api import StockAPI

class TestStockAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 실제 계좌 정보는 환경변수에서 읽음
        cls.account_info = {
            "CANO": os.getenv("KIS_ACCOUNT_NO"),
            "ACNT_PRDT_CD": os.getenv("KIS_ACCOUNT_CODE", "01")
        }
        cls.client = KISClient()
        cls.api = StockAPI(cls.client, cls.account_info)
        cls.test_code = "005930"  # 삼성전자

    def test_get_stock_price(self):
        result = self.api.get_stock_price(self.test_code)
        print("get_stock_price:", result)
        self.assertIsNotNone(result)
        self.assertIn("rt_cd", result)

    def test_get_daily_price(self):
        result = self.api.get_daily_price(self.test_code)
        print("get_daily_price:", result)
        self.assertIsNotNone(result)
        self.assertIn("rt_cd", result)

if __name__ == "__main__":
    unittest.main() 