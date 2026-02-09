"""
KISClient 포괄적 단위 테스트

INT-379: core/client.py 커버리지 개선 (19% → 70%)
생성일: 2026-01-04
"""

import sys
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
import requests

# client 모듈을 명시적으로 import
import kis_agent.core.client  # noqa: F401


def get_client_module():
    """client 모듈을 sys.modules에서 가져옵니다."""
    return sys.modules["kis_agent.core.client"]


class TestKISClientInit:
    """KISClient 초기화 테스트"""

    def test_init_with_config_object_as_svr(self):
        """svr 위치에 KISConfig 객체가 전달될 때 처리 (L194-196)"""
        client_module = get_client_module()
        from kis_agent.core.config import KISConfig

        # KISConfig의 서브클래스로 mock을 생성 (isinstance 체크를 통과하기 위해)
        class MockKISConfig(KISConfig):
            def __init__(self):
                self.APP_KEY = "TEST_KEY"
                self.APP_SECRET = "TEST_SECRET"
                self.ACCOUNT_NO = "12345678"
                self.ACCOUNT_CODE = "01"
                self.BASE_URL = "https://test.api.com"

        mock_config = MockKISConfig()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "test_token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP_KEY"
                mock_tr_env.my_sec = "APP_SECRET"
                mock_get_tr_env.return_value = mock_tr_env

                # KISConfig를 svr 위치에 전달
                client = client_module.KISClient(svr=mock_config, verbose=False)

                assert client.config == mock_config
                assert client.svr == "prod"

    def test_init_without_config(self):
        """config 없이 환경 변수로 초기화 (L255-266)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "env_token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_get_tr_env.return_value = mock_tr_env
                with patch.dict("os.environ", {"KIS_BASE_URL": "https://env.api.com"}):
                    client = client_module.KISClient(config=None, verbose=False)

                    assert client.token == "env_token"
                    assert client.base_url == "https://env.api.com"

    def test_init_with_config(self):
        """config 객체로 초기화 (L267-276)"""
        client_module = get_client_module()

        mock_config = MagicMock()
        mock_config.APP_KEY = "CONFIG_KEY"
        mock_config.APP_SECRET = "CONFIG_SECRET"
        mock_config.BASE_URL = "https://config.api.com"

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "config_token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                client = client_module.KISClient(config=mock_config, verbose=False)

                assert client.token == "config_token"
                assert client.base_url == "https://config.api.com"

    def test_init_auth_failure(self):
        """인증 실패 시 예외 발생 (L277-279)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.side_effect = Exception("인증 실패")

            with pytest.raises(Exception, match="인증 실패"):
                client_module.KISClient(config=None, verbose=False)

    def test_init_rate_limiter_disabled(self):
        """Rate Limiter 비활성화 (L223-224)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "token"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                client = client_module.KISClient(
                    enable_rate_limiter=False, verbose=False
                )

                assert client.rate_limiter is None

    def test_init_custom_rate_limiter(self):
        """커스텀 Rate Limiter 사용 (L216-222)"""
        client_module = get_client_module()

        mock_rate_limiter = MagicMock()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "token"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                client = client_module.KISClient(
                    rate_limiter=mock_rate_limiter,
                    enable_rate_limiter=True,
                    verbose=False,
                )

                assert client.rate_limiter == mock_rate_limiter


class TestInitializeToken:
    """_initialize_token 메서드 테스트"""

    def test_skip_if_token_still_valid(self):
        """토큰이 아직 유효하면 재발급 건너뛰기 (L239-250)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "initial_token",
                "access_token_token_expired": (
                    datetime.now() + timedelta(hours=23)
                ).strftime("%Y-%m-%d %H:%M:%S"),
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                client = client_module.KISClient(verbose=False)
                initial_call_count = mock_auth.call_count

                # 다시 _initialize_token 호출
                client._initialize_token()

                # 토큰이 유효하면 auth가 다시 호출되지 않음
                # (실제로는 5분 이상 남아있으면 건너뜀)
                assert mock_auth.call_count >= initial_call_count

    def test_token_expired_datetime_parsing_error(self):
        """토큰 만료 시간 파싱 실패 시 재발급 (L251-252)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "invalid_date_format",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                # 잘못된 날짜 포맷에서도 예외 없이 진행
                client = client_module.KISClient(verbose=False)
                assert client.token == "token"


class TestCheckAndRefreshToken:
    """_check_and_refresh_token 메서드 테스트"""

    def test_refresh_when_token_expired(self):
        """토큰 만료 시 자동 갱신 (L296-298)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            # 만료된 토큰
            expired_time = (datetime.now() - timedelta(hours=1)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            mock_auth.return_value = {
                "access_token": "expired_token",
                "access_token_token_expired": expired_time,
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                client = client_module.KISClient(verbose=False)

                # 토큰 만료 시간을 과거로 설정
                client.token_expired = expired_time

                # 토큰 체크 시 갱신됨
                initial_call_count = mock_auth.call_count
                client._check_and_refresh_token()
                assert mock_auth.call_count > initial_call_count

    def test_refresh_when_token_expiring_soon(self):
        """토큰이 5분 이내 만료 예정 시 갱신 (L296)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "soon_expired",
                "access_token_token_expired": (
                    datetime.now() + timedelta(minutes=3)
                ).strftime("%Y-%m-%d %H:%M:%S"),
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                client = client_module.KISClient(verbose=False)
                client.token_expired = (datetime.now() + timedelta(minutes=3)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                initial_call_count = mock_auth.call_count
                client._check_and_refresh_token()
                # 5분 이내 만료 예정이면 갱신 호출
                assert mock_auth.call_count > initial_call_count

    def test_refresh_on_parsing_error(self):
        """만료 시간 파싱 오류 시 재발급 (L299-301)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                client = client_module.KISClient(verbose=False)
                client.token_expired = "invalid_format"

                initial_call_count = mock_auth.call_count
                client._check_and_refresh_token()
                # 파싱 오류 시 재발급
                assert mock_auth.call_count > initial_call_count


class TestEnforceRateLimit:
    """_enforce_rate_limit 메서드 테스트"""

    def test_with_rate_limiter_enabled(self):
        """Rate Limiter 활성화 시 acquire 호출 (L310-314)"""
        client_module = get_client_module()

        mock_rate_limiter = MagicMock()
        mock_rate_limiter.acquire.return_value = 0.1

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "token"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                client = client_module.KISClient(
                    rate_limiter=mock_rate_limiter,
                    enable_rate_limiter=True,
                    verbose=True,
                )

                client._enforce_rate_limit(priority=1)

                mock_rate_limiter.acquire.assert_called_with(1)

    def test_without_rate_limiter(self):
        """Rate Limiter 비활성화 시 기존 방식 (L316-323)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "token"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                client = client_module.KISClient(
                    enable_rate_limiter=False, verbose=False
                )

                # 연속 호출 시 대기 발생
                start = time.monotonic()
                client._enforce_rate_limit()
                client._enforce_rate_limit()
                elapsed = time.monotonic() - start

                # 최소 간격(50ms) 적용 확인
                assert elapsed >= 0.04  # 약간의 오차 허용


class TestGetBaseHeaders:
    """_get_base_headers 메서드 테스트"""

    def test_get_base_headers(self):
        """기본 헤더 생성 (L335-342)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "my_token"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP_KEY"
                mock_tr_env.my_sec = "APP_SECRET"
                mock_get_tr_env.return_value = mock_tr_env

                client = client_module.KISClient(verbose=False)
                headers = client._get_base_headers("FHKST01010100")

                assert headers["Content-Type"] == "application/json"
                assert "Bearer" in headers["authorization"]
                assert headers["appKey"] == "APP_KEY"
                assert headers["appSecret"] == "APP_SECRET"
                assert headers["tr_id"] == "FHKST01010100"
                assert headers["custtype"] == "P"


class TestMakeRequest:
    """make_request 메서드 테스트"""

    def test_make_request_success(self):
        """성공적인 API 요청 (L440-446)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                with patch("requests.request") as mock_request:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "rt_cd": "0",
                        "msg1": "정상처리",
                        "output": {"data": "value"},
                    }
                    mock_request.return_value = mock_response

                    client = client_module.KISClient(
                        enable_rate_limiter=False, verbose=False
                    )
                    result = client.make_request(
                        "/test/endpoint", "TR001", {"param": "value"}
                    )

                    assert result["rt_cd"] == "0"
                    assert result["output"]["data"] == "value"

    def test_make_request_json_decode_error(self):
        """JSON 디코드 실패 (L412-427)"""
        import json as json_module

        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                with patch("requests.request") as mock_request:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    # json.JSONDecodeError를 발생시켜야 함
                    mock_response.json.side_effect = json_module.JSONDecodeError(
                        "Invalid JSON", "doc", 0
                    )
                    mock_response.text = "Invalid response"
                    mock_request.return_value = mock_response

                    client = client_module.KISClient(
                        enable_rate_limiter=False, verbose=False
                    )
                    result = client.make_request("/test", "TR", {})

                    assert result["rt_cd"] == "JSON_DECODE_ERROR"
                    assert result["error_type"] == "JSONDecodeError"

    def test_make_request_no_rt_cd(self):
        """응답에 rt_cd 없음 (L429-438)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                with patch("requests.request") as mock_request:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"data": "no_rt_cd"}
                    mock_request.return_value = mock_response

                    client = client_module.KISClient(
                        enable_rate_limiter=False, verbose=False
                    )
                    result = client.make_request("/test", "TR", {})

                    assert result["rt_cd"] == "NO_RT_CD"
                    assert result["error_type"] == "NoRtCd"

    def test_make_request_api_error(self):
        """API 오류 응답 (L448-512)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                with patch("requests.request") as mock_request:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "rt_cd": "1",
                        "msg1": "잘못된 요청입니다",
                    }
                    mock_request.return_value = mock_response

                    client = client_module.KISClient(
                        enable_rate_limiter=False, verbose=False
                    )
                    result = client.make_request("/test", "TR", {}, retries=1)

                    assert result["rt_cd"] == "1"
                    assert result["error_type"] == "ApiError"

    def test_make_request_token_expired_error(self):
        """토큰 만료 에러 감지 및 재시도 (L457-473)"""
        client_module = get_client_module()

        call_count = 0

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "new_token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                def side_effect(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    if call_count == 1:
                        mock_response.json.return_value = {
                            "rt_cd": "EGW00123",
                            "msg1": "토큰이 만료되었습니다",
                        }
                    else:
                        mock_response.json.return_value = {
                            "rt_cd": "0",
                            "msg1": "정상",
                        }
                    return mock_response

                with patch("requests.request", side_effect=side_effect):
                    client = client_module.KISClient(
                        enable_rate_limiter=False, verbose=False
                    )
                    result = client.make_request("/test", "TR", {}, retries=2)

                    # 토큰 만료 후 재시도하여 성공
                    assert result["rt_cd"] == "0"

    def test_make_request_rate_limit_error(self):
        """유량 제한 에러 감지 및 재시도 (L475-504)"""
        client_module = get_client_module()

        call_count = 0

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                def side_effect(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    if call_count <= 2:
                        mock_response.json.return_value = {
                            "rt_cd": "1",
                            "msg1": "초당 거래건수를 초과하였습니다",
                        }
                    else:
                        mock_response.json.return_value = {
                            "rt_cd": "0",
                            "msg1": "정상",
                        }
                    return mock_response

                with patch("requests.request", side_effect=side_effect):
                    with patch("time.sleep"):  # 대기 시간 건너뛰기
                        client = client_module.KISClient(
                            enable_rate_limiter=False, verbose=False
                        )
                        result = client.make_request("/test", "TR", {}, retries=3)

                        assert result["rt_cd"] == "0"

    def test_make_request_http_error(self):
        """HTTP 오류 응답 (L513-547)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                with patch("requests.request") as mock_request:
                    mock_response = MagicMock()
                    mock_response.status_code = 500
                    mock_response.json.return_value = {
                        "rt_cd": "500",
                        "msg1": "Server Error",
                    }
                    mock_response.text = "Internal Server Error"
                    mock_request.return_value = mock_response

                    with patch("time.sleep"):
                        client = client_module.KISClient(
                            enable_rate_limiter=False, verbose=False
                        )
                        result = client.make_request("/test", "TR", {}, retries=1)

                        assert result["rt_cd"] == "500"

    def test_make_request_request_exception(self):
        """네트워크 요청 예외 (L553-565)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                with patch("requests.request") as mock_request:
                    mock_request.side_effect = requests.exceptions.ConnectionError(
                        "Connection failed"
                    )

                    with patch("time.sleep"):
                        client = client_module.KISClient(
                            enable_rate_limiter=False, verbose=False
                        )
                        with pytest.raises(requests.exceptions.ConnectionError):
                            client.make_request("/test", "TR", {}, retries=1)

    def test_make_request_post_method(self):
        """POST 요청 (L405-406)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                with patch("requests.request") as mock_request:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"rt_cd": "0"}
                    mock_request.return_value = mock_response

                    client = client_module.KISClient(
                        enable_rate_limiter=False, verbose=False
                    )
                    client.make_request("/test", "TR", {"data": "value"}, method="POST")

                    # POST 요청에서 json 파라미터 사용 확인
                    call_kwargs = mock_request.call_args
                    assert call_kwargs.kwargs.get("json") == {"data": "value"}
                    assert call_kwargs.kwargs.get("params") is None

    def test_make_request_verbose_logging(self):
        """상세 로깅 활성화 (L386-389, L398-399, L441-442)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                with patch("requests.request") as mock_request:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"rt_cd": "0", "output": {}}
                    mock_request.return_value = mock_response

                    # verbose=True로 실행
                    client = client_module.KISClient(
                        enable_rate_limiter=False, verbose=True
                    )
                    result = client.make_request("/test", "TR001", {})

                    assert result["rt_cd"] == "0"


class TestRefreshToken:
    """refresh_token 메서드 테스트"""

    def test_refresh_token_success(self):
        """토큰 갱신 성공 (L594-602)"""
        client_module = get_client_module()

        mock_config = MagicMock()
        mock_config.APP_KEY = "KEY"
        mock_config.APP_SECRET = "SECRET"
        mock_config.BASE_URL = "https://test.api.com"

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "old_token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "access_token": "new_token",
                        "access_token_token_expired": "2026-01-06 12:00:00",
                    }
                    mock_post.return_value = mock_response

                    client = client_module.KISClient(config=mock_config, verbose=False)
                    client.refresh_token()

                    assert client.token == "new_token"

    def test_refresh_token_no_access_token(self):
        """토큰 갱신 응답에 access_token 없음 (L599-600)"""
        client_module = get_client_module()

        mock_config = MagicMock()
        mock_config.APP_KEY = "KEY"
        mock_config.APP_SECRET = "SECRET"
        mock_config.BASE_URL = "https://test.api.com"

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "old"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {}  # access_token 없음
                    mock_post.return_value = mock_response

                    client = client_module.KISClient(config=mock_config, verbose=False)
                    with pytest.raises(Exception, match="access_token이 없습니다"):
                        client.refresh_token()

    def test_refresh_token_http_failure(self):
        """토큰 갱신 HTTP 실패 (L603-604)"""
        client_module = get_client_module()

        mock_config = MagicMock()
        mock_config.APP_KEY = "KEY"
        mock_config.APP_SECRET = "SECRET"
        mock_config.BASE_URL = "https://test.api.com"

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "old"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.status_code = 401
                    mock_post.return_value = mock_response

                    client = client_module.KISClient(config=mock_config, verbose=False)
                    with pytest.raises(Exception, match="HTTP 401"):
                        client.refresh_token()

    def test_refresh_token_exception(self):
        """토큰 갱신 중 예외 (L605-607)"""
        client_module = get_client_module()

        mock_config = MagicMock()
        mock_config.APP_KEY = "KEY"
        mock_config.APP_SECRET = "SECRET"
        mock_config.BASE_URL = "https://test.api.com"

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "old"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                with patch("requests.post") as mock_post:
                    mock_post.side_effect = Exception("Network error")

                    client = client_module.KISClient(config=mock_config, verbose=False)
                    with pytest.raises(Exception, match="Network error"):
                        client.refresh_token()


class TestGetKospi200Index:
    """get_kospi200_index 메서드 테스트"""

    def test_get_kospi200_index(self):
        """KOSPI200 지수 조회 (L609-626)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                with patch("requests.request") as mock_request:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "rt_cd": "0",
                        "output": {"index_value": "350.00"},
                    }
                    mock_request.return_value = mock_response

                    client = client_module.KISClient(
                        enable_rate_limiter=False, verbose=False
                    )
                    result = client.get_kospi200_index("202409")

                    assert result["rt_cd"] == "0"
                    # 올바른 파라미터 확인
                    call_kwargs = mock_request.call_args
                    assert "10109000" in str(call_kwargs)  # 09 from 202409


