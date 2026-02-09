"""
core/base_api.py 모듈의 단위 테스트

이 파일은 BaseAPI 클래스의 공통 기능들을 테스트합니다:
- 초기화 (캐시 설정 포함)
- 숫자형 필드 변환
- API 요청 메서드 (_make_request_dict, _make_request_dataframe)
- 캐시 동작

커버리지 목표: 48% → 70%+
"""

import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from pykis.core.base_api import BaseAPI
from pykis.core.client import KISClient
from pykis.core.exceptions import APIException


class TestBaseAPIInit(unittest.TestCase):
    """BaseAPI 초기화 테스트"""

    def setUp(self):
        """각 테스트마다 새로운 mock client 생성"""
        self.mock_client = MagicMock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    def test_init_with_cache_enabled(self):
        """캐시 활성화 상태 초기화 테스트"""
        api = BaseAPI(self.mock_client, self.account_info, enable_cache=True)

        self.assertEqual(api.client, self.mock_client)
        self.assertEqual(api.account, self.account_info)
        self.assertIsNotNone(api.cache)
        self.assertIsNotNone(api.numeric_field_mappings)
        self.assertIsNotNone(api.request_manager)

    def test_init_with_cache_disabled(self):
        """캐시 비활성화 상태 초기화 테스트"""
        api = BaseAPI(self.mock_client, self.account_info, enable_cache=False)

        self.assertEqual(api.client, self.mock_client)
        self.assertIsNone(api.cache)

    def test_init_with_custom_cache_config(self):
        """커스텀 캐시 설정 초기화 테스트"""
        cache_config = {"default_ttl": 10, "max_size": 500}
        api = BaseAPI(
            self.mock_client,
            self.account_info,
            enable_cache=True,
            cache_config=cache_config,
        )

        self.assertIsNotNone(api.cache)
        self.assertEqual(api.cache.default_ttl, 10)
        self.assertEqual(api.cache.max_size, 500)

    def test_init_without_account_info(self):
        """계좌 정보 없이 초기화 테스트"""
        api = BaseAPI(self.mock_client, account_info=None, enable_cache=False)

        self.assertEqual(api.client, self.mock_client)
        self.assertIsNone(api.account)


class TestBaseAPINumericeFieldMappings(unittest.TestCase):
    """숫자형 필드 매핑 테스트"""

    def setUp(self):
        self.mock_client = MagicMock(spec=KISClient)
        self.api = BaseAPI(self.mock_client, enable_cache=False)

    def test_get_numeric_field_mappings_returns_dict(self):
        """숫자형 필드 매핑이 딕셔너리를 반환하는지 테스트"""
        mappings = self.api._get_numeric_field_mappings()

        self.assertIsInstance(mappings, dict)
        self.assertIn("account_balance", mappings)
        self.assertIn("stock_price", mappings)
        self.assertIn("daily_price", mappings)
        self.assertIn("minute_price", mappings)
        self.assertIn("member_data", mappings)
        self.assertIn("investor_data", mappings)
        self.assertIn("orderbook", mappings)
        self.assertIn("volume_power", mappings)
        self.assertIn("program_trade", mappings)

    def test_account_balance_fields(self):
        """계좌 잔고 필드 매핑 테스트"""
        mappings = self.api._get_numeric_field_mappings()
        account_fields = mappings["account_balance"]

        self.assertIn("hldg_qty", account_fields)
        self.assertIn("pchs_avg_pric", account_fields)
        self.assertIn("evlu_amt", account_fields)
        self.assertIn("evlu_pfls_amt", account_fields)

    def test_stock_price_fields(self):
        """주식 시세 필드 매핑 테스트"""
        mappings = self.api._get_numeric_field_mappings()
        price_fields = mappings["stock_price"]

        self.assertIn("stck_prpr", price_fields)
        self.assertIn("prdy_vrss", price_fields)
        self.assertIn("acml_vol", price_fields)


