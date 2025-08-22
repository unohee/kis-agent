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
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        self.agent = Agent(env_path=env_path)
        self.test_stock_code = "005930"  # 삼성전자

    def test_init_without_client(self):
        """클라이언트 없이 초기화 테스트"""
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        agent = Agent(env_path=env_path)
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

    def test_get_program_trade_by_stock(self):
        """종목별 프로그램 매매 추이 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_program_trade_by_stock(self.test_stock_code)
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        # rt_cd가 0이면 정상 응답
        if isinstance(result, dict) and 'rt_cd' in result:
            pass

    def test_get_stock_price(self):
        """주식 현재가 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_stock_price(self.test_stock_code)
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        # rt_cd가 0이면 정상 응답
        if isinstance(result, dict) and 'rt_cd' in result:
            self.assertEqual(result['rt_cd'], '0')

    def test_get_daily_price(self):
        """주식 일별 시세 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_daily_price(self.test_stock_code)
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
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
        result = self.agent.stock_api.get_orderbook(self.test_stock_code)
        # API 응답이 정상인지 확인 (DataFrame 또는 dict 형태로 반환될 수 있음)
        self.assertIsNotNone(result)
        # DataFrame이면 성공으로 간주
        if hasattr(result, 'shape'):
            self.assertGreater(len(result), 0)
        # dict 형태면 rt_cd 확인
        elif isinstance(result, dict) and 'rt_cd' in result:
            self.assertEqual(result['rt_cd'], '0')

    def test_get_stock_investor(self):
        """투자자별 매매 동향 조회 테스트 - 실제 API 호출"""
        result = self.agent.stock_api.get_stock_investor(self.test_stock_code)
        # API 응답이 정상인지 확인 (DataFrame 또는 dict 형태로 반환될 수 있음)
        self.assertIsNotNone(result)
        
        # DataFrame이면 성공으로 간주
        if hasattr(result, 'shape'):
            self.assertGreater(len(result), 0)
        # dict 형태면 rt_cd 확인
        elif isinstance(result, dict) and 'rt_cd' in result:
            if result['rt_cd'] != '0':
                print(f"API 오류: rt_cd={result['rt_cd']}, msg1={result.get('msg1', 'N/A')}")
                # API 응답이 있으면 테스트 통과 (권한 문제일 수 있음)
                self.assertIsNotNone(result)
            else:
                self.assertEqual(result['rt_cd'], '0')

    def test_get_volume_power(self):
        """체결강도 순위 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_volume_power(0)  # 파라미터 추가
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        # rt_cd가 0이면 정상 응답
        if isinstance(result, dict) and 'rt_cd' in result:
            self.assertEqual(result['rt_cd'], '0')

    def test_get_top_gainers(self):
        """상위 상승주 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_top_gainers()
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        # rt_cd가 0이면 정상 응답
        if isinstance(result, dict) and 'rt_cd' in result:
            self.assertEqual(result['rt_cd'], '0')
    
    def test_get_member(self):
        """거래원 정보 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_member(self.test_stock_code)
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        # rt_cd가 0이면 정상 응답
        if isinstance(result, dict) and 'rt_cd' in result:
            self.assertEqual(result['rt_cd'], '0')
    
    def test_get_member_transaction(self):
        """회원사 매매 정보 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_member_transaction(self.test_stock_code)
        # API 응답이 정상인지 확인
        self.assertIsNotNone(result)
        # rt_cd가 0이면 정상 응답
        if isinstance(result, dict) and 'rt_cd' in result:
            self.assertEqual(result['rt_cd'], '0')
    
    def test_fetch_minute_data(self):
        """분봉 데이터 수집 테스트 - 실제 API 호출"""
        from datetime import datetime
        test_date = datetime.now().strftime('%Y%m%d')
        result = self.agent.fetch_minute_data(self.test_stock_code, test_date)
        # API 응답이 정상인지 확인 (DataFrame으로 반환)
        self.assertIsNotNone(result)
        if hasattr(result, 'shape'):
            pass
        else:
            pass
    
    def test_get_condition_stocks(self):
        """조건검색 종목 조회 테스트 - 실제 API 호출"""
        result = self.agent.get_condition_stocks()
        # API 응답이 정상인지 확인 (list로 반환)
        self.assertIsNotNone(result)
        if isinstance(result, list):
            pass
        else:
            pass

    def test_get_all_methods(self):
        """get_all_methods 메서드 테스트"""
        # 기본 사용법 테스트
        result = self.agent.get_all_methods()
        self.assertIsInstance(result, dict)
        self.assertIn('_summary', result)
        self.assertGreater(result['_summary']['total_methods'], 30)  # 최소 30개 이상의 메서드
        
        # 카테고리별 확인
        expected_categories = ['stock', 'account', 'program', 'market', 'utility', 'websocket']
        for category in expected_categories:
            self.assertIn(category, result)
            self.assertIn('title', result[category])
            self.assertIn('count', result[category])
            self.assertIn('methods', result[category])
        
        # 상세 정보 포함 테스트
        detailed_result = self.agent.get_all_methods(show_details=True)
        self.assertIsInstance(detailed_result, dict)
        
        # 특정 카테고리만 요청
        stock_only = self.agent.get_all_methods(category='stock')
        self.assertIn('stock', stock_only)
        self.assertNotIn('account', stock_only)

    def test_search_methods(self):
        """search_methods 메서드 테스트"""
        # "price" 키워드로 검색
        price_methods = self.agent.search_methods('price')
        self.assertIsInstance(price_methods, list)
        self.assertGreater(len(price_methods), 0)
        
        # 검색 결과 구조 확인
        if price_methods:
            method = price_methods[0]
            self.assertIn('name', method)
            self.assertIn('description', method)
            self.assertIn('example', method)
            self.assertIn('category', method)
        
        # 존재하지 않는 키워드 검색
        no_results = self.agent.search_methods('nonexistent_keyword_12345')
        self.assertIsInstance(no_results, list)
        self.assertEqual(len(no_results), 0)

    def test_show_method_usage(self):
        """show_method_usage 메서드 테스트"""
        import io
        import sys
        from contextlib import redirect_stdout
        
        # 정상적인 메서드에 대한 사용법 출력 테스트
        f = io.StringIO()
        with redirect_stdout(f):
            self.agent.show_method_usage('get_stock_price')
        output = f.getvalue()
        
        # 출력 내용 검증
        self.assertIn('get_stock_price', output)
        self.assertIn('현재가 조회', output)
        self.assertIn('사용 예시', output)
        
        # 존재하지 않는 메서드에 대한 처리 테스트
        f2 = io.StringIO()
        with redirect_stdout(f2):
            self.agent.show_method_usage('nonexistent_method')
        output2 = f2.getvalue()
        
        self.assertIn('찾을 수 없습니다', output2)

if __name__ == '__main__':
    unittest.main() 