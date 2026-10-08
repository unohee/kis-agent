"""
해외주식 주문 API

OverseasOrderAPI는 해외주식 매수, 매도, 정정, 취소, 예약주문을 처리합니다.
"""

import logging
import warnings
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
        >>> from kis_agent import Agent
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

    _US_EXCHANGES = ("NASD", "NYSE", "AMEX")

    # 거래소별 주문 TR_ID (공식 샘플 examples_llm/overseas_stock/order, KIS 문서 v1_해외주식-001).
    _BUY_TR = {
        "NASD": "TTTT1002U",
        "NYSE": "TTTT1002U",
        "AMEX": "TTTT1002U",
        "SEHK": "TTTS1002U",
        "SHAA": "TTTS0202U",
        "SZAA": "TTTS0305U",
        "TKSE": "TTTS0308U",
        "HASE": "TTTS0311U",
        "VNSE": "TTTS0311U",
    }
    _SELL_TR = {
        "NASD": "TTTT1006U",
        "NYSE": "TTTT1006U",
        "AMEX": "TTTT1006U",
        "SEHK": "TTTS1001U",
        "SHAA": "TTTS1005U",
        "SZAA": "TTTS0304U",
        "TKSE": "TTTS0307U",
        "HASE": "TTTS0310U",
        "VNSE": "TTTS0310U",
    }
    # 정정취소 TR_ID (KIS 문서 v1_해외주식-003). 상해·심천·베트남은 취소만 가능.
    _CANCEL_TR = {
        "NASD": "TTTT1004U",
        "NYSE": "TTTT1004U",
        "AMEX": "TTTT1004U",
        "SEHK": "TTTS1003U",
        "TKSE": "TTTS0309U",
        "SHAA": "TTTS0302U",
        "SZAA": "TTTS0306U",
        "HASE": "TTTS0312U",
        "VNSE": "TTTS0312U",
    }
    _MODIFY_TR = {
        "NASD": "TTTT1004U",
        "NYSE": "TTTT1004U",
        "AMEX": "TTTT1004U",
        "SEHK": "TTTS1003U",
        "TKSE": "TTTS0309U",
    }
    # 예약주문 상품유형코드 (TTTS3013U 전용, KIS 문서 v1_해외주식-002)
    _RESV_PRDT_TYPE = {
        "TKSE": "515",
        "SEHK": "501",
        "HASE": "507",
        "VNSE": "508",
        "SHAA": "551",
        "SZAA": "552",
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

    def _tr_for(self, table: Dict[str, str], exchange: str, action: str) -> str:
        """거래소별 TR_ID를 고른다. 지원하지 않는 조합이면 ValueError."""
        tr_id = table.get(exchange)
        if not tr_id:
            raise ValueError(f"{exchange} 거래소는 {action}을(를) 지원하지 않습니다")
        return tr_id

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
        해외주식 매수주문 [v1_해외주식-001]

        TR_ID는 거래소별로 다르다 (미국 TTTT1002U, 홍콩 TTTS1002U, 상해 TTTS0202U,
        심천 TTTS0305U, 도쿄 TTTS0308U, 베트남 TTTS0311U).

        Args:
            ovrs_excg_cd (str): 거래소 코드 (NAS/NASD, NYS/NYSE, AMS/AMEX, HKS/SEHK 등)
            pdno (str): 종목코드 (예: AAPL, TSLA, NVDA)
            qty (int): 주문수량
            price (float): 주문단가 (해당 시장 통화 기준, 소수점 허용)
            ord_dvsn (str): 주문구분 (미국 매수는 MOO/MOC 불가!)
                - "00": 지정가 (기본값)
                - "32": LOO (Limit On Open, 장개시지정가)
                - "34": LOC (Limit On Close, 장마감지정가)
            ord_svr_dvsn_cd (str): 주문서버구분코드 ("0": 기본)

        Returns:
            Optional[Dict]: 주문 결과
                - output.odno: 주문번호
                - output.ord_tmd: 주문시각

        Example:
            >>> result = agent.overseas.buy_order("NASD", "AAPL", 10, 185.00)
            >>> result = agent.overseas.buy_order("SEHK", "00700", 100, 300.0)
        """
        try:
            account_params = self._get_account_params()
            exchange = self._normalize_exchange(ovrs_excg_cd)
            tr_id = self._tr_for(self._BUY_TR, exchange, "매수")

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
                tr_id=tr_id,
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
        해외주식 매도주문 [v1_해외주식-001]

        TR_ID는 거래소별로 다르다 (미국 TTTT1006U, 홍콩 TTTS1001U, 상해 TTTS1005U,
        심천 TTTS0304U, 도쿄 TTTS0307U, 베트남 TTTS0310U).

        Args:
            ovrs_excg_cd (str): 거래소 코드
            pdno (str): 종목코드
            qty (int): 주문수량
            price (float): 주문단가 (시장가 계열 MOO/MOC는 0)
            ord_dvsn (str): 주문구분
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

        Example:
            >>> result = agent.overseas.sell_order("NASD", "AAPL", 5, 190.00)
            >>> result = agent.overseas.sell_order("NASD", "TSLA", 10, 0, ord_dvsn="33")
        """
        try:
            account_params = self._get_account_params()
            exchange = self._normalize_exchange(ovrs_excg_cd)
            tr_id = self._tr_for(self._SELL_TR, exchange, "매도")

            params = {
                **account_params,
                "OVRS_EXCG_CD": exchange,
                "PDNO": pdno.upper(),
                "ORD_QTY": str(qty),
                "OVRS_ORD_UNPR": str(price),
                "SLL_TYPE": "00",  # 판매유형: 매도 주문은 "00"
                "ORD_DVSN": ord_dvsn,
                "ORD_SVR_DVSN_CD": ord_svr_dvsn_cd,
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/trading/order",
                tr_id=tr_id,
                params=params,
                method="POST",
                use_cache=False,
            )
        except Exception as e:
            logging.error(f"해외주식 매도주문 실패: {e}")
            raise

    @staticmethod
    def _warn_ignored_ord_dvsn(ord_dvsn: str, method: str) -> None:
        if ord_dvsn != "00":
            warnings.warn(
                f"{method}의 ord_dvsn은 KIS 정정취소 API에 해당 필드가 없어 무시됩니다",
                DeprecationWarning,
                stacklevel=3,
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
        """
        해외주식 정정주문 [v1_해외주식-003]

        미체결 주문의 가격이나 수량을 정정합니다. TR_ID는 거래소별로 다르다
        (미국 TTTT1004U, 홍콩 TTTS1003U, 도쿄 TTTS0309U). 상해·심천·베트남은
        KIS가 정정을 제공하지 않으므로 취소 후 재주문해야 한다.

        Args:
            ovrs_excg_cd (str): 거래소 코드
            pdno (str): 종목코드
            orgn_odno (str): 원주문번호 (정정할 주문번호)
            qty (int): 정정 후 주문수량
            price (float): 정정 후 주문단가
            ord_dvsn (str): 사용하지 않음 (정정취소 API에 주문구분 필드가 없다).
                하위 호환을 위해 남겨 두며, 기본값이 아니면 DeprecationWarning.

        Returns:
            Optional[Dict]: 정정 결과
                - output.odno: 신규 주문번호
                - output.ord_tmd: 정정시각

        Raises:
            ValueError: 정정을 지원하지 않는 거래소(상해·심천·베트남)

        Example:
            >>> result = agent.overseas.modify_order("NASD", "AAPL", "0001234", 10, 190.00)
        """
        try:
            self._warn_ignored_ord_dvsn(ord_dvsn, "modify_order")
            account_params = self._get_account_params()
            exchange = self._normalize_exchange(ovrs_excg_cd)
            tr_id = self._tr_for(
                self._MODIFY_TR, exchange, "정정 (취소 후 재주문 필요)"
            )

            params = {
                **account_params,
                "OVRS_EXCG_CD": exchange,
                "PDNO": pdno.upper(),
                "ORGN_ODNO": orgn_odno,
                "RVSE_CNCL_DVSN_CD": "01",  # 01: 정정
                "ORD_QTY": str(qty),
                "OVRS_ORD_UNPR": str(price),
                "ORD_SVR_DVSN_CD": "0",
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/trading/order-rvsecncl",
                tr_id=tr_id,
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
        해외주식 취소주문 [v1_해외주식-003]

        미체결 주문을 취소합니다. TR_ID는 거래소별로 다르다 (미국 TTTT1004U,
        홍콩 TTTS1003U, 도쿄 TTTS0309U, 상해 TTTS0302U, 심천 TTTS0306U,
        베트남 TTTS0312U). 정정과 취소는 ``RVSE_CNCL_DVSN_CD``로 구분한다.

        Args:
            ovrs_excg_cd (str): 거래소 코드
            pdno (str): 종목코드
            orgn_odno (str): 원주문번호 (취소할 주문번호)
            qty (int): 취소수량
            ord_dvsn (str): 사용하지 않음 (하위 호환용, 기본값이 아니면 DeprecationWarning)

        Returns:
            Optional[Dict]: 취소 결과
                - output.odno: 취소 주문번호
                - output.ord_tmd: 취소시각

        Example:
            >>> result = agent.overseas.cancel_order("NASD", "AAPL", "0001234", 10)
        """
        try:
            self._warn_ignored_ord_dvsn(ord_dvsn, "cancel_order")
            account_params = self._get_account_params()
            exchange = self._normalize_exchange(ovrs_excg_cd)
            tr_id = self._tr_for(self._CANCEL_TR, exchange, "취소")

            params = {
                **account_params,
                "OVRS_EXCG_CD": exchange,
                "PDNO": pdno.upper(),
                "ORGN_ODNO": orgn_odno,
                "RVSE_CNCL_DVSN_CD": "02",  # 02: 취소
                "ORD_QTY": str(qty),
                "OVRS_ORD_UNPR": "0",  # 취소 시 "0"
                "ORD_SVR_DVSN_CD": "0",
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/trading/order-rvsecncl",
                tr_id=tr_id,
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
        해외주식 예약주문접수 [v1_해외주식-002]

        다음 영업일 장 시작 시 접수될 예약주문을 등록합니다.

        - 미국: 매수 TTTT3014U, 매도 TTTT3016U. ``ord_dvsn``으로 지정가(00),
          MOO(31, 매도만), TWAP(35), VWAP(36)을 고른다.
        - 홍콩·중국·일본·베트남: TTTS3013U. 상품유형코드는 거래소에서 정해진다.

        Args:
            ovrs_excg_cd (str): 거래소 코드
            pdno (str): 종목코드
            sll_buy_dvsn_cd (str): 매도매수구분 ("01": 매도, "02": 매수)
            qty (int): 주문수량
            price (float): 주문단가
            ord_dvsn (str): 주문구분 (미국만 사용, 기본 "00" 지정가)
            rsvn_ord_end_dt (str): 사용하지 않음. KIS 예약주문접수 API에 종료일자
                필드가 없다. 값을 주면 DeprecationWarning.

        Returns:
            Optional[Dict]: 예약주문 결과
                - output.odno: 예약주문번호 (취소 시 ``ovrs_rsvn_odno``로 사용)
                - output.rsvn_ord_rcit_dt: 예약주문접수일자 (아시아만)
                - output.ovrs_rsvn_odno: 해외예약주문번호 (아시아만)

        Raises:
            ValueError: ``sll_buy_dvsn_cd``가 "01"/"02"가 아닌 경우

        Example:
            >>> result = agent.overseas.reserve_order("NASD", "AAPL", "02", 10, 180.00)
        """
        try:
            if sll_buy_dvsn_cd not in ("01", "02"):
                raise ValueError(
                    f"sll_buy_dvsn_cd는 '01'(매도) 또는 '02'(매수)여야 합니다: {sll_buy_dvsn_cd}"
                )
            if rsvn_ord_end_dt:
                warnings.warn(
                    "reserve_order의 rsvn_ord_end_dt는 KIS 예약주문접수 API에 없는 필드라 무시됩니다",
                    DeprecationWarning,
                    stacklevel=2,
                )
            account_params = self._get_account_params()
            exchange = self._normalize_exchange(ovrs_excg_cd)
            is_us = exchange in self._US_EXCHANGES
            is_buy = sll_buy_dvsn_cd == "02"

            params = {
                **account_params,
                "PDNO": pdno.upper(),
                "OVRS_EXCG_CD": exchange,
                "FT_ORD_QTY": str(qty),
                "FT_ORD_UNPR3": str(price),
                "ORD_SVR_DVSN_CD": "0",
            }
            if is_us:
                params["ORD_DVSN"] = ord_dvsn
            else:
                params["SLL_BUY_DVSN_CD"] = sll_buy_dvsn_cd
                params["RVSE_CNCL_DVSN_CD"] = "00"  # 매수/매도 주문
                params["PRDT_TYPE_CD"] = self._RESV_PRDT_TYPE[exchange]

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/trading/order-resv",
                tr_id=(
                    ("TTTT3014U" if is_buy else "TTTT3016U") if is_us else "TTTS3013U"
                ),
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
        해외주식 예약주문 정정 — 지원하지 않음.

        .. deprecated:: 2.0.0
            KIS는 해외주식 예약주문 *정정* API를 제공하지 않는다. 이전 버전이
            호출하던 ``order-resv-rvsecncl``(TTTS6037U)은 공식 문서에 없는 경로이고,
            TTTS6037U는 미국 주간주문용 TR이다. ``cancel_reserve_order``로 취소한 뒤
            ``reserve_order``로 다시 등록하라. 다음 메이저 버전에서 제거된다.

        Raises:
            NotImplementedError: 항상
        """
        warnings.warn(
            "modify_reserve_order는 KIS에 대응 API가 없어 폐기되었습니다",
            DeprecationWarning,
            stacklevel=2,
        )
        raise NotImplementedError(
            "KIS는 해외주식 예약주문 정정 API를 제공하지 않습니다. "
            "cancel_reserve_order로 취소한 뒤 reserve_order로 다시 등록하세요."
        )

    def cancel_reserve_order(
        self,
        ovrs_rsvn_odno: str,
        rsvn_ord_rcit_dt: str,
        ovrs_excg_cd: str = "NASD",
        pdno: str = "",
        qty: int = 0,
        price: float = 0,
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 예약주문 취소 [v1_해외주식-004, v1_해외주식-002]

        - 미국: 예약주문접수취소 API (TTTT3017U)
        - 홍콩·중국·일본·베트남: 예약주문접수 API에 취소구분 "02"로 보낸다
          (TTTS3013U). KIS 문서상 원 주문의 종목·수량·단가가 필요하다.

        Args:
            ovrs_rsvn_odno (str): 해외예약주문번호 (예약주문 결과 ``odno`` /
                ``ovrs_rsvn_odno``, 예약주문조회 결과 참고)
            rsvn_ord_rcit_dt (str): 예약주문접수일자 (YYYYMMDD)
            ovrs_excg_cd (str): 거래소 코드 (기본 NASD)
            pdno (str): 종목코드 (아시아 필수)
            qty (int): 원 주문수량 (아시아 필수)
            price (float): 원 주문단가 (아시아 필수)

        Returns:
            Optional[Dict]: 취소 결과

        Raises:
            ValueError: 아시아 예약주문 취소에 종목코드·수량이 없는 경우

        Example:
            >>> agent.overseas.cancel_reserve_order("0030008244", "20260108")
        """
        try:
            account_params = self._get_account_params()
            exchange = self._normalize_exchange(ovrs_excg_cd)
            if exchange in self._US_EXCHANGES:
                return self._make_request_dict(
                    endpoint="/uapi/overseas-stock/v1/trading/order-resv-ccnl",
                    tr_id="TTTT3017U",
                    params={
                        **account_params,
                        "RSVN_ORD_RCIT_DT": rsvn_ord_rcit_dt,
                        "OVRS_RSVN_ODNO": ovrs_rsvn_odno,
                    },
                    method="POST",
                    use_cache=False,
                )
            if not pdno or qty <= 0:
                raise ValueError(
                    f"{exchange} 예약주문 취소에는 종목코드(pdno)와 원 주문수량(qty)이 필요합니다"
                )
            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/trading/order-resv",
                tr_id="TTTS3013U",
                params={
                    **account_params,
                    "PDNO": pdno.upper(),
                    "OVRS_EXCG_CD": exchange,
                    "FT_ORD_QTY": str(qty),
                    "FT_ORD_UNPR3": str(price),
                    "RVSE_CNCL_DVSN_CD": "02",  # 취소
                    "PRDT_TYPE_CD": self._RESV_PRDT_TYPE[exchange],
                    "RSVN_ORD_RCIT_DT": rsvn_ord_rcit_dt,
                    "OVRS_RSVN_ODNO": ovrs_rsvn_odno,
                    "ORD_SVR_DVSN_CD": "0",
                },
                method="POST",
                use_cache=False,
            )
        except Exception as e:
            logging.error(f"해외주식 예약주문 취소 실패: {e}")
            raise

    # ------------------------------------------------------------------
    # 미국 주간거래 (daytime) 주문. 지정가만 가능하고 모의투자는 지원하지 않는다.
    # ------------------------------------------------------------------

    def _daytime_exchange(self, ovrs_excg_cd: str) -> str:
        """주간거래 거래소를 검증한다. 미국(NASD/NYSE/AMEX)만 가능."""
        exchange = self._normalize_exchange(ovrs_excg_cd)
        if exchange not in self._US_EXCHANGES:
            raise ValueError(
                f"미국 주간거래는 미국 거래소(NASD/NYSE/AMEX)만 지원합니다: {ovrs_excg_cd}"
            )
        return exchange

    @staticmethod
    def _daytime_qty(qty: int) -> str:
        if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
            raise ValueError(f"qty는 1 이상의 정수여야 합니다: {qty!r}")
        return str(qty)

    @staticmethod
    def _daytime_price(price: float) -> str:
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise ValueError(f"price는 숫자여야 합니다: {price!r}")
        if price <= 0:
            raise ValueError(
                f"미국 주간거래는 지정가만 가능합니다. price는 0보다 커야 합니다: {price}"
            )
        return str(price)

    @staticmethod
    def _daytime_orgn_odno(orgn_odno: str) -> str:
        if not orgn_odno:
            raise ValueError("orgn_odno(원주문번호)는 필수입니다")
        return orgn_odno

    def daytime_buy_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        qty: int,
        price: float,
        ctac_tlno: str = "",
        mgco_aptm_odno: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 미국주간 매수주문 [v1_해외주식-026]

        미국 주간거래 시간에 지정가 매수 주문을 냅니다 (TR_ID TTTS6036U).
        주간거래는 지정가만 가능하며 모의투자는 지원하지 않습니다
        (``PaperTradingNotSupportedError``).

        Args:
            ovrs_excg_cd (str): 거래소 코드 (NASD/NYSE/AMEX 또는 NAS/NYS/AMS)
            pdno (str): 종목코드
            qty (int): 주문수량 (1 이상)
            price (float): 주문단가 (0보다 커야 함, 지정가)
            ctac_tlno (str): 연락전화번호 (선택)
            mgco_aptm_odno (str): 운용사지정주문번호 (선택)

        Returns:
            Optional[Dict]: 주문 결과
                - output.KRX_FWDG_ORD_ORGNO: 한국거래소전송주문조직번호
                - output.ODNO: 주문번호
                - output.ORD_TMD: 주문시각

        Raises:
            ValueError: 미국 외 거래소, 수량/단가 오류. 요청은 전송되지 않는다.

        Example:
            >>> agent.overseas.daytime_buy_order("NASD", "AAPL", 10, 185.00)
        """
        account_params = self._get_account_params()
        exchange = self._daytime_exchange(ovrs_excg_cd)
        order_qty = self._daytime_qty(qty)
        order_price = self._daytime_price(price)

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/daytime-order",
            tr_id="TTTS6036U",
            params={
                **account_params,
                "OVRS_EXCG_CD": exchange,
                "PDNO": pdno.upper(),
                "ORD_QTY": order_qty,
                "OVRS_ORD_UNPR": order_price,
                "CTAC_TLNO": ctac_tlno,
                "MGCO_APTM_ODNO": mgco_aptm_odno,
                "ORD_SVR_DVSN_CD": "0",
                "ORD_DVSN": "00",
            },
            method="POST",
            use_cache=False,
        )

    def daytime_sell_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        qty: int,
        price: float,
        ctac_tlno: str = "",
        mgco_aptm_odno: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 미국주간 매도주문 [v1_해외주식-026]

        미국 주간거래 시간에 지정가 매도 주문을 냅니다 (TR_ID TTTS6037U).
        주간거래는 지정가만 가능하며 모의투자는 지원하지 않습니다
        (``PaperTradingNotSupportedError``).

        Args:
            ovrs_excg_cd (str): 거래소 코드 (NASD/NYSE/AMEX 또는 NAS/NYS/AMS)
            pdno (str): 종목코드
            qty (int): 주문수량 (1 이상)
            price (float): 주문단가 (0보다 커야 함, 지정가)
            ctac_tlno (str): 연락전화번호 (선택)
            mgco_aptm_odno (str): 운용사지정주문번호 (선택)

        Returns:
            Optional[Dict]: 주문 결과 (output.ODNO, output.ORD_TMD 등)

        Raises:
            ValueError: 미국 외 거래소, 수량/단가 오류. 요청은 전송되지 않는다.

        Example:
            >>> agent.overseas.daytime_sell_order("NASD", "AAPL", 5, 190.00)
        """
        account_params = self._get_account_params()
        exchange = self._daytime_exchange(ovrs_excg_cd)
        order_qty = self._daytime_qty(qty)
        order_price = self._daytime_price(price)

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/daytime-order",
            tr_id="TTTS6037U",
            params={
                **account_params,
                "OVRS_EXCG_CD": exchange,
                "PDNO": pdno.upper(),
                "ORD_QTY": order_qty,
                "OVRS_ORD_UNPR": order_price,
                "CTAC_TLNO": ctac_tlno,
                "MGCO_APTM_ODNO": mgco_aptm_odno,
                "ORD_SVR_DVSN_CD": "0",
                "ORD_DVSN": "00",
            },
            method="POST",
            use_cache=False,
        )

    def daytime_modify_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        orgn_odno: str,
        qty: int,
        price: float,
        ctac_tlno: str = "",
        mgco_aptm_odno: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 미국주간 정정주문 [v1_해외주식-027]

        미국 주간거래 미체결 주문의 수량·가격을 정정합니다 (TR_ID TTTS6038U,
        RVSE_CNCL_DVSN_CD 01). 모의투자는 지원하지 않습니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드 (미국만)
            pdno (str): 종목코드
            orgn_odno (str): 원주문번호 (정정할 주문번호)
            qty (int): 정정 후 주문수량 (1 이상)
            price (float): 정정 후 주문단가 (0보다 커야 함)
            ctac_tlno (str): 연락전화번호 (선택)
            mgco_aptm_odno (str): 운용사지정주문번호 (선택)

        Returns:
            Optional[Dict]: 정정 결과 (output.ODNO, output.ORD_TMD 등)

        Raises:
            ValueError: 미국 외 거래소, 원주문번호/수량/단가 오류. 요청은 전송되지 않는다.

        Example:
            >>> agent.overseas.daytime_modify_order("NASD", "AAPL", "0001234", 10, 190.00)
        """
        account_params = self._get_account_params()
        exchange = self._daytime_exchange(ovrs_excg_cd)
        original = self._daytime_orgn_odno(orgn_odno)
        order_qty = self._daytime_qty(qty)
        order_price = self._daytime_price(price)

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/daytime-order-rvsecncl",
            tr_id="TTTS6038U",
            params={
                **account_params,
                "OVRS_EXCG_CD": exchange,
                "PDNO": pdno.upper(),
                "ORGN_ODNO": original,
                "RVSE_CNCL_DVSN_CD": "01",
                "ORD_QTY": order_qty,
                "OVRS_ORD_UNPR": order_price,
                "CTAC_TLNO": ctac_tlno,
                "MGCO_APTM_ODNO": mgco_aptm_odno,
                "ORD_SVR_DVSN_CD": "0",
            },
            method="POST",
            use_cache=False,
        )

    def daytime_cancel_order(
        self,
        ovrs_excg_cd: str,
        pdno: str,
        orgn_odno: str,
        qty: int,
        ctac_tlno: str = "",
        mgco_aptm_odno: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 미국주간 취소주문 [v1_해외주식-027]

        미국 주간거래 미체결 주문을 취소합니다 (TR_ID TTTS6038U,
        RVSE_CNCL_DVSN_CD 02, 단가 "0"). 모의투자는 지원하지 않습니다.

        Args:
            ovrs_excg_cd (str): 거래소 코드 (미국만)
            pdno (str): 종목코드
            orgn_odno (str): 원주문번호 (취소할 주문번호)
            qty (int): 취소수량 (1 이상)
            ctac_tlno (str): 연락전화번호 (선택)
            mgco_aptm_odno (str): 운용사지정주문번호 (선택)

        Returns:
            Optional[Dict]: 취소 결과 (output.ODNO, output.ORD_TMD 등)

        Raises:
            ValueError: 미국 외 거래소, 원주문번호/수량 오류. 요청은 전송되지 않는다.

        Example:
            >>> agent.overseas.daytime_cancel_order("NASD", "AAPL", "0001234", 10)
        """
        account_params = self._get_account_params()
        exchange = self._daytime_exchange(ovrs_excg_cd)
        original = self._daytime_orgn_odno(orgn_odno)
        order_qty = self._daytime_qty(qty)

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/trading/daytime-order-rvsecncl",
            tr_id="TTTS6038U",
            params={
                **account_params,
                "OVRS_EXCG_CD": exchange,
                "PDNO": pdno.upper(),
                "ORGN_ODNO": original,
                "RVSE_CNCL_DVSN_CD": "02",
                "ORD_QTY": order_qty,
                "OVRS_ORD_UNPR": "0",
                "CTAC_TLNO": ctac_tlno,
                "MGCO_APTM_ODNO": mgco_aptm_odno,
                "ORD_SVR_DVSN_CD": "0",
            },
            method="POST",
            use_cache=False,
        )
