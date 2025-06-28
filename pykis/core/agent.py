from . import client as core_client
from .client import API_ENDPOINTS
from ..account.balance import AccountBalanceAPI as AccountAPI
from ..stock.api import StockAPI
from ..stock.market import StockMarketAPI
from ..program.trade import ProgramTradeAPI
from typing import Optional, Dict
import logging
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import os
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
        self.market_api = StockMarketAPI(self.client, self.account_info)
        
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
    
    def get_program_trade_by_stock(self, code: str):
        """종목별 프로그램매매추이(체결) 조회"""
        return self.program_api.get_program_trade_by_stock(code)
    
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
        """종목별 일별 프로그램 매매 집계 조회"""
        return self.program_api.get_program_trade_daily_summary(code, date_str)
    
    def get_program_trade_period_detail(self, start_date: str, end_date: str):
        """기간별 프로그램 매매 상세 조회"""
        return self.program_api.get_program_trade_period_detail(start_date, end_date)
    
    def get_program_trade_market_daily(self, start_date: str, end_date: str):
        """시장 전체 프로그램 매매 종합현황 (일별) 조회"""
        return self.program_api.get_program_trade_market_daily(start_date, end_date)
    

    
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

    def get_holiday_info(self):
        """휴장일 정보를 조회합니다.
        
        Returns:
            Dict: 휴장일 정보, 실패 시 None
        """
        try:
            return self.stock_api.get_holiday_info()
        except Exception as e:
            logging.error(f"휴장일 정보 조회 실패: {e}")
            return None

    def is_holiday(self, date: str) -> Optional[bool]:
        """주어진 날짜(YYYYMMDD)가 한국 주식 시장 휴장일인지 확인합니다.
        
        Args:
            date: YYYYMMDD 형식의 날짜 문자열
            
        Returns:
            bool: 휴장일이면 True, 거래일이면 False, 확인 불가면 None
        """
        try:
            return self.stock_api.is_holiday(date)
        except Exception as e:
            logging.error(f"휴장일 확인 실패: {e}")
            return None

    def init_minute_db(self, db_path='stonks_candles.db'):
        """분봉 데이터용 DB 및 테이블 생성 (최초 1회)"""
        try:
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
                    stck_bsop_date TEXT,
                    PRIMARY KEY (code, date, stck_cntg_hour)
                )
            ''')
            conn.close()
            return True
        except Exception as e:
            logging.error(f"분봉 DB 초기화 실패: {e}")
            return False

    def migrate_minute_csv_to_db(self, code, db_path='stonks_candles.db'):
        """기존 csv 분봉 데이터를 DB로 이관 (한 번만)"""
        cache_dir = 'cache'
        csv_file_path = os.path.join(cache_dir, f'{code}_minute_data.csv')
        if not os.path.exists(csv_file_path):
            logging.info(f"CSV 파일이 존재하지 않음: {csv_file_path}")
            return True  # 파일이 없는 것은 오류가 아님
        try:
            df = pd.read_csv(csv_file_path)
            if df.empty:
                logging.info(f"CSV 파일이 비어있음: {csv_file_path}")
                return True  # 빈 파일도 오류가 아님
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
            logging.info(f"CSV to DB 마이그레이션 완료: {code}")
            return True
        except Exception as e:
            logging.error(f"CSV to DB migration failed: {e}")
            return False

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
                data_response = self.stock_api.get_minute_chart(code, time_str)
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
            
            # DB에도 저장 시도 (선택적)
            try:
                db_path = 'stonks_candles.db'
                conn = sqlite3.connect(db_path)
                # 기존 해당 날짜 데이터 삭제 후 새로 저장
                conn.execute('DELETE FROM minute_data WHERE code = ? AND date = ?', (code, today))
                all_data.to_sql('minute_data', conn, if_exists='append', index=False)
                conn.close()
                logging.info(f"[{code}] {today} 분봉 데이터 DB 저장 완료")
            except Exception as e:
                logging.warning(f"DB 저장 실패: {e}")
            
            return all_data
            
        return pd.DataFrame()  # 데이터 없으면 빈 DataFrame 반환 (전략/흐름/의미 변경 없음)

    def get_condition_stocks(self, user_id: str = "unohee", seq: int = 0, tr_cont: str = 'N'):
        """조건검색 결과를 조회합니다.
        
        Args:
            user_id (str): 사용자 ID (기본값: "unohee")
            seq (int): 조건검색 시퀀스 번호 (기본값: 0)
            tr_cont (str): 연속조회 여부 (기본값: 'N')
            
        Returns:
            List[Dict]: 조건검색 결과 리스트, 실패 시 None
        """
        try:
            from ..stock.condition import ConditionAPI
            condition_api = ConditionAPI(self.client)
            return condition_api.get_condition_stocks(user_id, seq, tr_cont)
        except Exception as e:
            logging.error(f"조건검색 종목 조회 실패: {e}")
            return None

    def get_top_gainers(self):
        """상승률 상위 종목 조회 (국내주식 등락률 순위)"""
        try:
            return self.stock_api.get_market_fluctuation()
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
        """
        # StockAPI를 최우선으로 확인 (메인 주식 API)
        if hasattr(self.stock_api, name):
            attr = getattr(self.stock_api, name)
            if not callable(attr):
                return attr
            return attr
            
        # 나머지 API 모듈에서 메서드 찾기
        for api in (self.account_api, self.program_api, self.market_api):
            if hasattr(api, name):
                attr = getattr(api, name)
                if not callable(attr):
                    return attr
                return attr
                
        raise AttributeError(f"{self.__class__.__name__} object has no attribute '{name}'")

# Expose facade class for flat import
__all__ = ['Agent'] 
