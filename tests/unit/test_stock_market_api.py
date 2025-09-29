"""
Stock Market API 모듈 테스트

시장 정보 및 순위 조회 API 기능을 종합적으로 테스트합니다.

테스트 대상 기능:
- 시장 변동성 정보 조회 (get_market_fluctuation)
- 거래량 기준 종목 순위 (get_market_rankings)
- 체결강도 순위 조회 (get_volume_power)
- 종목 기본 정보 조회 (get_stock_info)

테스트 시나리오:
- 기본 파라미터와 커스텀 파라미터 처리
- API 응답 구조 검증
- 에러 처리 및 예외 상황 대응
- 다양한 거래량 조건에 대한 테스트
- 잘못된 종목코드 처리
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from pykis.core.client import API_ENDPOINTS
from pykis.stock.market_api import StockMarketAPI


class TestStockMarketAPI(unittest.TestCase):
    """StockMarketAPI 테스트"""

    def setUp(self):
        self.mock_client = Mock()
        self.api = StockMarketAPI(client=self.mock_client, enable_cache=False)

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.api.client, self.mock_client)

    def test_get_market_fluctuation_success(self):
        """시장 변동성 정보 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"market_data": "test"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_market_fluctuation()

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_ASKING_PRICE_EXP_CCN"],
            tr_id="FHKST01010600",
            params={"FID_COND_MRKT_DIV_CODE": "J"},
        )

    def test_get_market_fluctuation_failure(self):
        """시장 변동성 정보 조회 실패"""
        self.mock_client.make_request.return_value = None

        result = self.api.get_market_fluctuation()

        self.assertIsNone(result)

    def test_get_market_rankings_default_volume(self):
        """거래량 순위 조회 - 기본 거래량"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"rank": 1, "code": "005930"}],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_market_rankings()

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_INVESTOR"],
            tr_id="FHKST01010900",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": "20171",
                "FID_INPUT_ISCD": "0000",
                "FID_RANK_SORT_CLS_CODE": "0",
                "FID_INPUT_CNT_1": "50",
                "FID_PRC_CLS_CODE": "1",
                "FID_INPUT_PRICE_1": "",
                "FID_INPUT_PRICE_2": "",
                "FID_VOL_CNT": "5000000",
            },
        )

    def test_get_market_rankings_custom_volume(self):
        """거래량 순위 조회 - 커스텀 거래량"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"rank": 1, "code": "005930"}],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_market_rankings(volume=10000000)

        self.assertEqual(result, expected_response)

        # 파라미터에서 volume이 올바르게 설정되었는지 확인
        call_args = self.mock_client.make_request.call_args
        self.assertEqual(call_args[1]["params"]["FID_VOL_CNT"], "10000000")

    def test_get_volume_power_default_volume(self):
        """체결강도 순위 조회 - 기본 거래량"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"code": "005930", "power": "150.5"}],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_volume_power()

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_INVESTOR"],
            tr_id="FHKST01010900",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": "20171",
                "FID_INPUT_ISCD": "0000",
                "FID_RANK_SORT_CLS_CODE": "0",
                "FID_INPUT_CNT_1": "50",
                "FID_PRC_CLS_CODE": "1",
                "FID_INPUT_PRICE_1": "",
                "FID_INPUT_PRICE_2": "",
                "FID_VOL_CNT": "0",
            },
        )

    def test_get_volume_power_custom_volume(self):
        """체결강도 순위 조회 - 커스텀 거래량"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"code": "005930", "power": "150.5"}],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_volume_power(volume=1000000)

        self.assertEqual(result, expected_response)

        # 파라미터에서 volume이 올바르게 설정되었는지 확인
        call_args = self.mock_client.make_request.call_args
        self.assertEqual(call_args[1]["params"]["FID_VOL_CNT"], "1000000")

    def test_get_stock_info_success(self):
        """종목 기본 정보 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"code": "005930", "name": "삼성전자"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_stock_info("005930")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_PRICE"],
            tr_id="FHKST01010100",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"},
        )

    def test_get_stock_info_invalid_ticker(self):
        """잘못된 종목코드로 정보 조회"""
        error_response = {"rt_cd": "1", "msg1": "종목코드 오류", "output": None}
        self.mock_client.make_request.return_value = error_response

        result = self.api.get_stock_info("INVALID")

        self.assertEqual(result, error_response)

    @patch("logging.error")
    def test_api_request_exception(self, mock_log):
        """API 요청 중 예외 발생"""
        self.mock_client.make_request.side_effect = Exception("Network error")

        with self.assertRaises(Exception) as context:
            self.api.get_market_fluctuation()

        self.assertIn("API 요청 실패", str(context.exception))
        mock_log.assert_called_once()

    def test_multiple_api_calls(self):
        """여러 API 연속 호출"""
        responses = [
            {"rt_cd": "0", "output": {"market": "data1"}},
            {"rt_cd": "0", "output": [{"rank": 1}]},
            {"rt_cd": "0", "output": {"stock": "info"}},
        ]
        self.mock_client.make_request.side_effect = responses

        # 연속 호출
        result1 = self.api.get_market_fluctuation()
        result2 = self.api.get_market_rankings()
        result3 = self.api.get_stock_info("005930")

        # 결과 검증
        self.assertEqual(result1, responses[0])
        self.assertEqual(result2, responses[1])
        self.assertEqual(result3, responses[2])

        # 총 3번 호출되었는지 확인
        self.assertEqual(self.mock_client.make_request.call_count, 3)


if __name__ == "__main__":
    unittest.main()
