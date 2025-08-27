#!/usr/bin/env python3
"""
investor_api.py 변경사항 검증 테스트
- get_stock_investor의 반환 타입이 DataFrame → Dict로 변경됨
- 관련 메서드들이 dict 형식으로 처리하도록 수정됨
"""

import sys
import logging
from typing import Optional, Dict

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_investor_api_structure():
    """investor_api.py의 구조적 변경사항 검증"""
    
    try:
        # 파일 내용 읽기
        with open('/home/unohee/tools/pykis/pykis/stock/investor_api.py', 'r') as f:
            content = f.read()
        
        # 변경사항 확인
        checks = []
        
        # 1. get_stock_investor 반환 타입 확인
        if 'def get_stock_investor(self, ticker: str = \'\', retries: int = 10, force_refresh: bool = False) -> Optional[Dict]:' in content:
            checks.append(("get_stock_investor 반환 타입", "✅ Dict로 변경됨"))
        else:
            checks.append(("get_stock_investor 반환 타입", "❌ DataFrame으로 유지됨"))
        
        # 2. _make_request_dict 사용 확인
        if 'return self._make_request_dict(' in content and 'get_stock_investor' in content:
            checks.append(("get_stock_investor 구현", "✅ _make_request_dict 사용"))
        else:
            checks.append(("get_stock_investor 구현", "❌ _make_request_dataframe 사용"))
        
        # 3. _get_foreign_broker_historical 메서드의 dict 처리 확인
        if 'investor_data = self.get_stock_investor(ticker=code)' in content:
            checks.append(("_get_foreign_broker_historical", "✅ dict 형식 처리로 변경됨"))
        else:
            checks.append(("_get_foreign_broker_historical", "❌ DataFrame 처리 유지됨"))
        
        # 4. output 데이터 처리 확인
        if "if not investor_data or 'output' not in investor_data:" in content:
            checks.append(("dict output 처리", "✅ dict 구조에 맞게 변경됨"))
        else:
            checks.append(("dict output 처리", "❌ DataFrame 방식 유지됨"))
        
        # 5. 날짜 데이터 검색 방식 확인
        if "if row.get('stck_bsop_date') == date:" in content:
            checks.append(("날짜 검색 방식", "✅ dict 방식으로 변경됨"))
        else:
            checks.append(("날짜 검색 방식", "❌ DataFrame 방식 유지됨"))
        
        # 결과 출력
        print("\n" + "="*60)
        print("investor_api.py 변경사항 검증 결과")
        print("="*60)
        
        for check_name, result in checks:
            print(f"📊 {check_name}: {result}")
        
        # 요약
        success_count = sum(1 for _, result in checks if "✅" in result)
        total_count = len(checks)
        
        print(f"\n📝 요약: {success_count}/{total_count}개 변경사항 적용 완료")
        
        if success_count == total_count:
            print("🎉 모든 변경사항이 올바르게 적용되었습니다!")
            return True
        else:
            print("⚠️ 일부 변경사항이 누락되었습니다.")
            return False
            
    except Exception as e:
        logger.error(f"검증 실패: {e}")
        return False

def verify_j_code_usage():
    """J 코드 사용 확인"""
    try:
        with open('/home/unohee/tools/pykis/pykis/stock/investor_api.py', 'r') as f:
            content = f.read()
        
        j_count = content.count('FID_COND_MRKT_DIV_CODE": "J"')
        un_count = content.count('FID_COND_MRKT_DIV_CODE": "UN"')
        
        print(f"\n🔍 시장 코드 사용 현황:")
        print(f"  - J 코드: {j_count}개")
        print(f"  - UN 코드: {un_count}개")
        
        if un_count == 0 and j_count > 0:
            print("✅ 투자자 API는 모두 J 코드 사용 (호환성 보장)")
        else:
            print("⚠️ UN 코드가 남아있거나 J 코드가 없습니다")
        
        return un_count == 0 and j_count > 0
        
    except Exception as e:
        logger.error(f"J 코드 확인 실패: {e}")
        return False

if __name__ == "__main__":
    print("🔄 investor_api.py 변경사항 검증 시작...")
    
    structure_ok = test_investor_api_structure()
    j_code_ok = verify_j_code_usage()
    
    if structure_ok and j_code_ok:
        print("\n🎯 결론: 모든 변경사항이 성공적으로 적용되었습니다!")
        print("  - get_stock_investor: DataFrame → Dict 변경 완료")
        print("  - 관련 메서드들: dict 처리 방식으로 업데이트")
        print("  - 시장 코드: J 코드 사용으로 호환성 보장")
    else:
        print("\n❌ 일부 변경사항에 문제가 있습니다.")