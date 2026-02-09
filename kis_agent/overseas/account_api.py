"""
해외주식 계좌 조회 API

OverseasAccountAPI는 해외주식 잔고, 체결내역, 미체결, 매수가능금액 등을 조회합니다.
"""

from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient


class OverseasAccountAPI(BaseAPI):
    """
    해외주식 계좌 조회 API

    해외주식 잔고, 주문체결내역, 미체결내역, 매수가능금액 등 계좌 관련 조회 기능을 제공합니다.

    Attributes:
        client (KISClient): API 통신 클라이언트
        account (Dict): 계좌 정보 (CANO, ACNT_PRDT_CD)

    Example:
        >>> from kis_agent import Agent
        >>> agent = Agent(...)
        >>> balance = agent.overseas.get_balance()
        >>> for item in balance['output1']:
        ...     print(f"{item['ovrs_pdno']}: {item['ovrs_cblc_qty']}주")
    """

    def __init__(
        self,
        client: KISClient,
        account_info: Optional[Dict[str, Any]] = None,
        enable_cache: bool = True,
        cache_config: Optional[Dict[str, Any]] = None,
        _from_agent: bool = False,
    ) -> None:
        """
        OverseasAccountAPI 초기화

        Args:
            client (KISClient): API 통신 클라이언트
            account_info (dict): 계좌 정보 (CANO, ACNT_PRDT_CD 필수)
            enable_cache (bool): 캐시 사용 여부 (기본: True)
            cache_config (dict, optional): 캐시 설정
            _from_agent (bool): Agent를 통해 생성되었는지 여부
        """
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

    def _get_account_params(self) -> Dict[str, str]:
        """계좌 파라미터 반환"""
        if not self.account:
            raise ValueError("계좌 정보가 설정되지 않았습니다.")
        return {
            "CANO": self.account.get("CANO", ""),
            "ACNT_PRDT_CD": self.account.get("ACNT_PRDT_CD", "01"),
        }

    def get_balance(
        self,
        ovrs_excg_cd: str = "",
        tr_crcy_cd: str = "",
        ctx_area_fk200: str = "",
        ctx_area_nk200: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 잔고 조회

        보유 해외주식 종목별 잔고와 평가금액을 조회합니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드 (공백: 전체, NASD/NYSE/AMEX/SEHK/SHAA/SZAA/TKSE/HASE/VNSE)
            tr_crcy_cd (str): 거래통화코드 (공백: 전체, USD/HKD/CNY/JPY/VND)
            ctx_area_fk200 (str): 연속조회검색조건200 (최초조회시 공백)
            ctx_area_nk200 (str): 연속조회키200 (최초조회시 공백)

        Returns:
            Optional[Dict]: 잔고 정보
                - output1: 보유종목 리스트
                    - ovrs_pdno: 해외종목번호
                    - ovrs_item_name: 해외종목명
                    - frcr_evlu_pfls_amt: 외화평가손익금액
                    - evlu_pfls_rt: 평가손익율
                    - pchs_avg_pric: 매입평균가격
                    - ovrs_cblc_qty: 해외잔고수량
                    - ord_psbl_qty: 주문가능수량
                    - frcr_pchs_amt1: 외화매입금액
                    - ovrs_stck_evlu_amt: 해외주식평가금액
                    - now_pric2: 현재가격
                - output2: 요약 정보
                    - tot_evlu_pfls_amt: 총평가손익금액
                    - tot_pftrt: 총수익률
                    - frcr_buy_amt_smtl1: 외화매수금액합계

        Example:
            >>> balance = agent.overseas.get_balance()
            >>> for item in balance['output1']:
            ...     print(f"{item['ovrs_item_name']}: {item['ovrs_cblc_qty']}주, 손익: {item['evlu_pfls_rt']}%")
        """
        account_params = self._get_account_params()

        params = {
            **account_params,
            "OVRS_EXCG_CD": ovrs_excg_cd,
            "TR_CRCY_CD": tr_crcy_cd,
            "CTX_AREA_FK200": ctx_area_fk200,
            "CTX_AREA_NK200": ctx_area_nk200,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/inquire-balance",
            tr_id="TTTS3012R",
            params=params,
            use_cache=True,
            cache_ttl=10,
        )

    def get_order_history(
        self,
        ovrs_excg_cd: str = "",
        sort_sqn: str = "DS",
        cont_fk200: str = "",
        cont_nk200: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 주문체결내역 조회

        당일 해외주식 주문 및 체결 내역을 조회합니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드 (공백: 전체)
            sort_sqn (str): 정렬순서 (DS: 정순, AS: 역순)
            cont_fk200 (str): 연속조회검색조건200
            cont_nk200 (str): 연속조회키200

        Returns:
            Optional[Dict]: 체결내역
                - output:
                    - ord_dt: 주문일자
                    - ord_gno_brno: 주문채번지점번호
                    - odno: 주문번호
                    - orgn_odno: 원주문번호
                    - sll_buy_dvsn_cd: 매도매수구분코드 (01: 매도, 02: 매수)
                    - sll_buy_dvsn_cd_name: 매도매수구분명
                    - rvse_cncl_dvsn: 정정취소구분
                    - pdno: 상품번호
                    - prdt_name: 상품명
                    - ft_ord_qty: FT주문수량
                    - ft_ord_unpr3: FT주문단가
                    - ft_ccld_qty: FT체결수량
                    - ft_ccld_unpr3: FT체결단가
                    - nccs_qty: 미체결수량
                    - ord_tmd: 주문시각
                    - tr_crcy_cd: 거래통화코드

        Example:
            >>> history = agent.overseas.get_order_history(ovrs_excg_cd="NASD")
            >>> for order in history['output']:
            ...     print(f"{order['prdt_name']}: {order['ft_ccld_qty']}주 체결")
        """
        account_params = self._get_account_params()

        params = {
            **account_params,
            "OVRS_EXCG_CD": ovrs_excg_cd,
            "SORT_SQN": sort_sqn,
            "CTX_AREA_FK200": cont_fk200,
            "CTX_AREA_NK200": cont_nk200,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/inquire-ccnl",
            tr_id="TTTS3035R",
            params=params,
            use_cache=False,  # 체결내역은 실시간성 필요
        )

    def get_unfilled_orders(
        self,
        ovrs_excg_cd: str = "",
        sort_sqn: str = "DS",
        ctx_area_fk200: str = "",
        ctx_area_nk200: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 미체결내역 조회

        미체결 상태의 해외주식 주문을 조회합니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드 (공백: 전체)
            sort_sqn (str): 정렬순서 (DS: 정순, AS: 역순)
            ctx_area_fk200 (str): 연속조회검색조건200
            ctx_area_nk200 (str): 연속조회키200

        Returns:
            Optional[Dict]: 미체결 내역
                - output:
                    - ord_dt: 주문일자
                    - ord_gno_brno: 주문채번지점번호
                    - odno: 주문번호
                    - orgn_odno: 원주문번호
                    - pdno: 상품번호
                    - prdt_name: 상품명
                    - sll_buy_dvsn_cd: 매도매수구분코드
                    - ft_ord_qty: FT주문수량
                    - ft_ord_unpr3: FT주문단가
                    - ft_ccld_qty: FT체결수량
                    - nccs_qty: 미체결수량
                    - ord_tmd: 주문시각
                    - ovrs_excg_cd: 해외거래소코드

        Example:
            >>> unfilled = agent.overseas.get_unfilled_orders()
            >>> for order in unfilled['output']:
            ...     print(f"{order['prdt_name']}: {order['nccs_qty']}주 미체결")
        """
        account_params = self._get_account_params()

        params = {
            **account_params,
            "OVRS_EXCG_CD": ovrs_excg_cd,
            "SORT_SQN": sort_sqn,
            "CTX_AREA_FK200": ctx_area_fk200,
            "CTX_AREA_NK200": ctx_area_nk200,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/inquire-nccs",
            tr_id="TTTS3018R",
            params=params,
            use_cache=False,
        )

    def get_buyable_amount(
        self,
        ovrs_excg_cd: str,
        ovrs_ord_unpr: str = "0",
        item_cd: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 매수가능금액 조회

        해외주식 매수 가능한 금액과 수량을 조회합니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드 (NASD/NYSE/AMEX/SEHK/SHAA/SZAA/TKSE/HASE/VNSE)
            ovrs_ord_unpr (str): 해외주문단가 (시장가: "0")
            item_cd (str): 종목코드 (공백 시 통화별 총 매수가능금액)

        Returns:
            Optional[Dict]: 매수가능 정보
                - output:
                    - ovrs_ord_psbl_amt: 해외주문가능금액
                    - frcr_ord_psbl_amt1: 외화주문가능금액
                    - max_ord_psbl_qty: 최대주문가능수량
                    - echm_af_ord_psbl_amt: 환전후주문가능금액
                    - ord_psbl_frcr_amt: 주문가능외화금액
                    - ovrs_excg_cd: 해외거래소코드
                    - tr_crcy_cd: 거래통화코드

        Example:
            >>> buyable = agent.overseas.get_buyable_amount("NASD", item_cd="AAPL")
            >>> print(f"매수가능금액: ${buyable['output']['frcr_ord_psbl_amt1']}")
            >>> print(f"최대매수수량: {buyable['output']['max_ord_psbl_qty']}주")
        """
        account_params = self._get_account_params()

        params = {
            **account_params,
            "OVRS_EXCG_CD": ovrs_excg_cd,
            "OVRS_ORD_UNPR": ovrs_ord_unpr,
            "ITEM_CD": item_cd,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/inquire-psamount",
            tr_id="TTTS3007R",
            params=params,
            use_cache=True,
            cache_ttl=5,
        )

    def get_present_balance(
        self,
        wcrc_frcr_dvsn_cd: str = "02",
        natn_cd: str = "",
        tr_mket_cd: str = "",
        inqr_dvsn_cd: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 체결기준현재잔고 조회

        체결 기준의 현재 해외주식 잔고를 조회합니다.

        Args:
            wcrc_frcr_dvsn_cd (str): 원화외화구분코드 (01: 원화, 02: 외화)
            natn_cd (str): 국가코드 (공백: 전체, 840: 미국 등)
            tr_mket_cd (str): 거래시장코드 (공백: 전체)
            inqr_dvsn_cd (str): 조회구분코드

        Returns:
            Optional[Dict]: 체결기준잔고
                - output1: 보유종목 리스트
                    - cano: 계좌번호
                    - prdt_name: 상품명
                    - frcr_pchs_amt: 외화매입금액
                    - ovrs_cblc_qty: 해외잔고수량
                    - pchs_avg_pric: 매입평균가격
                    - frcr_evlu_amt: 외화평가금액
                    - evlu_pfls_amt: 평가손익금액
                    - evlu_pfls_rt: 평가손익율
                - output2: 요약 정보
                    - frcr_pchs_amt_smtl: 외화매입금액합계
                    - frcr_evlu_amt_smtl: 외화평가금액합계
                    - evlu_pfls_amt_smtl: 평가손익금액합계

        Example:
            >>> balance = agent.overseas.get_present_balance()
            >>> print(f"총 평가손익: {balance['output2']['evlu_pfls_amt_smtl']}")
        """
        account_params = self._get_account_params()

        params = {
            **account_params,
            "WCRC_FRCR_DVSN_CD": wcrc_frcr_dvsn_cd,
            "NATN_CD": natn_cd,
            "TR_MKET_CD": tr_mket_cd,
            "INQR_DVSN_CD": inqr_dvsn_cd,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/inquire-present-balance",
            tr_id="CTRP6504R",
            params=params,
            use_cache=True,
            cache_ttl=10,
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
        """
        해외주식 기간손익 조회

        특정 기간의 해외주식 실현손익을 조회합니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드 (공백: 전체)
            natn_cd (str): 국가코드 (공백: 전체)
            crcy_cd (str): 통화코드 (공백: 전체)
            pdno (str): 종목코드 (공백: 전체)
            inqr_strt_dt (str): 조회시작일자 (YYYYMMDD)
            inqr_end_dt (str): 조회종료일자 (YYYYMMDD)
            wcrc_frcr_dvsn_cd (str): 원화외화구분 (01: 원화, 02: 외화)
            ctx_area_fk200 (str): 연속조회검색조건
            ctx_area_nk200 (str): 연속조회키

        Returns:
            Optional[Dict]: 기간손익
                - output1: 종목별 손익 리스트
                    - ovrs_pdno: 해외상품번호
                    - ovrs_item_name: 해외종목명
                    - frcr_sll_amt_smtl: 외화매도금액합계
                    - frcr_buy_amt_smtl: 외화매수금액합계
                    - ovrs_rlzt_pfls_amt: 해외실현손익금액
                    - pftrt: 수익률
                    - sll_qty: 매도수량
                    - buy_qty: 매수수량
                - output2: 요약 정보
                    - frcr_sll_amt_smtl: 외화매도금액합계
                    - frcr_buy_amt_smtl: 외화매수금액합계
                    - ovrs_rlzt_pfls_amt: 해외실현손익금액

        Example:
            >>> profit = agent.overseas.get_period_profit(
            ...     inqr_strt_dt="20250101",
            ...     inqr_end_dt="20250107"
            ... )
            >>> print(f"기간 실현손익: {profit['output2']['ovrs_rlzt_pfls_amt']}")
        """
        account_params = self._get_account_params()

        params = {
            **account_params,
            "OVRS_EXCG_CD": ovrs_excg_cd,
            "NATN_CD": natn_cd,
            "CRCY_CD": crcy_cd,
            "PDNO": pdno,
            "INQR_STRT_DT": inqr_strt_dt,
            "INQR_END_DT": inqr_end_dt,
            "WCRC_FRCR_DVSN_CD": wcrc_frcr_dvsn_cd,
            "CTX_AREA_FK200": ctx_area_fk200,
            "CTX_AREA_NK200": ctx_area_nk200,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/inquire-period-profit",
            tr_id="TTTS3039R",
            params=params,
            use_cache=True,
            cache_ttl=30,
        )

    def get_reserve_order_list(
        self,
        ovrs_excg_cd: str = "",
        sort_sqn: str = "DS",
        ctx_area_fk200: str = "",
        ctx_area_nk200: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 예약주문내역 조회

        예약된 해외주식 주문 내역을 조회합니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드 (공백: 전체)
            sort_sqn (str): 정렬순서 (DS: 정순, AS: 역순)
            ctx_area_fk200 (str): 연속조회검색조건
            ctx_area_nk200 (str): 연속조회키

        Returns:
            Optional[Dict]: 예약주문 내역
                - output:
                    - rsvn_ord_seq: 예약주문순번
                    - rsvn_ord_dt: 예약주문일자
                    - rsvn_ord_rcit_dt: 예약주문접수일자
                    - ord_dvsn_cd: 주문구분코드
                    - sll_buy_dvsn_cd: 매도매수구분
                    - pdno: 상품번호
                    - prdt_name: 상품명
                    - rsvn_ord_qty: 예약주문수량
                    - rsvn_ord_pric: 예약주문가격
                    - rsvn_ord_rcit_pric: 예약주문접수가격
                    - rsvn_ord_stat_cd: 예약주문상태코드
                    - ovrs_excg_cd: 해외거래소코드

        Example:
            >>> reserves = agent.overseas.get_reserve_order_list()
            >>> for order in reserves['output']:
            ...     print(f"{order['prdt_name']}: {order['rsvn_ord_qty']}주 예약")
        """
        account_params = self._get_account_params()

        params = {
            **account_params,
            "OVRS_EXCG_CD": ovrs_excg_cd,
            "SORT_SQN": sort_sqn,
            "CTX_AREA_FK200": ctx_area_fk200,
            "CTX_AREA_NK200": ctx_area_nk200,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/order-resv-list",
            tr_id="TTTT3039R",
            params=params,
            use_cache=False,
        )

    def get_foreign_margin(
        self,
        crcy_cd: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 외화증거금 조회

        해외주식 거래를 위한 외화 증거금 현황을 조회합니다.

        Args:
            crcy_cd (str): 통화코드 (공백: 전체, USD/HKD/CNY/JPY/VND)

        Returns:
            Optional[Dict]: 외화증거금 정보
                - output:
                    - crcy_cd: 통화코드
                    - crcy_cd_name: 통화코드명
                    - frst_bltn_exrt: 최초고시환율
                    - frcr_dncl_amt: 외화예수금액
                    - frcr_evlu_amt: 외화평가금액
                    - frcr_use_psbl_amt: 외화사용가능금액
                    - frcr_ord_psbl_amt: 외화주문가능금액

        Example:
            >>> margin = agent.overseas.get_foreign_margin(crcy_cd="USD")
            >>> print(f"USD 주문가능금액: ${margin['output']['frcr_ord_psbl_amt']}")
        """
        account_params = self._get_account_params()

        params = {
            **account_params,
            "CRCY_CD": crcy_cd,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/foreign-margin",
            tr_id="TTTC2101R",
            params=params,
            use_cache=True,
            cache_ttl=10,
        )
