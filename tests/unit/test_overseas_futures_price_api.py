"""
OverseasFuturesPriceAPI 모듈 테스트

해외선물옵션 시세 조회 API를 테스트합니다.

테스트 대상 기능:
- 해외선물 현재가 조회 (get_price)
- 해외옵션 현재가 조회 (get_option_price)
- 분봉 차트 조회 (get_minute_chart)
- 일간 체결추이 조회 (get_daily_trend)
- 해외선물 호가 조회 (get_futures_orderbook)
- 해외옵션 호가 조회 (get_option_orderbook)
- 상품기본정보 조회 (get_futures_info, get_option_info)
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from pykis.overseas_futures.price_api import OverseasFuturesPriceAPI


class TestOverseasFuturesPriceAPI(unittest.TestCase):
    """OverseasFuturesPriceAPI 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.mock_client = Mock()
        self.account_info = {"account_no": "12345678", "account_code": "03"}
        self.api = OverseasFuturesPriceAPI(
            client=self.mock_client,
            account_info=self.account_info,
            enable_cache=False,
        )

    def test_get_price(self):
        """해외선물 현재가 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "last": "100.50",
                "diff": "0.25",
                "rate": "0.25",
                "tvol": "150000",
                "oi": "250000",
            },
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_price("CNHU24")

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_option_price(self):
        """해외옵션 현재가 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "last": "15.25",
                "theo_pric": "15.30",
                "iv": "18.5",
                "delta": "0.65",
                "gamma": "0.02",
                "theta": "-0.15",
                "vega": "0.25",
            },
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_option_price("ES2401C5000")

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_minute_chart(self):
        """해외선물 분봉 차트 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output1": {"index_key": ""},
            "output2": [
                {
                    "bsop_date": "20260123",
                    "bsop_time": "143000",
                    "open": "100.25",
                    "high": "100.50",
                    "low": "100.10",
                    "last": "100.45",
                    "tvol": "1500",
                }
            ],
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_minute_chart("CNHU24", "CME", qry_gap="5")

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_daily_trend(self):
        """해외선물 일간 체결추이 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output2": [
                {
                    "bsop_date": "20260122",
                    "open": "100.00",
                    "high": "101.00",
                    "low": "99.50",
                    "last": "100.50",
                    "tvol": "250000",
                    "oi": "500000",
                }
            ],
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_daily_trend("CNHU24", "CME")

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_futures_orderbook(self):
        """해외선물 호가 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output1": {
                "askp1": "100.55",
                "askp2": "100.60",
                "askp_rsqn1": "100",
                "askp_rsqn2": "150",
            },
            "output2": {
                "bidp1": "100.50",
                "bidp2": "100.45",
                "bidp_rsqn1": "120",
                "bidp_rsqn2": "80",
            },
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_futures_orderbook("CNHU24")

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_option_orderbook(self):
        """해외옵션 호가 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output1": {"askp1": "15.30"},
            "output2": {"bidp1": "15.25"},
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_option_orderbook("ES2401C5000")

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_futures_info(self):
        """해외선물 상품기본정보 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": [
                {
                    "srs_cd": "CNHU24",
                    "prdt_nm": "E-mini Nasdaq 100",
                    "exch_cd": "CME",
                    "tick_sz": "0.25",
                    "tick_val": "5.00",
                    "ctrt_sz": "20",
                    "expr_date": "20240920",
                }
            ],
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_futures_info(["CNHU24", "ESM24"])

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_get_option_info(self):
        """해외옵션 상품기본정보 조회 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": [
                {
                    "srs_cd": "ES2401C5000",
                    "expr_date": "20240119",
                }
            ],
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.get_option_info(["ES2401C5000"])

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()


@pytest.mark.parametrize(
    "method_name,args",
    [
        ("get_price", ("CNHU24",)),
        ("get_option_price", ("ES2401C5000",)),
        ("get_futures_orderbook", ("CNHU24",)),
        ("get_option_orderbook", ("ES2401C5000",)),
        ("get_futures_info", (["CNHU24"],)),
        ("get_option_info", (["ES2401C5000"],)),
    ],
)
def test_price_api_methods_exist(method_name, args):
    """Price API 메서드 존재 확인"""
    mock_client = Mock()
    api = OverseasFuturesPriceAPI(
        client=mock_client,
        account_info={"account_no": "12345678", "account_code": "03"},
        enable_cache=False,
    )

    assert hasattr(api, method_name)
    method = getattr(api, method_name)
    assert callable(method)


if __name__ == "__main__":
    unittest.main()
