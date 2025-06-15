"""
KIS(한국투자증권) API 통합 테스트

- 본 파일은 KISClient, KIS_Agent, StockAPI, ProgramTradeAPI 등 한국투자 관련 핵심 모듈의 통합 테스트를 제공합니다.
- 계좌 잔고, 시세, 프로그램 매매, 종목 정보 등 실제 API 연동이 필요한 주요 기능을 한 번에 검증할 수 있습니다.
- 테스트 실행 전 반드시 venv 환경을 활성화하고, .env 파일에 인증정보가 올바르게 세팅되어 있어야 합니다.

실행 방법:
    venv
    pytest tests/kis_integration_test.py -v

※ 실계좌 주문/매수 등은 실제 주문이 발생할 수 있으니 주의하세요.
"""

import pytest
import os
from kis.core.client import KISClient
from kis.agent import KIS_Agent
from kis.stock.market import StockAPI
from kis.program.trade import ProgramTradeAPI

if not os.getenv('RUN_LIVE_TESTS'):
    pytest.skip('실제 API 테스트 건너뜀', allow_module_level=True)

def safe_call(name, func, *args, **kwargs):
    """안전한 함수 호출을 위한 헬퍼 함수"""
    try:
        res = func(*args, **kwargs)
        print(f"{name}: {res}\n")
        return res
    except Exception as e:
        print(f"{name} Error: {e}\n")
        return None

def test_account_balance(account_info):
    """계좌 잔고 조회 테스트"""
    print("\n[잔고 조회 테스트]")
    client = KISClient(verbose=True)
    stock = StockAPI(client, account_info)
    df = stock.get_account_balance_df()
    assert df is not None and not df.empty, "잔고 데이터가 없거나 오류가 발생했습니다."
    print(df)

def test_agent_api(account_info, test_stock_code):
    """KIS_Agent의 주요 API 기능 테스트"""
    agent = KIS_Agent(account_info=account_info)
    
    # 주식 가격 조회 테스트
    print("\n[주식 가격 조회 테스트]")
    price = safe_call("get_stock_price", agent.get_stock_price, test_stock_code)
    assert price is not None, "주식 가격 조회 실패"
    
    daily_price = safe_call("get_daily_price", agent.get_daily_price, test_stock_code)
    assert daily_price is not None, "일별 가격 조회 실패"
    
    # 계좌 잔고 조회 테스트
    print("\n[계좌 잔고 조회 테스트]")
    balance = safe_call("get_account_balance", agent.get_account_balance)
    assert balance is not None, "계좌 잔고 조회 실패"
    
    cash = safe_call("get_cash_available", agent.get_cash_available)
    assert cash is not None, "현금 잔고 조회 실패"
    
    total = safe_call("get_total_asset", agent.get_total_asset)
    assert total is not None, "총 자산 조회 실패"

def test_stock_api(account_info, test_stock_code):
    """StockAPI 시세/투자자/호가 테스트"""
    print("\n[StockAPI 시세/투자자/호가 테스트]")
    client = KISClient(verbose=True)
    stock = StockAPI(client, account_info)
    
    price = stock.get_stock_price(test_stock_code)
    assert price is not None, "주식 가격 조회 실패"
    print("- get_stock_price:", price)
    
    daily = stock.get_daily_price(test_stock_code)
    assert daily is not None, "일별 가격 조회 실패"
    print("- get_daily_price:", daily)
    
    orderbook = stock.get_orderbook(test_stock_code)
    assert orderbook is not None, "호가 조회 실패"
    print("- get_orderbook:", orderbook)
    
    member = stock.get_stock_member(test_stock_code)
    assert member is not None, "회원사 조회 실패"
    print("- get_stock_member:", member)
    
    investor = stock.get_stock_investor(test_stock_code)
    assert investor is not None, "투자자 조회 실패"
    print("- get_stock_investor:", investor)
    
    detail = stock.get_stock_investor_detail(test_stock_code)
    assert detail is not None, "투자자 상세 조회 실패"
    print("- get_stock_investor_detail:", detail)

def test_program_trade(test_stock_code):
    """ProgramTradeAPI 프로그램 매매 테스트"""
    print("\n[ProgramTradeAPI 프로그램 매매 테스트]")
    client = KISClient(verbose=True)
    pgm_api = ProgramTradeAPI(client)
    ref_date = "20250516"
    
    result = pgm_api.get_pgm_trade(test_stock_code, ref_date=ref_date)
    assert result is not None, "프로그램 매매 데이터 조회 실패"
    
    print(f"\n🔍 테스트 결과 for {test_stock_code} on {ref_date}")
    print(f"PGM 일별 매수량 (today): {result.get('today')}")
    print(f"PGM 일별 매도량 (net29): {result.get('net29')}")
    print(f"PGM 총거래량 (합산): {result.get('program_today_volume')}")
    print(f"PGM 매수비율 (%): {result.get('today_ratio')}")
    print(f"PGM 매수금액 (억원): {result.get('today_amt')}")
    print(f"PGM 매수금액 비율 (%): {result.get('today_amt_ratio')}") 
