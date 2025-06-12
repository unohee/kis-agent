"""
auth 모듈의 단위 테스트 모듈입니다.

이 모듈은 auth 모듈의 기능을 테스트합니다:
- 토큰 발급
- 토큰 갱신
- 토큰 저장 및 읽기

의존성:
- unittest: 테스트 프레임워크
- unittest.mock: 모킹
- kis.core.auth: 테스트 대상
- kis.core.config: 설정 관리

사용 예시:
    >>> python -m unittest tests/unit/test_auth.py
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import requests

from kis.core.auth import auth, reAuth, read_token
from kis.core.config import KISConfig

class TestAuth(unittest.TestCase):
    """
    auth 모듈의 단위 테스트 클래스입니다.

    이 클래스는 auth 모듈의 각 함수를 테스트합니다.
    """

    def setUp(self):
        """
        테스트 케이스 실행 전에 호출되는 메서드입니다.
        """
        self.config = KISConfig()
        self.test_token = {
            'access_token': 'test_token',
            'expires_in': 86400,
            'expires_at': 1234567890
        }

    @patch('requests.post')
    def test_auth(self, mock_post):
        """
        auth 함수를 테스트합니다.
        """
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = self.test_token
        mock_post.return_value = mock_response

        # 토큰 발급 테스트
        token = auth(self.config)
        self.assertEqual(token['access_token'], 'test_token')

    @patch('requests.post')
    def test_reAuth(self, mock_post):
        """
        reAuth 함수를 테스트합니다.
        """
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = self.test_token
        mock_post.return_value = mock_response

        # 토큰 갱신 테스트
        token = reAuth(self.config)
        self.assertEqual(token['access_token'], 'test_token')

    def test_read_token(self):
        """
        read_token 함수를 테스트합니다.
        """
        # 테스트 토큰 파일 생성
        token_path = os.path.join(os.path.dirname(__file__), 'token.json')
        with open(token_path, 'w') as f:
            json.dump(self.test_token, f)

        try:
            # 토큰 읽기 테스트
            token = read_token()
            self.assertEqual(token['access_token'], 'test_token')
        finally:
            # 테스트 토큰 파일 삭제
            if os.path.exists(token_path):
                os.remove(token_path)

    @patch('requests.post')
    def test_auth_error(self, mock_post):
        """
        auth 함수의 에러 처리를 테스트합니다.
        """
        # Mock 에러 응답 설정
        mock_post.side_effect = requests.exceptions.RequestException('API 오류')

        # 에러 처리 테스트
        with self.assertRaises(Exception):
            auth(self.config)

if __name__ == '__main__':
    unittest.main() 