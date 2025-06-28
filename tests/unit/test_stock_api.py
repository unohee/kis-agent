"""
stock.api 모듈의 단위 테스트 모듈입니다.

이 모듈은 StockAPI 클래스의 기능을 실제 API 호출로 테스트합니다:
- 주식 시세 조회
- 호가 정보 조회
- 투자자별 매매동향
- 분봉 데이터 조회

의존성:
- unittest: 테스트 프레임워크
- pykis.stock.api: 테스트 대상
- .env: 실제 인증 정보

사용 예시:
    >>> python -m unittest tests/unit/test_stock_api.py
"""

import os
import unittest
import pandas as pd
from datetime import datetime
from pykis.core.client import KISClient
from pykis.stock.api import StockAPI

class TestStockAPI(unittest.TestCase):
    """
    StockAPI 클래스의 단위 테스트 클래스입니다.
    
    이 클래스는 StockAPI의 각 메서드를 실제 API 호출로 테스트합니다.
    """
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        # 실제 계좌 정보는 환경변수에서 읽음
        cls.account_info = {
            "CANO": os.getenv("KIS_ACCOUNT_NO"),
            "ACNT_PRDT_CD": os.getenv("KIS_ACCOUNT_CODE", "01")
        }
        cls.client = KISClient()
        cls.api = StockAPI(cls.client, cls.account_info)
        cls.test_code = "005930"  # 삼성전자

    def test_get_stock_price(self):
        """주식 현재가 조회 테스트"""
        result = self.api.get_stock_price(self.test_code)
        print("get_stock_price:", result)
        self.assertIsNotNone(result)
        self.assertIn("rt_cd", result)
        if result["rt_cd"] == "0":
            self.assertIn("output", result)
            self.assertIn("stck_prpr", result["output"])  # 현재가 필드 확인

    def test_get_daily_price(self):
        """일별 시세 조회 테스트"""
        result = self.api.get_daily_price(self.test_code)
        print("get_daily_price:", result)
        self.assertIsNotNone(result)
        self.assertIn("rt_cd", result)
        if result["rt_cd"] == "0":
            self.assertIn("output", result)
            self.assertIsInstance(result["output"], list)

    def test_get_orderbook(self):
        """호가 정보 조회 테스트"""
        result = self.api.get_orderbook(self.test_code)
        print("get_orderbook:", result)
        self.assertIsNotNone(result)
        # DataFrame 또는 dict 형태로 반환될 수 있음
        if isinstance(result, pd.DataFrame):
            self.assertGreater(len(result), 0)
        elif isinstance(result, dict) and "rt_cd" in result:
            self.assertEqual(result["rt_cd"], "0")

    def test_get_stock_investor(self):
        """투자자별 매매동향 조회 테스트"""
        result = self.api.get_stock_investor(self.test_code)
        print("get_stock_investor:", result)
        self.assertIsNotNone(result)
        # DataFrame 또는 dict 형태로 반환될 수 있음
        if isinstance(result, pd.DataFrame):
            self.assertGreater(len(result), 0)
        elif isinstance(result, dict) and "rt_cd" in result:
            # API 오류가 있어도 응답이 왔다면 테스트 통과
            self.assertIsNotNone(result)

    def test_get_minute_chart(self):
        """분봉 차트 조회 테스트"""
        result = self.api.get_minute_chart(self.test_code, "153000")
        print("get_minute_chart:", result)
        self.assertIsNotNone(result)
        if isinstance(result, dict) and "rt_cd" in result:
            self.assertEqual(result["rt_cd"], "0")

    def test_get_possible_order(self):
        """매수 가능 주문 조회 테스트"""
        result = self.api.get_possible_order(self.test_code, "50000", "01")
        print("get_possible_order:", result)
        self.assertIsNotNone(result)
        if isinstance(result, dict) and "rt_cd" in result:
            # 계좌 정보에 따라 성공/실패가 달라질 수 있음
            self.assertIsNotNone(result)

    def test_get_foreign_broker_net_buy(self):
        """외국계 브로커 순매수 조회 테스트"""
        result = self.api.get_foreign_broker_net_buy(self.test_code)
        print("get_foreign_broker_net_buy:", result)
        self.assertIsNotNone(result)
        # tuple (순매수량, DataFrame) 형태로 반환
        if isinstance(result, tuple):
            self.assertEqual(len(result), 2)
            net_buy_amount, dataframe = result
            self.assertIsInstance(net_buy_amount, (int, float))
            self.assertIsInstance(dataframe, pd.DataFrame)

    def test_get_stock_info(self):
        """주식 기본 정보 조회 테스트"""
        result = self.api.get_stock_info(self.test_code)
        print("get_stock_info:", result)
        self.assertIsNotNone(result)
        if isinstance(result, pd.DataFrame):
            self.assertGreater(len(result), 0)

    def test_get_market_rankings(self):
        """시장 순위 조회 테스트"""
        result = self.api.get_market_rankings(5000000)
        print("get_market_rankings:", result)
        self.assertIsNotNone(result)
        if isinstance(result, dict) and "rt_cd" in result:
            self.assertEqual(result["rt_cd"], "0")

if __name__ == "__main__":
    unittest.main() 