"""한국투자증권 API 유량 제한 관리.

전역 싱글턴 RateLimiter로 모든 KISClient·Agent의 호출을 통합 제어한다.

## API 한도와 안전 마진

| 항목 | 공식 스펙 | 본 라이브러리 기본값 | 마진 |
|------|----------|--------------------|------|
| 초당 | 20회 | **15회** | 25% (5회 여유) |
| 분당 | 1000회 | **800회** | 20% (200회 여유) |
| 최소 간격 | — | **70ms** | 15 RPS의 이론적 67ms + 3ms jitter |

마진을 25%까지 두는 이유:
- 네트워크 jitter와 OS sleep 정확도 오차 누적
- burst 사용 시에도 절대 한도(20 RPS) 위반 방지
- 분당 한도는 sliding window라 burst가 쌓이면 위반 위험이 큼

## 동시성 설계

- ``time.sleep()``을 lock **바깥에서** 수행 → 한 스레드의 대기가 다른 스레드를 블록하지 않음
- 슬롯 예약(reserved_until) 방식으로 동시 호출 시 정확한 다음 슬롯 시간 분배
- 전역 싱글턴 보장 — 명시적 rate_limiter 미전달 시 항상 공유 인스턴스 사용
"""

import logging
import threading
import time
from collections import deque
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# KIS 공식 스펙 & 권장 기본값 (단일 진실의 출처)
# ============================================================================

# KIS 공식 API 한도
KIS_OFFICIAL_RPS_LIMIT = 20
KIS_OFFICIAL_RPM_LIMIT = 1000

# 본 라이브러리 안전 기본값 (공식 한도의 75~80%)
DEFAULT_RPS = 15
DEFAULT_RPM = 800
DEFAULT_MIN_INTERVAL_MS = 70
DEFAULT_BURST_SIZE = 3  # priority>=1 사용 시에도 RPS + 3 <= 20 보장
DEFAULT_MAX_BACKOFF = 5.0


# ============================================================================
# 전역 싱글턴 Rate Limiter
# ============================================================================

_global_rate_limiter: Optional["RateLimiter"] = None
_global_rate_limiter_lock = threading.Lock()


def get_global_rate_limiter(
    requests_per_second: int = DEFAULT_RPS,
    requests_per_minute: int = DEFAULT_RPM,
    min_interval_ms: int = DEFAULT_MIN_INTERVAL_MS,
    burst_size: int = DEFAULT_BURST_SIZE,
    enable_adaptive: bool = True,
) -> "RateLimiter":
    """전역 싱글턴 Rate Limiter 인스턴스를 반환한다.

    모든 KISClient/Agent가 동일한 Rate Limiter를 공유하여 API 호출 제한을
    프로세스 전역으로 관리한다. 첫 호출 시 인스턴스가 생성되고, 이후 호출은
    동일 인스턴스를 반환한다 (인자는 무시).

    Note:
        설정 변경이 필요하면 ``limiter.set_limits()`` 또는
        ``reset_global_rate_limiter()`` 후 재생성을 사용.
    """
    global _global_rate_limiter

    if _global_rate_limiter is None:
        with _global_rate_limiter_lock:
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
                    f"{requests_per_minute} RPM / {min_interval_ms}ms 간격 / "
                    f"burst {burst_size}"
                )
    else:
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
    """전역 Rate Limiter를 초기화한다.

    테스트나 설정 변경이 필요할 때 호출. 다음
    ``get_global_rate_limiter()`` 호출 시 새 인스턴스가 생성된다.
    """
    global _global_rate_limiter

    with _global_rate_limiter_lock:
        if _global_rate_limiter is not None:
            _global_rate_limiter.reset()
            _global_rate_limiter = None
            logger.info("전역 Rate Limiter 리셋 완료")


