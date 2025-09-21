"""
Response Processor 모듈 테스트

Factory Pattern과 Template Method Pattern이 적용된 API 응답 처리기를 테스트합니다.

이 모듈은 다음 디자인 패턴들의 구현을 검증합니다:
- Factory Pattern: ResponseProcessorFactory를 통한 프로세서 생성
- Template Method Pattern: BaseResponseProcessor의 템플릿 메서드 구조  
- Strategy Pattern: 다양한 응답 처리 전략 (Dict, DataFrame, Raw)

테스트 범위:
- APIRequestManager의 통합 요청 처리
- 각 ResponseProcessor 구현체의 동작 검증
- Factory의 올바른 프로세서 생성
- 오류 상황에서의 안정성
"""

import unittest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import pytest

from pykis.core.response_processor import (
    ResponseProcessor,
    DictResponseProcessor,
    DataFrameResponseProcessor,
    ResponseProcessorFactory,
    APIRequestManager,
)


class TestDictResponseProcessor(unittest.TestCase):
    """DictResponseProcessor 테스트"""

    def setUp(self):
        self.processor = DictResponseProcessor()

    def test_process_valid_response(self):
        """유효한 응답 처리 테스트"""
        response = {"rt_cd": "0", "msg1": "성공", "data": {"price": 100}}
        result = self.processor.process(response)
        self.assertEqual(result, response)

    def test_process_empty_response(self):
        """빈 응답 처리 테스트"""
        result = self.processor.process({})
        self.assertIsNone(result)

    def test_process_none_response(self):
        """None 응답 처리 테스트"""
        result = self.processor.process(None)
        self.assertIsNone(result)


class TestDataFrameResponseProcessor(unittest.TestCase):
    """DataFrameResponseProcessor 테스트"""

    def setUp(self):
        self.mock_metadata_adder = Mock()
        self.mock_field_converter = Mock()
        self.processor = DataFrameResponseProcessor(
            self.mock_metadata_adder, self.mock_field_converter
        )

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.processor.add_metadata, self.mock_metadata_adder)
        self.assertEqual(self.processor.convert_fields, self.mock_field_converter)

    def test_process_success_with_output(self):
        """output이 있는 성공 응답 처리"""
        response = {"rt_cd": "0", "msg1": "성공", "output": [{"price": 100, "qty": 10}]}

        # DataFrame 생성 mock
        expected_df = pd.DataFrame([{"price": 100, "qty": 10}])

        # metadata_adder mock 설정
        self.mock_metadata_adder.return_value = expected_df
        self.mock_field_converter.return_value = expected_df

        result = self.processor.process(response, "stock_price")

        self.assertIsInstance(result, pd.DataFrame)
        self.mock_metadata_adder.assert_called_once()
        self.mock_field_converter.assert_called_once()

    def test_process_success_with_output1(self):
        """output1이 있는 성공 응답 처리"""
        response = {"rt_cd": "0", "msg1": "성공", "output1": [{"price": 100}]}

        expected_df = pd.DataFrame([{"price": 100}])
        self.mock_metadata_adder.return_value = expected_df
        self.mock_field_converter.return_value = expected_df

        result = self.processor.process(response)
        self.assertIsInstance(result, pd.DataFrame)

    def test_process_error_response(self):
        """에러 응답 처리"""
        response = {"rt_cd": "1", "msg1": "실패", "output": []}

        result = self.processor.process(response)
        self.assertIsNone(result)

    def test_process_no_output(self):
        """output이 없는 응답 처리"""
        response = {"rt_cd": "0", "msg1": "성공"}

        result = self.processor.process(response)
        self.assertIsNone(result)

    def test_extract_output_data_priority(self):
        """output 데이터 추출 우선순위 테스트"""
        response = {
            "output": [{"data1": 1}],
            "output1": [{"data2": 2}],
            "output2": [{"data3": 3}],
        }

        result = self.processor._extract_output_data(response)
        self.assertEqual(result, [{"data1": 1}])

    def test_extract_output_data_no_data(self):
        """output 데이터가 없는 경우"""
        response = {"rt_cd": "0", "msg1": "성공"}

        result = self.processor._extract_output_data(response)
        self.assertIsNone(result)

    def test_convert_to_dataframe_list(self):
        """리스트 데이터 DataFrame 변환"""
        output_data = [{"price": 100}, {"price": 200}]

        result = self.processor._convert_to_dataframe(output_data)
        expected = pd.DataFrame([{"price": 100}, {"price": 200}])

        pd.testing.assert_frame_equal(result, expected)

    def test_convert_to_dataframe_dict(self):
        """딕트 데이터 DataFrame 변환"""
        output_data = {"price": 100, "qty": 10}

        result = self.processor._convert_to_dataframe(output_data)
        expected = pd.DataFrame([{"price": 100, "qty": 10}])

        pd.testing.assert_frame_equal(result, expected)

    def test_convert_to_dataframe_invalid(self):
        """잘못된 타입 데이터"""
        output_data = "invalid"

        result = self.processor._convert_to_dataframe(output_data)
        self.assertIsNone(result)

    @patch("pykis.core.response_processor.logging.error")
    def test_convert_to_dataframe_exception(self, mock_log):
        """DataFrame 변환 중 예외 발생"""
        with patch("pandas.DataFrame", side_effect=Exception("Test error")):
            output_data = [{"price": 100}]

            result = self.processor._convert_to_dataframe(output_data)
            self.assertIsNone(result)
            mock_log.assert_called_once()