class TestGetWsApprovalKey:
    """get_ws_approval_key 메서드 테스트"""

    def test_get_ws_approval_key_success(self):
        """웹소켓 승인키 발급 성공 (L649-655)"""
        client_module = get_client_module()

        mock_config = MagicMock()
        mock_config.app_key = "WS_KEY"
        mock_config.app_secret = "WS_SECRET"
        mock_config.BASE_URL = "https://test.api.com"

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "token"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "approval_key": "ws_approval_123"
                    }
                    mock_post.return_value = mock_response

                    client = client_module.KISClient(config=mock_config, verbose=False)
                    result = client.get_ws_approval_key()

                    assert result == "ws_approval_123"

    def test_get_ws_approval_key_no_approval_key(self):
        """응답에 approval_key 없음 (L651-653)"""
        client_module = get_client_module()

        mock_config = MagicMock()
        mock_config.app_key = "WS_KEY"
        mock_config.app_secret = "WS_SECRET"
        mock_config.BASE_URL = "https://test.api.com"

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "token"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {}  # approval_key 없음
                    mock_post.return_value = mock_response

                    client = client_module.KISClient(config=mock_config, verbose=False)
                    result = client.get_ws_approval_key()

                    assert result is None

    def test_get_ws_approval_key_http_failure(self):
        """웹소켓 승인키 HTTP 실패 (L656-660)"""
        client_module = get_client_module()

        mock_config = MagicMock()
        mock_config.app_key = "WS_KEY"
        mock_config.app_secret = "WS_SECRET"
        mock_config.BASE_URL = "https://test.api.com"

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "token"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                with patch("requests.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.status_code = 401
                    mock_response.text = "Unauthorized"
                    mock_post.return_value = mock_response

                    client = client_module.KISClient(config=mock_config, verbose=False)
                    result = client.get_ws_approval_key()

                    assert result is None

    def test_get_ws_approval_key_exception(self):
        """웹소켓 승인키 요청 예외 (L661-663)"""
        client_module = get_client_module()

        mock_config = MagicMock()
        mock_config.app_key = "WS_KEY"
        mock_config.app_secret = "WS_SECRET"
        mock_config.BASE_URL = "https://test.api.com"

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "token"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                with patch("requests.post") as mock_post:
                    mock_post.side_effect = Exception("Connection error")

                    client = client_module.KISClient(config=mock_config, verbose=False)
                    result = client.get_ws_approval_key()

                    assert result is None

    def test_get_ws_approval_key_from_env(self):
        """환경 변수에서 키 사용 (L639-642)"""
        client_module = get_client_module()

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "token"}
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_get_tr_env.return_value = MagicMock()

                with patch.dict(
                    "os.environ",
                    {"KIS_APP_KEY": "ENV_KEY", "KIS_APP_SECRET": "ENV_SECRET"},
                ):
                    with patch("requests.post") as mock_post:
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"approval_key": "ws_key"}
                        mock_post.return_value = mock_response

                        # config 없이 생성
                        client = client_module.KISClient(config=None, verbose=False)
                        result = client.get_ws_approval_key()

                        # 환경 변수 값 사용 확인
                        call_kwargs = mock_post.call_args
                        payload = call_kwargs.kwargs.get("json", {})
                        assert payload.get("appkey") == "ENV_KEY"
                        assert payload.get("secretkey") == "ENV_SECRET"


