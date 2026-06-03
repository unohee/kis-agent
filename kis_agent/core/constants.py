"""kis-agent 전역 상수 정의 모듈.

URL/엔드포인트/계좌 상품코드 등 코드 곳곳에 산재했던 매직 리터럴을
단일 진실의 출처(single source of truth)로 모은다.

다른 모듈에서는 항상 이 모듈을 import해서 참조한다 — 문자열 리터럴 중복 금지.
"""

from enum import Enum

REAL_BASE_URL = "https://openapi.koreainvestment.com:9443"
MOCK_BASE_URL = "https://openapivts.koreainvestment.com:29443"

WS_REAL_URL = "ws://ops.koreainvestment.com:21000"
WS_MOCK_URL = "ws://ops.koreainvestment.com:31000"

KIS_USER_AGENT_DEFAULT = "KIS_AGENT"


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
]