class RateLimiter:
    """한국투자증권 API 유량 제한 관리 클래스.

    안전 마진 (공식 스펙 대비 기본값):
    - 초당: 공식 20회 → 본 라이브러리 15회 (75%)
    - 분당: 공식 1000회 → 본 라이브러리 800회 (80%)
    - 최소 간격 70ms (15 RPS 이론적 67ms + 3ms jitter)

    동시성:
    - acquire() 내부의 ``time.sleep()``을 lock **바깥에서** 호출하여
      한 스레드의 대기가 다른 스레드를 블록하지 않음
    - "슬롯 예약" 방식으로 동시 N개 호출이 들어와도 각 호출에 서로 다른
      미래 슬롯 시간을 분배하여 순차적으로 통과시킴
    """

    def __init__(
        self,
        requests_per_second: int = DEFAULT_RPS,
        requests_per_minute: int = DEFAULT_RPM,
        min_interval_ms: int = DEFAULT_MIN_INTERVAL_MS,
        burst_size: int = DEFAULT_BURST_SIZE,
        enable_adaptive: bool = True,
    ):
        # 절대 한도 위반 방지 — KIS_OFFICIAL_RPS_LIMIT 초과 금지
        if requests_per_second > KIS_OFFICIAL_RPS_LIMIT:
            logger.warning(
                f"requests_per_second={requests_per_second}가 공식 한도 "
                f"{KIS_OFFICIAL_RPS_LIMIT}을 초과합니다. {KIS_OFFICIAL_RPS_LIMIT}로 클램프."
            )
            requests_per_second = KIS_OFFICIAL_RPS_LIMIT
        if requests_per_minute > KIS_OFFICIAL_RPM_LIMIT:
            logger.warning(
                f"requests_per_minute={requests_per_minute}가 공식 한도 "
                f"{KIS_OFFICIAL_RPM_LIMIT}을 초과합니다. {KIS_OFFICIAL_RPM_LIMIT}로 클램프."
            )
            requests_per_minute = KIS_OFFICIAL_RPM_LIMIT

        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        # min_interval은 명시값과 (1/RPS + safety) 중 더 큰 값으로 강제.
        # 1초 sliding window 내 N개 제한을 확실히 지키려면 슬롯 간격이 1/RPS보다
        # 조금 커야 함. 그렇지 않으면 윈도우 경계와 슬롯이 우연히 정확히 겹치며
        # N+1개가 1초 안에 들어올 수 있다 (예: 5 RPS에 200ms 간격이면 윈도우
        # [t-ε, t+1-ε)에 6개). 실제 sleep의 undershoot와 스레드 재개 편차도
        # 고려해 20ms safety를 둔다.
        rps_floor = (1.0 / requests_per_second) + 0.020
        self.min_interval = max(min_interval_ms / 1000.0, rps_floor)
        self.burst_size = burst_size
        self.enable_adaptive = enable_adaptive

        # 요청 기록 (RPM과 동일 길이로 deque maxlen — over-count 방지)
        self.request_times: deque = deque(maxlen=requests_per_minute)
        self.lock = threading.Lock()

        # 슬롯 예약: 다음 호출이 통과 가능한 시점.
        # 동시 N개 호출이 들어와도 lock 안에서 각자 서로 다른 미래 시점을 받아간다.
        self.reserved_until: float = 0.0

        # 적응형 백오프
        self.consecutive_errors = 0
        self.backoff_multiplier = 1.0
        self.max_backoff = DEFAULT_MAX_BACKOFF

        # 통계
        self.total_requests = 0
        self.total_wait_time = 0.0
        self.throttled_count = 0

    def acquire(self, priority: int = 0) -> float:
        """API 호출 권한 획득 (필요 시 대기).

        동시성: 슬롯 예약 시간을 lock 안에서 계산하고, 실제 ``time.sleep()``은
        lock 바깥에서 수행. 한 스레드의 대기가 다른 스레드를 블록하지 않는다.

        절대 한도 보호: priority와 무관하게 RPS·RPM 한도를 절대 위반하지 않는다
        (이전 구현은 priority>=1이면 RPS + burst까지 허용해 한도 초과 위험이 있었음).

        Args:
            priority: 우선순위 (0=일반, 1=중요, 2=긴급). 현재 구현에서는 RPS/RPM
                절대 한도를 우회하는 용도로 사용되지 않으며, 적응형 백오프와
                burst 허용 여부에만 영향을 준다.

        Returns:
            대기한 시간 (초).
        """
        with self.lock:
            now = time.monotonic()

            # 1) 최소 간격: 마지막 요청 또는 예약된 슬롯 중 더 큰 값 기준
            min_interval = self.min_interval * self.backoff_multiplier
            earliest = max(self.reserved_until, 0.0) + min_interval

            # 슬립 정확도 jitter 보정: 1초 / 60초 윈도우 끝에 _SAFETY_PADDING_S
            # 만큼 추가 대기. monotonic 시계와 time.sleep()의 oversleep/undersleep
            # 누적으로 윈도우 경계 직전에 요청이 몰리는 것을 방지.
            # macOS/Linux의 time.sleep은 최대 ~10ms undersleep 발생할 수 있어
            # CI/macOS의 스레드 스케줄링 편차까지 고려해 50ms를 둔다. 경계에서
            # 실제 완료 시각이 앞당겨져 sliding-window 한도를 넘는 것을 막는다.
            _SAFETY_PADDING_S = 0.050

            # 2) 초당 한도: 1초 이내 요청이 RPS 이상이면 가장 오래된 요청
            #    + 1초 + padding이 다음 가용 시점. burst는 priority>=1에서만 허용하되,
            #    절대 한도(RPS + burst <= 공식 RPS 한도)는 클램프된 한도 내에서 안전.
            second_ago = now - 1.0
            recent_second = [t for t in self.request_times if t > second_ago]
            effective_rps = self.requests_per_second
            if priority >= 1:
                effective_rps = min(
                    self.requests_per_second + self.burst_size,
                    KIS_OFFICIAL_RPS_LIMIT,
                )
            if len(recent_second) >= effective_rps:
                next_second_slot = recent_second[0] + 1.0 + _SAFETY_PADDING_S
                earliest = max(earliest, next_second_slot)

            # 3) 분당 한도
            minute_ago = now - 60.0
            recent_minute = [t for t in self.request_times if t > minute_ago]
            if len(recent_minute) >= self.requests_per_minute:
                next_minute_slot = recent_minute[0] + 60.0 + _SAFETY_PADDING_S
                earliest = max(earliest, next_minute_slot)

            # 슬롯 예약: 이 시점을 다음 호출들이 참조해 순차적으로 미래를 받게 됨
            slot_time = max(earliest, now)
            self.reserved_until = slot_time

            wait_time = max(0.0, slot_time - now)
            if wait_time > 0:
                self.throttled_count += 1

            # 요청 기록은 lock 안에서 (예약된 슬롯 시간으로 기록)
            self.request_times.append(slot_time)
            self.total_requests += 1
            self.total_wait_time += wait_time

        # 실제 sleep은 lock 바깥에서 — 동시 요청 시 다른 스레드를 블록하지 않음
        if wait_time > 0:
            if wait_time >= 1.0:
                logger.info(f"Rate limit 대기: {wait_time:.2f}초 (우선순위={priority})")
            else:
                logger.debug(
                    f"Rate limit 대기: {wait_time:.3f}초 (우선순위={priority})"
                )
            time.sleep(wait_time)

        return wait_time

    def report_success(self):
        """API 호출 성공 보고 — 백오프 점진 감소."""
        if not self.enable_adaptive:
            return
        with self.lock:
            self.consecutive_errors = 0
            if self.backoff_multiplier > 1.0:
                self.backoff_multiplier = max(1.0, self.backoff_multiplier * 0.9)
                logger.debug(f"백오프 감소: {self.backoff_multiplier:.2f}x")

    def report_error(self, error_code: Optional[str] = None):
        """API 호출 실패 보고 — 백오프 증가.

        Args:
            error_code: KIS 에러 코드. EGW00201/00202/00203 (유량 제한 계열)은
                즉시 강한 백오프, 그 외는 연속 3회 이상일 때 완만한 백오프.
        """
        if not self.enable_adaptive:
            return
        with self.lock:
            self.consecutive_errors += 1
            if error_code in ("EGW00201", "EGW00202", "EGW00203"):
                self.backoff_multiplier = min(
                    self.max_backoff, self.backoff_multiplier * 2.0
                )
                logger.warning(
                    f"유량 제한 감지 ({error_code}). 백오프 증가: "
                    f"{self.backoff_multiplier:.2f}x"
                )
            elif self.consecutive_errors >= 3:
                self.backoff_multiplier = min(
                    self.max_backoff, self.backoff_multiplier * 1.5
                )
                logger.debug(
                    f"연속 에러 {self.consecutive_errors}회. 백오프: "
                    f"{self.backoff_multiplier:.2f}x"
                )

    def get_current_rate(self) -> Dict[str, Any]:
        """현재 유량 상태 스냅샷."""
        with self.lock:
            now = time.monotonic()
            second_ago = now - 1.0
            minute_ago = now - 60.0
            recent_second = sum(1 for t in self.request_times if t > second_ago)
            recent_minute = sum(1 for t in self.request_times if t > minute_ago)
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
        """Rate limiter 상태 초기화."""
        with self.lock:
            self.request_times.clear()
            self.reserved_until = 0.0
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
        """런타임에 제한 값 변경. 공식 한도 초과 시 자동 클램프."""
        with self.lock:
            if requests_per_second is not None:
                if requests_per_second > KIS_OFFICIAL_RPS_LIMIT:
                    logger.warning(
                        f"requests_per_second={requests_per_second}가 공식 한도 "
                        f"{KIS_OFFICIAL_RPS_LIMIT}을 초과. 클램프."
                    )
                    requests_per_second = KIS_OFFICIAL_RPS_LIMIT
                self.requests_per_second = requests_per_second
                # min_interval도 (1/RPS + safety) 이상 유지
                rps_floor = (1.0 / requests_per_second) + 0.001
                if self.min_interval < rps_floor:
                    self.min_interval = rps_floor
                logger.info(f"초당 제한 변경: {requests_per_second}")

            if requests_per_minute is not None:
                if requests_per_minute > KIS_OFFICIAL_RPM_LIMIT:
                    logger.warning(
                        f"requests_per_minute={requests_per_minute}가 공식 한도 "
                        f"{KIS_OFFICIAL_RPM_LIMIT}을 초과. 클램프."
                    )
                    requests_per_minute = KIS_OFFICIAL_RPM_LIMIT
                self.requests_per_minute = requests_per_minute
                self.request_times = deque(
                    self.request_times, maxlen=requests_per_minute
                )
                logger.info(f"분당 제한 변경: {requests_per_minute}")

            if min_interval_ms is not None:
                self.min_interval = min_interval_ms / 1000.0
                logger.info(f"최소 간격 변경: {min_interval_ms}ms")


__all__ = [
    "RateLimiter",
    "get_global_rate_limiter",
    "reset_global_rate_limiter",
    "KIS_OFFICIAL_RPS_LIMIT",
    "KIS_OFFICIAL_RPM_LIMIT",
    "DEFAULT_RPS",
    "DEFAULT_RPM",
    "DEFAULT_MIN_INTERVAL_MS",
    "DEFAULT_BURST_SIZE",
]
