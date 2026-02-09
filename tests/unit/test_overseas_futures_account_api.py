"""
OverseasFuturesAccountAPI 모듈 테스트

해외선물옵션 계좌/잔고 조회 API를 테스트합니다.

테스트 대상 기능:
- 잔고 조회 (get_balance)
- 예수금 조회 (get_deposit)
- 증거금 상세 (get_margin_detail)
- 주문가능 조회 (get_order_amount)
- 당일 주문내역 (get_today_orders)
- 일별 주문내역 (get_daily_orders)
- 일별 체결내역 (get_daily_executions)
- 기간 계좌손익 (get_period_profit)
- 기간 거래내역 (get_period_transactions)
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from pykis.overseas_futures.account_api import OverseasFuturesAccountAPI


class TestOverseasFuturesAccountAPI(unittest.TestCase):
    """OverseasFuturesAccountAPI 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.mock_client = Mock()
        self.account_info = {"account_no": "12345678", "account_code": "03"}
        self.api = OverseasFuturesAccountAPI(
            client=self.mock_client,
            account_info=self.account_info,
            enable_cache=False,
        )

    def test_get_balance(self):
        """해외선물옵션 잔고 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": [
                {
                    "srs_cd": "CNHU24",
                    "unsttl_qty": "2",
                    "avg_pric": "100.25",
                    "evlt_amt": "200.50",
                }
            ],
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_balance()

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_balance_with_filter(self):
        """해외선물옵션 잔고 조회 (필터 적용) 테스트"""
        expected_response = {"rt_cd": "0", "msg1": "정상처리 되었습니다.", "output": []}

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_balance(fuop_dvsn="01")  # 선물만

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_deposit(self):
        """해외선물옵션 예수금 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "dps_amt": "50000.00",
                "use_mrgn": "10000.00",
                "ord_psbl_amt": "40000.00",
            },
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_deposit()

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_margin_detail(self):
        """해외선물옵션 증거금 상세 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "opng_mrgn": "5000.00",
                "mnt_mrgn": "4000.00",
            },
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_margin_detail()

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_order_amount(self):
        """해외선물옵션 주문가능 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "ord_psbl_qty": "10",
                "ord_psbl_amt": "10000.00",
            },
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_order_amount("CNHU24", "02", "100.50")

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_today_orders(self):
        """해외선물옵션 당일 주문내역 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": [
                {
                    "odno": "0000001234",
                    "srs_cd": "CNHU24",
                    "ord_qty": "1",
                    "ccld_qty": "1",
                }
            ],
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_today_orders()

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_daily_orders(self):
        """해외선물옵션 일별 주문내역 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": [],
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_daily_orders("20260101", "20260123")

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_daily_executions(self):
        """해외선물옵션 일별 체결내역 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": [],
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_daily_executions("20260101", "20260123")

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_period_profit(self):
        """해외선물옵션 기간 계좌손익 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "tot_plamt": "5000.00",
                "tot_ccld_amt": "100000.00",
            },
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_period_profit("20260101", "20260123")

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_period_transactions(self):
        """해외선물옵션 기간 거래내역 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": [],
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_period_transactions("20260101", "20260123")

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()


@pytest.mark.parametrize(
    "method_name,args",
    [
        ("get_balance", ()),
        ("get_deposit", ()),
        ("get_margin_detail", ()),
        ("get_order_amount", ("CNHU24", "02", "100.00")),
        ("get_today_orders", ()),
        ("get_daily_orders", ("20260101", "20260123")),
        ("get_daily_executions", ("20260101", "20260123")),
        ("get_period_profit", ("20260101", "20260123")),
        ("get_period_transactions", ("20260101", "20260123")),
    ],
)
def test_account_api_methods_exist(method_name, args):
    """Account API 메서드 존재 확인"""
    mock_client = Mock()
    api = OverseasFuturesAccountAPI(
        client=mock_client,
        account_info={"account_no": "12345678", "account_code": "03"},
        enable_cache=False,
    )

    assert hasattr(api, method_name)
    method = getattr(api, method_name)
    assert callable(method)


if __name__ == "__main__":
    unittest.main()
