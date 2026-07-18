"""auth 모듈의 파일 불일치와 환경 분기 회귀 테스트."""

import builtins
import hashlib
import importlib
import json
import runpy
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

auth = importlib.import_module("kis_agent.core.auth")


def test_read_token_hash_prefix_and_missing_file(tmp_path):
    hashed = tmp_path / "token.json"
    app_key = "abcdefgh123"
    path = auth._get_token_path_for_app_key(app_key, str(hashed))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"token": "x", "valid-date": "2099-01-01T00:00:00", "app_key_hash": "wrong"}, handle)
    assert auth.read_token(str(hashed), app_key) is None
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"token": "x", "valid-date": "2099-01-01T00:00:00", "app_key_prefix": "wrong"}, handle)
    assert auth.read_token(str(hashed), app_key) is None
    with patch("builtins.open", side_effect=FileNotFoundError("gone")):
        assert auth.read_token(str(tmp_path / "missing.json")) is None


def test_environment_branches_and_auth_failure(monkeypatch):
    original = auth._cfg.copy()
    original_paper, original_env = auth._isPaper, auth._TRENV
    try:
        auth._cfg.update({"my_acct_future": "F", "my_paper_stock": "P", "my_paper_future": "PF", "paper_app": "paper", "paper_sec": "secret"})
        auth.changeTREnv("token", "prod", "03")
        assert auth.getTREnv().my_acct == "F"
        auth.changeTREnv("token", "vps", "01")
        assert auth.isPaperTrading() and auth.getTREnv().my_acct == "P"
        auth.changeTREnv("token", "vps", "03")
        assert auth.getTREnv().my_acct == "PF"
        monkeypatch.setattr(auth, "read_token", lambda **kwargs: None)
        monkeypatch.setattr(auth.requests, "post", lambda *args, **kwargs: SimpleNamespace(status_code=500, text="bad"))
        with __import__("pytest").raises(RuntimeError):
            auth.auth(svr="vps", product="01")
        monkeypatch.setattr(auth, "read_token", lambda **kwargs: {"access_token": "cached", "access_token_token_expired": "2099-01-01 00:00:00"})
        assert auth.reAuth(svr="vps")["access_token"] == "cached"
    finally:
        auth._cfg.clear()
        auth._cfg.update(original)
        auth._isPaper, auth._TRENV = original_paper, original_env


def test_require_aiohttp_reports_installation_guidance(monkeypatch):
    real_import = builtins.__import__

    def fail_aiohttp(name, *args, **kwargs):
        if name == "aiohttp":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_aiohttp)
    with pytest.raises(ImportError, match="aiohttp is not installed"):
        auth._require_aiohttp()


def test_read_token_caches_valid_app_specific_file(tmp_path):
    app_key = "abcdefgh123"
    base_path = tmp_path / "token.json"
    path = auth._get_token_path_for_app_key(app_key, str(base_path))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "token": "cached-token", "valid-date": "2099-01-01T00:00:00",
                "app_key_hash": hashlib.sha256(app_key.encode()).hexdigest()[:16],
            },
            handle,
        )
    auth._token_cache.clear()
    assert auth.read_token(str(base_path), app_key)["access_token"] == "cached-token"
    assert len(auth._token_cache) == 1


def test_module_initialization_loads_dotenv_and_creates_token_file(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("KIS_APP_KEY=test\n", encoding="utf-8")
    token_path = tmp_path / "new-token.json"
    monkeypatch.setenv("KIS_TOKEN_PATH", str(token_path))
    with patch("dotenv.load_dotenv") as load:
        runpy.run_module("kis_agent.core.auth", run_name="kis_agent.core._auth_coverage")
    load.assert_called_once_with(dotenv_path=str(tmp_path / ".env"), override=False)
    assert json.loads(token_path.read_text(encoding="utf-8")) == {}


def test_read_token_direct_format_invalid_format_and_open_race(tmp_path):
    path = tmp_path / "token.json"
    path.write_text(json.dumps({"access_token": "direct"}), encoding="utf-8")
    assert auth.read_token(str(path)) == {"access_token": "direct"}
    path.write_text(json.dumps({"unexpected": True}), encoding="utf-8")
    assert auth.read_token(str(path)) is None

    with patch.object(auth.os.path, "exists", return_value=True), patch(
        "builtins.open", side_effect=FileNotFoundError("raced")
    ):
        assert auth.read_token(str(path)) is None


def test_auth_with_config_issues_and_reuses_token(monkeypatch):
    config = SimpleNamespace(
        APP_KEY="app",
        APP_SECRET="secret",
        ACCOUNT_NO="12345678",
        ACCOUNT_CODE="01",
        BASE_URL="https://example.test",
    )
    original_cfg = auth._cfg.copy()
    original_env = auth._TRENV
    original_headers = auth._base_headers.copy()
    response = SimpleNamespace(
        status_code=200,
        json=lambda: {
            "access_token": "issued",
            "access_token_token_expired": "2099-01-01 00:00:00",
        },
        text="ok",
    )
    try:
        monkeypatch.setattr(auth, "read_token", MagicMock(return_value=None))
        monkeypatch.setattr(auth.requests, "post", MagicMock(return_value=response))
        monkeypatch.setattr(auth, "save_token", MagicMock())
        issued = auth.auth(config=config)
        assert issued["access_token"] == "issued"
        auth.save_token.assert_called_once_with(
            "issued", "2099-01-01 00:00:00", app_key="app"
        )
        assert auth.getTREnv().my_url == "https://example.test"

        auth.read_token.return_value = {"access_token": "cached"}
        cached = auth.auth(config=config, product="01")
        assert cached["access_token"] == "cached"
        assert cached["access_token_token_expired"]
    finally:
        auth._cfg.clear()
        auth._cfg.update(original_cfg)
        auth._TRENV = original_env
        auth._base_headers.clear()
        auth._base_headers.update(original_headers)


def test_api_response_exposes_original_response():
    response = SimpleNamespace(status_code=500, headers={})
    assert auth.APIResp(response).getResponse() is response


def test_auth_uses_global_product_and_debug_output(monkeypatch, capsys):
    original_env = auth._TRENV
    original_debug = auth._DEBUG
    original_headers = auth._base_headers.copy()
    try:
        monkeypatch.setattr(
            auth,
            "read_token",
            lambda **_kwargs: {
                "access_token": "cached",
                "access_token_token_expired": "2099-01-01 00:00:00",
            },
        )
        auth._DEBUG = True
        result = auth.auth(config=None, svr="prod", product=None)
        assert result["access_token"] == "cached"
        assert "get AUTH Key completed" in capsys.readouterr().out
    finally:
        auth._TRENV = original_env
        auth._DEBUG = original_debug
        auth._base_headers.clear()
        auth._base_headers.update(original_headers)
