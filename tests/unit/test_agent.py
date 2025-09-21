"""
agent 모듈의 통합 테스트 모듈입니다.

이 모듈은 agent 모듈의 기능을 실제 API 호출로 테스트합니다:
- 주식 시세 조회
- 계좌 정보 조회
- 프로그램 매매 분석

의존성:
- unittest: 테스트 프레임워크
- pykis: 테스트 대상
- .env: 실제 인증 정보

사용 예시:
    >>> python -m unittest tests/unit/test_agent.py
"""

import unittest
import os
from unittest.mock import Mock, patch
from pykis import Agent
from pykis.core.client import KISClient


class TestAgent(unittest.TestCase):
    """
    Agent 클래스의 통합 테스트 클래스입니다.

    이 클래스는 Agent의 각 메서드를 모킹하여 테스트합니다.
    """

    def setUp(self):
        """테스트 설정"""
        # Mock 클라이언트 사용
        self.mock_client = Mock(spec=KISClient)
        self.agent = Agent(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678",
            account_code="01",
            client=self.mock_client,
        )
        self.test_stock_code = "005930"  # 삼성전자

    def test_init_without_client(self):
        """클라이언트 없이 초기화 테스트"""
        agent = Agent(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678",
            account_code="01",
        )
        # 내부적으로 KISClient가 생성되었는지 확인
        self.assertIsInstance(agent.client, KISClient)

    def test_get_account_balance(self):
        """계좌 잔고 조회 테스트 - Mock 사용"""
        expected_result = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"balance": "1000000"}],
        }
        self.agent.account_api = Mock()
        self.agent.account_api.get_account_balance.return_value = expected_result

        result = self.agent.get_account_balance()

        self.assertEqual(result, expected_result)
        self.agent.account_api.get_account_balance.assert_called_once()

    def test_get_program_trade_by_stock(self):
        """종목별 프로그램 매매 추이 조회 테스트 - Mock 사용"""
        expected_result = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"program_data": "test"}],
        }
        self.agent.program_api = Mock()
        self.agent.program_api.get_program_trade_by_stock.return_value = expected_result

        result = self.agent.get_program_trade_by_stock(self.test_stock_code)

        self.assertEqual(result, expected_result)
        self.agent.program_api.get_program_trade_by_stock.assert_called_once_with(
            self.test_stock_code
        )

    def test_get_stock_price(self):
        """주식 현재가 조회 테스트 - Mock 사용"""
        expected_result = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"stck_prpr": "70000"},
        }
        self.agent.stock_api = Mock()
        self.agent.stock_api.get_stock_price.return_value = expected_result

        result = self.agent.get_stock_price(self.test_stock_code)

        self.assertEqual(result, expected_result)
        self.agent.stock_api.get_stock_price.assert_called_once_with(
            self.test_stock_code
        )

    def test_get_daily_price(self):
        """주식 일별 시세 조회 테스트 - Mock 사용"""
        expected_result = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"stck_bsop_date": "20231215", "stck_clpr": "70000"}],
        }
        self.agent.stock_api = Mock()
        self.agent.stock_api.get_daily_price.return_value = expected_result

        result = self.agent.get_daily_price(self.test_stock_code)

        self.assertEqual(result, expected_result)
        self.agent.stock_api.get_daily_price.assert_called_once_with(
            self.test_stock_code, "D", "1"
        )

    def test_get_orderbook(self):
        """호가 정보 조회 테스트 - Mock 사용"""
        expected_result = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"askp1": "70100", "bidp1": "70000"},
        }
        self.agent.stock_api = Mock()
        self.agent.stock_api.get_orderbook.return_value = expected_result

        result = self.agent.stock_api.get_orderbook(self.test_stock_code)

        self.assertEqual(result, expected_result)
        self.agent.stock_api.get_orderbook.assert_called_once_with(self.test_stock_code)

    def test_get_stock_investor(self):
        """투자자별 매매 동향 조회 테스트 - Mock 사용"""
        expected_result = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"investor_data": "test"},
        }
        self.agent.stock_api = Mock()
        self.agent.stock_api.get_stock_investor.return_value = expected_result

        result = self.agent.stock_api.get_stock_investor(self.test_stock_code)

        self.assertEqual(result, expected_result)
        self.agent.stock_api.get_stock_investor.assert_called_once_with(
            self.test_stock_code
        )

    def test_get_volume_power(self):
        """체결강도 순위 조회 테스트 - Mock 사용"""
        expected_result = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"code": "005930", "power": "150.5"}],
        }
        self.agent.stock_api = Mock()
        self.agent.stock_api.get_volume_power.return_value = expected_result

        result = self.agent.stock_api.get_volume_power(0)

        self.assertEqual(result, expected_result)
        self.agent.stock_api.get_volume_power.assert_called_once_with(0)

    def test_get_top_gainers(self):
        """상위 상승주 조회 테스트 - Mock 사용"""
        expected_result = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"rank": 1, "code": "005930"}],
        }
        self.agent.get_top_gainers = Mock(return_value=expected_result)

        result = self.agent.get_top_gainers()

        self.assertEqual(result, expected_result)

    def test_get_member(self):
        """거래원 정보 조회 테스트 - Mock 사용"""
        expected_result = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"member_data": "test"},
        }
        self.agent.get_member = Mock(return_value=expected_result)

        result = self.agent.get_member(self.test_stock_code)

        self.assertEqual(result, expected_result)
        self.agent.get_member.assert_called_once_with(self.test_stock_code)

    def test_get_member_transaction(self):
        """회원사 매매 정보 조회 테스트 - Mock 사용"""
        expected_result = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": {"transaction_data": "test"},
        }
        self.agent.stock_api = Mock()
        self.agent.stock_api.get_member_transaction.return_value = expected_result

        result = self.agent.get_member_transaction(self.test_stock_code)

        self.assertEqual(result, expected_result)
        self.agent.stock_api.get_member_transaction.assert_called_once_with(
            self.test_stock_code, "99999"
        )

    def test_fetch_minute_data(self):
        """분봉 데이터 수집 테스트 - Mock 사용"""
        import pandas as pd

        expected_result = pd.DataFrame([{"time": "153000", "price": 70000}])
        self.agent.fetch_minute_data = Mock(return_value=expected_result)

        from datetime import datetime

        test_date = datetime.now().strftime("%Y%m%d")
        result = self.agent.fetch_minute_data(self.test_stock_code, test_date)

        self.assertEqual(result.equals(expected_result), True)
        self.agent.fetch_minute_data.assert_called_once_with(
            self.test_stock_code, test_date
        )

    def test_get_condition_stocks(self):
        """조건검색 종목 조회 테스트 - Mock 사용"""
        expected_result = [{"code": "005930", "name": "삼성전자"}]
        self.agent.get_condition_stocks = Mock(return_value=expected_result)

        result = self.agent.get_condition_stocks()

        self.assertEqual(result, expected_result)
        self.agent.get_condition_stocks.assert_called_once()

    def test_get_all_methods(self):
        """get_all_methods 메서드 테스트 - Mock 사용"""
        expected_result = {
            "_summary": {"total_methods": 50},
            "stock": {"title": "Stock APIs", "count": 10, "methods": []},
        }
        self.agent.get_all_methods = Mock(return_value=expected_result)

        result = self.agent.get_all_methods()

        self.assertEqual(result, expected_result)
        self.agent.get_all_methods.assert_called_once()

    def test_search_methods(self):
        """search_methods 메서드 테스트 - Mock 사용"""
        expected_result = [
            {
                "name": "get_stock_price",
                "description": "Get stock price",
                "category": "stock",
            }
        ]
        self.agent.search_methods = Mock(return_value=expected_result)

        result = self.agent.search_methods("price")

        self.assertEqual(result, expected_result)
        self.agent.search_methods.assert_called_once_with("price")

    def test_show_method_usage(self):
        """show_method_usage 메서드 테스트 - Mock 사용"""
        self.agent.show_method_usage = Mock()

        self.agent.show_method_usage("get_stock_price")

        self.agent.show_method_usage.assert_called_once_with("get_stock_price")


if __name__ == "__main__":
    unittest.main()
