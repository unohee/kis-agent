"""Historical intraday volume profiles used to shape VWAP schedules.

A profile answers one question: for a given minute of the trading session, how
much volume does this ticker usually trade? The VWAP executor turns that into
per-bucket weights so the parent order is worked harder when the market is
liquid and backs off when it is not.

The profile is built from completed prior sessions only. Today's partial tape
is deliberately excluded — half a session tells you nothing about the buckets
that have not happened yet, and mixing it in would silently bias the schedule
toward the morning.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Mapping, Optional, Sequence

logger = logging.getLogger(__name__)

__all__ = ["VolumeProfile", "build_profile_from_bars", "fetch_volume_profile"]

# Guard against an unbounded walk backwards when a market is closed for a long
# stretch (holidays, suspensions). Roughly six weeks of calendar days.
_MAX_LOOKBACK_DAYS = 45


def _to_float(value: Any) -> float:
    """Parse a KIS numeric field, tolerating commas, blanks and None."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _minute_of_day(hhmmss: Any) -> Optional[int]:
    """Convert a ``HHMMSS`` (or ``HHMM``) stamp to minutes since midnight."""
    text = str(hhmmss or "").strip()
    if len(text) < 4 or not text[:4].isdigit():
        return None
    hour = int(text[:2])
    minute = int(text[2:4])
    if hour > 23 or minute > 59:
        return None
    return hour * 60 + minute


@dataclass
class VolumeProfile:
    """Average traded volume per minute of the session.

    Attributes:
        minute_volumes: Minutes since midnight mapped to the average volume
            observed in that minute across ``source_dates``.
        source_dates: ``YYYYMMDD`` sessions that contributed to the average.
        fallback_reason: Human-readable explanation of why the profile is
            empty, or ``None`` when real data was collected. Callers surface
            this instead of silently degrading to an even split.
    """

    minute_volumes: Dict[int, float] = field(default_factory=dict)
    source_dates: List[str] = field(default_factory=list)
    fallback_reason: Optional[str] = None

    @property
    def is_empty(self) -> bool:
        """True when the profile carries no usable volume information."""
        return not self.minute_volumes or sum(self.minute_volumes.values()) <= 0

    def bucket_weights(
        self, start: datetime, duration: timedelta, buckets: int
    ) -> Optional[List[float]]:
        """Aggregate the profile into ``buckets`` weights over a time window.

        Each bucket covers ``duration / buckets`` and is half-open — the minute
        that starts exactly on a boundary belongs to the later bucket, so no
        minute is counted twice.

        Args:
            start: Wall-clock start of the execution window.
            duration: Total length of the execution window. Must be positive.
            buckets: Number of equal buckets to aggregate into. Must be > 0.

        Returns:
            One weight per bucket, or ``None`` when the profile is empty or the
            window covers no traded minutes at all (for example an overnight
            window). ``None`` tells the caller to fall back to an even split.

        Raises:
            ValueError: If ``buckets`` or ``duration`` is not positive.
        """
        if buckets <= 0:
            raise ValueError(f"buckets must be positive, got {buckets}")
        if duration <= timedelta(0):
            raise ValueError(f"duration must be positive, got {duration}")
        if self.is_empty:
            return None

        interval = duration / buckets
        weights: List[float] = []
        for i in range(buckets):
            window_start = start + interval * i
            window_end = start + interval * (i + 1)
            weights.append(self._volume_between(window_start, window_end))

        if sum(weights) <= 0:
            return None
        return weights

    def _volume_between(self, start: datetime, end: datetime) -> float:
        """Sum profiled volume over the half-open interval ``[start, end)``."""
        total = 0.0
        # Walk minute by minute rather than filtering the dict, so a window
        # spanning a day boundary still lands on the right minute-of-day keys.
        cursor = start.replace(second=0, microsecond=0)
        if cursor < start:
            cursor += timedelta(minutes=1)
        # A window longer than a session would double-count the same
        # minute-of-day key; cap the walk at 24h for safety.
        limit = min(end, start + timedelta(days=1))
        while cursor < limit:
            total += self.minute_volumes.get(cursor.hour * 60 + cursor.minute, 0.0)
            cursor += timedelta(minutes=1)
        return total


