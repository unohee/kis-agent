"""
KIS(한국투자증권) API 통합 테스트

- 본 파일은 Agent 중심의 한국투자 관련 핵심 모듈의 통합 테스트를 제공합니다.
- 계좌 잔고, 시세, 프로그램 매매, 종목 정보 등 실제 API 연동이 필요한 주요 기능을 한 번에 검증할 수 있습니다.
- 테스트 실행 전 반드시 venv 환경을 활성화하고, .env 파일에 인증정보가 올바르게 세팅되어 있어야 합니다.

실행 방법:
    venv
    pytest tests/kis_integration_test.py -v

※ 실계좌 주문/매수 등은 실제 주문이 발생할 수 있으니 주의하세요.
"""

import pytest
import os
from datetime import datetime, timedelta  # [변경 이유] 날짜 계산을 위해 추가
from pykis import Agent
import logging

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
    agent = Agent()
    df = agent.get_account_balance_df()
    assert df is not None and not df.empty, "잔고 데이터가 없거나 오류가 발생했습니다."

def test_agent_api(account_info, test_stock_code):
    """Agent의 주요 API 기능 테스트"""
    agent = Agent()
    
    # 주식 가격 조회 테스트
    print("\n[주식 가격 조회 테스트]")
    price = safe_call("get_stock_price", agent.get_stock_price, test_stock_code)
    assert price is not None, "주식 가격 조회 실패"
    
    # [변경 이유] Agent.get_daily_price는 code만 받으므로 인자 개수 수정
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
    """Agent 시세/투자자/호가 테스트"""
    agent = Agent()
    
    price = agent.get_stock_price(test_stock_code)
    assert price is not None, "주식 가격 조회 실패"
    
    # [변경 이유] get_daily_price 인자 추가 (최근 1개월)
    end_date = datetime.today().strftime('%Y%m%d')
    start_date = (datetime.today() - timedelta(days=30)).strftime('%Y%m%d')
    daily = agent.get_daily_price(test_stock_code, start_date, end_date)
    assert daily is not None, "일별 가격 조회 실패"
    
    orderbook = agent.get_orderbook(test_stock_code)
    assert orderbook is not None, "호가 조회 실패"
    
    member = agent.get_stock_member(test_stock_code)
    assert member is not None, "회원사 조회 실패"
    
    investor = agent.get_stock_investor(test_stock_code)
    assert investor is not None, "투자자 조회 실패"

def test_program_trade(test_stock_code):
    """Agent 프로그램 매매 테스트"""
    agent = Agent()
    trend = agent.get_program_trade_trend(test_stock_code)
    assert trend is not None, "프로그램 매매 추이 조회 실패"
    net_buy = agent.get_net_buy_volume(test_stock_code)
    assert net_buy is not None, "순매수량 확인 실패"
    analysis = agent.analyze_trade_trend(test_stock_code)
    assert analysis is not None, "매매 동향 분석 실패"

def test_condition_search():
    """조건검색 테스트"""
    # 로깅 레벨을 임시로 변경하여 조건검색 종목 조회 성공 메시지 숨김
    original_level = logging.getLogger().level
    logging.getLogger().setLevel(logging.WARNING)
    
    try:
        agent = Agent()
        # 조건검색 목록 조회
        conditions = agent.get_condition_list()
        assert conditions is not None, "조건검색 목록 조회 실패"
        assert isinstance(conditions, list), "조건검색 목록이 리스트가 아닙니다"
        
        if conditions:
            # 첫 번째 조건으로 종목 조회
            condition = conditions[0]
            stocks = agent.get_condition_stocks(condition['condition_index'])
            assert stocks is not None, "조건검색 종목 조회 실패"
            assert isinstance(stocks, list), "조건검색 종목이 리스트가 아닙니다"
    finally:
        # 로깅 레벨 복원
        logging.getLogger().setLevel(original_level) 
