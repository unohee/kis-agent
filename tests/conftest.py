"""
테스트 설정을 관리하는 모듈입니다.
"""
import os
import sys
import pytest
from pykis import Agent
from pykis.core import auth

# src 디렉토리를 파이썬 경로에 추가하여 패키지를 임포트합니다.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

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