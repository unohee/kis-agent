"""
해외주식 주문 API

OverseasOrderAPI는 해외주식 매수, 매도, 정정, 취소, 예약주문을 처리합니다.
"""

import logging
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient


class OverseasOrderAPI(BaseAPI):
    """
    해외주식 주문 API

    해외주식 매수/매도, 정정/취소, 예약주문 기능을 제공합니다.

    지원 거래소:
    - NASD: NASDAQ (미국)
    - NYSE: NYSE (미국)
    - AMEX: AMEX (미국)
    - SEHK: 홍콩
    - SHAA: 상해 A주
    - SZAA: 심천 A주
    - TKSE: 도쿄
    - HASE: 하노이
    - VNSE: 호치민

    주문 유형 (ORD_DVSN):
    [미국 매수]
    - "00": 지정가 (Limit Order)
    - "32": LOO (Limit On Open, 장개시지정가)
    - "34": LOC (Limit On Close, 장마감지정가)

    [미국 매도]
    - "00": 지정가 (Limit Order)
    - "31": MOO (Market On Open, 장개시시장가)
    - "32": LOO (Limit On Open, 장개시지정가)
    - "33": MOC (Market On Close, 장마감시장가)
    - "34": LOC (Limit On Close, 장마감지정가)

    [홍콩]
    - "00": 지정가
    - "50": 단주지정가 (Odd Lot Limit Order)

    Example:
        >>> from pykis import Agent
        >>> agent = Agent(...)
        >>> # AAPL 10주 매수 (지정가 $185)
        >>> result = agent.overseas.buy_order("NASD", "AAPL", 10, 185.00)
        >>> print(f"주문번호: {result['output']['odno']}")
    """

    # 거래소 코드 매핑 (조회용 -> 주문용)
    EXCHANGE_MAP = {
        "NAS": "NASD",
        "NYS": "NYSE",
        "AMS": "AMEX",
        "HKS": "SEHK",
        "SHS": "SHAA",
        "SZS": "SZAA",
        "TSE": "TKSE",
        "HSX": "VNSE",
        "HNX": "HASE",
        # 직접 사용도 허용
        "NASD": "NASD",
        "NYSE": "NYSE",
        "AMEX": "AMEX",
        "SEHK": "SEHK",
        "SHAA": "SHAA",
        "SZAA": "SZAA",
        "TKSE": "TKSE",
        "VNSE": "VNSE",
        "HASE": "HASE",
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
        OverseasOrderAPI 초기화

        Args:
            client (KISClient): API 통신 클라이언트
            account_info (dict): 계좌 정보 (CANO, ACNT_PRDT_CD 필수)
            enable_cache (bool): 캐시 사용 여부 (주문은 캐시 미사용)
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

    def _normalize_exchange(self, excd: str) -> str:
        """거래소 코드를 주문용 코드로 변환"""
        normalized = self.EXCHANGE_MAP.get(excd.upper())
        if not normalized:
            raise ValueError(f"지원하지 않는 거래소 코드입니다: {excd}")
        return normalized

    def buy_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        qty: int,
        price: float,
        ord_dvsn: str = "00",
        ord_svr_dvsn_cd: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 매수주문

        Args:
            ovrs_excg_cd (str): 거래소 코드 (NAS/NASD, NYS/NYSE, AMS/AMEX, HKS/SEHK 등)
            pdno (str): 종목코드 (예: AAPL, TSLA, NVDA)
            qty (int): 주문수량
            price (float): 주문단가 (USD 기준, 소수점 허용)
            ord_dvsn (str): 주문구분 (미국 매수는 MOO/MOC 불가!)
                - "00": 지정가 (기본값)
                - "32": LOO (Limit On Open, 장개시지정가)
                - "34": LOC (Limit On Close, 장마감지정가)
            ord_svr_dvsn_cd (str): 주문서버구분코드 ("0": 기본)

        Returns:
            Optional[Dict]: 주문 결과
                - output.odno: 주문번호
                - output.ord_tmd: 주문시각

        Note:
            미국 매수주문은 MOO(31), MOC(33) 사용 불가.
            MOO/MOC는 매도주문(sell_order)에서만 지원됩니다.

        Example:
            >>> # AAPL 10주 지정가 $185 매수
            >>> result = agent.overseas.buy_order("NASD", "AAPL", 10, 185.00)
            >>> print(f"주문번호: {result['output']['odno']}")
            >>>
            >>> # TSLA 5주 LOO 주문 (장개시지정가)
            >>> result = agent.overseas.buy_order("NASD", "TSLA", 5, 250.00, ord_dvsn="32")
        """
        try:
            account_params = self._get_account_params()
            exchange = self._normalize_exchange(ovrs_excg_cd)

            params = {
                **account_params,
                "OVRS_EXCG_CD": exchange,
                "PDNO": pdno.upper(),
                "ORD_QTY": str(qty),
                "OVRS_ORD_UNPR": str(price),
                "ORD_DVSN": ord_dvsn,
                "ORD_SVR_DVSN_CD": ord_svr_dvsn_cd,
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/trading/order",
                tr_id="TTTT1002U",
                params=params,
                method="POST",
                use_cache=False,
            )
        except Exception as e:
            logging.error(f"해외주식 매수주문 실패: {e}")
            raise

    def sell_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        qty: int,
        price: float,
        ord_dvsn: str = "00",
        ord_svr_dvsn_cd: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 매도주문

        Args:
            ovrs_excg_cd (str): 거래소 코드
            pdno (str): 종목코드
            qty (int): 주문수량
            price (float): 주문단가
            ord_dvsn (str): 주문구분 (매도는 MOO/MOC 포함 5가지 지원)
                - "00": 지정가 (기본값)
                - "31": MOO (Market On Open, 장개시시장가)
                - "32": LOO (Limit On Open, 장개시지정가)
                - "33": MOC (Market On Close, 장마감시장가)
                - "34": LOC (Limit On Close, 장마감지정가)
            ord_svr_dvsn_cd (str): 주문서버구분코드

        Returns:
            Optional[Dict]: 주문 결과
                - output.odno: 주문번호
                - output.ord_tmd: 주문시각

        Note:
            미국 매도주문은 MOO(31), MOC(33) 포함 모든 주문유형 지원.
            시장가 주문(MOO, MOC) 시 price=0 설정.

        Example:
            >>> # AAPL 5주 지정가 $190 매도
            >>> result = agent.overseas.sell_order("NASD", "AAPL", 5, 190.00)
            >>>
            >>> # TSLA 10주 MOC (장마감시장가) 매도
            >>> result = agent.overseas.sell_order("NASD", "TSLA", 10, 0, ord_dvsn="33")
        """
        try:
            account_params = self._get_account_params()
            exchange = self._normalize_exchange(ovrs_excg_cd)

            params = {
                **account_params,
                "OVRS_EXCG_CD": exchange,
                "PDNO": pdno.upper(),
                "ORD_QTY": str(qty),
                "OVRS_ORD_UNPR": str(price),
                "ORD_DVSN": ord_dvsn,
                "ORD_SVR_DVSN_CD": ord_svr_dvsn_cd,
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/trading/order",
                tr_id="TTTT1006U",
                params=params,
                method="POST",
                use_cache=False,
            )
        except Exception as e:
            logging.error(f"해외주식 매도주문 실패: {e}")
            raise

    def modify_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        orgn_odno: str,
        qty: int,
        price: float,
        ord_dvsn: str = "00",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 정정주문

        미체결 주문의 가격이나 수량을 정정합니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드
            pdno (str): 종목코드
            orgn_odno (str): 원주문번호 (정정할 주문번호)
            qty (int): 정정 후 주문수량
            price (float): 정정 후 주문단가
            ord_dvsn (str): 주문구분 ("00": 지정가)

        Returns:
            Optional[Dict]: 정정 결과
                - output.odno: 신규 주문번호
                - output.ord_tmd: 정정시각

        Example:
            >>> # 주문번호 "0001234" 주문을 $190으로 정정
            >>> result = agent.overseas.modify_order("NASD", "AAPL", "0001234", 10, 190.00)
        """
        try:
            account_params = self._get_account_params()
            exchange = self._normalize_exchange(ovrs_excg_cd)

            params = {
                **account_params,
                "OVRS_EXCG_CD": exchange,
                "PDNO": pdno.upper(),
                "ORGN_ODNO": orgn_odno,
                "RVSE_CNCL_DVSN_CD": "01",  # 01: 정정
                "ORD_QTY": str(qty),
                "OVRS_ORD_UNPR": str(price),
                "ORD_DVSN": ord_dvsn,
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/trading/order-rvsecncl",
                tr_id="TTTT1004U",
                params=params,
                method="POST",
                use_cache=False,
            )
        except Exception as e:
            logging.error(f"해외주식 정정주문 실패: {e}")
            raise

    def cancel_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        orgn_odno: str,
        qty: int,
        ord_dvsn: str = "00",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 취소주문

        미체결 주문을 취소합니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드
            pdno (str): 종목코드
            orgn_odno (str): 원주문번호 (취소할 주문번호)
            qty (int): 취소수량
            ord_dvsn (str): 주문구분 ("00": 지정가)

        Returns:
            Optional[Dict]: 취소 결과
                - output.odno: 취소 주문번호
                - output.ord_tmd: 취소시각

        Example:
            >>> # 주문번호 "0001234" 전량 취소
            >>> result = agent.overseas.cancel_order("NASD", "AAPL", "0001234", 10)
        """
        try:
            account_params = self._get_account_params()
            exchange = self._normalize_exchange(ovrs_excg_cd)

            params = {
                **account_params,
                "OVRS_EXCG_CD": exchange,
                "PDNO": pdno.upper(),
                "ORGN_ODNO": orgn_odno,
                "RVSE_CNCL_DVSN_CD": "02",  # 02: 취소
                "ORD_QTY": str(qty),
                "OVRS_ORD_UNPR": "0",  # 취소 시 가격 불필요
                "ORD_DVSN": ord_dvsn,
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/trading/order-rvsecncl",
                tr_id="TTTT1003U",
                params=params,
                method="POST",
                use_cache=False,
            )
        except Exception as e:
            logging.error(f"해외주식 취소주문 실패: {e}")
            raise

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
        """
        해외주식 예약주문

        지정된 날짜에 주문을 자동으로 실행하는 예약주문을 등록합니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드
            pdno (str): 종목코드
            sll_buy_dvsn_cd (str): 매도매수구분 ("01": 매도, "02": 매수)
            qty (int): 주문수량
            price (float): 주문단가
            ord_dvsn (str): 주문구분 ("00": 지정가)
            rsvn_ord_end_dt (str): 예약종료일자 (YYYYMMDD, 공백 시 당일)

        Returns:
            Optional[Dict]: 예약주문 결과
                - output.rsvn_ord_seq: 예약주문순번

        Example:
            >>> # AAPL 10주 예약매수 (지정가 $180)
            >>> result = agent.overseas.reserve_order(
            ...     "NASD", "AAPL", "02", 10, 180.00
            ... )
        """
        try:
            account_params = self._get_account_params()
            exchange = self._normalize_exchange(ovrs_excg_cd)

            params = {
                **account_params,
                "OVRS_EXCG_CD": exchange,
                "PDNO": pdno.upper(),
                "SLL_BUY_DVSN_CD": sll_buy_dvsn_cd,
                "RSVN_ORD_QTY": str(qty),
                "RSVN_ORD_UNPR": str(price),
                "ORD_DVSN": ord_dvsn,
                "RSVN_ORD_END_DT": rsvn_ord_end_dt,
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/trading/order-resv",
                tr_id="TTTS6036U",
                params=params,
                method="POST",
                use_cache=False,
            )
        except Exception as e:
            logging.error(f"해외주식 예약주문 실패: {e}")
            raise

    def modify_reserve_order(
        self,
        rsvn_ord_seq: str,
        qty: int,
        price: float,
        ord_dvsn: str = "00",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 예약주문 정정

        등록된 예약주문의 수량이나 가격을 정정합니다.

        Args:
            rsvn_ord_seq (str): 예약주문순번 (정정할 예약주문)
            qty (int): 정정 후 주문수량
            price (float): 정정 후 주문단가
            ord_dvsn (str): 주문구분 ("00": 지정가)

        Returns:
            Optional[Dict]: 정정 결과

        Example:
            >>> # 예약주문 "001" 정정
            >>> result = agent.overseas.modify_reserve_order("001", 15, 175.00)
        """
        try:
            account_params = self._get_account_params()

            params = {
                **account_params,
                "RSVN_ORD_SEQ": rsvn_ord_seq,
                "RSVN_ORD_QTY": str(qty),
                "RSVN_ORD_UNPR": str(price),
                "ORD_DVSN": ord_dvsn,
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/trading/order-resv-rvsecncl",
                tr_id="TTTS6037U",
                params=params,
                method="POST",
                use_cache=False,
            )
        except Exception as e:
            logging.error(f"해외주식 예약주문 정정 실패: {e}")
            raise

    def cancel_reserve_order(
        self,
        rsvn_ord_seq: str,
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 예약주문 취소

        등록된 예약주문을 취소합니다.

        Args:
            rsvn_ord_seq (str): 예약주문순번 (취소할 예약주문)

        Returns:
            Optional[Dict]: 취소 결과

        Example:
            >>> # 예약주문 "001" 취소
            >>> result = agent.overseas.cancel_reserve_order("001")
        """
        try:
            account_params = self._get_account_params()

            params = {
                **account_params,
                "RSVN_ORD_SEQ": rsvn_ord_seq,
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/trading/order-resv-ccnl",
                tr_id="TTTS6038U",
                params=params,
                method="POST",
                use_cache=False,
            )
        except Exception as e:
            logging.error(f"해외주식 예약주문 취소 실패: {e}")
            raise
