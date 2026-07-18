"""InvestorPositionDB의 조회, 필터 및 실패 경로 회귀 테스트."""

import sqlite3
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import kis_agent.stock.investor_db as investor_db
from kis_agent.stock.investor_db import InvestorPositionDB, InvestorPositionRecord


def test_default_path_and_position_by_date(tmp_path, monkeypatch):
    fake_os = SimpleNamespace(
        makedirs=lambda *args, **kwargs: None,
        path=SimpleNamespace(join=lambda *parts: str(tmp_path / parts[-1])),
    )
    monkeypatch.setattr(investor_db, "os", fake_os)
    default_db = InvestorPositionDB()
    assert default_db.db_path.endswith("investor_positions.db")

    monkeypatch.setattr(investor_db, "os", __import__("os"))

    db = InvestorPositionDB(str(tmp_path / "positions.db"))
    record = InvestorPositionRecord("005930", "20250102", foreign_net_vol=9)
    assert db.save_daily_position(record)
    assert db.get_position_by_date("005930", "20250102").foreign_net_vol == 9
    assert db.get_position_by_date("005930", "20250103") is None
    assert db.export_data("005930", "20250101", "20250102")


def test_database_error_fallbacks(tmp_path):
    db = InvestorPositionDB(str(tmp_path / "positions.db"))
    with patch("kis_agent.stock.investor_db.sqlite3.connect", side_effect=sqlite3.Error("offline")):
        assert db.get_30day_positions("005930") == []
        assert db.get_position_by_date("005930", "20250101") is None
        assert not db.save_market_trend("20250101", "KOSPI", {})
        assert db.get_market_summary("20250101") == {}
        assert not db.cleanup_old_data()
        assert db.get_database_stats() == {}
        assert db.export_data() == []


def test_backup_default_and_error_paths(tmp_path):
    db = InvestorPositionDB(str(tmp_path / "positions.db"))
    assert db.backup_database(str(tmp_path / "copy.db"))
    with patch("shutil.copy2", side_effect=OSError("full")):
        assert not db.backup_database(str(tmp_path / "bad.db"))


def test_initialize_failure_and_default_backup_name(tmp_path):
    db = object.__new__(InvestorPositionDB)
    db.db_path = str(tmp_path / "broken.db")
    db.logger = MagicMock()
    with patch("kis_agent.stock.investor_db.sqlite3.connect", side_effect=sqlite3.Error("broken")):
        try:
            db._initialize_database()
        except sqlite3.Error:
            pass
        else:
            raise AssertionError("sqlite error must propagate")
    normal = InvestorPositionDB(str(tmp_path / "positions.db"))
    assert normal.backup_database()
