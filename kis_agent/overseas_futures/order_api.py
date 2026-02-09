"""
Overseas Futures Order API - 해외선물옵션 주문 전용 모듈

단일 책임 원칙(SRP)에 따라 주문 관련 기능만 분리
- 신규 주문
- 정정/취소 주문
"""

from typing import Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS


class OverseasFuturesOrderAPI(BaseAPI):
    """해외선물옵션 주문 전용 API 클래스 (2개 메서드)"""

    def order(
        self,
        ovrs_futr_fx_pdno: str,
        sll_buy_dvsn_cd: str,
        fm_ord_qty: str,
        pric_dvsn_cd: str,
        fm_limit_ord_pric: str = "",
        fm_stop_ord_pric: str = "",
        ccld_cndt_cd: str = "6",
    ) -> Optional[Dict]:
        """
        해외선물옵션 주문

        Args:
            ovrs_futr_fx_pdno: 해외선물FX상품번호 (종목코드)
            sll_buy_dvsn_cd: 매도매수구분코드 (01:매도, 02:매수)
            fm_ord_qty: FM주문수량
            pric_dvsn_cd: 가격구분코드
                - 1: 지정가
                - 2: 시장가
                - 3: STOP
                - 4: S/L (Stop Loss)
            fm_limit_ord_pric: FM지정가주문가격
                - 지정가(1), S/L(4)인 경우 입력
                - 시장가(2), STOP(3)인 경우 공백
            fm_stop_ord_pric: FM스탑주문가격
                - STOP(3), S/L(4)인 경우 입력
                - 지정가(1), 시장가(2)인 경우 공백
            ccld_cndt_cd: 체결조건코드
                - 2: IOC (시장가만 사용)
                - 5: GTD
                - 6: EOD (기본값, 지정가)

        Returns:
            OverseasFuturesOrderResponse: 주문 결과
                - output.odno: 주문번호
                - output.ord_dt: 주문일자
                - output.ord_tmd: 주문시각

        Example:
            >>> # 지정가 매수 주문
            >>> result = agent.overseas_futures.order(
            ...     ovrs_futr_fx_pdno="CNHU24",
            ...     sll_buy_dvsn_cd="02",  # 매수
            ...     fm_ord_qty="1",
            ...     pric_dvsn_cd="1",  # 지정가
            ...     fm_limit_ord_pric="100.00"
            ... )
            >>> print(f"주문번호: {result['output']['odno']}")

            >>> # 시장가 매도 주문
            >>> result = agent.overseas_futures.order(
            ...     ovrs_futr_fx_pdno="CNHU24",
            ...     sll_buy_dvsn_cd="01",  # 매도
            ...     fm_ord_qty="1",
            ...     pric_dvsn_cd="2",  # 시장가
            ...     ccld_cndt_cd="2"  # IOC
            ... )

            >>> # STOP 주문
            >>> result = agent.overseas_futures.order(
            ...     ovrs_futr_fx_pdno="CNHU24",
            ...     sll_buy_dvsn_cd="02",  # 매수
            ...     fm_ord_qty="1",
            ...     pric_dvsn_cd="3",  # STOP
            ...     fm_stop_ord_pric="105.00"
            ... )

        Note:
            - 주문 전 get_order_amount()로 주문가능수량 확인 권장
            - STOP 주문은 지정한 가격에 도달 시 시장가 주문으로 전환
            - S/L 주문은 STOP 가격 도달 시 지정가 주문으로 전환
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_ORDER"],
            tr_id="OTFM3001U",  # 해외선물옵션 주문
            params={
                "CANO": self.account["account_no"],
                "ACNT_PRDT_CD": self.account["account_code"],
                "OVRS_FUTR_FX_PDNO": ovrs_futr_fx_pdno,
                "SLL_BUY_DVSN_CD": sll_buy_dvsn_cd,
                "FM_LQD_USTL_CCLD_DT": "",  # hedge청산만 사용
                "FM_LQD_USTL_CCNO": "",  # hedge청산만 사용
                "PRIC_DVSN_CD": pric_dvsn_cd,
                "FM_LIMIT_ORD_PRIC": fm_limit_ord_pric,
                "FM_STOP_ORD_PRIC": fm_stop_ord_pric,
                "FM_ORD_QTY": fm_ord_qty,
                "FM_LQD_LMT_ORD_PRIC": "",  # hedge청산만 사용
                "FM_LQD_STOP_ORD_PRIC": "",  # hedge청산만 사용
                "CCLD_CNDT_CD": ccld_cndt_cd,
                "CPLX_ORD_DVSN_CD": "0",  # hedge청산만 사용
                "ECIS_RSVN_ORD_YN": "N",
                "FM_HDGE_ORD_SCRN_YN": "N",
            },
            use_cache=False,
            method="POST",
        )

    def modify_cancel(
        self,
        ord_dv: str,
        orgn_ord_dt: str,
        orgn_odno: str,
        fm_limit_ord_pric: str = "",
        fm_stop_ord_pric: str = "",
        fm_lqd_lmt_ord_pric: str = "",
        fm_lqd_stop_ord_pric: str = "",
        fm_mkpr_cvsn_yn: str = "N",
    ) -> Optional[Dict]:
        """
        해외선물옵션 정정/취소 주문

        Args:
            ord_dv: 주문구분 (0:정정, 1:취소)
            orgn_ord_dt: 원주문일자 (주문 응답의 ORD_DT 값)
            orgn_odno: 원주문번호 (8자리, 예: "00360686")
            fm_limit_ord_pric: FM지정가주문가격 (정정 시 사용)
            fm_stop_ord_pric: FM스탑주문가격 (정정 시 사용)
            fm_lqd_lmt_ord_pric: FM청산지정가주문가격 (정정 시 사용)
            fm_lqd_stop_ord_pric: FM청산스탑주문가격 (정정 시 사용)
            fm_mkpr_cvsn_yn: FM시장가전환여부 (취소 시만 사용)
                - N: 일반 취소
                - Y: 취소 확인 후 시장가 주문 자동 발송

        Returns:
            OverseasFuturesModifyCancelResponse: 정정/취소 결과
                - output.odno: 주문번호
                - output.orgn_odno: 원주문번호
                - output.ord_dt: 주문일자

        Example:
            >>> # 주문 정정 (가격 변경)
            >>> result = agent.overseas_futures.modify_cancel(
            ...     ord_dv="0",  # 정정
            ...     orgn_ord_dt="20260123",
            ...     orgn_odno="00360686",
            ...     fm_limit_ord_pric="101.00"
            ... )
            >>> print(f"정정 주문번호: {result['output']['odno']}")

            >>> # 주문 취소
            >>> result = agent.overseas_futures.modify_cancel(
            ...     ord_dv="1",  # 취소
            ...     orgn_ord_dt="20260123",
            ...     orgn_odno="00360686"
            ... )
            >>> print(f"취소 완료: {result['output']['odno']}")

        Note:
            - orgn_odno는 8자리 문자열로 "0" 포함하여 전송
            - 정정 시 fm_limit_ord_pric 또는 fm_stop_ord_pric 중 해당 값 입력
            - 취소 시 fm_mkpr_cvsn_yn="Y"로 설정하면 취소 후 시장가 주문 자동 발송
        """
        # 정정(0)과 취소(1)에 따라 TR_ID 결정
        tr_id = "OTFM3002U" if ord_dv == "0" else "OTFM3003U"

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_ORDER_RVSECNCL"],
            tr_id=tr_id,
            params={
                "CANO": self.account["account_no"],
                "ORD_DV": ord_dv,
                "ACNT_PRDT_CD": self.account["account_code"],
                "ORGN_ORD_DT": orgn_ord_dt,
                "ORGN_ODNO": orgn_odno,
                "FM_LIMIT_ORD_PRIC": fm_limit_ord_pric,
                "FM_STOP_ORD_PRIC": fm_stop_ord_pric,
                "FM_LQD_LMT_ORD_PRIC": fm_lqd_lmt_ord_pric,
                "FM_LQD_STOP_ORD_PRIC": fm_lqd_stop_ord_pric,
                "FM_HDGE_ORD_SCRN_YN": "N",
                "FM_MKPR_CVSN_YN": fm_mkpr_cvsn_yn,
            },
            use_cache=False,
            method="POST",
        )

    # 편의 메서드들

    def buy(
        self,
        code: str,
        qty: str,
        price: str = "",
        order_type: str = "1",
    ) -> Optional[Dict]:
        """
        해외선물옵션 매수 주문 (편의 메서드)

        Args:
            code: 종목코드
            qty: 주문수량
            price: 주문가격 (시장가인 경우 공백)
            order_type: 주문유형 (1:지정가, 2:시장가)

        Returns:
            주문 결과

        Example:
            >>> # 지정가 매수
            >>> result = agent.overseas_futures.order.buy(
            ...     code="CNHU24",
            ...     qty="1",
            ...     price="100.00"
            ... )

            >>> # 시장가 매수
            >>> result = agent.overseas_futures.order.buy(
            ...     code="CNHU24",
            ...     qty="1",
            ...     order_type="2"
            ... )
        """
        ccld_cndt_cd = "2" if order_type == "2" else "6"
        return self.order(
            ovrs_futr_fx_pdno=code,
            sll_buy_dvsn_cd="02",  # 매수
            fm_ord_qty=qty,
            pric_dvsn_cd=order_type,
            fm_limit_ord_pric=price if order_type == "1" else "",
            ccld_cndt_cd=ccld_cndt_cd,
        )

    def sell(
        self,
        code: str,
        qty: str,
        price: str = "",
        order_type: str = "1",
    ) -> Optional[Dict]:
        """
        해외선물옵션 매도 주문 (편의 메서드)

        Args:
            code: 종목코드
            qty: 주문수량
            price: 주문가격 (시장가인 경우 공백)
            order_type: 주문유형 (1:지정가, 2:시장가)

        Returns:
            주문 결과

        Example:
            >>> result = agent.overseas_futures.order.sell(
            ...     code="CNHU24",
            ...     qty="1",
            ...     price="102.00"
            ... )
        """
        ccld_cndt_cd = "2" if order_type == "2" else "6"
        return self.order(
            ovrs_futr_fx_pdno=code,
            sll_buy_dvsn_cd="01",  # 매도
            fm_ord_qty=qty,
            pric_dvsn_cd=order_type,
            fm_limit_ord_pric=price if order_type == "1" else "",
            ccld_cndt_cd=ccld_cndt_cd,
        )

    def cancel(self, orgn_ord_dt: str, orgn_odno: str) -> Optional[Dict]:
        """
        해외선물옵션 주문 취소 (편의 메서드)

        Args:
            orgn_ord_dt: 원주문일자
            orgn_odno: 원주문번호

        Returns:
            취소 결과

        Example:
            >>> result = agent.overseas_futures.order.cancel(
            ...     orgn_ord_dt="20260123",
            ...     orgn_odno="00360686"
            ... )
        """
        return self.modify_cancel(
            ord_dv="1",  # 취소
            orgn_ord_dt=orgn_ord_dt,
            orgn_odno=orgn_odno,
        )

    def modify(
        self,
        orgn_ord_dt: str,
        orgn_odno: str,
        new_price: str,
    ) -> Optional[Dict]:
        """
        해외선물옵션 주문 정정 (편의 메서드)

        Args:
            orgn_ord_dt: 원주문일자
            orgn_odno: 원주문번호
            new_price: 새 주문가격

        Returns:
            정정 결과

        Example:
            >>> result = agent.overseas_futures.order.modify(
            ...     orgn_ord_dt="20260123",
            ...     orgn_odno="00360686",
            ...     new_price="101.50"
            ... )
        """
        return self.modify_cancel(
            ord_dv="0",  # 정정
            orgn_ord_dt=orgn_ord_dt,
            orgn_odno=orgn_odno,
            fm_limit_ord_pric=new_price,
        )
