"""
auth 모듈의 단위 테스트 모듈입니다.

이 모듈은 auth 모듈의 기능을 테스트합니다:
- 토큰 발급
- 토큰 갱신
- 토큰 저장 및 읽기
- APIResp 클래스
- 유틸리티 함수

의존성:
- unittest: 테스트 프레임워크
- unittest.mock: 모킹
- kis.core.auth: 테스트 대상
- kis.core.config: 설정 관리

사용 예시:
    >>> python -m unittest tests/unit/test_auth.py
"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import requests

from kis_agent.core.auth import (
    APIResp,
    _get_token_path_for_app_key,
    auth,
    changeTREnv,
    clearConsole,
    getEnv,
    getTREnv,
    isPaperTrading,
    read_token,
    reAuth,
    save_token,
    set_order_hash_key,
)
from kis_agent.core.config import KISConfig


class TestAuth(unittest.TestCase):
    """
    auth 모듈의 단위 테스트 클래스입니다.

    이 클래스는 auth 모듈의 각 함수를 테스트합니다.
    """

    def setUp(self):
        """
        테스트 케이스 실행 전에 호출되는 메서드입니다.
        """
        # KISConfig는 직접 매개변수를 받아야 함
        self.config = KISConfig(
            app_key="test_app_key",
            app_secret="test_app_secret",
            base_url="http://test.api.com",
            account_no="11111111",
            account_code="01",
        )
        self.test_token = {
            "access_token": "test_token",
            "expires_in": 86400,
            "expires_at": 1234567890,
        }

    @patch("kis_agent.core.auth.save_token")
    @patch("kis_agent.core.auth.read_token")
    @patch("requests.post")
    def test_auth(self, mock_post, mock_read_token, mock_save_token):
        """
        auth 함수를 테스트합니다.
        """
        # Mock 응답 설정
        mock_read_token.return_value = None
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # 토큰 발급 테스트
        token = auth(self.config)
        self.assertEqual(
            token,
            {
                "access_token": "test_token",
                "access_token_token_expired": "2099-01-01 00:00:00",
            },
        )
        mock_save_token.assert_called_once()

    @patch("kis_agent.core.auth.save_token")
    @patch("kis_agent.core.auth.read_token")
    @patch("requests.post")
    def test_reAuth(self, mock_post, mock_read_token, mock_save_token):
        """
        reAuth 함수를 테스트합니다.
        """
        # Mock 응답 설정
        mock_read_token.return_value = None
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-01-01 00:00:00",
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # 토큰 갱신 테스트
        token = reAuth(self.config)
        self.assertEqual(
            token,
            {
                "access_token": "test_token",
                "access_token_token_expired": "2099-01-01 00:00:00",
            },
        )
        mock_save_token.assert_called_once()

    def test_read_token(self):
        """
        read_token 함수를 테스트합니다.
        """
        # 테스트 토큰 파일 생성
        token_path = os.path.join(os.path.dirname(__file__), "token.json")
        with open(token_path, "w") as f:
            json.dump(self.test_token, f)

        try:
            # 토큰 읽기 테스트
            token = read_token(token_path)
            self.assertEqual(token["access_token"], "test_token")
        finally:
            # 테스트 토큰 파일 삭제
            if os.path.exists(token_path):
                os.remove(token_path)

    @patch("kis_agent.core.auth.save_token")
    @patch("kis_agent.core.auth.read_token")
    @patch("requests.post")
    def test_auth_error(self, mock_post, mock_read_token, mock_save_token):
        """
        auth 함수의 에러 처리를 테스트합니다.

        auth 함수는 requests.post에서 예외가 발생하면 그대로 예외를 발생시킵니다.
        """
        # Mock 에러 응답 설정
        mock_read_token.return_value = None
        mock_post.side_effect = requests.exceptions.RequestException("API 오류")

        # 에러 시 예외가 발생해야 함
        with self.assertRaises(requests.exceptions.RequestException):
            auth(self.config)
        mock_save_token.assert_not_called()


class TestTokenPathForAppKey(unittest.TestCase):
    """_get_token_path_for_app_key 함수 테스트"""

    def test_empty_app_key_returns_base_path(self):
        """app_key가 비어있으면 기본 경로 반환"""
        base_path = "/some/path/token.json"
        result = _get_token_path_for_app_key("", base_path)
        self.assertEqual(result, base_path)

    def test_none_app_key_returns_base_path(self):
        """app_key가 None이면 기본 경로 반환"""
        base_path = "/some/path/token.json"
        result = _get_token_path_for_app_key(None, base_path)
        self.assertEqual(result, base_path)

    def test_app_key_creates_unique_path(self):
        """app_key가 있으면 고유한 경로 생성"""
        base_path = "/some/path/token.json"
        app_key = "ABCD1234EFGH5678"
        result = _get_token_path_for_app_key(app_key, base_path)
        self.assertIn("ABCD1234", result)
        self.assertIn("token_", result)
        self.assertTrue(result.endswith(".json"))

    def test_short_app_key(self):
        """짧은 app_key 처리"""
        base_path = "/some/path/token.json"
        app_key = "ABC"  # 8자리 미만
        result = _get_token_path_for_app_key(app_key, base_path)
        self.assertIn("ABC", result)


class TestSaveAndReadToken(unittest.TestCase):
    """save_token 및 read_token 함수 테스트"""

    def setUp(self):
        """임시 디렉토리 생성"""
        self.temp_dir = tempfile.mkdtemp()
        self.token_path = os.path.join(self.temp_dir, "test_token.json")

    def tearDown(self):
        """임시 파일 정리"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_save_and_read_token_without_app_key(self):
        """app_key 없이 토큰 저장 및 읽기"""
        future_time = (datetime.now() + timedelta(hours=12)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        save_token("test_token_value", future_time, path=self.token_path)

        result = read_token(path=self.token_path)
        self.assertIsNotNone(result)
        self.assertEqual(result["access_token"], "test_token_value")

    def test_save_and_read_token_with_app_key(self):
        """app_key와 함께 토큰 저장 및 읽기"""
        future_time = (datetime.now() + timedelta(hours=12)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        app_key = "TESTKEY1234"
        save_token(
            "test_token_with_key", future_time, path=self.token_path, app_key=app_key
        )

        # 같은 app_key로 읽기
        result = read_token(path=self.token_path, app_key=app_key)
        self.assertIsNotNone(result)
        self.assertEqual(result["access_token"], "test_token_with_key")

    def test_read_token_with_wrong_app_key(self):
        """다른 app_key로 읽기 시도 시 None 반환"""
        future_time = (datetime.now() + timedelta(hours=12)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        app_key = "TESTKEY1234"
        save_token("test_token", future_time, path=self.token_path, app_key=app_key)

        # 다른 app_key로 읽기 시도
        result = read_token(path=self.token_path, app_key="WRONGKEY5678")
        self.assertIsNone(result)

    def test_read_expired_token_returns_none(self):
        """만료된 토큰은 None 반환"""
        past_time = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        save_token("expired_token", past_time, path=self.token_path)

        result = read_token(path=self.token_path)
        self.assertIsNone(result)

    def test_read_token_nonexistent_file(self):
        """존재하지 않는 파일 읽기"""
        result = read_token(path="/nonexistent/path/token.json")
        self.assertIsNone(result)

    def test_read_token_invalid_json(self):
        """잘못된 JSON 파일 읽기"""
        with open(self.token_path, "w") as f:
            f.write("invalid json content")

        result = read_token(path=self.token_path)
        self.assertIsNone(result)

    def test_read_token_missing_fields(self):
        """필수 필드가 없는 토큰 파일"""
        with open(self.token_path, "w") as f:
            json.dump({"some_field": "value"}, f)

        result = read_token(path=self.token_path)
        self.assertIsNone(result)


class TestAPIResp(unittest.TestCase):
    """APIResp 클래스 테스트"""

    def test_successful_response(self):
        """성공 응답 처리"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"tr_id": "TTTC0081R", "Content-Type": "application/json"}
        mock_resp.json.return_value = {
            "rt_cd": "0",
            "msg_cd": "SUCCESS",
            "msg1": "정상처리",
            "output": {"data": "test"},
        }

        api_resp = APIResp(mock_resp)

        self.assertEqual(api_resp.getResCode(), 200)
        self.assertTrue(api_resp.isOK())
        self.assertEqual(api_resp.getErrorCode(), "00000000")
        self.assertEqual(api_resp.getErrorMessage(), "정상처리")
        self.assertIsNotNone(api_resp.getBody())
        self.assertIsNotNone(api_resp.getHeader())
        self.assertEqual(api_resp.getResponse(), mock_resp)

    def test_error_response(self):
        """에러 응답 처리"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"tr_id": "TTTC0081R"}
        mock_resp.json.return_value = {
            "rt_cd": "1",
            "msg_cd": "EGW00001",
            "msg1": "에러가 발생했습니다",
        }

        api_resp = APIResp(mock_resp)

        self.assertFalse(api_resp.isOK())
        self.assertEqual(api_resp.getErrorCode(), "EGW00001")
        self.assertEqual(api_resp.getErrorMessage(), "에러가 발생했습니다")

    def test_non_200_response(self):
        """HTTP 200이 아닌 응답"""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.headers = {}
        mock_resp.json.side_effect = ValueError("No JSON")

        api_resp = APIResp(mock_resp)

        self.assertEqual(api_resp.getResCode(), 500)
        self.assertIsNone(api_resp.getBody())

    def test_is_ok_exception_handling(self):
        """isOK 메서드에서 예외 발생 시 처리"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.json.return_value = None  # body가 None이면 예외 발생

        api_resp = APIResp(mock_resp)
        # body가 None이므로 isOK()에서 예외 발생 후 False 반환
        self.assertFalse(api_resp.isOK())

    @patch("builtins.print")
    def test_print_all(self, mock_print):
        """printAll 메서드 테스트"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"tr_id": "TEST"}
        mock_resp.json.return_value = {"rt_cd": "0", "msg_cd": "SUCCESS", "msg1": "OK"}

        api_resp = APIResp(mock_resp)
        api_resp.printAll()

        self.assertTrue(mock_print.called)
        self.assertGreaterEqual(mock_print.call_count, 5)

    @patch("builtins.print")
    def test_print_error(self, mock_print):
        """printError 메서드 테스트"""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.headers = {}
        mock_resp.json.return_value = {"rt_cd": "1", "msg_cd": "ERR", "msg1": "Error"}

        api_resp = APIResp(mock_resp)
        api_resp.printError("http://test.url")

        self.assertTrue(mock_print.called)


class TestUtilityFunctions(unittest.TestCase):
    """유틸리티 함수 테스트"""

    def test_get_env(self):
        """getEnv 함수 테스트"""
        env = getEnv()
        self.assertIsInstance(env, dict)
        self.assertIn("my_app", env)
        self.assertIn("my_sec", env)

    def test_is_paper_trading(self):
        """isPaperTrading 함수 테스트"""
        result = isPaperTrading()
        self.assertIsInstance(result, bool)

    @patch("os.system")
    def test_clear_console(self, mock_system):
        """clearConsole 함수 테스트"""
        mock_system.return_value = 0
        result = clearConsole()
        self.assertTrue(mock_system.called)

    def test_get_tr_env(self):
        """getTREnv 함수 테스트"""
        # 초기 상태에서는 빈 튜플
        result = getTREnv()
        # 튜플이거나 namedtuple이어야 함
        self.assertTrue(isinstance(result, tuple) or hasattr(result, "_fields"))


class TestChangeTREnv(unittest.TestCase):
    """changeTREnv 함수 테스트"""

    def test_change_tr_env_prod(self):
        """실전투자 환경 설정"""
        changeTREnv("Bearer test_token", svr="prod", product="01")
        env = getTREnv()
        # 환경이 설정되었는지 확인 (빈 튜플이 아님)
        if hasattr(env, "my_token"):
            self.assertIn("Bearer", env.my_token)

    def test_change_tr_env_with_config(self):
        """config 객체와 함께 환경 설정"""
        mock_config = MagicMock()
        mock_config.BASE_URL = "http://test.api.com"

        changeTREnv("Bearer test_token", svr="prod", product="01", config=mock_config)
        env = getTREnv()
        if hasattr(env, "my_url"):
            self.assertEqual(env.my_url, "http://test.api.com")


class TestSetOrderHashKey(unittest.TestCase):
    """set_order_hash_key 함수 테스트"""

    @patch("kis_agent.core.auth.getTREnv")
    @patch("requests.post")
    def test_set_order_hash_key_success(self, mock_post, mock_get_tr_env):
        """hashkey 설정 성공"""
        mock_env = MagicMock()
        mock_env.my_url = "http://test.api.com"
        mock_get_tr_env.return_value = mock_env

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"HASH": "test_hash_value"}
        mock_post.return_value = mock_response

        headers = {}
        params = {"key": "value"}
        set_order_hash_key(headers, params)

        self.assertEqual(headers.get("hashkey"), "test_hash_value")

    @patch("kis_agent.core.auth.getTREnv")
    @patch("requests.post")
    @patch("builtins.print")
    def test_set_order_hash_key_error(self, mock_print, mock_post, mock_get_tr_env):
        """hashkey 설정 실패"""
        mock_env = MagicMock()
        mock_env.my_url = "http://test.api.com"
        mock_get_tr_env.return_value = mock_env

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        headers = {}
        params = {"key": "value"}
        set_order_hash_key(headers, params)

        self.assertNotIn("hashkey", headers)
        mock_print.assert_called()


class TestAuthTokenReuse(unittest.TestCase):
    """토큰 재사용 테스트"""

    def setUp(self):
        # KISConfig는 직접 매개변수를 받아야 함
        self.config = KISConfig(
            app_key="test_app_key",
            app_secret="test_app_secret",
            base_url="http://test.api.com",
            account_no="11111111",
            account_code="01",
        )

    @patch("kis_agent.core.auth.read_token")
    def test_auth_uses_saved_token(self, mock_read_token):
        """저장된 유효 토큰이 있으면 재사용"""
        mock_read_token.return_value = {
            "access_token": "saved_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }

        result = auth(self.config)

        self.assertEqual(result["access_token"], "saved_token")


class TestReAuthWithoutConfig(unittest.TestCase):
    """config 없이 reAuth 테스트"""

    @patch("kis_agent.core.auth.read_token")
    def test_reauth_returns_saved_token_within_24h(self, mock_read_token):
        """24시간 이내에는 저장된 토큰 반환"""
        mock_read_token.return_value = {
            "access_token": "cached_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }

        result = reAuth(config=None, svr="prod")

        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
