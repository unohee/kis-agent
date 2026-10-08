"""예탁원 정보 API

[국내주식] 종목정보 메뉴의 예탁원(ksdinfo/*) 일정: 증자, 배당, 매수청구, 합병/분할,
액면교체, 자본감소, 상장정보, 공모주청약, 실권주, 의무예치, 주주총회. 연속조회 커서는 CTS.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from typing import Any, Dict, List, Optional  # noqa: F401

from ..core.base_api import BaseAPI
from ..core.tr_mapping import PaperTradingNotSupportedError  # noqa: F401


class StockKsdInfoAPI(BaseAPI):
    """예탁원 일정 정보 (ksdinfo/*)"""
