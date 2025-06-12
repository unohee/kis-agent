"""
테스트 설정을 관리하는 모듈입니다.
"""
import os
import pytest
from kis.core.config import KISConfig

@pytest.fixture
def account_info():
    """테스트용 계좌 정보를 반환합니다."""
    config = KISConfig()
    return {
        "CANO": config.account_stock,
        "ACNT_PRDT_CD": config.account_product
    }

@pytest.fixture
def test_stock_code():
    """테스트용 종목 코드를 반환합니다."""
    return "005930"  # 삼성전자 