"""
Overseas Futures Price API - 해외선물옵션 시세 조회 전용 모듈

단일 책임 원칙(SRP)에 따라 시세 관련 기능만 분리
- 선물/옵션 현재가 조회
- 선물/옵션 호가 조회
- 분봉/일간 차트 조회
- 상품기본정보 조회
"""

from datetime import datetime
from typing import Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS


class OverseasFuturesPriceAPI(BaseAPI):
    """해외선물옵션 시세 조회 전용 API 클래스 (8개 메서드)"""

    def get_price(self, srs_cd: str) -> Optional[Dict]:
        """
        해외선물 현재가 조회

        Args:
            srs_cd: 종목코드 (예: 'CNHU24', 'ESM24')

        Returns:
            OverseasFuturesPriceResponse: 해외선물 현재가 정보
                - output.last: 현재가
                - output.diff: 전일 대비
                - output.rate: 등락률
                - output.tvol: 거래량
                - output.oi: 미결제약정

        Example:
            >>> price = agent.overseas_futures.get_price("CNHU24")
            >>> print(f"현재가: {price['output']['last']}")
            >>> print(f"등락률: {price['output']['rate']}%")

        Note:
            종목코드는 한국투자증권 포럼 > FAQ > 종목정보 다운로드(해외) 참조
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_INQUIRE_PRICE"],
            tr_id="HHDFC55010000",  # 해외선물 현재가
            params={"SRS_CD": srs_cd},
        )

    def get_option_price(self, srs_cd: str) -> Optional[Dict]:
        """
        해외옵션 현재가 조회

        Args:
            srs_cd: 옵션 종목코드

        Returns:
            OverseasOptionPriceResponse: 해외옵션 현재가 정보
                - output.last: 현재가
                - output.theo_pric: 이론가
                - output.iv: 내재변동성
                - output.delta: 델타
                - output.gamma: 감마
                - output.theta: 세타
                - output.vega: 베가

        Example:
            >>> price = agent.overseas_futures.get_option_price("ES2401C5000")
            >>> print(f"현재가: {price['output']['last']}")
            >>> print(f"IV: {price['output']['iv']}%")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_OPT_PRICE"],
            tr_id="HHDFC55020000",  # 해외옵션 현재가
            params={"SRS_CD": srs_cd},
        )

    def get_minute_chart(
        self,
        srs_cd: str,
        exch_cd: str,
        end_date: str = "",
        qry_cnt: str = "120",
        qry_gap: str = "1",
    ) -> Optional[Dict]:
        """
        해외선물 분봉 차트 조회

        Args:
            srs_cd: 종목코드 (예: 'CNHU24')
            exch_cd: 거래소코드 (CME, EUREX, NYMEX, COMEX, ICE 등)
            end_date: 조회종료일시 (YYYYMMDD, 공백 시 현재)
            qry_cnt: 조회건수 (최대 120)
            qry_gap: 분간격 (1, 3, 5, 10, 30, 60)

        Returns:
            OverseasFuturesMinuteChartResponse: 분봉 OHLCV 데이터
                - output1.index_key: 다음 조회 키
                - output2[].bsop_date: 영업일자
                - output2[].bsop_time: 영업시간
                - output2[].open: 시가
                - output2[].high: 고가
                - output2[].low: 저가
                - output2[].last: 종가
                - output2[].tvol: 거래량

        Example:
            >>> chart = agent.overseas_futures.get_minute_chart(
            ...     srs_cd="CNHU24",
            ...     exch_cd="CME",
            ...     qry_gap="5"  # 5분봉
            ... )
            >>> for candle in chart['output2']:
            ...     print(f"{candle['bsop_time']}: {candle['last']}")
        """
        # 종료일시가 없으면 오늘 날짜
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_MINUTE_CHART"],
            tr_id="HHDFC55030100",  # 해외선물 분봉
            params={
                "SRS_CD": srs_cd,
                "EXCH_CD": exch_cd,
                "START_DATE_TIME": "",  # 공백
                "CLOSE_DATE_TIME": end_date,
                "QRY_TP": "Q",  # Q:최초조회, P:다음조회
                "QRY_CNT": qry_cnt,
                "QRY_GAP": qry_gap,
                "INDEX_KEY": "",
            },
        )

    def get_daily_trend(
        self,
        srs_cd: str,
        exch_cd: str,
        end_date: str = "",
        qry_cnt: str = "30",
    ) -> Optional[Dict]:
        """
        해외선물 체결추이(일간) 조회

        Args:
            srs_cd: 종목코드
            exch_cd: 거래소코드
            end_date: 조회종료일자 (YYYYMMDD, 공백 시 현재)
            qry_cnt: 조회건수 (최대 40)

        Returns:
            OverseasFuturesDailyTrendResponse: 일간 OHLCV 데이터
                - output2[].bsop_date: 영업일자
                - output2[].open: 시가
                - output2[].high: 고가
                - output2[].low: 저가
                - output2[].last: 종가
                - output2[].tvol: 거래량
                - output2[].oi: 미결제약정

        Example:
            >>> trend = agent.overseas_futures.get_daily_trend(
            ...     srs_cd="6AM24",
            ...     exch_cd="CME"
            ... )
            >>> for day in trend['output2']:
            ...     print(f"{day['bsop_date']}: {day['last']}")
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_DAILY_CCNL"],
            tr_id="HHDFC55030200",  # 해외선물 일간체결
            params={
                "SRS_CD": srs_cd,
                "EXCH_CD": exch_cd,
                "START_DATE_TIME": "",
                "CLOSE_DATE_TIME": end_date,
                "QRY_TP": "Q",
                "QRY_CNT": qry_cnt,
                "QRY_GAP": "",  # 일간은 공백
                "INDEX_KEY": "",
            },
        )

    def get_futures_orderbook(self, srs_cd: str) -> Optional[Dict]:
        """
        해외선물 호가 조회

        Args:
            srs_cd: 종목코드

        Returns:
            OverseasFuturesOrderbookResponse: 호가 정보
                - output1: 매도호가 (askp1~askp5, askp_rsqn1~askp_rsqn5)
                - output2: 매수호가 (bidp1~bidp5, bidp_rsqn1~bidp_rsqn5)

        Example:
            >>> orderbook = agent.overseas_futures.get_futures_orderbook("CNHU24")
            >>> print(f"매도1호가: {orderbook['output1']['askp1']}")
            >>> print(f"매수1호가: {orderbook['output2']['bidp1']}")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_ASKING_PRICE"],
            tr_id="HHDFC55010100",  # 해외선물 호가
            params={"SRS_CD": srs_cd},
        )

    def get_option_orderbook(self, srs_cd: str) -> Optional[Dict]:
        """
        해외옵션 호가 조회

        Args:
            srs_cd: 옵션 종목코드

        Returns:
            해외옵션 호가 정보
                - output1: 매도호가
                - output2: 매수호가

        Example:
            >>> orderbook = agent.overseas_futures.get_option_orderbook("ES2401C5000")
            >>> print(f"매도1호가: {orderbook['output1']['askp1']}")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_OPT_ASKING_PRICE"],
            tr_id="HHDFC55020100",  # 해외옵션 호가
            params={"SRS_CD": srs_cd},
        )

    def get_futures_info(self, srs_codes: list) -> Optional[Dict]:
        """
        해외선물 상품기본정보 조회

        Args:
            srs_codes: 종목코드 리스트 (최대 32개)

        Returns:
            OverseasFuturesInfoResponse: 상품기본정보
                - output[].srs_cd: 종목코드
                - output[].prdt_nm: 상품명
                - output[].exch_cd: 거래소코드
                - output[].tick_sz: 틱사이즈
                - output[].tick_val: 틱가치
                - output[].ctrt_sz: 계약크기
                - output[].expr_date: 만기일

        Example:
            >>> info = agent.overseas_futures.get_futures_info(["CNHU24", "ESM24"])
            >>> for item in info['output']:
            ...     print(f"{item['srs_cd']}: {item['prdt_nm']}")
        """
        # 종목코드 파라미터 구성 (srs_cd_01 ~ srs_cd_32)
        params = {"QRY_CNT": str(len(srs_codes))}
        for i, code in enumerate(srs_codes[:32], 1):
            params[f"SRS_CD_{i:02d}"] = code

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_CONTRACT_DETAIL"],
            tr_id="HHDFC55040000",  # 해외선물 상품정보
            params=params,
        )

    def get_option_info(self, srs_codes: list) -> Optional[Dict]:
        """
        해외옵션 상품기본정보 조회

        Args:
            srs_codes: 옵션 종목코드 리스트 (최대 30개)

        Returns:
            해외옵션 상품기본정보
                - output[]: 옵션 상품 정보 리스트

        Example:
            >>> info = agent.overseas_futures.get_option_info(["ES2401C5000"])
            >>> for item in info['output']:
            ...     print(f"{item['srs_cd']}: 만기 {item['expr_date']}")
        """
        params = {"QRY_CNT": str(len(srs_codes))}
        for i, code in enumerate(srs_codes[:30], 1):
            params[f"SRS_CD_{i:02d}"] = code

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["OVRS_FUTR_OPT_DETAIL"],
            tr_id="HHDFC55050000",  # 해외옵션 상품정보
            params=params,
        )
