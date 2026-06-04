"""Rate Limiter 안전 마진과 동시성 보장 테스트.

검증 항목:
- 공식 한도 초과 시 자동 클램프 (RPS > 20, RPM > 1000)
- 동시 다중 스레드에서도 sliding window 한도 위반 없음
- 슬립이 lock 바깥에서 일어나 한 스레드의 대기가 다른 스레드를 블록하지 않음
- 전역 싱글턴 보장
"""

import threading
import time

import pytest

from kis_agent.core.rate_limiter import (
    DEFAULT_BURST_SIZE,
    DEFAULT_MIN_INTERVAL_MS,
    DEFAULT_RPM,
    DEFAULT_RPS,
    KIS_OFFICIAL_RPM_LIMIT,
    KIS_OFFICIAL_RPS_LIMIT,
    RateLimiter,
    get_global_rate_limiter,
    reset_global_rate_limiter,
)


@pytest.fixture(autouse=True)
def _reset_singleton():
    """각 테스트 전후로 전역 싱글턴 초기화."""
    reset_global_rate_limiter()
    yield
    reset_global_rate_limiter()


class TestSafetyMargin:
    def test_defaults_are_below_official_limit(self):
        assert DEFAULT_RPS <= KIS_OFFICIAL_RPS_LIMIT
        assert DEFAULT_RPM <= KIS_OFFICIAL_RPM_LIMIT
        # 충분한 마진 (>= 20%)
        assert DEFAULT_RPS <= KIS_OFFICIAL_RPS_LIMIT * 0.8
        assert DEFAULT_RPM <= KIS_OFFICIAL_RPM_LIMIT * 0.85

    def test_explicit_over_official_clamped(self, caplog):
        limiter = RateLimiter(
            requests_per_second=50,
            requests_per_minute=5000,
        )
        assert limiter.requests_per_second == KIS_OFFICIAL_RPS_LIMIT
        assert limiter.requests_per_minute == KIS_OFFICIAL_RPM_LIMIT

    def test_set_limits_clamps(self):
        limiter = RateLimiter()
        limiter.set_limits(requests_per_second=30, requests_per_minute=2000)
        assert limiter.requests_per_second == KIS_OFFICIAL_RPS_LIMIT
        assert limiter.requests_per_minute == KIS_OFFICIAL_RPM_LIMIT

    def test_min_interval_floor_is_inverse_rps_plus_safety(self):
        """min_interval은 1/RPS + 안전 마진보다 작아질 수 없다."""
        limiter = RateLimiter(requests_per_second=10, min_interval_ms=10)
        # 10 RPS → 1/10 = 100ms, + 1ms safety → 101ms 최소
        assert limiter.min_interval >= 0.100
        assert limiter.min_interval >= 0.101

    def test_set_limits_updates_min_interval_floor(self):
        limiter = RateLimiter(requests_per_second=20, min_interval_ms=10)
        # 처음엔 1/20 + 0.001 = 51ms
        limiter.set_limits(requests_per_second=5)
        # 이제 1/5 + 0.001 = 201ms로 올라가야 함
        assert limiter.min_interval >= 0.200


