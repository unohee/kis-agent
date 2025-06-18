#!/usr/bin/env python3
"""
API 호출 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# pykis 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pykis.core.client import KISClient
from pykis.core.config import KISConfig

def test_api_call():
    """API 호출 테스트"""
    print("=== API 호출 테스트 ===")
    
    try:
        # KISConfig 객체 생성
        config = KISConfig()
        print(f"Config loaded: APP_KEY={config.APP_KEY[:10]}...")
        
        # KISClient 생성
        print("\nKISClient 생성...")
        client = KISClient(config=config)
        print(f"Client created: base_url={client.base_url}")
        
        # 현재가 조회 API 호출
        print("\n현재가 조회 API 호출...")
        response = client.make_request(
            endpoint="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": "005930"
            }
        )
        
        print(f"API 응답: rt_cd={response.get('rt_cd', 'N/A')}")
        if response.get('rt_cd') == '0':
            print("✅ API 호출 성공!")
            output = response.get('output', {})
            if output:
                print(f"현재가: {output.get('stck_prpr', 'N/A')}")
                print(f"등락률: {output.get('prdy_ctrt', 'N/A')}%")
        else:
            print(f"❌ API 호출 실패: {response.get('msg1', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"API 호출 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_call()
    if success:
        print("\n✅ API 호출 테스트 성공!")
    else:
        print("\n❌ API 호출 테스트 실패!")
        sys.exit(1) 