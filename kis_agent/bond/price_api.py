"""장내채권 시세 API

[장내채권] 기본시세 (domestic-bond/v1/quotations/*). 모의투자 미지원.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from typing import Any, Dict, List, Optional  # noqa: F401

from ..core.base_api import BaseAPI
from ..core.tr_mapping import PaperTradingNotSupportedError  # noqa: F401


class BondPriceAPI(BaseAPI):
    """장내채권 시세"""
