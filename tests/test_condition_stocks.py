"""
조건검색식 종목 조회 테스트
"""
import pytest
import os
from kis.core.client import KISClient
from kis.stock.condition import ConditionAPI

if not os.getenv('RUN_LIVE_TESTS'):
    pytest.skip('실제 API 테스트 건너뜀', allow_module_level=True)

def test_condition_stocks():
    """조건검색식 종목 조회 테스트"""
    print("\n[조건검색식 종목 조회 테스트]")
    client = KISClient(verbose=True)
    condition = ConditionAPI(client)
    
    # 조건검색식 목록 조회
    conditions = condition.get_condition_list()
    assert conditions is not None, "조건검색식 목록 조회 실패"
    print("조건검색식 목록:", conditions)
    
    if conditions and len(conditions) > 0:
        # 첫 번째 조건검색식으로 종목 조회
        first_condition = conditions[0]
        stocks = condition.get_condition_stocks(first_condition["condition_name"])
        assert stocks is not None, "조건검색식 종목 조회 실패"
        print(f"\n{first_condition['condition_name']} 조건검색식 종목:")
        print(stocks) 