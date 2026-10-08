"""국내주식 분봉·시간외 API

당일분봉, 장마감 예상체결가, 시간외 시간별체결 등 기본시세 보강.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from typing import Any, Dict, List, Optional  # noqa: F401

from ..core.base_api import BaseAPI
from ..core.tr_mapping import PaperTradingNotSupportedError  # noqa: F401


class StockChartAPI(BaseAPI):
    """국내주식 분봉·시간외 시세"""