class TestResponseProcessorFactory(unittest.TestCase):
    """ResponseProcessorFactory 테스트"""

    def test_create_dict_processor(self):
        """Dict 처리기 생성 테스트"""
        processor = ResponseProcessorFactory.create_processor(return_dataframe=False)

        self.assertIsInstance(processor, DictResponseProcessor)

    def test_create_dataframe_processor(self):
        """DataFrame 처리기 생성 테스트"""
        mock_metadata_adder = Mock()
        mock_field_converter = Mock()

        processor = ResponseProcessorFactory.create_processor(
            return_dataframe=True,
            metadata_adder=mock_metadata_adder,
            field_converter=mock_field_converter,
        )

        self.assertIsInstance(processor, DataFrameResponseProcessor)
        self.assertEqual(processor.add_metadata, mock_metadata_adder)
        self.assertEqual(processor.convert_fields, mock_field_converter)

    def test_create_dataframe_processor_missing_params(self):
        """DataFrame 처리기 생성 시 필수 파라미터 누락"""
        with self.assertRaises(ValueError) as context:
            ResponseProcessorFactory.create_processor(return_dataframe=True)

        self.assertIn(
            "metadata_adder와 field_converter가 필요합니다", str(context.exception)
        )


class TestAPIRequestManager(unittest.TestCase):
    """APIRequestManager 테스트"""

    def setUp(self):
        self.mock_client = Mock()
        self.mock_metadata_adder = Mock()
        self.mock_field_converter = Mock()

        self.manager = APIRequestManager(
            client=self.mock_client,
            metadata_adder=self.mock_metadata_adder,
            field_converter=self.mock_field_converter,
        )

    def test_init(self):
        """초기화 테스트"""
        self.assertEqual(self.manager.client, self.mock_client)
        self.assertEqual(self.manager.metadata_adder, self.mock_metadata_adder)
        self.assertEqual(self.manager.field_converter, self.mock_field_converter)

    @patch("pykis.core.response_processor.ResponseProcessorFactory.create_processor")
    def test_make_request_with_processing_dataframe(self, mock_factory):
        """DataFrame 반환 요청 처리"""
        # Mock 설정
        mock_response = {"rt_cd": "0", "output": [{"price": 100}]}
        self.mock_client.make_request.return_value = mock_response

        mock_processor = Mock()
        expected_df = pd.DataFrame([{"price": 100}])
        mock_processor.process.return_value = expected_df
        mock_factory.return_value = mock_processor

        # 테스트 실행
        result = self.manager.make_request_with_processing(
            endpoint="/test",
            tr_id="TEST001",
            params={"code": "005930"},
            field_type="stock_price",
            return_dataframe=True,
        )

        # 검증
        self.mock_client.make_request.assert_called_once_with(
            endpoint="/test", tr_id="TEST001", params={"code": "005930"}
        )

        mock_factory.assert_called_once_with(
            return_dataframe=True,
            metadata_adder=self.mock_metadata_adder,
            field_converter=self.mock_field_converter,
        )

        mock_processor.process.assert_called_once_with(mock_response, "stock_price")
        pd.testing.assert_frame_equal(result, expected_df)

    @patch("pykis.core.response_processor.ResponseProcessorFactory.create_processor")
    def test_make_request_with_processing_dict(self, mock_factory):
        """Dict 반환 요청 처리"""
        # Mock 설정
        mock_response = {"rt_cd": "0", "data": {"price": 100}}
        self.mock_client.make_request.return_value = mock_response

        mock_processor = Mock()
        mock_processor.process.return_value = mock_response
        mock_factory.return_value = mock_processor

        # 테스트 실행
        result = self.manager.make_request_with_processing(
            endpoint="/test",
            tr_id="TEST001",
            params={"code": "005930"},
            return_dataframe=False,
        )

        # 검증
        mock_factory.assert_called_once_with(
            return_dataframe=False,
            metadata_adder=self.mock_metadata_adder,
            field_converter=self.mock_field_converter,
        )

        self.assertEqual(result, mock_response)

    @patch("pykis.core.response_processor.logging.error")
    def test_make_request_with_processing_exception(self, mock_log):
        """API 요청 중 예외 발생"""
        # Mock 설정
        self.mock_client.make_request.side_effect = Exception("API Error")

        # 테스트 실행 및 검증
        with self.assertRaises(Exception) as context:
            self.manager.make_request_with_processing(
                endpoint="/test", tr_id="TEST001", params={"code": "005930"}
            )

        self.assertIn("API 요청 실패", str(context.exception))
        mock_log.assert_called_once()


if __name__ == "__main__":
    unittest.main()
