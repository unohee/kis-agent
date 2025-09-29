#!/usr/bin/env python3
"""
캐시 동작 테스트
"""

import os
import time
from dotenv import load_dotenv
from pykis import Agent

# .env 파일 로드
load_dotenv()

def test_cache():
    """캐시 동작 테스트"""
    
    # 환경변수에서 API 정보 로드
    app_key = os.getenv('APP_KEY')
    app_secret = os.getenv('APP_SECRET') 
    account_no = os.getenv('CANO')
    account_code = os.getenv('ACNT_PRDT_CD', '01')
    
    if not all([app_key, app_secret, account_no]):
        print("❌ 환경변수 설정이 필요합니다.")
        return
    
    try:
        # Agent 초기화 (캐시 활성화 기본값)
        print("Agent 초기화 중...")
        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code,
            base_url="https://openapi.koreainvestment.com:9443"
        )
        print("Agent 초기화 완료")
        
        # 1. 첫 번째 호출 (캐시 미스)
        print("\n[1차] LG이노텍 현재가 조회...")
        start_time = time.time()
        price1 = agent.get_stock_price("011070")
        time1 = time.time() - start_time
        
        if price1 and 'output' in price1:
            current_price = price1['output'].get('stck_prpr', '0')
            print(f"   현재가: {current_price}원")
            print(f"   소요시간: {time1:.3f}초")
            print(f"   캐시 여부: {'_cached' in price1}")
        
        # 2. 두 번째 호출 (캐시 히트 예상)
        print("\n[2차] LG이노텍 현재가 조회 (캐시 사용 예상)...")
        start_time = time.time()
        price2 = agent.get_stock_price("011070")
        time2 = time.time() - start_time
        
        if price2 and 'output' in price2:
            current_price = price2['output'].get('stck_prpr', '0')
            print(f"   현재가: {current_price}원")
            print(f"   소요시간: {time2:.3f}초")
            print(f"   캐시 여부: {'_cached' in price2}")
        
        # 3. 캐시 통계 확인
        if hasattr(agent.stock_api, 'cache') and agent.stock_api.cache:
            stats = agent.stock_api.cache.get_stats()
            print("\n캐시 통계:")
            print(f"   캐시 크기: {stats['size']}/{stats['max_size']}")
            print(f"   히트: {stats['hits']}")
            print(f"   미스: {stats['misses']}")
            print(f"   히트율: {stats['hit_rate']}")
            print(f"   기본 TTL: {stats['default_ttl']}초")
        
        # 4. 속도 향상 비교
        if time2 < time1:
            improvement = ((time1 - time2) / time1) * 100
            print(f"\n캐시로 인한 속도 향상: {improvement:.1f}%")
            print(f"   1차 호출: {time1:.3f}초")
            print(f"   2차 호출: {time2:.3f}초 (캐시)")
        
        # 5. 다른 종목 조회 (캐시 미스)
        print("\n[3차] 삼성전자 현재가 조회 (다른 종목)...")
        start_time = time.time()
        price3 = agent.get_stock_price("005930")
        time3 = time.time() - start_time
        
        if price3 and 'output' in price3:
            current_price = price3['output'].get('stck_prpr', '0')
            print(f"   현재가: {current_price}원")
            print(f"   소요시간: {time3:.3f}초")
            print(f"   캐시 여부: {'_cached' in price3}")
        
        # 6. TTL 만료 테스트 (10초 대기)
        print("\n⏳ 10초 대기 (TTL 만료 테스트)...")
        time.sleep(11)
        
        print("\n[4차] LG이노텍 현재가 조회 (TTL 만료 후)...")
        start_time = time.time()
        price4 = agent.get_stock_price("011070")
        time4 = time.time() - start_time
        
        if price4 and 'output' in price4:
            current_price = price4['output'].get('stck_prpr', '0')
            print(f"   현재가: {current_price}원")
            print(f"   소요시간: {time4:.3f}초")
            print(f"   캐시 여부: {'_cached' in price4}")
        
        # 최종 캐시 통계
        if hasattr(agent.stock_api, 'cache') and agent.stock_api.cache:
            stats = agent.stock_api.cache.get_stats()
            print("\n최종 캐시 통계:")
            print(f"   히트: {stats['hits']}")
            print(f"   미스: {stats['misses']}")
            print(f"   히트율: {stats['hit_rate']}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cache()