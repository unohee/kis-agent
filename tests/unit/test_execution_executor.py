"""Unit tests for the sliced-order execution loop.

Every test drives a fake clock, so the suite exercises real pacing logic without
sleeping and without depending on wall-clock behaviour.
"""

from datetime import datetime, timedelta

import pytest

from kis_agent.execution.executor import (
    REASON_INTERRUPTED,
    REASON_ORDER_REJECTED,
    REASON_PRICE_LIMIT,
    REASON_PRICE_UNAVAILABLE,
    REASON_SESSION,
    REASON_UPSTREAM_ABORT,
    SLICE_CANCELLED,
    SLICE_FAILED,
    SLICE_FILLED,
    SLICE_SIMULATED,
    SLICE_SKIPPED,
    AlgoExecutor,
)
from kis_agent.execution.schedule import build_twap_schedule

START = datetime(2026, 8, 21, 10, 0)
OK = {"rt_cd": "0", "msg1": "정상처리", "output": {"ODNO": "0000123456"}}


class FakeClock:
    """Monotonic clock and sleep that advance together, never in real time."""

    def __init__(self, start: datetime = START):
        self.wall = start
        self.mono = 1000.0
        self.slept = []

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.mono += seconds
        self.wall += timedelta(seconds=seconds)

    def monotonic(self) -> float:
        return self.mono

    def now(self) -> datetime:
        return self.wall

    @property
    def total_slept(self) -> float:
        return sum(self.slept)


class RecordingOrder:
    """Order callable that records every submission and replays canned results."""

    def __init__(self, results=None):
        self.calls = []
        self._results = list(results) if results else None

    def __call__(self, code, quantity, side, **kwargs):
        self.calls.append({"code": code, "quantity": quantity, "side": side, **kwargs})
        if self._results is None:
            return OK
        return self._results[min(len(self.calls) - 1, len(self._results) - 1)]


def make_executor(order=None, price=None, clock=None):
    clock = clock or FakeClock()
    return (
        AlgoExecutor(
            order_func=order or RecordingOrder(),
            price_func=price,
            sleep_func=clock.sleep,
            monotonic_func=clock.monotonic,
            now_func=clock.now,
        ),
        clock,
    )


class TestHappyPath:
    def test_every_slice_is_submitted_in_order(self):
        order = RecordingOrder()
        executor, _ = make_executor(order)
        schedule = build_twap_schedule(100, 4, START, timedelta(minutes=20))

        result = executor.run(schedule, code="005930", side="buy")

        assert result.status == "completed"
        assert [c["quantity"] for c in order.calls] == [25, 25, 25, 25]
        assert result.submitted_quantity == 100
        assert result.unfilled_quantity == 0
        assert all(s.status == SLICE_FILLED for s in result.slices)

    def test_order_number_is_captured(self):
        executor, _ = make_executor()
        schedule = build_twap_schedule(10, 1, START, timedelta(minutes=5))
        result = executor.run(schedule, code="005930", side="buy")
        assert result.slices[0].order_no == "0000123456"

    def test_lowercase_odno_key_is_also_accepted(self):
        order = RecordingOrder([{"rt_cd": "0", "output": {"odno": "999"}}])
        executor, _ = make_executor(order)
        schedule = build_twap_schedule(10, 1, START, timedelta(minutes=5))
        result = executor.run(schedule, code="005930", side="buy")
        assert result.slices[0].order_no == "999"

    def test_extra_order_kwargs_are_forwarded(self):
        order = RecordingOrder()
        executor, _ = make_executor(order)
        schedule = build_twap_schedule(10, 1, START, timedelta(minutes=5))
        executor.run(
            schedule, code="005930", side="buy", order_kwargs={"exchange": "NXT"}
        )
        assert order.calls[0]["exchange"] == "NXT"

    def test_progress_callback_sees_each_slice(self):
        seen = []
        executor, _ = make_executor()
        schedule = build_twap_schedule(30, 3, START, timedelta(minutes=15))
        executor.run(schedule, code="005930", side="buy", progress=seen.append)
        assert [s.index for s in seen] == [0, 1, 2]


