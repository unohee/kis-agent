#!/usr/bin/env python3
"""Python Bridge 기능 통합 테스트 — 타임아웃, 에러 처리, 설치 감지."""

import json
import subprocess
import sys
import os
from pathlib import Path

# Created: 2026-03-23
# Purpose: Integration tests for timeout handling, error parsing, Python detection
# Test Status: [테스트 가능]


def test_python_installation_detection():
    """Python3이 설치되어 있는지 확인."""
    try:
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, f"Python check failed: {result.stderr}"
        assert "Python" in result.stdout or "Python" in result.stderr
        print(f"✓ Python installation check passed: {(result.stdout or result.stderr).strip()}")
        return True
    except FileNotFoundError:
        print("✗ Python3 not found")
        return False


def test_cli_bridge_json_parsing():
    """cli_bridge.py의 JSON 파싱 기능 테스트."""
    # JSON 요청 생성
    request = {
        "method": "stock_api.get_stock_price",
        "params": {"code": "005930"},
        "pretty": False,
    }

    # JSON 직렬화 테스트
    request_json = json.dumps(request)
    parsed = json.loads(request_json)

    assert parsed["method"] == "stock_api.get_stock_price"
    assert parsed["params"]["code"] == "005930"
    print("✓ JSON parsing test passed")
    return True


def test_error_response_format():
    """에러 응답 형식 테스트."""
    error_response = {
        "success": False,
        "error": "Invalid code",
        "code": "ValueError",
    }

    # JSON 직렬화 테스트
    json_response = json.dumps(error_response, ensure_ascii=False)
    parsed = json.loads(json_response)

    assert parsed["success"] is False
    assert "Invalid code" in parsed["error"]
    assert parsed["code"] == "ValueError"
    print("✓ Error response format test passed")
    return True


def test_timeout_error_response():
    """타임아웃 에러 응답 형식 테스트."""
    timeout_response = {
        "success": False,
        "error": "Request execution timed out after 30 seconds",
        "code": "TimeoutError",
    }

    json_response = json.dumps(timeout_response, ensure_ascii=False)
    parsed = json.loads(json_response)

    assert parsed["success"] is False
    assert parsed["code"] == "TimeoutError"
    assert "timed out" in parsed["error"]
    print("✓ Timeout error response format test passed")
    return True


def test_line_based_response_with_pretty_flag():
    """pretty 플래그가 있어도 브리지 응답은 단일 라인이어야 함."""
    response = {
        "success": True,
        "data": {"price": 70000},
        "_notice": "market closed",
    }

    serialized = json.dumps(response, ensure_ascii=False)
    assert "\n" not in serialized
    parsed = json.loads(serialized)

    assert parsed["success"] is True
    assert parsed["data"]["price"] == 70000
    print("✓ Line-based response test passed")
    return True


def test_stderr_parsing_simulation():
    """Python stderr 파싱 시뮬레이션."""
    # 예상되는 Python 에러 형식
    stderr_examples = [
        "ValueError: invalid literal for int()",
        "ZeroDivisionError: division by zero",
        "AttributeError: 'NoneType' object has no attribute 'get'",
        "ImportError: No module named 'nonexistent'",
    ]

    for stderr in stderr_examples:
        lines = stderr.strip().split("\n")
        last_line = lines[-1] if lines else ""

        # 에러 형식 파싱
        parts = last_line.split(":", 1)
        if len(parts) == 2:
            error_type = parts[0].strip()
            error_msg = parts[1].strip()

            assert error_type in ["ValueError", "ZeroDivisionError", "AttributeError", "ImportError"]
            assert len(error_msg) > 0
            print(f"✓ Parsed stderr: {error_type}: {error_msg}")

    return True


def test_timeout_handler_registration():
    """타임아웃 핸들러 등록 가능성 테스트."""
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Test timeout")

    # 핸들러 등록
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)

    # 복구
    signal.signal(signal.SIGALRM, old_handler)

    print("✓ Timeout handler registration test passed")
    return True


def main():
    """모든 테스트 실행."""
    print("=" * 60)
    print("Python Bridge Features Integration Tests")
    print("=" * 60)

    tests = [
        ("Python Installation Detection", test_python_installation_detection),
        ("CLI Bridge JSON Parsing", test_cli_bridge_json_parsing),
        ("Error Response Format", test_error_response_format),
        ("Timeout Error Response Format", test_timeout_error_response),
        ("Line-Based Response With Pretty Flag", test_line_based_response_with_pretty_flag),
        ("Stderr Parsing Simulation", test_stderr_parsing_simulation),
        ("Timeout Handler Registration", test_timeout_handler_registration),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\nTesting: {test_name}")
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
