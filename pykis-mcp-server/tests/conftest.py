"""PyTest configuration and fixtures"""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("KIS_APP_KEY", "test_app_key")
    monkeypatch.setenv("KIS_SECRET", "test_secret")
    monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_ACCOUNT_CODE", "01")


@pytest.fixture
def mock_agent():
    """Mock PyKIS Agent for testing"""
    agent = MagicMock()
    agent.get_stock_price.return_value = {
        "rt_cd": "0",
        "msg1": "정상처리",
        "output": {"stck_prpr": "70000", "prdy_vrss": "1000", "prdy_ctrt": "1.45"},
    }
    return agent
