import logging
import threading
import time
from collections import deque
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# 전역 싱글턴 Rate Limiter
# ============================================================================

_global_rate_limiter: Optional["RateLimiter"] = None
_global_rate_limiter_lock = threading.Lock()


def get_global_rate_limiter(
    requests_per_second: int = 18,
    requests_per_minute: int = 900,
    min_interval_ms: int = 55,
    burst_size: int = 10,
    enable_adaptive: bool = True,
) -> "RateLimiter":
    """
    전역 싱글턴 Rate Limiter 인스턴스를 반환합니다.

    모든 KISClient와 Agent가 동일한 Rate Limiter를 공유하여
    API 호출 제한을 전역적으로 관리합니다.

    Args:
        requests_per_second: 초당 최대 요청 수 (기본값: 18, 첫 호출 시에만 적용)
        requests_per_minute: 분당 최대 요청 수 (기본값: 900, 첫 호출 시에만 적용)
        min_interval_ms: 연속 호출 최소 간격 (기본값: 55ms, 첫 호출 시에만 적용)
        burst_size: 순간 버스트 크기 (기본값: 10, 첫 호출 시에만 적용)
        enable_adaptive: 적응형 속도 조절 활성화 (기본값: True, 첫 호출 시에만 적용)

    Returns:
        RateLimiter: 전역 Rate Limiter 인스턴스

    Example:
        >>> from kis_agent.core.rate_limiter import get_global_rate_limiter
        >>> limiter = get_global_rate_limiter()
        >>> wait_time = limiter.acquire()
        >>> # API 호출 수행
        >>> limiter.report_success()

    Note:
        - 싱글턴 패턴: 첫 호출 시 인스턴스가 생성되며, 이후 호출은 동일한 인스턴스 반환
        - 설정 변경: 이미 생성된 후에는 전달된 설정이 무시됨
        - 런타임 설정 변경: limiter.set_limits() 메서드 사용
        - 완전 리셋: reset_global_rate_limiter() 호출 후 다시 get_global_rate_limiter() 호출

    Warning:
        이미 Rate Limiter가 생성된 상태에서 다른 설정으로 호출하면 경고 로그가 출력됩니다.
        이 경우 기존 설정이 유지됩니다.
    """
    global _global_rate_limiter

    if _global_rate_limiter is None:
        with _global_rate_limiter_lock:
            # Double-check locking
            if _global_rate_limiter is None:
                _global_rate_limiter = RateLimiter(
                    requests_per_second=requests_per_second,
                    requests_per_minute=requests_per_minute,
                    min_interval_ms=min_interval_ms,
                    burst_size=burst_size,
                    enable_adaptive=enable_adaptive,
                )
                logger.info(
                    f"전역 Rate Limiter 생성: {requests_per_second} RPS / "
                    f"{requests_per_minute} RPM / {min_interval_ms}ms 간격"
                )
    else:
        # 이미 생성된 상태에서 다른 설정으로 호출된 경우 경고
        current = _global_rate_limiter
        if (
            requests_per_second != current.requests_per_second
            or requests_per_minute != current.requests_per_minute
        ):
            logger.debug(
                f"전역 Rate Limiter가 이미 존재합니다. "
                f"전달된 설정 ({requests_per_second} RPS / {requests_per_minute} RPM)은 무시됩니다. "
                f"현재 설정: {current.requests_per_second} RPS / {current.requests_per_minute} RPM. "
                f"설정 변경은 limiter.set_limits() 또는 reset_global_rate_limiter() 사용"
            )

    return _global_rate_limiter


def reset_global_rate_limiter() -> None:
    """
    전역 Rate Limiter를 초기화합니다.

    테스트나 설정 변경이 필요한 경우 사용합니다.
    다음 get_global_rate_limiter() 호출 시 새 인스턴스가 생성됩니다.
    """
    global _global_rate_limiter

    with _global_rate_limiter_lock:
        if _global_rate_limiter is not None:
            _global_rate_limiter.reset()
            _global_rate_limiter = None
            logger.info("전역 Rate Limiter 리셋 완료")


class RateLimiter:
    """
    한국투자증권 API 유량 제한 관리 클래스

    실측 기반으로 최적화된 Rate Limiter로 API 제한을 효과적으로 관리합니다.

    API 제한사항 (2025.09.21 실측 기준):
    - 공식 스펙: 초당 최대 20회 / 분당 최대 1000회 호출
    - 안정 운영: 초당 15-18회 / 분당 800-900회 호출 (실제 안정 한계)
    - 연속 호출 시 최소 50ms 간격 권장
    - 적응형 백오프로 에러 시 자동 속도 조절

    Features:
    - 우선순위 기반 요청 처리 (긴급/중요/일반)
    - 순간 버스트 허용 (제한된 크기)
    - 에러 발생 시 자동 백오프 메커니즘
    - 실시간 성능 모니터링 및 통계
    - 런타임 설정 변경 지원

    Example:
        >>> limiter = RateLimiter(
        ...     requests_per_second=15,  # 보수적 설정
        ...     requests_per_minute=800,
        ...     enable_adaptive=True
        ... )
        >>> wait_time = limiter.acquire(priority=1)  # 중요 요청
        >>> # API 호출 수행
        >>> limiter.report_success()  # 성공 보고
    """

    def __init__(
        self,
        requests_per_second: int = 18,  # 안정적 운영 기준 (API 최대 20회/초)
        requests_per_minute: int = 900,  # 안정적 운영 기준 (API 최대 1000회/분)
        min_interval_ms: int = 50,  # 안전한 최소 간격 (50ms)
        burst_size: int = 10,  # 순간 처리량 (안정성 우선)
        enable_adaptive: bool = True,  # 적응형 속도 조절 활성화
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
                if (
                    priority == 0
                    or len(recent_second_requests)
                    >= self.requests_per_second + self.burst_size
                ):
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
                logger.debug(
                    f"Rate limit 대기: {wait_time:.3f}초 (우선순위: {priority})"
                )

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
                if error_code in [
                    "EGW00201",
                    "EGW00202",
                    "EGW00203",
                ]:  # KIS API 유량 제한 에러 코드
                    self.backoff_multiplier = min(
                        self.max_backoff, self.backoff_multiplier * 2.0
                    )
                    logger.warning(
                        f"유량 제한 감지. 백오프 증가: {self.backoff_multiplier:.2f}x"
                    )
                elif self.consecutive_errors >= 3:
                    self.backoff_multiplier = min(
                        self.max_backoff, self.backoff_multiplier * 1.5
                    )
                    logger.debug(
                        f"연속 에러 {self.consecutive_errors}회. 백오프: {self.backoff_multiplier:.2f}x"
                    )

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
                "avg_wait_time": self.total_wait_time / max(1, self.total_requests),
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
        min_interval_ms: Optional[int] = None,
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
                self.request_times = deque(
                    self.request_times, maxlen=requests_per_minute
                )
                logger.info(f"분당 제한 변경: {requests_per_minute}")

            if min_interval_ms is not None:
                self.min_interval = min_interval_ms / 1000.0
                logger.info(f"최소 간격 변경: {min_interval_ms}ms")
