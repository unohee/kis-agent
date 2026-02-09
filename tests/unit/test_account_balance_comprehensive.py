"""
account/balance.py 모듈 단위 테스트

자동 생성됨 - /boost-coverage 스킬
생성일: 2026-01-04
대상 함수: get_account_balance, get_cash_available, get_total_asset
"""

import unittest
from unittest.mock import MagicMock, Mock

import pandas as pd

from kis_agent.account.balance import AccountAPI, AccountBalance, AccountBalanceAPI


class TestAccountBalanceAPI(unittest.TestCase):
    """AccountAPI (balance.py) 클래스 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.mock_client = MagicMock()
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = AccountAPI(self.mock_client, self.account_info)

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.api.client, self.mock_client)
        self.assertEqual(self.api.account, self.account_info)

    def test_aliases(self):
        """레거시 별칭 테스트"""
        # AccountBalance와 AccountBalanceAPI가 AccountAPI의 별칭인지 확인
        self.assertIs(AccountBalance, AccountAPI)
        self.assertIs(AccountBalanceAPI, AccountAPI)

    # get_account_balance 테스트
    def test_get_account_balance_success(self):
        """계좌 잔고 조회 성공 테스트"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg_cd": "00000000",
            "msg1": "정상처리 되었습니다.",
            "output1": [
                {
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "hldg_qty": "10",
                    "pchs_avg_pric": "65000",
                    "evlu_amt": "700000",
                },
                {
                    "pdno": "000660",
                    "prdt_name": "SK하이닉스",
                    "hldg_qty": "5",
                    "pchs_avg_pric": "120000",
                    "evlu_amt": "650000",
                },
            ],
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_account_balance()

        # Then
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["rt_cd"].iloc[0], "0")
        self.assertEqual(result["msg_cd"].iloc[0], "00000000")
        self.mock_client.make_request.assert_called_once()
        call_args = self.mock_client.make_request.call_args
        self.assertEqual(call_args[1]["tr_id"], "TTTC8434R")
        self.assertEqual(call_args[1]["params"]["CANO"], "12345678")
        self.assertEqual(call_args[1]["params"]["ACNT_PRDT_CD"], "01")

    def test_get_account_balance_empty_output(self):
        """계좌 잔고 조회 - 보유 종목 없음"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg_cd": "00000000",
            "msg1": "정상처리 되었습니다.",
            "output1": [],
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_account_balance()

        # Then
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)

    def test_get_account_balance_no_output1(self):
        """계좌 잔고 조회 - output1 키 없음"""
        # Given
        mock_response = {"rt_cd": "1", "msg_cd": "EGW00123", "msg1": "에러 메시지"}
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_account_balance()

        # Then
        self.assertIsNone(result)

    def test_get_account_balance_none_response(self):
        """계좌 잔고 조회 - None 응답"""
        # Given
        self.mock_client.make_request.return_value = None

        # When
        result = self.api.get_account_balance()

        # Then
        self.assertIsNone(result)

    # get_cash_available 테스트
    def test_get_cash_available_success(self):
        """현금 조회 성공 테스트"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg_cd": "00000000",
            "msg1": "정상처리 되었습니다.",
            "output": {"ord_psbl_cash": "1000000"},
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_cash_available()

        # Then
        self.assertEqual(result, mock_response)
        call_args = self.mock_client.make_request.call_args
        self.assertEqual(call_args[1]["tr_id"], "TTTC8901R")
        self.assertEqual(call_args[1]["params"]["CANO"], "12345678")

    def test_get_cash_available_settlement_time_json_decode_error(self):
        """현금 조회 - 정산 시간 JSON 디코드 에러"""
        # Given
        mock_response = {
            "rt_cd": "JSON_DECODE_ERROR",
            "msg1": "JSON decode error",
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_cash_available()

        # Then
        self.assertEqual(result["rt_cd"], "JSON_DECODE_ERROR")
        self.assertIn("정산안내", result)
        self.assertIn("정산 시간", result["정산안내"])

    def test_get_cash_available_settlement_time_404(self):
        """현금 조회 - 정산 시간 404 에러"""
        # Given
        mock_response = {"status_code": 404, "msg1": "Not Found"}
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_cash_available()

        # Then
        self.assertIn("정산안내", result)

    def test_get_cash_available_none_response(self):
        """현금 조회 - None 응답"""
        # Given
        self.mock_client.make_request.return_value = None

        # When
        result = self.api.get_cash_available()

        # Then
        self.assertIsNone(result)

    def test_get_cash_available_normal_error(self):
        """현금 조회 - 일반 에러 응답"""
        # Given
        mock_response = {"rt_cd": "1", "msg1": "일반 에러"}
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_cash_available()

        # Then
        self.assertEqual(result["rt_cd"], "1")
        self.assertNotIn("정산안내", result)

    # get_total_asset 테스트
    def test_get_total_asset_success(self):
        """총 자산 조회 성공 테스트"""
        # Given
        mock_response = {
            "rt_cd": "0",
            "msg_cd": "00000000",
            "msg1": "정상처리 되었습니다.",
            "output": {"tot_evlu_amt": "10000000", "pchs_amt_smtl": "8000000"},
        }
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_total_asset()

        # Then
        self.assertEqual(result, mock_response)
        call_args = self.mock_client.make_request.call_args
        self.assertEqual(call_args[1]["tr_id"], "TTTC8522R")
        self.assertEqual(call_args[1]["params"]["INQR_DVSN"], "02")
        self.assertEqual(call_args[1]["params"]["UNPR_DVSN"], "01")

    def test_get_total_asset_settlement_time_json_decode_error(self):
        """총 자산 조회 - 정산 시간 JSON 디코드 에러"""
        # Given
        mock_response = {"rt_cd": "JSON_DECODE_ERROR", "msg1": "JSON decode error"}
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_total_asset()

        # Then
        self.assertEqual(result["rt_cd"], "JSON_DECODE_ERROR")
        self.assertIn("정산안내", result)
        self.assertIn("정산 시간", result["정산안내"])

    def test_get_total_asset_settlement_time_404(self):
        """총 자산 조회 - 정산 시간 404 에러"""
        # Given
        mock_response = {"status_code": 404, "msg1": "Not Found"}
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_total_asset()

        # Then
        self.assertIn("정산안내", result)

    def test_get_total_asset_none_response(self):
        """총 자산 조회 - None 응답"""
        # Given
        self.mock_client.make_request.return_value = None

        # When
        result = self.api.get_total_asset()

        # Then
        self.assertIsNone(result)

    def test_get_total_asset_normal_error(self):
        """총 자산 조회 - 일반 에러 응답"""
        # Given
        mock_response = {"rt_cd": "1", "msg1": "일반 에러"}
        self.mock_client.make_request.return_value = mock_response

        # When
        result = self.api.get_total_asset()

        # Then
        self.assertEqual(result["rt_cd"], "1")
        self.assertNotIn("정산안내", result)


if __name__ == "__main__":
    unittest.main()
