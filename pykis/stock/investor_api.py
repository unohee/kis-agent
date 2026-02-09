"""
Stock Investor API - 투자자별 매매 정보 전용 모듈

투자자 유형별 매매 동향과 거래원 정보를 담당
- 투자자별 순매수 동향
- 거래원별 매매 정보
- 외국인 매매 추이
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS


class StockInvestorAPI(BaseAPI):
    """투자자별 매매 정보 조회 전용 API 클래스"""

    def get_stock_investor(
        self,
        ticker: str = "",
        retries: int = 10,
        force_refresh: bool = False,
        market: str = "J",
    ) -> Optional[Dict]:
        """
        투자자별 매매동향 조회

        Args:
            ticker: 종목코드 (6자리)
            retries: 재시도 횟수 (기본값: 10)
            force_refresh: 캐시 무시 여부
            market: 시장구분 (J: KRX, NX: NXT 대체거래소, UN: 통합)

        Returns:
            StockInvestorResponse 형식의 Dict:
                - output.stck_bsop_date: 주식 영업일자
                - output.stck_clpr: 주식 종가
                - output.prdy_vrss: 전일 대비
                - output.prdy_vrss_sign: 전일 대비 부호
                - output.prdy_ctrt: 전일 대비율
                - output.acml_vol: 누적 거래량
                개인:
                - output.prsn_ntby_qty: 개인 순매수 수량
                - output.prsn_ntby_tr_pbmn: 개인 순매수 거래대금
                - output.prsn_shnu_vol: 개인 매수 거래량
                - output.prsn_seln_vol: 개인 매도 거래량
                외국인:
                - output.frgn_ntby_qty: 외국인 순매수 수량
                - output.frgn_ntby_tr_pbmn: 외국인 순매수 거래대금
                - output.frgn_shnu_vol: 외국인 매수 거래량
                - output.frgn_seln_vol: 외국인 매도 거래량
                기관:
                - output.orgn_ntby_qty: 기관 순매수 수량
                - output.orgn_ntby_tr_pbmn: 기관 순매수 거래대금
                - output.orgn_shnu_vol: 기관 매수 거래량
                - output.orgn_seln_vol: 기관 매도 거래량

        Example:
            >>> investor = agent.stock.get_stock_investor("005930")
            >>> investor_nxt = agent.stock.get_stock_investor("005930", market="NX")
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_INPUT_ISCD": ticker,
        }
        # Note: retries parameter is kept for backwards compatibility but not used
        # _make_request_dict doesn't accept retries parameter
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_INVESTOR"],
            tr_id="FHKST01010900",
            params=params,
        )

    def get_stock_member(
        self, ticker: str, retries: int = 10, market: str = "J"
    ) -> Optional[Dict]:
        """
        거래원별 매매 정보 조회 (rt_cd 메타데이터 포함)

        Args:
            ticker: 종목코드 (6자리)
            retries: 재시도 횟수 (기본값: 10, 하위 호환용)
            market: 시장구분 (J: KRX, NX: NXT 대체거래소, UN: 통합)
        """
        # Note: retries parameter is kept for backwards compatibility but not used
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_MEMBER"],
            tr_id="FHKST01010600",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": ticker,
            },
        )

    def get_member_transaction(
        self, code: str, mem_code: str, market: str = "J"
    ) -> Optional[Dict[str, Any]]:
        """
        특정 거래원의 매매 내역 조회 (rt_cd 메타데이터 포함)

        Args:
            code: 종목코드 (6자리)
            mem_code: 거래원 코드
            market: 시장구분 (J: KRX, NX: NXT 대체거래소, UN: 통합)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_MEMBER"],
            tr_id="FHKST01010600",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_MEM_CODE": mem_code,
            },
        )

    def get_frgnmem_pchs_trend(self, code: str) -> Optional[Dict[str, Any]]:
        """외국인 매수 추이 조회 (rt_cd 메타데이터가 포함된)"""
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FRGNMEM_PCHS_TREND"],
            tr_id="FHKST644400C0",
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_input_iscd_2": "99999",
            },
        )

    def get_foreign_broker_net_buy(
        self,
        code: str,
        foreign_brokers: Optional[list] = None,
        date: Optional[str] = None,
    ) -> Optional[tuple]:
        """
        거래원 정보를 활용해 외국계 증권사의 순매수(매수-매도) 합계를 집계합니다.

        Args:
            code: 종목코드
            foreign_brokers: 외국계 브로커명 리스트 (사용되지 않음, 자동 패턴 매칭)
            date: 조회일자(YYYYMMDD), None이면 당일, 특정 날짜면 해당 날짜 데이터 조회

        Returns:
            tuple: (순매수량, 상세정보 dict) 또는 None
                - 순매수량: 외국계 증권사 순매수량 (매수-매도)
                - 상세정보: {'brokers': [...], 'buy_total': int, 'sell_total': int}
        """
        # 날짜 파라미터가 있고 당일이 아닌 경우 외국계 순매수추이 API 사용
        if date and date != datetime.now().strftime("%Y%m%d"):
            return self._get_foreign_broker_historical(code, date)

        # 당일인 경우 기존 거래원 정보 방식 사용
        return self._get_foreign_broker_current(code, date)

    def _get_foreign_broker_historical(self, code: str, date: str) -> Optional[tuple]:
        """과거 날짜의 외국인 순매수 조회 (투자자별 매매 동향 기반)"""
        try:
            # get_stock_investor로 30일간 외국인 매매 데이터 조회
            investor_data = self.get_stock_investor(ticker=code)

            if not investor_data or "output" not in investor_data:
                logging.warning(f"[{code}] 투자자별 매매 동향 데이터 조회 실패")
                return None

            # output이 리스트인지 확인
            output_data = investor_data["output"]
            if not isinstance(output_data, list):
                output_data = [output_data]

            # 사용 가능한 날짜 범위 미리 추출 (details에서 사용)
            available_dates = [row.get("stck_bsop_date", "") for row in output_data]

            # 해당 날짜 데이터 찾기
            target_row = None
            for row in output_data:
                if row.get("stck_bsop_date") == date:
                    target_row = row
                    break

            if not target_row:
                logging.warning(
                    f"[{code}] {date} 날짜 데이터 없음 (최근 30일 범위 내에서만 조회 가능)"
                )
                # 사용 가능한 날짜 범위 표시
                if available_dates:
                    logging.info(
                        f"[{code}] 사용 가능한 날짜: {available_dates[0]} ~ {available_dates[-1]}"
                    )
                return None

            # 외국인 매매 데이터 추출
            frgn_ntby_qty = (
                int(target_row.get("frgn_ntby_qty", 0))
                if target_row.get("frgn_ntby_qty")
                else 0
            )
            frgn_buy_vol = (
                int(target_row.get("frgn_shnu_vol", 0))
                if target_row.get("frgn_shnu_vol")
                else 0
            )
            frgn_sell_vol = (
                int(target_row.get("frgn_seln_vol", 0))
                if target_row.get("frgn_seln_vol")
                else 0
            )

            details = {
                "brokers": [],  # 과거 날짜는 개별 거래원 정보 없음
                "buy_total": frgn_buy_vol,
                "sell_total": frgn_sell_vol,
                "total_brokers_found": 0,
                "query_date": date,
                "note": "투자자별 매매 동향 기반 외국인 전체 순매수 (과거 날짜)",
                "api_method": "stock_investor",
                "data_range": f"{available_dates[0] if available_dates else ''} ~ {available_dates[-1] if available_dates else ''}",
            }

            logging.info(
                f"[{code}] {date} 외국인 순매수: {frgn_ntby_qty:,}주 (매수: {frgn_buy_vol:,}, 매도: {frgn_sell_vol:,})"
            )
            return frgn_ntby_qty, details

        except Exception as e:
            logging.error(f"[{code}] 과거 날짜 외국인 순매수 조회 실패 ({date}): {e}")
            return None

    def _get_foreign_broker_current(
        self, code: str, date: str = None
    ) -> Optional[tuple]:
        """당일 외국계 증권사 순매수 조회 (거래원 정보 기반)"""
        # 거래원 정보 조회
        member_data = self.get_stock_member(code)
        if not member_data or "output" not in member_data:
            logging.warning(f"[{code}] 거래원 정보 조회 실패")
            return None

        try:
            output = member_data["output"]

            # API 응답 구조: 딕셔너리 형태로 상위 5개 매도/매수 회원사 정보
            # seln_mbcr_name1~5: 매도 회원사명
            # shnu_mbcr_name1~5: 매수 회원사명
            # total_seln_qty1~5: 매도 수량
            # total_shnu_qty1~5: 매수 수량
            # seln_mbcr_glob_yn_1~5: 매도 외국계 여부 ('Y'/'N')
            # shnu_mbcr_glob_yn_1~5: 매수 외국계 여부 ('Y'/'N')

            foreign_brokers = []
            total_buy = 0
            total_sell = 0

            # 매도 상위 5개 회원사 확인
            for i in range(1, 6):
                broker_name = output.get(f"seln_mbcr_name{i}", "")
                is_foreign = output.get(f"seln_mbcr_glob_yn_{i}", "N") == "Y"
                sell_qty = int(output.get(f"total_seln_qty{i}", 0) or 0)

                if is_foreign and broker_name and sell_qty > 0:
                    total_sell += sell_qty
                    foreign_brokers.append(
                        {
                            "name": broker_name,
                            "type": "sell",
                            "volume": sell_qty,
                            "rank": i,
                        }
                    )

            # 매수 상위 5개 회원사 확인
            for i in range(1, 6):
                broker_name = output.get(f"shnu_mbcr_name{i}", "")
                is_foreign = output.get(f"shnu_mbcr_glob_yn_{i}", "N") == "Y"
                buy_qty = int(output.get(f"total_shnu_qty{i}", 0) or 0)

                if is_foreign and broker_name and buy_qty > 0:
                    total_buy += buy_qty
                    foreign_brokers.append(
                        {
                            "name": broker_name,
                            "type": "buy",
                            "volume": buy_qty,
                            "rank": i,
                        }
                    )

            net_buy = total_buy - total_sell

            details = {
                "brokers": foreign_brokers,
                "buy_total": total_buy,
                "sell_total": total_sell,
                "total_brokers_found": len(foreign_brokers),
                "query_date": date or datetime.now().strftime("%Y%m%d"),
                "note": "거래원 정보 기반 외국계 증권사 순매수",
                "api_method": "member_data",
            }

            logging.info(
                f"[{code}] 외국계 {len(foreign_brokers)}개사 순매수: {net_buy:,}주 (매수: {total_buy:,}, 매도: {total_sell:,})"
            )
            return net_buy, details

        except Exception as e:
            logging.error(f"[{code}] 외국계 순매수 집계 실패: {e}")
            return None

    def get_frgnmem_trade_estimate(
        self,
        fid_cond_mrkt_div_code: str = "J",
        fid_cond_scr_div_code: str = "16441",
        fid_input_iscd: str = "0000",
        fid_rank_sort_cls_code: str = "0",
        fid_rank_sort_cls_code_2: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        외국계 매매종목 가집계 조회

        Args:
            fid_cond_mrkt_div_code: 조건시장분류코드 (J: 주식)
            fid_cond_scr_div_code: 조건화면분류코드 (16441: 기본)
            fid_input_iscd: 입력종목코드 (0000: 전체, 1001: 코스피, 2001: 코스닥)
            fid_rank_sort_cls_code: 순위정렬구분코드 (0: 금액순, 1: 수량순)
            fid_rank_sort_cls_code_2: 순위정렬구분코드2 (0: 매수순, 1: 매도순)

        Returns:
            Optional[Dict[str, Any]]: 외국계 매매종목 가집계 데이터
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
            "FID_COND_SCR_DIV_CODE": fid_cond_scr_div_code,
            "FID_INPUT_ISCD": fid_input_iscd,
            "FID_RANK_SORT_CLS_CODE": fid_rank_sort_cls_code,
            "FID_RANK_SORT_CLS_CODE_2": fid_rank_sort_cls_code_2,
        }
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FRGNMEM_TRADE_ESTIMATE"],
            tr_id="FHKST644100C0",
            params=params,
        )

    def get_frgnmem_trade_trend(
        self,
        fid_cond_scr_div_code: str = "20432",
        fid_cond_mrkt_div_code: str = "J",
        fid_input_iscd: str = "",
        fid_input_iscd_2: str = "99999",
        fid_mrkt_cls_code: str = "A",
        fid_vol_cnt: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        회원사 실시간 매매동향(틱) 조회

        Args:
            fid_cond_scr_div_code: 조건화면분류코드 (20432)
            fid_cond_mrkt_div_code: 조건시장분류코드 (J 고정)
            fid_input_iscd: 종목코드 (예: 005930)
            fid_input_iscd_2: 회원사코드 (99999: 전체)
            fid_mrkt_cls_code: 시장구분코드 (A: 전체, K: 코스피, Q: 코스닥)
            fid_vol_cnt: 거래량

        Returns:
            Optional[Dict[str, Any]]: 회원사 실시간 매매동향 데이터
        """
        params = {
            "FID_COND_SCR_DIV_CODE": fid_cond_scr_div_code,
            "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
            "FID_INPUT_ISCD": fid_input_iscd,
            "FID_INPUT_ISCD_2": fid_input_iscd_2,
            "FID_MRKT_CLS_CODE": fid_mrkt_cls_code,
            "FID_VOL_CNT": fid_vol_cnt,
        }
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FRGNMEM_TRADE_TREND"],
            tr_id="FHPST04320000",
            params=params,
        )

    def get_investor_program_trade_today(
        self, mrkt_div_cls_code: str = "1"
    ) -> Optional[Dict[str, Any]]:
        """
        프로그램매매 투자자매매동향(당일) 조회

        Args:
            mrkt_div_cls_code: 시장구분코드 (1: 코스피, 4: 코스닥)

        Returns:
            Optional[Dict[str, Any]]: 프로그램매매 투자자매매동향 데이터
        """
        params = {"MRKT_DIV_CLS_CODE": mrkt_div_cls_code}
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INVESTOR_PROGRAM_TRADE_TODAY"],
            tr_id="HHPPG046600C1",
            params=params,
        )

    def get_investor_trade_by_stock_daily(
        self,
        fid_cond_mrkt_div_code: str = "J",
        fid_input_iscd: str = "",
        fid_input_date_1: str = "",
        fid_org_adj_prc: str = "",
        fid_etc_cls_code: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        종목별 투자자매매동향(일별) 조회

        Args:
            fid_cond_mrkt_div_code: 조건시장분류코드 (J: KRX, NX: NXT, UN: 통합)
            fid_input_iscd: 종목코드 (6자리)
            fid_input_date_1: 조회날짜 (YYYYMMDD)
            fid_org_adj_prc: 수정주가원주가가격 (공란)
            fid_etc_cls_code: 기타구분코드 (공란)

        Returns:
            Optional[Dict[str, Any]]: 종목별 투자자매매동향 데이터
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
            "FID_INPUT_ISCD": fid_input_iscd,
            "FID_INPUT_DATE_1": fid_input_date_1,
            "FID_ORG_ADJ_PRC": fid_org_adj_prc,
            "FID_ETC_CLS_CODE": fid_etc_cls_code,
        }
        return self._make_request_dict(
            endpoint=API_ENDPOINTS.get(
                "INVESTOR_TRADE_BY_STOCK_DAILY",
                "/uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily",
            ),
            tr_id="FHPTJ04160001",
            params=params,
        )

    def get_investor_trend_estimate(
        self, mksc_shrn_iscd: str
    ) -> Optional[Dict[str, Any]]:
        """
        종목별 외국인/기관 추정가집계 조회

        장중에 증권사 직원이 집계한 외국인/기관 매매 추정치를 조회합니다.
        입력시간: 외국인 09:30, 11:20, 13:20, 14:30 / 기관종합 10:00, 11:20, 13:20, 14:30

        Args:
            mksc_shrn_iscd: 종목코드 (6자리)

        Returns:
            Optional[Dict[str, Any]]: 종목별 외국인/기관 추정가집계 데이터
        """
        params = {"MKSC_SHRN_ISCD": mksc_shrn_iscd}
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INVESTOR_TREND_ESTIMATE"],
            tr_id="HHPTJ04160200",
            params=params,
        )

    def get_member_trading_daily(
        self,
        code: str,
        start_date: str,
        end_date: str,
        member_code: str = "99999",
        fid_cond_mrkt_div_code: str = "J",
        fid_sctn_cls_code: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        주식현재가 회원사 종목매매동향 (일별) 조회

        특정 기간 동안 회원사(증권사)별 종목 매매동향을 조회합니다.
        회원사코드 99999를 사용하면 전체 회원사의 매매동향을 확인할 수 있습니다.

        Args:
            code: 종목코드 (6자리, 예: "005930")
            start_date: 조회 시작일자 (YYYYMMDD, 예: "20250101")
            end_date: 조회 종료일자 (YYYYMMDD, 예: "20250624")
            member_code: 회원사코드 (기본값: "99999" - 전체)
            fid_cond_mrkt_div_code: 조건시장분류코드 (J: KRX, NX: NXT, 기본값: "J")
            fid_sctn_cls_code: 구간구분코드 (공란 - 기본값: "")

        Returns:
            Optional[Dict[str, Any]]: 회원사 종목매매동향 데이터
                - output: dict 형태로 반환 (일별 회원사 매매 데이터)

        Example:
            >>> # 삼성전자 2025년 1월~6월 전체 회원사 매매동향
            >>> data = agent.stock.get_member_trading_daily(
            ...     code="005930",
            ...     start_date="20250101",
            ...     end_date="20250624"
            ... )
            >>> print(data['output'])
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": fid_cond_mrkt_div_code,
            "FID_INPUT_ISCD": code,
            "FID_INPUT_ISCD_2": member_code,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_SCTN_CLS_CODE": fid_sctn_cls_code,
        }
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_MEMBER_DAILY"],
            tr_id="FHPST04540000",
            params=params,
        )
