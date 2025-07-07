# -*- coding: utf-8 -*-
"""
Created on Wed Feb 15 16:57:19 2023

@author: Administrator
"""
#====|  토큰 발급에 필요한 API 호출 샘플 아래 참고하시기 바랍니다.  |=====================
#====|  토큰 발급에 필요한 API 호출 샘플 아래 참고하시기 바랍니다.  |=====================
#====|  토큰 발급에 필요한 API 호출 샘플 아래 참고하시기 바랍니다.  |=====================
#====|  API 호출 공통 함수 포함                                  |=====================


import time, copy
import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd
from collections import namedtuple
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode

# 환경설정 파일 로드 우선순위: 1) 현재 작업 디렉토리 .env, 2) PyKIS 패키지 루트 .env
# 다른 프로젝트에서 PyKIS를 사용할 때는 해당 프로젝트의 .env를 우선 사용
current_dir_env = os.path.join(os.getcwd(), '.env')
pykis_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(current_dir_env):
    load_dotenv(dotenv_path=current_dir_env, override=True)  # 현재 디렉토리 .env 우선
elif os.path.exists(pykis_root_env):
    load_dotenv(dotenv_path=pykis_root_env, override=True)  # PyKIS 루트 .env 대체

clearConsole = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')

key_bytes = 32

# 토큰 저장 경로 설정 - 다른 프로젝트에서 사용할 때도 항상 pykis 패키지 내부의 credit 디렉토리 사용
# __file__의 절대 경로를 기준으로 pykis/core/credit 디렉토리 지정 (다른 프로젝트에서 import해도 안전)
config_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credit')
token_tmp = os.getenv('KIS_TOKEN_PATH', os.path.join(config_root, 'KIS_Token.json'))

# 디렉토리가 없으면 생성
os.makedirs(config_root, exist_ok=True)

# 접근토큰 관리하는 파일 존재여부 체크, 없으면 생성
if not os.path.exists(token_tmp):
    # 빈 JSON 파일 생성 또는 기본 구조 생성
    with open(token_tmp, "w+", encoding='utf-8') as f:
         json.dump({}, f) # 빈 JSON 객체로 초기화

# 환경 변수 기반 설정 로드 - 기본값 추가
_cfg = {
    'my_app': os.getenv('KIS_APP_KEY', ''),
    'my_sec': os.getenv('KIS_APP_SECRET', ''),
    'my_acct_stock': os.getenv('KIS_ACCOUNT_NO', ''),
    'my_prod': os.getenv('KIS_ACCOUNT_CODE', ''),
    'prod': os.getenv('KIS_BASE_URL', 'https://openapi.koreainvestment.com:9443'),
    'vps': os.getenv('KIS_VPS_URL', 'https://openapivts.koreainvestment.com:29443'),
    'my_agent': os.getenv('KIS_USER_AGENT', 'KIS_AGENT'),
}

# 이전 설정 파일 로드 로직 제거
# if not os.path.exists(config_path):
#     raise FileNotFoundError(f"Configuration file not found at: {config_path}. Please create '{config_file_name}' in the '{config_root}' directory.")
#
# with open(config_path, encoding='UTF-8') as f:
#     _cfg = yaml.load(f, Loader=yaml.FullLoader)

_TRENV = tuple()
_last_auth_time = datetime.now()
_autoReAuth = False
_DEBUG = False
_isPaper = False

# 기본 헤더값 정의
_base_headers = {
    "Content-Type": "application/json"
}


# 토큰 발급 받아 저장 (토큰값, 토큰 유효시간,1일, 6시간 이내 발급신청시는 기존 토큰값과 동일, 발급시 알림톡 발송)
def save_token(my_token, my_expired, path: str = token_tmp):
    valid_date = datetime.strptime(my_expired, '%Y-%m-%d %H:%M:%S')
    token_data = {
        'token': my_token,
        # valid-date를 ISO 형식 문자열로 저장 (JSON 호환)
        'valid-date': valid_date.isoformat()
    }
    # print('Save token date: ', valid_date)
    # with open(token_tmp, 'w', encoding='utf-8') as f:
    #     f.write(f'token: {my_token}\n') # 이전 YAML 형식 쓰기 제거
    #     f.write(f'valid-date: {valid_date}\n')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(token_data, f, ensure_ascii=False, indent=4)


