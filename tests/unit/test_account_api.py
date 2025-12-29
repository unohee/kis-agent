"""
account/api.py 모듈의 단위 테스트

이 파일은 account/api.py의 35% 커버리지를 높이기 위해 생성되었습니다.
AccountAPI 클래스의 계좌 관련 메서드들을 테스트합니다.

커버리지 목표: 35% → 85%+
"""

import unittest
from unittest.mock import MagicMock

import pytest

from pykis.account.api import AccountAPI
from pykis.core.client import KISClient
from pykis.core.exceptions import APIException


class TestAccountAPI(unittest.TestCase):
    """AccountAPI 클래스의 포괄적인 테스트"""

    def setUp(self):
        """각 테스트마다 새로운 인스턴스 생성"""
        self.client = MagicMock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        # 캐시 비활성화하여 테스트 독립성 보장
        self.api = AccountAPI(self.client, self.account_info, enable_cache=False)
        self.test_code = "005930"

    def test_init(self):
        """AccountAPI 초기화 테스트"""
        api = AccountAPI(self.client, self.account_info)
        self.assertEqual(api.client, self.client)
        self.assertEqual(api.account, self.account_info)
        self.assertEqual(api.account["CANO"], "12345678")
        self.assertEqual(api.account["ACNT_PRDT_CD"], "01")

    def test_get_account_balance_success(self):
        """계좌 잔고 조회 성공 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "0",
            "output1": [
                {
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "hldg_qty": "10",
                    "pchs_avg_pric": "60000",
                    "evlu_amt": "650000",
                    "evlu_pfls_amt": "50000",
                },
                {
                    "pdno": "000660",
                    "prdt_name": "SK하이닉스",
                    "hldg_qty": "5",
                    "pchs_avg_pric": "120000",
                    "evlu_amt": "650000",
                    "evlu_pfls_amt": "50000",
                },
            ],
        }

        result = self.api.get_account_balance()

        self.assertIsInstance(result, dict)
        self.assertIn("output1", result)
        self.assertEqual(len(result["output1"]), 2)
        self.assertEqual(result["output1"][0]["pdno"], "005930")
        self.assertEqual(result["output1"][0]["prdt_name"], "삼성전자")

        # API 호출 파라미터 확인
        self.client.make_request.assert_called_once()
        args, kwargs = self.client.make_request.call_args
        self.assertIn("params", kwargs)
        params = kwargs["params"]
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")

    def test_get_account_balance_no_output1(self):
        """계좌 잔고 조회 output1 없음 테스트"""
        self.client.make_request.return_value = {"rt_cd": "0", "output2": ["some data"]}

        result = self.api.get_account_balance()

        # Dict 반환되지만 output1이 없음
        self.assertIsInstance(result, dict)
        self.assertNotIn("output1", result)

    def test_get_account_balance_no_response(self):
        """계좌 잔고 조회 응답 없음 테스트"""
        self.client.make_request.return_value = None

        result = self.api.get_account_balance()

        self.assertIsNone(result)

    def test_get_cash_available_success(self):
        """현금 매수 가능 금액 조회 성공 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "0",
            "output": {
                "ord_psbl_cash": "1000000",
                "ord_psbl_sbst": "950000",
                "ruse_psbl_amt": "50000",
            },
        }

        result = self.api.get_cash_available()

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        self.assertIn("output", result)

        # API 호출 파라미터 확인
        self.client.make_request.assert_called_once()
        args, kwargs = self.client.make_request.call_args
        self.assertIn("params", kwargs)
        params = kwargs["params"]
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")
        self.assertEqual(params["PDNO"], "005930")  # 기본 종목코드 (삼성전자)
        self.assertEqual(params["ORD_UNPR"], "0")
        self.assertEqual(params["ORD_DVSN"], "00")
        self.assertEqual(params["CMA_EVLU_AMT_ICLD_YN"], "Y")
        self.assertEqual(params["OVRS_ICLD_YN"], "N")

    def test_get_cash_available_json_decode_error(self):
        """현금 매수 가능 금액 조회 JSON 디코드 오류 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "JSON_DECODE_ERROR",
            "msg1": "서버 오류",
        }

        result = self.api.get_cash_available()

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "JSON_DECODE_ERROR")
        self.assertIn("디버깅_정보", result)
        self.assertIn("원시 응답 텍스트 확인 필요", result["디버깅_정보"])

    def test_get_cash_available_404_error(self):
        """현금 매수 가능 금액 조회 404 오류 테스트"""
        self.client.make_request.return_value = {
            "status_code": 404,
            "rt_cd": "ERROR",
            "msg1": "서비스 이용 불가",
        }

        result = self.api.get_cash_available()

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "ERROR")
        self.assertEqual(result["status_code"], 404)

    def test_get_cash_available_normal_response(self):
        """현금 매수 가능 금액 조회 정상 응답 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"ord_psbl_cash": "1000000"},
        }

        result = self.api.get_cash_available()

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        self.assertIn("output", result)

    def test_get_total_asset_success(self):
        """총 자산 평가 조회 성공 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "0",
            "output2": {
                "tot_evlu_amt": "5000000",
                "evlu_pfls_smtl_amt": "500000",
                "pchs_amt_smtl_amt": "4500000",
                "evlu_amt_smtl_amt": "5000000",
            },
        }

        result = self.api.get_total_asset()

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        self.assertIn("output2", result)

        # API 호출 파라미터 확인
        self.client.make_request.assert_called_once()
        args, kwargs = self.client.make_request.call_args
        self.assertIn("params", kwargs)
        params = kwargs["params"]
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")
        self.assertEqual(params["INQR_DVSN_1"], "")  # 조회구분1 공백
        self.assertEqual(
            params["BSPR_BF_DT_APLY_YN"], ""
        )  # 기준가이전일자적용여부 공백

    def test_get_total_asset_json_decode_error(self):
        """총 자산 평가 조회 JSON 디코드 오류 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "JSON_DECODE_ERROR",
            "msg1": "서버 오류",
        }

        result = self.api.get_total_asset()

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "JSON_DECODE_ERROR")
        self.assertIn("디버깅_정보", result)
        self.assertIn("원시 응답 텍스트 확인 필요", result["디버깅_정보"])

    def test_get_total_asset_404_error(self):
        """총 자산 평가 조회 404 오류 테스트"""
        self.client.make_request.return_value = {
            "status_code": 404,
            "rt_cd": "ERROR",
            "msg1": "서비스 이용 불가",
        }

        result = self.api.get_total_asset()

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "ERROR")
        self.assertEqual(result["status_code"], 404)

    def test_get_account_order_quantity_success(self):
        """계좌별 주문 수량 조회 성공 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"ord_psbl_qty": "100", "ord_unpr": "60000"},
        }

        result = self.api.get_account_order_quantity(self.test_code)

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

        # API 호출 파라미터 확인
        self.client.make_request.assert_called_once()
        args, kwargs = self.client.make_request.call_args
        self.assertIn("params", kwargs)
        params = kwargs["params"]
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")
        self.assertEqual(params["PDNO"], self.test_code)

    def test_get_account_order_quantity_exception(self):
        """계좌별 주문 수량 조회 예외 테스트

        @api_method(reraise=True) 기본값으로 인해 예외가 APIException으로 래핑되어 발생합니다.
        """
        self.client.make_request.side_effect = Exception("API 오류")

        with pytest.raises(APIException):
            self.api.get_account_order_quantity(self.test_code)

    def test_get_possible_order_amount_success(self):
        """주문 가능 금액 조회 성공 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "0",
            "output": {"ord_psbl_cash": "1000000", "max_buy_amt": "950000"},
        }

        result = self.api.get_possible_order_amount()

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")

        # API 호출 파라미터 확인
        self.client.make_request.assert_called_once()
        args, kwargs = self.client.make_request.call_args
        self.assertIn("params", kwargs)
        params = kwargs["params"]
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")
        self.assertEqual(params["CMA_EVLU_AMT_ICLD_YN"], "Y")
        self.assertEqual(params["OVRS_ICLD_YN"], "N")

    def test_get_possible_order_amount_exception(self):
        """주문 가능 금액 조회 예외 테스트

        @api_method(reraise=True) 기본값으로 인해 예외가 APIException으로 래핑되어 발생합니다.
        """
        self.client.make_request.side_effect = Exception("API 오류")

        with pytest.raises(APIException):
            self.api.get_possible_order_amount()

    def test_account_info_validation(self):
        """계좌 정보 유효성 검증 테스트"""
        # 올바른 계좌 정보로 초기화된 API 확인
        self.assertEqual(self.api.account["CANO"], "12345678")
        self.assertEqual(self.api.account["ACNT_PRDT_CD"], "01")

        # 다른 계좌 정보로 새 API 생성
        different_account = {"CANO": "87654321", "ACNT_PRDT_CD": "02"}
        different_api = AccountAPI(self.client, different_account)
        self.assertEqual(different_api.account["CANO"], "87654321")
        self.assertEqual(different_api.account["ACNT_PRDT_CD"], "02")


