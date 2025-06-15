import os
import sys
import pytest
from dotenv import load_dotenv
from pykis.core import auth

# .env 파일 로드
load_dotenv()

def test_token_issuance():
    """토큰 발급 테스트"""
    try:
        # 환경 변수 확인
        required_env_vars = ['KIS_APP_KEY', 'KIS_APP_SECRET', 'KIS_BASE_URL', 'KIS_ACCOUNT_NO', 'KIS_ACCOUNT_CODE']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            pytest.skip(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")

        # 헤더 확인
        headers = _getBaseHeader()
        print(f"[디버그] 요청 헤더: {headers}")
        assert headers == {"Content-Type": "application/json"}, "헤더가 올바르게 설정되지 않았습니다."

        # 토큰 발급 시도
        token = auth(svr='prod')
        print(f"[디버그] 발급된 토큰: {token}")
        assert token is not None, "토큰이 발급되지 않았습니다."

    except Exception as e:
        pytest.fail(f"토큰 발급 중 오류 발생: {str(e)}")

if __name__ == '__main__':
    test_token_issuance() 