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
            method="GET",
        )

    def test_get_stock_price_failure(self):
        """주식 현재가 조회 실패"""
        self.mock_client.make_request.return_value = None

        result = self.api.get_stock_price("005930")

        self.assertIsNone(result)

    def test_inquire_daily_price_default_params(self):
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

        result = self.api.inquire_daily_price("005930")

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint=API_ENDPOINTS["INQUIRE_DAILY_PRICE"],
            tr_id="FHKST01010400",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930",
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "1",
            },
            method="GET",
        )

    def test_inquire_daily_price_custom_params(self):
        """일별 시세 조회 - 커스텀 파라미터"""
        expected_response = {"rt_cd": "0", "msg1": "성공", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_daily_price("005930", period="W", org_adj_prc="0")

        self.assertEqual(result, expected_response)

        # 파라미터가 올바르게 설정되었는지 확인
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_PERIOD_DIV_CODE"], "W")
        self.assertEqual(params["FID_ORG_ADJ_PRC"], "0")

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
            method="GET",
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
            method="GET",
        )

    def test_get_minute_price_deprecated_warning(self):
        """[DEPRECATED] get_minute_price - deprecation 경고 발생 확인"""
        import warnings

        # get_intraday_price가 호출될 때 반환할 응답 설정
        expected_response = {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "하루 전체 분봉 데이터 수집 완료 (총 0건)",
            "output1": {},
            "output2": [],
        }
        self.mock_client.make_request.return_value = expected_response

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self.api.get_minute_price("005930")

            # deprecation 경고 발생 확인
            self.assertTrue(
                any(issubclass(warning.category, DeprecationWarning) for warning in w),
                "DeprecationWarning이 발생해야 합니다",
            )

        # get_intraday_price 응답 구조 확인 (output1, output2)
        self.assertIn("output1", result)
        self.assertIn("output2", result)

    def test_get_minute_price_forwards_to_intraday(self):
        """[DEPRECATED] get_minute_price - get_intraday_price로 포워딩 확인"""
        import warnings

        # get_intraday_price 내부에서 4번의 API 호출이 발생함
        self.mock_client.make_request.return_value = {
            "rt_cd": "0",
            "output1": {"test": "data"},
            "output2": [{"stck_cntg_hour": "153000"}],
        }

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = self.api.get_minute_price("005930", hour="120000")

        # hour 파라미터는 무시되고 get_intraday_price 구조로 반환
        self.assertIn("output2", result)

    @unittest.skip("API 메서드 시그니처 변경 - 추후 수정 필요")
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
            method="GET",
        )

    def test_get_daily_minute_price_full_day(self):
        """특정일 분봉 시세 조회 - 하루 전체 데이터 (내부 페이지네이션)"""
        # 4개의 시간대별 응답 모킹 (090000, 110000, 130000, 153000)
        responses = [
            {
                "rt_cd": "0",
                "output1": {"stck_prpr": "70000"},
                "output2": [{"stck_cntg_hour": "090000"}],
            },
            {
                "rt_cd": "0",
                "output1": {"stck_prpr": "70100"},
                "output2": [{"stck_cntg_hour": "110000"}],
            },
            {
                "rt_cd": "0",
                "output1": {"stck_prpr": "70200"},
                "output2": [{"stck_cntg_hour": "130000"}],
            },
            {
                "rt_cd": "0",
                "output1": {"stck_prpr": "70300"},
                "output2": [{"stck_cntg_hour": "153000"}],
            },
        ]
        self.mock_client.make_request.side_effect = responses

        result = self.api.get_daily_minute_price("005930", "20231215")

        self.assertEqual(result["rt_cd"], "0")
        self.assertEqual(len(result["output2"]), 4)  # 4개 시간대 데이터
        self.assertEqual(self.mock_client.make_request.call_count, 4)  # 4번 호출

    def test_error_response_handling(self):
        """에러 응답 처리"""
        error_response = {"rt_cd": "1", "msg1": "종목코드 오류", "msg_cd": "EGW00123"}
        self.mock_client.make_request.return_value = error_response

        result = self.api.get_stock_price("INVALID")

        self.assertEqual(result, error_response)
        self.assertEqual(result["rt_cd"], "1")

    def test_api_request_exception(self):
        """API 요청 중 예외 발생"""
        self.mock_client.make_request.side_effect = Exception("Connection error")

        with self.assertRaises(Exception) as context:
            self.api.get_stock_price("005930")

        # 새로운 예외 처리 형식: [API 요청 (Dict)] 또는 [컨텍스트] 형식
        self.assertIn("Connection error", str(context.exception))

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
        result2 = self.api.inquire_daily_price("005930")
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


