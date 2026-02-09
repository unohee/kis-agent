"""
Overseas Futures Account API - 해외선물옵션 계좌/잔고 조회 전용 모듈

단일 책임 원칙(SRP)에 따라 계좌 관련 기능만 분리
- 미결제내역(잔고) 조회
- 예수금 현황
- 증거금 상세
- 주문가능 조회
- 주문/체결 내역
- 기간 손익/거래내역
"""

from datetime import datetime
from typing import Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS


class OverseasFuturesAccountAPI(BaseAPI):
    """해외선물옵션 계좌/잔고 조회 전용 API 클래스 (9개 메서드)"""

    def get_balance(self, fuop_dvsn: str = "00") -> Optional[Dict]:
        """
        해외선물옵션 미결제내역 조회 (잔고)

        Args:
            fuop_dvsn: 선물옵션구분 (00:전체, 01:선물, 02:옵션)

        Returns:
            OverseasFuturesBalanceResponse: 잔고 정보
                - output[].srs_cd: 종목코드
                - output[].prdt_nm: 상품명
                - output[].sll_buy_dvsn_cd: 매도매수구분 (01:매도, 02:매수)
                - output[].unsttl_qty: 미결제수량
                - output[].avg_pchs_pric: 평균매입가
                - output[].now_pric: 현재가
                - output[].evlu_pfls_amt: 평가손익금액
                - output[].evlu_pfls_rate: 평가손익률

        Example:
            >>> balance = agent.overseas_futures.get_balance()
            >>> for pos in balance['output']:
            ...     print(f"{pos['srs_cd']}: {pos['unsttl_qty']}계약")
            ...     print(f"  평가손익: {pos['evlu_pfls_amt']}")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_BALANCE"],
            tr_id="OTFM3116R",  # 해외선물옵션 미결제내역
            params={
                "CANO": self.account["account_no"],
                "ACNT_PRDT_CD": self.account["account_code"],
                "FUOP_DVSN": fuop_dvsn,
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
            use_cache=False,  # 잔고는 실시간성 필요
        )

    def get_deposit(self, crcy_cd: str = "TUS", inqr_dt: str = "") -> Optional[Dict]:
        """
        해외선물옵션 예수금 현황 조회

        Args:
            crcy_cd: 통화코드
                - TUS: TOT_USD (미국 달러 합계)
                - TKR: TOT_KRW (한국 원화 합계)
                - USD: 미국
                - EUR: 유로
                - JPY: 일본 엔
                - HKD: 홍콩 달러
                - CNY: 중국 위안
            inqr_dt: 조회일자 (YYYYMMDD, 공백 시 당일)

        Returns:
            OverseasFuturesDepositResponse: 예수금 정보
                - output.dps_amt: 예수금액
                - output.ustl_pfls_amt: 미결제손익금액
                - output.tot_evlu_amt: 총평가금액
                - output.wdrw_psbl_amt: 출금가능금액
                - output.mrgn_amt: 증거금액

        Example:
            >>> deposit = agent.overseas_futures.get_deposit(crcy_cd="TUS")
            >>> print(f"예수금: ${deposit['output']['dps_amt']}")
            >>> print(f"출금가능: ${deposit['output']['wdrw_psbl_amt']}")
        """
        if not inqr_dt:
            inqr_dt = datetime.now().strftime("%Y%m%d")

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_DEPOSIT"],
            tr_id="OTFM3304R",  # 해외선물옵션 예수금
            params={
                "CANO": self.account["account_no"],
                "ACNT_PRDT_CD": self.account["account_code"],
                "CRCY_CD": crcy_cd,
                "INQR_DT": inqr_dt,
            },
            use_cache=False,
        )

    def get_margin_detail(
        self, crcy_cd: str = "TUS", inqr_dt: str = ""
    ) -> Optional[Dict]:
        """
        해외선물옵션 증거금 상세 조회

        Args:
            crcy_cd: 통화코드 (TKR, TUS, USD, HKD, CNY, JPY, VND)
            inqr_dt: 조회일자 (YYYYMMDD, 공백 시 당일)

        Returns:
            OverseasFuturesMarginResponse: 증거금 상세
                - output.tot_mrgn_amt: 총증거금액
                - output.init_mrgn_amt: 개시증거금액
                - output.maint_mrgn_amt: 유지증거금액
                - output.add_mrgn_amt: 추가증거금액

        Example:
            >>> margin = agent.overseas_futures.get_margin_detail()
            >>> print(f"총증거금: ${margin['output']['tot_mrgn_amt']}")
            >>> print(f"유지증거금: ${margin['output']['maint_mrgn_amt']}")
        """
        if not inqr_dt:
            inqr_dt = datetime.now().strftime("%Y%m%d")

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_MARGIN"],
            tr_id="OTFM1412R",  # 해외선물옵션 증거금상세
            params={
                "CANO": self.account["account_no"],
                "ACNT_PRDT_CD": self.account["account_code"],
                "CRCY_CD": crcy_cd,
                "INQR_DT": inqr_dt,
            },
        )

    def get_order_amount(
        self,
        ovrs_futr_fx_pdno: str,
        sll_buy_dvsn_cd: str,
        fm_ord_pric: str,
        ecis_rsvn_ord_yn: str = "N",
    ) -> Optional[Dict]:
        """
        해외선물옵션 주문가능 조회

        Args:
            ovrs_futr_fx_pdno: 해외선물FX상품번호 (종목코드)
            sll_buy_dvsn_cd: 매도매수구분코드 (01:매도, 02:매수)
            fm_ord_pric: FM주문가격
            ecis_rsvn_ord_yn: 행사예약주문여부 (Y/N)

        Returns:
            OverseasFuturesOrderAmountResponse: 주문가능 정보
                - output.ord_psbl_qty: 주문가능수량
                - output.new_ord_mrgn_amt: 신규주문증거금액

        Example:
            >>> amount = agent.overseas_futures.get_order_amount(
            ...     ovrs_futr_fx_pdno="CNHU24",
            ...     sll_buy_dvsn_cd="02",  # 매수
            ...     fm_ord_pric="100.00"
            ... )
            >>> print(f"주문가능수량: {amount['output']['ord_psbl_qty']}")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_PSAMOUNT"],
            tr_id="OTFM3118R",  # 해외선물옵션 주문가능
            params={
                "CANO": self.account["account_no"],
                "ACNT_PRDT_CD": self.account["account_code"],
                "OVRS_FUTR_FX_PDNO": ovrs_futr_fx_pdno,
                "SLL_BUY_DVSN_CD": sll_buy_dvsn_cd,
                "FM_ORD_PRIC": fm_ord_pric,
                "ECIS_RSVN_ORD_YN": ecis_rsvn_ord_yn,
            },
            use_cache=False,
        )

    def get_today_orders(
        self,
        ccld_nccs_dvsn: str = "01",
        sll_buy_dvsn_cd: str = "%%",
        fuop_dvsn: str = "00",
    ) -> Optional[Dict]:
        """
        해외선물옵션 당일 주문내역 조회

        Args:
            ccld_nccs_dvsn: 체결미체결구분 (01:전체, 02:체결, 03:미체결)
            sll_buy_dvsn_cd: 매도매수구분 (%%:전체, 01:매도, 02:매수)
            fuop_dvsn: 선물옵션구분 (00:전체, 01:선물, 02:옵션)

        Returns:
            OverseasFuturesTodayOrderResponse: 당일 주문내역
                - output[].ord_dt: 주문일자
                - output[].odno: 주문번호
                - output[].srs_cd: 종목코드
                - output[].sll_buy_dvsn_cd: 매도매수구분
                - output[].ord_qty: 주문수량
                - output[].ccld_qty: 체결수량
                - output[].ord_stat: 주문상태

        Example:
            >>> orders = agent.overseas_futures.get_today_orders()
            >>> for order in orders['output']:
            ...     print(f"주문번호: {order['odno']}")
            ...     print(f"  {order['srs_cd']}: {order['ord_qty']}계약")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_TODAY_CCLD"],
            tr_id="OTFM3122R",  # 해외선물옵션 당일주문
            params={
                "CANO": self.account["account_no"],
                "ACNT_PRDT_CD": self.account["account_code"],
                "CCLD_NCCS_DVSN": ccld_nccs_dvsn,
                "SLL_BUY_DVSN_CD": sll_buy_dvsn_cd,
                "FUOP_DVSN": fuop_dvsn,
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": "",
            },
            use_cache=False,
        )

    def get_daily_orders(
        self,
        strt_dt: str,
        end_dt: str,
        ccld_nccs_dvsn: str = "01",
        sll_buy_dvsn_cd: str = "%%",
        fuop_dvsn: str = "00",
        fm_pdgr_cd: str = "",
    ) -> Optional[Dict]:
        """
        해외선물옵션 일별 주문내역 조회

        Args:
            strt_dt: 시작일자 (YYYYMMDD)
            end_dt: 종료일자 (YYYYMMDD)
            ccld_nccs_dvsn: 체결미체결구분 (01:전체, 02:체결, 03:미체결)
            sll_buy_dvsn_cd: 매도매수구분 (%%:전체, 01:매도, 02:매수)
            fuop_dvsn: 선물옵션구분 (00:전체, 01:선물, 02:옵션)
            fm_pdgr_cd: FM상품군코드 (공백 시 전체)

        Returns:
            OverseasFuturesDailyOrderResponse: 일별 주문내역
                - output[].ord_dt: 주문일자
                - output[].odno: 주문번호
                - output[].srs_cd: 종목코드
                - output[].ord_qty: 주문수량
                - output[].ccld_qty: 체결수량

        Example:
            >>> orders = agent.overseas_futures.get_daily_orders(
            ...     strt_dt="20260101",
            ...     end_dt="20260131"
            ... )
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_DAILY_ORDER"],
            tr_id="OTFM3120R",  # 해외선물옵션 일별주문
            params={
                "CANO": self.account["account_no"],
                "ACNT_PRDT_CD": self.account["account_code"],
                "STRT_DT": strt_dt,
                "END_DT": end_dt,
                "FM_PDGR_CD": fm_pdgr_cd,
                "CCLD_NCCS_DVSN": ccld_nccs_dvsn,
                "SLL_BUY_DVSN_CD": sll_buy_dvsn_cd,
                "FUOP_DVSN": fuop_dvsn,
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": "",
            },
        )

    def get_daily_executions(
        self,
        strt_dt: str,
        end_dt: str,
        fuop_dvsn_cd: str = "00",
        sll_buy_dvsn_cd: str = "%%",
        crcy_cd: str = "%%%",
    ) -> Optional[Dict]:
        """
        해외선물옵션 일별 체결내역 조회

        Args:
            strt_dt: 시작일자 (YYYYMMDD)
            end_dt: 종료일자 (YYYYMMDD)
            fuop_dvsn_cd: 선물옵션구분 (00:전체, 01:선물, 02:옵션)
            sll_buy_dvsn_cd: 매도매수구분 (%%:전체, 01:매도, 02:매수)
            crcy_cd: 통화코드 (%%%:전체, TUS, TKR, USD, EUR 등)

        Returns:
            OverseasFuturesDailyExecutionResponse: 일별 체결내역
                - output[].ccld_dt: 체결일자
                - output[].srs_cd: 종목코드
                - output[].ccld_qty: 체결수량
                - output[].ccld_pric: 체결가격
                - output[].fee_amt: 수수료
                - output1: 합계 정보

        Example:
            >>> executions = agent.overseas_futures.get_daily_executions(
            ...     strt_dt="20260101",
            ...     end_dt="20260131"
            ... )
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_DAILY_CCLD"],
            tr_id="OTFM3114R",  # 해외선물옵션 일별체결
            params={
                "CANO": self.account["account_no"],
                "ACNT_PRDT_CD": self.account["account_code"],
                "STRT_DT": strt_dt,
                "END_DT": end_dt,
                "FUOP_DVSN_CD": fuop_dvsn_cd,
                "FM_PDGR_CD": "",
                "CRCY_CD": crcy_cd,
                "FM_ITEM_FTNG_YN": "N",
                "SLL_BUY_DVSN_CD": sll_buy_dvsn_cd,
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": "",
            },
        )

    def get_period_profit(
        self,
        from_dt: str,
        to_dt: str,
        crcy_cd: str = "%%%",
        fuop_dvsn: str = "00",
        whol_trsl_yn: str = "N",
    ) -> Optional[Dict]:
        """
        해외선물옵션 기간계좌손익 조회

        Args:
            from_dt: 조회시작일자 (YYYYMMDD)
            to_dt: 조회종료일자 (YYYYMMDD)
            crcy_cd: 통화코드 (%%%:전체, TUS, TKR, USD 등)
            fuop_dvsn: 선물옵션구분 (00:전체, 01:선물, 02:옵션)
            whol_trsl_yn: 전체환산여부 (Y/N)

        Returns:
            OverseasFuturesPeriodProfitResponse: 기간손익
                - output1[].bsop_date: 영업일자
                - output1[].rlzt_pfls_amt: 실현손익금액
                - output1[].fee_amt: 수수료금액
                - output1[].net_pfls_amt: 순손익금액
                - output2.tot_net_pfls_amt: 총순손익금액

        Example:
            >>> profit = agent.overseas_futures.get_period_profit(
            ...     from_dt="20260101",
            ...     to_dt="20260131"
            ... )
            >>> print(f"총순손익: ${profit['output2']['tot_net_pfls_amt']}")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_PERIOD_CCLD"],
            tr_id="OTFM3106R",  # 해외선물옵션 기간손익
            params={
                "INQR_TERM_FROM_DT": from_dt,
                "INQR_TERM_TO_DT": to_dt,
                "CANO": self.account["account_no"],
                "ACNT_PRDT_CD": self.account["account_code"],
                "CRCY_CD": crcy_cd,
                "WHOL_TRSL_YN": whol_trsl_yn,
                "FUOP_DVSN": fuop_dvsn,
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": "",
            },
        )

    def get_period_transactions(
        self,
        from_dt: str,
        to_dt: str,
        acnt_tr_type_cd: str = "1",
        crcy_cd: str = "%%%",
    ) -> Optional[Dict]:
        """
        해외선물옵션 기간계좌거래내역 조회

        Args:
            from_dt: 조회시작일자 (YYYYMMDD)
            to_dt: 조회종료일자 (YYYYMMDD)
            acnt_tr_type_cd: 계좌거래유형코드 (1:전체, 2:입출금, 3:결제)
            crcy_cd: 통화코드 (%%%:전체, TUS, TKR, USD 등)

        Returns:
            OverseasFuturesPeriodTransResponse: 기간거래내역
                - output[].trns_dt: 거래일자
                - output[].trns_type: 거래유형
                - output[].trns_amt: 거래금액
                - output[].bal_amt: 잔액

        Example:
            >>> trans = agent.overseas_futures.get_period_transactions(
            ...     from_dt="20260101",
            ...     to_dt="20260131"
            ... )
            >>> for t in trans['output']:
            ...     print(f"{t['trns_dt']}: {t['trns_type']} {t['trns_amt']}")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_PERIOD_TRANS"],
            tr_id="OTFM3108R",  # 해외선물옵션 기간거래내역
            params={
                "INQR_TERM_FROM_DT": from_dt,
                "INQR_TERM_TO_DT": to_dt,
                "CANO": self.account["account_no"],
                "ACNT_PRDT_CD": self.account["account_code"],
                "ACNT_TR_TYPE_CD": acnt_tr_type_cd,
                "CRCY_CD": crcy_cd,
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
                "PWD_CHK_YN": "N",
            },
        )
