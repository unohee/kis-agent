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
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kis_agent.core.client import API_ENDPOINTS, KISClient
from kis_agent.core.config import KISConfig
from kis_agent.futures.order_api import FuturesOrderAPI
from kis_agent.responses.futures import FuturesOrderResponse


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
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO1101U")  # 매수/매도 공통
        self.assertEqual(call_kwargs[1]["params"]["SLL_BUY_DVSN_CD"], "02")
        self.assertEqual(call_kwargs[1]["params"]["ORD_DVSN_CD"], "02")  # 시장가

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
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO1101U")  # 매수/매도 공통
        self.assertEqual(call_kwargs[1]["params"]["ORD_DVSN_CD"], "01")  # 지정가

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
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO1101U")  # 매수/매도 공통
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
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO1101U")  # 매수/매도 공통
        self.assertEqual(call_kwargs[1]["params"]["ORD_DVSN_CD"], "01")  # 지정가

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
        self.assertEqual(call_kwargs[1]["params"]["KRX_NMPR_CNDT_CD"], "3")

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
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO1103U")  # 정정/취소 공통
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
        self.assertEqual(call_kwargs[1]["tr_id"], "TTTO1103U")  # 정정/취소 공통
        self.assertEqual(call_kwargs[1]["params"]["UNIT_PRICE"], "341.00")

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
        ("01", "TTTO1101U"),  # 매도
        ("02", "TTTO1101U"),  # 매수
    ],
)
def test_order_tr_id_selection(order_type, expected_tr_id):
    """주간 주문은 매수/매도 모두 TTTO1101U 하나를 쓴다.

    매수/매도 구분은 TR_ID가 아니라 SLL_BUY_DVSN_CD 필드로 한다 (공식 문서
    '선물옵션 주문' 시트: "TTTO1101U : 선물 옵션 매수 매도 주문 주간").
    이전에는 매도에 TTTO1102U를 보냈으나 그런 TR_ID는 존재하지 않는다.
    """
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
        ("0", "02"),  # 시장가
        ("340.50", "01"),  # 지정가
        ("341.00", "01"),  # 지정가
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


def api_with_capture():
    mock_client = Mock()
    mock_client.make_request.return_value = {"rt_cd": "0", "output": {}}
    api = FuturesOrderAPI(
        client=mock_client,
        account_info={"account_no": "12345678", "account_code": "03"},
        enable_cache=False,
    )
    return api, mock_client


@pytest.mark.parametrize(
    "price,nmpr_type,ord_dvsn",
    [("0", "02", "02"), ("340.50", "01", "01")],
)
def test_order_market_and_limit_use_official_body_fields(price, nmpr_type, ord_dvsn):
    api, mock_client = api_with_capture()
    api.order("101S12", "02", "1", price, "1")
    call_kwargs = mock_client.make_request.call_args[1]
    assert call_kwargs["tr_id"] == "TTTO1101U"
    assert call_kwargs["params"] == {
        "ORD_PRCS_DVSN_CD": "02", "CANO": "12345678", "ACNT_PRDT_CD": "03",
        "SHTN_PDNO": "101S12", "SLL_BUY_DVSN_CD": "02", "ORD_QTY": "1",
        "UNIT_PRICE": price, "NMPR_TYPE_CD": nmpr_type,
        "KRX_NMPR_CNDT_CD": "3", "ORD_DVSN_CD": "12" if price == "0" else "10",
    }


@pytest.mark.parametrize("action,expected_price,expected_ord_dvsn", [("01", "341.00", "01"), ("02", "0", "02")])
def test_order_correction_and_cancellation_use_official_body_fields(action, expected_price, expected_ord_dvsn):
    api, mock_client = api_with_capture()
    api.order_rvsecncl("0000123456", "1", action, "341.00")
    call_kwargs = mock_client.make_request.call_args[1]
    assert call_kwargs["tr_id"] == "TTTO1103U"
    assert call_kwargs["params"] == {
        "ORD_PRCS_DVSN_CD": "02", "CANO": "12345678", "ACNT_PRDT_CD": "03", "ORGN_ODNO": "0000123456",
        "RVSE_CNCL_DVSN_CD": action, "ORD_QTY": "1",
        "UNIT_PRICE": expected_price, "NMPR_TYPE_CD": "02" if expected_price == "0" else "01",
        "KRX_NMPR_CNDT_CD": "0", "RMN_QTY_YN": "N", "ORD_DVSN_CD": expected_ord_dvsn,
    }


def test_official_order_response_shape_through_api_return_path():
    api, mock_client = api_with_capture()
    fixture = {"rt_cd": "0", "output": {"odno": "123", "ord_tmd": "101530"}}
    mock_client.make_request.return_value = fixture

    order_response: FuturesOrderResponse = api.order("101S12", "02", "1", "0")
    amend_response: FuturesOrderResponse = api.order_rvsecncl(
        "0000123456", "1", "01", "341.00"
    )

    for response in (order_response, amend_response):
        assert response["output"]["odno"] == "123"
        assert response["output"]["ord_tmd"] == "101530"
    assert mock_client.make_request.call_count == 2


def test_paper_daytime_four_paths_resolve_final_tr_ids(monkeypatch):
    """Credential-safe dry run through KISClient.make_request's TR resolution gate."""
    monkeypatch.setenv("KIS_PAPER", "1")
    monkeypatch.setenv("KIS_ACCOUNT_CODE", "03")
    monkeypatch.setenv("KIS_APP_KEY", "dry-run-app-key")
    monkeypatch.setenv("KIS_APP_SECRET", "dry-run-app-secret")
    monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")
    config = KISConfig.from_env()
    client = KISClient(config=config, enable_rate_limiter=False, _defer_token=True)
    client.token = "dry-run-token"
    monkeypatch.setattr(client, "_check_and_refresh_token", lambda: None)
    monkeypatch.setattr(
        "kis_agent.core.client.getTREnv",
        lambda: SimpleNamespace(
            my_token="dry-run-token", my_app=config.APP_KEY, my_sec=config.APP_SECRET
        ),
    )
    requests = []

    class DryRunResponse:
        status_code = 200
        text = '{"rt_cd":"0","output":{}}'

        def json(self):
            return {"rt_cd": "0", "output": {}}

    def capture_transport(method, url, **kwargs):
        requests.append(kwargs)
        return DryRunResponse()

    monkeypatch.setattr("kis_agent.core.client.httpx.request", capture_transport)
    api = FuturesOrderAPI(
        client=client,
        account_info={"account_no": config.ACCOUNT_NO, "account_code": config.ACCOUNT_CODE},
        enable_cache=False,
    )

    for invoke in (
        lambda: api.order("101S12", "02", "1", "0"),
        lambda: api.order("101S12", "01", "1", "341.00"),
        lambda: api.order_rvsecncl("0000123456", "1", "01", "341.00"),
        lambda: api.order_rvsecncl("0000123456", "1", "02", "341.00"),
    ):
        invoke()

    assert [request["headers"]["tr_id"] for request in requests] == [
        "VTTO1101U",
        "VTTO1101U",
        "VTTO1103U",
        "VTTO1103U",
    ]
    assert all(
        (request["json"] or request["params"])["ACNT_PRDT_CD"] == "03"
        for request in requests
    )


if __name__ == "__main__":
    unittest.main()