class TestStockPriceAPIAdditionalMethods(unittest.TestCase):
    """StockPriceAPI 추가 메서드 테스트 - 커버리지 향상용"""

    def setUp(self):
        self.mock_client = Mock()
        self.api = StockPriceAPI(client=self.mock_client, enable_cache=False)

    def test_inquire_daily_itemchartprice_default_params(self):
        """기간별 시세 조회 - 기본 파라미터"""
        expected_response = {
            "rt_cd": "0",
            "output1": [{"stck_bsop_date": "20231215", "stck_clpr": "70000"}],
            "output2": {},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_daily_itemchartprice("005930")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_INPUT_DATE_1"], "")
        self.assertEqual(params["FID_INPUT_DATE_2"], "")
        self.assertEqual(params["FID_PERIOD_DIV_CODE"], "D")
        self.assertEqual(params["FID_ORG_ADJ_PRC"], "1")

    def test_inquire_daily_itemchartprice_with_dates(self):
        """기간별 시세 조회 - 날짜 지정"""
        expected_response = {"rt_cd": "0", "output1": [], "output2": {}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_daily_itemchartprice(
            "005930", start_date="20240101", end_date="20240131", period="W"
        )

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_INPUT_DATE_1"], "20240101")
        self.assertEqual(params["FID_INPUT_DATE_2"], "20240131")
        self.assertEqual(params["FID_PERIOD_DIV_CODE"], "W")

    def test_inquire_time_itemconclusion(self):
        """시간대별 체결 조회"""
        expected_response = {"rt_cd": "0", "output1": {}, "output2": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_time_itemconclusion("005930", hour="120000")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_INPUT_HOUR_1"], "120000")

    def test_inquire_ccnl(self):
        """체결 정보 조회 (최근 30건)"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_ccnl("005930", market="NX")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_COND_MRKT_DIV_CODE"], "NX")

    def test_inquire_price(self):
        """현재가 시세 조회"""
        expected_response = {"rt_cd": "0", "output": {"stck_prpr": "70000"}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_price("005930")

        self.assertEqual(result, expected_response)

    def test_inquire_price_2(self):
        """현재가 시세2 조회"""
        expected_response = {"rt_cd": "0", "output": {"stck_prpr": "70000"}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_price_2("005930")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        self.assertEqual(call_args[1]["tr_id"], "FHPST01010000")

    def test_search_stock_info(self):
        """주식 기본정보 조회"""
        expected_response = {
            "rt_cd": "0",
            "output": {"prdt_abrv_name": "삼성전자", "std_pdno": "005930"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.search_stock_info("005930")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["PDNO"], "005930")
        self.assertEqual(params["PRDT_TYPE_CD"], "300")

    def test_news_title(self):
        """뉴스 제목 조회"""
        expected_response = {"rt_cd": "0", "output1": [], "output2": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.news_title(code="005930", date="20240101")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_INPUT_ISCD"], "005930")
        self.assertEqual(params["FID_INPUT_DATE_1"], "20240101")

    def test_fluctuation(self):
        """등락률 순위 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.fluctuation(market="J", count="50")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["fid_cond_mrkt_div_code"], "J")
        self.assertEqual(params["fid_input_cnt_1"], "50")

    def test_volume_rank(self):
        """거래량 순위 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.volume_rank(market="J", volume="10000")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_VOL_CNT"], "10000")

    def test_market_cap(self):
        """시가총액 순위 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.market_cap(stock_code="0001")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["fid_input_iscd"], "0001")

    def test_inquire_daily_overtimeprice(self):
        """시간외 일자별주가 조회"""
        expected_response = {"rt_cd": "0", "output1": {}, "output2": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_daily_overtimeprice("005930")

        self.assertEqual(result, expected_response)

    def test_inquire_elw_price(self):
        """ELW 현재가 조회"""
        expected_response = {"rt_cd": "0", "output": {}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_elw_price("580001")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_COND_MRKT_DIV_CODE"], "W")

    def test_inquire_index_category_price(self):
        """업종 구분별 전체시세 조회"""
        expected_response = {"rt_cd": "0", "output1": {}, "output2": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_index_category_price("0001", market_cls="K")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_MRKT_CLS_CODE"], "K")

    def test_inquire_index_price_deprecated(self):
        """지수 현재가 조회 (deprecated)"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self.api.inquire_index_price("0001")
            # deprecation 경고가 발생하는지 확인
            self.assertTrue(
                any("deprecated" in str(warning.message).lower() for warning in w)
            )

        self.assertEqual(result, expected_response)

    def test_inquire_index_tickprice(self):
        """지수 틱 시세 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_index_tickprice("0001")

        self.assertEqual(result, expected_response)

    def test_inquire_index_timeprice(self):
        """지수 시간별 시세 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_index_timeprice("0001", time_div="300")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["fid_input_hour_1"], "300")

    def test_inquire_overtime_asking_price(self):
        """시간외 호가 조회"""
        expected_response = {"rt_cd": "0", "output": {}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_overtime_asking_price("005930")

        self.assertEqual(result, expected_response)

    def test_inquire_overtime_price(self):
        """시간외 현재가 조회"""
        expected_response = {"rt_cd": "0", "output": {}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_overtime_price("005930")

        self.assertEqual(result, expected_response)

    def test_disparity(self):
        """이격도 순위 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.disparity(hour_cls="10", sort_code="1")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["fid_hour_cls_code"], "10")
        self.assertEqual(params["fid_rank_sort_cls_code"], "1")

    def test_dividend_rate(self):
        """배당률 상위 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.dividend_rate(gb1="1", gb3="2")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["GB1"], "1")
        self.assertEqual(params["GB3"], "2")

    def test_market_time(self):
        """시장 영업시간 조회"""
        expected_response = {"rt_cd": "0", "output": {"open_time": "090000"}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.market_time()

        self.assertEqual(result, expected_response)

    def test_market_value(self):
        """종목별 시가총액 조회"""
        expected_response = {"rt_cd": "0", "output": {"mktc_amt": "500000000000000"}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.market_value("005930")

        self.assertEqual(result, expected_response)

    def test_profit_asset_index(self):
        """자산/수익지수 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.profit_asset_index("1001")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_INPUT_ISCD"], "1001")

    def test_intstock_multprice(self):
        """복수종목 현재가 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.intstock_multprice("005930,000660,035420")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_INPUT_ISCD"], "005930,000660,035420")

    def test_foreign_institution_total(self):
        """외국인/기관 종합 매매동향 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.foreign_institution_total(etc_cls="1")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_ETC_CLS_CODE"], "1")

    def test_daily_credit_balance(self):
        """신용잔고 일별추이 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.daily_credit_balance("005930", date="20240101")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_INPUT_DATE_1"], "20240101")

    def test_short_sale(self):
        """공매도 상위종목 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.short_sale(period="1", count="50")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_PERIOD_DIV_CODE"], "1")
        self.assertEqual(params["FID_INPUT_CNT_1"], "50")

    def test_inquire_vi_status(self):
        """VI 발동 현황 조회"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.inquire_vi_status(div_cls="1", market="1")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_DIV_CLS_CODE"], "1")
        self.assertEqual(params["FID_MRKT_CLS_CODE"], "1")

    def test_get_stock_ccnl(self):
        """체결 조회 래퍼"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_stock_ccnl("005930")

        self.assertEqual(result, expected_response)

    def test_get_intraday_price_success(self):
        """하루 전체 분봉 조회 성공"""
        # 4번의 API 호출 결과 Mock
        responses = [
            {
                "rt_cd": "0",
                "output1": {"summary": "data"},
                "output2": [
                    {"stck_cntg_hour": "090000", "stck_prpr": "70000"},
                    {"stck_cntg_hour": "091000", "stck_prpr": "70100"},
                ],
            },
            {
                "rt_cd": "0",
                "output2": [
                    {"stck_cntg_hour": "110000", "stck_prpr": "70200"},
                    {"stck_cntg_hour": "111000", "stck_prpr": "70300"},
                ],
            },
            {
                "rt_cd": "0",
                "output2": [
                    {"stck_cntg_hour": "130000", "stck_prpr": "70400"},
                ],
            },
            {
                "rt_cd": "0",
                "output2": [
                    {"stck_cntg_hour": "153000", "stck_prpr": "70500"},
                ],
            },
        ]
        self.mock_client.make_request.side_effect = responses

        result = self.api.get_intraday_price("005930")

        self.assertEqual(result["rt_cd"], "0")
        self.assertEqual(len(result["output2"]), 6)  # 중복 없이 6건
        self.assertEqual(self.mock_client.make_request.call_count, 4)  # 4번 호출

    def test_get_intraday_price_with_api_error(self):
        """당일 전체 분봉 조회 - API 오류 시에도 계속 진행"""
        responses = [
            {"rt_cd": "0", "output1": {}, "output2": [{"stck_cntg_hour": "090000"}]},
            {"rt_cd": "1", "msg1": "error"},  # 오류 응답
            {"rt_cd": "0", "output2": [{"stck_cntg_hour": "130000"}]},
            Exception("Connection error"),  # 예외 발생
        ]
        self.mock_client.make_request.side_effect = responses

        result = self.api.get_intraday_price("005930")

        # 오류에도 불구하고 수집된 데이터 반환
        self.assertEqual(result["rt_cd"], "0")
        self.assertEqual(len(result["output2"]), 2)  # 성공한 2건만

    def test_get_index_timeprice(self):
        """지수 시간별 시세 조회 (래퍼)"""
        expected_response = {"rt_cd": "0", "output": []}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_index_timeprice("1001", "120")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["fid_input_iscd"], "1001")
        self.assertEqual(params["fid_input_hour_1"], "120")

    @patch("pykis.stock.api.get_kospi200_futures_code")
    def test_get_future_option_price_default(self, mock_futures_code):
        """선물옵션 시세 조회 - 기본값"""
        mock_futures_code.return_value = "101T12"
        expected_response = {"rt_cd": "0", "output": {}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_future_option_price()

        self.assertEqual(result, expected_response)
        mock_futures_code.assert_called_once()
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["fid_input_iscd"], "101T12")

    def test_get_future_option_price_with_code(self):
        """선물옵션 시세 조회 - 코드 지정"""
        expected_response = {"rt_cd": "0", "output": {}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_future_option_price("O", "201T12370")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["fid_cond_mrkt_div_code"], "O")
        self.assertEqual(params["fid_input_iscd"], "201T12370")

    def test_get_future_orderbook_default(self):
        """선물 호가창 조회 - 기본값 (지수선물)"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output1": {
                "fuop_name": "KOSPI200 F 202509",
                "futs_prpr": "365.25",
                "prdy_vrss": "1.50",
            },
            "output2": {
                "askp1": "365.30",
                "bidp1": "365.20",
                "askp_rsqn1": "100",
                "bidp_rsqn1": "150",
            },
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_future_orderbook("101W09")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_COND_MRKT_DIV_CODE"], "F")
        self.assertEqual(params["FID_INPUT_ISCD"], "101W09")

    def test_get_future_orderbook_option(self):
        """선물 호가창 조회 - 옵션"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output1": {"fuop_name": "KOSPI200 C 202509 370"},
            "output2": {"askp1": "5.50", "bidp1": "5.45"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_future_orderbook("201W09370", market_div_code="O")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_COND_MRKT_DIV_CODE"], "O")
        self.assertEqual(params["FID_INPUT_ISCD"], "201W09370")

    def test_get_future_orderbook_stock_futures(self):
        """선물 호가창 조회 - 주식선물"""
        expected_response = {
            "rt_cd": "0",
            "msg1": "정상처리 되었습니다.",
            "output1": {"fuop_name": "삼성전자 F 202509"},
            "output2": {"askp1": "75000", "bidp1": "74900"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api.get_future_orderbook("005930F09", market_div_code="JF")

        self.assertEqual(result, expected_response)
        call_args = self.mock_client.make_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["FID_COND_MRKT_DIV_CODE"], "JF")
        self.assertEqual(params["FID_INPUT_ISCD"], "005930F09")


if __name__ == "__main__":
    unittest.main()
