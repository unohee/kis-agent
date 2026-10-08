"""접근토큰폐기(P) [인증-002] — KISClient.revoke_token and auth.forget_token."""

import hashlib
import importlib
import json
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import kis_agent.core.client as client_module
from kis_agent.core.client import KISClient

# kis_agent.core re-exports the function `auth`, which shadows the submodule name.
auth_module = importlib.import_module("kis_agent.core.auth")


def _client(token="tok"):
    client = object.__new__(KISClient)
    client.base_url = "https://example.test"
    client.config = SimpleNamespace(APP_KEY="app-key", APP_SECRET="app-secret")
    client.token = token
    client.token_expired = "2099-01-01 00:00:00"
    client.token_refresh_lock = threading.Lock()
    return client


def _response(status, payload=None, bad_json=False):
    response = MagicMock(status_code=status)
    if bad_json:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = payload or {}
    return response


def test_revoke_posts_spec_body_and_forgets_the_token():
    client = _client()
    with patch.object(client_module.requests, "post", return_value=_response(200, {"code": 200, "message": "ok"})) as post, patch.object(
        client_module, "forget_token"
    ) as forget:
        assert client.revoke_token() == {"code": 200, "message": "ok"}
    post.assert_called_once_with(
        "https://example.test/oauth2/revokeP",
        json={"appkey": "app-key", "appsecret": "app-secret", "token": "tok"},
        headers={"content-type": "application/json"},
        timeout=10,
    )
    forget.assert_called_once_with("app-key")
    assert client.token is None and client.token_expired is None


@pytest.mark.parametrize("bad_json", [False, True])
def test_revoke_failure_keeps_the_token(bad_json):
    client = _client()
    with patch.object(
        client_module.requests, "post", return_value=_response(403, {"message": "denied"}, bad_json)
    ), patch.object(client_module, "forget_token") as forget, pytest.raises(Exception, match="HTTP 403"):
        client.revoke_token()
    forget.assert_not_called()
    assert client.token == "tok"


def test_revoke_requires_credentials_and_a_token():
    with pytest.raises(ValueError, match="APP_KEY"):
        client = _client()
        client.config = None
        client.revoke_token()
    with pytest.raises(ValueError, match="접근토큰"):
        _client(token=None).revoke_token()


def test_forget_token_clears_memory_and_file(tmp_path):
    base = tmp_path / "KIS_Token.json"
    key_hash = hashlib.sha256(b"app-key").hexdigest()[:16]
    token_file = tmp_path / f"KIS_Token_{key_hash}.json"
    token_file.write_text(json.dumps({"token": "tok"}), encoding="utf-8")
    auth_module._token_cache[key_hash] = {"access_token": "tok"}

    auth_module.forget_token("app-key", str(base))

    assert key_hash not in auth_module._token_cache
    assert json.loads(token_file.read_text(encoding="utf-8")) == {}

    auth_module.forget_token("", str(base))  # no app key: nothing to do
    auth_module.forget_token("other-key", str(base))  # no file: nothing to do
