"""집행 원장 테스트 (STO-1730).

핵심 계약은 하나다: **프로세스가 어떻게 죽든 이미 나간 주문번호는 디스크에 있다.**
"""

import json
import signal
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

import pytest

from kis_agent.execution.journal import (
    EVENT_END,
    EVENT_SLICE,
    EVENT_START,
    ExecutionJournal,
    default_journal_dir,
    find_incomplete_runs,
    make_run_id,
    read_journal,
)

NOW = datetime(2026, 8, 21, 13, 30)


class TestRunId:
    def test_is_chronologically_sortable(self):
        early = make_run_id("005930", "buy", datetime(2026, 8, 21, 9, 0))
        late = make_run_id("005930", "buy", datetime(2026, 8, 21, 15, 0))
        assert early < late

    def test_carries_code_and_side(self):
        rid = make_run_id("005930", "SELL", NOW)
        assert "005930" in rid and "sell" in rid

    def test_two_runs_in_the_same_second_do_not_collide(self):
        a = make_run_id("005930", "buy", NOW)
        b = make_run_id("005930", "buy", NOW)
        assert a != b


class TestDefaultDir:
    def test_env_override_wins(self, monkeypatch, tmp_path):
        monkeypatch.setenv("KIS_EXECUTION_JOURNAL_DIR", str(tmp_path / "jrnl"))
        assert default_journal_dir() == tmp_path / "jrnl"

    def test_falls_back_to_home(self, monkeypatch):
        monkeypatch.delenv("KIS_EXECUTION_JOURNAL_DIR", raising=False)
        assert default_journal_dir() == Path.home() / ".kis-agent" / "executions"

    def test_tilde_in_override_is_expanded(self, monkeypatch):
        monkeypatch.setenv("KIS_EXECUTION_JOURNAL_DIR", "~/somewhere")
        assert default_journal_dir() == Path.home() / "somewhere"


class TestWriting:
    def test_file_lands_under_a_date_directory(self, tmp_path):
        j = ExecutionJournal.create("005930", "buy", base_dir=tmp_path, now=NOW)
        assert j.path.parent.name == "20260821"
        assert j.path.suffix == ".jsonl"

    def test_events_are_appended_in_order(self, tmp_path):
        j = ExecutionJournal.create("005930", "buy", base_dir=tmp_path, now=NOW)
        j.record_start({"code": "005930", "totalQuantity": 100})
        j.record_slice({"index": 0, "quantity": 50, "orderNo": "A1"})
        j.record_end({"status": "completed"})

        events = read_journal(j.path)
        assert [e["event"] for e in events] == [EVENT_START, EVENT_SLICE, EVENT_END]
        assert all(e["runId"] == j.run_id for e in events)
        assert events[1]["orderNo"] == "A1"

    def test_each_record_is_flushed_immediately(self, tmp_path):
        """다음 record를 기다리지 않고 즉시 읽을 수 있어야 한다."""
        j = ExecutionJournal.create("005930", "buy", base_dir=tmp_path, now=NOW)
        j.record_slice({"index": 0, "orderNo": "A1"})
        assert len(read_journal(j.path)) == 1

    def test_unwritable_journal_does_not_raise(self, tmp_path):
        # 디스크가 차서 원장을 못 써도 진행 중인 주문을 중단시켜서는 안 된다.
        j = ExecutionJournal(path=tmp_path / "nope" / "deep" / "x.jsonl", run_id="R")
        j.record_slice({"index": 0})  # 예외가 나면 실패

    def test_non_serialisable_payload_falls_back_to_str(self, tmp_path):
        j = ExecutionJournal.create("005930", "buy", base_dir=tmp_path, now=NOW)
        j.record_slice({"when": datetime(2026, 8, 21, 10, 0)})
        assert "2026-08-21" in read_journal(j.path)[0]["when"]


class TestReading:
    def test_missing_file_reads_as_empty(self, tmp_path):
        assert read_journal(tmp_path / "absent.jsonl") == []

    def test_torn_final_line_does_not_lose_earlier_records(self, tmp_path):
        path = tmp_path / "torn.jsonl"
        good = json.dumps({"event": "slice", "orderNo": "A1"})
        path.write_text(good + '\n{"event": "slice", "orderN', encoding="utf-8")
        events = read_journal(path)
        # SIGKILL이 마지막 줄을 자르더라도 그 앞은 온전해야 한다.
        assert len(events) == 1
        assert events[0]["orderNo"] == "A1"

    def test_blank_lines_are_skipped(self, tmp_path):
        path = tmp_path / "blanks.jsonl"
        path.write_text('\n{"event": "start"}\n\n', encoding="utf-8")
        assert len(read_journal(path)) == 1


