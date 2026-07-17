"""
Created on Wed Feb 15 16:57:19 2023

@author: Administrator
"""

# ====|  토큰 발급에 필요한 API 호출 샘플 아래 참고하시기 바랍니다.  |=====================
# ====|  토큰 발급에 필요한 API 호출 샘플 아래 참고하시기 바랍니다.  |=====================
# ====|  토큰 발급에 필요한 API 호출 샘플 아래 참고하시기 바랍니다.  |=====================
# ====|  API 호출 공통 함수 포함                                  |=====================

import copy
import json
import logging
import os

# [변경 이유] 린트 정리: 사용하지 않는 import 제거, lambda(E731) 제거
from collections import namedtuple
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from .constants import KIS_USER_AGENT_DEFAULT, MOCK_BASE_URL, REAL_BASE_URL

# 모듈 레벨 로거 설정 (기본적으로 WARNING 이상만 출력)
_logger = logging.getLogger(__name__)

# 전역 토큰 캐시 (APP_KEY별로 23시간 유지)
# 구조: {app_key_prefix: {"access_token": str, "access_token_token_expired": str, "cached_at": datetime, "expired": datetime}}
_token_cache: Dict[str, Dict[str, Any]] = {}

# .env 자동 로드: 현재 작업 디렉토리의 .env만 인식하며, 기존 환경변수는 덮어쓰지 않음.
# (이전 버전은 패키지 부모 디렉토리(../../.env)까지 검색하고 override=True로 덮어썼으나,
#  의도치 않은 환경 오염 가능성이 있어 v1.8.0에서 제거. 사용자가 임포트 위치와 무관하게
#  자기 프로젝트의 .env를 사용하려면 dotenv를 직접 호출하거나 KISConfig에 매개변수 전달.)
current_dir_env = os.path.join(os.getcwd(), ".env")
if os.path.exists(current_dir_env):
    load_dotenv(dotenv_path=current_dir_env, override=False)


def clearConsole() -> int:
    """터미널 화면을 지웁니다.

    Returns:
        int: 시스템 호출 반환 코드
    """
    # [변경 이유] E731(lambda 사용 금지) 해결을 위해 함수로 변경
    return os.system("cls" if os.name in ("nt", "dos") else "clear")


key_bytes = 32

# 토큰 저장 경로 설정 - 다른 프로젝트에서 사용할 때도 항상 pykis 패키지 내부의 credit 디렉토리 사용
# __file__의 절대 경로를 기준으로 pykis/core/credit 디렉토리 지정 (다른 프로젝트에서 import해도 안전)
config_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credit")
token_tmp = os.getenv("KIS_TOKEN_PATH", os.path.join(config_root, "KIS_Token.json"))

# 디렉토리가 없으면 생성
os.makedirs(config_root, exist_ok=True)

# 접근토큰 관리하는 파일 존재여부 체크, 없으면 생성
if not os.path.exists(token_tmp):
    # 빈 JSON 파일 생성 또는 기본 구조 생성
    with open(token_tmp, "w+", encoding="utf-8") as f:
        json.dump({}, f)  # 빈 JSON 객체로 초기화


def _get_token_path_for_app_key(app_key: str, base_path: str = token_tmp) -> str:
    """APP_KEY별로 분리된 토큰 파일 경로 반환

    Args:
        app_key: 애플리케이션 키
        base_path: 기본 토큰 파일 경로

    Returns:
        str: APP_KEY별 토큰 파일 경로
    """
    import hashlib

    if not app_key:
        return base_path

    # APP_KEY 전체의 SHA256 해시를 사용하여 충돌 방지 (앞 16자리만 사용)
    # SHA256는 동일한 입력에 대해 항상 동일한 출력을 보장하며, 충돌 가능성이 극히 낮음
    key_hash = hashlib.sha256(app_key.encode()).hexdigest()[:16]
    dir_path = os.path.dirname(base_path)
    base_name = os.path.basename(base_path).replace(".json", "")

    return os.path.join(dir_path, f"{base_name}_{key_hash}.json")


