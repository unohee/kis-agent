"""
config 모듈의 단위 테스트 모듈입니다.

이 모듈은 config 모듈의 기능을 테스트합니다:
- 설정 로드
- 환경 변수 처리
- 설정 유효성 검증

의존성:
- unittest: 테스트 프레임워크
- unittest.mock: 모킹
- kis.core.config: 테스트 대상
- os: 환경 변수 관리

사용 예시:
    >>> python -m unittest tests/unit/test_config.py
"""

import unittest
from unittest.mock import patch, mock_open
import os
import yaml

from kis.core.config import KISConfig

class TestKISConfig(unittest.TestCase):
    """
    KISConfig 클래스의 단위 테스트 클래스입니다.

    이 클래스는 KISConfig의 각 메서드를 테스트합니다.
    """

    def setUp(self):
        """
        테스트 케이스 실행 전에 호출되는 메서드입니다.
        """
        self.test_config = {
            'app_key': 'test_app_key',
            'app_secret': 'test_app_secret',
            'base_url': 'https://test.api.com',
            'account_no': '1234567890',
            'account_code': '01'
        }

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch.dict(os.environ, {
        'KIS_APP_KEY': 'env_app_key',
        'KIS_APP_SECRET': 'env_app_secret',
        'KIS_BASE_URL': 'https://env.api.com',
        'KIS_ACCOUNT_NO': '9876543210',
        'KIS_ACCOUNT_CODE': '02'
    })
    def test_init_with_env(self, mock_yaml_load, mock_file):
        """
        환경 변수를 사용한 초기화를 테스트합니다.
        """
        # Mock YAML 로드 설정
        mock_yaml_load.return_value = self.test_config

        # 설정 초기화 테스트
        config = KISConfig()
        self.assertEqual(config.APP_KEY, 'env_app_key')
        self.assertEqual(config.APP_SECRET, 'env_app_secret')
        self.assertEqual(config.BASE_URL, 'https://env.api.com')
        self.assertEqual(config.ACCOUNT_NO, '9876543210')
        self.assertEqual(config.ACCOUNT_CODE, '02')

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_init_with_file(self, mock_yaml_load, mock_file):
        """
        설정 파일을 사용한 초기화를 테스트합니다.
        """
        # Mock YAML 로드 설정
        mock_yaml_load.return_value = self.test_config

        # 설정 초기화 테스트
        config = KISConfig()
        self.assertEqual(config.APP_KEY, 'test_app_key')
        self.assertEqual(config.APP_SECRET, 'test_app_secret')
        self.assertEqual(config.BASE_URL, 'https://test.api.com')
        self.assertEqual(config.ACCOUNT_NO, '1234567890')
        self.assertEqual(config.ACCOUNT_CODE, '01')

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_validate_config(self, mock_yaml_load, mock_file):
        """
        설정 유효성 검증을 테스트합니다.
        """
        # Mock YAML 로드 설정
        mock_yaml_load.return_value = {}

        # 유효성 검증 테스트
        with self.assertRaises(Exception):
            KISConfig()

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_init_with_custom_path(self, mock_yaml_load, mock_file):
        """
        사용자 정의 경로로 초기화를 테스트합니다.
        """
        # Mock YAML 로드 설정
        mock_yaml_load.return_value = self.test_config

        # 사용자 정의 경로로 초기화 테스트
        config = KISConfig(config_path='/custom/path/config.yaml')
        mock_file.assert_called_with('/custom/path/config.yaml', 'r')

if __name__ == '__main__':
    unittest.main() 