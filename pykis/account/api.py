import pandas as pd
from ..core.client import KISClient, API_ENDPOINTS
from typing import Optional, Dict, Any
import logging

"""
account.py - 계좌 정보 조회 전용 모듈

이 모듈은 한국투자증권 OpenAPI를 통해 다음과 같은 기능을 제공합니다:
- 보유 종목 및 잔고 조회
- 현금 매수 가능 금액 조회
- 총 자산 평가 (예수금, 주식, 평가손익 등 포함)

✅ 의존:
- client.py: 모든 API 요청은 이 객체를 통해 수행됩니다.

🔗 연관 모듈:
- stock.py: 종목 단위 시세 및 주문 API 담당
- program.py: 프로그램 매매 추이 및 순매수량 확인
- (전략 관련 모듈은 deprecated되어 제거됨)

💡 사용 예시:
client = KISClient()
account = AccountAPI(client, {"CANO": "12345678", "ACNT_PRDT_CD": "01"})
df = account.get_account_balance()
"""

class AccountAPI:
    def __init__(self, client: KISClient, account_info: Dict[str, str]):
        """Wrapper around KIS account related endpoints.

        Parameters
        ----------
        client : :class:`KISClient`
            Authenticated client instance.
        account_info : dict
            Dictionary with ``CANO`` and ``ACNT_PRDT_CD`` keys. Values are
            usually loaded from ``credit/kis_devlp.yaml``.

        Example
        -------
        >>> account = load_account_info()
        >>> api = AccountAPI(KISClient(), account)
        """
        self.client = client
        self.account = account_info  # { 'CANO': '12345678', 'ACNT_PRDT_CD': '01' }

    def get_account_balance(self) -> Optional[pd.DataFrame]:
        """Return current holdings and profit/loss information.

        Returns
        -------
        Optional[pandas.DataFrame]
            ``output1`` from the API on success.

        Example
        -------
        >>> api.get_account_balance().head()
        """
        res = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-balance",
            tr_id="TTTC8434R",
            params={
                "CANO": self.account['CANO'],
                "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "01",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "00",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
        )
        if res and 'output1' in res:
            return pd.DataFrame(res['output1'])
        return None

    def get_cash_available(self) -> Optional[Dict[str, Any]]:
        """Query available cash for trading.

        Returns
        -------
        Optional[dict]
            Response JSON with ``rt_cd`` and ``cash`` fields.

        Example
        -------
        >>> api.get_cash_available()
        """
        res = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-available-amount",
            tr_id="TTTC8901R",
            params={
                "CANO": self.account['CANO'],
                "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                "CASH_CLO_CD": "10",
                "TR_MKET_CD": "0"
            }
        )
        # 새벽 정산 시간(404/JSONDecodeError) 안내 메시지 추가
        if res is not None and (res.get('rt_cd') == 'JSON_DECODE_ERROR' or res.get('status_code') == 404):
            # 변경 이유: 새벽 정산 시간에는 계좌 관련 API가 일시적으로 차단되어 혼동 방지 목적 안내 메시지 추가
            return {"rt_cd": res.get('rt_cd', ''), "msg1": res.get('msg1', ''), "정산안내": "정산 시간(23:30~01:00 등)에는 계좌 관련 API가 일시적으로 차단될 수 있습니다. 잠시 후 다시 시도해 주세요."}
        return res

    def get_total_asset(self) -> Optional[Dict[str, Any]]:
        """Total asset evaluation including cash and stocks.

        Returns
        -------
        Optional[dict]
            JSON structure describing account summary.

        Example
        -------
        >>> api.get_total_asset()
        """
        res = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-account-summary",
            tr_id="TTTC8522R",
            params={
                "CANO": self.account['CANO'],
                "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                "INQR_DVSN": "02",  # 01: 잔고 기준, 02: 평가 기준
                "UNPR_DVSN": "01"   # 01: 현재가 기준
            }
        )
        # 새벽 정산 시간(404/JSONDecodeError) 안내 메시지 추가
        if res is not None and (res.get('rt_cd') == 'JSON_DECODE_ERROR' or res.get('status_code') == 404):
            # 변경 이유: 새벽 정산 시간에는 계좌 관련 API가 일시적으로 차단되어 혼동 방지 목적 안내 메시지 추가
            return {"rt_cd": res.get('rt_cd', ''), "msg1": res.get('msg1', ''), "정산안내": "정산 시간(23:30~01:00 등)에는 계좌 관련 API가 일시적으로 차단될 수 있습니다. 잠시 후 다시 시도해 주세요."}
        return res

    def get_account_order_quantity(self, code: str) -> Optional[Dict]:
        """계좌별 주문 수량 조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-account-order-quantity",
                tr_id="TTTC8434R",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PDNO": code,
                    "ORD_UNPR": "0",
                    "CTX_AREA_FK200": "",
                    "CTX_AREA_NK200": ""
                }
            )
        except Exception as e:
            logging.error(f"계좌별 주문 수량 조회 실패: {e}")
            return None

    def get_possible_order_amount(self) -> Optional[Dict]:
        """주문 가능 금액 조회"""
        try:
            return self.client.make_request(
                endpoint=API_ENDPOINTS['INQUIRE_PSBL_ORDER'],
                tr_id="TTTC8908R",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PDNO": "",
                    "ORD_UNPR": "0",
                    "ORD_DVSN": "00",
                    "CMA_EVLU_AMT_ICLD_YN": "Y",
                    "OVRS_ICLD_YN": "N"
                }
            )
        except Exception as e:
            logging.error(f"주문 가능 금액 조회 실패: {e}")
            return None

    def order_credit(self, code: str, qty: int, price: int, order_type: str) -> Optional[Dict]:
        """주식주문(신용)"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-credit",
                tr_id="TTTC0852U",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PDNO": code,
                    "CRDT_TYPE": "21",
                    "LOAN_DT": "",
                    "ORD_DVSN": order_type,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price)
                }
            )
        except Exception as e:
            logging.error(f"신용 주문 실패: {e}")
            return None

    def order_rvsecncl(self, org_order_no: str, qty: int, price: int, order_type: str, cncl_type: str) -> Optional[Dict]:
        """주식주문(정정취소)"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-rvsecncl",
                tr_id="TTTC0803U",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "KRX_FWDG_ORD_ORGNO": "",
                    "ORGN_ODNO": org_order_no,
                    "ORD_DVSN": order_type,
                    "RVSE_CNCL_DVSN_CD": cncl_type,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "QTY_ALL_ORD_YN": "Y"
                }
            )
        except Exception as e:
            logging.error(f"정정/취소 주문 ��패: {e}")
            return None

    def inquire_psbl_rvsecncl(self) -> Optional[Dict]:
        """주식정정취소가능주문조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl",
                tr_id="TTTC8036R",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "CTX_AREA_FK100": "",
                    "CTX_AREA_NK100": "",
                    "INQR_DVSN_1": "1",
                    "INQR_DVSN_2": "0"
                }
            )
        except Exception as e:
            logging.error(f"정정/취소 가능 주문 조회 실패: {e}")
            return None

    def order_resv(self, code: str, qty: int, price: int, order_type: str) -> Optional[Dict]:
        """주식예약주문"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-resv",
                tr_id="CTSC0008U",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PDNO": code,
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "SLL_BUY_DVSN_CD": "02",
                    "ORD_DVSN_CD": order_type,
                    "ORD_OBJT_CBLC_DVSN_CD": "10"
                }
            )
        except Exception as e:
            logging.error(f"예약 주문 실패: {e}")
            return None

    def order_resv_rvsecncl(self, seq: int, qty: int, price: int, order_type: str) -> Optional[Dict]:
        """주식예약주문정정취소"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-resv-rvsecncl",
                tr_id="CTSC0013U",
                params={
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PDNO": "",
                    "ORD_QTY": str(qty),
                    "ORD_UNPR": str(price),
                    "SLL_BUY_DVSN_CD": "02",
                    "ORD_DVSN_CD": order_type,
                    "ORD_OBJT_CBLC_DVSN_CD": "10",
                    "RSVN_ORD_SEQ": str(seq)
                }
            )
        except Exception as e:
            logging.error(f"예약 주문 정정/취소 실패: {e}")
            return None

    def order_resv_ccnl(self) -> Optional[Dict]:
        """주식예약주문조회"""
        try:
            return self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/order-resv-ccnl",
                tr_id="CTSC0004R",
                params={
                    "RSVN_ORD_ORD_DT": "",
                    "RSVN_ORD_END_DT": "",
                    "RSVN_ORD_SEQ": "",
                    "TMNL_MDIA_KIND_CD": "00",
                    "CANO": self.account['CANO'],
                    "ACNT_PRDT_CD": self.account['ACNT_PRDT_CD'],
                    "PRCS_DVSN_CD": "0",
                    "CNCL_YN": "Y",
                    "PDNO": "",
                    "SLL_BUY_DVSN_CD": "",
                    "CTX_AREA_FK200": "",
                    "CTX_AREA_NK200": ""
                }
            )
        except Exception as e:
            logging.error(f"예약 주문 조회 실패: {e}")
            return None



# Expose facade class for flat import
__all__ = ['AccountAPI']
