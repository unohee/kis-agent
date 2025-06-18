"""
프로그램 매매 통합 테스트 모듈입니다.

이 모듈은 프로그램 매매 기능의 통합 테스트를 수행합니다:
- 시간별 프로그램 매매 조회
- 일별 프로그램 매매 조회
- 프로그램 매매 분석
- 기간별 프로그램 매매 조회

의존성:
- unittest: 테스트 프레임워크
- pykis.Agent: 테스트 대상

사용 예시:
    >>> python -m unittest tests/integration/test_program_trade.py
"""

import unittest
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytest

if not os.getenv('RUN_LIVE_TESTS'):
    pytest.skip('실제 API 테스트 건너뜀', allow_module_level=True)

from pykis import Agent

class TestProgramTrade(unittest.TestCase):
    """
    프로그램 매매 통합 테스트 클래스입니다.

    이 클래스는 실제 API를 호출하여 프로그램 매매 기능을 테스트합니다.
    """

    @classmethod
    def setUpClass(cls):
        """
        테스트 클래스 실행 전에 호출되는 메서드입니다.
        """
        # 환경 변수 로드
        load_dotenv()

        # 필수 환경 변수 확인
        required_env_vars = [
            'KIS_APP_KEY',
            'KIS_APP_SECRET',
            'KIS_BASE_URL',
            'KIS_ACCOUNT_NO',
            'KIS_ACCOUNT_CODE'
        ]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")

        # Agent 인스턴스 생성 (Agent 중심 설계)
        cls.agent = Agent()

    def test_get_hourly_trade(self):
        """
        시간별 프로그램 매매 조회 API를 테스트합니다.
        """
        # 삼성전자 시간별 프로그램 매매 조회
        hourly_data = self.agent.get_program_trade_hourly_trend('005930')
        
        # 응답 검증
        self.assertIsNotNone(hourly_data)
        self.assertIsInstance(hourly_data, list)
        if hourly_data:
            self.assertIn('time', hourly_data[0])  # 시간
            self.assertIn('buy_amount', hourly_data[0])  # 매수금액
            self.assertIn('sell_amount', hourly_data[0])  # 매도금액

    def test_get_daily_trade(self):
        """
        일별 프로그램 매매 조회 API를 테스트합니다.
        """
        # 삼성전자 일별 프로그램 매매 조회
        daily_data = self.agent.get_program_trade_daily_summary('005930', '20250516')
        
        # 응답 검증
        self.assertIsNotNone(daily_data)
        self.assertIsInstance(daily_data, list)
        if daily_data:
            self.assertIn('date', daily_data[0])  # 날짜
            self.assertIn('buy_amount', daily_data[0])  # 매수금액
            self.assertIn('sell_amount', daily_data[0])  # 매도금액

    def test_get_program_trade_summary(self):
        """
        프로그램 매매 분석 API를 테스트합니다.
        """
        # 삼성전자 프로그램 매매 분석
        summary = self.agent.get_program_trade_summary('005930')
        
        # 응답 검증
        self.assertIsNotNone(summary)
        self.assertIn('today_trend', summary)  # 오늘의 추세
        self.assertIn('net_buy_amount', summary)  # 순매수금액
        self.assertIn('buy_ratio', summary)  # 매수비율
        self.assertIn('momentum_score', summary)  # 모멘텀 점수
        self.assertIn('volume_trend', summary)  # 거래량 추세

    def test_get_program_trade_period(self):
        """
        기간별 프로그램 매매 조회 API를 테스트합니다.
        """
        # 시작일과 종료일 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # 삼성전자 기간별 프로그램 매매 조회
        period_data = self.agent.get_program_trade_period_detail(
            start_date.strftime('%Y%m%d'),
            end_date.strftime('%Y%m%d')
        )
        
        # 응답 검증
        self.assertIsNotNone(period_data)
        self.assertIsInstance(period_data, list)
        if period_data:
            self.assertIn('date', period_data[0])  # 날짜
            self.assertIn('buy_amount', period_data[0])  # 매수금액
            self.assertIn('sell_amount', period_data[0])  # 매도금액

    def test_invalid_stock_code(self):
        """
        잘못된 종목코드에 대한 에러 처리를 테스트합니다.
        """
        # 잘못된 종목코드로 프로그램 매매 조회
        with self.assertRaises(Exception):
            self.agent.get_program_trade_hourly_trend('000000')

if __name__ == '__main__':
    unittest.main() 