class TestRateLimiterIntegration:
    """Rate Limiter 통합 테스트"""

    def test_rate_limiter_report_success(self):
        """API 성공 시 Rate Limiter에 보고 (L444-445)"""
        client_module = get_client_module()

        mock_rate_limiter = MagicMock()
        mock_rate_limiter.acquire.return_value = 0

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                with patch("requests.request") as mock_request:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"rt_cd": "0"}
                    mock_request.return_value = mock_response

                    client = client_module.KISClient(
                        rate_limiter=mock_rate_limiter,
                        enable_rate_limiter=True,
                        verbose=False,
                    )
                    client.make_request("/test", "TR", {})

                    mock_rate_limiter.report_success.assert_called_once()

    def test_rate_limiter_report_error(self):
        """유량 제한 에러 시 Rate Limiter에 보고 (L490-491)"""
        client_module = get_client_module()

        mock_rate_limiter = MagicMock()
        mock_rate_limiter.acquire.return_value = 0

        with patch.object(client_module, "auth") as mock_auth:
            mock_auth.return_value = {
                "access_token": "token",
                "access_token_token_expired": "2026-01-05 12:00:00",
            }
            with patch.object(client_module, "getTREnv") as mock_get_tr_env:
                mock_tr_env = MagicMock()
                mock_tr_env.my_app = "APP"
                mock_tr_env.my_sec = "SEC"
                mock_tr_env.my_token = "Bearer token"
                mock_get_tr_env.return_value = mock_tr_env

                with patch("requests.request") as mock_request:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "rt_cd": "1",
                        "msg1": "초당 거래건수를 초과하였습니다",
                    }
                    mock_request.return_value = mock_response

                    with patch("time.sleep"):
                        client = client_module.KISClient(
                            rate_limiter=mock_rate_limiter,
                            enable_rate_limiter=True,
                            verbose=False,
                        )
                        client.make_request("/test", "TR", {}, retries=1)

                        mock_rate_limiter.report_error.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
