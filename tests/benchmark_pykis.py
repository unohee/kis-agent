#!/usr/bin/env python3
"""
PyKIS 실제 성능 벤치마크
실제 API 호출 속도를 측정합니다.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from pykis import Agent


def benchmark_sequential(agent: Agent, codes: List[str], iterations: int = 3):
    """순차 처리 벤치마크"""
    print("\n 순차 처리 벤치마크")
    print("-" * 40)

    total_requests = len(codes) * iterations
    start_time = time.time()
    success_count = 0

    for _i in range(iterations):
        for code in codes:
            try:
                result = agent.get_stock_price(code)
                if result and result.get("rt_cd") == "0":
                    success_count += 1
            except Exception as e:
                print(f"Error: {e}")

    elapsed = time.time() - start_time

    print(f"총 요청: {total_requests}개")
    print(f"성공: {success_count}개")
    print(f"소요 시간: {elapsed:.2f}초")
    print(f"처리 속도: {total_requests/elapsed:.2f} req/s")

    return elapsed, total_requests / elapsed


def benchmark_parallel(
    agent: Agent, codes: List[str], iterations: int = 3, workers: int = 10
):
    """병렬 처리 벤치마크"""
    print(f"\n 병렬 처리 벤치마크 (workers={workers})")
    print("-" * 40)

    total_requests = len(codes) * iterations

    def make_request(code_iter):
        code, i = code_iter
        try:
            result = agent.get_stock_price(code)
            return result and result.get("rt_cd") == "0"
        except Exception as e:
            print(f"Error getting stock price for {code}: {e}")
            import traceback

            traceback.print_exc()
            return False

    start_time = time.time()

    # 모든 요청 준비
    all_requests = [(code, i) for i in range(iterations) for code in codes]

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(make_request, req) for req in all_requests]
        success_count = sum(1 for f in as_completed(futures) if f.result())

    elapsed = time.time() - start_time

    print(f"총 요청: {total_requests}개")
    print(f"성공: {success_count}개")
    print(f"소요 시간: {elapsed:.2f}초")
    print(f"처리 속도: {total_requests/elapsed:.2f} req/s")

    return elapsed, total_requests / elapsed


def verify_rate_limiter_settings(agent: Agent):
    """Rate Limiter 설정 확인"""
    print("\n  Rate Limiter 설정")
    print("-" * 40)

    if agent.client.rate_limiter:
        rl = agent.client.rate_limiter
        print(f"초당 제한: {rl.requests_per_second}회")
        print(f"분당 제한: {rl.requests_per_minute}회")
        print(f"최소 간격: {rl.min_interval * 1000:.0f}ms")
        print(f"버스트 크기: {rl.burst_size}")
        print(f"적응형 모드: {rl.enable_adaptive}")
    else:
        print(" Rate Limiter가 비활성화되어 있습니다!")


def main():
    print("=" * 60)
    print(" PyKIS 성능 벤치마크")
    print("=" * 60)

    # Agent 초기화 - 환경변수에서 가져오기
    import os

    app_key = os.environ.get("KIS_APP_KEY")
    app_secret = os.environ.get("KIS_APP_SECRET")
    account_no = os.environ.get("KIS_ACCOUNT_NO")
    account_code = os.environ.get("KIS_ACCOUNT_CODE", "01")

    if not all([app_key, app_secret, account_no]):
        print(
            "필수 환경변수가 설정되지 않았습니다: KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NO"
        )
        return

    agent = Agent(
        app_key=app_key,
        app_secret=app_secret,
        account_no=account_no,
        account_code=account_code,
    )

    # Rate Limiter 설정 확인
    verify_rate_limiter_settings(agent)

    # 테스트할 종목 코드들
    test_codes = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "035420",  # NAVER
        "035720",  # 카카오
        "051910",  # LG화학
    ]

    # 순차 처리 테스트
    seq_time, seq_speed = benchmark_sequential(agent, test_codes, iterations=2)

    # 5초 대기 (API 쿨다운)
    print("\n⏳ API 쿨다운 5초...")
    time.sleep(5)

    # 병렬 처리 테스트 (5 workers)
    par5_time, par5_speed = benchmark_parallel(
        agent, test_codes, iterations=2, workers=5
    )

    # 5초 대기
    print("\n⏳ API 쿨다운 5초...")
    time.sleep(5)

    # 병렬 처리 테스트 (10 workers)
    par10_time, par10_speed = benchmark_parallel(
        agent, test_codes, iterations=2, workers=10
    )

    # 결과 요약
    print("\n" + "=" * 60)
    print(" 벤치마크 결과 요약")
    print("=" * 60)

    print(f"\n순차 처리:  {seq_speed:.2f} req/s")
    print(f"병렬 (5):   {par5_speed:.2f} req/s (순차 대비 {par5_speed/seq_speed:.1f}x)")
    print(
        f"병렬 (10):  {par10_speed:.2f} req/s (순차 대비 {par10_speed/seq_speed:.1f}x)"
    )

    # 판정
    print("\n 판정:")
    if par10_speed > 20:
        print(f" 초당 20회 이상 달성 ({par10_speed:.2f} req/s)")
    elif par10_speed > 15:
        print(f"  초당 15-20회 수준 ({par10_speed:.2f} req/s)")
    else:
        print(f" 초당 15회 미만 ({par10_speed:.2f} req/s)")

    # Rate Limiter 최종 통계
    if agent.client.rate_limiter:
        stats = agent.client.rate_limiter.get_current_rate()
        print("\n Rate Limiter 통계:")
        print(f"  - 총 요청: {stats['total_requests']}")
        print(f"  - 스로틀링: {stats['throttled_count']}회")
        print(f"  - 평균 대기: {stats['avg_wait_time']:.3f}초")


if __name__ == "__main__":
    main()