class TestPacing:
    def test_waits_the_scheduled_gap_between_slices(self):
        executor, clock = make_executor()
        schedule = build_twap_schedule(40, 4, START, timedelta(minutes=20))

        executor.run(schedule, code="005930", side="buy")

        # Three 5-minute gaps after the immediate first slice.
        assert clock.total_slept == pytest.approx(900.0)

    def test_first_slice_fires_immediately_when_start_is_now(self):
        executor, clock = make_executor()
        schedule = build_twap_schedule(10, 1, START, timedelta(minutes=5))
        executor.run(schedule, code="005930", side="buy")
        assert clock.total_slept == 0.0

    def test_past_schedule_never_sleeps_negative(self):
        clock = FakeClock(start=START + timedelta(hours=1))
        executor, _ = make_executor(clock=clock)
        schedule = build_twap_schedule(40, 4, START, timedelta(minutes=20))

        executor.run(schedule, code="005930", side="buy")

        assert clock.slept == []

    def test_order_latency_does_not_accumulate_drift(self):
        """A slow slice must not push every later slice out by the same amount."""
        clock = FakeClock()

        class SlowOrder(RecordingOrder):
            def __call__(self, code, quantity, side, **kwargs):
                clock.sleep(60)  # one minute of API latency
                return super().__call__(code, quantity, side, **kwargs)

        order = SlowOrder()
        executor, _ = make_executor(order=order, clock=clock)
        schedule = build_twap_schedule(40, 4, START, timedelta(minutes=20))

        executor.run(schedule, code="005930", side="buy")

        # Anchored pacing: total elapsed is the schedule span plus the final
        # order's latency, not span + 4x latency.
        elapsed = clock.mono - 1000.0
        assert elapsed == pytest.approx(15 * 60 + 60)


class TestPriceGuard:
    def test_buy_slice_above_limit_is_skipped(self):
        order = RecordingOrder()
        executor, _ = make_executor(order, price=lambda code: 71000.0)
        schedule = build_twap_schedule(20, 2, START, timedelta(minutes=10))

        result = executor.run(
            schedule, code="005930", side="buy", limit_price=70000.0
        )

        assert order.calls == []
        assert result.status == "partial"
        assert all(s.status == SLICE_SKIPPED for s in result.slices)
        assert all(s.reason == REASON_PRICE_LIMIT for s in result.slices)
        assert result.unfilled_quantity == 20

    def test_buy_slice_at_or_below_limit_goes_through(self):
        order = RecordingOrder()
        executor, _ = make_executor(order, price=lambda code: 70000.0)
        schedule = build_twap_schedule(20, 2, START, timedelta(minutes=10))

        result = executor.run(schedule, code="005930", side="buy", limit_price=70000.0)

        assert len(order.calls) == 2
        assert result.status == "completed"

    def test_sell_guard_is_inverted(self):
        order = RecordingOrder()
        executor, _ = make_executor(order, price=lambda code: 69000.0)
        schedule = build_twap_schedule(20, 2, START, timedelta(minutes=10))

        result = executor.run(schedule, code="005930", side="sell", limit_price=70000.0)

        assert order.calls == []
        assert result.slices[0].reason == REASON_PRICE_LIMIT

    def test_abort_policy_cancels_remaining_slices(self):
        order = RecordingOrder()
        executor, _ = make_executor(order, price=lambda code: 71000.0)
        schedule = build_twap_schedule(40, 4, START, timedelta(minutes=20))

        result = executor.run(
            schedule,
            code="005930",
            side="buy",
            limit_price=70000.0,
            on_price_breach="abort",
        )

        assert result.status == "aborted"
        assert result.slices[0].status == SLICE_SKIPPED
        assert [s.status for s in result.slices[1:]] == [SLICE_CANCELLED] * 3
        assert all(s.reason == REASON_UPSTREAM_ABORT for s in result.slices[1:])
        assert "지정가 이탈로 중단했습니다" in result.notes

    def test_price_lookup_failure_skips_rather_than_orders_blind(self):
        order = RecordingOrder()

        def broken_price(code):
            raise RuntimeError("network down")

        executor, _ = make_executor(order, price=broken_price)
        schedule = build_twap_schedule(10, 1, START, timedelta(minutes=5))

        result = executor.run(schedule, code="005930", side="buy", limit_price=70000.0)

        assert order.calls == []
        assert result.slices[0].reason == REASON_PRICE_UNAVAILABLE

    def test_limit_without_price_func_is_rejected_up_front(self):
        executor, _ = make_executor()
        schedule = build_twap_schedule(10, 1, START, timedelta(minutes=5))
        with pytest.raises(ValueError, match="limit_price requires a price_func"):
            executor.run(schedule, code="005930", side="buy", limit_price=70000.0)


