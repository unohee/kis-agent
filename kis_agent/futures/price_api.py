"""
Futures Price API - 선물옵션 시세 조회 전용 모듈

단일 책임 원칙(SRP)에 따라 시세 관련 기능만 분리
- 현재가/호가 조회
- 일별/분봉 차트
- 전광판 데이터
"""

from typing import Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS


class FuturesPriceAPI(BaseAPI):
    """선물옵션 시세 조회 전용 API 클래스 (11개 메서드)"""

    def get_price(self, code: str, market: str = "F") -> Optional[Dict]:
        """
        선물옵션 현재가 시세 조회

        Args:
            code: 선물옵션 종목코드 (예: 'A01606' KOSPI200 선물 6월물)
            market: 시장 구분 코드
                - F: 지수선물, O: 지수옵션
                - JF: 주식선물, JO: 주식옵션
                - CF: 상품/금리/통화선물
                - CM: 야간선물, EU: 야간옵션

        Returns:
            FuturesPriceResponse: 선물옵션 현재가 정보

        Example:
            >>> price = agent.futures.get_price("A01606")  # 주간 선물
            >>> price = agent.futures.get_price("A01606", market="CM")  # 야간 선물
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_PRICE"],
            tr_id="FHMIF10000000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
        )

    def get_orderbook(self, code: str, market: str = "F") -> Optional[Dict]:
        """
        선물옵션 현재가 호가 조회

        Args:
            code: 선물옵션 종목코드
            market: 시장 구분 코드 (F/O/CM/EU 등, get_price 참조)

        Example:
            >>> orderbook = agent.futures.get_orderbook("A01606")  # 주간
            >>> orderbook = agent.futures.get_orderbook("A01606", market="CM")  # 야간
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_ASKING_PRICE"],
            tr_id="FHMIF10010000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
        )

    def inquire_daily_fuopchartprice(
        self,
        code: str,
        start_date: str = "",
        end_date: str = "",
        period: str = "D",
        market: str = "F",
    ) -> Optional[Dict]:
        """
        선물옵션 일별차트 조회

        Args:
            code: 선물옵션 종목코드
            start_date: 조회 시작일자 (YYYYMMDD, 공백 시 당일 기준 과거 데이터)
            end_date: 조회 종료일자 (YYYYMMDD, 공백 시 당일)
            period: 기간 구분 (D:일, W:주, M:월)

        Returns:
            FuturesDailyChartResponse: 일별 OHLCV 데이터 (최대 100건)
                - output[].stck_bsop_date: 영업일자
                - output[].fuop_oprc: 시가
                - output[].fuop_hgpr: 고가
                - output[].fuop_lwpr: 저가
                - output[].fuop_clpr: 종가
                - output[].acml_vol: 거래량

        Example:
            >>> chart = agent.futures.inquire_daily_fuopchartprice(
            ...     "101S12", start_date="20260101", end_date="20260131"
            ... )
            >>> for day in chart['output']:
            ...     print(day['stck_bsop_date'], day['fuop_clpr'])
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_DAILY_FUOPCHARTPRICE"],
            tr_id="FHKIF03020100",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date,
                "FID_PERIOD_DIV_CODE": period,
            },
        )

    def inquire_time_fuopchartprice(
        self, code: str, hour: str = "153000", tick_range: str = "1", market: str = "F"
    ) -> Optional[Dict]:
        """
        선물옵션 분봉 차트 조회

        Args:
            code: 선물옵션 종목코드
            hour: 조회 종료 시각 (HHMMSS, 기본값: 153000 장마감)
            tick_range: 분봉 구분 (1:1분, 3:3분, 5:5분, 10:10분, 30:30분, 60:60분)

        Returns:
            FuturesTimeChartResponse: 분봉 OHLCV 데이터 (최대 120건)
                - output[].stck_cntg_hour: 체결시간
                - output[].fuop_oprc: 시가
                - output[].fuop_prpr: 현재가
                - output[].cntg_vol: 체결거래량

        Example:
            >>> chart = agent.futures.inquire_time_fuopchartprice(
            ...     "101S12", tick_range="5"  # 5분봉
            ... )
            >>> for candle in chart['output']:
            ...     print(candle['stck_cntg_hour'], candle['fuop_prpr'])
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_TIME_FUOPCHARTPRICE"],
            tr_id="FHKIF03020200",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": hour,
                "FID_PW_DATA_INCU_YN": "Y",
                "FID_TICK_RANGE": tick_range,
            },
        )

    def display_board_callput(
        self,
        expiry: str,
        strike_base: str = "",
    ) -> Optional[Dict]:
        """
        옵션 콜/풋 전광판 조회

        Args:
            expiry: 만기월 (YYYYMM, 예: '202601')
            strike_base: 행사가 기준 (공백 시 ATM 기준)

        Returns:
            DisplayBoardCallPutResponse: 콜/풋옵션 리스트
                - output1[]: 콜옵션 리스트 (최대 100건)
                - output2[]: 풋옵션 리스트 (최대 100건)
                - item_code: 종목코드
                - fuop_prpr: 현재가
                - optn_theo_pric: 이론가
                - impl_vola: 내재변동성

        Example:
            >>> board = agent.futures.display_board_callput("202601")
            >>> print("콜옵션:", len(board['output1']))
            >>> print("풋옵션:", len(board['output2']))

        Note:
            - 조회시간이 긴 API (1초당 최대 1건 권장)
            - output1, output2 각각 100건까지만 조회 가능
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_DISPLAY_BOARD_CALLPUT"],
            tr_id="FHPIF05030100",
            params={
                "FID_COND_MRKT_DIV_CODE": "O",  # O:옵션
                "FID_COND_SCR_DIV_CODE": "20503",
                "FID_MRKT_CLS_CODE": "CO",  # CO:콜옵션
                "FID_MTRT_CNT": expiry,
                "FID_MRKT_CLS_CODE1": "PO",  # PO:풋옵션
                "FID_COND_MRKT_CLS_CODE": strike_base,
            },
        )

    def display_board_futures(self) -> Optional[Dict]:
        """
        선물 전광판 조회

        Returns:
            선물 종목 리스트
                - output[]: 선물 종목 리스트
                - item_code: 종목코드
                - item_name: 종목명
                - fuop_prpr: 현재가
                - acml_vol: 거래량

        Example:
            >>> board = agent.futures.display_board_futures()
            >>> for item in board['output']:
            ...     print(item['item_name'], item['fuop_prpr'])

        Note:
            조회시간이 긴 API (1초당 최대 1건 권장)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_DISPLAY_BOARD_FUTURES"],
            tr_id="FHPIF05030200",
            params={
                "FID_COND_MRKT_DIV_CODE": "F",
                "FID_COND_SCR_DIV_CODE": "20502",
                "FID_COND_MRKT_CLS_CODE": "",
            },
        )

    def display_board_option_list(self, expiry: str) -> Optional[Dict]:
        """
        옵션 종목 목록 조회

        Args:
            expiry: 만기월 (YYYYMM)

        Returns:
            옵션 종목 목록
                - output[]: 옵션 종목 리스트
                - item_code: 종목코드
                - item_name: 종목명

        Example:
            >>> options = agent.futures.display_board_option_list("202601")
            >>> print(f"총 {len(options['output'])}개 옵션")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_DISPLAY_BOARD_OPTION_LIST"],
            tr_id="FHPIO056104C0",
            params={
                "FID_COND_MRKT_DIV_CODE": "O",
                "FID_COND_SCR_DIV_CODE": "20561",
                "FID_MRKT_CLS_CODE": "ALL",
                "FID_MTRT_CNT": expiry,
            },
        )

    def display_board_top(self, sort_type: str = "01") -> Optional[Dict]:
        """
        선물옵션 상위 종목 조회

        Args:
            sort_type: 정렬 구분
                - 01: 거래량순
                - 02: 거래대금순
                - 03: 등락률순

        Returns:
            상위 종목 리스트
                - output[]: 상위 종목
                - item_code: 종목코드
                - fuop_prpr: 현재가
                - acml_vol: 거래량
                - prdy_ctrt: 등락률

        Example:
            >>> top = agent.futures.display_board_top(sort_type="01")  # 거래량순
            >>> for item in top['output'][:10]:  # 상위 10개
            ...     print(item['item_name'], item['acml_vol'])
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_DISPLAY_BOARD_TOP"],
            tr_id="FHPIF05030000",
            params={
                "FID_COND_MRKT_DIV_CODE": "F",
                "FID_COND_SCR_DIV_CODE": "20503",
                "FID_RANK_SORT_CLS_CODE": sort_type,
            },
        )

    def exp_price_trend(self, code: str, market: str = "F") -> Optional[Dict]:
        """
        선물옵션 일중 예상체결가 추이 조회

        Args:
            code: 선물옵션 종목코드

        Returns:
            예상 체결가 추이 데이터
                - output[]: 시간대별 예상체결가
                - stck_cntg_hour: 시각
                - fuop_exp_pric: 예상체결가
                - acml_vol: 누적거래량

        Example:
            >>> trend = agent.futures.exp_price_trend("101S12")
            >>> for t in trend['output']:
            ...     print(t['stck_cntg_hour'], t['fuop_exp_pric'])
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_EXP_PRICE_TREND"],
            tr_id="FHPIF05110100",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
            },
        )

    def inquire_ccnl_bstime(
        self, code: str, start_time: str = "090000", end_time: str = "153000",
        market: str = "F",
    ) -> Optional[Dict]:
        """
        선물옵션 시간대별 체결내역 조회

        Args:
            code: 선물옵션 종목코드
            start_time: 조회 시작 시각 (HHMMSS)
            end_time: 조회 종료 시각 (HHMMSS)

        Returns:
            시간대별 체결 내역
                - output[]: 체결 내역 리스트
                - stck_cntg_hour: 체결시각
                - fuop_prpr: 체결가
                - cntg_vol: 체결량

        Example:
            >>> ccnl = agent.futures.inquire_ccnl_bstime(
            ...     "101S12", "090000", "120000"  # 오전 시간대
            ... )
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_CCNL_BSTIME"],
            tr_id="CTFO5139R",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_HOUR_1": start_time,
                "FID_INPUT_HOUR_2": end_time,
            },
        )

    def inquire_daily_amount_fee(
        self, start_date: str, end_date: str
    ) -> Optional[Dict]:
        """
        선물옵션 기간별 약정수수료 일별 조회

        Args:
            start_date: 조회 시작일 (YYYYMMDD)
            end_date: 조회 종료일 (YYYYMMDD)

        Returns:
            일별 거래량 및 수수료 정보
                - output[]: 일별 데이터
                - stck_bsop_date: 영업일자
                - acml_vol: 누적거래량
                - tot_fee_amt: 총수수료금액

        Example:
            >>> fee = agent.futures.inquire_daily_amount_fee(
            ...     "20260101", "20260131"
            ... )
            >>> for day in fee['output']:
            ...     print(day['stck_bsop_date'], day['tot_fee_amt'])
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTURES_INQUIRE_DAILY_AMOUNT_FEE"],
            tr_id="CTFO6119R",
            params={
                "INQR_STRT_DT": start_date,
                "INQR_END_DT": end_date,
                "AFHR_FLPR_YN": "N",  # 시간외단일가여부
            },
        )
