"""
계좌 관련 통합 테스트 모듈입니다.

이 모듈은 계좌 관련 기능의 통합 테스트를 수행합니다:
- 계좌 잔고 조회
- 주문 가능 금액 조회
- 총 평가 금액 조회
- 계좌별 주문 수량 조회

의존성:
- unittest: 테스트 프레임워크
- account.api: 테스트 대상
- core.config: 설정 관리

사용 예시:
    >>> python -m unittest tests/integration/test_account.py
"""

import unittest
import os
from dotenv import load_dotenv

from account.api import AccountAPI
from core.client import KISClient
from core.config import KISConfig

class TestAccount(unittest.TestCase):
    """
    계좌 관련 통합 테스트 클래스입니다.

    이 클래스는 실제 API를 호출하여 계좌 관련 기능을 테스트합니다.
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
        cls.api = AccountAPI(client)

    def test_get_account_balance(self):
        """
        계좌 잔고 조회 API를 테스트합니다.
        """
        # 계좌 잔고 조회
        balance = self.api.get_account_balance()
        
        # 응답 검증
        self.assertIsNotNone(balance)
        self.assertIn('prvs_rcdl_excc_amt', balance)  # D+2 예수금
        self.assertIn('dnca_tot_amt', balance)  # 입금총액
        self.assertIn('tot_evlu_amt', balance)  # 총평가금액
        self.assertIn('tot_evlu_pfls_amt', balance)  # 총평가손익금액

    def test_get_possible_order_amount(self):
        """
        주문 가능 금액 조회 API를 테스트합니다.
        """
        # 주문 가능 금액 조회
        amount = self.api.get_possible_order_amount()
        
        # 응답 검증
        self.assertIsNotNone(amount)
        self.assertIn('ord_psbl_cash', amount)  # 주문가능현금
        self.assertIn('ord_psbl_sbst', amount)  # 주문가능대용
        self.assertIn('ord_psbl_amt', amount)  # 주문가능금액

    def test_get_total_evaluation(self):
        """
        총 평가 금액 조회 API를 테스트합니다.
        """
        # 총 평가 금액 조회
        evaluation = self.api.get_total_evaluation()
        
        # 응답 검증
        self.assertIsNotNone(evaluation)
        self.assertIn('tot_evlu_amt', evaluation)  # 총평가금액
        self.assertIn('tot_evlu_pfls_amt', evaluation)  # 총평가손익금액
        self.assertIn('tot_evlu_pfls_rt', evaluation)  # 총평가손익률

    def test_get_account_order_quantity(self):
        """
        계좌별 주문 수량 조회 API를 테스트합니다.
        """
        # 삼성전자 계좌별 주문 수량 조회
        quantity = self.api.get_account_order_quantity('005930')
        
        # 응답 검증
        self.assertIsNotNone(quantity)
        self.assertIn('ord_psbl_qty', quantity)  # 주문가능수량
        self.assertIn('ord_psbl_cash_qty', quantity)  # 현금주문가능수량
        self.assertIn('ord_psbl_sbst_qty', quantity)  # 대용주문가능수량

    def test_invalid_stock_code(self):
        """
        잘못된 종목코드에 대한 에러 처리를 테스트합니다.
        """
        # 잘못된 종목코드로 계좌별 주문 수량 조회
        with self.assertRaises(Exception):
            self.api.get_account_order_quantity('000000')

if __name__ == '__main__':
    unittest.main() 