#!/usr/bin/env python
"""Rate Limiter 실제 동작 검증"""

import time

from kis_agent import Agent


def test_rate_limiter_live():
    """실제 환경에서 Rate Limiter 동작 테스트"""
    print(" Rate Limiter 실제 동작 검증 시작")

    # Agent 생성
    agent = Agent(".env")
    print(" Agent 초기화 성공")

    # 초기 상태 확인
    status = agent.get_rate_limiter_status()
    print(
        f" 초기 설정: {status['limit_per_second']}/초, {status['limit_per_minute']}/분"
    )

    # API 호출 시뮬레이션
    print(" API 호출 시뮬레이션 (3회)...")

    start_time = time.time()
    results = []

    for i in range(3):
        call_start = time.time()
        try:
            agent.get_stock_price("005930")
            call_elapsed = time.time() - call_start
            results.append(call_elapsed)
            print(f"  요청 {i+1}: 삼성전자 현재가 조회 완료 ({call_elapsed:.3f}초)")
        except Exception as e:
            print(f"  요청 {i+1}: 에러 - {e}")
            results.append(0)

    total_elapsed = time.time() - start_time

    # 최종 상태 확인
    final_status = agent.get_rate_limiter_status()

    print("\n 결과 요약:")
    print(f"  총 소요시간: {total_elapsed:.3f}초")
    print(f"  총 요청수: {final_status['total_requests']}개")
    print(f"  평균 대기시간: {final_status['avg_wait_time']:.3f}초")
    print(f"  제한 도달 횟수: {final_status['throttled_count']}회")
    print(
        f"  현재 요청률: {final_status['requests_per_second']}/{final_status['limit_per_second']}"
    )

    # Rate Limiter 설정 테스트
    print("\n 동적 설정 변경 테스트:")
    agent.set_rate_limits(requests_per_second=20)
    new_status = agent.get_rate_limiter_status()
    print(f"  초당 제한 변경: {new_status['limit_per_second']}")

    # 상태 리셋 테스트
    print("\n Rate Limiter 리셋 테스트:")
    agent.reset_rate_limiter()
    reset_status = agent.get_rate_limiter_status()
    print(f"  리셋 후 총 요청수: {reset_status['total_requests']}")

    print("\n Rate Limiter 검증 완료!")


if __name__ == "__main__":
    test_rate_limiter_live()
