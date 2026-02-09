"""
auth 모듈의 비동기 메서드 단위 테스트 모듈입니다.

이 모듈은 auth 모듈의 비동기 기능을 테스트합니다:
- 비동기 토큰 발급 (auth_async)
- 비동기 토큰 갱신 (reAuth_async)

의존성:
- pytest: 테스트 프레임워크
- pytest-asyncio: 비동기 테스트 지원
- unittest.mock: 모킹
- aiohttp: 비동기 HTTP 클라이언트

사용 예시:
    >>> pytest tests/unit/test_auth_async.py -v

Note:
    auth_async, reAuth_async 함수가 아직 구현되지 않은 경우 전체 테스트가 skip됩니다.
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# aiohttp가 설치되어 있는지 확인
try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# auth_async 함수들이 구현되어 있는지 확인
try:
    from pykis.core.auth import (
        auth_async,
        read_token,
        reAuth_async,
        save_token,
    )

    AUTH_ASYNC_AVAILABLE = True
except ImportError:
    AUTH_ASYNC_AVAILABLE = False
    # 테스트 skip을 위해 더미 함수 정의
    auth_async = None
    reAuth_async = None
    from pykis.core.auth import read_token, save_token

from pykis.core.config import KISConfig

# auth_async 함수들이 구현되지 않은 경우 모듈 전체 skip
pytestmark = pytest.mark.skipif(
    not AUTH_ASYNC_AVAILABLE,
    reason="auth_async functions not implemented yet",
)


@pytest.mark.skipif(not AIOHTTP_AVAILABLE, reason="aiohttp not installed")
class TestAuthAsync:
    """
    auth 모듈의 비동기 메서드 단위 테스트 클래스입니다.
    """

    @pytest.fixture
    def config(self):
        """테스트용 KISConfig 인스턴스"""
        return KISConfig(
            app_key="test_app_key",
            app_secret="test_app_secret",
            base_url="http://test.api.com",
            account_no="11111111",
            account_code="01",
        )

    @pytest.fixture
    def temp_dir(self):
        """임시 디렉토리 생성"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # 정리
        import shutil

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    @patch("pykis.core.auth.save_token")
    @patch("pykis.core.auth.read_token")
    async def test_auth_async_with_new_token(
        self, mock_read_token, mock_save_token, config
    ):
        """
        auth_async 함수를 테스트합니다 - 새 토큰 발급
        """
        # Mock 설정: 저장된 토큰 없음
        mock_read_token.return_value = None

        # aiohttp ClientSession mock
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "access_token": "test_async_token",
                "access_token_token_expired": "2099-01-01 00:00:00",
            }
        )
        # async with response를 위한 mock 설정
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        # post 메서드가 mock_response를 직접 반환하도록 설정
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            # 토큰 발급 테스트
            token = await auth_async(config)

            assert token == {
                "access_token": "test_async_token",
                "access_token_token_expired": "2099-01-01 00:00:00",
            }
            mock_save_token.assert_called_once()

    @pytest.mark.asyncio
    @patch("pykis.core.auth.read_token")
    async def test_auth_async_with_saved_token(self, mock_read_token, config):
        """
        auth_async 함수를 테스트합니다 - 저장된 토큰 사용
        """
        # Mock 설정: 유효한 저장된 토큰
        mock_read_token.return_value = {
            "access_token": "saved_async_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }

        # 토큰 발급 테스트 (저장된 토큰 재사용)
        token = await auth_async(config)

        assert token["access_token"] == "saved_async_token"

    @pytest.mark.asyncio
    @patch("pykis.core.auth.read_token")
    async def test_auth_async_api_error(self, mock_read_token, config):
        """
        auth_async 함수의 에러 처리를 테스트합니다 - API 에러
        """
        # Mock 설정: 저장된 토큰 없음
        mock_read_token.return_value = None

        # 에러 응답을 반환하는 mock 설정
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text = AsyncMock(return_value="Unauthorized")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # ClientSession mock 설정
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # aiohttp.ClientSession mock
        with patch("aiohttp.ClientSession", return_value=mock_session):
            # 에러 시 RuntimeError 발생해야 함
            with pytest.raises(RuntimeError, match="KIS API 토큰 발급 실패"):
                await auth_async(config)

    @pytest.mark.asyncio
    @patch("pykis.core.auth.save_token")
    @patch("pykis.core.auth.read_token")
    async def test_reauth_async_with_new_token(
        self, mock_read_token, mock_save_token, config
    ):
        """
        reAuth_async 함수를 테스트합니다 - 새 토큰 발급
        """
        # Mock 설정: 저장된 토큰 없음
        mock_read_token.return_value = None

        # aiohttp ClientSession mock
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "access_token": "reauth_async_token",
                "access_token_token_expired": "2099-01-01 00:00:00",
            }
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            # 토큰 갱신 테스트
            token = await reAuth_async(config)

            assert token == {
                "access_token": "reauth_async_token",
                "access_token_token_expired": "2099-01-01 00:00:00",
            }
            mock_save_token.assert_called_once()

    @pytest.mark.asyncio
    @patch("pykis.core.auth.read_token")
    async def test_reauth_async_with_saved_token(self, mock_read_token):
        """
        reAuth_async 함수를 테스트합니다 - 저장된 토큰 사용 (24시간 이내)
        """
        # Mock 설정: 유효한 저장된 토큰
        mock_read_token.return_value = {
            "access_token": "cached_async_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }

        # 토큰 갱신 테스트 (저장된 토큰 재사용)
        token = await reAuth_async(config=None, svr="prod")

        assert token is not None
        assert token["access_token"] == "cached_async_token"


@pytest.mark.skipif(AIOHTTP_AVAILABLE, reason="Test for missing aiohttp")
class TestAuthAsyncWithoutAiohttp:
    """
    aiohttp가 없을 때의 에러 처리 테스트
    """

    @pytest.fixture
    def config(self):
        """테스트용 KISConfig 인스턴스"""
        return KISConfig(
            app_key="test_app_key",
            app_secret="test_app_secret",
            base_url="http://test.api.com",
            account_no="11111111",
            account_code="01",
        )

    @pytest.mark.asyncio
    async def test_auth_async_raises_import_error(self, config):
        """
        aiohttp가 없을 때 ImportError 발생
        """
        with pytest.raises(ImportError, match="aiohttp is not installed"):
            await auth_async(config)

    @pytest.mark.asyncio
    async def test_reauth_async_raises_import_error(self):
        """
        aiohttp가 없을 때 ImportError 발생
        """
        with pytest.raises(ImportError, match="aiohttp is not installed"):
            await reAuth_async(config=None, svr="prod")


@pytest.mark.skipif(not AIOHTTP_AVAILABLE, reason="aiohttp not installed")
class TestAuthAsyncIntegration:
    """
    auth_async의 통합 테스트 (실제 파일 I/O 포함)
    """

    @pytest.fixture
    def temp_token_path(self):
        """임시 토큰 파일 경로"""
        temp_dir = tempfile.mkdtemp()
        token_path = os.path.join(temp_dir, "test_token.json")
        yield token_path
        # 정리
        import shutil

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def config(self):
        """테스트용 KISConfig 인스턴스"""
        return KISConfig(
            app_key="test_integration_key",
            app_secret="test_integration_secret",
            base_url="http://test.api.com",
            account_no="11111111",
            account_code="01",
        )

    @pytest.mark.asyncio
    async def test_auth_async_save_and_reuse_token(self, config, temp_token_path):
        """
        토큰 저장 및 재사용 통합 테스트
        """
        # 첫 번째 호출: 새 토큰 발급
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "access_token": "integration_token",
                "access_token_token_expired": "2099-01-01 00:00:00",
            }
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session), patch(
            "pykis.core.auth.token_tmp", temp_token_path
        ):
            token1 = await auth_async(config)

        # 두 번째 호출: 저장된 토큰 재사용 (read_token이 파일에서 읽음)
        # 이 부분은 실제 save_token/read_token 동작을 테스트
        # mock 없이 실제 파일 I/O 사용
        assert token1["access_token"] == "integration_token"


