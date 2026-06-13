"""Agent의 Rate Limiter 제어 메서드를 분리한 Mixin.

원래 ``Agent`` 클래스에 직접 정의되어 있던 4개의 rate-limiter 제어 메서드
(``get_rate_limiter_status``, ``set_rate_limits``, ``reset_rate_limiter``,
``enable_adaptive_rate_limiting``)를 별도 Mixin으로 옮긴 것.

분리 이유:
- 본 메서드들은 ``self.rate_limiter``에만 의존하며 다른 도메인 API와 결합이 없음
- 모두 단순 위임 layer (예외 처리·비활성 경고 외에는 로직 없음)
- ``TechnicalAnalysisMixin``/``MethodDiscoveryMixin``과 동일한 컨벤션
- ``Agent``의 LOC를 100줄 줄이고 도메인 API 코드와 인프라 제어 코드를 분리

사용자 입장의 API는 변경되지 않음 — ``agent.get_rate_limiter_status()``
등은 동일하게 호출 가능.
"""

import logging
from typing import Any, Dict, Optional


class RateLimiterControlMixin:
    """Agent의 Rate Limiter를 외부에서 제어하기 위한 Mixin.

    사용 측에서는 다음 속성이 셋업되어 있어야 한다:

    - ``self.rate_limiter``: ``RateLimiter`` 인스턴스 또는 ``None``
      (``Agent.__init__``에서 ``KISClient``의 rate limiter를 그대로 저장)
    """

    def get_rate_limiter_status(self) -> Optional[Dict[str, Any]]:
        """
        Rate Limiter 상태 조회

        Returns:
            Dict: Rate Limiter 상태 정보
                - requests_per_second: 현재 초당 요청 수
                - requests_per_minute: 현재 분당 요청 수
                - limit_per_second: 초당 제한
                - limit_per_minute: 분당 제한
                - backoff_multiplier: 백오프 배수
                - total_requests: 총 요청 수
                - throttled_count: 제한된 요청 수
                - avg_wait_time: 평균 대기 시간
            None: Rate Limiter가 비활성화된 경우

        Example:
            >>> status = agent.get_rate_limiter_status()
            >>> if status:
            ...     print(f"현재 요청률: {status['requests_per_second']}/초")
            ...     print(f"제한 도달 횟수: {status['throttled_count']}")
        """
        if self.rate_limiter:
            return self.rate_limiter.get_current_rate()
        return None

    def set_rate_limits(
        self,
        requests_per_second: Optional[int] = None,
        requests_per_minute: Optional[int] = None,
        min_interval_ms: Optional[int] = None,
    ) -> None:
        """
        Rate Limiter 제한 값 동적 변경

        Args:
            requests_per_second: 초당 최대 요청 수 (None이면 변경 안 함)
            requests_per_minute: 분당 최대 요청 수 (None이면 변경 안 함)
            min_interval_ms: 최소 간격 (밀리초) (None이면 변경 안 함)

        Example:
            >>> # 더 보수적인 설정으로 변경
            >>> agent.set_rate_limits(
            ...     requests_per_second=10,
            ...     requests_per_minute=500
            ... )
            >>>
            >>> # 최소 간격만 변경
            >>> agent.set_rate_limits(min_interval_ms=100)
        """
        if self.rate_limiter:
            self.rate_limiter.set_limits(
                requests_per_second=requests_per_second,
                requests_per_minute=requests_per_minute,
                min_interval_ms=min_interval_ms,
            )
            logging.info("Rate limits 업데이트 완료")
        else:
            logging.warning("Rate Limiter가 비활성화 상태입니다")

    def reset_rate_limiter(self) -> None:
        """
        Rate Limiter 상태 초기화

        모든 요청 기록과 통계를 초기화합니다.
        백오프 배수도 1.0으로 리셋됩니다.

        Example:
            >>> agent.reset_rate_limiter()
            >>> print("Rate limiter 초기화 완료")  # cxt-ignore: fake_execution
        """
        if self.rate_limiter:
            self.rate_limiter.reset()
            logging.info("Rate limiter 초기화 완료")
        else:
            logging.warning("Rate Limiter가 비활성화 상태입니다")

    def enable_adaptive_rate_limiting(self, enable: bool = True) -> None:
        """
        적응형 속도 조절 활성화/비활성화

        Args:
            enable: True면 활성화, False면 비활성화

        Example:
            >>> # 적응형 속도 조절 비활성화
            >>> agent.enable_adaptive_rate_limiting(False)
        """
        if self.rate_limiter:
            self.rate_limiter.enable_adaptive = enable
            status = "활성화" if enable else "비활성화"
            logging.info(f"적응형 속도 조절 {status}")
        else:
            logging.warning("Rate Limiter가 비활성화 상태입니다")


__all__ = ["RateLimiterControlMixin"]
