#!/usr/bin/env python3
"""
토큰 발급 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# pykis 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pykis.core.auth import auth, getTREnv
from pykis.core.config import KISConfig

def test_token_auth():
    """토큰 발급 테스트"""
    print("=== 토큰 발급 테스트 ===")
    
    # 환경 변수 확인
    print(f"APP_KEY: {os.getenv('KIS_APP_KEY', 'NOT_SET')[:10]}...")
    print(f"APP_SECRET: {os.getenv('KIS_APP_SECRET', 'NOT_SET')[:10]}...")
    print(f"BASE_URL: {os.getenv('KIS_BASE_URL', 'NOT_SET')}")
    print(f"ACCOUNT_NO: {os.getenv('KIS_ACCOUNT_NO', 'NOT_SET')}")
    print(f"ACCOUNT_CODE: {os.getenv('KIS_ACCOUNT_CODE', 'NOT_SET')}")
    
    try:
        # KISConfig 객체 생성
        config = KISConfig()
        print(f"Config loaded: APP_KEY={config.APP_KEY[:10]}...")
        
        # 토큰 발급
        print("\n토큰 발급 시도...")
        token_data = auth(config=config, svr='prod')
        
        print(f"토큰 발급 성공!")
        print(f"Access Token: {token_data['access_token'][:20]}...")
        print(f"Expired: {token_data['access_token_token_expired']}")
        
        # 환경 설정 확인
        env = getTREnv()
        print(f"\n환경 설정:")
        print(f"my_app: {env.my_app[:10]}...")
        print(f"my_token: {env.my_token[:20]}...")
        print(f"my_url: {env.my_url}")
        
        return True
        
    except Exception as e:
        print(f"토큰 발급 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_token_auth()
    if success:
        print("\n✅ 토큰 발급 테스트 성공!")
    else:
        print("\n❌ 토큰 발급 테스트 실패!")
        sys.exit(1) 