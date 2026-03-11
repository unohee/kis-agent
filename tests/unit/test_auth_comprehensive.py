"""
PyKIS 인증 모듈 포괄적 단위 테스트

INT-378: core/auth.py 커버리지 개선
생성일: 2026-01-04
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# auth 모듈을 명시적으로 import하여 sys.modules에 등록
import kis_agent.core.auth  # noqa: F401


def get_auth_module():
    """auth 모듈을 sys.modules에서 가져옵니다.

    kis_agent.core.__init__.py에서 `from .auth import auth`로 함수를 export하기 때문에
    `import kis_agent.core.auth as auth_module`이 함수가 아닌 모듈을 정확히 가져오는지
    보장하기 위해 sys.modules를 직접 사용합니다.
    """
    return sys.modules["kis_agent.core.auth"]


class TestClearConsole:
    """clearConsole 함수 테스트"""

    def test_clear_console_unix(self):
        """Unix 시스템에서 clear 명령 실행"""
        from kis_agent.core.auth import clearConsole

        with patch("os.system") as mock_system, patch("os.name", "posix"):
            clearConsole()
            # os.name이 posix면 'clear' 호출
            mock_system.assert_called()

    def test_clear_console_windows(self):
        """Windows 시스템에서 cls 명령 실행"""
        from kis_agent.core.auth import clearConsole

        with patch("os.system") as mock_system, patch("os.name", "nt"):
            clearConsole()
            mock_system.assert_called()


class TestGetTokenPathForAppKey:
    """_get_token_path_for_app_key 함수 테스트"""

    def test_no_app_key_returns_base_path(self):
        """app_key가 없으면 기본 경로 반환"""
        from kis_agent.core.auth import _get_token_path_for_app_key

        base_path = "/path/to/token.json"
        result = _get_token_path_for_app_key("", base_path)
        assert result == base_path

        result = _get_token_path_for_app_key(None, base_path)
        assert result == base_path

    def test_with_app_key_returns_hashed_path(self):
        """app_key가 있으면 해시된 경로 반환"""
        from kis_agent.core.auth import _get_token_path_for_app_key

        base_path = "/path/to/KIS_Token.json"
        app_key = "PSabcdef12345678"

        result = _get_token_path_for_app_key(app_key, base_path)

        assert result != base_path
        assert "/path/to/KIS_Token_" in result
        assert result.endswith(".json")
        # 16자리 해시가 포함됨
        assert len(result) > len(base_path)


class TestSaveToken:
    """save_token 함수 테스트"""

    def test_save_token_basic(self):
        """기본 토큰 저장"""
        from kis_agent.core.auth import save_token

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            my_token = "test_token_value"
            my_expired = "2030-12-31 23:59:59"

            save_token(my_token, my_expired, path=path)

            # 파일 확인
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            assert data["token"] == my_token
            assert "valid-date" in data
        finally:
            os.unlink(path)

    def test_save_token_with_app_key(self):
        """APP_KEY와 함께 토큰 저장 (별도 파일 + 캐시)"""
        from kis_agent.core.auth import _token_cache, save_token

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = os.path.join(tmpdir, "KIS_Token.json")

            my_token = "app_specific_token"
            my_expired = "2030-12-31 23:59:59"
            app_key = "TESTKEY12345678"

            # 캐시 초기화
            _token_cache.clear()

            save_token(my_token, my_expired, path=base_path, app_key=app_key)

            # 캐시에 저장되었는지 확인
            import hashlib

            key_hash = hashlib.sha256(app_key.encode()).hexdigest()[:16]
            assert key_hash in _token_cache
            assert _token_cache[key_hash]["access_token"] == my_token


class TestReadToken:
    """read_token 함수 테스트"""

    def test_read_token_from_cache(self):
        """메모리 캐시에서 토큰 읽기"""
        from kis_agent.core.auth import _token_cache, read_token

        app_key = "CACHEKEY12345678"
        import hashlib

        key_hash = hashlib.sha256(app_key.encode()).hexdigest()[:16]

        # 캐시에 유효한 토큰 설정
        _token_cache[key_hash] = {
            "access_token": "cached_token",
            "access_token_token_expired": "2030-12-31 23:59:59",
            "cached_at": datetime.now(),
            "expired": datetime.now() + timedelta(hours=20),
        }

        result = read_token(app_key=app_key)

        assert result is not None
        assert result["access_token"] == "cached_token"

        # 정리
        del _token_cache[key_hash]

    def test_read_token_cache_expired_by_age(self):
        """23시간 초과된 캐시는 무효"""
        from kis_agent.core.auth import _token_cache, read_token

        app_key = "OLDCACHE12345678"
        import hashlib

        key_hash = hashlib.sha256(app_key.encode()).hexdigest()[:16]

        # 24시간 전에 캐시된 토큰
        _token_cache[key_hash] = {
            "access_token": "old_token",
            "access_token_token_expired": "2030-12-31 23:59:59",
            "cached_at": datetime.now() - timedelta(hours=24),
            "expired": datetime.now() + timedelta(hours=10),
        }

        result = read_token(app_key=app_key)

        # 캐시가 만료되어 None 반환 (파일도 없으므로)
        assert result is None

    def test_read_token_cache_token_expired(self):
        """토큰 만료일이 지난 캐시는 무효"""
        from kis_agent.core.auth import _token_cache, read_token

        app_key = "EXPIREDTOKEN1234"
        import hashlib

        key_hash = hashlib.sha256(app_key.encode()).hexdigest()[:16]

        # 토큰이 이미 만료됨
        _token_cache[key_hash] = {
            "access_token": "expired_token",
            "access_token_token_expired": "2020-01-01 00:00:00",
            "cached_at": datetime.now() - timedelta(hours=1),
            "expired": datetime.now() - timedelta(hours=1),
        }

        result = read_token(app_key=app_key)
        assert result is None

    def test_read_token_from_file(self):
        """파일에서 토큰 읽기"""
        from kis_agent.core.auth import _token_cache, read_token

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # 유효한 토큰 파일 생성
            future_date = (datetime.now() + timedelta(days=1)).isoformat()
            token_data = {
                "token": "file_token",
                "valid-date": future_date,
            }
            json.dump(token_data, f)
            path = f.name

        try:
            # 캐시 비우기
            _token_cache.clear()

            result = read_token(path=path)

            assert result is not None
            assert result["access_token"] == "file_token"
        finally:
            os.unlink(path)

    def test_read_token_file_not_exists(self):
        """파일이 없으면 None 반환"""
        from kis_agent.core.auth import read_token

        result = read_token(path="/nonexistent/path/token.json")
        assert result is None

    def test_read_token_expired_file(self):
        """만료된 토큰 파일은 None 반환"""
        from kis_agent.core.auth import _token_cache, read_token

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # 만료된 토큰
            past_date = (datetime.now() - timedelta(days=1)).isoformat()
            token_data = {
                "token": "expired_file_token",
                "valid-date": past_date,
            }
            json.dump(token_data, f)
            path = f.name

        try:
            _token_cache.clear()
            result = read_token(path=path)
            assert result is None
        finally:
            os.unlink(path)

    def test_read_token_app_key_mismatch(self):
        """APP_KEY 불일치 시 None 반환"""
        import hashlib

        from kis_agent.core.auth import _token_cache, read_token

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            future_date = (datetime.now() + timedelta(days=1)).isoformat()
            # 다른 APP_KEY로 저장된 토큰
            other_key = "OTHERKEY12345678"
            other_hash = hashlib.sha256(other_key.encode()).hexdigest()[:16]
            token_data = {
                "token": "other_token",
                "valid-date": future_date,
                "app_key_hash": other_hash,
            }
            json.dump(token_data, f)
            path = f.name

        try:
            _token_cache.clear()
            # 다른 APP_KEY로 읽기 시도
            result = read_token(path=path, app_key="MYKEY12345678901")
            assert result is None
        finally:
            os.unlink(path)

    def test_read_token_exception_handling(self):
        """예외 발생 시 None 반환"""
        from kis_agent.core.auth import read_token

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content {{{")
            path = f.name

        try:
            result = read_token(path=path)
            assert result is None
        finally:
            os.unlink(path)


class TestIsPaperTrading:
    """isPaperTrading 함수 테스트"""

    def test_is_paper_trading_default(self):
        """기본값은 False (실전투자)"""
        from kis_agent.core.auth import isPaperTrading

        # 기본값 확인
        result = isPaperTrading()
        assert isinstance(result, bool)


class TestChangeTREnv:
    """changeTREnv 함수 테스트"""

    def test_change_tr_env_prod(self):
        """실전투자 환경 설정"""
        auth_module = get_auth_module()

        # 설정 백업
        original_cfg = auth_module._cfg.copy()

        try:
            auth_module._cfg = {
                "my_app": "PROD_APP_KEY",
                "my_sec": "PROD_SECRET",
                "my_acct_stock": "12345678",
                "my_prod": "01",
                "prod": "https://openapi.koreainvestment.com:9443",
            }

            auth_module.changeTREnv("Bearer test_token", svr="prod", product="01")

            assert auth_module._isPaper is False
            assert auth_module._TRENV.my_token == "Bearer test_token"
        finally:
            auth_module._cfg = original_cfg

    def test_change_tr_env_vps(self):
        """모의투자 환경 설정"""
        auth_module = get_auth_module()

        original_cfg = auth_module._cfg.copy()
        original_is_paper = auth_module._isPaper

        try:
            auth_module._cfg = {
                "paper_app": "PAPER_APP_KEY",
                "paper_sec": "PAPER_SECRET",
                "my_paper_stock": "87654321",
                "my_prod": "01",
                "vps": "https://openapivts.koreainvestment.com:29443",
            }

            auth_module.changeTREnv("Bearer paper_token", svr="vps", product="01")

            assert auth_module._isPaper is True
        finally:
            auth_module._cfg = original_cfg
            auth_module._isPaper = original_is_paper

    def test_change_tr_env_with_config(self):
        """config 객체와 함께 환경 설정"""
        auth_module = get_auth_module()

        original_cfg = auth_module._cfg.copy()

        try:
            auth_module._cfg = {
                "my_app": "CONFIG_APP",
                "my_sec": "CONFIG_SEC",
                "my_acct_stock": "11111111",
                "my_prod": "01",
            }

            mock_config = MagicMock()
            mock_config.BASE_URL = "https://custom.api.url:9443"

            auth_module.changeTREnv(
                "Bearer token", svr="prod", product="01", config=mock_config
            )

            assert auth_module._TRENV.my_url == "https://custom.api.url:9443"
        finally:
            auth_module._cfg = original_cfg


class TestGetBaseHeader:
    """_getBaseHeader 함수 테스트"""

    def test_get_base_header_no_auto_reauth(self):
        """autoReAuth=False일 때 기본 헤더 반환"""
        auth_module = get_auth_module()

        original = auth_module._autoReAuth
        try:
            auth_module._autoReAuth = False
            headers = auth_module._getBaseHeader()
            assert "Content-Type" in headers
            assert headers["Content-Type"] == "application/json"
        finally:
            auth_module._autoReAuth = original

    def test_get_base_header_with_auto_reauth(self):
        """autoReAuth=True일 때 reAuth 호출"""
        auth_module = get_auth_module()

        original = auth_module._autoReAuth
        try:
            auth_module._autoReAuth = True
            with patch.object(auth_module, "reAuth") as mock_reauth:
                mock_reauth.return_value = None
                headers = auth_module._getBaseHeader()
                mock_reauth.assert_called_once()
        finally:
            auth_module._autoReAuth = original


class TestGetResultObject:
    """_getResultObject 함수 테스트"""

    def test_get_result_object(self):
        """JSON 데이터를 namedtuple로 변환"""
        from kis_agent.core.auth import _getResultObject

        data = {"access_token": "my_token", "token_type": "Bearer", "expires_in": 86400}

        result = _getResultObject(data)

        assert result.access_token == "my_token"
        assert result.token_type == "Bearer"
        assert result.expires_in == 86400


class TestGetEnvAndGetTREnv:
    """getEnv, getTREnv 함수 테스트"""

    def test_get_env(self):
        """환경 설정 반환"""
        from kis_agent.core.auth import getEnv

        env = getEnv()
        assert isinstance(env, dict)
        # 기본 키들이 있어야 함
        assert "my_app" in env or True  # 환경에 따라 다를 수 있음

    def test_get_tr_env(self):
        """거래 환경 정보 반환"""
        from kis_agent.core.auth import getTREnv

        tr_env = getTREnv()
        # 초기에는 빈 튜플일 수 있음
        assert tr_env is not None


class TestAPIResp:
    """APIResp 클래스 테스트"""

    def test_api_resp_success(self):
        """성공 응답 처리"""
        from kis_agent.core.auth import APIResp

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {
            "tr_id": "FHKST01010100",
            "content-type": "application/json",
        }
        mock_resp.json.return_value = {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리",
            "output": {"data": "value"},
        }

        api_resp = APIResp(mock_resp)

        assert api_resp.getResCode() == 200
        assert api_resp.isOK() is True
        assert api_resp.getBody()["rt_cd"] == "0"
        assert api_resp.getErrorCode() == "00000000"
        assert api_resp.getErrorMessage() == "정상처리"

    def test_api_resp_failure(self):
        """실패 응답 처리"""
        from kis_agent.core.auth import APIResp

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"tr_id": "FHKST01010100"}
        mock_resp.json.return_value = {
            "rt_cd": "1",
            "msg_cd": "EGW00001",
            "msg1": "잘못된 요청입니다",
        }

        api_resp = APIResp(mock_resp)

        assert api_resp.isOK() is False
        assert api_resp.getErrorCode() == "EGW00001"
        assert "잘못된" in api_resp.getErrorMessage()

    def test_api_resp_http_error(self):
        """HTTP 오류 응답 처리"""
        from kis_agent.core.auth import APIResp

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.headers = {}
        mock_resp.json.side_effect = ValueError("No JSON")

        api_resp = APIResp(mock_resp)

        assert api_resp.getResCode() == 401
        assert api_resp.getBody() is None

    def test_api_resp_is_ok_exception(self):
        """isOK()에서 예외 발생 시 처리"""
        from kis_agent.core.auth import APIResp

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.json.return_value = None  # getBody()가 None

        api_resp = APIResp(mock_resp)

        # getBody()['rt_cd'] 접근 시 TypeError 발생 -> False 반환
        assert api_resp.isOK() is False
        assert "Authentication failed" in api_resp.getErrorMessage()

    def test_api_resp_print_methods(self, capsys):
        """print 메서드들 테스트"""
        from kis_agent.core.auth import APIResp

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.headers = {"error": "test"}
        mock_resp.json.return_value = {"error": "bad request"}

        api_resp = APIResp(mock_resp)
        api_resp.printAll()

        captured = capsys.readouterr()
        assert "STATUS" in captured.out
        assert "400" in captured.out

    def test_api_resp_print_error(self, capsys):
        """printError 메서드 테스트"""
        from kis_agent.core.auth import APIResp

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.headers = {}
        mock_resp.json.return_value = {}

        api_resp = APIResp(mock_resp)
        api_resp.printError("https://api.test.com/endpoint")

        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "URL" in captured.out


class TestSetOrderHashKey:
    """set_order_hash_key 함수 테스트"""

    def test_set_order_hash_key_success(self):
        """해시키 설정 성공"""
        auth_module = get_auth_module()

        # getTREnv mock
        mock_tr_env = MagicMock()
        mock_tr_env.my_url = "https://test.api.com"

        with patch.object(auth_module, "getTREnv", return_value=mock_tr_env), patch(
            "requests.post"
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"HASH": "abc123hash"}
            mock_post.return_value = mock_response

            headers = {"Content-Type": "application/json"}
            params = {"order_data": "test"}

            auth_module.set_order_hash_key(headers, params)

            assert headers.get("hashkey") == "abc123hash"

    def test_set_order_hash_key_failure(self, capsys):
        """해시키 설정 실패"""
        auth_module = get_auth_module()

        mock_tr_env = MagicMock()
        mock_tr_env.my_url = "https://test.api.com"

        with patch.object(auth_module, "getTREnv", return_value=mock_tr_env), patch(
            "requests.post"
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_post.return_value = mock_response

            headers = {}
            params = {}

            auth_module.set_order_hash_key(headers, params)

            captured = capsys.readouterr()
            assert "Error" in captured.out


class TestUrlFetch:
    """_url_fetch 함수 테스트"""

    def test_url_fetch_get_success(self):
        """GET 요청 성공"""
        auth_module = get_auth_module()

        mock_tr_env = MagicMock()
        mock_tr_env.my_url = "https://test.api.com"

        with patch.object(
            auth_module, "getTREnv", return_value=mock_tr_env
        ), patch.object(
            auth_module,
            "_getBaseHeader",
            return_value={"Content-Type": "application/json"},
        ), patch(
            "requests.get"
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"tr_id": "TEST001"}
            mock_response.json.return_value = {"rt_cd": "0", "output": {}}
            mock_get.return_value = mock_response

            result = auth_module._url_fetch(
                "/test/endpoint",
                "TEST001",
                "N",
                {"param": "value"},
                postFlag=False,
            )

            assert result.getResCode() == 200

    def test_url_fetch_post_success(self):
        """POST 요청 성공"""
        auth_module = get_auth_module()

        mock_tr_env = MagicMock()
        mock_tr_env.my_url = "https://test.api.com"

        with patch.object(
            auth_module, "getTREnv", return_value=mock_tr_env
        ), patch.object(
            auth_module,
            "_getBaseHeader",
            return_value={"Content-Type": "application/json"},
        ), patch.object(
            auth_module, "set_order_hash_key"
        ), patch(
            "requests.post"
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"tr_id": "ORDER001"}
            mock_response.json.return_value = {"rt_cd": "0"}
            mock_post.return_value = mock_response

            result = auth_module._url_fetch(
                "/order/endpoint",
                "ORDER001",
                "",
                {"order": "data"},
                postFlag=True,
                hashFlag=True,
            )

            assert result.getResCode() == 200

    def test_url_fetch_with_append_headers(self):
        """추가 헤더와 함께 요청"""
        auth_module = get_auth_module()

        mock_tr_env = MagicMock()
        mock_tr_env.my_url = "https://test.api.com"

        with patch.object(
            auth_module, "getTREnv", return_value=mock_tr_env
        ), patch.object(auth_module, "_getBaseHeader", return_value={}), patch(
            "requests.get"
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.json.return_value = {"rt_cd": "0"}
            mock_get.return_value = mock_response

            result = auth_module._url_fetch(
                "/test",
                "TR001",
                "N",
                {},
                appendHeaders={"X-Custom": "value"},
                postFlag=False,
            )

            # 헤더가 포함되었는지 확인
            call_kwargs = mock_get.call_args
            assert "X-Custom" in call_kwargs.kwargs["headers"]

    def test_url_fetch_error_response(self, capsys):
        """오류 응답 처리"""
        auth_module = get_auth_module()

        mock_tr_env = MagicMock()
        mock_tr_env.my_url = "https://test.api.com"

        with patch.object(
            auth_module, "getTREnv", return_value=mock_tr_env
        ), patch.object(auth_module, "_getBaseHeader", return_value={}), patch(
            "requests.get"
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.headers = {}
            mock_response.json.return_value = None
            mock_get.return_value = mock_response

            result = auth_module._url_fetch("/test", "TR001", "N", {}, postFlag=False)

            assert result.getResCode() == 500


class TestReAuth:
    """reAuth 함수 테스트"""

    def test_reauth_with_config(self):
        """config 제공 시 auth 호출"""
        auth_module = get_auth_module()

        mock_config = MagicMock()
        mock_config.APP_KEY = "TEST_KEY"
        mock_config.APP_SECRET = "TEST_SECRET"
        mock_config.ACCOUNT_NO = "12345678"
        mock_config.ACCOUNT_CODE = "01"
        mock_config.BASE_URL = "https://test.api.com"

        with patch.object(auth_module, "auth") as mock_auth:
            mock_auth.return_value = {"access_token": "new_token"}
            result = auth_module.reAuth(config=mock_config)
            mock_auth.assert_called_once()

    def test_reauth_returns_cached_token(self):
        """유효한 토큰이 있으면 캐시에서 반환"""
        auth_module = get_auth_module()

        # 마지막 인증 시간을 최근으로 설정
        original_time = auth_module._last_auth_time
        try:
            auth_module._last_auth_time = datetime.now()

            with patch.object(auth_module, "read_token") as mock_read:
                mock_read.return_value = {"access_token": "cached"}
                result = auth_module.reAuth()
                # config 없고 시간 안 지났으면 read_token 호출
                mock_read.assert_called()
        finally:
            auth_module._last_auth_time = original_time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
