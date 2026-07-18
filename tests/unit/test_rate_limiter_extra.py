"""RateLimiter의 비적응형과 분당 경계 분기 테스트."""

from unittest.mock import patch

from kis_agent.core.rate_limiter import RateLimiter


def test_non_adaptive_and_minute_window_reservation():
    limiter = RateLimiter(requests_per_second=5, requests_per_minute=1, enable_adaptive=False)
    limiter.report_success()
    limiter.report_error("EGW00201")
    assert limiter.backoff_multiplier == 1.0
    limiter.request_times.append(0.5)
    with patch("kis_agent.core.rate_limiter.time.monotonic", return_value=1.0), patch("kis_agent.core.rate_limiter.time.sleep"):
        assert limiter.acquire() > 59
