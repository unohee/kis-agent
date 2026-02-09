import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from pykis.core.agent import Agent
from pykis.core.config import KISConfig as Config

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("stock_monitor.log")],
)


class StockMonitor:
    def __init__(self):
        """
        주식 모니터링 클래스 초기화
        """
        self.config = Config()
        self.agent = Agent(self.config)
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
            "name": name,
            "interval": interval,
            "last_price": None,
            "last_volume": None,
            "last_program_ratio": None,
            "last_member_ratio": None,
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
            name = self.monitored_stocks[code]["name"]
            del self.monitored_stocks[code]
            del self.last_check_time[code]
            logging.info(f"종목 제거: {name}({code})")

    def get_stock_price(self, code: str) -> Optional[Dict]:
        """
        현재가 조회

        Args:
            code (str): 종목 코드

        Returns:
            Optional[Dict]: 현재가 정보
        """
        try:
            return self.agent.get_stock_price(code)
        except Exception as e:
            logging.error(f"현재가 조회 실패 ({code}): {e}")
            return None

    def get_daily_price(self, code: str) -> Optional[Dict]:
        """
        일별 시세 조회

        Args:
            code (str): 종목 코드

        Returns:
            Optional[Dict]: 일별 시세 정보
        """
        try:
            return self.agent.get_daily_price(code)
        except Exception as e:
            logging.error(f"일별 시세 조회 실패 ({code}): {e}")
            return None

    def get_program_trade_summary(self, code: str) -> Optional[Dict]:
        """
        프로그램 매매 요약 조회

        Args:
            code (str): 종목 코드

        Returns:
            Optional[Dict]: 프로그램 매매 요약 정보
        """
        try:
            return self.agent.get_program_trade_summary(code)
        except Exception as e:
            logging.error(f"프로그램 매매 요약 조회 실패 ({code}): {e}")
            return None

    def get_member_transaction(
        self, code: str, mem_code: str = "99999"
    ) -> Optional[Dict]:
        """
        회원사 매매 정보 조회

        Args:
            code (str): 종목 코드
            mem_code (str): 회원사 코드

        Returns:
            Optional[Dict]: 회원사 매매 정보
        """
        try:
            return self.agent.get_member_transaction(code, mem_code)
        except Exception as e:
            logging.error(f"회원사 매매 정보 조회 실패 ({code}): {e}")
            return None

    def get_volume_ratio(self, code: str) -> Optional[float]:
        """
        거래량 급증도 계산

        Args:
            code (str): 종목 코드

        Returns:
            Optional[float]: 거래량 급증도
        """
        try:
            daily_price = self.get_daily_price(code)
            if not daily_price or "output" not in daily_price:
                return None

            output = daily_price["output"]
            if not output:
                return None

            # 최근 20일 거래량 평균
            volumes = [float(item["acml_vol"]) for item in output[:20]]
            avg_volume = sum(volumes) / len(volumes)
            current_volume = float(output[0]["acml_vol"])

            return current_volume / avg_volume if avg_volume > 0 else 0
        except Exception as e:
            logging.error(f"거래량 급증도 계산 실패 ({code}): {e}")
            return None

    def check_stock(self, code: str) -> None:
        """
        종목 모니터링 체크

        Args:
            code (str): 종목 코드
        """
        try:
            # 현재가 조회
            price_info = self.get_stock_price(code)
            if not price_info or "output" not in price_info:
                return

            current_price = float(price_info["output"]["stck_prpr"])
            current_volume = float(price_info["output"]["acml_vol"])

            # 프로그램 매매 비중 조회
            program_info = self.get_program_trade_summary(code)
            program_ratio = 0.0
            if program_info and "output" in program_info:
                program_ratio = float(program_info["output"]["pgm_rat"]) / 100

            # 회원사 매매 비중 조회
            member_info = self.get_member_transaction(code)
            member_ratio = 0.0
            if member_info and "output" in member_info:
                member_ratio = float(member_info["output"]["mem_rat"]) / 100

            # 이전 데이터와 비교
            stock_data = self.monitored_stocks[code]
            if stock_data["last_price"] is not None:
                price_change = (
                    abs(current_price - stock_data["last_price"])
                    / stock_data["last_price"]
                )
                volume_change = (
                    current_volume / stock_data["last_volume"]
                    if stock_data["last_volume"] > 0
                    else 0
                )

                # 알림 조건 체크
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

            # 데이터 업데이트
            stock_data["last_price"] = current_price
            stock_data["last_volume"] = current_volume
            stock_data["last_program_ratio"] = program_ratio
            stock_data["last_member_ratio"] = member_ratio

        except Exception as e:
            logging.error(f"종목 체크 중 오류 발생 ({code}): {e}")

    def run(self) -> None:
        """
        모니터링 실행
        """
        logging.info("주식 모니터링 시작")
        try:
            while True:
                current_time = datetime.now()
                for code in list(self.monitored_stocks.keys()):
                    if (
                        current_time - self.last_check_time[code]
                    ).total_seconds() >= self.monitored_stocks[code]["interval"]:
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
    monitor.add_stock("035720", "카카오", 300)  # 5분 간격

    # 모니터링 시작
    monitor.run()


if __name__ == "__main__":
    main()
