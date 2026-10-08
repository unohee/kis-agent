"""
해외주식 계좌 조회 API

OverseasAccountAPI는 해외주식 잔고, 체결내역, 미체결, 매수가능금액 등을 조회합니다.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import pytz

from ..core.base_api import BaseAPI
from ..core.client import KISClient
from ._compat import kst_date, warn_ignored

# 거래소 현지 기준일을 맞추기 위한 시간대 (미국 현지일은 KST보다 하루 늦다).
_KST = pytz.timezone("Asia/Seoul")
_NEW_YORK = pytz.timezone("America/New_York")

# 예약주문조회: 미국(TTTT3039R)과 그 외 아시아 거래소(TTTS3014R)는 TR_ID가 다르다.
_ASIA_EXCHANGES = ("SEHK", "SHAA", "SZAA", "TKSE", "HASE", "VNSE")


def _utc_now() -> datetime:
    """현재 시각(UTC). 테스트에서 고정값으로 바꿀 수 있도록 분리했다."""
    return datetime.now(pytz.utc)


def _local_date_range() -> Tuple[str, str]:
    """지원 거래소의 '오늘'을 모두 포함하는 (시작일, 종료일)을 YYYYMMDD로 반환한다.

    KIS 주문 조회의 일자는 현지시각 기준이다. KST 오전에는 미국 현지일이 KST보다
    하루 늦으므로 KST 날짜만 쓰면 미국 당일 주문이 빠진다. 서울과 뉴욕의 현지 날짜
    중 이른 쪽을 시작일, 늦은 쪽을 종료일로 쓴다.
    """
    now = _utc_now()
    dates = sorted(
        {
            now.astimezone(_KST).strftime("%Y%m%d"),
            now.astimezone(_NEW_YORK).strftime("%Y%m%d"),
        }
    )
    return dates[0], dates[-1]


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

    def _all_filter(self, value: str) -> str:
        """'전체' 필터값을 환경에 맞게 변환한다.

        실전투자는 전체를 ``"%"``로, 모의투자는 ``""``만 허용한다
        (주문체결내역 PDNO/OVRS_EXCG_CD). 호출자는 둘 중 무엇을 줘도 된다.
        """
        if getattr(self.client, "is_real", True):
            return value or "%"
        return "" if value in ("", "%") else value

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
        pdno: str = "",
        ord_strt_dt: str = "",
        ord_end_dt: str = "",
        sll_buy_dvsn: str = "00",
        ccld_nccs_dvsn: str = "00",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 주문체결내역 조회

        기간 내 해외주식 주문 및 체결 내역을 조회합니다. 기간을 주지 않으면 당일
        (서울과 뉴욕의 현지 날짜를 모두 포함)을 조회합니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드 (공백: 전체. 실전은 "%", 모의는 ""로 자동 변환)
            sort_sqn (str): 정렬순서 (DS: 정순, AS: 역순)
            cont_fk200 (str): 연속조회검색조건200
            cont_nk200 (str): 연속조회키200
            pdno (str): 종목코드 (공백: 전종목. 실전은 "%", 모의는 ""로 자동 변환)
            ord_strt_dt (str): 주문시작일자 YYYYMMDD, 현지시각 기준 (공백: 당일)
            ord_end_dt (str): 주문종료일자 YYYYMMDD, 현지시각 기준 (공백: 당일)
            sll_buy_dvsn (str): 매도매수구분 (00: 전체, 01: 매도, 02: 매수)
            ccld_nccs_dvsn (str): 체결미체결구분 (00: 전체, 01: 체결, 02: 미체결)

        모의투자는 sll_buy_dvsn, ccld_nccs_dvsn 모두 "00"만 지원하고 정렬순서도
        무시됩니다. ORD_DT, ORD_GNO_BRNO, ODNO는 공식 문서에서 빈 값만 허용하므로
        항상 ""로 전송합니다(주문번호로 검색할 수 없음).

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
                    - ft_ccld_amt3: FT체결금액
                    - nccs_qty: 미체결수량
                    - prcs_stat_name: 처리상태명
                    - rjct_rson_name: 거부사유명
                    - ord_tmd: 주문시각
                    - tr_crcy_cd: 거래통화코드

        Example:
            >>> history = agent.overseas.get_order_history(ovrs_excg_cd="NASD")
            >>> for order in history['output']:
            ...     print(f"{order['prdt_name']}: {order['ft_ccld_qty']}주 체결")
        """
        account_params = self._get_account_params()
        default_strt, default_end = _local_date_range()

        params = {
            **account_params,
            "PDNO": self._all_filter(pdno.upper()),
            "ORD_STRT_DT": ord_strt_dt or default_strt,
            "ORD_END_DT": ord_end_dt or default_end,
            "SLL_BUY_DVSN": sll_buy_dvsn,
            "CCLD_NCCS_DVSN": ccld_nccs_dvsn,
            "OVRS_EXCG_CD": self._all_filter(ovrs_excg_cd),
            "SORT_SQN": sort_sqn,
            "ORD_DT": "",
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "CTX_AREA_NK200": cont_nk200,
            "CTX_AREA_FK200": cont_fk200,
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
        inqr_strt_dt: str = "",
        inqr_end_dt: str = "",
        inqr_dvsn_cd: str = "00",
        prdt_type_cd: str = "",
        nat_dv: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 예약주문내역 조회

        예약된 해외주식 주문 내역을 조회합니다. 미국은 TTTT3039R, 홍콩·중국·일본·
        베트남은 TTTS3014R로 TR_ID가 갈립니다. ``ovrs_excg_cd``가 아시아 거래소
        (SEHK/SHAA/SZAA/TKSE/HASE/VNSE)이거나 ``nat_dv="asia"``이면 TTTS3014R,
        그 외에는 TTTT3039R을 사용합니다. 모의투자는 지원하지 않습니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드 (공백: 해당 TR의 전체 거래소)
            sort_sqn (str): 사용하지 않음. 공식 문서에 없는 필드라 전송하지 않습니다.
                기본값("DS")이 아니면 DeprecationWarning.
            ctx_area_fk200 (str): 연속조회검색조건200
            ctx_area_nk200 (str): 연속조회키200
            inqr_strt_dt (str): 조회시작일자 YYYYMMDD (공백: 7일 전)
            inqr_end_dt (str): 조회종료일자 YYYYMMDD (공백: 당일, 서울·뉴욕 현지일 중 늦은 쪽)
            inqr_dvsn_cd (str): 조회구분 (00: 전체, 01: 일반해외주식, 02: 미니스탁)
            prdt_type_cd (str): 상품유형코드 (공백: 해당 TR의 전체. 512: 나스닥,
                513: 뉴욕, 529: 아멕스, 515: 일본, 501: 홍콩, 543: 홍콩CNY,
                558: 홍콩USD, 507: 하노이, 508: 호치민, 551: 상해A, 552: 심천A)
            nat_dv (str): 시장 구분 ("us" 또는 "asia"). 공백이면 거래소로 판단하고,
                거래소도 비어 있으면 미국

        Raises:
            ValueError: ``nat_dv``가 "", "us", "asia"가 아닌 경우

        Returns:
            Optional[Dict]: 예약주문 내역
                - output:
                    - rsvn_ord_rcit_dt: 예약주문접수일자
                    - ovrs_rsvn_odno: 해외예약주문번호
                    - ord_dt: 주문일자
                    - odno: 주문번호
                    - sll_buy_dvsn_cd: 매도매수구분코드
                    - sll_buy_dvsn_name: 매도매수구분명
                    - ovrs_rsvn_ord_stat_cd: 해외예약주문상태코드
                    - pdno: 상품번호
                    - prdt_name: 상품명
                    - ft_ord_qty: FT주문수량
                    - ft_ord_unpr3: FT주문단가
                    - ovrs_excg_cd: 해외거래소코드

        Example:
            >>> reserves = agent.overseas.get_reserve_order_list()
            >>> for order in reserves['output']:
            ...     print(f"{order['prdt_name']}: {order['ft_ord_qty']}주 예약")
        """
        if sort_sqn != "DS":
            warn_ignored("get_reserve_order_list", "sort_sqn")
        if nat_dv not in ("", "us", "asia"):
            raise ValueError(f"nat_dv는 'us' 또는 'asia'여야 합니다: {nat_dv}")

        account_params = self._get_account_params()
        exchange = ovrs_excg_cd.upper()
        is_asia = nat_dv == "asia" or (nat_dv == "" and exchange in _ASIA_EXCHANGES)
        inqr_end_dt = inqr_end_dt or _local_date_range()[1]
        if not inqr_strt_dt:
            end_day = datetime.strptime(inqr_end_dt, "%Y%m%d")
            inqr_strt_dt = (end_day - timedelta(days=7)).strftime("%Y%m%d")

        params = {
            **account_params,
            "INQR_STRT_DT": inqr_strt_dt,
            "INQR_END_DT": inqr_end_dt,
            "INQR_DVSN_CD": inqr_dvsn_cd,
            "OVRS_EXCG_CD": exchange,
            "PRDT_TYPE_CD": prdt_type_cd,
            "CTX_AREA_FK200": ctx_area_fk200,
            "CTX_AREA_NK200": ctx_area_nk200,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/order-resv-list",
            tr_id="TTTS3014R" if is_asia else "TTTT3039R",
            params=params,
            use_cache=False,
        )

    def get_foreign_margin(
        self,
        crcy_cd: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 외화증거금 조회

        해외주식 거래를 위한 외화 증거금 현황을 조회합니다. 통화별 행이 모두 반환되며
        공식 API에는 통화 필터가 없습니다. 모의투자는 지원하지 않습니다.

        Args:
            crcy_cd (str): 사용하지 않음. 공식 문서에 없는 필드라 전송하지 않습니다.
                값을 주면 DeprecationWarning. 필요하면 응답 ``output``에서
                ``crcy_cd``로 직접 고르세요.

        Returns:
            Optional[Dict]: 외화증거금 정보 (통화별 행 리스트)
                - output:
                    - natn_name: 국가명
                    - crcy_cd: 통화코드
                    - frcr_dncl_amt1: 외화예수금액
                    - ustl_buy_amt: 미결제매수금액
                    - ustl_sll_amt: 미결제매도금액
                    - frcr_rcvb_amt: 외화미수금액
                    - frcr_mgn_amt: 외화증거금액
                    - frcr_gnrl_ord_psbl_amt: 외화일반주문가능금액
                    - frcr_ord_psbl_amt1: 외화주문가능금액 (원화주문가능환산금액)
                    - itgr_ord_psbl_amt: 통합주문가능금액
                    - bass_exrt: 기준환율

        Example:
            >>> margin = agent.overseas.get_foreign_margin()
            >>> for row in margin['output']:
            ...     if row['crcy_cd'] == 'USD':
            ...         print(f"USD 주문가능금액: ${row['frcr_ord_psbl_amt1']}")
        """
        if crcy_cd:
            warn_ignored(
                "get_foreign_margin",
                "crcy_cd",
                "응답 output에서 crcy_cd로 직접 고르세요",
            )
        params = self._get_account_params()

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/foreign-margin",
            tr_id="TTTC2101R",
            params=params,
            use_cache=True,
            cache_ttl=10,
        )

    def get_algo_ordno(
        self,
        trad_dt: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 지정가주문번호조회 [해외주식-071]

        해외주식 지정가(알고리즘) 주문의 주문번호를 조회합니다. 여기서 얻은
        ``odno``를 ``get_inquire_algo_ccnl``에 넘겨 체결내역을 조회합니다.
        모의투자는 지원하지 않습니다.

        Args:
            trad_dt (str): 거래일자 YYYYMMDD (공백: 오늘, 서울 기준)
            max_pages (int): 최대 페이지 수

        Returns:
            Optional[Dict]: output 리스트 (odno, trad_dvsn_name, pdno, item_name,
                ft_ord_qty, ft_ord_unpr3, splt_buy_attr_name, ft_ccld_qty)

        Note:
            공식 문서(2025-12-12 xlsx)는 이 API만 계좌상품코드 키를 ``ACNO_PRDT_CD``로
            적었다. 나머지 72개 API와 공식 샘플은 모두 ``ACNT_PRDT_CD``라 문서 오타로 보고
            ``ACNT_PRDT_CD``를 보낸다.

        Example:
            >>> agent.overseas.get_algo_ordno("20250619")
        """
        account = self._get_account_params()
        return self._paginate(
            endpoint="/uapi/overseas-stock/v1/trading/algo-ordno",
            tr_id="TTTS6058R",
            params={
                "CANO": account["CANO"],
                "ACNT_PRDT_CD": account["ACNT_PRDT_CD"],
                "TRAD_DT": trad_dt or kst_date(),
                "CTX_AREA_NK200": "",
                "CTX_AREA_FK200": "",
            },
            cursor=[
                ("CTX_AREA_FK200", "ctx_area_fk200"),
                ("CTX_AREA_NK200", "ctx_area_nk200"),
            ],
            output_keys=("output",),
            max_pages=max_pages,
        )

    def get_inquire_algo_ccnl(
        self,
        odno: str,
        ord_dt: str = "",
        ord_gno_brno: str = "",
        ttlz_icld_yn: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 지정가체결내역조회 [해외주식-070]

        지정가(알고리즘) 주문번호별 체결내역을 조회합니다. 모의투자는 지원하지 않습니다.

        Args:
            odno (str): 지정가주문번호 (``get_algo_ordno``에서 조회한 주문번호)
            ord_dt (str): 주문일자 YYYYMMDD (공백: 오늘, 서울 기준)
            ord_gno_brno (str): 주문채번지점번호 (공백)
            ttlz_icld_yn (str): 집계포함여부 (공백)
            max_pages (int): 최대 페이지 수

        Returns:
            Optional[Dict]:
                - output: 체결 리스트 (ccld_seq, ccld_btwn, pdno, item_name,
                  ft_ccld_qty, ft_ccld_unpr3, ft_ccld_amt3)
                - output3: 주문 요약 (odno, trad_dvsn_name, ft_ord_qty, ft_ord_unpr3,
                  ccld_cnt 등)

        Raises:
            ValueError: ``odno``가 비어 있는 경우

        Example:
            >>> agent.overseas.get_inquire_algo_ccnl("0030012345")
        """
        if not odno:
            raise ValueError(
                "odno는 필수입니다 (get_algo_ordno로 조회한 지정가주문번호)"
            )
        account = self._get_account_params()
        return self._paginate(
            endpoint="/uapi/overseas-stock/v1/trading/inquire-algo-ccnl",
            tr_id="TTTS6059R",
            params={
                **account,
                "ORD_DT": ord_dt or kst_date(),
                "ORD_GNO_BRNO": ord_gno_brno,
                "ODNO": odno,
                "TTLZ_ICLD_YN": ttlz_icld_yn,
                "CTX_AREA_NK200": "",
                "CTX_AREA_FK200": "",
            },
            cursor=[
                ("CTX_AREA_FK200", "ctx_area_fk200"),
                ("CTX_AREA_NK200", "ctx_area_nk200"),
            ],
            output_keys=("output", "output3"),
            max_pages=max_pages,
        )

    def get_inquire_paymt_stdr_balance(
        self,
        bass_dt: str = "",
        wcrc_frcr_dvsn_cd: str = "02",
        inqr_dvsn_cd: str = "00",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 결제기준잔고 [해외주식-064]

        기준일자의 결제기준 해외주식 잔고를 조회합니다. 모의투자는 지원하지 않습니다.

        Args:
            bass_dt (str): 기준일자 YYYYMMDD (공백: 오늘, 서울 기준)
            wcrc_frcr_dvsn_cd (str): 원화외화구분코드 (01: 원화기준, 02: 외화기준)
            inqr_dvsn_cd (str): 조회구분코드 (00: 전체, 01: 일반, 02: 미니스탁)

        Returns:
            Optional[Dict]:
                - output1: 보유종목 (pdno, prdt_name, cblc_qty13, ord_psbl_qty1,
                  avg_unpr3, ovrs_now_pric1, frcr_evlu_amt2, evlu_pfls_amt2)
                - output2: 통화별 (crcy_cd, frcr_dncl_amt_2, frst_bltn_exrt)
                - output3: 합계 (pchs_amt_smtl_amt, tot_evlu_pfls_amt, tot_asst_amt2)

        Example:
            >>> agent.overseas.get_inquire_paymt_stdr_balance("20230630")
        """
        account = self._get_account_params()
        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/inquire-paymt-stdr-balance",
            tr_id="CTRP6010R",
            params={
                **account,
                "BASS_DT": bass_dt or kst_date(),
                "WCRC_FRCR_DVSN_CD": wcrc_frcr_dvsn_cd,
                "INQR_DVSN_CD": inqr_dvsn_cd,
            },
            use_cache=False,
        )

    def get_inquire_period_trans(
        self,
        erlm_strt_dt: str = "",
        erlm_end_dt: str = "",
        ovrs_excg_cd: str = "",
        pdno: str = "",
        sll_buy_dvsn_cd: str = "00",
        loan_dvsn_cd: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 일별거래내역 [해외주식-063]

        기간 내 해외주식 일별 거래(체결·정산) 내역을 조회합니다. 모의투자는 지원하지
        않습니다.

        Args:
            erlm_strt_dt (str): 등록시작일자 YYYYMMDD (공백: 종료일 30일 전)
            erlm_end_dt (str): 등록종료일자 YYYYMMDD (공백: 오늘, 서울 기준)
            ovrs_excg_cd (str): 해외거래소코드 (공백: 전체)
            pdno (str): 상품번호 (공백: 전체, 개별종목은 종목코드)
            sll_buy_dvsn_cd (str): 매도매수구분코드 (00: 전체, 01: 매도, 02: 매수)
            loan_dvsn_cd (str): 대출구분코드 (공백)
            max_pages (int): 최대 페이지 수

        Returns:
            Optional[Dict]:
                - output1: 거래 리스트 (trad_dt, sttl_dt, sll_buy_dvsn_name, pdno,
                  ovrs_item_name, ccld_qty, ft_ccld_unpr2, tr_frcr_amt2, frcr_excc_amt_1,
                  wcrc_excc_amt, frcr_fee1, crcy_cd)
                - output2: 합계 (frcr_buy_amt_smtl, frcr_sll_amt_smtl, dmst_fee_smtl,
                  ovrs_fee_smtl)

        Example:
            >>> agent.overseas.get_inquire_period_trans("20240420", "20240520")
        """
        account = self._get_account_params()
        erlm_end_dt = erlm_end_dt or kst_date()
        if not erlm_strt_dt:
            end_day = datetime.strptime(erlm_end_dt, "%Y%m%d")
            erlm_strt_dt = (end_day - timedelta(days=30)).strftime("%Y%m%d")
        return self._paginate(
            endpoint="/uapi/overseas-stock/v1/trading/inquire-period-trans",
            tr_id="CTOS4001R",
            params={
                **account,
                "ERLM_STRT_DT": erlm_strt_dt,
                "ERLM_END_DT": erlm_end_dt,
                "OVRS_EXCG_CD": ovrs_excg_cd,
                "PDNO": pdno.upper(),
                "SLL_BUY_DVSN_CD": sll_buy_dvsn_cd,
                "LOAN_DVSN_CD": loan_dvsn_cd,
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
            cursor=[
                ("CTX_AREA_FK100", "ctx_area_fk100"),
                ("CTX_AREA_NK100", "ctx_area_nk100"),
            ],
            output_keys=("output1",),
            max_pages=max_pages,
        )
