"""
Stock Market API - 시장 정보 및 순위 조회 전용 모듈

시장 전체 정보와 종목 순위 분석 기능을 담당
- 시장 변동성 정보
- 거래량/체결강도 순위
- 종목 기본 정보
"""

from typing import Optional, Dict, Any, List
import pandas as pd
from ..core.client import KISClient, API_ENDPOINTS
from ..core.base_api import BaseAPI


class StockMarketAPI(BaseAPI):
    """주식 시장 정보 조회 전용 API 클래스"""

    def get_market_fluctuation(self) -> Optional[Dict[str, Any]]:
        """시장 변동성 정보 조회
        
        Returns:
            Optional[Dict[str, Any]]: 시장 변동성 정보를 포함한 응답 데이터
                - rt_cd: 응답 코드 ("0": 성공)
                - msg1: 응답 메시지
                - output: 시장 변동성 데이터
                
        Example:
            >>> market_api = StockMarketAPI(client)
            >>> fluctuation = market_api.get_market_fluctuation()
            >>> print(fluctuation['rt_cd'])  # "0"
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_ASKING_PRICE_EXP_CCN'],
            tr_id="FHKST01010600",
            params={"FID_COND_MRKT_DIV_CODE": "UN"}
        )

    def get_market_rankings(self, volume: int = 5000000) -> Optional[Dict[str, Any]]:
        """거래량 기준 종목 순위 조회
        
        Args:
            volume (int, optional): 최소 거래량 기준. Defaults to 5000000.
            
        Returns:
            Optional[Dict[str, Any]]: 종목 순위 정보를 포함한 응답 데이터
                - rt_cd: 응답 코드 ("0": 성공)
                - msg1: 응답 메시지  
                - output: 순위 데이터 리스트
                
        Example:
            >>> market_api = StockMarketAPI(client)
            >>> rankings = market_api.get_market_rankings(volume=10000000)
            >>> for stock in rankings['output']:
            ...     print(f"코드: {stock['code']}, 순위: {stock['rank']}")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_INVESTOR'],
            tr_id="FHKST01010900",
            params={
                "FID_COND_MRKT_DIV_CODE": "UN",
                "FID_COND_SCR_DIV_CODE": "20171",
                "FID_INPUT_ISCD": "0000",
                "FID_RANK_SORT_CLS_CODE": "0",
                "FID_INPUT_CNT_1": "50",
                "FID_PRC_CLS_CODE": "1",
                "FID_INPUT_PRICE_1": "",
                "FID_INPUT_PRICE_2": "",
                "FID_VOL_CNT": str(volume)
            }
        )

    def get_volume_power(self, volume: int = 0) -> Optional[Dict[str, Any]]:
        """체결강도 순위 조회
        
        Args:
            volume (int, optional): 최소 거래량 기준. Defaults to 0.
            
        Returns:
            Optional[Dict[str, Any]]: 체결강도 순위 정보를 포함한 응답 데이터
                - rt_cd: 응답 코드 ("0": 성공)
                - msg1: 응답 메시지
                - output: 체결강도 데이터 리스트
                
        Example:
            >>> market_api = StockMarketAPI(client)
            >>> power = market_api.get_volume_power()
            >>> for stock in power['output']:
            ...     print(f"코드: {stock['code']}, 체결강도: {stock['power']}")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_INVESTOR'],
            tr_id="FHKST01010900",
            params={
                "FID_COND_MRKT_DIV_CODE": "UN",
                "FID_COND_SCR_DIV_CODE": "20171",
                "FID_INPUT_ISCD": "0000",
                "FID_RANK_SORT_CLS_CODE": "0",
                "FID_INPUT_CNT_1": "50",
                "FID_PRC_CLS_CODE": "1",
                "FID_INPUT_PRICE_1": "",
                "FID_INPUT_PRICE_2": "",
                "FID_VOL_CNT": str(volume)
            }
        )

    def get_stock_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """종목 기본 정보 조회
        
        Args:
            ticker (str): 종목 코드 (예: "005930")
            
        Returns:
            Optional[Dict[str, Any]]: 종목 기본 정보를 포함한 응답 데이터
                - rt_cd: 응답 코드 ("0": 성공)
                - msg1: 응답 메시지
                - output: 종목 기본 정보
                
        Example:
            >>> market_api = StockMarketAPI(client)
            >>> info = market_api.get_stock_info("005930")
            >>> print(f"종목명: {info['output']['name']}")
        """
        return self._make_request_dict(
            endpoint=API_ENDPOINTS['INQUIRE_PRICE'],
            tr_id="FHKST01010100",
            params={"FID_COND_MRKT_DIV_CODE": "UN", "FID_INPUT_ISCD": ticker}
        )

    def get_fluctuation_rank(
        self,
        market: str = "ALL",
        count: str = "50",
        price_min: str = "0",
        price_max: str = "1000000",
        volume_min: str = "100000",
        target_cls_code: str = "0",
        target_exls_cls_code: str = "0",
        div_cls_code: str = "0",
        rate_min: str = "-30",
        rate_max: str = "30"
    ) -> Optional[pd.DataFrame]:
        """등락률 순위 조회
        
        Args:
            market (str): 시장 구분 ("ALL":전체, "KOSPI":코스피, "KOSDAQ":코스닥, "KONEX":코넥스, 기본값: "ALL")
            count (str): 조회할 종목 수 (기본값: "50")
            price_min (str): 최소 가격 (기본값: "0")
            price_max (str): 최대 가격 (기본값: "1000000")
            volume_min (str): 최소 거래량 (기본값: "100000")
            target_cls_code (str): 대상 구분 코드 (기본값: "0" - 전체)
            target_exls_cls_code (str): 대상 제외 구분 코드 (기본값: "0" - 제외없음)
            div_cls_code (str): 분류 구분 코드 (0:전체, 1:보통주, 2:우선주, 기본값: "0")
            rate_min (str): 최소 등락률 % (기본값: "-30")
            rate_max (str): 최대 등락률 % (기본값: "30")
            
        Returns:
            Optional[pd.DataFrame]: 등락률 순위 데이터프레임
                
        Example:
            >>> market_api = StockMarketAPI(client)
            >>> # 코스피 상승률 상위 20개
            >>> df = market_api.get_fluctuation_rank(market="KOSPI", count="20", rate_min="0")
            >>> # 코스닥 하락률 상위 20개
            >>> df = market_api.get_fluctuation_rank(market="KOSDAQ", count="20", rate_max="0")
        """
        # 시장 코드 매핑
        market_code_map = {
            "ALL": "J",      # 전체 (KRX)
            "KOSPI": "J",    # 코스피
            "KOSDAQ": "J",   # 코스닥도 J 사용 (input_iscd로 구분)
            "KONEX": "N"     # 코넥스
        }
        
        # input_iscd 매핑 (시장별 필터링)
        market_iscd_map = {
            "ALL": "0000",     # 전체
            "KOSPI": "0001",   # 코스피
            "KOSDAQ": "1001",  # 코스닥
            "KONEX": "0000"    # 코넥스는 market_code로 구분
        }
        
        market_code = market_code_map.get(market.upper(), "J")
        input_iscd = market_iscd_map.get(market.upper(), "0000")
        
        params = {
            "fid_cond_mrkt_div_code": market_code,
            "fid_cond_scr_div_code": "20170",
            "fid_input_iscd": input_iscd,
            "fid_rank_sort_cls_code": "0",
            "fid_input_cnt_1": count,
            "fid_prc_cls_code": "0",
            "fid_input_price_1": price_min,
            "fid_input_price_2": price_max,
            "fid_vol_cnt": volume_min,
            "fid_trgt_cls_code": target_cls_code,
            "fid_trgt_exls_cls_code": target_exls_cls_code,
            "fid_div_cls_code": div_cls_code,
            "fid_rsfl_rate1": rate_min,
            "fid_rsfl_rate2": rate_max
        }
        
        response = self._make_request_dict(
            endpoint=API_ENDPOINTS['FLUCTUATION'],
            tr_id="FHPST01700000",
            params=params
        )
        
        if response and response.get('rt_cd') == '0' and 'output' in response:
            return pd.DataFrame(response['output'])
        return None

    def get_volume_rank(
        self,
        market: str = "ALL",
        blng_cls_code: str = "0",
        price_min: str = "0",
        price_max: str = "1000000",
        volume_min: str = "100000",
        target_cls_code: str = "111111111",
        target_exls_cls_code: str = "0000000000",
        div_cls_code: str = "0"
    ) -> Optional[pd.DataFrame]:
        """거래량 순위 조회
        
        Args:
            market (str): 시장 구분 ("ALL":전체, "KOSPI":코스피, "KOSDAQ":코스닥, "KONEX":코넥스, "ELW":ELW, 기본값: "ALL")
            blng_cls_code (str): 소속 구분 코드 (0:평균거래량, 1:거래증가율, 2:평균거래회전율, 3:거래금액순, 4:평균거래금액회전율, 기본값: "0")
            price_min (str): 최소 가격 (기본값: "0")
            price_max (str): 최대 가격 (기본값: "1000000")
            volume_min (str): 최소 거래량 (기본값: "100000")
            target_cls_code (str): 대상 구분 코드 (9자리, 기본값: "111111111")
            target_exls_cls_code (str): 대상 제외 구분 코드 (10자리, 기본값: "0000000000")
            div_cls_code (str): 분류 구분 코드 (0:전체, 1:보통주, 2:우선주, 기본값: "0")
            
        Returns:
            Optional[pd.DataFrame]: 거래량 순위 데이터프레임
                
        Example:
            >>> market_api = StockMarketAPI(client)
            >>> # 코스피 거래량 상위
            >>> df = market_api.get_volume_rank(market="KOSPI", volume_min="500000")
            >>> # 코스닥 거래금액순
            >>> df = market_api.get_volume_rank(market="KOSDAQ", blng_cls_code="3")
        """
        # 시장 코드 매핑
        market_code_map = {
            "ALL": "J",      # 전체 (KRX)
            "KOSPI": "J",    # 코스피
            "KOSDAQ": "J",   # 코스닥도 J 사용
            "KONEX": "NX",   # 코넥스
            "ELW": "W"       # ELW
        }
        
        # input_iscd 매핑 (시장별 필터링)
        market_iscd_map = {
            "ALL": "0000",     # 전체
            "KOSPI": "0001",   # 코스피
            "KOSDAQ": "1001",  # 코스닥
            "KONEX": "0000",   # 코넥스
            "ELW": "0000"      # ELW
        }
        
        market_code = market_code_map.get(market.upper(), "J")
        input_iscd = market_iscd_map.get(market.upper(), "0000")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": market_code,
            "FID_COND_SCR_DIV_CODE": "20171",
            "FID_INPUT_ISCD": input_iscd,
            "FID_DIV_CLS_CODE": div_cls_code,
            "FID_BLNG_CLS_CODE": blng_cls_code,
            "FID_TRGT_CLS_CODE": target_cls_code,
            "FID_TRGT_EXLS_CLS_CODE": target_exls_cls_code,
            "FID_INPUT_PRICE_1": price_min,
            "FID_INPUT_PRICE_2": price_max,
            "FID_VOL_CNT": volume_min,
            "FID_INPUT_DATE_1": ""
        }
        
        response = self._make_request_dict(
            endpoint=API_ENDPOINTS['VOLUME_RANK'],
            tr_id="FHPST01710000",
            params=params
        )
        
        if response and response.get('rt_cd') == '0' and 'output' in response:
            return pd.DataFrame(response['output'])
        return None

    def get_volume_power_rank(
        self,
        market: str = "ALL",
        div_cls_code: str = "0",
        price_min: str = "",
        price_max: str = "",
        volume_min: str = "",
        target_cls_code: str = "0",
        target_exls_cls_code: str = "0"
    ) -> Optional[pd.DataFrame]:
        """체결강도 상위 조회
        
        Args:
            market (str): 시장 구분 ("ALL":전체, "KOSPI":코스피(거래소), "KOSDAQ":코스닥, "KOSPI200":코스피200, 기본값: "ALL")
            div_cls_code (str): 분류 구분 코드 (0:전체, 1:보통주, 2:우선주, 기본값: "0")
            price_min (str): 최소 가격 (빈값:전체, 기본값: "")
            price_max (str): 최대 가격 (빈값:전체, 기본값: "")
            volume_min (str): 최소 거래량 (빈값:전체, 기본값: "")
            target_cls_code (str): 대상 구분 코드 (기본값: "0" - 전체)
            target_exls_cls_code (str): 대상 제외 구분 코드 (기본값: "0" - 전체)
            
        Returns:
            Optional[pd.DataFrame]: 체결강도 상위 데이터프레임
                
        Example:
            >>> market_api = StockMarketAPI(client)
            >>> # 코스피 체결강도 상위
            >>> df = market_api.get_volume_power_rank(market="KOSPI")
            >>> # 코스닥 체결강도 상위
            >>> df = market_api.get_volume_power_rank(market="KOSDAQ")
        """
        # 시장 코드는 항상 J (체결강도 API는 J만 지원)
        market_code = "J"
        
        # input_iscd 매핑 (시장별 필터링)
        market_iscd_map = {
            "ALL": "0000",        # 전체
            "KOSPI": "0001",      # 코스피(거래소)
            "KOSDAQ": "1001",     # 코스닥
            "KOSPI200": "2001"    # 코스피200
        }
        
        input_iscd = market_iscd_map.get(market.upper(), "0000")
        
        params = {
            "fid_cond_mrkt_div_code": market_code,
            "fid_cond_scr_div_code": "20168",
            "fid_input_iscd": input_iscd,
            "fid_div_cls_code": div_cls_code,
            "fid_input_price_1": price_min,
            "fid_input_price_2": price_max,
            "fid_vol_cnt": volume_min,
            "fid_trgt_cls_code": target_cls_code,
            "fid_trgt_exls_cls_code": target_exls_cls_code
        }
        
        response = self._make_request_dict(
            endpoint=API_ENDPOINTS['VOLUME_POWER'],
            tr_id="FHPST01680000",
            params=params
        )
        
        if response and response.get('rt_cd') == '0' and 'output' in response:
            return pd.DataFrame(response['output'])
        return None