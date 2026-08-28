"""Unit tests for the agent-facing TWAP/VWAP entry points."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from kis_agent.execution.runner import krx_regular_session, run_twap, run_vwap
from kis_agent.execution.volume_profile import VolumeProfile, build_profile_from_bars

START = datetime(2026, 8, 21, 10, 0)  # Friday, inside the KRX session


@pytest.fixture(autouse=True)
def isolated_journal_dir(tmp_path, monkeypatch):
    """집행 원장을 임시 디렉터리로 격리한다.

    이게 없으면 테스트가 사용자의 ~/.kis-agent/executions 에 실제 파일을 쓴다
    (실측으로 65개를 흘린 뒤 추가했다).
    """
    monkeypatch.setenv("KIS_EXECUTION_JOURNAL_DIR", str(tmp_path / "journal"))


class FakeAccountAPI:
    def __init__(self):
        self.orders = []

    def order_cash(self, pdno, qty, price, buy_sell, order_type, exchange):
        self.orders.append(
            {
                "pdno": pdno,
                "qty": qty,
                "price": price,
                "buy_sell": buy_sell,
                "order_type": order_type,
                "exchange": exchange,
            }
        )
        return {
            "rt_cd": "0",
            "msg1": "정상",
            "output": {"ODNO": f"A{len(self.orders)}"},
        }


class FakeStockAPI:
    def __init__(self, price=70000, minute_bars=None):
        self.price = price
        self.minute_bars = minute_bars or {}
        self.price_calls = 0

    def get_stock_price(self, code, market="J"):
        self.price_calls += 1
        return {"rt_cd": "0", "output": {"stck_prpr": str(self.price)}}

    def get_daily_minute_price(self, code, date, market="J"):
        return {"rt_cd": "0", "output2": self.minute_bars.get(date, [])}


class FakeAgent:
    def __init__(self, price=70000, minute_bars=None):
        self.account_api = FakeAccountAPI()
        self.stock_api = FakeStockAPI(price=price, minute_bars=minute_bars)


class FastClock:
    """Fake clock whose sleep advances time instantly, so tests never block.

    ``now`` is pinned unless the test overrides it: slice timestamps are not
    what these tests assert on, and a frozen wall clock keeps the KRX session
    guard inside the trading window for the whole run.
    """

    def __init__(self, now=START):
        self.mono = 0.0
        self._now = now

    def sleep(self, seconds):
        self.mono += seconds

    def monotonic(self):
        return self.mono

    def now(self):
        return self._now


def instant_executor(agent, clock=None, **overrides):
    """Executor wired to a fast clock, so a 20-minute schedule runs instantly."""
    from kis_agent.execution.executor import AlgoExecutor
    from kis_agent.execution.runner import _make_order_func, _make_price_func

    clock = clock or FastClock()
    return AlgoExecutor(
        order_func=overrides.get("order_func", _make_order_func(agent)),
        price_func=overrides.get("price_func", _make_price_func(agent)),
        sleep_func=clock.sleep,
        monotonic_func=clock.monotonic,
        now_func=clock.now,
    )


class TestKrxRegularSession:
    @pytest.mark.parametrize(
        "moment,expected",
        [
            (datetime(2026, 8, 21, 9, 0), True),  # open bell
            (datetime(2026, 8, 21, 15, 29), True),
            (datetime(2026, 8, 21, 15, 30), False),  # close is exclusive
            (datetime(2026, 8, 21, 8, 59), False),
            (datetime(2026, 8, 22, 10, 0), False),  # Saturday
            (datetime(2026, 8, 23, 10, 0), False),  # Sunday
        ],
    )
    def test_session_window(self, moment, expected):
        assert krx_regular_session(moment) is expected


class TestRunTwap:
    def test_places_every_slice_through_order_cash(self):
        agent = FakeAgent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=100,
            duration_minutes=20,
            slices=4,
            start=START,
            executor=instant_executor(agent),
        )
        assert result.status == "completed"
        assert [o["qty"] for o in agent.account_api.orders] == [25, 25, 25, 25]
        assert agent.account_api.orders[0]["buy_sell"] == "BUY"
        assert agent.account_api.orders[0]["order_type"] == "03"

    def test_order_parameters_are_threaded_through(self):
        agent = FakeAgent()
        run_twap(
            agent,
            code="005930",
            side="sell",
            quantity=10,
            duration_minutes=5,
            slices=1,
            order_type="00",
            price=71000,
            exchange="NXT",
            start=START,
            executor=instant_executor(agent),
        )
        order = agent.account_api.orders[0]
        assert order["buy_sell"] == "SELL"
        assert order["order_type"] == "00"
        assert order["price"] == 71000
        assert order["exchange"] == "NXT"

    def test_dry_run_places_nothing(self):
        agent = FakeAgent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=100,
            duration_minutes=20,
            slices=4,
            dry_run=True,
            start=START,
            executor=instant_executor(agent),
        )
        assert agent.account_api.orders == []
        assert result.dry_run is True
        assert result.submitted_quantity == 100

    def test_limit_price_guard_uses_the_live_price(self):
        agent = FakeAgent(price=71000)
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            limit_price=70000,
            start=START,
            executor=instant_executor(agent),
        )
        assert agent.account_api.orders == []
        assert result.unfilled_quantity == 20

    def test_session_restriction_blocks_out_of_hours_runs(self):
        agent = FakeAgent()
        after_close = datetime(2026, 8, 21, 16, 0)
        executor = instant_executor(agent, clock=FastClock(now=after_close))
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            start=after_close,
            executor=executor,
        )
        assert agent.account_api.orders == []
        assert result.status == "partial"

    def test_session_restriction_can_be_disabled(self):
        agent = FakeAgent()
        after_close = datetime(2026, 8, 21, 16, 0)
        executor = instant_executor(agent, clock=FastClock(now=after_close))
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            start=after_close,
            restrict_to_session=False,
            executor=executor,
        )
        assert len(agent.account_api.orders) == 2
        assert result.status == "completed"

    @pytest.mark.parametrize(
        "qty,duration,slices",
        [(0, 30, 6), (-5, 30, 6), (10, 0, 6), (10, -1, 6), (10, 30, 0), (10, 30, -2)],
    )
    def test_rejects_out_of_range_arguments(self, qty, duration, slices):
        agent = FakeAgent()
        with pytest.raises(ValueError):
            run_twap(
                agent,
                code="005930",
                side="buy",
                quantity=qty,
                duration_minutes=duration,
                slices=slices,
                executor=instant_executor(agent),
            )

    def test_zero_slices_error_names_the_slices_argument(self):
        # run_vwap와 같은 메시지를 내야 한다 — 깊은 계층의 "parts"가 아니라.
        agent = FakeAgent()
        with pytest.raises(ValueError, match="slices must be positive"):
            run_twap(
                agent,
                code="005930",
                side="buy",
                quantity=10,
                duration_minutes=30,
                slices=0,
                executor=instant_executor(agent),
            )


class TestRunVwap:
    def test_quantities_follow_the_supplied_profile(self):
        agent = FakeAgent()
        profile = build_profile_from_bars(
            {
                "20260820": [
                    {"stck_cntg_hour": "100000", "cntg_vol": "100"},
                    {"stck_cntg_hour": "101000", "cntg_vol": "300"},
                ]
            }
        )
        result = run_vwap(
            agent,
            code="005930",
            side="buy",
            quantity=100,
            duration_minutes=20,
            slices=2,
            start=START,
            profile=profile,
            executor=instant_executor(agent),
        )
        assert [o["qty"] for o in agent.account_api.orders] == [25, 75]
        assert result.algorithm == "vwap"

    def test_profile_provenance_is_reported(self):
        agent = FakeAgent()
        profile = build_profile_from_bars(
            {"20260820": [{"stck_cntg_hour": "100000", "cntg_vol": "100"}]}
        )
        result = run_vwap(
            agent,
            code="005930",
            side="buy",
            quantity=10,
            duration_minutes=20,
            slices=2,
            start=START,
            profile=profile,
            executor=instant_executor(agent),
        )
        assert any("거래량 프로파일" in note for note in result.notes)

    def test_missing_profile_falls_back_to_even_split_and_says_so(self):
        agent = FakeAgent()
        empty = VolumeProfile(fallback_reason="분봉 없음")
        result = run_vwap(
            agent,
            code="005930",
            side="buy",
            quantity=100,
            duration_minutes=20,
            slices=4,
            start=START,
            profile=empty,
            executor=instant_executor(agent),
        )
        assert [o["qty"] for o in agent.account_api.orders] == [25, 25, 25, 25]
        assert result.notes
        assert "균등 분할" in result.notes[0]
        assert "분봉 없음" in result.notes[0]

    def test_profile_is_fetched_from_the_agent_when_not_supplied(self):
        bars = {
            "20260820": [
                {"stck_cntg_hour": "100000", "cntg_vol": "100"},
                {"stck_cntg_hour": "101000", "cntg_vol": "300"},
            ]
        }
        agent = FakeAgent(minute_bars=bars)
        run_vwap(
            agent,
            code="005930",
            side="buy",
            quantity=100,
            duration_minutes=20,
            slices=2,
            profile_days=1,
            start=START,
            executor=instant_executor(agent),
        )
        assert [o["qty"] for o in agent.account_api.orders] == [25, 75]

    def test_dry_run_places_nothing(self):
        agent = FakeAgent()
        result = run_vwap(
            agent,
            code="005930",
            side="buy",
            quantity=50,
            duration_minutes=20,
            slices=2,
            start=START,
            profile=VolumeProfile(fallback_reason="none"),
            dry_run=True,
            executor=instant_executor(agent),
        )
        assert agent.account_api.orders == []
        assert result.submitted_quantity == 50

    @pytest.mark.parametrize(
        "qty,duration,slices", [(0, 30, 4), (10, 0, 4), (10, 30, 0)]
    )
    def test_rejects_out_of_range_arguments(self, qty, duration, slices):
        agent = FakeAgent()
        with pytest.raises(ValueError):
            run_vwap(
                agent,
                code="005930",
                side="buy",
                quantity=qty,
                duration_minutes=duration,
                slices=slices,
                executor=instant_executor(agent),
            )


class TestPriceParsing:
    def test_comma_formatted_price_is_parsed(self):
        from kis_agent.execution.runner import _make_price_func

        agent = FakeAgent()
        agent.stock_api.price = "70,500"
        assert _make_price_func(agent)("005930") == 70500.0

    def test_blank_price_returns_none(self):
        from kis_agent.execution.runner import _make_price_func

        class Blank:
            def get_stock_price(self, code, market="J"):
                return {"output": {"stck_prpr": ""}}

        agent = FakeAgent()
        agent.stock_api = Blank()
        assert _make_price_func(agent)("005930") is None

    def test_missing_output_returns_none(self):
        from kis_agent.execution.runner import _make_price_func

        class Missing:
            def get_stock_price(self, code, market="J"):
                return None

        agent = FakeAgent()
        agent.stock_api = Missing()
        assert _make_price_func(agent)("005930") is None


class FakeCreditAccountAPI(FakeAccountAPI):
    """계좌 API 스텁 — 현금/신용 주문을 각각 기록하고 신용 거부를 흉내낸다."""

    def __init__(self, credit_accepts=True):
        super().__init__()
        self.credit_buys = []
        self.credit_sells = []
        self.credit_accepts = credit_accepts

    def _credit_response(self, bucket):
        if self.credit_accepts:
            return {"rt_cd": "0", "msg1": "정상", "output": {"ODNO": f"C{len(bucket)}"}}
        return {"rt_cd": "1", "msg1": "신용융자 매수가 불가능한 종목입니다"}

    def order_credit_buy(
        self,
        pdno,
        qty,
        price,
        order_type="00",
        credit_type="21",
        exchange="KRX",
        loan_dt="",
    ):
        self.credit_buys.append(
            {
                "pdno": pdno,
                "qty": qty,
                "price": price,
                "order_type": order_type,
                "credit_type": credit_type,
                "exchange": exchange,
                "loan_dt": loan_dt,
            }
        )
        return self._credit_response(self.credit_buys)

    def order_credit_sell(self, pdno, qty, price, order_type="00", credit_type="11"):
        self.credit_sells.append(
            {
                "pdno": pdno,
                "qty": qty,
                "price": price,
                "order_type": order_type,
                "credit_type": credit_type,
            }
        )
        return self._credit_response(self.credit_sells)


def credit_agent(credit_accepts=True):
    agent = FakeAgent()
    agent.account_api = FakeCreditAccountAPI(credit_accepts=credit_accepts)
    return agent


class TestCreditFunding:
    def test_credit_buy_routes_to_the_credit_endpoint(self):
        agent = credit_agent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=100,
            duration_minutes=20,
            slices=2,
            funding="credit",
            start=START,
            executor=instant_executor(agent),
        )
        assert agent.account_api.orders == []  # 현금 경로는 타지 않는다
        assert [o["qty"] for o in agent.account_api.credit_buys] == [50, 50]
        assert result.status == "completed"

    def test_credit_buy_defaults_to_shinyong_yungja(self):
        agent = credit_agent()
        run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=10,
            duration_minutes=5,
            slices=1,
            funding="credit",
            start=START,
            executor=instant_executor(agent),
        )
        assert agent.account_api.credit_buys[0]["credit_type"] == "21"

    def test_credit_sell_defaults_to_repayment_code(self):
        agent = credit_agent()
        run_twap(
            agent,
            code="005930",
            side="sell",
            quantity=10,
            duration_minutes=5,
            slices=1,
            funding="credit",
            start=START,
            executor=instant_executor(agent),
        )
        assert agent.account_api.credit_sells[0]["credit_type"] == "11"
        assert agent.account_api.credit_buys == []

    def test_explicit_credit_type_and_loan_date_are_forwarded(self):
        agent = credit_agent()
        run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=10,
            duration_minutes=5,
            slices=1,
            funding="credit",
            credit_type="22",
            loan_dt="20260821",
            start=START,
            executor=instant_executor(agent),
        )
        order = agent.account_api.credit_buys[0]
        assert order["credit_type"] == "22"
        assert order["loan_dt"] == "20260821"

    def test_rejected_credit_order_fails_the_slice_without_fallback(self):
        agent = credit_agent(credit_accepts=False)
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            funding="credit",
            max_consecutive_failures=5,
            start=START,
            executor=instant_executor(agent),
        )
        assert agent.account_api.orders == []  # 말없이 현금으로 바꾸지 않는다
        assert result.submitted_quantity == 0
        assert result.status == "partial"

    def test_fallback_switches_to_cash_and_says_so(self):
        agent = credit_agent(credit_accepts=False)
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            funding="credit",
            credit_fallback_to_cash=True,
            start=START,
            executor=instant_executor(agent),
        )
        assert len(agent.account_api.credit_buys) == 2
        assert [o["qty"] for o in agent.account_api.orders] == [10, 10]
        assert result.status == "completed"
        assert result.submitted_quantity == 20
        # 자금 조달 방식이 바뀐 사실이 슬라이스 보고에 남아야 한다.
        assert "현금 폴백" in result.slices[0].message
        assert "신용융자 매수가 불가능한 종목입니다" in result.slices[0].message

    def test_fallback_is_not_used_when_credit_succeeds(self):
        agent = credit_agent(credit_accepts=True)
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            funding="credit",
            credit_fallback_to_cash=True,
            start=START,
            executor=instant_executor(agent),
        )
        assert agent.account_api.orders == []
        assert all("폴백" not in s.message for s in result.slices)

    def test_cash_is_still_the_default(self):
        agent = credit_agent()
        run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=10,
            duration_minutes=5,
            slices=1,
            start=START,
            executor=instant_executor(agent),
        )
        assert len(agent.account_api.orders) == 1
        assert agent.account_api.credit_buys == []

    def test_vwap_honours_the_funding_source(self):
        agent = credit_agent()
        run_vwap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            funding="credit",
            start=START,
            profile=VolumeProfile(fallback_reason="none"),
            executor=instant_executor(agent),
        )
        assert len(agent.account_api.credit_buys) == 2

    def test_dry_run_never_touches_the_credit_endpoint(self):
        agent = credit_agent()
        run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            funding="credit",
            dry_run=True,
            start=START,
            executor=instant_executor(agent),
        )
        assert agent.account_api.credit_buys == []
        assert agent.account_api.orders == []

    @pytest.mark.parametrize("bad", ["margin", "loan", ""])
    def test_unknown_funding_source_is_rejected(self, bad):
        agent = credit_agent()
        if bad == "":
            # 빈 문자열은 기본값(cash)으로 정규화된다.
            run_twap(
                agent,
                code="005930",
                side="buy",
                quantity=10,
                duration_minutes=5,
                slices=1,
                funding=bad,
                start=START,
                executor=instant_executor(agent),
            )
            assert len(agent.account_api.orders) == 1
            return
        with pytest.raises(ValueError, match="funding must be one of"):
            run_twap(
                agent,
                code="005930",
                side="buy",
                quantity=10,
                duration_minutes=5,
                slices=1,
                funding=bad,
                start=START,
                executor=instant_executor(agent),
            )

    def test_funding_is_case_insensitive(self):
        agent = credit_agent()
        run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=10,
            duration_minutes=5,
            slices=1,
            funding="CREDIT",
            start=START,
            executor=instant_executor(agent),
        )
        assert len(agent.account_api.credit_buys) == 1


class TestPriceParsingEdges:
    def test_non_numeric_price_returns_none(self):
        from kis_agent.execution.runner import _make_price_func

        class Garbled:
            def get_stock_price(self, code, market="J"):
                return {"output": {"stck_prpr": "N/A"}}

        agent = FakeAgent()
        agent.stock_api = Garbled()
        assert _make_price_func(agent)("005930") is None


class TestSessionBoundary:
    def test_open_bell_is_inclusive_and_close_is_exclusive(self):
        # 15:30:00 is the close itself, not a tradable instant.
        assert krx_regular_session(datetime(2026, 8, 21, 9, 0, 0)) is True
        assert krx_regular_session(datetime(2026, 8, 21, 15, 29, 59)) is True
        assert krx_regular_session(datetime(2026, 8, 21, 15, 30, 0)) is False


class TestJournalIntegration:
    def test_every_placed_order_is_journalled_with_its_order_number(self, tmp_path):
        from kis_agent.execution.journal import read_journal

        agent = FakeAgent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=100,
            duration_minutes=20,
            slices=4,
            start=START,
            journal_dir=tmp_path,
            executor=instant_executor(agent),
        )

        assert result.run_id
        assert result.journal_path
        events = read_journal(Path(result.journal_path))
        slices = [e for e in events if e["event"] == "slice"]
        assert [s["quantity"] for s in slices] == [25, 25, 25, 25]
        assert [s["orderNo"] for s in slices] == ["A1", "A2", "A3", "A4"]

    def test_plan_is_recorded_before_the_first_order(self, tmp_path):
        from kis_agent.execution.journal import read_journal

        agent = FakeAgent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=100,
            duration_minutes=20,
            slices=4,
            funding="credit",
            limit_price=70000,
            start=START,
            journal_dir=tmp_path,
            executor=instant_executor(agent),
        )
        events = read_journal(Path(result.journal_path))
        start_event = events[0]
        assert start_event["event"] == "start"
        assert start_event["funding"] == "credit"
        assert start_event["limitPrice"] == 70000
        assert len(start_event["schedule"]) == 4

    def test_end_record_closes_the_run(self, tmp_path):
        from kis_agent.execution.journal import find_incomplete_runs, read_journal

        agent = FakeAgent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=40,
            duration_minutes=10,
            slices=2,
            start=START,
            journal_dir=tmp_path,
            executor=instant_executor(agent),
        )
        events = read_journal(Path(result.journal_path))
        assert events[-1]["event"] == "end"
        assert events[-1]["submittedQuantity"] == 40
        assert find_incomplete_runs("005930", base_dir=tmp_path) == []

    def test_vwap_notes_land_in_the_end_record(self, tmp_path):
        from kis_agent.execution.journal import read_journal

        agent = FakeAgent()
        result = run_vwap(
            agent,
            code="005930",
            side="buy",
            quantity=40,
            duration_minutes=10,
            slices=2,
            start=START,
            journal_dir=tmp_path,
            profile=VolumeProfile(fallback_reason="분봉 없음"),
            executor=instant_executor(agent),
        )
        events = read_journal(Path(result.journal_path))
        assert any("균등 분할" in n for n in events[-1]["notes"])

    def test_journal_can_be_disabled(self, tmp_path):
        agent = FakeAgent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            start=START,
            journal_dir=tmp_path,
            journal_enabled=False,
            executor=instant_executor(agent),
        )
        assert result.run_id == ""
        assert result.journal_path == ""
        assert list(tmp_path.rglob("*.jsonl")) == []

    def test_unopenable_journal_does_not_stop_the_order(self, tmp_path, monkeypatch):
        from kis_agent.execution import runner as runner_mod

        def explode(*a, **kw):
            raise OSError("read-only filesystem")

        monkeypatch.setattr(runner_mod.ExecutionJournal, "create", explode)
        agent = FakeAgent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            start=START,
            journal_dir=tmp_path,
            executor=instant_executor(agent),
        )
        # 원장을 못 열어도 주문은 나가야 한다 — 관측성 저하이지 정지 사유가 아니다.
        assert len(agent.account_api.orders) == 2
        assert result.status == "completed"
        assert result.journal_path == ""

    def test_dry_run_journal_is_marked_and_never_blocks_the_next_run(self, tmp_path):
        from kis_agent.execution.journal import find_incomplete_runs, read_journal

        agent = FakeAgent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            dry_run=True,
            start=START,
            journal_dir=tmp_path,
            executor=instant_executor(agent),
        )
        events = read_journal(Path(result.journal_path))
        assert events[0]["dryRun"] is True
        assert find_incomplete_runs("005930", base_dir=tmp_path) == []


class TestIncompleteGuardInRunner:
    """CLI뿐 아니라 Python API 호출자도 보호받아야 한다."""

    def _crash(self, base, code="005930"):
        from kis_agent.execution.journal import ExecutionJournal

        j = ExecutionJournal.create(code, "buy", base_dir=base)
        j.record_start(
            {"code": code, "side": "buy", "totalQuantity": 100, "dryRun": False}
        )
        j.record_slice(
            {"index": 0, "quantity": 40, "status": "filled", "orderNo": "LIVE-9"}
        )

    def test_run_twap_refuses_after_a_crashed_run(self, tmp_path):
        from kis_agent.execution import IncompleteExecutionError

        self._crash(tmp_path)
        agent = FakeAgent()
        with pytest.raises(IncompleteExecutionError) as exc:
            run_twap(
                agent,
                code="005930",
                side="buy",
                quantity=100,
                duration_minutes=10,
                slices=2,
                start=START,
                journal_dir=tmp_path,
                executor=instant_executor(agent),
            )
        assert agent.account_api.orders == []
        assert exc.value.runs[0].order_numbers == ["LIVE-9"]
        assert "LIVE-9" in str(exc.value)

    def test_run_vwap_refuses_too(self, tmp_path):
        from kis_agent.execution import IncompleteExecutionError

        self._crash(tmp_path)
        agent = FakeAgent()
        with pytest.raises(IncompleteExecutionError):
            run_vwap(
                agent,
                code="005930",
                side="buy",
                quantity=100,
                duration_minutes=10,
                slices=2,
                start=START,
                journal_dir=tmp_path,
                profile=VolumeProfile(fallback_reason="none"),
                executor=instant_executor(agent),
            )

    def test_dry_run_is_never_refused(self, tmp_path):
        self._crash(tmp_path)
        agent = FakeAgent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            dry_run=True,
            start=START,
            journal_dir=tmp_path,
            executor=instant_executor(agent),
        )
        assert result.status == "simulated"  # STO-1731: dry-run is not "completed"

    def test_opt_out_allows_proceeding(self, tmp_path):
        self._crash(tmp_path)
        agent = FakeAgent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            start=START,
            journal_dir=tmp_path,
            check_incomplete=False,
            executor=instant_executor(agent),
        )
        assert len(agent.account_api.orders) == 2
        assert result.status == "completed"

    def test_a_different_ticker_is_unaffected(self, tmp_path):
        self._crash(tmp_path, code="000660")
        agent = FakeAgent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            start=START,
            journal_dir=tmp_path,
            executor=instant_executor(agent),
        )
        assert result.status == "completed"


class TestJournalClosesOnEveryNormalExit:
    """문서가 "정상 종료와 Ctrl+C는 원장을 닫는다"고 주장한다 — 실제로 그런지 고정한다.

    이 성질이 깨지면 의도적으로 멈춘 운영자가 다음 집행에서 가드에 걸린다.
    """

    def _journal_is_closed(self, result):
        from kis_agent.execution.journal import read_journal

        events = read_journal(Path(result.journal_path))
        return any(e["event"] == "end" for e in events)

    def test_ctrl_c_closes_the_journal(self, tmp_path):
        calls = {"n": 0}

        def interrupting(code, quantity, side, **kwargs):
            calls["n"] += 1
            if calls["n"] == 2:
                raise KeyboardInterrupt
            return {"rt_cd": "0", "output": {"ODNO": "A1"}}

        agent = FakeAgent()
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=40,
            duration_minutes=10,
            slices=4,
            start=START,
            journal_dir=tmp_path,
            executor=instant_executor(agent, order_func=interrupting),
        )
        assert result.status == "cancelled"
        assert self._journal_is_closed(result)
        # 의도적 중단은 다음 집행을 막지 않는다.
        from kis_agent.execution.journal import find_incomplete_runs

        assert find_incomplete_runs("005930", base_dir=tmp_path, side="buy") == []

    def test_aborted_run_closes_the_journal(self, tmp_path):
        agent = FakeAgent()
        agent.account_api.order_cash = lambda **kw: {"rt_cd": "1", "msg1": "거부"}
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=50,
            duration_minutes=10,
            slices=5,
            max_consecutive_failures=2,
            start=START,
            journal_dir=tmp_path,
            executor=instant_executor(agent),
        )
        assert result.status == "aborted"
        assert self._journal_is_closed(result)

    def test_partial_run_closes_the_journal(self, tmp_path):
        agent = FakeAgent(price=71000)
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            limit_price=70000,
            start=START,
            journal_dir=tmp_path,
            executor=instant_executor(agent),
        )
        assert result.status == "partial"
        assert self._journal_is_closed(result)

    def test_skipped_slices_are_journaled_for_audit(self, tmp_path):
        from kis_agent.execution.journal import read_journal

        agent = FakeAgent(price=71000)
        result = run_twap(
            agent,
            code="005930",
            side="buy",
            quantity=20,
            duration_minutes=10,
            slices=2,
            limit_price=70000,
            start=START,
            journal_dir=tmp_path,
            executor=instant_executor(agent),
        )
        slices = [
            e for e in read_journal(Path(result.journal_path)) if e["event"] == "slice"
        ]
        assert [s["status"] for s in slices] == ["skipped", "skipped"]
        assert all(s["reason"] == "price_limit" for s in slices)


class TestGuardDoesNotBlockUnwinding:
    def test_crashed_buy_does_not_block_a_sell(self, tmp_path):
        from kis_agent.execution.journal import ExecutionJournal

        j = ExecutionJournal.create("005930", "buy", base_dir=tmp_path)
        j.record_start(
            {"code": "005930", "side": "buy", "totalQuantity": 100, "dryRun": False}
        )
        j.record_slice(
            {"index": 0, "quantity": 40, "status": "filled", "orderNo": "LIVE-9"}
        )

        agent = FakeAgent()
        # 크래시한 매수 이후 청산 매도는 통과해야 한다.
        result = run_twap(
            agent,
            code="005930",
            side="sell",
            quantity=40,
            duration_minutes=10,
            slices=2,
            start=START,
            journal_dir=tmp_path,
            executor=instant_executor(agent),
        )
        assert result.status == "completed"
        assert len(agent.account_api.orders) == 2

    def test_crashed_buy_still_blocks_another_buy(self, tmp_path):
        from kis_agent.execution import IncompleteExecutionError
        from kis_agent.execution.journal import ExecutionJournal

        j = ExecutionJournal.create("005930", "buy", base_dir=tmp_path)
        j.record_start(
            {"code": "005930", "side": "buy", "totalQuantity": 100, "dryRun": False}
        )
        j.record_slice(
            {"index": 0, "quantity": 40, "status": "filled", "orderNo": "LIVE-9"}
        )

        agent = FakeAgent()
        with pytest.raises(IncompleteExecutionError):
            run_twap(
                agent,
                code="005930",
                side="buy",
                quantity=40,
                duration_minutes=10,
                slices=2,
                start=START,
                journal_dir=tmp_path,
                executor=instant_executor(agent),
            )
