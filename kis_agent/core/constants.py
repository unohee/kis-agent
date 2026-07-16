"""kis-agent 전역 상수 정의 모듈.

URL/엔드포인트/계좌 상품코드 등 코드 곳곳에 산재했던 매직 리터럴을
단일 진실의 출처(single source of truth)로 모은다.

다른 모듈에서는 항상 이 모듈을 import해서 참조한다 — 문자열 리터럴 중복 금지.
"""

import os
from enum import Enum
from typing import Optional, Tuple

REAL_BASE_URL = "https://openapi.koreainvestment.com:9443"
MOCK_BASE_URL = "https://openapivts.koreainvestment.com:29443"

# `KIS_PAPER` 환경변수에서 모의투자로 해석하는 값 (대소문자 무시).
_PAPER_TRUTHY = {"1", "true", "yes", "y", "on"}
_PAPER_FALSY = {"0", "false", "no", "n", "off"}

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


def paper_from_env() -> Optional[bool]:
    """Read the `KIS_PAPER` environment variable.

    Returns:
        `True`/`False` if `KIS_PAPER` is set to a recognized value, `None` if it
        is unset (so that a caller can fall back to another signal).

    Raises:
        ValueError: If `KIS_PAPER` is set to an unrecognized value. Silently
            treating a typo as real trading could send live orders.
    """
    raw = os.environ.get("KIS_PAPER")
    if raw is None or raw.strip() == "":
        return None
    value = raw.strip().lower()
    if value in _PAPER_TRUTHY:
        return True
    if value in _PAPER_FALSY:
        return False
    raise ValueError(
        f"KIS_PAPER 환경변수 값이 올바르지 않습니다: {raw!r}. "
        f"허용 값: {sorted(_PAPER_TRUTHY)} 또는 {sorted(_PAPER_FALSY)}"
    )


def resolve_environment(
    base_url: Optional[str] = None, paper: Optional[bool] = None
) -> Tuple[str, bool]:
    """Resolve the base URL and paper-trading flag from the caller's intent.

    Intent may arrive three ways, in descending precedence: the explicit `paper`
    argument, the `KIS_PAPER` environment variable, and the shape of `base_url`
    (`KIS_BASE_URL` included). They are reconciled here so that every entry
    point — `Agent`, the CLI, the bridge — agrees on one answer.

    Args:
        base_url: Explicit base URL, or `None` to derive it from `paper`.
        paper: `True` for paper trading, `False` for real, `None` to infer.

    Returns:
        `(base_url, is_real)`.

    Raises:
        ValueError: If `paper` and `base_url` contradict each other. Guessing
            which one the caller meant risks routing orders to the wrong
            environment, so this fails loudly instead.
    """
    if paper is None:
        paper = paper_from_env()

    if base_url is None:
        base_url = os.environ.get("KIS_BASE_URL") or None

    if base_url is None:
        # 아무 신호도 없으면 실전 (기존 기본값 유지).
        paper = bool(paper)
        return (MOCK_BASE_URL if paper else REAL_BASE_URL), not paper

    url_is_mock = MOCK_BASE_URL in base_url
    if paper is not None and paper != url_is_mock:
        raise ValueError(
            f"paper={paper} 와 base_url={base_url!r} 이 서로 모순됩니다.\n"
            f"  - 모의투자: paper=True (base_url 생략) 또는 base_url={MOCK_BASE_URL!r}\n"
            f"  - 실전투자: paper=False (base_url 생략) 또는 base_url={REAL_BASE_URL!r}"
        )

    return base_url, not url_is_mock


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
    "paper_from_env",
    "resolve_environment",
]
