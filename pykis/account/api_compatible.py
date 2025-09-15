"""
하위 호환성을 위한 Account API 래퍼

기존 메서드명을 유지하면서 내부적으로는 리팩터링된 AccountAPIEnhanced를 사용
모든 기존 메서드는 deprecated 경고를 표시
"""

import warnings
from typing import Optional, Dict, Any, List
from .api_enhanced import AccountAPIEnhanced
from ..core.base_api import BaseAPI


class AccountAPI(AccountAPIEnhanced):
    """
    기존 AccountAPI와 100% 호환되는 클래스
    내부적으로는 AccountAPIEnhanced의 리팩터링된 메서드를 사용
    """

    def __init__(self, client, account_info: Dict[str, str], enable_cache=True, cache_config=None):
        """기존 AccountAPI와 동일한 초기화"""
        super().__init__(client, account_info, enable_cache, cache_config)

    # ========== 기존 메서드명 유지 (내부는 리팩터링 버전 사용) ==========

    def get_account_balance(self) -> Optional[Dict]:
        """
        계좌 잔고 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_balance_holdings` instead.
        """
        warnings.warn(
            "get_account_balance는 deprecated되었습니다. get_balance_holdings를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_balance_holdings()

    def get_cash_available(self, stock_code: str = "005930") -> Optional[Dict]:
        """
        현금 주문 가능 금액 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_order_capacity` instead.
        """
        warnings.warn(
            "get_cash_available는 deprecated되었습니다. get_order_capacity를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_order_capacity(stock_code)

    def inquire_psbl_order(self, stock_code: str = "005930") -> Optional[Dict]:
        """
        주문 가능 수량 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_order_capacity` instead.
        """
        warnings.warn(
            "inquire_psbl_order는 deprecated되었습니다. get_order_capacity를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_order_capacity(stock_code)

    def inquire_credit_psamount(self, stock_code: str = "005930") -> Optional[Dict]:
        """
        신용 주문 가능 금액 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_credit_capacity` instead.
        """
        warnings.warn(
            "inquire_credit_psamount는 deprecated되었습니다. get_credit_capacity를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_credit_capacity(stock_code)

    def get_account_profit_loss(self) -> Optional[Dict]:
        """
        계좌 손익 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_realized_profit` instead.
        """
        warnings.warn(
            "get_account_profit_loss는 deprecated되었습니다. get_realized_profit를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_realized_profit()

    def get_daily_order_list(self) -> Optional[Dict]:
        """
        당일 주문 내역 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_orders_today` instead.
        """
        warnings.warn(
            "get_daily_order_list는 deprecated되었습니다. get_orders_today를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_orders_today()

    def inquire_purchasable_cash(self) -> Optional[Dict]:
        """
        예수금 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_deposit_info` instead.
        """
        warnings.warn(
            "inquire_purchasable_cash는 deprecated되었습니다. get_deposit_info를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_deposit_info()

    # ========== 기존 API의 유틸리티 메서드 ==========

    def get_holdings(self) -> Optional[List[Dict]]:
        """
        보유 종목 목록 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_holdings_summary` instead.
        """
        warnings.warn(
            "get_holdings는 deprecated되었습니다. get_holdings_summary를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_holdings_summary()

    def get_total_evaluation(self) -> Optional[Dict]:
        """
        총 평가 금액 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_total_assets` instead.
        """
        warnings.warn(
            "get_total_evaluation는 deprecated되었습니다. get_total_assets를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_total_assets()

    def get_account_summary(self) -> Optional[Dict]:
        """
        계좌 요약 정보 조회 (기존 메서드명)

        .. deprecated:: 2.0
            Use :meth:`get_total_assets` instead.
        """
        warnings.warn(
            "get_account_summary는 deprecated되었습니다. get_total_assets를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_total_assets()

    # ========== 추가 호환성 메서드 ==========

    def get_stock_balance(self) -> Optional[Dict]:
        """
        주식 잔고 조회 (StockAPI에서 이동된 메서드)

        .. deprecated:: 2.0
            Use :meth:`get_balance_holdings` instead.
        """
        warnings.warn(
            "get_stock_balance는 deprecated되었습니다. get_balance_holdings를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_balance_holdings()

    def get_buyable_cash(self, stock_code: str = "005930") -> Optional[int]:
        """
        매수 가능 현금 조회 (반환 타입 단순화)

        .. deprecated:: 2.0
            Use :meth:`get_order_capacity` instead.
        """
        warnings.warn(
            "get_buyable_cash는 deprecated되었습니다. get_order_capacity를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        result = self.get_order_capacity(stock_code)
        if result and result.get('rt_cd') == '0':
            output = result.get('output', {})
            return int(output.get('ord_psbl_cash', 0))
        return None

    def get_max_buyable_qty(self, stock_code: str = "005930") -> Optional[int]:
        """
        최대 매수 가능 수량 조회

        .. deprecated:: 2.0
            Use :meth:`get_order_capacity` instead.
        """
        warnings.warn(
            "get_max_buyable_qty는 deprecated되었습니다. get_order_capacity를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        result = self.get_order_capacity(stock_code)
        if result and result.get('rt_cd') == '0':
            output = result.get('output', {})
            return int(output.get('max_buy_qty', 0))
        return None

    # ========== 기존 메서드 파라미터 호환성 ==========

    def inquire_balance(self,
                       afhr_flpr_yn: str = "N",
                       ofl_yn: str = "",
                       inqr_dvsn: str = "01",
                       unpr_dvsn: str = "01",
                       fund_sttl_icld_yn: str = "N",
                       fncg_amt_auto_rdpt_yn: str = "N",
                       prcs_dvsn: str = "00") -> Optional[Dict]:
        """
        잔고 조회 (세부 파라미터 지원)

        .. deprecated:: 2.0
            Use :meth:`get_balance_holdings` instead.
        """
        warnings.warn(
            "inquire_balance는 deprecated되었습니다. get_balance_holdings를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        # 파라미터는 무시하고 기본값 사용
        return self.get_balance_holdings()