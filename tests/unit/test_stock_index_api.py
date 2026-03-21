"""
Stock Index API 모듈 테스트

주식 지수 시세 조회 API 기능을 종합적으로 테스트합니다.

테스트 대상 기능:
- 업종별 전체시세 조회 (inquire_index_category_price)
- 업종 현재지수 조회 (inquire_index_price) - deprecated
- 업종 시간별지수 틱 조회 (inquire_index_tickprice)
- 업종 지수 시간별 시세 조회 (inquire_index_timeprice)
- 지수 시간별 시세 조회 (get_index_timeprice)
- 지수 일자별 시세 조회 (get_index_daily_price)
- 선물옵션 시세 조회 (get_future_option_price)
- 선물옵션 호가창 조회 (get_future_orderbook)

테스트 시나리오:
- 정상적인 API 응답 처리
- 다양한 파라미터 조합 테스트
- 에러 응답 및 예외 상황 처리
- deprecation warning 테스트
- 자동 종목코드 생성 테스트
"""

import unittest
import warnings
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from kis_agent.core.client import API_ENDPOINTS
from kis_agent.stock.index_api import StockIndexAPI


class TestStockIndexAPI(unittest.TestCase):
    """StockIndexAPI 테스트"""

    def setUp(self):
        self.mock_client = Mock()
        self.api = StockIndexAPI(client=self.mock_client, enable_cache=False)

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.api.client, self.mock_client)

    def test_inquire_index_category_price_success(self):
        """업종별 전체시세 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output1": {"kospi_value": "2500.00"},
            "output2": [{"sector_name": "전기전자", "sector_value": "100.50"}],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_index_category_price("0001")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_CATEGORY_PRICE"],
            tr_id="FHPUP02140000",
            params={
                "FID_COND_MRKT_DIV_CODE": "U",
                "FID_INPUT_ISCD": "0001",
                "FID_COND_SCR_DIV_CODE": "20214",
                "FID_MRKT_CLS_CODE": "K",
                "FID_BLNG_CLS_CODE": "0",
            },
            method="GET",
        )

    def test_inquire_index_category_price_with_custom_params(self):
        """업종별 전체시세 조회 - 커스텀 파라미터"""
        expected_response = {"rt_cd": "0", "msg1": "성공"}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_index_category_price(
            index_code="1001",
            screen_code="20215",
            market_cls="Q",
            belong_cls="1",
            market="K",
        )

        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_CATEGORY_PRICE"],
            tr_id="FHPUP02140000",
            params={
                "FID_COND_MRKT_DIV_CODE": "K",
                "FID_INPUT_ISCD": "1001",
                "FID_COND_SCR_DIV_CODE": "20215",
                "FID_MRKT_CLS_CODE": "Q",
                "FID_BLNG_CLS_CODE": "1",
            },
            method="GET",
        )

    def test_inquire_index_price_deprecated_warning(self):
        """업종 현재지수 조회 - deprecation warning 테스트"""
        expected_response = {"rt_cd": "0", "msg1": "성공"}
        self.mock_client.make_request.return_value = expected_response

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self.api.inquire_index_price("0001")

            # Warning 발생 확인
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertIn("deprecated", str(w[0].message))

    def test_inquire_index_tickprice_success(self):
        """업종 시간별지수 틱 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"tick_time": "093000", "tick_value": "2500.00"}],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_index_tickprice("0001")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_TICKPRICE"],
            tr_id="FHPUP02110100",
            params={"FID_INPUT_ISCD": "0001", "FID_COND_MRKT_DIV_CODE": "U"},
            method="GET",
        )

    def test_inquire_index_timeprice_success(self):
        """업종 지수 시간별 시세 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"time": "093000", "value": "2500.00"}],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_index_timeprice("0001", time_div="300")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_TIMEPRICE"],
            tr_id="FHPUP02110200",
            params={
                "fid_cond_mrkt_div_code": "U",
                "fid_input_iscd": "0001",
                "fid_input_hour_1": "300",
            },
            method="GET",
        )

    def test_get_index_timeprice_default_params(self):
        """지수 시간별 시세 조회 - 기본값"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_index_timeprice()

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_TIMEPRICE"],
            tr_id="FHPUP02110200",
            params={
                "fid_cond_mrkt_div_code": "U",
                "fid_input_iscd": "1029",
                "fid_input_hour_1": "600",
            },
            method="GET",
        )

    def test_get_index_daily_price_default_params(self):
        """지수 일자별 시세 조회 - 기본값"""
        expected_response = {
            "rt_cd": "0",
            "output1": {"index_name": "KOSPI"},
            "output2": [{"stck_bsop_date": "20250101", "bstp_nmix_prpr": "2500.00"}],
        }
        self.mock_client.make_request.return_value = expected_response

        # 특정 날짜로 테스트 (현재 날짜 대신)
        result = self.api.get_index_daily_price(end_date="20250115")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_DAILY_PRICE"],
            tr_id="FHPUP02120000",
            params={
                "FID_PERIOD_DIV_CODE": "D",
                "FID_COND_MRKT_DIV_CODE": "U",
                "FID_INPUT_ISCD": "0001",
                "FID_INPUT_DATE_1": "20250115",
            },
            method="GET",
        )

    def test_get_index_daily_price_custom_params(self):
        """지수 일자별 시세 조회 - 커스텀 파라미터"""
        expected_response = {"rt_cd": "0", "output1": {}, "output2": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_index_daily_price(
            index_code="1001", end_date="20251201", period="W"
        )

        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_DAILY_PRICE"],
            tr_id="FHPUP02120000",
            params={
                "FID_PERIOD_DIV_CODE": "W",
                "FID_COND_MRKT_DIV_CODE": "U",
                "FID_INPUT_ISCD": "1001",
                "FID_INPUT_DATE_1": "20251201",
            },
            method="GET",
        )

    @patch("kis_agent.stock.api.get_kospi200_futures_code")
    def test_get_future_option_price_auto_code(self, mock_get_code):
        """선물옵션 시세 조회 - 자동 종목코드 생성"""
        mock_get_code.return_value = "101S03"
        expected_response = {
            "rt_cd": "0",
            "output": {"stck_prpr": "350.50"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_future_option_price()

        self.assertEqual(result, expected_response)
        mock_get_code.assert_called_once()
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["FUTUREOPTION_INQUIRE_PRICE"],
            tr_id="FHMIF10000000",
            params={
                "fid_cond_mrkt_div_code": "F",
                "fid_input_iscd": "101S03",
            },
            method="GET",
        )

    def test_get_future_option_price_manual_code(self):
        """선물옵션 시세 조회 - 수동 종목코드"""
        expected_response = {"rt_cd": "0", "output": {"stck_prpr": "370.25"}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_future_option_price("O", "201T12370")

        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["FUTUREOPTION_INQUIRE_PRICE"],
            tr_id="FHMIF10000000",
            params={
                "fid_cond_mrkt_div_code": "O",
                "fid_input_iscd": "201T12370",
            },
            method="GET",
        )

    def test_get_future_orderbook_success(self):
        """선물옵션 호가창 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "output1": {"current_price": "350.00"},
            "output2": {"askp1": "350.25", "bidp1": "349.75"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_future_orderbook("101S03")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["FUTUREOPTION_INQUIRE_ASKING_PRICE"],
            tr_id="FHMIF10010000",
            params={
                "FID_COND_MRKT_DIV_CODE": "F",
                "FID_INPUT_ISCD": "101S03",
            },
            method="GET",
        )

    def test_get_future_orderbook_option(self):
        """선물옵션 호가창 조회 - 옵션"""
        expected_response = {"rt_cd": "0", "output1": {}, "output2": {}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_future_orderbook("201W09370", "O")

        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["FUTUREOPTION_INQUIRE_ASKING_PRICE"],
            tr_id="FHMIF10010000",
            params={
                "FID_COND_MRKT_DIV_CODE": "O",
                "FID_INPUT_ISCD": "201W09370",
            },
            method="GET",
        )

    def test_api_error_handling(self):
        """API 오류 응답 처리"""
        error_response = None
        self.mock_client.make_request.return_value = error_response

        result = self.api.inquire_index_category_price("0001")
        self.assertIsNone(result)

        error_response = {"rt_cd": "1", "msg1": "오류 발생"}
        self.mock_client.make_request.return_value = error_response

        result = self.api.get_index_daily_price()
        self.assertEqual(result, error_response)


if __name__ == "__main__":
    unittest.main()
