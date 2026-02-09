"""
종목별 투자자매매동향(일별) API 테스트

TR_ID: FHPTJ04160001
Endpoint: /uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from kis_agent.core.client import KISClient
from kis_agent.stock.investor_api import StockInvestorAPI

# 실제 API 응답 구조를 반영한 Mock 데이터
MOCK_RESPONSE_SUCCESS = {
    "rt_cd": "0",
    "msg_cd": "MCA00000",
    "msg1": "정상처리 되었습니다.",
    "output1": {
        "stck_prpr": "106300",
        "prdy_vrss": "-1300",
        "prdy_vrss_sign": "5",
        "prdy_ctrt": "-1.21",
        "acml_vol": "25917098",
        "prdy_vol": "18000000",
        "rprs_mrkt_kor_name": "KOSPI",
    },
    "output2": [
        {
            "stck_bsop_date": "20251219",
            "stck_clpr": "106300",
            "prdy_vrss": "-1300",
            "prdy_vrss_sign": "5",
            "prdy_ctrt": "-1.21",
            "acml_vol": "25917098",
            "acml_tr_pbmn": "2775502209243",
            "stck_oprc": "109700",
            "stck_hgpr": "110000",
            "stck_lwpr": "106000",
            "frgn_ntby_qty": "-1500000",
            "frgn_reg_ntby_qty": "-1400000",
            "frgn_nreg_ntby_qty": "-100000",
            "prsn_ntby_qty": "2000000",
            "orgn_ntby_qty": "-500000",
            "scrt_ntby_qty": "-200000",
            "ivtr_ntby_qty": "-100000",
            "pe_fund_ntby_vol": "-50000",
            "bank_ntby_qty": "-30000",
            "insu_ntby_qty": "-20000",
            "mrbn_ntby_qty": "0",
            "fund_ntby_qty": "-80000",
            "etc_ntby_qty": "-20000",
        },
        {
            "stck_bsop_date": "20251218",
            "stck_clpr": "107600",
            "prdy_vrss": "200",
            "prdy_vrss_sign": "2",
            "prdy_ctrt": "0.19",
            "acml_vol": "18000000",
            "acml_tr_pbmn": "1900000000000",
            "stck_oprc": "107200",
            "stck_hgpr": "108000",
            "stck_lwpr": "106800",
            "frgn_ntby_qty": "500000",
            "prsn_ntby_qty": "-300000",
            "orgn_ntby_qty": "-200000",
        },
    ],
}

MOCK_RESPONSE_ERROR = {
    "rt_cd": "1",
    "msg_cd": "MCA00001",
    "msg1": "잘못된 종목코드입니다.",
}

MOCK_RESPONSE_EMPTY = {
    "rt_cd": "0",
    "msg_cd": "MCA00000",
    "msg1": "정상처리 되었습니다.",
    "output1": {},
    "output2": [],
}


class TestInvestorTradeByStockDaily(unittest.TestCase):
    """종목별 투자자매매동향(일별) API 단위 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.mock_client = Mock(spec=KISClient)
        self.api = StockInvestorAPI(
            client=self.mock_client,
            account_info={"account_no": "12345", "account_code": "01"},
            enable_cache=False,
            _from_agent=True,
        )

    def test_basic_call_success(self):
        """기본 호출 성공 테스트"""
        self.mock_client.make_request.return_value = MOCK_RESPONSE_SUCCESS

        result = self.api.get_investor_trade_by_stock_daily(
            fid_input_iscd="005930",
            fid_input_date_1="20251219",
        )

        # 응답 검증
        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        self.assertEqual(result["msg1"], "정상처리 되었습니다.")

        # output1 검증
        self.assertIn("output1", result)
        self.assertEqual(result["output1"]["stck_prpr"], "106300")
        self.assertEqual(result["output1"]["prdy_vrss"], "-1300")

        # output2 검증
        self.assertIn("output2", result)
        self.assertEqual(len(result["output2"]), 2)
        self.assertEqual(result["output2"][0]["stck_bsop_date"], "20251219")

    def test_request_params(self):
        """요청 파라미터 검증"""
        self.mock_client.make_request.return_value = MOCK_RESPONSE_SUCCESS

        self.api.get_investor_trade_by_stock_daily(
            fid_cond_mrkt_div_code="J",
            fid_input_iscd="005930",
            fid_input_date_1="20251219",
            fid_org_adj_prc="",
            fid_etc_cls_code="",
        )

        # make_request 호출 검증
        self.mock_client.make_request.assert_called_once()
        call_kwargs = self.mock_client.make_request.call_args

        # 파라미터 검증
        params = call_kwargs.kwargs.get("params", call_kwargs[1].get("params", {}))
        self.assertEqual(params["FID_COND_MRKT_DIV_CODE"], "J")
        self.assertEqual(params["FID_INPUT_ISCD"], "005930")
        self.assertEqual(params["FID_INPUT_DATE_1"], "20251219")

    def test_default_params(self):
        """기본 파라미터 테스트"""
        self.mock_client.make_request.return_value = MOCK_RESPONSE_SUCCESS

        self.api.get_investor_trade_by_stock_daily()

        call_kwargs = self.mock_client.make_request.call_args
        params = call_kwargs.kwargs.get("params", call_kwargs[1].get("params", {}))

        # 기본값 검증
        self.assertEqual(params["FID_COND_MRKT_DIV_CODE"], "J")
        self.assertEqual(params["FID_INPUT_ISCD"], "")
        self.assertEqual(params["FID_INPUT_DATE_1"], "")

    def test_nxt_market(self):
        """NXT 시장 조회 테스트"""
        self.mock_client.make_request.return_value = MOCK_RESPONSE_SUCCESS

        self.api.get_investor_trade_by_stock_daily(
            fid_cond_mrkt_div_code="NX",
            fid_input_iscd="005930",
        )

        call_kwargs = self.mock_client.make_request.call_args
        params = call_kwargs.kwargs.get("params", call_kwargs[1].get("params", {}))
        self.assertEqual(params["FID_COND_MRKT_DIV_CODE"], "NX")

    def test_unified_market(self):
        """통합 시장(UN) 조회 테스트"""
        self.mock_client.make_request.return_value = MOCK_RESPONSE_SUCCESS

        self.api.get_investor_trade_by_stock_daily(
            fid_cond_mrkt_div_code="UN",
            fid_input_iscd="005930",
        )

        call_kwargs = self.mock_client.make_request.call_args
        params = call_kwargs.kwargs.get("params", call_kwargs[1].get("params", {}))
        self.assertEqual(params["FID_COND_MRKT_DIV_CODE"], "UN")

    def test_error_response(self):
        """에러 응답 처리 테스트"""
        self.mock_client.make_request.return_value = MOCK_RESPONSE_ERROR

        result = self.api.get_investor_trade_by_stock_daily(
            fid_input_iscd="INVALID",
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "1")
        self.assertIn("잘못된", result["msg1"])

    def test_empty_response(self):
        """빈 응답 처리 테스트"""
        self.mock_client.make_request.return_value = MOCK_RESPONSE_EMPTY

        result = self.api.get_investor_trade_by_stock_daily(
            fid_input_iscd="005930",
            fid_input_date_1="19900101",  # 과거 날짜
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        self.assertEqual(len(result["output2"]), 0)

    def test_none_response(self):
        """None 응답 처리 테스트"""
        self.mock_client.make_request.return_value = None

        result = self.api.get_investor_trade_by_stock_daily(
            fid_input_iscd="005930",
        )

        self.assertIsNone(result)

    def test_tr_id_and_endpoint(self):
        """TR_ID 및 엔드포인트 검증"""
        self.mock_client.make_request.return_value = MOCK_RESPONSE_SUCCESS

        self.api.get_investor_trade_by_stock_daily(fid_input_iscd="005930")

        call_kwargs = self.mock_client.make_request.call_args

        # TR_ID 검증
        tr_id = call_kwargs.kwargs.get("tr_id", call_kwargs[1].get("tr_id", ""))
        self.assertEqual(tr_id, "FHPTJ04160001")

        # 엔드포인트 검증
        endpoint = call_kwargs.kwargs.get(
            "endpoint", call_kwargs[1].get("endpoint", "")
        )
        self.assertIn("investor-trade-by-stock-daily", endpoint)

    def test_output2_investor_fields(self):
        """output2의 투자자별 순매수 필드 검증"""
        self.mock_client.make_request.return_value = MOCK_RESPONSE_SUCCESS

        result = self.api.get_investor_trade_by_stock_daily(fid_input_iscd="005930")

        first_item = result["output2"][0]

        # 투자자별 순매수 수량 필드 존재 확인
        investor_fields = [
            "frgn_ntby_qty",  # 외국인 순매수 수량
            "prsn_ntby_qty",  # 개인 순매수 수량
            "orgn_ntby_qty",  # 기관계 순매수 수량
            "scrt_ntby_qty",  # 증권 순매수 수량
            "ivtr_ntby_qty",  # 투자신탁 순매수 수량
            "bank_ntby_qty",  # 은행 순매수 수량
            "insu_ntby_qty",  # 보험 순매수 수량
            "fund_ntby_qty",  # 기금 순매수 수량
        ]

        for field in investor_fields:
            self.assertIn(field, first_item, f"{field} 필드가 없습니다")


class TestInvestorTradeByStockDailyFacade(unittest.TestCase):
    """StockAPI Facade를 통한 호출 테스트"""

    def setUp(self):
        """테스트 설정"""
        from kis_agent.stock.api_facade import StockAPI

        self.mock_client = Mock(spec=KISClient)

        with patch("pykis.stock.api_facade.StockPriceAPI"), patch(
            "pykis.stock.api_facade.StockMarketAPI"
        ), patch("pykis.stock.api_facade.StockInvestorAPI"):
            self.api = StockAPI(
                client=self.mock_client,
                account_info={"account_no": "12345", "account_code": "01"},
                enable_cache=False,
            )

    def test_facade_delegation(self):
        """Facade 위임 테스트"""
        expected_result = MOCK_RESPONSE_SUCCESS
        self.api.investor_api.get_investor_trade_by_stock_daily = Mock(
            return_value=expected_result
        )

        result = self.api.get_investor_trade_by_stock_daily(
            fid_input_iscd="005930",
            fid_input_date_1="20251219",
        )

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_investor_trade_by_stock_daily.assert_called_once_with(
            "J", "005930", "20251219", "", ""
        )

    def test_facade_default_params(self):
        """Facade 기본 파라미터 위임 테스트"""
        expected_result = MOCK_RESPONSE_SUCCESS
        self.api.investor_api.get_investor_trade_by_stock_daily = Mock(
            return_value=expected_result
        )

        result = self.api.get_investor_trade_by_stock_daily()

        self.assertEqual(result, expected_result)
        self.api.investor_api.get_investor_trade_by_stock_daily.assert_called_once_with(
            "J", "", "", "", ""
        )


if __name__ == "__main__":
    unittest.main()
