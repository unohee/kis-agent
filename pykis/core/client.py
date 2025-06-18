import json
import logging
import threading
import time
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import requests

from .auth import auth, getTREnv
from .config import KISConfig

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_ENDPOINTS = {
    # === 주식 기본 API ===
    'STOCK_PRICE': '/uapi/domestic-stock/v1/quotations/inquire-price',
    'STOCK_DAILY': '/uapi/domestic-stock/v1/quotations/inquire-daily-price',
    'STOCK_MINUTE': '/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice',
    'STOCK_MEMBER': '/uapi/domestic-stock/v1/quotations/inquire-member',
    'STOCK_INVESTOR': '/uapi/domestic-stock/v1/quotations/inquire-investor',
    'STOCK_INFO': '/uapi/domestic-stock/v1/quotations/search-stock-info',
    'STOCK_BASIC': '/uapi/domestic-stock/v1/quotations/inquire-basic-info',
    
    # === 프로그램매매 API ===
    'PROGRAM_TRADE_BY_STOCK_DAILY': '/uapi/domestic-stock/v1/quotations/program-trade-by-stock-daily',  # 종목별 프로그램매매추이(일별)
    'PROGRAM_TRADE_BY_STOCK': '/uapi/domestic-stock/v1/quotations/program-trade-by-stock',  # 종목별 프로그램매매추이(체결)
    'PROGRAM_TRADE_SUMMARY': '/uapi/domestic-stock/v1/quotations/inquire-program-trade',  # 프로그램매매 요약
    'PROGRAM_TRADE_PERIOD': '/uapi/domestic-stock/v1/quotations/comp-program-trade-daily',  # 프로그램매매종합추이(기간)
    'NET_BUY_VOLUME': '/uapi/domestic-stock/v1/quotations/inquire-net-buy-volume',  # 순매수량
    
    # === 거래/주문 API ===
    'ACCOUNT_BALANCE': '/uapi/domestic-stock/v1/trading/inquire-balance',
    'POSSIBLE_ORDER': '/uapi/domestic-stock/v1/trading/inquire-psbl-order',
    'ORDER_CASH': '/uapi/domestic-stock/v1/trading/order-cash',
    'MEMBER_TRANSACTION': '/uapi/domestic-stock/v1/quotations/inquire-member-daily',
    
    # === 기타 시세 API ===
    'PBAR_TRATIO': '/uapi/domestic-stock/v1/quotations/inquire-price-by-time',
    'ORDERBOOK': '/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn',
    'OVERTIME': '/uapi/domestic-stock/v1/quotations/inquire-daily-overtimeprice',
    'CCNL': '/uapi/domestic-stock/v1/quotations/inquire-ccnl',
    'MINUTE_PRICE': '/uapi/domestic-stock/v1/quotations/inquire-minute-price',
    'TIME_CONCLUSION': '/uapi/domestic-stock/v1/quotations/inquire-time-itemconclusion',
    'OVERTIME_CONCLUSION': '/uapi/domestic-stock/v1/quotations/inquire-time-overtimeconclusion',
    'DAILY_CHART': '/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice',
    'INDEX_CHART': '/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice',
    'EXPECTED_CLOSING_PRICE': '/uapi/domestic-stock/v1/quotations/exp-closing-price',
    
    # === 시장 정보 API ===
    'MARKET_FLUCTUATION': '/uapi/domestic-stock/v1/quotations/inquire-market-index',
    'MARKET_RANKINGS': '/uapi/domestic-stock/v1/quotations/volume-rank',
    'VOLUME_RANK': '/uapi/domestic-stock/v1/quotations/inquire-volume-rank',
    'PRICE_RANK': '/uapi/domestic-stock/v1/quotations/inquire-price-rank',
    'PROFIT_RANK': '/uapi/domestic-stock/v1/quotations/inquire-profit-rank',
    'MARKET_MONEY': '/uapi/domestic-stock/v1/quotations/inquire-market-money',
    
    # === 투자자별 API ===
    'DOMESTIC_INVESTOR': '/uapi/domestic-stock/v1/quotations/inquire-domestic-investor',
    'FOREIGN_INVESTOR': '/uapi/domestic-stock/v1/quotations/inquire-foreign-investor',
    'FOREIGN_TRADE': '/uapi/domestic-stock/v1/quotations/inquire-foreign-trade',
    'FOREIGN_NET_BUY': '/uapi/domestic-stock/v1/quotations/inquire-foreign-net-buy',
    
    # === 재무 정보 API ===
    'STOCK_INCOME': '/uapi/domestic-stock/v1/quotations/inquire-income-statement',
    'STOCK_FINANCIAL': '/uapi/domestic-stock/v1/quotations/inquire-financial-ratio',
    'STOCK_STABILITY': '/uapi/domestic-stock/v1/quotations/inquire-stability-ratio',
    'STOCK_GROWTH': '/uapi/domestic-stock/v1/quotations/inquire-growth-ratio',
    'STOCK_ESTIMATE': '/uapi/domestic-stock/v1/quotations/inquire-estimate',
    'STOCK_BROKER_OPINION': '/uapi/domestic-stock/v1/quotations/inquire-broker-opinion',
    'STOCK_OPINION': '/uapi/domestic-stock/v1/quotations/inquire-stock-opinion',
    
    # === 기타 ===
    'HOLIDAY_CHECK': '/uapi/domestic-stock/v1/quotations/chk-holiday',
    'HOLIDAY_INFO': '/uapi/domestic-stock/v1/quotations/chk-holiday',
    'CONDITIONED_STOCK': '/uapi/domestic-stock/v1/quotations/psearch-result',
    'STOCK_PRICE_2': '/uapi/domestic-stock/v1/quotations/inquire-price-2',
    
    # === 해외 API ===
    'OVERSEAS_PRICE': '/uapi/overseas-price/v1/quotations/inquire-price',
    'OVERSEAS_PRICE_DETAIL': '/uapi/overseas-price/v1/quotations/inquire-price-detail',
    'OVERSEAS_NEWS': '/uapi/overseas-price/v1/quotations/inquire-news',
    'OVERSEAS_RIGHT': '/uapi/overseas-price/v1/quotations/inquire-right',
    
    # === 채권 API ===
    'BOND_PRICE': '/uapi/domestic-bond/v1/quotations/inquire-price',
}

