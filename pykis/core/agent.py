from . import client as core_client
from .client import API_ENDPOINTS
from ..account.balance import AccountBalanceAPI as AccountAPI
from ..stock.api import StockAPI
from ..stock.market import StockMarketAPI
from ..program.trade import ProgramTradeAPI
from ..strategy.trigger import StrategyTrigger
from typing import Optional, Dict
import logging
import datetime
import sqlite3
import pandas as pd
import os
from datetime import timedelta
import json
import time
from dotenv import load_dotenv
from .auth import auth
from .client import KISClient
from .config import KISConfig

# .env 파일 로드
load_dotenv()

class Agent:
    """
    한국투자증권 API의 통합 인터페이스입니다.
    
    모든 API 기능을 하나의 클래스에서 제공하여 사용자가 일관된 인터페이스로
    주식 시세, 계좌 정보, 프로그램 매매, 전략 실행 등을 사용할 수 있습니다.
    
    Example:
        >>> from pykis import Agent
        >>> agent = Agent()
        >>> 
        >>> # 주식 시세 조회
        >>> price = agent.get_stock_price("005930")
        >>> 
        >>> # 계좌 잔고 조회
        >>> balance = agent.get_account_balance()
        >>> 
        >>> # 프로그램 매매 정보 조회
        >>> program_info = agent.get_program_trade_summary("005930")
        >>> 
        >>> # 조건검색식 종목 조회
        >>> condition_stocks = agent.get_condition_stocks()
    """
    
    def __init__(self, client: Optional[KISClient] = None, account_info: Optional[Dict] = None):
        """
        Agent를 초기화합니다.
        
        Args:
            client (KISClient, optional): API 클라이언트. None이면 새로 생성
            account_info (Dict, optional): 계좌 정보. None이면 .env에서 자동 로드
        """
        self.client = client or KISClient()
        
        # 계좌 정보 설정
        if account_info is None:
            # .env 파일에서 계좌 정보 자동 로드
            config = KISConfig()
            self.account_info = {
                'CANO': config.account_stock,
                'ACNT_PRDT_CD': config.account_product
            }
        else:
            self.account_info = account_info
        
        # API 모듈 초기화
        self._init_apis()
        
    def _init_apis(self):
        """API 모듈들을 초기화합니다."""
        self.account_api = AccountAPI(self.client, self.account_info)
        self.stock_api = StockAPI(self.client, self.account_info)
        self.program_api = ProgramTradeAPI(self.client, self.account_info)
        self.strategy_api = StrategyTrigger(self.client, self.account_info)
    
    # ============================================================================
    # 주식 시세 관련 메서드들 (StockAPI 위임)
    # ============================================================================
    
    def get_stock_price(self, code: str):
        """현재가 조회"""
        return self.stock_api.get_stock_price(code)
    
    def get_daily_price(self, code: str, period: str = "D", org_adj_prc: str = "1"):
        """
        일별 시세 조회 (Postman 검증된 방식)
        
        Args:
            code: 종목코드 (6자리)
            period: 기간구분 (D: 일, W: 주, M: 월, Y: 년)
            org_adj_prc: 수정주가구분 (0: 수정주가 미사용, 1: 수정주가 사용)
        """
        return self.stock_api.get_daily_price(code, period, org_adj_prc)
    
    def get_minute_price(self, code: str, hour: str = "153000"):
        """
        주식당일분봉조회 (Postman 검증된 방식)
        
        Args:
            code: 종목코드 (6자리)
            hour: 시간 (HHMMSS 형식, 기본값: 153000)
        """
        return self.stock_api.get_minute_price(code, hour)
    
    def get_member(self, code: str):
        """거래원 조회"""
        return self.stock_api.get_member(code)
    
    def get_program_trade_summary(self, code: str):
        """프로그램 매매 요약 조회"""
        return self.program_api.get_program_trade_summary(code)
    
    def get_member_transaction(self, code: str, mem_code: str = "99999"):
        """회원사 매매 정보 조회"""
        return self.stock_api.get_member_transaction(code, mem_code)
    
    def get_volume_power(self, volume: int = 0):
        """체결강도 순위 조회"""
        return self.stock_api.get_volume_power(volume)
    
    # ============================================================================
    # 계좌 관련 메서드들 (AccountAPI 위임)
    # ============================================================================
    
    def get_account_balance(self):
        """계좌 잔고 조회"""
        return self.account_api.get_account_balance()
    
    def get_possible_order_amount(self):
        """주문 가능 금액 조회"""
        return self.account_api.get_possible_order_amount()
    
    def get_total_evaluation(self):
        """총 평가 금액 조회"""
        return self.account_api.get_total_evaluation()
    
    def get_account_order_quantity(self, code: str):
        """계좌별 주문 수량 조회"""
        return self.account_api.get_account_order_quantity(code)
    
    # ============================================================================
    # 프로그램 매매 관련 메서드들 (ProgramTradeAPI 위임)
    # ============================================================================
    
    def get_program_trade_hourly_trend(self, code: str):
        """시간별 프로그램 매매 추이 조회"""
        return self.program_api.get_program_trade_hourly_trend(code)
    
    def get_program_trade_daily_summary(self, code: str, date_str: str):
        """일별 프로그램 매매 집계 조회"""
        return self.program_api.get_program_trade_daily_summary(code, date_str)
    
    def get_program_trade_period_detail(self, start_date: str, end_date: str):
        """기간별 프로그램 매매 상세 조회"""
        return self.program_api.get_program_trade_period_detail(start_date, end_date)
    
    def get_pgm_trade(self, code: str, ref_date: str = None):
        """프로그램 매매 정보 종합 조회"""
        return self.program_api.get_pgm_trade(code, ref_date)
    
    # ============================================================================
    # 전략 관련 메서드들 (StrategyTrigger 위임)
    # ============================================================================
    
    def check_entry_condition(self, code: str):
        """매수 진입 조건 체크"""
        return self.strategy_api.check_entry_condition(code)
    
    def execute_buy_order(self, code: str, quantity: int):
        """매수 주문 실행"""
        return self.strategy_api.execute_buy_order(code, quantity)
    
    def monitor_strategy(self, code: str):
        """전략 모니터링"""
        return self.strategy_api.monitor_strategy(code)
    
    def check_exit_condition(self, code: str):
        """매도 진출 조건 체크"""
        return self.strategy_api.check_exit_condition(code)
    
    # ============================================================================
    # 기타 유틸리티 메서드들
    # ============================================================================
    
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
            # 이관 완료 후 csv 파일 삭제
            os.remove(csv_file_path)
        except Exception as e:
            logging.error(f"CSV to DB migration failed: {e}")

    def fetch_minute_data(self, code, date=None, cache_dir='cache'):
        """분봉 데이터 조회 및 캐시"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        # 캐시 디렉토리 생성
        os.makedirs(cache_dir, exist_ok=True)
        
        # DB에서 조회 시도
        db_path = 'stonks_candles.db'
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                query = '''
                    SELECT * FROM minute_data 
                    WHERE code = ? AND date = ? 
                    ORDER BY stck_cntg_hour
                '''
                df = pd.read_sql_query(query, conn, params=(code, date))
                conn.close()
                if not df.empty:
                    return df
            except Exception as e:
                logging.warning(f"DB 조회 실패: {e}")
        
        # API에서 조회
        def fetch_data_for_time(time_str):
            try:
                response = self.client.make_request(
                    endpoint="/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
                    tr_id="FHKST03010200",
                    params={
                        "FID_COND_MRKT_DIV_CODE": "J",
                        "FID_COND_SCR_DIV_CODE": "20171",
                        "FID_INPUT_ISCD": code,
                        "FID_INPUT_HOUR_1": time_str,
                        "FID_PW_DATA_INCU_YN": "Y"
                    }
                )
                return response
            except Exception as e:
                logging.error(f"API 호출 실패 ({time_str}): {e}")
                return None
        
        # 시간대별 데이터 수집
        time_slots = ["0900", "1000", "1100", "1200", "1300", "1400", "1500", "1600"]
        all_data = []
        
        for time_slot in time_slots:
            data = fetch_data_for_time(time_slot)
            if data and 'output' in data and data['output']:
                all_data.extend(data['output'])
            time.sleep(0.1)  # API 호출 간격 조절
        
        if not all_data:
            return pd.DataFrame()
        
        # DataFrame으로 변환
        df = pd.DataFrame(all_data)
        df['code'] = code
        df['date'] = date
        
        # DB에 저장
        try:
            conn = sqlite3.connect(db_path)
            df.to_sql('minute_data', conn, if_exists='append', index=False)
            conn.close()
        except Exception as e:
            logging.warning(f"DB 저장 실패: {e}")
        
        return df

    def get_condition_stocks(self):
        """조건검색식 종목 조회"""
        try:
            from ..stock.condition import get_condition_stocks_dict
            return get_condition_stocks_dict(self)
        except Exception as e:
            logging.error(f"조건검색식 종목 조회 실패: {e}")
            return {}

    def get_top_gainers(self):
        """상승률 상위 종목 조회"""
        try:
            # 간단한 구현 예시
            return self.stock_api.get_top_gainers()
        except Exception as e:
            logging.error(f"상승률 상위 종목 조회 실패: {e}")
            return []
    
    # ============================================================================
    # 하위 호환성을 위한 __getattr__ 메서드 (기존 코드와의 호환성)
    # ============================================================================
    
    def __getattr__(self, name: str):
        """API 모듈의 메서드를 위임 (하위 호환성)
        
        우선순위:
        1. StockAPI - 주식 관련 기본 API (최우선)
        2. AccountAPI - 계좌 관련 API
        3. ProgramTradeAPI - 프로그램매매 관련 API
        4. StrategyTrigger - 전략 관련 API
        """
        # StockAPI를 최우선으로 확인 (메인 주식 API)
        if hasattr(self.stock_api, name):
            attr = getattr(self.stock_api, name)
            if not callable(attr):
                return attr
            return attr
            
        # 나머지 API 모듈에서 메서드 찾기
        for api in (self.account_api, self.program_api, self.strategy_api):
            if hasattr(api, name):
                attr = getattr(api, name)
                if not callable(attr):
                    return attr
                return attr
                
        raise AttributeError(f"{self.__class__.__name__} object has no attribute '{name}'")

# Expose facade class for flat import
__all__ = ['Agent'] 
