"""
DataFrame Helper 함수들을 테스트하는 모듈
"""

from unittest.mock import Mock

import pandas as pd
import pytest

from pykis.core.dataframe_helper import (
    add_api_metadata_to_dataframe,
    create_dataframe_with_metadata,
    extract_output_data,
)


class TestDataFrameHelper:
    """DataFrame Helper 함수 테스트"""

    def test_add_api_metadata_to_dataframe_success(self):
        """DataFrame에 메타데이터를 성공적으로 추가"""
        # Given
        df = pd.DataFrame([{"name": "test", "value": 123}])
        response = {"rt_cd": "0", "msg_cd": "SUCCESS", "msg1": "조회 성공"}

        # When
        result = add_api_metadata_to_dataframe(df, response)

        # Then
        assert isinstance(result, pd.DataFrame)
        assert result["rt_cd"].iloc[0] == "0"
        assert result["msg_cd"].iloc[0] == "SUCCESS"
        assert result["msg1"].iloc[0] == "조회 성공"
        assert result["name"].iloc[0] == "test"
        assert result["value"].iloc[0] == 123

    def test_add_api_metadata_to_dataframe_missing_metadata(self):
        """메타데이터가 부분적으로 누락된 경우"""
        # Given
        df = pd.DataFrame([{"name": "test"}])
        response = {"rt_cd": "0"}  # msg_cd, msg1 누락

        # When
        result = add_api_metadata_to_dataframe(df, response)

        # Then
        assert result["rt_cd"].iloc[0] == "0"
        assert result["msg_cd"].iloc[0] == ""
        assert result["msg1"].iloc[0] == ""

    def test_add_api_metadata_to_dataframe_empty_response(self):
        """빈 응답 처리"""
        # Given
        df = pd.DataFrame([{"name": "test"}])
        response = {}

        # When
        result = add_api_metadata_to_dataframe(df, response)

        # Then
        assert result["rt_cd"].iloc[0] == ""
        assert result["msg_cd"].iloc[0] == ""
        assert result["msg1"].iloc[0] == ""

    def test_create_dataframe_with_metadata_from_list(self):
        """리스트 데이터로부터 메타데이터 포함 DataFrame 생성"""
        # Given
        data = [{"name": "item1", "value": 100}, {"name": "item2", "value": 200}]
        response = {"rt_cd": "0", "msg_cd": "SUCCESS"}

        # When
        result = create_dataframe_with_metadata(data, response)

        # Then
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert result["rt_cd"].iloc[0] == "0"
        assert result["name"].iloc[0] == "item1"
        assert result["value"].iloc[1] == 200

    def test_create_dataframe_with_metadata_from_dict(self):
        """딕셔너리 데이터로부터 메타데이터 포함 DataFrame 생성"""
        # Given
        data = {"name": "single_item", "value": 500}
        response = {"rt_cd": "0", "msg_cd": "SUCCESS"}

        # When
        result = create_dataframe_with_metadata(data, response)

        # Then
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result["rt_cd"].iloc[0] == "0"
        assert result["name"].iloc[0] == "single_item"
        assert result["value"].iloc[0] == 500

    def test_create_dataframe_with_metadata_empty_data(self):
        """빈 데이터 처리"""
        # Given
        data = []
        response = {"rt_cd": "0"}

        # When
        result = create_dataframe_with_metadata(data, response)

        # Then
        assert result is None

    def test_create_dataframe_with_metadata_none_data(self):
        """None 데이터 처리"""
        # Given
        data = None
        response = {"rt_cd": "0"}

        # When
        result = create_dataframe_with_metadata(data, response)

        # Then
        assert result is None

    def test_create_dataframe_with_metadata_invalid_data_type(self):
        """지원하지 않는 데이터 타입 처리"""
        # Given
        data = "invalid_string_data"
        response = {"rt_cd": "0"}

        # When
        result = create_dataframe_with_metadata(data, response)

        # Then
        assert result is None

    def test_extract_output_data_with_output(self):
        """output 키가 있는 경우"""
        # Given
        response = {
            "rt_cd": "0",
            "output": [{"data": "value"}],
            "output1": [{"data": "other"}],
        }

        # When
        result = extract_output_data(response)

        # Then
        assert result == [{"data": "value"}]

    def test_extract_output_data_with_output1(self):
        """output1 키만 있는 경우"""
        # Given
        response = {
            "rt_cd": "0",
            "output1": [{"data": "value1"}],
            "output2": [{"data": "value2"}],
        }

        # When
        result = extract_output_data(response)

        # Then
        assert result == [{"data": "value1"}]

    def test_extract_output_data_with_preferred_key(self):
        """우선 키 지정된 경우"""
        # Given
        response = {"output": [{"data": "default"}], "output2": [{"data": "preferred"}]}

        # When
        result = extract_output_data(response, preferred_key="output2")

        # Then
        assert result == [{"data": "preferred"}]

    def test_extract_output_data_preferred_key_not_exist(self):
        """우선 키가 존재하지 않는 경우"""
        # Given
        response = {"output": [{"data": "default"}], "output1": [{"data": "fallback"}]}

        # When
        result = extract_output_data(response, preferred_key="nonexistent")

        # Then
        assert result == [{"data": "default"}]

    def test_extract_output_data_no_output(self):
        """output 관련 키가 없는 경우"""
        # Given
        response = {"rt_cd": "0", "msg1": "no output data"}

        # When
        result = extract_output_data(response)

        # Then
        assert result is None

    def test_extract_output_data_empty_output(self):
        """output이 빈 값인 경우"""
        # Given
        response = {"rt_cd": "0", "output": [], "output1": [{"data": "fallback"}]}

        # When
        result = extract_output_data(response)

        # Then
        assert result == [{"data": "fallback"}]

    def test_extract_output_data_none_response(self):
        """None 응답 처리"""
        # Given
        response = None

        # When
        result = extract_output_data(response)

        # Then
        assert result is None

    def test_extract_output_data_empty_response(self):
        """빈 응답 처리"""
        # Given
        response = {}

        # When
        result = extract_output_data(response)

        # Then
        assert result is None
