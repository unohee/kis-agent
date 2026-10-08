"""Regression tests for the CodeQL audit of 2026-10-08 (real defects only).

- py/clear-text-logging-sensitive-data: verbose request logging printed the
  access token and app key/secret.
- py/call/wrong-named-class-argument: the legacy KisWebSocket built
  AccountAPI(auth=...), a TypeError at runtime.
- py/uninitialized-local-variable: auth()/changeTREnv() with an unknown svr
  crashed with UnboundLocalError instead of a clear error.
"""

import importlib
import logging
from unittest.mock import MagicMock

import pytest

import kis_agent.core.client as client_module

auth_module = importlib.import_module("kis_agent.core.auth")


def test_redact_headers_masks_credentials_only():
    headers = {
        "authorization": "Bearer secret-token",
        "appkey": "key",
        "AppSecret": "secret",
        "approval_key": "ws-key",
        "tr_id": "FHKST01010100",
    }
    redacted = client_module._redact_headers(headers)
    assert redacted == {
        "authorization": "***",
        "appkey": "***",
        "AppSecret": "***",
        "approval_key": "***",
        "tr_id": "FHKST01010100",
    }
    assert headers["authorization"] == "Bearer secret-token"  # original untouched


def test_verbose_request_log_does_not_contain_the_token(caplog, monkeypatch):
    client = object.__new__(client_module.KISClient)
    client.verbose = True
    client.is_real = True
    client.base_url = "https://example.test"
    client._check_and_refresh_token = lambda: None
    client._auth_headers = lambda: {
        "authorization": "Bearer secret-token",
        "appkey": "k",
        "appsecret": "s",
    }
    response = MagicMock(status_code=200, headers={})
    response.json.return_value = {"rt_cd": "0"}
    monkeypatch.setattr(client_module.httpx, "request", lambda *a, **k: response)
    with caplog.at_level(logging.DEBUG, logger=client_module.logger.name):
        try:
            client.make_request("/uapi/x", "FHKST01010100", params={"A": "1"})
        except (
            Exception
        ):  # partial construction may fail later; the log line comes first
            pass
    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert "요청 헤더" in logged
    assert "secret-token" not in logged
    assert "'appsecret': 's'" not in logged


def test_legacy_websocket_builds_account_api_with_account_info(monkeypatch):
    from kis_agent.websocket import client as legacy

    seen = {}

    class StrictAccountAPI:
        def __init__(
            self,
            client,
            account_info,
            enable_cache=True,
            cache_config=None,
            _from_agent=False,
        ):
            seen["account_info"] = account_info
            raise RuntimeError("stop")

    monkeypatch.setattr("kis_agent.account.api.AccountAPI", StrictAccountAPI)
    ws = object.__new__(legacy.KisWebSocket)
    ws.client = MagicMock()
    ws.account_info = {"CANO": "1", "ACNT_PRDT_CD": "01"}
    import asyncio

    with pytest.raises(RuntimeError, match="stop"):
        asyncio.run(ws.update_holdings_loop())
    assert seen["account_info"] == {"CANO": "1", "ACNT_PRDT_CD": "01"}


@pytest.mark.parametrize(
    "call",
    [
        lambda: auth_module.auth(svr="bad"),
        lambda: auth_module.changeTREnv("t", svr="bad"),
    ],
)
def test_unknown_server_type_is_a_clear_error(call):
    with pytest.raises(ValueError, match="svr"):
        call()
