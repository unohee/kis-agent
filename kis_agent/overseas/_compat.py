"""
해외주식 API 하위 호환 보조 함수

공식 스펙에 없는 인자를 받기만 하고 전송하지 않을 때 쓰는 경고 헬퍼.
"""

import warnings
from datetime import datetime, timedelta

import pytz


def warn_ignored(method: str, arg: str, hint: str = "") -> None:
    """KIS API에 대응 필드가 없어 무시되는 인자에 DeprecationWarning을 낸다.

    호출부가 기본값이 아닌 값을 줬을 때만 호출해야 한다. 경고 위치가 호출자의
    코드를 가리키도록 ``stacklevel``은 헬퍼 -> 메서드 -> 호출자 기준이다.

    Args:
        method: 메서드 이름
        arg: 무시되는 인자 이름
        hint: 대체 방법 등 추가 안내
    """
    message = f"{method}의 {arg}은(는) KIS API에 없는 필드라 무시됩니다"
    if hint:
        message += f". {hint}"
    warnings.warn(message, DeprecationWarning, stacklevel=3)


def warn_renamed(method: str, old: str, new: str) -> None:
    """옛 인자 이름이 새 이름으로 바뀌었음을 DeprecationWarning으로 알린다.

    값은 새 필드로 그대로 전달된다. 호출부가 옛 인자를 줬을 때만 호출해야 한다.

    Args:
        method: 메서드 이름
        old: 옛 인자 이름
        new: 새 인자 이름
    """
    warnings.warn(
        f"{method}의 {old}은(는) {new}로 이름이 바뀌었습니다. {new}를 쓰세요",
        DeprecationWarning,
        stacklevel=3,
    )


_KST = pytz.timezone("Asia/Seoul")


def _utc_now() -> datetime:
    """현재 시각(UTC). 테스트에서 고정값으로 바꿀 수 있도록 분리했다."""
    return datetime.now(pytz.utc)


def kst_date(days: int = 0) -> str:
    """서울 기준 오늘(+``days``일)을 YYYYMMDD로 반환한다.

    조회 API의 날짜 기본값(오늘, N일 전/후)을 호출 시점에 계산하는 데 쓴다.
    """
    return (_utc_now().astimezone(_KST) + timedelta(days=days)).strftime("%Y%m%d")
