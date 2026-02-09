"""
Futures Account API 모듈 테스트

선물옵션 계좌/잔고 조회 API 기능을 종합적으로 테스트합니다.

자동 생성됨 - /boost-coverage 스킬
생성일: 2026-01-19

테스트 대상 기능:
- 선물옵션 잔고 조회 (inquire_balance)
- 잔고 청산손익 조회 (inquire_balance_settlement_pl)
- 잔고 평가손익 조회 (inquire_balance_valuation_pl)
- 예수금 조회 (inquire_deposit)
- 야간 잔고 조회 (inquire_ngt_balance)
- 야간 증거금 상세 (ngt_margin_detail)

테스트 시나리오:
- 정상적인 API 응답 처리
- 실전/모의 환경 TR_ID 자동 선택
- 계좌 정보 추출 헬퍼 메서드
- 에러 응답 및 예외 상황 처리
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from pykis.core.client import API_ENDPOINTS
from pykis.futures.account_api import FuturesAccountAPI


class TestFuturesAccountAPI(unittest.TestCase):
    """FuturesAccountAPI 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.mock_client = Mock()
        self.mock_client.base_url = "https://openapi.koreainvestment.com:9443"
        self.account_info = {"account_no": "12345678", "account_code": "03"}
        self.api = FuturesAccountAPI(
            client=self.mock_client,
            account_info=self.account_info,
            enable_cache=False,
        )

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.api.client, self.mock_client)
        self.assertEqual(self.api.account, self.account_info)

    def test_get_account_no(self):
        """계좌번호 추출 테스트"""
        account_no = self.api._get_account_no()
        self.assertEqual(account_no, "12345678")

    def test_get_account_code(self):
        """계좌 코드 추출 테스트"""
        account_code = self.api._get_account_code()
        self.assertEqual(account_code, "03")

    def test_get_account_code_default(self):
        """계좌 코드 기본값 테스트"""
        api_no_code = FuturesAccountAPI(
            client=self.mock_client, account_info={}, enable_cache=False
        )
        account_code = api_no_code._get_account_code()
        self.assertEqual(account_code, "03")

    def test_is_virtual_real(self):
        """실전 환경 감지"""
        self.mock_client.base_url = "https://openapi.koreainvestment.com:9443"
        is_virtual = self.api._is_virtual()
        self.assertFalse(is_virtual)

    def test_is_virtual_mock(self):
        """모의투자 환경 감지"""
        self.mock_client.base_url = "https://openapivts.koreainvestment.com:29443"
        is_virtual = self.api._is_virtual()
        self.assertTrue(is_virtual)

    def test_inquire_balance_success(self):
        """선물옵션 잔고 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "fuop_item_code": "101S12",
                    "item_name": "KOSPI200 선물 2612",
                    "ord_psbl_qty": "10",
                    "avg_pric": "340.00",
                    "prsnt_pric": "341.50",
                    "fnoat_plamt": "15000",
                    "erng_rate": "0.44",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_balance()

        self.assertEqual(result, expected_response)
        self.assertEqual(len(result["output"]), 1)
        self.assertEqual(result["output"][0]["fuop_item_code"], "101S12")

    def test_inquire_balance_real_env(self):
        """실전 환경에서 잔고 조회 - TR_ID 확인"""
        self.mock_client.base_url = "https://openapi.koreainvestment.com:9443"
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_balance()

        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["tr_id"], "CTFO6118R")

    def test_inquire_balance_virtual_env(self):
        """모의투자 환경에서 잔고 조회 - TR_ID 확인"""
        self.mock_client.base_url = "https://openapivts.koreainvestment.com:29443"
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_balance()

        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["tr_id"], "VTFO6118R")

    def test_inquire_balance_empty(self):
        """잔고 없음"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_balance()

        self.assertEqual(result, expected_response)
        self.assertEqual(len(result["output"]), 0)

    def test_inquire_balance_settlement_pl_success(self):
        """청산손익 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "fuop_item_code": "101S12",
                    "item_name": "KOSPI200 선물 2612",
                    "lqd_amt": "1000000",
                    "lqd_pfls_amt": "50000",
                    "lqd_pfls_rt": "5.0",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_balance_settlement_pl()

        self.assertEqual(result, expected_response)
        self.assertIn("lqd_pfls_amt", result["output"][0])

    def test_inquire_balance_valuation_pl_success(self):
        """평가손익 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "fuop_item_code": "101S12",
                    "item_name": "KOSPI200 선물 2612",
                    "evlu_amt": "1700000",
                    "evlu_pfls_amt": "20000",
                    "evlu_pfls_rt": "1.18",
                    "fnoat_plamt": "20000",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_balance_valuation_pl()

        self.assertEqual(result, expected_response)
        self.assertIn("evlu_pfls_amt", result["output"][0])

    def test_inquire_deposit_success(self):
        """예수금 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {
                "fuop_dps_amt": "10000000",
                "fuop_evlu_pfls_amt": "150000",
                "tot_evlu_amt": "10150000",
                "tot_asst_amt": "10150000",
                "maint_mrgn_amt": "500000",
                "nass_amt": "9650000",
            },
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_deposit()

        self.assertEqual(result, expected_response)
        self.assertEqual(result["output"]["fuop_dps_amt"], "10000000")
        self.assertEqual(result["output"]["tot_asst_amt"], "10150000")

    def test_inquire_deposit_fields(self):
        """예수금 조회 - 필드 존재 확인"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {
                "fuop_dps_amt": "10000000",
                "fuop_evlu_pfls_amt": "150000",
                "tot_evlu_amt": "10150000",
                "tot_asst_amt": "10150000",
                "maint_mrgn_amt": "500000",
                "nass_amt": "9650000",
            },
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_deposit()

        output = result["output"]
        self.assertIn("fuop_dps_amt", output)
        self.assertIn("fuop_evlu_pfls_amt", output)
        self.assertIn("tot_evlu_amt", output)
        self.assertIn("tot_asst_amt", output)
        self.assertIn("maint_mrgn_amt", output)
        self.assertIn("nass_amt", output)

    def test_inquire_ngt_balance_success(self):
        """야간 잔고 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "fuop_item_code": "101S12",
                    "item_name": "KOSPI200 선물 2612",
                    "ord_psbl_qty": "5",
                    "avg_pric": "340.00",
                    "fnoat_plamt": "10000",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_ngt_balance()

        self.assertEqual(result, expected_response)
        self.assertEqual(len(result["output"]), 1)

    def test_ngt_margin_detail_success(self):
        """야간 증거금 상세 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "fuop_item_code": "101S12",
                    "item_name": "KOSPI200 선물 2612",
                    "maint_mrgn": "500000",
                    "ord_mrgn": "600000",
                    "dpsi_reqr_amt": "550000",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.ngt_margin_detail()

        self.assertEqual(result, expected_response)
        self.assertIn("maint_mrgn", result["output"][0])
        self.assertIn("ord_mrgn", result["output"][0])

    def test_inquire_balance_failure(self):
        """잔고 조회 실패"""
        self.mock_client.make_request.return_value = None

        result = self.api.inquire_balance()

        self.assertIsNone(result)

    def test_inquire_deposit_failure(self):
        """예수금 조회 실패"""
        self.mock_client.make_request.return_value = None

        result = self.api.inquire_deposit()

        self.assertIsNone(result)


@pytest.mark.parametrize(
    "account_code,expected",
    [
        ("03", "03"),  # 선물옵션
        ("01", "01"),  # 국내주식
        ("", "03"),  # 기본값
    ],
)
def test_account_code_handling(account_code, expected):
    """계좌 코드 처리 검증"""
    mock_client = Mock()
    account_info = {"account_no": "12345678"}
    if account_code:
        account_info["account_code"] = account_code

    api = FuturesAccountAPI(
        client=mock_client, account_info=account_info, enable_cache=False
    )

    result = api._get_account_code()
    assert result == expected


if __name__ == "__main__":
    unittest.main()
