"""PyKIS MCP Server - Main server implementation"""

import logging
from typing import Optional

from fastmcp import FastMCP
from pykis import Agent

from .config import MCPServerConfig
from .errors import ConfigurationError

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pykis-mcp-server")

# Set log levels for different components
logging.getLogger("pykis").setLevel(logging.WARNING)  # Reduce noise from PyKIS library
logging.getLogger("pykis.core.rate_limiter").setLevel(
    logging.INFO
)  # Important for monitoring

# Global server and agent instances
server = FastMCP("pykis-mcp-server")
_agent: Optional[Agent] = None
_config: Optional[MCPServerConfig] = None


def get_config() -> MCPServerConfig:
    """Get or create configuration instance

    Returns:
        MCPServerConfig: Server configuration

    Raises:
        ConfigurationError: If configuration is invalid
    """
    global _config
    if _config is None:
        try:
            _config = MCPServerConfig.from_env()
            logger.info("Configuration loaded successfully")
        except ValueError as e:
            raise ConfigurationError(str(e))
    return _config


def get_agent() -> Agent:
    """Get or create PyKIS Agent instance (singleton)

    Returns:
        Agent: PyKIS Agent instance

    Raises:
        ConfigurationError: If agent creation fails
    """
    global _agent
    if _agent is None:
        config = get_config()
        try:
            _agent = Agent(**config.to_agent_kwargs())
            logger.info(
                f"PyKIS Agent initialized "
                f"(account: {config.account_no}, "
                f"rate_limiter: {config.enable_rate_limiter})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize PyKIS Agent: {e}")
            raise ConfigurationError(f"Failed to initialize PyKIS Agent: {e}")
    return _agent


# Import tools after server instance is created
# CONSOLIDATED VERSION: Uses 18 high-level tools instead of 100+ individual tools
from .tools import consolidated_tools  # noqa: F401, E402

# Legacy individual tool modules (commented out, kept for reference)
# from .tools import (  # noqa: E402
#     stock_tools,
#     account_tools,
#     order_tools,
#     investor_tools,
#     utility_tools,
#     rate_limiter_tools,
#     orchestration_tools,
# )


def main():
    """Main entry point for MCP server"""
    try:
        # Initialize configuration and agent
        config = get_config()
        logger.info(f"Starting {config.server_name} v{config.server_version}")

        # Set logging level from config
        logging.getLogger().setLevel(config.log_level)

        # Pre-initialize agent to fail fast if configuration is invalid
        get_agent()

        # Run server using FastMCP
        server.run()
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
