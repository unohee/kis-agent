"""High-level TWAP/VWAP entry points wiring an Agent to the execution loop.

These helpers are what :class:`~kis_agent.core.agent.Agent` and the ``kis order
twap`` / ``kis order vwap`` CLI commands call. They own the boring glue —
turning an agent into order/price callables, sourcing a volume profile, picking
a start time — while the schedule and executor modules stay independently
testable.
"""

import logging
from datetime import datetime, timedelta
from datetime import time as dt_time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence

from .executor import NOTE_KEY, AlgoExecutionResult, AlgoExecutor, SliceExecution
from .journal import ExecutionJournal, IncompleteExecutionError, find_incomplete_runs
from .schedule import build_twap_schedule, build_vwap_schedule
from .volume_profile import VolumeProfile, fetch_volume_profile

logger = logging.getLogger(__name__)

__all__ = [
    "KRX_SESSION_OPEN",
    "KRX_SESSION_CLOSE",
    "FUNDING_CASH",
    "FUNDING_CREDIT",
    "DEFAULT_CREDIT_TYPE_BUY",
    "DEFAULT_CREDIT_TYPE_SELL",
    "krx_regular_session",
    "run_twap",
    "run_vwap",
]

KRX_SESSION_OPEN = dt_time(9, 0)
KRX_SESSION_CLOSE = dt_time(15, 30)


def krx_regular_session(moment: datetime) -> bool:
    """Report whether ``moment`` falls inside the KRX regular session.

    The window is half-open: 09:00:00 counts as open, 15:30:00 does not, since
    that instant is the close rather than a tradable moment.

    Weekends are excluded by calendar arithmetic. Public holidays are *not*
    known here. The CLI queries the KIS holiday endpoint when it builds an
    agent, but that only prints a notice — it does not block execution — so on
    a holiday this guard lets slices through and the exchange rejects them.

    Args:
        moment: Wall-clock instant to test.

    Returns:
        True when the regular session (Mon-Fri, 09:00 inclusive to 15:30
        exclusive) is open.
    """
    if moment.weekday() >= 5:
        return False
    return KRX_SESSION_OPEN <= moment.time() < KRX_SESSION_CLOSE


FUNDING_CASH = "cash"
FUNDING_CREDIT = "credit"
_FUNDING_CHOICES = (FUNDING_CASH, FUNDING_CREDIT)

# KIS credit-type codes differ by direction: a buy opens a margin position,
# a sell closes one.
DEFAULT_CREDIT_TYPE_BUY = "21"  # 신용융자
DEFAULT_CREDIT_TYPE_SELL = "11"  # 융자상환매도


def _accepted(response: Optional[Dict[str, Any]]) -> bool:
    """True when KIS acknowledged the order."""
    return bool(response) and response.get("rt_cd") == "0"


def _make_order_func(agent: Any) -> Callable[..., Optional[Dict[str, Any]]]:
    """Bind an agent into the ``order_func`` contract the executor expects.

    Routing (division, price, exchange, funding source) arrives per call through
    the executor's ``order_kwargs`` rather than being baked in at construction
    time, so an executor injected by the caller still honours the routing
    arguments passed to :func:`run_twap` / :func:`run_vwap`.

    When a credit order is rejected and ``credit_fallback_to_cash`` is set, the
    cash order that replaces it is annotated under :data:`NOTE_KEY` so the
    change of funding source shows up in the slice report. Switching how a
    position is financed without saying so would be the worst kind of silent
    success.
    """

    def _order(
        code: str,
        quantity: int,
        side: str,
        order_type: str = "03",
        price: int = 0,
        exchange: str = "KRX",
        funding: str = FUNDING_CASH,
        credit_type: Optional[str] = None,
        loan_dt: str = "",
        credit_fallback_to_cash: bool = False,
        **_: Any,
    ):
        is_buy = side.lower() == "buy"

        def _cash():
            return agent.account_api.order_cash(
                pdno=code,
                qty=quantity,
                price=price,
                buy_sell=side.upper(),
                order_type=order_type,
                exchange=exchange,
            )

        if funding != FUNDING_CREDIT:
            return _cash()

        if is_buy:
            response = agent.account_api.order_credit_buy(
                pdno=code,
                qty=quantity,
                price=price,
                order_type=order_type,
                credit_type=credit_type or DEFAULT_CREDIT_TYPE_BUY,
                exchange=exchange,
                loan_dt=loan_dt,
            )
        else:
            # 신용매도는 상환 주문이라 거래소 지정을 받지 않는다 (KIS 스펙).
            response = agent.account_api.order_credit_sell(
                pdno=code,
                qty=quantity,
                price=price,
                order_type=order_type,
                credit_type=credit_type or DEFAULT_CREDIT_TYPE_SELL,
            )

        if _accepted(response) or not credit_fallback_to_cash:
            return response

        rejection = (response or {}).get("msg1") or "응답 없음"
        logger.warning("신용 주문 거부 (%s): %s — 현금 주문으로 폴백", code, rejection)
        fallback = _cash()
        if isinstance(fallback, dict):
            fallback = dict(fallback)
            fallback[NOTE_KEY] = f"신용 거부({rejection}) → 현금 폴백"
        return fallback

    return _order