class TestBaseAPISafeNumericConvert(unittest.TestCase):
    """안전한 숫자 변환 테스트"""

    def setUp(self):
        self.mock_client = MagicMock(spec=KISClient)
        self.api = BaseAPI(self.mock_client, enable_cache=False)

    def test_convert_integer_string(self):
        """정수형 문자열 변환 테스트"""
        result = self.api._safe_numeric_convert("12345")
        self.assertEqual(result, 12345)
        self.assertIsInstance(result, int)

    def test_convert_float_string(self):
        """소수점 문자열 변환 테스트"""
        result = self.api._safe_numeric_convert("123.45")
        self.assertEqual(result, 123.45)
        self.assertIsInstance(result, float)

    def test_convert_float_with_zero_decimal(self):
        """소수점이 0인 실수 변환 테스트 (정수로 변환)"""
        result = self.api._safe_numeric_convert("123.00")
        self.assertEqual(result, 123)
        self.assertIsInstance(result, int)

    def test_convert_empty_string(self):
        """빈 문자열 변환 테스트"""
        result = self.api._safe_numeric_convert("")
        self.assertEqual(result, 0)

    def test_convert_none(self):
        """None 변환 테스트"""
        result = self.api._safe_numeric_convert(None)
        self.assertEqual(result, 0)

    def test_convert_nan(self):
        """NaN 변환 테스트"""
        import math

        result = self.api._safe_numeric_convert(float("nan"))
        self.assertEqual(result, 0)

    def test_convert_whitespace_string(self):
        """공백 문자열 변환 테스트"""
        result = self.api._safe_numeric_convert("   ")
        self.assertEqual(result, 0)

    def test_convert_string_with_whitespace(self):
        """앞뒤 공백이 있는 숫자 문자열 변환 테스트"""
        result = self.api._safe_numeric_convert("  12345  ")
        self.assertEqual(result, 12345)

    def test_convert_invalid_string(self):
        """변환 불가능한 문자열 테스트 (원래 값 반환)"""
        result = self.api._safe_numeric_convert("invalid")
        self.assertEqual(result, "invalid")

    def test_convert_negative_number(self):
        """음수 변환 테스트"""
        result = self.api._safe_numeric_convert("-5000")
        self.assertEqual(result, -5000)

    def test_convert_negative_float(self):
        """음수 소수점 변환 테스트"""
        result = self.api._safe_numeric_convert("-12.5")
        self.assertEqual(result, -12.5)


class TestBaseAPIConvertNumericFields(unittest.TestCase):
    """DataFrame 숫자형 필드 변환 테스트"""

    def setUp(self):
        self.mock_client = MagicMock(spec=KISClient)
        self.api = BaseAPI(self.mock_client, enable_cache=False)

    def test_convert_empty_dataframe(self):
        """빈 DataFrame 변환 테스트"""
        df = pd.DataFrame()
        result = self.api._convert_numeric_fields(df)

        self.assertTrue(result.empty)

    def test_convert_with_field_type(self):
        """field_type 지정하여 변환 테스트"""
        df = pd.DataFrame(
            {
                "stck_prpr": ["50000", "51000"],
                "prdy_vrss": ["1000", "-500"],
                "other_field": ["text", "text2"],
            }
        )

        result = self.api._convert_numeric_fields(df, field_type="stock_price")

        # 숫자형 필드는 변환됨
        self.assertEqual(result["stck_prpr"].iloc[0], 50000)
        self.assertEqual(result["prdy_vrss"].iloc[1], -500)
        # 기타 필드는 그대로
        self.assertEqual(result["other_field"].iloc[0], "text")

    def test_convert_without_field_type_auto_detect(self):
        """field_type 없이 자동 감지 변환 테스트"""
        df = pd.DataFrame(
            {
                "hldg_qty": ["100", "200"],  # qty 포함 - 숫자로 변환
                "pchs_amt": ["50000", "60000"],  # amt 포함 - 숫자로 변환
                "vol_rate": ["10.5", "20.3"],  # rate 포함 - 숫자로 변환
                "name": ["삼성전자", "SK하이닉스"],  # 일반 필드 - 변환 안됨
            }
        )

        result = self.api._convert_numeric_fields(df, field_type=None)

        self.assertEqual(result["hldg_qty"].iloc[0], 100)
        self.assertEqual(result["pchs_amt"].iloc[0], 50000)
        self.assertEqual(result["vol_rate"].iloc[0], 10.5)
        self.assertEqual(result["name"].iloc[0], "삼성전자")

    def test_convert_preserves_original_dataframe(self):
        """원본 DataFrame이 변경되지 않는지 테스트"""
        df = pd.DataFrame({"stck_prpr": ["50000"]})
        original_value = df["stck_prpr"].iloc[0]

        result = self.api._convert_numeric_fields(df, field_type="stock_price")

        # 원본은 변경되지 않음
        self.assertEqual(df["stck_prpr"].iloc[0], original_value)
        # 결과는 변환됨
        self.assertEqual(result["stck_prpr"].iloc[0], 50000)


