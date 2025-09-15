import pytest


class DummyClient:
    """외부 주입용 더미 클라이언트 (네트워크 호출 방지용)."""
    pass


class DummyKISClient:
    """Agent 내부 생성 경로 대체용 더미 KISClient (네트워크 호출 방지)."""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


@pytest.fixture
def agent_module(monkeypatch):
    import pykis.core.agent as agent_mod
    # 내부에서 생성되는 KISClient를 더미로 대체하여 auth 호출 제거
    monkeypatch.setattr(agent_mod, "KISClient", DummyKISClient)
    return agent_mod


def test_ensure_valid_token_skips_when_external_client_provided(agent_module, caplog, monkeypatch):
    # read_token/auth가 호출되지 않아야 함
    called = {"read": False, "auth": False}

    def fake_read():
        called["read"] = True
        return {"access_token": "dummy"}

    def fake_auth(**kwargs):
        called["auth"] = True
        return {"access_token": "dummy", "access_token_token_expired": "2099-01-01 00:00:00"}

    monkeypatch.setattr(agent_module, "read_token", fake_read)
    monkeypatch.setattr(agent_module, "auth", fake_auth)

    Agent = agent_module.Agent

    caplog.set_level("INFO")
    # 외부 클라이언트를 주입하면 config=None로 전달되어 토큰 검증을 생략해야 함
    Agent(
        app_key="k",
        app_secret="s",
        account_no="12345678",
        account_code="01",
        client=DummyClient(),
    )

    # read_token/auth가 호출되지 않았는지 확인
    assert called["read"] is False
    assert called["auth"] is False
    # 로깅 메시지 확인
    assert any("토큰 검증을 생략" in rec.message for rec in caplog.records)


def test_ensure_valid_token_uses_saved_token_when_present(agent_module, caplog, monkeypatch):
    # 저장된 토큰이 있을 때 auth는 호출되지 않아야 함
    called = {"auth": False}

    def fake_read():
        return {"access_token": "dummy"}

    def fake_auth(**kwargs):
        called["auth"] = True
        return {"access_token": "dummy2", "access_token_token_expired": "2099-01-01 00:00:00"}

    monkeypatch.setattr(agent_module, "read_token", fake_read)
    monkeypatch.setattr(agent_module, "auth", fake_auth)

    Agent = agent_module.Agent

    caplog.set_level("INFO")
    Agent(
        app_key="k",
        app_secret="s",
        account_no="12345678",
        account_code="01",
    )

    # auth가 호출되지 않았는지 확인
    assert called["auth"] is False
    # 로깅 메시지 확인
    assert any("유효한 토큰이 확인" in rec.message for rec in caplog.records)


def test_ensure_valid_token_requests_new_when_missing(agent_module, caplog, monkeypatch):
    # 저장된 토큰이 없으면 auth 호출
    called = {"auth": False}

    def fake_read():
        return None

    def fake_auth(**kwargs):
        called["auth"] = True
        return {"access_token": "dummy2", "access_token_token_expired": "2099-01-01 00:00:00"}

    monkeypatch.setattr(agent_module, "read_token", fake_read)
    monkeypatch.setattr(agent_module, "auth", fake_auth)

    Agent = agent_module.Agent

    caplog.set_level("INFO")
    Agent(
        app_key="k",
        app_secret="s",
        account_no="12345678",
        account_code="01",
    )

    assert called["auth"] is True
    assert any("새 토큰" in rec.message for rec in caplog.records)

