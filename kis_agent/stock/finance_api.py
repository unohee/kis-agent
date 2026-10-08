"""국내주식 종목정보·재무 API

[국내주식] 종목정보 메뉴: 상품기본조회, 투자의견, 추정실적, 당사 신용/대주 가능종목,
재무제표(대차대조표·손익계산서·수익성/안정성/성장성/기타 비율).

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from typing import Any, Dict, List, Optional  # noqa: F401

from ..core.base_api import BaseAPI
from ..core.tr_mapping import PaperTradingNotSupportedError  # noqa: F401


class StockFinanceAPI(BaseAPI):
    """국내주식 종목정보·재무"""
