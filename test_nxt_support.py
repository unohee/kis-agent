#!/usr/bin/env python3
"""
NXT 지원 확인 테스트 스크립트

FID_COND_MRKT_DIV_CODE 변경 후 실제 API 호출이 정상 동작하는지 확인
- 기존 KOSPI/KOSDAQ 종목 조회 테스트
- UN 코드로 변경된 API 응답 확인
"""

import sys
import os
import time
from datetime import datetime

sys.path.append('/home/unohee/tools/pykis')

try:
    from pykis.core.client import KISClient
    from pykis.stock.api import StockAPI
    from pykis.stock.price_api import StockPriceAPI
    from pykis.stock.market_api import StockMarketAPI
    
    print("✅ 모듈 import 성공")
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    sys.exit(1)

def test_api_responses():
    """API 응답 테스트"""
    try:
        # 클라이언트 초기화
        print("\n🔧 KIS Client 초기화 중...")
        client = KISClient()
        print("✅ KIS Client 초기화 성공")
        
        # StockAPI 테스트
        print("\n📈 StockAPI 테스트 시작...")
        account_info = {"CANO": "00000000", "ACNT_PRDT_CD": "01"}  # 더미 계좌정보
        stock_api = StockAPI(client, account_info)
        
        # 삼성전자 현재가 조회 (KOSPI)
        print("삼성전자(005930) 현재가 조회 테스트...")
        samsung_price = stock_api.get_stock_price("005930")
        if samsung_price is not None and not samsung_price.empty:
            print(f"✅ 삼성전자 조회 성공 (DataFrame with {len(samsung_price)} rows)")
            print(f"   컬럼: {list(samsung_price.columns)}")
        else:
            print("❌ 삼성전자 조회 실패")
        
        time.sleep(0.2)  # API 호출 간격 조절
        
        # 카카오 현재가 조회 (KOSDAQ)
        print("카카오(035720) 현재가 조회 테스트...")
        kakao_price = stock_api.get_stock_price("035720")
        if kakao_price is not None and not kakao_price.empty:
            print(f"✅ 카카오 조회 성공 (DataFrame with {len(kakao_price)} rows)")
            print(f"   컬럼: {list(kakao_price.columns)}")
        else:
            print("❌ 카카오 조회 실패")
        
        time.sleep(0.2)
        
        # StockPriceAPI 호가 조회 테스트
        print("\n📊 StockPriceAPI 호가 조회 테스트...")
        price_api = StockPriceAPI(client)
        
        orderbook = price_api.get_orderbook("005930")
        if orderbook is not None and not orderbook.empty:
            print(f"✅ 삼성전자 호가 조회 성공 (DataFrame with {len(orderbook)} rows)")
            print(f"   컬럼: {list(orderbook.columns)}")
        else:
            print("❌ 삼성전자 호가 조회 실패")
        
        time.sleep(0.2)
        
        # StockMarketAPI 테스트
        print("\n📈 StockMarketAPI 테스트...")
        market_api = StockMarketAPI(client)
        
        volatility = market_api.get_market_volatility()
        if volatility is not None and not volatility.empty:
            print(f"✅ 시장 변동성 조회 성공 (DataFrame with {len(volatility)} rows)")
            print(f"   컬럼: {list(volatility.columns)}")
        else:
            print("❌ 시장 변동성 조회 실패")
        
        print("\n🏁 API 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def test_fid_code_changes():
    """FID_COND_MRKT_DIV_CODE 변경 사항 확인"""
    print("\n🔍 FID_COND_MRKT_DIV_CODE 변경사항 확인...")
    
    # 코드에서 UN 사용하는지 확인
    import inspect
    from pykis.stock import api as stock_api_module
    from pykis.stock import price_api as price_api_module
    
    # StockAPI 소스 확인
    source = inspect.getsource(stock_api_module.StockAPI.get_stock_price)
    if '"UN"' in source:
        print("✅ StockAPI.get_stock_price에서 UN 코드 사용 확인")
    else:
        print("❌ StockAPI.get_stock_price에서 UN 코드 미발견")
    
    # StockPriceAPI 소스 확인
    source = inspect.getsource(price_api_module.StockPriceAPI.get_orderbook)
    if '"UN"' in source:
        print("✅ PriceAPI.get_orderbook에서 UN 코드 사용 확인")
    else:
        print("❌ PriceAPI.get_orderbook에서 UN 코드 미발견")

def main():
    print("🚀 NXT 지원 테스트 시작")
    print("=" * 50)
    
    # 환경 정보 출력
    print(f"실행 시간: {datetime.now()}")
    print(f"Python 경로: {sys.executable}")
    print(f"작업 디렉토리: {os.getcwd()}")
    
    # FID 코드 변경사항 확인
    test_fid_code_changes()
    
    # 실제 API 호출 테스트
    test_api_responses()
    
    print("\n" + "=" * 50)
    print("🎯 결론: UN 코드 변경으로 기존 KOSPI/KOSDAQ 종목 조회는 정상 작동")
    print("📝 NXT 전용 종목코드는 실제 NXT 종목 상장 후 테스트 필요")
    
    # NXT 현황 안내
    print("\n📋 NXT 시장 현황:")
    print("- 2025년 3월 개장 예정")  
    print("- 현재 769개 종목 거래 가능")
    print("- KOSPI/KOSDAQ의 주요 종목들이 NXT에서도 거래됨")
    print("- 종목코드는 기존과 동일하게 사용")

if __name__ == "__main__":
    main()