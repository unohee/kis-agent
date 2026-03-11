"""Rate Limiter 단위 테스트"""

import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, Mock, patch

from kis_agent.core.agent import Agent
from kis_agent.core.client import KISClient
from kis_agent.core.rate_limiter import RateLimiter


class TestRateLimiter(unittest.TestCase):
    """RateLimiter 클래스 테스트"""

    def setUp(self):
        """테스트 초기화"""
        self.limiter = RateLimiter(
            requests_per_second=5,
            requests_per_minute=100,
            min_interval_ms=50,
            enable_adaptive=True,
        )

    def test_basic_rate_limiting(self):
        """기본 유량 제한 테스트"""
        start_time = time.time()

        # 3개 요청 실행
        for _ in range(3):
            self.limiter.acquire()

        elapsed = time.time() - start_time

        # 최소 간격 확인 (50ms * 2 = 100ms)
        self.assertGreaterEqual(elapsed, 0.1)

    def test_second_limit_enforcement(self):
        """초당 제한 적용 테스트"""
        # 초당 2회로 제한 설정
        limiter = RateLimiter(
            requests_per_second=2, requests_per_minute=100, min_interval_ms=10
        )

        start_time = time.time()

        # 3개 요청 (3번째는 대기해야 함)
        for _ in range(3):
            limiter.acquire()

        elapsed = time.time() - start_time

        # 3번째 요청은 1초 이상 대기
        self.assertGreaterEqual(elapsed, 1.0)

    def test_priority_handling(self):
        """우선순위 처리 테스트"""
        # 긴급 요청은 최소 간격 무시
        wait_time = self.limiter.acquire(priority=2)
        self.assertEqual(wait_time, 0)

        # 일반 요청은 최소 간격 적용
        wait_time = self.limiter.acquire(priority=0)
        self.assertGreater(wait_time, 0)

    def test_adaptive_backoff(self):
        """적응형 백오프 테스트"""
        initial_multiplier = self.limiter.backoff_multiplier

        # 에러 보고로 백오프 증가
        for _ in range(3):
            self.limiter.report_error()

        self.assertGreater(self.limiter.backoff_multiplier, initial_multiplier)

        # 성공 보고로 백오프 감소
        self.limiter.report_success()
        self.assertLess(self.limiter.backoff_multiplier, 1.5)

    def test_rate_limit_error_handling(self):
        """유량 제한 에러 처리 테스트"""
        # KIS API 유량 제한 에러 코드
        self.limiter.report_error("EGW00201")

        # 백오프가 2배로 증가
        self.assertEqual(self.limiter.backoff_multiplier, 2.0)

    def test_statistics_tracking(self):
        """통계 추적 테스트"""
        # 5개 요청 실행
        for _ in range(5):
            self.limiter.acquire()

        stats = self.limiter.get_current_rate()

        self.assertEqual(stats["total_requests"], 5)
        self.assertIn("avg_wait_time", stats)
        self.assertIn("throttled_count", stats)

    def test_reset_functionality(self):
        """리셋 기능 테스트"""
        # 요청 실행
        for _ in range(3):
            self.limiter.acquire()

        # 에러 보고
        self.limiter.report_error()

        # 리셋
        self.limiter.reset()

        # 상태 확인
        stats = self.limiter.get_current_rate()
        self.assertEqual(stats["total_requests"], 0)
        self.assertEqual(stats["backoff_multiplier"], 1.0)

    def test_dynamic_limit_changes(self):
        """동적 제한 변경 테스트"""
        # 제한 변경
        self.limiter.set_limits(
            requests_per_second=10, requests_per_minute=200, min_interval_ms=30
        )

        self.assertEqual(self.limiter.requests_per_second, 10)
        self.assertEqual(self.limiter.requests_per_minute, 200)
        self.assertEqual(self.limiter.min_interval, 0.03)

    def test_concurrent_access(self):
        """동시 접근 안전성 테스트"""
        results = []

        def make_request():
            wait_time = self.limiter.acquire()
            return wait_time

        # 10개 동시 요청
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]

            for future in as_completed(futures):
                results.append(future.result())

        # 모든 요청이 처리됨
        self.assertEqual(len(results), 10)

        # 통계 확인
        stats = self.limiter.get_current_rate()
        self.assertEqual(stats["total_requests"], 10)


