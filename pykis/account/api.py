"""계좌 정보 조회 모듈. 잔고/주문/손익 조회 및 현금/신용 주문 기능."""

import logging
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS, KISClient


class AccountAPI(BaseAPI):
    def __init__(
        self,
        client: KISClient,
        account_info: Dict[str, str],
        enable_cache=True,
        cache_config=None,
        _from_agent=False,
    ):
        """KIS 계좌 API 래퍼. account_info에 CANO/ACNT_PRDT_CD 필요."""
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

    def get_account_balance(self) -> Optional[Dict]:
        """계좌 잔고 조회. output1=보유종목, output2=요약(예수금/총평가/순자산)."""
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-balance",
            tr_id="TTTC8434R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "01",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "00",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
        )

    def get_cash_available(
        self, stock_code: str = "005930"
    ) -> Optional[Dict[str, Any]]:
        """종목별 매수가능금액 조회. ord_psbl_cash/max_buy_qty 반환."""
        res = self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-psbl-order",
            tr_id="TTTC8908R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "PDNO": stock_code,  # 매수가능조회할 종목코드
                "ORD_UNPR": "0",  # 주문단가 (0으로 설정하면 현재가 기준)
                "ORD_DVSN": "00",  # 지정가
                "CMA_EVLU_AMT_ICLD_YN": "Y",  # CMA평가금액포함여부
                "OVRS_ICLD_YN": "N",  # 해외포함여부
            },
        )
        # JSON 디코드 실패 시 원시 응답 확인을 위한 상세 정보 제공
        if res is not None and res.get("rt_cd") == "JSON_DECODE_ERROR":
            # 원시 응답 텍스트 확인을 위해 추가 정보 제공
            res["디버깅_정보"] = (
                f"원시 응답 텍스트 확인 필요 (상태코드: {res.get('status_code', 'N/A')})"
            )
        return res

    def get_total_asset(self) -> Optional[Dict[str, Any]]:
        """계좌 총자산 조회. 예수금+주식 포함 전체 자산 평가."""
        res = self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-account-balance",
            tr_id="CTRP6548R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "INQR_DVSN_1": "",  # 조회구분1 (공백입력)
                "BSPR_BF_DT_APLY_YN": "",  # 기준가이전일자적용여부 (공백입력)
            },
        )
        # JSON 디코드 실패 시 원시 응답 확인을 위한 상세 정보 제공
        if res is not None and res.get("rt_cd") == "JSON_DECODE_ERROR":
            # 원시 응답 텍스트 확인을 위해 추가 정보 제공
            res["디버깅_정보"] = (
                f"원시 응답 텍스트 확인 필요 (상태코드: {res.get('status_code', 'N/A')})"
            )
        return res

    def get_account_order_quantity(self, code: str) -> Optional[Dict]:
        """종목별 주문가능수량 조회. output.ord_psbl_qty 반환."""
        try:
            return self._make_request_dict(
                endpoint=(
                    "/uapi/domestic-stock/v1/trading/inquire-account-order-quantity"
                ),
                tr_id="TTTC8434R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": code,
                    "ORD_UNPR": "0",
                    "CTX_AREA_FK200": "",
                    "CTX_AREA_NK200": "",
                },
            )
        except Exception as e:
            logging.error(f"계좌별 주문 수량 조회 실패: {e}")
            return None

    def get_possible_order_amount(self) -> Optional[Dict]:
        """주문가능금액 조회. output.ord_psbl_amt 반환."""
        try:
            return self._make_request_dict(
                endpoint=API_ENDPOINTS["INQUIRE_PSBL_ORDER"],
                tr_id="TTTC8908R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": "",
                    "ORD_UNPR": "0",
                    "ORD_DVSN": "00",
                    "CMA_EVLU_AMT_ICLD_YN": "Y",
                    "OVRS_ICLD_YN": "N",
                },
            )
        except Exception as e:
            logging.error(f"주문 가능 금액 조회 실패: {e}")
            return None

    def order_credit(
        self, code: str, qty: int, price: int, order_type: str
    ) -> Optional[Dict]:
        """신용주문 실행. output.odno 반환. 실제 주문 실행됨."""
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-credit",
                tr_id="TTTC0052U",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": code,
                    "CRDT_TYPE": "21",
                    "LOAN_DT": "",
                    "ORD_DVSN": order_type,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                },
                method="POST",  # 주문 API는 POST 메서드 사용
            )
        except Exception as e:
            logging.error(f"신용 주문 실패: {e}")
            return None

    def order_rvsecncl(
        self, org_order_no: str, qty: int, price: int, order_type: str, cncl_type: str
    ) -> Optional[Dict]:
        """주문 정정/취소. cncl_type='정정' 또는 '취소'."""
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-rvsecncl",
                tr_id="TTTC0013U",  # 정정/취소 TR (구: TTTC0803U)
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "KRX_FWDG_ORD_ORGNO": "",
                    "ORGN_ODNO": org_order_no,
                    "ORD_DVSN": order_type,
                    "RVSE_CNCL_DVSN_CD": cncl_type,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "QTY_ALL_ORD_YN": "Y",
                },
                method="POST",  # 주문 API는 POST 메서드 사용
            )
        except Exception as e:
            logging.error(f"정정/취소 주문 실패: {e}")
            return None

    def inquire_psbl_rvsecncl(self) -> Optional[Dict]:
        """정정/취소 가능한 미체결 주문 목록 조회."""
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl",
                tr_id="TTTC8036R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "CTX_AREA_FK100": "",
                    "CTX_AREA_NK100": "",
                    "INQR_DVSN_1": "1",
                    "INQR_DVSN_2": "0",
                },
            )
        except Exception as e:
            logging.error(f"정정/취소 가능 주문 조회 실패: {e}")
            return None

    def order_resv(
        self, code: str, qty: int, price: int, order_type: str
    ) -> Optional[Dict]:
        """예약주문 등록. 지정 시점에 주문 실행."""
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-resv",
                tr_id="CTSC0008U",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": code,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "SLL_BUY_DVSN_CD": "02",
                    "ORD_DVSN_CD": order_type,
                    "ORD_OBJT_CBLC_DVSN_CD": "10",
                },
                method="POST",  # 주문 API는 POST 메서드 사용
            )
        except Exception as e:
            logging.error(f"예약 주문 실패: {e}")
            return None

    def order_resv_rvsecncl(
        self, seq: int, qty: int, price: int, order_type: str
    ) -> Optional[Dict]:
        """예약주문 정정/취소. seq=예약주문 일련번호."""
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-resv-rvsecncl",
                tr_id="CTSC0013U",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": "",
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "SLL_BUY_DVSN_CD": "02",
                    "ORD_DVSN_CD": order_type,
                    "ORD_OBJT_CBLC_DVSN_CD": "10",
                    "RSVN_ORD_SEQ": str(seq),
                },
                method="POST",  # 주문 API는 POST 메서드 사용
            )
        except Exception as e:
            logging.error(f"예약 주문 정정/취소 실패: {e}")
            return None

    def order_resv_ccnl(self) -> Optional[Dict]:
        """등록된 예약주문 내역 조회."""
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-resv-ccnl",
                tr_id="CTSC0004R",
                params={
                    "RSVN_ORD_ORD_DT": "",
                    "RSVN_ORD_END_DT": "",
                    "RSVN_ORD_SEQ": "",
                    "TMNL_MDIA_KIND_CD": "00",
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PRCS_DVSN_CD": "0",
                    "CNCL_YN": "Y",
                    "PDNO": "",
                    "SLL_BUY_DVSN_CD": "",
                    "CTX_AREA_FK200": "",
                    "CTX_AREA_NK200": "",
                },
            )
        except Exception as e:
            logging.error(f"예약 주문 조회 실패: {e}")
            return None

    def inquire_daily_ccld(
        self,
        start_date: str = "",
        end_date: str = "",
        pdno: str = "",
        ord_dvsn_cd: str = "00",
        pagination: bool = False,
        ccld_dvsn: str = "00",
        inqr_dvsn: str = "01",
        inqr_dvsn_3: str = "00",
        max_pages: int = 100,
        page_callback: Optional[
            Callable[[int, List[Dict[str, Any]], Dict[str, Any]], None]
        ] = None,
    ) -> Optional[Dict[str, Any]]:
        """일별주문체결조회. pagination=True로 연속조회(100건+). output1=체결내역, output2=요약."""
        # 연속조회 사용
        if pagination:
            return self._inquire_daily_ccld_pagination(
                start_date=start_date,
                end_date=end_date,
                sll_buy_dvsn_cd=ord_dvsn_cd,
                inqr_dvsn=inqr_dvsn,
                pdno=pdno,
                ccld_dvsn=ccld_dvsn,
                inqr_dvsn_3=inqr_dvsn_3,
                max_pages=max_pages,
                page_callback=page_callback,
            )

        # 기존 단일 조회
        try:
            # 조회 기간에 따라 TR ID 선택
            from datetime import datetime, timedelta

            today = datetime.now()
            three_months_ago = (today - timedelta(days=90)).strftime("%Y%m%d")

            # start_date가 3개월 이전이면 CTSC9215R, 이내면 TTTC0081R
            if start_date and start_date < three_months_ago:
                tr_id = "CTSC9215R"  # 3개월 이전 데이터
            else:
                tr_id = "TTTC0081R"  # 3개월 이내 데이터

            res = self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
                tr_id=tr_id,
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "INQR_STRT_DT": start_date,
                    "INQR_END_DT": end_date,
                    "SLL_BUY_DVSN_CD": ord_dvsn_cd,
                    "INQR_DVSN": "00",
                    "PDNO": pdno,
                    "CCLD_DVSN": "00",  # 00: 전체, 01: 체결, 02: 미체결
                    "ORD_GNO_BRNO": "",
                    "ODNO": "",
                    "INQR_DVSN_3": "00",
                    "INQR_DVSN_1": "",
                    "CTX_AREA_FK100": "",
                    "CTX_AREA_NK100": "",
                },
            )

            # API 응답을 그대로 딕셔너리로 반환
            return res
        except Exception as e:
            logging.error(f"일별주문체결 조회 실패: {e}")
            return None

    def _inquire_daily_ccld_pagination(
        self,
        start_date: str,
        end_date: str,
        sll_buy_dvsn_cd: str = "00",
        inqr_dvsn: str = "01",
        pdno: str = "",
        ccld_dvsn: str = "01",
        inqr_dvsn_3: str = "00",
        max_pages: int = 100,
        page_callback: Optional[
            Callable[[int, List[Dict[str, Any]], Dict[str, Any]], None]
        ] = None,
    ) -> Optional[Dict[str, Any]]:
        """내부 헬퍼: 연속조회키(CTX_AREA_FK/NK100)로 페이지네이션. inquire_daily_ccld(pagination=True) 사용."""
        all_data = []
        ctx_area_fk100 = ""
        ctx_area_nk100 = ""
        page_count = 0

        # 조회 기간에 따라 TR ID 선택
        from datetime import datetime, timedelta

        today = datetime.now()
        three_months_ago = (today - timedelta(days=90)).strftime("%Y%m%d")

        # start_date가 3개월 이전이면 CTSC9215R, 이내면 TTTC0081R
        # 주의: 단일 조회와 동일한 TR ID 사용
        if start_date and start_date < three_months_ago:
            tr_id = "CTSC9215R"  # 3개월 이전 데이터
        else:
            tr_id = "TTTC0081R"  # 3개월 이내 데이터

        try:
            while page_count < max_pages:
                # 연속조회 헤더 설정
                # 첫 번째 조회: tr_cont = "" (빈 문자열)
                # 이후 조회: tr_cont = "N"
                req_headers = {}
                if page_count > 0:
                    req_headers["tr_cont"] = "N"

                # API 요청
                res = self.client.make_request(
                    endpoint="/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
                    tr_id=tr_id,
                    headers=req_headers,
                    params={
                        "CANO": self.account["CANO"],
                        "ACNT_PRDT_CD": self.account.get("ACNT_PRDT_CD", "01"),
                        "INQR_STRT_DT": start_date,
                        "INQR_END_DT": end_date,
                        "SLL_BUY_DVSN_CD": sll_buy_dvsn_cd,
                        "INQR_DVSN": inqr_dvsn,
                        "PDNO": pdno,
                        "CCLD_DVSN": ccld_dvsn,
                        "ORD_GNO_BRNO": "",
                        "ODNO": "",
                        "INQR_DVSN_3": inqr_dvsn_3,
                        "INQR_DVSN_1": "",
                        "CTX_AREA_FK100": ctx_area_fk100,
                        "CTX_AREA_NK100": ctx_area_nk100,
                    },
                )

                # 응답 처리
                if not res or res.get("rt_cd") != "0":
                    if page_count == 0:
                        logging.error(
                            f"일별주문체결 조회 실패: {res.get('msg1', 'Unknown error') if res else 'No response'}"
                        )
                        return None
                    else:
                        # 연속조회 중 오류 발생시 현재까지 데이터 반환
                        logging.warning(
                            f"페이지 {page_count + 1} 조회 실패, 현재까지 데이터 반환"
                        )
                        break

                # output1 데이터 처리
                output1 = res.get("output1", [])
                if not output1:
                    # 더 이상 데이터가 없음
                    break

                # 데이터 저장 (딕셔너리 리스트로 유지)
                all_data.extend(output1)

                page_count += 1

                # 콜백 호출
                if page_callback:
                    ctx_info = {
                        "FK100": res.get("ctx_area_fk100", ""),
                        "NK100": res.get("ctx_area_nk100", ""),
                        "total_rows": len(output1),
                    }
                    page_callback(page_count, output1, ctx_info)

                # 연속조회 키 추출 (소문자 키 사용)
                ctx_area_fk100 = res.get("ctx_area_fk100", "").strip()
                ctx_area_nk100 = res.get("ctx_area_nk100", "").strip()

                # 연속조회 종료 조건 확인
                # 1. msg1이 "조회가 계속됩니다"가 아니면 마지막 페이지
                # 2. 연속조회 키가 모두 비어있으면 마지막 페이지
                # 3. 데이터가 100건 미만이면 마지막 페이지
                msg1 = res.get("msg1", "").strip()
                is_continue = "계속" in msg1 or "조회가 계속됩니다" in msg1

                if not is_continue:
                    logging.info(f"연속조회 종료: msg1='{msg1}'")
                    break

                if not ctx_area_fk100 and not ctx_area_nk100:
                    logging.info("연속조회 종료: 연속조회키 없음")
                    break

                if len(output1) < 100:
                    logging.info(f"연속조회 종료: 데이터 {len(output1)}건 (100건 미만)")
                    break

            # 전체 데이터를 딕셔너리로 반환
            if all_data:
                # 중복 제거
                unique_data = []
                seen = set()
                for item in all_data:
                    key = (
                        item.get("ord_dt", ""),
                        item.get("odno", ""),
                        item.get("pdno", ""),
                    )
                    if key not in seen:
                        seen.add(key)
                        unique_data.append(item)

                # 정렬
                if unique_data:
                    unique_data.sort(
                        key=lambda x: (x.get("ord_dt", ""), x.get("ord_tmd", "")),
                        reverse=(inqr_dvsn == "00"),
                    )

                # 요약 정보 생성
                tot_ord_qty = sum(
                    int(item.get("ord_qty", 0))
                    for item in unique_data
                    if item.get("ord_qty")
                )
                tot_ccld_qty = sum(
                    int(item.get("tot_ccld_qty", 0))
                    for item in unique_data
                    if item.get("tot_ccld_qty")
                )
                tot_ccld_amt = sum(
                    float(item.get("tot_ccld_amt", 0))
                    for item in unique_data
                    if item.get("tot_ccld_amt")
                )

                logging.info(
                    f"일별주문체결 조회 완료: 총 {page_count}페이지, {len(unique_data)}건"
                )

                # output2 요약 정보 생성
                # 연속조회 시에는 prsm_tlex_smtl (추정제비용합계)와 pchs_avg_pric (매입평균가격)이
                # 제공되지 않으므로, 마지막 응답(res)의 output2를 기반으로 생성
                output2 = {
                    "tot_ord_qty": str(tot_ord_qty),
                    "tot_ccld_qty": str(tot_ccld_qty),
                    "tot_ccld_amt": str(tot_ccld_amt),
                    "page_count": page_count,
                    "total_count": len(unique_data),
                }

                # 마지막 응답의 output2에서 추가 필드 복사
                # (prsm_tlex_smtl, pchs_avg_pric 등)
                if res and "output2" in res:
                    last_output2 = res.get("output2", {})
                    if "prsm_tlex_smtl" in last_output2:
                        output2["prsm_tlex_smtl"] = last_output2["prsm_tlex_smtl"]
                    if "pchs_avg_pric" in last_output2:
                        output2["pchs_avg_pric"] = last_output2["pchs_avg_pric"]

                # 최종 결과 반환
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESSFUL",
                    "msg1": f"정상처리 완료 - 총 {len(unique_data)}건 조회",
                    "output1": unique_data,
                    "output2": output2,
                }

            # 빈 결과 반환
            return {
                "rt_cd": "0",
                "msg_cd": "NO_DATA",
                "msg1": "조회된 데이터가 없습니다",
                "output1": [],
                "output2": {
                    "tot_ord_qty": "0",
                    "tot_ccld_qty": "0",
                    "tot_ccld_amt": "0",
                    "page_count": 0,
                    "total_count": 0,
                },
            }

        except Exception as e:
            logging.error(f"일별주문체결 연속조회 실패: {e}")
            return None

    def inquire_period_trade_profit(
        self,
        start_date: str,
        end_date: str,
        pdno: str = "",
        sort_dvsn: str = "00",
        cblc_dvsn: str = "00",
        as_dict: bool = False,
    ) -> Optional[pd.DataFrame]:
        """기간별 실현손익 조회. as_dict=True면 Dict, False면 DataFrame 반환."""
        try:
            res = self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-period-trade-profit",
                tr_id="TTTC8715R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": pdno,
                    "INQR_STRT_DT": start_date,
                    "INQR_END_DT": end_date,
                    "SORT_DVSN": sort_dvsn,
                    "CBLC_DVSN": cblc_dvsn,
                    "CTX_AREA_FK100": "",
                    "CTX_AREA_NK100": "",
                },
            )

            if as_dict:
                # Dict 형태로 반환
                return res

            # DataFrame 형태로 반환 (기존 동작)
            if res and "output1" in res:
                df = pd.DataFrame(res["output1"])
                # rt_cd 컬럼 추가 (API 응답 성공/실패 추적용)
                df["rt_cd"] = res.get("rt_cd", "")
                df["msg_cd"] = res.get("msg_cd", "")
                df["msg1"] = res.get("msg1", "")
                return df
            return None
        except Exception as e:
            logging.error(f"기간별매매손익 조회 실패: {e}")
            return None

    def get_period_trade_profit(
        self,
        start_date: str,
        end_date: str,
        pdno: str = "",
        sort_dvsn: str = "00",
        cblc_dvsn: str = "00",
    ) -> Optional[Dict]:
        """기간별매매손익합산조회 - 특정 기간의 실현 매매손익을 Dict로 조회합니다.

        inquire_period_trade_profit의 Dict 반환 버전입니다.
        Agent facade에서 직접 호출할 수 있으며, 다른 계좌 API들과 일관된 Dict 형태로 반환합니다.

        Args:
            start_date: 조회시작일자 (YYYYMMDD 형식, 필수)
            end_date: 조회종료일자 (YYYYMMDD 형식, 필수)
            pdno: 상품번호 (종목코드, 6자리). 빈 문자열이면 전체 종목 조회
            sort_dvsn: 정렬구분 (기본값: "00")
                - "00": 역순 (최신 데이터부터)
                - "01": 정순 (과거 데이터부터)
            cblc_dvsn: 잔고구분 (기본값: "00")
                - "00": 전체
                - "01": 현금
                - "02": 신용

        Returns:
            Optional[Dict]: 기간별 매매손익 정보
                - rt_cd: 응답코드 ("0": 성공)
                - msg_cd: 메시지코드
                - msg1: 응답메시지
                - output1: 매매손익 리스트 (각 항목은 딕셔너리)
                    - trad_dt: 매매일자
                    - pdno: 상품번호
                    - prdt_name: 상품명
                    - trad_dvsn_name: 매매구분명
                    - loan_dt: 대출일자
                    - hldg_qty: 보유수량
                    - pchs_unpr: 매입단가
                    - buy_qty: 매수수량
                    - buy_amt: 매수금액
                    - sll_pric: 매도가격
                    - sll_qty: 매도수량
                    - sll_amt: 매도금액
                    - rlzt_pfls: 실현손익
                    - pfls_rt: 손익률(%)
                    - fee: 수수료
                    - tl_tax: 제세금
                    - loan_int: 대출이자
                - output2: 요약 정보
                    - sll_qty_smtl: 매도수량합계
                    - sll_tr_amt_smtl: 매도거래금액합계
                    - sll_fee_smtl: 매도수수료합계
                    - sll_tltx_smtl: 매도제세금합계
                    - sll_excc_amt_smtl: 매도정산금액합계
                    - buyqty_smtl: 매수수량합계
                    - buy_tr_amt_smtl: 매수거래금액합계
                    - buy_fee_smtl: 매수수수료합계
                    - buy_tax_smtl: 매수제세금합계
                    - buy_excc_amt_smtl: 매수정산금액합계
                    - tot_qty: 총수량
                    - tot_tr_amt: 총거래금액
                    - tot_fee: 총수수료
                    - tot_tltx: 총제세금
                    - tot_excc_amt: 총정산금액
                    - tot_rlzt_pfls: 총실현손익
                    - tot_pftrt: 총수익률
                실패 시 None 반환

        Example:
            >>> # 2025년 1월 전체 매매손익 조회
            >>> result = api.get_period_trade_profit("20250101", "20250131")
            >>> if result and result.get('rt_cd') == '0':
            ...     total_profit = result['output2']['tot_rlzt_pfls']
            ...     print(f"총 실현손익: {float(total_profit):,.0f}원")

            >>> # 특정 종목 매매손익 조회
            >>> result = api.get_period_trade_profit(
            ...     "20250101", "20250131", pdno="005930"
            ... )
            >>> if result and result.get('rt_cd') == '0':
            ...     for item in result['output1']:
            ...         print(f"{item['trad_dt']}: {item['rlzt_pfls']}원")
        """
        return self.inquire_period_trade_profit(
            start_date=start_date,
            end_date=end_date,
            pdno=pdno,
            sort_dvsn=sort_dvsn,
            cblc_dvsn=cblc_dvsn,
            as_dict=True,
        )

    def inquire_period_profit(
        self,
        start_date: str,
        end_date: str,
        sort_dvsn: str = "00",
        inqr_dvsn: str = "00",
        cblc_dvsn: str = "00",
        as_dict: bool = False,
    ) -> Optional[pd.DataFrame]:
        """기간별손익일별합산조회 - 특정 기간의 일별 손익을 합산하여 조회합니다.

        지정한 기간 동안의 일별 손익을 합산하여 제공합니다.
        inquire_period_trade_profit과 달리 일별 합산 기준으로 집계됩니다.

        Args:
            start_date: 조회시작일자 (YYYYMMDD 형식, 필수)
            end_date: 조회종료일자 (YYYYMMDD 형식, 필수)
            sort_dvsn: 정렬구분 (기본값: "00")
                - "00": 역순 (최신 데이터부터)
                - "01": 정순 (과거 데이터부터)
            inqr_dvsn: 조회구분 (기본값: "00")
                - "00": 전체
                - "01": 입금
                - "02": 출금
            cblc_dvsn: 잔고구분 (기본값: "00")
                - "00": 전체
                - "01": 현금
                - "02": 융자
                - "03": 대주
                - "04": 신용
            as_dict: True이면 Dict 반환, False이면 DataFrame 반환 (기본값: False)

        Returns:
            Optional[pd.DataFrame] 또는 Optional[Dict]: 기간별 일별 손익 합산 정보
                DataFrame 필드 (as_dict=False):
                - trad_dt: 거래일자
                - sll_amt: 매도금액
                - buy_amt: 매수금액
                - rlzt_pfls: 실현손익
                - fee_smtl: 수수료합계
                - tltx_smtl: 제세금합계
                - tot_rlzt_pfls: 총실현손익

                Dict 구조 (as_dict=True):
                - rt_cd: 응답코드 ("0": 성공)
                - msg1: 응답메시지
                - output1: 일별 손익 리스트
                - output2: 요약 정보

                실패 시 None 반환

        Example:
            >>> # 2025년 1월 일별 손익 조회 (DataFrame)
            >>> df = api.inquire_period_profit("20250101", "20250131")
            >>> if df is not None:
            ...     total = df['rlzt_pfls'].astype(float).sum()
            ...     print(f"총 실현손익: {total:,.0f}원")

            >>> # Dict 형태로 조회
            >>> result = api.inquire_period_profit("20250101", "20250131", as_dict=True)
            >>> if result and result.get('rt_cd') == '0':
            ...     for day in result['output1']:
            ...         print(f"{day['trad_dt']}: {day['rlzt_pfls']}원")
        """
        try:
            res = self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-period-profit",
                tr_id="TTTC8708R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": "",  # 종목코드 (빈값=전체)
                    "INQR_STRT_DT": start_date,
                    "INQR_END_DT": end_date,
                    "SORT_DVSN": sort_dvsn,
                    "INQR_DVSN": inqr_dvsn,
                    "CBLC_DVSN": cblc_dvsn,
                    "CTX_AREA_FK100": "",
                    "CTX_AREA_NK100": "",
                },
            )

            if as_dict:
                return res

            if res and "output1" in res:
                df = pd.DataFrame(res["output1"])
                df["rt_cd"] = res.get("rt_cd", "")
                df["msg_cd"] = res.get("msg_cd", "")
                df["msg1"] = res.get("msg1", "")
                return df
            return None
        except Exception as e:
            logging.error(f"기간별손익일별합산 조회 실패: {e}")
            return None

    def get_period_profit(
        self,
        start_date: str,
        end_date: str,
        sort_dvsn: str = "00",
        inqr_dvsn: str = "00",
        cblc_dvsn: str = "00",
    ) -> Optional[Dict]:
        """기간별손익일별합산조회 (Dict 반환) - 일별 손익 합산을 Dict로 조회합니다.

        inquire_period_profit의 Dict 반환 버전입니다.

        Args:
            start_date: 조회시작일자 (YYYYMMDD 형식, 필수)
            end_date: 조회종료일자 (YYYYMMDD 형식, 필수)
            sort_dvsn: 정렬구분 ("00": 역순, "01": 정순)
            inqr_dvsn: 조회구분 ("00": 전체, "01": 입금, "02": 출금)
            cblc_dvsn: 잔고구분 ("00": 전체, "01": 현금, "02": 융자, "03": 대주, "04": 신용)

        Returns:
            Optional[Dict]: 기간별 일별 손익 합산 정보
                - rt_cd: 응답코드 ("0": 성공)
                - output1: 일별 손익 리스트
                - output2: 요약 정보

        Example:
            >>> result = api.get_period_profit("20250101", "20250131")
            >>> if result and result.get('rt_cd') == '0':
            ...     print(f"총손익: {result['output2'].get('tot_rlzt_pfls', '0')}")
        """
        return self.inquire_period_profit(
            start_date, end_date, sort_dvsn, inqr_dvsn, cblc_dvsn, as_dict=True
        )

    def inquire_balance_rlz_pl(self) -> Optional[Dict]:
        """주식잔고조회_실현손익 - 보유 종목의 실현손익 정보를 포함한 잔고를 조회합니다.

        현재 보유 중인 종목의 평가손익과 함께 과거 매매로 인한 실현손익 정보를 제공합니다.
        일반 잔고 조회와 달리 실현손익 계산이 포함되어 있어 전체 투자 성과를 파악할 수 있습니다.

        Returns:
            Optional[Dict]: 실현손익이 포함된 잔고 정보
                - output1: 종목별 잔고 리스트
                    - pdno: 상품번호
                    - prdt_name: 상품명
                    - hldg_qty: 보유수량
                    - pchs_avg_pric: 매입평균가
                    - pchs_amt: 매입금액
                    - prpr: 현재가
                    - evlu_amt: 평가금액
                    - evlu_pfls_amt: 평가손익금액
                    - evlu_pfls_rt: 평가손익률(%)
                    - rlzt_pfls: 실현손익
                    - rlzt_pfls_rt: 실현손익률(%)
                - rt_cd: 결과 코드
                실패 시 None 반환

        Example:
            >>> result = api.inquire_balance_rlz_pl()
            >>> if result:
            ...     holdings = result.get('output1', [])
            ...     # 평가손익과 실현손익 계산
            ...     for item in holdings:
            ...         eval_profit = float(item.get('evlu_pfls_amt', 0))
            ...         realized_profit = float(item.get('rlzt_pfls', 0))
        """
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-balance-rlz-pl",
                tr_id="TTTC8494R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "AFHR_FLPR_YN": "N",
                    "OFL_YN": "",
                    "INQR_DVSN": "00",
                    "UNPR_DVSN": "01",
                    "FUND_STTL_ICLD_YN": "N",
                    "FNCG_AMT_AUTO_RDPT_YN": "N",
                    "PRCS_DVSN": "00",
                    "COST_ICLD_YN": "N",
                    "CTX_AREA_FK100": "",
                    "CTX_AREA_NK100": "",
                },
            )
        except Exception as e:
            logging.error(f"실현손익 잔고 조회 실패: {e}")
            return None

    def inquire_psbl_sell(self, pdno: str) -> Optional[Dict[str, Any]]:
        """매도가능수량조회 - 특정 종목의 매도 가능한 수량을 조회합니다.

        보유 종목 중 매도 가능한 수량을 확인하여 주문 전 검증에 활용합니다.
        미체결 매도 주문 수량을 제외한 실제 매도 가능 수량을 제공합니다.

        Args:
            pdno: 상품번호 (종목코드, 6자리, 필수)

        Returns:
            Optional[Dict[str, Any]]: 매도가능수량 정보를 담은 딕셔너리 (rt_cd 메타데이터가 포함된)
                - output: 조회 결과
                    - ord_psbl_qty: 주문가능수량
                    - ord_psbl_amt: 주문가능금액
                    - pchs_avg_pric: 매입평균가격
                    - hldg_qty: 보유수량
                    - rsvn_ord_psbl_qty: 예약주문가능수량
                실패 시 None 반환

        Example:
            >>> result = api.inquire_psbl_sell("005930")
            >>> if result and result.get('rt_cd') == '0':
            ...     qty = result['output']['ord_psbl_qty']
            ...     print(f"매도가능수량: {qty}주")
        """
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-psbl-sell",
                tr_id="TTTC8408R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": pdno,
                    "ORD_UNPR": "",
                    "ORD_DVSN": "01",
                },
            )
        except Exception as e:
            logging.error(f"매도가능수량 조회 실패: {e}")
            return None

    def order_cash(
        self,
        pdno: str,
        qty: int,
        price: int,
        buy_sell: str,
        order_type: str = "00",
        exchange: str = "KRX",
    ) -> Optional[Dict[str, Any]]:
        """주식주문(현금) - 현금으로 주식을 매수 또는 매도합니다.

        현금 계좌에서 주식 매수/매도 주문을 실행합니다.
        실제 주문이 체결되므로 신중하게 사용해야 합니다.

        Args:
            pdno: 상품번호 (종목코드, 6자리, 필수)
            qty: 주문수량 (1 이상의 정수, 필수)
            price: 주문단가 (원 단위, 시장가는 0, 필수)
            buy_sell: 매수매도구분 (필수)
                - "BUY": 매수
                - "SELL": 매도
            order_type: 주문구분 (기본값: "00")
                [KRX]
                - "00": 지정가
                - "01": 시장가
                - "02": 조건부지정가
                - "03": 최유리지정가
                - "04": 최우선지정가
                - "05": 장전시간외
                - "06": 장후시간외
                - "07": 시간외단일가
                [SOR]
                - "00": 지정가
                - "01": 시장가
                - "03": 최유리지정가
                - "04": 최우선지정가
            exchange: 주문 거래소 (기본값: "KRX")
                - "KRX": 한국거래소
                - "NXT": 대체거래소 (넥스트레이드)
                - "SOR": Smart Order Routing (최적 체결)

        Returns:
            Optional[Dict[str, Any]]: 주문 응답 정보 (rt_cd 메타데이터가 포함된)
                - rt_cd: 응답코드 ("0": 성공)
                - msg1: 응답메시지
                - output: 주문 결과
                    - odno: 주문번호
                    - ord_tmd: 주문시각
                실패 시 None 반환

        Warning:
            실제 주문이 실행되므로 테스트 시에는 소액으로 진행하세요.

        Example:
            >>> # 삼성전자 10주 지정가 매수
            >>> result = api.order_cash("005930", 10, 70000, "BUY")
            >>>
            >>> # 삼성전자 5주 시장가 매도
            >>> result = api.order_cash("005930", 5, 0, "SELL", "01")
            >>>
            >>> # SOR 최유리지정가 매수
            >>> result = api.order_cash("005930", 10, 0, "BUY", "03", "SOR")
        """
        try:
            # TR_ID 결정 (현금 주문은 KRX/NXT 모두 같은 TR ID 사용, EXCD 파라미터로 구분)
            # 매도: TTTC0011U, 매수: TTTC0012U
            tr_id = "TTTC0011U" if buy_sell.upper() == "SELL" else "TTTC0012U"

            # 파라미터 구성
            params = {
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "PDNO": pdno,
                "ORD_DVSN": order_type,
                "ORD_QTY": str(qty),
                "ORD_UNPR": str(price),
            }

            # NXT/SOR 선택 시 거래소 구분 추가
            if exchange != "KRX":
                params["EXCG_ID_DVSN_CD"] = exchange

            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-cash",
                tr_id=tr_id,
                params=params,
                method="POST",  # 주문 API는 POST 메서드 사용
            )
        except Exception as e:
            logging.error(f"현금 주문 실패: {e}")
            return None

    def order_cash_sor(
        self, pdno: str, qty: int, buy_sell: str, order_type: str = "03"
    ) -> Optional[Dict[str, Any]]:
        """SOR 최유리지정가 주문 - Smart Order Routing으로 최적 가격에 주문합니다.

        SOR(Smart Order Routing)을 통해 KRX와 NXT 중 최적의 거래소를 자동 선택하여
        최유리 가격으로 주문을 실행합니다.

        Args:
            pdno: 상품번호 (종목코드, 6자리, 필수)
            qty: 주문수량 (1 이상의 정수, 필수)
            buy_sell: 매수매도구분 (필수)
                - "BUY": 매수
                - "SELL": 매도
            order_type: 주문구분 (기본값: "03" 최유리지정가)
                - "00": 지정가
                - "01": 시장가
                - "03": 최유리지정가 (권장)
                - "04": 최우선지정가

        Returns:
            Optional[Dict[str, Any]]: 주문 응답 정보
                - rt_cd: 응답코드 ("0": 성공)
                - msg1: 응답메시지
                - output: 주문 결과
                    - odno: 주문번호
                    - ord_tmd: 주문시각
                    - excd: 체결 거래소
                실패 시 None 반환

        Example:
            >>> # SOR 최유리지정가 매수
            >>> result = api.order_cash_sor("005930", 10, "BUY")
            >>>
            >>> # SOR 시장가 매도
            >>> result = api.order_cash_sor("005930", 5, "SELL", "01")
        """
        return self.order_cash(
            pdno=pdno,
            qty=qty,
            price=0,  # SOR 최유리지정가는 가격 0
            buy_sell=buy_sell,
            order_type=order_type,
            exchange="SOR",
        )

    def inquire_credit_psamount(self, pdno: str) -> Optional[Dict[str, Any]]:
        """신용매수가능조회 - 신용거래로 매수 가능한 금액과 수량을 조회합니다.

        신용융자를 통해 매수할 수 있는 최대 금액과 수량을 확인합니다.
        신용거래 계좌가 아닌 경우 사용할 수 없습니다.

        Args:
            pdno: 상품번호 (종목코드, 6자리, 필수)

        Returns:
            Optional[Dict[str, Any]]: 신용매수가능 정보 (rt_cd 메타데이터가 포함된)
                - output: 조회 결과
                    - crdt_ord_psbl_amt: 신용주문가능금액
                    - max_buy_qty: 최대매수가능수량
                    - crdt_type: 신용거래구분
                    - loan_amt: 대출금액
                실패 시 None 반환

        Example:
            >>> result = api.inquire_credit_psamount("005930")
            >>> if result and result.get('rt_cd') == '0':
            ...     amt = result['output']['crdt_ord_psbl_amt']
            ...     print(f"신용매수가능금액: {amt}원")
        """
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-credit-psamount",
                tr_id="TTTC8909R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": pdno,
                    "ORD_UNPR": "0",
                    "ORD_DVSN": "00",
                    "CRDT_TYPE": "21",
                    "CRDT_LOAN_DT": "",
                    "CMA_EVLU_AMT_ICLD_YN": "Y",
                    "OVRS_ICLD_YN": "N",
                },
            )
        except Exception as e:
            logging.error(f"신용매수가능 조회 실패: {e}")
            return None

    def order_credit_buy(
        self,
        pdno: str,
        qty: int,
        price: int,
        order_type: str = "00",
        credit_type: str = "21",
        exchange: str = "KRX",
        loan_dt: str = "",
    ) -> Optional[Dict[str, Any]]:
        """주식주문(신용매수) - 신용으로 주식을 매수합니다.

        증권사로부터 자금을 대출받아 주식을 매수합니다.
        신용거래 계좌에서만 사용 가능하며, 이자와 상환 의무가 발생합니다.

        Args:
            pdno: 상품번호 (종목코드, 6자리, 필수)
            qty: 주문수량 (1 이상의 정수, 필수)
            price: 주문단가 (원 단위, 시장가는 0, 필수)
            order_type: 주문구분 (기본값: "00")
                - "00": 지정가
                - "01": 시장가
                - "02": 조건부지정가
                - "03": 최유리지정가 (SOR 사용 시)
            credit_type: 신용거래구분 (기본값: "21")
                - "21": 신용융자매수
                - "22": 자기융자매수 (loan_dt 자동 설정됨)
                - "23": 유통융자매수
            exchange: 주문 거래소 (기본값: "KRX")
                - "KRX": 한국거래소
                - "SOR": Smart Order Routing (최적 체결)
            loan_dt: 대출일자 (YYYYMMDD)
                - 자기융자(credit_type="22")인 경우 자동으로 당일 날짜로 설정됨
                - 명시적으로 지정 가능하지만, 일반적으로 빈 문자열 사용 권장

        Returns:
            Optional[Dict[str, Any]]: 주문 응답 정보 (rt_cd 메타데이터가 포함된)
                - rt_cd: 응답코드 ("0": 성공)
                - output: 주문 결과
                    - odno: 주문번호
                    - ord_tmd: 주문시각
                    - loan_dt: 대출일자
                실패 시 None 반환

        Warning:
            신용거래는 이자와 상환 의무가 발생하므로 신중하게 사용하세요.

        Example:
            >>> # 삼성전자 10주 신용융자 매수
            >>> result = api.order_credit_buy("005930", 10, 70000)

            >>> # 삼성전자 10주 자기융자 매수 (loan_dt 자동 설정)
            >>> result = api.order_credit_buy("005930", 10, 70000, credit_type="22")
        """
        try:
            # 자기융자(credit_type="22")인 경우 loan_dt를 당일 날짜로 자동 설정
            from datetime import datetime

            if credit_type == "22" and not loan_dt:
                loan_dt = datetime.now().strftime("%Y%m%d")

            params = {
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "PDNO": pdno,
                "ORD_DVSN": order_type,
                "ORD_QTY": str(qty),
                "ORD_UNPR": str(price),
                "CRDT_TYPE": credit_type,
                "LOAN_DT": loan_dt,
            }

            # NXT/SOR 선택 시 거래소 구분 추가
            if exchange != "KRX":
                params["EXCG_ID_DVSN_CD"] = exchange

            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-credit",
                tr_id="TTTC0052U",  # 신용매수
                params=params,
                method="POST",  # 주문 API는 POST 메서드 사용
            )
        except Exception as e:
            logging.error(f"신용매수 주문 실패: {e}")
            return None

    def order_credit_sell(
        self,
        pdno: str,
        qty: int,
        price: int,
        order_type: str = "00",
        credit_type: str = "11",
    ) -> Optional[Dict[str, Any]]:
        """주식주문(신용매도) - 신용으로 매수한 주식을 매도합니다.

        신용으로 매수한 주식을 매도하여 대출금을 상환합니다.
        신용매수 종목만 매도 가능합니다.

        Args:
            pdno: 상품번호 (종목코드, 6자리, 필수)
            qty: 주문수량 (1 이상의 정수, 필수)
            price: 주문단가 (원 단위, 시장가는 0, 필수)
            order_type: 주문구분 (기본값: "00")
                - "00": 지정가
                - "01": 시장가
                - "02": 조건부지정가
            credit_type: 신용거래구분 (기본값: "11")
                - "11": 융자상환매도
                - "12": 자기상환매도
                - "61": 대주상환매도

        Returns:
            Optional[Dict[str, Any]]: 주문 응답 정보 (rt_cd 메타데이터가 포함된)
                - rt_cd: 응답코드 ("0": 성공)
                - output: 주문 결과
                    - odno: 주문번호
                    - ord_tmd: 주문시각
                실패 시 None 반환

        Example:
            >>> # 신용매수 종목 매도로 상환
            >>> result = api.order_credit_sell("005930", 10, 75000)
        """
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-credit",
                tr_id="TTTC0051U",  # 신용매도
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": pdno,
                    "ORD_DVSN": order_type,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "CRDT_TYPE": credit_type,
                    "LOAN_DT": "",
                },
                method="POST",  # 주문 API는 POST 메서드 사용
            )
        except Exception as e:
            logging.error(f"신용매도 주문 실패: {e}")
            return None

    def inquire_intgr_margin(self) -> Optional[Dict[str, Any]]:
        """주식통합증거금 현황 - 통합증거금 계좌의 증거금 현황을 조회합니다.

        증거금률, 담보비율, 유지증거금 등 통합증거금 계좌의 주요 지표를 확인합니다.
        통합증거금 계좌가 아닌 경우 조회되지 않습니다.

        Returns:
            Optional[Dict[str, Any]]: 통합증거금 현황 정보 (rt_cd 메타데이터가 포함된)
                - output: 조회 결과
                    - dpsit_rate: 증거금률(%)
                    - cltr_rate: 담보비율(%)
                    - tot_loan_amt: 총대출금액
                    - rcvbl_amt: 미수금액
                    - ordbl_amt: 주문가능금액
                    - thdt_ord_psbl_amt: 당일주문가능금액
                실패 시 None 반환

        Example:
            >>> result = api.inquire_intgr_margin()
            >>> if result and result.get('rt_cd') == '0':
            ...     rate = result['output']['dpsit_rate']
            ...     print(f"증거금률: {rate}%")
        """
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/intgr-margin",
                tr_id="TTTC0869R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "LOAN_DT": "",
                },
            )
        except Exception as e:
            logging.error(f"통합증거금 조회 실패: {e}")
            return None

    def inquire_period_rights(
        self, start_date: str, end_date: str
    ) -> Optional[pd.DataFrame]:
        """기간별계좌권리현황조회 - 특정 기간 동안의 배당, 증자 등 권리 현황을 조회합니다.

        배당금, 주식배당, 증자, 감자, 합병, 분할 등 보유 종목의 권리 사항을 확인합니다.

        Args:
            start_date: 조회시작일자 (YYYYMMDD 형식, 필수)
            end_date: 조회종료일자 (YYYYMMDD 형식, 필수)

        Returns:
            Optional[pd.DataFrame]: 기간별 권리현황 DataFrame
                - pdno: 상품번호
                - prdt_name: 상품명
                - rght_type_name: 권리유형명 (배당, 증자 등)
                - stnd_dt: 기준일자
                - pvnt_dt: 지급일자
                - rght_amt: 권리금액
                - rght_qty: 권리주수
                실패 시 None 반환

        Example:
            >>> # 2025년 1월 권리현황 조회
            >>> df = api.inquire_period_rights("20250101", "20250131")
            >>> if df is not None:
            ...     dividends = df[df['rght_type_name'] == '배당']
            ...     total_div = dividends['rght_amt'].sum()
        """
        try:
            res = self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/period-rights",
                tr_id="CTRGA011R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "STRT_DT": start_date,
                    "END_DT": end_date,
                    "STND_DT": "",
                    "KST_STCK_CNTP_CD": "",
                    "PDNO": "",
                    "MRGN_DVSN": "",
                    "CTX_AREA_FK100": "",
                    "CTX_AREA_NK100": "",
                },
            )
            if res and "output1" in res:
                df = pd.DataFrame(res["output1"])
                # rt_cd 컬럼 추가 (API 응답 성공/실패 추적용)
                df["rt_cd"] = res.get("rt_cd", "")
                df["msg_cd"] = res.get("msg_cd", "")
                df["msg1"] = res.get("msg1", "")
                return df
            return None
        except Exception as e:
            logging.error(f"기간별권리현황 조회 실패: {e}")
            return None

    def inquire_psbl_order(
        self, price: int, pdno: str = "", ord_dvsn: str = "01"
    ) -> Optional[Dict]:
        """
        매수가능 조회

        Args:
            price: 주문 단가
            pdno: 종목코드 (선택)
            ord_dvsn: 주문구분 (01:시장가, 00:지정가 등)

        Returns:
            dict: 매수가능 정보
                - ord_psbl_cash: 주문가능현금
                - max_buy_qty: 최대매수수량
                - ord_psbl_qty: 주문가능수량
        """
        try:
            res = self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-psbl-order",
                tr_id="TTTC8908R" if self.client.is_real else "VTTC8908R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": pdno,
                    "ORD_UNPR": str(price),
                    "ORD_DVSN": ord_dvsn,
                    "CMA_EVLU_AMT_ICLD_YN": "Y",
                    "OVRS_ICLD_YN": "N",
                },
            )
            if res and res.get("rt_cd") == "0":
                return res.get("output", {})
            return None
        except Exception as e:
            logging.error(f"매수가능 조회 실패: {e}")
            return None


# Expose facade class for flat import
__all__ = ["AccountAPI"]
