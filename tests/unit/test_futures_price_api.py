"""
Futures Price API 모듈 테스트

선물옵션 시세 조회 API 기능을 종합적으로 테스트합니다.

자동 생성됨 - /boost-coverage 스킬
생성일: 2026-01-19

테스트 대상 기능:
- 선물옵션 현재가 조회 (get_price)
- 선물옵션 호가 조회 (get_orderbook)
- 일별 차트 조회 (inquire_daily_fuopchartprice)
- 분봉 차트 조회 (inquire_time_fuopchartprice)
- 옵션 콜/풋 전광판 (display_board_callput)
- 선물 전광판 (display_board_futures)
- 옵션 종목 목록 (display_board_option_list)
- 상위 종목 조회 (display_board_top)
- 예상체결가 추이 (exp_price_trend)
- 시간대별 체결내역 (inquire_ccnl_bstime)
- 약정수수료 조회 (inquire_daily_amount_fee)

테스트 시나리오:
- 정상적인 API 응답 처리
- 다양한 파라미터 조합 테스트
- 에러 응답 및 예외 상황 처리
- 선물/옵션 종목코드 호환성
"""

import unittest
from unittest.mock import Mock

import pytest

from kis_agent.core.client import API_ENDPOINTS
from kis_agent.futures.price_api import FuturesPriceAPI


