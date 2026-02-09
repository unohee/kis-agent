"""MCP Tools for PyKIS

This module exports all MCP tools for the PyKIS server.
Tools are automatically registered with the server through decorators.

CONSOLIDATED VERSION: Uses 18 high-level tools instead of 100+ individual tools
to reduce context window pressure for LLMs.
"""

# Import consolidated tools (18 tools replacing 110+ individual tools)
from . import consolidated_tools  # noqa: F401

# Legacy individual tool modules (commented out, kept for reference)
# from . import stock_tools  # noqa: F401
# from . import account_tools  # noqa: F401
# from . import order_tools  # noqa: F401
# from . import investor_tools  # noqa: F401
# from . import utility_tools  # noqa: F401
# from . import rate_limiter_tools  # noqa: F401
# from . import orchestration_tools  # noqa: F401

__all__ = [
    "consolidated_tools",
]
