"""
Overseas Account API 모듈 테스트

해외주식 계좌 조회 API 단위 테스트
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from pykis.core.client import KISClient
from pykis.overseas.account_api import OverseasAccountAPI


class TestOverseasAccountAPIInit(unittest.TestCase):
    """OverseasAccountAPI 초기화 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    def test_init_with_account_info(self):
        """계좌 정보와 함께 초기화"""
        api = OverseasAccountAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )
        self.assertEqual(api.client, self.mock_client)
        self.assertEqual(api.account, self.account_info)

    def test_init_without_account_info(self):
        """계좌 정보 없이 초기화"""
        api = OverseasAccountAPI(client=self.mock_client, _from_agent=True)
        self.assertEqual(api.client, self.mock_client)
        self.assertIsNone(api.account)

    def test_get_account_params_success(self):
        """계좌 파라미터 반환 성공"""
        api = OverseasAccountAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )
        params = api._get_account_params()
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")

    def test_get_account_params_no_account(self):
        """계좌 정보 없이 파라미터 요청 시 에러"""
        api = OverseasAccountAPI(client=self.mock_client, _from_agent=True)
        with self.assertRaises(ValueError) as context:
            api._get_account_params()
        self.assertIn("계좌 정보가 설정되지 않았습니다", str(context.exception))


class TestOverseasAccountAPIBalance(unittest.TestCase):
    """OverseasAccountAPI 잔고 조회 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasAccountAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_get_balance_default(self):
        """잔고 조회 기본값"""
        expected_result = {
            "rt_cd": "0",
            "output1": [{"ovrs_pdno": "AAPL", "ovrs_cblc_qty": "10"}],
            "output2": {"tot_evlu_pfls_amt": "1000.00"},
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.get_balance()

        self.assertEqual(result, expected_result)
        self.api._make_request_dict.assert_called_once()
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTS3012R")
        self.assertEqual(call_args.kwargs["params"]["CANO"], "12345678")

    def test_get_balance_with_exchange(self):
        """특정 거래소 잔고 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.get_balance(ovrs_excg_cd="NASD", tr_crcy_cd="USD")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["OVRS_EXCG_CD"], "NASD")
        self.assertEqual(call_args.kwargs["params"]["TR_CRCY_CD"], "USD")


class TestOverseasAccountAPIOrderHistory(unittest.TestCase):
    """OverseasAccountAPI 주문체결내역 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasAccountAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_get_order_history_default(self):
        """주문체결내역 조회"""
        expected_result = {
            "rt_cd": "0",
            "output": [{"odno": "0001", "prdt_name": "APPLE INC"}],
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.get_order_history()

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTS3035R")
        self.assertFalse(call_args.kwargs["use_cache"])  # 실시간성 필요

    def test_get_order_history_with_sort(self):
        """정렬순서 지정 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.get_order_history(ovrs_excg_cd="NYSE", sort_sqn="AS")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["SORT_SQN"], "AS")


