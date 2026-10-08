"""ELW facade."""

from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient
from .price_api import ElwPriceAPI
from .ranking_api import ElwRankingAPI


class ElwAPI(BaseAPI):
    """ELW(주식워런트증권) 시세·순위 API 파사드 (``agent.elw``).

    하위 API의 공개 메서드를 동적으로 위임한다::

        >>> agent.elw.<method>(...)
    """

    def __init__(
        self,
        client: KISClient,
        account_info: Optional[Dict[str, Any]] = None,
        enable_cache: bool = True,
        cache_config: Optional[Dict[str, Any]] = None,
        _from_agent: bool = False,
    ) -> None:
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )
        self.price_api = ElwPriceAPI(
            client, account_info, enable_cache, cache_config, _from_agent=True
        )
        self.ranking_api = ElwRankingAPI(
            client, account_info, enable_cache, cache_config, _from_agent=True
        )

    def __getattr__(self, name: str) -> Any:
        """하위 API로 동적 위임 (먼저 정의된 하위 API 우선)."""
        if name.startswith("_"):
            raise AttributeError(f"{type(self).__name__} has no attribute '{name}'")
        for api in (
            self.price_api,
            self.ranking_api,
        ):
            if hasattr(api, name):
                return getattr(api, name)
        raise AttributeError(f"{type(self).__name__} has no attribute '{name}'")
