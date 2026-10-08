"""국내주식 시세분석 API

[국내주식] 시세분석 메뉴: 공매도 일별추이, 상하한가 포착, 대차거래추이, 일별 매수매도 체결량,
체결금액별 매매비중, 증시자금 종합, 예상체결가 추이, 시장별 투자자매매동향(시세) 등.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from typing import Any, Dict, List, Optional  # noqa: F401

from ..core.base_api import BaseAPI
from ..core.tr_mapping import PaperTradingNotSupportedError  # noqa: F401


class StockAnalysisAPI(BaseAPI):
    """국내주식 시세분석"""
