"""예탁원 정보 API

[국내주식] 종목정보 메뉴의 예탁원(ksdinfo/*) 일정: 증자, 배당, 매수청구, 합병/분할,
액면교체, 자본감소, 상장정보, 공모주청약, 실권주, 의무예치, 주주총회. 연속조회 커서는 CTS.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional, Tuple

from ..core.base_api import BaseAPI


def _today() -> date:
    """Today's date (module-level so tests can freeze it)."""
    return date.today()


def _range(from_date: Optional[str], to_date: Optional[str]) -> Tuple[str, str]:
    """Default window: today through 30 days ahead (schedules are forward looking)."""
    today = _today()
    return (
        from_date or today.strftime("%Y%m%d"),
        to_date or (today + timedelta(days=30)).strftime("%Y%m%d"),
    )


class StockKsdInfoAPI(BaseAPI):
    """예탁원 일정 정보 (ksdinfo/*)

    All methods are real-trading only and share the signature
    ``(from_date=None, to_date=None, code="", max_pages=10)``; the CTS cursor is
    followed automatically up to ``max_pages``. Dates are YYYYMMDD and default
    to today .. today+30 days. ``code`` blank means every stock.
    """

    def get_ksd_bonus_issue(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        code: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """예탁원정보(무상증자일정) [국내주식-144]

        예탁결제원이 제공하는 무상증자일정를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            from_date: 조회 시작일 YYYYMMDD (기본: 오늘)
            to_date: 조회 종료일 YYYYMMDD (기본: 오늘+30일)
            code: 종목코드 (공백이면 전체)
            max_pages: CTS 연속조회 최대 페이지 수

        Returns:
            output1[]: record_date(기준일), sht_cd, isin_name, fix_rate(확정배정율), right_dt(권리락일), list_date(상장일)

        Example:
            >>> agent.get_ksd_bonus_issue("20260101", "20261231")
        """
        fd, td = _range(from_date, to_date)
        return self._paginate(
            "/uapi/domestic-stock/v1/ksdinfo/bonus-issue",
            "HHKDB669101C0",
            {
                "CTS": "",
                "F_DT": fd,
                "T_DT": td,
                "SHT_CD": code,
            },
            cursor=[("CTS", "cts")],
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_ksd_cap_dcrs(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        code: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """예탁원정보(자본감소일정) [국내주식-149]

        예탁결제원이 제공하는 자본감소일정를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            from_date: 조회 시작일 YYYYMMDD (기본: 오늘)
            to_date: 조회 종료일 YYYYMMDD (기본: 오늘+30일)
            code: 종목코드 (공백이면 전체)
            max_pages: CTS 연속조회 최대 페이지 수

        Returns:
            output1[]: record_date, sht_cd, isin_name, reduce_cap_type(감자구분), reduce_cap_rate(감자배정율), list_dt

        Example:
            >>> agent.get_ksd_cap_dcrs("20260101", "20261231")
        """
        fd, td = _range(from_date, to_date)
        return self._paginate(
            "/uapi/domestic-stock/v1/ksdinfo/cap-dcrs",
            "HHKDB669106C0",
            {
                "CTS": "",
                "F_DT": fd,
                "T_DT": td,
                "SHT_CD": code,
            },
            cursor=[("CTS", "cts")],
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_ksd_dividend(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        code: str = "",
        kind: str = "0",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """예탁원정보(배당일정) [국내주식-145]

        예탁결제원이 제공하는 배당일정를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            from_date: 조회 시작일 YYYYMMDD (기본: 오늘)
            to_date: 조회 종료일 YYYYMMDD (기본: 오늘+30일)
            code: 종목코드 (공백이면 전체)
            kind: 조회구분 (0: 배당전체, 1: 결산배당, 2: 중간배당)
            max_pages: CTS 연속조회 최대 페이지 수

        Returns:
            output1[]: record_date, sht_cd, isin_name, divi_kind(배당종류), per_sto_divi_amt(현금배당금), divi_rate(현금배당률), divi_pay_dt(배당금지급일)

        Example:
            >>> agent.get_ksd_dividend("20260101", "20261231")
        """
        fd, td = _range(from_date, to_date)
        return self._paginate(
            "/uapi/domestic-stock/v1/ksdinfo/dividend",
            "HHKDB669102C0",
            {
                "CTS": "",
                "GB1": kind,
                "F_DT": fd,
                "T_DT": td,
                "SHT_CD": code,
                "HIGH_GB": "",
            },
            cursor=[("CTS", "cts")],
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_ksd_forfeit(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        code: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """예탁원정보(실권주일정) [국내주식-152]

        예탁결제원이 제공하는 실권주일정를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            from_date: 조회 시작일 YYYYMMDD (기본: 오늘)
            to_date: 조회 종료일 YYYYMMDD (기본: 오늘+30일)
            code: 종목코드 (공백이면 전체)
            max_pages: CTS 연속조회 최대 페이지 수

        Returns:
            output1[]: record_date, sht_cd, isin_name, subscr_dt(청약일), subscr_price(공모가), refund_dt, list_dt

        Example:
            >>> agent.get_ksd_forfeit("20260101", "20261231")
        """
        fd, td = _range(from_date, to_date)
        return self._paginate(
            "/uapi/domestic-stock/v1/ksdinfo/forfeit",
            "HHKDB669109C0",
            {
                "SHT_CD": code,
                "T_DT": td,
                "F_DT": fd,
                "CTS": "",
            },
            cursor=[("CTS", "cts")],
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_ksd_list_info(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        code: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """예탁원정보(상장정보일정) [국내주식-150]

        예탁결제원이 제공하는 상장정보일정를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            from_date: 조회 시작일 YYYYMMDD (기본: 오늘)
            to_date: 조회 종료일 YYYYMMDD (기본: 오늘+30일)
            code: 종목코드 (공백이면 전체)
            max_pages: CTS 연속조회 최대 페이지 수

        Returns:
            output1[]: list_dt(상장일), sht_cd, isin_name, issue_type(사유), issue_stk_qty(상장주식수), issue_price(발행가)

        Example:
            >>> agent.get_ksd_list_info("20260101", "20261231")
        """
        fd, td = _range(from_date, to_date)
        return self._paginate(
            "/uapi/domestic-stock/v1/ksdinfo/list-info",
            "HHKDB669107C0",
            {
                "SHT_CD": code,
                "T_DT": td,
                "F_DT": fd,
                "CTS": "",
            },
            cursor=[("CTS", "cts")],
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_ksd_mand_deposit(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        code: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """예탁원정보(의무예치일정) [국내주식-153]

        예탁결제원이 제공하는 의무예치일정를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            from_date: 조회 시작일 YYYYMMDD (기본: 오늘)
            to_date: 조회 종료일 YYYYMMDD (기본: 오늘+30일)
            code: 종목코드 (공백이면 전체)
            max_pages: CTS 연속조회 최대 페이지 수

        Returns:
            output1[]: sht_cd, isin_name, stk_qty(주식수), depo_date(예치일), depo_reason(사유)

        Example:
            >>> agent.get_ksd_mand_deposit("20260101", "20261231")
        """
        fd, td = _range(from_date, to_date)
        return self._paginate(
            "/uapi/domestic-stock/v1/ksdinfo/mand-deposit",
            "HHKDB669110C0",
            {
                "T_DT": td,
                "SHT_CD": code,
                "F_DT": fd,
                "CTS": "",
            },
            cursor=[("CTS", "cts")],
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_ksd_merger_split(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        code: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """예탁원정보(합병/분할일정) [국내주식-147]

        예탁결제원이 제공하는 합병/분할일정를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            from_date: 조회 시작일 YYYYMMDD (기본: 오늘)
            to_date: 조회 종료일 YYYYMMDD (기본: 오늘+30일)
            code: 종목코드 (공백이면 전체)
            max_pages: CTS 연속조회 최대 페이지 수

        Returns:
            output1[]: record_date, sht_cd, opp_cust_nm(피합병회사명), cust_nm(합병회사명), merge_type(합병사유), merge_rate(비율), list_dt

        Example:
            >>> agent.get_ksd_merger_split("20260101", "20261231")
        """
        fd, td = _range(from_date, to_date)
        return self._paginate(
            "/uapi/domestic-stock/v1/ksdinfo/merger-split",
            "HHKDB669104C0",
            {
                "CTS": "",
                "F_DT": fd,
                "T_DT": td,
                "SHT_CD": code,
            },
            cursor=[("CTS", "cts")],
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_ksd_paidin_capin(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        code: str = "",
        kind: str = "1",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """예탁원정보(유상증자일정) [국내주식-143]

        예탁결제원이 제공하는 유상증자일정를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            from_date: 조회 시작일 YYYYMMDD (기본: 오늘)
            to_date: 조회 종료일 YYYYMMDD (기본: 오늘+30일)
            code: 종목코드 (공백이면 전체)
            kind: 조회구분 (1: 청약일별, 2: 기준일별)
            max_pages: CTS 연속조회 최대 페이지 수

        Returns:
            output[]: record_date, sht_cd, isin_name, fix_rate(확정배정율), disc_rate(할인율), fix_price(발행예정가), sub_term(청약기간), list_date

        Example:
            >>> agent.get_ksd_paidin_capin("20260101", "20261231")
        """
        fd, td = _range(from_date, to_date)
        return self._paginate(
            "/uapi/domestic-stock/v1/ksdinfo/paidin-capin",
            "HHKDB669100C0",
            {
                "CTS": "",
                "GB1": kind,
                "F_DT": fd,
                "T_DT": td,
                "SHT_CD": code,
            },
            cursor=[("CTS", "cts")],
            output_keys=("output",),
            max_pages=max_pages,
        )

    def get_ksd_pub_offer(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        code: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """예탁원정보(공모주청약일정) [국내주식-151]

        예탁결제원이 제공하는 공모주청약일정를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            from_date: 조회 시작일 YYYYMMDD (기본: 오늘)
            to_date: 조회 종료일 YYYYMMDD (기본: 오늘+30일)
            code: 종목코드 (공백이면 전체)
            max_pages: CTS 연속조회 최대 페이지 수

        Returns:
            output1[]: record_date, sht_cd, isin_name, fix_subscr_pri(공모가), subscr_dt(청약기간), pay_dt, refund_dt, list_dt, lead_mgr(주간사)

        Example:
            >>> agent.get_ksd_pub_offer("20260101", "20261231")
        """
        fd, td = _range(from_date, to_date)
        return self._paginate(
            "/uapi/domestic-stock/v1/ksdinfo/pub-offer",
            "HHKDB669108C0",
            {
                "SHT_CD": code,
                "CTS": "",
                "F_DT": fd,
                "T_DT": td,
            },
            cursor=[("CTS", "cts")],
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_ksd_purreq(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        code: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """예탁원정보(주식매수청구일정) [국내주식-146]

        예탁결제원이 제공하는 주식매수청구일정를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            from_date: 조회 시작일 YYYYMMDD (기본: 오늘)
            to_date: 조회 종료일 YYYYMMDD (기본: 오늘+30일)
            code: 종목코드 (공백이면 전체)
            max_pages: CTS 연속조회 최대 페이지 수

        Returns:
            output1[]: record_date, sht_cd, isin_name, buy_req_rcpt_term(매수청구접수시한), buy_req_price(매수청구가격), buy_amt_pay_dt, get_meet_dt(주총일)

        Example:
            >>> agent.get_ksd_purreq("20260101", "20261231")
        """
        fd, td = _range(from_date, to_date)
        return self._paginate(
            "/uapi/domestic-stock/v1/ksdinfo/purreq",
            "HHKDB669103C0",
            {
                "SHT_CD": code,
                "T_DT": td,
                "F_DT": fd,
                "CTS": "",
            },
            cursor=[("CTS", "cts")],
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_ksd_rev_split(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        code: str = "",
        market: str = "0",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """예탁원정보(액면교체일정) [국내주식-148]

        예탁결제원이 제공하는 액면교체일정를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            from_date: 조회 시작일 YYYYMMDD (기본: 오늘)
            to_date: 조회 종료일 YYYYMMDD (기본: 오늘+30일)
            code: 종목코드 (공백이면 전체)
            market: 시장구분 (0: 전체, 1: 코스피, 2: 코스닥)
            max_pages: CTS 연속조회 최대 페이지 수

        Returns:
            output1[]: record_date, sht_cd, isin_name, inter_bf_face_amt(변경전액면가), inter_af_face_amt(변경후액면가), td_stop_dt, list_dt

        Example:
            >>> agent.get_ksd_rev_split("20260101", "20261231")
        """
        fd, td = _range(from_date, to_date)
        return self._paginate(
            "/uapi/domestic-stock/v1/ksdinfo/rev-split",
            "HHKDB669105C0",
            {
                "SHT_CD": code,
                "CTS": "",
                "F_DT": fd,
                "T_DT": td,
                "MARKET_GB": market,
            },
            cursor=[("CTS", "cts")],
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_ksd_sharehld_meet(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        code: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """예탁원정보(주주총회일정) [국내주식-154]

        예탁결제원이 제공하는 주주총회일정를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            from_date: 조회 시작일 YYYYMMDD (기본: 오늘)
            to_date: 조회 종료일 YYYYMMDD (기본: 오늘+30일)
            code: 종목코드 (공백이면 전체)
            max_pages: CTS 연속조회 최대 페이지 수

        Returns:
            output1[]: record_date, sht_cd, isin_name, gen_meet_dt(주총일자), gen_meet_type(주총사유), agenda(주총의안), vote_tot_qty(의결권주식총수)

        Example:
            >>> agent.get_ksd_sharehld_meet("20260101", "20261231")
        """
        fd, td = _range(from_date, to_date)
        return self._paginate(
            "/uapi/domestic-stock/v1/ksdinfo/sharehld-meet",
            "HHKDB669111C0",
            {
                "CTS": "",
                "F_DT": fd,
                "T_DT": td,
                "SHT_CD": code,
            },
            cursor=[("CTS", "cts")],
            output_keys=("output1",),
            max_pages=max_pages,
        )
