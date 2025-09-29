import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS, KISClient

"""
account.py - 계좌 정보 조회 전용 모듈

이 모듈은 한국투자증권 OpenAPI를 통해 다음과 같은 기능을 제공합니다:
- 보유 종목 및 잔고 조회
- 현금 매수 가능 금액 조회
- 총 자산 평가 (예수금, 주식, 평가손익 등 포함)

 의존:
- client.py: 모든 API 요청은 이 객체를 통해 수행됩니다.

 연관 모듈:
- stock.py: 종목 단위 시세 및 주문 API 담당
- program.py: 프로그램 매매 추이 및 순매수량 확인
- (전략 관련 모듈은 deprecated되어 제거됨)

 사용 예시:
client = KISClient()
account = AccountAPI(client, {"CANO": "12345678", "ACNT_PRDT_CD": "01"})
df = account.get_account_balance()
"""


class AccountAPI(BaseAPI):
    def __init__(
        self,
        client: KISClient,
        account_info: Dict[str, str],
        enable_cache=True,
        cache_config=None,
    ):
        """Wrapper around KIS account related endpoints.

        Parameters
        ----------
        client : :class:`KISClient`
            Authenticated client instance.
        account_info : dict
            Dictionary with ``CANO`` and ``ACNT_PRDT_CD`` keys.
        enable_cache : bool
            캐시 사용 여부 (기본: True)
        cache_config : dict
            캐시 설정 (default_ttl, max_size)

        Example
        -------
        >>> account = load_account_info()
        >>> api = AccountAPI(KISClient(), account)
        """
        super().__init__(client, account_info, enable_cache, cache_config)

    def get_account_balance(self) -> Optional[Dict]:
        """Return current holdings and profit/loss information.

        Returns
        -------
        Optional[Dict]
            API response with rt_cd metadata included.

        Example
        -------
        >>> result = api.get_account_balance()
        >>> if result:
        >>>     holdings = result.get('output1', [])
        """
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
        """Query available cash for purchasing specific stock.

        Args
        ----
        stock_code : str, default "005930"
            Stock code to check purchase availability (default: Samsung Electronics)

        Returns
        -------
        Optional[dict]
            Response JSON with purchase availability information (rt_cd 메타데이터가 포함된).
            - ord_psbl_cash: Available cash for purchase
            - ord_psbl_sbst: Available substitution amount
            - max_buy_qty: Maximum purchasable quantity

        Example
        -------
        >>> api.get_cash_available("005930")  # Samsung Electronics
        >>> api.get_cash_available("000660")  # SK Hynix
        """
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
        """Query total asset evaluation including cash and stocks.

        Returns
        -------
        Optional[dict]
            JSON structure describing investment account balance (rt_cd 메타데이터가 포함된).
            - output1: Account summary information
            - output2: Detailed balance information

        Example
        -------
        >>> api.get_total_asset()
        """
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
        """
        계좌별 주문 수량 조회

        특정 종목에 대한 계좌별 주문 가능 수량과 관련 정보를 조회합니다.

        Args:
            code (str): 종목코드 (6자리, 예: "005930")

        Returns:
            Optional[Dict]: 계좌별 주문 수량 정보
                - 성공 시: rt_cd와 함께 주문 수량 정보 딕셔너리
                - 실패 시: None

        Example:
            >>> account_api = AccountAPI(client, account_info)
            >>> result = account_api.get_account_order_quantity("005930")
            >>> if result and result.get('rt_cd') == '0':
            ...     print(f"주문 가능 수량: {result['output']['ord_psbl_qty']}")
        """
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
        """
        주문 가능 금액 조회

        현재 계좌의 주문 가능한 금액과 관련 정보를 조회합니다.

        Returns:
            Optional[Dict]: 주문 가능 금액 정보
                - 성공 시: rt_cd와 함께 주문 가능 금액 정보 딕셔너리
                - 실패 시: None

        Example:
            >>> account_api = AccountAPI(client, account_info)
            >>> result = account_api.get_possible_order_amount()
            >>> if result and result.get('rt_cd') == '0':
            ...     available_amount = result['output']['ord_psbl_amt']
            ...     print(f"주문 가능 금액: {available_amount:,}원")
        """
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
        """
        주식 신용주문

        신용거래로 주식을 주문합니다. 실제 주문이 실행되므로 주의하세요.

        Args:
            code (str): 종목코드 (6자리, 예: "005930")
            qty (int): 주문 수량
            price (int): 주문 단가 (시장가는 0)
            order_type (str): 주문 구분 ("00": 지정가, "01": 시장가)

        Returns:
            Optional[Dict]: 신용주문 응답
                - 성공 시: rt_cd와 함께 주문 결과 정보 딕셔너리
                - 실패 시: None

        Warning:
            실제 신용주문이 실행되므로 테스트 시 소액으로 진행하세요.

        Example:
            >>> account_api = AccountAPI(client, account_info)
            >>> result = account_api.order_credit("005930", 10, 70000, "00")
            >>> if result and result.get('rt_cd') == '0':
            ...     print(f"주문번호: {result['output']['odno']}")
        """
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
            )
        except Exception as e:
            logging.error(f"신용 주문 실패: {e}")
            return None

    def order_rvsecncl(
        self, org_order_no: str, qty: int, price: int, order_type: str, cncl_type: str
    ) -> Optional[Dict]:
        """
        주식주문 정정/취소

        기존 주문을 정정하거나 취소합니다.

        Args:
            org_order_no (str): 원주문번호
            qty (int): 정정 수량 (취소시 0)
            price (int): 정정 단가 (취소시 0)
            order_type (str): 주문 구분
            cncl_type (str): 정정취소 구분 ("정정" 또는 "취소")

        Returns:
            Optional[Dict]: 정정/취소 응답
                - 성공 시: rt_cd와 함께 정정/취소 결과 정보
                - 실패 시: None
        """
        try:
            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-rvsecncl",
                tr_id="TTTC0803U",
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
            )
        except Exception as e:
            logging.error(f"정정/취소 주문 ��패: {e}")
            return None

    def inquire_psbl_rvsecncl(self) -> Optional[Dict]:
        """
        정정/취소 가능 주문 조회

        현재 정정하거나 취소할 수 있는 미체결 주문을 조회합니다.

        Returns:
            Optional[Dict]: 정정/취소 가능 주문 목록
                - 성공 시: rt_cd와 함께 주문 정보 리스트
                - 실패 시: None

        Example:
            >>> account_api = AccountAPI(client, account_info)
            >>> result = account_api.inquire_psbl_rvsecncl()
            >>> if result and result.get('rt_cd') == '0':
            ...     for order in result['output']:
            ...         print(f"주문번호: {order['odno']}")
        """
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
        """
        주식 예약주문

        지정된 시점에 주문이 실행되도록 예약주문을 등록합니다.

        Args:
            code (str): 종목코드 (6자리)
            qty (int): 주문 수량
            price (int): 주문 단가
            order_type (str): 주문 구분

        Returns:
            Optional[Dict]: 예약주문 응답
                - 성공 시: rt_cd와 함께 예약주문 결과
                - 실패 시: None

        Example:
            >>> account_api = AccountAPI(client, account_info)
            >>> result = account_api.order_resv("005930", 10, 70000, "00")
            >>> if result and result.get('rt_cd') == '0':
            ...     print(f"예약주문 등록: {result['output']['odno']}")
        """
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
            )
        except Exception as e:
            logging.error(f"예약 주문 실패: {e}")
            return None

    def order_resv_rvsecncl(
        self, seq: int, qty: int, price: int, order_type: str
    ) -> Optional[Dict]:
        """
        예약주문 정정/취소

        등록된 예약주문을 정정하거나 취소합니다.

        Args:
            seq (int): 예약주문 일련번호
            qty (int): 정정 수량
            price (int): 정정 단가
            order_type (str): 주문 구분

        Returns:
            Optional[Dict]: 예약주문 정정/취소 응답
                - 성공 시: rt_cd와 함께 정정/취소 결과
                - 실패 시: None

        Example:
            >>> account_api = AccountAPI(client, account_info)
            >>> result = account_api.order_resv_rvsecncl(123, 5, 75000, "00")
            >>> if result and result.get('rt_cd') == '0':
            ...     print("예약주문 정정 완료")
        """
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
            )
        except Exception as e:
            logging.error(f"예약 주문 정정/취소 실패: {e}")
            return None

    def order_resv_ccnl(self) -> Optional[Dict]:
        """
        예약주문 조회

        등록된 예약주문 내역을 조회합니다.

        Returns:
            Optional[Dict]: 예약주문 내역
                - 성공 시: rt_cd와 함께 예약주문 리스트
                - 실패 시: None

        Example:
            >>> account_api = AccountAPI(client, account_info)
            >>> result = account_api.order_resv_ccnl()
            >>> if result and result.get('rt_cd') == '0':
            ...     for order in result['output']:
            ...         print(f"예약주문: {order['pdno']} {order['ord_qty']}주")
        """
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
        """주식일별주문체결조회 - 일자별 주문 및 체결 내역을 조회합니다.

        특정 기간 동안의 주문 및 체결 내역을 조회하여 거래 이력을 확인할 수 있습니다.
        pagination=True 설정 시 실전계좌 연속조회를 통해 100건 이상의 데이터를 가져올 수 있습니다.

        Parameters
        ----------
        start_date : str, optional
            조회시작일자 (YYYYMMDD 형식). 빈 문자열이면 최근 30일.
        end_date : str, optional
            조회종료일자 (YYYYMMDD 형식). 빈 문자열이면 오늘.
        pdno : str, optional
            상품번호 (종목코드, 6자리). 빈 문자열이면 전체 종목.
        ord_dvsn_cd : str, optional
            주문구분코드 (매도매수구분). 기본값: "00".
            - "00": 전체
            - "01": 매도
            - "02": 매수
        pagination : bool, optional
            연속조회 사용 여부. 기본값: False.
            - False: 단일 조회 (최대 100건)
            - True: 연속조회 (페이지네이션 지원)
        ccld_dvsn : str, optional
            체결구분 (pagination=True일 때만 사용). 기본값: "00".
            - "00": 전체
            - "01": 체결
            - "02": 미체결
        inqr_dvsn : str, optional
            조회구분/정렬 (pagination=True일 때만 사용). 기본값: "01".
            - "00": 역순 (최신 데이터부터)
            - "01": 정순 (과거 데이터부터)
        inqr_dvsn_3 : str, optional
            조회구분3 (pagination=True일 때만 사용). 기본값: "00".
            - "00": 전체 (현금+신용+담보+대출)
            - "01": 현금
            - "02": 신용
            - "03": 담보
            - "04": 대출
        max_pages : int, optional
            최대 조회 페이지 수 (pagination=True일 때). 기본값: 100.
            페이지당 최대 100건, 100페이지면 최대 10,000건.
        page_callback : callable, optional
            각 페이지 조회 후 호출되는 콜백 함수 (pagination=True일 때).
            함수 시그니처: (page_num: int, page_data: pd.DataFrame, ctx_info: dict) -> None
            ctx_info 딕셔너리 포함 내용:
            - "FK100": 연속조회키 FK100 (str)
            - "NK100": 연속조회키 NK100 (str)
            - "total_rows": 현재 페이지 행 수 (int)

        Returns
        -------
        dict or None
            주문체결내역이 담긴 딕셔너리. 실패 시 None 반환.

            반환 딕셔너리 구조:
            - rt_cd (str): 응답코드 ("0": 성공)
            - msg_cd (str): 메시지 코드
            - msg1 (str): 응답 메시지
            - output1 (list): 주문체결내역 리스트 (각 항목은 딕셔너리)
                각 딕셔너리 항목의 주요 필드:
                - ord_dt: 주문일자 (YYYYMMDD)
                - ord_gno_brno: 주문채번지점번호
                - odno: 주문번호
                - orgn_odno: 원주문번호
                - ord_dvsn_name: 주문구분명
                - sll_buy_dvsn_cd: 매도매수구분코드 (01:매도, 02:매수)
                - sll_buy_dvsn_cd_name: 매도매수구분코드명
                - pdno: 상품번호 (종목코드)
                - prdt_name: 상품명
                - ord_qty: 주문수량
                - ord_unpr: 주문단가
                - ord_tmd: 주문시각 (HHMMSS)
                - tot_ccld_qty: 총체결수량
                - avg_prvs: 평균가
                - tot_ccld_amt: 총체결금액
                - cncl_yn: 취소여부 (Y/N)
                - loan_dt: 대출일자
                - rmn_qty: 잔여수량
                - rjct_qty: 거부수량
            - output2 (dict, optional): 요약 정보 (pagination=True일 때)
                - tot_ord_qty: 총주문수량
                - tot_ccld_qty: 총체결수량
                - tot_ccld_amt: 총체결금액
                - page_count: 조회한 페이지 수
                - total_count: 전체 조회 건수

        Raises
        ------
        Exception
            API 호출 실패 시 로그 기록 후 None 반환.

        Notes
        -----
        - 실전계좌에서는 한 번에 최대 100건까지만 조회 가능합니다.
        - pagination=True 설정 시 CTX_AREA_FK100, CTX_AREA_NK100을 활용한 연속조회를 수행합니다.
        - 연속조회 시 중복 데이터는 자동으로 제거됩니다.
        - 조회 기간은 최대 3개월까지 권장됩니다.

        Examples
        --------
        단일 조회 (최대 100건):

        >>> result = api.inquire_daily_ccld("20250501", "20250901")
        >>> if result and result['rt_cd'] == '0':
        ...     print(f"조회 건수: {len(result['output1'])}")
        ...     # DataFrame으로 변환하려면:
        ...     df = pd.DataFrame(result['output1'])

        연속조회로 전체 데이터 가져오기:

        >>> result = api.inquire_daily_ccld(
        ...     start_date="20250501",
        ...     end_date="20250901",
        ...     pagination=True,
        ...     ccld_dvsn="01"  # 체결된 거래만
        ... )
        >>> if result and result['rt_cd'] == '0':
        ...     print(f"총 {len(result['output1'])}건 조회 완료")
        ...     print(f"총 {result['output2']['page_count']}페이지 조회")

        콜백과 함께 연속조회:

        >>> def on_page(page_num: int, page_data: List[Dict], ctx_info: dict) -> None:
        ...     print(f"페이지 {page_num}: {len(page_data)}건 조회")
        ...     print(f"연속키 FK100: {ctx_info['FK100'][:20]}...")
        ...
        >>> result = api.inquire_daily_ccld(
        ...     start_date="20250501",
        ...     end_date="20250901",
        ...     pagination=True,
        ...     page_callback=on_page,
        ...     max_pages=10  # 최대 1,000건
        ... )

        매수 거래만 조회:

        >>> result = api.inquire_daily_ccld(
        ...     start_date="20250501",
        ...     end_date="20250901",
        ...     ord_dvsn_cd="02",  # 매수만
        ...     pagination=True,
        ...     ccld_dvsn="01"  # 체결된 것만
        ... )
        >>> # DataFrame으로 변환하려면:
        >>> if result and result['rt_cd'] == '0':
        ...     df = pd.DataFrame(result['output1'])
        """
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
            res = self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
                tr_id="TTTC0081R",
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
        """내부 헬퍼 메서드: 연속조회를 통한 일별주문체결 조회.

        CTX_AREA_FK100과 CTX_AREA_NK100을 활용하여 페이지네이션을 구현합니다.
        실전계좌에서 호출당 최대 100건의 데이터를 가져오며,
        연속조회키를 통해 다음 페이지를 요청합니다.

        Parameters
        ----------
        start_date : str
            조회시작일자 (YYYYMMDD 형식)
        end_date : str
            조회종료일자 (YYYYMMDD 형식)
        sll_buy_dvsn_cd : str
            매도매수구분코드 (00:전체, 01:매도, 02:매수)
        inqr_dvsn : str
            조회구분 (00:역순, 01:정순)
        pdno : str
            상품번호 (종목코드, 빈 문자열이면 전체)
        ccld_dvsn : str
            체결구분 (00:전체, 01:체결, 02:미체결)
        inqr_dvsn_3 : str
            조회구분3 (00:전체, 01:현금, 02:신용, 03:담보, 04:대출)
        max_pages : int
            최대 조회 페이지 수
        page_callback : callable, optional
            페이지별 콜백 함수

        Returns
        -------
        pd.DataFrame or None
            전체 주문체결내역 DataFrame 또는 실패 시 None
        """
        all_data = []
        ctx_area_fk100 = ""
        ctx_area_nk100 = ""
        page_count = 0

        try:
            while page_count < max_pages:
                # API 요청
                res = self.client.make_request(
                    endpoint="/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
                    tr_id="TTTC8001R",  # 실전계좌용 TR_ID
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
                        "FK100": res.get("CTX_AREA_FK100", ""),
                        "NK100": res.get("CTX_AREA_NK100", ""),
                        "total_rows": len(output1),
                    }
                    page_callback(page_count, output1, ctx_info)

                # 연속조회 키 추출
                ctx_area_fk100 = res.get("CTX_AREA_FK100", "")
                ctx_area_nk100 = res.get("CTX_AREA_NK100", "")

                # 연속조회 키가 없으면 종료
                if not ctx_area_fk100 and not ctx_area_nk100:
                    break

                # 데이터가 100건 미만이면 마지막 페이지
                if len(output1) < 100:
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

                # 최종 결과 반환
                return {
                    "rt_cd": "0",
                    "msg_cd": "SUCCESSFUL",
                    "msg1": f"정상처리 완료 - 총 {len(unique_data)}건 조회",
                    "output1": unique_data,
                    "output2": {
                        "tot_ord_qty": str(tot_ord_qty),
                        "tot_ccld_qty": str(tot_ccld_qty),
                        "tot_ccld_amt": str(tot_ccld_amt),
                        "page_count": page_count,
                        "total_count": len(unique_data),
                    },
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
        self, start_date: str, end_date: str
    ) -> Optional[pd.DataFrame]:
        """기간별매매손익현황조회 - 특정 기간의 실현 매매손익을 조회합니다.

        지정한 기간 동안 매도하여 실현된 손익을 종목별로 집계하여 제공합니다.
        투자 성과 분석 및 세금 계산에 활용할 수 있습니다.

        Args:
            start_date: 조회시작일자 (YYYYMMDD 형식, 필수)
            end_date: 조회종료일자 (YYYYMMDD 형식, 필수)

        Returns:
            Optional[pd.DataFrame]: 기간별 매매손익 정보가 담긴 DataFrame
                - pdno: 상품번호
                - prdt_name: 상품명
                - buy_amt: 매수금액
                - sell_amt: 매도금액
                - sell_pnl_smtl: 매도손익합계
                - pnl_rate: 손익률(%)
                - sell_qty: 매도수량
                - buy_qty: 매수수량
                실패 시 None 반환

        Example:
            >>> # 2025년 1월 매매손익 조회
            >>> df = api.inquire_period_trade_profit("20250101", "20250131")
            >>> if df is not None:
            ...     total_profit = df['sell_pnl_smtl'].astype(float).sum()
            ...     print(f"총 실현손익: {total_profit:,.0f}원")
        """
        try:
            res = self.client.make_request(
                endpoint="/uapi/domestic-stock/v1/trading/inquire-period-trade-profit",
                tr_id="TTTC8715R",
                params={
                    "CANO": self.account["CANO"],
                    "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                    "INQR_STRT_DT": start_date,
                    "INQR_END_DT": end_date,
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
            logging.error(f"기간별매매손익 조회 실패: {e}")
            return None

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
            # TR_ID 결정
            if buy_sell.upper() == "SELL":
                tr_id = "TTTC0011U"  # 매도
            else:
                tr_id = "TTTC0012U"  # 매수

            # 파라미터 구성
            params = {
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "PDNO": pdno,
                "ORD_DVSN": order_type,
                "ORD_QTY": str(qty),
                "ORD_UNPR": str(price),
            }

            # SOR 또는 NXT 선택 시 거래소 구분 추가
            if exchange != "KRX":
                params["EXCD"] = exchange

            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-cash",
                tr_id=tr_id,
                params=params,
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
                - "22": 자기융자매수
                - "23": 유통융자매수
            exchange: 주문 거래소 (기본값: "KRX")
                - "KRX": 한국거래소
                - "SOR": Smart Order Routing (최적 체결)

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
            >>> # 삼성전자 10주 신용매수
            >>> result = api.order_credit_buy("005930", 10, 70000)
        """
        try:
            params = {
                "CANO": self.account["CANO"],
                "ACNT_PRDT_CD": self.account["ACNT_PRDT_CD"],
                "PDNO": pdno,
                "ORD_DVSN": order_type,
                "ORD_QTY": str(qty),
                "ORD_UNPR": str(price),
                "CRDT_TYPE": credit_type,
                "LOAN_DT": "",
            }

            # SOR 선택 시 거래소 구분 추가
            if exchange != "KRX":
                params["EXCD"] = exchange

            return self._make_request_dict(
                endpoint="/uapi/domestic-stock/v1/trading/order-credit",
                tr_id="TTTC0052U",  # 신용매수
                params=params,
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

    def inquire_psbl_order(self, price: int, pdno: str = "", ord_dvsn: str = "01"):
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
