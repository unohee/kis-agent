"""
주식 시세 조회 통합 테스트 모듈입니다.

이 모듈은 주식 시세 조회 기능의 통합 테스트를 수행합니다:
- 현재가 조회
- 일별 시세 조회
- 분봉 시세 조회
- 거래원 조회

의존성:
- unittest: 테스트 프레임워크
- stock.market: 테스트 대상
- core.config: 설정 관리

사용 예시:
    >>> python -m unittest tests/integration/test_stock_market.py
"""

import unittest
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from stock.market import StockMarketAPI
from core.client import KISClient
from core.config import KISConfig

class TestStockMarket(unittest.TestCase):
    """
    주식 시세 조회 통합 테스트 클래스입니다.

    이 클래스는 실제 API를 호출하여 주식 시세 조회 기능을 테스트합니다.
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
        cls.api = StockMarketAPI(client)

    def test_get_stock_price(self):
        """
        현재가 조회 API를 테스트합니다.
        """
        # 삼성전자 현재가 조회
        price = self.api.get_stock_price('005930')
        
        # 응답 검증
        self.assertIsNotNone(price)
        self.assertIn('stck_prpr', price)  # 현재가
        self.assertIn('stck_oprc', price)  # 시가
        self.assertIn('stck_hgpr', price)  # 고가
        self.assertIn('stck_lwpr', price)  # 저가

    def test_get_daily_price(self):
        """
        일별 시세 조회 API를 테스트합니다.
        """
        # 시작일과 종료일 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # 삼성전자 일별 시세 조회
        daily_data = self.api.get_daily_price(
            '005930',
            start_date.strftime('%Y%m%d'),
            end_date.strftime('%Y%m%d')
        )
        
        # 응답 검증
        self.assertIsNotNone(daily_data)
        self.assertIsInstance(daily_data, list)
        if daily_data:
            self.assertIn('stck_bsop_date', daily_data[0])  # 날짜
            self.assertIn('stck_oprc', daily_data[0])  # 시가
            self.assertIn('stck_hgpr', daily_data[0])  # 고가
            self.assertIn('stck_lwpr', daily_data[0])  # 저가
            self.assertIn('stck_clpr', daily_data[0])  # 종가

    def test_get_minute_price(self):
        """
        분봉 시세 조회 API를 테스트합니다.
        """
        # 삼성전자 분봉 시세 조회
        minute_data = self.api.get_minute_price('005930')
        
        # 응답 검증
        self.assertIsNotNone(minute_data)
        self.assertIsInstance(minute_data, list)
        if minute_data:
            self.assertIn('stck_cntg_hour', minute_data[0])  # 시간
            self.assertIn('stck_oprc', minute_data[0])  # 시가
            self.assertIn('stck_hgpr', minute_data[0])  # 고가
            self.assertIn('stck_lwpr', minute_data[0])  # 저가
            self.assertIn('stck_clpr', minute_data[0])  # 종가

    def test_get_member(self):
        """
        거래원 조회 API를 테스트합니다.
        """
        # 삼성전자 거래원 조회
        member_data = self.api.get_member('005930')
        
        # 응답 검증
        self.assertIsNotNone(member_data)
        self.assertIsInstance(member_data, list)
        if member_data:
            self.assertIn('mbrn_nm', member_data[0])  # 거래원명
            self.assertIn('buy_amt', member_data[0])  # 매수금액
            self.assertIn('sell_amt', member_data[0])  # 매도금액

    def test_invalid_stock_code(self):
        """
        잘못된 종목코드에 대한 에러 처리를 테스트합니다.
        """
        # 잘못된 종목코드로 현재가 조회
        with self.assertRaises(Exception):
            self.api.get_stock_price('000000')

if __name__ == '__main__':
    unittest.main() 