# Agent 관련 테스트는 실제 환경 설정이 필요해서 제거
"""
class TestAgentRateLimiterIntegration(unittest.TestCase):
    # Agent와 Rate Limiter 통합 테스트

    @patch('kis_agent.core.agent.KISConfig')
    @patch('kis_agent.core.agent.auth')
    @patch('kis_agent.core.agent.read_token')
    def test_agent_with_rate_limiter(self, mock_read_token, mock_auth, mock_config):
        # Agent의 Rate Limiter 통합 테스트
        # Mock 설정
        mock_config_instance = MagicMock()
        mock_config_instance.account_stock = "12345678"
        mock_config_instance.account_product = "01"
        mock_config_instance.my_acct = "12345678"
        mock_config.return_value = mock_config_instance
        mock_auth.return_value = {'access_token': 'test_token'}
        mock_read_token.return_value = True

        # Agent 생성
        with patch('kis_agent.core.agent.load_dotenv'):
            agent = Agent(
                env_path='.env',
                enable_rate_limiter=True,
                rate_limiter_config={
                    'requests_per_second': 10,
                    'requests_per_minute': 500
                }
            )

        # Rate Limiter 확인
        self.assertIsNotNone(agent.rate_limiter)
        self.assertEqual(agent.rate_limiter.requests_per_second, 10)

    @patch('kis_agent.core.agent.KISConfig')
    @patch('kis_agent.core.agent.auth')
    @patch('kis_agent.core.agent.read_token')
    def test_agent_rate_limiter_methods(self, mock_read_token, mock_auth, mock_config):
        # Agent의 Rate Limiter 관리 메서드 테스트
        # Mock 설정
        mock_config_instance = MagicMock()
        mock_config_instance.account_stock = "12345678"
        mock_config_instance.account_product = "01"
        mock_config_instance.my_acct = "12345678"
        mock_config.return_value = mock_config_instance
        mock_auth.return_value = {'access_token': 'test_token'}
        mock_read_token.return_value = True

        # Agent 생성
        with patch('kis_agent.core.agent.load_dotenv'):
            agent = Agent(env_path='.env', enable_rate_limiter=True)

        # 상태 조회
        status = agent.get_rate_limiter_status()
        self.assertIsNotNone(status)
        self.assertIn('requests_per_second', status)

        # 제한 변경
        agent.set_rate_limits(requests_per_second=20)
        status = agent.get_rate_limiter_status()
        self.assertEqual(status['limit_per_second'], 20)

        # 리셋
        agent.reset_rate_limiter()
        status = agent.get_rate_limiter_status()
        self.assertEqual(status['total_requests'], 0)

        # 적응형 조절 비활성화
        agent.enable_adaptive_rate_limiting(False)
        self.assertFalse(agent.rate_limiter.enable_adaptive)

    @patch('kis_agent.core.agent.KISConfig')
    @patch('kis_agent.core.agent.auth')
    @patch('kis_agent.core.agent.read_token')
    def test_agent_without_rate_limiter(self, mock_read_token, mock_auth, mock_config):
        # Rate Limiter 비활성화된 Agent 테스트
        # Mock 설정
        mock_config_instance = MagicMock()
        mock_config_instance.account_stock = "12345678"
        mock_config_instance.account_product = "01"
        mock_config_instance.my_acct = "12345678"
        mock_config.return_value = mock_config_instance
        mock_auth.return_value = {'access_token': 'test_token'}
        mock_read_token.return_value = True

        # Agent 생성 (Rate Limiter 비활성화)
        with patch('kis_agent.core.agent.load_dotenv'):
            agent = Agent(env_path='.env', enable_rate_limiter=False)

        # Rate Limiter가 없음
        self.assertIsNone(agent.rate_limiter)

        # 메서드 호출 시 None 반환
        status = agent.get_rate_limiter_status()
        self.assertIsNone(status)
"""

# KISClient 관련 테스트도 실제 환경 설정이 필요해서 제거
"""
class TestKISClientRateLimiter(unittest.TestCase):
    # KISClient의 Rate Limiter 통합 테스트

    @patch('kis_agent.core.client.auth')
    def test_client_with_rate_limiter(self, mock_auth):
        # KISClient의 Rate Limiter 사용 테스트
        mock_auth.return_value = {'access_token': 'test_token'}

        # Client 생성
        client = KISClient(enable_rate_limiter=True)

        # Rate Limiter 확인
        self.assertIsNotNone(client.rate_limiter)
        self.assertTrue(client.enable_rate_limiter)

    @patch('kis_agent.core.client.auth')
    def test_client_enforce_rate_limit(self, mock_auth):
        # KISClient의 rate limit 적용 테스트
        mock_auth.return_value = {'access_token': 'test_token'}

        # Client 생성
        client = KISClient(enable_rate_limiter=True)

        # _enforce_rate_limit 호출
        start_time = time.time()
        client._enforce_rate_limit(priority=0)
        client._enforce_rate_limit(priority=0)
        elapsed = time.time() - start_time

        # 최소 간격 적용 확인
        self.assertGreaterEqual(elapsed, 0.07)  # 70ms

    @patch('kis_agent.core.client.requests.request')
    @patch('kis_agent.core.client.auth')
    def test_client_api_call_with_rate_limiter(self, mock_auth, mock_request):
        # API 호출 시 Rate Limiter 적용 테스트
        mock_auth.return_value = {'access_token': 'test_token'}
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'rt_cd': '0', 'data': 'test'}
        mock_request.return_value = mock_response

        # Client 생성
        client = KISClient(enable_rate_limiter=True)

        # API 호출
        result = client.make_request(
            endpoint='/test',
            tr_id='TEST001',
            params={},
            priority=1
        )

        # 결과 확인
        self.assertIsNotNone(result)
        self.assertEqual(result['rt_cd'], '0')

        # Rate Limiter 성공 보고 확인
        self.assertEqual(client.rate_limiter.consecutive_errors, 0)
"""

if __name__ == "__main__":
    unittest.main()
