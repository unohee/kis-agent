"""Algorithmic order execution — TWAP and VWAP slicing for domestic stocks.

Typical use goes through the agent facade::

    result = agent.twap_order("005930", "buy", quantity=1000, duration_minutes=30)
    print(result.submitted_quantity, result.status)

The building blocks are also importable directly when you need to inspect a
schedule before committing to it, or drive the loop against your own order
callable::

    from kis_agent.execution import build_twap_schedule, AlgoExecutor
"""

from .executor import (
    NOTE_KEY,
    REASON_INTERRUPTED,
    REASON_ORDER_REJECTED,
    REASON_PRICE_LIMIT,
    REASON_PRICE_UNAVAILABLE,
    REASON_SESSION,
    REASON_UPSTREAM_ABORT,
    SLICE_CANCELLED,
    SLICE_FAILED,
    SLICE_ACCEPTED,
    SLICE_FILLED,
    SLICE_SIMULATED,
    SLICE_SKIPPED,
    AlgoExecutionResult,
    AlgoExecutor,
    SliceExecution,
)
from .journal import (
    ExecutionJournal,
    IncompleteExecutionError,
    IncompleteRun,
    find_incomplete_runs,
    read_journal,
)
from .runner import (
    DEFAULT_CREDIT_TYPE_BUY,
    DEFAULT_CREDIT_TYPE_SELL,
    FUNDING_CASH,
    FUNDING_CREDIT,
    KRX_SESSION_CLOSE,
    KRX_SESSION_OPEN,
    krx_regular_session,
    run_twap,
    run_vwap,
)
from .schedule import (
    OrderSlice,
    build_twap_schedule,
    build_vwap_schedule,
    split_quantity,
    split_quantity_weighted,
)
from .volume_profile import VolumeProfile, build_profile_from_bars, fetch_volume_profile

__all__ = [
    # schedule
    "OrderSlice",
    "split_quantity",
    "split_quantity_weighted",
    "build_twap_schedule",
    "build_vwap_schedule",
    # volume profile
    "VolumeProfile",
    "build_profile_from_bars",
    "fetch_volume_profile",
    # executor
    "AlgoExecutor",
    "AlgoExecutionResult",
    "SliceExecution",
    "SLICE_ACCEPTED",
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
    # journal
    "ExecutionJournal",
    "IncompleteExecutionError",
    "IncompleteRun",
    "find_incomplete_runs",
    "read_journal",
    # runner
    "run_twap",
    "run_vwap",
    "krx_regular_session",
    "KRX_SESSION_OPEN",
    "KRX_SESSION_CLOSE",
    "FUNDING_CASH",
    "FUNDING_CREDIT",
    "DEFAULT_CREDIT_TYPE_BUY",
    "DEFAULT_CREDIT_TYPE_SELL",
]
