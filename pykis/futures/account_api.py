"""
Futures Account API - 선물옵션 계좌/잔고 조회 전용 모듈

단일 책임 원칙(SRP)에 따라 계좌 관련 기능만 분리
- 잔고 조회
- 손익 조회
- 예수금 조회
- 야간 거래 잔고
"""

from typing import Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS


class FuturesAccountAPI(BaseAPI):
    """선물옵션 계좌/잔고 조회 전용 API 클래스 (6개 메서드)"""

    def inquire_balance(self) -> Optional[Dict]:
        """
        선물옵션 잔고 현황 조회

        Args:
            없음 (계좌 정보는 Agent 초기화 시 설정)

        Returns:
            FuturesBalanceResponse: 선물옵션 잔고 리스트
                - output[].fuop_item_code: 선물옵션 종목코드
                - output[].item_name: 종목명
                - output[].ord_psbl_qty: 주문가능수량
                - output[].avg_pric: 평균가
                - output[].prsnt_pric: 현재가
                - output[].fnoat_plamt: 평가손익금액
                - output[].erng_rate: 수익률 (%)

        Example:
            >>> balance = agent.futures.account.inquire_balance()
            >>> for item in balance['output']:
            ...     print(f"{item['item_name']}: {item['fnoat_plamt']}원")

        Note:
            TR_ID는 실전/모의 환경에 따라 자동 선택
            - 실전: CTFO6118R
            - 모의: VTFO6118R
        """
        # 실전/모의 구분 (Agent 설정에 따라 자동 선택)
        tr_id = "VTFO6118R" if self._is_virtual() else "CTFO6118R"

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_BALANCE"],
            tr_id=tr_id,
            params={
                "ACNT_NO": self._get_account_no(),
                "ACNT_PDNO": self._get_account_code(),
                "AFHR_FLPR_YN": "N",  # 시간외단일가여부 (N: 정규장)
                "CTX_AREA_FK200": "",  # 연속조회검색조건
                "CTX_AREA_NK200": "",  # 연속조회키
            },
        )

    def inquire_balance_settlement_pl(self) -> Optional[Dict]:
        """
        선물옵션 잔고 청산손익 조회

        Returns:
            청산 손익 상세 정보
                - output[]: 청산 내역 리스트
                - fuop_item_code: 종목코드
                - item_name: 종목명
                - lqd_amt: 청산금액
                - lqd_pfls_amt: 청산손익금액
                - lqd_pfls_rt: 청산손익률 (%)

        Example:
            >>> pl = agent.futures.account.inquire_balance_settlement_pl()
            >>> total_pl = sum(float(item['lqd_pfls_amt']) for item in pl['output'])
            >>> print(f"총 청산손익: {total_pl}원")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_BALANCE_SETTLEMENT_PL"],
            tr_id="CTFO6117R",
            params={
                "ACNT_NO": self._get_account_no(),
                "ACNT_PDNO": self._get_account_code(),
                "INQR_STRT_DT": "",  # 조회시작일자 (공백 시 당일)
                "INQR_END_DT": "",  # 조회종료일자 (공백 시 당일)
                "SLL_BUY_DVSN_CD": "00",  # 매도매수구분 (00:전체, 01:매도, 02:매수)
            },
        )

    def inquire_balance_valuation_pl(self) -> Optional[Dict]:
        """
        선물옵션 잔고 평가손익 내역 조회

        Returns:
            평가 손익 상세 정보
                - output[]: 평가 내역 리스트
                - fuop_item_code: 종목코드
                - item_name: 종목명
                - evlu_amt: 평가금액
                - evlu_pfls_amt: 평가손익금액
                - evlu_pfls_rt: 평가손익률 (%)
                - fnoat_plamt: 평가손익금액 (Floating Profit/Loss)

        Example:
            >>> pl = agent.futures.account.inquire_balance_valuation_pl()
            >>> for item in pl['output']:
            ...     print(f"{item['item_name']}: {item['evlu_pfls_rt']}%")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_BALANCE_VALUATION_PL"],
            tr_id="CTFO6159R",
            params={
                "ACNT_NO": self._get_account_no(),
                "ACNT_PDNO": self._get_account_code(),
                "AFHR_FLPR_YN": "N",  # 시간외단일가여부
            },
        )

    def inquire_deposit(self) -> Optional[Dict]:
        """
        선물옵션 예수금 및 총자산 현황 조회

        Returns:
            FuturesDepositResponse: 예수금 및 자산 정보
                - output.fuop_dps_amt: 선물옵션예수금액
                - output.fuop_evlu_pfls_amt: 선물옵션평가손익금액
                - output.tot_evlu_amt: 총평가금액
                - output.tot_asst_amt: 총자산금액
                - output.maint_mrgn_amt: 유지증거금액
                - output.nass_amt: 순자산금액

        Example:
            >>> deposit = agent.futures.account.inquire_deposit()
            >>> print(f"예수금: {deposit['output']['fuop_dps_amt']}원")
            >>> print(f"총자산: {deposit['output']['tot_asst_amt']}원")
            >>> print(f"평가손익: {deposit['output']['fuop_evlu_pfls_amt']}원")

        Note:
            선물옵션 거래를 위한 증거금 및 예수금 상태 확인용
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_DEPOSIT"],
            tr_id="CTRP6550R",
            params={
                "ACNT_NO": self._get_account_no(),
                "ACNT_PDNO": self._get_account_code(),
                "AFHR_FLPR_YN": "N",  # 시간외단일가여부
                "INQR_DVSN_CD": "00",  # 조회구분 (00:전체)
            },
        )

    def inquire_ngt_balance(self) -> Optional[Dict]:
        """
        야간 선물옵션 잔고 현황 조회

        Returns:
            야간 거래 잔고 리스트
                - output[]: 야간 잔고 리스트
                - fuop_item_code: 종목코드
                - item_name: 종목명
                - ord_psbl_qty: 주문가능수량
                - avg_pric: 평균가
                - fnoat_plamt: 평가손익금액

        Example:
            >>> ngt_balance = agent.futures.account.inquire_ngt_balance()
            >>> print(f"야간 잔고: {len(ngt_balance['output'])}건")

        Note:
            야간 거래 시간대 (18:00 ~ 익일 05:00) 잔고 조회
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_NGT_BALANCE"],
            tr_id="CTFN6118R",
            params={
                "ACNT_NO": self._get_account_no(),
                "ACNT_PDNO": self._get_account_code(),
                "AFHR_FLPR_YN": "N",  # 시간외단일가여부
                "CTX_AREA_FK200": "",  # 연속조회검색조건
                "CTX_AREA_NK200": "",  # 연속조회키
            },
        )

    def ngt_margin_detail(self) -> Optional[Dict]:
        """
        야간 선물옵션 증거금 상세 조회

        Returns:
            야간 거래 증거금 상세 정보
                - output[]: 증거금 상세 리스트
                - fuop_item_code: 종목코드
                - item_name: 종목명
                - maint_mrgn: 유지증거금
                - ord_mrgn: 주문증거금
                - dpsi_reqr_amt: 예탁금필요금액

        Example:
            >>> margin = agent.futures.account.ngt_margin_detail()
            >>> for item in margin['output']:
            ...     print(f"{item['item_name']}: {item['maint_mrgn']}원")

        Note:
            야간 거래 시 필요한 증거금 및 예탁금 확인용
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_NGT_MARGIN_DETAIL"],
            tr_id="CTFN7107R",
            params={
                "ACNT_NO": self._get_account_no(),
                "ACNT_PDNO": self._get_account_code(),
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
        return "03"  # 기본값: 선물옵션

    def _is_virtual(self) -> bool:
        """모의투자 여부 확인"""
        # base_url에서 판단 (vts 포함 여부)
        if hasattr(self.client, "base_url"):
            return "vts" in self.client.base_url.lower()
        return False