class TestOverseasAccountAPIUnfilledOrders(unittest.TestCase):
    """OverseasAccountAPI 미체결내역 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasAccountAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_get_unfilled_orders(self):
        """미체결내역 조회"""
        expected_result = {
            "rt_cd": "0",
            "output": [{"odno": "0002", "nccs_qty": "5"}],
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.get_unfilled_orders()

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTS3018R")


class TestOverseasAccountAPIBuyableAmount(unittest.TestCase):
    """OverseasAccountAPI 매수가능금액 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasAccountAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_get_buyable_amount(self):
        """매수가능금액 조회"""
        expected_result = {
            "rt_cd": "0",
            "output": {"frcr_ord_psbl_amt1": "10000.00", "max_ord_psbl_qty": "50"},
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.get_buyable_amount("NASD", item_cd="AAPL")

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTS3007R")
        self.assertEqual(call_args.kwargs["params"]["OVRS_EXCG_CD"], "NASD")
        self.assertEqual(call_args.kwargs["params"]["ITEM_CD"], "AAPL")

    def test_get_buyable_amount_market_order(self):
        """시장가 매수가능금액 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.get_buyable_amount("NYSE", ovrs_ord_unpr="0")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["OVRS_ORD_UNPR"], "0")


class TestOverseasAccountAPIPresentBalance(unittest.TestCase):
    """OverseasAccountAPI 체결기준현재잔고 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasAccountAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_get_present_balance_default(self):
        """체결기준현재잔고 조회 기본값"""
        expected_result = {
            "rt_cd": "0",
            "output1": [{"prdt_name": "APPLE INC", "ovrs_cblc_qty": "10"}],
            "output2": {"evlu_pfls_amt_smtl": "500.00"},
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.get_present_balance()

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "CTRP6504R")
        self.assertEqual(
            call_args.kwargs["params"]["WCRC_FRCR_DVSN_CD"], "02"
        )  # 기본값: 외화

    def test_get_present_balance_krw(self):
        """원화 기준 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.get_present_balance(wcrc_frcr_dvsn_cd="01")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["WCRC_FRCR_DVSN_CD"], "01")


class TestOverseasAccountAPIPeriodProfit(unittest.TestCase):
    """OverseasAccountAPI 기간손익 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasAccountAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_get_period_profit(self):
        """기간손익 조회"""
        expected_result = {
            "rt_cd": "0",
            "output1": [{"ovrs_pdno": "AAPL", "ovrs_rlzt_pfls_amt": "100.00"}],
            "output2": {"ovrs_rlzt_pfls_amt": "100.00"},
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.get_period_profit(
            inqr_strt_dt="20250101",
            inqr_end_dt="20250107",
        )

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTS3039R")
        self.assertEqual(call_args.kwargs["params"]["INQR_STRT_DT"], "20250101")
        self.assertEqual(call_args.kwargs["params"]["INQR_END_DT"], "20250107")


class TestOverseasAccountAPIReserveOrder(unittest.TestCase):
    """OverseasAccountAPI 예약주문 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasAccountAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_get_reserve_order_list(self):
        """예약주문내역 조회"""
        expected_result = {
            "rt_cd": "0",
            "output": [{"rsvn_ord_seq": "001", "prdt_name": "APPLE INC"}],
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.get_reserve_order_list()

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTT3039R")


class TestOverseasAccountAPIForeignMargin(unittest.TestCase):
    """OverseasAccountAPI 외화증거금 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasAccountAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_get_foreign_margin_all(self):
        """전체 외화증거금 조회"""
        expected_result = {
            "rt_cd": "0",
            "output": [{"crcy_cd": "USD", "frcr_ord_psbl_amt": "5000.00"}],
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.get_foreign_margin()

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTC2101R")
        self.assertEqual(call_args.kwargs["params"]["CRCY_CD"], "")

    def test_get_foreign_margin_usd(self):
        """USD 외화증거금 조회"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.get_foreign_margin(crcy_cd="USD")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["CRCY_CD"], "USD")


class TestOverseasAccountAPINoAccount(unittest.TestCase):
    """계좌 정보 없이 API 호출 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.api = OverseasAccountAPI(client=self.mock_client, _from_agent=True)

    def test_get_balance_no_account_raises(self):
        """계좌 없이 잔고 조회 시 에러"""
        with self.assertRaises(ValueError) as context:
            self.api.get_balance()
        self.assertIn("계좌 정보가 설정되지 않았습니다", str(context.exception))

    def test_get_order_history_no_account_raises(self):
        """계좌 없이 주문내역 조회 시 에러"""
        with self.assertRaises(ValueError):
            self.api.get_order_history()

    def test_get_buyable_amount_no_account_raises(self):
        """계좌 없이 매수가능금액 조회 시 에러"""
        with self.assertRaises(ValueError):
            self.api.get_buyable_amount("NASD")


if __name__ == "__main__":
    unittest.main()
