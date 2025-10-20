"""Configuration management for PyKIS MCP Server"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class MCPServerConfig:
    """MCP Server configuration from environment variables"""

    # PyKIS Agent settings
    app_key: str
    app_secret: str
    account_no: str
    account_code: str = "01"
    base_url: Optional[str] = None

    # MCP Server settings
    server_name: str = "pykis-mcp-server"
    server_version: str = "0.1.0"

    # Rate Limiting
    enable_rate_limiter: bool = True
    requests_per_second: int = 18
    requests_per_minute: int = 900

    # Cache
    enable_cache: bool = True
    default_cache_ttl: int = 5

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "MCPServerConfig":
        """Create configuration from environment variables

        Raises:
            ValueError: If required environment variables are missing
        """
        app_key = os.getenv("KIS_APP_KEY")
        app_secret = os.getenv("KIS_SECRET")
        account_no = os.getenv("KIS_ACCOUNT_NO")

        if not all([app_key, app_secret, account_no]):
            missing = []
            if not app_key:
                missing.append("KIS_APP_KEY")
            if not app_secret:
                missing.append("KIS_SECRET")
            if not account_no:
                missing.append("KIS_ACCOUNT_NO")

            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Please set them in your .env file or environment."
            )

        return cls(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=os.getenv("KIS_ACCOUNT_CODE", "01"),
            base_url=os.getenv("KIS_BASE_URL"),
            enable_rate_limiter=os.getenv("ENABLE_RATE_LIMITER", "true").lower()
            == "true",
            requests_per_second=int(os.getenv("REQUESTS_PER_SECOND", "18")),
            requests_per_minute=int(os.getenv("REQUESTS_PER_MINUTE", "900")),
            enable_cache=os.getenv("ENABLE_CACHE", "true").lower() == "true",
            default_cache_ttl=int(os.getenv("DEFAULT_CACHE_TTL", "5")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    def to_agent_kwargs(self) -> dict:
        """Convert config to kwargs for PyKIS Agent initialization"""
        kwargs = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "account_no": self.account_no,
            "account_code": self.account_code,
            "enable_rate_limiter": self.enable_rate_limiter,
        }

        if self.base_url:
            kwargs["base_url"] = self.base_url

        return kwargs
