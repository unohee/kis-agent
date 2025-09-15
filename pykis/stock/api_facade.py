"""
Stock API Facade - 주식 관련 API 통합 인터페이스

Facade Pattern을 적용하여 복잡한 하위 시스템을 단순화
- StockPriceAPI: 시세 정보
- StockMarketAPI: 시장 정보  
- StockInvestorAPI: 투자자 정보
- 기존 StockAPI와 동일한 인터페이스 유지 (하위 호환성)
"""

from typing import Optional, Dict, Any, List, Tuple
from ..core.client import KISClient, API_ENDPOINTS
from ..core.base_api import BaseAPI

from .price_api import StockPriceAPI
from .market_api import StockMarketAPI
from .investor_api import StockInvestorAPI


class StockAPI(BaseAPI):
    """
    주식 관련 API 통합 Facade 클래스
    
    하위 시스템들을 통합하여 기존 인터페이스와 호환성을 유지하면서
    내부적으로는 책임 분산된 구조를 제공합니다.
    
    Attributes:
        price_api (StockPriceAPI): 시세 조회 전담 API
        market_api (StockMarketAPI): 시장 정보 전담 API  
        investor_api (StockInvestorAPI): 투자자 정보 전담 API
    """
    
    def __init__(self, client: KISClient, account_info=None, enable_cache=True, cache_config=None):
        """
        StockAPI Facade 초기화
        
        Args:
            client (KISClient): API 통신 클라이언트
            account_info (dict, optional): 계좌 정보
        """
        super().__init__(client, account_info, enable_cache, cache_config)
        
        # 하위 시스템 초기화
        self.price_api = StockPriceAPI(client, account_info)
        self.market_api = StockMarketAPI(client, account_info)
        self.investor_api = StockInvestorAPI(client, account_info)
    
    # ===== 시세 관련 메서드 (StockPriceAPI 위임) =====
    
    def get_stock_price(self, code: str) -> Optional[Dict]:
        """주식 현재가 조회"""
        return self.price_api.get_stock_price(code)
    
    def get_daily_price(self, code: str, period: str = "D", org_adj_prc: str = "1") -> Optional[Dict]:
        """일별 시세 조회"""
        return self.price_api.get_daily_price(code, period, org_adj_prc)
    
    def get_orderbook(self, code: str) -> Optional[Dict]:
        """주식 호가 정보 조회"""
        return self.price_api.get_orderbook(code)
    
    def get_orderbook_raw(self, code: str) -> Optional[Dict]:
        """호가 정보 원시 데이터 조회"""
        return self.price_api.get_orderbook_raw(code)
    
    def get_minute_price(self, code: str, hour: str = "153000") -> Optional[Dict]:
        """분봉 시세 조회"""
        return self.price_api.get_minute_price(code, hour)
    
    def get_daily_minute_price(self, code: str, date: str, hour: str = "153000") -> Optional[Dict]:
        """특정일 분봉 시세 조회"""
        return self.price_api.get_daily_minute_price(code, date, hour)
    
    # ===== 시장 정보 관련 메서드 (StockMarketAPI 위임) =====
    
    def get_market_fluctuation(self) -> Optional[Dict[str, Any]]:
        """시장 변동성 정보 조회"""
        return self.market_api.get_market_fluctuation()
    
    def get_market_rankings(self, volume: int = 5000000) -> Optional[Dict[str, Any]]:
        """거래량 기준 종목 순위 조회"""
        return self.market_api.get_market_rankings(volume)
    
    def get_volume_power(self, volume: int = 0) -> Optional[Dict]:
        """체결강도 순위 조회"""
        return self.market_api.get_volume_power(volume)
    
    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """종목 기본 정보 조회"""
        return self.market_api.get_stock_info(ticker)
    
    # ===== 투자자 정보 관련 메서드 (StockInvestorAPI 위임) =====
    
    def get_stock_investor(self, ticker: str = '', retries: int = 10, force_refresh: bool = False) -> Optional[Dict]:
        """투자자별 매매동향 조회 (원시 dict 반환)

        Note:
            - [변경 이유] StockInvestorAPI.get_stock_investor가 dict를 반환하므로 Facade도 일관성을 위해 dict로 타입을 맞춤
        """
        return self.investor_api.get_stock_investor(ticker, retries, force_refresh)
    
    def get_stock_member(self, ticker: str, retries: int = 10) -> Optional[Dict]:
        """거래원별 매매 정보 조회"""
        return self.investor_api.get_stock_member(ticker, retries)
    
    def get_member_transaction(self, code: str, mem_code: str) -> Optional[Dict[str, Any]]:
        """특정 거래원의 매매 내역 조회"""
        return self.investor_api.get_member_transaction(code, mem_code)
    
    def get_frgnmem_pchs_trend(self, code: str, date: str) -> Optional[Dict[str, Any]]:
        """외국인 매수 추이 조회"""
        return self.investor_api.get_frgnmem_pchs_trend(code, date)
    
    def get_foreign_broker_net_buy(self, code: str, foreign_brokers=None, date: str = None) -> Optional[tuple]:
        """외국계 증권사 순매수 집계"""
        return self.investor_api.get_foreign_broker_net_buy(code, foreign_brokers, date)

    # ===== 주문 및 가능금액 관련 메서드 (레거시에서 이전) =====

    def order_cash(
        self,
        ord_dv: str,
        pdno: str,
        ord_dvsn: str,
        ord_qty: str,
        ord_unpr: str,
        excg_id_dvsn_cd: str = "KRX",
        sll_type: str = "",
        cndt_pric: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내주식주문(현금) — 매수/매도 주문 전송

        Note:
            레거시 StockAPI에서 옮겨온 구현으로, Facade에서도 동일한 인터페이스를 제공합니다.
        """
        if not ord_dv or ord_dv not in ["buy", "sell"]:
            raise ValueError("ord_dv must be 'buy' or 'sell'")
        if not pdno:
            raise ValueError("pdno (종목코드) is required")
        if not ord_dvsn:
            raise ValueError("ord_dvsn (주문구분) is required")
        if not ord_qty:
            raise ValueError("ord_qty (주문수량) is required")
        if not ord_unpr:
            raise ValueError("ord_unpr (주문단가) is required")

        if not getattr(self, 'account', None):
            raise ValueError("Account information is required for trading")

        is_mock = getattr(self.client, 'is_mock', False)
        tr_id = ("VTTC0011U" if ord_dv == "sell" else "VTTC0012U") if is_mock else ("TTTC0011U" if ord_dv == "sell" else "TTTC0012U")

        params = {
            "CANO": self.account.get("CANO", ""),
            "ACNT_PRDT_CD": self.account.get("ACNT_PRDT_CD", ""),
            "PDNO": pdno,
            "ORD_DVSN": ord_dvsn,
            "ORD_QTY": ord_qty,
            "ORD_UNPR": ord_unpr,
            "EXCG_ID_DVSN_CD": excg_id_dvsn_cd,
            "SLL_TYPE": sll_type,
            "CNDT_PRIC": cndt_pric,
        }

        return self.client.make_request(
            endpoint=API_ENDPOINTS['ORDER_CASH'],
            tr_id=tr_id,
            params=params,
            method='POST',
        )

    def order_credit(
        self,
        ord_dv: str,
        pdno: str,
        crdt_type: str,
        ord_dvsn: str,
        ord_qty: str,
        ord_unpr: str,
        loan_dt: str = "",
        excg_id_dvsn_cd: str = "KRX",
        sll_type: str = "",
        rsvn_ord_yn: str = "N",
        emgc_ord_yn: str = "",
        cndt_pric: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내주식주문(신용) — 매수/매도 주문 전송 (모의 미지원)"""
        if not ord_dv or ord_dv not in ["buy", "sell"]:
            raise ValueError("ord_dv must be 'buy' or 'sell'")
        if not pdno:
            raise ValueError("pdno (종목코드) is required")
        if not crdt_type:
            raise ValueError("crdt_type is required")
        if not ord_dvsn:
            raise ValueError("ord_dvsn (주문구분) is required")
        if not ord_qty:
            raise ValueError("ord_qty (주문수량) is required")
        if not ord_unpr:
            raise ValueError("ord_unpr (주문단가) is required")

        if getattr(self.client, 'is_mock', False):
            raise ValueError("신용거래는 모의투자에서 지원되지 않습니다")

        if not getattr(self, 'account', None):
            raise ValueError("Account information is required for trading")

        tr_id = "TTTC0051U" if ord_dv == "sell" else "TTTC0052U"

        params = {
            "CANO": self.account.get("CANO", ""),
            "ACNT_PRDT_CD": self.account.get("ACNT_PRDT_CD", ""),
            "PDNO": pdno,
            "ORD_DVSN": ord_dvsn,
            "ORD_QTY": ord_qty,
            "ORD_UNPR": ord_unpr,
            "CRDT_TYPE": crdt_type,
            "LOAN_DT": loan_dt,
            "EXCG_ID_DVSN_CD": excg_id_dvsn_cd,
            "SLL_TYPE": sll_type,
            "RSVN_ORD_YN": rsvn_ord_yn,
            "EMGC_ORD_YN": emgc_ord_yn,
            "CNDT_PRIC": cndt_pric,
        }

        return self.client.make_request(
            endpoint=API_ENDPOINTS['ORDER_CREDIT'],
            tr_id=tr_id,
            params=params,
            method='POST',
        )

    def inquire_psbl_order(
        self,
        pdno: str,
        ord_unpr: str,
        ord_dvsn: str = "00",
        cma_evlu_amt_icld_yn: str = "N",
        ovrs_icld_yn: str = "N",
    ) -> Optional[Dict[str, Any]]:
        """매수가능조회"""
        if not pdno:
            raise ValueError("pdno (종목코드) is required")
        if not ord_unpr:
            raise ValueError("ord_unpr (주문단가) is required")
        if not getattr(self, 'account', None):
            raise ValueError("Account information is required for order inquiry")

        params = {
            "CANO": self.account.get("CANO", ""),
            "ACNT_PRDT_CD": self.account.get("ACNT_PRDT_CD", ""),
            "PDNO": pdno,
            "ORD_UNPR": ord_unpr,
            "ORD_DVSN": ord_dvsn,
            "CMA_EVLU_AMT_ICLD_YN": cma_evlu_amt_icld_yn,
            "OVRS_ICLD_YN": ovrs_icld_yn,
        }

        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_PSBL_ORDER'],
            tr_id="TTTC8908R",
            params=params,
        )

    def inquire_credit_psamount(
        self,
        pdno: str,
        ord_unpr: str,
        ord_dvsn: str = "00",
        crdt_type: str = "21",
        cma_evlu_amt_icld_yn: str = "N",
        ovrs_icld_yn: str = "N",
    ) -> Optional[Dict[str, Any]]:
        """신용매수가능조회"""
        if not pdno:
            raise ValueError("pdno (종목코드) is required")
        if not ord_unpr:
            raise ValueError("ord_unpr (주문단가) is required")
        if not getattr(self, 'account', None):
            raise ValueError("Account information is required for credit inquiry")

        params = {
            "CANO": self.account.get("CANO", ""),
            "ACNT_PRDT_CD": self.account.get("ACNT_PRDT_CD", ""),
            "PDNO": pdno,
            "ORD_DVSN": ord_dvsn,
            "CRDT_TYPE": crdt_type,
            "CMA_EVLU_AMT_ICLD_YN": cma_evlu_amt_icld_yn,
            "OVRS_ICLD_YN": ovrs_icld_yn,
            "ORD_UNPR": ord_unpr,
        }

        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_CREDIT_PSAMOUNT'],
            tr_id="TTTC8909R",
            params=params,
        )

    # ===== 추가 유틸 조회 =====

    def get_possible_order(self, code: str, price: str, order_type: str = "01") -> Optional[Dict[str, Any]]:
        """매수 가능 주문 조회 (rt_cd 메타데이터 포함)"""
        if not getattr(self, 'account', None):
            import logging
            logging.error("계좌 정보가 없습니다.")
            return None

        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_PSBL_ORDER'],
            tr_id="TTTC8908R",
            params={
                "CANO": self.account['CANO'],
                "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                "PDNO": code,
                "ORD_UNPR": price,
                "ORD_DVSN": order_type,
                "CMA_EVLU_AMT_ICLD_YN": "Y",
                "OVRS_ICLD_YN": "Y",
            },
        )

    def get_holiday_info(self, date: Optional[str] = None) -> Optional[Dict]:
        """국내 휴장일 정보 조회 (rt_cd 메타데이터 포함)"""
        params: Dict[str, Any] = {'CTX_AREA_NK': '', 'CTX_AREA_FK': ''}
        if date:
            params['BASS_DT'] = date

        try:
            return self._make_request_dict(
                endpoint=API_ENDPOINTS['CHK_HOLIDAY'],
                tr_id="CTCA0903R",
                params=params,
            )
        except Exception as e:
            import logging
            logging.error(f"국내 휴장일 정보 조회 실패: {e}")
            return None

    # ===== 선물/지수 관련 =====

    def get_kospi200_index(self, futures_month: str = "202409") -> Optional[Dict[str, Any]]:
        """KOSPI 200 지수 시세 조회 (기초자산)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_INDEX_PRICE'],
            tr_id="FHMIF10100000",
            params={
                "fid_cond_mrkt_cls_code": "K21",
                "fid_input_iscd": futures_month,
            },
        )

    def get_futures_price(self, code: str) -> Optional[Dict[str, Any]]:
        """선물 시세 조회"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_FUTURES_PRICE'],
            tr_id="FHMIF10000000",
            params={
                "fid_cond_mrkt_div_code": "F",
                "fid_input_iscd": code,
            },
        )


# 하위 호환성을 위한 별칭
StockAPIFacade = StockAPI