# 토큰 확인 (토큰값, 토큰 유효시간_1일, 6시간 이내 발급신청시는 기존 토큰값과 동일, 발급시 알림톡 발송)
def read_token(path: str = token_tmp):
    try:
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            tkg_tmp = json.load(f)

        # 테스트 호환을 위해 두 가지 포맷을 모두 처리합니다.
        if 'access_token' in tkg_tmp:
            return tkg_tmp
        if not tkg_tmp or 'valid-date' not in tkg_tmp or 'token' not in tkg_tmp:
            return None

        # 토큰 만료 일,시간 (ISO 형식 문자열에서 datetime 객체로 파싱)
        # exp_dt = datetime.strftime(tkg_tmp['valid-date'], '%Y-%m-%d %H:%M:%S') # YAML 형식 파싱 제거
        exp_dt_str = tkg_tmp['valid-date']
        exp_dt_obj = datetime.fromisoformat(exp_dt_str)
        exp_dt = exp_dt_obj.strftime('%Y-%m-%d %H:%M:%S') # 비교를 위해 문자열로 변환

        # 현재일자,시간
        now_dt = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

        # print('expire dt: ', exp_dt, ' vs now dt:', now_dt)
        # 저장된 토큰 만료일자 체크 (만료일시 > 현재일시 인경우 보관 토큰 리턴)
        if exp_dt > now_dt:
            # 딕셔너리 형태로 반환하여 테스트에서 활용
            return {
                'access_token': tkg_tmp['token'],
                'access_token_token_expired': exp_dt
            }
        else:
            # print('Need new token: ', tkg_tmp['valid-date'])
            return None
    except Exception as e:
        # print('read token error: ', e)
        return None

# 토큰 유효시간 체크해서 만료된 토큰이면 재발급처리
def _getBaseHeader():
    if _autoReAuth: reAuth()
    return copy.deepcopy(_base_headers)


# 가져오기 : 앱키, 앱시크리트, 종합계좌번호(계좌번호 중 숫자8자리), 계좌상품코드(계좌번호 중 숫자2자리), 토큰, 도메인
def _setTRENV(cfg):
    nt1 = namedtuple('KISEnv', ['my_app', 'my_sec', 'my_acct', 'my_prod', 'my_token', 'my_url'])
    d = {
        'my_app': cfg['my_app'],  # 앱키
        'my_sec': cfg['my_sec'],  # 앱시크리트
        'my_acct': cfg['my_acct'],  # 종합계좌번호(8자리)
        'my_prod': cfg['my_prod'],  # 계좌상품코드(2자리)
        'my_token': cfg['my_token'],  # 토큰
        'my_url': cfg['my_url']  # 실전 도메인 (https://openapi.koreainvestment.com:9443)
    }  # 모의 도메인 (https://openapivts.koreainvestment.com:29443)

    # print(cfg['my_app'])
    global _TRENV
    _TRENV = nt1(**d)


def isPaperTrading():  # 모의투자 매매
    return _isPaper


# 실전투자면 'prod', 모의투자면 'vps'를 셋팅 하시기 바랍니다.
def changeTREnv(token_key, svr='prod', product=_cfg['my_prod'], config=None):
    cfg = dict()

    global _isPaper
    if svr == 'prod':  # 실전투자
        ak1 = 'my_app'  # 실전투자용 앱키
        ak2 = 'my_sec'  # 실전투자용 앱시크리트
        _isPaper = False
    elif svr == 'vps':  # 모의투자
        ak1 = 'paper_app'  # 모의투자용 앱키
        ak2 = 'paper_sec'  # 모의투자용 앱시크리트
        _isPaper = True

    cfg['my_app'] = _cfg.get(ak1, '')
    cfg['my_sec'] = _cfg.get(ak2, '')

    if svr == 'prod' and product == '01':  # 실전투자 주식투자, 위탁계좌, 투자계좌
        cfg['my_acct'] = _cfg.get('my_acct_stock', '')
    elif svr == 'prod' and product == '30':  # 실전투자 증권저축계좌
        cfg['my_acct'] = _cfg.get('my_acct_stock', '')
    elif svr == 'prod' and product == '03':  # 실전투자 선물옵션(파생)
        cfg['my_acct'] = _cfg.get('my_acct_future', '')
    elif svr == 'prod' and product == '08':  # 실전투자 해외선물옵션(파생)
        cfg['my_acct'] = _cfg.get('my_acct_future', '')
    elif svr == 'vps' and product == '01':  # 모의투자 주식투자, 위탁계좌, 투자계좌
        cfg['my_acct'] = _cfg.get('my_paper_stock', '')
    elif svr == 'vps' and product == '03':  # 모의투자 선물옵션(파생)
        cfg['my_acct'] = _cfg.get('my_paper_future', '')

    cfg['my_prod'] = product
    cfg['my_token'] = token_key
    # config 객체가 있으면 BASE_URL을 무조건 사용하도록 수정 (환경 변수/내부 _cfg 신뢰 불가)
    # 이유: _cfg.get(svr, '')는 빈 값이거나 잘못된 값일 수 있음
    if config is not None:
        cfg['my_url'] = config.BASE_URL
    else:
        cfg['my_url'] = _cfg.get(svr, '')

    _setTRENV(cfg)


