"""국내주식 분봉·시간외 API

당일분봉, 장마감 예상체결가, 시간외 시간별체결 등 기본시세 보강.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI


def _now() -> datetime:
    """Current time (module-level so tests can freeze it)."""
    return datetime.now()


class StockChartAPI(BaseAPI):
    """국내주식 분봉·시간외 시세"""

    def get_today_minute_chart(
        self,
        code: str,
        hour: Optional[str] = None,
        include_past: str = "Y",
        market: str = "J",
    ) -> Optional[Dict[str, Any]]:
        """주식당일분봉조회 [v1_국내주식-022]

        당일 분봉(최대 30건)을 ``hour`` 이전 시각부터 거슬러 조회합니다. 모의투자 지원.
        특정 일자의 분봉은 ``get_daily_minute_price`` 를 사용하세요.

        Args:
            code: 종목코드 (예: "005930")
            hour: 조회 기준 시각 HHMMSS (기본: 호출 시각)
            include_past: 과거 데이터 포함 여부 (Y/N)
            market: 시장 분류 코드 (J: KRX, NX: NXT, UN: 통합)

        Returns:
            output1: 현재가·전일대비 등 요약; output2[]: stck_bsop_date, stck_cntg_hour,
            stck_prpr, stck_oprc, stck_hgpr, stck_lwpr, cntg_vol, acml_tr_pbmn

        Example:
            >>> agent.get_today_minute_chart("005930", "100000")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
            tr_id="FHKST03010200",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": hour or _now().strftime("%H%M%S"),
                "FID_PW_DATA_INCU_YN": include_past,
                "FID_ETC_CLS_CODE": "",
            },
        )

    def get_exp_closing_price(
        self,
        sort: str = "0",
        scope: str = "0000",
        belong: str = "0",
        market: str = "J",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 장마감 예상체결가 [국내주식-120]

        장마감 동시호가 구간의 예상체결가 순위를 조회합니다. 실전투자 전용.

        Args:
            sort: 순위 정렬 (0: 전체, 1: 상한가마감예상, 2: 하한가마감예상,
                3: 직전대비 상승률 상위, 4: 직전대비 하락률 상위)
            scope: 입력 종목코드 (0000 전체, 0001 거래소, 1001 코스닥,
                2001 코스피200, 4001 KRX100)
            belong: 소속 구분 (0: 전체, 1: 종가범위연장)
            market: 시장 분류 코드 (J)

        Returns:
            output1[]: stck_shrn_iscd, hts_kor_isnm, stck_prpr(예상체결가),
            prdy_ctrt, sdpr_vrss_prpr_rate(기준가 대비 비율), cntg_vol

        Example:
            >>> agent.get_exp_closing_price(sort="1")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/exp-closing-price",
            tr_id="FHKST117300C0",
            params={
                "FID_RANK_SORT_CLS_CODE": sort,
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_COND_SCR_DIV_CODE": "11173",
                "FID_INPUT_ISCD": scope,
                "FID_BLNG_CLS_CODE": belong,
            },
        )

    def get_overtime_conclusion_by_time(
        self, code: str, hour_cls: str = "1", market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """주식현재가 시간외시간별체결 [v1_국내주식-025]

        시간외 단일가 시세(output1)와 시간별 체결 내역(output2)을 조회합니다. 모의투자 지원.

        Args:
            code: 종목코드 (6자리, ETN은 Q로 시작, 예: Q500001)
            hour_cls: 시간 구분 코드 (1: 시간외)
            market: 시장 분류 코드 (J: 주식, ETF, ETN)

        Returns:
            output1: ovtm_untp_prpr(시간외 단일가), ovtm_untp_vol 등;
            output2[]: stck_cntg_hour, stck_prpr, askp, bidp, acml_vol, cntg_vol

        Example:
            >>> agent.get_overtime_conclusion_by_time("005930")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-time-overtimeconclusion",
            tr_id="FHPST02310000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_HOUR_CLS_CODE": hour_cls,
            },
        )
