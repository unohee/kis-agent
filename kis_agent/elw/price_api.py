"""ELW 시세 API

[국내주식] ELW 시세 메뉴의 시세·추이 조회 (elw/v1/quotations/*).

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.

Every ELW API is unsupported on the paper-trading server; calling one in paper
mode raises ``PaperTradingNotSupportedError`` from the client.
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI

# Every request key of ELW 종목검색 (cond-search), with the "no condition" value.
# The workbook marks all of them required, so all are always sent.
_COND_SEARCH_BLANK_KEYS = (
    "FID_RANK_SORT_CLS_CODE_2",
    "FID_INPUT_CNT_2",
    "FID_RANK_SORT_CLS_CODE_3",
    "FID_INPUT_CNT_3",
    "FID_TRGT_CLS_CODE",
    "FID_UNAS_INPUT_ISCD",
    "FID_INPUT_ISCD_2",
    "FID_INPUT_RMNN_DYNU_1",
    "FID_INPUT_RMNN_DYNU_2",
    "FID_PRPR_CNT1",
    "FID_PRPR_CNT2",
    "FID_RSFL_RATE1",
    "FID_RSFL_RATE2",
    "FID_VOL1",
    "FID_VOL2",
    "FID_APLY_RANG_PRC_1",
    "FID_APLY_RANG_PRC_2",
    "FID_LVRG_VAL1",
    "FID_LVRG_VAL2",
    "FID_VOL3",
    "FID_VOL4",
    "FID_INTS_VLTL1",
    "FID_INTS_VLTL2",
    "FID_PRMM_VAL1",
    "FID_PRMM_VAL2",
    "FID_GEAR1",
    "FID_GEAR2",
    "FID_PRLS_QRYR_RATE1",
    "FID_PRLS_QRYR_RATE2",
    "FID_DELTA1",
    "FID_DELTA2",
    "FID_ACPR1",
    "FID_ACPR2",
    "FID_STCK_CNVR_RATE1",
    "FID_STCK_CNVR_RATE2",
    "FID_PRIT1",
    "FID_PRIT2",
    "FID_CFP1",
    "FID_CFP2",
    "FID_INPUT_NMIX_PRICE_1",
    "FID_INPUT_NMIX_PRICE_2",
    "FID_EGEA_VAL1",
    "FID_EGEA_VAL2",
    "FID_INPUT_DVDN_ERT",
    "FID_INPUT_HIST_VLTL",
    "FID_THETA1",
    "FID_THETA2",
)


class ElwPriceAPI(BaseAPI):
    """ELW 시세·추이 조회"""

    # ------------------------------------------------------------------ search
    def get_elw_compare_stocks(self, code: str) -> Optional[Dict[str, Any]]:
        """ELW 비교대상종목조회 [국내주식-183]

        Lists the ELWs that can be compared with the given ELW/underlying.

        Args:
            code: 종목코드 (ELW 코드 또는 기초자산 종목코드, 예: "005930")
        Returns:
            output[]: elw_shrn_iscd(ELW단축종목코드), elw_kor_isnm(ELW한글종목명)
        Example:
            >>> agent.elw.get_elw_compare_stocks("005930")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/compare-stocks",
            tr_id="FHKEW151701C0",
            params={"FID_COND_SCR_DIV_CODE": "11517", "FID_INPUT_ISCD": code},
        )

    def get_elw_cond_search(
        self,
        rank_sort_cls_code: str = "0",
        input_cnt_1: str = "1",
        issuer_code: str = "00000",
        market_cls_code: str = "A",
        listing_period: str = "0",
        maturity_period: str = "0",
        strike_cls_code: str = "0",
        div_cls_code: str = "0",
        filters: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """ELW 종목검색 [국내주식-166]

        HTS [0291] ELW 종목검색. Each condition is a FID_* request key; the
        common ones are named arguments and every other key of the official spec
        (all default to blank = no condition) can be set through ``filters``.

        Args:
            rank_sort_cls_code: 정렬1 (0 정렬안함, 1 종목코드, 2 현재가, 3 대비율,
                4 거래량, 5 행사가격, 6 전환비율, 7 상장일, 8 만기일, 9 잔존일수,
                10 레버리지)
            input_cnt_1: 정렬1 기준 (1 상위, 2 하위)
            issuer_code: 발행사 종목코드 (00000 전체)
            market_cls_code: 권리유형 (A 전체, CO 콜, PO 풋)
            listing_period: 상장일 (0 전체, 1 금일, 2 7일이하, 3 8~30일, 4 31~90일)
            maturity_period: 만기일 (0 전체, 1 1개월, 2 1~2, 3 2~3, 4 3~6, 5 6~9,
                6 9~12, 7 12이상)
            strike_cls_code: 행사가 (0 전체, 1 >=)
            div_cls_code: 0 전체, 1 일반, 2 조기종료
            filters: extra FID_* request keys (e.g. {"FID_DELTA1": "0.3",
                "FID_UNAS_INPUT_ISCD": "005930"}). Unknown keys raise ValueError.
        Returns:
            output1[]: bond_shrn_iscd(단축코드), hts_kor_isnm(종목명), elw_prpr(현재가),
            prdy_ctrt(전일대비율), acpr(행사가), hts_rmnn_dynu(잔존일수), delta_val(델타)
        Example:
            >>> agent.elw.get_elw_cond_search(filters={"FID_UNAS_INPUT_ISCD": "005930"})
        """
        params: Dict[str, Any] = {
            "FID_COND_MRKT_DIV_CODE": "W",
            "FID_COND_SCR_DIV_CODE": "11510",
            "FID_RANK_SORT_CLS_CODE": rank_sort_cls_code,
            "FID_INPUT_CNT_1": input_cnt_1,
            "FID_INPUT_ISCD": issuer_code,
            "FID_MRKT_CLS_CODE": market_cls_code,
            "FID_INPUT_DATE_1": listing_period,
            "FID_INPUT_DATE_2": maturity_period,
            "FID_ETC_CLS_CODE": strike_cls_code,
            "FID_DIV_CLS_CODE": div_cls_code,
        }
        params.update(dict.fromkeys(_COND_SEARCH_BLANK_KEYS, ""))
        for key, value in (filters or {}).items():
            if key not in params:
                raise ValueError(f"unknown ELW cond-search filter: {key}")
            params[key] = value
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/cond-search",
            tr_id="FHKEW15100000",
            params=params,
        )

    def get_elw_expiration_stocks(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        call_put: str = "2",
        underlying: str = "000000",
        issuer: str = "00000",
        settle_type: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """ELW 만기예정/만기종목 [국내주식-184]

        Args:
            start_date: 만기 조회 시작일 (YYYYMMDD, 기본 오늘)
            end_date: 만기 조회 종료일 (YYYYMMDD, 기본 오늘+7일)
            call_put: 0 콜, 1 풋, 2 전체
            underlying: 기초자산 (000000 전체, 2001 KOSPI200, 종목코드)
            issuer: 발행회사 (00000 전체, 00003 한국투자증권, 00017 KB증권 ...)
            settle_type: 결제방법 (0 전체, 1 일반, 2 조기종료)
        Returns:
            output1[]: elw_shrn_iscd, elw_kor_isnm, unas_isnm, acpr, stck_last_tr_date,
            total_rdmp_amt(총상환금액), stlm_date(결제일자)
        Example:
            >>> agent.elw.get_elw_expiration_stocks("20260401", "20260410")
        """
        today = date.today()
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/expiration-stocks",
            tr_id="FHKEW154700C0",
            params={
                "FID_COND_MRKT_DIV_CODE": "W",
                "FID_COND_SCR_DIV_CODE": "11547",
                "FID_INPUT_DATE_1": start_date or today.strftime("%Y%m%d"),
                "FID_INPUT_DATE_2": end_date
                or (today + timedelta(days=7)).strftime("%Y%m%d"),
                "FID_DIV_CLS_CODE": call_put,
                "FID_ETC_CLS_CODE": "",
                "FID_UNAS_INPUT_ISCD": underlying,
                "FID_INPUT_ISCD_2": issuer,
                "FID_BLNG_CLS_CODE": settle_type,
                "FID_INPUT_OPTION_1": "",
            },
        )

    def get_elw_newly_listed(
        self,
        listing_date: Optional[str] = None,
        call_put: str = "02",
        underlying: str = "000000",
        issuer: str = "00003",
        settle_type: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """ELW 신규상장종목 [국내주식-181]

        Args:
            listing_date: 상장일 기준 (YYYYMMDD, 기본 오늘)
            call_put: 02 전체, 00 콜, 01 풋
            underlying: 기초자산 (000000 전체, 2001 코스피200, 3003 코스닥150, 종목코드)
            issuer: 발행사 (00003 한국투자증권, 00017 KB증권, 00005 미래에셋)
            settle_type: 결제방법 (0 전체, 1 일반, 2 조기종료)
        Returns:
            output[]: stck_lstn_date, elw_shrn_iscd, elw_kor_isnm, unas_isnm,
            pblc_co_name(발행회사), acpr(행사가), stck_last_tr_date
        Note:
            The request key is spelled ``FID_BLNC_CLS_CODE`` in the workbook (the
            examples_llm sample says ``FID_BLNG_CLS_CODE``); the workbook is followed.
        Example:
            >>> agent.elw.get_elw_newly_listed("20260401")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/newly-listed",
            tr_id="FHKEW154800C0",
            params={
                "FID_COND_MRKT_DIV_CODE": "W",
                "FID_COND_SCR_DIV_CODE": "11548",
                "FID_DIV_CLS_CODE": call_put,
                "FID_UNAS_INPUT_ISCD": underlying,
                "FID_INPUT_ISCD_2": issuer,
                "FID_INPUT_DATE_1": listing_date or date.today().strftime("%Y%m%d"),
                "FID_BLNC_CLS_CODE": settle_type,
            },
        )

    # --------------------------------------------------------------- underlying
    def get_elw_udrl_asset_list(
        self, sort_cls_code: str = "0", issuer: str = "00000"
    ) -> Optional[Dict[str, Any]]:
        """ELW 기초자산 목록조회 [국내주식-185]

        Args:
            sort_cls_code: 정렬 (0 종목명순, 1 콜발행종목순, 2 풋발행종목순,
                3 전일대비 상승율순, 4 하락율순, 5 현재가 크기순, 6 종목코드순)
            issuer: 발행사 (00000 전체, 00003 한국투자증권, 00017 KB증권, 00005 미래에셋)
        Returns:
            output[]: unas_shrn_iscd(기초자산코드), unas_isnm, unas_prpr, unas_prdy_vrss, unas_prdy_ctrt
        Example:
            >>> agent.elw.get_elw_udrl_asset_list()
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/udrl-asset-list",
            tr_id="FHKEW154100C0",
            params={
                "FID_COND_SCR_DIV_CODE": "11541",
                "FID_RANK_SORT_CLS_CODE": sort_cls_code,
                "FID_INPUT_ISCD": issuer,
            },
        )

    def get_elw_udrl_asset_price(
        self,
        underlying: str,
        market_cls_code: str = "A",
        issuer: str = "00000",
        prev_volume: str = "",
        exclude_untradable: str = "0",
        price_min: str = "",
        price_max: str = "",
        volume_min: str = "",
        volume_max: str = "",
        remain_days_min: str = "",
        remain_days_max: str = "",
        option_status: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """ELW 기초자산별 종목시세 [국내주식-186]

        Args:
            underlying: 기초자산 종목코드 (예: "005930")
            market_cls_code: A 전체, C 콜, P 풋
            issuer: 발행사 (00000 전체, 00003 한국투자증권, 00017 KB증권, 00005 미래에셋)
            prev_volume: 전일거래량 (정수량 미만, 공백 = 제한 없음)
            exclude_untradable: 거래불가종목 제외 (0 미체크, 1 체크)
            price_min / price_max: 가격 이상 / 이하
            volume_min / volume_max: 거래량 이상 / 이하
            remain_days_min / remain_days_max: 잔존일 이상 / 이하
            option_status: 옵션상태 (0 없음, 1 ATM, 2 ITM, 3 OTM)
        Returns:
            output[]: elw_shrn_iscd, hts_kor_isnm, elw_prpr, prdy_ctrt, acpr, hts_rmnn_dynu,
            hts_ints_vltl, lvrg_val, gear, delta_val, lp_hvol
        Example:
            >>> agent.elw.get_elw_udrl_asset_price("005930")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/udrl-asset-price",
            tr_id="FHKEW154101C0",
            params={
                "FID_COND_MRKT_DIV_CODE": "W",
                "FID_COND_SCR_DIV_CODE": "11541",
                "FID_MRKT_CLS_CODE": market_cls_code,
                "FID_INPUT_ISCD": issuer,
                "FID_UNAS_INPUT_ISCD": underlying,
                "FID_VOL_CNT": prev_volume,
                "FID_TRGT_EXLS_CLS_CODE": exclude_untradable,
                "FID_INPUT_PRICE_1": price_min,
                "FID_INPUT_PRICE_2": price_max,
                "FID_INPUT_VOL_1": volume_min,
                "FID_INPUT_VOL_2": volume_max,
                "FID_INPUT_RMNN_DYNU_1": remain_days_min,
                "FID_INPUT_RMNN_DYNU_2": remain_days_max,
                "FID_OPTION": option_status,
                "FID_INPUT_OPTION_1": "",
                "FID_INPUT_OPTION_2": "",
            },
        )

    # ------------------------------------------------------------------- trends
    def get_elw_indicator_trend_ccnl(
        self, code: str, market: str = "W"
    ) -> Optional[Dict[str, Any]]:
        """ELW 투자지표추이(체결) [국내주식-172]

        Args:
            code: ELW 종목코드 (예: "58J297")
            market: 시장구분 (W)
        Returns:
            output[]: stck_cntg_hour, elw_prpr, lvrg_val(레버리지), gear(기어링),
            tmvl_val(시간가치), invl_val(내재가치), prit(패리티), apprch_rate(접근도)
        Example:
            >>> agent.elw.get_elw_indicator_trend_ccnl("58J297")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/indicator-trend-ccnl",
            tr_id="FHPEW02740100",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_elw_indicator_trend_daily(
        self, code: str, market: str = "W"
    ) -> Optional[Dict[str, Any]]:
        """ELW 투자지표추이(일별) [국내주식-173]

        Args:
            code: ELW 종목코드 (예: "57K281")
            market: 시장구분 (W)
        Returns:
            output[]: stck_bsop_date, elw_prpr, elw_oprc/hgpr/lwpr, lvrg_val, gear,
            tmvl_val, invl_val, prit, apprch_rate
        Example:
            >>> agent.elw.get_elw_indicator_trend_daily("57K281")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/indicator-trend-daily",
            tr_id="FHPEW02740200",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_elw_indicator_trend_minute(
        self,
        code: str,
        hour_cls_code: str = "60",
        include_past: str = "N",
        market: str = "W",
    ) -> Optional[Dict[str, Any]]:
        """ELW 투자지표추이(분별) [국내주식-174]

        Args:
            code: ELW 종목코드 (예: "58J297")
            hour_cls_code: 시간구분 초 단위 (60 1분, 180 3분, 300 5분, 600 10분,
                1800 30분, 3600 60분)
            include_past: 과거데이터 포함 여부 (N 미포함, Y 포함)
            market: 시장구분 (W)
        Returns:
            output[]: stck_bsop_date, stck_cntg_hour, elw_prpr, lvrg_val, gear,
            prmm_val(프리미엄), invl_val, prit, acml_vol, cntg_vol
        Example:
            >>> agent.elw.get_elw_indicator_trend_minute("58J297", "300")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/indicator-trend-minute",
            tr_id="FHPEW02740300",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_HOUR_CLS_CODE": hour_cls_code,
                "FID_PW_DATA_INCU_YN": include_past,
            },
        )

    def get_elw_lp_trade_trend(
        self, code: str, market: str = "W"
    ) -> Optional[Dict[str, Any]]:
        """ELW LP매매추이 [국내주식-182]

        Args:
            code: ELW 종목코드 (예: "52K577")
            market: 시장구분 (W)
        Returns:
            output1: 종목 지표 (elw_prpr, acml_vol, prit, lvrg_val, gear, acpr ...)
            output2[]: 일별 LP 매매 (stck_bsop_date, lp_seln_qty, lp_shnu_qty,
            lp_hvol(LP보유량), lp_hldn_rate(LP보유비율))
        Note:
            The workbook's paper-trading cell for this API is blank (not marked
            unsupported); the paper-mode behaviour is therefore left to the server.
        Example:
            >>> agent.elw.get_elw_lp_trade_trend("52K577")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/lp-trade-trend",
            tr_id="FHPEW03760000",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_elw_sensitivity_trend_ccnl(
        self, code: str, market: str = "W"
    ) -> Optional[Dict[str, Any]]:
        """ELW 민감도 추이(체결) [국내주식-175]

        Args:
            code: ELW 종목코드 (예: "58J297")
            market: 시장구분 (W)
        Returns:
            output[]: stck_cntg_hour, elw_prpr, hts_thpr(이론가), delta_val, gama,
            theta, vega, rho
        Example:
            >>> agent.elw.get_elw_sensitivity_trend_ccnl("58J297")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/sensitivity-trend-ccnl",
            tr_id="FHPEW02830100",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_elw_sensitivity_trend_daily(
        self, code: str, market: str = "W"
    ) -> Optional[Dict[str, Any]]:
        """ELW 민감도 추이(일별) [국내주식-176]

        Args:
            code: ELW 종목코드 (예: "58J438")
            market: 시장구분 (W)
        Returns:
            output[]: stck_bsop_date, elw_prpr, hts_thpr, delta_val, gama, theta,
            vega, rho
        Example:
            >>> agent.elw.get_elw_sensitivity_trend_daily("58J438")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/sensitivity-trend-daily",
            tr_id="FHPEW02830200",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_elw_volatility_trend_ccnl(
        self, code: str, market: str = "W"
    ) -> Optional[Dict[str, Any]]:
        """ELW 변동성추이(체결) [국내주식-177]

        Args:
            code: ELW 종목코드 (예: "58J297")
            market: 시장구분 (W)
        Returns:
            output[]: stck_cntg_hour, elw_prpr, bidp/askp(호가), acml_vol, hts_ints_vltl(내재변동성)
        Example:
            >>> agent.elw.get_elw_volatility_trend_ccnl("58J297")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/volatility-trend-ccnl",
            tr_id="FHPEW02840100",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_elw_volatility_trend_daily(
        self, code: str, market: str = "W"
    ) -> Optional[Dict[str, Any]]:
        """ELW 변동성 추이(일별) [국내주식-178]

        Args:
            code: ELW 종목코드 (예: "58J297")
            market: 시장구분 (W)
        Returns:
            output[]: stck_bsop_date, elw_prpr, elw_oprc/hgpr/lwpr, acml_vol, hts_ints_vltl(내재변동성),
            d10/d20/d30/d60/d90_hist_vltl(역사적 변동성)
        Example:
            >>> agent.elw.get_elw_volatility_trend_daily("58J297")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/volatility-trend-daily",
            tr_id="FHPEW02840200",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_elw_volatility_trend_minute(
        self,
        code: str,
        hour_cls_code: str = "60",
        include_past: str = "N",
        market: str = "W",
    ) -> Optional[Dict[str, Any]]:
        """ELW 변동성 추이(분별) [국내주식-179]

        Args:
            code: ELW 종목코드 (예: "58J297")
            hour_cls_code: 시간구분 초 단위 (60 1분, 180 3분, 300 5분, 600 10분,
                1800 30분, 3600 60분)
            include_past: 과거데이터 포함 여부 (N 미포함, Y 포함)
            market: 시장구분 (W)
        Returns:
            output[]: stck_bsop_date, stck_cntg_hour, stck_prpr, elw_oprc/hgpr/lwpr,
            hts_ints_vltl(내재변동성), hist_vltl(역사적 변동성)
        Example:
            >>> agent.elw.get_elw_volatility_trend_minute("58J297", "300")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/volatility-trend-minute",
            tr_id="FHPEW02840300",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_HOUR_CLS_CODE": hour_cls_code,
                "FID_PW_DATA_INCU_YN": include_past,
            },
        )

    def get_elw_volatility_trend_tick(
        self, code: str, market: str = "W"
    ) -> Optional[Dict[str, Any]]:
        """ELW 변동성 추이(틱) [국내주식-180]

        Args:
            code: ELW 종목코드 (예: "58J297")
            market: 시장구분 (W)
        Returns:
            output[]: bsop_date, stck_cntg_hour, elw_prpr, hts_ints_vltl(내재변동성)
        Example:
            >>> agent.elw.get_elw_volatility_trend_tick("58J297")
        """
        return self._make_request_dict(
            endpoint="/uapi/elw/v1/quotations/volatility-trend-tick",
            tr_id="FHPEW02840400",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )
