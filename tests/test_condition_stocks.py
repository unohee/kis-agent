"""
조건검색식 종목 조회 테스트
"""
import pytest
import os
from pykis import Agent

if not os.getenv('RUN_LIVE_TESTS'):
    pytest.skip('실제 API 테스트 건너뜀', allow_module_level=True)

def test_condition_stocks():
    """조건검색식 종목 조회 테스트"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    agent = Agent(env_path=env_path)
    
    # 조건검색식 목록 조회
    conditions = agent.get_condition_list()
    assert conditions is not None, "조건검색식 목록 조회 실패"
    
    if conditions and len(conditions) > 0:
        # 첫 번째 조건검색식으로 ���목 조회
        first_condition = conditions[0]
        stocks = agent.get_condition_stocks(first_condition["condition_name"])
        assert stocks is not None, "조건검색식 종목 조회 실패" 