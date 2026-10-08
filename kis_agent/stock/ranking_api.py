"""국내주식 순위분석 API

[국내주식] 순위분석 메뉴 (ranking/*): 예상체결 상승/하락, 호가잔량, 신용잔고, 시간외 거래량/잔량/등락률,
HTS 조회상위, 수익자산지표, 신고/신저 근접, 우선주/괴리율, 대량체결건수, 재무비율, 당사매매,
시장가치, 관심종목등록 상위.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI


def _today() -> str:
    """Today as YYYYMMDD (module-level so tests can pin it)."""
    return datetime.now().strftime("%Y%m%d")


class StockRankingAPI(BaseAPI):
    """국내주식 순위분석 (ranking/*)"""

    def get_after_hour_balance_rank(
        self,
        sort: str = "1",
        market: str = "J",
        index_code: str = "0000",
        div_cls: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_min: str = "",
        price_max: str = "",
        min_volume: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 시간외잔량 순위 [v1_국내주식-093]

        국내주식 시간외잔량 순위 (``/uapi/domestic-stock/v1/ranking/after-hour-balance``, TR FHPST01760000). 모의투자 미지원.

        Args:
            sort: 순위 정렬 구분 (1: 장전 시간외, 2: 장후 시간외, 3: 매도잔량, 4: 매수잔량)
            market: 시장구분 (J: KRX, NX: NXT)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥, 2001: 코스피200)
            div_cls: 분류 구분 코드 (0: 전체)
            target_cls: 대상 구분 코드 (0: 전체)
            exclude_cls: 대상 제외 구분 코드 (0: 전체)
            price_min: 가격 하한 (공백: 전체)
            price_max: 가격 상한 (공백: 전체)
            min_volume: 거래량 하한 (공백: 전체)

        Returns:
            output[]: stck_shrn_iscd(종목코드), hts_kor_isnm(종목명), stck_prpr(현재가),
            ovtm_total_askp_rsqn(시간외 총매도잔량), ovtm_total_bidp_rsqn(시간외 총매수잔량)

        Example:
            >>> agent.get_after_hour_balance_rank()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/after-hour-balance",
            tr_id="FHPST01760000",
            params={
                "fid_input_price_1": price_min,
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": "20176",
                "fid_rank_sort_cls_code": sort,
                "fid_div_cls_code": div_cls,
                "fid_input_iscd": index_code,
                "fid_trgt_exls_cls_code": exclude_cls,
                "fid_trgt_cls_code": target_cls,
                "fid_vol_cnt": min_volume,
                "fid_input_price_2": price_max,
            },
        )

    def get_bulk_trans_num_rank(
        self,
        sort: str = "0",
        market: str = "J",
        index_code: str = "0000",
        div_cls: str = "0",
        stock_code: str = "",
        amount_min: str = "",
        price_min: str = "",
        price_max: str = "",
        target_cls: str = "0",
        exclude_cls: str = "0",
        min_volume: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 대량체결건수 상위 [국내주식-107]

        국내주식 대량체결건수 상위 (``/uapi/domestic-stock/v1/ranking/bulk-trans-num``, TR FHKST190900C0). 모의투자 미지원.

        Args:
            sort: 순위 정렬 구분 (0: 매수상위, 1: 매도상위)
            market: 시장구분 (J: KRX, NX: NXT)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥, 2001: 코스피200)
            div_cls: 분류 구분 코드 (0: 전체)
            stock_code: 종목코드 (공백: 전체종목, 개별종목 조회 시 예: 000660)
            amount_min: 건별 금액 하한 (공백: 제한 없음)
            price_min: 적용 범위 가격 하한 (공백: 전체)
            price_max: 적용 범위 가격 상한 (공백: 전체)
            target_cls: 대상 구분 코드 (0: 전체)
            exclude_cls: 대상 제외 구분 코드 (0: 전체)
            min_volume: 거래량 하한 (공백: 전체)

        Returns:
            output[]: mksc_shrn_iscd(종목코드), hts_kor_isnm(종목명), stck_prpr(현재가),
            shnu_cntg_csnu(매수 체결 건수), seln_cntg_csnu(매도 체결 건수), ntby_cnqn(순매수 수량)

        Example:
            >>> agent.get_bulk_trans_num_rank()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/bulk-trans-num",
            tr_id="FHKST190900C0",
            params={
                "fid_aply_rang_prc_2": price_max,
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": "11909",
                "fid_input_iscd": index_code,
                "fid_rank_sort_cls_code": sort,
                "fid_div_cls_code": div_cls,
                "fid_input_price_1": amount_min,
                "fid_aply_rang_prc_1": price_min,
                "fid_input_iscd_2": stock_code,
                "fid_trgt_exls_cls_code": exclude_cls,
                "fid_trgt_cls_code": target_cls,
                "fid_vol_cnt": min_volume,
            },
        )

    def get_credit_balance_rank(
        self,
        sort: str = "0",
        period: str = "2",
        market: str = "J",
        index_code: str = "0000",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 신용잔고 상위 [국내주식-109]

        국내주식 신용잔고 상위 (``/uapi/domestic-stock/v1/ranking/credit-balance``, TR FHKST17010000). 모의투자 미지원.

        Args:
            sort: 순위 정렬 구분 (융자 0: 잔고비율, 1: 잔고수량, 2: 잔고금액, 3: 잔고비율 증가, 4: 잔고비율 감소 / 대주 5~9: 같은 순서)
            period: 증가율 기간 (2~999)
            market: 시장구분 (J: KRX, NX: NXT)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥, 2001: 코스피200)

        Returns:
            output1: stnd_date1/stnd_date2(기준일), output2[]: mksc_shrn_iscd(종목코드), hts_kor_isnm(종목명),
            whol_loan_rmnd_rate(융자 잔고비율), whol_stln_rmnd_rate(대주 잔고비율)

        Example:
            >>> agent.get_credit_balance_rank()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/credit-balance",
            tr_id="FHKST17010000",
            params={
                "FID_COND_SCR_DIV_CODE": "11701",
                "FID_INPUT_ISCD": index_code,
                "FID_OPTION": period,
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_RANK_SORT_CLS_CODE": sort,
            },
        )

    def get_exp_trans_updown_rank(
        self,
        sort: str = "0",
        market: str = "J",
        index_code: str = "0000",
        div_cls: str = "0",
        price_min: str = "",
        min_volume: str = "",
        min_amount: str = "",
        belong_cls: str = "0",
        session: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 예상체결 상승/하락상위 [v1_국내주식-103]

        국내주식 예상체결 상승/하락상위 (``/uapi/domestic-stock/v1/ranking/exp-trans-updown``, TR FHPST01820000). 모의투자 미지원.

        Args:
            sort: 순위 정렬 구분 (0: 상승률, 1: 상승폭, 2: 보합, 3: 하락률, 4: 하락폭, 5: 체결량, 6: 거래대금)
            market: 시장구분 (J: KRX, NX: NXT)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥, 2001: 코스피200)
            div_cls: 분류 구분 코드 (0: 전체, 1: 보통주, 2: 우선주)
            price_min: 적용 범위 가격 하한 (공백: 전체)
            min_volume: 거래량 하한 (공백: 전체)
            min_amount: 거래대금 하한, 천원 단위 (공백: 전체)
            belong_cls: 소속 구분 코드 (0: 전체)
            session: 장운영 구분 (0: 장전 예상, 1: 장마감 예상)

        Returns:
            output[]: stck_shrn_iscd(종목코드), hts_kor_isnm(종목명), stck_prpr(현재가), prdy_ctrt(전일대비율),
            cntg_vol(예상 체결량), antc_tr_pbmn(예상 거래대금)

        Example:
            >>> agent.get_exp_trans_updown_rank()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/exp-trans-updown",
            tr_id="FHPST01820000",
            params={
                "fid_rank_sort_cls_code": sort,
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": "20182",
                "fid_input_iscd": index_code,
                "fid_div_cls_code": div_cls,
                "fid_aply_rang_prc_1": price_min,
                "fid_vol_cnt": min_volume,
                "fid_pbmn": min_amount,
                "fid_blng_cls_code": belong_cls,
                "fid_mkop_cls_code": session,
            },
        )

    def get_finance_ratio_rank(
        self,
        sort: str = "7",
        fiscal_year: Optional[str] = None,
        fiscal_period: str = "3",
        market: str = "J",
        index_code: str = "0000",
        div_cls: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_min: str = "",
        price_max: str = "",
        min_volume: str = "",
        belong_cls: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 재무비율 순위 [v1_국내주식-092]

        국내주식 재무비율 순위 (``/uapi/domestic-stock/v1/ranking/finance-ratio``, TR FHPST01750000). 모의투자 미지원.

        Args:
            sort: 순위 정렬 구분 (7: 수익성, 11: 안정성, 15: 성장성, 20: 활동성 분석)
            fiscal_year: 회계년도 (예: '2025', 기본값: 직전 연도)
            fiscal_period: 결산 분기 (0: 1/4분기, 1: 반기, 2: 3/4분기, 3: 결산)
            market: 시장구분 (J: KRX, NX: NXT)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥, 2001: 코스피200)
            div_cls: 분류 구분 코드 (0: 전체)
            target_cls: 대상 구분 코드 (0: 전체)
            exclude_cls: 대상 제외 구분 코드 (0: 전체)
            price_min: 가격 하한 (공백: 전체)
            price_max: 가격 상한 (공백: 전체)
            min_volume: 거래량 하한 (공백: 전체)
            belong_cls: 소속 구분 코드 (0)

        Returns:
            output[]: hts_kor_isnm(종목명), mksc_shrn_iscd(종목코드), cptl_op_prfi(총자본 경상이익률),
            sale_totl_rate(매출총이익률), lblt_rate(부채비율), op_prfi_inrt(영업이익 증가율)

        Example:
            >>> agent.get_finance_ratio_rank()
        """
        year = fiscal_year or str(int(_today()[:4]) - 1)
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/finance-ratio",
            tr_id="FHPST01750000",
            params={
                "fid_trgt_cls_code": target_cls,
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": "20175",
                "fid_input_iscd": index_code,
                "fid_div_cls_code": div_cls,
                "fid_input_price_1": price_min,
                "fid_input_price_2": price_max,
                "fid_vol_cnt": min_volume,
                "fid_input_option_1": year,
                "fid_input_option_2": fiscal_period,
                "fid_rank_sort_cls_code": sort,
                "fid_blng_cls_code": belong_cls,
                "fid_trgt_exls_cls_code": exclude_cls,
            },
        )

    def get_hts_top_view_rank(
        self,
    ) -> Optional[Dict[str, Any]]:
        """HTS조회상위20종목 [국내주식-214]

        HTS조회상위20종목 (``/uapi/domestic-stock/v1/ranking/hts-top-view``, TR HHMCM000100C0). 모의투자 미지원.

        Args:
            (없음)

        Returns:
            output1[]: mrkt_div_cls_code(시장구분), mksc_shrn_iscd(종목코드)

        Example:
            >>> agent.get_hts_top_view_rank()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/hts-top-view",
            tr_id="HHMCM000100C0",
            params={},
        )

    def get_market_value_rank(
        self,
        sort: str = "23",
        fiscal_year: Optional[str] = None,
        fiscal_period: str = "0",
        market: str = "J",
        index_code: str = "0000",
        div_cls: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_min: str = "",
        price_max: str = "",
        min_volume: str = "",
        belong_cls: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 시장가치 순위 [v1_국내주식-096]

        국내주식 시장가치 순위 (``/uapi/domestic-stock/v1/ranking/market-value``, TR FHPST01790000). 모의투자 미지원.

        Args:
            sort: 순위 정렬 구분 (23: PER, 24: PBR, 25: PCR, 26: PSR, 27: EPS, 28: EVA, 29: EBITDA, 30: EV/EBITDA, 31: EBITDA/금융비용)
            fiscal_year: 회계연도 (예: '2025', 기본값: 직전 연도)
            fiscal_period: 결산 분기 (0: 1/4분기, 1: 반기, 2: 3/4분기, 3: 결산)
            market: 시장구분 (J: KRX, NX: NXT)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥, 2001: 코스피200)
            div_cls: 분류 구분 코드 (0: 전체, 1: 관리종목, 2: 투자주의, 3: 투자경고, 4: 투자위험예고, 5: 투자위험, 6: 보통주, 7: 우선주)
            target_cls: 대상 구분 코드 (0: 전체)
            exclude_cls: 대상 제외 구분 코드 (0: 전체)
            price_min: 가격 하한 (공백: 전체)
            price_max: 가격 상한 (공백: 전체)
            min_volume: 거래량 하한 (공백: 전체)
            belong_cls: 소속 구분 코드 (0: 전체)

        Returns:
            output[]: hts_kor_isnm(종목명), mksc_shrn_iscd(종목코드), per, pbr, pcr, psr, eps,
            eva, ebitda, pv_div_ebitda(EV/EBITDA)

        Example:
            >>> agent.get_market_value_rank()
        """
        year = fiscal_year or str(int(_today()[:4]) - 1)
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/market-value",
            tr_id="FHPST01790000",
            params={
                "fid_trgt_cls_code": target_cls,
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": "20179",
                "fid_input_iscd": index_code,
                "fid_div_cls_code": div_cls,
                "fid_input_price_1": price_min,
                "fid_input_price_2": price_max,
                "fid_vol_cnt": min_volume,
                "fid_input_option_1": year,
                "fid_input_option_2": fiscal_period,
                "fid_rank_sort_cls_code": sort,
                "fid_blng_cls_code": belong_cls,
                "fid_trgt_exls_cls_code": exclude_cls,
            },
        )

    def get_near_new_highlow_rank(
        self,
        price_cls: str = "0",
        market: str = "J",
        index_code: str = "0000",
        div_cls: str = "0",
        gap_min: str = "0",
        gap_max: str = "100",
        min_volume: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_min: str = "",
        price_max: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 신고/신저근접종목 상위 [v1_국내주식-105]

        국내주식 신고/신저근접종목 상위 (``/uapi/domestic-stock/v1/ranking/near-new-highlow``, TR FHPST01870000). 모의투자 미지원.

        Args:
            price_cls: 가격 구분 (0: 신고근접, 1: 신저근접)
            market: 시장구분 (J: KRX, NX: NXT)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥, 2001: 코스피200)
            div_cls: 분류 구분 코드 (0: 전체, 1: 관리종목, 2: 투자주의, 3: 투자경고)
            gap_min: 괴리율 최소
            gap_max: 괴리율 최대
            min_volume: 적용 범위 거래량 (0: 전체, 100: 100주 이상)
            target_cls: 대상 구분 코드 (0: 전체)
            exclude_cls: 대상 제외 구분 코드 (0: 전체, 1: 관리종목, 2: 투자주의, 3: 투자경고, 4: 투자위험예고, 5: 투자위험, 6: 보통주, 7: 우선주)
            price_min: 적용 범위 가격 하한 (공백: 전체)
            price_max: 적용 범위 가격 상한 (공백: 전체)

        Returns:
            output[]: hts_kor_isnm(종목명), mksc_shrn_iscd(종목코드), stck_prpr(현재가),
            new_hgpr/hprc_near_rate(신고가/근접율), new_lwpr/lwpr_near_rate(신저가/근접율)

        Example:
            >>> agent.get_near_new_highlow_rank()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/near-new-highlow",
            tr_id="FHPST01870000",
            params={
                "fid_aply_rang_vol": min_volume,
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": "20187",
                "fid_div_cls_code": div_cls,
                "fid_input_cnt_1": gap_min,
                "fid_input_cnt_2": gap_max,
                "fid_prc_cls_code": price_cls,
                "fid_input_iscd": index_code,
                "fid_trgt_cls_code": target_cls,
                "fid_trgt_exls_cls_code": exclude_cls,
                "fid_aply_rang_prc_1": price_min,
                "fid_aply_rang_prc_2": price_max,
            },
        )

    def get_overtime_exp_trans_fluct_rank(
        self,
        sort: str = "0",
        market: str = "J",
        index_code: str = "0000",
        div_cls: str = "0",
        price_min: str = "",
        min_volume: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 시간외예상체결등락률 [국내주식-140]

        국내주식 시간외예상체결등락률 (``/uapi/domestic-stock/v1/ranking/overtime-exp-trans-fluct``, TR FHKST11860000). 모의투자 미지원.

        Args:
            sort: 순위 정렬 구분 (0: 상승률, 1: 상승폭, 2: 보합, 3: 하락률, 4: 하락폭)
            market: 시장구분 (J: 주식)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥)
            div_cls: 분류 구분 코드 (0: 전체, 1: 관리종목, 2: 투자주의, 3: 투자경고, 4: 투자위험예고, 5: 투자위험, 6: 보통주, 7: 우선주)
            price_min: 가격 하한 (공백: 전체)
            min_volume: 거래량 하한 (공백: 전체)

        Returns:
            output[]: stck_shrn_iscd(종목코드), hts_kor_isnm(종목명), ovtm_untp_antc_cnpr(시간외 예상체결가),
            ovtm_untp_antc_cntg_ctrt(예상 등락률), ovtm_untp_antc_cnqn(예상 체결량)

        Example:
            >>> agent.get_overtime_exp_trans_fluct_rank()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/overtime-exp-trans-fluct",
            tr_id="FHKST11860000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_COND_SCR_DIV_CODE": "11186",
                "FID_INPUT_ISCD": index_code,
                "FID_RANK_SORT_CLS_CODE": sort,
                "FID_DIV_CLS_CODE": div_cls,
                "FID_INPUT_PRICE_1": price_min,
                "FID_INPUT_PRICE_2": "",
                "FID_INPUT_VOL_1": min_volume,
            },
        )

    def get_overtime_fluctuation_rank(
        self,
        div_cls: str = "2",
        market: str = "J",
        index_code: str = "0000",
        price_min: str = "",
        price_max: str = "",
        min_volume: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 시간외등락율순위 [국내주식-138]

        국내주식 시간외등락율순위 (``/uapi/domestic-stock/v1/ranking/overtime-fluctuation``, TR FHPST02340000). 모의투자 미지원.

        Args:
            div_cls: 분류 구분 코드 (1: 상한가, 2: 상승률, 3: 보합, 4: 하한가, 5: 하락률)
            market: 시장구분 (J: 주식)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥)
            price_min: 가격 하한 (공백: 전체)
            price_max: 가격 상한 (공백: 전체)
            min_volume: 거래량 하한 (공백: 전체)

        Returns:
            output1: ovtm_untp_uplm_issu_cnt(상한 종목수) 등 시간외 단일가 집계,
            output2[]: mksc_shrn_iscd(종목코드), hts_kor_isnm(종목명), ovtm_untp_prpr(시간외 현재가),
            ovtm_untp_prdy_ctrt(시간외 등락률)

        Example:
            >>> agent.get_overtime_fluctuation_rank()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/overtime-fluctuation",
            tr_id="FHPST02340000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_MRKT_CLS_CODE": "",
                "FID_COND_SCR_DIV_CODE": "20234",
                "FID_INPUT_ISCD": index_code,
                "FID_DIV_CLS_CODE": div_cls,
                "FID_INPUT_PRICE_1": price_min,
                "FID_INPUT_PRICE_2": price_max,
                "FID_VOL_CNT": min_volume,
                "FID_TRGT_CLS_CODE": "",
                "FID_TRGT_EXLS_CLS_CODE": "",
            },
        )

    def get_overtime_volume_rank(
        self,
        sort: str = "2",
        market: str = "J",
        index_code: str = "0000",
        price_min: str = "",
        price_max: str = "",
        min_volume: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 시간외거래량순위 [국내주식-139]

        국내주식 시간외거래량순위 (``/uapi/domestic-stock/v1/ranking/overtime-volume``, TR FHPST02350000). 모의투자 미지원.

        Args:
            sort: 순위 정렬 구분 (0: 매수잔량, 1: 매도잔량, 2: 거래량)
            market: 시장구분 (J: 주식)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥)
            price_min: 가격 하한 (공백: 전체)
            price_max: 가격 상한 (공백: 전체)
            min_volume: 거래량 하한 (공백: 전체)

        Returns:
            output1: ovtm_untp_exch_vol(거래소 시간외 거래량) 등 집계,
            output2[]: stck_shrn_iscd(종목코드), hts_kor_isnm(종목명), ovtm_untp_prpr(시간외 현재가),
            ovtm_untp_vol(시간외 거래량)

        Example:
            >>> agent.get_overtime_volume_rank()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/overtime-volume",
            tr_id="FHPST02350000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_COND_SCR_DIV_CODE": "20235",
                "FID_INPUT_ISCD": index_code,
                "FID_RANK_SORT_CLS_CODE": sort,
                "FID_INPUT_PRICE_1": price_min,
                "FID_INPUT_PRICE_2": price_max,
                "FID_VOL_CNT": min_volume,
                "FID_TRGT_CLS_CODE": "",
                "FID_TRGT_EXLS_CLS_CODE": "",
            },
        )

    def get_prefer_disparate_ratio_rank(
        self,
        market: str = "J",
        index_code: str = "0000",
        div_cls: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_min: str = "",
        price_max: str = "",
        min_volume: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 우선주/괴리율 상위 [v1_국내주식-094]

        국내주식 우선주/괴리율 상위 (``/uapi/domestic-stock/v1/ranking/prefer-disparate-ratio``, TR FHPST01770000). 모의투자 미지원.

        Args:
            market: 시장구분 (J: KRX, NX: NXT)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥, 2001: 코스피200)
            div_cls: 분류 구분 코드 (0: 전체)
            target_cls: 대상 구분 코드 (0: 전체)
            exclude_cls: 대상 제외 구분 코드 (0: 전체)
            price_min: 가격 하한 (공백: 전체)
            price_max: 가격 상한 (공백: 전체)
            min_volume: 거래량 하한 (공백: 전체)

        Returns:
            output[]: mksc_shrn_iscd(종목코드), hts_kor_isnm(종목명), prst_iscd/prst_kor_isnm(우선주 종목),
            diff_prpr(괴리 가격), dprt(괴리율)

        Example:
            >>> agent.get_prefer_disparate_ratio_rank()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/prefer-disparate-ratio",
            tr_id="FHPST01770000",
            params={
                "fid_vol_cnt": min_volume,
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": "20177",
                "fid_div_cls_code": div_cls,
                "fid_input_iscd": index_code,
                "fid_trgt_cls_code": target_cls,
                "fid_trgt_exls_cls_code": exclude_cls,
                "fid_input_price_1": price_min,
                "fid_input_price_2": price_max,
            },
        )

    def get_profit_asset_index_rank(
        self,
        sort: str = "0",
        fiscal_year: Optional[str] = None,
        fiscal_period: str = "0",
        market: str = "J",
        index_code: str = "0000",
        div_cls: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_min: str = "",
        price_max: str = "",
        min_volume: str = "",
        belong_cls: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 수익자산지표 순위 [v1_국내주식-090]

        국내주식 수익자산지표 순위 (``/uapi/domestic-stock/v1/ranking/profit-asset-index``, TR FHPST01730000). 모의투자 미지원.

        Args:
            sort: 순위 정렬 구분 (0: 매출이익, 1: 영업이익, 2: 경상이익, 3: 당기순이익, 4: 자산총계, 5: 부채총계, 6: 자본총계)
            fiscal_year: 회계연도 (예: '2025', 기본값: 직전 연도)
            fiscal_period: 결산 분기 (0: 1/4분기, 1: 반기, 2: 3/4분기, 3: 결산)
            market: 시장구분 (J: KRX, NX: NXT)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥, 2001: 코스피200)
            div_cls: 분류 구분 코드 (0: 전체)
            target_cls: 대상 구분 코드 (0: 전체)
            exclude_cls: 대상 제외 구분 코드 (0: 전체)
            price_min: 가격 하한 (공백: 전체)
            price_max: 가격 상한 (공백: 전체)
            min_volume: 거래량 하한 (공백: 전체)
            belong_cls: 소속 구분 코드 (0: 전체)

        Returns:
            output[]: hts_kor_isnm(종목명), mksc_shrn_iscd(종목코드), sale_totl_prfi(매출총이익),
            op_prfi(영업이익), thtr_ntin(당기순이익), total_aset(자산총계)

        Example:
            >>> agent.get_profit_asset_index_rank()
        """
        year = fiscal_year or str(int(_today()[:4]) - 1)
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/profit-asset-index",
            tr_id="FHPST01730000",
            params={
                "fid_cond_mrkt_div_code": market,
                "fid_trgt_cls_code": target_cls,
                "fid_cond_scr_div_code": "20173",
                "fid_input_iscd": index_code,
                "fid_div_cls_code": div_cls,
                "fid_input_price_1": price_min,
                "fid_input_price_2": price_max,
                "fid_vol_cnt": min_volume,
                "fid_input_option_1": year,
                "fid_input_option_2": fiscal_period,
                "fid_rank_sort_cls_code": sort,
                "fid_blng_cls_code": belong_cls,
                "fid_trgt_exls_cls_code": exclude_cls,
            },
        )

    def get_quote_balance_rank(
        self,
        sort: str = "0",
        market: str = "J",
        index_code: str = "0000",
        div_cls: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_min: str = "",
        price_max: str = "",
        min_volume: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 호가잔량 순위 [국내주식-089]

        국내주식 호가잔량 순위 (``/uapi/domestic-stock/v1/ranking/quote-balance``, TR FHPST01720000). 모의투자 미지원.

        Args:
            sort: 순위 정렬 구분 (0: 순매수잔량순, 1: 순매도잔량순, 2: 매수비율순, 3: 매도비율순)
            market: 시장구분 (J: KRX, NX: NXT)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥, 2001: 코스피200)
            div_cls: 분류 구분 코드 (0: 전체)
            target_cls: 대상 구분 코드 (0: 전체)
            exclude_cls: 대상 제외 구분 코드 (0: 전체)
            price_min: 가격 하한 (공백: 전체)
            price_max: 가격 상한 (공백: 전체)
            min_volume: 거래량 하한 (공백: 전체)

        Returns:
            output[]: mksc_shrn_iscd(종목코드), hts_kor_isnm(종목명), stck_prpr(현재가),
            total_askp_rsqn(총매도잔량), total_bidp_rsqn(총매수잔량), shnu_rsqn_rate(매수 잔량비율)

        Example:
            >>> agent.get_quote_balance_rank()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/quote-balance",
            tr_id="FHPST01720000",
            params={
                "fid_vol_cnt": min_volume,
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": "20172",
                "fid_input_iscd": index_code,
                "fid_rank_sort_cls_code": sort,
                "fid_div_cls_code": div_cls,
                "fid_trgt_cls_code": target_cls,
                "fid_trgt_exls_cls_code": exclude_cls,
                "fid_input_price_1": price_min,
                "fid_input_price_2": price_max,
            },
        )

    def get_top_interest_stock_rank(
        self,
        market: str = "J",
        index_code: str = "0000",
        div_cls: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        price_min: str = "",
        price_max: str = "",
        min_volume: str = "",
        start_rank: str = "1",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 관심종목등록 상위 [v1_국내주식-102]

        국내주식 관심종목등록 상위 (``/uapi/domestic-stock/v1/ranking/top-interest-stock``, TR FHPST01800000). 모의투자 미지원.

        Args:
            market: 시장구분 (J: KRX, NX: NXT)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥, 2001: 코스피200)
            div_cls: 분류 구분 코드 (0: 전체, 1: 관리종목, 2: 투자주의, 3: 투자경고, 4: 투자위험예고, 5: 투자위험, 6: 보통주, 7: 우선주)
            target_cls: 대상 구분 코드 (0: 전체)
            exclude_cls: 대상 제외 구분 코드 (0: 전체)
            price_min: 가격 하한 (공백: 전체)
            price_max: 가격 상한 (공백: 전체)
            min_volume: 거래량 하한 (공백: 전체)
            start_rank: 순위 검색 시작값 (1: 1위부터, 10: 10위부터)

        Returns:
            output[]: mksc_shrn_iscd(종목코드), hts_kor_isnm(종목명), stck_prpr(현재가),
            data_rank(순위), inter_issu_reg_csnu(관심종목 등록 건수)

        Example:
            >>> agent.get_top_interest_stock_rank()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/top-interest-stock",
            tr_id="FHPST01800000",
            params={
                "fid_input_iscd_2": "000000",
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": "20180",
                "fid_input_iscd": index_code,
                "fid_trgt_cls_code": target_cls,
                "fid_trgt_exls_cls_code": exclude_cls,
                "fid_input_price_1": price_min,
                "fid_input_price_2": price_max,
                "fid_vol_cnt": min_volume,
                "fid_div_cls_code": div_cls,
                "fid_input_cnt_1": start_rank,
            },
        )

    def get_traded_by_company_rank(
        self,
        sort: str = "1",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        market: str = "J",
        index_code: str = "0000",
        div_cls: str = "0",
        target_cls: str = "0",
        exclude_cls: str = "0",
        min_volume: str = "0",
        price_min: str = "",
        price_max: str = "",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 당사매매종목 상위 [v1_국내주식-104]

        국내주식 당사매매종목 상위 (``/uapi/domestic-stock/v1/ranking/traded-by-company``, TR FHPST01860000). 모의투자 미지원.

        Args:
            sort: 순위 정렬 구분 (0: 매도상위, 1: 매수상위)
            start_date: 조회 시작일 (YYYYMMDD, 기본값: 오늘)
            end_date: 조회 종료일 (YYYYMMDD, 기본값: 오늘)
            market: 시장구분 (J: KRX, NX: NXT)
            index_code: 입력 종목코드 (0000: 전체, 0001: 코스피, 1001: 코스닥, 2001: 코스피200)
            div_cls: 분류 구분 코드 (0: 전체, 1: 관리종목, 2: 투자주의, 3: 투자경고, 4: 투자위험예고, 5: 투자위험, 6: 보통주, 7: 우선주)
            target_cls: 대상 구분 코드 (0: 전체)
            exclude_cls: 대상 제외 구분 코드 (0: 전체)
            min_volume: 적용 범위 거래량 (0: 전체, 100: 100주 이상)
            price_min: 적용 범위 가격 하한 (공백: 전체)
            price_max: 적용 범위 가격 상한 (공백: 전체)

        Returns:
            output[]: mksc_shrn_iscd(종목코드), hts_kor_isnm(종목명), stck_prpr(현재가),
            seln_cnqn_smtn(매도 체결량 합), shnu_cnqn_smtn(매수 체결량 합), ntby_cnqn(순매수 수량)

        Example:
            >>> agent.get_traded_by_company_rank()
        """
        start = start_date or _today()
        end = end_date or _today()
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/ranking/traded-by-company",
            tr_id="FHPST01860000",
            params={
                "fid_trgt_exls_cls_code": exclude_cls,
                "fid_cond_mrkt_div_code": market,
                "fid_cond_scr_div_code": "20186",
                "fid_div_cls_code": div_cls,
                "fid_rank_sort_cls_code": sort,
                "fid_input_date_1": start,
                "fid_input_date_2": end,
                "fid_input_iscd": index_code,
                "fid_trgt_cls_code": target_cls,
                "fid_aply_rang_vol": min_volume,
                "fid_aply_rang_prc_2": price_max,
                "fid_aply_rang_prc_1": price_min,
            },
        )
