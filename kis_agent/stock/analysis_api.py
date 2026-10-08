"""국내주식 시세분석 API

[국내주식] 시세분석 메뉴: 공매도 일별추이, 상하한가 포착, 대차거래추이, 일별 매수매도 체결량,
체결금액별 매매비중, 증시자금 종합, 예상체결가 추이, 시장별 투자자매매동향(시세) 등.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI


class StockAnalysisAPI(BaseAPI):
    """국내주식 시세분석"""

    def get_capture_uplowprice(
        self,
        limit_type: str = "0",
        div_cls: str = "0",
        index_code: str = "0000",
        market: str = "J",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 상하한가 포착 [국내주식-190]

        국내주식 상하한가 포착 (``/uapi/domestic-stock/v1/quotations/capture-uplowprice``, TR FHKST130000C0). 모의투자 미지원.

        Args:
            limit_type: 상하한가 구분 (0: 상한가, 1: 하한가)
            div_cls: 분류 구분 (0: 상하한가 종목, 6: 8% 근접, 5: 10% 근접, 1: 15% 근접, 2: 20% 근접, 3: 25% 근접)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥)
            market: 시장구분 (J: 주식)

        Returns:
            output[]: mksc_shrn_iscd(종목코드), hts_kor_isnm(종목명), stck_prpr(현재가), prdy_ctrt(전일대비율),
            stck_mxpr(상한가), stck_llam(하한가), total_askp_rsqn/total_bidp_rsqn(총 매도/매수 잔량)

        Example:
            >>> agent.get_capture_uplowprice(limit_type="0")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/capture-uplowprice",
            tr_id="FHKST130000C0",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_COND_SCR_DIV_CODE": "11300",
                "FID_PRC_CLS_CODE": limit_type,
                "FID_DIV_CLS_CODE": div_cls,
                "FID_INPUT_ISCD": index_code,
                "FID_TRGT_CLS_CODE": "",
                "FID_TRGT_EXLS_CLS_CODE": "",
                "FID_INPUT_PRICE_1": "",
                "FID_INPUT_PRICE_2": "",
                "FID_VOL_CNT": "",
            },
        )

    def get_daily_loan_trans(
        self,
        code: str = "",
        division: str = "3",
        start_date: str = "",
        end_date: str = "",
        cts: str = "",
    ) -> Optional[Dict[str, Any]]:
        """종목별 일별 대차거래추이 [국내주식-135]

        종목별 일별 대차거래추이 (``/uapi/domestic-stock/v1/quotations/daily-loan-trans``, TR HHPST074500C0). 모의투자 미지원.

        Note:
            응답 명세에 연속조회 KEY 필드가 없어 자동 페이징은 하지 않는다. 이전 응답의 KEY 가 있으면 ``cts`` 로 넘긴다.

        Args:
            code: 종목코드 (division 이 '3'(종목)일 때 필수, 예: '005930')
            division: 조회 구분 (1: 코스피, 2: 코스닥, 3: 종목)
            start_date: 조회 시작일 (YYYYMMDD, 공백: 서버 기본값)
            end_date: 조회 종료일 (YYYYMMDD, 공백: 서버 기본값)
            cts: 이전 조회 KEY (공백: 처음부터)

        Returns:
            output1[]: bsop_date(일자), stck_prpr(현재가), new_stcn(신규 대차 수량), rdmp_stcn(상환 수량),
            rmnd_stcn(잔고 수량), rmnd_amt(잔고 금액)

        Example:
            >>> agent.get_daily_loan_trans("005930", start_date="20260901", end_date="20261007")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/daily-loan-trans",
            tr_id="HHPST074500C0",
            params={
                "MRKT_DIV_CLS_CODE": division,
                "MKSC_SHRN_ISCD": code,
                "START_DATE": start_date,
                "END_DATE": end_date,
                "CTS": cts,
            },
        )

    def get_daily_short_sale(
        self,
        code: str,
        market: str = "J",
        start_date: str = "",
        end_date: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 공매도 일별추이 [국내주식-134]

        국내주식 공매도 일별추이 (``/uapi/domestic-stock/v1/quotations/daily-short-sale``, TR FHPST04830000). 모의투자 미지원.

        Args:
            code: 종목코드 (6자리, 예: '005930')
            market: 시장구분 (J: 주식)
            start_date: 조회 시작일 (YYYYMMDD, 공백: 전체 기간)
            end_date: 조회 종료일 (YYYYMMDD, 공백: 누적)

        Returns:
            output1: stck_prpr(현재가), acml_vol(누적 거래량),
            output2[]: stck_bsop_date(일자), ssts_cntg_qty(공매도 체결 수량), ssts_vol_rlim(공매도 거래량 비중),
            ssts_tr_pbmn(공매도 거래대금), avrg_prc(평균가)

        Example:
            >>> agent.get_daily_short_sale("005930", start_date="20260901", end_date="20261007")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/daily-short-sale",
            tr_id="FHPST04830000",
            params={
                "FID_INPUT_DATE_2": end_date,
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": start_date,
            },
        )

    def get_exp_price_trend(
        self,
        code: str,
        market: str = "J",
        session: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 예상체결가 추이 [국내주식-118]

        국내주식 예상체결가 추이 (``/uapi/domestic-stock/v1/quotations/exp-price-trend``, TR FHPST01810000). 모의투자 미지원.

        Args:
            code: 종목코드 (6자리, 예: '005930')
            market: 시장구분 (J: 주식)
            session: 장운영 구분 (0: 전체, 4: 체결량 0 제외)

        Returns:
            output1: antc_cnpr(예상체결가), antc_cntg_prdy_ctrt(예상 등락률), antc_vol(예상 체결량),
            output2[]: stck_cntg_hour(시간), stck_prpr(예상가), prdy_ctrt(전일대비율), acml_vol(누적 거래량)

        Example:
            >>> agent.get_exp_price_trend("005930")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/exp-price-trend",
            tr_id="FHPST01810000",
            params={
                "fid_mkop_cls_code": session,
                "fid_cond_mrkt_div_code": market,
                "fid_input_iscd": code,
            },
        )

    def get_daily_trade_volume(
        self,
        code: str,
        market: str = "J",
        period: str = "D",
        start_date: str = "",
        end_date: str = "",
    ) -> Optional[Dict[str, Any]]:
        """종목별일별매수매도체결량 [v1_국내주식-056]

        종목별일별매수매도체결량 (``/uapi/domestic-stock/v1/quotations/inquire-daily-trade-volume``, TR FHKST03010800). 모의투자 미지원.

        Args:
            code: 종목코드 (6자리, 예: '005930')
            market: 시장구분 (J: KRX, NX: NXT, UN: 통합)
            period: 기간 구분 (D)
            start_date: 조회 시작일 (YYYYMMDD, 공백: 서버 기본값)
            end_date: 조회 종료일 (YYYYMMDD, 공백: 서버 기본값)

        Returns:
            output1: shnu_cnqn_smtn(매수 체결량 합), seln_cnqn_smtn(매도 체결량 합),
            output2[]: stck_bsop_date(일자), total_seln_qty(총 매도 수량), total_shnu_qty(총 매수 수량)

        Example:
            >>> agent.get_daily_trade_volume("005930", start_date="20260901", end_date="20261007")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-daily-trade-volume",
            tr_id="FHKST03010800",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date,
                "FID_PERIOD_DIV_CODE": period,
            },
        )

    def get_investor_time_by_market(
        self,
        market: str = "KSP",
        sector: str = "0001",
    ) -> Optional[Dict[str, Any]]:
        """시장별 투자자매매동향(시세) [v1_국내주식-074]

        시장별 투자자매매동향(시세) (``/uapi/domestic-stock/v1/quotations/inquire-investor-time-by-market``, TR FHPTJ04030000). 모의투자 미지원.

        Args:
            market: 시장구분 (KSP: 코스피, KSQ: 코스닥, K2I: 선물/콜/풋옵션, 999: 주식선물, ETF, ELW, ETN, MKI: 미니, WKM: 위클리월, WKI: 위클리목, KQI: 코스닥150)
            sector: 업종 구분 (KSP: 0001 종합 ~ 0027 제조업, KSQ: 1001 종합 ~ 1041 IT부품, K2I: F001/OC01/OP01, 999: S001, ETF: T000)

        Returns:
            output[]: frgn_ntby_qty/prsn_ntby_qty/orgn_ntby_qty(외국인/개인/기관 순매수 수량),
            frgn_ntby_tr_pbmn/prsn_ntby_tr_pbmn/orgn_ntby_tr_pbmn(순매수 거래대금)

        Example:
            >>> agent.get_investor_time_by_market("KSP", "0001")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-investor-time-by-market",
            tr_id="FHPTJ04030000",
            params={
                "fid_input_iscd": market,
                "fid_input_iscd_2": sector,
            },
        )

    def get_mktfunds(
        self,
        date: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내 증시자금 종합 [국내주식-193]

        국내 증시자금 종합 (``/uapi/domestic-stock/v1/quotations/mktfunds``, TR FHKST649100C0). 모의투자 미지원.

        Args:
            date: 기준일 (YYYYMMDD, 공백: 서버 기본값)

        Returns:
            output[]: bsop_date(일자), bstp_nmix_prpr(지수), cust_dpmn_amt(고객예탁금), uncl_amt(미수금),
            crdt_loan_rmnd(신용융자 잔고), futs_tfam_amt(선물예수금), mmf_amt(MMF)

        Example:
            >>> agent.get_mktfunds()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/mktfunds",
            tr_id="FHKST649100C0",
            params={
                "FID_INPUT_DATE_1": date,
            },
        )

    def get_tradprt_byamt(
        self,
        code: str,
        market: str = "J",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 체결금액별 매매비중 [국내주식-192]

        국내주식 체결금액별 매매비중 (``/uapi/domestic-stock/v1/quotations/tradprt-byamt``, TR FHKST111900C0). 모의투자 미지원.

        Args:
            code: 종목코드 (6자리, 예: '005930')
            market: 시장구분 (J: KRX, NX: NXT, UN: 통합)

        Returns:
            output[]: prpr_name(가격대), smtn_avrg_prpr(평균가), acml_vol(누적 거래량),
            shnu_cntg_csnu/seln_cntg_csnu(매수/매도 체결 건수), whol_ntby_qty_rate(순매수 비중)

        Example:
            >>> agent.get_tradprt_byamt("005930")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/tradprt-byamt",
            tr_id="FHKST111900C0",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_COND_SCR_DIV_CODE": "11119",
                "FID_INPUT_ISCD": code,
            },
        )
