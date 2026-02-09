"""Rate Limiter and system management MCP tools"""

from typing import Any, Dict, Optional

from ..errors import InvalidParameterError
from ..server import get_agent, server


@server.tool()
async def get_rate_limiter_status() -> Dict[str, Any]:
    """Rate Limiter 상태 조회

    Returns:
        Dict: 현재 유량 상태 및 통계
            - requests_per_second: 최근 1초간 요청 수
            - requests_per_minute: 최근 1분간 요청 수
            - limit_per_second: 초당 최대 제한
            - limit_per_minute: 분당 최대 제한
            - backoff_multiplier: 현재 백오프 배수
            - total_requests: 총 요청 수
            - throttled_count: 제한으로 대기한 횟수
            - avg_wait_time: 평균 대기 시간
    """
    agent = get_agent()

    if not hasattr(agent, "client") or not agent.client:
        return {
            "success": False,
            "message": "Agent client가 초기화되지 않았습니다",
            "error_code": "CLIENT_NOT_INITIALIZED",
        }

    if not agent.client.enable_rate_limiter or not agent.client.rate_limiter:
        return {
            "success": False,
            "message": "Rate limiter가 비활성화되어 있습니다",
            "error_code": "RATE_LIMITER_DISABLED",
            "enabled": False,
        }

    status = agent.client.rate_limiter.get_current_rate()

    return {
        "success": True,
        "enabled": True,
        "status": status,
        "utilization": {
            "second": f"{status['requests_per_second']}/{status['limit_per_second']}",
            "minute": f"{status['requests_per_minute']}/{status['limit_per_minute']}",
            "second_percent": round(
                status["requests_per_second"]
                / max(1, status["limit_per_second"])
                * 100,
                2,
            ),
            "minute_percent": round(
                status["requests_per_minute"]
                / max(1, status["limit_per_minute"])
                * 100,
                2,
            ),
        },
    }


@server.tool()
async def reset_rate_limiter() -> Dict[str, Any]:
    """Rate Limiter 상태 초기화

    모든 요청 기록, 통계, 백오프 상태를 초기화합니다.

    Returns:
        Dict: 초기화 결과
    """
    agent = get_agent()

    if not hasattr(agent, "client") or not agent.client:
        return {
            "success": False,
            "message": "Agent client가 초기화되지 않았습니다",
            "error_code": "CLIENT_NOT_INITIALIZED",
        }

    if not agent.client.enable_rate_limiter or not agent.client.rate_limiter:
        return {
            "success": False,
            "message": "Rate limiter가 비활성화되어 있습니다",
            "error_code": "RATE_LIMITER_DISABLED",
        }

    agent.client.rate_limiter.reset()

    return {
        "success": True,
        "message": "Rate limiter가 초기화되었습니다",
        "status": agent.client.rate_limiter.get_current_rate(),
    }


@server.tool()
async def set_rate_limits(
    requests_per_second: Optional[int] = None,
    requests_per_minute: Optional[int] = None,
    min_interval_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """Rate Limiter 제한 값 설정

    런타임에 Rate Limiter의 제한 값을 변경합니다.

    Args:
        requests_per_second: 초당 최대 요청 수 (선택)
        requests_per_minute: 분당 최대 요청 수 (선택)
        min_interval_ms: 최소 요청 간격(ms) (선택)

    Returns:
        Dict: 설정 변경 결과 및 새로운 상태
    """
    agent = get_agent()

    if not hasattr(agent, "client") or not agent.client:
        return {
            "success": False,
            "message": "Agent client가 초기화되지 않았습니다",
            "error_code": "CLIENT_NOT_INITIALIZED",
        }

    if not agent.client.enable_rate_limiter or not agent.client.rate_limiter:
        return {
            "success": False,
            "message": "Rate limiter가 비활성화되어 있습니다",
            "error_code": "RATE_LIMITER_DISABLED",
        }

    # Validate parameters
    if requests_per_second is not None and (
        requests_per_second <= 0 or requests_per_second > 20
    ):
        raise InvalidParameterError(
            "requests_per_second",
            "초당 요청 수는 1-20 사이여야 합니다 (API 제한: 최대 20회/초)",
        )

    if requests_per_minute is not None and (
        requests_per_minute <= 0 or requests_per_minute > 1000
    ):
        raise InvalidParameterError(
            "requests_per_minute",
            "분당 요청 수는 1-1000 사이여야 합니다 (API 제한: 최대 1000회/분)",
        )

    if min_interval_ms is not None and (min_interval_ms < 0 or min_interval_ms > 1000):
        raise InvalidParameterError(
            "min_interval_ms", "최소 간격은 0-1000ms 사이여야 합니다"
        )

    # Apply changes
    changes = {}
    if requests_per_second is not None:
        changes["requests_per_second"] = requests_per_second
    if requests_per_minute is not None:
        changes["requests_per_minute"] = requests_per_minute
    if min_interval_ms is not None:
        changes["min_interval_ms"] = min_interval_ms

    if not changes:
        return {
            "success": False,
            "message": "변경할 값이 지정되지 않았습니다",
            "error_code": "NO_CHANGES",
        }

    agent.client.rate_limiter.set_limits(
        requests_per_second=requests_per_second,
        requests_per_minute=requests_per_minute,
        min_interval_ms=min_interval_ms,
    )

    return {
        "success": True,
        "message": "Rate limiter 설정이 변경되었습니다",
        "changes": changes,
        "new_status": agent.client.rate_limiter.get_current_rate(),
    }


@server.tool()
async def enable_adaptive_rate_limiting(enable: bool) -> Dict[str, Any]:
    """적응형 Rate Limiting 활성화/비활성화

    적응형 Rate Limiting은 API 에러 발생 시 자동으로 요청 속도를
    줄이고, 성공 시 다시 증가시키는 기능입니다.

    Args:
        enable: True=활성화, False=비활성화

    Returns:
        Dict: 설정 변경 결과
    """
    agent = get_agent()

    if not hasattr(agent, "client") or not agent.client:
        return {
            "success": False,
            "message": "Agent client가 초기화되지 않았습니다",
            "error_code": "CLIENT_NOT_INITIALIZED",
        }

    if not agent.client.enable_rate_limiter or not agent.client.rate_limiter:
        return {
            "success": False,
            "message": "Rate limiter가 비활성화되어 있습니다",
            "error_code": "RATE_LIMITER_DISABLED",
        }

    old_value = agent.client.rate_limiter.enable_adaptive
    agent.client.rate_limiter.enable_adaptive = enable

    # Reset backoff if disabling
    if not enable and old_value:
        agent.client.rate_limiter.backoff_multiplier = 1.0
        agent.client.rate_limiter.consecutive_errors = 0

    return {
        "success": True,
        "message": f"적응형 Rate Limiting이 {'활성화' if enable else '비활성화'}되었습니다",
        "previous_value": old_value,
        "current_value": enable,
        "current_status": agent.client.rate_limiter.get_current_rate(),
    }
