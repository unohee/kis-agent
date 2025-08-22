# DataFrame 변환 헬퍼 함수들
# 생성일: 2025-01-21
# 목적: API 응답을 DataFrame으로 변환할 때 rt_cd 등 메타데이터 추가

import pandas as pd
from typing import Any, Optional


def add_api_metadata_to_dataframe(df: pd.DataFrame, response: dict) -> pd.DataFrame:
    """
    DataFrame에 API 응답 메타데이터 추가

    Args:
        df: 원본 DataFrame
        response: API 응답 딕셔너리

    Returns:
        메타데이터가 추가된 DataFrame
    """
    df_copy = df.copy()
    df_copy["rt_cd"] = response.get("rt_cd", "")
    df_copy["msg_cd"] = response.get("msg_cd", "")
    df_copy["msg1"] = response.get("msg1", "")
    return df_copy


def create_dataframe_with_metadata(data, response: dict) -> Optional[pd.DataFrame]:
    """
    데이터와 API 응답으로부터 메타데이터가 포함된 DataFrame 생성

    Args:
        data: DataFrame으로 변환할 데이터 (list 또는 dict)
        response: API 응답 딕셔너리

    Returns:
        메타데이터가 포함된 DataFrame 또는 None
    """
    if not data:
        return None

    # DataFrame 생성
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        return None

    # 메타데이터 추가
    return add_api_metadata_to_dataframe(df, response)


def extract_output_data(response: dict, preferred_key: str = None) -> Any:
    """
    API 응답에서 output 데이터 추출 (output, output1, output2 등 대응)

    Args:
        response: API 응답 딕셔너리
        preferred_key: 우선적으로 찾을 키 (없으면 순서대로 검색)

    Returns:
        추출된 output 데이터
    """
    if not response:
        return None

    # 우선 키가 지정되고 해당 키가 존재하면 반환
    if preferred_key and preferred_key in response:
        return response[preferred_key]

    # 일반적인 output 키들을 순서대로 확인
    for key in ["output", "output1", "output2", "output3"]:
        if key in response and response[key]:
            return response[key]

    return None
