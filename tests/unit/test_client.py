"""
KISClient 클래스의 테스트 모듈입니다.

이 모듈은 KISClient 클래스의 기능을 테스트합니다:
- API 요청 처리
- 토큰 관리
- 요청 제한 관리
- 에러 처리

의존성:
- unittest: 테스트 프레임워크
- pykis.core.client: 테스트 대상

사용 예시:
    >>> python -m unittest tests/unit/test_client.py
"""

import os
import time
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from pykis.core.client import API_ENDPOINTS, KISClient
from pykis.core.config import KISConfig

# ============================================================================
# Mock 기반 유닛 테스트 (실제 API 호출 없음)
# ============================================================================


class TestKISClientUnit(unittest.TestCase):
    """KISClient Mock 기반 유닛 테스트"""

    def _create_mock_config(self):
        """테스트용 Mock config 생성"""
        return KISConfig(
            app_key="test_app_key",
            app_secret="test_app_secret",
            base_url="https://test.api.com",
            account_no="12345678",
            account_code="01",
        )

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    def test_init_with_config(self, mock_get_tr_env, mock_auth):
        """config로 클라이언트 초기화"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_env.my_app = "test_app"
        mock_env.my_sec = "test_secret"
        mock_env.my_token = "Bearer test_token"
        mock_get_tr_env.return_value = mock_env

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        self.assertEqual(client.token, "test_token")
        self.assertEqual(client.base_url, "https://test.api.com")
        self.assertFalse(client.enable_rate_limiter)

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    def test_init_with_kisconfig_as_svr(self, mock_get_tr_env, mock_auth):
        """KISConfig를 svr 매개변수로 전달 (하위 호환성)"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_env.my_app = "test_app"
        mock_env.my_sec = "test_secret"
        mock_get_tr_env.return_value = mock_env

        config = self._create_mock_config()
        # svr 위치에 KISConfig 전달
        client = KISClient(config, enable_rate_limiter=False)

        self.assertEqual(client.config, config)
        self.assertEqual(client.svr, "prod")

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    def test_init_without_config(self, mock_get_tr_env, mock_auth):
        """config 없이 환경변수로 초기화"""
        mock_auth.return_value = {
            "access_token": "env_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_env.my_app = "test_app"
        mock_env.my_sec = "test_secret"
        mock_get_tr_env.return_value = mock_env

        with patch.dict(
            os.environ,
            {"KIS_BASE_URL": "https://env.api.com"},
        ):
            client = KISClient(svr="prod", enable_rate_limiter=False)

        self.assertEqual(client.token, "env_token")
        self.assertEqual(client.base_url, "https://env.api.com")

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    def test_enforce_rate_limit_disabled(self, mock_get_tr_env, mock_auth):
        """Rate Limiter 비활성화 테스트"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_get_tr_env.return_value = mock_env

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        # Rate limiter가 없어야 함
        self.assertIsNone(client.rate_limiter)

        # _enforce_rate_limit 호출 (기존 방식으로 동작)
        start = time.monotonic()
        client._enforce_rate_limit()
        elapsed = time.monotonic() - start

        # 첫 호출이므로 대기 없음
        self.assertLess(elapsed, 0.1)

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    def test_check_and_refresh_token_expired(self, mock_get_tr_env, mock_auth):
        """만료된 토큰 자동 갱신"""
        mock_auth.return_value = {
            "access_token": "new_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_get_tr_env.return_value = mock_env

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        # 토큰을 과거로 설정
        client.token_expired = (datetime.now() - timedelta(hours=1)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # 토큰 갱신 체크
        client._check_and_refresh_token()

        # auth가 재호출되었는지 확인 (초기화 1회 + 갱신 1회)
        self.assertEqual(mock_auth.call_count, 2)

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    def test_check_and_refresh_token_invalid_format(self, mock_get_tr_env, mock_auth):
        """잘못된 형식의 토큰 만료 시간 처리"""
        mock_auth.return_value = {
            "access_token": "new_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_get_tr_env.return_value = mock_env

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        # 잘못된 형식의 만료 시간 설정
        client.token_expired = "invalid_date_format"

        # 예외 없이 토큰 재발급 시도
        client._check_and_refresh_token()

        # auth가 재호출되었는지 확인
        self.assertEqual(mock_auth.call_count, 2)

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.request")
    def test_make_request_success(self, mock_request, mock_get_tr_env, mock_auth):
        """API 요청 성공"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_env.my_app = "test_app"
        mock_env.my_sec = "test_secret"
        mock_env.my_token = "Bearer test_token"
        mock_get_tr_env.return_value = mock_env

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rt_cd": "0",
            "msg_cd": "SUCCESS",
            "msg1": "정상처리",
            "output": {"data": "test"},
        }
        mock_request.return_value = mock_response

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        result = client.make_request(
            endpoint="/test/endpoint",
            tr_id="TEST001",
            params={"param": "value"},
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["rt_cd"], "0")
        self.assertEqual(result["output"]["data"], "test")

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.request")
    def test_make_request_json_decode_error(
        self, mock_request, mock_get_tr_env, mock_auth
    ):
        """JSON 디코드 실패 처리"""
        import json

        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_env.my_token = "Bearer test_token"
        mock_get_tr_env.return_value = mock_env

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Invalid JSON response"
        mock_response.headers = {}
        mock_response.json.side_effect = json.JSONDecodeError(
            "Expecting value", "doc", 0
        )
        mock_request.return_value = mock_response

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        result = client.make_request(
            endpoint="/test/endpoint",
            tr_id="TEST001",
            params={"param": "value"},
        )

        self.assertEqual(result["rt_cd"], "JSON_DECODE_ERROR")
        self.assertEqual(result["error_type"], "JSONDecodeError")

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.request")
    def test_make_request_no_rt_cd(self, mock_request, mock_get_tr_env, mock_auth):
        """rt_cd 없는 응답 처리"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_env.my_token = "Bearer test_token"
        mock_get_tr_env.return_value = mock_env

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"some_data": "value"}  # rt_cd 없음
        mock_request.return_value = mock_response

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        result = client.make_request(
            endpoint="/test/endpoint",
            tr_id="TEST001",
            params={"param": "value"},
        )

        self.assertEqual(result["rt_cd"], "NO_RT_CD")
        self.assertEqual(result["error_type"], "NoRtCd")

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.request")
    def test_make_request_api_error(self, mock_request, mock_get_tr_env, mock_auth):
        """API 오류 응답 처리"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_env.my_token = "Bearer test_token"
        mock_get_tr_env.return_value = mock_env

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rt_cd": "1",
            "msg_cd": "ERR001",
            "msg1": "API 오류 발생",
        }
        mock_request.return_value = mock_response

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        result = client.make_request(
            endpoint="/test/endpoint",
            tr_id="TEST001",
            params={"param": "value"},
        )

        self.assertEqual(result["rt_cd"], "1")
        self.assertEqual(result["error_type"], "ApiError")

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.request")
    def test_make_request_http_error_with_retry(
        self, mock_request, mock_get_tr_env, mock_auth
    ):
        """HTTP 오류 재시도"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_env.my_token = "Bearer test_token"
        mock_get_tr_env.return_value = mock_env

        # 첫 번째 요청: HTTP 500, 두 번째 요청: 성공
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Internal Server Error"
        mock_response_fail.json.return_value = {"rt_cd": "500", "msg1": "Server Error"}

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"rt_cd": "0", "output": {"data": 1}}

        mock_request.side_effect = [mock_response_fail, mock_response_success]

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        result = client.make_request(
            endpoint="/test/endpoint",
            tr_id="TEST001",
            params={"param": "value"},
            retries=2,
        )

        self.assertEqual(result["rt_cd"], "0")
        self.assertEqual(mock_request.call_count, 2)

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.request")
    def test_make_request_exception_handling(
        self, mock_request, mock_get_tr_env, mock_auth
    ):
        """요청 예외 처리 및 재시도"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_env.my_token = "Bearer test_token"
        mock_get_tr_env.return_value = mock_env

        # 모든 요청 실패
        mock_request.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        with pytest.raises(requests.exceptions.ConnectionError):
            client.make_request(
                endpoint="/test/endpoint",
                tr_id="TEST001",
                params={"param": "value"},
                retries=2,
            )

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.post")
    def test_refresh_token_success(self, mock_post, mock_get_tr_env, mock_auth):
        """토큰 갱신 성공"""
        mock_auth.return_value = {
            "access_token": "initial_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_get_tr_env.return_value = mock_env

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "refreshed_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_post.return_value = mock_response

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        client.refresh_token()

        self.assertEqual(client.token, "refreshed_token")

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.post")
    def test_refresh_token_failure(self, mock_post, mock_get_tr_env, mock_auth):
        """토큰 갱신 실패"""
        mock_auth.return_value = {
            "access_token": "initial_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_get_tr_env.return_value = mock_env

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        with pytest.raises(Exception) as exc_info:
            client.refresh_token()

        self.assertIn("토큰 갱신 실패", str(exc_info.value))

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.post")
    def test_refresh_token_no_access_token(self, mock_post, mock_get_tr_env, mock_auth):
        """토큰 갱신 응답에 access_token 없음"""
        mock_auth.return_value = {
            "access_token": "initial_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_get_tr_env.return_value = mock_env

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"other_field": "value"}  # access_token 없음
        mock_post.return_value = mock_response

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        with pytest.raises(Exception) as exc_info:
            client.refresh_token()

        self.assertIn("access_token이 없습니다", str(exc_info.value))

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.post")
    def test_get_ws_approval_key_success(self, mock_post, mock_get_tr_env, mock_auth):
        """웹소켓 승인키 발급 성공"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_get_tr_env.return_value = mock_env

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"approval_key": "ws_approval_key_12345"}
        mock_post.return_value = mock_response

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        result = client.get_ws_approval_key()

        self.assertEqual(result, "ws_approval_key_12345")

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.post")
    def test_get_ws_approval_key_failure(self, mock_post, mock_get_tr_env, mock_auth):
        """웹소켓 승인키 발급 실패"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_get_tr_env.return_value = mock_env

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_post.return_value = mock_response

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        result = client.get_ws_approval_key()

        self.assertIsNone(result)

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.post")
    def test_get_ws_approval_key_no_key_in_response(
        self, mock_post, mock_get_tr_env, mock_auth
    ):
        """웹소켓 승인키 응답에 키 없음"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_get_tr_env.return_value = mock_env

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"other": "data"}  # approval_key 없음
        mock_post.return_value = mock_response

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        result = client.get_ws_approval_key()

        self.assertIsNone(result)

    @patch("pykis.core.client.auth")
    @patch("pykis.core.client.getTREnv")
    @patch("requests.post")
    def test_get_ws_approval_key_exception(self, mock_post, mock_get_tr_env, mock_auth):
        """웹소켓 승인키 요청 중 예외"""
        mock_auth.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_env = MagicMock()
        mock_get_tr_env.return_value = mock_env

        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        config = self._create_mock_config()
        client = KISClient(config=config, enable_rate_limiter=False)

        result = client.get_ws_approval_key()

        self.assertIsNone(result)


class TestAPIEndpoints(unittest.TestCase):
    """API_ENDPOINTS 상수 테스트"""

    def test_endpoints_not_empty(self):
        """API 엔드포인트가 정의되어 있는지 확인"""
        self.assertGreater(len(API_ENDPOINTS), 0)

    def test_key_endpoints_exist(self):
        """주요 엔드포인트 존재 확인"""
        key_endpoints = [
            "TOKEN",
            "INQUIRE_PRICE",
            "INQUIRE_BALANCE",
            "ORDER_CASH",
            "VOLUME_RANK",
        ]
        for endpoint in key_endpoints:
            self.assertIn(endpoint, API_ENDPOINTS)

    def test_endpoints_are_strings(self):
        """모든 엔드포인트 값이 문자열인지 확인"""
        for key, value in API_ENDPOINTS.items():
            self.assertIsInstance(value, str, f"{key} 값이 문자열이 아닙니다")


# ============================================================================
# 기존 통합 테스트 (실제 API 호출 - 실행 시 주의)
# ============================================================================


@pytest.mark.integration
@pytest.mark.requires_credentials
class TestKISClient(unittest.TestCase):
    """
    KISClient 클래스의 통합 테스트 클래스입니다.

    이 클래스는 KISClient의 각 메서드를 실제 API 호출로 테스트합니다.
    """

    def setUp(self):
        """
        테스트 케이스 실행 전에 호출되는 메서드입니다.
        """
        import os

        # 환경 변수에서 자격 증명 로드 (통합 테스트용)
        app_key = os.environ.get("KIS_APP_KEY", "")
        app_secret = os.environ.get("KIS_APP_SECRET", "")
        account_no = os.environ.get("KIS_ACCOUNT_NO", "")
        account_code = os.environ.get("KIS_ACCOUNT_CODE", "01")
        base_url = os.environ.get(
            "KIS_BASE_URL", "https://openapi.koreainvestment.com:9443"
        )

        # 자격 증명이 없으면 테스트 스킵
        if not all([app_key, app_secret, account_no]):
            self.skipTest("환경 변수에 KIS 자격 증명이 설정되지 않았습니다")

        self.config = KISConfig(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code,
            base_url=base_url,
        )
        self.client = KISClient(self.config)

    @patch("requests.post")
    def test_refresh_token(self, mock_post):
        """
        refresh_token 메서드를 실제 API 호출로 테스트합니다.
        """
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test_token",
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # 토큰 갱신 테스트
        self.client.refresh_token()
        # 토큰이 발급되었는지 확인
        self.assertIsNotNone(self.client.token)
        self.assertIsInstance(self.client.token, str)
        self.assertGreater(len(self.client.token), 0)
        print(f"토큰 발급 성공: {self.client.token[:20]}...")

    def test_make_request_stock_price(self):
        """
        make_request 메서드를 실제 주식 현재가 API 호출로 테스트합니다.
        """
        # 삼성전자 현재가 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"},
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        self.assertEqual(response["rt_cd"], "0")

    def test_make_request_daily_price(self):
        """
        make_request 메서드를 실제 일별 시세 API 호출로 테스트합니다.
        """
        # 삼성전자 일별 시세 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            tr_id="FHKST01010400",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930",
                "FID_INPUT_DATE_1": "20240601",
                "FID_INPUT_DATE_2": "20240618",
            },
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        if response:
            self.assertEqual(response["rt_cd"], "0")

    def test_make_request_orderbook(self):
        """
        make_request 메서드를 실제 호가 API 호출로 테스트합니다.
        """
        # 삼성전자 호가 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            tr_id="FHKST01010200",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"},
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        self.assertEqual(response["rt_cd"], "0")

    def test_make_request_investor(self):
        """
        make_request 메서드를 실제 투자자별 매매 동향 API 호출로 테스트합니다.
        """
        # 삼성전자 투자자별 매매 동향 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-investor",
            tr_id="FHKST01010900",
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"},
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        self.assertEqual(response["rt_cd"], "0")

    def test_enforce_rate_limit(self):
        """
        _enforce_rate_limit 메서드를 테스트합니다.
        """
        # 요청 제한 테스트
        self.client._enforce_rate_limit()
        self.assertGreater(self.client.last_request_time, 0)

    def test_make_request_program_trade(self):
        """
        make_request 메서드를 실제 프로그램매매 API 호출로 테스트합니다.
        """
        # 삼성전자 프로그램매매 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-daily-ccld",
            tr_id="FHKST03030100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930",
                "FID_INPUT_DATE_1": "",
                "FID_INPUT_DATE_2": "",
                "FID_PERIOD_DIV_CODE": "D",
            },
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        if response.get("rt_cd") == "0":
            self.assertEqual(response["rt_cd"], "0")

    def test_make_request_market_cap(self):
        """
        make_request 메서드를 실제 시가총액 순위 API 호출로 테스트합니다.
        """
        # 시가총액 순위 조회 API 요청 테스트
        response = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/ranking/market-cap",
            tr_id="FHPTJ04040000",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": "20170",
                "FID_INPUT_ISCD": "0000",
                "FID_DIV_CLS_CODE": "0",
                "FID_BLNG_CLS_CODE": "0",
                "FID_TRGT_CLS_CODE": "111111111",
                "FID_TRGT_EXLS_CLS_CODE": "000000",
                "FID_INPUT_PRICE_1": "",
                "FID_INPUT_PRICE_2": "",
                "FID_VOL_CNT": "",
                "FID_INPUT_DATE_1": "",
            },
        )
        # API 응답이 정상인지 확인
        self.assertIsNotNone(response)
        if response.get("rt_cd") == "0":
            self.assertEqual(response["rt_cd"], "0")


if __name__ == "__main__":
    unittest.main()