def _make_price_func(agent: Any) -> Callable[[str], Optional[float]]:
    """Bind an agent into the ``price_func`` contract the executor expects."""

    def _price(code: str) -> Optional[float]:
        data = agent.stock_api.get_stock_price(code)
        output = (data or {}).get("output") or {}
        raw = str(output.get("stck_prpr") or "").replace(",", "").strip()
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    return _price


def _build_executor(agent: Any) -> AlgoExecutor:
    return AlgoExecutor(
        order_func=_make_order_func(agent),
        price_func=_make_price_func(agent),
    )


def _routing_kwargs(
    order_type: str,
    price: int,
    exchange: str,
    funding: str,
    credit_type: Optional[str],
    loan_dt: str,
    credit_fallback_to_cash: bool,
) -> Dict[str, Any]:
    """Per-slice routing forwarded to the order callable."""
    return {
        "order_type": order_type,
        "price": price,
        "exchange": exchange,
        "funding": funding,
        "credit_type": credit_type,
        "loan_dt": loan_dt,
        "credit_fallback_to_cash": credit_fallback_to_cash,
    }


def _validate_funding(funding: str) -> str:
    """Normalise and check the funding source."""
    normalised = (funding or FUNDING_CASH).lower()
    if normalised not in _FUNDING_CHOICES:
        raise ValueError(f"funding must be one of {_FUNDING_CHOICES}, got {funding!r}")
    return normalised


def _resolve_start(start: Optional[datetime], now: Optional[datetime]) -> datetime:
    """Pick the schedule's first submission time.

    A start in the past fires immediately rather than being rewritten to ``now``,
    which keeps the remaining slice times anchored to the operator's intent.
    """
    return start or now or datetime.now()


def _guard_incomplete_runs(
    code: str, journal_dir: Optional[Path], enabled: bool, dry_run: bool
) -> None:
    """Refuse to start when a previous run for ``code`` never closed.

    Skipped for dry runs — they never reached the exchange, so there is nothing
    to reconcile.

    Raises:
        IncompleteExecutionError: If an unclosed journal exists for ``code``.
    """
    if not enabled or dry_run:
        return
    runs = find_incomplete_runs(code, base_dir=journal_dir)
    if runs:
        raise IncompleteExecutionError(runs)


def _open_journal(
    code: str,
    side: str,
    algorithm: str,
    quantity: int,
    slices: Sequence[Any],
    plan: Dict[str, Any],
    journal_dir: Optional[Path],
    enabled: bool,
) -> Optional[ExecutionJournal]:
    """Open a journal and write the plan before the first order goes out.

    Returns ``None`` when journaling is disabled or the journal cannot be
    opened. A missing journal degrades observability, not correctness, so it
    must never stop an execution — but the caller surfaces the reason.
    """
    if not enabled:
        return None
    try:
        journal = ExecutionJournal.create(code, side, base_dir=journal_dir)
    except OSError as e:  # noqa: BLE001 - degrade, never block the order
        logger.warning("집행 원장을 열지 못했습니다: %s", e)
        return None

    journal.record_start(
        {
            "algorithm": algorithm,
            "code": code,
            "side": side,
            "totalQuantity": quantity,
            "sliceCount": len(slices),
            "schedule": [
                {
                    "index": s.index,
                    "scheduledAt": s.scheduled_at.isoformat(),
                    "quantity": s.quantity,
                }
                for s in slices
            ],
            **plan,
        }
    )
    return journal


