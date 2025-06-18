import os
import sys
import time
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pykis import Agent, KISConfig
from pykis.core.client import KISClient
from pykis.stock.condition import get_condition_stocks_dict

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('stock_monitor.log')
    ]
)

class StockMonitor:
    def __init__(self, config_path: str = "credit/kis_devlp.yaml"):
        """
        주식 모니터링 클래스 초기화

        Args:
            config_path (str): 설정 파일 경로
        """
        self.config = KISConfig(config_path)
        self.client = KISClient(config=self.config)
        self.agent = Agent(self.client)
        self.monitored_stocks: Dict[str, Dict] = {}
        self.last_check_time: Dict[str, datetime] = {}
        self.check_interval = 60  # 기본 체크 간격 (초)
        self.volume_threshold = 2.0  # 거래량 급증 기준 (배)
        self.price_change_threshold = 0.03  # 가격 변동 기준 (3%)
        self.program_trade_threshold = 0.5  # 프로그램 매매 비중 기준 (50%)
        self.member_trade_threshold = 0.3  # 회원사 매매 비중 기준 (30%)

    def add_stock(self, code: str, name: str, interval: int = 60) -> None:
        """
        모니터링할 종목 추가

        Args:
            code (str): 종목 코드
            name (str): 종목명
            interval (int): 체크 간격 (초)
        """
        self.monitored_stocks[code] = {
            'name': name,
            'interval': interval,
            'last_price': None,
            'last_volume': None,
            'last_program_ratio': None,
            'last_member_ratio': None
        }
        self.last_check_time[code] = datetime.now() - timedelta(seconds=interval)
        logging.info(f"종목 추가: {name}({code}), 체크 간격: {interval}초")

    def remove_stock(self, code: str) -> None:
        """
        모니터링 종목 제거

        Args:
            code (str): 종목 코드
        """
        if code in self.monitored_stocks:
            name = self.monitored_stocks[code]['name']
            del self.monitored_stocks[code]
            del self.last_check_time[code]
            logging.info(f"종목 제거: {name}({code})")

    def get_stock_price(self, code: str) -> Optional[Dict]:
        """
        현재가 조회
        """
        try:
            result = self.agent.get_stock_price(code)
            if result is None:
                return None
            if isinstance(result, pd.DataFrame):
                if result.empty:
                    return None
            elif isinstance(result, dict):
                if 'output' not in result or not result['output']:
                    return None
            return result
        except Exception as e:
            logging.error(f"현재가 조회 실패 ({code}): {e}")
            return None

    def get_daily_price(self, code: str) -> Optional[Dict]:
        """
        일별 시세 조회
        """
        try:
            result = self.agent.get_daily_price(code)
            if result is None:
                return None
            if isinstance(result, pd.DataFrame):
                if result.empty:
                    return None
            elif isinstance(result, dict):
                if 'output' not in result or not result['output']:
                    return None
            return result
        except Exception as e:
            logging.error(f"일별 시세 조회 실패 ({code}): {e}")
            return None

    def get_program_trade_summary(self, code: str) -> Optional[Dict]:
        try:
            result = self.agent.get_program_trade_summary(code)
            if result is None:
                return None
            if isinstance(result, pd.DataFrame):
                if result.empty:
                    return None
            elif isinstance(result, dict):
                if 'output' not in result or not result['output']:
                    return None
            return result
        except Exception as e:
            logging.error(f"프로그램 매매 요약 조회 실패 ({code}): {e}")
            return None

    def get_member_transaction(self, code: str, mem_code: str = "99999") -> Optional[Dict]:
        try:
            result = self.agent.get_member_transaction(code, mem_code)
            if result is None:
                return None
            if isinstance(result, pd.DataFrame):
                if result.empty:
                    return None
            elif isinstance(result, dict):
                if 'output' not in result or not result['output']:
                    return None
            return result
        except Exception as e:
            logging.error(f"회원사 매매 정보 조회 실패 ({code}): {e}")
            return None

    def get_volume_power(self, code: str) -> Optional[float]:
        try:
            daily_price = self.get_daily_price(code)
            if daily_price is None:
                return None
            if isinstance(daily_price, pd.DataFrame):
                if daily_price.empty:
                    return None
                # DataFrame에서 거래량 평균 계산
                volumes = daily_price['acml_vol'].astype(float).head(20)
                avg_volume = volumes.mean()
                current_volume = volumes.iloc[0]
            elif isinstance(daily_price, dict):
                if 'output' not in daily_price or not daily_price['output']:
                    return None
                output = daily_price['output']
                volumes = [float(item['acml_vol']) for item in output[:20]]
                avg_volume = sum(volumes) / len(volumes)
                current_volume = float(output[0]['acml_vol'])
            else:
                return None
            return current_volume / avg_volume if avg_volume > 0 else 0
        except Exception as e:
            logging.error(f"거래량 급증도 계산 실패 ({code}): {e}")
            return None

    def check_stock(self, code: str) -> None:
        try:
            price_info = self.get_stock_price(code)
            if price_info is None:
                return
            if isinstance(price_info, pd.DataFrame):
                if price_info.empty:
                    return
                current_price = float(price_info['stck_prpr'].iloc[0])
                current_volume = float(price_info['acml_vol'].iloc[0])
            elif isinstance(price_info, dict):
                if 'output' not in price_info or not price_info['output']:
                    return
                current_price = float(price_info['output']['stck_prpr'])
                current_volume = float(price_info['output']['acml_vol'])
            else:
                return

            program_info = self.get_program_trade_summary(code)
            program_ratio = 0.0
            if program_info is not None:
                if isinstance(program_info, pd.DataFrame):
                    if not program_info.empty and 'pgm_rat' in program_info.columns:
                        program_ratio = float(program_info['pgm_rat'].iloc[0]) / 100
                elif isinstance(program_info, dict):
                    if 'output' in program_info and program_info['output'] and 'pgm_rat' in program_info['output']:
                        program_ratio = float(program_info['output']['pgm_rat']) / 100

            member_info = self.get_member_transaction(code)
            member_ratio = 0.0
            if member_info is not None:
                if isinstance(member_info, pd.DataFrame):
                    if not member_info.empty and 'mem_rat' in member_info.columns:
                        member_ratio = float(member_info['mem_rat'].iloc[0]) / 100
                elif isinstance(member_info, dict):
                    if 'output' in member_info and member_info['output'] and 'mem_rat' in member_info['output']:
                        member_ratio = float(member_info['output']['mem_rat']) / 100

            stock_data = self.monitored_stocks[code]
            if stock_data['last_price'] is not None:
                price_change = abs(current_price - stock_data['last_price']) / stock_data['last_price']
                volume_change = current_volume / stock_data['last_volume'] if stock_data['last_volume'] > 0 else 0
                alerts = []
                if price_change >= self.price_change_threshold:
                    alerts.append(f"가격 변동: {price_change:.1%}")
                if volume_change >= self.volume_threshold:
                    alerts.append(f"거래량 급증: {volume_change:.1f}배")
                if program_ratio >= self.program_trade_threshold:
                    alerts.append(f"프로그램 매매 비중: {program_ratio:.1%}")
                if member_ratio >= self.member_trade_threshold:
                    alerts.append(f"회원사 매매 비중: {member_ratio:.1%}")
                if alerts:
                    logging.info(f"종목 알림 ({code}): {', '.join(alerts)}")
            stock_data['last_price'] = current_price
            stock_data['last_volume'] = current_volume
            stock_data['last_program_ratio'] = program_ratio
            stock_data['last_member_ratio'] = member_ratio
        except Exception as e:
            logging.error(f"종목 체크 중 오류 발생 ({code}): {e}")

    def process_condition_stocks(self):
        """조건검색식 종목들을 처리합니다 (장시간과 관계없이 실행)"""
        logging.debug("Starting process_condition_stocks")
        try:
            # pykis의 조건검색식 모듈 사용
            condition_stocks_dict = get_condition_stocks_dict(self.agent)
            if not condition_stocks_dict:
                logging.warning("조건검색식 종목이 없습니다.")
                return
            
            # 모든 조건검색식 종목을 하나의 리스트로 합치기
            all_condition_stocks = []
            for condition_name, stocks in condition_stocks_dict.items():
                logging.debug(f"조건검색식 '{condition_name}'에서 {len(stocks)}개 종목 발견")
                for stock in stocks:
                    # 종목 정보 표준화
                    standardized_stock = {
                        'hts_kor_isnm': stock.get('name', stock.get('종목명', 'N/A')),
                        'stck_shrn_iscd': stock.get('code', stock.get('종목코드', '')),
                        'mksc_shrn_iscd': stock.get('code', stock.get('종목코드', '')),
                        'condition_name': condition_name,  # 어떤 조건검색식에서 나온 종목인지 표시
                        'market': 'KOSPI/KOSDAQ'  # 기본값
                    }
                    all_condition_stocks.append(standardized_stock)
            
            if not all_condition_stocks:
                logging.warning("처리할 조건검색식 종목이 없습니다.")
                return
            
            logging.debug(f"총 {len(all_condition_stocks)}개 조건검색식 종목을 처리합니다.")
            
            # 외국인소진율 필터링 적용 (20% 이상만 통과)
            foreign_filtered_stocks = []
            for stock in all_condition_stocks:
                code = stock.get('stck_shrn_iscd') or stock.get('mksc_shrn_iscd')
                name = stock.get('hts_kor_isnm', 'N/A')
                
                if not code:
                    logging.warning(f"[{name}] 종목코드가 없어 외국인소진율 확인 불가")
                    continue
                
                try:
                    # inquire-price 엔드포인트로 외국인소진율 확인
                    price_data = self.agent.get_stock_price(code)
                    if price_data and price_data.get('rt_cd') == '0':
                        output = price_data.get('output', {})
                        foreign_exhaustion_rate = output.get('hts_frgn_ehrt', '0')
                        
                        # 문자열을 float로 변환
                        try:
                            foreign_rate = float(foreign_exhaustion_rate)
                        except (ValueError, TypeError):
                            logging.warning(f"[{name}] 외국인소진율 변환 실패: {foreign_exhaustion_rate}")
                            continue
                        
                        # 20% 이상인 종목만 통과
                        if foreign_rate >= 20.0:
                            stock['foreign_exhaustion_rate'] = foreign_rate  # 외국인소진율 정보 추가
                            foreign_filtered_stocks.append(stock)
                            logging.debug(f"[{name}] 외국인소진율 {foreign_rate:.2f}% - 통과")
                        else:
                            logging.debug(f"[{name}] 외국인소진율 {foreign_rate:.2f}% - 필터링됨")
                    else:
                        logging.warning(f"[{name}] 가격 정보 조회 실패")
                        continue
                        
                except Exception as e:
                    logging.warning(f"[{name}] 외국인소진율 확인 중 오류: {e}")
                    continue
            
            if not foreign_filtered_stocks:
                logging.warning("외국인소진율 필터링 후 처리할 종목이 없습니다.")
                return
            
            logging.debug(f"외국인소진율 필터링 후 {len(foreign_filtered_stocks)}개 종목을 처리합니다.")
            
            # 병렬 처리로 종목 분석
            self.process_stocks_in_parallel(foreign_filtered_stocks)
            logging.debug("Finished process_condition_stocks.")
            
        except Exception as e:
            logging.error(f"Error in process_condition_stocks: {e}", exc_info=True)
            return

    def run(self) -> None:
        """
        모니터링 실행
        """
        logging.info("주식 모니터링 시작")
        try:
            while True:
                current_time = datetime.now()
                for code in list(self.monitored_stocks.keys()):
                    if (current_time - self.last_check_time[code]).total_seconds() >= self.monitored_stocks[code]['interval']:
                        self.check_stock(code)
                        self.last_check_time[code] = current_time
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("주식 모니터링 종료")
        except Exception as e:
            logging.error(f"모니터링 중 오류 발생: {e}")
            raise

def main():
    """
    메인 함수
    """
    monitor = StockMonitor()
    
    # 모니터링할 종목 추가
    monitor.add_stock("005930", "삼성전자", 60)  # 1분 간격
    monitor.add_stock("035720", "카카오", 300)   # 5분 간격
    
    # 모니터링 시작
    monitor.run()

if __name__ == "__main__":
    main()