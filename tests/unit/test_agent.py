"""
agent 모듈의 단위 테스트 모듈입니다.

이 모듈은 agent 모듈의 기능을 테스트합니다:
- 주식 시세 조회
- 계좌 정보 조회
- 프로그램 매매 분석

의존성:
- unittest: 테스트 프레임워크
- unittest.mock: 모킹
- kis.core.agent: 테스트 대상
- kis.core.client: API 클라이언트

사용 예시:
    >>> python -m unittest tests/unit/test_agent.py
"""

import unittest
from unittest.mock import patch, MagicMock

from kis.core.agent import KIS_Agent
from kis.core.client import KISClient

class TestKISAgent(unittest.TestCase):
    """
    KIS_Agent 클래스의 단위 테스트 클래스입니다.

    이 클래스는 KIS_Agent의 각 메서드를 테스트합니다.
    """

    def setUp(self):
        """
        테스트 케이스 실행 전에 호출되는 메서드입니다.
        """
        self.client = MagicMock(spec=KISClient)
        self.agent = KIS_Agent(self.client)

    @patch('kis.stock.market.StockMarketAPI.get_stock_price')
    def test_get_stock_price(self, mock_get_price):
        """
        get_stock_price 메서드를 테스트합니다.
        """
        # Mock 응답 설정
        mock_get_price.return_value = {
            'stck_prpr': '70000',
            'stck_oprc': '69000',
            'stck_hgpr': '71000',
            'stck_lwpr': '68000'
        }

        # 주식 시세 조회 테스트
        price = self.agent.get_stock_price('005930')
        self.assertEqual(price['stck_prpr'], '70000')
        mock_get_price.assert_called_once_with('005930')

    @patch('kis.account.balance.AccountBalanceAPI.get_account_balance')
    def test_get_account_balance(self, mock_get_balance):
        """
        get_account_balance 메서드를 테스트합니다.
        """
        # Mock 응답 설정
        mock_get_balance.return_value = {
            'prvs_rcdl_excc_amt': '1000000',
            'thdt_buyamt': '500000',
            'thdt_sllamt': '300000'
        }

        # 계좌 잔고 조회 테스트
        balance = self.agent.get_account_balance()
        self.assertEqual(balance['prvs_rcdl_excc_amt'], '1000000')
        mock_get_balance.assert_called_once()

    @patch('kis.program.trade.ProgramTradeAPI.get_program_trade_summary')
    def test_get_program_trade_summary(self, mock_get_summary):
        """
        get_program_trade_summary 메서드를 테스트합니다.
        """
        # Mock 응답 설정
        mock_get_summary.return_value = {
            'today_trend': '매수세',
            'net_buy_amount': 1000000000,
            'buy_ratio': 0.6,
            'momentum_score': 0.8,
            'volume_trend': '증가'
        }

        # 프로그램 매매 분석 테스트
        summary = self.agent.get_program_trade_summary('005930')
        self.assertEqual(summary['today_trend'], '매수세')
        mock_get_summary.assert_called_once_with('005930')

    def test_init_without_client(self):
        """
        클라이언트 없이 초기화하는 것을 테스트합니다.
        """
        with patch('kis.core.client.KISClient') as mock_client:
            agent = KIS_Agent()
            mock_client.assert_called_once()

if __name__ == '__main__':
    unittest.main() 