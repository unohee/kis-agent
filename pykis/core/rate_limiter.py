import time
import threading
from collections import deque
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    한국투자증권 API 유량 제한 관리 클래스
    
    한국투자증권 API 제한사항:
    - 초당 최대 20회 호출
    - 분당 최대 1000회 호출  
    - 연속 호출 시 최소 50ms 간격 권장
    """
    
    def __init__(
        self,
        requests_per_second: int = 18,  # 안정적 운영 기준 (API 최대 20회/초)
        requests_per_minute: int = 900,  # 안정적 운영 기준 (API 최대 1000회/분)
        min_interval_ms: int = 50,       # 안전한 최소 간격 (50ms)
        burst_size: int = 10,             # 순간 처리량 (안정성 우선)
        enable_adaptive: bool = True      # 적응형 속도 조절 활성화
    ):
        """
        Rate Limiter 초기화
        
        Args:
            requests_per_second: 초당 최대 요청 수
            requests_per_minute: 분당 최대 요청 수
            min_interval_ms: 연속 호출 최소 간격 (밀리초)
            burst_size: 순간적으로 허용할 버스트 크기
            enable_adaptive: 적응형 속도 조절 활성화 여부
        """
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.min_interval = min_interval_ms / 1000.0
        self.burst_size = burst_size
        self.enable_adaptive = enable_adaptive
        
        # 요청 기록 관리
        self.request_times = deque(maxlen=requests_per_minute)
        self.lock = threading.Lock()
        
        # 마지막 요청 시간
        self.last_request_time = 0.0
        
        # 적응형 속도 조절 파라미터
        self.consecutive_errors = 0
        self.backoff_multiplier = 1.0
        self.max_backoff = 5.0
        
        # 통계 정보
        self.total_requests = 0
        self.total_wait_time = 0.0
        self.throttled_count = 0
        
    def acquire(self, priority: int = 0) -> float:
        """
        API 호출 권한 획득 (필요시 대기)
        
        Args:
            priority: 요청 우선순위 (0=일반, 1=중요, 2=긴급)
            
        Returns:
            대기한 시간 (초)
        """
        with self.lock:
            current_time = time.time()
            wait_time = 0.0
            
            # 1. 최소 간격 체크
            min_interval = self.min_interval * self.backoff_multiplier
            if priority < 2:  # 긴급이 아닌 경우에만 최소 간격 적용
                elapsed = current_time - self.last_request_time
                if elapsed < min_interval:
                    wait_time = min_interval - elapsed
                    time.sleep(wait_time)
                    current_time = time.time()
            
            # 2. 초당 제한 체크
            second_ago = current_time - 1.0
            recent_second_requests = [t for t in self.request_times if t > second_ago]
            
            if len(recent_second_requests) >= self.requests_per_second:
                # 버스트 체크
                if priority == 0 or len(recent_second_requests) >= self.requests_per_second + self.burst_size:
                    wait_needed = 1.0 - (current_time - recent_second_requests[0])
                    if wait_needed > 0:
                        wait_time += wait_needed
                        time.sleep(wait_needed)
                        current_time = time.time()
                        self.throttled_count += 1
            
            # 3. 분당 제한 체크
            minute_ago = current_time - 60.0
            recent_minute_requests = [t for t in self.request_times if t > minute_ago]
            
            if len(recent_minute_requests) >= self.requests_per_minute:
                wait_needed = 60.0 - (current_time - recent_minute_requests[0])
                if wait_needed > 0:
                    wait_time += wait_needed
                    logger.warning(f"분당 제한 도달. {wait_needed:.2f}초 대기 필요")
                    time.sleep(wait_needed)
                    current_time = time.time()
                    self.throttled_count += 1
            
            # 요청 시간 기록
            self.request_times.append(current_time)
            self.last_request_time = current_time
            
            # 통계 업데이트
            self.total_requests += 1
            self.total_wait_time += wait_time
            
            if wait_time > 0:
                logger.debug(f"Rate limit 대기: {wait_time:.3f}초 (우선순위: {priority})")
            
            return wait_time
    
    def report_success(self):
        """API 호출 성공 보고 - 백오프 리셋"""
        if self.enable_adaptive:
            with self.lock:
                self.consecutive_errors = 0
                if self.backoff_multiplier > 1.0:
                    self.backoff_multiplier = max(1.0, self.backoff_multiplier * 0.9)
                    logger.debug(f"백오프 감소: {self.backoff_multiplier:.2f}x")
    
    def report_error(self, error_code: Optional[str] = None):
        """
        API 호출 실패 보고 - 백오프 증가
        
        Args:
            error_code: 에러 코드 (유량 제한 관련 에러 식별용)
        """
        if self.enable_adaptive:
            with self.lock:
                self.consecutive_errors += 1
                
                # 유량 제한 에러인 경우 더 강하게 백오프
                if error_code in ['EGW00201', 'EGW00202', 'EGW00203']:  # KIS API 유량 제한 에러 코드
                    self.backoff_multiplier = min(self.max_backoff, self.backoff_multiplier * 2.0)
                    logger.warning(f"유량 제한 감지. 백오프 증가: {self.backoff_multiplier:.2f}x")
                elif self.consecutive_errors >= 3:
                    self.backoff_multiplier = min(self.max_backoff, self.backoff_multiplier * 1.5)
                    logger.debug(f"연속 에러 {self.consecutive_errors}회. 백오프: {self.backoff_multiplier:.2f}x")
    
    def get_current_rate(self) -> Dict[str, Any]:
        """현재 유량 상태 조회"""
        with self.lock:
            current_time = time.time()
            second_ago = current_time - 1.0
            minute_ago = current_time - 60.0
            
            recent_second = len([t for t in self.request_times if t > second_ago])
            recent_minute = len([t for t in self.request_times if t > minute_ago])
            
            return {
                "requests_per_second": recent_second,
                "requests_per_minute": recent_minute,
                "limit_per_second": self.requests_per_second,
                "limit_per_minute": self.requests_per_minute,
                "backoff_multiplier": self.backoff_multiplier,
                "total_requests": self.total_requests,
                "throttled_count": self.throttled_count,
                "avg_wait_time": self.total_wait_time / max(1, self.total_requests)
            }
    
    def reset(self):
        """Rate limiter 상태 초기화"""
        with self.lock:
            self.request_times.clear()
            self.last_request_time = 0.0
            self.consecutive_errors = 0
            self.backoff_multiplier = 1.0
            self.total_requests = 0
            self.total_wait_time = 0.0
            self.throttled_count = 0
            logger.info("Rate limiter 초기화 완료")
    
    def set_limits(
        self,
        requests_per_second: Optional[int] = None,
        requests_per_minute: Optional[int] = None,
        min_interval_ms: Optional[int] = None
    ):
        """
        런타임에 제한 값 변경
        
        Args:
            requests_per_second: 새로운 초당 제한
            requests_per_minute: 새로운 분당 제한  
            min_interval_ms: 새로운 최소 간격 (밀리초)
        """
        with self.lock:
            if requests_per_second is not None:
                self.requests_per_second = requests_per_second
                logger.info(f"초당 제한 변경: {requests_per_second}")
            
            if requests_per_minute is not None:
                self.requests_per_minute = requests_per_minute
                self.request_times = deque(self.request_times, maxlen=requests_per_minute)
                logger.info(f"분당 제한 변경: {requests_per_minute}")
            
            if min_interval_ms is not None:
                self.min_interval = min_interval_ms / 1000.0
                logger.info(f"최소 간격 변경: {min_interval_ms}ms")