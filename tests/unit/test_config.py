import unittest
from unittest.mock import patch, mock_open
import os
from pykis.core.config import KISConfig

class TestKISConfig(unittest.TestCase):
    """
    KISConfig 클래스의 단위 테스트 클래스입니다.
    """

    def setUp(self):
        """
        테스트 케이스 실행 전에 호출되는 메서드입니다.
        """
        self.test_env_vars = {
            'KIS_APP_KEY': 'test_app_key',
            'KIS_APP_SECRET': 'test_app_secret',
            'KIS_BASE_URL': 'https://test.api.com',
            'KIS_ACCOUNT_NO': '1234567890',
            'KIS_ACCOUNT_CODE': '01'
        }

    @patch('os.path.exists', return_value=True)
    @patch('dotenv.load_dotenv')
    @patch.dict(os.environ, {}, clear=True)
    def test_init_with_env_file(self, mock_load_dotenv, mock_exists):
        """
        .env 파일을 사용한 초기화를 테스트합니다.
        """
        # .env 파일이 로드될 때 환경 변수를 설정하도록 mock_load_dotenv를 설정
        def side_effect(*args, **kwargs):
            os.environ.update(self.test_env_vars)
        mock_load_dotenv.side_effect = side_effect

        config = KISConfig()

        self.assertEqual(config.APP_KEY, 'test_app_key')
        self.assertEqual(config.APP_SECRET, 'test_app_secret')
        self.assertEqual(config.BASE_URL, 'https://test.api.com')
        self.assertEqual(config.ACCOUNT_NO, '1234567890')
        self.assertEqual(config.ACCOUNT_CODE, '01')
        mock_load_dotenv.assert_called_once_with(dotenv_path=".env")

    @patch('os.path.exists', return_value=False)
    def test_init_without_env_file(self, mock_exists):
        """
        .env 파일이 없을 때 FileNotFoundError를 발생하는지 테스트합니다.
        """
        with self.assertRaises(FileNotFoundError):
            KISConfig()

    @patch('os.path.exists', return_value=True)
    @patch('dotenv.load_dotenv')
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_config_missing_values(self, mock_load_dotenv, mock_exists):
        """
        필수 설정 값이 누락되었을 때 예외를 발생하는지 테스트합니다.
        """
        # .env 파일이 로드될 때 일부 환경 변수만 설정하도록 mock_load_dotenv를 설정
        def side_effect(*args, **kwargs):
            os.environ.update({'KIS_APP_KEY': 'test_app_key'})
        mock_load_dotenv.side_effect = side_effect

        with self.assertRaisesRegex(Exception, "필수 설정 값이 누락되었습니다"):
            KISConfig()

    @patch('os.path.exists', return_value=True)
    @patch('dotenv.load_dotenv')
    def test_init_with_custom_path(self, mock_load_dotenv, mock_exists):
        """
        사용자 정의 .env 파일 경로로 초기화를 테스트합니다.
        """
        config = KISConfig(env_path='/custom/path/.env')
        mock_load_dotenv.assert_called_with(dotenv_path='/custom/path/.env')

if __name__ == '__main__':
    unittest.main()