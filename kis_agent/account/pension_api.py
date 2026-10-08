"""퇴직연금 계좌 API

[국내주식] 주문/계좌 메뉴의 퇴직연금(trading/pension/*): 예수금, 미체결내역, 매수가능,
체결기준잔고, 잔고조회. 계좌 facade(AccountAPI)가 동적으로 위임한다.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.

Notes:
    * 55번 계좌(DC가입자계좌)는 이 API들을 이용할 수 없다 (공식 안내).
    * 모두 모의투자 미지원이다.
    * ``AccountBalanceQueryAPI.get_account_balance`` / ``inquire_psbl_order`` already
      route IRP accounts (ACNT_PRDT_CD "29") to the balance / buy-power URLs; the
      methods here are the explicit pension entry points with the full official
      parameter set.
"""

from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI

_CURSOR = [
    ("CTX_AREA_FK100", "ctx_area_fk100"),
    ("CTX_AREA_NK100", "ctx_area_nk100"),
]


class AccountPensionAPI(BaseAPI):
    """퇴직연금 계좌 조회 (trading/pension/*)"""

    def get_pension_deposit(self, acca_dvsn_cd: str = "00") -> Optional[Dict[str, Any]]:
        """퇴직연금 예수금조회 [국내주식-035]

        Args:
            acca_dvsn_cd: 적립금구분코드 (00)
        Returns:
            output: dnca_tota(예수금총액), nxdy_excc_amt(익일정산액),
            nxdy_sttl_amt(익일결제금액), nx2_day_sttl_amt(2익일결제금액)
        Example:
            >>> agent.get_pension_deposit()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/trading/pension/inquire-deposit",
            tr_id="TTTC0506R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "ACCA_DVSN_CD": acca_dvsn_cd,
            },
        )

    def get_pension_daily_ccld(
        self,
        sll_buy_dvsn_cd: str = "00",
        ccld_nccs_dvsn: str = "%%",
        inqr_dvsn_3: str = "00",
        user_dvsn_cd: str = "%%",
        include_nxt: bool = False,
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """퇴직연금 미체결내역 [국내주식-033]

        Follows the continuation cursor (CTX_AREA_FK100/NK100) up to ``max_pages``.

        Args:
            sll_buy_dvsn_cd: 매도매수구분 (00 전체, 01 매도, 02 매수)
            ccld_nccs_dvsn: 체결미체결구분 (%% 전체, 01 체결, 02 미체결)
            inqr_dvsn_3: 조회구분3 (00 전체)
            user_dvsn_cd: 사용자구분코드 (%%)
            include_nxt: False -> TTTC2201R (기존, KRX만),
                True -> TTTC2210R (KRX, NXT/SOR 포함)
            max_pages: 최대 페이지 수
        Returns:
            output[]: odno(주문번호), pdno, prdt_name, sll_buy_dvsn_cd, ord_unpr,
            ord_qty, tot_ccld_qty, nccs_qty(미체결수량), ord_tmd(주문시각)
        Example:
            >>> agent.get_pension_daily_ccld(ccld_nccs_dvsn="02")
        """
        return self._paginate(
            endpoint="/uapi/domestic-stock/v1/trading/pension/inquire-daily-ccld",
            tr_id="TTTC2210R" if include_nxt else "TTTC2201R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "USER_DVSN_CD": user_dvsn_cd,
                "SLL_BUY_DVSN_CD": sll_buy_dvsn_cd,
                "CCLD_NCCS_DVSN": ccld_nccs_dvsn,
                "INQR_DVSN_3": inqr_dvsn_3,
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
            cursor=_CURSOR,
            output_keys=("output",),
            max_pages=max_pages,
        )

    def get_pension_psbl_order(
        self,
        pdno: str,
        price: int = 0,
        ord_dvsn: str = "01",
        acca_dvsn_cd: str = "00",
        cma_evlu_amt_icld_yn: str = "Y",
    ) -> Optional[Dict[str, Any]]:
        """퇴직연금 매수가능조회 [국내주식-034]

        Args:
            pdno: 상품번호 (종목코드, 예: "069500")
            price: 주문단가 (시장가는 0)
            ord_dvsn: 주문구분 (00 지정가, 01 시장가)
            acca_dvsn_cd: 적립금구분코드 (00)
            cma_evlu_amt_icld_yn: CMA평가금액포함여부 (Y 포함, N 미포함)
        Returns:
            output: ord_psbl_cash(주문가능현금), ruse_psbl_amt, psbl_qty_calc_unpr,
            max_buy_amt(최대매수금액), max_buy_qty(최대매수수량)
        Example:
            >>> agent.get_pension_psbl_order("069500", 30800, "00")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/trading/pension/inquire-psbl-order",
            tr_id="TTTC0503R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "PDNO": pdno,
                "ACCA_DVSN_CD": acca_dvsn_cd,
                "CMA_EVLU_AMT_ICLD_YN": cma_evlu_amt_icld_yn,
                "ORD_DVSN": ord_dvsn,
                "ORD_UNPR": str(price),
            },
        )

    def get_pension_present_balance(
        self, user_dvsn_cd: str = "00", max_pages: int = 10
    ) -> Optional[Dict[str, Any]]:
        """퇴직연금 체결기준잔고 [국내주식-032]

        Follows the continuation cursor (CTX_AREA_FK100/NK100) up to ``max_pages``.

        Args:
            user_dvsn_cd: 사용자구분코드 (00)
            max_pages: 최대 페이지 수
        Returns:
            output1[]: 보유종목 (pdno, prdt_name, hldg_qty, slpsb_qty, pchs_avg_pric,
            prpr, evlu_amt, evlu_pfls_amt, evlu_pfls_rt)
            output2: 합계 (pchs_amt_smtl_amt, evlu_amt_smtl_amt, evlu_pfls_smtl_amt,
            pftrt)
        Example:
            >>> agent.get_pension_present_balance()
        """
        return self._paginate(
            endpoint="/uapi/domestic-stock/v1/trading/pension/inquire-present-balance",
            tr_id="TTTC2202R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "USER_DVSN_CD": user_dvsn_cd,
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
            cursor=_CURSOR,
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_pension_balance(
        self,
        acca_dvsn_cd: str = "00",
        inqr_dvsn: str = "00",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """퇴직연금 잔고조회 [국내주식-036]

        주식·ETF·ETN만 조회되며 펀드는 조회되지 않는다. Follows the continuation
        cursor (CTX_AREA_FK100/NK100) up to ``max_pages``.

        Args:
            acca_dvsn_cd: 적립금구분코드 (00)
            inqr_dvsn: 조회구분 (00 전체)
            max_pages: 최대 페이지 수
        Returns:
            output1[]: 보유종목 (pdno, prdt_name, hldg_qty, ord_psbl_qty, pchs_avg_pric,
            prpr, evlu_amt, evlu_pfls_amt, evlu_erng_rt)
            output2: 계좌 요약 (dnca_tot_amt, nxdy_excc_amt, scts_evlu_amt, tot_evlu_amt)
        Example:
            >>> agent.get_pension_balance()
        """
        return self._paginate(
            endpoint="/uapi/domestic-stock/v1/trading/pension/inquire-balance",
            tr_id="TTTC2208R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "ACCA_DVSN_CD": acca_dvsn_cd,
                "INQR_DVSN": inqr_dvsn,
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
            cursor=_CURSOR,
            output_keys=("output1",),
            max_pages=max_pages,
        )
