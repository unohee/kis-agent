"""장내채권 주문/계좌 API

[장내채권] 주문/계좌 (domestic-bond/v1/trading/*). 주문은 POST, 재시도 없음,
캐시 없음(use_cache=False). 모의투자 미지원.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from typing import Any, Dict, List, Optional  # noqa: F401

from ..core.base_api import BaseAPI
from ..core.tr_mapping import PaperTradingNotSupportedError  # noqa: F401


class BondOrderAPI(BaseAPI):
    """장내채권 주문/계좌"""
