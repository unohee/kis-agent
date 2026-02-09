"""
Overseas Order API 모듈 테스트

해외주식 주문 API 단위 테스트
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from kis_agent.core.client import KISClient
from kis_agent.overseas.order_api import OverseasOrderAPI


class TestOverseasOrderAPIInit(unittest.TestCase):
    """OverseasOrderAPI 초기화 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    def test_init_with_account_info(self):
        """계좌 정보와 함께 초기화"""
        api = OverseasOrderAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )
        self.assertEqual(api.client, self.mock_client)
        self.assertEqual(api.account, self.account_info)

    def test_init_without_account_info(self):
        """계좌 정보 없이 초기화"""
        api = OverseasOrderAPI(client=self.mock_client, _from_agent=True)
        self.assertEqual(api.client, self.mock_client)
        self.assertIsNone(api.account)

    def test_get_account_params_success(self):
        """계좌 파라미터 반환 성공"""
        api = OverseasOrderAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )
        params = api._get_account_params()
        self.assertEqual(params["CANO"], "12345678")
        self.assertEqual(params["ACNT_PRDT_CD"], "01")

    def test_get_account_params_no_account(self):
        """계좌 정보 없이 파라미터 요청 시 에러"""
        api = OverseasOrderAPI(client=self.mock_client, _from_agent=True)
        with self.assertRaises(ValueError) as context:
            api._get_account_params()
        self.assertIn("계좌 정보가 설정되지 않았습니다", str(context.exception))


class TestOverseasOrderAPIExchangeNormalization(unittest.TestCase):
    """거래소 코드 정규화 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasOrderAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_normalize_exchange_nas_to_nasd(self):
        """NAS -> NASD 변환"""
        self.assertEqual(self.api._normalize_exchange("NAS"), "NASD")

    def test_normalize_exchange_nys_to_nyse(self):
        """NYS -> NYSE 변환"""
        self.assertEqual(self.api._normalize_exchange("NYS"), "NYSE")

    def test_normalize_exchange_ams_to_amex(self):
        """AMS -> AMEX 변환"""
        self.assertEqual(self.api._normalize_exchange("AMS"), "AMEX")

    def test_normalize_exchange_hks_to_sehk(self):
        """HKS -> SEHK 변환"""
        self.assertEqual(self.api._normalize_exchange("HKS"), "SEHK")

    def test_normalize_exchange_direct_use(self):
        """직접 코드 사용 허용"""
        self.assertEqual(self.api._normalize_exchange("NASD"), "NASD")
        self.assertEqual(self.api._normalize_exchange("NYSE"), "NYSE")

    def test_normalize_exchange_case_insensitive(self):
        """대소문자 구분 없음"""
        self.assertEqual(self.api._normalize_exchange("nas"), "NASD")
        self.assertEqual(self.api._normalize_exchange("Nys"), "NYSE")

    def test_normalize_exchange_invalid(self):
        """잘못된 거래소 코드"""
        with self.assertRaises(ValueError) as context:
            self.api._normalize_exchange("INVALID")
        self.assertIn("지원하지 않는 거래소 코드", str(context.exception))


class TestOverseasOrderAPIBuyOrder(unittest.TestCase):
    """OverseasOrderAPI 매수주문 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasOrderAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_buy_order_default(self):
        """매수주문 기본값"""
        expected_result = {
            "rt_cd": "0",
            "output": {"odno": "0001234", "ord_tmd": "093000"},
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.buy_order("NASD", "AAPL", 10, 185.00)

        self.assertEqual(result, expected_result)
        self.api._make_request_dict.assert_called_once()
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTT1002U")
        self.assertEqual(call_args.kwargs["method"], "POST")
        self.assertFalse(call_args.kwargs["use_cache"])
        self.assertEqual(call_args.kwargs["params"]["OVRS_EXCG_CD"], "NASD")
        self.assertEqual(call_args.kwargs["params"]["PDNO"], "AAPL")
        self.assertEqual(call_args.kwargs["params"]["ORD_QTY"], "10")
        self.assertEqual(call_args.kwargs["params"]["OVRS_ORD_UNPR"], "185.0")

    def test_buy_order_with_exchange_conversion(self):
        """거래소 코드 변환 매수"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.buy_order("NAS", "TSLA", 5, 250.00)

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["OVRS_EXCG_CD"], "NASD")

    def test_buy_order_moo(self):
        """MOO 주문 (시장 개장시 시장가)"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.buy_order("NASD", "AAPL", 10, 0, ord_dvsn="31")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["ORD_DVSN"], "31")


class TestOverseasOrderAPISellOrder(unittest.TestCase):
    """OverseasOrderAPI 매도주문 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasOrderAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_sell_order_default(self):
        """매도주문 기본값"""
        expected_result = {
            "rt_cd": "0",
            "output": {"odno": "0001235", "ord_tmd": "093100"},
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.sell_order("NYSE", "MSFT", 5, 350.00)

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTT1006U")
        self.assertEqual(call_args.kwargs["params"]["OVRS_EXCG_CD"], "NYSE")
        self.assertEqual(call_args.kwargs["params"]["PDNO"], "MSFT")

    def test_sell_order_moc(self):
        """MOC 주문 (시장 마감시 시장가)"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.sell_order("NASD", "AAPL", 10, 0, ord_dvsn="33")

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["ORD_DVSN"], "33")


