import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pykis import Agent

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
    def __init__(self):
        """
        주식 모니터링 클래스 초기화 (pykis Agent 사용)
        """
        # pykis Agent를 사용하여 간단하게 초기화
        self.agent = Agent()
        self.monitored_stocks: Dict[str, Dict] = {}
        self.last_check_time: Dict[str, datetime] = {}
        self.check_interval = 60  # 기본 체크 간격 (초)
        self.volume_threshold = 2.0  # 거래량 급증 기준 (배)
        self.price_change_threshold = 0.03  # 가격 변동 기준 (3%)
        self.program_trade_threshold = 0.5  # 프로그램 매매 비중 기준 (50%)
        self.member_trade_threshold = 0.3  # 회원사 매매 비중 기준 (30%)
        self.foreign_exhaustion_threshold = 20.0  # 외국인소진율 기준 (20%)

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

    def get_stock_data(self, code: str) -> Optional[Dict]:
        """
        종목의 현재가 정보 조회 (pykis Agent 사용)
        """
        try:
            return self.agent.get_stock_price(code)
        except Exception as e:
            logging.error(f"현재가 조회 실패 ({code}): {e}")
            return None

    def get_daily_data(self, code: str) -> Optional[Dict]:
        """
        종목의 일별 시세 조회 (pykis Agent 사용)
        """
        try:
            return self.agent.get_daily_price(code)
        except Exception as e:
            logging.error(f"일별 시세 조회 실패 ({code}): {e}")
            return None

    def get_program_trade_data(self, code: str) -> Optional[Dict]:
        """
        프로그램 매매 정보 조회 (pykis Agent 사용)
        """
        try:
            return self.agent.get_program_trade_by_stock(code)
        except Exception as e:
            logging.error(f"프로그램 매매 정보 조회 실패 ({code}): {e}")
            return None

    def get_member_data(self, code: str) -> Optional[Dict]:
        """
        회원사 거래 정보 조회 (pykis Agent 사용)
        """
        try:
            return self.agent.get_member(code)
        except Exception as e:
            logging.error(f"회원사 정보 조회 실패 ({code}): {e}")
            return None

    def calculate_volume_ratio(self, code: str) -> Optional[float]:
        """
        거래량 급증도 계산
        """
        try:
            daily_data = self.get_daily_data(code)
            if not daily_data or 'output' not in daily_data:
                return None

            output = daily_data['output']
            if len(output) < 2:
                return None

            # 최근 20일 평균 거래량 계산
            volumes = [float(item['acml_vol']) for item in output[:20] if item.get('acml_vol')]
            if not volumes:
                return None

            avg_volume = sum(volumes) / len(volumes)
            current_volume = float(output[0]['acml_vol'])

            return current_volume / avg_volume if avg_volume > 0 else 0
        except Exception as e:
            logging.error(f"거래량 급증도 계산 실패 ({code}): {e}")
            return None

    def check_stock(self, code: str) -> None:
        """
        단일 종목 체크 (pykis Agent 사용)
        """
        try:
            # 현재가 정보 조회
            price_data = self.get_stock_data(code)
            if not price_data or 'output' not in price_data:
                return

            output = price_data['output']
            current_price = float(output['stck_prpr'])
            current_volume = float(output['acml_vol'])

            # 프로그램 매매 정보 조회
            program_data = self.get_program_trade_data(code)
            program_ratio = 0.0
            if program_data and 'output' in program_data and program_data['output']:
                # 프로그램 매매 비중 계산 (매수+매도 거래량 대비)
                pgm_buy = float(program_data['output'][0].get('prdy_pgm_buy_vol', 0))
                pgm_sell = float(program_data['output'][0].get('prdy_pgm_sell_vol', 0))
                total_vol = float(output['acml_vol'])
                if total_vol > 0:
                    program_ratio = (pgm_buy + pgm_sell) / total_vol

            # 기존 데이터와 비교하여 알림 조건 체크
            stock_data = self.monitored_stocks[code]
            alerts = []

            if stock_data['last_price'] is not None:
                # 가격 변동률 계산
                price_change = abs(current_price - stock_data['last_price']) / stock_data['last_price']
                if price_change >= self.price_change_threshold:
                    alerts.append(f"가격 변동: {price_change:.1%}")

                # 거래량 급증도 계산
                if stock_data['last_volume'] is not None and stock_data['last_volume'] > 0:
                    volume_change = current_volume / stock_data['last_volume']
                    if volume_change >= self.volume_threshold:
                        alerts.append(f"거래량 급증: {volume_change:.1f}배")

                # 프로그램 매매 비중 체크
                if program_ratio >= self.program_trade_threshold:
                    alerts.append(f"프로그램 매매 비중: {program_ratio:.1%}")

                # 알림 출력
                if alerts:
                    name = stock_data['name']
                    logging.info(f" 종목 알림 [{name}({code})]: {', '.join(alerts)}")

            # 데이터 업데이트
            stock_data['last_price'] = current_price
            stock_data['last_volume'] = current_volume
            stock_data['last_program_ratio'] = program_ratio

        except Exception as e:
            logging.error(f"종목 체크 중 오류 발생 ({code}): {e}")

    def process_condition_stocks(self) -> List[Dict]:
        """
        조건검색식 종목들을 처리합니다 (pykis Agent 사용)
        """
        try:
            logging.info(" 조건검색 종목 처리 시작")

            # pykis Agent를 사용한 조건검색 (통일된 방식)
            condition_result = self.agent.get_condition_stocks("unohee", 0, "N")

            # [수정] condition API는 직접 List를 반환하므로 'output' 필드 확인 불필요
            if not condition_result:
                logging.warning("조건검색 결과가 없습니다.")
                return []

            stocks = condition_result  # [수정] 직접 리스트 사용
            if not stocks:
                logging.warning("조건검색된 종목이 없습니다.")
                return []

            logging.info(f"조건검색에서 {len(stocks)}개 종목 발견")

            # 외국인소진율 필터링
            filtered_stocks = []
            for stock in stocks:
                code = stock.get('stck_shrn_iscd', '')
                name = stock.get('hts_kor_isnm', 'N/A')

                if not code:
                    continue

                # 현재가 정보에서 외국인소진율 확인
                price_data = self.get_stock_data(code)
                if price_data and 'output' in price_data:
                    foreign_rate_str = price_data['output'].get('hts_frgn_ehrt', '0')
                    try:
                        foreign_rate = float(foreign_rate_str)
                        if foreign_rate >= self.foreign_exhaustion_threshold:
                            stock['foreign_exhaustion_rate'] = foreign_rate
                            filtered_stocks.append(stock)
                            logging.info(f" [{name}({code})] 외국인소진율 {foreign_rate:.1f}% - 통과")
                        else:
                            logging.debug(f" [{name}({code})] 외국인소진율 {foreign_rate:.1f}% - 필터링")
                    except (ValueError, TypeError):
                        logging.warning(f"[{name}({code})] 외국인소진율 변환 실패: {foreign_rate_str}")

            logging.info(f"외국인소진율 필터링 후 {len(filtered_stocks)}개 종목 선별")
            return filtered_stocks

        except Exception as e:
            logging.error(f"조건검색 처리 중 오류: {e}")
            return []

    def analyze_stocks(self, stocks: List[Dict]) -> None:
        """
        선별된 종목들을 분석합니다 (pykis Agent 사용)
        """
        for stock in stocks:
            try:
                code = stock.get('stck_shrn_iscd', '')
                name = stock.get('hts_kor_isnm', 'N/A')
                foreign_rate = stock.get('foreign_exhaustion_rate', 0)

                if not code:
                    continue

                # 현재가 정보
                price_data = self.get_stock_data(code)
                if not price_data or 'output' not in price_data:
                    continue

                output = price_data['output']
                current_price = output.get('stck_prpr', '0')
                change_rate = output.get('prdy_ctrt', '0')
                volume = output.get('acml_vol', '0')

                # 프로그램 매매 정보
                program_data = self.get_program_trade_data(code)
                program_info = ""
                if program_data and 'output' in program_data and program_data['output']:
                    pgm_buy = program_data['output'][0].get('prdy_pgm_buy_vol', '0')
                    pgm_sell = program_data['output'][0].get('prdy_pgm_sell_vol', '0')
                    program_info = f"프로그램매매(매수:{pgm_buy}, 매도:{pgm_sell})"

                # 결과 출력
                logging.info(
                    f" 분석결과 [{name}({code})]: "
                    f"현재가 {current_price}원, 등락률 {change_rate}%, "
                    f"거래량 {volume}, 외국인소진율 {foreign_rate:.1f}%, "
                    f"{program_info}"
                )

            except Exception as e:
                logging.error(f"종목 분석 중 오류 ({code}): {e}")

    def run_monitoring(self) -> None:
        """
        등록된 종목들의 지속적인 모니터링 실행
        """
        logging.info(" 주식 모니터링 시작")
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

    def run_condition_analysis(self) -> None:
        """
        조건검색 기반 종목 분석 실행
        """
        logging.info(" 조건검색 기반 종목 분석 시작")
        try:
            # 조건검색 종목 처리
            condition_stocks = self.process_condition_stocks()

            if condition_stocks:
                # 선별된 종목 분석
                self.analyze_stocks(condition_stocks)
            else:
                logging.info("분석할 조건검색 종목이 없습니다.")

        except Exception as e:
            logging.error(f"조건검색 분석 중 오류: {e}")

