"""ELW 순위 API

[국내주식] ELW 시세 메뉴의 순위 조회 (elw/v1/ranking/*).

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.

Every ELW API is unsupported on the paper-trading server; calling one in paper
mode raises ``PaperTradingNotSupportedError`` from the client.
"""

from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI


class ElwRankingAPI(BaseAPI):
    """ELW 순위 조회"""

    def get_elw_indicator_rank(
        self,
        sort_cls_code: str = "0",
        underlying: str = "000000",
        issuer: str = "00000",
        call_put: str = "0",
        price_min: str = "",
        price_max: str = "",
        volume_min: str = "",
        volume_max: str = "",
        settle_type: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """ELW 지표순위 [국내주식-169]

        Args:
            sort_cls_code: 정렬 (0 전환비율, 1 레버리지, 2 행사가, 3 내재가치, 4 시간가치)
            underlying: 기초자산 (000000 전체, 2001 코스피200, 3003 코스닥150, 종목코드)
            issuer: 발행사 (00000 전체, 00003 한국투자증권, 00017 KB증권, 00005 미래에셋)
            call_put: 0 전체, 1 콜, 2 풋
            price_min / price_max: 가격 이상 / 이하 (공백 = 제한 없음)
            volume_min / volume_max: 거래량 이상 / 이하 (공백 = 제한 없음)
            settle_type: 결제방법 (0 전체, 1 일반, 2 조기종료)
        Returns:
            output1[]: elw_shrn_iscd, elw_kor_isnm, elw_prpr, prdy_ctrt, acml_vol,
            stck_cnvr_rate, lvrg_val, acpr, tmvl_val, invl_val
        Example:
            >>> agent.elw.get_elw_indicator_rank(sort_cls_code="1")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/ranking/indicator",
            tr_id="FHPEW02790000",
            params={
                "FID_COND_MRKT_DIV_CODE": "W",
                "FID_COND_SCR_DIV_CODE": "20279",
                "FID_UNAS_INPUT_ISCD": underlying,
                "FID_INPUT_ISCD": issuer,
                "FID_DIV_CLS_CODE": call_put,
                "FID_INPUT_PRICE_1": price_min,
                "FID_INPUT_PRICE_2": price_max,
                "FID_INPUT_VOL_1": volume_min,
                "FID_INPUT_VOL_2": volume_max,
                "FID_RANK_SORT_CLS_CODE": sort_cls_code,
                "FID_BLNG_CLS_CODE": settle_type,
            },
        )

    def get_elw_quick_change_rank(
        self,
        sort_cls_code: str = "1",
        hour_cls_code: str = "1",
        input_hour_1: str = "",
        input_hour_2: str = "",
        underlying: str = "000000",
        issuer: str = "00000",
        price_min: str = "",
        price_max: str = "",
        volume_min: str = "",
        volume_max: str = "",
        settle_type: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """ELW 당일급변종목 [국내주식-171]

        Args:
            sort_cls_code: 정렬 (1 가격급등, 2 가격급락, 3 거래량급증, 4 매수잔량급증,
                5 매도잔량급증)
            hour_cls_code: 시간구분 (1 분, 2 일)
            input_hour_1: 입력 일 또는 분
            input_hour_2: 기준시간 (분 선택 시)
            underlying: 기초자산 (000000 전체, 2001 코스피200, 3003 코스닥150, 종목코드)
            issuer: 발행사 (00000 전체, 00003 한국투자증권, 00017 KB증권, 00005 미래에셋)
            price_min / price_max: 가격 이상 / 이하 (공백 = 제한 없음)
            volume_min / volume_max: 거래량 이상 / 이하 (공백 = 제한 없음)
            settle_type: 결제방법 (0 전체, 1 일반, 2 조기종료)
        Returns:
            output[]: 급변 종목 목록
        Example:
            >>> agent.elw.get_elw_quick_change_rank(sort_cls_code="3")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/ranking/quick-change",
            tr_id="FHPEW02870000",
            params={
                "FID_COND_MRKT_DIV_CODE": "W",
                "FID_COND_SCR_DIV_CODE": "20287",
                "FID_UNAS_INPUT_ISCD": underlying,
                "FID_INPUT_ISCD": issuer,
                "FID_MRKT_CLS_CODE": "A",
                "FID_INPUT_PRICE_1": price_min,
                "FID_INPUT_PRICE_2": price_max,
                "FID_INPUT_VOL_1": volume_min,
                "FID_INPUT_VOL_2": volume_max,
                "FID_HOUR_CLS_CODE": hour_cls_code,
                "FID_INPUT_HOUR_1": input_hour_1,
                "FID_INPUT_HOUR_2": input_hour_2,
                "FID_RANK_SORT_CLS_CODE": sort_cls_code,
                "FID_BLNG_CLS_CODE": settle_type,
            },
        )

    def get_elw_sensitivity_rank(
        self,
        sort_cls_code: str = "0",
        underlying: str = "000000",
        issuer: str = "00000",
        call_put: str = "0",
        price_min: str = "",
        price_max: str = "",
        volume_min: str = "",
        volume_max: str = "",
        remain_days_min: str = "",
        base_date: str = "",
        settle_type: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """ELW 민감도 순위 [국내주식-170]

        Args:
            sort_cls_code: 정렬 (0 이론가, 1 델타, 2 감마, 3 세타, 4 베가, 5 로,
                6 내재변동성, 7 90일변동성)
            underlying: 기초자산 (000000 전체, 2001 코스피200, 3003 코스닥150, 종목코드)
            issuer: 발행사 (00000 전체, 00003 한국투자증권, 00017 KB증권, 00005 미래에셋)
            call_put: 0 전체, 1 콜, 2 풋
            price_min / price_max: 가격 이상 / 이하 (공백 = 제한 없음)
            volume_min / volume_max: 거래량 이상 / 이하 (공백 = 제한 없음)
            remain_days_min: 잔존일수 이상
            base_date: 조회기준일 (YYYYMMDD, 공백 = 당일)
            settle_type: 결제방법 (0 전체, 1 일반, 2 조기종료)
        Returns:
            output[]: 민감도 순위별 ELW 목록
        Example:
            >>> agent.elw.get_elw_sensitivity_rank(sort_cls_code="1")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/ranking/sensitivity",
            tr_id="FHPEW02850000",
            params={
                "FID_COND_MRKT_DIV_CODE": "W",
                "FID_COND_SCR_DIV_CODE": "20285",
                "FID_UNAS_INPUT_ISCD": underlying,
                "FID_INPUT_ISCD": issuer,
                "FID_DIV_CLS_CODE": call_put,
                "FID_INPUT_PRICE_1": price_min,
                "FID_INPUT_PRICE_2": price_max,
                "FID_INPUT_VOL_1": volume_min,
                "FID_INPUT_VOL_2": volume_max,
                "FID_RANK_SORT_CLS_CODE": sort_cls_code,
                "FID_INPUT_RMNN_DYNU_1": remain_days_min,
                "FID_INPUT_DATE_1": base_date,
                "FID_BLNG_CLS_CODE": settle_type,
            },
        )

    def get_elw_updown_rate_rank(
        self,
        sort_cls_code: str = "0",
        maturity_period: str = "0",
        underlying: str = "000000",
        issuer: str = "00000",
        call_put: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """ELW 상승률순위 [국내주식-167]

        Args:
            sort_cls_code: 정렬 (0 상승율, 1 하락율, 2 시가대비상승율, 3 시가대비하락율,
                4 변동율)
            maturity_period: 잔존만기 (0 전체, 1 1개월이하, 2 1~2개월, 3 2~3개월,
                4 3~6개월, 5 6~9개월, 6 9~12개월, 7 12개월이상)
            underlying: 기초자산 (000000 전체, 2001 코스피200, 3003 코스닥150, 종목코드)
            issuer: 발행사 (00000 전체, 00003 한국투자증권, 00017 KB증권, 00005 미래에셋)
            call_put: 0 전체, 1 콜, 2 풋
        Returns:
            output[]: 등락률 순위별 ELW 목록
        Note:
            The workbook labels several of this API's request fields with the wrong
            names (copy/paste); the keys and their descriptions are followed, and
            the unused price/volume/date keys are sent blank as the sample does.
        Example:
            >>> agent.elw.get_elw_updown_rate_rank(sort_cls_code="1")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/ranking/updown-rate",
            tr_id="FHPEW02770000",
            params={
                "FID_COND_MRKT_DIV_CODE": "W",
                "FID_COND_SCR_DIV_CODE": "20277",
                "FID_UNAS_INPUT_ISCD": underlying,
                "FID_INPUT_ISCD": issuer,
                "FID_INPUT_RMNN_DYNU_1": maturity_period,
                "FID_DIV_CLS_CODE": call_put,
                "FID_INPUT_PRICE_1": "",
                "FID_INPUT_PRICE_2": "",
                "FID_INPUT_VOL_1": "",
                "FID_INPUT_VOL_2": "",
                "FID_INPUT_DATE_1": "",
                "FID_RANK_SORT_CLS_CODE": sort_cls_code,
                "FID_BLNG_CLS_CODE": "0",
                "FID_INPUT_DATE_2": "",
            },
        )

    def get_elw_volume_rank(
        self,
        sort_cls_code: str = "0",
        underlying: str = "000000",
        issuer: str = "00000",
        call_put: str = "0",
        remain_days: str = "",
        price_min: str = "",
        price_max: str = "",
        volume_min: str = "",
        volume_max: str = "",
        base_date: str = "",
        lp_issuer: str = "0000",
    ) -> Optional[Dict[str, Any]]:
        """ELW 거래량순위 [국내주식-168]

        Args:
            sort_cls_code: 정렬 (0 거래량순, 1 평균거래증가율, 2 평균거래회전율,
                3 거래금액순, 4 순매수잔량순, 5 순매도잔량순)
            underlying: 기초자산 (000000 전체, 2001 코스피200, 3003 코스닥150, 종목코드)
            issuer: 발행사 (00000 전체, 00003 한국투자증권, 00017 KB증권, 00005 미래에셋)
            call_put: 0 전체, 1 콜, 2 풋
            remain_days: 입력잔존일수 (공백 = 제한 없음)
            price_min / price_max: 거래가격 이상 / 이하 (공백 = 제한 없음)
            volume_min / volume_max: 거래량 이상 / 이하 (공백 = 제한 없음)
            base_date: 조회기준일 (YYYYMMDD, 기준가 조회기준, 공백 = 당일)
            lp_issuer: LP발행사 (0000 전체)
        Returns:
            output[]: 거래량 순위별 ELW 목록
        Example:
            >>> agent.elw.get_elw_volume_rank(sort_cls_code="3")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/ranking/volume-rank",
            tr_id="FHPEW02780000",
            params={
                "FID_COND_MRKT_DIV_CODE": "W",
                "FID_COND_SCR_DIV_CODE": "20278",
                "FID_UNAS_INPUT_ISCD": underlying,
                "FID_INPUT_ISCD": issuer,
                "FID_INPUT_RMNN_DYNU_1": remain_days,
                "FID_DIV_CLS_CODE": call_put,
                "FID_INPUT_PRICE_1": price_min,
                "FID_INPUT_PRICE_2": price_max,
                "FID_INPUT_VOL_1": volume_min,
                "FID_INPUT_VOL_2": volume_max,
                "FID_INPUT_DATE_1": base_date,
                "FID_RANK_SORT_CLS_CODE": sort_cls_code,
                "FID_BLNG_CLS_CODE": "0",
                "FID_INPUT_ISCD_2": lp_issuer,
                "FID_INPUT_DATE_2": "",
            },
        )
