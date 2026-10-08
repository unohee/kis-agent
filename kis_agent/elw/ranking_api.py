"""ELW 순위 API

[국내주식] ELW 시세 메뉴의 순위 조회 (elw/v1/ranking/*).

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from typing import Any, Dict, List, Optional  # noqa: F401

from ..core.base_api import BaseAPI
from ..core.tr_mapping import PaperTradingNotSupportedError  # noqa: F401


class ElwRankingAPI(BaseAPI):
    """ELW 순위 조회"""
