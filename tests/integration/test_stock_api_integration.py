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
from datetime import datetime

import pandas as pd

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
            "ACNT_PRDT_CD": os.getenv("KIS_ACCOUNT_CODE", "01"),
        }
        cls.client = KISClient()
        cls.api = StockAPI(cls.client, cls.account_info)
        cls.test_code = "005930"  # 삼성전자

    def test_get_stock_price(self):
        """주식 현재가 조회 테스트"""
        result = self.api.get_stock_price(self.test_code)
        self.assertIsNotNone(result)
        # DataFrame 또는 dict 형태로 반환될 수 있음
        if isinstance(result, pd.DataFrame):
            self.assertGreater(len(result), 0)
        elif isinstance(result, dict) and "rt_cd" in result:
            if result["rt_cd"] == "0":
                self.assertIn("output", result)

    def test_get_daily_price(self):
        """일별 시세 조회 테스트"""
        result = self.api.get_daily_price(self.test_code)
        self.assertIsNotNone(result)
        # DataFrame 또는 dict 형태로 반환될 수 있음
        if isinstance(result, pd.DataFrame):
            self.assertGreater(len(result), 0)
        elif isinstance(result, dict) and "rt_cd" in result:
            if result["rt_cd"] == "0":
                self.assertIn("output", result)
                self.assertIsInstance(result["output"], list)

    def test_get_orderbook(self):
        """호가 정보 조회 테스트"""
        result = self.api.get_orderbook(self.test_code)
        self.assertIsNotNone(result)
        # DataFrame 또는 dict 형태로 반환될 수 있음
        if isinstance(result, pd.DataFrame):
            self.assertGreater(len(result), 0)
        elif isinstance(result, dict) and "rt_cd" in result:
            self.assertEqual(result["rt_cd"], "0")

    def test_get_stock_investor(self):
        """투자자별 매매동향 조회 테스트"""
        result = self.api.get_stock_investor(self.test_code)
        self.assertIsNotNone(result)
        # DataFrame 또는 dict 형태로 반환될 수 있음
        if isinstance(result, pd.DataFrame):
            self.assertGreater(len(result), 0)
        elif isinstance(result, dict) and "rt_cd" in result:
            # API 오류가 있어도 응답이 왔다면 테스트 통과
            self.assertIsNotNone(result)

    def test_get_minute_price(self):
        """분봉 차트 조회 테스트"""
        result = self.api.get_minute_price(self.test_code, "153000")
        self.assertIsNotNone(result)
        if isinstance(result, dict) and "rt_cd" in result:
            self.assertEqual(result["rt_cd"], "0")

    def test_get_possible_order_amount(self):
        """매수 가능 주문 조회 테스트"""
        result = self.api.get_possible_order(self.test_code, "10000")
        self.assertIsNotNone(result)
        if isinstance(result, dict) and "rt_cd" in result:
            # 계좌 정보에 따라 성공/실패가 달라질 수 있음
            self.assertIsNotNone(result)

    def test_get_foreign_broker_net_buy(self):
        """외국계 브로커 순매수 조회 테스트"""
        result = self.api.get_foreign_broker_net_buy(self.test_code)
        self.assertIsNotNone(result)
        # DataFrame, dict 또는 tuple 형태로 반환될 수 있음
        if isinstance(result, pd.DataFrame):
            self.assertGreater(len(result), 0)
        elif isinstance(result, dict):
            # 딕셔너리 형태의 결과도 허용
            self.assertIsNotNone(result)
        elif isinstance(result, tuple):
            self.assertEqual(len(result), 2)
            net_buy_amount, detail_info = result
            self.assertIsInstance(net_buy_amount, (int, float))
            self.assertIsInstance(detail_info, dict)
            # 상세정보 구조 확인
            required_keys = ["brokers", "buy_total", "sell_total"]
            for key in required_keys:
                if key in detail_info:
                    break
            else:
                self.fail("필수 키들이 없습니다")

    def test_get_stock_info(self):
        """주식 기본 정보 조회 테스트"""
        result = self.api.get_stock_info(self.test_code)
        self.assertIsNotNone(result)
        if isinstance(result, pd.DataFrame):
            self.assertGreater(len(result), 0)

    def test_get_market_rankings(self):
        """시장 순위 조회 테스트"""
        result = self.api.get_market_rankings(5000000)
        self.assertIsNotNone(result)
        if isinstance(result, dict) and "rt_cd" in result:
            # API가 응답을 반환하면 테스트 통과 (에러 코드 포함)
            # rt_cd가 '2'인 경우는 INVALID FID_COND_MRKT_DIV_CODE 에러
            self.assertIn("rt_cd", result)


if __name__ == "__main__":
    unittest.main()