class TestOverseasOrderAPIModifyOrder(unittest.TestCase):
    """OverseasOrderAPI 정정주문 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasOrderAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_modify_order(self):
        """정정주문"""
        expected_result = {
            "rt_cd": "0",
            "output": {"odno": "0001236", "ord_tmd": "094000"},
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.modify_order("NASD", "AAPL", "0001234", 10, 190.00)

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTT1004U")
        self.assertEqual(call_args.kwargs["params"]["ORGN_ODNO"], "0001234")
        self.assertEqual(call_args.kwargs["params"]["RVSE_CNCL_DVSN_CD"], "01")  # 정정
        self.assertEqual(call_args.kwargs["params"]["ORD_QTY"], "10")
        self.assertEqual(call_args.kwargs["params"]["OVRS_ORD_UNPR"], "190.0")


class TestOverseasOrderAPICancelOrder(unittest.TestCase):
    """OverseasOrderAPI 취소주문 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasOrderAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_cancel_order(self):
        """취소주문"""
        expected_result = {
            "rt_cd": "0",
            "output": {"odno": "0001237", "ord_tmd": "094500"},
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.cancel_order("NASD", "AAPL", "0001234", 10)

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTT1003U")
        self.assertEqual(call_args.kwargs["params"]["ORGN_ODNO"], "0001234")
        self.assertEqual(call_args.kwargs["params"]["RVSE_CNCL_DVSN_CD"], "02")  # 취소
        self.assertEqual(
            call_args.kwargs["params"]["OVRS_ORD_UNPR"], "0"
        )  # 취소 시 가격 0


class TestOverseasOrderAPIReserveOrder(unittest.TestCase):
    """OverseasOrderAPI 예약주문 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasOrderAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_reserve_order_buy(self):
        """예약 매수주문"""
        expected_result = {
            "rt_cd": "0",
            "output": {"rsvn_ord_seq": "001"},
        }
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.reserve_order("NASD", "AAPL", "02", 10, 180.00)

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTS6036U")
        self.assertEqual(call_args.kwargs["params"]["SLL_BUY_DVSN_CD"], "02")  # 매수
        self.assertEqual(call_args.kwargs["params"]["RSVN_ORD_QTY"], "10")
        self.assertEqual(call_args.kwargs["params"]["RSVN_ORD_UNPR"], "180.0")

    def test_reserve_order_sell(self):
        """예약 매도주문"""
        self.api._make_request_dict = Mock(return_value={"rt_cd": "0"})

        self.api.reserve_order(
            "NASD", "AAPL", "01", 5, 200.00, rsvn_ord_end_dt="20250131"
        )

        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["params"]["SLL_BUY_DVSN_CD"], "01")  # 매도
        self.assertEqual(call_args.kwargs["params"]["RSVN_ORD_END_DT"], "20250131")


class TestOverseasOrderAPIModifyReserveOrder(unittest.TestCase):
    """OverseasOrderAPI 예약주문 정정 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasOrderAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_modify_reserve_order(self):
        """예약주문 정정"""
        expected_result = {"rt_cd": "0", "output": {"rsvn_ord_seq": "001"}}
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.modify_reserve_order("001", 15, 175.00)

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTS6037U")
        self.assertEqual(call_args.kwargs["params"]["RSVN_ORD_SEQ"], "001")
        self.assertEqual(call_args.kwargs["params"]["RSVN_ORD_QTY"], "15")
        self.assertEqual(call_args.kwargs["params"]["RSVN_ORD_UNPR"], "175.0")


class TestOverseasOrderAPICancelReserveOrder(unittest.TestCase):
    """OverseasOrderAPI 예약주문 취소 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
        self.api = OverseasOrderAPI(
            client=self.mock_client,
            account_info=self.account_info,
            _from_agent=True,
        )

    def test_cancel_reserve_order(self):
        """예약주문 취소"""
        expected_result = {"rt_cd": "0", "output": {"rsvn_ord_seq": "001"}}
        self.api._make_request_dict = Mock(return_value=expected_result)

        result = self.api.cancel_reserve_order("001")

        self.assertEqual(result, expected_result)
        call_args = self.api._make_request_dict.call_args
        self.assertEqual(call_args.kwargs["tr_id"], "TTTS6038U")
        self.assertEqual(call_args.kwargs["params"]["RSVN_ORD_SEQ"], "001")


class TestOverseasOrderAPINoAccount(unittest.TestCase):
    """계좌 정보 없이 API 호출 테스트"""

    def setUp(self):
        self.mock_client = Mock(spec=KISClient)
        self.api = OverseasOrderAPI(client=self.mock_client, _from_agent=True)

    def test_buy_order_no_account_raises(self):
        """계좌 없이 매수 시 에러"""
        with self.assertRaises(ValueError) as context:
            self.api.buy_order("NASD", "AAPL", 10, 185.00)
        self.assertIn("계좌 정보가 설정되지 않았습니다", str(context.exception))

    def test_sell_order_no_account_raises(self):
        """계좌 없이 매도 시 에러"""
        with self.assertRaises(ValueError):
            self.api.sell_order("NASD", "AAPL", 10, 190.00)

    def test_modify_order_no_account_raises(self):
        """계좌 없이 정정 시 에러"""
        with self.assertRaises(ValueError):
            self.api.modify_order("NASD", "AAPL", "0001234", 10, 190.00)

    def test_cancel_order_no_account_raises(self):
        """계좌 없이 취소 시 에러"""
        with self.assertRaises(ValueError):
            self.api.cancel_order("NASD", "AAPL", "0001234", 10)

    def test_reserve_order_no_account_raises(self):
        """계좌 없이 예약주문 시 에러"""
        with self.assertRaises(ValueError):
            self.api.reserve_order("NASD", "AAPL", "02", 10, 180.00)


if __name__ == "__main__":
    unittest.main()
