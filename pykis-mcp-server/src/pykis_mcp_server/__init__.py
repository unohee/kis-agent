"""PyKIS MCP Server

한국투자증권 OpenAPI를 MCP 프로토콜로 제공하는 서버
"""

__version__ = "0.1.0"
__all__ = ["start_server"]

from .server import main as start_server
