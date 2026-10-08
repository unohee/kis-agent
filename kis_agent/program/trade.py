import datetime  # noqa: F401
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS

"""
program_trade_api.py - 프로그램 매매 정보 조회 전용 모듈

한국투자증권 API의 프로그램 매매 정보 조회 기능을 제공하는 모듈입니다.

이 모듈은 한국투자증권 OpenAPI를 통해 프로그램 매매 관련 정보를 조회합니다:
- 시간별 프로그램 매매 추이 (실시간 델타 등) - 종목별프로그램매매추이(체결) / FHPPG04650101
- 일별 프로그램 매매 집계 (당일 총 매수/매도량 등) - 종목별 프로그램매매추이(일별) / FHPPG04650201
- 기간별 프로그램 매매 상세 (차익/비차익 매매 내역)

 의존:
- kis_core.KISClient: API 호출 핸들링

 연관 모듈:
- agent_stock.py: 종목 시세 및 주문 처리
- account_api.py: 계좌 상태 및 주문 가능 금액 확인
- (전략 관련 모듈은 deprecated되어 제거됨)

 사용 예시:
client = KISClient()
pgm_api = ProgramTradeAPI(client)
hourly_trend = pgm_api.get_program_trade_hourly_trend("005930")
daily_summary = pgm_api.get_program_trade_daily_summary("005930", "20240726")
"""


