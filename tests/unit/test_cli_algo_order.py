"""CLI 알고리즘 주문(TWAP/VWAP) 유닛 테스트.

파서 계약, 확인 프롬프트, dry-run 미전송, 종료코드 규약을 검증한다.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from kis_agent.cli.main import build_parser, cmd_order
from kis_agent.execution import executor as executor_mod
from kis_agent.execution import runner as runner_mod


@pytest.fixture(autouse=True)
def isolated_journal_dir(tmp_path, monkeypatch):
    """집행 원장을 임시 디렉터리로 격리한다.

    이게 없으면 테스트가 사용자의 ~/.kis-agent/executions 에 실제 파일을 쓴다
    (실측으로 65개를 흘린 뒤 추가했다).
    """
    monkeypatch.setenv("KIS_EXECUTION_JOURNAL_DIR", str(tmp_path / "journal"))


@pytest.fixture(autouse=True)
def fast_and_open_market(monkeypatch):
    """스케줄 대기를 즉시 끝내고, 정규장 여부와 무관하게 결정적으로 돌린다.

    실제 벽시계에 의존하면 장 마감 후·주말 실행에서 테스트가 깨진다.
    """
    state = {"mono": 0.0}

    def fake_sleep(seconds):
        state["mono"] += seconds

    monkeypatch.setattr(executor_mod.time, "sleep", fake_sleep)
    monkeypatch.setattr(executor_mod.time, "monotonic", lambda: state["mono"])
    monkeypatch.setattr(runner_mod, "krx_regular_session", lambda moment: True)


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
    def __init__(self, price=70000):
        self.price = price

    def get_stock_price(self, code, market="J"):
        return {"rt_cd": "0", "output": {"stck_prpr": str(self.price)}}

    def search_stock_info(self, code):
        return {"rt_cd": "0", "output": {"prdt_abrv_name": "삼성전자"}}

    def get_daily_minute_price(self, code, date, market="J"):
        return {"rt_cd": "0", "output2": []}


class FakeAgent:
    def __init__(self, price=70000):
        self.account_api = FakeAccountAPI()
        self.stock_api = FakeStockAPI(price=price)


def parse(argv):
    return build_parser().parse_args(argv)


def run_cli(argv, agent=None, capsys=None):
    """cmd_order를 실행하고 (stdout JSON, agent, SystemExit code)를 돌려준다."""
    agent = agent or FakeAgent()
    args = parse(argv)
    code = None
    with patch("kis_agent.cli.main._create_agent", return_value=agent), patch(
        "kis_agent.cli.main._resolve", side_effect=lambda c: c
    ):
        try:
            cmd_order(args)
        except SystemExit as e:
            code = e.code
    payload = None
    if capsys is not None:
        out = capsys.readouterr().out.strip()
        if out:
            payload = json.loads(out.splitlines()[-1])
    return payload, agent, code


BASE = ["order", "twap", "005930", "--side", "buy", "--qty", "60"]


class TestParser:
    def test_twap_defaults(self):
        args = parse(BASE)
        assert args.action == "twap"
        assert args.duration == 30
        assert args.slices == 6
        assert args.type == "best"
        assert args.exchange == "KRX"
        assert args.on_breach == "skip"
        assert args.max_failures == 3
        assert args.dry_run is False
        assert args.no_session_guard is False

    def test_vwap_defaults_differ_and_add_profile_days(self):
        args = parse(["order", "vwap", "005930", "--side", "buy", "--qty", "60"])
        assert args.duration == 60
        assert args.profile_days == 5

    def test_twap_has_no_profile_days(self):
        args = parse(BASE)
        assert not hasattr(args, "profile_days")

    def test_side_is_required(self):
        with pytest.raises(SystemExit):
            parse(["order", "twap", "005930", "--qty", "10"])

    def test_qty_is_required(self):
        with pytest.raises(SystemExit):
            parse(["order", "twap", "005930", "--side", "buy"])

    def test_invalid_side_is_rejected(self):
        with pytest.raises(SystemExit):
            parse(["order", "twap", "005930", "--side", "hold", "--qty", "10"])

    def test_invalid_breach_policy_is_rejected(self):
        with pytest.raises(SystemExit):
            parse(BASE + ["--on-breach", "explode"])


class TestDryRun:
    def test_dry_run_sends_no_orders(self, capsys):
        payload, agent, code = run_cli(
            BASE + ["--duration", "1", "--slices", "3", "--dry-run", "--yes"],
            capsys=capsys,
        )
        assert agent.account_api.orders == []
        algo = payload["data"]["algoOrder"]
        assert algo["dryRun"] is True
        assert algo["submittedQuantity"] == 60
        assert algo["sliceCount"] == 3
        assert code is None  # completed → exit 0

    def test_dry_run_reports_the_schedule(self, capsys):
        payload, _, _ = run_cli(
            BASE + ["--duration", "1", "--slices", "3", "--dry-run", "--yes"],
            capsys=capsys,
        )
        slices = payload["data"]["algoOrder"]["slices"]
        assert [s["quantity"] for s in slices] == [20, 20, 20]
        assert all(s["status"] == "simulated" for s in slices)

    def test_stock_name_is_included(self, capsys):
        payload, _, _ = run_cli(
            BASE + ["--duration", "1", "--slices", "1", "--dry-run", "--yes"],
            capsys=capsys,
        )
        assert payload["data"]["algoOrder"]["name"] == "삼성전자"


class TestConfirmation:
    def test_declining_the_prompt_places_nothing(self, capsys):
        agent = FakeAgent()
        args = parse(BASE + ["--duration", "1", "--slices", "2"])
        with patch("kis_agent.cli.main._create_agent", return_value=agent), patch(
            "kis_agent.cli.main._resolve", side_effect=lambda c: c
        ), patch("kis_agent.cli.main._confirm_order", return_value=False):
            cmd_order(args)
        payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
        assert payload["cancelled"] is True
        assert agent.account_api.orders == []

    def test_prompt_shows_the_execution_plan(self):
        agent = FakeAgent()
        args = parse(BASE + ["--duration", "1", "--slices", "3", "--dry-run"])
        captured = {}

        def fake_confirm(action, details):
            captured["action"] = action
            captured["details"] = details
            return False

        with patch("kis_agent.cli.main._create_agent", return_value=agent), patch(
            "kis_agent.cli.main._resolve", side_effect=lambda c: c
        ), patch("kis_agent.cli.main._confirm_order", side_effect=fake_confirm):
            cmd_order(args)

        assert captured["action"] == "TWAP 매수"
        details = captured["details"]
        assert details["총수량"] == "60주"
        assert "3회" in details["분할"]
        assert details["집행시간"] == "1분"
        assert "DRY-RUN" in details["모드"]

    def test_vwap_prompt_mentions_the_profile_window(self):
        agent = FakeAgent()
        args = parse(
            [
                "order",
                "vwap",
                "005930",
                "--side",
                "buy",
                "--qty",
                "60",
                "--duration",
                "1",
                "--slices",
                "2",
                "--profile-days",
                "20",
                "--dry-run",
            ]
        )
        captured = {}
        with patch("kis_agent.cli.main._create_agent", return_value=agent), patch(
            "kis_agent.cli.main._resolve", side_effect=lambda c: c
        ), patch(
            "kis_agent.cli.main._confirm_order",
            side_effect=lambda a, d: captured.update(d) or False,
        ):
            cmd_order(args)
        assert captured["거래량 프로파일"] == "과거 20영업일"


class TestGuards:
    def test_limit_price_guard_blocks_orders(self, capsys):
        agent = FakeAgent(price=71000)
        payload, agent, code = run_cli(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "2",
                "--limit-price",
                "70000",
                "--yes",
            ],
            agent=agent,
            capsys=capsys,
        )
        assert agent.account_api.orders == []
        algo = payload["data"]["algoOrder"]
        assert algo["status"] == "partial"
        assert algo["unfilledQuantity"] == 60
        assert all(s["reason"] == "price_limit" for s in algo["slices"])

    def test_partial_execution_exits_non_zero(self, capsys):
        agent = FakeAgent(price=71000)
        _, _, code = run_cli(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "2",
                "--limit-price",
                "70000",
                "--yes",
            ],
            agent=agent,
            capsys=capsys,
        )
        # 스크립트가 부분 집행을 성공으로 오독하면 안 된다.
        assert code == 2

    def test_market_order_type_forces_price_zero(self, capsys):
        _, agent, _ = run_cli(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "1",
                "--type",
                "market",
                "--price",
                "70000",
                "--yes",
            ],
            capsys=capsys,
        )
        assert agent.account_api.orders[0]["price"] == 0
        assert agent.account_api.orders[0]["order_type"] == "01"

    def test_limit_order_type_keeps_the_price(self, capsys):
        _, agent, _ = run_cli(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "1",
                "--type",
                "limit",
                "--price",
                "70000",
                "--yes",
            ],
            capsys=capsys,
        )
        assert agent.account_api.orders[0]["price"] == 70000
        assert agent.account_api.orders[0]["order_type"] == "00"

    def test_invalid_quantity_reports_an_error(self, capsys):
        payload, _, code = run_cli(
            [
                "order",
                "twap",
                "005930",
                "--side",
                "buy",
                "--qty",
                "0",
                "--duration",
                "1",
                "--yes",
            ],
            capsys=capsys,
        )
        assert code == 1
        assert "quantity must be positive" in payload["error"]


class TestLiveExecution:
    def test_orders_are_placed_when_the_session_guard_is_off(self, capsys):
        payload, agent, code = run_cli(
            BASE + ["--duration", "1", "--slices", "3", "--yes"],
            capsys=capsys,
        )
        assert [o["qty"] for o in agent.account_api.orders] == [20, 20, 20]
        assert agent.account_api.orders[0]["buy_sell"] == "BUY"
        assert payload["data"]["algoOrder"]["status"] == "completed"
        assert code is None

    def test_sell_side_is_routed_through(self, capsys):
        _, agent, _ = run_cli(
            [
                "order",
                "twap",
                "005930",
                "--side",
                "sell",
                "--qty",
                "30",
                "--duration",
                "1",
                "--slices",
                "1",
                "--yes",
            ],
            capsys=capsys,
        )
        assert agent.account_api.orders[0]["buy_sell"] == "SELL"

    def test_exchange_is_routed_through(self, capsys):
        _, agent, _ = run_cli(
            BASE + ["--duration", "1", "--slices", "1", "--exchange", "nxt", "--yes"],
            capsys=capsys,
        )
        assert agent.account_api.orders[0]["exchange"] == "NXT"


class TestUnknownAction:
    def test_unknown_action_lists_the_algo_commands(self, capsys):
        args = parse(BASE)
        args.action = "bogus"
        with pytest.raises(SystemExit):
            cmd_order(args)
        payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
        assert "twap" in payload["error"] and "vwap" in payload["error"]


class TestSessionGuardWiring:
    def test_closed_market_blocks_every_slice(self, monkeypatch, capsys):
        monkeypatch.setattr(runner_mod, "krx_regular_session", lambda moment: False)
        payload, agent, code = run_cli(
            BASE + ["--duration", "1", "--slices", "2", "--yes"], capsys=capsys
        )
        assert agent.account_api.orders == []
        algo = payload["data"]["algoOrder"]
        assert all(s["reason"] == "outside_session" for s in algo["slices"])
        assert code == 2

    def test_no_session_guard_flag_bypasses_the_check(self, monkeypatch, capsys):
        monkeypatch.setattr(runner_mod, "krx_regular_session", lambda moment: False)
        _, agent, code = run_cli(
            BASE + ["--duration", "1", "--slices", "2", "--no-session-guard", "--yes"],
            capsys=capsys,
        )
        assert len(agent.account_api.orders) == 2
        assert code is None


class FakeCreditAccountAPI(FakeAccountAPI):
    def __init__(self, credit_accepts=True):
        super().__init__()
        self.credit_buys = []
        self.credit_sells = []
        self.credit_accepts = credit_accepts

    def _resp(self, bucket):
        if self.credit_accepts:
            return {"rt_cd": "0", "msg1": "정상", "output": {"ODNO": f"C{len(bucket)}"}}
        return {"rt_cd": "1", "msg1": "신용융자 매수 불가"}

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
                "qty": qty,
                "credit_type": credit_type,
                "loan_dt": loan_dt,
                "order_type": order_type,
                "exchange": exchange,
            }
        )
        return self._resp(self.credit_buys)

    def order_credit_sell(self, pdno, qty, price, order_type="00", credit_type="11"):
        self.credit_sells.append({"qty": qty, "credit_type": credit_type})
        return self._resp(self.credit_sells)


def credit_cli_agent(credit_accepts=True):
    agent = FakeAgent()
    agent.account_api = FakeCreditAccountAPI(credit_accepts=credit_accepts)
    return agent


class TestCreditCli:
    def test_funding_defaults_to_cash(self):
        assert parse(BASE).funding == "cash"
        assert parse(BASE).credit_fallback is False

    def test_invalid_funding_is_rejected_by_the_parser(self):
        with pytest.raises(SystemExit):
            parse(BASE + ["--funding", "margin"])

    def test_credit_flag_routes_to_the_credit_endpoint(self, capsys):
        agent = credit_cli_agent()
        payload, agent, code = run_cli(
            BASE + ["--duration", "1", "--slices", "2", "--funding", "credit", "--yes"],
            agent=agent,
            capsys=capsys,
        )
        assert agent.account_api.orders == []
        assert [o["qty"] for o in agent.account_api.credit_buys] == [30, 30]
        assert payload["data"]["algoOrder"]["status"] == "completed"
        assert code is None

    def test_credit_type_and_loan_date_reach_the_api(self, capsys):
        agent = credit_cli_agent()
        _, agent, _ = run_cli(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "1",
                "--funding",
                "credit",
                "--credit-type",
                "22",
                "--loan-date",
                "20260821",
                "--yes",
            ],
            agent=agent,
            capsys=capsys,
        )
        order = agent.account_api.credit_buys[0]
        assert order["credit_type"] == "22"
        assert order["loan_dt"] == "20260821"

    def test_credit_sell_uses_the_repayment_endpoint(self, capsys):
        agent = credit_cli_agent()
        _, agent, _ = run_cli(
            [
                "order",
                "twap",
                "005930",
                "--side",
                "sell",
                "--qty",
                "30",
                "--duration",
                "1",
                "--slices",
                "1",
                "--funding",
                "credit",
                "--yes",
            ],
            agent=agent,
            capsys=capsys,
        )
        assert len(agent.account_api.credit_sells) == 1
        assert agent.account_api.credit_buys == []

    def test_fallback_flag_switches_to_cash_and_reports_it(self, capsys):
        agent = credit_cli_agent(credit_accepts=False)
        payload, agent, code = run_cli(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "2",
                "--funding",
                "credit",
                "--credit-fallback",
                "--yes",
            ],
            agent=agent,
            capsys=capsys,
        )
        assert [o["qty"] for o in agent.account_api.orders] == [30, 30]
        slices = payload["data"]["algoOrder"]["slices"]
        assert all("현금 폴백" in s["message"] for s in slices)
        assert code is None

    def test_without_fallback_a_rejected_credit_order_is_not_retried_as_cash(
        self, capsys
    ):
        agent = credit_cli_agent(credit_accepts=False)
        payload, agent, code = run_cli(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "2",
                "--funding",
                "credit",
                "--max-failures",
                "5",
                "--yes",
            ],
            agent=agent,
            capsys=capsys,
        )
        assert agent.account_api.orders == []
        assert payload["data"]["algoOrder"]["submittedQuantity"] == 0
        assert code == 2

    def test_prompt_shows_the_funding_source(self):
        agent = credit_cli_agent()
        args = parse(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "2",
                "--funding",
                "credit",
                "--credit-type",
                "21",
                "--credit-fallback",
            ]
        )
        captured = {}
        with patch("kis_agent.cli.main._create_agent", return_value=agent), patch(
            "kis_agent.cli.main._resolve", side_effect=lambda c: c
        ), patch(
            "kis_agent.cli.main._confirm_order",
            side_effect=lambda a, d: captured.update(d) or False,
        ):
            cmd_order(args)
        assert "신용주문" in captured["자금구분"]
        assert captured["신용 거부 시"] == "현금주문으로 폴백"

    def test_cash_prompt_says_cash(self):
        agent = credit_cli_agent()
        args = parse(BASE + ["--duration", "1", "--slices", "2"])
        captured = {}
        with patch("kis_agent.cli.main._create_agent", return_value=agent), patch(
            "kis_agent.cli.main._resolve", side_effect=lambda c: c
        ), patch(
            "kis_agent.cli.main._confirm_order",
            side_effect=lambda a, d: captured.update(d) or False,
        ):
            cmd_order(args)
        assert captured["자금구분"] == "현금주문"
        assert "신용 거부 시" not in captured


class TestVwapCliExecution:
    def test_vwap_runs_end_to_end_and_reports_the_fallback(self, capsys):
        # FakeStockAPI가 분봉을 비워 돌려주므로 균등 분할 폴백 경로를 탄다.
        payload, agent, code = run_cli(
            [
                "order",
                "vwap",
                "005930",
                "--side",
                "buy",
                "--qty",
                "60",
                "--duration",
                "1",
                "--slices",
                "3",
                "--profile-days",
                "1",
                "--yes",
            ],
            capsys=capsys,
        )
        assert [o["qty"] for o in agent.account_api.orders] == [20, 20, 20]
        algo = payload["data"]["algoOrder"]
        assert algo["algorithm"] == "vwap"
        assert any("균등 분할" in note for note in algo["notes"])
        assert code is None

    def test_progress_is_written_to_stderr_not_stdout(self, capsys):
        # run_cli에 capsys를 넘기지 않는다 — 헬퍼가 버퍼를 비워버린다.
        run_cli(BASE + ["--duration", "1", "--slices", "2", "--dry-run", "--yes"])
        captured = capsys.readouterr()
        # stdout은 LLM 파싱용 JSON 전용이어야 한다.
        assert captured.out.strip().startswith("{")
        assert "슬라이스 1" in captured.err


class TestUnexpectedFailure:
    def test_unexpected_exception_is_reported_as_json_and_exits_1(self, capsys):
        agent = FakeAgent()
        args = parse(BASE + ["--duration", "1", "--slices", "1", "--yes"])
        with patch("kis_agent.cli.main._create_agent", return_value=agent), patch(
            "kis_agent.cli.main._resolve", side_effect=lambda c: c
        ), patch(
            "kis_agent.execution.run_twap",
            side_effect=ConnectionError("upstream gone"),
        ):
            with pytest.raises(SystemExit) as exc:
                cmd_order(args)
        payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
        assert exc.value.code == 1
        assert payload["code"] == "ConnectionError"
        assert "upstream gone" in payload["error"]


class TestJournalCli:
    def test_result_reports_the_journal_location(self, capsys):
        payload, _, _ = run_cli(
            BASE + ["--duration", "1", "--slices", "2", "--yes"], capsys=capsys
        )
        algo = payload["data"]["algoOrder"]
        assert algo["runId"]
        assert algo["journalPath"].endswith(".jsonl")
        assert Path(algo["journalPath"]).exists()

    def test_progress_line_carries_the_order_number(self, capsys):
        run_cli(BASE + ["--duration", "1", "--slices", "2", "--yes"])
        err = capsys.readouterr().err
        # 원장이 실패해도 스크롤백에는 남아야 한다.
        assert "주문번호 A1" in err

    def test_no_journal_flag_disables_recording(self, capsys):
        payload, _, _ = run_cli(
            BASE + ["--duration", "1", "--slices", "2", "--no-journal", "--yes"],
            capsys=capsys,
        )
        assert payload["data"]["algoOrder"]["journalPath"] == ""

    def test_journal_dir_override(self, tmp_path, capsys):
        payload, _, _ = run_cli(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "1",
                "--journal-dir",
                str(tmp_path / "custom"),
                "--yes",
            ],
            capsys=capsys,
        )
        assert str(tmp_path / "custom") in payload["data"]["algoOrder"]["journalPath"]


class TestIncompleteRunGuard:
    def _crash_a_run(self, journal_dir, code="005930"):
        """주문을 낸 뒤 죽은 실행을 흉내낸다 (end 레코드 없음)."""
        from kis_agent.execution.journal import ExecutionJournal

        j = ExecutionJournal.create(code, "buy", base_dir=Path(journal_dir))
        j.record_start(
            {"code": code, "side": "buy", "totalQuantity": 100, "dryRun": False}
        )
        j.record_slice(
            {"index": 0, "quantity": 30, "status": "filled", "orderNo": "LIVE-1"}
        )
        return j

    def test_incomplete_run_blocks_a_new_execution(self, tmp_path, capsys):
        self._crash_a_run(tmp_path)
        payload, agent, code = run_cli(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "2",
                "--journal-dir",
                str(tmp_path),
                "--yes",
            ],
            capsys=capsys,
        )
        assert agent.account_api.orders == []  # 중복 집행을 막았다
        assert code == 1
        assert payload["code"] == "IncompleteExecutionFound"
        runs = payload["data"]["incompleteRuns"]
        assert runs[0]["orderNumbers"] == ["LIVE-1"]
        assert runs[0]["submittedQuantity"] == 30

    def test_override_flag_allows_proceeding(self, tmp_path, capsys):
        self._crash_a_run(tmp_path)
        _, agent, code = run_cli(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "2",
                "--journal-dir",
                str(tmp_path),
                "--ignore-incomplete",
                "--yes",
            ],
            capsys=capsys,
        )
        assert len(agent.account_api.orders) == 2
        assert code is None

    def test_dry_run_is_not_blocked(self, tmp_path, capsys):
        self._crash_a_run(tmp_path)
        payload, _, code = run_cli(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "2",
                "--journal-dir",
                str(tmp_path),
                "--dry-run",
                "--yes",
            ],
            capsys=capsys,
        )
        # 모의 실행은 거래소에 닿지 않으므로 막을 이유가 없다.
        assert payload["data"]["algoOrder"]["dryRun"] is True
        assert code is None

    def test_a_different_ticker_is_not_blocked(self, tmp_path, capsys):
        self._crash_a_run(tmp_path, code="000660")
        _, agent, code = run_cli(
            BASE
            + [
                "--duration",
                "1",
                "--slices",
                "1",
                "--journal-dir",
                str(tmp_path),
                "--yes",
            ],
            capsys=capsys,
        )
        assert len(agent.account_api.orders) == 1
        assert code is None
