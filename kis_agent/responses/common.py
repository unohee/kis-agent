"""
Common Response Types - 공통 응답 구조체

한국투자증권 API의 기본 응답 형식 및 공통 필드 정의
"""

from typing import TypedDict


class BaseResponse(TypedDict, total=False):
    """
    API 기본 응답 구조

    모든 한국투자증권 API 응답의 공통 필드
    """

    rt_cd: str  # 응답코드 (Response Code) - "0": 성공, 기타: 오류
    msg_cd: str  # 메시지코드 (Message Code)
    msg1: str  # 응답메시지 (Response Message)
    status_code: int  # HTTP 상태코드 (HTTP Status Code, optional)


class OutputField(TypedDict, total=False):
    """
    일반 output 필드 구조

    대부분의 API 응답에서 사용되는 기본 출력 형식
    """

    pass  # 구체적인 output 구조는 각 API별로 정의