class TestSessionGuard:
    def test_slices_outside_the_session_are_skipped(self):
        order = RecordingOrder()
        executor, _ = make_executor(order)
        schedule = build_twap_schedule(20, 2, START, timedelta(minutes=10))

        result = executor.run(
            schedule, code="005930", side="buy", session_guard=lambda dt: False
        )

        assert order.calls == []
        assert all(s.reason == REASON_SESSION for s in result.slices)
        assert all(s.submitted_at is None for s in result.slices)


class TestFailureHandling:
    def test_transient_failure_does_not_stop_the_run(self):
        order = RecordingOrder([{"rt_cd": "1", "msg1": "거부"}, OK, OK, OK])
        executor, _ = make_executor(order)
        schedule = build_twap_schedule(40, 4, START, timedelta(minutes=20))

        result = executor.run(schedule, code="005930", side="buy")

        assert result.status == "partial"
        assert result.slices[0].status == SLICE_FAILED
        assert result.submitted_quantity == 30

    def test_consecutive_failures_abort_the_parent_order(self):
        order = RecordingOrder([{"rt_cd": "1", "msg1": "잔고부족"}])
        executor, _ = make_executor(order)
        schedule = build_twap_schedule(50, 5, START, timedelta(minutes=25))

        result = executor.run(
            schedule, code="005930", side="buy", max_consecutive_failures=2
        )

        assert result.status == "aborted"
        assert len(order.calls) == 2
        assert [s.status for s in result.slices] == [
            SLICE_FAILED,
            SLICE_FAILED,
            SLICE_CANCELLED,
            SLICE_CANCELLED,
            SLICE_CANCELLED,
        ]
        assert "연속 2회 주문 실패로 중단했습니다" in result.notes

    def test_failure_counter_resets_after_a_success(self):
        order = RecordingOrder(
            [{"rt_cd": "1", "msg1": "거부"}, OK, {"rt_cd": "1", "msg1": "거부"}, OK]
        )
        executor, _ = make_executor(order)
        schedule = build_twap_schedule(40, 4, START, timedelta(minutes=20))

        result = executor.run(
            schedule, code="005930", side="buy", max_consecutive_failures=2
        )

        assert result.status == "partial"
        assert len(order.calls) == 4

    def test_none_response_counts_as_failure(self):
        order = RecordingOrder([None])
        executor, _ = make_executor(order)
        schedule = build_twap_schedule(10, 1, START, timedelta(minutes=5))
        result = executor.run(schedule, code="005930", side="buy")
        assert result.slices[0].status == SLICE_FAILED
        assert result.slices[0].reason == REASON_ORDER_REJECTED

    def test_order_exception_is_contained_in_the_slice(self):
        def exploding(code, quantity, side, **kwargs):
            raise ConnectionError("boom")

        executor, _ = make_executor(exploding)
        schedule = build_twap_schedule(10, 1, START, timedelta(minutes=5))
        result = executor.run(schedule, code="005930", side="buy")
        assert result.slices[0].status == SLICE_FAILED
        assert "ConnectionError: boom" in result.slices[0].message


class TestInterruption:
    def test_interrupt_during_order_reports_partial_progress(self):
        calls = {"n": 0}

        def interrupting(code, quantity, side, **kwargs):
            calls["n"] += 1
            if calls["n"] == 2:
                raise KeyboardInterrupt
            return OK

        executor, _ = make_executor(interrupting)
        schedule = build_twap_schedule(40, 4, START, timedelta(minutes=20))

        result = executor.run(schedule, code="005930", side="buy")

        assert result.status == "cancelled"
        assert result.submitted_quantity == 10
        assert [s.status for s in result.slices[1:]] == [SLICE_CANCELLED] * 3
        assert all(s.reason == REASON_INTERRUPTED for s in result.slices[1:])

    def test_interrupt_while_waiting_reports_partial_progress(self):
        clock = FakeClock()
        state = {"n": 0}

        def interrupting_sleep(seconds):
            state["n"] += 1
            if state["n"] > 2:
                raise KeyboardInterrupt
            clock.sleep(seconds)

        executor = AlgoExecutor(
            order_func=RecordingOrder(),
            sleep_func=interrupting_sleep,
            monotonic_func=clock.monotonic,
            now_func=clock.now,
        )
        schedule = build_twap_schedule(40, 4, START, timedelta(minutes=20))

        result = executor.run(schedule, code="005930", side="buy")

        assert result.status == "cancelled"
        assert result.submitted_quantity == 10


