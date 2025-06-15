"""
KISClient 클래스의 단위 테스트 모듈입니다.

이 모듈은 KISClient 클래스의 기능을 테스트합니다:
- API 요청 처리
- 토큰 관리
- 요청 제한 관리
- 에러 처리

의존성:
- unittest: 테스트 프레임워크
- unittest.mock: 모킹
- pykis.core.client: 테스트 대상
- pykis.core.config: 설정 관리

사용 예시:
    >>> python -m unittest tests/unit/test_client.py
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import requests
import os

from pykis.core.client import KISClient
from pykis.core.config import KISConfig

class TestKISClient(unittest.TestCase):
    """
    KISClient 클래스의 단위 테스트 클래스입니다.

    이 클래스는 KISClient의 각 메서드를 테스트합니다.
    """

    def setUp(self):
        """
        테스트 케이스 실행 전에 호출되는 메서드입니다.
        """
        os.environ.setdefault('KIS_APP_KEY', 'k')
        os.environ.setdefault('KIS_APP_SECRET', 's')
        os.environ.setdefault('KIS_BASE_URL', 'http://test')
        os.environ.setdefault('KIS_ACCOUNT_NO', '11111111')
        os.environ.setdefault('KIS_ACCOUNT_CODE', '01')
        self.config = KISConfig()
        self.client = KISClient(self.config)

    @patch('requests.post')
    def test_refresh_token(self, mock_post):
        """
        refresh_token 메서드를 테스트합니다.
        """
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 86400
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # 토큰 갱신 테스트
        self.client.refresh_token()
        self.assertEqual(self.client.token, 'test_token')

    @patch('requests.request')
    def test_make_request(self, mock_request):
        """
        make_request 메서드를 테스트합니다.
        """
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = {'rt_cd': '0', 'msg1': '성공'}
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # API 요청 테스트
        response = self.client.make_request(
            endpoint='/test',
            tr_id='TEST001',
            params={'test': 'value'}
        )
        self.assertEqual(response['rt_cd'], '0')

    @patch('requests.request')
    def test_make_request_error(self, mock_request):
        """
        make_request 메서드의 에러 처리를 테스트합니다.
        """
        # Mock 에러 응답 설정
        mock_request.side_effect = requests.exceptions.RequestException('API 오류')

        # 에러 처리 테스트
        with self.assertRaises(Exception):
            self.client.make_request(
                endpoint='/test',
                tr_id='TEST001',
                params={'test': 'value'}
            )

    def test_enforce_rate_limit(self):
        """
        _enforce_rate_limit 메서드를 테스트합니다.
        """
        # 요청 제한 테스트
        self.client._enforce_rate_limit()
        self.assertGreater(self.client.last_request_time, 0)

if __name__ == '__main__':
    unittest.main() 