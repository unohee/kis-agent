"""계좌 API Facade 모듈.

잔고/주문/손익 조회 및 현금/신용 주문 기능을 통합 제공하는 Facade.
실제 구현은 balance_query_api, order_api, profit_api에 위임.
"""

from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient
from .balance_query_api import AccountBalanceQueryAPI
from .order_api import AccountOrderAPI
from .profit_api import AccountProfitAPI


class AccountAPI(BaseAPI):
    """계좌 API Facade. 잔고/주문/손익 조회 및 주문 실행 기능 통합 제공.

    실제 구현은 하위 API 클래스에 위임:
    - AccountBalanceQueryAPI: 잔고, 자산, 증거금 조회
    - AccountOrderAPI: 현금/신용 주문, 정정/취소, 예약주문
    - AccountProfitAPI: 체결, 손익, 권리현황 조회
    """

    def __init__(
        self,
        client: KISClient,
        account_info: Dict[str, str],
        enable_cache=True,
        cache_config=None,
        _from_agent=False,
    ):
        """KIS 계좌 API Facade. account_info에 CANO/ACNT_PRDT_CD 필요."""
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

        # 하위 API 초기화
        self._balance_api = AccountBalanceQueryAPI(
            client, account_info, enable_cache, cache_config, _from_agent=True
        )
        self._order_api = AccountOrderAPI(
            client, account_info, enable_cache, cache_config, _from_agent=True
        )
        self._profit_api = AccountProfitAPI(
            client, account_info, enable_cache, cache_config, _from_agent=True
        )

        # 위임할 메서드 목록 (자동 위임용)
        self._delegate_methods = {
            # Balance Query API
            "get_account_balance": self._balance_api,
            "get_cash_available": self._balance_api,
            "get_total_asset": self._balance_api,
            "get_account_order_quantity": self._balance_api,
            "get_possible_order_amount": self._balance_api,
            "inquire_balance_rlz_pl": self._balance_api,
            "inquire_psbl_sell": self._balance_api,
            "inquire_intgr_margin": self._balance_api,
            "inquire_psbl_order": self._balance_api,
            "inquire_credit_psamount": self._balance_api,
            # Order API
            "order_cash": self._order_api,
            "order_cash_sor": self._order_api,
            "order_credit": self._order_api,
            "order_credit_buy": self._order_api,
            "order_credit_sell": self._order_api,
            "order_rvsecncl": self._order_api,
            "inquire_psbl_rvsecncl": self._order_api,
            "order_resv": self._order_api,
            "order_resv_rvsecncl": self._order_api,
            "order_resv_ccnl": self._order_api,
            # Profit API
            "inquire_daily_ccld": self._profit_api,
            "inquire_period_trade_profit": self._profit_api,
            "get_period_trade_profit": self._profit_api,
            "inquire_period_profit": self._profit_api,
            "get_period_profit": self._profit_api,
            "inquire_period_rights": self._profit_api,
        }

    def __getattr__(self, name: str) -> Any:
        """메서드 호출을 하위 API로 위임."""
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        if name in self._delegate_methods:
            return getattr(self._delegate_methods[name], name)

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    # ===== Balance Query API 직접 노출 (IDE 자동완성 지원) =====

    def get_account_balance(self) -> Optional[Dict]:
        """계좌 잔고 조회. output1=보유종목, output2=요약(예수금/총평가/순자산)."""
        return self._balance_api.get_account_balance()

    def get_cash_available(
        self, stock_code: str = "005930"
    ) -> Optional[Dict[str, Any]]:
        """종목별 매수가능금액 조회."""
        return self._balance_api.get_cash_available(stock_code)

    def get_total_asset(self) -> Optional[Dict[str, Any]]:
        """계좌 총자산 조회."""
        return self._balance_api.get_total_asset()

    def get_account_order_quantity(self, code: str) -> Optional[Dict]:
        """종목별 주문가능수량 조회."""
        return self._balance_api.get_account_order_quantity(code)

    def get_possible_order_amount(self) -> Optional[Dict]:
        """주문가능금액 조회."""
        return self._balance_api.get_possible_order_amount()

    def inquire_balance_rlz_pl(self) -> Optional[Dict]:
        """주식잔고조회_실현손익."""
        return self._balance_api.inquire_balance_rlz_pl()

    def inquire_psbl_sell(self, pdno: str) -> Optional[Dict[str, Any]]:
        """매도가능수량 조회."""
        return self._balance_api.inquire_psbl_sell(pdno)

    def inquire_intgr_margin(self) -> Optional[Dict[str, Any]]:
        """주식통합증거금 현황 조회."""
        return self._balance_api.inquire_intgr_margin()

    def inquire_psbl_order(
        self, price: int, pdno: str = "", ord_dvsn: str = "01"
    ) -> Optional[Dict]:
        """매수가능 조회."""
        return self._balance_api.inquire_psbl_order(price, pdno, ord_dvsn)

    def inquire_credit_psamount(self, pdno: str) -> Optional[Dict[str, Any]]:
        """신용매수가능 조회."""
        return self._balance_api.inquire_credit_psamount(pdno)

    # ===== Order API 직접 노출 =====

    def order_cash(
        self,
        pdno: str,
        qty: int,
        price: int,
        buy_sell: str,
        order_type: str = "00",
        exchange: str = "KRX",
    ) -> Optional[Dict[str, Any]]:
        """주식주문(현금)."""
        return self._order_api.order_cash(
            pdno, qty, price, buy_sell, order_type, exchange
        )

    def order_cash_sor(
        self, pdno: str, qty: int, buy_sell: str, order_type: str = "03"
    ) -> Optional[Dict[str, Any]]:
        """SOR 최유리지정가 주문."""
        return self._order_api.order_cash_sor(pdno, qty, buy_sell, order_type)

    def order_credit(
        self, code: str, qty: int, price: int, order_type: str
    ) -> Optional[Dict]:
        """신용주문 실행."""
        return self._order_api.order_credit(code, qty, price, order_type)

    def order_credit_buy(
        self,
        pdno: str,
        qty: int,
        price: int,
        order_type: str = "00",
        credit_type: str = "21",
        exchange: str = "KRX",
        loan_dt: str = "",
    ) -> Optional[Dict[str, Any]]:
        """주식주문(신용매수)."""
        return self._order_api.order_credit_buy(
            pdno, qty, price, order_type, credit_type, exchange, loan_dt
        )

    def order_credit_sell(
        self,
        pdno: str,
        qty: int,
        price: int,
        order_type: str = "00",
        credit_type: str = "11",
    ) -> Optional[Dict[str, Any]]:
        """주식주문(신용매도)."""
        return self._order_api.order_credit_sell(
            pdno, qty, price, order_type, credit_type
        )

    def order_rvsecncl(
        self, org_order_no: str, qty: int, price: int, order_type: str, cncl_type: str
    ) -> Optional[Dict]:
        """주문 정정/취소."""
        return self._order_api.order_rvsecncl(
            org_order_no, qty, price, order_type, cncl_type
        )

    def inquire_psbl_rvsecncl(self) -> Optional[Dict]:
        """정정/취소 가능 주문 목록 조회."""
        return self._order_api.inquire_psbl_rvsecncl()

    def order_resv(
        self, code: str, qty: int, price: int, order_type: str
    ) -> Optional[Dict]:
        """예약주문 등록."""
        return self._order_api.order_resv(code, qty, price, order_type)

    def order_resv_rvsecncl(
        self, seq: int, qty: int, price: int, order_type: str
    ) -> Optional[Dict]:
        """예약주문 정정/취소."""
        return self._order_api.order_resv_rvsecncl(seq, qty, price, order_type)

    def order_resv_ccnl(self) -> Optional[Dict]:
        """예약주문 내역 조회."""
        return self._order_api.order_resv_ccnl()

    # ===== Profit API 직접 노출 =====

    def inquire_daily_ccld(
        self,
        start_date: str = "",
        end_date: str = "",
        pdno: str = "",
        ord_dvsn_cd: str = "00",
        pagination: bool = False,
        ccld_dvsn: str = "00",
        inqr_dvsn: str = "01",
        inqr_dvsn_3: str = "00",
        max_pages: int = 100,
        page_callback=None,
    ) -> Optional[Dict[str, Any]]:
        """일별주문체결조회."""
        return self._profit_api.inquire_daily_ccld(
            start_date,
            end_date,
            pdno,
            ord_dvsn_cd,
            pagination,
            ccld_dvsn,
            inqr_dvsn,
            inqr_dvsn_3,
            max_pages,
            page_callback,
        )

    def inquire_period_trade_profit(
        self,
        start_date: str,
        end_date: str,
        pdno: str = "",
        sort_dvsn: str = "00",
        cblc_dvsn: str = "00",
        as_dict: bool = False,
    ):
        """기간별 실현손익 조회."""
        return self._profit_api.inquire_period_trade_profit(
            start_date, end_date, pdno, sort_dvsn, cblc_dvsn, as_dict
        )

    def get_period_trade_profit(
        self,
        start_date: str,
        end_date: str,
        pdno: str = "",
        sort_dvsn: str = "00",
        cblc_dvsn: str = "00",
    ) -> Optional[Dict]:
        """기간별매매손익합산조회 (Dict 반환)."""
        return self._profit_api.get_period_trade_profit(
            start_date, end_date, pdno, sort_dvsn, cblc_dvsn
        )

    def inquire_period_profit(
        self,
        start_date: str,
        end_date: str,
        sort_dvsn: str = "00",
        inqr_dvsn: str = "00",
        cblc_dvsn: str = "00",
        as_dict: bool = False,
    ):
        """기간별손익일별합산조회."""
        return self._profit_api.inquire_period_profit(
            start_date, end_date, sort_dvsn, inqr_dvsn, cblc_dvsn, as_dict
        )

    def get_period_profit(
        self,
        start_date: str,
        end_date: str,
        sort_dvsn: str = "00",
        inqr_dvsn: str = "00",
        cblc_dvsn: str = "00",
    ) -> Optional[Dict]:
        """기간별손익일별합산조회 (Dict 반환)."""
        return self._profit_api.get_period_profit(
            start_date, end_date, sort_dvsn, inqr_dvsn, cblc_dvsn
        )

    def inquire_period_rights(self, start_date: str, end_date: str):
        """기간별계좌권리현황조회."""
        return self._profit_api.inquire_period_rights(start_date, end_date)


# Expose facade class for flat import
__all__ = ["AccountAPI"]
