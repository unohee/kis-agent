"""
해외주식 시세 조회 API

OverseasPriceAPI는 해외주식의 시세, 호가, 차트 데이터를 조회합니다.

지원 거래소:
- NAS: NASDAQ, NYS: NYSE, AMS: AMEX (미국)
- HKS: 홍콩, TSE: 도쿄 (일본)
- SHS: 상해, SZS: 심천 (중국)
- HSX: 호치민, HNX: 하노이 (베트남)
"""

from typing import Any, Dict, List, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient


class OverseasPriceAPI(BaseAPI):
    """
    해외주식 시세 조회 API

    해외주식의 현재가, 일봉, 분봉, 호가 등 시세 관련 데이터를 조회합니다.

    Attributes:
        client (KISClient): API 통신 클라이언트
        account (Dict): 계좌 정보

    Example:
        >>> from pykis import Agent
        >>> agent = Agent(...)
        >>> price = agent.overseas.get_price(excd="NAS", symb="AAPL")
        >>> print(f"AAPL 현재가: ${price['output']['last']}")
    """

    # 지원 거래소 코드 매핑
    EXCHANGE_CODES = {
        # 미국
        "NAS": "나스닥",
        "NYS": "뉴욕증권거래소",
        "AMS": "아멕스",
        # 아시아
        "HKS": "홍콩",
        "TSE": "도쿄",
        "SHS": "상해",
        "SZS": "심천",
        "HSX": "호치민",
        "HNX": "하노이",
    }

    def __init__(
        self,
        client: KISClient,
        account_info: Optional[Dict[str, Any]] = None,
        enable_cache: bool = True,
        cache_config: Optional[Dict[str, Any]] = None,
        _from_agent: bool = False,
    ) -> None:
        """
        OverseasPriceAPI 초기화

        Args:
            client (KISClient): API 통신 클라이언트
            account_info (dict, optional): 계좌 정보
            enable_cache (bool): 캐시 사용 여부 (기본: True)
            cache_config (dict, optional): 캐시 설정
            _from_agent (bool): Agent를 통해 생성되었는지 여부 (내부 사용)
        """
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

    def _validate_exchange(self, excd: str) -> bool:
        """거래소 코드 유효성 검증"""
        if excd.upper() not in self.EXCHANGE_CODES:
            raise ValueError(
                f"유효하지 않은 거래소 코드: {excd}. "
                f"지원 거래소: {list(self.EXCHANGE_CODES.keys())}"
            )
        return True

    def get_price(
        self,
        excd: str,
        symb: str,
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 현재체결가 조회

        해외주식의 현재 체결가, 전일대비, 등락률 등 기본 시세를 조회합니다.

        Args:
            excd (str): 거래소 코드 (NAS, NYS, AMS, HKS, TSE, SHS, SZS, HSX, HNX)
            symb (str): 종목코드 (예: AAPL, TSLA, NVDA)

        Returns:
            Optional[Dict]: 시세 정보
                - rt_cd: 응답코드 ("0": 성공)
                - msg1: 응답메시지
                - output:
                    - rsym: 실시간조회종목코드
                    - zdiv: 소수점자리수
                    - base: 전일종가
                    - pvol: 전일거래량
                    - last: 현재가
                    - sign: 대비부호
                    - diff: 전일대비
                    - rate: 등락률
                    - tvol: 거래량
                    - tamt: 거래대금
                    - ordy: 매수가능여부

        Example:
            >>> price = agent.overseas.get_price("NAS", "AAPL")
            >>> print(f"현재가: ${price['output']['last']}")
            >>> print(f"등락률: {price['output']['rate']}%")
        """
        self._validate_exchange(excd)

        params = {
            "AUTH": "",
            "EXCD": excd.upper(),
            "SYMB": symb.upper(),
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/price",
            tr_id="HHDFS00000300",
            params=params,
            use_cache=True,
            cache_ttl=5,  # 시세 데이터는 5초 캐시
        )

    def get_price_detail(
        self,
        excd: str,
        symb: str,
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 현재가 상세 조회

        52주 최고/최저, 거래량, PER, EPS 등 상세 시세 정보를 조회합니다.

        Args:
            excd (str): 거래소 코드
            symb (str): 종목코드

        Returns:
            Optional[Dict]: 상세 시세 정보
                - output:
                    - rsym: 실시간조회종목코드
                    - last: 현재가
                    - sign: 대비부호
                    - diff: 전일대비
                    - rate: 등락률
                    - pvol: 전일거래량
                    - tvol: 거래량
                    - h52p: 52주최고가
                    - l52p: 52주최저가
                    - perx: PER
                    - pbrx: PBR
                    - epsx: EPS
                    - bpsx: BPS
                    - t_xprc: 원화환산가격 (예상)

        Example:
            >>> detail = agent.overseas.get_price_detail("NAS", "AAPL")
            >>> print(f"52주 최고가: ${detail['output']['h52p']}")
        """
        self._validate_exchange(excd)

        params = {
            "AUTH": "",
            "EXCD": excd.upper(),
            "SYMB": symb.upper(),
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/price-detail",
            tr_id="HHDFS76200200",
            params=params,
            use_cache=True,
            cache_ttl=10,  # 상세 정보는 10초 캐시
        )

    def get_daily_price(
        self,
        excd: str,
        symb: str,
        gubn: str = "0",
        bymd: str = "",
        modp: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 기간별 시세 조회 (일봉)

        해외주식의 일별 시세 데이터를 조회합니다.

        Args:
            excd (str): 거래소 코드
            symb (str): 종목코드
            gubn (str): 일/주/월 구분 ("0": 일, "1": 주, "2": 월)
            bymd (str): 조회기준일자 (YYYYMMDD, 공백 시 최근일)
            modp (str): 수정주가반영여부 ("0": 미반영, "1": 반영)

        Returns:
            Optional[Dict]: 기간별 시세 정보
                - output1: 종목 기본 정보
                    - rsym: 종목코드
                    - zdiv: 소수점자리수
                    - nrec: 레코드갯수
                - output2: 일별 시세 리스트
                    - xymd: 일자 (YYYYMMDD)
                    - clos: 종가
                    - sign: 대비부호
                    - diff: 전일대비
                    - rate: 등락률
                    - open: 시가
                    - high: 고가
                    - low: 저가
                    - tvol: 거래량
                    - tamt: 거래대금
                    - pbid: 매수호가
                    - vbid: 매수잔량
                    - pask: 매도호가
                    - vask: 매도잔량

        Example:
            >>> daily = agent.overseas.get_daily_price("NAS", "AAPL")
            >>> for candle in daily['output2'][:5]:
            ...     print(f"{candle['xymd']}: {candle['clos']}")
        """
        self._validate_exchange(excd)

        params = {
            "AUTH": "",
            "EXCD": excd.upper(),
            "SYMB": symb.upper(),
            "GUBN": gubn,
            "BYMD": bymd,
            "MODP": modp,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/dailyprice",
            tr_id="HHDFS76240000",
            params=params,
            use_cache=True,
            cache_ttl=60,  # 일봉은 1분 캐시
        )

    def get_minute_price(
        self,
        excd: str,
        symb: str,
        nmin: str = "1",
        pinc: str = "0",
        nrec: str = "120",
        fill: str = "",
        keyb: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 분봉 조회

        해외주식의 분봉 데이터를 조회합니다.

        Args:
            excd (str): 거래소 코드
            symb (str): 종목코드
            nmin (str): 분봉 간격 ("1": 1분, "5": 5분, "30": 30분, "60": 60분)
            pinc (str): 전일포함여부 ("0": 당일만, "1": 전일포함)
            nrec (str): 조회건수 (최대 120)
            fill (str): 빈값채움여부 (미사용, 빈값)
            keyb (str): 연속조회키 (다음 페이지 조회 시)

        Returns:
            Optional[Dict]: 분봉 데이터
                - output1: 종목 기본 정보
                    - rsym: 종목코드
                    - zdiv: 소수점자리수
                - output2: 분봉 리스트
                    - tymd: 일자
                    - xhms: 시간 (HHMMSS)
                    - open: 시가
                    - high: 고가
                    - low: 저가
                    - last: 종가
                    - evol: 거래량
                    - eamt: 거래대금

        Example:
            >>> minute = agent.overseas.get_minute_price("NAS", "AAPL", nmin="5")
            >>> for candle in minute['output2'][:10]:
            ...     print(f"{candle['xhms']}: {candle['last']}")
        """
        self._validate_exchange(excd)

        params = {
            "AUTH": "",
            "EXCD": excd.upper(),
            "SYMB": symb.upper(),
            "NMIN": nmin,
            "PINC": pinc,
            "NREC": nrec,
            "FILL": fill,
            "KEYB": keyb,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice",
            tr_id="HHDFS76950200",
            params=params,
            use_cache=True,
            cache_ttl=30,  # 분봉은 30초 캐시
        )

    def get_orderbook(
        self,
        excd: str,
        symb: str,
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 10호가 조회

        해외주식의 매수/매도 10호가 정보를 조회합니다.

        Args:
            excd (str): 거래소 코드
            symb (str): 종목코드

        Returns:
            Optional[Dict]: 호가 정보
                - output1: 종목 기본 정보
                    - rsym: 종목코드
                    - zdiv: 소수점자리수
                - output2: 호가 데이터
                    - pask1~10: 매도호가 1~10단계
                    - vask1~10: 매도잔량 1~10단계
                    - pbid1~10: 매수호가 1~10단계
                    - vbid1~10: 매수잔량 1~10단계
                    - tamt: 거래대금
                    - tvol: 거래량

        Example:
            >>> orderbook = agent.overseas.get_orderbook("NAS", "AAPL")
            >>> print(f"매수1호가: {orderbook['output2']['pbid1']}")
            >>> print(f"매도1호가: {orderbook['output2']['pask1']}")
        """
        self._validate_exchange(excd)

        params = {
            "AUTH": "",
            "EXCD": excd.upper(),
            "SYMB": symb.upper(),
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/inquire-asking-price",
            tr_id="HHDFS76200100",
            params=params,
            use_cache=True,
            cache_ttl=3,  # 호가는 3초 캐시
        )

    def get_stock_info(
        self,
        prdt_type_cd: str = "512",
        pdno: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 상품기본정보 조회

        해외주식의 기본 정보 (종목명, 섹터, 상장주식수 등)를 조회합니다.

        Args:
            prdt_type_cd (str): 상품유형코드
                - "512": 미국주식
                - "513": 홍콩주식
                - "514": 중국(상해A)
                - "515": 중국(심천A)
                - "516": 일본주식
                - "517": 베트남주식
            pdno (str): 상품번호 (거래소코드+종목코드, 예: "NAS.AAPL")

        Returns:
            Optional[Dict]: 상품 기본 정보
                - output:
                    - pdno: 상품번호
                    - prdt_name: 상품명
                    - prdt_eng_name: 상품영문명
                    - natn_cd: 국가코드
                    - tr_mket_name: 거래시장명
                    - sctg_name: 업종명
                    - lstg_stck_num: 상장주식수
                    - crcy_cd: 통화코드 (USD, HKD, CNY, JPY, VND)
                    - lstg_dt: 상장일

        Example:
            >>> info = agent.overseas.get_stock_info(pdno="NAS.AAPL")
            >>> print(f"종목명: {info['output']['prdt_eng_name']}")
        """
        params = {
            "PRDT_TYPE_CD": prdt_type_cd,
            "PDNO": pdno.upper(),
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/search-info",
            tr_id="CTPF1702R",
            params=params,
            use_cache=True,
            cache_ttl=3600,  # 기본정보는 1시간 캐시
        )

    def get_ccnl(
        self,
        excd: str,
        symb: str,
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 체결정보 조회

        해외주식의 최근 체결 내역을 조회합니다.

        Args:
            excd (str): 거래소 코드
            symb (str): 종목코드

        Returns:
            Optional[Dict]: 체결 정보
                - output1: 종목 기본 정보
                - output2: 체결 내역 리스트
                    - tymd: 일자
                    - xhms: 체결시각
                    - last: 체결가
                    - diff: 전일대비
                    - sign: 대비부호
                    - tvol: 거래량
                    - tamt: 거래대금

        Example:
            >>> ccnl = agent.overseas.get_ccnl("NAS", "AAPL")
            >>> for trade in ccnl['output2'][:5]:
            ...     print(f"{trade['xhms']}: ${trade['last']} ({trade['tvol']}주)")
        """
        self._validate_exchange(excd)

        params = {
            "AUTH": "",
            "EXCD": excd.upper(),
            "SYMB": symb.upper(),
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/inquire-ccnl",
            tr_id="HHDFS76200300",
            params=params,
            use_cache=True,
            cache_ttl=5,
        )

    def get_holiday(
        self,
        trad_dt: str = "",
        ctx_area_fk: str = "",
        ctx_area_nk: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외거래소 휴장일 조회

        해외거래소의 휴장일 정보를 조회합니다.

        Args:
            trad_dt (str): 기준일자 (YYYYMMDD, 공백 시 당일)
            ctx_area_fk (str): 연속조회키 (FK)
            ctx_area_nk (str): 연속조회키 (NK)

        Returns:
            Optional[Dict]: 휴장일 정보
                - output:
                    - trad_dt: 거래일자
                    - gubn: 구분
                    - natn_cd: 국가코드
                    - natn_name: 국가명
                    - hldy_dt: 휴장일
                    - hldy_nm: 휴장일명

        Example:
            >>> holidays = agent.overseas.get_holiday("20260101")
            >>> for h in holidays['output']:
            ...     print(f"{h['natn_name']}: {h['hldy_dt']} - {h['hldy_nm']}")
        """
        params = {
            "TRAD_DT": trad_dt,
            "CTX_AREA_FK": ctx_area_fk,
            "CTX_AREA_NK": ctx_area_nk,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-stock/v1/quotations/countries-holiday",
            tr_id="CTOS5011R",
            params=params,
            use_cache=True,
            cache_ttl=3600,  # 휴장일은 1시간 캐시
        )

    def get_news_title(
        self,
        excd: str = "",
        symb: str = "",
        news_gb: str = "",
        bymd: str = "",
        nrec: str = "20",
        ctx_area_fk: str = "",
        ctx_area_nk: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외뉴스종합(제목) 조회

        해외주식 관련 뉴스 제목을 조회합니다.

        Args:
            excd (str): 거래소 코드 (공백 시 전체)
            symb (str): 종목코드 (공백 시 전체)
            news_gb (str): 뉴스구분 (공백 시 전체)
            bymd (str): 기준일자 (YYYYMMDD)
            nrec (str): 조회건수 (기본 20)
            ctx_area_fk (str): 연속조회키 (FK)
            ctx_area_nk (str): 연속조회키 (NK)

        Returns:
            Optional[Dict]: 뉴스 제목 리스트
                - output:
                    - data_dt: 등록일자
                    - data_tm: 등록시간
                    - news_sn: 뉴스순번
                    - natn_cd: 국가코드
                    - news_gb: 뉴스구분
                    - news_titl: 뉴스제목

        Example:
            >>> news = agent.overseas.get_news_title(excd="NAS", symb="AAPL")
            >>> for n in news['output'][:5]:
            ...     print(f"{n['data_dt']} {n['data_tm']}: {n['news_titl']}")
        """
        params = {
            "AUTH": "",
            "EXCD": excd.upper() if excd else "",
            "SYMB": symb.upper() if symb else "",
            "NEWS_GB": news_gb,
            "BYMD": bymd,
            "NREC": nrec,
            "CTX_AREA_FK": ctx_area_fk,
            "CTX_AREA_NK": ctx_area_nk,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/news-title",
            tr_id="HHPSTH60100C1",
            params=params,
            use_cache=True,
            cache_ttl=300,  # 뉴스는 5분 캐시
        )

    def get_industry_theme(
        self,
        excd: str,
        symb: str = "",
        iscd_cond: str = "0",
        co_yn: str = "N",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 업종/테마 조회

        해외주식의 업종 및 테마 정보를 조회합니다.

        Args:
            excd (str): 거래소 코드
            symb (str): 종목코드 (공백 시 전체 업종)
            iscd_cond (str): 종목조건 ("0": 전체)
            co_yn (str): 기업여부 ("N": 전체, "Y": 기업만)

        Returns:
            Optional[Dict]: 업종/테마 정보
                - output1: 요약 정보
                - output2: 상세 리스트

        Example:
            >>> theme = agent.overseas.get_industry_theme("NAS")
            >>> print(theme['output2'])
        """
        self._validate_exchange(excd)

        params = {
            "AUTH": "",
            "EXCD": excd.upper(),
            "SYMB": symb.upper() if symb else "",
            "ISCD_COND": iscd_cond,
            "CO_YN": co_yn,
        }

        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/industry-theme",
            tr_id="HHDFS76370000",
            params=params,
            use_cache=True,
            cache_ttl=300,
        )

    def search_symbol(
        self,
        excd: str,
        symb: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        해외주식 종목 검색

        종목코드 또는 종목명으로 해외주식을 검색합니다.

        Args:
            excd (str): 거래소 코드
            symb (str): 검색어 (종목코드 또는 종목명 일부)

        Returns:
            Optional[List[Dict]]: 검색 결과 리스트
                - rsym: 종목코드
                - rnme: 종목명
                - excd: 거래소코드

        Note:
            이 메서드는 get_stock_info를 활용한 검색 기능입니다.
        """
        # 거래소별 상품유형코드 매핑
        prdt_type_map = {
            "NAS": "512",
            "NYS": "512",
            "AMS": "512",
            "HKS": "513",
            "SHS": "514",
            "SZS": "515",
            "TSE": "516",
            "HSX": "517",
            "HNX": "517",
        }

        prdt_type = prdt_type_map.get(excd.upper(), "512")
        pdno = f"{excd.upper()}.{symb.upper()}"

        result = self.get_stock_info(prdt_type_cd=prdt_type, pdno=pdno)

        if result and result.get("rt_cd") == "0":
            return [result.get("output", {})]
        return None