class TestDryRun:
    def test_dry_run_never_touches_the_order_api(self):
        order = RecordingOrder()
        executor, _ = make_executor(order)
        schedule = build_twap_schedule(40, 4, START, timedelta(minutes=20))

        result = executor.run(schedule, code="005930", side="buy", dry_run=True)

        assert order.calls == []
        assert result.dry_run is True
        # STO-1731: a dry run must not read as "completed" execution
        assert result.status == "simulated"
        assert all(s.status == SLICE_SIMULATED for s in result.slices)
        assert result.submitted_quantity == 40

    def test_dry_run_still_evaluates_the_price_guard(self):
        order = RecordingOrder()
        executor, _ = make_executor(order, price=lambda code: 71000.0)
        schedule = build_twap_schedule(20, 2, START, timedelta(minutes=10))

        result = executor.run(
            schedule, code="005930", side="buy", limit_price=70000.0, dry_run=True
        )

        assert all(s.status == SLICE_SKIPPED for s in result.slices)


class TestValidation:
    @pytest.mark.parametrize(
        "kwargs,match",
        [
            ({"side": "hold"}, "side must be"),
            ({"on_price_breach": "explode"}, "on_price_breach must be"),
            ({"max_consecutive_failures": 0}, "max_consecutive_failures"),
        ],
    )
    def test_invalid_arguments_are_rejected(self, kwargs, match):
        executor, _ = make_executor()
        schedule = build_twap_schedule(10, 1, START, timedelta(minutes=5))
        params = {"code": "005930", "side": "buy"}
        params.update(kwargs)
        with pytest.raises(ValueError, match=match):
            executor.run(schedule, **params)

    def test_empty_schedule_is_rejected(self):
        executor, _ = make_executor()
        with pytest.raises(ValueError, match="schedule must not be empty"):
            executor.run([], code="005930", side="buy")

    def test_side_is_case_insensitive(self):
        order = RecordingOrder()
        executor, _ = make_executor(order)
        schedule = build_twap_schedule(10, 1, START, timedelta(minutes=5))
        executor.run(schedule, code="005930", side="BUY")
        assert order.calls[0]["side"] == "buy"


class TestSerialisation:
    def test_result_dict_is_json_serialisable(self):
        import json

        executor, _ = make_executor()
        schedule = build_twap_schedule(20, 2, START, timedelta(minutes=10))
        result = executor.run(schedule, code="005930", side="buy")

        payload = json.dumps(result.to_dict(), ensure_ascii=False)
        restored = json.loads(payload)

        assert restored["algorithm"] == "twap"
        assert restored["submittedQuantity"] == 20
        assert restored["sliceCount"] == 2
        assert restored["slices"][0]["orderNo"] == "0000123456"


class TestPriceLookupEdges:
    def test_missing_price_func_yields_no_reference_price(self):
        # limit_price is rejected up front, so an unguarded run simply has none.
        order = RecordingOrder()
        executor, _ = make_executor(order)
        schedule = build_twap_schedule(10, 1, START, timedelta(minutes=5))
        result = executor.run(schedule, code="005930", side="buy")
        assert result.slices[0].reference_price is None
        assert executor._current_price("005930") is None

    @pytest.mark.parametrize("bad_price", [None, 0, -1])
    def test_non_positive_price_is_treated_as_unavailable(self, bad_price):
        order = RecordingOrder()
        executor, _ = make_executor(order, price=lambda code: bad_price)
        schedule = build_twap_schedule(10, 1, START, timedelta(minutes=5))
        result = executor.run(schedule, code="005930", side="buy", limit_price=70000.0)
        assert order.calls == []
        assert result.slices[0].reason == REASON_PRICE_UNAVAILABLE

    def test_interrupt_during_price_lookup_propagates_to_the_run(self):
        def interrupting_price(code):
            raise KeyboardInterrupt

        order = RecordingOrder()
        executor, _ = make_executor(order, price=interrupting_price)
        schedule = build_twap_schedule(20, 2, START, timedelta(minutes=10))
        result = executor.run(schedule, code="005930", side="buy", limit_price=70000.0)
        assert result.status == "cancelled"
        assert order.calls == []
