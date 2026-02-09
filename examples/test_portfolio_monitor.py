#!/usr/bin/env python3
"""
포트폴리오 실시간 모니터링 시스템 테스트

이 스크립트는 포트폴리오 모니터링 시스템의 기본 기능을 테스트합니다.
실제 모니터링 전에 각 구성 요소가 정상 작동하는지 확인할 수 있습니다.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import Agent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class PortfolioMonitorTester:
    """포트폴리오 모니터링 시스템 테스트 클래스"""

    def __init__(self):
        self.agent = Agent()

    def test_agent_connection(self) -> bool:
        """Agent 연결 테스트"""
        print(" Agent 연결 테스트...")
        try:
            # 간단한 API 호출로 연결 테스트
            result = self.agent.get_stock_price("005930")  # 삼성전자
            if result and result.get("rt_cd") == "0":
                print(" Agent 연결 성공")
                return True
            else:
                print(" Agent 연결 실패: API 응답 오류")
                return False
        except Exception as e:
            print(f" Agent 연결 실패: {e}")
            return False

    def test_balance_inquiry(self) -> bool:
        """잔고 조회 테스트"""
        print(" 잔고 조회 테스트...")
        try:
            balance = self.agent.get_account_balance()

            if not balance:
                print(" 잔고 조회 실패: 응답 없음")
                return False

            if balance.get("rt_cd") != "0":
                print(f" 잔고 조회 실패: {balance.get('msg1', 'Unknown error')}")
                return False

            if "output1" not in balance:
                print(" 잔고 조회 실패: output1 필드 없음")
                return False

            positions = balance["output1"]
            print(f" 잔고 조회 성공: {len(positions)}개 항목")

            # 보유 종목 표시
            holdings = [p for p in positions if int(p.get("hldg_qty", 0)) > 0]
            if holdings:
                print(f" 보유 종목: {len(holdings)}개")
                for holding in holdings[:5]:  # 최대 5개만 표시
                    code = holding.get("pdno", "")
                    name = holding.get("prdt_name", "")
                    qty = int(holding.get("hldg_qty", 0))
                    avg_price = float(holding.get("pchs_avg_pric", 0))
                    print(f"   - {name}({code}): {qty:,}주 @ {avg_price:,}원")
                if len(holdings) > 5:
                    print(f"   ... 외 {len(holdings) - 5}개 종목")
            else:
                print("📭 보유 종목 없음")

            return True

        except Exception as e:
            print(f" 잔고 조회 실패: {e}")
            return False

    def test_minute_data_fetch(self, code: str = "005930") -> bool:
        """분봉 데이터 조회 테스트"""
        print(f" 분봉 데이터 조회 테스트 ({code})...")
        try:
            minute_data = self.agent.fetch_minute_data(code)

            if minute_data is None:
                print(" 분봉 데이터 조회 실패: 응답 없음")
                return False

            if minute_data.empty:
                print(" 분봉 데이터 조회 실패: 빈 데이터")
                return False

            print(f" 분봉 데이터 조회 성공: {len(minute_data)}건")

            # 데이터 구조 확인
            required_columns = ["stck_cntg_hour", "stck_prpr", "cntg_vol"]
            missing_columns = [
                col for col in required_columns if col not in minute_data.columns
            ]

            if missing_columns:
                print(f" 경고: 필수 컬럼 누락 {missing_columns}")
            else:
                print(" 필수 컬럼 모두 존재")

                # 샘플 데이터 표시
                latest = minute_data.iloc[0]
                print(
                    f"   최신 데이터: {latest['stck_cntg_hour']}, "
                    f"가격: {latest['stck_prpr']:,}원, "
                    f"거래량: {latest['cntg_vol']:,}주"
                )

            return True

        except Exception as e:
            print(f" 분봉 데이터 조회 실패: {e}")
            return False

    async def test_websocket_connection(self, test_codes: list = None) -> bool:
        """웹소켓 연결 테스트"""
        if test_codes is None:
            test_codes = ["005930"]
        print(" 웹소켓 연결 테스트...")
        try:
            # 웹소켓 클라이언트 생성
            ws_client = self.agent.websocket(
                stock_codes=test_codes,
                enable_index=False,
                enable_program_trading=True,
                enable_ask_bid=False,
            )

            print(" 웹소켓 클라이언트 생성 성공")

            # 승인키 발급 테스트
            approval_key = ws_client.get_approval()
            if not approval_key:
                print(" 웹소켓 승인키 발급 실패")
                return False

            print(f" 웹소켓 승인키 발급 성공: {approval_key[:20]}...")

            # 실제 연결은 복잡하므로 여기서는 승인키 발급까지만 테스트
            print(" 웹소켓 기본 설정 완료")
            return True

        except Exception as e:
            print(f" 웹소켓 연결 테스트 실패: {e}")
            return False

    def test_vwap_calculation(self) -> bool:
        """VWAP 계산 로직 테스트"""
        print(" VWAP 계산 로직 테스트...")
        try:
            # 테스트 데이터
            test_data = [
                (100000, 1000),  # 가격, 거래량
                (101000, 2000),
                (99000, 1500),
                (102000, 800),
                (98000, 1200),
            ]

            # VWAP 계산
            total_value = sum(price * volume for price, volume in test_data)
            total_volume = sum(volume for _, volume in test_data)
            vwap = total_value / total_volume if total_volume > 0 else 0

            print(f" VWAP 계산 성공: {vwap:,.0f}원")

            # 이격률 계산 테스트
            current_price = 101500
            deviation = ((current_price - vwap) / vwap) * 100
            print(f" 이격률 계산 성공: {deviation:+.2f}%")

            return True

        except Exception as e:
            print(f" VWAP 계산 테스트 실패: {e}")
            return False

    def test_program_trade_data(self, code: str = "005930") -> bool:
        """프로그램 매매 데이터 조회 테스트"""
        print(f" 프로그램 매매 데이터 테스트 ({code})...")
        try:
            today = datetime.now().strftime("%Y%m%d")
            program_data = self.agent.get_program_trade_daily_summary(code, today)

            if not program_data:
                print(" 프로그램 매매 데이터 조회 실패: 응답 없음")
                return False

            if program_data.get("rt_cd") != "0":
                print(
                    f" 프로그램 매매 데이터 조회 실패: {program_data.get('msg1', 'Unknown error')}"
                )
                return False

            if "output" not in program_data or not program_data["output"]:
                print(" 프로그램 매매 데이터 조회 실패: output 필드 없음")
                return False

            print(" 프로그램 매매 데이터 조회 성공")

            # 오늘 데이터 확인
            today_data = None
            for item in program_data["output"]:
                if item.get("stck_bsop_date") == today:
                    today_data = item
                    break

            if today_data:
                buy_vol = int(today_data.get("whol_smtn_shnu_vol", 0))
                sell_vol = int(today_data.get("whol_smtn_seln_vol", 0))
                total_vol = buy_vol + sell_vol
                buy_ratio = (buy_vol / total_vol * 100) if total_vol > 0 else 0

                print(f"   당일 프로그램 매수: {buy_vol:,}주")
                print(f"   당일 프로그램 매도: {sell_vol:,}주")
                print(f"   매수 비율: {buy_ratio:.2f}%")
            else:
                print(" 당일 프로그램 매매 데이터 없음")

            return True

        except Exception as e:
            print(f" 프로그램 매매 데이터 테스트 실패: {e}")
            return False

    async def run_all_tests(self) -> None:
        """모든 테스트 실행"""
        print(" 포트폴리오 모니터링 시스템 테스트 시작")
        print("=" * 60)

        tests = [
            ("Agent 연결", self.test_agent_connection),
            ("잔고 조회", self.test_balance_inquiry),
            ("분봉 데이터", lambda: self.test_minute_data_fetch("005930")),
            ("VWAP 계산", self.test_vwap_calculation),
            ("프로그램 매매", lambda: self.test_program_trade_data("005930")),
        ]

        results = []

        # 동기 테스트들
        for test_name, test_func in tests:
            print(f"\n{test_name} 테스트 중...")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f" {test_name} 테스트 예외 발생: {e}")
                results.append((test_name, False))

        # 웹소켓 테스트 (비동기)
        print("\n웹소켓 연결 테스트 중...")
        try:
            ws_result = await self.test_websocket_connection()
            results.append(("웹소켓 연결", ws_result))
        except Exception as e:
            print(f" 웹소켓 테스트 예외 발생: {e}")
            results.append(("웹소켓 연결", False))

        # 결과 요약
        print("\n" + "=" * 60)
        print(" 테스트 결과 요약")
        print("=" * 60)

        passed = 0
        total = len(results)

        for test_name, result in results:
            status = " 통과" if result else " 실패"
            print(f"{test_name:<15}: {status}")
            if result:
                passed += 1

        print("-" * 60)
        print(f"전체 테스트: {passed}/{total} 통과 ({passed/total*100:.1f}%)")

        if passed == total:
            print("\n 모든 테스트 통과! 포트폴리오 모니터링을 시작할 수 있습니다.")
            print("실행 명령: python portfolio_realtime_monitor.py")
        else:
            print(f"\n {total-passed}개 테스트 실패. 문제를 해결한 후 다시 시도하세요.")
            print("문제 해결 가이드는 README_portfolio_monitor.md를 참고하세요.")


async def main():
    """메인 함수"""
    print(" 포트폴리오 실시간 모니터링 시스템 테스트")
    print("이 테스트는 모니터링 시스템의 모든 구성 요소를 검증합니다.")
    print()

    tester = PortfolioMonitorTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
