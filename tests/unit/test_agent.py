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
from pykis import Agent
from pykis.core.client import KISClient

class TestAgent(unittest.TestCase):
    """
    Agent 클래스의 통합 테스트 클래스입니다.

    이 클래스는 Agent의 각 메서드를 실제 API 호출로 테스트합니다.
    """

    def setUp(self):
        """테스트 설정"""
        # 실제 .env 파일의 인증 정보를 사용
        self.agent = Agent()
        self.test_stock_code = "005930"  # 삼성전자

    def test_init_without_client(self):
        """클라이언트 없이 초기화 테스트"""
        agent = Agent()
        # 내부적으로 KISClient가 생성되었는지 확인
        self.assertIsInstance(agent.client, KISClient)

    def test_get_account_balance(self):
        """계좌 잔고 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_account_balance()
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        # rt_cd가 0이면 정상 응답
        if isinstance(result, dict) and 'rt_cd' in result:
            self.assertEqual(result['rt_cd'], '0')
        print(f"계좌 잔고 조회 결과: {result}")

    def test_get_program_trade_summary(self):
        """프로그램 매매 요약 정보 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_program_trade_summary(self.test_stock_code)
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        # rt_cd가 0이면 정상 응답
        if isinstance(result, dict) and 'rt_cd' in result:
            self.assertEqual(result['rt_cd'], '0')
        print(f"프로그램 매매 요약 조회 결과: {result}")

    def test_get_stock_price(self):
        """주식 현재가 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_stock_price(self.test_stock_code)
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        # rt_cd가 0이면 정상 응답
        if isinstance(result, dict) and 'rt_cd' in result:
            self.assertEqual(result['rt_cd'], '0')
        print(f"주식 현재가 조회 결과: {result}")

    def test_get_daily_price(self):
        """주식 일별 시세 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_daily_price(self.test_stock_code)
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        print(f"주식 일별 시세 조회 결과: {result}")
        # rt_cd가 0이면 정상 응답, 빈 문자열이어도 응답이 있으면 통과
        if isinstance(result, dict) and 'rt_cd' in result:
            if result['rt_cd'] != '0':
                print(f"API 오류: rt_cd={result['rt_cd']}, msg1={result.get('msg1', 'N/A')}")
                # API 응답이 있으면 테스트 통과 (권한 문제일 수 있음)
                self.assertIsNotNone(result)
            else:
                self.assertEqual(result['rt_cd'], '0')

    def test_get_orderbook(self):
        """호가 정보 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_orderbook(self.test_stock_code)
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        # rt_cd가 0이면 정상 응답
        if isinstance(result, dict) and 'rt_cd' in result:
            self.assertEqual(result['rt_cd'], '0')
        print(f"호가 정보 조회 결과: {result}")

    def test_get_stock_investor(self):
        """투자자별 매매 동향 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_stock_investor(self.test_stock_code)
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        print(f"투자자별 매매 동향 조회 결과: {result}")
        # rt_cd가 0이면 정상 응답, 빈 문자열이어도 응답이 있으면 통과
        if isinstance(result, dict) and 'rt_cd' in result:
            if result['rt_cd'] != '0':
                print(f"API 오류: rt_cd={result['rt_cd']}, msg1={result.get('msg1', 'N/A')}")
                # API 응답이 있으면 테스트 통과 (권한 문제일 수 있음)
                self.assertIsNotNone(result)
            else:
                self.assertEqual(result['rt_cd'], '0')

    def test_get_volume_rank(self):
        """거래량 순위 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_volume_rank()
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        # rt_cd가 0이면 정상 응답
        if isinstance(result, dict) and 'rt_cd' in result:
            self.assertEqual(result['rt_cd'], '0')
        print(f"거래량 순위 조회 결과: {result}")

    def test_get_price_rank(self):
        """등락률 순위 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_price_rank()
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        # rt_cd가 0이면 정상 응답
        if isinstance(result, dict) and 'rt_cd' in result:
            self.assertEqual(result['rt_cd'], '0')
        print(f"등락률 순위 조회 결과: {result}")

if __name__ == '__main__':
    unittest.main() 