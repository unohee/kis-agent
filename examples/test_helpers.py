"""
PyKIS 테스트 헬퍼 함수 모듈

이 모듈은 PyKIS API 테스트를 위한 유틸리티 함수들을 제공합니다.
주피터 노트북에서 import해서 사용할 수 있습니다.

사용 예시:
    from test_helpers import test_api_method, get_test_results, setup_test_environment
    
    # 테스트 환경 설정
    agent, TEST_STOCK, TEST_DATE = setup_test_environment()
    
    # API 메서드 테스트
    result = test_api_method("get_stock_price", agent.get_stock_price, TEST_STOCK)
    
    # 테스트 결과 조회
    summary = get_test_results()
"""

import sys
import os
import time
import json
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional, Union
import pandas as pd

# 전역 테스트 결과 저장소
test_results = {
    'success': [],
    'failed': [],
    'partial': [],
    'total_tests': 0
}


def reset_test_results():
    """테스트 결과 초기화"""
    global test_results
    test_results = {
        'success': [],
        'failed': [],
        'partial': [],
        'total_tests': 0
    }


def get_test_results() -> Dict[str, Any]:
    """현재 테스트 결과 요약 반환"""
    global test_results
    
    total = test_results['total_tests']
    success_count = len(test_results['success'])
    failed_count = len(test_results['failed'])
    partial_count = len(test_results['partial'])
    
    success_rate = (success_count / total * 100) if total > 0 else 0
    
    return {
        'total_tests': total,
        'success_count': success_count,
        'failed_count': failed_count,
        'partial_count': partial_count,
        'success_rate': round(success_rate, 2),
        'success_methods': test_results['success'],
        'failed_methods': test_results['failed'],
        'partial_methods': test_results['partial']
    }


def print_test_summary():
    """테스트 결과 요약을 예쁘게 출력"""
    summary = get_test_results()
    
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    print(f"📈 총 테스트 수: {summary['total_tests']}개")
    print(f"✅ 성공: {summary['success_count']}개 ({summary['success_rate']}%)")
    print(f"❌ 실패: {summary['failed_count']}개")
    print(f"⚠️ 부분 성공: {summary['partial_count']}개")
    
    if summary['failed_methods']:
        print(f"\n❌ 실패한 메서드들:")
        for method in summary['failed_methods']:
            print(f"   • {method}")
    
    if summary['partial_methods']:
        print(f"\n⚠️ 부분 성공한 메서드들:")
        for method in summary['partial_methods']:
            print(f"   • {method}")
    
    print("="*60)


def test_api_method(method_name: str, method_func: callable, *args, **kwargs) -> Any:
    """
    API 메서드 테스트 헬퍼 함수 - 모든 타입의 응답을 상세히 표시
    
    Args:
        method_name: 테스트할 메서드의 이름
        method_func: 테스트할 메서드 함수
        *args: 메서드에 전달할 위치 인수
        **kwargs: 메서드에 전달할 키워드 인수
        
    Returns:
        메서드 실행 결과 (실패 시 None)
    """
    global test_results
    test_results['total_tests'] += 1
    
    print(f"\n🔍 테스트: {method_name}")
    print(f"📝 파라미터: args={args}, kwargs={kwargs}")
    
    try:
        start_time = time.time()
        result = method_func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        
        if result is None:
            print(f"❌ 실패: {method_name} - 결과 없음")
            test_results['failed'].append(method_name)
            return None
            
        elif isinstance(result, dict):
            return _handle_dict_result(method_name, result, elapsed_time)
            
        elif isinstance(result, pd.DataFrame):
            return _handle_dataframe_result(method_name, result, elapsed_time)
            
        elif isinstance(result, tuple):
            return _handle_tuple_result(method_name, result, elapsed_time)
            
        elif isinstance(result, list):
            return _handle_list_result(method_name, result, elapsed_time)
            
        elif isinstance(result, bool):
            return _handle_bool_result(method_name, result, elapsed_time)
            
        else:
            return _handle_other_result(method_name, result, elapsed_time)
            
    except Exception as e:
        print(f"❌ 예외 발생: {method_name} - {str(e)}")
        test_results['failed'].append(method_name)
        return None


