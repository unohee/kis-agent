"""국내주식 순위분석 API

[국내주식] 순위분석 메뉴 (ranking/*): 예상체결 상승/하락, 호가잔량, 신용잔고, 시간외 거래량/잔량/등락률,
HTS 조회상위, 수익자산지표, 신고/신저 근접, 우선주/괴리율, 대량체결건수, 재무비율, 당사매매,
시장가치, 관심종목등록 상위.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from typing import Any, Dict, List, Optional  # noqa: F401

from ..core.base_api import BaseAPI
from ..core.tr_mapping import PaperTradingNotSupportedError  # noqa: F401


class StockRankingAPI(BaseAPI):
    """국내주식 순위분석 (ranking/*)"""
