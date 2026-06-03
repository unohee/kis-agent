"""kis-agent 전역 상수 정의 모듈.

URL/엔드포인트/계좌 상품코드 등 코드 곳곳에 산재했던 매직 리터럴을
단일 진실의 출처(single source of truth)로 모은다.

다른 모듈에서는 항상 이 모듈을 import해서 참조한다 — 문자열 리터럴 중복 금지.
"""

from enum import Enum

REAL_BASE_URL = "https://openapi.koreainvestment.com:9443"
MOCK_BASE_URL = "https://openapivts.koreainvestment.com:29443"

# WebSocket 엔드포인트
# (KIS 공식 샘플 open-trading-api/legacy/websocket/python/* 에서 확인된 값)
WS_REAL_URL = "ws://ops.koreainvestment.com:21000"
WS_MOCK_URL = "ws://ops.koreainvestment.com:31000"

KIS_USER_AGENT_DEFAULT = "KIS_AGENT"


def get_ws_url(is_real: bool = True) -> str:
    """실전/모의 WebSocket URL을 선택한다.

    KIS는 실전과 모의 WS 엔드포인트를 분리 운영한다:
    - 실전: `ws://ops.koreainvestment.com:21000` (`WS_REAL_URL`)
    - 모의: `ws://ops.koreainvestment.com:31000` (`WS_MOCK_URL`)

    Args:
        is_real: True면 실전 URL, False면 모의 URL.

    Returns:
        선택된 WebSocket URL.

    Example:
        >>> from kis_agent.core.constants import get_ws_url
        >>> from kis_agent.websocket import WSAgent
        >>> ws = WSAgent(approval_key, url=get_ws_url(is_real=False))
    """
    return WS_REAL_URL if is_real else WS_MOCK_URL


class AccountProductCode(str, Enum):
    """계좌 상품코드 (KIS 공식).

    Python 3.8 호환을 위해 `StrEnum` 대신 `str, Enum` 패턴 사용
    (선례: `kis_agent.message_schema.ResponseStatus`).
    """

    STOCK = "01"
    FUTURES = "03"  # 선물옵션 및 해외선물옵션 공통 코드


__all__ = [
    "REAL_BASE_URL",
    "MOCK_BASE_URL",
    "WS_REAL_URL",
    "WS_MOCK_URL",
    "KIS_USER_AGENT_DEFAULT",
    "AccountProductCode",
    "get_ws_url",
]