def _close_journal(
    journal: Optional[ExecutionJournal], result: AlgoExecutionResult
) -> None:
    """Stamp the result onto the run and close the journal."""
    if journal is None:
        return
    result.run_id = journal.run_id
    result.journal_path = str(journal.path)
    journal.record_end(result.to_dict())


def run_twap(
    agent: Any,
    code: str,
    side: str,
    quantity: int,
    duration_minutes: int = 30,
    slices: int = 6,
    order_type: str = "03",
    price: int = 0,
    exchange: str = "KRX",
    funding: str = FUNDING_CASH,
    credit_type: Optional[str] = None,
    loan_dt: str = "",
    credit_fallback_to_cash: bool = False,
    limit_price: Optional[float] = None,
    on_price_breach: str = "skip",
    max_consecutive_failures: int = 3,
    dry_run: bool = False,
    restrict_to_session: bool = True,
    start: Optional[datetime] = None,
    progress: Optional[Callable[[SliceExecution], None]] = None,
    executor: Optional[AlgoExecutor] = None,
    journal_dir: Optional[Path] = None,
    journal_enabled: bool = True,
    check_incomplete: bool = True,
) -> AlgoExecutionResult:
    """Work a parent order evenly across ``duration_minutes`` (TWAP).

    Args:
        agent: Agent exposing ``account_api.order_cash`` and
            ``stock_api.get_stock_price``.
        code: Six-digit domestic ticker.
        side: ``"buy"`` or ``"sell"``.
        quantity: Parent order size in shares. Must be > 0.
        duration_minutes: Wall-clock window to work the order over. Must be > 0.
        slices: Requested child-order count, capped at ``quantity``.
        order_type: KIS order division. Defaults to ``"03"`` (최유리지정가),
            which fills like a market order without the slippage of ``"01"``.
        price: Limit price sent with each child order. Ignored by the exchange
            for market-style divisions, so it defaults to 0.
        exchange: ``KRX``, ``NXT`` or ``SOR``. Credit sells ignore it, since
            KIS routes repayment orders itself.
        funding: ``"cash"`` for a cash order or ``"credit"`` for a margin
            order.
        credit_type: KIS credit-type code. Defaults to ``"21"`` (신용융자) on
            buys and ``"11"`` (융자상환매도) on sells.
        loan_dt: 대출일자 (``YYYYMMDD``), only meaningful for 자기융자 buys.
        credit_fallback_to_cash: Retry a rejected credit order as a cash order.
            Off by default — silently changing how a position is financed is
            not something to do without being asked. The fallback is recorded
            in the slice message when it happens.
        limit_price: Worst acceptable market price; slices outside it are
            skipped (or abort the run, see ``on_price_breach``).
        on_price_breach: ``"skip"`` or ``"abort"``.
        max_consecutive_failures: Rejected slices tolerated before aborting.
        dry_run: Build and pace the schedule without sending any order.
        restrict_to_session: Skip slices that land outside the KRX regular
            session.
        start: First submission time. Defaults to now.
        progress: Called with each slice result as it completes.
        executor: Pre-built executor, mainly for tests. Routing arguments are
            still forwarded to its order callable.
        journal_dir: Where to write the execution journal. Defaults to
            ``~/.kis-agent/executions`` (override with
            ``KIS_EXECUTION_JOURNAL_DIR``).
        journal_enabled: Write a durable record of every child order. Leave it
            on unless you have another audit trail — without it, a process that
            dies mid-run takes its order numbers with it.
        check_incomplete: Refuse to start when a previous run for this ticker
            died without closing its journal. Turn it off only after you have
            reconciled the orders that run left on the exchange.

    Returns:
        The aggregate execution result.

    Raises:
        ValueError: If ``quantity``, ``slices`` or ``duration_minutes`` is not
            positive, or a guard argument is invalid.
    """
    if quantity <= 0:
        raise ValueError(f"quantity must be positive, got {quantity}")
    if duration_minutes <= 0:
        raise ValueError(f"duration_minutes must be positive, got {duration_minutes}")
    # Checked here as well as downstream so the error names the argument the
    # caller actually passed, matching run_vwap.
    if slices <= 0:
        raise ValueError(f"slices must be positive, got {slices}")
    funding = _validate_funding(funding)
    _guard_incomplete_runs(code, journal_dir, check_incomplete, dry_run)

    runner = executor or _build_executor(agent)
    begin = _resolve_start(start, None)
    schedule = build_twap_schedule(
        total_quantity=quantity,
        slices=slices,
        start=begin,
        duration=timedelta(minutes=duration_minutes),
    )

    plan = {
        "orderType": order_type,
        "price": price,
        "exchange": exchange,
        "funding": funding,
        "creditType": credit_type,
        "creditFallbackToCash": credit_fallback_to_cash,
        "limitPrice": limit_price,
        "onPriceBreach": on_price_breach,
        "dryRun": dry_run,
        "restrictToSession": restrict_to_session,
        "durationMinutes": duration_minutes,
    }
    journal = _open_journal(
        code, side, "twap", quantity, schedule, plan, journal_dir, journal_enabled
    )

    result = runner.run(
        schedule=schedule,
        code=code,
        side=side,
        algorithm="twap",
        limit_price=limit_price,
        on_price_breach=on_price_breach,
        max_consecutive_failures=max_consecutive_failures,
        dry_run=dry_run,
        session_guard=krx_regular_session if restrict_to_session else None,
        progress=progress,
        order_kwargs=_routing_kwargs(
            order_type,
            price,
            exchange,
            funding,
            credit_type,
            loan_dt,
            credit_fallback_to_cash,
        ),
        journal=journal,
    )
    _close_journal(journal, result)
    return result


