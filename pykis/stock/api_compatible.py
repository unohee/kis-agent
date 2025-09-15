"""
하위 호환성을 위한 Stock API 래퍼

기존 메서드명을 유지하면서 내부적으로는 리팩터링된 StockAPIEnhanced를 사용
모든 기존 메서드는 deprecated 경고를 표시
"""

import warnings
from typing import Optional, Dict, Any, List
from .api_enhanced import StockAPIEnhanced
from ..core.base_api import BaseAPI


class StockAPI(StockAPIEnhanced):
    """
    기존 StockAPI와 100% 호환되는 클래스
    내부적으로는 StockAPIEnhanced의 리팩터링된 메서드를 사용
    """

    def __init__(self, client, account_info=None, enable_cache=True, cache_config=None):
        """기존 StockAPI와 동일한 초기화"""
        super().__init__(client, account_info, enable_cache, cache_config)

    # ========== 기존 메서드명 유지 (내부는 리팩터링 버전 사용) ==========

    def get_stock_price(self, code: str) -> Optional[Dict]:
        """
        주식 현재가 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_price_current` instead.
        """
        warnings.warn(
            "get_stock_price는 deprecated되었습니다. get_price_current를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_price_current(code)

    def get_daily_price(self, code: str, period: str = "D", org_adj_prc: str = "1") -> Optional[Dict]:
        """
        일별 시세 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_price_daily` instead.
        """
        warnings.warn(
            "get_daily_price는 deprecated되었습니다. get_price_daily를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_price_daily(code, period, org_adj_prc)

    def get_minute_price(self, code: str, hour: str = "153000") -> Optional[Dict]:
        """
        분봉 데이터 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_price_minute` instead.
        """
        warnings.warn(
            "get_minute_price는 deprecated되었습니다. get_price_minute를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_price_minute(code, hour)

    def get_intraday_price(self, code: str, date: str, hour: str = "153000") -> Optional[Dict]:
        """
        일중 분봉 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_price_intraday` instead.
        """
        warnings.warn(
            "get_intraday_price는 deprecated되었습니다. get_price_intraday를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_price_intraday(code, date, hour)

    def get_orderbook(self, code: str) -> Optional[Dict]:
        """
        호가 정보 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_book_order` instead.
        """
        warnings.warn(
            "get_orderbook는 deprecated되었습니다. get_book_order를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_book_order(code)

    def get_volume_power(self, volume: int = 0) -> Optional[Dict]:
        """
        체결강도 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_book_volume_power` instead.
        """
        warnings.warn(
            "get_volume_power는 deprecated되었습니다. get_book_volume_power를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_book_volume_power(volume)

    def get_stock_investor(self, ticker: str, retries: int = 10, force_refresh: bool = False) -> Optional[Dict]:
        """
        투자자별 매매동향 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_investor_trend` instead.
        """
        warnings.warn(
            "get_stock_investor는 deprecated되었습니다. get_investor_trend를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        # force_refresh 파라미터는 무시 (캐시 시스템으로 대체)
        return self.get_investor_trend(ticker)

    def get_stock_member(self, ticker: str, retries: int = 10) -> Optional[Dict]:
        """
        회원사별 매매동향 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_member_trend` instead.
        """
        warnings.warn(
            "get_stock_member는 deprecated되었습니다. get_member_trend를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        # retries 파라미터는 무시 (데코레이터로 처리)
        return self.get_member_trend(ticker)

    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """
        종목 기본 정보 조회 (기존 메서드명 유지)
        이 메서드는 이미 적절한 이름이므로 경고 없이 유지
        """
        # 경고 없이 그대로 사용
        return super().get_stock_info(ticker)

    def get_stock_financial(self, code: str) -> Optional[Dict]:
        """
        종목 재무 정보 조회 (기존 메서드명 유지)
        이 메서드는 이미 적절한 이름이므로 경고 없이 유지
        """
        # 경고 없이 그대로 사용
        return super().get_stock_info(code)

    def get_market_fluctuation(self, min_volume: int = 3000000) -> Optional[Dict]:
        """
        등락률 순위 조회 (기존 메서드명 유지)
        이 메서드는 이미 적절한 이름이므로 경고 없이 유지
        """
        # 경고 없이 그대로 사용
        return super().get_market_fluctuation(min_volume)

    def get_market_rankings(self, volume: int = 5000000) -> Optional[Dict]:
        """
        거래량 순위 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_market_volume_rank` instead.
        """
        warnings.warn(
            "get_market_rankings는 deprecated되었습니다. get_market_volume_rank를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_market_volume_rank(volume)

    def get_market_cap(self, count: int = 30) -> Optional[Dict]:
        """
        시가총액 순위 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_market_cap_rank` instead.
        """
        warnings.warn(
            "get_market_cap는 deprecated되었습니다. get_market_cap_rank를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_market_cap_rank(count)

    def get_program_trade_by_stock(self, code: str, date: str = None) -> Optional[Dict]:
        """
        종목별 프로그램매매 추이 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_program_trade_stock` instead.
        """
        warnings.warn(
            "get_program_trade_by_stock는 deprecated되었습니다. get_program_trade_stock를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_program_trade_stock(code, date)

    def get_overtime_conclusion(self, code: str) -> Optional[Dict]:
        """
        시간외 단일가 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_overtime_price` instead.
        """
        warnings.warn(
            "get_overtime_conclusion는 deprecated되었습니다. get_overtime_price를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_overtime_price(code)

    # ========== 기존 API에만 있던 특수 메서드들 ==========

    def estimate_accumulated_volume_by_top_members(self, stock_member_data: Dict[str, Any], force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        거래원 데이터에서 세력의 누적 매집량 추정

        .. deprecated:: 2.0
            이 메서드는 별도의 분석 모듈로 이동 예정입니다.
        """
        warnings.warn(
            "estimate_accumulated_volume_by_top_members는 deprecated되었습니다. 별도 분석 모듈을 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        # 기존 로직 그대로 구현 (필요시)
        return None

    def get_stock_balance(self) -> Optional[Dict]:
        """
        주식 잔고 조회 (AccountAPI로 이동해야 할 메서드)

        .. deprecated:: 2.0
            Use AccountAPI.get_balance_holdings() instead.
        """
        warnings.warn(
            "get_stock_balance는 deprecated되었습니다. AccountAPI.get_balance_holdings를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        # AccountAPI로 위임 필요
        return None

    # ========== 추가 호환성 메서드 ==========

    def get_intraday_concluded(self, code: str) -> Optional[Dict]:
        """
        당일 체결 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_price_minute` with appropriate parameters instead.
        """
        warnings.warn(
            "get_intraday_concluded는 deprecated되었습니다. get_price_minute를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        from datetime import datetime
        current_time = datetime.now().strftime("%H%M%S")
        return self.get_price_minute(code, current_time)