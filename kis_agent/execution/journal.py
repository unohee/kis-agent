"""Durable, append-only record of what an algorithmic order actually sent.

A sliced parent order works for 30 to 120 minutes. In that window the process
can die in ways it never gets to handle — SIGKILL, a closed laptop lid, an OOM,
an agent harness timeout. Everything the run knew then lives only in memory and
in a stdout payload that is written once, at the very end.

That is the wrong shape for money. This module writes each child order to disk
the instant the exchange acknowledges it, flushed and fsynced, so the answer to
"what went out before it died?" is always a file rather than a guess. The same
file makes the second question answerable too: a run that has no ``end`` record
crashed, and re-running the same parent order blindly would double the position.

The journal is deliberately dumb — newline-delimited JSON, no index, no schema
migration. It has to survive the process that writes it.
"""

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

__all__ = [
    "ExecutionJournal",
    "IncompleteRun",
    "IncompleteExecutionError",
    "default_journal_dir",
    "make_run_id",
    "read_journal",
    "find_incomplete_runs",
    "EVENT_START",
    "EVENT_SLICE",
    "EVENT_END",
]

EVENT_START = "start"
EVENT_SLICE = "slice"
EVENT_END = "end"

_ENV_JOURNAL_DIR = "KIS_EXECUTION_JOURNAL_DIR"


def default_journal_dir() -> Path:
    """Where journals live unless the caller says otherwise.

    Honours ``KIS_EXECUTION_JOURNAL_DIR`` so a deployment can put the record on
    a volume that outlives the container running the order.

    Returns:
        Base directory for journals. Not created here.
    """
    override = os.environ.get(_ENV_JOURNAL_DIR)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".kis-agent" / "executions"


def make_run_id(code: str, side: str, now: Optional[datetime] = None) -> str:
    """Build a human-scannable, collision-resistant run identifier.

    The timestamp prefix makes a directory listing read chronologically; the
    random suffix keeps two runs started in the same second apart.

    Args:
        code: Ticker being worked.
        side: ``buy`` or ``sell``.
        now: Clock override for tests.

    Returns:
        Something like ``20260821-133000-005930-buy-3f9a2c``.
    """
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{code}-{side.lower()}-{uuid.uuid4().hex[:6]}"


class IncompleteExecutionError(RuntimeError):
    """Raised when a previous run for the same ticker never closed its journal.

    An unclosed journal means orders may already be sitting on the exchange from
    a process that died. Working the same parent order again without looking at
    them is how a position silently doubles, so this stops the caller rather
    than warning them.

    Attributes:
        runs: The incomplete runs found, each carrying its order numbers.
    """

    def __init__(self, runs: List["IncompleteRun"]) -> None:
        self.runs = runs
        summaries = "; ".join(r.describe() for r in runs)
        super().__init__(
            f"완료되지 않은 집행 기록 {len(runs)}건: {summaries}. "
            "이미 나간 주문을 확인한 뒤 진행하세요."
        )


@dataclass
class IncompleteRun:
    """A journal that was opened but never closed — the run died mid-flight."""

    run_id: str
    path: Path
    code: str
    side: str
    total_quantity: int
    submitted_quantity: int
    order_numbers: List[str] = field(default_factory=list)
    started_at: Optional[str] = None

    def describe(self) -> str:
        """One-line summary for an operator staring at a warning."""
        orders = ", ".join(self.order_numbers) if self.order_numbers else "없음"
        return (
            f"{self.run_id}: {self.code} {self.side} "
            f"{self.submitted_quantity}/{self.total_quantity}주 접수 "
            f"(주문번호 {orders})"
        )


