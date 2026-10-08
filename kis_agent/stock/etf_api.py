"""ETF/ETN API

ETF/ETN 시세 (etfetn/*): 현재가, 구성종목시세, NAV 비교추이(종목/일/분).

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI


def _today() -> date:
    """Today's date (module-level so tests can freeze it)."""
    return date.today()


class StockEtfAPI(BaseAPI):
    """ETF/ETN 시세 (etfetn/*)"""

    def get_etf_price(self, code: str, market: str = "J") -> Optional[Dict[str, Any]]:
        """ETF/ETN 현재가 [v1_국내주식-068]

        ETF/ETN의 현재가와 NAV·추적오차율·순자산총액 등 ETF 고유 지표를 조회합니다. 실전투자 전용.

        Args:
            code: 종목코드 (예: "069500")
            market: 시장 분류 코드 (J)

        Returns:
            output: stck_prpr(현재가), prdy_vrss(전일대비), nav(NAV), nav_prdy_vrss,
            trc_errt(추적오차율), etf_ntas_ttam(순자산총액), acml_vol(누적거래량)

        Example:
            >>> agent.get_etf_price("069500")
        """
        return self._make_request_dict(
            endpoint="/uapi/etfetn/v1/quotations/inquire-price",
            tr_id="FHPST02400000",
            params={"fid_input_iscd": code, "fid_cond_mrkt_div_code": market},
        )

    def get_etf_component_stock_price(
        self, code: str, market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """ETF 구성종목시세 [국내주식-073]

        ETF의 요약(output1)과 구성종목별 시세·비중(output2)을 조회합니다. 실전투자 전용.

        Args:
            code: ETF 종목코드 (예: "069500")
            market: 시장 분류 코드 (J)

        Returns:
            output1: ETF 요약(현재가, NAV, 순자산총액 등);
            output2[]: stck_shrn_iscd, hts_kor_isnm, stck_prpr, prdy_ctrt,
            etf_cnfg_issu_rlim(구성종목비중), etf_vltn_amt(평가금액)

        Example:
            >>> agent.get_etf_component_stock_price("069500")
        """
        return self._make_request_dict(
            endpoint="/uapi/etfetn/v1/quotations/inquire-component-stock-price",
            tr_id="FHKST121600C0",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_COND_SCR_DIV_CODE": "11216",
            },
        )

    def get_etf_nav_comparison_trend(
        self, code: str, market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """NAV 비교추이(종목) [v1_국내주식-069]

        ETF/ETN의 시세(output1)와 NAV(output2)를 함께 조회합니다. 실전투자 전용.

        Args:
            code: 종목코드 (예: "069500")
            market: 시장 분류 코드 (J)

        Returns:
            output1: stck_prpr, prdy_vrss, acml_vol 등 시세; output2: nav, nav_prdy_vrss(ctrt), prdy_clpr_nav, oprc/hprc/lprc_nav

        Example:
            >>> agent.get_etf_nav_comparison_trend("069500")
        """
        return self._make_request_dict(
            endpoint="/uapi/etfetn/v1/quotations/nav-comparison-trend",
            tr_id="FHPST02440000",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_etf_nav_comparison_daily_trend(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        market: str = "J",
    ) -> Optional[Dict[str, Any]]:
        """NAV 비교추이(일) [v1_국내주식-071]

        ETF/ETN의 일자별 종가·NAV·괴리율 추이를 조회합니다. 실전투자 전용.

        Args:
            code: 종목코드 (6자리)
            start_date: 조회 시작일 YYYYMMDD (기본: 호출일 기준 30일 전)
            end_date: 조회 종료일 YYYYMMDD (기본: 호출일)
            market: 시장 분류 코드 (J)

        Returns:
            output[]: stck_bsop_date, stck_clpr(종가), nav, dprt(괴리율), nav_vrss_prpr(NAV 대비 현재가)

        Example:
            >>> agent.get_etf_nav_comparison_daily_trend("069500")
        """
        today = _today()
        return self._make_request_dict(
            endpoint="/uapi/etfetn/v1/quotations/nav-comparison-daily-trend",
            tr_id="FHPST02440200",
            params={
                "fid_cond_mrkt_div_code": market,
                "fid_input_iscd": code,
                "fid_input_date_1": start_date
                or (today - timedelta(days=30)).strftime("%Y%m%d"),
                "fid_input_date_2": end_date or today.strftime("%Y%m%d"),
            },
        )

    def get_etf_nav_comparison_time_trend(
        self, code: str, interval_seconds: int = 60
    ) -> Optional[Dict[str, Any]]:
        """NAV 비교추이(분) [v1_국내주식-070]

        ETF/ETN의 분 단위 현재가·NAV·괴리율 추이를 조회합니다. 실전투자 전용.

        Args:
            code: 종목코드 (예: "069500")
            interval_seconds: 시간 구분(초). 60=1분, 180=3분, ..., 7200=120분

        Returns:
            output[]: bsop_hour(시각), stck_prpr, nav, dprt(괴리율), nav_vrss_prpr, cntg_vol

        Example:
            >>> agent.get_etf_nav_comparison_time_trend("069500", 180)
        """
        return self._make_request_dict(
            endpoint="/uapi/etfetn/v1/quotations/nav-comparison-time-trend",
            tr_id="FHPST02440100",
            params={
                "fid_hour_cls_code": str(interval_seconds),
                "fid_cond_mrkt_div_code": "E",
                "fid_input_iscd": code,
            },
        )
