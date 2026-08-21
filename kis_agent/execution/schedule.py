"""Deterministic order-slicing schedules for algorithmic execution.

This module is intentionally free of I/O and clock access: every function is
pure, so schedules can be built, inspected and unit-tested without touching the
KIS API. The executor consumes the resulting :class:`OrderSlice` list.

Two schedule shapes are supported:

* TWAP (Time Weighted Average Price) — the quantity is spread evenly across
  equally spaced slices.
* VWAP (Volume Weighted Average Price) — the quantity follows a historical
  intraday volume profile, so more shares are worked during the parts of the
  session that usually trade the most.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Sequence

__all__ = [
    "OrderSlice",
    "split_quantity",
    "split_quantity_weighted",
    "build_twap_schedule",
    "build_vwap_schedule",
]


@dataclass(frozen=True)
class OrderSlice:
    """A single child order produced by a slicing schedule.

    Attributes:
        index: Zero-based position of the slice within the schedule.
        scheduled_at: Wall-clock time the slice should be submitted at.
        quantity: Share count for this slice. Always >= 1.
        weight: Fraction of the parent order this slice represents (0.0-1.0).
            For TWAP every slice carries the same weight.
    """

    index: int
    scheduled_at: datetime
    quantity: int
    weight: float = 0.0


def split_quantity(total: int, parts: int) -> List[int]:
    """Split ``total`` into ``parts`` chunks using the largest-remainder method.

    The returned chunks always sum back to ``total`` exactly, and differ from
    each other by at most one share. When ``total`` is smaller than ``parts``
    the result is shorter than ``parts`` rather than padded with zeros, because
    a zero-share child order is not a thing the exchange accepts.

    Args:
        total: Total share count to distribute. Must be > 0.
        parts: Desired number of chunks. Must be > 0.

    Returns:
        Chunk sizes, largest first where the remainder forces a difference.

    Raises:
        ValueError: If ``total`` or ``parts`` is not positive.

    Examples:
        >>> split_quantity(10, 3)
        [4, 3, 3]
        >>> split_quantity(2, 5)
        [1, 1]
    """
    if total <= 0:
        raise ValueError(f"total must be positive, got {total}")
    if parts <= 0:
        raise ValueError(f"parts must be positive, got {parts}")

    parts = min(parts, total)
    base, remainder = divmod(total, parts)
    return [base + (1 if i < remainder else 0) for i in range(parts)]


def split_quantity_weighted(total: int, weights: Sequence[float]) -> List[int]:
    """Distribute ``total`` across ``weights`` using the largest-remainder method.

    The chunks sum back to ``total`` exactly. Buckets whose weight is too small
    to earn a whole share receive ``0`` and are meant to be dropped by the
    caller — that is the correct outcome for a volume schedule, since working
    shares into a bucket that historically trades nothing only adds impact.

    Args:
        total: Total share count to distribute. Must be > 0.
        weights: Relative weight per bucket. Negative values are rejected; a
            weight vector that sums to zero falls back to an even split.

    Returns:
        Share count per bucket, positionally aligned with ``weights``.

    Raises:
        ValueError: If ``total`` is not positive, ``weights`` is empty, or any
            weight is negative.

    Examples:
        >>> split_quantity_weighted(100, [1.0, 3.0])
        [25, 75]
        >>> split_quantity_weighted(10, [0.0, 0.0])
        [5, 5]
    """
    if total <= 0:
        raise ValueError(f"total must be positive, got {total}")
    if not weights:
        raise ValueError("weights must not be empty")
    if any(w < 0 for w in weights):
        raise ValueError("weights must not contain negative values")

    weight_sum = float(sum(weights))
    if weight_sum <= 0:
        # A flat (or empty) profile carries no information — fall back to TWAP.
        even = split_quantity(total, len(weights))
        return even + [0] * (len(weights) - len(even))

    exact = [w / weight_sum * total for w in weights]
    floors = [int(x) for x in exact]
    remainder = total - sum(floors)

    # Largest-remainder: hand the leftover shares to the buckets that lost the
    # most in truncation. Position breaks ties so the outcome is deterministic.
    order = sorted(range(len(weights)), key=lambda i: (-(exact[i] - floors[i]), i))
    for i in order[:remainder]:
        floors[i] += 1

    return floors


def _slice_times(start: datetime, count: int, interval: timedelta) -> List[datetime]:
    """Return ``count`` evenly spaced timestamps beginning at ``start``."""
    return [start + interval * i for i in range(count)]


def build_twap_schedule(
    total_quantity: int,
    slices: int,
    start: datetime,
    duration: timedelta,
) -> List[OrderSlice]:
    """Build an evenly spaced, evenly sized TWAP schedule.

    The first slice fires at ``start`` and the last one fires ``duration`` minus
    one interval later, so the whole schedule finishes within ``duration``
    rather than one interval past it.

    Args:
        total_quantity: Parent order size in shares. Must be > 0.
        slices: Requested number of child orders. Must be > 0. Capped at
            ``total_quantity`` because a slice cannot be smaller than a share.
        start: Timestamp of the first child order.
        duration: Total wall-clock window the parent order should be worked
            over. Must be > 0.

    Returns:
        Child orders in chronological order.

    Raises:
        ValueError: If any argument is out of range.

    Examples:
        >>> from datetime import datetime, timedelta
        >>> sched = build_twap_schedule(
        ...     100, 4, datetime(2026, 8, 21, 10, 0), timedelta(minutes=20)
        ... )
        >>> [(s.quantity, s.scheduled_at.strftime("%H:%M")) for s in sched]
        [(25, '10:00'), (25, '10:05'), (25, '10:10'), (25, '10:15')]
    """
    if duration <= timedelta(0):
        raise ValueError(f"duration must be positive, got {duration}")

    quantities = split_quantity(total_quantity, slices)
    count = len(quantities)
    interval = duration / count

    times = _slice_times(start, count, interval)
    weight = 1.0 / count
    return [
        OrderSlice(
            index=i, scheduled_at=times[i], quantity=quantities[i], weight=weight
        )
        for i in range(count)
    ]


def build_vwap_schedule(
    total_quantity: int,
    slices: int,
    start: datetime,
    duration: timedelta,
    weights: Optional[Sequence[float]] = None,
) -> List[OrderSlice]:
    """Build a volume-weighted schedule over equally spaced time buckets.

    The timing grid is identical to :func:`build_twap_schedule`; only the size
    of each child order differs, following ``weights``. Passing ``None`` (or an
    all-zero profile) degrades gracefully to an even TWAP-style split.

    Args:
        total_quantity: Parent order size in shares. Must be > 0.
        slices: Number of time buckets. Must be > 0.
        start: Timestamp of the first bucket.
        duration: Total wall-clock window. Must be > 0.
        weights: Relative expected volume per bucket. Must have exactly
            ``slices`` entries when provided.

    Returns:
        Child orders in chronological order. Buckets whose expected volume is
        too small to earn a whole share are omitted entirely, so the returned
        list can be shorter than ``slices``.

    Raises:
        ValueError: If any argument is out of range, or ``weights`` length does
            not match ``slices``.

    Examples:
        >>> from datetime import datetime, timedelta
        >>> sched = build_vwap_schedule(
        ...     100, 2, datetime(2026, 8, 21, 10, 0), timedelta(minutes=20),
        ...     weights=[1.0, 3.0],
        ... )
        >>> [s.quantity for s in sched]
        [25, 75]
    """
    if total_quantity <= 0:
        raise ValueError(f"total_quantity must be positive, got {total_quantity}")
    if slices <= 0:
        raise ValueError(f"slices must be positive, got {slices}")
    if duration <= timedelta(0):
        raise ValueError(f"duration must be positive, got {duration}")

    if weights is None:
        return build_twap_schedule(total_quantity, slices, start, duration)

    if len(weights) != slices:
        raise ValueError(
            f"weights length {len(weights)} does not match slices {slices}"
        )

    quantities = split_quantity_weighted(total_quantity, weights)
    interval = duration / slices
    times = _slice_times(start, slices, interval)

    weight_sum = float(sum(weights))
    if weight_sum > 0:
        normalized = [w / weight_sum for w in weights]
    else:
        normalized = [1.0 / slices] * slices

    schedule: List[OrderSlice] = []
    for i, qty in enumerate(quantities):
        if qty <= 0:
            # Bucket too thin to earn a whole share — skip it entirely.
            continue
        schedule.append(
            OrderSlice(
                index=len(schedule),
                scheduled_at=times[i],
                quantity=qty,
                weight=normalized[i],
            )
        )
    return schedule
