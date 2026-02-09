"""
PyKIS 비동기 인증 사용 예제

이 예제는 auth_async와 reAuth_async 함수를 사용하여
비동기적으로 KIS API 토큰을 발급받는 방법을 보여줍니다.

Requirements:
    - aiohttp: pip install pykis[websocket]

Usage:
    python examples/async_auth_example.py
"""

import asyncio
import os

from dotenv import load_dotenv

from kis_agent.core.auth import auth_async, reAuth_async
from kis_agent.core.config import KISConfig


async def main():
    """비동기 인증 예제 메인 함수"""

    # 환경 변수 로드
    load_dotenv()

    # KISConfig 초기화
    config = KISConfig(
        app_key=os.getenv("KIS_APP_KEY"),
        app_secret=os.getenv("KIS_APP_SECRET"),
        base_url=os.getenv("KIS_BASE_URL"),
        account_no=os.getenv("KIS_ACCOUNT_NO"),
        account_code=os.getenv("KIS_ACCOUNT_CODE", "01"),
    )

    print("=" * 60)
    print("PyKIS 비동기 인증 예제")
    print("=" * 60)

    # 1. 비동기 토큰 발급
    print("\n1. auth_async()로 토큰 발급 중...")
    try:
        token_info = await auth_async(config, svr="prod")
        print("✓ 토큰 발급 성공!")
        print(f"  - Access Token: {token_info['access_token'][:20]}...")
        print(f"  - Expires At: {token_info['access_token_token_expired']}")
    except Exception as e:
        print(f"✗ 토큰 발급 실패: {e}")
        return

    # 2. 비동기 토큰 재인증 (캐시된 토큰 사용)
    print("\n2. reAuth_async()로 토큰 재인증 중...")
    try:
        reauth_info = await reAuth_async(config=None, svr="prod")
        if reauth_info:
            print("✓ 토큰 재인증 성공! (캐시 사용)")
            print(f"  - Access Token: {reauth_info['access_token'][:20]}...")
        else:
            print("✗ 캐시된 토큰 없음")
    except Exception as e:
        print(f"✗ 토큰 재인증 실패: {e}")

    # 3. 여러 비동기 작업을 동시에 실행하는 예제
    print("\n3. 여러 인증 작업을 동시에 실행...")
    try:
        tasks = [
            reAuth_async(config=None, svr="prod"),
            reAuth_async(config=None, svr="prod"),
            reAuth_async(config=None, svr="prod"),
        ]
        results = await asyncio.gather(*tasks)
        print(f"✓ {len(results)}개의 동시 요청 완료!")
        for i, result in enumerate(results, 1):
            if result:
                print(f"  - Task {i}: {result['access_token'][:20]}...")
    except Exception as e:
        print(f"✗ 동시 실행 실패: {e}")

    print("\n" + "=" * 60)
    print("예제 완료!")
    print("=" * 60)


if __name__ == "__main__":
    # Python 3.7+에서 asyncio.run() 사용
    asyncio.run(main())