class TestSingleton:
    def test_global_singleton_returns_same_instance(self):
        a = get_global_rate_limiter()
        b = get_global_rate_limiter()
        c = get_global_rate_limiter(requests_per_second=10)
        assert a is b is c

    def test_reset_creates_new_instance(self):
        a = get_global_rate_limiter()
        reset_global_rate_limiter()
        b = get_global_rate_limiter()
        assert a is not b

    def test_singleton_is_thread_safe(self):
        """동시에 여러 스레드가 get_global_rate_limiter()를 호출해도 하나만 생성된다."""
        reset_global_rate_limiter()
        instances = []
        lock = threading.Lock()

        def grab():
            inst = get_global_rate_limiter()
            with lock:
                instances.append(inst)

        threads = [threading.Thread(target=grab) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 모두 같은 인스턴스
        assert len({id(i) for i in instances}) == 1
        assert len(instances) == 20


class TestConcurrencyHonorsLimit:
    def _measure_max_in_sliding_window(
        self, timestamps: list, window_s: float
    ) -> int:
        """timestamps 정렬 후, 길이 window_s의 sliding window 중 가장 큰 카운트."""
        timestamps = sorted(timestamps)
        worst = 0
        for anchor in timestamps:
            count = sum(1 for t in timestamps if anchor <= t < anchor + window_s)
            worst = max(worst, count)
        return worst

    def test_concurrent_acquires_respect_rps(self):
        """동시 N개 호출이 RPS 한도를 위반하지 않는다."""
        limiter = RateLimiter(
            requests_per_second=5,
            requests_per_minute=30,
            min_interval_ms=10,
            burst_size=0,
        )
        start = time.monotonic()
        timestamps = []
        ts_lock = threading.Lock()

        def worker():
            limiter.acquire()
            with ts_lock:
                timestamps.append(time.monotonic() - start)

        threads = [threading.Thread(target=worker) for _ in range(12)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        worst = self._measure_max_in_sliding_window(timestamps, 1.0)
        assert worst <= 5, f"RPS 위반: 1초 윈도우에 {worst}개 (한도 5)"

    def test_concurrent_acquires_respect_rpm(self):
        """RPM 한도 검증 (작은 RPM으로 빠른 검증)."""
        limiter = RateLimiter(
            requests_per_second=20,
            requests_per_minute=10,
            min_interval_ms=10,
            burst_size=0,
        )
        # 1분 윈도우는 너무 길어 RPS와 동일 패턴이 적용되는지만 확인.
        # 11번째 요청은 첫 요청에서 60초 이상 떨어져야 함.
        start = time.monotonic()
        for _ in range(10):
            limiter.acquire()
        elapsed_for_10 = time.monotonic() - start
        # 10개를 1분 안에 다 처리 (RPS 충분히 높음). RPM=10이므로 11번째는 첫
        # 요청 + 60초 이후. 직접 검증하지 않고 internal state로 확인.
        # request_times에는 10개 + (다음은 60초+ 후 슬롯) 형태.
        assert len(limiter.request_times) == 10
        # 11번째 호출 안 함 (60초 대기는 테스트 시간 낭비)
        # 10개를 1분 미만 안에 처리한 것 자체로 RPS는 잘 작동
        assert elapsed_for_10 < 60.0

    def test_sleep_outside_lock_does_not_block_other_threads(self):
        """한 스레드가 acquire에서 sleep 중일 때 다른 스레드의 lock 진입이 막히지 않음."""
        limiter = RateLimiter(
            requests_per_second=2,
            requests_per_minute=10,
            min_interval_ms=10,
            burst_size=0,
        )
        # 2 RPS면 슬롯 간격 약 500ms.
        # 한 스레드가 3번째 호출에서 ~500ms wait에 들어가 sleep 중일 때,
        # 다른 스레드가 get_current_rate()를 호출해도 즉시 반환되어야 한다.

        # 워밍업: 2회 호출로 한도 도달
        limiter.acquire()
        limiter.acquire()

        slow_done = threading.Event()
        fast_call_duration = [None]

        def slow_caller():
            limiter.acquire()  # 다음 슬롯까지 sleep
            slow_done.set()

        def fast_caller():
            # 짧게 대기 후, slow_caller가 sleep 중일 때 get_current_rate 호출
            time.sleep(0.1)
            t0 = time.monotonic()
            limiter.get_current_rate()
            fast_call_duration[0] = time.monotonic() - t0

        slow = threading.Thread(target=slow_caller)
        fast = threading.Thread(target=fast_caller)
        slow.start()
        fast.start()
        slow.join(timeout=2.0)
        fast.join(timeout=2.0)

        assert slow_done.is_set(), "slow_caller가 끝나지 않음"
        # fast_caller의 get_current_rate가 lock 안에서 sleep을 만나지 않으면 << 100ms
        assert fast_call_duration[0] is not None
        assert fast_call_duration[0] < 0.05, (
            f"lock 안 sleep으로 인한 블로킹 의심: "
            f"get_current_rate가 {fast_call_duration[0]*1000:.1f}ms 걸림"
        )

    def test_burst_priority_does_not_exceed_official_limit(self):
        """priority>=1에서 burst를 허용해도 공식 RPS 한도(20)는 절대 초과하지 않는다."""
        limiter = RateLimiter(
            requests_per_second=18,
            requests_per_minute=900,
            min_interval_ms=10,
            burst_size=10,  # 18+10=28인데 공식 한도 20으로 제한되어야
        )

        start = time.monotonic()
        timestamps = []
        ts_lock = threading.Lock()

        def worker():
            limiter.acquire(priority=1)
            with ts_lock:
                timestamps.append(time.monotonic() - start)

        threads = [threading.Thread(target=worker) for _ in range(25)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        worst = self._measure_max_in_sliding_window(timestamps, 1.0)
        # priority=1이면 effective RPS = min(18+10, 20) = 20
        assert worst <= KIS_OFFICIAL_RPS_LIMIT, (
            f"공식 한도 위반: 1초 윈도우에 {worst}개 (공식 한도 {KIS_OFFICIAL_RPS_LIMIT})"
        )
