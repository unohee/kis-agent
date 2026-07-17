"""비동기 인증이 동기 auth()의 계약을 지키는지 검증.

`test_auth_async.py`는 "토큰 dict가 반환되는가"만 본다. 그것만으로는 아래 두
결함을 못 잡는다 — 둘 다 "인증은 성공했는데 이후 API 호출이 실패"하는,
원인을 찾기 어려운 형태로 나타난다:

1. 동기 `auth()`는 토큰 발급 후 `_base_headers`/TR 환경까지 설치한다.
   비동기가 이를 빠뜨리면 호출부는 인증됐다고 믿지만 헤더가 비거나 낡는다.
2. 토큰 캐시는 APP_KEY별로 분리된다. 캐시 조회와 토큰 요청이 서로 다른 키
   슬롯을 고르면(vps인데 prod 키를 보는 등) 잘못된 토큰을 재사용한다.
"""

import importlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kis_agent.core.auth import _app_key_for, auth_async, reAuth_async
from kis_agent.core.config import KISConfig

# `from kis_agent.core import auth`는 같은 이름의 auth() **함수**를 준다
# (패키지가 re-export). 모듈 전역(_cfg/_base_headers)을 봐야 하므로 명시적으로
# 모듈을 가져온다.
auth_mod = importlib.import_module("kis_agent.core.auth")

pytest.importorskip("aiohttp", reason="비동기 인증에는 aiohttp가 필요하다")


@pytest.fixture
def config():
    return KISConfig(
        app_key="test_app_key",
        app_secret="test_app_secret",
        base_url="http://test.api.com",
        account_no="11111111",
        account_code="01",
    )


def _mock_session(token="fresh_token"):
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(
        return_value={
            "access_token": token,
            "access_token_token_expired": "2099-01-01 00:00:00",
        }
    )
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock()

    session = AsyncMock()
    session.post = MagicMock(return_value=resp)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock()
    return session


class TestAppKeySlotSelection:
    """캐시 조회와 토큰 요청이 같은 APP_KEY 슬롯을 골라야 한다."""

    def test_config_wins_over_module_config(self, config):
        assert _app_key_for(config, svr="prod") == "test_app_key"
        assert _app_key_for(config, svr="vps") == "test_app_key"

    def test_prod_uses_my_app(self, monkeypatch):
        monkeypatch.setitem(auth_mod._cfg, "my_app", "real_key")
        monkeypatch.setitem(auth_mod._cfg, "paper_app", "paper_key")
        assert _app_key_for(None, svr="prod") == "real_key"

    def test_vps_uses_paper_app_not_my_app(self, monkeypatch):
        """vps인데 my_app을 보면 실전 토큰을 모의에 재사용하게 된다."""
        monkeypatch.setitem(auth_mod._cfg, "my_app", "real_key")
        monkeypatch.setitem(auth_mod._cfg, "paper_app", "paper_key")
        assert _app_key_for(None, svr="vps") == "paper_key"

    def test_cache_lookup_and_token_request_agree(self, monkeypatch):
        """_build_token_request가 쓰는 키 == 캐시 조회 키."""
        monkeypatch.setitem(auth_mod._cfg, "my_app", "real_key")
        monkeypatch.setitem(auth_mod._cfg, "paper_app", "paper_key")
        monkeypatch.setitem(auth_mod._cfg, "paper_sec", "paper_sec")
        for svr in ("prod", "vps"):
            _, _, request_key = auth_mod._build_token_request(None, svr)
            assert request_key == _app_key_for(None, svr), f"{svr} 슬롯 불일치"


class TestTokenEnvInstalled:
    """auth_async는 동기 auth()처럼 헤더/TR 환경을 설치해야 한다."""

    @pytest.mark.asyncio
    @patch("kis_agent.core.auth.save_token")
    @patch("kis_agent.core.auth.read_token", return_value=None)
    async def test_new_token_installs_headers(self, _read, _save, config):
        with patch("aiohttp.ClientSession", return_value=_mock_session("fresh_token")):
            await auth_async(config)

        assert auth_mod._base_headers["authorization"] == "Bearer fresh_token"
        assert auth_mod._base_headers["appkey"] == "test_app_key"
        assert auth_mod.getTREnv().my_token == "Bearer fresh_token"

    @pytest.mark.asyncio
    @patch("kis_agent.core.auth.read_token")
    async def test_cached_token_also_installs_headers(self, mock_read, config):
        """캐시 히트일 때만 설치를 건너뛰면 2회차부터 헤더가 낡는다."""
        mock_read.return_value = {
            "access_token": "cached_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        # 직전 상태를 오염시켜 두고, 캐시 경로가 덮어쓰는지 본다.
        auth_mod._base_headers["authorization"] = "Bearer stale"

        await auth_async(config)

        assert auth_mod._base_headers["authorization"] == "Bearer cached_token"

    @pytest.mark.asyncio
    @patch("kis_agent.core.auth.read_token")
    async def test_reauth_async_also_installs_headers(self, mock_read, config):
        mock_read.return_value = {
            "access_token": "reauth_cached",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        auth_mod._base_headers["authorization"] = "Bearer stale"

        await reAuth_async(config)

        assert auth_mod._base_headers["authorization"] == "Bearer reauth_cached"


class TestRefreshTokenAsyncInstallsEnv:
    """client.refresh_token_async()도 새 토큰을 환경에 반영해야 한다."""

    @pytest.mark.asyncio
    @patch("kis_agent.core.client.auth_async")
    async def test_refresh_updates_headers(self, mock_auth_async, config):
        from kis_agent.core.client import KISClient

        mock_auth_async.return_value = {
            "access_token": "initial",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }
        client = await KISClient.create_async(config=config)

        with patch(
            "aiohttp.ClientSession", return_value=_mock_session("refreshed_token")
        ), patch("kis_agent.core.auth.save_token"):
            await client.refresh_token_async()

        assert client.token == "refreshed_token"
        # 갱신했는데 헤더가 이전 토큰이면 이후 호출이 조용히 401난다.
        assert auth_mod._base_headers["authorization"] == "Bearer refreshed_token"