# 환경 변수 기반 설정 로드 — KIS_* prefix 전용
# (Legacy 별칭 MY_APP/MY_SEC/KIS_SECRET/MY_ACCT_STOCK/MY_PROD/PROD_URL/VPS_URL/MY_AGENT 는
#  v1.8.0에서 제거됨. 마이그레이션은 README 참조)
_cfg = {
    "my_app": os.getenv("KIS_APP_KEY", ""),
    "my_sec": os.getenv("KIS_APP_SECRET", ""),
    "my_acct_stock": os.getenv("KIS_ACCOUNT_NO", ""),
    "my_prod": os.getenv("KIS_ACCOUNT_CODE", "01"),
    "prod": os.getenv("KIS_BASE_URL", REAL_BASE_URL),
    "vps": os.getenv("KIS_VPS_URL", MOCK_BASE_URL),
    "my_agent": os.getenv("KIS_USER_AGENT", KIS_USER_AGENT_DEFAULT),
}

# 이전 설정 파일 로드 로직 제거
# Configuration file loading has been removed.
# API keys must be passed directly as parameters.

_TRENV = ()
_last_auth_time = datetime.now()
_autoReAuth = False
_DEBUG = False
_isPaper = False

# 기본 헤더값 정의
_base_headers = {"Content-Type": "application/json"}


