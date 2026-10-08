"""장내채권 시세 API

[장내채권] 기본시세 (domestic-bond/v1/quotations/*). 모의투자 미지원.

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI

# FID_COND_MRKT_DIV_CODE for on-exchange bonds ("B: 장내").
_BOND_MARKET = "B"
# PRDT_TYPE_CD "Unique key(302)" used by the bond reference-data APIs.
_BOND_PRDT_TYPE = "302"


class BondPriceAPI(BaseAPI):
    """장내채권 시세"""

    def get_bond_asking_price(
        self, code: str, market: str = _BOND_MARKET
    ) -> Optional[Dict[str, Any]]:
        """장내채권현재가(호가) [국내주식-132]

        매도/매수 5호가와 잔량, 호가별 수익률을 조회한다.

        Args:
            code: 채권종목코드 (예: "KR2088012A16")
            market: 조건 시장 분류 코드 ("B": 장내)
        Returns:
            output: aspr_acpt_hour, bond_askp1~5, bond_bidp1~5, askp_rsqn1~5,
                bidp_rsqn1~5, total_askp_rsqn, total_bidp_rsqn
        Example:
            >>> agent.bond.get_bond_asking_price("KR2088012A16")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-bond/v1/quotations/inquire-asking-price",
            tr_id="FHKBJ773401C0",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_bond_price(
        self, code: str, market: str = _BOND_MARKET
    ) -> Optional[Dict[str, Any]]:
        """장내채권현재가(시세) [국내주식-200]

        현재가, 전일 대비, 시가/고가/저가와 각 수익률, 상/하한가를 조회한다.

        Args:
            code: 채권종목코드 (예: "KR2033022D33")
            market: 조건 시장 분류 코드 ("B": 장내)
        Returns:
            output: stnd_iscd, hts_kor_isnm, bond_prpr, bond_prdy_vrss,
                prdy_ctrt, acml_vol, bond_oprc, bond_hgpr, bond_lwpr
        Example:
            >>> agent.bond.get_bond_price("KR2033022D33")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-bond/v1/quotations/inquire-price",
            tr_id="FHKBJ773400C0",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_bond_ccnl(
        self, code: str, market: str = _BOND_MARKET
    ) -> Optional[Dict[str, Any]]:
        """장내채권현재가(체결) [국내주식-201]

        최근 체결 시각, 체결가, 전일 대비, 체결/누적 거래량을 조회한다.

        Args:
            code: 채권종목코드 (예: "KR2033022D33")
            market: 조건 시장 분류 코드 ("B": 장내)
        Returns:
            output: stck_cntg_hour, bond_prpr, bond_prdy_vrss, prdy_ctrt,
                cntg_vol, acml_vol
        Example:
            >>> agent.bond.get_bond_ccnl("KR2033022D33")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-bond/v1/quotations/inquire-ccnl",
            tr_id="FHKBJ773403C0",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_bond_daily_price(
        self, code: str, market: str = _BOND_MARKET
    ) -> Optional[Dict[str, Any]]:
        """장내채권현재가(일별) [국내주식-202]

        일자별 종가, 전일 대비, 시가/고가/저가, 누적 거래량을 조회한다.

        Args:
            code: 채권종목코드 (예: "KR2033022D33")
            market: 조건 시장 분류 코드 ("B": 장내)
        Returns:
            output: stck_bsop_date, bond_prpr, bond_prdy_vrss, prdy_ctrt,
                acml_vol, bond_oprc, bond_hgpr, bond_lwpr
        Example:
            >>> agent.bond.get_bond_daily_price("KR2033022D33")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-bond/v1/quotations/inquire-daily-price",
            tr_id="FHKBJ773404C0",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_bond_daily_chart(
        self, code: str, market: str = _BOND_MARKET
    ) -> Optional[Dict[str, Any]]:
        """장내채권 기간별시세(일) [국내주식-159]

        일봉(시가/고가/저가/종가/거래량)을 조회한다. 기간 인자는 없다.

        Args:
            code: 채권종목코드
            market: 조건 시장 분류 코드 ("B": 장내)
        Returns:
            output: list of stck_bsop_date, bond_oprc, bond_hgpr, bond_lwpr,
                bond_prpr, acml_vol
        Example:
            >>> agent.bond.get_bond_daily_chart("KR2033022D33")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-bond/v1/quotations/inquire-daily-itemchartprice",
            tr_id="FHKBJ773701C0",
            params={"FID_COND_MRKT_DIV_CODE": market, "FID_INPUT_ISCD": code},
        )

    def get_bond_avg_unit(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        code: str = "",
        prdt_type_cd: str = _BOND_PRDT_TYPE,
        vrfc_kind_cd: str = "00",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """장내채권 평균단가조회 [국내주식-158]

        민간 평가사(한국신용평가/한국채권평가/NICE/FnP)의 평가단가·수익률의
        평균을 조회한다. 연속조회가 있으면 ``max_pages``까지 이어 붙인다.

        Args:
            start_date: 조회시작일자 YYYYMMDD (기본: 오늘)
            end_date: 조회종료일자 YYYYMMDD (기본: 오늘)
            code: 채권종목코드 (공백: 전체)
            prdt_type_cd: 상품유형코드 (고정 "302")
            vrfc_kind_cd: 검증종류코드 (고정 "00")
            max_pages: 최대 페이지 수
        Returns:
            output1: evlu_dt, pdno, kis_unpr, kbp_unpr, nice_evlu_unpr,
                avg_evlu_unpr, avg_evlu_erng_rt
            output2: 평가금액(avg_evlu_amt 등), output3: 평가단위가격(avg_evlu_pric 등)
        Example:
            >>> agent.bond.get_bond_avg_unit("20260101", "20260131", "KR2033022D33")
        """
        today = datetime.now().strftime("%Y%m%d")
        return self._paginate(
            "/uapi/domestic-bond/v1/quotations/avg-unit",
            "CTPF2005R",
            {
                "INQR_STRT_DT": start_date or today,
                "INQR_END_DT": end_date or today,
                "PDNO": code,
                "PRDT_TYPE_CD": prdt_type_cd,
                "VRFC_KIND_CD": vrfc_kind_cd,
                "CTX_AREA_NK30": "",
                "CTX_AREA_FK100": "",
            },
            cursor=[
                ("CTX_AREA_NK30", "ctx_area_nk30"),
                ("CTX_AREA_FK100", "ctx_area_fk100"),
            ],
            output_keys=("output1", "output2", "output3"),
            max_pages=max_pages,
        )

    def get_bond_issue_info(
        self, code: str, prdt_type_cd: str = _BOND_PRDT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """장내채권 발행정보 [국내주식-156]

        발행기관, 액면가, 표면이율, 만기/상환 일자, 이자지급 정보, 신용등급을 조회한다.

        Args:
            code: 채권 종목번호 (예: "KR6449111CB8")
            prdt_type_cd: 상품유형코드 (고정 "302")
        Returns:
            output: pdno, prdt_name, issu_istt_name, papr, srfc_inrt, issu_dt,
                expd_dt, nxtm_int_dfrm_dt, kis_crdt_grad_text
        Example:
            >>> agent.bond.get_bond_issue_info("KR6449111CB8")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-bond/v1/quotations/issue-info",
            tr_id="CTPF1101R",
            params={"PDNO": code, "PRDT_TYPE_CD": prdt_type_cd},
        )

    def get_bond_info(
        self, code: str, prdt_type_cd: str = _BOND_PRDT_TYPE
    ) -> Optional[Dict[str, Any]]:
        """장내채권 기본조회 [국내주식-129]

        예탁원 기준 채권 기본정보(종목명, 이자지급방법, 발행/상환일, 예탁가능 여부 등)를 조회한다.

        Args:
            code: 상품번호(채권종목코드)
            prdt_type_cd: 상품유형코드 (고정 "302")
        Returns:
            output: pdno, ksd_bond_item_name, issu_dt, rdpt_dt,
                bond_int_dfrm_mthd_cd, ksd_rcvg_bond_srfc_inrt, dpsi_psbl_yn
        Example:
            >>> agent.bond.get_bond_info("KR6449111CB8")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-bond/v1/quotations/search-bond-info",
            tr_id="CTPF1114R",
            params={"PDNO": code, "PRDT_TYPE_CD": prdt_type_cd},
        )
