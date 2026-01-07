"""
해외주식 순위 API

OverseasRankingAPI는 해외주식 시장의 각종 순위 데이터를 조회합니다.
"""

import logging
from typing import Any, Dict, Optional

from ..core.base_api import BaseAPI
from ..core.client import KISClient


class OverseasRankingAPI(BaseAPI):
    """
    해외주식 순위 API

    해외주식 시장의 거래량, 거래대금, 등락률, 시가총액 등
    각종 순위 데이터를 조회합니다.

    지원 거래소:
    - NAS: NASDAQ (미국)
    - NYS: NYSE (미국)
    - AMS: AMEX (미국)
    - HKS: 홍콩
    - SHS: 상해
    - SZS: 심천
    - TSE: 도쿄
    - HSX: 호치민
    - HNX: 하노이

    공통 파라미터:
    - vol_rang: 거래량조건
        - "0": 전체
        - "1": 100주 이상
        - "2": 1,000주 이상
        - "3": 10,000주 이상
        - "4": 100,000주 이상
        - "5": 1,000,000주 이상
        - "6": 10,000,000주 이상
    - nday: N일자값
        - "0": 당일
        - "1": 2일
        - "2": 3일
        - "3": 5일
        - "4": 10일
        - "5": 20일
        - "6": 30일
        - "7": 60일
        - "8": 120일
        - "9": 1년

    Example:
        >>> from pykis import Agent
        >>> agent = Agent(...)
        >>> # 나스닥 거래량 순위 조회
        >>> result = agent.overseas.trade_volume_ranking("NAS")
        >>> for item in result['output2']:
        ...     print(f"{item['symb']}: {item['tvol']} 주")
    """

    def __init__(
        self,
        client: KISClient,
        account_info: Optional[Dict[str, Any]] = None,
        enable_cache: bool = True,
        cache_config: Optional[Dict[str, Any]] = None,
        _from_agent: bool = False,
    ) -> None:
        """
        OverseasRankingAPI 초기화

        Args:
            client (KISClient): API 통신 클라이언트
            account_info (dict): 계좌 정보 (순위 조회는 필요 없음)
            enable_cache (bool): 캐시 사용 여부
            cache_config (dict, optional): 캐시 설정
            _from_agent (bool): Agent를 통해 생성되었는지 여부
        """
        super().__init__(
            client, account_info, enable_cache, cache_config, _from_agent=_from_agent
        )

    def trade_volume_ranking(
        self,
        excd: str,
        nday: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 거래량순위 [해외주식-043]

        거래량 기준 상위 종목을 조회합니다.

        Args:
            excd (str): 거래소 코드 (NAS, NYS, AMS, HKS, SHS, SZS, TSE, HSX, HNX)
            nday (str): N일자값 ("0": 당일, "1": 2일, ... "9": 1년)
            vol_rang (str): 거래량조건 ("0": 전체, "1": 100주이상, ...)

        Returns:
            Optional[Dict]: 거래량 순위 데이터
                - output1: 요약 정보
                - output2: 종목별 순위 리스트
                    - symb: 종목코드
                    - name: 종목명
                    - tvol: 거래량
                    - last: 현재가
                    - diff: 전일대비
                    - rate: 등락률

        Example:
            >>> result = agent.overseas.trade_volume_ranking("NAS")
            >>> for item in result['output2'][:10]:
            ...     print(f"{item['name']}: {item['tvol']}주")
        """
        try:
            params = {
                "EXCD": excd.upper(),
                "NDAY": nday,
                "VOL_RANG": vol_rang,
                "AUTH": "",
                "KEYB": "",
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/ranking/trade-vol",
                tr_id="HHDFS76310010",
                params=params,
                use_cache=True,
                cache_ttl=30,  # 순위 데이터는 30초 캐시
            )
        except Exception as e:
            logging.error(f"해외주식 거래량순위 조회 실패: {e}")
            return None

    def trade_amount_ranking(
        self,
        excd: str,
        nday: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 거래대금순위 [해외주식-044]

        거래대금 기준 상위 종목을 조회합니다.

        Args:
            excd (str): 거래소 코드
            nday (str): N일자값
            vol_rang (str): 거래량조건

        Returns:
            Optional[Dict]: 거래대금 순위 데이터
                - output1: 요약 정보
                - output2: 종목별 순위 리스트
                    - symb: 종목코드
                    - name: 종목명
                    - tamt: 거래대금
                    - tvol: 거래량
                    - last: 현재가

        Example:
            >>> result = agent.overseas.trade_amount_ranking("NYS")
        """
        try:
            params = {
                "EXCD": excd.upper(),
                "NDAY": nday,
                "VOL_RANG": vol_rang,
                "AUTH": "",
                "KEYB": "",
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/ranking/trade-pbmn",
                tr_id="HHDFS76320010",
                params=params,
                use_cache=True,
                cache_ttl=30,
            )
        except Exception as e:
            logging.error(f"해외주식 거래대금순위 조회 실패: {e}")
            return None

    def trade_growth_ranking(
        self,
        excd: str,
        nday: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 거래증가율순위 [해외주식-045]

        거래량 증가율 기준 상위 종목을 조회합니다.

        Args:
            excd (str): 거래소 코드
            nday (str): N일자값
            vol_rang (str): 거래량조건

        Returns:
            Optional[Dict]: 거래증가율 순위 데이터
                - output2: 종목별 순위 리스트
                    - symb: 종목코드
                    - name: 종목명
                    - grt: 거래증가율

        Example:
            >>> result = agent.overseas.trade_growth_ranking("NAS")
        """
        try:
            params = {
                "EXCD": excd.upper(),
                "NDAY": nday,
                "VOL_RANG": vol_rang,
                "AUTH": "",
                "KEYB": "",
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/ranking/trade-growth",
                tr_id="HHDFS76330000",
                params=params,
                use_cache=True,
                cache_ttl=30,
            )
        except Exception as e:
            logging.error(f"해외주식 거래증가율순위 조회 실패: {e}")
            return None

    def trade_turnover_ranking(
        self,
        excd: str,
        nday: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 거래회전율순위 [해외주식-046]

        거래회전율 기준 상위 종목을 조회합니다.

        Args:
            excd (str): 거래소 코드
            nday (str): N일자값
            vol_rang (str): 거래량조건

        Returns:
            Optional[Dict]: 거래회전율 순위 데이터
                - output2: 종목별 순위 리스트
                    - symb: 종목코드
                    - name: 종목명
                    - turn: 거래회전율

        Example:
            >>> result = agent.overseas.trade_turnover_ranking("HKS")
        """
        try:
            params = {
                "EXCD": excd.upper(),
                "NDAY": nday,
                "VOL_RANG": vol_rang,
                "AUTH": "",
                "KEYB": "",
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/ranking/trade-turnover",
                tr_id="HHDFS76340000",
                params=params,
                use_cache=True,
                cache_ttl=30,
            )
        except Exception as e:
            logging.error(f"해외주식 거래회전율순위 조회 실패: {e}")
            return None

    def market_cap_ranking(
        self,
        excd: str,
        nday: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 시가총액순위 [해외주식-047]

        시가총액 기준 상위 종목을 조회합니다.

        Args:
            excd (str): 거래소 코드
            nday (str): N일자값
            vol_rang (str): 거래량조건

        Returns:
            Optional[Dict]: 시가총액 순위 데이터
                - output2: 종목별 순위 리스트
                    - symb: 종목코드
                    - name: 종목명
                    - mcap: 시가총액
                    - last: 현재가

        Example:
            >>> result = agent.overseas.market_cap_ranking("NAS")
            >>> # 나스닥 시총 Top 10
            >>> for item in result['output2'][:10]:
            ...     print(f"{item['name']}: ${item['mcap']}")
        """
        try:
            params = {
                "EXCD": excd.upper(),
                "NDAY": nday,
                "VOL_RANG": vol_rang,
                "AUTH": "",
                "KEYB": "",
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/ranking/market-cap",
                tr_id="HHDFS76350100",
                params=params,
                use_cache=True,
                cache_ttl=60,  # 시가총액 순위는 1분 캐시
            )
        except Exception as e:
            logging.error(f"해외주식 시가총액순위 조회 실패: {e}")
            return None

    def price_change_ranking(
        self,
        excd: str,
        nday: str = "0",
        gubn: str = "1",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 상승률/하락률 순위

        등락률 기준 상위/하위 종목을 조회합니다.

        Args:
            excd (str): 거래소 코드
            nday (str): N일자값
            gubn (str): 상승/하락 구분
                - "1": 상승률 순위 (기본값)
                - "2": 하락률 순위
            vol_rang (str): 거래량조건

        Returns:
            Optional[Dict]: 등락률 순위 데이터
                - output2: 종목별 순위 리스트
                    - symb: 종목코드
                    - name: 종목명
                    - last: 현재가
                    - diff: 전일대비
                    - rate: 등락률

        Example:
            >>> # 나스닥 상승률 순위
            >>> result = agent.overseas.price_change_ranking("NAS", gubn="1")
            >>> # 나스닥 하락률 순위
            >>> result = agent.overseas.price_change_ranking("NAS", gubn="2")
        """
        try:
            params = {
                "EXCD": excd.upper(),
                "NDAY": nday,
                "GUBN": gubn,
                "VOL_RANG": vol_rang,
                "AUTH": "",
                "KEYB": "",
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/ranking/updown-rate",
                tr_id="HHDFS76290000",
                params=params,
                use_cache=True,
                cache_ttl=30,
            )
        except Exception as e:
            logging.error(f"해외주식 등락률순위 조회 실패: {e}")
            return None

    def price_fluctuation_ranking(
        self,
        excd: str,
        nday: str = "0",
        gubn: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 가격급등락 [해외주식-038]

        가격이 급등/급락한 종목을 조회합니다.

        Args:
            excd (str): 거래소 코드
            nday (str): N일자값
            gubn (str): 급등/급락 구분
                - "0": 급등 (기본값)
                - "1": 급락
            vol_rang (str): 거래량조건

        Returns:
            Optional[Dict]: 가격급등락 데이터
                - output2: 종목별 리스트

        Example:
            >>> # 나스닥 급등 종목
            >>> result = agent.overseas.price_fluctuation_ranking("NAS", gubn="0")
        """
        try:
            params = {
                "EXCD": excd.upper(),
                "NDAY": nday,
                "GUBN": gubn,
                "VOL_RANG": vol_rang,
                "AUTH": "",
                "KEYB": "",
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/ranking/price-fluct",
                tr_id="HHDFS76260000",
                params=params,
                use_cache=True,
                cache_ttl=30,
            )
        except Exception as e:
            logging.error(f"해외주식 가격급등락 조회 실패: {e}")
            return None

    def new_high_low_ranking(
        self,
        excd: str,
        nday: str = "0",
        gubn: str = "1",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 신고/신저가 [해외주식-042]

        신고가 또는 신저가 갱신 종목을 조회합니다.

        Args:
            excd (str): 거래소 코드
            nday (str): N일자값
            gubn (str): 신고/신저 구분
                - "0": 신저가
                - "1": 신고가 (기본값)
            vol_rang (str): 거래량조건

        Returns:
            Optional[Dict]: 신고/신저가 데이터
                - output2: 종목별 리스트
                    - symb: 종목코드
                    - name: 종목명
                    - last: 현재가
                    - high: 고가
                    - low: 저가

        Example:
            >>> # 나스닥 신고가 종목
            >>> result = agent.overseas.new_high_low_ranking("NAS", gubn="1")
        """
        try:
            params = {
                "EXCD": excd.upper(),
                "NDAY": nday,
                "GUBN": gubn,
                "VOL_RANG": vol_rang,
                "AUTH": "",
                "KEYB": "",
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/ranking/new-highlow",
                tr_id="HHDFS76300000",
                params=params,
                use_cache=True,
                cache_ttl=60,  # 신고/신저가는 1분 캐시
            )
        except Exception as e:
            logging.error(f"해외주식 신고/신저가 조회 실패: {e}")
            return None

    def volume_power_ranking(
        self,
        excd: str,
        nday: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 매수체결강도상위 [해외주식-040]

        매수 체결강도 기준 상위 종목을 조회합니다.
        체결강도는 매수 vs 매도 세력의 우위를 나타냅니다.

        Args:
            excd (str): 거래소 코드
            nday (str): N일자값
            vol_rang (str): 거래량조건

        Returns:
            Optional[Dict]: 매수체결강도 순위 데이터
                - output2: 종목별 순위 리스트
                    - symb: 종목코드
                    - name: 종목명
                    - vpwr: 체결강도

        Example:
            >>> result = agent.overseas.volume_power_ranking("NAS")
        """
        try:
            params = {
                "EXCD": excd.upper(),
                "NDAY": nday,
                "VOL_RANG": vol_rang,
                "AUTH": "",
                "KEYB": "",
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/ranking/volume-power",
                tr_id="HHDFS76280000",
                params=params,
                use_cache=True,
                cache_ttl=30,
            )
        except Exception as e:
            logging.error(f"해외주식 매수체결강도 조회 실패: {e}")
            return None

    def volume_surge_ranking(
        self,
        excd: str,
        mixn: str = "0",
        vol_rang: str = "0",
    ) -> Optional[Dict[str, Any]]:
        """
        해외주식 거래량급증 [해외주식-039]

        최근 N분 대비 거래량이 급증한 종목을 조회합니다.

        Args:
            excd (str): 거래소 코드
            mixn (str): N분전 콤보값
                - "0": 1분전 (기본값)
                - "1": 2분전
                - "2": 3분전
                - "3": 5분전
                - "4": 10분전
                - "5": 15분전
                - "6": 20분전
                - "7": 30분전
                - "8": 60분전
                - "9": 120분전
            vol_rang (str): 거래량조건

        Returns:
            Optional[Dict]: 거래량급증 데이터
                - output2: 종목별 리스트
                    - symb: 종목코드
                    - name: 종목명
                    - tvol: 거래량
                    - surge_rate: 급증률

        Example:
            >>> # 나스닥 5분간 거래량 급증 종목
            >>> result = agent.overseas.volume_surge_ranking("NAS", mixn="3")
        """
        try:
            params = {
                "EXCD": excd.upper(),
                "MIXN": mixn,
                "VOL_RANG": vol_rang,
                "AUTH": "",
                "KEYB": "",
            }

            return self._make_request_dict(
                endpoint="/uapi/overseas-stock/v1/ranking/volume-surge",
                tr_id="HHDFS76270000",
                params=params,
                use_cache=True,
                cache_ttl=15,  # 거래량급증은 15초 캐시 (실시간성 중요)
            )
        except Exception as e:
            logging.error(f"해외주식 거래량급증 조회 실패: {e}")
            return None
