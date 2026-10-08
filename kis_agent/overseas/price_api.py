"""
해외주식 시세 조회 API

OverseasPriceAPI는 해외주식의 시세, 호가, 차트 데이터를 조회합니다.

지원 거래소:
- NAS: NASDAQ, NYS: NYSE, AMS: AMEX (미국)
- HKS: 홍콩, TSE: 도쿄 (일본)
- SHS: 상해, SZS: 심천 (중국)
- HSX: 호치민, HNX: 하노이 (베트남)
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..core.base_api import BaseAPI
from ..core.client import KISClient
from ._compat import kst_date, warn_ignored, warn_renamed


def _range_condition(bounds: Optional[Tuple[Any, Any]]) -> Tuple[str, str, str]:
    """조건검색 범위를 (선택조건, 시작, 끝)으로 바꾼다. 미사용이면 모두 공백."""
    if bounds is None:
        return "", "", ""
    start, end = bounds
    return "1", str(start), str(end)


class OverseasPriceAPI(BaseAPI):
    """
    해외주식 시세 조회 API

    해외주식의 현재가, 일봉, 분봉, 호가 등 시세 관련 데이터를 조회합니다.

    Attributes:
        client (KISClient): API 통신 클라이언트
        account (Dict): 계좌 정보

    Example:
        >>> from kis_agent import Agent
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
        next_flag: Optional[str] = None,
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
            keyb (str): 연속조회키 (다음 페이지 조회 시). 이전 조회 결과의 마지막 분봉을
                이용해 1분(또는 n분) 전 시각을 YYYYMMDDHHMMSS로 입력
            next_flag (str, optional): 다음여부 ("": 처음 조회, "1": 다음 조회).
                생략하면 keyb가 있을 때 "1", 없으면 "". 다음 조회 시 pinc는 "1"로 줘야 함

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
            "NEXT": next_flag if next_flag is not None else ("1" if keyb else ""),
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
        tday: str = "1",
        keyb: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 체결추이 조회

        해외주식의 최근 체결 내역을 조회합니다.

        Args:
            excd (str): 거래소 코드
            symb (str): 종목코드
            tday (str): 당일전일구분 ("1": 당일, "0": 전일). 기본 당일
            keyb (str): NEXT KEY BUFF (공식 문서상 공백)

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
            "EXCD": excd.upper(),
            "AUTH": "",
            "KEYB": keyb,
            "TDAY": tday,
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
        info_gb: str = "",
        class_cd: str = "",
        nation_cd: str = "",
        exchange_cd: str = "",
        data_dt: str = "",
        data_tm: str = "",
        cts: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외뉴스종합(제목) 조회

        해외주식 관련 뉴스 제목을 조회합니다. 모든 필터는 공백이면 전체입니다.
        이 API는 tr_cont 연속조회가 불가하며 ``cts``(다음키)로 이어 조회합니다.

        Args:
            excd (str): 사용하지 않음. 공식 API는 거래소를 ``exchange_cd``로 받는데
                코드 체계가 다르다(NAS 등과 같다고 보장할 수 없음)고 보아 자동 변환하지
                않습니다. 값을 주면 DeprecationWarning.
            symb (str): 종목코드 (공백 시 전체)
            news_gb (str): ``info_gb``의 옛 이름. ``info_gb``가 비어 있으면 그 값으로
                사용하며 DeprecationWarning.
            bymd (str): ``data_dt``의 옛 이름. ``data_dt``가 비어 있으면 그 값으로
                사용하며 DeprecationWarning.
            nrec (str): 사용하지 않음. 기본값("20")이 아니면 DeprecationWarning.
            ctx_area_fk (str): 사용하지 않음. 값을 주면 DeprecationWarning.
            ctx_area_nk (str): 사용하지 않음 (``cts`` 사용). 값을 주면 DeprecationWarning.
            info_gb (str): 뉴스구분 (공백 시 전체)
            class_cd (str): 중분류 (공백 시 전체)
            nation_cd (str): 국가코드 (공백 시 전체, CN: 중국, HK: 홍콩, US: 미국)
            exchange_cd (str): 거래소코드 (공백 시 전체)
            data_dt (str): 조회일자 (공백 시 전체, 특정일자는 YYYYMMDD)
            data_tm (str): 조회시간 (공백 시 전체, 특정시간은 HHMMSS)
            cts (str): 다음키 (처음 조회는 공백)

        Returns:
            Optional[Dict]: 뉴스 제목 리스트
                - outblock1:
                    - info_gb: 뉴스구분
                    - news_key: 뉴스키
                    - data_dt: 조회일자
                    - data_tm: 조회시간
                    - class_cd: 중분류
                    - class_name: 중분류명
                    - source: 자료원
                    - nation_cd: 국가코드
                    - exchange_cd: 거래소코드
                    - symb: 종목코드
                    - symb_name: 종목명
                    - title: 제목

        Example:
            >>> news = agent.overseas.get_news_title(symb="AAPL")
            >>> for n in news['outblock1'][:5]:
            ...     print(f"{n['data_dt']} {n['data_tm']}: {n['title']}")
        """
        if excd:
            warn_ignored("get_news_title", "excd", "거래소 필터는 exchange_cd를 쓰세요")
        if nrec != "20":
            warn_ignored("get_news_title", "nrec")
        if ctx_area_fk:
            warn_ignored("get_news_title", "ctx_area_fk")
        if ctx_area_nk:
            warn_ignored("get_news_title", "ctx_area_nk", "다음키는 cts를 쓰세요")
        if news_gb and not info_gb:
            warn_renamed("get_news_title", "news_gb", "info_gb")
            info_gb = news_gb
        if bymd and not data_dt:
            warn_renamed("get_news_title", "bymd", "data_dt")
            data_dt = bymd

        params = {
            "INFO_GB": info_gb,
            "CLASS_CD": class_cd,
            "NATION_CD": nation_cd,
            "EXCHANGE_CD": exchange_cd,
            "SYMB": symb.upper() if symb else "",
            "DATA_DT": data_dt,
            "DATA_TM": data_tm,
            "CTS": cts,
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
        icod: str = "",
        vol_rang: str = "0",
        keyb: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 업종별시세 조회

        해외주식의 업종별 시세를 조회합니다. 업종코드(``icod``)는 필수 항목이며
        해외주식 업종코드별조회(HHDFS76370100)로 확인합니다. 이 라이브러리에는 아직
        그 조회 래퍼가 없으므로 코드를 직접 넘겨야 합니다.

        Args:
            excd (str): 거래소 코드
            symb (str): 사용하지 않음. 값을 주면 DeprecationWarning.
            iscd_cond (str): 사용하지 않음. 기본값("0")이 아니면 DeprecationWarning.
            co_yn (str): 사용하지 않음. 기본값("N")이 아니면 DeprecationWarning.
            icod (str): 업종코드
            vol_rang (str): 거래량조건 ("0": 전체, "1": 1백주이상, "2": 1천주이상,
                "3": 1만주이상, "4": 10만주이상, "5": 100만주이상, "6": 1000만주이상)
            keyb (str): NEXT KEY BUFF (공식 문서상 공백)

        Returns:
            Optional[Dict]: 업종별시세
                - output1: 요약 정보 (zdiv, stat, crec, trec, nrec)
                - output2: 종목 리스트 (rsym, excd, symb, name, last, sign, diff,
                  rate, tvol, vask, pask, pbid, vbid, seqn, ename, e_ordyn)

        Example:
            >>> theme = agent.overseas.get_industry_theme("NAS", icod="<업종코드>")
            >>> print(theme['output2'])
        """
        self._validate_exchange(excd)
        if symb:
            warn_ignored("get_industry_theme", "symb")
        if iscd_cond != "0":
            warn_ignored("get_industry_theme", "iscd_cond")
        if co_yn != "N":
            warn_ignored("get_industry_theme", "co_yn")

        params = {
            "KEYB": keyb,
            "AUTH": "",
            "EXCD": excd.upper(),
            "ICOD": icod,
            "VOL_RANG": vol_rang,
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

    def get_inquire_search(
        self,
        excd: str,
        price: Optional[Tuple[Any, Any]] = None,
        rate: Optional[Tuple[Any, Any]] = None,
        market_cap: Optional[Tuple[Any, Any]] = None,
        shares: Optional[Tuple[Any, Any]] = None,
        volume: Optional[Tuple[Any, Any]] = None,
        amount: Optional[Tuple[Any, Any]] = None,
        eps: Optional[Tuple[Any, Any]] = None,
        per: Optional[Tuple[Any, Any]] = None,
        keyb: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식조건검색 [해외주식-015]

        현재가, 등락율, 시가총액 등 조건에 맞는 해외주식을 검색합니다. 각 조건은
        ``(시작, 끝)`` 튜플로 주며, 주지 않은 조건은 사용하지 않습니다(선택조건 공백).
        모의투자도 지원합니다.

        Args:
            excd (str): 거래소 코드 (NYS, NAS, AMS, HKS, SHS, SZS, HSX, HNX, TSE)
            price (tuple): 현재가 범위 (각국 통화 단위)
            rate (tuple): 등락율 범위 (%)
            market_cap (tuple): 시가총액 범위 (단위: 천)
            shares (tuple): 발행주식수 범위 (단위: 천)
            volume (tuple): 거래량 범위 (단위: 주)
            amount (tuple): 거래대금 범위 (단위: 천)
            eps (tuple): EPS 범위
            per (tuple): PER 범위
            keyb (str): NEXT KEY BUFF (처음 조회는 공백)

        Returns:
            Optional[Dict]: 검색 결과
                - output1: 요약 (zdiv, stat, crec, trec, nrec)
                - output2: 종목 리스트 (symb, name, last, rate, tvol, valx, eps, per, rank)

        Example:
            >>> agent.overseas.get_inquire_search("NAS", price=(10, 50), rate=(3, 20))
        """
        self._validate_exchange(excd)
        yn_price, st_price, en_price = _range_condition(price)
        yn_rate, st_rate, en_rate = _range_condition(rate)
        yn_valx, st_valx, en_valx = _range_condition(market_cap)
        yn_shar, st_shar, en_shar = _range_condition(shares)
        yn_volume, st_volume, en_volume = _range_condition(volume)
        yn_amt, st_amt, en_amt = _range_condition(amount)
        yn_eps, st_eps, en_eps = _range_condition(eps)
        yn_per, st_per, en_per = _range_condition(per)

        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/inquire-search",
            tr_id="HHDFS76410000",
            params={
                "AUTH": "",
                "EXCD": excd.upper(),
                "CO_YN_PRICECUR": yn_price,
                "CO_ST_PRICECUR": st_price,
                "CO_EN_PRICECUR": en_price,
                "CO_YN_RATE": yn_rate,
                "CO_ST_RATE": st_rate,
                "CO_EN_RATE": en_rate,
                "CO_YN_VALX": yn_valx,
                "CO_ST_VALX": st_valx,
                "CO_EN_VALX": en_valx,
                "CO_YN_SHAR": yn_shar,
                "CO_ST_SHAR": st_shar,
                "CO_EN_SHAR": en_shar,
                "CO_YN_VOLUME": yn_volume,
                "CO_ST_VOLUME": st_volume,
                "CO_EN_VOLUME": en_volume,
                "CO_YN_AMT": yn_amt,
                "CO_ST_AMT": st_amt,
                "CO_EN_AMT": en_amt,
                "CO_YN_EPS": yn_eps,
                "CO_ST_EPS": st_eps,
                "CO_EN_EPS": en_eps,
                "CO_YN_PER": yn_per,
                "CO_ST_PER": st_per,
                "CO_EN_PER": en_per,
                "KEYB": keyb,
            },
            use_cache=True,
            cache_ttl=30,
        )

    def get_inquire_time_indexchartprice(
        self,
        code: str,
        market: str = "N",
        hour_cls_code: str = "0",
        past_data: str = "Y",
    ) -> Optional[Dict[str, Any]]:
        """
        해외지수분봉조회 [해외주식-031]

        해외지수·환율의 분봉을 조회합니다. 모의투자는 지원하지 않습니다.

        Args:
            code: 종목코드 (지수 예: SPX, 환율 코드)
            market: 조건 시장 분류 코드 (N: 해외지수, X: 환율, KX: 원화환율)
            hour_cls_code: 시간 구분 코드 (0: 정규장, 1: 시간외)
            past_data: 과거 데이터 포함 여부 (Y/N)

        Returns:
            Optional[Dict]: 분봉 데이터
                - output1: 기본 정보 (hts_kor_isnm, ovrs_nmix_prpr, prdy_ctrt, acml_vol)
                - output2: 분봉 리스트 (stck_bsop_date, stck_cntg_hour, optn_prpr,
                  optn_oprc, optn_hgpr, optn_lwpr, cntg_vol)

        Example:
            >>> agent.overseas.get_inquire_time_indexchartprice("SPX")
        """
        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/inquire-time-indexchartprice",
            tr_id="FHKST03030200",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_HOUR_CLS_CODE": hour_cls_code,
                "FID_PW_DATA_INCU_YN": past_data,
            },
            use_cache=True,
            cache_ttl=30,
        )

    def get_industry_price(self, excd: str) -> Optional[Dict[str, Any]]:
        """
        해외주식 업종별코드조회 [해외주식-049]

        거래소의 업종코드와 업종명을 조회합니다. 여기서 얻은 ``icod``를
        ``get_industry_theme``에 넘깁니다. 모의투자는 지원하지 않습니다.

        Args:
            excd: 거래소 코드 (NYS, NAS, AMS, HKS, SHS, SZS, HSX, HNX, TSE)

        Returns:
            Optional[Dict]:
                - output1: nrec (레코드 수)
                - output2: 업종 리스트 (icod: 업종코드, name: 업종명)

        Example:
            >>> agent.overseas.get_industry_price("NAS")
        """
        self._validate_exchange(excd)
        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/industry-price",
            tr_id="HHDFS76370100",
            params={"AUTH": "", "EXCD": excd.upper()},
            use_cache=True,
            cache_ttl=3600,
        )

    def get_inquire_daily_chartprice(
        self,
        code: str,
        start_date: str = "",
        end_date: str = "",
        market: str = "N",
        period: str = "D",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 종목/지수/환율기간별시세(일/주/월/년) [해외주식-012]

        해외지수·환율·국채·금선물과 일부 미국 종목(다우30, 나스닥100, S&P500)의
        기간별 시세를 조회합니다. 그 외 종목은 ``get_daily_price``를 쓰세요.
        모의투자도 지원합니다.

        Args:
            code: 종목코드 (해외주식 마스터 코드 참조, 예: .DJI)
            start_date: 시작일자 YYYYMMDD (공백: 종료일자 30일 전)
            end_date: 종료일자 YYYYMMDD (공백: 오늘, 서울 기준)
            market: 조건 시장 분류 코드 (N: 해외지수, X: 환율, I: 국채, S: 금선물)
            period: 기간 분류 코드 (D: 일, W: 주, M: 월, Y: 년)

        Returns:
            Optional[Dict]:
                - output1: 기본 정보 (hts_kor_isnm, ovrs_nmix_prpr, prdy_ctrt, acml_vol)
                - output2: 기간별 리스트 (stck_bsop_date, ovrs_nmix_prpr, ovrs_nmix_oprc,
                  ovrs_nmix_hgpr, ovrs_nmix_lwpr, acml_vol)

        Example:
            >>> agent.overseas.get_inquire_daily_chartprice(".DJI", "20240101", "20240331")
        """
        end_date = end_date or kst_date()
        if not start_date:
            end_day = datetime.strptime(end_date, "%Y%m%d")
            start_date = (end_day - timedelta(days=30)).strftime("%Y%m%d")
        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/inquire-daily-chartprice",
            tr_id="FHKST03030100",
            params={
                "FID_COND_MRKT_DIV_CODE": market,
                "FID_INPUT_ISCD": code,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date,
                "FID_PERIOD_DIV_CODE": period,
            },
            use_cache=True,
            cache_ttl=60,
        )

    def get_period_rights(
        self,
        rght_type_cd: str = "%%",
        inqr_dvsn_cd: str = "02",
        inqr_strt_dt: str = "",
        inqr_end_dt: str = "",
        pdno: str = "",
        prdt_type_cd: str = "",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 기간별권리조회 [해외주식-052]

        기간 내 권리(배당, 유무상증자, 분할 등) 일정을 조회합니다. 연속조회는 끝까지
        (최대 ``max_pages``) 이어 받아 합칩니다. 모의투자는 지원하지 않습니다.

        Args:
            rght_type_cd: 권리유형코드 (%%: 전체, 01: 유상, 02: 무상, 03: 배당,
                11: 합병, 14: 액면분할, 15: 액면병합, 17: 감자, 54: WR청구,
                61: 원리금상환, 71: WR소멸, 74: 배당옵션, 75: 특별배당,
                76: ISINCODE변경, 77: 실권주청약)
            inqr_dvsn_cd: 조회구분코드 (02: 현지기준일, 03: 청약시작일, 04: 청약종료일)
            inqr_strt_dt: 조회시작일자 YYYYMMDD (공백: 오늘, 서울 기준)
            inqr_end_dt: 조회종료일자 YYYYMMDD (공백: 시작일 이후 30일)
            pdno: 상품번호 (공백: 전체)
            prdt_type_cd: 상품유형코드 (공백: 전체)
            max_pages: 최대 페이지 수

        Returns:
            Optional[Dict]: output 리스트 (bass_dt, rght_type_cd, pdno, prdt_name,
                acpl_bass_dt, sbsc_strt_dt, sbsc_end_dt, cash_alct_rt, stck_alct_rt, crcy_cd)

        Example:
            >>> agent.overseas.get_period_rights(inqr_strt_dt="20240417", inqr_end_dt="20240517")
        """
        inqr_strt_dt = inqr_strt_dt or kst_date()
        inqr_end_dt = inqr_end_dt or kst_date(30)
        return self._paginate(
            endpoint="/uapi/overseas-price/v1/quotations/period-rights",
            tr_id="CTRGT011R",
            params={
                "RGHT_TYPE_CD": rght_type_cd,
                "INQR_DVSN_CD": inqr_dvsn_cd,
                "INQR_STRT_DT": inqr_strt_dt,
                "INQR_END_DT": inqr_end_dt,
                "PDNO": pdno,
                "PRDT_TYPE_CD": prdt_type_cd,
                "CTX_AREA_NK50": "",
                "CTX_AREA_FK50": "",
            },
            cursor=[
                ("CTX_AREA_FK50", "ctx_area_fk50"),
                ("CTX_AREA_NK50", "ctx_area_nk50"),
            ],
            output_keys=("output",),
            max_pages=max_pages,
        )

    def get_colable_by_company(
        self,
        pdno: str,
        natn_cd: str = "840",
        inqr_sqn_dvsn: str = "01",
        max_pages: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        당사 해외주식담보대출 가능 종목 [해외주식-051]

        당사에서 담보대출이 가능한 해외주식과 담보비율을 조회합니다.
        모의투자는 지원하지 않습니다.

        Args:
            pdno: 상품번호 (종목코드, 예: AMD)
            natn_cd: 국가코드 (840: 미국, 344: 홍콩, 156: 중국)
            inqr_sqn_dvsn: 조회순서구분 (01: 이름순, 02: 코드순)
            max_pages: 최대 페이지 수

        Returns:
            Optional[Dict]:
                - output1: 종목 리스트 (pdno, ovrs_item_name, loan_rt, mgge_mntn_rt,
                  mgge_ensu_rt, loan_exec_psbl_yn, crcy_cd, ovrs_excg_cd)
                - output2: loan_psbl_item_num (대출가능종목수)

        Example:
            >>> agent.overseas.get_colable_by_company("AMD")
        """
        return self._paginate(
            endpoint="/uapi/overseas-price/v1/quotations/colable-by-company",
            tr_id="CTLN4050R",
            params={
                "PDNO": pdno,
                "PRDT_TYPE_CD": "",
                "INQR_STRT_DT": "",
                "INQR_END_DT": "",
                "INQR_DVSN": "",
                "NATN_CD": natn_cd,
                "INQR_SQN_DVSN": inqr_sqn_dvsn,
                "RT_DVSN_CD": "",
                "RT": "",
                "LOAN_PSBL_YN": "",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
            cursor=[
                ("CTX_AREA_FK100", "ctx_area_fk100"),
                ("CTX_AREA_NK100", "ctx_area_nk100"),
            ],
            output_keys=("output1",),
            max_pages=max_pages,
        )

    def get_brknews_title(
        self, news_ofer_entp_code: str = "0"
    ) -> Optional[Dict[str, Any]]:
        """
        해외속보(제목) [해외주식-055]

        해외 속보 뉴스 제목을 조회합니다. 나머지 조건은 공식 문서상 공백입니다.
        모의투자는 지원하지 않습니다.

        Args:
            news_ofer_entp_code: 뉴스제공업체코드 (0: 전체조회)

        Returns:
            Optional[Dict]: output 리스트 (cntt_usiq_srno, news_ofer_entp_code,
                data_dt, data_tm, hts_pbnt_titl_cntt, dorg, iscd1~10, kor_isnm1~10)

        Example:
            >>> agent.overseas.get_brknews_title()
        """
        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/brknews-title",
            tr_id="FHKST01011801",
            params={
                "FID_NEWS_OFER_ENTP_CODE": news_ofer_entp_code,
                "FID_COND_MRKT_CLS_CODE": "",
                "FID_INPUT_ISCD": "",
                "FID_TITL_CNTT": "",
                "FID_INPUT_DATE_1": "",
                "FID_INPUT_HOUR_1": "",
                "FID_RANK_SORT_CLS_CODE": "",
                "FID_INPUT_SRNO": "",
                "FID_COND_SCR_DIV_CODE": "11801",
            },
            use_cache=True,
            cache_ttl=60,
        )

    def get_rights_by_ice(
        self,
        ncod: str,
        symb: str,
        st_ymd: str = "",
        ed_ymd: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 권리종합 [해외주식-050]

        ICE 공시 기준 종목의 권리(배당락, 지급일, 기준일, 상환 등) 일정을 조회합니다.
        모의투자는 지원하지 않습니다.

        Args:
            ncod: 국가코드 (CN: 중국, HK: 홍콩, US: 미국, JP: 일본, VN: 베트남)
            symb: 종목코드
            st_ymd: 일자 시작일 YYYYMMDD (공백: 오늘 - 3개월)
            ed_ymd: 일자 종료일 YYYYMMDD (공백: 오늘 + 3개월)

        Returns:
            Optional[Dict]: output1 리스트 (anno_dt, ca_title, div_lock_dt, pay_dt,
                record_dt, validity_dt, lock_dt, delist_dt, redempt_dt, effective_dt)

        Example:
            >>> agent.overseas.get_rights_by_ice("US", "NVDL")
        """
        return self._make_request_dict(
            endpoint="/uapi/overseas-price/v1/quotations/rights-by-ice",
            tr_id="HHDFS78330900",
            params={
                "NCOD": ncod.upper(),
                "SYMB": symb.upper(),
                "ST_YMD": st_ymd,
                "ED_YMD": ed_ymd,
            },
            use_cache=True,
            cache_ttl=300,
        )
