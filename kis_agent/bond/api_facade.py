"""장내채권 facade."""

from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient
from .order_api import BondOrderAPI
from .price_api import BondPriceAPI


class BondAPI(BaseAPI):
    """장내채권 시세·주문/계좌 API 파사드 (``agent.bond``). 모의투자 미지원.

    하위 API의 공개 메서드를 동적으로 위임한다::

        >>> agent.bond.<method>(...)
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
        self.price_api = BondPriceAPI(
            client, account_info, enable_cache, cache_config, _from_agent=True
        )
        self.order_api = BondOrderAPI(
            client, account_info, enable_cache, cache_config, _from_agent=True
        )

    def __getattr__(self, name: str) -> Any:
        """하위 API로 동적 위임 (먼저 정의된 하위 API 우선)."""
        if name.startswith("_"):
            raise AttributeError(f"{type(self).__name__} has no attribute '{name}'")
        for api in (
            self.price_api,
            self.order_api,
        ):
            if hasattr(api, name):
                return getattr(api, name)
        raise AttributeError(f"{type(self).__name__} has no attribute '{name}'")
