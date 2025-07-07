from . import client as core_client
from .client import KISClient
from ..account.balance import AccountBalanceAPI as AccountAPI
from ..stock.api import StockAPI
from ..stock import StockMarketAPI
from ..program.trade import ProgramTradeAPI
from ..websocket.client import KisWebSocket
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
        
    def websocket(self, stock_codes: list = None, purchase_prices: dict = None, 
                  enable_index: bool = True, enable_program_trading: bool = True, 
                  enable_ask_bid: bool = False) -> KisWebSocket:
        """
        실시간 웹소켓 클라이언트를 생성합니다.

        Args:
            stock_codes (list, optional): 구독할 종목코드 리스트. Defaults to None.
            purchase_prices (dict, optional): 매수 정보 딕셔너리 {'종목코드': (매입가격, 보유 수량)}. Defaults to None.
            enable_index (bool): 지수 실시간 데이터 구독 여부. Defaults to True.
            enable_program_trading (bool): 프로그램매매 실시간 데이터 구독 여부. Defaults to True.
            enable_ask_bid (bool): 호가 실시간 데이터 구독 여부. Defaults to False.

        Returns:
            KisWebSocket: 웹소켓 클라이언트 객체
        """
        return KisWebSocket(
            client=self.client,
            account_info=self.account_info,
            stock_codes=stock_codes,
            purchase_prices=purchase_prices,
            enable_index=enable_index,
            enable_program_trading=enable_program_trading,
            enable_ask_bid=enable_ask_bid
        )

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
    
    def get_possible_order_amount(self, code: str, price: str, order_type: str = "01"):
        """주문 가능 금액 조회"""
        return self.stock_api.get_possible_order(code, price, order_type)
    

    
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
    
    def get_all_methods(self, show_details: bool = False, category: str = None):
        """
        Agent에서 사용 가능한 모든 메서드를 카테고리별로 정리하여 반환합니다.
        
        Args:
            show_details (bool): 각 메서드의 상세 설명 포함 여부 (기본값: False)
            category (str): 특정 카테고리만 보기 (기본값: None - 전체)
                          가능한 값: 'stock', 'account', 'program', 'market', 'utility', 'websocket'
        
        Returns:
            dict: 메서드 정보가 담긴 딕셔너리
        
        Example:
            >>> agent = Agent()
            >>> methods = agent.get_all_methods()
            >>> print(f"총 {len(sum(methods.values(), []))}개 메서드 사용 가능")
            >>> 
            >>> # 주식 관련 메서드만 보기
            >>> stock_methods = agent.get_all_methods(category='stock')
            >>> 
            >>> # 상세 설명 포함
            >>> detailed = agent.get_all_methods(show_details=True)
        """
        
        # 메서드 카테고리별 분류
        methods_info = {
            'stock': {
                'title': '📈 주식 시세 관련',
                'methods': [
                    ('get_stock_price', '현재가 조회', 'get_stock_price("005930")'),
                    ('get_daily_price', '일별/주별/월별 시세 조회', 'get_daily_price("005930", period="D")'),
                    ('get_minute_price', '분봉 시세 조회', 'get_minute_price("005930", hour="153000")'),
                    ('get_orderbook', '호가 정보 조회', 'get_orderbook("005930")'),
                    ('get_stock_investor', '투자자별 매매 동향', 'get_stock_investor("005930")'),
                    ('get_stock_info', '종목 기본 정보', 'get_stock_info("005930")'),
                    ('get_stock_financial', '종목 재무 정보', 'get_stock_financial("005930")'),
                    ('get_stock_basic', '종목 기초 정보', 'get_stock_basic("005930")'),
                    ('get_foreign_broker_net_buy', '외국계 브로커 순매수', 'get_foreign_broker_net_buy("005930")'),
                    ('get_member', '거래원 정보 조회', 'get_member("005930")'),
                    ('get_member_transaction', '회원사 매매 정보', 'get_member_transaction("005930")'),
                ]
            },
            'market': {
                'title': '📊 시장 정보 관련',
                'methods': [
                    ('get_volume_power', '체결강도 순위', 'get_volume_power(0)'),
                    ('get_top_gainers', '상위 상승주', 'get_top_gainers()'),
                    ('get_market_fluctuation', '시장 등락 현황', 'get_market_fluctuation()'),
                    ('get_market_rankings', '시장 순위 정보', 'get_market_rankings(volume=5000000)'),
                    ('get_kospi200_index', 'KOSPI200 지수', 'get_kospi200_index()'),
                    ('get_futures_price', '선물 시세', 'get_futures_price("101S12")'),
                    ('get_future_option_price', '선물옵션 시세', 'get_future_option_price()'),
                    ('get_daily_index_chart_price', '지수 차트', 'get_daily_index_chart_price("0001", "D")'),
                ]
            },
            'account': {
                'title': '💰 계좌 관련',
                'methods': [
                    ('get_account_balance', '계좌 잔고 조회', 'get_account_balance()'),
                    ('get_cash_available', '매수 가능 금액', 'get_cash_available("005930")'),
                    ('get_total_asset', '계좌 총 자산', 'get_total_asset()'),
                    ('get_possible_order_amount', '주문 가능 금액', 'get_possible_order_amount("005930", "60000")'),
                    ('get_account_order_quantity', '계좌별 주문 수량', 'get_account_order_quantity("005930")'),
                ]
            },
            'program': {
                'title': '🤖 프로그램 매매 관련',
                'methods': [
                    ('get_program_trade_by_stock', '종목별 프로그램매매 추이', 'get_program_trade_by_stock("005930")'),
                    ('get_program_trade_hourly_trend', '시간별 프로그램매매 추이', 'get_program_trade_hourly_trend("005930")'),
                    ('get_program_trade_daily_summary', '일별 프로그램매매 집계', 'get_program_trade_daily_summary("005930", "20250107")'),
                    ('get_program_trade_period_detail', '기간별 프로그램매매 상세', 'get_program_trade_period_detail("20250101", "20250107")'),
                    ('get_program_trade_market_daily', '시장 전체 프로그램매매', 'get_program_trade_market_daily("20250101", "20250107")'),
                ]
            },
            'utility': {
                'title': '🛠️ 유틸리티',
                'methods': [
                    ('get_holiday_info', '휴장일 정보', 'get_holiday_info()'),
                    ('is_holiday', '휴장일 여부 확인', 'is_holiday("20250107")'),
                    ('fetch_minute_data', '분봉 데이터 수집', 'fetch_minute_data("005930", "20250107")'),
                    ('get_condition_stocks', '조건검색 종목', 'get_condition_stocks()'),
                    ('init_minute_db', 'SQLite DB 초기화', 'init_minute_db("my_data.db")'),
                    ('migrate_minute_csv_to_db', 'CSV→DB 마이그레이션', 'migrate_minute_csv_to_db("005930")'),
                    ('classify_broker', '거래원 성격 분류', 'classify_broker("모간스탠리")'),
                ]
            },
            'websocket': {
                'title': '⚡ 실시간 웹소켓',
                'methods': [
                    ('websocket', '실시간 웹소켓 클라이언트', 'websocket(["005930"], enable_index=True)'),
                ]
            }
        }
        
        # 특정 카테고리만 요청된 경우
        if category:
            if category not in methods_info:
                available_categories = list(methods_info.keys())
                return {
                    'error': f'유효하지 않은 카테고리: {category}',
                    'available_categories': available_categories
                }
            methods_info = {category: methods_info[category]}
        
        # 결과 정리
        result = {}
        total_methods = 0
        
        for cat_key, cat_info in methods_info.items():
            if show_details:
                # 상세 정보 포함
                result[cat_key] = {
                    'title': cat_info['title'],
                    'count': len(cat_info['methods']),
                    'methods': [
                        {
                            'name': method[0],
                            'description': method[1],
                            'example': method[2]
                        }
                        for method in cat_info['methods']
                    ]
                }
            else:
                # 간단한 정보만
                result[cat_key] = {
                    'title': cat_info['title'],
                    'count': len(cat_info['methods']),
                    'methods': [method[0] for method in cat_info['methods']]
                }
            
            total_methods += len(cat_info['methods'])
        
        # 요약 정보 추가
        result['_summary'] = {
            'total_methods': total_methods,
            'total_categories': len(result) - 1,  # _summary 제외
            'usage_tip': 'agent.get_all_methods(show_details=True, category="stock") 형태로 상세 정보를 확인할 수 있습니다.'
        }
        
        return result
    
    def search_methods(self, keyword: str):
        """
        키워드로 메서드를 검색합니다.
        
        Args:
            keyword (str): 검색할 키워드 (메서드명이나 설명에서 검색)
        
        Returns:
            list: 매칭되는 메서드 정보 리스트
        
        Example:
            >>> agent = Agent()
            >>> # "price"라는 키워드로 검색
            >>> results = agent.search_methods("price")
            >>> for method in results:
            ...     print(f"{method['name']}: {method['description']}")
        """
        all_methods = self.get_all_methods(show_details=True)
        results = []
        keyword_lower = keyword.lower()
        
        for category_key, category_info in all_methods.items():
            if category_key == '_summary':
                continue
                
            for method in category_info['methods']:
                # 메서드명이나 설명에서 키워드 검색
                if (keyword_lower in method['name'].lower() or 
                    keyword_lower in method['description'].lower()):
                    results.append({
                        'name': method['name'],
                        'description': method['description'],
                        'example': method['example'],
                        'category': category_info['title']
                    })
        
        return results
    
    def show_method_usage(self, method_name: str):
        """
        특정 메서드의 사용법을 출력합니다.
        
        Args:
            method_name (str): 확인할 메서드명
        
        Example:
            >>> agent = Agent()
            >>> agent.show_method_usage("get_stock_price")
        """
        all_methods = self.get_all_methods(show_details=True)
        
        for category_key, category_info in all_methods.items():
            if category_key == '_summary':
                continue
                
            for method in category_info['methods']:
                if method['name'] == method_name:
                    print(f"📋 메서드: {method['name']}")
                    print(f"📝 설명: {method['description']}")
                    print(f"📂 카테고리: {category_info['title']}")
                    print(f"💡 사용 예시: agent.{method['example']}")
                    
                    # 실제 메서드가 있는지 확인하고 docstring 출력
                    if hasattr(self, method_name):
                        actual_method = getattr(self, method_name)
                        if hasattr(actual_method, '__doc__') and actual_method.__doc__:
                            print(f"📖 상세 문서:")
                            print(f"    {actual_method.__doc__.strip()}")
                    return
        
        print(f"❌ '{method_name}' 메서드를 찾을 수 없습니다.")
        print("💡 사용 가능한 메서드 확인: agent.get_all_methods()")
    
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
                data_response = self.stock_api.get_minute_price(code, time_str)
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
            return getattr(self.stock_api, name)
        
        # StockMarketAPI 확인 (시장 데이터 관련 API)
        if hasattr(self.market_api, name):
            return getattr(self.market_api, name)

        # 나머지 API 모듈에서 메서드 찾기
        for api in (self.account_api, self.program_api):
            if hasattr(api, name):
                return getattr(api, name)
                
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

# Expose facade class for flat import
__all__ = ['Agent'] 
 