class ExecutionJournal:
    """Append-only JSONL record of one parent order.

    Every :meth:`record` call flushes and fsyncs before returning. That costs a
    syscall per child order — irrelevant next to an HTTP round trip, and it is
    the whole reason the file is trustworthy after a SIGKILL.
    """

    def __init__(self, path: Path, run_id: str) -> None:
        """Bind a journal to a path. Use :meth:`create` to open a fresh one."""
        self.path = path
        self.run_id = run_id
        self._closed = False

    @classmethod
    def create(
        cls,
        code: str,
        side: str,
        base_dir: Optional[Path] = None,
        now: Optional[datetime] = None,
        run_id: Optional[str] = None,
    ) -> "ExecutionJournal":
        """Open a new journal under ``base_dir/YYYYMMDD/``.

        Args:
            code: Ticker being worked.
            side: ``buy`` or ``sell``.
            base_dir: Journal root. Defaults to :func:`default_journal_dir`.
            now: Clock override for tests.
            run_id: Explicit run id, mainly for tests.

        Returns:
            An open journal. The directory is created if needed.

        Raises:
            OSError: If the directory cannot be created.
        """
        moment = now or datetime.now()
        rid = run_id or make_run_id(code, side, moment)
        directory = (base_dir or default_journal_dir()) / moment.strftime("%Y%m%d")
        directory.mkdir(parents=True, exist_ok=True)
        return cls(path=directory / f"{rid}.jsonl", run_id=rid)

    def record(self, event: str, payload: Dict[str, Any]) -> None:
        """Append one event and force it to disk.

        Journal failures never abort an execution — losing the record is bad,
        but aborting a half-worked parent order because a disk is full is worse.
        The failure is logged at warning level instead.

        Args:
            event: One of ``start`` / ``slice`` / ``end``.
            payload: Event body. Must be JSON-serialisable.
        """
        line = {
            "ts": datetime.now().isoformat(),
            "runId": self.run_id,
            "event": event,
        }
        line.update(payload)
        try:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        except OSError as e:  # noqa: BLE001 - never kill a live order over a log
            logger.warning("집행 원장 기록 실패 (%s): %s", self.path, e)

    def record_start(self, payload: Dict[str, Any]) -> None:
        """Record the execution plan before the first child order goes out."""
        self.record(EVENT_START, payload)

    def record_slice(self, payload: Dict[str, Any]) -> None:
        """Record one child order's outcome, including its order number."""
        self.record(EVENT_SLICE, payload)

    def record_end(self, payload: Dict[str, Any]) -> None:
        """Close the journal. A journal without this event means the run died."""
        self.record(EVENT_END, payload)
        self._closed = True


def read_journal(path: Path) -> List[Dict[str, Any]]:
    """Read a journal back, skipping any line torn by an abrupt kill.

    Args:
        path: Journal file.

    Returns:
        Parsed events in write order. A missing file yields an empty list.
    """
    events: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    # A process killed mid-write leaves a partial final line.
                    # Everything before it is still good.
                    logger.warning("집행 원장의 손상된 줄을 건너뜁니다 (%s)", path)
    except OSError as e:  # noqa: BLE001
        logger.warning("집행 원장을 읽지 못했습니다 (%s): %s", path, e)
    return events


def find_incomplete_runs(
    code: str,
    base_dir: Optional[Path] = None,
    now: Optional[datetime] = None,
    side: Optional[str] = None,
) -> List[IncompleteRun]:
    """Find today's journals for ``code`` that never recorded an ``end``.

    An incomplete journal is the signature of a run that died with orders
    already on the exchange. Starting another parent order for the same ticker
    without looking at it is how a position silently doubles.

    Dry runs are excluded: they never reached the exchange, so an unfinished one
    has nothing to reconcile.

    The search is scoped to today on purpose. A clean stop — normal completion
    or Ctrl+C — closes its journal, so only an unhandled kill leaves one open;
    and KRX day orders do not survive the close, so yesterday's wreckage is not
    a reason to block this morning's order. Bounding it this way also keeps a
    single crash from blocking the ticker forever.

    Args:
        code: Ticker to check.
        base_dir: Journal root. Defaults to :func:`default_journal_dir`.
        now: Clock override for tests.
        side: Restrict to runs in this direction. Pass the side you are about
            to work: a crashed buy must not stand between an operator and the
            sell that unwinds it, and duplication is a same-side hazard anyway.
            ``None`` matches every direction.

    Returns:
        Incomplete runs, oldest first. Empty when the directory is missing.

    Note:
        ``order_numbers`` can undercount. Orders are never resent, so a request
        whose response was lost is recorded as ``failed`` even though the
        exchange may have accepted it. Treat the list as a starting point for
        reconciliation, not a complete inventory — ``kis order list`` and
        ``kis trades`` are authoritative.
    """
    moment = now or datetime.now()
    directory = (base_dir or default_journal_dir()) / moment.strftime("%Y%m%d")
    if not directory.is_dir():
        return []

    incomplete: List[IncompleteRun] = []
    for path in sorted(directory.glob("*.jsonl")):
        events = read_journal(path)
        if not events:
            continue
        if any(e.get("event") == EVENT_END for e in events):
            continue

        start = next((e for e in events if e.get("event") == EVENT_START), {})
        if start.get("code") != code:
            continue
        if side is not None and str(start.get("side", "")).lower() != side.lower():
            continue
        if start.get("dryRun"):
            # A dry run never reached the exchange, so an unfinished one leaves
            # nothing to reconcile and must not block the next real order.
            continue

        slices = [e for e in events if e.get("event") == EVENT_SLICE]
        worked = [s for s in slices if s.get("status") in ("filled", "simulated")]
        incomplete.append(
            IncompleteRun(
                run_id=start.get("runId") or path.stem,
                path=path,
                code=start.get("code", code),
                side=start.get("side", ""),
                total_quantity=int(start.get("totalQuantity") or 0),
                submitted_quantity=sum(int(s.get("quantity") or 0) for s in worked),
                order_numbers=[s["orderNo"] for s in worked if s.get("orderNo")],
                started_at=start.get("ts"),
            )
        )
    return incomplete