# 토큰 발급 받아 저장 (토큰값, 토큰 유효시간,1일, 6시간 이내 발급신청시는 기존 토큰값과 동일, 발급시 알림톡 발송)
def save_token(
    my_token: str, my_expired: str, path: str = token_tmp, app_key: str = None
) -> None:
    """토큰을 APP_KEY별로 분리하여 저장 (파일 + 메모리 캐시)

    Args:
        my_token: 토큰 값
        my_expired: 토큰 만료 시간
        path: 기본 저장 경로
        app_key: APP_KEY (제공시 별도 파일로 저장)
    """
    # APP_KEY가 제공되면 해당 키 전용 파일에 저장
    if app_key:
        path = _get_token_path_for_app_key(app_key, path)

    import hashlib

    valid_date = datetime.strptime(my_expired, "%Y-%m-%d %H:%M:%S")
    token_data = {
        "token": my_token,
        # valid-date를 ISO 형식 문자열로 저장 (JSON 호환)
        "valid-date": valid_date.isoformat(),
        # APP_KEY의 SHA256 해시를 저장하여 토큰 매칭 검증에 사용 (충돌 방지)
        "app_key_hash": (
            hashlib.sha256(app_key.encode()).hexdigest()[:16] if app_key else ""
        ),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(token_data, f, ensure_ascii=False, indent=4)

    # 메모리 캐시에도 저장 (23시간 유지)
    if app_key:
        import hashlib

        # SHA256 해시를 사용하여 API 키 격리 (파일명과 동일한 해시 사용)
        key_hash = hashlib.sha256(app_key.encode()).hexdigest()[:16]
        _token_cache[key_hash] = {
            "access_token": my_token,
            "access_token_token_expired": my_expired,
            "cached_at": datetime.now(),
            "expired": valid_date,
        }
        _logger.debug(f"토큰 캐시 저장: {key_hash} (만료: {my_expired})")


# 토큰 확인 (토큰값, 토큰 유효시간_1일, 6시간 이내 발급신청시는 기존 토큰값과 동일, 발급시 알림톡 발송)
def read_token(path: str = token_tmp, app_key: str = None) -> Optional[Dict[str, Any]]:
    """APP_KEY별로 분리된 토큰 파일에서 토큰 읽기 (메모리 캐시 우선)

    Args:
        path: 기본 토큰 파일 경로
        app_key: APP_KEY (제공시 해당 키 전용 파일에서 읽기)

    Returns:
        Optional[Dict[str, Any]]: 유효한 토큰 정보 또는 None

    Note:
        메모리 캐시를 먼저 확인하여 파일 I/O를 최소화하고,
        23시간 이내 캐시된 토큰을 우선 사용합니다.
    """
    from datetime import timedelta

    try:
        # 1. 메모리 캐시 먼저 확인 (23시간 이내)
        if app_key:
            import hashlib

            # SHA256 해시를 사용하여 API 키 격리
            key_hash = hashlib.sha256(app_key.encode()).hexdigest()[:16]
            if key_hash in _token_cache:
                cached = _token_cache[key_hash]
                now = datetime.now()

                # 23시간 캐시 유효성 검증
                cache_age = now - cached["cached_at"]
                if cache_age < timedelta(hours=23):
                    # KIS 토큰 만료일 검증
                    if cached["expired"] > now:
                        _logger.debug(
                            f"메모리 캐시 사용: {key_hash} "
                            f"(캐시 나이: {cache_age.seconds}초, 만료: {cached['expired']})"
                        )
                        return {
                            "access_token": cached["access_token"],
                            "access_token_token_expired": cached[
                                "access_token_token_expired"
                            ],
                        }
                    else:
                        _logger.info(f"캐시된 토큰 만료됨: {cached['expired']}")
                        # 만료된 캐시 제거
                        del _token_cache[key_hash]
                else:
                    _logger.info(f"캐시 만료 (23시간 초과): {cache_age}")
                    # 오래된 캐시 제거
                    del _token_cache[key_hash]

        # 2. 캐시 미스 또는 만료 시 파일에서 읽기
        if app_key:
            path = _get_token_path_for_app_key(app_key, path)
            _logger.debug(f"토큰 파일 읽기: {path}")

        if not os.path.exists(path):
            _logger.debug(f"토큰 파일이 존재하지 않음: {path}")
            return None
        with open(path, encoding="utf-8") as f:
            tkg_tmp = json.load(f)

        # 테스트 호환을 위해 두 가지 포맷을 모두 처리합니다.
        if "access_token" in tkg_tmp:
            return tkg_tmp
        if not tkg_tmp or "valid-date" not in tkg_tmp or "token" not in tkg_tmp:
            return None

        # APP_KEY 일치 여부 검증 (app_key_hash가 저장되어 있는 경우)
        if app_key and "app_key_hash" in tkg_tmp:
            import hashlib

            key_hash = hashlib.sha256(app_key.encode()).hexdigest()[:16]
            if tkg_tmp["app_key_hash"] != key_hash:
                # APP_KEY가 일치하지 않으면 None 반환 (새 토큰 발급 필요)
                _logger.warning(
                    f"APP_KEY 불일치: 파일={tkg_tmp['app_key_hash']}, 요청={key_hash}"
                )
                return None
        # 레거시 호환: app_key_prefix가 있는 경우도 검증 (기존 토큰 파일 지원)
        elif app_key and "app_key_prefix" in tkg_tmp:
            key_prefix = app_key[:8] if len(app_key) >= 8 else app_key
            if tkg_tmp["app_key_prefix"] != key_prefix:
                _logger.warning(
                    f"APP_KEY 불일치 (레거시): 파일={tkg_tmp['app_key_prefix']}, 요청={key_prefix}"
                )
                return None

        # 토큰 만료 일,시간 (ISO 형식 문자열에서 datetime 객체로 파싱)
        exp_dt_str = tkg_tmp["valid-date"]
        exp_dt_obj = datetime.fromisoformat(exp_dt_str)
        exp_dt = exp_dt_obj.strftime("%Y-%m-%d %H:%M:%S")  # 비교를 위해 문자열로 변환

        # 현재일자,시간
        now_dt = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

        # 저장된 토큰 만료일자 체크 (만료일시 > 현재일시 인경우 보관 토큰 리턴)
        if exp_dt > now_dt:
            _logger.debug(f"파일에서 유효한 토큰 발견: 만료={exp_dt}")

            # 3. 파일에서 읽은 토큰도 메모리 캐시에 저장 (23시간 유지)
            if app_key:
                import hashlib

                # SHA256 해시를 사용하여 API 키 격리
                key_hash = hashlib.sha256(app_key.encode()).hexdigest()[:16]
                _token_cache[key_hash] = {
                    "access_token": tkg_tmp["token"],
                    "access_token_token_expired": exp_dt,
                    "cached_at": datetime.now(),
                    "expired": exp_dt_obj,
                }
                _logger.debug(f"파일 토큰을 메모리 캐시에 저장: {key_hash}")

            # 딕셔너리 형태로 반환하여 테스트에서 활용
            return {
                "access_token": tkg_tmp["token"],
                "access_token_token_expired": exp_dt,
            }
        else:
            return None
    except FileNotFoundError as e:
        _logger.warning(f"토큰 파일을 찾을 수 없음: {path} - {str(e)}")
        return None
    except json.JSONDecodeError as e:
        _logger.error(f"토큰 파일 JSON 파싱 실패: {path} - {str(e)}")
        return None
    except Exception as e:
        _logger.error(f"토큰 읽기 중 예상치 못한 오류: {str(e)}", exc_info=True)
        return None


# 토큰 유효시간 체크해서 만료된 토큰이면 재발급처리
def _getBaseHeader():
    if _autoReAuth:
        reAuth()
    return copy.deepcopy(_base_headers)


# 가져오기 : 앱키, 앱시크리트, 종합계좌번호(계좌번호 중 숫자8자리), 계좌상품코드(계좌번호 중 숫자2자리), 토큰, 도메인
def _setTRENV(cfg):
    nt1 = namedtuple(
        "KISEnv", ["my_app", "my_sec", "my_acct", "my_prod", "my_token", "my_url"]
    )
    d = {
        "my_app": cfg["my_app"],  # 앱키
        "my_sec": cfg["my_sec"],  # 앱시크리트
        "my_acct": cfg["my_acct"],  # 종합계좌번호(8자리)
        "my_prod": cfg["my_prod"],  # 계좌상품코드(2자리)
        "my_token": cfg["my_token"],  # 토큰
        "my_url": cfg[
            "my_url"
        ],  # 실전 도메인 (https://openapi.koreainvestment.com:9443)
    }  # 모의 도메인 (https://openapivts.koreainvestment.com:29443)

    global _TRENV
    _TRENV = nt1(**d)


def isPaperTrading() -> bool:  # 모의투자 매매
    """모의투자 여부 확인

    Returns:
        bool: 모의투자면 True, 실전투자면 False
    """
    return _isPaper


# 실전투자면 'prod', 모의투자면 'vps'를 셋팅 하시기 바랍니다.
def changeTREnv(
    token_key: str,
    svr: str = "prod",
    product: str = _cfg["my_prod"],
    config: Optional[Dict[str, Any]] = None,
) -> None:
    cfg = {}

    global _isPaper
    if svr == "prod":  # 실전투자
        ak1 = "my_app"  # 실전투자용 앱키
        ak2 = "my_sec"  # 실전투자용 앱시크리트
        _isPaper = False
    elif svr == "vps":  # 모의투자
        ak1 = "paper_app"  # 모의투자용 앱키
        ak2 = "paper_sec"  # 모의투자용 앱시크리트
        _isPaper = True

    cfg["my_app"] = _cfg.get(ak1, "")
    cfg["my_sec"] = _cfg.get(ak2, "")

    if (
        svr == "prod" and product == "01" or svr == "prod" and product == "30"
    ):  # 실전투자 주식투자, 위탁계좌, 투자계좌
        cfg["my_acct"] = _cfg.get("my_acct_stock", "")
    elif (
        svr == "prod" and product == "03" or svr == "prod" and product == "08"
    ):  # 실전투자 선물옵션(파생)
        cfg["my_acct"] = _cfg.get("my_acct_future", "")
    elif svr == "vps" and product == "01":  # 모의투자 주식투자, 위탁계좌, 투자계좌
        cfg["my_acct"] = _cfg.get("my_paper_stock", "")
    elif svr == "vps" and product == "03":  # 모의투자 선물옵션(파생)
        cfg["my_acct"] = _cfg.get("my_paper_future", "")

    cfg["my_prod"] = product
    cfg["my_token"] = token_key
    # config 객체가 있으면 BASE_URL을 무조건 사용하도록 수정 (환경 변수/내부 _cfg 신뢰 불가)
    # 이유: _cfg.get(svr, '')는 빈 값이거나 잘못된 값일 수 있음
    if config is not None:
        cfg["my_url"] = config.BASE_URL
    else:
        cfg["my_url"] = _cfg.get(svr, "")

    _setTRENV(cfg)


def _getResultObject(json_data):
    _tc_ = namedtuple("res", json_data.keys())

    return _tc_(**json_data)


# Token 발급, 유효기간 1일, 6시간 이내 발급시 기존 token값 유지, 발급시 알림톡 무조건 발송
# 모의투자인 경우  svr='vps', 투자계좌(01)이 아닌경우 product='XX' 변경하세요 (계좌번호 뒤 2자리)
def auth(
    config=None,
    svr: str = "prod",
    product: Optional[str] = None,
    url: Optional[str] = None,
) -> Any:
    """API 인증 토큰을 발급받습니다.

    Args:
        config: KISConfig 인스턴스 또는 None
        svr (str): 서버 타입 ('prod' or 'vps'). Defaults to 'prod'.
        product (Optional[str]): 상품 코드. Defaults to None.
        url (Optional[str]): API URL. Defaults to None.

    Returns:
        Any: 인증 토큰 정보를 포함한 응답 객체
    """
    # [변경 이유] flake8 F824 (unused global) 경고 제거: 실제 재할당하는 전역 변수만 선언
    global _cfg

    if config is not None:
        _cfg = {
            "my_app": config.APP_KEY,
            "my_sec": config.APP_SECRET,
            "my_acct_stock": config.ACCOUNT_NO,
            "my_prod": config.ACCOUNT_CODE,
            "prod": config.BASE_URL,
        }
        if product is None:
            product = config.ACCOUNT_CODE
    if product is None:
        product = _cfg.get("my_prod", "")
    # API 키는 config 매개변수로 전달되어야 합니다.
    if svr == "prod":  # 실전투자
        ak1 = "my_app"  # 앱키 (실전투자용)
        ak2 = "my_sec"  # 앱시크리트 (실전투자용)
    elif svr == "vps":  # 모의투자
        ak1 = "paper_app"  # 앱키 (모의투자용)
        ak2 = "paper_sec"  # 앱시크리트 (모의투자용)

    # 앱키, 앱시크리트 가져오기
    p = {
        "grant_type": "client_credentials",
        "appkey": _cfg.get(ak1, ""),
        "appsecret": _cfg.get(ak2, ""),
    }

    # 현재 APP_KEY 가져오기 (토큰 파일 분리를 위해)
    current_app_key = _cfg.get(ak1, "")

    # 기존 발급된 토큰이 있는지 확인 (APP_KEY별로 조회)
    saved_token = read_token(app_key=current_app_key)

    if saved_token is None:  # 기존 발급 토큰 확인이 안되면 발급처리
        # config.BASE_URL이 비어 있으면 환경 변수에서 직접 가져옴 (이중 안전장치)
        base_url = (
            config.BASE_URL
            if config and config.BASE_URL
            else os.getenv("KIS_BASE_URL", "")
        )
        _logger.debug(f"인증 URL: {base_url}")  # 디버그 레벨로 변경 (기본 출력 안됨)
        url = f"{base_url}/oauth2/tokenP"
        res = requests.post(
            url, data=json.dumps(p), headers=_getBaseHeader()
        )  # 토큰 발급
        rescode = res.status_code
        if rescode == 200:  # 토큰 정상 발급
            my_token = _getResultObject(res.json()).access_token  # 토큰값 가져오기
            my_expired = _getResultObject(
                res.json()
            ).access_token_token_expired  # 토큰값 만료일시 가져오기
            save_token(
                my_token, my_expired, app_key=current_app_key
            )  # APP_KEY별로 저장
            _logger.info("토큰 발급 완료")
        else:
            _logger.error(f"토큰 발급 실패 - 응답코드: {rescode}, 응답내용: {res.text}")
            # 토큰 발급 실패 시 예외 발생(이후 코드 실행 방지)
            raise RuntimeError(f"KIS API 토큰 발급 실패 (HTTP {rescode})")
    else:
        # 저장된 토큰 사용 (read_token()에서 반환한 유효한 토큰)
        my_token = saved_token.get("access_token", saved_token)
        # 저장된 토큰의 실제 만료 시간 사용 (중요!)
        my_expired = saved_token.get(
            "access_token_token_expired", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    # 발급토큰 정보 포함해서 헤더값 저장 관리, API 호출시 필요
    changeTREnv(f"Bearer {my_token}", svr, product, config)

    _base_headers["authorization"] = _TRENV.my_token
    _base_headers["appkey"] = _TRENV.my_app
    _base_headers["appsecret"] = _TRENV.my_sec

    global _last_auth_time
    _last_auth_time = datetime.now()

    if _DEBUG:
        print(f"[{_last_auth_time}] => get AUTH Key completed!")

    # 토큰 정보를 반환해 테스트에서 활용할 수 있도록 합니다.
    return {"access_token": my_token, "access_token_token_expired": my_expired}


# end of initialize, 토큰 재발급, 토큰 발급시 유효시간 1일
# 프로그램 실행시 _last_auth_time에 저장하여 유효시간 체크, 유효시간 만료시 토큰 발급 처리
def reAuth(
    config=None, svr: str = "prod", product: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """토큰 재인증

    Args:
        config: KISConfig 인스턴스 또는 None
        svr (str): 서버 타입. Defaults to 'prod'.
        product (Optional[str]): 상품 코드. Defaults to None.

    Returns:
        Optional[Dict[str, Any]]: 인증 토큰 정보
    """
    n2 = datetime.now()
    if config is not None or (n2 - _last_auth_time).seconds >= 86400:
        if product is None:
            product = _cfg.get("my_prod", "")
        return auth(config, svr, product)

    # APP_KEY 가져오기 (토큰 파일 분리를 위해)
    if svr == "prod":
        app_key = _cfg.get("my_app", "")
    else:  # vps (모의투자)
        app_key = _cfg.get("paper_app", "")

    return read_token(app_key=app_key)


def getEnv() -> Dict[str, Any]:
    """환경 설정 반환

    Returns:
        Dict[str, Any]: 현재 환경 설정
    """
    return _cfg


def getTREnv() -> Any:
    """거래 환경 정보 반환

    Returns:
        Any: 거래 환경 설정 정보
    """
    return _TRENV


# 주문 API에서 사용할 hash key값을 받아 header에 설정해 주는 함수
# 현재는 hash key 필수 사항아님, 생략가능, API 호출과정에서 변조 우려를 하는 경우 사용
# Input: HTTP Header, HTTP post param
# Output: None
def set_order_hash_key(h: Dict[str, str], p: Dict[str, Any]) -> None:
    url = f"{getTREnv().my_url}/uapi/hashkey"  # hashkey 발급 API URL

    res = requests.post(url, data=json.dumps(p), headers=h)
    rescode = res.status_code
    if rescode == 200:
        h["hashkey"] = _getResultObject(res.json()).HASH
    else:
        print("Error:", rescode)


# API 호출 응답에 필요한 처리 공통 함수
class APIResp:
    def __init__(self, resp):
        self._resp = resp
        self._header = None
        self._body = None
        self._error_code = "00000000"
        self._error_message = "정상처리"
        self._rt_cd = "0"

        self._setHeader()
        self._setBody()

    def getResCode(self):
        return self._resp.status_code

    def _setHeader(self):
        self._header = self._resp.headers
        if "tr_id" in self._header:
            self._tr_id = self._header["tr_id"]

    def _setBody(self):
        if self._resp.status_code == 200:
            self._body = self._resp.json()

    def getHeader(self):
        return self._header

    def getBody(self):
        return self._body

    def getResponse(self):
        return self._resp

    def isOK(self):
        try:
            if self.getBody()["rt_cd"] == "0":
                return True
            else:
                self._rt_cd = self.getBody()["rt_cd"]
                self._error_code = self.getBody()["msg_cd"]
                self._error_message = self.getBody()["msg1"]
                return False
        except Exception as e:
            self._error_message = f"Authentication failed: {str(e)}"
            return False

    def getErrorCode(self):
        return self._error_code

    def getErrorMessage(self):
        return self._error_message

    def printAll(self):
        print(f"STATUS: {self.getResCode()}")
        print(f"HEADER: {self.getHeader()}")
        print(f"BODY: {self.getBody()}")
        print(f"ErrorCode: {self.getErrorCode()}")
        print(f"ErrorMessage: {self.getErrorMessage()}")

    def printError(self, url):
        print(f"Error: {self.getResCode()}")
        print(f"URL: {url}")
        print(f"Header: {self.getHeader()}")
        print(f"Body: {self.getBody()}")
        print(f"ErrorCode: {self.getErrorCode()}")
        print(f"ErrorMessage: {self.getErrorMessage()}")


# 공통 API 호출부분, 모든 API 호출은 이 함수를 통해서 호출된다.
def _url_fetch(
    api_url, ptr_id, tr_cont, params, appendHeaders=None, postFlag=False, hashFlag=True
):
    url = f"{getTREnv().my_url}{api_url}"

    headers = _getBaseHeader()

    # 추가 Header 설정
    tr_id = ptr_id
    if tr_cont == "N":
        tr_cont = ""

    headers["tr_id"] = tr_id
    headers["tr_cont"] = tr_cont

    if appendHeaders is not None and len(appendHeaders) > 0:
        for header in appendHeaders:
            headers[header] = appendHeaders[header]

    if postFlag:  # POST로 호출
        if hashFlag:
            set_order_hash_key(headers, params)
        res = requests.post(url, headers=headers, data=json.dumps(params))
    else:  # GET으로 호출
        res = requests.get(url, headers=headers, params=params)

    if res.status_code == 200:
        ar = APIResp(res)
        return ar
    else:
        ar = APIResp(res)
        ar.printError(url)
        return ar


# =============================================================================
# 비동기 인증 (aiohttp)
# =============================================================================
#
# 동기 auth()/reAuth()의 비동기 짝. 토큰 발급은 네트워크 대기가 대부분이라
# 여러 계정을 동시에 인증하거나 asyncio 앱에서 이벤트 루프를 막지 않으려면
# 비동기 경로가 필요하다.
#
# aiohttp는 선택적 의존성이다. 모듈 임포트 시점이 아니라 호출 시점에 확인해서,
# 동기 경로만 쓰는 사용자가 aiohttp 없이도 이 모듈을 임포트할 수 있게 한다.


def apply_token_env(
    token: str,
    svr: str = "prod",
    product: Optional[str] = None,
    config=None,
) -> None:
    """Install an already-issued token into the TR environment and headers.

    `auth()`가 토큰을 받은 뒤 수행하는 마무리 단계만 떼어낸 것. 비동기 경로가
    토큰을 이미 await로 받아둔 상태에서 `auth()`를 다시 부르면 동기 HTTP가
    한 번 더 나가므로(그리고 이벤트 루프를 막으므로) 이 부분만 재사용한다.

    Args:
        token: 발급받은 access token (Bearer 접두어 없이).
        svr: 'prod' 또는 'vps'.
        product: 계좌 상품코드. None이면 config/모듈 설정에서 가져온다.
        config: `KISConfig` 인스턴스.
    """
    if product is None:
        product = config.ACCOUNT_CODE if config is not None else _cfg.get("my_prod", "")

    # changeTREnv()는 appkey/appsecret을 인자 config가 아니라 모듈 `_cfg`에서
    # 읽는다. 동기 auth()가 그 전에 _cfg를 config로 채우기 때문에 동작하는 것이라,
    # 이 단계를 빠뜨리면 헤더의 appkey가 빈 문자열이 된다.
    # auth()처럼 _cfg를 통째로 재할당하지는 않는다 — 그러면 paper_app/vps 같은
    # 다른 슬롯이 사라진다.
    if config is not None:
        slot_app, slot_sec = (
            ("my_app", "my_sec") if svr == "prod" else ("paper_app", "paper_sec")
        )
        _cfg[slot_app] = config.APP_KEY
        _cfg[slot_sec] = config.APP_SECRET
        _cfg["my_acct_stock"] = config.ACCOUNT_NO
        _cfg["my_prod"] = config.ACCOUNT_CODE
        _cfg[svr] = config.BASE_URL

    changeTREnv(f"Bearer {token}", svr, product, config)

    _base_headers["authorization"] = _TRENV.my_token
    _base_headers["appkey"] = _TRENV.my_app
    _base_headers["appsecret"] = _TRENV.my_sec

    global _last_auth_time
    _last_auth_time = datetime.now()


def _require_aiohttp():
    """Import aiohttp lazily so the sync path does not depend on it."""
    try:
        import aiohttp
    except ImportError as e:
        raise ImportError(
            "aiohttp is not installed. 비동기 인증을 쓰려면 설치하세요: "
            "pip install 'kis-agent[async]' 또는 pip install aiohttp"
        ) from e
    return aiohttp


def _app_key_for(config=None, svr: str = "prod") -> str:
    """Pick the APP_KEY slot the way the sync auth() does.

    토큰 캐시는 APP_KEY별로 분리되므로 캐시 조회와 토큰 요청이 **같은 키**를
    골라야 한다. 여기서 갈라지면 모의(vps)인데 실전 토큰을 재사용하거나,
    맞는 모의 토큰을 두고도 캐시 미스가 난다.
    """
    if config is not None:
        return config.APP_KEY
    # svr에 따라 실전/모의 키 슬롯을 고른다 (동기 auth()와 동일 규칙).
    return _cfg.get("my_app" if svr == "prod" else "paper_app", "")


def _build_token_request(config=None, svr: str = "prod"):
    """Assemble the token request shared by auth_async and reAuth_async.

    Mirrors the sync auth(): config가 있으면 그 값을, 없으면 모듈 `_cfg`를 쓴다.

    Returns:
        (url, payload, app_key) — app_key는 토큰 캐시를 APP_KEY별로 분리하는 데 쓴다.
    """
    app_key = _app_key_for(config, svr)
    if config is not None:
        app_secret = config.APP_SECRET
        base_url = config.BASE_URL
    else:
        app_secret = _cfg.get("my_sec" if svr == "prod" else "paper_sec", "")
        base_url = _cfg.get(svr, "") or os.getenv("KIS_BASE_URL", REAL_BASE_URL)

    payload = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret,
    }
    return f"{base_url}/oauth2/tokenP", payload, app_key


async def _issue_token_async(config=None, svr: str = "prod") -> Dict[str, Any]:
    """Request a fresh token over aiohttp and cache it.

    Raises:
        ImportError: aiohttp가 설치되지 않은 경우.
        RuntimeError: 토큰 발급이 실패한 경우 (동기 auth()와 동일하게 조용히
            None을 반환하지 않는다 — 인증 실패를 감추면 이후 모든 호출이
            영문 모를 401로 실패한다).
    """
    aiohttp = _require_aiohttp()

    url, payload, app_key = _build_token_request(config=config, svr=svr)

    async with aiohttp.ClientSession() as session, session.post(
        url, data=json.dumps(payload), headers=_getBaseHeader()
    ) as res:
        if res.status != 200:
            body = await res.text()
            _logger.error(f"토큰 발급 실패 - 응답코드: {res.status}, 응답내용: {body}")
            raise RuntimeError(f"KIS API 토큰 발급 실패 (HTTP {res.status})")

        data = await res.json()

    token = {
        "access_token": data.get("access_token"),
        "access_token_token_expired": data.get("access_token_token_expired"),
    }
    save_token(
        token["access_token"], token["access_token_token_expired"], app_key=app_key
    )
    # 동기 auth()는 토큰 발급 후 헤더/TR 환경까지 설치한다. 비동기가 이를
    # 빠뜨리면 "인증은 됐는데 이후 호출이 헤더 없이 나가는" 비대칭이 생긴다.
    apply_token_env(token["access_token"], svr=svr, config=config)
    _logger.info("토큰 발급 완료 (async)")
    return token


async def _auth_async_impl(
    config=None, svr: str = "prod", context: str = "async"
) -> Dict[str, Any]:
    """Shared body of auth_async/reAuth_async: reuse the cache, else issue.

    캐시를 쓰든 새로 발급하든 **항상** TR 환경을 설치한다. 캐시 히트일 때만
    건너뛰면 "두 번째 호출부터 헤더가 안 붙는" 자리 잡기 힘든 버그가 된다.
    """
    app_key = _app_key_for(config, svr)
    cached = read_token(app_key=app_key) if app_key else read_token()
    if cached:
        _logger.debug(f"캐시된 토큰 재사용 ({context})")
        apply_token_env(cached["access_token"], svr=svr, config=config)
        return cached

    return await _issue_token_async(config=config, svr=svr)


async def auth_async(config=None, svr: str = "prod") -> Dict[str, Any]:
    """Issue an access token asynchronously, reusing the cached one when valid.

    동기 `auth()`의 비동기 짝. 캐시된 토큰이 있으면 네트워크를 타지 않는다
    (KIS는 1일 1회 발급이 원칙이라 캐시 재사용이 중요하다).

    Args:
        config: `KISConfig` 인스턴스. None이면 모듈 `_cfg`를 사용한다.
        svr: 'prod'(실전) 또는 'vps'(모의).

    Returns:
        `{"access_token": ..., "access_token_token_expired": ...}`

    Raises:
        ImportError: aiohttp 미설치.
        RuntimeError: 토큰 발급 실패.

    Example:
        >>> token = await auth_async(config)
    """
    return await _auth_async_impl(config=config, svr=svr, context="async")


async def reAuth_async(config=None, svr: str = "prod") -> Dict[str, Any]:
    """Refresh the access token asynchronously.

    동기 `reAuth()`의 비동기 짝. `auth_async()`와 마찬가지로 유효한 캐시가
    있으면 그대로 쓴다 — 만료 전 재발급은 KIS가 기존 토큰을 그대로 돌려주므로
    호출만 낭비된다.

    Args:
        config: `KISConfig` 인스턴스. None이면 모듈 `_cfg`를 사용한다.
        svr: 'prod'(실전) 또는 'vps'(모의).

    Returns:
        `{"access_token": ..., "access_token_token_expired": ...}`

    Raises:
        ImportError: aiohttp 미설치.
        RuntimeError: 토큰 발급 실패.
    """
    return await _auth_async_impl(config=config, svr=svr, context="async reAuth")