class ProgramTradeAPI(BaseAPI):
    """
    한국투자증권 API의 프로그램 매매 정보 조회 기능을 제공하는 클래스입니다.

    이 클래스는 시간별/일별/기간별 프로그램 매매 정보를 조회하는 기능을 제공합니다.

    Attributes:
        client (KISClient): API 통신을 담당하는 클라이언트

    Example:
        >>> client = KISClient()
        >>> pgm_api = ProgramTradeAPI(client)
        >>> hourly_trend = pgm_api.get_program_trade_hourly_trend("005930")
        >>> daily_summary = pgm_api.get_program_trade_daily_summary("005930", "20240726")
    """

    def __init__(
        self,
        client,
        account_info=None,
        enable_cache=True,
        cache_config=None,
        _from_agent: bool = False,
    ):
        """
        ProgramTradeAPI를 초기화합니다.

        Args:
            client (KISClient): API 통신을 담당하는 클라이언트
            account_info (dict, optional): 계좌 정보
            enable_cache (bool): 캐시 사용 여부 (기본: True)
            cache_config (dict): 캐시 설정
            _from_agent (bool): Agent를 통해 생성되었는지 여부 (내부 사용)
        """
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

    def get_program_trade_by_stock(
        self, code: str, ref_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        종목별 프로그램매매추이를 조회합니다.

        ``ref_date``가 없으면 당일 체결 추이(FHPPG04650101), 있으면 해당일까지의
        일별 추이(FHPPG04650201, ``get_program_trade_daily_summary``)를 조회한다.
        체결 API에는 날짜 필드가 없다 (이전 버전은 날짜를 붙여 보냈다).

        Args:
            code (str): 종목 코드 (예: "005930")
            ref_date (Optional[str]): 기준 일자 (YYYYMMDD 형식)

        Returns:
            Optional[Dict[str, Any]]: rt_cd 메타데이터가 포함된 API 응답 데이터
        """
        if ref_date:
            return self.get_program_trade_daily_summary(code, ref_date)
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": code,
        }

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["PROGRAM_TRADE_BY_STOCK"],
            tr_id="FHPPG04650101",  # 종목별프로그램매매추이(체결)
            params=params,
        )

    def get_program_trade_hourly_trend(self, code: str) -> Optional[Dict[str, Any]]:
        """
        시간별 프로그램 매매 추이를 조회합니다. `get_program_trade_by_stock` 메서드를 호출하여 당일 데이터를 가져옵니다.

        Args:
            code (str): 종목 코드 (예: "005930")

        Returns:
            Optional[Dict[str, Any]]: API 응답 데이터
        """
        return self.get_program_trade_by_stock(code, ref_date=None)

    def get_program_trade_daily_summary(
        self, code: str, date_str: str
    ) -> Optional[Dict[str, Any]]:
        """
        종목별 프로그램매매추이(일별) - 일별 프로그램 매매 집계를 조회합니다.

        Args:
            code (str): 종목 코드 (예: "005930")
            date_str (str): 조회 일자 (YYYYMMDD 형식)

        Returns:
            Optional[Dict[str, Any]]: rt_cd 메타데이터가 포함된 API 응답 데이터
                - 성공 시: 일별 프로그램 매매 집계 정보를 포함한 응답 데이터
                - 실패 시: None

        Note:
            이 API는 특정 '일자'를 지정하여 해당일의 프로그램 매매 총 집계 현황을 반환합니다.
            주요 응답 필드 (output 리스트의 첫 번째 항목 예상):
            - stck_bsop_date: 주식 영업 일자
            - prgr_shnu_vol: 프로그램 순매수 체결 수량 (일별 총계)
            - prgr_seln_vol: 프로그램 순매도 체결 수량 (일별 총계)

        Example:
            >>> api.get_program_trade_daily_summary("005930", "20240726")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["PROGRAM_TRADE_BY_STOCK_DAILY"],
            tr_id="FHPPG04650201",  # 종목별 프로그램매매추이(일별), 구TR FHPPG04650200
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": date_str,  # 기준일자 (YYYYMMDD)
            },
        )

    def get_program_trade_market_daily(
        self, start_date: str, end_date: str
    ) -> Optional[Dict[str, Any]]:
        """
        프로그램 매매 종합현황 (일별)을 조회합니다.

        Args:
            start_date (str): 시작 일자 (YYYYMMDD 형식)
            end_date (str): 종료 일자 (YYYYMMDD 형식)

        Returns:
            Optional[Dict[str, Any]]: rt_cd 메타데이터가 포함된 API 응답 데이터
                - 성공 시: 일별 프로그램 매매 종합현황 정보를 포함한 응답 데이터
                - 실패 시: None

        Example:
            >>> api.get_program_trade_market_daily("20240701", "20240726")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/comp-program-trade-daily",
            tr_id="FHPPG04600001",  # 프로그램매매종합현황(일별), 구TR FHPPG04600000
            params={
                "FID_MRKT_CLS_CODE": "",  # 시장 분류 코드 (전체는 공백)
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date,
                "FID_COND_MRKT_DIV_CODE": "J",  # UN: 통합장 (KOSPI+KOSDAQ+NXT)
            },
        )

    def get_comp_program_trade_today(
        self,
        market_cls: str = "K",
        market: str = "J",
    ) -> Optional[Dict[str, Any]]:
        """프로그램매매 종합현황(시간) [국내주식-114]

        프로그램매매 종합현황(시간) (``/uapi/domestic-stock/v1/quotations/comp-program-trade-today``, TR FHPPG04600101). 모의투자 미지원.

        Args:
            market_cls: 시장 구분 (K: 코스피, Q: 코스닥)
            market: 시장 분류 (J: KRX, NX: NXT, UN: 통합)

        Returns:
            output1[]: bsop_hour(시간), arbt_smtn_ntby_tr_pbmn(차익 순매수 거래대금),
            nabt_smtn_ntby_tr_pbmn(비차익 순매수 거래대금), whol_smtn_ntby_tr_pbmn(전체 순매수 거래대금)

        Example:
            >>> agent.get_comp_program_trade_today("K")
        """
        return self._make_request_dict(
            endpoint="/uapi/domestic-stock/v1/quotations/comp-program-trade-today",
            tr_id="FHPPG04600101",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_MRKT_CLS_CODE": market_cls,
                "FID_SCTN_CLS_CODE": "",
                "FID_INPUT_ISCD": "",
                "FID_COND_MRKT_DIV_CODE1": "",
                "FID_INPUT_HOUR_1": "",
            },
        )


ProgramTrade = ProgramTradeAPI
