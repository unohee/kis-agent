"""ETF/ETN API

ETF/ETN 시세 (etfetn/*): 현재가, 구성종목시세, NAV 비교추이(종목/일/분).

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from typing import Any, Dict, List, Optional  # noqa: F401

from ..core.base_api import BaseAPI
from ..core.tr_mapping import PaperTradingNotSupportedError  # noqa: F401


class StockEtfAPI(BaseAPI):
    """ETF/ETN 시세 (etfetn/*)"""