def run_vwap(
    agent: Any,
    code: str,
    side: str,
    quantity: int,
    duration_minutes: int = 60,
    slices: int = 6,
    profile_days: int = 5,
    order_type: str = "03",
    price: int = 0,
    exchange: str = "KRX",
    funding: str = FUNDING_CASH,
    credit_type: Optional[str] = None,
    loan_dt: str = "",
    credit_fallback_to_cash: bool = False,
    limit_price: Optional[float] = None,
    on_price_breach: str = "skip",
    max_consecutive_failures: int = 3,
    dry_run: bool = False,
    restrict_to_session: bool = True,
    start: Optional[datetime] = None,
    progress: Optional[Callable[[SliceExecution], None]] = None,
    executor: Optional[AlgoExecutor] = None,
    journal_dir: Optional[Path] = None,
    journal_enabled: bool = True,
    check_incomplete: bool = True,
    profile: Optional[VolumeProfile] = None,
) -> AlgoExecutionResult:
    """Work a parent order along the historical intraday volume curve (VWAP).

    When no usable profile can be built the run degrades to an even TWAP split
    and records why in ``result.notes`` — a silent downgrade would leave the
    operator believing the order tracked volume when it did not.

    Args:
        agent: Agent exposing ``account_api.order_cash``,
            ``stock_api.get_stock_price`` and
            ``stock_api.get_daily_minute_price``.
        code: Six-digit domestic ticker.
        side: ``"buy"`` or ``"sell"``.
        quantity: Parent order size in shares. Must be > 0.
        duration_minutes: Wall-clock window to work the order over. Must be > 0.
        slices: Number of volume buckets, capped in effect by ``quantity``.
        profile_days: Completed sessions to average for the volume profile.
        order_type: KIS order division. Defaults to ``"03"`` (최유리지정가).
        price: Limit price sent with each child order.
        exchange: ``KRX``, ``NXT`` or ``SOR``. Credit sells ignore it, since
            KIS routes repayment orders itself.
        funding: ``"cash"`` for a cash order or ``"credit"`` for a margin
            order.
        credit_type: KIS credit-type code. Defaults to ``"21"`` (신용융자) on
            buys and ``"11"`` (융자상환매도) on sells.
        loan_dt: 대출일자 (``YYYYMMDD``), only meaningful for 자기융자 buys.
        credit_fallback_to_cash: Retry a rejected credit order as a cash order.
            Off by default — silently changing how a position is financed is
            not something to do without being asked. The fallback is recorded
            in the slice message when it happens.
        limit_price: Worst acceptable market price.
        on_price_breach: ``"skip"`` or ``"abort"``.
        max_consecutive_failures: Rejected slices tolerated before aborting.
        dry_run: Build and pace the schedule without sending any order.
        restrict_to_session: Skip slices outside the KRX regular session.
        start: First submission time. Defaults to now.
        progress: Called with each slice result as it completes.
        executor: Pre-built executor, mainly for tests. Routing arguments are
            still forwarded to its order callable.
        journal_dir: Where to write the execution journal. Defaults to
            ``~/.kis-agent/executions`` (override with
            ``KIS_EXECUTION_JOURNAL_DIR``).
        journal_enabled: Write a durable record of every child order. Leave it
            on unless you have another audit trail — without it, a process that
            dies mid-run takes its order numbers with it.
        check_incomplete: Refuse to start when a previous run for this ticker
            died without closing its journal. Turn it off only after you have
            reconciled the orders that run left on the exchange.
        profile: Pre-built volume profile, mainly for tests. When omitted the
            profile is fetched from the agent.

    Returns:
        The aggregate execution result, with a note when the volume profile was
        unavailable and an even split was used instead.

    Raises:
        ValueError: If ``quantity``, ``slices`` or ``duration_minutes`` is not
            positive, or a guard argument is invalid.
    """
    if quantity <= 0:
        raise ValueError(f"quantity must be positive, got {quantity}")
    if duration_minutes <= 0:
        raise ValueError(f"duration_minutes must be positive, got {duration_minutes}")
    if slices <= 0:
        raise ValueError(f"slices must be positive, got {slices}")
    funding = _validate_funding(funding)
    _guard_incomplete_runs(code, journal_dir, check_incomplete, dry_run)

    runner = executor or _build_executor(agent)
    begin = _resolve_start(start, None)
    duration = timedelta(minutes=duration_minutes)

    if profile is None:
        profile = fetch_volume_profile(agent, code=code, days=profile_days)

    weights = profile.bucket_weights(begin, duration, slices)
    fallback_note: Optional[str] = None
    if weights is None:
        fallback_note = (
            "거래량 프로파일을 사용할 수 없어 균등 분할(TWAP)로 실행합니다"
            + (f" — {profile.fallback_reason}" if profile.fallback_reason else "")
        )
        logger.warning(fallback_note)

    schedule = build_vwap_schedule(
        total_quantity=quantity,
        slices=slices,
        start=begin,
        duration=duration,
        weights=weights,
    )

    plan = {
        "orderType": order_type,
        "price": price,
        "exchange": exchange,
        "funding": funding,
        "creditType": credit_type,
        "creditFallbackToCash": credit_fallback_to_cash,
        "limitPrice": limit_price,
        "onPriceBreach": on_price_breach,
        "dryRun": dry_run,
        "restrictToSession": restrict_to_session,
        "durationMinutes": duration_minutes,
        "profileDays": profile_days,
    }
    journal = _open_journal(
        code, side, "vwap", quantity, schedule, plan, journal_dir, journal_enabled
    )

    result = runner.run(
        schedule=schedule,
        code=code,
        side=side,
        algorithm="vwap",
        limit_price=limit_price,
        on_price_breach=on_price_breach,
        max_consecutive_failures=max_consecutive_failures,
        dry_run=dry_run,
        session_guard=krx_regular_session if restrict_to_session else None,
        progress=progress,
        order_kwargs=_routing_kwargs(
            order_type,
            price,
            exchange,
            funding,
            credit_type,
            loan_dt,
            credit_fallback_to_cash,
        ),
        journal=journal,
    )

    if fallback_note:
        result.notes.insert(0, fallback_note)
    elif profile.source_dates:
        result.notes.append(
            f"거래량 프로파일: {len(profile.source_dates)}개 영업일 평균 "
            f"({profile.source_dates[0]}~{profile.source_dates[-1]})"
        )
    # notes가 확정된 뒤에 닫아야 원장의 end 레코드에 함께 남는다.
    _close_journal(journal, result)
    return result
