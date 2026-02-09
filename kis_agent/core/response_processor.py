"""
API Response Processor - API 응답 처리 전용 모듈

Factory Pattern을 적용하여 BaseAPI의 복잡한 응답 처리 로직을 분리
- 응답 검증
- 데이터 추출
- DataFrame 변환
- 메타데이터 추가
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import pandas as pd


class ResponseProcessor(ABC):
    """API 응답 처리기 추상 클래스"""

    @abstractmethod
    def process(self, response: Dict, field_type: Optional[str] = None) -> Any:
        """응답 처리 추상 메서드"""
        pass


class DictResponseProcessor(ResponseProcessor):
    """Dict 형태 응답 처리기"""

    def process(
        self, response: Dict, field_type: Optional[str] = None
    ) -> Optional[Dict]:
        """Dict 응답을 그대로 반환 (이미 rt_cd 포함)"""
        if not response:
            return None
        return response


class DataFrameResponseProcessor(ResponseProcessor):
    """DataFrame 형태 응답 처리기"""

    def __init__(self, metadata_adder, field_converter):
        """
        DataFrame 처리기 초기화

        Args:
            metadata_adder: 메타데이터 추가 함수
            field_converter: 필드 변환 함수
        """
        self.add_metadata = metadata_adder
        self.convert_fields = field_converter

    def process(
        self, response: Dict, field_type: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """응답을 DataFrame으로 변환하여 반환"""
        if not response or response.get("rt_cd") != "0":
            return None

        # 1. 데이터 추출
        output_data = self._extract_output_data(response)
        if not output_data:
            return None

        # 2. DataFrame 변환
        df = self._convert_to_dataframe(output_data)
        if df is None:
            return None

        # 3. 메타데이터 추가
        df = self.add_metadata(df, response)

        # 4. 숫자형 필드 변환
        return self.convert_fields(df, field_type)

    def _extract_output_data(self, response: Dict) -> Optional[Union[List, Dict]]:
        """응답에서 output 데이터 추출"""
        for key in ["output", "output1", "output2"]:
            if key in response and response[key]:
                return response[key]
        return None

    def _convert_to_dataframe(
        self, output_data: Union[List, Dict]
    ) -> Optional[pd.DataFrame]:
        """output 데이터를 DataFrame으로 변환"""
        try:
            if isinstance(output_data, list):
                return pd.DataFrame(output_data)
            elif isinstance(output_data, dict):
                return pd.DataFrame([output_data])
            else:
                return None
        except Exception as e:
            logging.error(f"DataFrame 변환 실패: {e}")
            return None


class ResponseProcessorFactory:
    """
    Factory Pattern을 적용한 응답 처리기 팩토리

    응답 타입에 따라 적절한 처리기를 생성합니다.
    """

    @staticmethod
    def create_processor(
        return_dataframe: bool, metadata_adder=None, field_converter=None
    ) -> ResponseProcessor:
        """
        응답 타입에 따른 처리기 생성

        Args:
            return_dataframe: DataFrame 반환 여부
            metadata_adder: 메타데이터 추가 함수
            field_converter: 필드 변환 함수

        Returns:
            ResponseProcessor: 적절한 응답 처리기
        """
        if return_dataframe:
            if not metadata_adder or not field_converter:
                raise ValueError(
                    "DataFrame 처리기는 metadata_adder와 field_converter가 필요합니다"
                )
            return DataFrameResponseProcessor(metadata_adder, field_converter)
        else:
            return DictResponseProcessor()


class APIRequestManager:
    """
    API 요청 관리자 - Template Method Pattern 적용

    공통 요청 플로우를 정의하고 세부사항은 하위 클래스에서 구현
    """

    def __init__(self, client, metadata_adder=None, field_converter=None):
        """
        API 요청 관리자 초기화

        Args:
            client: API 클라이언트
            metadata_adder: 메타데이터 추가 함수
            field_converter: 필드 변환 함수
        """
        self.client = client
        self.metadata_adder = metadata_adder
        self.field_converter = field_converter

    def make_request_with_processing(
        self,
        endpoint: str,
        tr_id: str,
        params: Dict,
        field_type: Optional[str] = None,
        return_dataframe: bool = True,
    ) -> Union[Optional[pd.DataFrame], Optional[Dict]]:
        """
        API 요청 및 응답 처리 통합 메서드

        Template Method Pattern으로 공통 플로우 정의:
        1. API 요청 실행
        2. 응답 처리기 생성
        3. 응답 처리 및 반환
        """
        try:
            # 1. API 요청 실행
            response = self.client.make_request(
                endpoint=endpoint, tr_id=tr_id, params=params
            )

            # 2. 응답 처리기 생성 (Factory Pattern)
            processor = ResponseProcessorFactory.create_processor(
                return_dataframe=return_dataframe,
                metadata_adder=self.metadata_adder,
                field_converter=self.field_converter,
            )

            # 3. 응답 처리 및 반환
            return processor.process(response, field_type)

        except Exception as e:
            logging.error(
                f"API 요청 실패 - TR_ID: {tr_id}, Endpoint: {endpoint}, Error: {e}"
            )
            raise Exception(
                f"API 요청 실패 - TR_ID: {tr_id}, Endpoint: {endpoint}, Error: {e}"
            ) from e
