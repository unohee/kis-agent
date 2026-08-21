"""Execution loop that works a sliced schedule into the market.

The executor is deliberately decoupled from :class:`~kis_agent.core.agent.Agent`:
it receives an order callable, an optional price callable and an optional clock.
That keeps the scheduling and guard logic testable without network access, and
lets the same loop drive cash, credit or overseas orders later on.

Timing uses a monotonic anchor rather than repeated wall-clock reads, so an NTP
correction mid-execution cannot compress or stretch the remaining slices, and
order latency does not accumulate into schedule drift.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Sequence

from .schedule import OrderSlice

logger = logging.getLogger(__name__)

__all__ = [
    "SliceExecution",
    "AlgoExecutionResult",
    "AlgoExecutor",
    "SLICE_FILLED",
    "SLICE_SIMULATED",
    "SLICE_SKIPPED",
    "SLICE_FAILED",
    "SLICE_CANCELLED",
    "REASON_SESSION",
    "REASON_PRICE_LIMIT",
    "REASON_PRICE_UNAVAILABLE",
    "REASON_ORDER_REJECTED",
    "REASON_INTERRUPTED",
    "REASON_UPSTREAM_ABORT",
    "NOTE_KEY",
]

SLICE_FILLED = "filled"
SLICE_SIMULATED = "simulated"
SLICE_SKIPPED = "skipped"
SLICE_FAILED = "failed"
SLICE_CANCELLED = "cancelled"

# Machine-readable reasons attached to non-filled slices, so callers branch on
# a stable token instead of parsing the human-readable message.
REASON_SESSION = "outside_session"
REASON_PRICE_LIMIT = "price_limit"
REASON_PRICE_UNAVAILABLE = "price_unavailable"
REASON_ORDER_REJECTED = "order_rejected"
REASON_INTERRUPTED = "interrupted"
REASON_UPSTREAM_ABORT = "upstream_abort"

# Optional key an ``order_func`` may set on its response to attach a note to the
# slice report — used, for example, when a credit order falls back to cash.
NOTE_KEY = "_kis_note"

# Longest single sleep between wake-ups. Bounded so a Ctrl+C during a long
# inter-slice wait is handled promptly and progress callbacks stay responsive.
_SLEEP_CHUNK_SECONDS = 1.0


@dataclass
class SliceExecution:
    """Outcome of one child order."""

    index: int
    scheduled_at: datetime
    quantity: int
    status: str
    submitted_at: Optional[datetime] = None
    order_no: str = ""
    reference_price: Optional[float] = None
    message: str = ""
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Render as a JSON-serialisable mapping."""
        return {
            "index": self.index,
            "scheduledAt": self.scheduled_at.isoformat(),
            "submittedAt": self.submitted_at.isoformat() if self.submitted_at else None,
            "quantity": self.quantity,
            "status": self.status,
            "reason": self.reason,
            "orderNo": self.order_no,
            "referencePrice": self.reference_price,
            "message": self.message,
        }


@dataclass
class AlgoExecutionResult:
    """Aggregate outcome of a sliced parent order.

    ``status`` is one of:

    * ``completed`` — every slice was submitted (or simulated) successfully.
    * ``partial`` — the run finished but some slices were skipped or failed.
    * ``aborted`` — a guard stopped the run before the schedule ran out.
    * ``cancelled`` — the operator interrupted the run (Ctrl+C).
    """

    algorithm: str
    code: str
    side: str
    total_quantity: int
    slices: List[SliceExecution] = field(default_factory=list)
    status: str = "completed"
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    dry_run: bool = False
    notes: List[str] = field(default_factory=list)

    @property
    def submitted_quantity(self) -> int:
        """Shares actually sent to (or simulated against) the exchange."""
        return sum(
            s.quantity
            for s in self.slices
            if s.status in (SLICE_FILLED, SLICE_SIMULATED)
        )

    @property
    def unfilled_quantity(self) -> int:
        """Shares of the parent order that were never worked."""
        return self.total_quantity - self.submitted_quantity

    def to_dict(self) -> Dict[str, Any]:
        """Render as a JSON-serialisable mapping for the CLI."""
        return {
            "algorithm": self.algorithm,
            "code": self.code,
            "side": self.side,
            "status": self.status,
            "dryRun": self.dry_run,
            "totalQuantity": self.total_quantity,
            "submittedQuantity": self.submitted_quantity,
            "unfilledQuantity": self.unfilled_quantity,
            "startedAt": self.started_at.isoformat() if self.started_at else None,
            "finishedAt": self.finished_at.isoformat() if self.finished_at else None,
            "sliceCount": len(self.slices),
            "notes": list(self.notes),
            "slices": [s.to_dict() for s in self.slices],
        }


