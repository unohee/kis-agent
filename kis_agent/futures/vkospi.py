"""
VKOSPI 프록시 계산기

KRX가 공식 발표하는 VKOSPI는 KOSPI200 OTM 옵션의 베가 가중 내재변동성(IV)을
선근월/차근월 사이 선형 보간하여 30일 잔존만기 기준으로 환산한 값이다.

이 모듈은 KIS display_board_callput API가 제공하는 `hts_ints_vltl`(HTS 내재변동성)을
활용해 장중 VKOSPI를 근사 계산한다. 공식값 대비 ±2pt 오차 목표.

산출 공식 (KRX VIX 방법론 준용):
    w_near = (T2 - 30) / (T2 - T1)
    w_far  = (30 - T1) / (T2 - T1)
    VKOSPI_proxy = w_near * IV_near + w_far * IV_far

단, T1/T2 = 선근월/차근월 잔존 거래일수(캘린더일 아닌 영업일 기준은 단순화하여
만기까지 캘린더일 사용).

참고:
    - 필터 조건: OTM만 사용 (atm_cls_name이 "OTM" 포함)
    - 최소 거래량: acml_vol >= MIN_VOLUME (기본 10)
    - 유효 IV: hts_ints_vltl이 비어있지 않고 0이 아닌 경우
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

# 최소 거래량 필터 — 유동성 없는 OTM 제거
MIN_VOLUME = 10


def get_second_thursday(year: int, month: int) -> date:
    """해당 년월의 두 번째 목요일(선물옵션 만기일) 반환"""
    first = date(year, month, 1)
    days_to_thursday = (3 - first.weekday()) % 7
    first_thursday = first + timedelta(days=days_to_thursday)
    return first_thursday + timedelta(days=7)


def get_option_expiry_months(
    today: date | None = None,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    선근월/차근월 (year, month) 쌍 반환.

    KOSPI200 옵션은 매월 만기(두 번째 목요일). 만기일이 지나면 다음달로 넘어간다.

    Returns:
        ((near_year, near_month), (far_year, far_month))
    """
    if today is None:
        today = date.today()

    # 이번달 만기일
    expiry = get_second_thursday(today.year, today.month)

    if today > expiry:
        # 만기 지난 경우 → 선근월=다음달, 차근월=다음다음달
        near = _add_months(today.year, today.month, 1)
    else:
        near = (today.year, today.month)

    far = _add_months(near[0], near[1], 1)
    return near, far


def get_days_to_expiry(year: int, month: int, today: date | None = None) -> int:
    """오늘부터 해당 년월 만기일까지 캘린더일 수"""
    if today is None:
        today = date.today()
    expiry = get_second_thursday(year, month)
    return max(0, (expiry - today).days)


def interpolation_weights(t1: int, t2: int) -> tuple[float, float]:
    """
    30일 잔존만기 기준 선형 보간 가중치.

    Args:
        t1: 선근월 잔존일수
        t2: 차근월 잔존일수

    Returns:
        (w_near, w_far) — 합계 1.0
    """
    if t2 == t1:
        return 1.0, 0.0
    w_near = (t2 - 30) / (t2 - t1)
    w_far = (30 - t1) / (t2 - t1)
    # 30일이 t1/t2 범위 밖이면 클리핑 (비정상 만기 구조 대응)
    w_near = max(0.0, min(1.0, w_near))
    w_far = 1.0 - w_near
    return w_near, w_far


def _add_months(year: int, month: int, n: int) -> tuple[int, int]:
    month += n
    year += (month - 1) // 12
    month = (month - 1) % 12 + 1
    return year, month


def _parse_float(s: str) -> float | None:
    """문자열을 float으로 변환. 빈 문자열/'-'/공백은 None."""
    if not s or s.strip() in ("-", ""):
        return None
    try:
        v = float(s.strip())
        return v if v != 0.0 else None
    except ValueError:
        return None


def _is_otm(row: dict) -> bool:
    """OTM 옵션 여부 — atm_cls_name 필드 기준."""
    cls = row.get("atm_cls_name", "")
    return "OTM" in cls.upper()


