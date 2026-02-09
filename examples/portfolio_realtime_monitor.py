#!/usr/bin/env python3
"""
포트폴리오 실시간 모니터링 모듈

기능:
- 계좌 잔고 조회 후 보유 종목 자동 추출
- 보유 종목들의 실시간 시세 모니터링 (웹소켓)
- VWAP 이격률 실시간 계산
- 프로그램 매매 실시간 모니터링
- 종합 대시보드 표시
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import websockets

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import Agent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("portfolio_monitor.log")],
)


@dataclass
class StockPosition:
    """보유 종목 정보"""

    code: str
    name: str
    quantity: int
    avg_price: float
    current_price: float = 0.0
    vwap: float = 0.0
    vwap_deviation: float = 0.0
    program_buy_ratio: float = 0.0
    program_sell_ratio: float = 0.0
    program_net_ratio: float = 0.0
    volume: int = 0
    market_value: float = 0.0
    profit_loss: float = 0.0
    profit_loss_rate: float = 0.0


class PortfolioRealtimeMonitor:
    """포트폴리오 실시간 모니터링 클래스"""

    def __init__(self, refresh_balance_interval: int = 300):
        """
        초기화

        Args:
            refresh_balance_interval: 잔고 새로고침 간격 (초, 기본값: 5분)
        """
        self.agent = Agent()
        self.positions: Dict[str, StockPosition] = {}
        self.ws_client = None
        self.refresh_balance_interval = refresh_balance_interval
        self.last_balance_refresh = datetime.now() - timedelta(
            seconds=refresh_balance_interval
        )

        # VWAP 계산을 위한 데이터 저장소
        self.price_volume_data: Dict[str, List[Tuple[float, int, datetime]]] = {}
        self.vwap_window_minutes = 60  # VWAP 계산 윈도우 (분)

        # 실시간 데이터 저장소
        self.realtime_data: Dict[str, Dict] = {}
        self.program_trade_data: Dict[str, Dict] = {}

        logging.info("포트폴리오 실시간 모니터링 시스템 초기화 완료")

    async def initialize_portfolio(self) -> bool:
        """포트폴리오 초기화 (잔고 조회 및 종목 등록)"""
        try:
            logging.info(" 계좌 잔고 조회 중...")
            balance = self.agent.get_account_balance()

            if not balance or "output1" not in balance:
                logging.error(" 잔고 조회 실패")
                return False

            positions = balance["output1"]
            self.positions.clear()

            for position in positions:
                code = position.get("pdno", "")
                name = position.get("prdt_name", "")
                quantity = int(position.get("hldg_qty", 0))
                avg_price = float(position.get("pchs_avg_pric", 0))

                # 보유 수량이 있는 종목만 등록
                if quantity > 0 and code:
                    self.positions[code] = StockPosition(
                        code=code, name=name, quantity=quantity, avg_price=avg_price
                    )

                    # 가격-거래량 데이터 초기화
                    self.price_volume_data[code] = []

                    logging.info(
                        f" 종목 등록: {name}({code}) - {quantity:,}주 @ {avg_price:,}원"
                    )

            logging.info(f" 총 {len(self.positions)}개 종목 등록 완료")
            return True

        except Exception as e:
            logging.error(f" 포트폴리오 초기화 실패: {e}")
            return False

    async def fetch_historical_minute_data(self, code: str) -> None:
        """분봉 데이터로 VWAP 초기값 설정"""
        try:
            # 당일 분봉 데이터 조회
            minute_data = self.agent.fetch_minute_data(code)

            if minute_data is not None and not minute_data.empty:
                current_time = datetime.now()
                cutoff_time = current_time - timedelta(minutes=self.vwap_window_minutes)

                for _, row in minute_data.iterrows():
                    try:
                        # 시간 파싱 (stck_cntg_hour가 YYYYMMDDHHMMSS 형태)
                        time_str = str(row["stck_cntg_hour"])
                        if len(time_str) >= 14:
                            data_time = datetime.strptime(time_str, "%Y%m%d%H%M%S")

                            if data_time >= cutoff_time:
                                price = float(row["stck_prpr"])
                                volume = int(row["cntg_vol"])

                                if volume > 0:  # 거래량이 있는 데이터만
                                    self.price_volume_data[code].append(
                                        (price, volume, data_time)
                                    )
                    except Exception:
                        continue

                logging.info(
                    f" {code} 과거 분봉 데이터 {len(self.price_volume_data[code])}건 로드"
                )

        except Exception as e:
            logging.warning(f" {code} 과거 분봉 데이터 로드 실패: {e}")

    def calculate_vwap(self, code: str) -> float:
        """VWAP (거래량 가중 평균가) 계산"""
        try:
            if code not in self.price_volume_data:
                return 0.0

            current_time = datetime.now()
            cutoff_time = current_time - timedelta(minutes=self.vwap_window_minutes)

            # 윈도우 내 데이터만 필터링
            valid_data = [
                (price, volume)
                for price, volume, timestamp in self.price_volume_data[code]
                if timestamp >= cutoff_time
            ]

            if not valid_data:
                return 0.0

            total_value = sum(price * volume for price, volume in valid_data)
            total_volume = sum(volume for _, volume in valid_data)

            return total_value / total_volume if total_volume > 0 else 0.0

        except Exception as e:
            logging.error(f" {code} VWAP 계산 실패: {e}")
            return 0.0

    def calculate_vwap_deviation(
        self, code: str, current_price: float, vwap: float
    ) -> float:
        """VWAP 이격률 계산 (%)"""
        if vwap <= 0:
            return 0.0
        return ((current_price - vwap) / vwap) * 100

    async def setup_websocket(self) -> bool:
        """웹소켓 연결 설정"""
        try:
            if not self.positions:
                logging.error(" 등록된 종목이 없습니다")
                return False

            stock_codes = list(self.positions.keys())

            # 웹소켓 클라이언트 생성
            self.ws_client = self.agent.websocket(
                stock_codes=stock_codes,
                enable_index=False,  # 지수는 필요 없음
                enable_program_trading=True,  # 프로그램 매매 활성화
                enable_ask_bid=False,  # 호가는 비활성화
            )

            logging.info(" 웹소켓 클라이언트 생성 완료")

            # 승인키 발급
            approval_key = self.ws_client.get_approval()
            if not approval_key:
                logging.error(" 웹소켓 승인키 발급 실패")
                return False

            logging.info("🔑 웹소켓 승인키 발급 완료")
            return True

        except Exception as e:
            logging.error(f" 웹소켓 설정 실패: {e}")
            return False

    async def start_realtime_monitoring(self) -> None:
        """실시간 모니터링 시작"""
        try:
            if not self.ws_client:
                logging.error(" 웹소켓 클라이언트가 설정되지 않았습니다")
                return

            # 모든 종목의 과거 분봉 데이터 로드
            logging.info(" 과거 분봉 데이터 로드 중...")
            for code in self.positions:
                await self.fetch_historical_minute_data(code)

            approval_key = self.ws_client.get_approval()

            async with websockets.connect(
                self.ws_client.url, ping_interval=30, ping_timeout=30
            ) as websocket:
                self.ws_client.ws = websocket

                # 종목별 구독 요청
                for stock_code in self.positions:
                    # 체결정보 구독
                    await self._subscribe_stock_trade(
                        websocket, approval_key, stock_code
                    )

                    # 프로그램매매 구독
                    await self._subscribe_program_trade(
                        websocket, approval_key, stock_code
                    )

                    await asyncio.sleep(0.1)  # 요청 간격

                logging.info(" 실시간 모니터링 시작")
                await self._start_monitoring_loop(websocket)

        except Exception as e:
            logging.error(f" 실시간 모니터링 실행 실패: {e}")

    async def _subscribe_stock_trade(
        self, websocket, approval_key: str, stock_code: str
    ) -> None:
        """종목 체결정보 구독"""
        senddata = {
            "header": {
                "approval_key": approval_key,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8",
            },
            "body": {"input": {"tr_id": "H0STCNT0", "tr_key": stock_code}},
        }
        await websocket.send(json.dumps(senddata))

    async def _subscribe_program_trade(
        self, websocket, approval_key: str, stock_code: str
    ) -> None:
        """프로그램매매 구독"""
        senddata = {
            "header": {
                "approval_key": approval_key,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8",
            },
            "body": {"input": {"tr_id": "H0GSCNT0", "tr_key": stock_code}},
        }
        await websocket.send(json.dumps(senddata))

    async def _start_monitoring_loop(self, websocket) -> None:
        """모니터링 루프"""
        last_display_time = datetime.now()
        display_interval = 5  # 5초마다 화면 갱신

        try:
            while True:
                # 웹소켓 메시지 수신
                try:
                    data = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    await self._process_websocket_message(data)
                except asyncio.TimeoutError:
                    pass

                # 주기적으로 잔고 새로고침
                await self._refresh_balance_if_needed()

                # 주기적으로 화면 갱신
                now = datetime.now()
                if (now - last_display_time).total_seconds() >= display_interval:
                    self._display_portfolio_status()
                    last_display_time = now

                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            logging.info("🛑 사용자에 의해 모니터링 중단")
        except Exception as e:
            logging.error(f" 모니터링 루프 오류: {e}")

    async def _process_websocket_message(self, data: str) -> None:
        """웹소켓 메시지 처리"""
        try:
            if "PINGPONG" in data or "SUBSCRIBE SUCCESS" in data:
                return

            if data.startswith("0|H0STCNT0"):
                # 체결 데이터 처리
                await self._process_trade_data(data)
            elif data.startswith("0|H0GSCNT0"):
                # 프로그램매매 데이터 처리
                await self._process_program_trade_data(data)

        except Exception as e:
            logging.error(f" 웹소켓 메시지 처리 실패: {e}")

    async def _process_trade_data(self, data: str) -> None:
        """체결 데이터 처리"""
        try:
            parts = data.split("|")
            if len(parts) < 4:
                return

            trade_data = parts[3].split("^")
            if len(trade_data) < 20:
                return

            stock_code = trade_data[0]
            current_price = float(trade_data[2])
            volume = int(trade_data[10]) if trade_data[10] else 0

            if stock_code in self.positions and volume > 0:
                # 가격-거래량 데이터 추가
                current_time = datetime.now()
                self.price_volume_data[stock_code].append(
                    (current_price, volume, current_time)
                )

                # 오래된 데이터 정리 (윈도우 밖 데이터 제거)
                cutoff_time = current_time - timedelta(minutes=self.vwap_window_minutes)
                self.price_volume_data[stock_code] = [
                    (p, v, t)
                    for p, v, t in self.price_volume_data[stock_code]
                    if t >= cutoff_time
                ]

                # 포지션 업데이트
                position = self.positions[stock_code]
                position.current_price = current_price
                position.volume = volume
                position.vwap = self.calculate_vwap(stock_code)
                position.vwap_deviation = self.calculate_vwap_deviation(
                    stock_code, current_price, position.vwap
                )
                position.market_value = position.quantity * current_price
                position.profit_loss = position.market_value - (
                    position.quantity * position.avg_price
                )
                position.profit_loss_rate = (
                    position.profit_loss / (position.quantity * position.avg_price)
                ) * 100

        except Exception as e:
            logging.error(f" 체결 데이터 처리 실패: {e}")

    async def _process_program_trade_data(self, data: str) -> None:
        """프로그램매매 데이터 처리"""
        try:
            parts = data.split("|")
            if len(parts) < 4:
                return

            program_data = parts[3].split("^")
            if len(program_data) < 10:
                return

            stock_code = program_data[0]

            # 프로그램매매 데이터는 별도 처리 필요
            if stock_code in self.positions:
                pass

        except Exception as e:
            logging.error(f" 프로그램매매 데이터 처리 실패: {e}")

    async def _refresh_balance_if_needed(self) -> None:
        """필요시 잔고 새로고침"""
        now = datetime.now()
        if (
            now - self.last_balance_refresh
        ).total_seconds() >= self.refresh_balance_interval:
            await self.initialize_portfolio()
            self.last_balance_refresh = now

    def _display_portfolio_status(self) -> None:
        """포트폴리오 현황 표시"""
        os.system("cls" if os.name == "nt" else "clear")

        print("=" * 120)
        print("💼 포트폴리오 실시간 모니터링 대시보드")
        print(f" 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 120)

        if not self.positions:
            print("📭 보유 종목이 없습니다.")
            return

        # 헤더
        print(
            f"{'종목명':<12} {'현재가':>10} {'매입가':>10} {'손익률':>8} {'VWAP':>10} {'이격률':>8} {'프로그램':>8} {'거래량':>10}"
        )
        print("-" * 120)

        total_investment = 0
        total_market_value = 0

        for position in self.positions.values():
            total_investment += position.quantity * position.avg_price
            total_market_value += position.market_value

            vwap_str = f"{position.vwap:,.0f}" if position.vwap > 0 else "-"
            deviation_str = (
                f"{position.vwap_deviation:+.2f}%"
                if position.vwap_deviation != 0
                else "-"
            )
            program_str = (
                f"{position.program_net_ratio:+.2f}%"
                if hasattr(position, "program_net_ratio")
                else "-"
            )
            volume_str = f"{position.volume:,}" if position.volume > 0 else "-"

            print(
                f"{position.name:<12} "
                f"{position.current_price:>10,.0f} "
                f"{position.avg_price:>10,.0f} "
                f"{position.profit_loss_rate:>+7.2f}% "
                f"{vwap_str:>10} "
                f"{deviation_str:>8} "
                f"{program_str:>8} "
                f"{volume_str:>10}"
            )

        # 종합 현황
        total_profit_loss = total_market_value - total_investment
        total_profit_loss_rate = (
            (total_profit_loss / total_investment * 100) if total_investment > 0 else 0
        )

        print("-" * 120)
        print(f" 총 투자금액: {total_investment:>15,.0f}원")
        print(f"💎 총 평가금액: {total_market_value:>15,.0f}원")
        print(
            f" 총 손익금액: {total_profit_loss:>+15,.0f}원 ({total_profit_loss_rate:+.2f}%)"
        )
        print("=" * 120)

    async def run(self) -> None:
        """메인 실행 함수"""
        try:
            logging.info(" 포트폴리오 실시간 모니터링 시작")

            # 1. 포트폴리오 초기화
            if not await self.initialize_portfolio():
                return

            # 2. 웹소켓 설정
            if not await self.setup_websocket():
                return

            # 3. 실시간 모니터링 시작
            await self.start_realtime_monitoring()

        except Exception as e:
            logging.error(f" 실행 실패: {e}")
        finally:
            logging.info("🛑 포트폴리오 모니터링 종료")


async def main():
    """메인 함수"""
    print(" 포트폴리오 실시간 모니터링 시스템")
    print("기능:")
    print("- 계좌 잔고 자동 조회")
    print("- 보유 종목 실시간 시세 모니터링")
    print("- VWAP 이격률 실시간 계산")
    print("- 프로그램 매매 모니터링")
    print()

    monitor = PortfolioRealtimeMonitor(
        refresh_balance_interval=300
    )  # 5분마다 잔고 새로고침
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
