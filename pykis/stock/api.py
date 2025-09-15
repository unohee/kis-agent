"""
Compatibility shim: StockAPI

레거시 경로 `pykis.stock.api.StockAPI`를 새 구조의 Facade로 연결합니다.
이 모듈은 구현을 포함하지 않으며, 신규 `api_facade.StockAPI`만 노출합니다.
"""

from .api_facade import StockAPI  # noqa: F401

__all__ = ["StockAPI"]