def _calc_vega_weighted_iv(rows: list[dict]) -> float | None:
    """
    OTM 행들의 베가 가중 평균 IV 계산.

    vega 필드가 없거나 모두 0이면 단순 평균으로 대체.
    """
    valid = []
    for row in rows:
        if not _is_otm(row):
            continue
        vol = _parse_float(row.get("acml_vol", ""))
        if vol is None or vol < MIN_VOLUME:
            continue
        iv = _parse_float(row.get("hts_ints_vltl", ""))
        if iv is None:
            continue
        vega = _parse_float(row.get("vega", "")) or 1.0  # vega 없으면 동등 가중
        valid.append((iv, abs(vega)))

    if not valid:
        return None

    total_vega = sum(v for _, v in valid)
    return sum(iv * v for iv, v in valid) / total_vega


class VKOSPIResult:
    """VKOSPI 프록시 계산 결과"""

    def __init__(
        self,
        value: float,
        near_iv: float,
        far_iv: float,
        near_days: int,
        far_days: int,
        w_near: float,
        w_far: float,
        near_sample_count: int,
        far_sample_count: int,
        calculated_at: datetime,
    ):
        self.value = value
        self.near_iv = near_iv
        self.far_iv = far_iv
        self.near_days = near_days
        self.far_days = far_days
        self.w_near = w_near
        self.w_far = w_far
        self.near_sample_count = near_sample_count
        self.far_sample_count = far_sample_count
        self.calculated_at = calculated_at

    def __repr__(self) -> str:
        return (
            f"VKOSPIResult(value={self.value:.2f}, "
            f"near_iv={self.near_iv:.2f}(T={self.near_days}d, n={self.near_sample_count}), "
            f"far_iv={self.far_iv:.2f}(T={self.far_days}d, n={self.far_sample_count}), "
            f"w=[{self.w_near:.3f}, {self.w_far:.3f}])"
        )


class VKOSPICalculator:
    """
    VKOSPI 프록시 계산기.

    KIS display_board_callput 응답(output1=콜, output2=풋)을 받아
    선근월/차근월 베가 가중 IV를 보간하여 VKOSPI를 근사한다.

    Usage:
        calc = VKOSPICalculator()
        result = calc.calculate(near_response, far_response)
        print(result.value)  # VKOSPI 프록시 값
    """

    def calculate(
        self,
        near_response: dict,
        far_response: dict,
        today: date | None = None,
    ) -> VKOSPIResult | None:
        """
        VKOSPI 프록시 계산.

        Args:
            near_response: 선근월 display_board_callput 응답 dict
                           (output1=콜 List[Row], output2=풋 List[Row])
            far_response:  차근월 응답 (동일 구조)
            today:         기준일 (None이면 date.today())

        Returns:
            VKOSPIResult 또는 None (유효 샘플 부족)
        """
        if today is None:
            today = date.today()

        near_month, far_month = get_option_expiry_months(today)
        t1 = get_days_to_expiry(*near_month, today)
        t2 = get_days_to_expiry(*far_month, today)

        near_rows = (near_response.get("output1") or []) + (
            near_response.get("output2") or []
        )
        far_rows = (far_response.get("output1") or []) + (
            far_response.get("output2") or []
        )

        near_iv = _calc_vega_weighted_iv(near_rows)
        far_iv = _calc_vega_weighted_iv(far_rows)

        if near_iv is None or far_iv is None:
            return None

        w_near, w_far = interpolation_weights(t1, t2)
        value = w_near * near_iv + w_far * far_iv

        near_sample_count = sum(
            1
            for r in near_rows
            if _is_otm(r)
            and (_parse_float(r.get("acml_vol", "")) or 0) >= MIN_VOLUME
            and _parse_float(r.get("hts_ints_vltl", "")) is not None
        )
        far_sample_count = sum(
            1
            for r in far_rows
            if _is_otm(r)
            and (_parse_float(r.get("acml_vol", "")) or 0) >= MIN_VOLUME
            and _parse_float(r.get("hts_ints_vltl", "")) is not None
        )

        return VKOSPIResult(
            value=round(value, 2),
            near_iv=round(near_iv, 4),
            far_iv=round(far_iv, 4),
            near_days=t1,
            far_days=t2,
            w_near=round(w_near, 4),
            w_far=round(w_far, 4),
            near_sample_count=near_sample_count,
            far_sample_count=far_sample_count,
            calculated_at=datetime.now(),
        )

    def calculate_from_single(
        self,
        response: dict,
        today: date | None = None,
    ) -> float | None:
        """
        단일 만기 응답으로 단순 베가 가중 IV만 반환 (보간 없음).
        선근월 만료까지 30일 이내일 때 빠른 근사에 사용.
        """
        rows = (response.get("output1") or []) + (response.get("output2") or [])
        return _calc_vega_weighted_iv(rows)
