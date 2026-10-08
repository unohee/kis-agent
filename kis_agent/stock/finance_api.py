"""국내주식 종목정보·재무 API

[국내주식] 종목정보 메뉴: 상품기본조회, 투자의견, 추정실적, 당사 신용/대주 가능종목,
재무제표(대차대조표·손익계산서·수익성/안정성/성장성/기타 비율).

Implemented per the official KIS spec (workbook + open-trading-api
examples_llm); verify with ``scripts/spec_conformance/check.py``.
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI


def _today() -> date:
    """Today's date (module-level so tests can freeze it)."""
    return date.today()


class StockFinanceAPI(BaseAPI):
    """국내주식 종목정보·재무"""

    def get_balance_sheet(
        self, code: str, period: str = "0", market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """국내주식 대차대조표 [v1_국내주식-078]

        종목의 결산기별 재무 데이터를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            code: 종목코드 (6자리, 예: "005930")
            period: 분류 구분 코드 (0: 년, 1: 분기)
            market: 시장 분류 코드 (J: 주식)

        Returns:
            output[]: stac_yymm(결산년월), cras(유동자산), fxas(고정자산), total_aset(자산총계), flow_lblt(유동부채), fix_lblt(고정부채), total_lblt(부채총계), cpfn(자본금), total_cptl(자본총계)

        Example:
            >>> agent.get_balance_sheet("005930")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/finance/balance-sheet",
            tr_id="FHKST66430100",
            params={
                "FID_DIV_CLS_CODE": period,
                "fid_cond_mrkt_div_code": market,
                "fid_input_iscd": code,
            },
        )

    def get_income_statement(
        self, code: str, period: str = "0", market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """국내주식 손익계산서 [v1_국내주식-079]

        종목의 결산기별 재무 데이터를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            code: 종목코드 (6자리, 예: "005930")
            period: 분류 구분 코드 (0: 년, 1: 분기)
            market: 시장 분류 코드 (J: 주식)

        Returns:
            output[]: stac_yymm(결산년월), sale_account(매출액), sale_cost(매출원가), sale_totl_prfi(매출총이익), bsop_prti(영업이익), op_prfi(경상이익), thtr_ntin(당기순이익). 분기 데이터는 연단위 누적합산

        Example:
            >>> agent.get_income_statement("005930")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/finance/income-statement",
            tr_id="FHKST66430200",
            params={
                "FID_DIV_CLS_CODE": period,
                "fid_cond_mrkt_div_code": market,
                "fid_input_iscd": code,
            },
        )

    def get_profit_ratio(
        self, code: str, period: str = "0", market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """국내주식 수익성비율 [v1_국내주식-081]

        종목의 결산기별 재무 데이터를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            code: 종목코드 (6자리, 예: "005930")
            period: 분류 구분 코드 (0: 년, 1: 분기)
            market: 시장 분류 코드 (J: 주식)

        Returns:
            output[]: stac_yymm(결산년월), cptl_ntin_rate(총자본순이익율), self_cptl_ntin_inrt(자기자본순이익율), sale_ntin_rate(매출액순이익율), sale_totl_rate(매출액총이익율)

        Example:
            >>> agent.get_profit_ratio("005930")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/finance/profit-ratio",
            tr_id="FHKST66430400",
            params={
                "fid_input_iscd": code,
                "FID_DIV_CLS_CODE": period,
                "fid_cond_mrkt_div_code": market,
            },
        )

    def get_other_major_ratios(
        self, code: str, period: str = "0", market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """국내주식 기타주요비율 [v1_국내주식-082]

        종목의 결산기별 재무 데이터를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            code: 종목코드 (6자리, 예: "005930")
            period: 분류 구분 코드 (0: 년, 1: 분기)
            market: 시장 분류 코드 (J: 주식)

        Returns:
            output[]: stac_yymm(결산년월), eva, ebitda, ev_ebitda (payout_rate는 비정상 값이라 무시)

        Example:
            >>> agent.get_other_major_ratios("005930")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/finance/other-major-ratios",
            tr_id="FHKST66430500",
            params={
                "fid_input_iscd": code,
                "fid_div_cls_code": period,
                "fid_cond_mrkt_div_code": market,
            },
        )

    def get_stability_ratio(
        self, code: str, period: str = "0", market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """국내주식 안정성비율 [v1_국내주식-083]

        종목의 결산기별 재무 데이터를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            code: 종목코드 (6자리, 예: "005930")
            period: 분류 구분 코드 (0: 년, 1: 분기)
            market: 시장 분류 코드 (J: 주식)

        Returns:
            output[]: stac_yymm(결산년월), lblt_rate(부채비율), bram_depn(차입금의존도), crnt_rate(유동비율), quck_rate(당좌비율)

        Example:
            >>> agent.get_stability_ratio("005930")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/finance/stability-ratio",
            tr_id="FHKST66430600",
            params={
                "fid_input_iscd": code,
                "fid_div_cls_code": period,
                "fid_cond_mrkt_div_code": market,
            },
        )

    def get_growth_ratio(
        self, code: str, period: str = "0", market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """국내주식 성장성비율 [v1_국내주식-085]

        종목의 결산기별 재무 데이터를 조회합니다. 실전투자 전용(모의투자 미지원).

        Args:
            code: 종목코드 (6자리, 예: "005930")
            period: 분류 구분 코드 (0: 년, 1: 분기)
            market: 시장 분류 코드 (J: 주식)

        Returns:
            output[]: stac_yymm(결산년월), grs(매출액증가율), bsop_prfi_inrt(영업이익증가율), equt_inrt(자기자본증가율), totl_aset_inrt(총자산증가율)

        Example:
            >>> agent.get_growth_ratio("005930")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/finance/growth-ratio",
            tr_id="FHKST66430800",
            params={
                "fid_input_iscd": code,
                "fid_div_cls_code": period,
                "fid_cond_mrkt_div_code": market,
            },
        )

    def get_search_info(
        self, code: str, product_type: str = "300"
    ) -> Optional[Dict[str, Any]]:
        """상품기본조회 [v1_국내주식-029]

        상품(주식·선물옵션·채권·해외주식 등)의 기본 정보를 조회합니다. 실전투자 전용.

        Args:
            code: 상품번호 (주식: 종목코드 "000660", 선물: "KR4101SC0009", 미국: "AAPL")
            product_type: 상품유형코드 (300 주식, 301 선물옵션, 302 채권,
                512 나스닥, 513 뉴욕, 529 아멕스, 515 일본, 501 홍콩 등)

        Returns:
            output: pdno(상품번호), prdt_name(상품명), prdt_abrv_name(약어명),
            prdt_eng_name(영문명), std_pdno(표준상품번호), prdt_clsf_name(분류명)

        Example:
            >>> agent.get_search_info("000660")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/search-info",
            tr_id="CTPF1604R",
            params={"PDNO": code, "PRDT_TYPE_CD": product_type},
        )

    def get_invest_opinion(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        market: str = "J",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 종목투자의견 [국내주식-188]

        종목에 대한 증권사별 투자의견과 목표가 변경 이력을 조회합니다. 실전투자 전용.

        Args:
            code: 종목코드 (예: "005930")
            start_date: 조회 시작일 YYYYMMDD (기본: 호출일 기준 90일 전)
            end_date: 조회 종료일 YYYYMMDD (기본: 호출일)
            market: 시장 분류 코드 (J)

        Returns:
            output[]: stck_bsop_date(영업일자), invt_opnn(투자의견), rgbf_invt_opnn(직전의견),
            mbcr_name(회원사명), hts_goal_prc(목표가), stck_prdy_clpr(전일종가), dprt(괴리율)

        Example:
            >>> agent.get_invest_opinion("005930")
        """
        today = _today()
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/invest-opinion",
            tr_id="FHKST663300C0",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_COND_SCR_DIV_CODE": "16633",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": start_date
                or (today - timedelta(days=90)).strftime("%Y%m%d"),
                "FID_INPUT_DATE_2": end_date or today.strftime("%Y%m%d"),
            },
        )

    def get_invest_opinion_by_sec(
        self,
        member_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        opinion: str = "0",
        market: str = "J",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 증권사별 투자의견 [국내주식-189]

        한 증권사(회원사)가 낸 종목별 투자의견을 조회합니다. 실전투자 전용.

        Args:
            member_code: 회원사 코드 (KIS Developers 포털 FAQ의 종목정보 다운로드 참조)
            start_date: 조회 시작일 YYYYMMDD (기본: 호출일 기준 90일 전)
            end_date: 조회 종료일 YYYYMMDD (기본: 호출일)
            opinion: 분류구분코드 (0 전체, 1 매수, 2 중립, 3 매도)
            market: 시장 분류 코드 (J)

        Returns:
            output[]: stck_bsop_date, stck_shrn_iscd(종목코드), hts_kor_isnm(종목명),
            invt_opnn(투자의견), mbcr_name(회원사명), hts_goal_prc(목표가), dprt(괴리율)

        Example:
            >>> agent.get_invest_opinion_by_sec("J04")
        """
        today = _today()
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/invest-opbysec",
            tr_id="FHKST663400C0",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_COND_SCR_DIV_CODE": "16634",
                "FID_INPUT_ISCD": member_code,
                "FID_DIV_CLS_CODE": opinion,
                "FID_INPUT_DATE_1": start_date
                or (today - timedelta(days=90)).strftime("%Y%m%d"),
                "FID_INPUT_DATE_2": end_date or today.strftime("%Y%m%d"),
            },
        )

    def get_credit_by_company(
        self,
        sort: str = "0",
        credit_available: str = "0",
        scope: str = "0000",
        market: str = "J",
    ) -> Optional[Dict[str, Any]]:
        """국내주식 당사 신용가능종목 [국내주식-111]

        당사에서 신용주문이 가능(또는 불가)한 종목 목록을 조회합니다. 실전투자 전용.

        Args:
            sort: 정렬 (0: 코드순, 1: 이름순)
            credit_available: 선택 여부 (0: 신용주문가능, 1: 신용주문불가)
            scope: 입력 종목코드 (0000 전체, 0001 거래소, 1001 코스닥,
                2001 코스피200, 4001 KRX100)
            market: 시장 분류 코드 (J)

        Returns:
            output[]: stck_shrn_iscd(종목코드), hts_kor_isnm(종목명), crdt_rate(신용비율)

        Example:
            >>> agent.get_credit_by_company()
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/credit-by-company",
            tr_id="FHPST04770000",
            params={
                "fid_rank_sort_cls_code": sort,
                "fid_slct_yn": credit_available,
                "fid_input_iscd": scope,
                "fid_cond_scr_div_code": "20477",
                "fid_cond_mrkt_div_code": market,
            },
        )

    def get_lendable_by_company(
        self,
        exchange: str = "00",
        code: str = "",
        sort: str = "0",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """당사 대주가능 종목 [국내주식-195]

        당사에서 대주(주식 빌리기)가 가능한 종목과 한도를 조회합니다. 실전투자 전용.
        연속조회 커서(CTX_AREA_FK200/NK100)를 따라 끝까지(최대 ``max_pages``) 합칩니다.

        Args:
            exchange: 거래소구분코드 (00 전체, 02 거래소, 03 코스닥)
            code: 종목코드 (공백이면 전체)
            sort: 조회구분 (0: 전체조회, 1: 종목코드순 정렬)
            max_pages: 최대 페이지 수

        Returns:
            output1[]: pdno, prdt_name, bfdy_clpr(전일종가), lmt_qty1(한도수량),
            use_qty1(사용수량), trad_psbl_qty2(가능수량), psbl_yn(가능여부);
            output2: tot_stup_lmt_qty, brch_lmt_qty, rqst_psbl_qty

        Example:
            >>> agent.get_lendable_by_company("00")
        """
        return self._paginate(
            "/uapi/domestic-stock/v1/quotations/lendable-by-company",
            "CTSC2702R",
            {
                "EXCG_DVSN_CD": exchange,
                "PDNO": code,
                "THCO_STLN_PSBL_YN": "Y",
                "INQR_DVSN_1": sort,
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK100": "",
            },
            cursor=[
                ("CTX_AREA_FK200", "ctx_area_fk200"),
                ("CTX_AREA_NK100", "ctx_area_nk100"),
            ],
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_estimate_perform(self, code: str) -> Optional[Dict[str, Any]]:
        """국내주식 종목추정실적 [국내주식-187]

        증권사 추정 손익계산서·투자지표를 조회합니다. 실전투자 전용.

        Args:
            code: 종목코드 (예: "265520")

        Returns:
            output1: 종목 기본정보; output2: 추정 손익계산서(매출액·영업이익·순이익 등,
            data1~data5); output3: 투자지표(EBITDA·EPS·PER·ROE 등); output4: 결산년월(dt)

        Example:
            >>> agent.get_estimate_perform("265520")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/estimate-perform",
            tr_id="HHKST668300C0",
            params={"SHT_CD": code},
        )
