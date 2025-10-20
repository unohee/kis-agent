"""Tests for MCP tools"""
import pytest
from unittest.mock import Mock, patch


class TestErrorHandling:
    """Test error handling in tools"""

    def test_invalid_stock_code_length(self):
        """Test that invalid stock code length raises error"""
        from pykis_mcp_server.errors import InvalidParameterError

        with pytest.raises(InvalidParameterError) as exc_info:
            raise InvalidParameterError("code", "종목코드는 6자리여야 합니다")

        assert "종목코드는 6자리여야 합니다" in str(exc_info.value)

    def test_api_error_handling(self):
        """Test API error handling"""
        from pykis_mcp_server.errors import APIError

        error = APIError("Test error", rt_cd="40", msg1="Invalid request")

        assert str(error) == "Test error"
        assert error.details["rt_cd"] == "40"
        assert error.details["msg1"] == "Invalid request"

    def test_validate_api_response_success(self):
        """Test validate_api_response with successful response"""
        from pykis_mcp_server.errors import validate_api_response

        result = {
            "rt_cd": "0",
            "msg1": "Success",
            "output": {"data": "test"}
        }

        validated = validate_api_response(result, "Test operation")
        assert validated == result

    def test_validate_api_response_failure(self):
        """Test validate_api_response with failed response"""
        from pykis_mcp_server.errors import validate_api_response, APIError

        result = {
            "rt_cd": "40",
            "msg1": "Invalid request",
            "msg_cd": "EGW00001"
        }

        with pytest.raises(APIError) as exc_info:
            validate_api_response(result, "Test operation")

        assert "Test operation failed" in str(exc_info.value)

    def test_validate_api_response_none(self):
        """Test validate_api_response with None response"""
        from pykis_mcp_server.errors import validate_api_response, APIError

        with pytest.raises(APIError) as exc_info:
            validate_api_response(None, "Test operation")

        assert "No response from API" in str(exc_info.value)


class TestConfiguration:
    """Test configuration management"""

    def test_config_from_env(self, mock_env_vars):
        """Test loading config from environment variables"""
        from pykis_mcp_server.config import MCPServerConfig

        config = MCPServerConfig.from_env()

        assert config.app_key == "test_app_key"
        assert config.app_secret == "test_secret"
        assert config.account_no == "12345678"
        assert config.account_code == "01"

    def test_config_to_agent_kwargs(self, mock_env_vars):
        """Test converting config to Agent kwargs"""
        from pykis_mcp_server.config import MCPServerConfig

        config = MCPServerConfig.from_env()
        kwargs = config.to_agent_kwargs()

        assert "app_key" in kwargs
        assert "app_secret" in kwargs
        assert "account_no" in kwargs
        assert "enable_rate_limiter" in kwargs

    def test_config_missing_required(self, monkeypatch):
        """Test that missing required config raises error"""
        from pykis_mcp_server.config import MCPServerConfig

        # Clear all env vars
        monkeypatch.delenv("KIS_APP_KEY", raising=False)
        monkeypatch.delenv("KIS_SECRET", raising=False)
        monkeypatch.delenv("KIS_ACCOUNT_NO", raising=False)

        with pytest.raises(ValueError):
            MCPServerConfig.from_env()


class TestToolRegistration:
    """Test that tools are properly registered"""

    def test_all_tool_modules_imported(self):
        """Test that all tool modules are imported"""
        from pykis_mcp_server import tools

        assert hasattr(tools, 'stock_tools')
        assert hasattr(tools, 'account_tools')
        assert hasattr(tools, 'order_tools')
        assert hasattr(tools, 'investor_tools')
        assert hasattr(tools, 'utility_tools')
        assert hasattr(tools, 'rate_limiter_tools')

    def test_server_has_tools_registered(self):
        """Test that server has tools registered"""
        from pykis_mcp_server.server import server

        # Server should have tools registered
        assert server is not None
        assert hasattr(server, '_request_handlers')


class TestRetryableErrors:
    """Test retryable error detection"""

    def test_is_retryable_error(self):
        """Test that rate limit errors are detected as retryable"""
        from pykis_mcp_server.errors import is_retryable_error

        # Rate limit errors should be retryable
        assert is_retryable_error("EGW00201") is True
        assert is_retryable_error("EGW00202") is True
        assert is_retryable_error("EGW00503") is True

        # Other errors should not be retryable
        assert is_retryable_error("40") is False
        assert is_retryable_error("50") is False
        assert is_retryable_error("EGW00123") is False


class TestErrorCodeMappings:
    """Test error code mappings"""

    def test_get_error_code(self):
        """Test error code mapping"""
        from pykis_mcp_server.errors import get_error_code
        from mcp.types import ErrorCode

        # Success should return no error
        assert get_error_code("0") is None

        # Invalid request
        assert get_error_code("40") == ErrorCode.INVALID_REQUEST

        # Server error
        assert get_error_code("50") == ErrorCode.INTERNAL_ERROR

        # Unknown error should default to INTERNAL_ERROR
        assert get_error_code("unknown") == ErrorCode.INTERNAL_ERROR
