"""
전략 관련 통합 테스트 모듈입니다.

이 모듈은 전략 관련 기능의 통합 테스트를 수행합니다:
- 기본 전략 실행
- 조건 전략 실행
- 전략 모니터링
- 매수 트리거 실행

의존성:
- unittest: 테스트 프레임워크
- strategy.trigger: 테스트 대상
- core.config: 설정 관리

사용 예시:
    >>> python -m unittest tests/integration/test_strategy.py
"""

import unittest
import os
from dotenv import load_dotenv

from strategy.trigger import StrategyTrigger
from core.client import KISClient
from core.config import KISConfig

class TestStrategy(unittest.TestCase):
    """
    전략 관련 통합 테스트 클래스입니다.

    이 클래스는 실제 API를 호출하여 전략 관련 기능을 테스트합니다.
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

        # API 클라이언트 초기화
        config = KISConfig()
        client = KISClient(config)
        cls.trigger = StrategyTrigger(client)

    def test_check_entry_condition(self):
        """
        매수 진입 조건 체크 API를 테스트합니다.
        """
        # 삼성전자 매수 진입 조건 체크
        result = self.trigger.check_entry_condition('005930')
        
        # 응답 검증
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('can_enter', result)  # 진입 가능 여부
        self.assertIn('reason', result)  # 진입/미진입 사유

    def test_execute_buy_order(self):
        """
        매수 주문 실행 API를 테스트합니다.
        """
        # 삼성전자 매수 주문 실행 (1주)
        result = self.trigger.execute_buy_order('005930', 1)
        
        # 응답 검증
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('order_id', result)  # 주문 ID
        self.assertIn('order_status', result)  # 주문 상태

    def test_monitor_strategy(self):
        """
        전략 모니터링 API를 테스트합니다.
        """
        # 삼성전자 전략 모니터링
        result = self.trigger.monitor_strategy('005930')
        
        # 응답 검증
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('strategy_status', result)  # 전략 상태
        self.assertIn('current_position', result)  # 현재 포지션
        self.assertIn('profit_loss', result)  # 손익

    def test_check_exit_condition(self):
        """
        매도 진출 조건 체크 API를 테스트합니다.
        """
        # 삼성전자 매도 진출 조건 체크
        result = self.trigger.check_exit_condition('005930')
        
        # 응답 검증
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('should_exit', result)  # 진출 여부
        self.assertIn('reason', result)  # 진출/미진출 사유

    def test_invalid_stock_code(self):
        """
        잘못된 종목코드에 대한 에러 처리를 테스트합니다.
        """
        # 잘못된 종목코드로 매수 진입 조건 체크
        with self.assertRaises(Exception):
            self.trigger.check_entry_condition('000000')

if __name__ == '__main__':
    unittest.main() 