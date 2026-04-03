#!/usr/bin/env python3
"""kis-agent CLI Bridge — Node.js와 Python 간의 JSON 기반 subprocess 통신.

stdin으로 JSON 명령을 수신하여 Agent 메서드를 호출하고,
stdout으로 JSON 응답을 출력합니다.

JSON 요청 형식:
{
    "method": "stock_api.get_stock_price",
    "params": {"code": "005930"},
    "pretty": false
}

JSON 응답 형식:
{
    "success": true,
    "data": {...},
    "_notice": "optional market status notice"
}

또는 에러 시:
{
    "success": false,
    "error": "error message",
    "code": "ErrorClassName"
}
"""

import json
import logging
import os
import signal
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Any, Dict

# Created: 2026-03-22
# Purpose: JSON-based subprocess bridge for Node.js ↔ Python kis-agent communication
# Dependencies: kis_agent, python-dotenv


class TimeoutError(Exception):
    """타임아웃 에러."""
    pass


def timeout_handler(signum, frame):
    """타임아웃 신호 핸들러."""
    raise TimeoutError("Request execution timed out")


def setup_logging():
    """에러 로깅을 stderr로 설정."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )


def check_python_installation():
    """Python이 설치되어 있는지 확인."""
    for python_cmd in ["python3", "python"]:
        try:
            result = subprocess.run(
                [python_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return True, python_cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    return False, None


def load_env():
    """환경변수 로드."""
    from dotenv import load_dotenv

    for p in [
        ".env",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        os.path.expanduser("~/.env"),
    ]:
        if os.path.exists(p):
            load_dotenv(p)
            break


def create_agent():
    """환경변수에서 인증 정보를 로드하여 Agent 생성."""
    load_env()

    from kis_agent import Agent

    agent = Agent(
        app_key=os.environ.get("KIS_APP_KEY", ""),
        app_secret=os.environ.get("KIS_APP_SECRET", os.environ.get("KIS_SECRET", "")),
        account_no=os.environ.get("KIS_ACCOUNT_NO", ""),
        account_code=os.environ.get("KIS_ACCOUNT_CODE", "01"),
        base_url=os.environ.get(
            "KIS_BASE_URL", "https://openapi.koreainvestment.com:9443"
        ),
    )

    return agent


# 영업일 캐시 — 세션 내 재사용
_market_status = {
    "checked": False,
    "is_holiday": None,
    "last_business_day": None,
    "notice": None,
}


def check_market_status(agent) -> None:
    """한투 API로 오늘이 영업일인지 확인하고 캐싱."""
    if _market_status["checked"]:
        return

    today = datetime.now()
    today_str = today.strftime("%Y%m%d")

    try:
        holiday = agent.stock_api.is_holiday(today_str)
    except Exception:
        # API 실패 시 주말만 체크
        holiday = today.weekday() >= 5

    _market_status["is_holiday"] = holiday
    _market_status["checked"] = True

    if holiday:
        # 직전 영업일 탐색 (최대 10일)
        for i in range(1, 11):
            prev = today - timedelta(days=i)
            prev_str = prev.strftime("%Y%m%d")
            try:
                prev_holiday = agent.stock_api.is_holiday(prev_str)
                if prev_holiday is False:
                    _market_status["last_business_day"] = prev_str
                    bday = prev.strftime("%Y-%m-%d %a")
                    _market_status["notice"] = f"휴장일 — 데이터는 직전 영업일({bday}) 기준"
                    break
            except Exception:
                if prev.weekday() < 5:
                    _market_status["last_business_day"] = prev_str
                    bday = prev.strftime("%Y-%m-%d %a")
                    _market_status["notice"] = (
                        f"휴장일 — 데이터는 직전 영업일({bday}) 기준 (공휴일 미확인)"
                    )
                    break
    else:
        _market_status["last_business_day"] = today_str
        hour = today.hour
        if hour < 9:
            _market_status["notice"] = "장 시작 전 — 데이터는 전일 종가 기준"
        elif hour >= 16:
            _market_status["notice"] = "장 마감 후 — 데이터는 금일 종가 기준"


def output_json(data: Dict[str, Any], pretty: bool = False) -> None:
    """JSON을 stdout으로 출력.

    Bridge 프로토콜은 line-based JSON이므로 pretty 옵션이 들어와도
    항상 단일 라인 JSON만 출력합니다.
    """
    notice = _market_status.get("notice")
    if notice and isinstance(data, dict) and "data" in data:
        data["_notice"] = notice
    print(json.dumps(data, ensure_ascii=False, default=str), flush=True)


def call_method(agent: Any, method_path: str, params: Dict[str, Any]) -> Any:
    """
    "domain.method" 형식의 메서드를 호출합니다.

    예시:
        - "stock_api.get_stock_price" → agent.stock_api.get_stock_price(code=...)
        - "account_api.get_account_balance" → agent.account_api.get_account_balance()
    """
    parts = method_path.split(".", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid method path: {method_path}. Use 'domain.method'")

    domain, method = parts
    obj = getattr(agent, domain, None)
    if obj is None:
        raise AttributeError(f"Agent has no attribute '{domain}'")

    fn = getattr(obj, method, None)
    if fn is None:
        raise AttributeError(f"{domain} has no method '{method}'")

    if not callable(fn):
        raise TypeError(f"{domain}.{method} is not callable")

    return fn(**params)


def _format_timeout_error(timeout_ms: int) -> str:
    """타임아웃 에러 메시지를 프로토콜 표기와 맞춰 생성."""
    if timeout_ms % 1000 == 0:
        seconds = timeout_ms // 1000
        unit = "second" if seconds == 1 else "seconds"
        return f"Request execution timed out after {seconds} {unit}"

    return f"Request execution timed out after {timeout_ms} ms"


def handle_request(request_json: str, agent: Any, timeout: int = 30000) -> str:
    """
    JSON 요청을 처리하고 JSON 응답을 반환합니다.

    Args:
        request_json: {"method": "...", "params": {...}, "pretty": false, "timeout": 30000}
        agent: kis_agent.Agent 인스턴스
        timeout: 타임아웃 (밀리초), 기본값 30000ms

    Returns:
        JSON 응답 문자열
    """
    try:
        request = json.loads(request_json)
    except json.JSONDecodeError as e:
        return json.dumps(
            {"success": False, "error": f"Invalid JSON: {str(e)}", "code": "JSONDecodeError"}
        )

    method = request.get("method")
    params = request.get("params", {})
    pretty = request.get("pretty", False)
    timeout_ms = request.get("timeout", timeout)

    if not method:
        return json.dumps(
            {"success": False, "error": "Missing 'method' field", "code": "ValidationError"}
        )

    if not isinstance(timeout_ms, int) or timeout_ms <= 0:
        return json.dumps(
            {"success": False, "error": "'timeout' must be a positive integer", "code": "ValidationError"}
        )

    # 타임아웃 설정
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, timeout_ms / 1000)

    try:
        result = call_method(agent, method, params)
        signal.setitimer(signal.ITIMER_REAL, 0)  # 타임아웃 취소
        response = {"success": True, "data": result}
        output_json(response, pretty)
        return ""  # output_json 이미 출력됨
    except TimeoutError:
        signal.setitimer(signal.ITIMER_REAL, 0)
        error_msg = _format_timeout_error(timeout_ms)
        response = {
            "success": False,
            "error": error_msg,
            "code": "TimeoutError",
        }
        return json.dumps(response, ensure_ascii=False, default=str)
    except Exception as e:
        signal.setitimer(signal.ITIMER_REAL, 0)
        error_code = type(e).__name__
        error_msg = str(e)
        response = {
            "success": False,
            "error": error_msg,
            "code": error_code,
        }
        return json.dumps(response, ensure_ascii=False, default=str)


def main():
    """CLI 브리지 메인 진입점 — stdin에서 JSON 읽고 처리."""
    setup_logging()

    # Python 설치 여부 확인
    is_installed, python_cmd = check_python_installation()
    if not is_installed:
        error_response = {
            "success": False,
            "error": "Python is not installed or not found in PATH. Please install Python 3.8+ and ensure it's accessible as 'python3' or 'python'.",
            "code": "PythonNotFound",
        }
        print(json.dumps(error_response, ensure_ascii=False, default=str))
        sys.exit(1)

    try:
        # Agent 생성
        agent = create_agent()

        # 영업일 상태 확인 (한 번만)
        check_market_status(agent)
    except Exception as e:
        error_response = {
            "success": False,
            "error": f"Failed to initialize agent: {str(e)}",
            "code": type(e).__name__,
        }
        print(json.dumps(error_response, ensure_ascii=False, default=str))
        sys.exit(1)

    # stdin에서 한 줄씩 JSON 읽고 처리
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            response = handle_request(line, agent)
            if response:  # handle_request에서 이미 출력되지 않은 경우만
                print(response)
        except Exception as e:
            error_response = {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "code": type(e).__name__,
            }
            print(json.dumps(error_response, ensure_ascii=False, default=str))
        finally:
            # 타임아웃 신호 취소 (다음 요청 대비)
            signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    main()