class TestBaseAPIAddResponseMetadata(unittest.TestCase):
    """응답 메타데이터 추가 테스트"""

    def setUp(self):
        self.mock_client = MagicMock(spec=KISClient)
        self.api = BaseAPI(self.mock_client, enable_cache=False)

    def test_add_metadata_success(self):
        """메타데이터 추가 성공 테스트"""
        df = pd.DataFrame({"data": [1, 2, 3]})
        response = {"rt_cd": "0", "msg_cd": "KIOK0000", "msg1": "정상 처리되었습니다."}

        result = self.api._add_response_metadata(df, response)

        self.assertEqual(result["rt_cd"].iloc[0], "0")
        self.assertEqual(result["msg_cd"].iloc[0], "KIOK0000")
        self.assertEqual(result["msg1"].iloc[0], "정상 처리되었습니다.")

    def test_add_metadata_missing_fields(self):
        """메타데이터 필드가 없는 경우 테스트"""
        df = pd.DataFrame({"data": [1]})
        response = {}

        result = self.api._add_response_metadata(df, response)

        self.assertEqual(result["rt_cd"].iloc[0], "")
        self.assertEqual(result["msg_cd"].iloc[0], "")
        self.assertEqual(result["msg1"].iloc[0], "")


class TestBaseAPIMakeRequestDict(unittest.TestCase):
    """_make_request_dict 메서드 테스트"""

    def setUp(self):
        self.mock_client = MagicMock(spec=KISClient)
        self.api = BaseAPI(self.mock_client, enable_cache=False)

    def test_make_request_dict_success(self):
        """Dict 요청 성공 테스트"""
        expected_response = {
            "rt_cd": "0",
            "output": {"stck_prpr": "50000"},
        }
        self.mock_client.make_request.return_value = expected_response

        result = self.api._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/test",
            tr_id="FHKST01010100",
            params={"FID_INPUT_ISCD": "005930"},
            use_cache=False,
        )

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint="/uapi/domestic-stock/v1/test",
            tr_id="FHKST01010100",
            params={"FID_INPUT_ISCD": "005930"},
            method="GET",
        )

    def test_make_request_dict_with_post_method(self):
        """POST 메서드로 Dict 요청 테스트"""
        expected_response = {"rt_cd": "0", "output": {}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/order",
            tr_id="TTTC0012U",  # 현금 매수 TR
            params={"PDNO": "005930", "ORD_QTY": "10"},
            method="POST",
            use_cache=False,
        )

        self.assertEqual(result, expected_response)
        self.mock_client.make_request.assert_called_once_with(
            endpoint="/uapi/domestic-stock/v1/order",
            tr_id="TTTC0012U",  # 현금 매수 TR
            params={"PDNO": "005930", "ORD_QTY": "10"},
            method="POST",
        )

    def test_make_request_dict_none_response(self):
        """응답이 None인 경우 테스트"""
        self.mock_client.make_request.return_value = None

        result = self.api._make_request_dict(
            endpoint="/test",
            tr_id="TEST",
            params={},
            use_cache=False,
        )

        self.assertIsNone(result)

    def test_make_request_dict_exception(self):
        """예외 발생 테스트"""
        self.mock_client.make_request.side_effect = Exception("API 오류")

        with pytest.raises(APIException):
            self.api._make_request_dict(
                endpoint="/test",
                tr_id="TEST",
                params={},
                use_cache=False,
            )