def _getResultObject(json_data):
    _tc_ = namedtuple('res', json_data.keys())

    return _tc_(**json_data)


# Token 발급, 유효기간 1일, 6시간 이내 발급시 기존 token값 유지, 발급시 알림톡 무조건 발송
# 모의투자인 경우  svr='vps', 투자계좌(01)이 아닌경우 product='XX' 변경하세요 (계좌번호 뒤 2자리)
def auth(config=None, svr='prod', product=None, url=None):
    """API 인증 토큰을 발급받습니다."""
    global _cfg, _TRENV, _base_headers

    if config is not None:
        _cfg = {
            'my_app': config.APP_KEY,
            'my_sec': config.APP_SECRET,
            'my_acct_stock': config.ACCOUNT_NO,
            'my_prod': config.ACCOUNT_CODE,
            'prod': config.BASE_URL
        }
        if product is None:
            product = config.ACCOUNT_CODE
    if product is None:
        product = _cfg.get('my_prod', '')
    # 개인 환경파일 "kis_devlp.yaml" 파일을 참조하여 앱키, 앱시크리트 정보 가져오기
    # 개인 환경파일명과 위치는 고객님만 아는 위치로 설정 바랍니다.
    if svr == 'prod':  # 실전투자
        ak1 = 'my_app'  # 앱키 (실전투자용)
        ak2 = 'my_sec'  # 앱시크리트 (실전투자용)
    elif svr == 'vps':  # 모의투자
        ak1 = 'paper_app'  # 앱키 (모의투자용)
        ak2 = 'paper_sec'  # 앱시크리트 (모의투자용)

    # 앱키, 앱시크리트 가져오기
    p = {
        "grant_type": "client_credentials",
        "appkey": _cfg.get(ak1, ''),
        "appsecret": _cfg.get(ak2, '')
    }

    # 기존 발급된 토큰이 있는지 확인
    saved_token = read_token()

    if saved_token is None:  # 기존 발급 토큰 확인이 안되면 발급처리
        # config.BASE_URL이 비어 있으면 환경 변수에서 직접 가져옴 (이중 안전장치)
        base_url = config.BASE_URL if config and config.BASE_URL else os.getenv('KIS_BASE_URL', '')
        print(f"[디버그] 인증 URL base_url={base_url}")  # 실제 URL 확인용
        url = f"{base_url}/oauth2/tokenP"
        res = requests.post(url, data=json.dumps(p), headers=_getBaseHeader())  # 토큰 발급
        rescode = res.status_code
        if rescode == 200:  # 토큰 정상 발급
            my_token = _getResultObject(res.json()).access_token  # 토큰값 가져오기
            my_expired= _getResultObject(res.json()).access_token_token_expired  # 토큰값 만료일시 가져오기
            save_token(my_token, my_expired)  # 새로 발급 받은 토큰 저장
        else:
            print(f'Get Authentification token fail!\nYou have to restart your app!!!\n[디버그] 응답코드: {rescode}, 응답내용: {res.text}')
            # 토큰 발급 실패 시 예외 발생(이후 코드 실행 방지)
            raise RuntimeError('KIS API 토큰 발급 실패')
    else:
        # 저장된 포맷이 딕셔너리일 경우 access_token 필드 사용
        if isinstance(saved_token, dict) and 'access_token' in saved_token:
            my_token = saved_token['access_token']
        else:
            my_token = saved_token
        # 저장된 토큰 사용 시 만료일이 필요 없으므로 임시 값 사용
        my_expired = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 발급토큰 정보 포함해서 헤더값 저장 관리, API 호출시 필요
    changeTREnv(f"Bearer {my_token}", svr, product, config)

    _base_headers["authorization"] = _TRENV.my_token
    _base_headers["appkey"] = _TRENV.my_app
    _base_headers["appsecret"] = _TRENV.my_sec

    global _last_auth_time
    _last_auth_time = datetime.now()

    if (_DEBUG):
        print(f'[{_last_auth_time}] => get AUTH Key completed!')

    # 토큰 정보를 반환해 테스트에서 활용할 수 있도록 합니다.
    return {
        'access_token': my_token,
        'access_token_token_expired': my_expired
    }


