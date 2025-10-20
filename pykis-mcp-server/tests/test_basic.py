"""Basic tests for project structure and imports"""
import pytest


def test_package_import():
    """Test that the package can be imported"""
    import pykis_mcp_server

    assert pykis_mcp_server.__version__ == "0.1.0"


def test_tools_module_exists():
    """Test that tools module exists"""
    from pykis_mcp_server import tools

    assert tools is not None


def test_server_module_exists():
    """Test that server module exists"""
    from pykis_mcp_server import server

    assert server is not None
    assert hasattr(server, 'server')
    assert hasattr(server, 'get_agent')
    assert hasattr(server, 'get_config')


def test_mock_env_vars(mock_env_vars):
    """Test that environment variables are mocked correctly"""
    import os

    assert os.getenv("KIS_APP_KEY") == "test_app_key"
    assert os.getenv("KIS_SECRET") == "test_secret"
    assert os.getenv("KIS_ACCOUNT_NO") == "12345678"
    assert os.getenv("KIS_ACCOUNT_CODE") == "01"
