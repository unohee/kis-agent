"""
Futures Order API - 선물옵션 주문/체결 조회 전용 모듈

단일 책임 원칙(SRP)에 따라 주문 관련 기능만 분리
- 체결 내역 조회
- 주문 가능 수량 조회
- 주문 실행
- 주문 정정/취소
"""

from typing import Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS


class FuturesOrderAPI(BaseAPI):
    """선물옵션 주문/체결 조회 전용 API 클래스 (6개 메서드)"""

    def inquire_ccnl(
        self, inqr_strt_dt: str = "", inqr_end_dt: str = ""
    ) -> Optional[Dict]:
        """
        선물옵션 체결 내역 조회

        Args:
            inqr_strt_dt: 조회 시작일자 (YYYYMMDD, 공백 시 당일)
            inqr_end_dt: 조회 종료일자 (YYYYMMDD, 공백 시 당일)

        Returns:
            FuturesConclusionResponse: 체결 내역 리스트
                - output[].ord_dt: 주문일자
                - output[].odno: 주문번호
                - output[].fuop_item_code: 선물옵션종목코드
                - output[].sll_buy_dvsn_cd: 매도매수구분 (1:매도, 2:매수)
                - output[].ord_qty: 주문수량
                - output[].ccld_qty: 체결수량
                - output[].ccld_unpr: 체결단가
                - output[].ccld_amt: 체결금액

        Example:
            >>> ccnl = agent.futures.order.inquire_ccnl("20260119", "20260119")
            >>> for item in ccnl['output']:
            ...     print(f"{item['fuop_item_code']}: {item['ccld_qty']}계약")

        Note:
            TR_ID는 실전/모의 환경에 따라 자동 선택
            - 실전: TTTO5201R
            - 모의: VTTO5201R
        """
        tr_id = "VTTO5201R" if self._is_virtual() else "TTTO5201R"

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_CCNL"],
            tr_id=tr_id,
            params={
                "ACNT_NO": self._get_account_no(),
                "ACNT_PDNO": self._get_account_code(),
                "INQR_STRT_DT": inqr_strt_dt,
                "INQR_END_DT": inqr_end_dt,
                "SLL_BUY_DVSN_CD": "00",  # 매도매수구분 (00:전체, 01:매도, 02:매수)
                "FUOP_ITEM_DVSN_CD": "00",  # 선물옵션종목구분 (00:전체, F:선물, O:옵션)
                "CCLD_NCCS_DVSN_CD": "00",  # 체결미체결구분 (00:전체, 01:체결, 02:미체결)
                "CTX_AREA_FK200": "",  # 연속조회검색조건
                "CTX_AREA_NK200": "",  # 연속조회키
            },
        )

    def inquire_ngt_ccnl(
        self, inqr_strt_dt: str = "", inqr_end_dt: str = ""
    ) -> Optional[Dict]:
        """
        야간 선물옵션 체결 내역 조회

        Args:
            inqr_strt_dt: 조회 시작일자 (YYYYMMDD)
            inqr_end_dt: 조회 종료일자 (YYYYMMDD)

        Returns:
            야간 거래 체결 내역 리스트
                - output[]: 체결 내역

        Example:
            >>> ngt_ccnl = agent.futures.order.inquire_ngt_ccnl()
            >>> print(f"야간 체결: {len(ngt_ccnl['output'])}건")

        Note:
            야간 거래 시간대 (18:00 ~ 익일 05:00) 체결 내역
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_NGT_CCNL"],
            tr_id="STTN5201R",
            params={
                "ACNT_NO": self._get_account_no(),
                "ACNT_PDNO": self._get_account_code(),
                "INQR_STRT_DT": inqr_strt_dt,
                "INQR_END_DT": inqr_end_dt,
                "SLL_BUY_DVSN_CD": "00",
                "FUOP_ITEM_DVSN_CD": "00",
                "CCLD_NCCS_DVSN_CD": "00",
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": "",
            },
        )

    def inquire_psbl_order(self, code: str) -> Optional[Dict]:
        """
        선물옵션 주문 가능 수량 조회

        Args:
            code: 선물옵션 종목코드

        Returns:
            주문 가능 수량 정보
                - output.ord_psbl_qty: 주문가능수량
                - output.max_ord_psbl_qty: 최대주문가능수량
                - output.ord_mrgn_amt: 주문증거금액
                - output.maint_mrgn_amt: 유지증거금액

        Example:
            >>> psbl = agent.futures.order.inquire_psbl_order("101S12")
            >>> print(f"주문가능: {psbl['output']['ord_psbl_qty']}계약")
            >>> print(f"필요증거금: {psbl['output']['ord_mrgn_amt']}원")

        Note:
            TR_ID는 실전/모의 환경에 따라 자동 선택
            - 실전: TTTO5105R
            - 모의: VTTO5105R
        """
        tr_id = "VTTO5105R" if self._is_virtual() else "TTTO5105R"

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_PSBL_ORDER"],
            tr_id=tr_id,
            params={
                "ACNT_NO": self._get_account_no(),
                "ACNT_PDNO": self._get_account_code(),
                "FUOP_ITEM_CODE": code,
                "SLL_BUY_DVSN_CD": "02",  # 매도매수구분 (01:매도, 02:매수)
                "ORD_UNPR": "0",  # 주문단가 (시장가 시 0)
                "ORD_QTY": "1",  # 주문수량 (조회용 기본값)
            },
        )

    def inquire_psbl_ngt_order(self, code: str) -> Optional[Dict]:
        """
        야간 선물옵션 주문 가능 수량 조회

        Args:
            code: 선물옵션 종목코드

        Returns:
            야간 거래 주문 가능 수량 정보

        Example:
            >>> psbl = agent.futures.order.inquire_psbl_ngt_order("101S12")
            >>> print(f"야간 주문가능: {psbl['output']['ord_psbl_qty']}계약")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_PSBL_NGT_ORDER"],
            tr_id="STTN5105R",
            params={
                "ACNT_NO": self._get_account_no(),
                "ACNT_PDNO": self._get_account_code(),
                "FUOP_ITEM_CODE": code,
                "SLL_BUY_DVSN_CD": "02",
                "ORD_UNPR": "0",
                "ORD_QTY": "1",
            },
        )

    def order(
        self,
        code: str,
        order_type: str,
        qty: str,
        price: str = "0",
        order_cond: str = "0",
    ) -> Optional[Dict]:
        """
        선물옵션 주문 (매수/매도)

        Args:
            code: 선물옵션 종목코드 (예: '101S12' KOSPI200 선물)
            order_type: 주문 구분
                - '01': 매도
                - '02': 매수
            qty: 주문 수량 (계약 수)
            price: 주문 단가 (0: 시장가, 그 외: 지정가)
            order_cond: 주문 조건
                - '0': 없음 (일반)
                - '1': IOC (Immediate or Cancel)
                - '2': FOK (Fill or Kill)

        Returns:
            FuturesOrderResponse: 주문 응답
                - output.odno: 주문번호
                - output.ord_tmd: 주문시각

        Example:
            >>> # 시장가 매수
            >>> result = agent.futures.order.order(
            ...     code="101S12",
            ...     order_type="02",  # 매수
            ...     qty="1",
            ...     price="0"  # 시장가
            ... )
            >>> print(f"주문번호: {result['output']['odno']}")
            >>>
            >>> # 지정가 매도
            >>> result = agent.futures.order.order(
            ...     code="101S12",
            ...     order_type="01",  # 매도
            ...     qty="1",
            ...     price="340.50"  # 지정가
            ... )

        Note:
            TR_ID는 실전/모의 환경 및 매도/매수에 따라 자동 선택
            - 실전 매수: TTTO1101U
            - 실전 매도: TTTO1102U
            - 야간 매수: STTN1101U (야간 거래 시)
            - 야간 매도: STTN1102U (야간 거래 시)

        Warning:
            실전 주문 시 반드시 주의하여 사용하세요.
            주문 전 inquire_psbl_order()로 주문 가능 수량을 확인하세요.
        """
        # TR_ID 선택 (매수/매도 구분)
        if order_type == "01":  # 매도
            tr_id = "TTTO1102U"
        elif order_type == "02":  # 매수
            tr_id = "TTTO1101U"
        else:
            raise ValueError(f"Invalid order_type: {order_type} (01:매도, 02:매수)")

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_ORDER"],
            tr_id=tr_id,
            params={
                "ACNT_NO": self._get_account_no(),
                "ACNT_PDNO": self._get_account_code(),
                "FUOP_ITEM_CODE": code,
                "SLL_BUY_DVSN_CD": order_type,
                "ORD_QTY": qty,
                "ORD_UNPR": price,
                "ORD_DVSN_CD": "01" if price == "0" else "00",  # 01:시장가, 00:지정가
                "ORD_CNDI_DVSN_CD": order_cond,
            },
        )

    def order_rvsecncl(
        self,
        orgn_odno: str,
        qty: str,
        action: str = "02",
        price: str = "0",
    ) -> Optional[Dict]:
        """
        선물옵션 주문 정정/취소

        Args:
            orgn_odno: 원주문번호 (정정/취소할 주문번호)
            qty: 정정/취소 수량
            action: 정정/취소 구분
                - '01': 정정
                - '02': 취소
            price: 정정 시 변경할 단가 (취소 시 무시)

        Returns:
            정정/취소 응답
                - output.odno: 주문번호
                - output.ord_tmd: 주문시각

        Example:
            >>> # 주문 취소
            >>> result = agent.futures.order.order_rvsecncl(
            ...     orgn_odno="0000123456",
            ...     qty="1",
            ...     action="02"  # 취소
            ... )
            >>>
            >>> # 주문 정정 (가격 변경)
            >>> result = agent.futures.order.order_rvsecncl(
            ...     orgn_odno="0000123456",
            ...     qty="1",
            ...     action="01",  # 정정
            ...     price="341.00"  # 변경할 가격
            ... )

        Note:
            TR_ID는 정정/취소 구분에 따라 자동 선택
            - 정정: TTTO1103U
            - 취소: TTTO1104U
        """
        # TR_ID 선택 (정정/취소 구분)
        if action == "01":  # 정정
            tr_id = "TTTO1103U"
        elif action == "02":  # 취소
            tr_id = "TTTO1104U"
        else:
            raise ValueError(f"Invalid action: {action} (01:정정, 02:취소)")

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_ORDER_RVSECNCL"],
            tr_id=tr_id,
            params={
                "ACNT_NO": self._get_account_no(),
                "ACNT_PDNO": self._get_account_code(),
                "ORGN_ODNO": orgn_odno,
                "ORD_QTY": qty,
                "ORD_UNPR": price if action == "01" else "0",  # 정정 시에만 가격 사용
                "ORD_DVSN_CD": "01" if price == "0" else "00",
            },
        )

    # Helper methods (private)
    def _get_account_no(self) -> str:
        """계좌번호 추출"""
        if self.account and "account_no" in self.account:
            return self.account["account_no"]
        return ""

    def _get_account_code(self) -> str:
        """계좌 상품코드 추출 (선물옵션: '03')"""
        if self.account and "account_code" in self.account:
            return self.account["account_code"]
        return "03"

    def _is_virtual(self) -> bool:
        """모의투자 여부 확인"""
        if hasattr(self.client, "base_url"):
            return "vts" in self.client.base_url.lower()
        return False
