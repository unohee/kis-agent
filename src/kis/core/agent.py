import kis.core.client as core_client
from kis.core.client import API_ENDPOINTS
from kis.account.balance import AccountBalanceAPI as AccountAPI
from kis.stock.market import StockMarketAPI as StockAPI
from kis.program.trade import ProgramTradeAPI
from kis.strategy.trigger import StrategyTrigger
from typing import Optional
import logging
import datetime
import sqlite3
import pandas as pd
import os
from datetime import timedelta
import json
import time


class KIS_Agent:
    """
    Facade for Korean Investment Securities APIs.
    Delegates to specialized modules:
      - StockAPI
      - AccountAPI
      - ProgramTradeAPI
      - StrategyTrigger
    """
    def __init__(self, account_info: Optional[dict] = None, svr: str = 'prod', verbose: bool = False):
        """클라이언트 또는 계좌 정보를 받아 초기화"""
        if account_info and hasattr(account_info, 'make_request'):
            # 외부에서 전달된 클라이언트 사용
            self.client = account_info
            account_info = {"CANO": "", "ACNT_PRDT_CD": ""}
        else:
            self.client = core_client.KISClient(svr=svr, verbose=verbose)
        # Force token refresh during initialization to avoid soft-banned session tokens
        # self.client.refresh_token()

        # Instantiate API modules with shared client and account info
        self.account_api = AccountAPI(self.client, account_info)
        self.stock_api   = StockAPI(self.client, account_info)
        self.program_api = ProgramTradeAPI(self.client)
        self.strategy_api = StrategyTrigger(self.client, account_info)

        # Add today attribute
        self.today = datetime.datetime.now().strftime('%Y%m%d')

    def __getattr__(self, name: str):
        # Delegate attribute lookup to underlying API modules
        for api in (self.account_api, self.stock_api, self.program_api, self.strategy_api):
            if hasattr(api, name):
                return getattr(api, name)
        raise AttributeError(f"{self.__class__.__name__} object has no attribute '{name}'")
    
    
    @staticmethod
    def classify_broker(name: str) -> str:
        """간단한 거래원 성격 분류기: 외국계 / 리테일 / 기관"""
        # Guard clause: if name is not a string, return "N/A"
        if not isinstance(name, str):
            return "N/A"
        foreign_brokers = ["모간", "CS", "맥쿼리", "골드만", "바클레이", "노무라", "UBS", "BOA", "BNP"]
        retail_brokers = ["키움", "NH투자", "미래에셋", "삼성증권", "신한증권"]
        name = name.upper()

        if any(fb.upper() in name for fb in foreign_brokers):
            return "외국계"
        elif any(rb.upper() in name for rb in retail_brokers):
            return "리테일/국내기관"
        else:
            return "기타"

    def is_holiday(self, date: str, retries: int = 10) -> Optional[bool]:
        """주어진 날짜(YYYYMMDD)가 한국 주식 시장 휴장일인지 확인합니다.
        
        Args:
            date: YYYYMMDD 형식의 날짜 문자열
            retries: API 호출 실패 시 재시도 횟수
            
        Returns:
            bool: 휴장일이면 True, 거래일이면 False, 확인 불가면 None
        """
        # 로깅 레벨 설정
        logging.getLogger().setLevel(logging.DEBUG)
        
        # 캐시 디렉토리 생성
        cache_dir = 'cache'
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, 'holiday_cache.json')
        
        # 캐시 로드
        holiday_cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    holiday_cache = json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load holiday cache: {e}")
        
        # 캐시된 결과가 있으면 반환
        if date in holiday_cache:
            logging.debug(f"캐시에서 휴장일 정보 조회: {date} -> {holiday_cache[date]}")
            return holiday_cache[date]
        
        # [변경 이유] 현재 월의 첫 거래일을 기준일로 사용
        current_date = datetime.datetime.strptime(date, '%Y%m%d')
        first_day_of_month = current_date.replace(day=1)
        bass_dt = first_day_of_month.strftime('%Y%m%d')
        logging.debug(f"기준일 계산: {date} -> {bass_dt}")
        
        # API 호출
        params = {
            "BASS_DT": bass_dt,  # 현재 월의 첫 거래일
            "CTX_AREA_NK": "",
            "CTX_AREA_FK": ""
        }
        
        response = None  # response 변수 초기화
        for attempt in range(retries):
            try:
                logging.debug(f"API 호출 시도 {attempt + 1}/{retries}")
                logging.debug(f"요청 파라미터: {params}")
                
                response = self.client.make_request(
                    endpoint=API_ENDPOINTS['HOLIDAY_CHECK'],
                    tr_id="CTCA0903R",
                    params=params,
                    retries=1  # 이미 retries 루프가 있으므로 1로 설정
                )
                
                logging.debug(f"API 응답: {json.dumps(response, ensure_ascii=False, indent=2)}")
                
                # [변경 이유] API 응답이 에러인 경우 처리
                if response.get('rt_cd') != '0':
                    error_msg = response.get('msg1', '알 수 없는 오류')
                    logging.error(f"API 호출 실패: {error_msg}")
                    if attempt < retries - 1:
                        time.sleep(1)
                        continue
                    return None
                
                if response and response.get('output'):
                    # [변경 이유] output 리스트에서 오늘 날짜(bass_dt==date) 항목을 찾아야 함
                    today_info = next((item for item in response['output'] if item.get('bass_dt') == date), None)
                    if today_info:
                        opnd_yn = today_info.get('opnd_yn')
                        is_holiday = opnd_yn == 'N'
                        logging.debug(f"휴장일 정보 조회: {date} -> {is_holiday} (opnd_yn: {opnd_yn})")
                    # 결과 캐시에 저장
                    holiday_cache[date] = is_holiday
                    try:
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(holiday_cache, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        logging.warning(f"Failed to save holiday cache: {e}")
                    return is_holiday
                    
                    # [변경 이유] 오늘 날짜가 현재 페이지에 없으면 다음 페이지 확인
                    ctx_area_nk = response.get('ctx_area_nk', '').strip()
                    if ctx_area_nk:  # 다음 페이지가 있는 경우
                        params['CTX_AREA_NK'] = ctx_area_nk
                        params['CTX_AREA_FK'] = response.get('ctx_area_fk', '').strip()
                        logging.debug(f"다음 페이지 요청: CTX_AREA_NK={ctx_area_nk}, CTX_AREA_FK={params['CTX_AREA_FK']}")
                        continue
                    
                    # [변경 이유] 모든 페이지를 확인했는데도 오늘 날짜를 찾지 못한 경우
                    logging.warning(f"output에 오늘 날짜({date}) 데이터가 없음: {response['output']}")
                    return None
                
                # API 응답이 없거나 실패한 경우
                if attempt < retries - 1:
                    time.sleep(1)  # 재시도 전 대기
                    continue
                    
            except Exception as e:
                logging.error(f"Error checking holiday status for {date}: {e}")
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
        
        # 모든 재시도 실패
        if response is None:
            logging.warning(f"휴장일 상태를 확인할 수 없습니다 ({date}). API 응답 없음")
        logging.warning(f"휴장일 상태를 확인할 수 없습니다 ({date}). 응답: {response}")
        return None

    def init_minute_db(self, db_path='stonks_candles.db'):
        """분봉 데이터용 DB 및 테이블 생성 (최초 1회)"""
        conn = sqlite3.connect(db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS minute_data (
                code TEXT,
                date TEXT,
                tm TEXT,
                stck_cntg_hour TEXT,
                stck_prpr REAL,
                stck_oprc REAL,
                stck_hgpr REAL,
                stck_lwpr REAL,
                cntg_vol INTEGER,
                acml_tr_pbmn REAL,
                PRIMARY KEY (code, date, stck_cntg_hour)
            )
        ''')
        conn.close()

    def migrate_minute_csv_to_db(self, code, db_path='stonks_candles.db'):
        """기존 csv 분봉 데이터를 DB로 이관 (한 번만)"""
        cache_dir = 'cache'
        csv_file_path = os.path.join(cache_dir, f'{code}_minute_data.csv')
        if not os.path.exists(csv_file_path):
            return
        try:
            df = pd.read_csv(csv_file_path)
            if df.empty:
                return
            # code, date 컬럼 추가
            today = datetime.now().strftime('%Y%m%d')
            df['code'] = code
            df['date'] = today
            # DB에 저장
            conn = sqlite3.connect(db_path)
            df.to_sql('minute_data', conn, if_exists='append', index=False)
            conn.close()
            # 이관 후 csv 삭제
            os.remove(csv_file_path)
        except Exception as e:
            print(f"[migrate_minute_csv_to_db] {code} 이관 실패: {e}")

    def fetch_minute_data(self, code, date=None, cache_dir='cache'):
        """분봉 데이터 CSV에서 조회, 없으면 API로 수집 후 CSV에 저장 (DB는 장 마감 후 별도 이관)"""
        import datetime  # datetime 모듈 명시적 임포트 (datetime.now() 오류 방지)
        import pandas as pd
        import os
        os.makedirs(cache_dir, exist_ok=True)
        today = date or datetime.datetime.now().strftime('%Y%m%d')
        csv_file_path = os.path.join(cache_dir, f'{code}_minute_data.csv')

        # 1. CSV에서 조회 (기존 방식)
        if os.path.exists(csv_file_path):
            try:
                df = pd.read_csv(csv_file_path)
                if not df.empty:
                    return df
            except Exception as e:
                logging.warning(f"[{code}] CSV 로드 실패: {e}")

        # 2. CSV에 없으면 API로 수집
        now = datetime.datetime.now()
        current_date = now.date()
        market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
        market_open_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if market_open_time <= now <= market_close_time:
            current_time_to_fetch = now
        else:
            current_time_to_fetch = market_close_time
        data_frames = []
        def fetch_data_for_time(time_str):
            try:
                data_response = self.get_minute_chart(code, time_str)
                if not data_response or data_response.get('rt_cd') != '0' or 'output2' not in data_response:
                    return None
                data = data_response['output2']
                if data:
                    df = pd.DataFrame(data)
                    if not df.empty and 'stck_cntg_hour' in df.columns:
                        df['stck_cntg_hour'] = df['stck_cntg_hour'].apply(
                            lambda x: int(current_date.strftime('%Y%m%d') + str(x).zfill(6)[-6:])
                        )
                        return df
            except Exception:
                return None
            return None
        from datetime import timedelta
        loop_time = current_time_to_fetch
        while loop_time >= market_open_time:
            time_str = loop_time.strftime('%H%M%S')
            data = fetch_data_for_time(time_str)
            if data is not None:
                data_frames.append(data)
            loop_time -= timedelta(minutes=30)
        if data_frames:
            all_data = pd.concat(data_frames, ignore_index=True)
            all_data['code'] = code
            all_data['date'] = today
            # CSV에 저장 (DB 저장은 장 마감 후 별도 이관)
            all_data.to_csv(csv_file_path, index=False)
            return all_data
        return pd.DataFrame()  # 데이터 없으면 빈 DataFrame 반환 (전략/흐름/의미 변경 없음)

    def get_condition_stocks(self):
        """조건검색 종목 조회"""
        try:
            # 필수 파라미터만 포함
            params = {
                "user_id": "unohee",
                "seq": "0",
                "tr_cont": "N"
            }
            
            # API 호출
            response = self.client.make_request(
                endpoint=API_ENDPOINTS['CONDITIONED_STOCK'],
                tr_id="HHKST03900400",
                params=params
            )
            
            if response and response.get('rt_cd') == '0':
                logging.info(f"조건검색 종목 조회 성공: {response}")
            else:
                logging.error(f"조건검색 종목 조회 실패: {response}")
            
            return response
            
        except Exception as e:
            logging.error(f"Error in get_condition_stocks: {e}", exc_info=True)
            return None

    def get_top_gainers(self):
        """등락률 상위 종목 조회"""
        try:
            # 필수 파라미터만 포함
            params = {
                "user_id": "unohee",
                "seq": "0",
                "tr_cont": "N"
            }
            
            # API 호출
            response = self.client.make_request(
                endpoint=API_ENDPOINTS['MARKET_RANKINGS'],
                tr_id="FHPST01700000",
                params=params
            )
            
            if response and response.get('rt_cd') == '0':
                logging.info(f"등락률 상위 종목 조회 성공: {response}")
            else:
                logging.error(f"등락률 상위 종목 조회 실패: {response}")
            
            return response
            
        except Exception as e:
            logging.error(f"Error in get_top_gainers: {e}", exc_info=True)
            return None


# Expose facade class for flat import
__all__ = ['KIS_Agent'] 
