"""
Futures Order API 모듈 테스트

선물옵션 주문/체결 조회 API 기능을 종합적으로 테스트합니다.

자동 생성됨 - /boost-coverage 스킬
생성일: 2026-01-19

테스트 대상 기능:
- 선물옵션 체결 내역 조회 (inquire_ccnl)
- 야간 체결 내역 조회 (inquire_ngt_ccnl)
- 주문 가능 수량 조회 (inquire_psbl_order)
- 야간 주문 가능 수량 조회 (inquire_psbl_ngt_order)
- 선물옵션 주문 (order)
- 선물옵션 정정/취소 (order_rvsecncl)

테스트 시나리오:
- 정상적인 API 응답 처리
- 매수/매도 구분 처리
- 시장가/지정가 구분
- 주문 정정/취소 구분
- TR_ID 자동 선택
- 에러 응답 및 예외 상황 처리
"""

import unittest
from unittest.mock import Mock

import pytest

from pykis.core.client import API_ENDPOINTS
from pykis.futures.order_api import FuturesOrderAPI


class TestFuturesOrderAPI(unittest.TestCase):
    """FuturesOrderAPI 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.mock_client = Mock()
        self.mock_client.base_url = "https://openapi.koreainvestment.com:9443"
        self.account_info = {"account_no": "12345678", "account_code": "03"}
        self.api = FuturesOrderAPI(
            client=self.mock_client,
            account_info=self.account_info,
            enable_cache=False,
        )

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.api.client, self.mock_client)
        self.assertEqual(self.api.account, self.account_info)

    def test_inquire_ccnl_success(self):
        """체결 내역 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "ord_dt": "20260119",
                    "odno": "0000123456",
                    "fuop_item_code": "101S12",
                    "sll_buy_dvsn_cd": "2",
                    "ord_qty": "1",
                    "ccld_qty": "1",
                    "ccld_unpr": "340.50",
                    "ccld_amt": "17025000",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_ccnl("20260119", "20260119")

        self.assertEqual(result, expected_response)
        self.assertEqual(len(result["output"]), 1)
        self.assertEqual(result["output"][0]["odno"], "0000123456")

    def test_inquire_ccnl_real_env(self):
        """실전 환경 체결 내역 - TR_ID 확인"""
        self.mock_client.base_url = "https://openapi.koreainvestment.com:9443"
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_ccnl()

        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO5201R")

    def test_inquire_ccnl_virtual_env(self):
        """모의투자 환경 체결 내역 - TR_ID 확인"""
        self.mock_client.base_url = "https://openapivts.koreainvestment.com:29443"
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_ccnl()

        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["tr_id"], "VTTO5201R")

    def test_inquire_ccnl_empty(self):
        """체결 내역 없음"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_ccnl()

        self.assertEqual(result, expected_response)
        self.assertEqual(len(result["output"]), 0)

    def test_inquire_ngt_ccnl_success(self):
        """야간 체결 내역 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "ord_dt": "20260119",
                    "odno": "0000789012",
                    "fuop_item_code": "101S12",
                    "sll_buy_dvsn_cd": "1",
                    "ord_qty": "1",
                    "ccld_qty": "1",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_ngt_ccnl("20260119", "20260119")

        self.assertEqual(result, expected_response)
        self.assertEqual(len(result["output"]), 1)

    def test_inquire_psbl_order_success(self):
        """주문 가능 수량 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {
                "ord_psbl_qty": "10",
                "max_ord_psbl_qty": "15",
                "ord_mrgn_amt": "500000",
                "maint_mrgn_amt": "450000",
            },
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_psbl_order("101S12")

        self.assertEqual(result, expected_response)
        self.assertEqual(result["output"]["ord_psbl_qty"], "10")
        self.assertEqual(result["output"]["ord_mrgn_amt"], "500000")

    def test_inquire_psbl_order_real_env(self):
        """실전 환경 주문 가능 수량 - TR_ID 확인"""
        self.mock_client.base_url = "https://openapi.koreainvestment.com:9443"
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": {}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_psbl_order("101S12")

        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO5105R")

    def test_inquire_psbl_order_virtual_env(self):
        """모의투자 환경 주문 가능 수량 - TR_ID 확인"""
        self.mock_client.base_url = "https://openapivts.koreainvestment.com:29443"
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": {}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_psbl_order("101S12")

        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["tr_id"], "VTTO5105R")

    def test_inquire_psbl_ngt_order_success(self):
        """야간 주문 가능 수량 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"ord_psbl_qty": "5", "max_ord_psbl_qty": "8"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_psbl_ngt_order("101S12")

        self.assertEqual(result, expected_response)
        self.assertEqual(result["output"]["ord_psbl_qty"], "5")

    def test_order_buy_market_success(self):
        """매수 주문 성공 - 시장가"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"odno": "0000123456", "ord_tmd": "092500"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.order(code="101S12", order_type="02", qty="1", price="0")

        self.assertEqual(result, expected_response)
        self.assertEqual(result["output"]["odno"], "0000123456")
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO1101U")  # 매수
        self.assertEqual(call_kwargs[1]["params"]["SLL_BUY_DVSN_CD"], "02")
        self.assertEqual(call_kwargs[1]["params"]["ORD_DVSN_CD"], "01")  # 시장가

    def test_order_buy_limit_success(self):
        """매수 주문 성공 - 지정가"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"odno": "0000123457", "ord_tmd": "093000"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.order(code="101S12", order_type="02", qty="1", price="340.50")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO1101U")  # 매수
        self.assertEqual(call_kwargs[1]["params"]["ORD_DVSN_CD"], "00")  # 지정가

    def test_order_sell_market_success(self):
        """매도 주문 성공 - 시장가"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"odno": "0000123458", "ord_tmd": "094500"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.order(code="101S12", order_type="01", qty="1", price="0")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO1102U")  # 매도
        self.assertEqual(call_kwargs[1]["params"]["SLL_BUY_DVSN_CD"], "01")

    def test_order_sell_limit_success(self):
        """매도 주문 성공 - 지정가"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"odno": "0000123459", "ord_tmd": "095000"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.order(code="101S12", order_type="01", qty="1", price="341.00")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO1102U")  # 매도
        self.assertEqual(call_kwargs[1]["params"]["ORD_DVSN_CD"], "00")  # 지정가

    def test_order_invalid_order_type(self):
        """잘못된 주문 구분"""
        with self.assertRaises(ValueError) as context:
            self.api.order(code="101S12", order_type="03", qty="1", price="0")

        self.assertIn("Invalid order_type", str(context.exception))

    def test_order_with_ioc_condition(self):
        """IOC 조건부 주문"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"odno": "0000123460"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.order(
            code="101S12", order_type="02", qty="1", price="340.50", order_cond="1"
        )

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["params"]["ORD_CNDI_DVSN_CD"], "1")

    def test_order_rvsecncl_cancel_success(self):
        """주문 취소 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "취소 완료",
            "output": {"odno": "0000123456", "ord_tmd": "100000"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.order_rvsecncl(
            orgn_odno="0000123456", qty="1", action="02"  # 취소
        )

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO1104U")  # 취소
        self.assertEqual(call_kwargs[1]["params"]["ORGN_ODNO"], "0000123456")

    def test_order_rvsecncl_modify_success(self):
        """주문 정정 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정정 완료",
            "output": {"odno": "0000123456", "ord_tmd": "101000"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.order_rvsecncl(
            orgn_odno="0000123456", qty="1", action="01", price="341.00"  # 정정
        )

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO1103U")  # 정정
        self.assertEqual(call_kwargs[1]["params"]["ORD_UNPR"], "341.00")

    def test_order_rvsecncl_invalid_action(self):
        """잘못된 정정/취소 구분"""
        with self.assertRaises(ValueError) as context:
            self.api.order_rvsecncl(orgn_odno="0000123456", qty="1", action="03")

        self.assertIn("Invalid action", str(context.exception))

    def test_order_failure(self):
        """주문 실패"""
        self.mock_client.make_request.return_value = None

        result = self.api.order(code="101S12", order_type="02", qty="1", price="0")

        self.assertIsNone(result)


@pytest.mark.parametrize(
    "order_type,expected_tr_id",
    [
        ("01", "TTTO1102U"),  # 매도
        ("02", "TTTO1101U"),  # 매수
    ],
)
def test_order_tr_id_selection(order_type, expected_tr_id):
    """주문 구분에 따른 TR_ID 선택 검증"""
    mock_client = Mock()
    mock_client.base_url = "https://openapi.koreainvestment.com:9443"
    api = FuturesOrderAPI(
        client=mock_client,
        account_info={"account_no": "12345678", "account_code": "03"},
        enable_cache=False,
    )

    mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}
    api.order(code="101S12", order_type=order_type, qty="1", price="0")

    call_kwargs = mock_client.make_request.call_args
    assert call_kwargs[1]["tr_id"] == expected_tr_id


@pytest.mark.parametrize(
    "price,expected_ord_dvsn",
    [
        ("0", "01"),  # 시장가
        ("340.50", "00"),  # 지정가
        ("341.00", "00"),  # 지정가
    ],
)
def test_order_type_by_price(price, expected_ord_dvsn):
    """가격에 따른 주문 구분 검증"""
    mock_client = Mock()
    api = FuturesOrderAPI(
        client=mock_client,
        account_info={"account_no": "12345678", "account_code": "03"},
        enable_cache=False,
    )

    mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}
    api.order(code="101S12", order_type="02", qty="1", price=price)

    call_kwargs = mock_client.make_request.call_args
    assert call_kwargs[1]["params"]["ORD_DVSN_CD"] == expected_ord_dvsn


if __name__ == "__main__":
    unittest.main()
