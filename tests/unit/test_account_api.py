"""
account/api.py 모듈의 단위 테스트

이 파일은 account/api.py의 35% 커버리지를 높이기 위해 생성되었습니다.
AccountAPI 클래스의 계좌 관련 메서드들을 테스트합니다.

커버리지 목표: 35% → 85%+
"""

import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
from pykis.core.client import KISClient
from pykis.account.api import AccountAPI


class TestAccountAPI(unittest.TestCase):
    """AccountAPI 클래스의 포괄적인 테스트"""
    
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
        
    def test_init(self):
        """AccountAPI 초기화 테스트"""
        api = AccountAPI(self.client, self.account_info)
        self.assertEqual(api.client, self.client)
        self.assertEqual(api.account, self.account_info)
        self.assertEqual(api.account['CANO'], "12345678")
        self.assertEqual(api.account['ACNT_PRDT_CD'], "01")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_account_balance_success(self, mock_request):
        """계좌 잔고 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output1": [
                {
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "hldg_qty": "10",
                    "pchs_avg_pric": "60000",
                    "evlu_amt": "650000",
                    "evlu_pfls_amt": "50000"
                },
                {
                    "pdno": "000660",
                    "prdt_name": "SK하이닉스",
                    "hldg_qty": "5",
                    "pchs_avg_pric": "120000",
                    "evlu_amt": "650000",
                    "evlu_pfls_amt": "50000"
                }
            ]
        }
        
        result = self.api.get_account_balance()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]["pdno"], "005930")
        self.assertEqual(result.iloc[0]["prdt_name"], "삼성전자")
        
        # API 호출 파라미터 확인
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertIn("params", kwargs)
        params = kwargs["params"]
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_account_balance_no_output1(self, mock_request):
        """계좌 잔고 조회 output1 없음 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output2": ["some data"]
        }
        
        result = self.api.get_account_balance()
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_account_balance_no_response(self, mock_request):
        """계좌 잔고 조회 응답 없음 테스트"""
        mock_request.return_value = None
        
        result = self.api.get_account_balance()
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_cash_available_success(self, mock_request):
        """현금 매수 가능 금액 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {
                "ord_psbl_cash": "1000000",
                "ord_psbl_sbst": "950000",
                "ruse_psbl_amt": "50000"
            }
        }
        
        result = self.api.get_cash_available()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        self.assertIn("output", result)
        
        # API 호출 파라미터 확인
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertIn("params", kwargs)
        params = kwargs["params"]
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_cash_available_json_decode_error(self, mock_request):
        """현금 매수 가능 금액 조회 JSON 디코드 오류 테스트"""
        mock_request.return_value = {
            "rt_cd": "JSON_DECODE_ERROR",
            "msg1": "서버 오류"
        }
        
        result = self.api.get_cash_available()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "JSON_DECODE_ERROR")
        self.assertIn("정산안내", result)
        self.assertIn("정산 시간", result["정산안내"])

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_cash_available_404_error(self, mock_request):
        """현금 매수 가능 금액 조회 404 오류 테스트"""
        mock_request.return_value = {
            "status_code": 404,
            "rt_cd": "ERROR",
            "msg1": "서비스 이용 불가"
        }
        
        result = self.api.get_cash_available()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "ERROR")
        self.assertIn("정산안내", result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_cash_available_normal_response(self, mock_request):
        """현금 매수 가능 금액 조회 정상 응답 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {"ord_psbl_cash": "1000000"}
        }
        
        result = self.api.get_cash_available()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        self.assertNotIn("정산안내", result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_total_asset_success(self, mock_request):
        """총 자산 평가 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output2": {
                "tot_evlu_amt": "5000000",
                "evlu_pfls_smtl_amt": "500000",
                "pchs_amt_smtl_amt": "4500000",
                "evlu_amt_smtl_amt": "5000000"
            }
        }
        
        result = self.api.get_total_asset()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        self.assertIn("output2", result)
        
        # API 호출 파라미터 확인
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertIn("params", kwargs)
        params = kwargs["params"]
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")
        self.assertEqual(params["INQR_DVSN"], "02")  # 평가 기준
        self.assertEqual(params["UNPR_DVSN"], "01")  # 현재가 기준

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_total_asset_json_decode_error(self, mock_request):
        """총 자산 평가 조회 JSON 디코드 오류 테스트"""
        mock_request.return_value = {
            "rt_cd": "JSON_DECODE_ERROR",
            "msg1": "서버 오류"
        }
        
        result = self.api.get_total_asset()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "JSON_DECODE_ERROR")
        self.assertIn("정산안내", result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_total_asset_404_error(self, mock_request):
        """총 자산 평가 조회 404 오류 테스트"""
        mock_request.return_value = {
            "status_code": 404,
            "rt_cd": "ERROR",
            "msg1": "서비스 이용 불가"
        }
        
        result = self.api.get_total_asset()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "ERROR")
        self.assertIn("정산안내", result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_account_order_quantity_success(self, mock_request):
        """계좌별 주문 수량 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {
                "ord_psbl_qty": "100",
                "ord_unpr": "60000"
            }
        }
        
        result = self.api.get_account_order_quantity(self.test_code)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        
        # API 호출 파라미터 확인
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertIn("params", kwargs)
        params = kwargs["params"]
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")
        self.assertEqual(params["PDNO"], self.test_code)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_account_order_quantity_exception(self, mock_request):
        """계좌별 주문 수량 조회 예외 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        result = self.api.get_account_order_quantity(self.test_code)
        
        self.assertIsNone(result)

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_possible_order_amount_success(self, mock_request):
        """주문 가능 금액 조회 성공 테스트"""
        mock_request.return_value = {
            "rt_cd": "0",
            "output": {
                "ord_psbl_cash": "1000000",
                "max_buy_amt": "950000"
            }
        }
        
        result = self.api.get_possible_order_amount()
        
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        
        # API 호출 파라미터 확인
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertIn("params", kwargs)
        params = kwargs["params"]
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")
        self.assertEqual(params["CMA_EVLU_AMT_ICLD_YN"], "Y")
        self.assertEqual(params["OVRS_ICLD_YN"], "N")

    @patch('pykis.core.client.KISClient.make_request')
    def test_get_possible_order_amount_exception(self, mock_request):
        """주문 가능 금액 조회 예외 테스트"""
        mock_request.side_effect = Exception("API 오류")
        
        result = self.api.get_possible_order_amount()
        
        self.assertIsNone(result)

    def test_account_info_validation(self):
        """계좌 정보 유효성 검증 테스트"""
        # 올바른 계좌 정보로 초기화된 API 확인
        self.assertEqual(self.api.account['CANO'], "12345678")
        self.assertEqual(self.api.account['ACNT_PRDT_CD'], "01")
        
        # 다른 계좌 정보로 새 API 생성
        different_account = {
            "CANO": "87654321",
            "ACNT_PRDT_CD": "02"
        }
        different_api = AccountAPI(self.client, different_account)
        self.assertEqual(different_api.account['CANO'], "87654321")
        self.assertEqual(different_api.account['ACNT_PRDT_CD'], "02")


if __name__ == "__main__":
    unittest.main() 