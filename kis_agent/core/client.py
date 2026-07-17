import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
import requests

from .auth import (
    _issue_token_async,
    apply_token_env,
    auth,
    auth_async,
    getTREnv,
    read_token,
)
from .config import KISConfig
from .constants import MOCK_BASE_URL, REAL_BASE_URL, resolve_environment  # noqa: F401
from .endpoints import API_ENDPOINTS
from .rate_limiter import RateLimiter, get_global_rate_limiter
from .tr_mapping import PaperTradingNotSupportedError, resolve_tr_id  # noqa: F401

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 글로벌 rate limit 변수들 제거됨 - 인스턴스별 관리로 변경


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
        >>> response = client.make_request('/uapi/domestic-stock/v1/quotations/inquire-price', 'FHKST01010100', {'FID_COND_MRKT_DIV_CODE': 'UN', 'FID_INPUT_ISCD': '005930'})
    """

    def __init__(
        self,
        svr: str = "prod",
        config=None,
        verbose: bool = False,
        enable_rate_limiter: bool = True,
        rate_limiter: Optional[RateLimiter] = None,
        _defer_token: bool = False,
    ):
        """
        KISClient를 초기화합니다.

        Args:
            svr (str): 서버 환경 ('prod' 또는 'dev')
            config (KISConfig, optional): API 설정 정보
            verbose (bool): 상세 로깅 여부
            enable_rate_limiter (bool): Rate Limiter 사용 여부
            rate_limiter (RateLimiter, optional): 커스텀 Rate Limiter 인스턴스
            _defer_token (bool): 내부용. True면 생성자에서 토큰을 발급하지 않는다.
                `create_async()`가 동기 인증(블로킹 네트워크 호출)을 건너뛰고
                직접 await하기 위해 사용한다. 직접 쓰지 말 것 — 토큰 없는
                클라이언트가 만들어진다.

        Raises:
            Exception: 인증 실패 시 발생
        """
        if isinstance(svr, KISConfig):
            self.config = svr
            svr = "prod"
        else:
            self.config = config

        # config가 명시되지 않았으면 환경변수에서 자동 채움.
        # KIS_* 환경변수가 충분치 않으면 None으로 둬서 기존 backward 경로(auth())가
        # 자체적으로 처리하도록 둔다.
        if self.config is None:
            try:
                self.config = KISConfig.from_env()
            except ValueError:
                self.config = None
        self.verbose = verbose
        self.token: Optional[str] = None
        self.token_expired: Optional[str] = None  # 토큰 만료 시간 저장
        self.svr = svr  # 서버 환경 저장
        self.last_api_call_time = time.monotonic()
        self.last_request_time = 0.0
        self.min_interval = 0.05  # 50ms
        self.rate_limit_lock = threading.Lock()  # 인스턴스별 rate limit lock
        self.token_refresh_lock = threading.Lock()  # 토큰 재생성 동기화용 락

        # Rate Limiter 설정 — 기본값은 kis_agent.core.rate_limiter의 DEFAULT_*
        # (공식 스펙 20 RPS / 1000 RPM 대비 75% / 80% 안전 마진).
        # 전역 싱글턴 사용: 모든 KISClient/Agent가 동일한 Rate Limiter 공유.
        # 명시적으로 전달된 rate_limiter가 있으면 그것을 사용 (테스트 등 특수 목적).
        self.enable_rate_limiter = enable_rate_limiter
        if enable_rate_limiter:
            self.rate_limiter = rate_limiter or get_global_rate_limiter()
        else:
            self.rate_limiter = None

        # base_url/is_real을 토큰 발급 *전에* 확정한다. is_real은 TR_ID 변환의
        # 근거이므로 _initialize_token의 부수효과에 의존해선 안 된다.
        if self.config and self.config.BASE_URL:
            self.base_url = self.config.BASE_URL
        else:
            # config가 없는 경로도 KIS_PAPER를 존중해야 한다 (Agent/CLI와 동일 헬퍼).
            self.base_url, _ = resolve_environment()
        self.is_real = MOCK_BASE_URL not in self.base_url

        # 초기 토큰 발급 또는 기존 토큰 재사용 (내부에서 base_url을 다시 확정한다).
        # create_async()는 여기서 동기 네트워크 호출이 일어나면 이벤트 루프가
        # 막히므로 건너뛰고 직접 await한다.
        if not _defer_token:
            self._initialize_token()

        # 토큰 발급 과정에서 base_url이 바뀌었을 수 있으므로 is_real을 재계산.
        self.is_real = MOCK_BASE_URL not in getattr(self, "base_url", "")

    @classmethod
    async def create_async(
        cls,
        svr: str = "prod",
        config=None,
        verbose: bool = False,
        enable_rate_limiter: bool = True,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> "KISClient":
        """Create a client, issuing the token without blocking the event loop.

        `KISClient(...)`는 생성자에서 동기 HTTP로 토큰을 발급하므로 asyncio
        애플리케이션에서는 이벤트 루프를 막는다. 이 팩토리는 같은 초기화를
        하되 토큰만 `auth_async()`로 await한다.

        Args:
            svr: 'prod'(실전) 또는 'vps'(모의).
            config: `KISConfig` 인스턴스.
            verbose: 상세 로깅 여부.
            enable_rate_limiter: Rate Limiter 사용 여부.
            rate_limiter: 커스텀 Rate Limiter.

        Returns:
            토큰이 설정된 `KISClient`.

        Raises:
            ImportError: aiohttp 미설치.
            RuntimeError: 토큰 발급 실패.

        Example:
            >>> client = await KISClient.create_async(config=config)
        """
        client = cls(
            svr=svr,
            config=config,
            verbose=verbose,
            enable_rate_limiter=enable_rate_limiter,
            rate_limiter=rate_limiter,
            _defer_token=True,
        )

        token_data = await auth_async(config=config, svr=svr)
        if token_data:
            client.token = token_data.get("access_token")
            client.token_expired = token_data.get("access_token_token_expired")
            # 동기 경로는 auth()가 헤더/TR 환경까지 세팅한다. 비동기 경로도
            # 맞춰줘야 make_request()의 getTREnv()가 이 토큰을 본다.
            # auth()를 다시 부르면 동기 HTTP가 또 나가므로 마무리 단계만 재사용.
            apply_token_env(client.token, svr=svr, config=config)
        return client

    async def refresh_token_async(self) -> None:
        """Force-issue a new token asynchronously and apply it to this client.

        캐시를 건너뛰고 새로 발급한다 — 갱신을 요청했다는 건 기존 토큰을
        믿지 못한다는 뜻이므로 캐시를 재사용하면 의미가 없다.

        Raises:
            ImportError: aiohttp 미설치.
            RuntimeError: 토큰 발급 실패.
        """
        token_data = await _issue_token_async(config=self.config, svr=self.svr)
        if token_data:
            self.token = token_data.get("access_token")
            self.token_expired = token_data.get("access_token_token_expired")
            logger.info(f"토큰 갱신 완료 (async, 만료: {self.token_expired})")

    def _initialize_token(self) -> None:
        """초기 토큰 발급 또는 기존 토큰 재사용 (Thread-Safe)"""
        with self.token_refresh_lock:
            try:
                # 토큰이 이미 유효한 경우 재발급하지 않음 (중복 방지)
                if self.token and self.token_expired:
                    try:
                        exp_dt = (
                            datetime.strptime(self.token_expired, "%Y-%m-%d %H:%M:%S")
                            if isinstance(self.token_expired, str)
                            else self.token_expired
                        )
                        now_dt = datetime.now()
                        # 5분 이상 남았으면 재발급하지 않음
                        if exp_dt > now_dt + timedelta(minutes=5):
                            logger.debug("토큰이 아직 유효합니다. 재발급하지 않습니다.")
                            return
                    except Exception as e:
                        logger.warning(f"토큰 만료 시간 파싱 실패, 재발급 진행: {e}")

                # 캐시된 토큰 먼저 확인 (네트워크 호출 없이)
                app_key = (
                    self.config.APP_KEY if self.config else os.getenv("KIS_APP_KEY", "")
                )
                cached = read_token(app_key=app_key) if app_key else None

                if cached:
                    self.token = cached.get("access_token")
                    self.token_expired = cached.get("access_token_token_expired")
                    logger.info(f"캐시된 토큰 사용 (만료: {self.token_expired})")
                    # auth() 호출하여 헤더 설정 (토큰 재발급 없이 기존 토큰 로드)
                    if self.config is None:
                        auth(svr=self.svr)
                        self.base_url, _ = resolve_environment()
                    else:
                        auth(config=self.config, svr=self.svr)
                        self.base_url = self.config.BASE_URL
                else:
                    logger.info("토큰 발급을 시작합니다...")
                    if self.config is None:
                        token_data = auth(svr=self.svr)
                        if token_data:
                            self.token = token_data.get("access_token")
                            self.token_expired = token_data.get(
                                "access_token_token_expired"
                            )
                            logger.info(f"토큰 발급 완료 (만료: {self.token_expired})")
                        self.base_url, _ = resolve_environment()
                    else:
                        token_data = auth(config=self.config, svr=self.svr)
                        if token_data:
                            self.token = token_data.get("access_token")
                            self.token_expired = token_data.get(
                                "access_token_token_expired"
                            )
                            logger.info(f"토큰 발급 완료 (만료: {self.token_expired})")
                        self.base_url = self.config.BASE_URL
            except Exception as e:
                logger.error(f"인증 실패: {e}", exc_info=True)
                raise

    def _check_and_refresh_token(self) -> None:
        """토큰 만료 체크 및 자동 갱신"""
        if self.token_expired:
            try:
                # 토큰 만료 시간 파싱
                exp_dt = (
                    datetime.strptime(self.token_expired, "%Y-%m-%d %H:%M:%S")
                    if isinstance(self.token_expired, str)
                    else self.token_expired
                )

                # 현재 시간
                now_dt = datetime.now()

                # 토큰이 만료되었거나 5분 이내 만료 예정이면 갱신
                if exp_dt <= now_dt + timedelta(minutes=5):
                    # logger.info("토큰이 만료되었거나 곧 만료됩니다. 자동 갱신을 시작합니다.")
                    self._initialize_token()
            except Exception as e:
                logger.warning(f"토큰 만료 체크 중 오류 발생, 토큰 재발급 시도: {e}")
                self._initialize_token()

    def _enforce_rate_limit(self, priority: int = 0) -> None:
        """
        API 요청 제한을 관리합니다 (인스턴스별).

        Args:
            priority: 요청 우선순위 (0=일반, 1=중요, 2=긴급)
        """
        if self.enable_rate_limiter and self.rate_limiter:
            # 새로운 Rate Limiter 사용
            wait_time = self.rate_limiter.acquire(priority)
            if wait_time > 0 and self.verbose:
                logger.debug(f"Rate limiter 대기: {wait_time:.3f}초")
        else:
            # 기존 방식 유지 (하위 호환성)
            with self.rate_limit_lock:
                now = time.monotonic()
                elapsed = now - self.last_api_call_time
                if elapsed < self.min_interval:
                    time.sleep(self.min_interval - elapsed)
                self.last_api_call_time = time.monotonic()
                self.last_request_time = self.last_api_call_time

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
        method: str = "GET",
        retries: int = 2,  # [변경 이유] 테스트 속도 향상을 위해 재시도 횟수를 5회 → 2회로 단축
        headers: Dict[str, str] = None,
        priority: int = 0,  # 요청 우선순위 (0=일반, 1=중요, 2=긴급)
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
            PaperTradingNotSupportedError: 모의투자 환경에서 모의투자를 지원하지
                않는 API를 호출한 경우.
            Exception: API 요청 실패 시 발생
        """
        # 요청 전 토큰 만료 체크 및 자동 갱신
        self._check_and_refresh_token()

        # 모의투자면 TR_ID를 모의투자용으로 변환한다. 호출부가 실전 TR_ID를
        # 하드코딩해도 여기서 일괄 처리되도록 이 지점을 단일 관문으로 둔다.
        tr_id = resolve_tr_id(tr_id, self.is_real)

        url = f"{self.base_url}{endpoint}"

        # getTREnv()를 사용하여 올바른 헤더 설정
        env = getTREnv()
        headers = headers or {}
        headers["authorization"] = env.my_token
        headers["content-type"] = "application/json"
        headers["appkey"] = env.my_app
        headers["appsecret"] = env.my_sec
        headers["tr_id"] = tr_id
        headers["custtype"] = "P"  # 개인 고객 (필수: 주문 API에서 요구됨)

        if self.verbose:
            logger.debug(f"요청 URL: {url}")
            logger.debug(f"요청 헤더: {headers}")
            logger.debug(f"요청 파라미터: {params}")

        last_exception = None

        for attempt in range(retries):
            self._enforce_rate_limit(priority)
            response = None
            data = None
            try:
                if self.verbose:
                    logger.info(f"[API] ({method}) {tr_id} 시도 {attempt+1}/{retries}")

                response = httpx.request(
                    method.upper(),
                    url,
                    headers=headers,
                    params=params if method.upper() == "GET" else None,
                    json=params if method.upper() != "GET" else None,
                    timeout=15,
                )

                try:
                    data = response.json()
                except json.JSONDecodeError:
                    logger.error(
                        f"[{tr_id}] JSON 디코드 실패 (시도 {attempt+1}/{retries})"
                    )
                    logger.error(
                        f"[{tr_id}] 원시 응답 텍스트: {response.text[:500]}..."
                    )
                    logger.error(f"[{tr_id}] 응답 상태 코드: {response.status_code}")
                    logger.error(f"[{tr_id}] 응답 헤더: {dict(response.headers)}")
                    return {
                        "rt_cd": "JSON_DECODE_ERROR",
                        "msg1": "JSON 디코드 실패",
                        "raw_text": response.text,
                        "status_code": response.status_code,
                        "error_type": "JSONDecodeError",
                    }

                rt_cd = data.get("rt_cd")
                if rt_cd is None:
                    logger.error(f"[{tr_id}] rt_cd 값이 없음: {data}")
                    return {
                        "rt_cd": "NO_RT_CD",
                        "msg1": "응답에 rt_cd 값이 없음",
                        "raw_data": data,
                        "status_code": response.status_code,
                        "error_type": "NoRtCd",
                    }

                if response.status_code == 200 and rt_cd == "0":
                    if self.verbose and tr_id != "TTTC8434R":
                        logger.info(f"[API] 응답: {data}")
                    # 성공 시 Rate Limiter에 보고
                    if self.enable_rate_limiter and self.rate_limiter:
                        self.rate_limiter.report_success()
                    return data
                else:
                    if response.status_code == 200 and rt_cd != "0":
                        api_msg = data.get("msg1", "")
                        api_code = data.get("rt_cd")
                        logger.warning(
                            f"[{tr_id}] API 오류 응답 (시도 {attempt+1}/{retries}): {api_msg} (code: {api_code})"
                        )

                        # 유량 제한 에러 체크
                        # 토큰 만료 에러 체크
                        is_token_expired = (
                            isinstance(api_code, str)
                            and api_code
                            in ["EGW00123", "EGW00124"]  # 토큰 만료 에러 코드
                        ) or (
                            isinstance(api_msg, str)
                            and ("토큰" in api_msg and "만료" in api_msg)
                        )

                        if is_token_expired:
                            logger.warning(f"[{tr_id}] 토큰 만료 감지. 재발급 시도...")
                            self._initialize_token()
                            # 헤더 업데이트
                            env = getTREnv()
                            headers["authorization"] = env.my_token
                            if attempt < retries - 1:
                                continue  # 토큰 갱신 후 재시도

                        is_rate_limit_error = (
                            isinstance(api_code, str)
                            and (
                                api_code == "1"
                                or api_code in ["EGW00201", "EGW00202", "EGW00203"]
                            )
                            and isinstance(api_msg, str)
                            and (
                                "초당 거래건수를 초과" in api_msg
                                or "유량 제한" in api_msg
                            )
                        )

                        if is_rate_limit_error:
                            # Rate Limiter에 에러 보고
                            if self.enable_rate_limiter and self.rate_limiter:
                                self.rate_limiter.report_error(api_code)

                            if attempt < retries - 1:
                                logger.warning(
                                    f"[{tr_id}] API 유량 제한 감지 (code: {api_code}). 0.5초 대기 후 재시도... ({attempt+1}/{retries})"
                                )
                                time.sleep(
                                    0.5
                                )  # [변경 이유] 테스트 속도 향상을 위해 대기 시간을 1초 → 0.5초로 단축
                            else:
                                logger.error(
                                    f"[{tr_id}] API 유량 제한 최종 실패 (재시도 소진)."
                                )
                                return data
                        else:
                            return {
                                "rt_cd": api_code,
                                "msg1": api_msg,
                                "raw_data": data,
                                "status_code": response.status_code,
                                "error_type": "ApiError",
                            }
                    elif response.status_code != 200:
                        http_error_msg = (
                            data.get("msg1", response.text)
                            if data and isinstance(data, dict)
                            else response.text
                        )
                        http_error_code_from_json = (
                            data.get("rt_cd")
                            if data and isinstance(data, dict)
                            else None
                        )
                        log_entry = f"[{tr_id}] HTTP 오류 응답 (시도 {attempt+1}/{retries}): Status {response.status_code}, Message: {http_error_msg}"
                        if http_error_code_from_json:
                            log_entry += (
                                f" (API Code in JSON: {http_error_code_from_json})"
                            )
                        logger.warning(log_entry)
                        if attempt < retries - 1:
                            time.sleep(
                                0.2
                            )  # [변경 이유] 테스트 속도 향상을 위해 HTTP 오류 시 대기 시간을 단축
                            continue
                        else:
                            logger.error(
                                f"[{tr_id}] HTTP 오류 최종 실패 (재시도 소진)."
                            )
                            return (
                                data
                                if data
                                else {
                                    "rt_cd": str(response.status_code),
                                    "msg1": response.text,
                                    "error_type": "HTTPErrorFinal",
                                }
                            )
                    else:
                        logger.error(
                            f"[{tr_id}] 로직 오류: 예상치 못한 HTTP/API 상태 (시도 {attempt+1}/{retries}). 응답: {data}. HTTP Status: {response.status_code if response else 'N/A'}"
                        )
                        return data
            except (httpx.RequestError, requests.exceptions.RequestException) as e:
                logger.error(f"[{tr_id}] 요청 실패 (시도 {attempt+1}/{retries}): {e}")
                last_exception = e
                if attempt < retries - 1:
                    time.sleep(
                        0.2
                    )  # [변경 이유] 테스트 속도 향상을 위해 요청 실패 시 대기 시간을 단축
                    continue
                else:
                    logger.error(
                        f"[{tr_id}] 요청 최종 실패 (재시도 소진): {last_exception}"
                    )
                    raise last_exception

        logger.error(
            f"[{tr_id}] 최종 실패 후 루프 외부 도달: {last_exception if last_exception else '알 수 없는 오류'}"
        )
        if last_exception:
            raise last_exception
        raise Exception("Unknown error after retries")

    def refresh_token(self) -> None:
        """
        API 토큰을 갱신합니다. (Thread-Safe)

        Raises:
            Exception: 토큰 갱신 실패 시 발생
        """
        with self.token_refresh_lock:
            try:
                logger.info("토큰 갱신을 시작합니다...")
                response = requests.post(
                    f"{self.base_url}/oauth2/tokenP",
                    json={
                        "grant_type": "client_credentials",
                        "appkey": self.config.APP_KEY,
                        "appsecret": self.config.APP_SECRET,
                    },
                    headers={"content-type": "application/json"},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")
                    self.token_expired = data.get("access_token_token_expired")

                    if not self.token:
                        raise Exception("토큰 갱신 실패: access_token이 없습니다.")

                    logger.info(f"토큰 갱신 완료 (만료: {self.token_expired})")
                else:
                    raise Exception(f"토큰 갱신 실패: HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"토큰 갱신 실패: {e}")
                raise

    def get_kospi200_index(
        self, futures_month: str = "202409"
    ) -> Optional[Dict[str, Any]]:
        """
        KOSPI200 지수 조회

        Args:
            futures_month (str): 선물 만료월 (YYYYMM 형식)

        Returns:
            Dict[str, Any]: KOSPI200 지수 정보
        """
        endpoint = API_ENDPOINTS["INQUIRE_INDEX_PRICE"]
        params = {
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": f"101{futures_month[-2:]}000",
        }
        return self.make_request(endpoint, "FHMIF10100000", params)

    def get_ws_approval_key(self) -> Optional[str]:
        """
        웹소켓 접속을 위한 승인키를 가져옵니다.

        Returns:
            str: 웹소켓 승인키
        """
        url = f"{self.base_url}/oauth2/Approval"

        payload = {
            "grant_type": "client_credentials",
            "appkey": (
                self.config.app_key if self.config else os.getenv("KIS_APP_KEY", "")
            ),
            "secretkey": (
                self.config.app_secret
                if self.config
                else os.getenv("KIS_APP_SECRET", "")
            ),
        }

        headers = {"content-type": "application/json"}

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                approval_key = response.json().get("approval_key")
                if not approval_key:
                    logger.error("응답에서 approval_key를 추출하지 못했습니다.")
                    return None
                logger.info(f"웹소켓 승인키 발급 완료: {approval_key[:10]}...")
                return approval_key
            else:
                logger.error(
                    f"웹소켓 승인키 요청 실패: {response.status_code} - {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"웹소켓 승인키 요청 중 오류 발생: {e}")
            return None


__all__ = ["KISClient", "API_ENDPOINTS"]
