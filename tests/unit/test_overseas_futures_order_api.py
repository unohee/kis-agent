"""
OverseasFuturesOrderAPI 모듈 테스트

해외선물옵션 주문 API를 테스트합니다.

테스트 대상 기능:
- 신규 주문 (order)
- 정정/취소 주문 (modify_cancel)
- 편의 메서드 (buy, sell, cancel, modify)
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from pykis.overseas_futures.order_api import OverseasFuturesOrderAPI


class TestOverseasFuturesOrderAPI(unittest.TestCase):
    """OverseasFuturesOrderAPI 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.mock_client = Mock()
        self.account_info = {"account_no": "12345678", "account_code": "03"}
        self.api = OverseasFuturesOrderAPI(
            client=self.mock_client,
            account_info=self.account_info,
            enable_cache=False,
        )

    def test_order_limit_buy(self):
        """해외선물옵션 지정가 매수 주문 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "odno": "00360686",
                "ord_dt": "20260123",
                "ord_tmd": "143000",
            },
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.order(
                ovrs_futr_fx_pdno="CNHU24",
                sll_buy_dvsn_cd="02",  # 매수
                fm_ord_qty="1",
                pric_dvsn_cd="1",  # 지정가
                fm_limit_ord_pric="100.00",
            )

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_order_market_sell(self):
        """해외선물옵션 시장가 매도 주문 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "odno": "00360687",
                "ord_dt": "20260123",
                "ord_tmd": "143100",
            },
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.order(
                ovrs_futr_fx_pdno="CNHU24",
                sll_buy_dvsn_cd="01",  # 매도
                fm_ord_qty="1",
                pric_dvsn_cd="2",  # 시장가
                ccld_cndt_cd="2",  # IOC
            )

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_order_stop(self):
        """해외선물옵션 STOP 주문 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {"odno": "00360688"},
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.order(
                ovrs_futr_fx_pdno="CNHU24",
                sll_buy_dvsn_cd="02",
                fm_ord_qty="1",
                pric_dvsn_cd="3",  # STOP
                fm_stop_ord_pric="105.00",
            )

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_modify_cancel_modify(self):
        """해외선물옵션 주문 정정 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "odno": "00360689",
                "orgn_odno": "00360686",
                "ord_dt": "20260123",
            },
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.modify_cancel(
                ord_dv="0",  # 정정
                orgn_ord_dt="20260123",
                orgn_odno="00360686",
                fm_limit_ord_pric="101.00",
            )

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_modify_cancel_cancel(self):
        """해외선물옵션 주문 취소 테스트"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output": {
                "odno": "00360690",
                "orgn_odno": "00360686",
            },
        }

        with patch.object(
            self.api, "_make_request_dict", return_value=expected_response
        ):
            result = self.api.modify_cancel(
                ord_dv="1",  # 취소
                orgn_ord_dt="20260123",
                orgn_odno="00360686",
            )

            self.assertEqual(result, expected_response)
            self.api._make_request_dict.assert_called_once()

    def test_buy_convenience_method(self):
        """buy 편의 메서드 테스트"""
        expected_response = {"rt_cd": "0", "output": {"odno": "00360691"}}

        with patch.object(
            self.api, "order", return_value=expected_response
        ) as mock_order:
            result = self.api.buy(code="CNHU24", qty="1", price="100.00")

            self.assertEqual(result, expected_response)
            mock_order.assert_called_once_with(
                ovrs_futr_fx_pdno="CNHU24",
                sll_buy_dvsn_cd="02",  # 매수
                fm_ord_qty="1",
                pric_dvsn_cd="1",  # 지정가
                fm_limit_ord_pric="100.00",
                ccld_cndt_cd="6",  # EOD
            )

    def test_buy_market_order(self):
        """buy 시장가 주문 테스트"""
        expected_response = {"rt_cd": "0", "output": {"odno": "00360692"}}

        with patch.object(
            self.api, "order", return_value=expected_response
        ) as mock_order:
            result = self.api.buy(code="CNHU24", qty="1", order_type="2")

            self.assertEqual(result, expected_response)
            mock_order.assert_called_once_with(
                ovrs_futr_fx_pdno="CNHU24",
                sll_buy_dvsn_cd="02",
                fm_ord_qty="1",
                pric_dvsn_cd="2",  # 시장가
                fm_limit_ord_pric="",
                ccld_cndt_cd="2",  # IOC
            )

    def test_sell_convenience_method(self):
        """sell 편의 메서드 테스트"""
        expected_response = {"rt_cd": "0", "output": {"odno": "00360693"}}

        with patch.object(
            self.api, "order", return_value=expected_response
        ) as mock_order:
            result = self.api.sell(code="CNHU24", qty="1", price="102.00")

            self.assertEqual(result, expected_response)
            mock_order.assert_called_once_with(
                ovrs_futr_fx_pdno="CNHU24",
                sll_buy_dvsn_cd="01",  # 매도
                fm_ord_qty="1",
                pric_dvsn_cd="1",
                fm_limit_ord_pric="102.00",
                ccld_cndt_cd="6",
            )

    def test_cancel_convenience_method(self):
        """cancel 편의 메서드 테스트"""
        expected_response = {"rt_cd": "0", "output": {"odno": "00360694"}}

        with patch.object(
            self.api, "modify_cancel", return_value=expected_response
        ) as mock_modify_cancel:
            result = self.api.cancel(orgn_ord_dt="20260123", orgn_odno="00360686")

            self.assertEqual(result, expected_response)
            mock_modify_cancel.assert_called_once_with(
                ord_dv="1",
                orgn_ord_dt="20260123",
                orgn_odno="00360686",
            )

    def test_modify_convenience_method(self):
        """modify 편의 메서드 테스트"""
        expected_response = {"rt_cd": "0", "output": {"odno": "00360695"}}

        with patch.object(
            self.api, "modify_cancel", return_value=expected_response
        ) as mock_modify_cancel:
            result = self.api.modify(
                orgn_ord_dt="20260123",
                orgn_odno="00360686",
                new_price="101.50",
            )

            self.assertEqual(result, expected_response)
            mock_modify_cancel.assert_called_once_with(
                ord_dv="0",
                orgn_ord_dt="20260123",
                orgn_odno="00360686",
                fm_limit_ord_pric="101.50",
            )


@pytest.mark.parametrize(
    "method_name,args,kwargs",
    [
        ("order", ("CNHU24", "02", "1", "1"), {"fm_limit_ord_pric": "100.00"}),
        ("modify_cancel", ("0", "20260123", "00360686"), {}),
        ("buy", ("CNHU24", "1"), {"price": "100.00"}),
        ("sell", ("CNHU24", "1"), {"price": "100.00"}),
        ("cancel", ("20260123", "00360686"), {}),
        ("modify", ("20260123", "00360686", "101.00"), {}),
    ],
)
def test_order_api_methods_exist(method_name, args, kwargs):
    """Order API 메서드 존재 확인"""
    mock_client = Mock()
    api = OverseasFuturesOrderAPI(
        client=mock_client,
        account_info={"account_no": "12345678", "account_code": "03"},
        enable_cache=False,
    )

    assert hasattr(api, method_name)
    method = getattr(api, method_name)
    assert callable(method)


def test_order_uses_post_method():
    """주문 API가 POST 메서드를 사용하는지 확인"""
    mock_client = Mock()
    api = OverseasFuturesOrderAPI(
        client=mock_client,
        account_info={"account_no": "12345678", "account_code": "03"},
        enable_cache=False,
    )

    with patch.object(api, "_make_request_dict") as mock_request:
        mock_request.return_value = {"rt_cd": "0", "output": {}}

        api.order("CNHU24", "02", "1", "1", "100.00")

        # _make_request_dict가 method="POST"로 호출되었는지 확인
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs.get("method") == "POST"
        assert call_kwargs.get("use_cache") is False


if __name__ == "__main__":
    unittest.main()
