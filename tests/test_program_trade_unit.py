"""
프로그램매매 정보 조회 테스트
"""
import pytest
import os
from pykis import Agent

if not os.getenv('RUN_LIVE_TESTS'):
    pytest.skip('실제 API 테스트 건너뜀', allow_module_level=True)

def test_program_trade_hourly_trend(test_stock_code):
    """시간별 프로그램 매매 추이 조회 테스트"""
    print("\n[시간별 프로그램 매매 추이 조회 테스트]")
    agent = Agent()
    
    # 시간별 프로그램 매매 추이 조회
    result = agent.get_program_trade_hourly_trend(test_stock_code)
    assert result is not None, "시간별 프로그램 매매 추이 조회 실패"

    # 결과 출력
    print(f"시간별 프로그램 매매 추이 ({test_stock_code}):")
    print(result)

def test_program_trade_by_stock(test_stock_code):
    """종목별 프로그램매매추이(체결) 조회 테스트"""
    print("\n[종목별 프로그램매매추이(체결) 조회 테스트]")
    agent = Agent()
    
    # 당일 시간별 조회
    result_today = agent.get_program_trade_by_stock(test_stock_code)
    assert result_today is not None, "당일 시간별 프로그램매매추이 조회 실패"
    print(f"당일 시간별 프로그램매매추이 ({test_stock_code}):")
    print(result_today)
    
    # 특정일 조회
    ref_date = "20250516"
    result_specific_date = agent.get_program_trade_by_stock(test_stock_code, ref_date=ref_date)
    assert result_specific_date is not None, "특정일 프로그램매매추이 조회 실패"
    print(f"특정일 프로그램매매추이 ({test_stock_code}, {ref_date}):")
    print(result_specific_date)

def test_program_trade_daily_summary(test_stock_code):
    """종목별 프로그램매매추이(일별) 조회 테스트"""
    print("\n[종목별 프로그램매매추이(일별) 조회 테스트]")
    agent = Agent()
    
    # 특정일 조회
    ref_date = "20250516"
    result = agent.get_program_trade_daily_summary(test_stock_code, ref_date)
    assert result is not None, "일별 프로그램매매추이 조회 실패"
    print(f"일별 프로그램매매추이 ({test_stock_code}, {ref_date}):")
    print(result)

def test_program_trade_market_daily():
    """프로그램매매종합현황(일별) 조회 테스트"""
    print("\n[프로그램매매종합현황(일별) 조회 테스트]")
    agent = Agent()
    
    # 기간 조회
    start_date = "20250501"
    end_date = "20250516"
    result = agent.get_program_trade_market_daily(start_date, end_date)
    assert result is not None, "프로그램매매종합현황(일별) 조회 실패"
    print(f"프로그램매매종합현황(일별) ({start_date}~{end_date}):")
    print(result)
