"""
stock/data.py 모듈의 단위 테스트

이 파일은 stock/data.py의 17% 커버리지를 높이기 위해 생성되었습니다.
StockAPI 클래스의 모든 주요 메서드를 테스트합니다.

커버리지 목표: 17% → 80%+
"""

import unittest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock
from pykis.core.client import KISClient
from pykis.stock.data import StockAPI


class TestStockData(unittest.TestCase):
    """StockAPI 클래스의 포괄적인 테스트"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        cls.client = KISClient()
        cls.account_info = {
            "CANO": "12345678",
            "ACNT_PRDT_CD": "01"
        }
        cls.api = StockAPI(cls.client, cls.account_info)
        cls.api_no_account = StockAPI(cls.client)  # 계좌 정보 없는 인스턴스
        cls.test_code = "005930"
        
    def test_init_with_account(self):
        """계좌 정보가 있는 초기화 테스트"""
        api = StockAPI(self.client, self.account_info)
        self.assertEqual(api.account, self.account_info)
        self.assertEqual(api.client, self.client)
        
    def test_init_without_account(self):
        """계좌 정보가 없는 초기화 테스트"""
        api = StockAPI(self.client)
        self.assertIsNone(api.account)
        self.assertEqual(api.client, self.client)

    @patch('pykis.core.client.KISClient.make_request')
    def test_make_request_dataframe_success(self, mock_request):
        """_make_request_dataframe 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"col1": "val1", "col2": "val2"}]
        }
        
        result = self.api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST123",
            params={"test": "param"}
        )
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["col1"], "val1")

    @patch('pykis.core.client.KISClient.make_request')
    def test_make_request_dataframe_dict_output(self, mock_request):
        """_make_request_dataframe dict 출력 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"col1": "val1", "col2": "val2"}
        }
        
        result = self.api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST123",
            params={"test": "param"}
        )
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)

    @patch('pykis.core.client.KISClient.make_request')
    def test_make_request_dataframe_failure(self, mock_request):
        """_make_request_dataframe 실패 테스트"""
        mock_request.return_value = {"rt_cd": "1", "msg1": "오류"}
        
        result = self.api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST123",
            params={"test": "param"}
        )
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_stock_price_success(self, mock_request):
        """주식 시세 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"stck_prpr": "60000"}
        }
        
        result = self.api.get_stock_price(self.test_code)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        mock_request.assert_called_once()

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_stock_price_exception(self, mock_request):
        """주식 시세 조회 예외 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        result = self.api.get_stock_price(self.test_code)
        
        self.assertIsNone(result)

    def test_execute_order_without_account(self):
        """계좌 정보 없이 주문 실행 테스트"""
        result = self.api_no_account.execute_order(self.test_code, 10, 60000)
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_execute_order_success(self, mock_request):
        """주문 실행 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"order_id": "123456"}
        }
        
        result = self.api.execute_order(self.test_code, 10, 60000)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_execute_order_exception(self, mock_request):
        """주문 실행 예외 테스트"""
        mock_request.side_effect = Exception("주문 실행 오류")
        
        result = self.api.execute_order(self.test_code, 10, 60000)
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_daily_price_with_dates(self, mock_request):
        """날짜 지정 일별 시세 조회 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"stck_bsop_date": "20241201"}]
        }
        
        result = self.api.get_daily_price(self.test_code, "20241201", "20241210")
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_minute_chart_success(self, mock_request):
        """분봉 차트 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output1": [{"time": "153000", "price": "60000"}]
        }
        
        result = self.api.get_minute_chart(self.test_code, "153000")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_orderbook_success(self, mock_request):
        """호가 정보 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": [{"askp1": "60500", "bidp1": "60000"}]
        }
        
        result = self.api.get_orderbook(self.test_code)
        
        self.assertIsInstance(result, pd.DataFrame)

    @patch('pykis.stock.data.StockAPI._make_request_dataframe')
    def test_get_stock_investor_success(self, mock_dataframe):
        """투자자별 매매동향 조회 성공 테스트"""
        mock_dataframe.return_value = pd.DataFrame([{
            "prsn_ntby_qty": "1000",
            "frgn_ntby_qty": "2000"
        }])
        
        result = self.api.get_stock_investor(self.test_code)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)

    @patch('pykis.stock.data.StockAPI._make_request_dataframe')
    def test_get_foreign_broker_net_buy_success(self, mock_dataframe):
        """외국계 브로커 순매수 조회 성공 테스트"""
        mock_dataframe.return_value = pd.DataFrame([{
            "frgn_ntby_qty": "1000",
            "stck_bsop_date": "20241201"
        }])
        
        result = self.api.get_foreign_broker_net_buy(self.test_code)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 1000)  # 외국인 순매수량
        self.assertIsInstance(result[1], pd.DataFrame)


if __name__ == "__main__":
    unittest.main() 