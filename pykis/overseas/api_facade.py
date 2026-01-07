"""
해외주식 API Facade - 해외주식 관련 API 통합 인터페이스

Facade Pattern을 적용하여 복잡한 하위 시스템을 단순화합니다.
- OverseasPriceAPI: 시세 조회
- OverseasAccountAPI: 계좌 조회
- OverseasOrderAPI: 주문
- OverseasRankingAPI: 시장 순위 조회
"""

from typing import Any, Dict, List, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient
from .account_api import OverseasAccountAPI
from .order_api import OverseasOrderAPI
from .price_api import OverseasPriceAPI
from .ranking_api import OverseasRankingAPI


class OverseasStockAPI(BaseAPI):
    """
    해외주식 API 통합 Facade 클래스

    해외주식 거래에 필요한 모든 API를 통합된 인터페이스로 제공합니다.

    지원 거래소:
    - 미국: NAS (NASDAQ), NYS (NYSE), AMS (AMEX)
    - 아시아: HKS (홍콩), TSE (도쿄), SHS (상해), SZS (심천), HSX (호치민), HNX (하노이)

    Attributes:
        price_api (OverseasPriceAPI): 시세 조회 전담 API
        account_api (OverseasAccountAPI): 계좌 조회 전담 API
        order_api (OverseasOrderAPI): 주문 전담 API
        ranking_api (OverseasRankingAPI): 시장 순위 조회 전담 API

    Example:
        >>> from pykis import Agent
        >>> agent = Agent(...)
        >>>
        >>> # 시세 조회
        >>> price = agent.overseas.get_price(excd="NAS", symb="AAPL")
        >>> print(f"AAPL: ${price['output']['last']}")
        >>>
        >>> # 일봉 조회
        >>> daily = agent.overseas.get_daily_price(excd="NAS", symb="TSLA")
    """

    # 지원 거래소 정보
    EXCHANGES = {
        "NAS": {"name": "NASDAQ", "country": "미국", "currency": "USD"},
        "NYS": {"name": "NYSE", "country": "미국", "currency": "USD"},
        "AMS": {"name": "AMEX", "country": "미국", "currency": "USD"},
        "HKS": {"name": "홍콩증권거래소", "country": "홍콩", "currency": "HKD"},
        "TSE": {"name": "도쿄증권거래소", "country": "일본", "currency": "JPY"},
        "SHS": {"name": "상해증권거래소", "country": "중국", "currency": "CNY"},
        "SZS": {"name": "심천증권거래소", "country": "중국", "currency": "CNY"},
        "HSX": {"name": "호치민증권거래소", "country": "베트남", "currency": "VND"},
        "HNX": {"name": "하노이증권거래소", "country": "베트남", "currency": "VND"},
    }

    def __init__(
        self,
        client: KISClient,
        account_info: Optional[Dict[str, Any]] = None,
        enable_cache: bool = True,
        cache_config: Optional[Dict[str, Any]] = None,
        _from_agent: bool = False,
    ) -> None:
        """
        OverseasStockAPI Facade 초기화

        Args:
            client (KISClient): API 통신 클라이언트
            account_info (dict, optional): 계좌 정보
            enable_cache (bool): 캐시 사용 여부 (기본: True)
            cache_config (dict, optional): 캐시 설정
            _from_agent (bool): Agent를 통해 생성되었는지 여부 (내부 사용)
        """
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

        # 하위 시스템 초기화
        self.price_api = OverseasPriceAPI(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )
        self.account_api = OverseasAccountAPI(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )
        self.order_api = OverseasOrderAPI(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )
        self.ranking_api = OverseasRankingAPI(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

    # =========================================================================
    # 시세 조회 메서드 (OverseasPriceAPI 위임)
    # =========================================================================

    def get_price(
        self,
        excd: str,
        symb: str,
    ) -> Optional[Dict[str, Any]]:
        """해외주식 현재체결가 조회

        Args:
            excd: 거래소 코드 (NAS, NYS, AMS, HKS, TSE, SHS, SZS, HSX, HNX)
            symb: 종목코드 (예: AAPL, TSLA, NVDA)

        Returns:
            시세 정보 Dict (last: 현재가, diff: 전일대비, rate: 등락률 등)
        """
        return self.price_api.get_price(excd, symb)

    def get_price_detail(
        self,
        excd: str,
        symb: str,
    ) -> Optional[Dict[str, Any]]:
        """해외주식 현재가 상세 조회 (52주 최고/최저, PER, EPS 등)"""
        return self.price_api.get_price_detail(excd, symb)

    def get_daily_price(
        self,
        excd: str,
        symb: str,
        gubn: str = "0",
        bymd: str = "",
        modp: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 기간별 시세 조회 (일봉)

        Args:
            excd: 거래소 코드
            symb: 종목코드
            gubn: 일/주/월 구분 ("0": 일, "1": 주, "2": 월)
            bymd: 조회기준일자 (YYYYMMDD, 공백 시 최근일)
            modp: 수정주가반영여부 ("0": 미반영, "1": 반영)
        """
        return self.price_api.get_daily_price(excd, symb, gubn, bymd, modp)

    def get_minute_price(
        self,
        excd: str,
        symb: str,
        nmin: str = "1",
        pinc: str = "0",
        nrec: str = "120",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 분봉 조회

        Args:
            excd: 거래소 코드
            symb: 종목코드
            nmin: 분봉 간격 ("1": 1분, "5": 5분, "30": 30분, "60": 60분)
            pinc: 전일포함여부 ("0": 당일만, "1": 전일포함)
            nrec: 조회건수 (최대 120)
        """
        return self.price_api.get_minute_price(excd, symb, nmin, pinc, nrec)

    def get_orderbook(
        self,
        excd: str,
        symb: str,
    ) -> Optional[Dict[str, Any]]:
        """해외주식 10호가 조회"""
        return self.price_api.get_orderbook(excd, symb)

    def get_stock_info(
        self,
        prdt_type_cd: str = "512",
        pdno: str = "",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 상품기본정보 조회

        Args:
            prdt_type_cd: 상품유형코드 (512: 미국, 513: 홍콩, 514: 상해, 515: 심천, 516: 일본, 517: 베트남)
            pdno: 상품번호 (거래소코드.종목코드, 예: "NAS.AAPL")
        """
        return self.price_api.get_stock_info(prdt_type_cd, pdno)

    def get_ccnl(
        self,
        excd: str,
        symb: str,
    ) -> Optional[Dict[str, Any]]:
        """해외주식 체결정보 조회"""
        return self.price_api.get_ccnl(excd, symb)

    def get_holiday(
        self,
        trad_dt: str = "",
    ) -> Optional[Dict[str, Any]]:
        """해외거래소 휴장일 조회

        Args:
            trad_dt: 기준일자 (YYYYMMDD, 공백 시 당일)
        """
        return self.price_api.get_holiday(trad_dt)

    def get_news_title(
        self,
        excd: str = "",
        symb: str = "",
        nrec: str = "20",
    ) -> Optional[Dict[str, Any]]:
        """해외뉴스종합(제목) 조회

        Args:
            excd: 거래소 코드 (공백 시 전체)
            symb: 종목코드 (공백 시 전체)
            nrec: 조회건수 (기본 20)
        """
        return self.price_api.get_news_title(excd=excd, symb=symb, nrec=nrec)

    def get_industry_theme(
        self,
        excd: str,
        symb: str = "",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 업종/테마 조회"""
        return self.price_api.get_industry_theme(excd, symb)

    def search_symbol(
        self,
        excd: str,
        symb: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """해외주식 종목 검색"""
        return self.price_api.search_symbol(excd, symb)

    # =========================================================================
    # 계좌 조회 메서드 (OverseasAccountAPI 위임)
    # =========================================================================

    def get_balance(
        self,
        ovrs_excg_cd: str = "",
        tr_crcy_cd: str = "",
        ctx_area_fk200: str = "",
        ctx_area_nk200: str = "",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 잔고 조회

        Args:
            ovrs_excg_cd: 거래소 코드 (공백: 전체)
            tr_crcy_cd: 거래통화코드 (공백: 전체)
            ctx_area_fk200: 연속조회검색조건200
            ctx_area_nk200: 연속조회키200

        Returns:
            잔고 정보 Dict (output1: 보유종목, output2: 요약)
        """
        return self.account_api.get_balance(
            ovrs_excg_cd, tr_crcy_cd, ctx_area_fk200, ctx_area_nk200
        )

    def get_order_history(
        self,
        ovrs_excg_cd: str = "",
        sort_sqn: str = "DS",
        cont_fk200: str = "",
        cont_nk200: str = "",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 주문체결내역 조회

        Args:
            ovrs_excg_cd: 거래소 코드 (공백: 전체)
            sort_sqn: 정렬순서 (DS: 정순, AS: 역순)
            cont_fk200: 연속조회검색조건200
            cont_nk200: 연속조회키200

        Returns:
            주문체결내역 Dict
        """
        return self.account_api.get_order_history(
            ovrs_excg_cd, sort_sqn, cont_fk200, cont_nk200
        )

    def get_unfilled_orders(
        self,
        ovrs_excg_cd: str = "",
        sort_sqn: str = "DS",
        ctx_area_fk200: str = "",
        ctx_area_nk200: str = "",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 미체결내역 조회

        Args:
            ovrs_excg_cd: 거래소 코드 (공백: 전체)
            sort_sqn: 정렬순서 (DS: 정순, AS: 역순)
            ctx_area_fk200: 연속조회검색조건200
            ctx_area_nk200: 연속조회키200

        Returns:
            미체결 주문 내역 Dict
        """
        return self.account_api.get_unfilled_orders(
            ovrs_excg_cd, sort_sqn, ctx_area_fk200, ctx_area_nk200
        )

    def get_buyable_amount(
        self,
        ovrs_excg_cd: str,
        ovrs_ord_unpr: str = "0",
        item_cd: str = "",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 매수가능금액 조회

        Args:
            ovrs_excg_cd: 거래소 코드 (필수)
            ovrs_ord_unpr: 해외주문단가 (시장가: "0")
            item_cd: 종목코드 (공백 시 통화별 총 매수가능금액)

        Returns:
            매수가능 정보 Dict
        """
        return self.account_api.get_buyable_amount(ovrs_excg_cd, ovrs_ord_unpr, item_cd)

    def get_present_balance(
        self,
        wcrc_frcr_dvsn_cd: str = "02",
        natn_cd: str = "",
        tr_mket_cd: str = "",
        inqr_dvsn_cd: str = "",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 체결기준현재잔고 조회

        Args:
            wcrc_frcr_dvsn_cd: 원화외화구분코드 (01: 원화, 02: 외화)
            natn_cd: 국가코드 (공백: 전체)
            tr_mket_cd: 거래시장코드 (공백: 전체)
            inqr_dvsn_cd: 조회구분코드

        Returns:
            체결기준잔고 Dict
        """
        return self.account_api.get_present_balance(
            wcrc_frcr_dvsn_cd, natn_cd, tr_mket_cd, inqr_dvsn_cd
        )

    def get_period_profit(
        self,
        ovrs_excg_cd: str = "",
        natn_cd: str = "",
        crcy_cd: str = "",
        pdno: str = "",
        inqr_strt_dt: str = "",
        inqr_end_dt: str = "",
        wcrc_frcr_dvsn_cd: str = "02",
        ctx_area_fk200: str = "",
        ctx_area_nk200: str = "",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 기간손익 조회

        Args:
            ovrs_excg_cd: 거래소 코드 (공백: 전체)
            natn_cd: 국가코드 (공백: 전체)
            crcy_cd: 통화코드 (공백: 전체)
            pdno: 종목코드 (공백: 전체)
            inqr_strt_dt: 조회시작일자 (YYYYMMDD)
            inqr_end_dt: 조회종료일자 (YYYYMMDD)
            wcrc_frcr_dvsn_cd: 원화외화구분 (01: 원화, 02: 외화)
            ctx_area_fk200: 연속조회검색조건
            ctx_area_nk200: 연속조회키

        Returns:
            기간손익 Dict
        """
        return self.account_api.get_period_profit(
            ovrs_excg_cd,
            natn_cd,
            crcy_cd,
            pdno,
            inqr_strt_dt,
            inqr_end_dt,
            wcrc_frcr_dvsn_cd,
            ctx_area_fk200,
            ctx_area_nk200,
        )

    def get_reserve_order_list(
        self,
        ovrs_excg_cd: str = "",
        sort_sqn: str = "DS",
        ctx_area_fk200: str = "",
        ctx_area_nk200: str = "",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 예약주문내역 조회

        Args:
            ovrs_excg_cd: 거래소 코드 (공백: 전체)
            sort_sqn: 정렬순서 (DS: 정순, AS: 역순)
            ctx_area_fk200: 연속조회검색조건
            ctx_area_nk200: 연속조회키

        Returns:
            예약주문 내역 Dict
        """
        return self.account_api.get_reserve_order_list(
            ovrs_excg_cd, sort_sqn, ctx_area_fk200, ctx_area_nk200
        )

    def get_foreign_margin(
        self,
        crcy_cd: str = "",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 외화증거금 조회

        Args:
            crcy_cd: 통화코드 (공백: 전체, USD/HKD/CNY/JPY/VND)

        Returns:
            외화증거금 정보 Dict
        """
        return self.account_api.get_foreign_margin(crcy_cd)

    # =========================================================================
    # 주문 메서드 (OverseasOrderAPI 위임)
    # =========================================================================

    def buy_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        qty: int,
        price: float,
        ord_dvsn: str = "00",
        ord_svr_dvsn_cd: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 매수주문

        Args:
            ovrs_excg_cd: 거래소 코드 (NAS/NASD, NYS/NYSE, AMS/AMEX, HKS/SEHK 등)
            pdno: 종목코드 (예: AAPL, TSLA, NVDA)
            qty: 주문수량
            price: 주문단가 (USD 기준, 소수점 허용)
            ord_dvsn: 주문구분
                - "00": 지정가 (기본값)
                - "31": MOO (시장 개장시 시장가)
                - "32": LOO (시장 개장시 지정가)
                - "33": MOC (시장 마감시 시장가)
                - "34": LOC (시장 마감시 지정가)
            ord_svr_dvsn_cd: 주문서버구분코드 ("0": 기본)

        Returns:
            주문 결과 Dict (output.odno: 주문번호, output.ord_tmd: 주문시각)
        """
        return self.order_api.buy_order(
            ovrs_excg_cd, pdno, qty, price, ord_dvsn, ord_svr_dvsn_cd
        )

    def sell_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        qty: int,
        price: float,
        ord_dvsn: str = "00",
        ord_svr_dvsn_cd: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 매도주문

        Args:
            ovrs_excg_cd: 거래소 코드
            pdno: 종목코드
            qty: 주문수량
            price: 주문단가
            ord_dvsn: 주문구분 ("00": 지정가, "31": MOO, "33": MOC 등)
            ord_svr_dvsn_cd: 주문서버구분코드

        Returns:
            주문 결과 Dict (output.odno: 주문번호, output.ord_tmd: 주문시각)
        """
        return self.order_api.sell_order(
            ovrs_excg_cd, pdno, qty, price, ord_dvsn, ord_svr_dvsn_cd
        )

    def modify_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        orgn_odno: str,
        qty: int,
        price: float,
        ord_dvsn: str = "00",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 정정주문

        미체결 주문의 가격이나 수량을 정정합니다.

        Args:
            ovrs_excg_cd: 거래소 코드
            pdno: 종목코드
            orgn_odno: 원주문번호 (정정할 주문번호)
            qty: 정정 후 주문수량
            price: 정정 후 주문단가
            ord_dvsn: 주문구분 ("00": 지정가)

        Returns:
            정정 결과 Dict (output.odno: 신규 주문번호)
        """
        return self.order_api.modify_order(
            ovrs_excg_cd, pdno, orgn_odno, qty, price, ord_dvsn
        )

    def cancel_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        orgn_odno: str,
        qty: int,
        ord_dvsn: str = "00",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 취소주문

        미체결 주문을 취소합니다.

        Args:
            ovrs_excg_cd: 거래소 코드
            pdno: 종목코드
            orgn_odno: 원주문번호 (취소할 주문번호)
            qty: 취소수량
            ord_dvsn: 주문구분 ("00": 지정가)

        Returns:
            취소 결과 Dict (output.odno: 취소 주문번호)
        """
        return self.order_api.cancel_order(ovrs_excg_cd, pdno, orgn_odno, qty, ord_dvsn)

    def reserve_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        sll_buy_dvsn_cd: str,
        qty: int,
        price: float,
        ord_dvsn: str = "00",
        rsvn_ord_end_dt: str = "",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 예약주문

        지정된 날짜에 주문을 자동으로 실행하는 예약주문을 등록합니다.

        Args:
            ovrs_excg_cd: 거래소 코드
            pdno: 종목코드
            sll_buy_dvsn_cd: 매도매수구분 ("01": 매도, "02": 매수)
            qty: 주문수량
            price: 주문단가
            ord_dvsn: 주문구분 ("00": 지정가)
            rsvn_ord_end_dt: 예약종료일자 (YYYYMMDD, 공백 시 당일)

        Returns:
            예약주문 결과 Dict (output.rsvn_ord_seq: 예약주문순번)
        """
        return self.order_api.reserve_order(
            ovrs_excg_cd, pdno, sll_buy_dvsn_cd, qty, price, ord_dvsn, rsvn_ord_end_dt
        )

    def modify_reserve_order(
        self,
        rsvn_ord_seq: str,
        qty: int,
        price: float,
        ord_dvsn: str = "00",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 예약주문 정정

        등록된 예약주문의 수량이나 가격을 정정합니다.

        Args:
            rsvn_ord_seq: 예약주문순번 (정정할 예약주문)
            qty: 정정 후 주문수량
            price: 정정 후 주문단가
            ord_dvsn: 주문구분 ("00": 지정가)

        Returns:
            정정 결과 Dict
        """
        return self.order_api.modify_reserve_order(rsvn_ord_seq, qty, price, ord_dvsn)

    def cancel_reserve_order(
        self,
        rsvn_ord_seq: str,
    ) -> Optional[Dict[str, Any]]:
        """해외주식 예약주문 취소

        등록된 예약주문을 취소합니다.

        Args:
            rsvn_ord_seq: 예약주문순번 (취소할 예약주문)

        Returns:
            취소 결과 Dict
        """
        return self.order_api.cancel_reserve_order(rsvn_ord_seq)

    # =========================================================================
    # 순위 조회 메서드 (OverseasRankingAPI 위임)
    # =========================================================================

    def trade_volume_ranking(
        self,
        excd: str,
        nday: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 거래량순위 [해외주식-043]

        Args:
            excd: 거래소 코드 (NAS, NYS, AMS, HKS 등)
            nday: N일자값 ("0": 당일, "1": 2일, ...)
            vol_rang: 거래량조건 ("0": 전체, "1": 100주이상, ...)

        Returns:
            거래량 순위 데이터 Dict
        """
        return self.ranking_api.trade_volume_ranking(excd, nday, vol_rang)

    def trade_amount_ranking(
        self,
        excd: str,
        nday: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 거래대금순위 [해외주식-044]"""
        return self.ranking_api.trade_amount_ranking(excd, nday, vol_rang)

    def trade_growth_ranking(
        self,
        excd: str,
        nday: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 거래증가율순위 [해외주식-045]"""
        return self.ranking_api.trade_growth_ranking(excd, nday, vol_rang)

    def trade_turnover_ranking(
        self,
        excd: str,
        nday: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 거래회전율순위 [해외주식-046]"""
        return self.ranking_api.trade_turnover_ranking(excd, nday, vol_rang)

    def market_cap_ranking(
        self,
        excd: str,
        nday: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 시가총액순위 [해외주식-047]"""
        return self.ranking_api.market_cap_ranking(excd, nday, vol_rang)

    def price_change_ranking(
        self,
        excd: str,
        nday: str = "0",
        gubn: str = "1",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 상승률/하락률 순위

        Args:
            excd: 거래소 코드
            nday: N일자값
            gubn: 상승/하락 구분 ("1": 상승률, "2": 하락률)
            vol_rang: 거래량조건
        """
        return self.ranking_api.price_change_ranking(excd, nday, gubn, vol_rang)

    def price_fluctuation_ranking(
        self,
        excd: str,
        nday: str = "0",
        gubn: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 가격급등락 [해외주식-038]

        Args:
            excd: 거래소 코드
            nday: N일자값
            gubn: 급등/급락 구분 ("0": 급등, "1": 급락)
            vol_rang: 거래량조건
        """
        return self.ranking_api.price_fluctuation_ranking(excd, nday, gubn, vol_rang)

    def new_high_low_ranking(
        self,
        excd: str,
        nday: str = "0",
        gubn: str = "1",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 신고/신저가 [해외주식-042]

        Args:
            excd: 거래소 코드
            nday: N일자값
            gubn: 신고/신저 구분 ("0": 신저가, "1": 신고가)
            vol_rang: 거래량조건
        """
        return self.ranking_api.new_high_low_ranking(excd, nday, gubn, vol_rang)

    def volume_power_ranking(
        self,
        excd: str,
        nday: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 매수체결강도상위 [해외주식-040]"""
        return self.ranking_api.volume_power_ranking(excd, nday, vol_rang)

    def volume_surge_ranking(
        self,
        excd: str,
        mixn: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """해외주식 거래량급증 [해외주식-039]

        Args:
            excd: 거래소 코드
            mixn: N분전 콤보값 ("0": 1분전, "3": 5분전, ...)
            vol_rang: 거래량조건
        """
        return self.ranking_api.volume_surge_ranking(excd, mixn, vol_rang)

    # =========================================================================
    # 유틸리티 메서드
    # =========================================================================

    def get_supported_exchanges(self) -> Dict[str, Dict[str, str]]:
        """지원 거래소 목록 조회

        Returns:
            Dict[str, Dict]: 거래소 코드별 정보
                - name: 거래소명
                - country: 국가
                - currency: 통화
        """
        return self.EXCHANGES.copy()

    def is_valid_exchange(self, excd: str) -> bool:
        """거래소 코드 유효성 검사

        Args:
            excd: 거래소 코드

        Returns:
            bool: 유효한 거래소 코드인지 여부
        """
        return excd.upper() in self.EXCHANGES

    def get_exchange_info(self, excd: str) -> Optional[Dict[str, str]]:
        """거래소 정보 조회

        Args:
            excd: 거래소 코드

        Returns:
            거래소 정보 (name, country, currency) 또는 None
        """
        return self.EXCHANGES.get(excd.upper())

    # =========================================================================
    # __getattr__: 하위 API로 동적 위임
    # =========================================================================

    def __getattr__(self, name: str) -> Any:
        """하위 모듈로 동적 위임

        Facade에 명시적으로 정의되지 않은 메서드는
        하위 API에서 자동으로 찾아 호출합니다.
        """
        # 등록된 하위 API들에서 순차적으로 검색
        for api in (self.price_api, self.account_api, self.order_api, self.ranking_api):
            if hasattr(api, name):
                return getattr(api, name)

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


# 하위 호환성을 위한 별칭
OverseasAPI = OverseasStockAPI
