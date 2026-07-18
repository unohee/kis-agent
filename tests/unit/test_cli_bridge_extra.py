"""CLI bridge 환경 점검과 main 입출력 경로 테스트."""

import io
import runpy
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

import kis_agent.cli_bridge as bridge


def test_python_installation_and_load_env(tmp_path, monkeypatch):
    run = MagicMock(side_effect=[FileNotFoundError(), MagicMock(returncode=0)])
    monkeypatch.setattr(bridge.subprocess, "run", run)
    assert bridge.check_python_installation() == (True, "python")
    monkeypatch.setattr(bridge.subprocess, "run", MagicMock(side_effect=bridge.subprocess.TimeoutExpired("python", 1)))
    assert bridge.check_python_installation() == (False, None)
    monkeypatch.chdir(tmp_path)
    with patch("dotenv.load_dotenv") as load:
        bridge.load_env()
        load.assert_not_called()
        (tmp_path / ".env").write_text("X=1")
        bridge.load_env()
        load.assert_called_once_with(".env", override=False)


def test_main_not_installed_initialization_failure_and_line_loop(monkeypatch, capsys):
    monkeypatch.setattr(bridge, "setup_logging", lambda: None)
    monkeypatch.setattr(bridge, "check_python_installation", lambda: (False, None))
    with pytest.raises(SystemExit):
        bridge.main()
    assert "PythonNotFound" in capsys.readouterr().out

    monkeypatch.setattr(bridge, "check_python_installation", lambda: (True, "python"))
    monkeypatch.setattr(bridge, "create_agent", lambda: (_ for _ in ()).throw(RuntimeError("bad init")))
    with pytest.raises(SystemExit):
        bridge.main()
    assert "RuntimeError" in capsys.readouterr().out

    agent = MagicMock()
    monkeypatch.setattr(bridge, "create_agent", lambda: agent)
    monkeypatch.setattr(bridge, "check_market_status", lambda _: None)
    monkeypatch.setattr(bridge.sys, "stdin", io.StringIO("\nfirst\nsecond\n"))
    monkeypatch.setattr(bridge, "handle_request", MagicMock(side_effect=["{\"ok\": 1}", RuntimeError("boom")]))
    bridge.main()
    output = capsys.readouterr().out
    assert '"ok": 1' in output and "Unexpected error" in output


def test_logging_market_holiday_and_timeout_format(monkeypatch):
    with patch.object(bridge.logging, "basicConfig") as config:
        bridge.setup_logging()
    config.assert_called_once()

    saturday = datetime(2025, 1, 4, 10, 0, 0)
    monkeypatch.setattr(bridge, "datetime", MagicMock(now=MagicMock(return_value=saturday)))
    bridge._market_status.update({"checked": False, "notice": None, "last_business_day": None})
    agent = MagicMock()
    agent.stock_api.is_holiday.side_effect = [True, False]
    bridge.check_market_status(agent)
    assert bridge._market_status["last_business_day"] == "20250103"

    bridge._market_status.update({"checked": False, "notice": None, "last_business_day": None})
    morning = datetime(2025, 1, 6, 8, 0, 0)
    monkeypatch.setattr(bridge, "datetime", MagicMock(now=MagicMock(return_value=morning)))
    agent.stock_api.is_holiday.return_value = False
    bridge.check_market_status(agent)
    assert "장 시작 전" in bridge._market_status["notice"]
    assert bridge._format_timeout_error(1000).endswith("1 second")
    assert bridge._format_timeout_error(2000).endswith("2 seconds")


def test_module_entrypoint_invokes_main(monkeypatch):
    monkeypatch.setattr(bridge.subprocess, "run", MagicMock(side_effect=FileNotFoundError()))
    with pytest.raises(SystemExit):
        runpy.run_path(bridge.__file__, run_name="__main__")
