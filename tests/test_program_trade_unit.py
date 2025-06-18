"""
프로그램매매 정보 조회 테스트
"""
import pytest
import os
from pykis import Agent

if not os.getenv('RUN_LIVE_TESTS'):
    pytest.skip('실제 API 테스트 건너뜀', allow_module_level=True)

def test_program_trade_info(test_stock_code):
    """프로그램매매 정보 조회 테스트"""
    print("\n[프로그램매매 정보 조회 테스트]")
    agent = Agent()
    
    # 프로그램매매 정보 조회
    ref_date = "20250516"
    result = agent.get_program_trade_summary(test_stock_code, ref_date=ref_date)
    assert result is not None, "프로그램매매 정보 조회 실패"
    
    print(f"\n🔍 테스트 결과 for {test_stock_code} on {ref_date}")
    print(f"PGM 일별 매수량 (today): {result.get('today')}")
    print(f"PGM 일별 매도량 (net29): {result.get('net29')}")
    print(f"PGM 총거래량 (합산): {result.get('program_today_volume')}")
    print(f"PGM 매수비율 (%): {result.get('today_ratio')}")
    print(f"PGM 매수금액 (억원): {result.get('today_amt')}")
    print(f"PGM 매수금액 비율 (%): {result.get('today_amt_ratio')}")
    
    # 추가 정보 출력
    print(f"\n📊 추가 프로그램 매매 정보:")
    print(f"프로그램 매수량: {result.get('program_day_shnu_vol')}")
    print(f"프로그램 매도량: {result.get('program_day_seln_vol')}")
    print(f"프로그램 총 거래량: {result.get('program_day_total_volume')}")
    print(f"프로그램 매수 비율: {result.get('program_day_buy_ratio')}%")
    print(f"29일 누적 순매수금액: {result.get('net29_amt')}")
    
    print("\n✅ 프로그램매매 정보 조회 테스트 완료")