"""계좌 주문 API 모듈.

현금/신용 주문, 정정/취소, 예약주문 등 주문 실행 기능 제공.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient


class AccountOrderAPI(BaseAPI):
    """계좌 주문 실행 API."""

    def __init__(
        self,
        client: KISClient,
        account_info: Dict[str, str],
        enable_cache=True,
        cache_config=None,
        _from_agent=False,
    ):
        """초기화. account_info에 CANO/ACNT_PRDT_CD 필요."""
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

    def order_cash(
        self,
        pdno: str,
        qty: int,
        price: int,
        buy_sell: str,
        order_type: str = "00",
        exchange: str = "KRX",
    ) -> Optional[Dict[str, Any]]:
        """주식주문(현금) - 현금으로 주식을 매수 또는 매도.

        Args:
            pdno: 종목코드 6자리
            qty: 주문수량
            price: 주문단가 (시장가는 0)
            buy_sell: "BUY" 또는 "SELL"
            order_type: "00"=지정가, "01"=시장가, "02"=조건부지정가, "03"=최유리지정가
            exchange: "KRX", "NXT", "SOR"
        """
        try:
            tr_id = "TTTC0011U" if buy_sell.upper() == "SELL" else "TTTC0012U"
            params = {
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "PDNO": pdno,
                "ORD_DVSN": order_type,
                "ORD_QTY": str(qty),
                "ORD_UNPR": str(price),
            }
            if exchange != "KRX":
                params["EXCG_ID_DVSN_CD"] = exchange

            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-cash",
                tr_id=tr_id,
                params=params,
                method="POST",
            )
        except Exception as e:
            logging.error(f"현금 주문 실패: {e}")
            return None

    def order_cash_sor(
        self, pdno: str, qty: int, buy_sell: str, order_type: str = "03"
    ) -> Optional[Dict[str, Any]]:
        """SOR 최유리지정가 주문 - Smart Order Routing으로 최적 가격에 주문."""
        return self.order_cash(
            pdno=pdno,
            qty=qty,
            price=0,
            buy_sell=buy_sell,
            order_type=order_type,
            exchange="SOR",
        )

    def order_credit(
        self, code: str, qty: int, price: int, order_type: str
    ) -> Optional[Dict]:
        """신용주문 실행. output.odno 반환."""
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-credit",
                tr_id="TTTC0052U",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": code,
                    "CRDT_TYPE": "21",
                    "LOAN_DT": "",
                    "ORD_DVSN": order_type,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                },
                method="POST",
            )
        except Exception as e:
            logging.error(f"신용 주문 실패: {e}")
            return None

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
        """주식주문(신용매수) - 신용으로 주식을 매수.

        Args:
            pdno: 종목코드 6자리
            qty: 주문수량
            price: 주문단가 (시장가는 0)
            order_type: "00"=지정가, "01"=시장가
            credit_type: "21"=신용융자, "22"=자기융자, "23"=유통융자
            exchange: "KRX" 또는 "SOR"
            loan_dt: 대출일자 (자기융자 시 자동설정)
        """
        try:
            if credit_type == "22" and not loan_dt:
                loan_dt = datetime.now().strftime("%Y%m%d")

            params = {
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "PDNO": pdno,
                "ORD_DVSN": order_type,
                "ORD_QTY": str(qty),
                "ORD_UNPR": str(price),
                "CRDT_TYPE": credit_type,
                "LOAN_DT": loan_dt,
            }
            if exchange != "KRX":
                params["EXCG_ID_DVSN_CD"] = exchange

            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-credit",
                tr_id="TTTC0052U",
                params=params,
                method="POST",
            )
        except Exception as e:
            logging.error(f"신용매수 주문 실패: {e}")
            return None

    def order_credit_sell(
        self,
        pdno: str,
        qty: int,
        price: int,
        order_type: str = "00",
        credit_type: str = "11",
    ) -> Optional[Dict[str, Any]]:
        """주식주문(신용매도) - 신용으로 매수한 주식을 매도.

        Args:
            credit_type: "11"=융자상환매도, "12"=자기상환매도, "61"=대주상환매도
        """
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-credit",
                tr_id="TTTC0051U",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": pdno,
                    "ORD_DVSN": order_type,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "CRDT_TYPE": credit_type,
                    "LOAN_DT": "",
                },
                method="POST",
            )
        except Exception as e:
            logging.error(f"신용매도 주문 실패: {e}")
            return None

    def order_rvsecncl(
        self, org_order_no: str, qty: int, price: int, order_type: str, cncl_type: str
    ) -> Optional[Dict]:
        """주문 정정/취소. cncl_type='정정' 또는 '취소'."""
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-rvsecncl",
                tr_id="TTTC0013U",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "KRX_FWDG_ORD_ORGNO": "",
                    "ORGN_ODNO": org_order_no,
                    "ORD_DVSN": order_type,
                    "RVSE_CNCL_DVSN_CD": cncl_type,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "QTY_ALL_ORD_YN": "Y",
                },
                method="POST",
            )
        except Exception as e:
            logging.error(f"정정/취소 주문 실패: {e}")
            return None

    def inquire_psbl_rvsecncl(self) -> Optional[Dict]:
        """정정/취소 가능한 미체결 주문 목록 조회."""
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl",
                tr_id="TTTC0084R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "CTX_AREA_FK100": "",
                    "CTX_AREA_NK100": "",
                    "INQR_DVSN_1": "1",
                    "INQR_DVSN_2": "0",
                },
            )
        except Exception as e:
            logging.error(f"정정/취소 가능 주문 조회 실패: {e}")
            return None

    def order_resv(
        self, code: str, qty: int, price: int, order_type: str
    ) -> Optional[Dict]:
        """예약주문 등록. 지정 시점에 주문 실행."""
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-resv",
                tr_id="CTSC0008U",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": code,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "SLL_BUY_DVSN_CD": "02",
                    "ORD_DVSN_CD": order_type,
                    "ORD_OBJT_CBLC_DVSN_CD": "10",
                },
                method="POST",
            )
        except Exception as e:
            logging.error(f"예약 주문 실패: {e}")
            return None

    def order_resv_rvsecncl(
        self,
        seq: int,
        qty: int = 0,
        price: int = 0,
        order_type: str = "00",
        action: str = "modify",
        pdno: str = "",
        sll_buy_dvsn_cd: str = "",
        rsvn_ord_orgno: str = "",
        rsvn_ord_ord_dt: str = "",
        ord_objt_cblc_dvsn_cd: str = "10",
        rsvn_ord_end_dt: str = "",
    ) -> Optional[Dict]:
        """주식예약주문정정취소 [국내주식-018]

        ``action``으로 정정(CTSC0013U)과 취소(CTSC0009U)를 고른다. 이전 버전은
        항상 정정 TR을 보내 취소가 불가능했고, 매수 구분("02")을 하드코딩해
        매도 예약을 정정하면 매수로 바뀌었다.

        Args:
            seq: 예약주문순번 (예약주문조회 ``rsvn_ord_seq``)
            qty: 정정 주문수량 (정정 시)
            price: 정정 주문단가 (정정 시)
            order_type: 주문구분코드 (00 지정가, 01 시장가 ...; 정정 시)
            action: "modify"(정정) 또는 "cancel"(취소)
            pdno: 종목코드 (정정 시 필수)
            sll_buy_dvsn_cd: "01" 매도 / "02" 매수 (정정 시 필수)
            rsvn_ord_orgno: 예약주문조직번호 (예약주문조회 결과, 있으면 전송)
            rsvn_ord_ord_dt: 예약주문주문일자 YYYYMMDD (예약주문조회 결과, 있으면 전송)
            ord_objt_cblc_dvsn_cd: 주문대상잔고구분코드 (기본 "10" 현금)
            rsvn_ord_end_dt: 예약주문종료일자 (기간예약주문 정정 시)

        Returns:
            응답 Dict, 실패 시 None

        Raises:
            ValueError: action이 잘못됐거나, 정정에 종목·매매구분이 없는 경우
        """
        if action not in ("modify", "cancel"):
            raise ValueError(
                f"action은 'modify' 또는 'cancel'이어야 합니다: {action!r}"
            )
        is_modify = action == "modify"
        if is_modify and (not pdno or sll_buy_dvsn_cd not in ("01", "02")):
            raise ValueError(
                "예약주문 정정에는 pdno와 sll_buy_dvsn_cd('01' 매도/'02' 매수)가 필요합니다"
            )
        params = {
            "CANO": self.account["CANO"],
            "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
            "RSVN_ORD_SEQ": str(seq),
        }
        if rsvn_ord_orgno:
            params["RSVN_ORD_ORGNO"] = rsvn_ord_orgno
        if rsvn_ord_ord_dt:
            params["RSVN_ORD_ORD_DT"] = rsvn_ord_ord_dt
        if is_modify:
            params["PDNO"] = pdno
            params["ORD_QTY"] = str(qty)
            params["ORD_UNPR"] = str(price)
            params["SLL_BUY_DVSN_CD"] = sll_buy_dvsn_cd
            params["ORD_DVSN_CD"] = order_type
            params["ORD_OBJT_CBLC_DVSN_CD"] = ord_objt_cblc_dvsn_cd
        if is_modify and rsvn_ord_end_dt:
            params["RSVN_ORD_END_DT"] = rsvn_ord_end_dt
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-resv-rvsecncl",
                tr_id="CTSC0013U" if is_modify else "CTSC0009U",
                params=params,
                method="POST",
                use_cache=False,
            )
        except Exception as e:
            logging.error(f"예약 주문 정정/취소 실패: {e}")
            return None

    def order_resv_ccnl(self) -> Optional[Dict]:
        """등록된 예약주문 내역 조회."""
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-resv-ccnl",
                tr_id="CTSC0004R",
                params={
                    "RSVN_ORD_ORD_DT": "",
                    "RSVN_ORD_END_DT": "",
                    "RSVN_ORD_SEQ": "",
                    "TMNL_MDIA_KIND_CD": "00",
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PRCS_DVSN_CD": "0",
                    "CNCL_YN": "Y",
                    "PDNO": "",
                    "SLL_BUY_DVSN_CD": "",
                    "CTX_AREA_FK200": "",
                    "CTX_AREA_NK200": "",
                },
            )
        except Exception as e:
            logging.error(f"예약 주문 조회 실패: {e}")
            return None
