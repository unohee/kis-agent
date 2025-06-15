"""
agent 모듈의 단위 테스트 모듈입니다.

이 모듈은 agent 모듈의 기능을 테스트합니다:
- 주식 시세 조회
- 계좌 정보 조회
- 프로그램 매매 분석

의존성:
- unittest: 테스트 프레임워크
- unittest.mock: 모킹
- pykis.core.agent: 테스트 대상
- pykis.core.client: API 클라이언트

사용 예시:
    >>> python -m unittest tests/unit/test_agent.py
"""

import unittest
from unittest.mock import MagicMock, patch
from pykis.core.agent import Agent
from pykis.core.client import KISClient
from pykis.core.config import KISConfig
from pykis.core.auth import auth
from pykis.account.api import AccountAPI
from pykis.stock.api import StockAPI
from pykis.program.api import ProgramTradeAPI

class TestAgent(unittest.TestCase):
    """
    Agent 클래스의 단위 테스트 클래스입니다.

    이 클래스는 Agent의 각 메서드를 테스트합니다.
    """

    def setUp(self):
        """테스트 설정"""
        # [변경 이유] 테스트용 설정 파일 경로 지정
        self.config = KISConfig('tests/config/test_config.yaml')
        # [변경 이유] 테스트용 인증 정보 설정
        self.auth = auth(self.config)
        # [변경 이유] 테스트용 클라이언트 생성
        self.client = KISClient(config=self.config)
        # [변경 이유] 테스트용 Agent 인스턴스 생성
        self.agent = Agent(self.client)

    def test_init_without_client(self):
        """클라이언트 없이 초기화 테스트"""
        # [변경 이유] 클라이언트 없이 Agent 생성
        agent = Agent()
        # [변경 이유] 내부적으로 KISClient가 생성되었는지 확인
        self.assertIsInstance(agent.client, KISClient)

    def test_get_account_balance(self):
        """계좌 잔고 조회 테스트"""
        # [변경 이유] 테스트용 계좌 잔고 데이터 설정
        expected = {
            'output': {
                'tot_evlu_amt': '1000000',
                'scts_evlu_amt': '800000',
                'tot_loan_amt': '0'
            }
        }
        # [변경 이유] MagicMock을 사용하여 account_api의 get_account_balance 메서드 모킹
        self.agent.account_api = MagicMock()
        self.agent.account_api.get_account_balance.return_value = expected
        # [변경 이유] 실제 메서드 호출 및 결과 검증
        result = self.agent.get_account_balance()
        self.assertEqual(result, expected)
        # [변경 이유] 메서드가 올바른 인자로 호출되었는지 확인
        self.agent.account_api.get_account_balance.assert_called_once()

    def test_get_program_trade_summary(self):
        """프로그램 매매 요약 정보 조회 테스트"""
        # [변경 이유] 테스트용 프로그램 매매 요약 데이터 설정
        expected = {
            'output': {
                'tot_buy_amt': '1000000',
                'tot_sell_amt': '500000'
            }
        }
        # [변경 이유] MagicMock을 사용하여 program_api의 get_program_trade_summary 메서드 모킹
        self.agent.program_api = MagicMock()
        self.agent.program_api.get_program_trade_summary.return_value = expected
        # [변경 이유] 실제 메서드 호출 및 결과 검증
        result = self.agent.get_program_trade_summary('005930')
        self.assertEqual(result, expected)
        # [변경 이유] 메서드가 올바른 인자로 호출되었는지 확인
        self.agent.program_api.get_program_trade_summary.assert_called_once_with('005930')

    def test_get_stock_price(self):
        """주식 현재가 조회 테스트"""
        # [변경 이유] 테스트용 주식 현재가 데이터 설정
        expected = {
            'output': {
                'stck_prpr': '50000',
                'stck_oprc': '49000',
                'stck_hgpr': '51000',
                'stck_lwpr': '48000'
            }
        }
        # [변경 이유] MagicMock을 사용하여 stock_api의 get_stock_price 메서드 모킹
        self.agent.stock_api = MagicMock()
        self.agent.stock_api.get_stock_price.return_value = expected
        # [변경 이유] 실제 메서드 호출 및 결과 검증
        result = self.agent.get_stock_price('005930')  # 삼성전자
        self.assertEqual(result, expected)
        # [변경 이유] 메서드가 올바른 인자로 호출되었는지 확인
        self.agent.stock_api.get_stock_price.assert_called_once_with('005930')

if __name__ == '__main__':
    unittest.main() 