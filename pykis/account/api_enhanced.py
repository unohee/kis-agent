"""
강화된 Account API - 데코레이터 기반 리팩터링

계좌 관련 API를 데코레이터 패턴으로 리팩터링하고
fail-fast 예외 처리를 적용한 버전
"""

from typing import Optional, Dict, Any, List
import logging
from ..core.base_api import BaseAPI
from ..core.decorators import api_endpoint, deprecated, with_retry, cache_result
from ..core.client import API_ENDPOINTS

logger = logging.getLogger(__name__)


class AccountAPIEnhanced(BaseAPI):
    """계좌 관련 API - 데코레이터 기반 강화 버전"""

    def __init__(self, client, account_info: Dict[str, str], enable_cache=True, cache_config=None):
        """
        계좌 API 초기화

        Args:
            client: KISClient 인스턴스
            account_info: 계좌 정보 (CANO, ACNT_PRDT_CD 포함)
            enable_cache: 캐시 사용 여부
            cache_config: 캐시 설정

        Raises:
            ValueError: 필수 계좌 정보 누락
        """
        if not account_info:
            raise ValueError("계좌 정보가 필요합니다")

        if 'CANO' not in account_info or 'ACNT_PRDT_CD' not in account_info:
            raise ValueError("CANO와 ACNT_PRDT_CD가 필요합니다")

        super().__init__(client, account_info, enable_cache, cache_config)

    # ========== 계좌 잔고 조회 API ==========

    @api_endpoint('INQUIRE_BALANCE', 'TTTC8434R')
    @cache_result(ttl=5)  # 5초 캐시
    def get_balance_holdings(self) -> Dict[str, Any]:
        """
        보유종목 및 잔고 조회

        Returns:
            보유종목 및 잔고 정보

        Raises:
            Exception: API 호출 실패 (fail-fast)
        """
        return {
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
        }

    @api_endpoint('INQUIRE_PSBL_ORDER', 'TTTC8908R')
    def get_order_capacity(self, stock_code: str = "005930") -> Dict[str, Any]:
        """
        주문 가능 금액 조회

        Args:
            stock_code: 조회할 종목코드 (기본: 삼성전자)

        Returns:
            주문 가능 금액 정보

        Raises:
            ValueError: 잘못된 종목코드
            Exception: API 호출 실패 (fail-fast)
        """
        if not stock_code or len(stock_code) != 6:
            raise ValueError(f"잘못된 종목코드: {stock_code}")

        return {
            "CANO": self.account["CANO"],
            "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
            "PDNO": stock_code,
            "ORD_UNPR": "0",
            "ORD_DVSN": "00",
            "CMA_EVLU_AMT_ICLD_YN": "Y",
            "OVRS_ICLD_YN": "N",
        }

    @api_endpoint('INQUIRE_CREDIT_PSAMOUNT', 'TTTC1200R')
    def get_credit_capacity(self, stock_code: str = "005930") -> Dict[str, Any]:
        """
        신용 주문 가능 금액 조회

        Args:
            stock_code: 조회할 종목코드 (기본: 삼성전자)

        Returns:
            신용 주문 가능 금액 정보

        Raises:
            ValueError: 잘못된 종목코드
            Exception: API 호출 실패 (fail-fast)
        """
        if not stock_code or len(stock_code) != 6:
            raise ValueError(f"잘못된 종목코드: {stock_code}")

        return {
            "CANO": self.account["CANO"],
            "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
            "PDNO": stock_code,
            "ORD_UNPR": "0",
            "ORD_DVSN": "00",
            "CDIT_LOAN_IAMT_AUTO_RDPT_YN": "N",
            "KRW_AUTO_BUY_FCCY_EXEC_YN": "N",
        }

    # ========== 주문 내역 조회 API ==========

    @api_endpoint('INQUIRE_DAILY_ORDER', 'TTTC8001R')
    def get_orders_today(self) -> Dict[str, Any]:
        """
        당일 주문 내역 조회

        Returns:
            당일 주문 내역

        Raises:
            Exception: API 호출 실패 (fail-fast)
        """
        return {
            "CANO": self.account["CANO"],
            "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
            "INQR_STRT_DT": "",  # 오늘
            "INQR_END_DT": "",    # 오늘
            "SLL_BUY_DVSN_CD": "00",  # 전체
            "INQR_DVSN": "00",
            "PDNO": "",
            "CCLD_DVSN": "00",  # 전체 (체결/미체결)
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "INQR_DVSN_2": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

    @api_endpoint('INQUIRE_BALANCE_RLZPL', 'TTTC8494R')
    def get_realized_profit(self) -> Dict[str, Any]:
        """
        실현손익 조회

        Returns:
            실현손익 정보

        Raises:
            Exception: API 호출 실패 (fail-fast)
        """
        return {
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
        }

    # ========== 예수금 조회 API ==========

    @api_endpoint('INQUIRE_PURCHASE_AMOUNT', 'TTTC8012R')
    def get_deposit_info(self) -> Dict[str, Any]:
        """
        예수금 조회

        Returns:
            예수금 정보

        Raises:
            Exception: API 호출 실패 (fail-fast)
        """
        return {
            "CANO": self.account["CANO"],
            "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
            "INQR_DVSN_1": "",
            "BSPR_BF_DT_APLY_YN": "",
        }

    # ========== 유틸리티 메서드 ==========

    def get_total_assets(self) -> Optional[Dict[str, Any]]:
        """
        총 자산 정보 계산

        Returns:
            총 자산 정보 (예수금, 주식평가액, 총자산, 손익 등)

        Raises:
            Exception: 계산 실패
        """
        try:
            # 잔고 조회
            balance_result = self.get_balance_holdings()
            if not balance_result or balance_result.get('rt_cd') != '0':
                raise Exception(f"잔고 조회 실패: {balance_result.get('msg1', '알 수 없는 오류')}")

            output2 = balance_result.get('output2', [{}])[0]

            # 총 자산 정보 구성
            total_assets = {
                "예수금": int(output2.get("dnca_tot_amt", 0)),
                "D+2예수금": int(output2.get("nxdy_excc_amt", 0)),
                "주식평가액": int(output2.get("evlu_amt_smtl_amt", 0)),
                "평가손익": int(output2.get("evlu_pfls_smtl_amt", 0)),
                "총자산": int(output2.get("tot_evlu_amt", 0)),
                "수익률": float(output2.get("erng_rt", 0)),
            }

            # 보유종목 정보 추가
            holdings = balance_result.get('output1', [])
            total_assets["보유종목수"] = len(holdings)

            return total_assets

        except Exception as e:
            logger.error(f"총 자산 계산 실패: {e}")
            raise

    def get_holdings_summary(self) -> Optional[List[Dict[str, Any]]]:
        """
        보유종목 요약 정보

        Returns:
            보유종목 요약 리스트

        Raises:
            Exception: 조회 실패
        """
        try:
            balance_result = self.get_balance_holdings()
            if not balance_result or balance_result.get('rt_cd') != '0':
                raise Exception(f"잔고 조회 실패: {balance_result.get('msg1', '알 수 없는 오류')}")

            holdings = balance_result.get('output1', [])
            summary = []

            for holding in holdings:
                summary.append({
                    "종목코드": holding.get("pdno"),
                    "종목명": holding.get("prdt_name"),
                    "보유수량": int(holding.get("hldg_qty", 0)),
                    "매입단가": int(holding.get("pchs_avg_pric", 0)),
                    "현재가": int(holding.get("prpr", 0)),
                    "평가금액": int(holding.get("evlu_amt", 0)),
                    "평가손익": int(holding.get("evlu_pfls_amt", 0)),
                    "수익률": float(holding.get("evlu_pfls_rt", 0)),
                })

            return summary

        except Exception as e:
            logger.error(f"보유종목 요약 조회 실패: {e}")
            raise

    # ========== 하위 호환성을 위한 Alias 메서드 ==========

    @deprecated(alternative="get_balance_holdings")
    def get_account_balance(self) -> Optional[Dict]:
        """Deprecated: Use get_balance_holdings() instead"""
        return self.get_balance_holdings()

    @deprecated(alternative="get_order_capacity")
    def get_cash_available(self, stock_code: str = "005930") -> Optional[Dict]:
        """Deprecated: Use get_order_capacity() instead"""
        return self.get_order_capacity(stock_code)

    @deprecated(alternative="get_order_capacity")
    def inquire_psbl_order(self, stock_code: str = "005930") -> Optional[Dict]:
        """Deprecated: Use get_order_capacity() instead"""
        return self.get_order_capacity(stock_code)

    @deprecated(alternative="get_credit_capacity")
    def inquire_credit_psamount(self, stock_code: str = "005930") -> Optional[Dict]:
        """Deprecated: Use get_credit_capacity() instead"""
        return self.get_credit_capacity(stock_code)