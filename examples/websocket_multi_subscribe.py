"""
다중 구독 웹소켓 예제
WSAgent를 활용한 실시간 시세 수신
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis.core.client import KISClient
from pykis.websocket.enhanced_client import EnhancedWebSocketClient

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class MarketMonitor:
    """시장 모니터링 클래스"""

    def __init__(self, ws_client: EnhancedWebSocketClient):
        self.ws_client = ws_client
        self.trade_count = 0
        self.last_display_time = datetime.now()

    def on_stock_trade(self, data: dict):
        """주식 체결 콜백"""
        self.trade_count += 1

        # 1초마다 화면 업데이트
        now = datetime.now()
        if (now - self.last_display_time).total_seconds() >= 1:
            self.display_market_status()
            self.last_display_time = now

    def on_index_update(self, data: dict):
        """지수 업데이트 콜백"""
        print(
            f"[지수] {data['name']}: {data['value']:,.2f} ({data['change_rate']:+.2f}%)"
        )

    def on_ask_bid_update(self, data: dict):
        """호가 업데이트 콜백"""
        code = data["code"]
        name = data["name"]

        # 매도/매수 1호가만 표시
        sell1 = data["sell_prices"][0]
        buy1 = data["buy_prices"][0]
        spread = sell1 - buy1

        print(
            f"[호가] {name}({code}): 매도1 {sell1:,.0f} | 매수1 {buy1:,.0f} | 스프레드 {spread:,.0f}"
        )

    def on_program_trade(self, data: dict):
        """프로그램매매 콜백"""
        code = data["code"]
        name = data["name"]
        net_volume = data["net_volume"]
        net_amount = data["net_amount"]

        if abs(net_amount) > 1_000_000_000:  # 10억 이상만 표시
            print(
                f"[프로그램] {name}({code}): 순매수 {net_volume:,}주 / {net_amount/100_000_000:,.1f}억"
            )

    def display_market_status(self):
        """시장 상태 표시"""
        os.system("cls" if os.name == "nt" else "clear")

        print("=" * 80)
        print(f"실시간 시장 모니터링 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # 시장 요약
        summary = self.ws_client.get_market_summary()

        # 지수 정보
        print("\n[주요 지수]")
        for name, data in summary["indices"].items():
            print(f"  {name}: {data['value']:,.2f} ({data['change_rate']:+.2f}%)")

        # 종목 정보
        print("\n[감시 종목]")
        print(
            f"{'종목명':<12} {'현재가':>10} {'등락률':>8} {'거래량':>12} {'체결강도':>8}"
        )
        print("-" * 60)

        for _code, data in summary["stocks"].items():
            print(
                f"{data['name']:<12} {data['price']:>10,.0f} {data['change_rate']:>7.2f}% "
                f"{data['volume']:>12,} {data['strength']:>7.1f}%"
            )

        # 통계
        stats = self.ws_client.get_stats()
        print("\n[통계]")
        print(f"  수신 메시지: {stats['messages_received']:,}")
        print(f"  처리 메시지: {stats['messages_processed']:,}")
        print(f"  에러: {stats['errors']:,}")
        print(f"  재연결: {stats['reconnects']:,}")
        print(f"  활성 구독: {stats['total_subscriptions']}")

        print("\nESC 키를 누르면 종료합니다...")


async def main():
    """메인 함수"""

    # 환경변수 또는 설정 파일에서 인증 정보 로드
    from dotenv import load_dotenv

    load_dotenv()

    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    account_number = os.getenv("KIS_ACCOUNT_NUMBER")

    if not all([app_key, app_secret, account_number]):
        print(
            "환경변수를 설정해주세요: KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NUMBER"
        )
        return

    # 클라이언트 초기화
    client = KISClient(
        app_key=app_key,
        app_secret=app_secret,
        account_number=account_number,
        is_real=True,  # 실전투자
    )

    account_info = {"CANO": account_number[:8], "ACNT_PRDT_CD": account_number[8:]}

    # 감시할 종목 설정
    stock_codes = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "035420",  # NAVER
        "035720",  # 카카오
        "051910",  # LG화학
    ]

    # 웹소켓 클라이언트 생성
    ws_client = EnhancedWebSocketClient(
        client=client,
        account_info=account_info,
        stock_codes=stock_codes,
        enable_index=True,  # 지수 구독
        enable_program_trading=True,  # 프로그램매매 구독
        enable_ask_bid=True,  # 호가 구독
        enable_futures=False,  # 선물 미구독
        enable_options=False,  # 옵션 미구독
    )

    # 모니터 생성
    monitor = MarketMonitor(ws_client)

    # 콜백 등록
    ws_client.register_callback("on_trade", monitor.on_stock_trade)
    ws_client.register_callback("on_index", monitor.on_index_update)
    ws_client.register_callback("on_ask_bid", monitor.on_ask_bid_update)
    ws_client.register_callback("on_program", monitor.on_program_trade)

    # 종료 핸들러
    async def handle_exit():
        """ESC 키 감지 및 종료 처리"""
        try:
            import msvcrt

            while True:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b"\x1b":  # ESC
                        print("\n종료 중...")
                        await ws_client.stop()
                        return
                await asyncio.sleep(0.1)
        except ImportError:
            # Windows가 아닌 경우
            import select
            import sys

            while True:
                dr, dw, de = select.select([sys.stdin], [], [], 0)
                if dr:
                    ch = sys.stdin.read(1)
                    if ch == "\x1b":  # ESC
                        print("\n종료 중...")
                        await ws_client.stop()
                        return
                await asyncio.sleep(0.1)

    try:
        # 웹소켓 시작
        print("웹소켓 연결 중...")

        # 두 태스크를 동시에 실행
        ws_task = asyncio.create_task(ws_client.start())
        exit_task = asyncio.create_task(handle_exit())

        # 둘 중 하나가 완료되면 종료
        done, pending = await asyncio.wait(
            [ws_task, exit_task], return_when=asyncio.FIRST_COMPLETED
        )

        # 남은 태스크 취소
        for task in pending:
            task.cancel()

    except KeyboardInterrupt:
        print("\n키보드 인터럽트 감지")

    finally:
        await ws_client.stop()
        print("프로그램 종료")


if __name__ == "__main__":
    asyncio.run(main())
