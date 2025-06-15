"""
프로그램매매 정보 조회 테스트
"""
import pytest
import os
from kis.core.client import KISClient
from kis.program.trade import ProgramTradeAPI

if not os.getenv('RUN_LIVE_TESTS'):
    pytest.skip('실제 API 테스트 건너뜀', allow_module_level=True)

def test_program_trade_info(test_stock_code):
    """프로그램매매 정보 조회 테스트"""
    print("\n[프로그램매매 정보 조회 테스트]")
    client = KISClient(verbose=True)
    pgm_api = ProgramTradeAPI(client)
    
    # 프로그램매매 정보 조회
    ref_date = "20250516"
    result = pgm_api.get_pgm_trade(test_stock_code, ref_date=ref_date)
    assert result is not None, "프로그램매매 정보 조회 실패"
    
    print(f"\n🔍 테스트 결과 for {test_stock_code} on {ref_date}")
    print(f"PGM 일별 매수량 (today): {result.get('today')}")
    print(f"PGM 일별 매도량 (net29): {result.get('net29')}")
    print(f"PGM 총거래량 (합산): {result.get('program_today_volume')}")
    print(f"PGM 매수비율 (%): {result.get('today_ratio')}")
    print(f"PGM 매수금액 (억원): {result.get('today_amt')}")
    print(f"PGM 매수금액 비율 (%): {result.get('today_amt_ratio')}")
    
    # 프로그램매매 상세 정보 조회
    detail = pgm_api.get_pgm_trade_detail(test_stock_code, ref_date=ref_date)
    assert detail is not None, "프로그램매매 상세 정보 조회 실패"
    print("\n프로그램매매 상세 정보:")
    print(detail)