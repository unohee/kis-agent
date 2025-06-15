import json
import logging
import threading
import time
from typing import Dict, Any, Optional

import requests

from kis.core.auth import auth, read_token, getTREnv
from kis.core.config import KISConfig

logging.basicConfig(level=logging.INFO)

API_ENDPOINTS = {
    'STOCK_PRICE': '/uapi/domestic-stock/v1/quotations/inquire-price',
    'STOCK_DAILY': '/uapi/domestic-stock/v1/quotations/inquire-daily-price',
    'STOCK_MINUTE': '/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice',
    'STOCK_MEMBER': '/uapi/domestic-stock/v1/quotations/inquire-member',
    'STOCK_INVESTOR': '/uapi/domestic-stock/v1/quotations/inquire-investor',  # 투자자별 매매 동향 조회
    'PBAR_TRATIO': '/uapi/domestic-stock/v1/quotations/inquire-price-by-time',
    'ORDERBOOK': '/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn',
    'ACCOUNT_BALANCE': '/uapi/domestic-stock/v1/trading/inquire-balance',
    'POSSIBLE_ORDER': '/uapi/domestic-stock/v1/trading/inquire-psbl-order',
    'ORDER_CASH': '/uapi/domestic-stock/v1/trading/order-cash',
    'OVERTIME': '/uapi/domestic-stock/v1/quotations/inquire-daily-overtimeprice',
    'CCNL': '/uapi/domestic-stock/v1/quotations/inquire-ccnl',
    'VOLUME_POWER': '/uapi/domestic-stock/v1/quotations/volume-rank',
    'MARKET_FLUCTUATION': '/uapi/domestic-stock/v1/quotations/inquire-market-index',
    'MARKET_RANKINGS': '/uapi/domestic-stock/v1/quotations/volume-rank',
    'STOCK_INFO': '/uapi/domestic-stock/v1/quotations/search-stock-info',
    'MEMBER_TRANSACTION': '/uapi/domestic-stock/v1/quotations/inquire-member-daily',
    'HOLIDAY_CHECK': '/uapi/domestic-stock/v1/quotations/chk-holiday',
    'CONDITIONED_STOCK': '/uapi/domestic-stock/v1/quotations/psearch-result',  # 조건검색 결과 조회 엔드포인트 수정
}

_shared_rate_limit_lock = threading.Lock()
_last_api_call_time = [0]

