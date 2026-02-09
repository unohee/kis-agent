"""
한국투자증권 API의 계좌 잔고 조회 기능을 제공하는 모듈입니다.

이 모듈은 한국투자증권 OpenAPI를 통해 다음과 같은 기능을 제공합니다:
- 보유 종목 및 잔고 조회
- 현금 매수 가능 금액 조회
- 총 자산 평가 (예수금, 주식, 평가손익 등 포함)

의존성:
- kis.core.client.KISClient: 모든 API 요청은 이 객체를 통해 수행됩니다.

연관 모듈:
- kis.stock: 종목 단위 시세 및 주문 API 담당
- kis.program: 프로그램 매매 추이 및 순매수량 확인
- (전략 관련 모듈은 deprecated되어 제거됨)

사용 예시:
    >>> client = KISClient()
    >>> account = AccountAPI(client, {"CANO": "12345678", "ACNT_PRDT_CD": "01"})
    >>> df = account.get_account_balance()
"""

from typing import Any, Dict, Optional

import pandas as pd

from ..core.client import KISClient


class AccountAPI:
    """
    한국투자증권 API의 계좌 잔고 조회 기능을 제공하는 클래스입니다.

    이 클래스는 계좌 잔고 조회, 현금 조회, 자산 평가 등의 기능을 제공합니다.

    Attributes:
        client (KISClient): API 통신을 담당하는 클라이언트
        account (Dict[str, str]): 계좌 정보
            - CANO (str): 계좌번호
            - ACNT_PRDT_CD (str): 계좌상품코드

    Example:
        >>> client = KISClient()
        >>> account = AccountAPI(client, {"CANO": "12345678", "ACNT_PRDT_CD": "01"})
        >>> balance = account.get_account_balance()
        >>> cash = account.get_cash_available()
        >>> total = account.get_total_asset()
    """

    def __init__(self, client: KISClient, account_info: Dict[str, str]):
        """
        AccountAPI를 초기화합니다.

        Args:
            client (KISClient): API 통신을 담당하는 클라이언트
            account_info (Dict[str, str]): 계좌 정보
                - CANO (str): 계좌번호
                - ACNT_PRDT_CD (str): 계좌상품코드

        Example:
            >>> account = load_account_info()
            >>> api = AccountAPI(KISClient(), account)
        """
        self.client = client
        self.account = account_info  # { 'CANO': '12345678', 'ACNT_PRDT_CD': '01' }

    def get_account_balance(self) -> Optional[pd.DataFrame]:
        """
        현재 보유 종목 및 손익 정보를 조회합니다.

        Returns:
            Optional[pd.DataFrame]: API 응답의 output1 필드를 DataFrame으로 변환한 결과
                - 성공 시: 보유 종목 및 손익 정보가 포함된 DataFrame
                - 실패 시: None

        Example:
            >>> api.get_account_balance().head()
        """
        res = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-balance",
            tr_id="TTTC8434R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
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

    def get_cash_available(self) -> Optional[Dict[str, Any]]:
        """
        매매 가능한 현금을 조회합니다.

        Returns:
            Optional[Dict[str, Any]]: API 응답 데이터
                - 성공 시: rt_cd와 cash 필드를 포함한 응답 데이터
                - 실패 시: 에러 정보를 포함한 응답 데이터
                - 정산 시간: 정산 시간 안내 메시지를 포함한 응답 데이터

        Note:
            정산 시간(23:30~01:00 등)에는 계좌 관련 API가 일시적으로 차단될 수 있습니다.

        Example:
            >>> api.get_cash_available()
        """
        res = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-available-amount",
            tr_id="TTTC8901R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "CASH_CLO_CD": "10",
                "TR_MKET_CD": "0",
            },
        )
        # 새벽 정산 시간(404/JSONDecodeError) 안내 메시지 추가
        if res is not None and (
            res.get("rt_cd") == "JSON_DECODE_ERROR" or res.get("status_code") == 404
        ):
            return {
                "rt_cd": res.get("rt_cd", ""),
                "msg1": res.get("msg1", ""),
                "정산안내": (
                    "정산 시간(23:30~01:00 등)에는 계좌 관련 API가 "
                    "일시적으로 차단될 수 있습니다. 잠시 후 다시 시도해 주세요."
                ),
            }
        return res

    def get_total_asset(self) -> Optional[Dict[str, Any]]:
        """
        현금과 주식을 포함한 총 자산을 평가합니다.

        Returns:
            Optional[Dict[str, Any]]: API 응답 데이터
                - 성공 시: 계좌 요약 정보를 포함한 응답 데이터
                - 실패 시: 에러 정보를 포함한 응답 데이터
                - 정산 시간: 정산 시간 안내 메시지를 포함한 응답 데이터

        Note:
            정산 시간(23:30~01:00 등)에는 계좌 관련 API가 일시적으로 차단될 수 있습니다.

        Example:
            >>> api.get_total_asset()
        """
        res = self.client.make_request(
            endpoint="/uapi/domestic-stock/v1/trading/inquire-account-summary",
            tr_id="TTTC8522R",
            params={
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "INQR_DVSN": "02",  # 01: 잔고 기준, 02: 평가 기준
                "UNPR_DVSN": "01",  # 01: 현재가 기준
            },
        )
        # 새벽 정산 시간(404/JSONDecodeError) 안내 메시지 추가
        if res is not None and (
            res.get("rt_cd") == "JSON_DECODE_ERROR" or res.get("status_code") == 404
        ):
            return {
                "rt_cd": res.get("rt_cd", ""),
                "msg1": res.get("msg1", ""),
                "정산안내": (
                    "정산 시간(23:30~01:00 등)에는 계좌 관련 API가 "
                    "일시적으로 차단될 수 있습니다. 잠시 후 다시 시도해 주세요."
                ),
            }
        return res


# 기존 호환성을 위해 별칭 제공
AccountBalance = AccountAPI
AccountBalanceAPI = AccountAPI