def _handle_dict_result(method_name: str, result: dict, elapsed_time: float) -> dict:
    """Dict 타입 결과 처리"""
    global test_results
    
    rt_cd = result.get('rt_cd')
    
    # JSON 디코드 에러 처리
    if rt_cd == 'JSON_DECODE_ERROR':
        print(f"❌ JSON 디코드 실패: {method_name}")
        if 'raw_text' in result:
            raw_text = result['raw_text'][:200] + "..." if len(result['raw_text']) > 200 else result['raw_text']
            print(f"📄 원시 응답 (처음 200자): {raw_text}")
        print(f"🔢 HTTP 상태 코드: {result.get('status_code', 'N/A')}")
        if '디버깅_정보' in result:
            print(f"🔧 {result['디버깅_정보']}")
        test_results['failed'].append(method_name)
        return result
    
    elif rt_cd == '0' or rt_cd == 0:
        print(f"✅ 성공: {method_name} (응답시간: {elapsed_time:.2f}초)")
        print(f"📊 응답 키: {list(result.keys())}")
        
        # output 데이터 분석
        if 'output' in result:
            _analyze_output_data(result['output'])
        elif 'output1' in result:
            print(f"📊 output1 타입: {type(result['output1'])}")
        elif 'output2' in result:
            print(f"📊 output2 타입: {type(result['output2'])}")
            
        test_results['success'].append(method_name)
        return result
    else:
        print(f"⚠️ 부분 성공: {method_name} - rt_cd: {rt_cd}, msg: {result.get('msg1', '')}")
        test_results['partial'].append(method_name)
        return result


def _handle_dataframe_result(method_name: str, result: pd.DataFrame, elapsed_time: float) -> pd.DataFrame:
    """DataFrame 타입 결과 처리"""
    global test_results
    
    print(f"✅ 성공: {method_name} (응답시간: {elapsed_time:.2f}초)")
    print(f"📊 DataFrame 정보:")
    print(f"   • 형태: {result.shape} (행x열)")
    
    if len(result.columns) <= 10:
        print(f"   • 컬럼: {list(result.columns)}")
    else:
        print(f"   • 컬럼 (처음 10개): {list(result.columns)[:10]}...")
    
    if len(result) > 0:
        print(f"   • 샘플 데이터 (첫 3개 행):")
        try:
            print(result.head(3).to_string(max_cols=8, max_colwidth=12))
        except:
            print("   [데이터 표시 오류 - 복잡한 구조]")
    else:
        print(f"   • 데이터: 비어있음")
    
    test_results['success'].append(method_name)
    return result


def _handle_tuple_result(method_name: str, result: tuple, elapsed_time: float) -> tuple:
    """Tuple 타입 결과 처리"""
    global test_results
    
    print(f"✅ 성공: {method_name} (응답시간: {elapsed_time:.2f}초)")
    print(f"📊 Tuple 정보:")
    print(f"   • 길이: {len(result)}개 요소")
    
    for i, item in enumerate(result):
        if isinstance(item, pd.DataFrame):
            print(f"   • [{i}]: DataFrame {item.shape} (행x열)")
        elif isinstance(item, dict):
            print(f"   • [{i}]: Dict ({len(item)}개 키)")
        elif isinstance(item, list):
            print(f"   • [{i}]: List ({len(item)}개 항목)")
        else:
            print(f"   • [{i}]: {type(item).__name__} = {item}")
    
    test_results['success'].append(method_name)
    return result


def _handle_list_result(method_name: str, result: list, elapsed_time: float) -> list:
    """List 타입 결과 처리"""
    global test_results
    
    print(f"✅ 성공: {method_name} (응답시간: {elapsed_time:.2f}초)")
    print(f"📊 List 정보:")
    print(f"   • 길이: {len(result)}개 항목")
    
    if len(result) > 0:
        first_item = result[0]
        if isinstance(first_item, dict):
            print(f"   • 첫 번째 항목: Dict ({len(first_item)}개 키)")
            if len(first_item.keys()) <= 15:
                print(f"   • 첫 번째 항목 키: {list(first_item.keys())}")
            else:
                print(f"   • 첫 번째 항목 키 (처음 10개): {list(first_item.keys())[:10]}...")
        else:
            print(f"   • 첫 번째 항목 타입: {type(first_item).__name__}")
            print(f"   • 첫 번째 항목 값: {str(first_item)[:100]}...")
    
    test_results['success'].append(method_name)
    return result


def _handle_bool_result(method_name: str, result: bool, elapsed_time: float) -> bool:
    """Boolean 타입 결과 처리"""
    global test_results
    
    print(f"✅ 성공: {method_name} (응답시간: {elapsed_time:.2f}초)")
    print(f"📊 Boolean 결과: {result}")
    
    test_results['success'].append(method_name)
    return result


