"""Error handling for PyKIS MCP Server"""
import logging
from enum import IntEnum
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ErrorCode(IntEnum):
    """Custom error codes for MCP compatibility"""
    INTERNAL_ERROR = -32603
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602


class PyKISMCPError(Exception):
    """Base exception for PyKIS MCP Server"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

        # Log error with structured information
        logger.error(
            f"PyKISMCPError: {message}",
            extra={
                "error_code": error_code.value if hasattr(error_code, 'value') else str(error_code),
                "details": self.details
            }
        )


class ConfigurationError(PyKISMCPError):
    """Configuration error"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCode.INVALID_PARAMS, details)


class APIError(PyKISMCPError):
    """PyKIS API call error"""

    def __init__(self, message: str, rt_cd: Optional[str] = None, msg1: Optional[str] = None):
        details = {}
        if rt_cd:
            details["rt_cd"] = rt_cd
        if msg1:
            details["msg1"] = msg1
        super().__init__(message, ErrorCode.INTERNAL_ERROR, details)


class RateLimitError(PyKISMCPError):
    """Rate limit exceeded"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, ErrorCode.INTERNAL_ERROR)


class InvalidParameterError(PyKISMCPError):
    """Invalid parameter provided"""

    def __init__(self, parameter: str, message: str):
        super().__init__(f"Invalid parameter '{parameter}': {message}", ErrorCode.INVALID_PARAMS)


# Error code mappings from PyKIS API response codes
# Based on Korea Investment Securities OpenAPI specification
ERROR_CODE_MAPPINGS = {
    "0": None,  # Success
    "40": ErrorCode.INVALID_REQUEST,  # Invalid request
    "50": ErrorCode.INTERNAL_ERROR,  # Server error
    "99": ErrorCode.METHOD_NOT_FOUND,  # API not supported
    # Rate limit errors
    "EGW00201": ErrorCode.INTERNAL_ERROR,  # Exceeded per-second limit
    "EGW00202": ErrorCode.INTERNAL_ERROR,  # Exceeded per-minute limit
    "EGW00203": ErrorCode.INTERNAL_ERROR,  # Exceeded daily limit
    # Authentication errors
    "EGW00123": ErrorCode.INVALID_REQUEST,  # Invalid token
    "EGW00124": ErrorCode.INVALID_REQUEST,  # Token expired
    # Parameter validation errors
    "EGW00133": ErrorCode.INVALID_PARAMS,  # Required parameter missing
    "EGW00134": ErrorCode.INVALID_PARAMS,  # Invalid parameter format
    # System errors
    "EGW00500": ErrorCode.INTERNAL_ERROR,  # Internal server error
    "EGW00503": ErrorCode.INTERNAL_ERROR,  # Service unavailable
}


def get_error_code(rt_cd: str) -> ErrorCode:
    """Get MCP error code from PyKIS API response code

    Args:
        rt_cd: PyKIS API response code

    Returns:
        ErrorCode: MCP error code
    """
    return ERROR_CODE_MAPPINGS.get(rt_cd, ErrorCode.INTERNAL_ERROR)


def is_retryable_error(rt_cd: str) -> bool:
    """Check if error is retryable

    Args:
        rt_cd: PyKIS API response code

    Returns:
        bool: True if error is retryable
    """
    # Rate limit errors and temporary system errors are retryable
    retryable_codes = [
        "EGW00201",  # Exceeded per-second limit
        "EGW00202",  # Exceeded per-minute limit
        "EGW00503",  # Service unavailable
    ]
    return rt_cd in retryable_codes


def validate_api_response(
    result: Optional[Dict[str, Any]],
    operation: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate PyKIS API response with detailed logging

    Args:
        result: API response
        operation: Operation name for error messages
        context: Additional context for logging (e.g., parameters used)

    Returns:
        Dict: Validated API response

    Raises:
        APIError: If response is invalid or indicates error
    """
    # Log operation attempt
    logger.info(f"Validating API response for operation: {operation}", extra={"context": context})

    if result is None:
        logger.error(f"{operation} failed: No response from API", extra={"context": context})
        raise APIError(f"{operation} failed: No response from API")

    rt_cd = result.get("rt_cd", "")
    msg1 = result.get("msg1", "")
    msg_cd = result.get("msg_cd", "")

    if rt_cd != "0":
        # Determine if error is retryable
        retryable = is_retryable_error(rt_cd)

        # Log detailed error information
        logger.error(
            f"{operation} failed: {msg1 or 'Unknown error'}",
            extra={
                "rt_cd": rt_cd,
                "msg_cd": msg_cd,
                "msg1": msg1,
                "retryable": retryable,
                "context": context
            }
        )

        # Raise appropriate error with retry hint
        error = APIError(
            f"{operation} failed: {msg1 or 'Unknown error'}",
            rt_cd=rt_cd,
            msg1=msg1
        )
        error.details["retryable"] = retryable
        error.details["msg_cd"] = msg_cd
        raise error

    # Log success
    logger.debug(f"{operation} completed successfully", extra={"context": context})
    return result


def format_error_response(error: Exception, operation: str) -> Dict[str, Any]:
    """Format error as JSON response

    Args:
        error: Exception that occurred
        operation: Operation that failed

    Returns:
        Dict: Formatted error response
    """
    if isinstance(error, PyKISMCPError):
        return {
            "success": False,
            "error": str(error),
            "error_code": error.error_code.value if hasattr(error.error_code, 'value') else str(error.error_code),
            "details": error.details,
            "operation": operation
        }
    else:
        return {
            "success": False,
            "error": str(error),
            "error_code": "UNKNOWN_ERROR",
            "operation": operation
        }
