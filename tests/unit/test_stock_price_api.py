"""
Stock Price API 모듈 테스트

주식 시세 조회 API 기능을 종합적으로 테스트합니다.

테스트 대상 기능:
- 실시간 주식 현재가 조회 (get_stock_price)
- 일별 시세 데이터 조회 (get_daily_price) 
- 호가 정보 조회 (get_orderbook, get_orderbook_raw)
- 분봉 시세 데이터 (get_minute_price, get_daily_minute_price)

테스트 시나리오:
- 정상적인 API 응답 처리
- 다양한 파라미터 조합 테스트
- 에러 응답 및 예외 상황 처리
- 연속적인 API 호출 안정성
- 다양한 종목 코드에 대한 호환성
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from pykis.core.client import API_ENDPOINTS
from pykis.stock.price_api import StockPriceAPI


class TestStockPriceAPI(unittest.TestCase):
    """StockPriceAPI 테스트"""

    def setUp(self):
        self.mock_client = Mock()
        self.api = StockPriceAPI(client=self.mock_client, enable_cache=False)

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.api.client, self.mock_client)

    def test_get_stock_price_success(self):
        """주식 현재가 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"stck_prpr": "70000", "prdy_vrss": "1000"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_stock_price("005930")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_PRICE"],
            tr_id="FHKST01010100",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"},
        )

    def test_get_stock_price_failure(self):
        """주식 현재가 조회 실패"""
        self.mock_client.make_request.return_value = None

        result = self.api.get_stock_price("005930")

        self.assertIsNone(result)

    def test_get_daily_price_default_params(self):
        """일별 시세 조회 - 기본 파라미터"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {"stck_bsop_date": "20231215", "stck_clpr": "70000"},
                {"stck_bsop_date": "20231214", "stck_clpr": "69500"},
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_daily_price("005930")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_DAILY_ITEMCHARTPRICE"],
            tr_id="FHKST01010400",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": "005930",
                "fid_period_div_code": "D",
                "fid_org_adj_prc": "1",
            },
        )

    def test_get_daily_price_custom_params(self):
        """일별 시세 조회 - 커스텀 파라미터"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_daily_price("005930", period="W", org_adj_prc="0")

        self.assertEqual(result, expected_response)

        # 파라미터가 올바르게 설정되었는지 확인
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["fid_period_div_code"], "W")
        self.assertEqual(params["fid_org_adj_prc"], "0")

    def test_get_orderbook_success(self):
        """호가 정보 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {
                "askp1": "70100",
                "bidp1": "70000",
                "askp_rsqn1": "1000",
                "bidp_rsqn1": "1500",
            },
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_orderbook("005930")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_ASKING_PRICE_EXP_CCN"],
            tr_id="FHKST01010200",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"},
        )

    def test_get_orderbook_raw_success(self):
        """호가 원시 데이터 조회 성공"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": {"raw": "data"}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_orderbook_raw("005930")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_ASKING_PRICE_EXP_CCN"],
            tr_id="FHKST01010200",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"},
        )

    def test_get_minute_price_default_hour(self):
        """분봉 시세 조회 - 기본 시간"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {"stck_cntg_hour": "153000", "stck_prpr": "70000"},
                {"stck_cntg_hour": "152900", "stck_prpr": "69900"},
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_minute_price("005930")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_TIME_ITEMCHARTPRICE"],
            tr_id="FHKST01010300",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930",
                "FID_INPUT_HOUR_1": "153000",
            },
        )

    def test_get_minute_price_custom_hour(self):
        """분봉 시세 조회 - 커스텀 시간"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_minute_price("005930", hour="120000")

        self.assertEqual(result, expected_response)

        # 파라미터가 올바르게 설정되었는지 확인
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_INPUT_HOUR_1"], "120000")

    def test_get_daily_minute_price_success(self):
        """특정일 분봉 시세 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "stck_bsop_date": "20231215",
                    "stck_cntg_hour": "153000",
                    "stck_prpr": "70000",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_daily_minute_price("005930", "20231215")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_TIME_ITEMCHARTPRICE"],
            tr_id="FHKST01010300",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930",
                "FID_INPUT_DATE_1": "20231215",
                "FID_INPUT_HOUR_1": "153000",
            },
        )

    def test_get_daily_minute_price_custom_hour(self):
        """특정일 분봉 시세 조회 - 커스텀 시간"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_daily_minute_price("005930", "20231215", hour="090000")

        self.assertEqual(result, expected_response)

        # 파라미터가 올바르게 설정되었는지 확인
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_INPUT_DATE_1"], "20231215")
        self.assertEqual(params["FID_INPUT_HOUR_1"], "090000")

    def test_error_response_handling(self):
        """에러 응답 처리"""
        error_response = {"rt_cd": "1", "msg1": "종목코드 오류", "msg_cd": "EGW00123"}
        self.mock_client.make_request.return_value = error_response

        result = self.api.get_stock_price("INVALID")

        self.assertEqual(result, error_response)
        self.assertEqual(result["rt_cd"], "1")

    @patch("logging.error")
    def test_api_request_exception(self, mock_log):
        """API 요청 중 예외 발생"""
        self.mock_client.make_request.side_effect = Exception("Connection error")

        with self.assertRaises(Exception) as context:
            self.api.get_stock_price("005930")

        self.assertIn("API 요청 실패", str(context.exception))
        mock_log.assert_called_once()

    def test_multiple_consecutive_calls(self):
        """연속적인 API 호출"""
        responses = [
            {"rt_cd": "0", "output": {"stck_prpr": "70000"}},
            {"rt_cd": "0", "output": [{"stck_bsop_date": "20231215"}]},
            {"rt_cd": "0", "output": {"askp1": "70100"}},
        ]
        self.mock_client.make_request.side_effect = responses

        # 연속 호출
        result1 = self.api.get_stock_price("005930")
        result2 = self.api.get_daily_price("005930")
        result3 = self.api.get_orderbook("005930")

        # 결과 검증
        self.assertEqual(result1, responses[0])
        self.assertEqual(result2, responses[1])
        self.assertEqual(result3, responses[2])

        # 총 3번 호출되었는지 확인
        self.assertEqual(self.mock_client.make_request.call_count, 3)

    def test_different_stock_codes(self):
        """다양한 종목 코드 테스트"""
        test_codes = ["005930", "000660", "035420", "035720"]
        expected_responses = [
            {"rt_cd": "0", "output": {"code": code}} for code in test_codes
        ]
        self.mock_client.make_request.side_effect = expected_responses

        results = []
        for code in test_codes:
            result = self.api.get_stock_price(code)
            results.append(result)

        # 모든 결과가 예상대로인지 확인
        for i, result in enumerate(results):
            self.assertEqual(result, expected_responses[i])

        # 총 4번 호출되었는지 확인
        self.assertEqual(self.mock_client.make_request.call_count, 4)


if __name__ == "__main__":
    unittest.main()
