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