class TestAccountAPIPeriodProfit(unittest.TestCase):
    """기간별 손익 조회 메서드들 테스트"""

    def setUp(self):
        """각 테스트마다 새로운 인스턴스 생성"""
        self.client = MagicMock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = AccountAPI(self.client, self.account_info, enable_cache=False)

    def test_inquire_period_trade_profit_success(self):
        """기간별매매손익현황조회 성공 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "0",
            "msg1": "정상 처리되었습니다.",
            "output1": [
                {
                    "trad_dt": "20250101",
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "trad_dvsn_name": "매도",
                    "sll_qty": "10",
                    "sll_amt": "650000",
                    "rlzt_pfls": "50000",
                    "pfls_rt": "8.33",
                },
            ],
            "output2": {
                "sll_qty_smtl": "10",
                "sll_tr_amt_smtl": "650000",
                "tot_rlzt_pfls": "50000",
            },
        }

        result = self.api.inquire_period_trade_profit(
            start_date="20250101",
            end_date="20250131",
        )

        self.assertIsNotNone(result)
        # DataFrame 반환 확인 (as_dict=False 기본값)
        import pandas as pd

        self.assertIsInstance(result, pd.DataFrame)

        # API 호출 파라미터 확인
        self.client.make_request.assert_called_once()
        args, kwargs = self.client.make_request.call_args
        params = kwargs["params"]
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")
        self.assertEqual(params["INQR_STRT_DT"], "20250101")
        self.assertEqual(params["INQR_END_DT"], "20250131")

    def test_inquire_period_trade_profit_with_optional_params(self):
        """기간별매매손익현황조회 선택 파라미터 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "0",
            "output1": [{"trad_dt": "20250101", "pdno": "005930"}],
            "output2": {"tot_rlzt_pfls": "50000"},
        }

        result = self.api.inquire_period_trade_profit(
            start_date="20250101",
            end_date="20250131",
            pdno="005930",
            sort_dvsn="01",
            cblc_dvsn="01",
        )

        # API 호출 파라미터 확인
        args, kwargs = self.client.make_request.call_args
        params = kwargs["params"]
        self.assertEqual(params["PDNO"], "005930")
        self.assertEqual(params["SORT_DVSN"], "01")
        self.assertEqual(params["CBLC_DVSN"], "01")

    def test_inquire_period_trade_profit_as_dict(self):
        """기간별매매손익현황조회 Dict 반환 테스트"""
        expected_response = {
            "rt_cd": "0",
            "output1": [{"trad_dt": "20250101"}],
            "output2": {"tot_rlzt_pfls": "50000"},
        }
        self.client.make_request.return_value = expected_response

        result = self.api.inquire_period_trade_profit(
            start_date="20250101",
            end_date="20250131",
            as_dict=True,
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["rt_cd"], "0")
        self.assertIn("output1", result)
        self.assertIn("output2", result)

    def test_get_period_trade_profit_success(self):
        """get_period_trade_profit 헬퍼 메서드 테스트"""
        expected_response = {
            "rt_cd": "0",
            "output1": [{"trad_dt": "20250101", "rlzt_pfls": "50000"}],
            "output2": {"tot_rlzt_pfls": "50000"},
        }
        self.client.make_request.return_value = expected_response

        result = self.api.get_period_trade_profit(
            start_date="20250101",
            end_date="20250131",
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["rt_cd"], "0")

    def test_inquire_period_profit_success(self):
        """기간별손익일별합산조회 성공 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "0",
            "msg1": "정상 처리되었습니다.",
            "output1": [
                {
                    "trad_dt": "20250101",
                    "sll_amt": "650000",
                    "buy_amt": "600000",
                    "rlzt_pfls": "50000",
                    "fee_smtl": "1000",
                    "tltx_smtl": "500",
                    "tot_rlzt_pfls": "48500",
                },
                {
                    "trad_dt": "20250102",
                    "sll_amt": "700000",
                    "buy_amt": "680000",
                    "rlzt_pfls": "20000",
                    "fee_smtl": "800",
                    "tltx_smtl": "400",
                    "tot_rlzt_pfls": "18800",
                },
            ],
            "output2": {
                "tot_sll_amt": "1350000",
                "tot_buy_amt": "1280000",
                "tot_rlzt_pfls": "67300",
            },
        }

        result = self.api.inquire_period_profit(
            start_date="20250101",
            end_date="20250131",
        )

        self.assertIsNotNone(result)
        # DataFrame 반환 확인
        import pandas as pd

        self.assertIsInstance(result, pd.DataFrame)

        # API 호출 파라미터 확인
        self.client.make_request.assert_called_once()
        args, kwargs = self.client.make_request.call_args
        params = kwargs["params"]
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")
        self.assertEqual(params["INQR_STRT_DT"], "20250101")
        self.assertEqual(params["INQR_END_DT"], "20250131")
        self.assertEqual(params.get("CTX_AREA_FK200"), "")
        self.assertEqual(params.get("CTX_AREA_NK200"), "")

    def test_inquire_period_profit_as_dict(self):
        """기간별손익일별합산조회 Dict 반환 테스트"""
        expected_response = {
            "rt_cd": "0",
            "output1": [{"trad_dt": "20250101", "rlzt_pfls": "50000"}],
            "output2": {"tot_rlzt_pfls": "50000"},
        }
        self.client.make_request.return_value = expected_response

        result = self.api.inquire_period_profit(
            start_date="20250101",
            end_date="20250131",
            as_dict=True,
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["rt_cd"], "0")
        self.assertIn("output1", result)
        self.assertIn("output2", result)

    def test_get_period_profit_success(self):
        """get_period_profit 헬퍼 메서드 테스트"""
        expected_response = {
            "rt_cd": "0",
            "output1": [{"trad_dt": "20250101", "rlzt_pfls": "50000"}],
            "output2": {"tot_rlzt_pfls": "50000"},
        }
        self.client.make_request.return_value = expected_response

        result = self.api.get_period_profit(
            start_date="20250101",
            end_date="20250131",
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["rt_cd"], "0")

    def test_inquire_period_trade_profit_api_error(self):
        """기간별매매손익현황조회 API 오류 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "1",
            "msg1": "조회 결과가 없습니다.",
        }

        result = self.api.inquire_period_trade_profit(
            start_date="20250101",
            end_date="20250131",
            as_dict=True,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "1")

    def test_inquire_period_profit_no_data(self):
        """기간별손익일별합산조회 데이터 없음 테스트"""
        self.client.make_request.return_value = {
            "rt_cd": "0",
            "output1": [],
            "output2": {"tot_rlzt_pfls": "0"},
        }

        result = self.api.inquire_period_profit(
            start_date="20250101",
            end_date="20250131",
        )

        # 빈 output1이면 DataFrame이 비어있음
        import pandas as pd

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