_shared_rate_limit_lock = threading.Lock()
_last_api_call_time = [0]

class KISClient:
    """
    한국투자증권 OpenAPI 클라이언트

    이 클래스는 한국투자증권 OpenAPI와의 통신을 담당합니다.
    API 요청, 토큰 관리, 요청 제한 관리 등의 기능을 제공합니다.

    Attributes:
        config (KISConfig): API 설정 정보
        token (str): API 인증 토큰
        base_url (str): API 기본 URL
        verbose (bool): 상세 로깅 여부

    Example:
        >>> client = KISClient()
        >>> response = client.make_request('/uapi/domestic-stock/v1/quotations/inquire-price', 'FHKST01010100', {'FID_COND_MRKT_DIV_CODE': 'J', 'FID_INPUT_ISCD': '005930'})
    """

    def __init__(self, svr: str = 'prod', config=None, verbose: bool = False):
        """
        KISClient를 초기화합니다.

        Args:
            svr (str): 서버 환경 ('prod' 또는 'dev')
            config (KISConfig, optional): API 설정 정보
            verbose (bool): 상세 로깅 여부

        Raises:
            Exception: 인증 실패 시 발생
        """
        if isinstance(svr, KISConfig):
            self.config = svr
            svr = 'prod'
        else:
            self.config = None
        self.verbose = verbose
        self.token: Optional[dict] = None
        self.last_api_call_time = time.monotonic()
        self.last_request_time = 0.0
        self.min_interval = 0.05  # 50ms
        self.lock = threading.Lock()

        try:
            if self.config is None:
                # config가 없으면 환경 변수로 토큰 발급
                token_data = auth(svr=svr)
                self.token = token_data['access_token'] if token_data else None
                self.base_url = os.getenv('KIS_BASE_URL', 'https://openapi.koreainvestment.com:9443')
            else:
                # config가 있으면 config로 토큰 발급
                token_data = auth(config=self.config, svr=svr)
                self.token = token_data['access_token'] if token_data else None
                self.base_url = self.config.BASE_URL
        except Exception as e:
            logger.error(f"인증 실패: {e}", exc_info=True)
            raise

    def _enforce_rate_limit(self) -> None:
        """API 요청 제한을 관리합니다."""
        with _shared_rate_limit_lock:
            now = time.monotonic()
            elapsed = now - _last_api_call_time[0]
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            _last_api_call_time[0] = time.monotonic()
            self.last_request_time = _last_api_call_time[0]

    def _get_base_headers(self, tr_id: str) -> Dict[str, str]:
        """
        기본 HTTP 헤더를 생성합니다.

        Args:
            tr_id (str): API 트랜잭션 ID

        Returns:
            Dict[str, str]: HTTP 헤더
        """
        return {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.token}",
            "appKey": getTREnv().my_app,
            "appSecret": getTREnv().my_sec,
            "tr_id": tr_id,
            "custtype": "P",
        }

    def make_request(
        self,
        endpoint: str,
        tr_id: str,
        params: Dict[str, Any],
        method: str = 'GET',
        retries: int = 5,
        headers: Dict[str, str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        API 요청을 보내고 응답을 처리합니다.

        Args:
            endpoint (str): API 엔드포인트 URL
            tr_id (str): API 트랜잭션 ID
            params (Dict[str, Any]): API 요청 파라미터
            method (str): HTTP 메서드 (기본값: 'GET')
            retries (int): 재시도 횟수 (기본값: 5)
            headers (Dict[str, str], optional): 추가 HTTP 헤더

        Returns:
            Optional[Dict[str, Any]]: API 응답 데이터

        Raises:
            Exception: API 요청 실패 시 발생
        """
        url = f"{self.base_url}{endpoint}"
        
        # getTREnv()를 사용하여 올바른 헤더 설정
        env = getTREnv()
        headers = headers or {}
        headers["authorization"] = env.my_token
        headers["content-type"] = "application/json"
        headers["appkey"] = env.my_app
        headers["appsecret"] = env.my_sec
        headers["tr_id"] = tr_id
        
        if self.verbose:
            logger.debug(f"요청 URL: {url}")
            logger.debug(f"요청 헤더: {headers}")
            logger.debug(f"요청 파라미터: {params}")
        
        last_exception = None

        for attempt in range(retries):
            self._enforce_rate_limit()
            response = None
            data = None
            try:
                if self.verbose:
                    logger.info(f"[API] ({method}) {tr_id} 시도 {attempt+1}/{retries}")

                response = requests.request(
                    method.upper(),
                    url,
                    headers=headers,
                    params=params if method.upper() == 'GET' else None,
                    json=params if method.upper() != 'GET' else None,
                    timeout=15,
                )

                try:
                    data = response.json()
                except json.JSONDecodeError:
                    logger.error(f"[{tr_id}] JSON 디코드 실패 (시도 {attempt+1}/{retries}): {response.text}")
                    return {
                        'rt_cd': 'JSON_DECODE_ERROR',
                        'msg1': 'JSON 디코드 실패',
                        'raw_text': response.text,
                        'status_code': response.status_code,
                        'error_type': 'JSONDecodeError',
                    }

                rt_cd = data.get('rt_cd')
                if rt_cd is None:
                    logger.error(f"[{tr_id}] rt_cd 값이 없음: {data}")
                    return {
                        'rt_cd': 'NO_RT_CD',
                        'msg1': '응답에 rt_cd 값이 없음',
                        'raw_data': data,
                        'status_code': response.status_code,
                        'error_type': 'NoRtCd',
                    }

                if response.status_code == 200 and rt_cd == '0':
                    if self.verbose and tr_id != "TTTC8434R":
                        logger.info(f"[API] 응답: {data}")
                    return data
                else:
                    if response.status_code == 200 and rt_cd != '0':
                        api_msg = data.get('msg1', '')
                        api_code = data.get('rt_cd')
                        logger.warning(f"[{tr_id}] API 오류 응답 (시도 {attempt+1}/{retries}): {api_msg} (code: {api_code})")
                        is_rate_limit_error = (
                            isinstance(api_code, str)
                            and api_code == '1'
                            and isinstance(api_msg, str)
                            and "초당 거래건수를 초과하였습니다" in api_msg
                        )
                        if is_rate_limit_error:
                            if attempt < retries - 1:
                                logger.warning(f"[{tr_id}] API 유량 제한 감지 (code: {api_code}). 1초(+증가분) 대기 후 재시도... ({attempt+1}/{retries})")
                                time.sleep(1)
                                time.sleep(0.1 * attempt)
                            else:
                                logger.error(f"[{tr_id}] API 유량 제한 최종 실패 (재시도 소진).")
                                return data
                        else:
                            return {
                                'rt_cd': api_code,
                                'msg1': api_msg,
                                'raw_data': data,
                                'status_code': response.status_code,
                                'error_type': 'ApiError',
                            }
                    elif response.status_code != 200:
                        http_error_msg = data.get('msg1', response.text) if data and isinstance(data, dict) else response.text
                        http_error_code_from_json = data.get('rt_cd') if data and isinstance(data, dict) else None
                        final_http_error_code = (
                            http_error_code_from_json if http_error_code_from_json else str(response.status_code)
                        )
                        log_entry = f"[{tr_id}] HTTP 오류 응답 (시도 {attempt+1}/{retries}): Status {response.status_code}, Message: {http_error_msg}"
                        if http_error_code_from_json:
                            log_entry += f" (API Code in JSON: {http_error_code_from_json})"
                        logger.warning(log_entry)
                        if attempt < retries - 1:
                            time.sleep(0.5 * (attempt + 1))
                            continue
                        else:
                            logger.error(f"[{tr_id}] HTTP 오류 최종 실패 (재시도 소진).")
                            return data if data else {
                                'rt_cd': str(response.status_code),
                                'msg1': response.text,
                                'error_type': 'HTTPErrorFinal',
                            }
                    else:
                        logger.error(f"[{tr_id}] 로직 오류: 예상치 못한 HTTP/API 상태 (시도 {attempt+1}/{retries}). 응답: {data}. HTTP Status: {response.status_code if response else 'N/A'}")
                        return data
            except requests.exceptions.RequestException as e:
                logger.error(f"[{tr_id}] 요청 실패 (시도 {attempt+1}/{retries}): {e}")
                last_exception = e
                if attempt < retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    logger.error(f"[{tr_id}] 요청 최종 실패 (재시도 소진): {last_exception}")
                    raise last_exception

        logger.error(f"[{tr_id}] 최종 실패 후 루프 외부 도달: {last_exception if last_exception else '알 수 없는 오류'}")
        if last_exception:
            raise last_exception
        raise Exception('Unknown error after retries')

    def refresh_token(self) -> None:
        """
        API 토큰을 갱신합니다.

        Raises:
            Exception: 토큰 갱신 실패 시 발생
        """
        try:
            response = requests.post(
                f"{self.base_url}/oauth2/tokenP",
                json={
                    "grant_type": "client_credentials",
                    "appkey": self.config.APP_KEY,
                    "appsecret": self.config.APP_SECRET
                },
                headers={"content-type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                if not self.token:
                    raise Exception("토큰 갱신 실패: access_token이 없습니다.")
            else:
                raise Exception(f"토큰 갱신 실패: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"토큰 갱신 실패: {e}")
            raise

__all__ = ['KISClient', 'API_ENDPOINTS']
