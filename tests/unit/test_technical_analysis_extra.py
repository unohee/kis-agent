"""TechnicalAnalysisMixin의 예외·캐시·CSV 이관 회귀 테스트."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from kis_agent.core.technical_analysis import TechnicalAnalysisMixin


class _Agent(TechnicalAnalysisMixin):
    def __init__(self):
        self.stock_api = MagicMock()
        self.is_holiday = MagicMock(return_value=False)


def test_init_migrate_and_business_day_fallbacks(tmp_path, monkeypatch):
    agent = _Agent()
    assert agent.init_minute_db(str(tmp_path / "minute.db"))
    with patch("kis_agent.core.technical_analysis.sqlite3.connect", side_effect=RuntimeError("db")):
        assert not agent.init_minute_db("bad")
    monkeypatch.chdir(tmp_path)
    assert agent.migrate_minute_csv_to_db("005930")
    Path("cache").mkdir()
    Path("cache/005930_minute_data.csv").write_text("stck_prpr\n", encoding="utf-8")
    assert agent.migrate_minute_csv_to_db("005930")
    pd.DataFrame({"stck_prpr": [1]}).to_csv("cache/005930_minute_data.csv", index=False)
    assert agent.migrate_minute_csv_to_db("005930", str(tmp_path / "minute.db"))
    assert not Path("cache/005930_minute_data.csv").exists()
    Path("cache/005930_minute_data.csv").write_text("bad\n\"", encoding="utf-8")
    assert not agent.migrate_minute_csv_to_db("005930")
    agent.is_holiday.side_effect = RuntimeError("offline")
    assert agent._get_last_business_day("20250106") == "20250106"
    agent.is_holiday.side_effect = lambda _: True
    assert agent._get_last_business_day("20250106") == "20250106"


def test_fetch_cache_and_db_failure_paths(tmp_path, monkeypatch):
    agent = _Agent()
    now = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    path = tmp_path / "today.csv"
    pd.DataFrame({"x": [1]}).to_csv(path, index=False)
    monkeypatch.setattr("kis_agent.core.technical_analysis.datetime", MagicMock(now=MagicMock(return_value=now), fromtimestamp=datetime.fromtimestamp, strptime=datetime.strptime))
    # 파일 생성 시각과 고정된 테스트 시각의 날짜/시간 차이에 의존하지 않도록
    # 유효 캐시와 만료 캐시의 mtime을 모두 명시적으로 설정한다.
    import os
    os.utime(path, (now.timestamp(), now.timestamp()))
    assert agent._check_cache(str(path), now.strftime("%Y%m%d"), now) is not None
    old = now - timedelta(hours=1)
    os.utime(path, (old.timestamp(), old.timestamp()))
    assert agent._check_cache(str(path), now.strftime("%Y%m%d"), now) is None
    agent.stock_api.get_intraday_price.return_value = {"rt_cd": "0", "output2": []}
    assert agent.fetch_minute_data("005930", "20250101", str(tmp_path)).empty
    with patch("kis_agent.core.technical_analysis.sqlite3.connect", side_effect=RuntimeError("db")):
        agent._save_to_db(pd.DataFrame({"x": [1]}), "005930", "20250101")


def test_default_date_fetch_cache_modes_and_db_save(tmp_path, monkeypatch):
    agent = _Agent()
    now = datetime(2025, 1, 6, 10, 0, 0)
    fake_datetime = MagicMock(now=MagicMock(return_value=now), fromtimestamp=datetime.fromtimestamp, strptime=datetime.strptime)
    monkeypatch.setattr("kis_agent.core.technical_analysis.datetime", fake_datetime)
    agent._get_last_business_day = MagicMock(side_effect=["20250106", "20250103"])
    agent.stock_api.get_intraday_price.return_value = {"rt_cd": "0", "output2": []}
    assert agent.fetch_minute_data("005930", cache_dir=str(tmp_path)).empty
    assert agent._get_last_business_day.call_count == 2

    path = tmp_path / "bad.csv"
    path.write_text("bad\n\"", encoding="utf-8")
    assert agent._check_cache(str(path), "20250101", now) is None

    conn = MagicMock()
    with patch("kis_agent.core.technical_analysis.sqlite3.connect", return_value=conn), patch.object(pd.DataFrame, "to_sql") as to_sql:
        agent._save_to_db(pd.DataFrame({"x": [1]}), "005930", "20250101")
    conn.execute.assert_called_once()
    conn.close.assert_called_once()
    to_sql.assert_called_once()


def test_premarket_default_and_after_hours_cache(tmp_path, monkeypatch):
    agent = _Agent()
    now = datetime(2025, 1, 6, 8, 0, 0)
    monkeypatch.setattr("kis_agent.core.technical_analysis.datetime", MagicMock(now=MagicMock(return_value=now), fromtimestamp=datetime.fromtimestamp, strptime=datetime.strptime))
    agent._get_last_business_day = MagicMock(return_value="20250103")
    agent.stock_api.get_intraday_price.return_value = {"rt_cd": "0", "output2": []}
    assert agent.fetch_minute_data("005930", cache_dir=str(tmp_path)).empty

    import os
    path = tmp_path / "same-day.csv"
    pd.DataFrame({"x": [1]}).to_csv(path, index=False)
    evening = datetime(2025, 1, 6, 18, 0, 0)
    os.utime(path, (evening.timestamp(), evening.timestamp()))
    assert agent._check_cache(str(path), "20250106", evening) is not None