class KISClient:
    def __init__(self, svr: str = 'prod', verbose: bool = False):
        """클라이언트를 초기화합니다."""
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
                # 환경 변수 기반 초기화 시 토큰 갱신
                self.refresh_token(svr=svr)
                self.base_url = getTREnv().my_url
            else:
                # 외부에서 전달된 설정 사용 시 즉시 도메인 설정
                self.base_url = self.config.BASE_URL
        except Exception as e:
            logging.error(f"[KISClient] 인증 실패: {e}", exc_info=True)
            raise

    def refresh_token(self, svr: str = 'prod', config=None) -> None:
        """토큰을 갱신하고 반환값을 저장합니다."""
        token_data = auth(config, svr)
        if token_data:
            self.token = token_data
        else:
            self.token = read_token()

    def _enforce_rate_limit(self) -> None:
        with _shared_rate_limit_lock:
            now = time.monotonic()
            elapsed = now - _last_api_call_time[0]
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            _last_api_call_time[0] = time.monotonic()
            self.last_request_time = _last_api_call_time[0]

    def _get_base_headers(self, tr_id: str) -> Dict[str, str]:
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
    ) -> Optional[Dict[str, Any]]:
        """API 요청을 보내고 응답을 처리합니다.
        
        Args:
            endpoint: API 엔드포인트 URL
            tr_id: API 트랜잭션 ID
            params: API 요청 파라미터
            method: HTTP 메서드 (기본값: 'GET')
            retries: 재시도 횟수 (기본값: 5)
            
        Returns:
            Optional[Dict[str, Any]]: API 응답 데이터
        """
        url = f"{self.base_url}{endpoint}"
        
        # 필수 헤더 설정
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.token}",
            "appKey": getTREnv().my_app,
            "appSecret": getTREnv().my_sec,
            "tr_id": tr_id,
            "custtype": "P"
        }
        
        last_exception = None

        for attempt in range(retries):
            self._enforce_rate_limit()
            response = None
            data = None
            try:
                if self.verbose:
                    logging.info(f"[API] ({method}) {tr_id} Attempt {attempt+1}/{retries}")

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
                    logging.error(
                        f"[{tr_id}] JSON 디코드 실패 (시도 {attempt+1}/{retries}): {response.text}"
                    )
                    return {
                        'rt_cd': 'JSON_DECODE_ERROR',
                        'msg1': 'JSON 디코드 실패',
                        'raw_text': response.text,
                        'status_code': response.status_code,
                        'error_type': 'JSONDecodeError',
                    }

                rt_cd = data.get('rt_cd')
                if rt_cd is None:
                    logging.error(f"[{tr_id}] rt_cd 값이 없음: {data}")
                    return {
                        'rt_cd': 'NO_RT_CD',
                        'msg1': '응답에 rt_cd 값이 없음',
                        'raw_data': data,
                        'status_code': response.status_code,
                        'error_type': 'NoRtCd',
                        }

                if response.status_code == 200 and rt_cd == '0':
                    if self.verbose and tr_id != "TTTC8434R":
                        logging.info(f"[API] Response: {data}")
                    return data
                else:
                    if response.status_code == 200 and rt_cd != '0':
                        api_msg = data.get('msg1', '')
                        api_code = data.get('rt_cd')
                        logging.warning(
                            f"[{tr_id}] API 오류 응답 (시도 {attempt+1}/{retries}): {api_msg} (code: {api_code})"
                        )
                        is_rate_limit_error = (
                            isinstance(api_code, str)
                            and api_code == '1'
                            and isinstance(api_msg, str)
                            and "초당 거래건수를 초과하였습니다" in api_msg
                        )
                        if is_rate_limit_error:
                            if attempt < retries - 1:
                                logging.warning(
                                    f"[{tr_id}] API 유량 제한 감지 (code: {api_code}). 1초(+증가분) 대기 후 재시도... ({attempt+1}/{retries})"
                                )
                                time.sleep(1)
                                time.sleep(0.1 * attempt)
                                continue
                            else:
                                logging.error(f"[{tr_id}] API 유량 제한 최종 실패 (재시도 소진).")
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
                        log_entry = (
                            f"[{tr_id}] HTTP 오류 응답 (시도 {attempt+1}/{retries}): Status {response.status_code}, Message: {http_error_msg}"
                        )
                        if http_error_code_from_json:
                            log_entry += f" (API Code in JSON: {http_error_code_from_json})"
                        logging.warning(log_entry)
                        if attempt < retries - 1:
                            time.sleep(0.5 * (attempt + 1))
                            continue
                        else:
                            logging.error(f"[{tr_id}] HTTP 오류 최종 실패 (재시도 소진).")
                            return (
                                data
                                if data and isinstance(data, dict)
                                else {
                                    'rt_cd': str(response.status_code),
                                    'msg1': response.text,
                                    'error_type': 'HTTPErrorFinal',
                                }
                            )
                    else:
                        logging.error(
                            f"[{tr_id}] 로직 오류: 예상치 못한 HTTP/API 상태 (시도 {attempt+1}/{retries}). 응답: {data}. HTTP Status: {response.status_code if response else 'N/A'}"
                        )
                        return data
            except requests.exceptions.RequestException as e:
                logging.error(f"[{tr_id}] 요청 실패 (시도 {attempt+1}/{retries}): {e}")
                last_exception = e
                if attempt < retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    logging.error(f"[{tr_id}] 요청 최종 실패 (재시도 소진): {last_exception}")
                    raise last_exception
        logging.error(
            f"[{tr_id}] 최종 실패 후 루프 외부 도달: {last_exception if last_exception else '알 수 없는 오류'}"
        )
        if last_exception:
            raise last_exception
        raise Exception('Unknown error after retries')

__all__ = ['KISClient', 'API_ENDPOINTS']