class TestBaseAPIMakeRequestDictWithCache(unittest.TestCase):
    """_make_request_dict 캐시 동작 테스트"""

    def setUp(self):
        self.mock_client = MagicMock(spec=KISClient)
        # 캐시 활성화
        self.api = BaseAPI(self.mock_client, enable_cache=True)

    def test_cache_hit(self):
        """캐시 히트 테스트"""
        # 첫 번째 요청
        expected_response = {"rt_cd": "0", "output": {"stck_prpr": "50000"}}
        self.mock_client.make_request.return_value = expected_response

        result1 = self.api._make_request_dict(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            use_cache=True,
        )

        # 두 번째 요청 - 캐시에서 가져옴
        result2 = self.api._make_request_dict(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            use_cache=True,
        )

        # API는 한 번만 호출됨
        self.assertEqual(self.mock_client.make_request.call_count, 1)
        # 캐시된 결과에는 _cached 플래그가 있음
        self.assertTrue(result2.get("_cached", False))

    def test_cache_disabled(self):
        """캐시 비활성화 테스트"""
        expected_response = {"rt_cd": "0", "output": {}}
        self.mock_client.make_request.return_value = expected_response

        result1 = self.api._make_request_dict(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            use_cache=False,
        )

        result2 = self.api._make_request_dict(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            use_cache=False,
        )

        # API는 두 번 호출됨
        self.assertEqual(self.mock_client.make_request.call_count, 2)

    def test_cache_not_stored_for_error_response(self):
        """에러 응답은 캐시에 저장되지 않음 테스트"""
        error_response = {"rt_cd": "1", "msg1": "에러"}
        success_response = {"rt_cd": "0", "output": {}}
        self.mock_client.make_request.side_effect = [error_response, success_response]

        result1 = self.api._make_request_dict(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            use_cache=True,
        )

        result2 = self.api._make_request_dict(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            use_cache=True,
        )

        # 에러 응답은 캐시되지 않으므로 API 두 번 호출
        self.assertEqual(self.mock_client.make_request.call_count, 2)
        self.assertEqual(result1["rt_cd"], "1")
        self.assertEqual(result2["rt_cd"], "0")

    def test_cache_with_custom_ttl(self):
        """커스텀 TTL로 캐시 테스트"""
        expected_response = {"rt_cd": "0", "output": {}}
        self.mock_client.make_request.return_value = expected_response

        result = self.api._make_request_dict(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            use_cache=True,
            cache_ttl=60,  # 60초 TTL
        )

        self.assertEqual(result, expected_response)


class TestBaseAPIMakeRequestDataframe(unittest.TestCase):
    """_make_request_dataframe 메서드 테스트"""

    def setUp(self):
        self.mock_client = MagicMock(spec=KISClient)
        self.api = BaseAPI(self.mock_client, enable_cache=False)

    def test_make_request_dataframe_success(self):
        """DataFrame 요청 성공 테스트"""
        # request_manager를 mock
        self.api.request_manager = MagicMock()
        expected_df = pd.DataFrame({"stck_prpr": [50000], "prdy_vrss": [1000]})
        self.api.request_manager.make_request_with_processing.return_value = expected_df

        result = self.api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            use_cache=False,
        )

        pd.testing.assert_frame_equal(result, expected_df)
        self.api.request_manager.make_request_with_processing.assert_called_once()

    def test_make_request_dataframe_with_field_type(self):
        """field_type 지정하여 DataFrame 요청 테스트"""
        self.api.request_manager = MagicMock()
        expected_df = pd.DataFrame({"stck_prpr": [50000]})
        self.api.request_manager.make_request_with_processing.return_value = expected_df

        result = self.api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            field_type="stock_price",
            use_cache=False,
        )

        call_args = self.api.request_manager.make_request_with_processing.call_args
        self.assertEqual(call_args[1]["field_type"], "stock_price")

    def test_make_request_dataframe_none_result(self):
        """결과가 None인 경우 테스트"""
        self.api.request_manager = MagicMock()
        self.api.request_manager.make_request_with_processing.return_value = None

        result = self.api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST",
            params={},
            use_cache=False,
        )

        self.assertIsNone(result)

    def test_make_request_dataframe_exception(self):
        """예외 발생 테스트"""
        self.api.request_manager = MagicMock()
        self.api.request_manager.make_request_with_processing.side_effect = Exception(
            "API 오류"
        )

        with pytest.raises(APIException):
            self.api._make_request_dataframe(
                endpoint="/test",
                tr_id="TEST",
                params={},
                use_cache=False,
            )