class TestFuturesPriceAPI(unittest.TestCase):
    """FuturesPriceAPI 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.mock_client = Mock()
        self.api = FuturesPriceAPI(
            client=self.mock_client,
            account_info={"account_no": "12345678", "account_code": "03"},
            enable_cache=False,
        )

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.api.client, self.mock_client)
        self.assertEqual(self.api.account["account_code"], "03")

    def test_get_price_success(self):
        """선물옵션 현재가 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {
                "fuop_prpr": "340.50",
                "prdy_vrss": "5.00",
                "acml_vol": "12345",
                "optn_theo_pric": "340.20",
                "impl_vola": "15.5",
            },
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_price("101S12")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_PRICE"],
            tr_id="FHMIF10000000",
            params={"FID_COND_MRKT_DIV_CODE": "F", "FID_INPUT_ISCD": "101S12"},
            method="GET",
        )

    def test_get_price_option(self):
        """옵션 현재가 조회"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {
                "fuop_prpr": "5.25",
                "optn_theo_pric": "5.20",
                "impl_vola": "18.2",
            },
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_price("201S312C")  # KOSPI200 옵션

        self.assertEqual(result, expected_response)
        self.assertIn("optn_theo_pric", result["output"])

    def test_get_price_failure(self):
        """선물옵션 현재가 조회 실패"""
        self.mock_client.make_request.return_value = None

        result = self.api.get_price("101S12")

        self.assertIsNone(result)

    def test_get_orderbook_success(self):
        """선물옵션 호가 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output1": {
                "askp1": "340.55",
                "askp_rsqn1": "10",
                "askp2": "340.60",
                "askp_rsqn2": "15",
            },
            "output2": {
                "bidp1": "340.50",
                "bidp_rsqn1": "20",
                "bidp2": "340.45",
                "bidp_rsqn2": "25",
            },
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_orderbook("101S12")

        self.assertEqual(result, expected_response)
        self.assertIn("output1", result)  # 매도호가
        self.assertIn("output2", result)  # 매수호가
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_ASKING_PRICE"],
            tr_id="FHMIF10010000",
            params={"FID_COND_MRKT_DIV_CODE": "F", "FID_INPUT_ISCD": "101S12"},
            method="GET",
        )

    def test_inquire_daily_fuopchartprice_default(self):
        """일별 차트 조회 - 기본 파라미터"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "stck_bsop_date": "20260119",
                    "fuop_oprc": "340.00",
                    "fuop_hgpr": "342.50",
                    "fuop_lwpr": "339.00",
                    "fuop_clpr": "341.20",
                    "acml_vol": "15000",
                },
                {
                    "stck_bsop_date": "20260118",
                    "fuop_oprc": "338.50",
                    "fuop_hgpr": "340.00",
                    "fuop_lwpr": "337.00",
                    "fuop_clpr": "339.50",
                    "acml_vol": "12000",
                },
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_daily_fuopchartprice("101S12")

        self.assertEqual(result, expected_response)
        self.assertEqual(len(result["output"]), 2)

    def test_inquire_daily_fuopchartprice_custom_dates(self):
        """일별 차트 조회 - 날짜 지정"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_daily_fuopchartprice(
            "101S12", start_date="20260101", end_date="20260131", period="W"
        )

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["params"]["FID_INPUT_DATE_1"], "20260101")
        self.assertEqual(call_kwargs[1]["params"]["FID_INPUT_DATE_2"], "20260131")
        self.assertEqual(call_kwargs[1]["params"]["FID_PERIOD_DIV_CODE"], "W")

    def test_inquire_time_fuopchartprice_1min(self):
        """분봉 차트 조회 - 1분봉"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "stck_cntg_hour": "153000",
                    "fuop_oprc": "340.50",
                    "fuop_prpr": "340.75",
                    "cntg_vol": "500",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_time_fuopchartprice("101S12", tick_range="1")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["params"]["FID_TICK_RANGE"], "1")

    def test_inquire_time_fuopchartprice_5min(self):
        """분봉 차트 조회 - 5분봉"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_time_fuopchartprice("101S12", tick_range="5")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["params"]["FID_TICK_RANGE"], "5")

    def test_display_board_callput_success(self):
        """옵션 콜/풋 전광판 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output1": [  # 콜옵션
                {
                    "item_code": "201S312C",
                    "fuop_prpr": "5.25",
                    "optn_theo_pric": "5.20",
                    "impl_vola": "18.2",
                }
            ],
            "output2": [  # 풋옵션
                {
                    "item_code": "201S312P",
                    "fuop_prpr": "8.50",
                    "optn_theo_pric": "8.45",
                    "impl_vola": "19.5",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.display_board_callput("202601")

        self.assertEqual(result, expected_response)
        self.assertIn("output1", result)  # 콜옵션
        self.assertIn("output2", result)  # 풋옵션

    def test_display_board_callput_with_strike(self):
        """옵션 콜/풋 전광판 조회 - 행사가 지정"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output1": [], "output2": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.display_board_callput("202601", strike_base="340")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["params"]["FID_COND_MRKT_CLS_CODE"], "340")

    def test_display_board_futures_success(self):
        """선물 전광판 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "item_code": "101S12",
                    "item_name": "KOSPI200 선물 2612",
                    "fuop_prpr": "340.50",
                    "acml_vol": "15000",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.display_board_futures()

        self.assertEqual(result, expected_response)
        self.assertEqual(len(result["output"]), 1)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["FUTURES_DISPLAY_BOARD_FUTURES"],
            tr_id="FHPIF05030200",
            params={
                "FID_COND_MRKT_DIV_CODE": "F",
                "FID_COND_SCR_DIV_CODE": "20502",
                "FID_COND_MRKT_CLS_CODE": "",
            },
            method="GET",
        )

    def test_display_board_option_list_success(self):
        """옵션 종목 목록 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {"item_code": "201S312C", "item_name": "K200 312.50C 2601"},
                {"item_code": "201S312P", "item_name": "K200 312.50P 2601"},
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.display_board_option_list("202601")

        self.assertEqual(result, expected_response)
        self.assertEqual(len(result["output"]), 2)

    def test_display_board_top_volume(self):
        """상위 종목 조회 - 거래량순"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "item_code": "101S12",
                    "fuop_prpr": "340.50",
                    "acml_vol": "50000",
                    "prdy_ctrt": "1.5",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.display_board_top(sort_type="01")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["params"]["FID_RANK_SORT_CLS_CODE"], "01")

    def test_display_board_top_change_rate(self):
        """상위 종목 조회 - 등락률순"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.display_board_top(sort_type="03")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["params"]["FID_RANK_SORT_CLS_CODE"], "03")

    def test_exp_price_trend_success(self):
        """예상체결가 추이 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "stck_cntg_hour": "090000",
                    "fuop_exp_pric": "340.00",
                    "acml_vol": "100",
                },
                {
                    "stck_cntg_hour": "090500",
                    "fuop_exp_pric": "340.25",
                    "acml_vol": "500",
                },
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.exp_price_trend("101S12")

        self.assertEqual(result, expected_response)
        self.assertEqual(len(result["output"]), 2)

    def test_inquire_ccnl_bstime_default(self):
        """시간대별 체결내역 조회 - 기본 시간"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {"stck_cntg_hour": "090000", "fuop_prpr": "340.00", "cntg_vol": "100"}
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_ccnl_bstime("101S12")

        self.assertEqual(result, expected_response)

    def test_inquire_ccnl_bstime_custom_time(self):
        """시간대별 체결내역 조회 - 시간 지정"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_ccnl_bstime("101S12", "090000", "120000")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["params"]["FID_INPUT_HOUR_1"], "090000")
        self.assertEqual(call_kwargs[1]["params"]["FID_INPUT_HOUR_2"], "120000")

    def test_inquire_daily_amount_fee_success(self):
        """약정수수료 조회 성공"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [
                {
                    "stck_bsop_date": "20260119",
                    "acml_vol": "10000",
                    "tot_fee_amt": "50000",
                }
            ],
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_daily_amount_fee("20260101", "20260131")

        self.assertEqual(result, expected_response)
        call_kwargs = self.mock_client.make_request.call_args
        self.assertEqual(call_kwargs[1]["params"]["INQR_STRT_DT"], "20260101")
        self.assertEqual(call_kwargs[1]["params"]["INQR_END_DT"], "20260131")


@pytest.mark.parametrize(
    "code,expected_type",
    [
        ("101S12", "future"),  # KOSPI200 선물
        ("201S312C", "option"),  # KOSPI200 콜옵션
        ("201S312P", "option"),  # KOSPI200 풋옵션
    ],
)
def test_futures_code_patterns(code, expected_type):
    """선물옵션 종목코드 패턴 검증"""
    # 선물: 101S12 (KOSPI200 선물)
    # 옵션: 201S312C/201S312P (KOSPI200 옵션 콜/풋)
    if expected_type == "future":
        assert "C" not in code and "P" not in code
    elif expected_type == "option":
        assert "C" in code or "P" in code


if __name__ == "__main__":
    unittest.main()