def _handle_other_result(method_name: str, result: Any, elapsed_time: float) -> Any:
    """기타 타입 결과 처리"""
    global test_results
    
    print(f"✅ 성공: {method_name} (응답시간: {elapsed_time:.2f}초)")
    print(f"📊 결과 타입: {type(result).__name__}")
    
    result_str = str(result)
    if len(result_str) <= 200:
        print(f"📋 결과 값: {result}")
    else:
        print(f"📋 결과 값 (처음 200자): {result_str[:200]}...")
    
    test_results['success'].append(method_name)
    return result


def _analyze_output_data(output: Any):
    """output 데이터 분석 및 표시"""
    if isinstance(output, list) and len(output) > 0:
        print(f"📋 데이터 수: {len(output)}개")
        if len(output[0].keys()) <= 20:  # 키가 적으면 모두 표시
            print(f"📋 첫 번째 항목 키: {list(output[0].keys())}")
        else:  # 키가 많으면 처음 10개만 표시
            print(f"📋 첫 번째 항목 키 (처음 10개): {list(output[0].keys())[:10]}...")
    elif isinstance(output, dict):
        if len(output.keys()) <= 20:
            print(f"📋 데이터 키: {list(output.keys())}")
        else:
            print(f"📋 데이터 키 (처음 15개): {list(output.keys())[:15]}...")
    else:
        print(f"📊 output: {output}")


def setup_test_environment():
    """
    테스트 환경을 설정하고 기본 객체들을 반환
    
    Returns:
        tuple: (agent, TEST_STOCK, TEST_DATE)
    """
    try:
        # PyKIS Agent 초기화
        sys.path.append('..' if os.path.exists('../pykis') else '.')
        from pykis import Agent
        
        agent = Agent()
        TEST_STOCK = "005930"  # 삼성전자
        TEST_DATE = datetime.now().strftime('%Y%m%d')
        
        print("✅ 테스트 환경 설정 완료")
        print(f"🎯 테스트 종목: {TEST_STOCK} (삼성전자)")
        print(f"📅 테스트 날짜: {TEST_DATE}")
        
        return agent, TEST_STOCK, TEST_DATE
        
    except Exception as e:
        print(f"❌ 테스트 환경 설정 실패: {e}")
        raise


def reload_modules():
    """PyKIS 관련 모듈들을 완전히 재로드"""
    modules_to_reload = [
        'pykis.core.client',
        'pykis.core.auth',
        'pykis.stock.api', 
        'pykis.stock.market',
        'pykis.stock.condition',
        'pykis.account.api',
        'pykis.program.api',
        'pykis.core.agent'
    ]

    print("🔄 모듈 완전 재로드 시작...")
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            del sys.modules[module_name]
            print(f"🗑️  {module_name} 모듈 제거")
    
    print("✅ 모듈 재로드 완료")


def batch_test_methods(agent, method_configs: List[Dict[str, Any]]):
    """
    여러 메서드를 일괄 테스트
    
    Args:
        agent: PyKIS Agent 인스턴스
        method_configs: 테스트할 메서드 설정 리스트
                       [{'name': '메서드명', 'func': 함수, 'args': [인수들], 'kwargs': {키워드인수}}]
    """
    print(f"\n🚀 일괄 테스트 시작 - {len(method_configs)}개 메서드")
    print("="*50)
    
    for config in method_configs:
        method_name = config['name']
        method_func = config['func']
        args = config.get('args', [])
        kwargs = config.get('kwargs', {})
        
        test_api_method(method_name, method_func, *args, **kwargs)
        time.sleep(0.1)  # API 호출 간격 조절
    
    print_test_summary()


# 자주 사용하는 테스트 설정들
def get_common_test_configs(agent, test_stock: str, test_date: str) -> List[Dict[str, Any]]:
    """자주 사용하는 테스트 설정 반환"""
    return [
        {'name': 'get_stock_price', 'func': agent.get_stock_price, 'args': [test_stock]},
        {'name': 'get_daily_price', 'func': agent.get_daily_price, 'args': [test_stock]},
        {'name': 'get_minute_price', 'func': agent.get_minute_price, 'args': [test_stock, "153000"]},
        {'name': 'fetch_minute_data', 'func': agent.fetch_minute_data, 'args': [test_stock, test_date]},
        {'name': 'get_account_balance', 'func': agent.get_account_balance, 'args': []},
    ]


if __name__ == "__main__":
    # 모듈이 직접 실행될 때의 테스트
    print("🧪 테스트 헬퍼 모듈 - 직접 실행 테스트")
    
    try:
        agent, TEST_STOCK, TEST_DATE = setup_test_environment()
        
        # 간단한 테스트 실행
        result = test_api_method("get_stock_price", agent.get_stock_price, TEST_STOCK)
        
        print_test_summary()
        
    except Exception as e:
        print(f"❌ 테스트 실행 실패: {e}") 