class TestBaseAPIMakeRequestDataframeWithCache(unittest.TestCase):
    """_make_request_dataframe 캐시 동작 테스트"""

    def setUp(self):
        self.mock_client = MagicMock(spec=KISClient)
        # 캐시 활성화
        self.api = BaseAPI(self.mock_client, enable_cache=True)

    def test_dataframe_cache_hit(self):
        """DataFrame 캐시 히트 테스트"""
        self.api.request_manager = MagicMock()
        expected_df = pd.DataFrame({"stck_prpr": [50000]})
        self.api.request_manager.make_request_with_processing.return_value = expected_df

        # 첫 번째 요청
        result1 = self.api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            use_cache=True,
        )

        # 두 번째 요청 - 캐시에서 가져옴
        result2 = self.api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            use_cache=True,
        )

        # request_manager는 한 번만 호출됨
        self.assertEqual(
            self.api.request_manager.make_request_with_processing.call_count, 1
        )
        pd.testing.assert_frame_equal(result1, result2)

    def test_dataframe_cache_not_stored_for_empty(self):
        """빈 DataFrame은 캐시에 저장되지 않음 테스트"""
        self.api.request_manager = MagicMock()
        empty_df = pd.DataFrame()
        non_empty_df = pd.DataFrame({"data": [1]})
        self.api.request_manager.make_request_with_processing.side_effect = [
            empty_df,
            non_empty_df,
        ]

        result1 = self.api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            use_cache=True,
        )

        result2 = self.api._make_request_dataframe(
            endpoint="/test",
            tr_id="TEST",
            params={"code": "005930"},
            use_cache=True,
        )

        # 빈 DataFrame은 캐시되지 않으므로 두 번 호출
        self.assertEqual(
            self.api.request_manager.make_request_with_processing.call_count, 2
        )


class TestDirectAPIUsageWarning(unittest.TestCase):
    """Agent를 거치지 않고 직접 API 사용 시 경고 테스트"""

    def setUp(self):
        """각 테스트마다 새로운 mock client 생성"""
        self.mock_client = MagicMock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    def test_warning_when_direct_instantiation(self):
        """직접 인스턴스화 시 DirectAPIUsageWarning 발생 확인"""
        import warnings

        from pykis.core.base_api import DirectAPIUsageWarning

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 직접 BaseAPI 인스턴스화 (_from_agent=False가 기본값)
            api = BaseAPI(self.mock_client)

            # 경고가 발생했는지 확인
            self.assertGreaterEqual(len(w), 1, "경고가 발생해야 합니다")

            # DirectAPIUsageWarning인지 확인
            warning_types = [warning.category for warning in w]
            self.assertIn(
                DirectAPIUsageWarning,
                warning_types,
                "DirectAPIUsageWarning이 발생해야 합니다",
            )

    def test_no_warning_when_from_agent(self):
        """Agent를 통해 생성 시 경고 없음 확인"""
        import warnings

        from pykis.core.base_api import DirectAPIUsageWarning

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # _from_agent=True로 인스턴스화
            api = BaseAPI(self.mock_client, _from_agent=True)

            # DirectAPIUsageWarning이 발생하지 않아야 함
            warning_types = [warning.category for warning in w]
            self.assertNotIn(
                DirectAPIUsageWarning,
                warning_types,
                "Agent를 통해 생성 시 경고가 발생하면 안 됩니다",
            )

    def test_created_via_agent_flag_set_correctly(self):
        """_created_via_agent 플래그가 올바르게 설정되는지 확인"""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # _from_agent=True
            api_from_agent = BaseAPI(self.mock_client, _from_agent=True)
            self.assertTrue(api_from_agent._created_via_agent)

            # _from_agent=False (기본값)
            api_direct = BaseAPI(self.mock_client, _from_agent=False)
            self.assertFalse(api_direct._created_via_agent)

    def test_warning_message_contains_class_name(self):
        """경고 메시지에 클래스 이름이 포함되는지 확인"""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            api = BaseAPI(self.mock_client)

            # 경고 메시지에 클래스 이름이 포함되어야 함
            self.assertGreaterEqual(len(w), 1)
            warning_message = str(w[0].message)
            self.assertIn("BaseAPI", warning_message)

    def test_warning_message_contains_usage_guide(self):
        """경고 메시지에 올바른 사용법 안내가 포함되는지 확인"""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            api = BaseAPI(self.mock_client)

            # 경고 메시지에 Agent 사용법 안내가 포함되어야 함
            self.assertGreaterEqual(len(w), 1)
            warning_message = str(w[0].message)
            self.assertTrue(
                "pykis" in warning_message.lower() or "Agent" in warning_message
            )


