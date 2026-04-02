"""
Stock Index API - 주식 지수 시세 조회 전용 모듈

국내 업종/지수 관련 API:
- 업종 현재지수 조회
- 업종 시간별 시세
- 업종 일자별 시세
"""

from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import API_ENDPOINTS


class StockIndexAPI(BaseAPI):
    """주식 지수 시세 조회 전용 API 클래스"""

    def inquire_index_category_price(
        self,
        index_code: str,
        screen_code: str = "20214",
        market_cls: str = "K",
        belong_cls: str = "0",
        market: str = "U",
    ) -> Optional[Dict]:
        """
        국내업종 구분별 전체시세 조회

        Args:
            index_code: 업종코드 (0001:코스피, 1001:코스닥, 2001:코스피200)
            screen_code: 화면코드 (20214:고정값)
            market_cls: 시장구분코드 (K:거래소, Q:코스닥, K2:코스피200)
            belong_cls: 소속구분코드 (0:전업종, 1:기타구분, 2:자본금/벤처구분, 3:상업별/일반구분)
            market: 시장구분 (U:업종)

        Returns:
            업종별 전체시세 데이터 (output1: 요약, output2: 업종별 리스트)
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_CATEGORY_PRICE"],
            tr_id="FHPUP02140000",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": index_code,
                "FID_COND_SCR_DIV_CODE": screen_code,
                "FID_MRKT_CLS_CODE": market_cls,
                "FID_BLNG_CLS_CODE": belong_cls,
            },
        )

    def inquire_index_price(self, index_code: str, market: str = "U") -> Optional[Dict]:
        """
        국내업종 현재지수 조회

        DEPRECATION WARNING:
            이 메서드는 원본 KIS API 엔드포인트(FHPUP02100000)가 404를 반환하여
            내부적으로 inquire_index_timeprice()를 호출합니다.
            향후 버전에서 제거될 수 있으니 inquire_index_timeprice() 사용을 권장합니다.

        TODO: v2.0에서 제거 예정 - inquire_index_timeprice() 또는 get_index_timeprice() 사용

        Args:
            index_code: 업종코드 (0001:코스피, 1001:코스닥, 2001:코스피200)
            market: 시장구분 (U:업종)

        Returns:
            업종 지수 데이터 (분봉 시세)
        """
        import warnings

        warnings.warn(
            "inquire_index_price()는 deprecated되었습니다. "
            "inquire_index_timeprice() 또는 get_index_timeprice() 사용을 권장합니다. "
            "(원본 API 엔드포인트 404 에러)",
            DeprecationWarning,
            stacklevel=2,
        )
        # 404 에러 발생하는 원본 엔드포인트 대신 정상 작동하는 메서드 사용
        return self.inquire_index_timeprice(index_code, market, time_div="600")

    def inquire_index_tickprice(
        self, index_code: str, market: str = "U"
    ) -> Optional[Dict]:
        """
        국내업종 시간별지수(틱) 조회

        Args:
            index_code: 업종코드 (0001:거래소, 1001:코스닥, 2001:코스피200, 3003:KSQ150)
            market: 시장구분 (U:업종)

        Returns:
            시간별지수 틱 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_TICKPRICE"],
            tr_id="FHPUP02110100",
            params={
                "FID_INPUT_ISCD": index_code,
                "FID_COND_MRKT_DIV_CODE": market,
            },
        )

    def inquire_index_timeprice(
        self, index_code: str, market: str = "U", time_div: str = "600"
    ) -> Optional[Dict]:
        """
        국내업종 지수 시간별 시세 조회

        Args:
            index_code: 업종코드 (0001:코스피, 1001:코스닥, 2001:코스피200)
            market: 시장구분 (U:업종)
            time_div: 시간간격(초) - 기본값 600 (10분봉)
                - "60": 1분봉
                - "120": 2분봉
                - "300": 5분봉
                - "600": 10분봉
                - "900": 15분봉
                - "1800": 30분봉
                - "3600": 60분봉

        Returns:
            지수 시간별 시세 데이터
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_TIMEPRICE"],
            tr_id="FHPUP02110200",
            params={
                "fid_cond_mrkt_div_code": market,
                "fid_input_iscd": index_code,
                "fid_input_hour_1": time_div,
            },
        )

    def get_index_timeprice(
        self,
        fid_input_iscd: str = "1029",
        fid_input_hour_1: str = "600",
        fid_cond_mrkt_div_code: str = "U",
    ) -> Optional[Dict[str, Any]]:
        """
        국내업종 시간별 지수 조회 (기본값: KOSPI200)

        Args:
            fid_input_iscd: 종목코드 (1001:KOSPI, 2001:KOSDAQ, 1029:KOSPI200)
            fid_input_hour_1: 시간(초) (60/120/180/300/600/900/1800/3600 = 분봉)
            fid_cond_mrkt_div_code: 시장분류 (U:업종)

        Returns:
            Dict: output에 시간별 지수 데이터 리스트
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_TIMEPRICE"],
            tr_id="FHPUP02110200",
            params={
                "fid_cond_mrkt_div_code": fid_cond_mrkt_div_code,
                "fid_input_iscd": fid_input_iscd,
                "fid_input_hour_1": fid_input_hour_1,
            },
        )

    def get_index_daily_price(
        self, index_code: str = "0001", end_date: str = None, period: str = "D"
    ) -> Optional[Dict[str, Any]]:
        """
        국내 지수 일자별 시세 조회 (rt_cd 메타데이터가 포함된)

        KOSPI, KOSDAQ 등 주요 지수의 일별/주별/월별 시세를 조회합니다.
        베타 계산, 시장 상관관계 분석 등에 활용할 수 있습니다.

        Args:
            index_code (str): 지수코드 (기본값: "0001")
                - "0001": KOSPI
                - "1001": KOSDAQ
                - "2001": KOSPI200
            end_date (str): 조회 종료일 (YYYYMMDD), None이면 오늘
            period (str): 기간 구분 (기본값: "D")
                - "D": 일별
                - "W": 주별
                - "M": 월별

        Returns:
            Dict: 지수 일별 시세 데이터
                - output1: 지수 기본 정보 (지수명, 현재가 등)
                - output2: 일자별 시세 리스트 (최대 100건)
                    - stck_bsop_date: 영업일자 (YYYYMMDD)
                    - bstp_nmix_prpr: 업종지수 현재가
                    - bstp_nmix_oprc: 업종지수 시가
                    - bstp_nmix_hgpr: 업종지수 고가
                    - bstp_nmix_lwpr: 업종지수 저가
                    - acml_vol: 누적거래량
                    - acml_tr_pbmn: 누적거래대금
                    - prdy_vrss: 전일대비
                    - prdy_vrss_sign: 전일대비부호

        Example:
            >>> # KOSPI 일별 시세 조회
            >>> result = agent.stock.get_index_daily_price("0001")
            >>> for day in result['output2']:
            ...     print(day['stck_bsop_date'], day['bstp_nmix_prpr'])

            >>> # KOSDAQ 최근 100일 시세
            >>> result = agent.stock.get_index_daily_price("1001", "20251210")

            >>> # KOSPI200 월별 시세
            >>> result = agent.stock.get_index_daily_price("2001", period="M")

        Note:
            - TR ID: FHPUP02120000
            - 최대 100건까지 조회 가능
            - 베타 계산 시: β = Cov(Stock, Market) / Var(Market)
        """
        if end_date is None:
            from datetime import datetime

            end_date = datetime.now().strftime("%Y%m%d")

        return self._make_request_dict(
            endpoint=API_ENDPOINTS["INQUIRE_INDEX_DAILY_PRICE"],
            tr_id="FHPUP02120000",
            params={
                "FID_PERIOD_DIV_CODE": period,
                "FID_COND_MRKT_DIV_CODE": "U",
                "FID_INPUT_ISCD": index_code,
                "FID_INPUT_DATE_1": end_date,
            },
        )

    def get_future_option_price(
        self, market_div_code: str = "F", input_iscd: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        선물옵션 시세 조회 (rt_cd 메타데이터가 포함된)

        KOSPI200 선물/옵션, 주식선물/옵션의 실시간 시세를 조회합니다.
        종목코드를 지정하지 않으면 가장 활발한 KOSPI200 선물 시세를 조회합니다.

        Args:
            market_div_code (str, optional): 시장분류코드. Defaults to "F".
                - "F": 지수선물 (KOSPI200 선물)
                - "O": 지수옵션 (KOSPI200 옵션)
                - "JF": 주식선물 (개별주식 선물)
                - "JO": 주식옵션 (개별주식 옵션)
            input_iscd (Optional[str], optional): 선물옵션종목코드. Defaults to None.
                - None인 경우 가장 활발한 KOSPI200 선물코드 자동 사용
                - 선물: 6자리 (예: "101T12", "101S03")
                - 옵션: 9자리 (예: "201T12370", "201S03370")

        Returns:
            Optional[Dict[str, Any]]: 선물옵션 시세 데이터
                - 성공 시: rt_cd와 함께 시세 정보 딕셔너리
                - 실패 시: None

        Example:
            >>> # 가장 활발한 KOSPI200 선물 시세 조회 (기본값)
            >>> result = stock_api.get_future_option_price()
            >>> if result and result.get('rt_cd') == '0':
            ...     print(f"현재가: {result['output']['stck_prpr']}")

            >>> # 특정 KOSPI200 선물 시세 조회
            >>> result = stock_api.get_future_option_price("F", "101T12")

            >>> # KOSPI200 옵션 시세 조회
            >>> result = stock_api.get_future_option_price("O", "201T12370")

            >>> # 개별주식 선물 시세 조회
            >>> result = stock_api.get_future_option_price("JF", "005930T12")

        Note:
            - 실시간 데이터이므로 시장 개장 시간에만 유효한 데이터 제공
            - 옵션의 경우 행사가가 포함된 9자리 코드 필요
            - rt_cd가 '0'이면 성공, 그 외는 오류
            - 주식선물/옵션은 종목별로 상장 여부 확인 필요
        """
        if input_iscd is None:
            # get_kospi200_futures_code는 pykis.stock.api 모듈에 있으므로 import
            from .api import get_kospi200_futures_code

            input_iscd = get_kospi200_futures_code()
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTUREOPTION_INQUIRE_PRICE"],
            tr_id="FHMIF10000000",
            params={
                "FID_COND_MRKT_DIV_CODE": market_div_code,
                "FID_INPUT_ISCD": input_iscd,
            },
        )

    def get_future_orderbook(
        self, code: str, market_div_code: str = "F"
    ) -> Optional[Dict[str, Any]]:
        """
        선물옵션 호가창 조회 (미결제약정 정보 포함)

        KOSPI200 선물/옵션의 매도/매수 호가 10단계와 미결제약정 정보를 조회합니다.
        현물/선물 포지션 분석 시 호가 분포와 미결제약정 변화를 분석할 수 있습니다.

        Args:
            code (str): 선물옵션 종목코드
                - 지수선물: 6자리 (예: "101W09" - KOSPI200 2025년 9월물)
                - 주식선물: 6자리 (예: "005930F09")
                - 옵션: 9자리 (예: "201W09370" - 콜옵션 행사가 370)
            market_div_code (str, optional): 시장 분류 코드. Defaults to "F".
                - "F": 지수선물 (KOSPI200 선물)
                - "JF": 주식선물 (개별종목 선물)
                - "O": 옵션 (KOSPI200 옵션)
                - "JO": 주식옵션

        Returns:
            Optional[Dict[str, Any]]: 선물옵션 호가 데이터
                - rt_cd: 응답 코드 ("0" = 성공)
                - msg1: 응답 메시지
                - output1: 호가 요약 정보 (객체)
                    - 현재가, 거래량 등 요약 정보
                    - 미결제약정 관련 필드 (API 응답 구조에 따라 다름)
                - output2: 호가 상세 정보 (객체)
                    - 매도호가 1~10단계 (askp1~askp10)
                    - 매수호가 1~10단계 (bidp1~bidp10)
                    - 각 호가별 잔량 정보
                    - 총 매도/매수 호가 잔량

        Example:
            >>> # KOSPI200 선물 호가창 조회
            >>> orderbook = agent.stock.get_future_orderbook("101W09", "F")
            >>> if orderbook and orderbook.get('rt_cd') == '0':
            ...     output1 = orderbook['output1']
            ...     output2 = orderbook['output2']
            ...     print(f"매도1호가: {output2.get('askp1')}")
            ...     print(f"매수1호가: {output2.get('bidp1')}")

            >>> # 옵션 호가창 조회
            >>> opt_orderbook = agent.stock.get_future_orderbook("201W09370", "O")

        Note:
            - TR ID: FHMIF10010000
            - 실시간 호가 데이터는 WebSocket `subscribe_futures(with_orderbook=True)` 사용
            - 미결제약정(Open Interest) 데이터는 output1 또는 output2에 포함 가능
            - 호가 조회는 시장 개장 시간에만 유효한 데이터 제공
            - 선물 종목코드는 `get_kospi200_futures_code()`로 자동 생성 가능
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS["FUTUREOPTION_INQUIRE_ASKING_PRICE"],
            tr_id="FHMIF10010000",
            params={
                "FID_COND_MRKT_DIV_CODE": market_div_code,
                "FID_INPUT_ISCD": code,
            },
        )
