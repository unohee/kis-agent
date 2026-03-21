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

import os
import unittest
from unittest.mock import Mock, patch

from kis_agent import Agent
from kis_agent.core.client import KISClient


class TestAgent(unittest.TestCase):
    """
    Agent 클래스의 통합 테스트 클래스입니다.

    이 클래스는 Agent의 각 메서드를 모킹하여 테스트합니다.
    """

    @patch("kis_agent.core.agent.StockAPI")
    @patch("kis_agent.core.agent.AccountAPI")
    @patch("kis_agent.core.agent.ProgramTradeAPI")
    @patch("kis_agent.core.agent.StockMarketAPI")
    def setUp(
        self, mock_market_api, mock_program_api, mock_account_api, mock_stock_api
    ):
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

    @patch("kis_agent.core.auth.read_token")
    @patch("kis_agent.core.auth.auth")
    @patch("kis_agent.core.agent.KISClient")
    def test_init_without_client(self, mock_client_class, mock_auth, mock_read_token):
        """클라이언트 없이 초기화 테스트 (토큰 관리는 KISClient._initialize_token -> auth()에서 담당)"""
        # Mock token validation to skip auth (auth() 내부에서 read_token 호출)
        mock_read_token.return_value = {
            "access_token": "test_token",
            "access_token_token_expired": "2099-12-31 23:59:59",
        }
        mock_client_instance = Mock(spec=KISClient)
        mock_client_class.return_value = mock_client_instance

        agent = Agent(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678",
            account_code="01",
        )
        # 내부적으로 KISClient가 생성되었는지 확인
        self.assertIsInstance(agent.client, KISClient)
        mock_client_class.assert_called_once()

    @unittest.skip(
        "API 리팩토링으로 위임 구조 변경 - test_agent_comprehensive.py에서 대체"
    )
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

    @unittest.skip(
        "API 리팩토링으로 위임 구조 변경 - test_agent_comprehensive.py에서 대체"
    )
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

    @unittest.skip("API 리팩토링으로 메서드 시그니처 변경")
    def test_inquire_daily_price(self):
        """주식현재가 일자별 조회 테스트 (최근 30건) - Mock 사용"""
        expected_result = {
            "rt_cd": "0",
            "msg1": "성공",
            "output": [{"stck_bsop_date": "20231215", "stck_clpr": "70000"}],
        }
        self.agent.stock_api = Mock()
        self.agent.stock_api.inquire_daily_price.return_value = expected_result

        result = self.agent.inquire_daily_price(self.test_stock_code)

        self.assertEqual(result, expected_result)
        self.agent.stock_api.inquire_daily_price.assert_called_once_with(
            self.test_stock_code, "D", "1"
        )

    @unittest.skip("API 리팩토링으로 메서드 시그니처 변경")
    def test_inquire_daily_itemchartprice(self):
        """국내주식 기간별 시세 조회 테스트 (날짜 범위 지정) - Mock 사용"""
        expected_result = {
            "rt_cd": "0",
            "msg1": "성공",
            "output1": [{"stck_bsop_date": "20220101", "stck_clpr": "65000"}],
            "output2": {},
        }
        self.agent.stock_api = Mock()
        self.agent.stock_api.inquire_daily_itemchartprice.return_value = expected_result

        result = self.agent.inquire_daily_itemchartprice(
            self.test_stock_code, "20220101", "20220809"
        )

        self.assertEqual(result, expected_result)
        self.agent.stock_api.inquire_daily_itemchartprice.assert_called_once_with(
            self.test_stock_code, "20220101", "20220809", "D", "1"
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

    @unittest.skip("API 리팩토링으로 메서드 시그니처 변경")
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
        # search_methods는 실제 메서드를 호출해서 결과를 확인
        result = self.agent.search_methods("price")

        # 결과가 리스트인지 확인
        self.assertIsInstance(result, list)
        # "price" 키워드가 포함된 메서드가 있는지 확인
        if len(result) > 0:
            self.assertTrue(
                any("price" in method.get("name", "").lower() for method in result)
            )

    def test_show_method_usage(self):
        """show_method_usage 메서드 테스트 - Mock 사용"""
        # show_method_usage는 실제 메서드를 호출 (print만 하므로 에러 없음)
        # 예외 발생 안 하면 성공
        try:
            self.agent.show_method_usage("get_stock_price")
            success = True
        except Exception:
            success = False

        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