def build_profile_from_bars(
    bars_by_date: Mapping[str, Sequence[Mapping[str, Any]]],
    time_field: str = "stck_cntg_hour",
    volume_field: str = "cntg_vol",
) -> VolumeProfile:
    """Average a set of per-session minute bars into a single volume profile.

    Args:
        bars_by_date: ``YYYYMMDD`` mapped to that session's minute bars, as
            returned in ``output2`` of the KIS minute-chart endpoint.
        time_field: Bar key holding the ``HHMMSS`` stamp.
        volume_field: Bar key holding that minute's traded volume.

    Returns:
        A profile averaged over the sessions that actually contributed volume.
        Sessions that are empty or unparseable are skipped and excluded from
        ``source_dates``, so the average is never diluted by blank days.
    """
    totals: Dict[int, float] = {}
    contributing: List[str] = []

    for date, bars in sorted(bars_by_date.items()):
        session_added = False
        for bar in bars or []:
            minute = _minute_of_day(bar.get(time_field))
            if minute is None:
                continue
            volume = _to_float(bar.get(volume_field))
            if volume <= 0:
                continue
            totals[minute] = totals.get(minute, 0.0) + volume
            session_added = True
        if session_added:
            contributing.append(date)

    if not contributing:
        return VolumeProfile(fallback_reason="분봉 거래량 데이터를 수집하지 못했습니다")

    divisor = float(len(contributing))
    averaged = {minute: total / divisor for minute, total in totals.items()}
    return VolumeProfile(minute_volumes=averaged, source_dates=contributing)


def fetch_volume_profile(
    agent: Any,
    code: str,
    days: int = 5,
    end_date: Optional[datetime] = None,
    market: str = "J",
) -> VolumeProfile:
    """Fetch and average minute bars for the last ``days`` completed sessions.

    Weekends are skipped by calendar arithmetic; holidays are skipped implicitly
    because the endpoint returns no bars for them. The walk backwards is bounded
    so a long market closure cannot spin forever.

    Args:
        agent: Object exposing ``stock_api.get_daily_minute_price(code, date)``.
        code: Six-digit domestic ticker.
        days: Number of completed sessions to average. Must be > 0.
        end_date: Treat this date as "today"; sessions strictly before it are
            collected. Defaults to the current date.
        market: KIS market division code (``J`` = KRX).

    Returns:
        The averaged profile. On total failure the profile is empty and carries
        a ``fallback_reason`` — this function never raises for API problems,
        because a missing profile degrades to an even split rather than
        blocking execution.

    Raises:
        ValueError: If ``days`` is not positive.
    """
    if days <= 0:
        raise ValueError(f"days must be positive, got {days}")

    cursor = (end_date or datetime.now()).date()
    bars_by_date: Dict[str, Sequence[Mapping[str, Any]]] = {}
    errors: List[str] = []
    walked = 0

    while len(bars_by_date) < days and walked < _MAX_LOOKBACK_DAYS:
        cursor -= timedelta(days=1)
        walked += 1
        if cursor.weekday() >= 5:  # Saturday/Sunday
            continue

        date_str = cursor.strftime("%Y%m%d")
        try:
            result = agent.stock_api.get_daily_minute_price(
                code=code, date=date_str, market=market
            )
        except Exception as e:  # noqa: BLE001 - degrade to even split, never crash
            logger.warning("분봉 조회 실패 (%s %s): %s", code, date_str, e)
            errors.append(f"{date_str}: {e}")
            continue

        bars = (result or {}).get("output2") or []
        if bars:
            bars_by_date[date_str] = bars

    if not bars_by_date:
        reason = "최근 영업일 분봉 데이터를 찾지 못했습니다"
        if errors:
            reason += f" (오류 {len(errors)}건: {errors[0]})"
        return VolumeProfile(fallback_reason=reason)

    return build_profile_from_bars(bars_by_date)