def main():
    """
    메인 함수 - pykis를 사용한 주식 모니터링
    """
    monitor = StockMonitor()

    print("=== pykis 기반 주식 모니터링 시스템 ===")
    print("1. 종목 모니터링")
    print("2. 조건검색 분석")
    print("3. 통합 실행")

    choice = input("선택하세요 (1-3): ").strip()

    if choice == "1":
        # 모니터링할 종목 추가
        monitor.add_stock("005930", "삼성전자", 60)  # 1분 간격
        monitor.add_stock("035720", "카카오", 120)   # 2분 간격
        monitor.add_stock("000660", "SK하이닉스", 180)  # 3분 간격

        # 모니터링 시작
        monitor.run_monitoring()

    elif choice == "2":
        # 조건검색 분석 실행
        monitor.run_condition_analysis()

    elif choice == "3":
        # 조건검색 분석 후 주요 종목 모니터링
        condition_stocks = monitor.process_condition_stocks()

        # 조건검색 결과의 상위 3개 종목을 모니터링 추가
        for _i, stock in enumerate(condition_stocks[:3]):
            code = stock.get('stck_shrn_iscd', '')
            name = stock.get('hts_kor_isnm', 'N/A')
            if code:
                monitor.add_stock(code, name, 60)

        # 기본 종목들도 추가
        monitor.add_stock("005930", "삼성전자", 60)

        # 분석 실행
        monitor.analyze_stocks(condition_stocks)

        # 모니터링 시작
        monitor.run_monitoring()
    else:
        print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()