class AlgoExecutor:
    """Works an :class:`OrderSlice` schedule, applying guards between slices.

    Instances hold no mutable per-run state — every :meth:`run` call keeps its
    bookkeeping in locals — so a single executor may be reused sequentially. It
    is *not* designed to run two schedules concurrently on the same instance:
    the injected callables would be shared without synchronisation, and the KIS
    account-level rate limit makes parallel parent orders a bad idea anyway.
    """

    def __init__(
        self,
        order_func: Callable[..., Optional[Dict[str, Any]]],
        price_func: Optional[Callable[[str], Optional[float]]] = None,
        sleep_func: Optional[Callable[[float], None]] = None,
        monotonic_func: Optional[Callable[[], float]] = None,
        now_func: Optional[Callable[[], datetime]] = None,
    ) -> None:
        """Wire up the executor.

        Args:
            order_func: Called as ``order_func(code=..., quantity=..., side=...)``
                plus any extra keyword arguments passed to :meth:`run` via
                ``order_kwargs``. Should return the raw KIS response dict, or
                ``None`` on transport failure. May attach a :data:`NOTE_KEY`
                entry to the response to have a note appear on the slice.
            price_func: Called as ``price_func(code)`` to fetch the current
                price for the limit guard. Required only when ``limit_price``
                is used.
            sleep_func: Blocking sleep, injectable for tests. Defaults to
                :func:`time.sleep`.
            monotonic_func: Monotonic clock source, injectable for tests.
                Defaults to :func:`time.monotonic`.
            now_func: Wall-clock source used for reporting timestamps. Defaults
                to :meth:`datetime.datetime.now`.
        """
        self._order = order_func
        self._price = price_func
        # Resolved here rather than as default arguments: a default binds the
        # function object at class-definition time, which would make the clock
        # unpatchable from tests that monkeypatch the ``time`` module.
        self._sleep = sleep_func or time.sleep
        self._monotonic = monotonic_func or time.monotonic
        self._now = now_func or datetime.now

    def run(
        self,
        schedule: Sequence[OrderSlice],
        code: str,
        side: str,
        algorithm: str = "twap",
        limit_price: Optional[float] = None,
        on_price_breach: str = "skip",
        max_consecutive_failures: int = 3,
        dry_run: bool = False,
        session_guard: Optional[Callable[[datetime], bool]] = None,
        progress: Optional[Callable[[SliceExecution], None]] = None,
        order_kwargs: Optional[Dict[str, Any]] = None,
    ) -> AlgoExecutionResult:
        """Execute ``schedule``, waiting between slices and applying guards.

        Args:
            schedule: Child orders in chronological order.
            code: Ticker passed through to ``order_func``.
            side: ``"buy"`` or ``"sell"``. Drives the direction of the limit
                guard comparison.
            algorithm: Label recorded on the result (``"twap"`` / ``"vwap"``).
            limit_price: Worst acceptable price. Buy orders are guarded when
                the market trades *above* it, sell orders when it trades
                *below*. Requires ``price_func``.
            on_price_breach: ``"skip"`` leaves the breaching slice unworked and
                continues; ``"abort"`` stops the whole parent order.
            max_consecutive_failures: Consecutive rejected slices tolerated
                before aborting. Must be >= 1.
            dry_run: Evaluate guards and timing but never call ``order_func``.
            session_guard: Called with each slice's submission time; returning
                ``False`` skips that slice as outside tradable hours.
            progress: Invoked with each :class:`SliceExecution` as it completes.
            order_kwargs: Extra keyword arguments forwarded to ``order_func``
                (order division, exchange, price, ...).

        Returns:
            The aggregate result. Guard rejections and API failures are recorded
            per slice rather than raised, so the caller always learns how much
            of the parent order was worked.

        Raises:
            ValueError: If the schedule is empty, ``side`` is not buy/sell,
                ``on_price_breach`` is unknown, ``max_consecutive_failures`` is
                below 1, or ``limit_price`` is set without a ``price_func``.
        """
        side_norm = side.lower()
        if side_norm not in ("buy", "sell"):
            raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")
        if not schedule:
            raise ValueError("schedule must not be empty")
        if on_price_breach not in ("skip", "abort"):
            raise ValueError(
                f"on_price_breach must be 'skip' or 'abort', got {on_price_breach!r}"
            )
        if max_consecutive_failures < 1:
            raise ValueError(
                f"max_consecutive_failures must be >= 1, got {max_consecutive_failures}"
            )
        if limit_price is not None and self._price is None:
            # Refusing here rather than ignoring the guard: a limit silently
            # dropped on a live order is exactly the failure worth preventing.
            raise ValueError("limit_price requires a price_func")

        order_kwargs = dict(order_kwargs or {})
        total_quantity = sum(s.quantity for s in schedule)
        result = AlgoExecutionResult(
            algorithm=algorithm,
            code=code,
            side=side_norm,
            total_quantity=total_quantity,
            started_at=self._now(),
            dry_run=dry_run,
        )

        # Anchor the schedule once. Every wait is measured as an offset from
        # this pair, so latency in one slice does not push out the next.
        anchor_wall = result.started_at or self._now()
        anchor_mono = self._monotonic()
        consecutive_failures = 0

        for position, slice_ in enumerate(schedule):
            try:
                self._wait_until(slice_.scheduled_at, anchor_wall, anchor_mono)
            except KeyboardInterrupt:
                self._cancel_remaining(
                    result,
                    schedule[position:],
                    "실행 중단 (Ctrl+C)",
                    REASON_INTERRUPTED,
                )
                result.status = "cancelled"
                result.finished_at = self._now()
                return result

            try:
                execution = self._execute_slice(
                    slice_=slice_,
                    code=code,
                    side=side_norm,
                    limit_price=limit_price,
                    dry_run=dry_run,
                    session_guard=session_guard,
                    order_kwargs=order_kwargs,
                )
            except KeyboardInterrupt:
                self._cancel_remaining(
                    result,
                    schedule[position:],
                    "실행 중단 (Ctrl+C)",
                    REASON_INTERRUPTED,
                )
                result.status = "cancelled"
                result.finished_at = self._now()
                return result

            result.slices.append(execution)
            if progress:
                progress(execution)

            if execution.status == SLICE_FAILED:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    result.notes.append(
                        f"연속 {consecutive_failures}회 주문 실패로 중단했습니다"
                    )
                    self._cancel_remaining(
                        result,
                        schedule[position + 1 :],
                        "선행 슬라이스 실패로 미실행",
                        REASON_UPSTREAM_ABORT,
                    )
                    result.status = "aborted"
                    result.finished_at = self._now()
                    return result
            else:
                consecutive_failures = 0

            if (
                on_price_breach == "abort"
                and execution.status == SLICE_SKIPPED
                and execution.reason == REASON_PRICE_LIMIT
            ):
                result.notes.append("지정가 이탈로 중단했습니다")
                self._cancel_remaining(
                    result,
                    schedule[position + 1 :],
                    "지정가 이탈로 미실행",
                    REASON_UPSTREAM_ABORT,
                )
                result.status = "aborted"
                result.finished_at = self._now()
                return result

        worked = {SLICE_FILLED, SLICE_SIMULATED}
        result.status = (
            "completed" if all(s.status in worked for s in result.slices) else "partial"
        )
        result.finished_at = self._now()
        return result

    def _wait_until(
        self, target: datetime, anchor_wall: datetime, anchor_mono: float
    ) -> None:
        """Block until ``target``, measured on the monotonic clock.

        Waiting is chunked so an interrupt during a long gap is noticed quickly.
        A target already in the past returns immediately instead of sleeping a
        negative amount.
        """
        offset = (target - anchor_wall).total_seconds()
        while True:
            remaining = offset - (self._monotonic() - anchor_mono)
            if remaining <= 0:
                return
            self._sleep(min(remaining, _SLEEP_CHUNK_SECONDS))

    def _execute_slice(
        self,
        slice_: OrderSlice,
        code: str,
        side: str,
        limit_price: Optional[float],
        dry_run: bool,
        session_guard: Optional[Callable[[datetime], bool]],
        order_kwargs: Dict[str, Any],
    ) -> SliceExecution:
        """Apply the guards to one slice and submit it if they all pass."""
        evaluated_at = self._now()
        # Guard rejections never reach the exchange, so they carry no
        # submitted_at; only attempted and simulated slices do.
        base = {
            "index": slice_.index,
            "scheduled_at": slice_.scheduled_at,
            "quantity": slice_.quantity,
        }

        if session_guard is not None and not session_guard(evaluated_at):
            return SliceExecution(
                status=SLICE_SKIPPED,
                reason=REASON_SESSION,
                message="거래 가능 시간이 아닙니다",
                **base,
            )

        reference_price: Optional[float] = None
        if limit_price is not None:
            reference_price = self._current_price(code)
            if reference_price is None:
                return SliceExecution(
                    status=SLICE_SKIPPED,
                    reason=REASON_PRICE_UNAVAILABLE,
                    message="지정가 확인용 현재가 조회 실패",
                    **base,
                )
            breached = (
                reference_price > limit_price
                if side == "buy"
                else reference_price < limit_price
            )
            if breached:
                direction = "초과" if side == "buy" else "미만"
                return SliceExecution(
                    status=SLICE_SKIPPED,
                    reason=REASON_PRICE_LIMIT,
                    reference_price=reference_price,
                    message=(
                        f"지정가 {direction}: 현재가 {reference_price:,.0f} "
                        f"vs 지정가 {limit_price:,.0f}"
                    ),
                    **base,
                )

        if dry_run:
            return SliceExecution(
                status=SLICE_SIMULATED,
                reference_price=reference_price,
                submitted_at=evaluated_at,
                message="dry-run (주문 미전송)",
                **base,
            )

        try:
            response = self._order(
                code=code, quantity=slice_.quantity, side=side, **order_kwargs
            )
        except KeyboardInterrupt:
            raise
        except Exception as e:  # noqa: BLE001 - one bad slice must not kill the run
            logger.warning("슬라이스 %d 주문 예외: %s", slice_.index, e)
            return SliceExecution(
                status=SLICE_FAILED,
                reason=REASON_ORDER_REJECTED,
                reference_price=reference_price,
                submitted_at=evaluated_at,
                message=f"{type(e).__name__}: {e}",
                **base,
            )

        if not response:
            return SliceExecution(
                status=SLICE_FAILED,
                reason=REASON_ORDER_REJECTED,
                reference_price=reference_price,
                submitted_at=evaluated_at,
                message="주문 응답 없음",
                **base,
            )
        if response.get("rt_cd") != "0":
            rejected = response.get("msg1") or "주문 거부"
            note = response.get(NOTE_KEY)
            return SliceExecution(
                status=SLICE_FAILED,
                reason=REASON_ORDER_REJECTED,
                reference_price=reference_price,
                submitted_at=evaluated_at,
                message=f"{rejected} [{note}]" if note else rejected,
                **base,
            )

        output = response.get("output") or {}
        message = response.get("msg1") or ""
        note = response.get(NOTE_KEY)
        if note:
            message = f"{message} [{note}]" if message else str(note)
        return SliceExecution(
            status=SLICE_FILLED,
            reference_price=reference_price,
            submitted_at=evaluated_at,
            order_no=str(output.get("ODNO") or output.get("odno") or ""),
            message=message,
            **base,
        )

    def _current_price(self, code: str) -> Optional[float]:
        """Fetch the current price for the limit guard, or ``None`` on failure."""
        if self._price is None:
            return None
        try:
            price = self._price(code)
        except KeyboardInterrupt:
            raise
        except Exception as e:  # noqa: BLE001 - guard failure must not crash the run
            logger.warning("현재가 조회 실패 (%s): %s", code, e)
            return None
        if price is None or price <= 0:
            return None
        return float(price)

    @staticmethod
    def _cancel_remaining(
        result: AlgoExecutionResult,
        remaining: Sequence[OrderSlice],
        message: str,
        reason: str,
    ) -> None:
        """Record the slices that will never be worked."""
        for slice_ in remaining:
            result.slices.append(
                SliceExecution(
                    index=slice_.index,
                    scheduled_at=slice_.scheduled_at,
                    quantity=slice_.quantity,
                    status=SLICE_CANCELLED,
                    reason=reason,
                    message=message,
                )
            )
