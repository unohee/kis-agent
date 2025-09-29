import os
import unittest
from unittest.mock import patch

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
            "app_key": "test_app_key",
            "app_secret": "test_app_secret",
            "base_url": "https://test.api.com",
            "account_no": "1234567890",
            "account_code": "01",
        }

    def test_init_with_args(self):
        """
        인자를 사용한 초기화를 테스트합니다.
        """
        config = KISConfig(**self.test_env_vars)

        self.assertEqual(config.APP_KEY, "test_app_key")
        self.assertEqual(config.APP_SECRET, "test_app_secret")
        self.assertEqual(config.BASE_URL, "https://test.api.com")
        self.assertEqual(config.ACCOUNT_NO, "1234567890")
        self.assertEqual(config.ACCOUNT_CODE, "01")

    def test_init_without_required_params(self):
        """
        필수 매개변수 없이 초기화할 때 ValueError를 발생하는지 테스트합니다.
        """
        with self.assertRaises(ValueError) as context:
            KISConfig()

        self.assertIn("필수 설정 값이 누락되었습니다", str(context.exception))

    def test_validate_config_missing_values(self):
        """
        필수 설정 값이 누락되었을 때 예외를 발생하는지 테스트합니다.
        """
        with self.assertRaisesRegex(ValueError, "필수 설정 값이 누락되었습니다"):
            KISConfig(
                app_key="test_app_key",
                app_secret="secret",
                base_url="url",
                account_no="no",
                account_code=None,
            )


if __name__ == "__main__":
    unittest.main()