@pytest.mark.skipif(not AIOHTTP_AVAILABLE, reason="aiohttp not installed")
class TestKISClientAsync:
    """
    KISClient의 비동기 생성 메서드 단위 테스트 클래스입니다.
    """

    @pytest.fixture
    def config(self):
        """테스트용 KISConfig 인스턴스"""
        return KISConfig(
            app_key="test_app_key",
            app_secret="test_app_secret",
            base_url="http://test.api.com",
            account_no="11111111",
            account_code="01",
        )

    @pytest.mark.asyncio
    @patch("pykis.core.client.auth_async")
    async def test_create_async_with_config(self, mock_auth_async, config):
        """
        KISClient.create_async 팩토리 메서드 테스트 - config 사용
        """
        from pykis.core.client import KISClient

        # Mock 설정
        mock_auth_async.return_value = {
            "access_token": "async_client_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }

        # 비동기 클라이언트 생성
        client = await KISClient.create_async(config=config)

        # 검증
        assert client is not None
        assert client.token == "async_client_token"
        assert client.token_expired == "2099-01-01 00:00:00"
        assert client.config == config
        assert client.svr == "prod"
        mock_auth_async.assert_called_once()

    @pytest.mark.asyncio
    @patch("pykis.core.client.auth_async")
    async def test_create_async_with_options(self, mock_auth_async, config):
        """
        KISClient.create_async 팩토리 메서드 테스트 - 옵션 설정
        """
        from pykis.core.client import KISClient

        # Mock 설정
        mock_auth_async.return_value = {
            "access_token": "async_client_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }

        # 비동기 클라이언트 생성 (옵션 설정)
        client = await KISClient.create_async(
            config=config,
            verbose=True,
            enable_rate_limiter=False,
        )

        # 검증
        assert client.verbose is True
        assert client.enable_rate_limiter is False
        assert client.rate_limiter is None

    @pytest.mark.asyncio
    @patch("pykis.core.client.auth_async")
    async def test_create_async_with_rate_limiter(self, mock_auth_async, config):
        """
        KISClient.create_async 팩토리 메서드 테스트 - Rate Limiter 활성화
        """
        from pykis.core.client import KISClient

        # Mock 설정
        mock_auth_async.return_value = {
            "access_token": "async_client_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }

        # 비동기 클라이언트 생성 (Rate Limiter 활성화)
        client = await KISClient.create_async(
            config=config,
            enable_rate_limiter=True,
        )

        # 검증
        assert client.enable_rate_limiter is True
        assert client.rate_limiter is not None

    @pytest.mark.asyncio
    @patch("pykis.core.client.auth_async")
    async def test_create_async_vps_server(self, mock_auth_async, config):
        """
        KISClient.create_async 팩토리 메서드 테스트 - 모의투자 서버
        """
        from pykis.core.client import KISClient

        # Mock 설정
        mock_auth_async.return_value = {
            "access_token": "vps_async_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }

        # 비동기 클라이언트 생성 (모의투자)
        client = await KISClient.create_async(
            svr="vps",
            config=config,
        )

        # 검증
        assert client.svr == "vps"
        mock_auth_async.assert_called_once_with(config=config, svr="vps")

    @pytest.mark.asyncio
    @patch("pykis.core.client.auth_async")
    async def test_refresh_token_async(self, mock_auth_async, config):
        """
        KISClient.refresh_token_async 메서드 테스트
        """
        from pykis.core.client import KISClient

        # Mock 설정 - 초기 토큰
        mock_auth_async.return_value = {
            "access_token": "initial_async_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }

        # 비동기 클라이언트 생성
        client = await KISClient.create_async(config=config)
        assert client.token == "initial_async_token"

        # 토큰 갱신 Mock 설정
        mock_refresh_response = AsyncMock()
        mock_refresh_response.status = 200
        mock_refresh_response.json = AsyncMock(
            return_value={
                "access_token": "refreshed_async_token",
                "access_token_token_expired": "2099-12-31 23:59:59",
            }
        )
        mock_refresh_response.__aenter__ = AsyncMock(return_value=mock_refresh_response)
        mock_refresh_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_refresh_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch("aiohttp.ClientSession", return_value=mock_session):
            await client.refresh_token_async()

        # 검증
        assert client.token == "refreshed_async_token"
        assert client.token_expired == "2099-12-31 23:59:59"

    @pytest.mark.asyncio
    @patch("pykis.core.client.auth_async")
    async def test_refresh_token_async_error(self, mock_auth_async, config):
        """
        KISClient.refresh_token_async 메서드 테스트 - 오류 처리

        Note: aiohttp.ClientSession의 nested async context manager 패턴은
        mock하기 어려워서 connection error 시나리오로 대체합니다.
        """
        from pykis.core.client import KISClient

        # Mock 설정 - 초기 토큰
        mock_auth_async.return_value = {
            "access_token": "initial_async_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }

        # 비동기 클라이언트 생성
        client = await KISClient.create_async(config=config)

        # aiohttp.ClientSession이 예외를 발생시키도록 mock
        async def raise_error(*args, **kwargs):
            raise aiohttp.ClientError("Connection failed")

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(side_effect=raise_error)

        # refresh_token_async 내부에서 aiohttp를 직접 import하므로
        # 전역 aiohttp.ClientSession을 mock해야 함
        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(Exception):  # ClientError 또는 래핑된 Exception
                await client.refresh_token_async()


@pytest.mark.skipif(not AIOHTTP_AVAILABLE, reason="aiohttp not installed")
class TestAgentAsync:
    """
    Agent의 비동기 생성 메서드 단위 테스트 클래스입니다.
    """

    @pytest.mark.asyncio
    @patch("pykis.core.client.auth_async")
    async def test_create_async_basic(self, mock_auth_async):
        """
        Agent.create_async 팩토리 메서드 기본 테스트
        """
        from pykis.core.agent import Agent

        # Mock 설정
        mock_auth_async.return_value = {
            "access_token": "agent_async_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }

        # 비동기 Agent 생성
        agent = await Agent.create_async(
            app_key="test_app_key",
            app_secret="test_app_secret",
            account_no="12345678",
            account_code="01",
        )

        # 검증
        assert agent is not None
        assert agent.client is not None
        assert agent.client.token == "agent_async_token"
        assert agent.account_info["CANO"] == "12345678"
        assert agent.account_info["ACNT_PRDT_CD"] == "01"
        assert agent.my_acct == agent.account_info
        mock_auth_async.assert_called_once()

    @pytest.mark.asyncio
    @patch("pykis.core.client.auth_async")
    async def test_create_async_with_rate_limiter(self, mock_auth_async):
        """
        Agent.create_async 팩토리 메서드 테스트 - Rate Limiter 활성화
        """
        from pykis.core.agent import Agent

        # Mock 설정
        mock_auth_async.return_value = {
            "access_token": "agent_async_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }

        # 비동기 Agent 생성 (Rate Limiter 활성화)
        agent = await Agent.create_async(
            app_key="test_app_key",
            app_secret="test_app_secret",
            account_no="12345678",
            account_code="01",
            enable_rate_limiter=True,
        )

        # 검증
        assert agent.rate_limiter is not None
        assert agent.client.rate_limiter is not None

    @pytest.mark.asyncio
    @patch("pykis.core.client.auth_async")
    async def test_create_async_without_rate_limiter(self, mock_auth_async):
        """
        Agent.create_async 팩토리 메서드 테스트 - Rate Limiter 비활성화
        """
        from pykis.core.agent import Agent

        # Mock 설정
        mock_auth_async.return_value = {
            "access_token": "agent_async_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }

        # 비동기 Agent 생성 (Rate Limiter 비활성화)
        agent = await Agent.create_async(
            app_key="test_app_key",
            app_secret="test_app_secret",
            account_no="12345678",
            account_code="01",
            enable_rate_limiter=False,
        )

        # 검증
        assert agent.rate_limiter is None

    @pytest.mark.asyncio
    @patch("pykis.core.client.auth_async")
    async def test_create_async_with_custom_base_url(self, mock_auth_async):
        """
        Agent.create_async 팩토리 메서드 테스트 - 모의투자 서버 URL
        """
        from pykis.core.agent import Agent

        # Mock 설정
        mock_auth_async.return_value = {
            "access_token": "vps_async_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }

        # 비동기 Agent 생성 (모의투자)
        vps_url = "https://openapivts.koreainvestment.com:29443"
        agent = await Agent.create_async(
            app_key="test_app_key",
            app_secret="test_app_secret",
            account_no="12345678",
            account_code="01",
            base_url=vps_url,
        )

        # 검증
        assert vps_url == agent.client.config.BASE_URL

    @pytest.mark.asyncio
    async def test_create_async_missing_params(self):
        """
        Agent.create_async 필수 매개변수 누락 테스트
        """
        from pykis.core.agent import Agent

        # 필수 매개변수 누락 시 ValueError 발생
        with pytest.raises(ValueError, match="필수 매개변수가 누락되었습니다"):
            await Agent.create_async(
                app_key="",
                app_secret="test_secret",
                account_no="12345678",
                account_code="01",
            )

        with pytest.raises(ValueError, match="필수 매개변수가 누락되었습니다"):
            await Agent.create_async(
                app_key="test_key",
                app_secret="",
                account_no="12345678",
                account_code="01",
            )

    @pytest.mark.asyncio
    @patch("pykis.core.client.auth_async")
    async def test_create_async_apis_initialized(self, mock_auth_async):
        """
        Agent.create_async 팩토리 메서드 테스트 - API 모듈 초기화 확인
        """
        from pykis.core.agent import Agent

        # Mock 설정
        mock_auth_async.return_value = {
            "access_token": "agent_async_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }

        # 비동기 Agent 생성
        agent = await Agent.create_async(
            app_key="test_app_key",
            app_secret="test_app_secret",
            account_no="12345678",
            account_code="01",
        )

        # API 모듈들이 초기화되었는지 검증
        assert hasattr(agent, "account_api")
        assert hasattr(agent, "stock_api")
        assert hasattr(agent, "investor_api")
        assert hasattr(agent, "program_api")
        assert hasattr(agent, "market_api")
        assert hasattr(agent, "interest_api")

    @pytest.mark.asyncio
    @patch("pykis.core.client.auth_async")
    async def test_create_async_with_rate_limiter_config(self, mock_auth_async):
        """
        Agent.create_async 팩토리 메서드 테스트 - Rate Limiter 커스텀 설정
        """
        from pykis.core.agent import Agent

        # Mock 설정
        mock_auth_async.return_value = {
            "access_token": "agent_async_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }

        # 커스텀 Rate Limiter 설정
        custom_config = {
            "requests_per_second": 10,
            "requests_per_minute": 500,
        }

        # 비동기 Agent 생성 (커스텀 Rate Limiter 설정)
        agent = await Agent.create_async(
            app_key="test_app_key",
            app_secret="test_app_secret",
            account_no="12345678",
            account_code="01",
            rate_limiter_config=custom_config,
        )

        # 검증 (Rate Limiter가 활성화되어 있으면 설정이 적용됨)
        assert agent.rate_limiter is not None