class TestAPIClassesWithFromAgent(unittest.TestCase):
    """각 API 클래스가 _from_agent 파라미터를 올바르게 처리하는지 테스트"""

    def setUp(self):
        """각 테스트마다 새로운 mock client 생성"""
        self.mock_client = MagicMock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    def test_account_api_from_agent(self):
        """AccountAPI가 _from_agent 파라미터를 올바르게 처리하는지 확인"""
        import warnings

        from pykis.account.api import AccountAPI
        from pykis.core.base_api import DirectAPIUsageWarning

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # _from_agent=True로 생성
            api = AccountAPI(self.mock_client, self.account_info, _from_agent=True)

            # DirectAPIUsageWarning이 발생하지 않아야 함
            warning_types = [warning.category for warning in w]
            self.assertNotIn(DirectAPIUsageWarning, warning_types)

    def test_stock_api_facade_from_agent(self):
        """StockAPI (Facade)가 _from_agent 파라미터를 올바르게 처리하는지 확인"""
        import warnings

        from pykis.core.base_api import DirectAPIUsageWarning
        from pykis.stock.api_facade import StockAPI

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # _from_agent=True로 생성
            api = StockAPI(self.mock_client, self.account_info, _from_agent=True)

            # DirectAPIUsageWarning이 발생하지 않아야 함
            warning_types = [warning.category for warning in w]
            self.assertNotIn(DirectAPIUsageWarning, warning_types)

    def test_program_trade_api_from_agent(self):
        """ProgramTradeAPI가 _from_agent 파라미터를 올바르게 처리하는지 확인"""
        import warnings

        from pykis.core.base_api import DirectAPIUsageWarning
        from pykis.program.trade import ProgramTradeAPI

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # _from_agent=True로 생성
            api = ProgramTradeAPI(self.mock_client, self.account_info, _from_agent=True)

            # DirectAPIUsageWarning이 발생하지 않아야 함
            warning_types = [warning.category for warning in w]
            self.assertNotIn(DirectAPIUsageWarning, warning_types)

    def test_interest_stock_api_from_agent(self):
        """InterestStockAPI가 _from_agent 파라미터를 올바르게 처리하는지 확인"""
        import warnings

        from pykis.core.base_api import DirectAPIUsageWarning
        from pykis.stock.interest import InterestStockAPI

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # _from_agent=True로 생성
            api = InterestStockAPI(
                self.mock_client, self.account_info, _from_agent=True
            )

            # DirectAPIUsageWarning이 발생하지 않아야 함
            warning_types = [warning.category for warning in w]
            self.assertNotIn(DirectAPIUsageWarning, warning_types)


class TestDirectAPIWarningInSubAPIs(unittest.TestCase):
    """직접 API 사용 시 각 API에서 경고가 발생하는지 테스트"""

    def setUp(self):
        """각 테스트마다 새로운 mock client 생성"""
        self.mock_client = MagicMock(spec=KISClient)
        self.account_info = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}

    def test_account_api_direct_warns(self):
        """AccountAPI 직접 사용 시 경고 발생 확인"""
        import warnings

        from pykis.account.api import AccountAPI
        from pykis.core.base_api import DirectAPIUsageWarning

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 직접 생성 (기본값 _from_agent=False)
            api = AccountAPI(self.mock_client, self.account_info)

            # DirectAPIUsageWarning이 발생해야 함
            warning_types = [warning.category for warning in w]
            self.assertIn(DirectAPIUsageWarning, warning_types)

    def test_stock_api_facade_direct_warns(self):
        """StockAPI (Facade) 직접 사용 시 경고 발생 확인"""
        import warnings

        from pykis.core.base_api import DirectAPIUsageWarning
        from pykis.stock.api_facade import StockAPI

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 직접 생성
            api = StockAPI(self.mock_client, self.account_info)

            # DirectAPIUsageWarning이 발생해야 함 (StockAPI + 하위 API들)
            warning_types = [warning.category for warning in w]
            self.assertIn(DirectAPIUsageWarning, warning_types)


if __name__ == "__main__":
    unittest.main()
