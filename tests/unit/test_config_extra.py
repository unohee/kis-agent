"""
Config 모듈 추가 테스트

KISConfig 클래스의 추가적인 기능과 엣지 케이스를 테스트합니다.

테스트 대상:
- 모든 매개변수를 포함한 초기화
- 설정값 검증 로직 (validation)
- 누락된 매개변수에 대한 에러 처리
- 문자열/repr 표현 형식
- 계좌 관련 프로퍼티 동작

검증 항목:
- 필수 필드 누락 시 적절한 에러 메시지
- 여러 필드가 동시에 누락된 경우 처리
- 프로퍼티를 통한 데이터 접근 안정성
- 설정 객체의 문자열 표현 형식
"""

import unittest
from unittest.mock import Mock, patch
import pytest

from pykis.core.config import KISConfig


class TestKISConfigExtra(unittest.TestCase):
    """KISConfig 추가 테스트"""

    def test_init_with_all_params(self):
        """모든 파라미터로 초기화"""
        config = KISConfig(
            app_key="test_app_key",
            app_secret="test_app_secret",
            account_no="12345",
            account_code="01",
        )

        self.assertEqual(config.app_key, "test_app_key")
        self.assertEqual(config.app_secret, "test_app_secret")
        self.assertEqual(config.account_no, "12345")
        self.assertEqual(config.ACCOUNT_CODE, "01")

    def test_validate_config_success(self):
        """설정 검증 성공"""
        config = KISConfig(
            app_key="valid_key",
            app_secret="valid_secret",
            account_no="12345",
            account_code="01",
        )

        # 예외가 발생하지 않으면 성공 (_validate는 초기화 시 자동 호출됨)
        self.assertEqual(config.app_key, "valid_key")

    def test_validate_config_missing_app_key(self):
        """app_key 누락 시 검증 실패"""
        with self.assertRaises(ValueError) as context:
            KISConfig(
                app_key=None,
                app_secret="valid_secret",
                account_no="12345",
                account_code="01",
            )

        self.assertIn("app_key", str(context.exception))

    def test_validate_config_missing_app_secret(self):
        """app_secret 누락 시 검증 실패"""
        with self.assertRaises(ValueError) as context:
            KISConfig(
                app_key="valid_key",
                app_secret="",
                account_no="12345",
                account_code="01",
            )

        self.assertIn("app_secret", str(context.exception))

    def test_validate_config_missing_account_no(self):
        """account_no 누락 시 검증 실패"""
        with self.assertRaises(ValueError) as context:
            KISConfig(
                app_key="valid_key",
                app_secret="valid_secret",
                account_no=None,
                account_code="01",
            )

        self.assertIn("account_no", str(context.exception))

    def test_validate_config_missing_account_code(self):
        """account_code 누락 시 검증 실패"""
        with self.assertRaises(ValueError) as context:
            KISConfig(
                app_key="valid_key",
                app_secret="valid_secret",
                account_no="12345",
                account_code="",
            )

        self.assertIn("account_code", str(context.exception))

    def test_validate_config_multiple_missing(self):
        """여러 파라미터 누락 시 모두 표시"""
        with self.assertRaises(ValueError) as context:
            KISConfig(app_key="", app_secret="", account_no="", account_code="")

        error_msg = str(context.exception)
        self.assertIn("app_key", error_msg)
        self.assertIn("app_secret", error_msg)
        self.assertIn("account_no", error_msg)
        self.assertIn("account_code", error_msg)

    def test_str_representation(self):
        """문자열 표현 테스트"""
        config = KISConfig(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345",
            account_code="01",
        )

        str_repr = str(config)
        self.assertIn("KISConfig", str_repr)
        # 실제 구현에서는 민감한 정보가 포함됨
        self.assertIn("test_key", str_repr)
        self.assertIn("test_secret", str_repr)

    def test_repr_representation(self):
        """repr 표현 테스트"""
        config = KISConfig(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345",
            account_code="01",
        )

        repr_str = repr(config)
        self.assertIn("KISConfig", repr_str)
        # 실제 구현에서는 전체 정보가 표시됨
        self.assertIn("test_key", repr_str)
        self.assertIn("test_secret", repr_str)

    def test_account_properties(self):
        """계좌 관련 프로퍼티 테스트"""
        config = KISConfig(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345",
            account_code="01",
        )

        # 계좌 관련 프로퍼티들 테스트
        self.assertEqual(config.account_stock, "12345")
        self.assertEqual(config.account_product, "01")
        self.assertEqual(config.account_product_code, "01")


if __name__ == "__main__":
    unittest.main()
