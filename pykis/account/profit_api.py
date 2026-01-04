"""계좌 손익 및 체결 조회 API 모듈.

일별 체결, 기간별 손익, 권리현황 등 손익/체결 조회 기능 제공.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from ..core.base_api import BaseAPI
from ..core.client import KISClient


class AccountProfitAPI(BaseAPI):
    """계좌 손익 및 체결 조회 API."""

    def __init__(
        self,
        client: KISClient,
        account_info: Dict[str, str],
        enable_cache=True,
        cache_config=None,
        _from_agent=False,
    ):
        """초기화. account_info에 CANO/ACNT_PRDT_CD 필요."""
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

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
        """일별주문체결조회. pagination=True로 연속조회(100건+)."""
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

        try:
            today = datetime.now()
            three_months_ago = (today - timedelta(days=90)).strftime("%Y%m%d")
            tr_id = (
                "CTSC9215R"
                if start_date and start_date < three_months_ago
                else "TTTC0081R"
            )

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
                    "CCLD_DVSN": "00",
                    "ORD_GNO_BRNO": "",
                    "ODNO": "",
                    "INQR_DVSN_3": "00",
                    "INQR_DVSN_1": "",
                    "CTX_AREA_FK100": "",
                    "CTX_AREA_NK100": "",
                },
            )
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
        """내부 헬퍼: 연속조회키로 페이지네이션."""
        all_data = []
        ctx_area_fk100 = ""
        ctx_area_nk100 = ""
        page_count = 0

        today = datetime.now()
        three_months_ago = (today - timedelta(days=90)).strftime("%Y%m%d")
        tr_id = (
            "CTSC9215R" if start_date and start_date < three_months_ago else "TTTC0081R"
        )

        try:
            while page_count < max_pages:
                req_headers = {}
                if page_count > 0:
                    req_headers["tr_cont"] = "N"

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

                if not res or res.get("rt_cd") != "0":
                    if page_count == 0:
                        logging.error(
                            f"일별주문체결 조회 실패: {res.get('msg1', 'Unknown error') if res else 'No response'}"
                        )
                        return None
                    else:
                        logging.warning(
                            f"페이지 {page_count + 1} 조회 실패, 현재까지 데이터 반환"
                        )
                        break

                output1 = res.get("output1", [])
                if not output1:
                    break

                all_data.extend(output1)
                page_count += 1

                if page_callback:
                    ctx_info = {
                        "FK100": res.get("ctx_area_fk100", ""),
                        "NK100": res.get("ctx_area_nk100", ""),
                        "total_rows": len(output1),
                    }
                    page_callback(page_count, output1, ctx_info)

                ctx_area_fk100 = res.get("ctx_area_fk100", "").strip()
                ctx_area_nk100 = res.get("ctx_area_nk100", "").strip()

                msg1 = res.get("msg1", "").strip()
                is_continue = "계속" in msg1 or "조회가 계속됩니다" in msg1

                if not is_continue:
                    break
                if not ctx_area_fk100 and not ctx_area_nk100:
                    break
                if len(output1) < 100:
                    break

            if all_data:
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

                if unique_data:
                    unique_data.sort(
                        key=lambda x: (x.get("ord_dt", ""), x.get("ord_tmd", "")),
                        reverse=(inqr_dvsn == "00"),
                    )

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

                output2 = {
                    "tot_ord_qty": str(tot_ord_qty),
                    "tot_ccld_qty": str(tot_ccld_qty),
                    "tot_ccld_amt": str(tot_ccld_amt),
                    "page_count": page_count,
                    "total_count": len(unique_data),
                }

                if res and "output2" in res:
                    last_output2 = res.get("output2", {})
                    if "prsm_tlex_smtl" in last_output2:
                        output2["prsm_tlex_smtl"] = last_output2["prsm_tlex_smtl"]
                    if "pchs_avg_pric" in last_output2:
                        output2["pchs_avg_pric"] = last_output2["pchs_avg_pric"]

                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESSFUL",
                    "msg1": f"정상처리 완료 - 총 {len(unique_data)}건 조회",
                    "output1": unique_data,
                    "output2": output2,
                }

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
                return res

            if res and "output1" in res:
                df = pd.DataFrame(res["output1"])
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
        """기간별매매손익합산조회 - Dict 반환 버전."""
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
        """기간별손익일별합산조회 - 일별 손익 합산 조회."""
        try:
            res = self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-period-profit",
                tr_id="TTTC8708R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "PDNO": "",
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
        """기간별손익일별합산조회 (Dict 반환)."""
        return self.inquire_period_profit(
            start_date, end_date, sort_dvsn, inqr_dvsn, cblc_dvsn, as_dict=True
        )

    def inquire_period_rights(
        self, start_date: str, end_date: str
    ) -> Optional[pd.DataFrame]:
        """기간별계좌권리현황조회 - 배당, 증자 등 권리 현황 조회."""
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
                df["rt_cd"] = res.get("rt_cd", "")
                df["msg_cd"] = res.get("msg_cd", "")
                df["msg1"] = res.get("msg1", "")
                return df
            return None
        except Exception as e:
            logging.error(f"기간별권리현황 조회 실패: {e}")
            return None
