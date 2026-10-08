"""퇴직연금 계좌 API

[국내주식] 주문/계좌 메뉴의 퇴직연금(trading/pension/*): 예수금, 미체결내역, 매수가능,
체결기준잔고, 잔고조회. 계좌 facade(AccountAPI)가 동적으로 위임한다.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from typing import Any, Dict, List, Optional  # noqa: F401

from ..core.base_api import BaseAPI
from ..core.tr_mapping import PaperTradingNotSupportedError  # noqa: F401


class AccountPensionAPI(BaseAPI):
    """퇴직연금 계좌 조회 (trading/pension/*)"""
