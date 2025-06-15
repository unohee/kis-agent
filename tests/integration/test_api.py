"""
API 통합 테스트 모듈입니다.

이 모듈은 API 통합 테스트를 수행합니다:
- API 인증
- 주식 가격 조회
- 계좌 정보 조회
- 프로그램 매매 분석

의존성:
- unittest: 테스트 프레임워크
- core.agent: 테스트 대상
- core.config: 설정 관리

사용 예시:
    >>> python -m unittest tests/integration/test_api.py
"""

import unittest
import os
from dotenv import load_dotenv
import pytest

if not os.getenv('RUN_LIVE_TESTS'):
    pytest.skip('실제 API 테스트 건너뜀', allow_module_level=True)

from core.agent import KIS_Agent
from core.config import KISConfig

class TestKISAPI(unittest.TestCase):
    """
    API 통합 테스트 클래스입니다.

    이 클래스는 실제 API를 호출하여 API 기능을 테스트합니다.
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
        cls.agent = KIS_Agent(config)

    def test_get_stock_price(self):
        """
        주식 가격 조회 API를 테스트합니다.
        """
        # 삼성전자 현재가 조회
        price = self.agent.get_stock_price('005930')
        
        # 응답 검증
        self.assertIsNotNone(price)
        self.assertIn('stck_prpr', price)  # 현재가
        self.assertIn('stck_oprc', price)  # 시가
        self.assertIn('stck_hgpr', price)  # 고가
        self.assertIn('stck_lwpr', price)  # 저가

    def test_get_account_balance(self):
        """
        계좌 잔고 조회 API를 테스트합니다.
        """
        # 계좌 잔고 조회
        balance = self.agent.get_account_balance()
        
        # 응답 검증
        self.assertIsNotNone(balance)
        self.assertIn('prvs_rcdl_excc_amt', balance)  # D+2 예수금
        self.assertIn('dnca_tot_amt', balance)  # 입금총액
        self.assertIn('tot_evlu_amt', balance)  # 총평가금액
        self.assertIn('tot_evlu_pfls_amt', balance)  # 총평가손익금액

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

    def test_invalid_stock_code(self):
        """
        잘못된 종목코드에 대한 에러 처리를 테스트합니다.
        """
        # 잘못된 종목코드로 현재가 조회
        with self.assertRaises(Exception):
            self.agent.get_stock_price('000000')

if __name__ == '__main__':
    unittest.main() 