# end of initialize, 토큰 재발급, 토큰 발급시 유효시간 1일
# 프로그램 실행시 _last_auth_time에 저장하여 유효시간 체크, 유효시간 만료시 토큰 발급 처리
def reAuth(config=None, svr='prod', product=None):
    n2 = datetime.now()
    if config is not None or (n2 - _last_auth_time).seconds >= 86400:
        if product is None:
            product = _cfg.get('my_prod', '')
        return auth(config, svr, product)
    return read_token()


def getEnv():
    return _cfg


def getTREnv():
    # 디버깅용: 반환 객체 타입과 내용 출력 - 디버그 메시지 비활성화
    # print(f"[디버그] getTREnv() 반환 타입: {type(_TRENV)}, 값: {_TRENV}")
    return _TRENV

# 주문 API에서 사용할 hash key값을 받아 header에 설정해 주는 함수
# 현재는 hash key 필수 사항아님, 생략가능, API 호출과정에서 변조 우려를 하는 경우 사용
# Input: HTTP Header, HTTP post param
# Output: None
def set_order_hash_key(h, p):
    url = f"{getTREnv().my_url}/uapi/hashkey"  # hashkey 발급 API URL

    res = requests.post(url, data=json.dumps(p), headers=h)
    rescode = res.status_code
    if rescode == 200:
        h['hashkey'] = _getResultObject(res.json()).HASH
    else:
        print("Error:", rescode)


# API 호출 응답에 필요한 처리 공통 함수
class APIResp:
    def __init__(self, resp):
        self._resp = resp
        self._header = None
        self._body = None
        self._error_code = '00000000'
        self._error_message = '정상처리'
        self._rt_cd = '0'

        self._setHeader()
        self._setBody()

    def getResCode(self):
        return self._resp.status_code

    def _setHeader(self):
        self._header = self._resp.headers
        if 'tr_id' in self._header:
            self._tr_id = self._header['tr_id']

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
            if self.getBody()['rt_cd'] == '0':
                return True
            else:
                self._rt_cd = self.getBody()['rt_cd']
                self._error_code = self.getBody()['msg_cd']
                self._error_message = self.getBody()['msg1']
                return False
        except:
            return False

    def getErrorCode(self):
        return self._error_code

    def getErrorMessage(self):
        return self._error_message

    def printAll(self):
        print("STATUS: %s" % self.getResCode())
        print("HEADER: %s" % self.getHeader())
        print("BODY: %s" % self.getBody())
        print("ErrorCode: %s" % self.getErrorCode())
        print("ErrorMessage: %s" % self.getErrorMessage())

    def printError(self, url):
        print("Error: %s" % self.getResCode())
        print('URL: %s' % url)
        print('Header: %s' % self.getHeader())
        print('Body: %s' % self.getBody())
        print('ErrorCode: %s' % self.getErrorCode())
        print('ErrorMessage: %s' % self.getErrorMessage())


# 공통 API 호출부분, 모든 API 호출은 이 함수를 통해서 호출된다.
def _url_fetch(api_url, ptr_id, tr_cont, params, appendHeaders=None, postFlag=False, hashFlag=True):
    url = f"{getTREnv().my_url}{api_url}"

    headers = _getBaseHeader()

    # 추가 Header 설정
    tr_id = ptr_id
    if tr_cont == 'N':
        tr_cont = ''

    headers["tr_id"] = tr_id
    headers["tr_cont"] = tr_cont

    if appendHeaders is not None:
        if len(appendHeaders) > 0:
            for header in appendHeaders:
                headers[header] = appendHeaders[header]

    if (postFlag):  # POST로 호출
        if (hashFlag):
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