class TestIncompleteRuns:
    def _write(self, tmp_path, *, code, closed, dry_run=False, orders=("A1",)):
        j = ExecutionJournal.create(code, "buy", base_dir=tmp_path, now=NOW)
        j.record_start(
            {"code": code, "side": "buy", "totalQuantity": 100, "dryRun": dry_run}
        )
        for i, no in enumerate(orders):
            j.record_slice(
                {"index": i, "quantity": 30, "status": "filled", "orderNo": no}
            )
        if closed:
            j.record_end({"status": "completed"})
        return j

    def test_unclosed_run_is_reported(self, tmp_path):
        self._write(tmp_path, code="005930", closed=False)
        found = find_incomplete_runs("005930", base_dir=tmp_path, now=NOW)
        assert len(found) == 1
        assert found[0].order_numbers == ["A1"]
        assert found[0].submitted_quantity == 30
        assert found[0].total_quantity == 100

    def test_closed_run_is_not_reported(self, tmp_path):
        self._write(tmp_path, code="005930", closed=True)
        assert find_incomplete_runs("005930", base_dir=tmp_path, now=NOW) == []

    def test_dry_run_is_never_reported(self, tmp_path):
        # 모의 실행은 거래소에 닿지 않았으므로 대사할 것이 없다.
        self._write(tmp_path, code="005930", closed=False, dry_run=True)
        assert find_incomplete_runs("005930", base_dir=tmp_path, now=NOW) == []

    def test_other_tickers_are_ignored(self, tmp_path):
        self._write(tmp_path, code="000660", closed=False)
        assert find_incomplete_runs("005930", base_dir=tmp_path, now=NOW) == []

    def test_missing_directory_reads_as_empty(self, tmp_path):
        assert find_incomplete_runs("005930", base_dir=tmp_path / "nope", now=NOW) == []

    def test_empty_journal_is_skipped(self, tmp_path):
        directory = tmp_path / "20260821"
        directory.mkdir(parents=True)
        (directory / "empty.jsonl").write_text("", encoding="utf-8")
        assert find_incomplete_runs("005930", base_dir=tmp_path, now=NOW) == []

    def test_describe_names_the_order_numbers(self, tmp_path):
        self._write(tmp_path, code="005930", closed=False, orders=("A1", "A2"))
        summary = find_incomplete_runs("005930", base_dir=tmp_path, now=NOW)[0].describe()
        assert "A1" in summary and "A2" in summary
        assert "60/100주" in summary

    def test_run_with_no_orders_reports_none(self, tmp_path):
        self._write(tmp_path, code="005930", closed=False, orders=())
        found = find_incomplete_runs("005930", base_dir=tmp_path, now=NOW)
        assert found[0].submitted_quantity == 0
        assert "없음" in found[0].describe()


class TestSurvivesSigkill:
    """이 모듈의 존재 이유를 직접 증명한다."""

    def test_order_numbers_survive_an_unhandled_kill(self, tmp_path):
        script = textwrap.dedent(
            f"""
            import os, signal, sys
            sys.path.insert(0, {str(Path(__file__).resolve().parents[2])!r})
            from datetime import datetime
            from pathlib import Path
            from kis_agent.execution.journal import ExecutionJournal

            j = ExecutionJournal.create(
                "005930", "buy",
                base_dir=Path({str(tmp_path)!r}),
                now=datetime(2026, 8, 21, 13, 30),
                run_id="killrun",
            )
            j.record_start({{"code": "005930", "side": "buy", "totalQuantity": 100}})
            j.record_slice({{"index": 0, "quantity": 50, "status": "filled",
                            "orderNo": "LIVE-0001"}})
            # 핸들러가 없는 즉사. finally도, atexit도 돌지 않는다.
            os.kill(os.getpid(), signal.SIGKILL)
            """
        )
        proc = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, timeout=60
        )
        assert proc.returncode == -signal.SIGKILL

        journal = tmp_path / "20260821" / "killrun.jsonl"
        events = read_journal(journal)
        order_numbers = [e.get("orderNo") for e in events if e.get("orderNo")]
        # 프로세스는 죽었지만 나간 주문은 디스크에 남아야 한다.
        assert order_numbers == ["LIVE-0001"]
        assert not any(e["event"] == EVENT_END for e in events)

        # 그리고 그 기록이 다음 실행을 막아야 한다.
        found = find_incomplete_runs("005930", base_dir=tmp_path, now=NOW)
        assert found[0].order_numbers == ["LIVE-0001"]
