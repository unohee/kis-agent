"""계좌 잔고 및 자산 조회 API 모듈.

잔고, 현금, 총자산, 주문가능금액, 증거금 등 계좌 조회 기능 제공.
"""

import logging
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS, KISClient
from ..core.tr_mapping import PaperTradingNotSupportedError


class AccountBalanceQueryAPI(BaseAPI):
    """계좌 잔고 및 자산 조회 API."""

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

    def get_account_balance(self) -> Optional[Dict]:
        """계좌 잔고 조회. output1=보유종목, output2=요약(예수금/총평가/순자산)."""
        is_irp = self.account["ACNT_PRDT_CD"] == "29"
        endpoint = (
            "/uapi/domestic-stock/v1/trading/inquire-balance"
            if not is_irp
            else "/uapi/domestic-stock/v1/trading/pension/inquire-balance"
        )
        tr_id = "TTTC8434R" if not is_irp else "TTTC2208R"
        params = {
            "CANO": self.account["CANO"],
            "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
            "INQR_DVSN": "01" if not is_irp else "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        if not is_irp:
            params["AFHR_FLPR_YN"] = "N"
            params["OFL_YN"] = ""
            params["UNPR_DVSN"] = "01"
            params["FUND_STTL_ICLD_YN"] = "N"
            params["FNCG_AMT_AUTO_RDPT_YN"] = "N"
            params["PRCS_DVSN"] = "00"
        else:
            params["ACCA_DVSN_CD"] = "00"
        return self._make_request_dict(
            endpoint=endpoint,
            tr_id=tr_id,
            params=params,
        )

    def get_cash_available(
        self, stock_code: str = "005930"
    ) -> Optional[Dict[str, Any]]:
        """종목별 매수가능금액 조회. ord_psbl_cash/max_buy_qty 반환."""
        res = self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-psbl-order",
            tr_id="TTTC8908R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "PDNO": stock_code,
                "ORD_UNPR": "0",
                "ORD_DVSN": "00",
                "CMA_EVLU_AMT_ICLD_YN": "Y",
                "OVRS_ICLD_YN": "N",
            },
        )
        if res is not None and res.get("rt_cd") == "JSON_DECODE_ERROR":
            res["디버깅_정보"] = (
                f"원시 응답 텍스트 확인 필요 (상태코드: {res.get('status_code', 'N/A')})"
            )
        return res

    def get_total_asset(self) -> Optional[Dict[str, Any]]:
        """계좌 총자산 조회. 예수금+주식 포함 전체 자산 평가."""
        res = self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-account-balance",
            tr_id="CTRP6548R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "INQR_DVSN_1": "",
                "BSPR_BF_DT_APLY_YN": "",
            },
        )
        if res is not None and res.get("rt_cd") == "JSON_DECODE_ERROR":
            res["디버깅_정보"] = (
                f"원시 응답 텍스트 확인 필요 (상태코드: {res.get('status_code', 'N/A')})"
            )
        return res

    def get_account_order_quantity(self, code: str) -> Optional[Dict]:
        """종목별 주문가능수량 조회. output.max_buy_qty/nrcvb_buy_qty 반환.

        공식 매수가능조회(inquire-psbl-order, TTTC8908R)로 조회한다. 이전 구현이
        호출하던 ``inquire-account-order-quantity``는 공식 명세에 없는 URL이다.
        명세 권고에 따라 시장가(ORD_DVSN=01, ORD_UNPR 공란)로 조회해 증거금율이
        반영된 전량매수 가능수량을 얻는다.

        Note:
            응답 필드가 바뀌었다. 구 응답에 있던 ``output.ord_psbl_qty``는 매수가능
            조회에 없으며, 미수 미사용 시 ``output.nrcvb_buy_qty``, 미수 사용 시
            ``output.max_buy_qty``를 확인한다.
        """
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-psbl-order",
                tr_id="TTTC8908R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": code,
                    "ORD_UNPR": "",
                    "ORD_DVSN": "01",
                    "CMA_EVLU_AMT_ICLD_YN": "Y",
                    "OVRS_ICLD_YN": "N",
                },
            )
        except PaperTradingNotSupportedError:
            raise
        except Exception as e:
            logging.error(f"계좌별 주문 수량 조회 실패: {e}")
            return None

    def get_possible_order_amount(self) -> Optional[Dict]:
        """주문가능금액 조회. output.ord_psbl_amt 반환."""
        try:
            return self._make_request_dict(
                endpoint=API_ENDPOINTS["INQUIRE_PSBL_ORDER"],
                tr_id="TTTC8908R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": "",
                    "ORD_UNPR": "0",
                    "ORD_DVSN": "00",
                    "CMA_EVLU_AMT_ICLD_YN": "Y",
                    "OVRS_ICLD_YN": "N",
                },
            )
        except Exception as e:
            logging.error(f"주문 가능 금액 조회 실패: {e}")
            return None

    def inquire_balance_rlz_pl(self) -> Optional[Dict]:
        """주식잔고조회_실현손익 - 보유 종목의 실현손익 정보 포함 잔고 조회."""
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-balance-rlz-pl",
                tr_id="TTTC8494R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "AFHR_FLPR_YN": "N",
                    "OFL_YN": "",
                    "INQR_DVSN": "00",
                    "UNPR_DVSN": "01",
                    "FUND_STTL_ICLD_YN": "N",
                    "FNCG_AMT_AUTO_RDPT_YN": "N",
                    "PRCS_DVSN": "00",
                    "COST_ICLD_YN": "N",
                    "CTX_AREA_FK100": "",
                    "CTX_AREA_NK100": "",
                },
            )
        except Exception as e:
            logging.error(f"실현손익 잔고 조회 실패: {e}")
            return None

    def inquire_psbl_sell(self, pdno: str) -> Optional[Dict[str, Any]]:
        """매도가능수량조회 - 특정 종목의 매도 가능 수량 조회.

        Note:
            구 구현이 보내던 ``ORD_UNPR``/``ORD_DVSN``은 공식 명세에 없어 제거했다.
        """
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-psbl-sell",
                tr_id="TTTC8408R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": pdno,
                },
            )
        except PaperTradingNotSupportedError:
            raise
        except Exception as e:
            logging.error(f"매도가능수량 조회 실패: {e}")
            return None

    def inquire_intgr_margin(
        self,
        cma_evlu_amt_icld_yn: str = "N",
        wcrc_frcr_dvsn_cd: str = "01",
        fwex_ctrt_frcr_dvsn_cd: str = "01",
    ) -> Optional[Dict[str, Any]]:
        """주식통합증거금 현황 - 통합증거금 계좌의 증거금 현황 조회.

        Args:
            cma_evlu_amt_icld_yn: CMA평가금액포함여부 (공식 명세: "N" 입력).
            wcrc_frcr_dvsn_cd: 원화외화구분코드 (01: 외화기준, 02: 원화기준).
            fwex_ctrt_frcr_dvsn_cd: 선도환계약외화구분코드 (01: 외화기준, 02: 원화기준).

        Note:
            구 구현이 보내던 ``LOAN_DT``는 공식 명세에 없어 제거했다. 세 구분 코드는
            명세상 필수이며 기본값은 공식 샘플(chk_intgr_margin)과 같다.
        """
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/intgr-margin",
                tr_id="TTTC0869R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "CMA_EVLU_AMT_ICLD_YN": cma_evlu_amt_icld_yn,
                    "WCRC_FRCR_DVSN_CD": wcrc_frcr_dvsn_cd,
                    "FWEX_CTRT_FRCR_DVSN_CD": fwex_ctrt_frcr_dvsn_cd,
                },
            )
        except PaperTradingNotSupportedError:
            raise
        except Exception as e:
            logging.error(f"통합증거금 조회 실패: {e}")
            return None

    def inquire_psbl_order(
        self, price: int, pdno: str = "", ord_dvsn: str = "01"
    ) -> Optional[Dict]:
        """매수가능 조회. ord_psbl_cash/max_buy_qty/ord_psbl_qty 반환."""
        try:
            is_irp = self.account["ACNT_PRDT_CD"] == "29"
            endpoint = (
                "/uapi/domestic-stock/v1/trading/inquire-psbl-order"
                if not is_irp
                else "/uapi/domestic-stock/v1/trading/pension/inquire-psbl-order"
            )
            tr_id = (
                "TTTC8908R" if not is_irp else "TTTC0503R"
            )  # 모의투자 변환은 client.make_request가 처리
            params = {
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "PDNO": pdno,
                "ORD_UNPR": str(price),
                "ORD_DVSN": ord_dvsn,
                "CMA_EVLU_AMT_ICLD_YN": "Y",
            }
            if not is_irp:
                params["OVRS_ICLD_YN"] = "N"
            else:
                params["ACCA_DVSN_CD"] = "00"
            res = self.client.make_request(
                endpoint=endpoint,
                tr_id=tr_id,  # 모의투자 변환은 client.make_request가 처리
                params=params,
            )
            if res and res.get("rt_cd") == "0":
                return res.get("output", {})
            return None
        except Exception as e:
            logging.error(f"매수가능 조회 실패: {e}")
            return None

    def inquire_credit_psamount(self, pdno: str) -> Optional[Dict[str, Any]]:
        """신용매수가능조회 - 신용거래로 매수 가능한 금액과 수량 조회.

        Note:
            구 구현이 보내던 ``CRDT_LOAN_DT``는 공식 명세에 없어 제거했다.
        """
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-credit-psamount",
                tr_id="TTTC8909R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": pdno,
                    "ORD_UNPR": "0",
                    "ORD_DVSN": "00",
                    "CRDT_TYPE": "21",
                    "CMA_EVLU_AMT_ICLD_YN": "Y",
                    "OVRS_ICLD_YN": "N",
                },
            )
        except PaperTradingNotSupportedError:
            raise
        except Exception as e:
            logging.error(f"신용매수가능 조회 실패: {e}")
            return None
