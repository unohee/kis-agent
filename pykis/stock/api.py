"""
agent_stock.py - 종목 단위 시세 조회 및 주문 전용 모듈 (레거시)

DEPRECATION NOTICE:
- 이 파일의 `StockAPI`는 레거시 호환성을 위해 유지됩니다.
- 신규 코드에서는 `from pykis.stock import StockAPI`를 사용하세요.
- 실제 구현은 api_facade.py와 하위 API 모듈에 있습니다.

Created: 2026-01-03
Purpose: LOC gate 준수를 위해 기존 3,358줄을 최소화
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient

logger = logging.getLogger(__name__)


def get_kospi200_futures_code(today: Optional[datetime] = None) -> str:
    """
    현재 날짜 기준으로 거래되고 있는 가장 활발한 KOSPI200 선물 종목코드를 반환합니다.

    KOSPI200 선물은 3, 6, 9, 12월 만기로 거래되며, 만기일은 매월 두 번째 주 목요일입니다.
    현재 날짜를 기준으로 가장 가까운 활성 선물 코드를 자동으로 계산합니다.

    Args:
        today (Optional[datetime]): 기준 날짜. None이면 현재 날짜 사용

    Returns:
        str: KOSPI200 선물 종목코드 (6자리, 예: "101W09")

    Example:
        >>> from pykis.stock.api import get_kospi200_futures_code
        >>> from datetime import datetime
        >>>
        >>> # 현재 활성 선물 코드
        >>> current_code = get_kospi200_futures_code()
        >>> print(current_code)  # "101W09" (2025년 9월물)
        >>>
        >>> # 특정 날짜 기준
        >>> specific_date = datetime(2025, 10, 1)
        >>> future_code = get_kospi200_futures_code(specific_date)
        >>> print(future_code)  # "101W12" (2025년 12월물)

    Note:
        - 종목코드 패턴: 101W + MM (MM: 03, 06, 09, 12)
        - 만기일: 매월 두 번째 주 목요일 (15:30 마감)
        - 만기일 지나면 자동으로 다음 만기월로 전환
        - 12월물 만기 후에는 다음해 3월물로 전환
    """
    if today is None:
        today = datetime.now()

    def get_second_thursday(year: int, month: int) -> datetime:
        """특정 년월의 두 번째 주 목요일 날짜를 반환"""
        first_day = datetime(year, month, 1)
        days_until_first_thursday = (3 - first_day.weekday()) % 7
        first_thursday = first_day + timedelta(days=days_until_first_thursday)
        second_thursday = first_thursday + timedelta(days=7)
        return second_thursday

    expiry_months = [3, 6, 9, 12]
    current_year = today.year
    current_month = today.month

    if current_month in expiry_months:
        expiry_date = get_second_thursday(current_year, current_month)
        if today.date() > expiry_date.date():
            for month in expiry_months:
                if month > current_month:
                    expiry = month
                    break
            else:
                expiry = 3
        else:
            expiry = current_month
    else:
        for month in expiry_months:
            if month > current_month:
                expiry = month
                break
        else:
            expiry = 3

    return f"101W{expiry:02d}"


class StockAPI(BaseAPI):
    """
    레거시 StockAPI - 하위 호환성을 위해 유지

    DEPRECATION NOTICE:
    이 클래스는 더 이상 직접 사용하지 마세요.
    대신 `from pykis.stock import StockAPI`를 사용하세요.

    이 클래스는 api_facade.StockAPI와 하위 API 모듈들로 위임합니다.
    """

    def __init__(
        self,
        client: KISClient,
        account_info: Optional[Dict[str, str]] = None,
        enable_cache: bool = True,
        cache_config: Optional[Dict[str, Any]] = None,
        _from_agent: bool = False,
    ) -> None:
        """레거시 StockAPI 초기화 - 내부적으로 Facade API들을 사용"""
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

        # 지연 import로 순환 참조 방지
        from .investor_api import StockInvestorAPI
        from .market_api import StockMarketAPI
        from .price_api import StockPriceAPI

        # 하위 API 초기화
        self._price_api = StockPriceAPI(client, account_info, _from_agent=_from_agent)
        self._market_api = StockMarketAPI(client, account_info, _from_agent=_from_agent)
        self._investor_api = StockInvestorAPI(
            client, account_info, _from_agent=_from_agent
        )

        logger.warning(
            "DEPRECATION: pykis.stock.api.StockAPI는 레거시입니다. "
            "from pykis.stock import StockAPI를 사용하세요."
        )

    def __getattr__(self, name: str) -> Any:
        """
        하위 API로 메서드 위임

        우선순위:
        1. StockPriceAPI - 시세 관련
        2. StockMarketAPI - 시장 정보 관련
        3. StockInvestorAPI - 투자자 정보 관련
        """
        # 내부 속성은 위임하지 않음
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

        # 하위 API에서 메서드 찾기
        for api in (self._price_api, self._market_api, self._investor_api):
            if hasattr(api, name):
                return getattr(api, name)

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'. "
            f"This is a legacy class. Use 'from pykis.stock import StockAPI' instead."
        )

    # ===== 주문 관련 메서드 - AccountAPI로 이동됨 =====
    # order_cash, order_credit 등은 AccountAPI를 사용하세요

    def order_cash(self, *args, **kwargs):
        """DEPRECATED: AccountAPI.order_cash를 사용하세요"""
        raise DeprecationWarning(
            "order_cash는 StockAPI에서 제거되었습니다. "
            "AccountAPI.order_cash() 또는 agent.order_stock_cash()를 사용하세요."
        )

    def order_credit(self, *args, **kwargs):
        """DEPRECATED: AccountAPI.order_credit를 사용하세요"""
        raise DeprecationWarning(
            "order_credit는 StockAPI에서 제거되었습니다. "
            "AccountAPI.order_credit() 또는 agent.order_stock_credit()를 사용하세요."
        )


__all__ = ["StockAPI", "get_kospi200_futures_code"]
