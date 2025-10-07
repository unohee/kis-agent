#!/usr/bin/env python3
"""
코스피200 지수선물 베이시스 계산 테스트

베이시스 = 선물가격 - 현물가격
- 양수: 콘탱고 (정상적인 시장 상태)
- 음수: 백워데이션 (비정상적인 시장 상태)
"""

import os
import sys
from datetime import datetime
from typing import Dict, Optional

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import KISClient, StockAPI
from pykis.stock.api import get_kospi200_futures_code


class KospiBasisTester:
    """코스피200 베이시스 계산 테스터"""

    def __init__(self):
        """KISClient 및 StockAPI 초기화"""
        self.client = KISClient()
        self.stock_api = StockAPI(self.client, {})

    def get_current_futures_code(self) -> str:
        """현재 날짜 기준 가장 가까운 선물 종목코드 계산"""
        current_code = get_kospi200_futures_code()
        print(f" 현재 날짜 기준 선물 종목코드: {current_code}")
        return current_code

    def calculate_basis(self, futures_code: str = None) -> Dict:
        """베이시스 계산"""
        print(f"\n{'='*60}")
        print(" 코스피200 지수선물 베이시스 계산")
        print(f"{'='*60}")

        # 선물 종목코드 설정
        if not futures_code:
            futures_code = self.get_current_futures_code()

        print(f" 사용할 선물 종목코드: {futures_code}")

        # 선물옵션 시세 조회
        print("\n 선물옵션 시세 조회 중...")
        futures_info = self.stock_api.get_future_option_price(
            market_div_code="F",
            input_iscd=futures_code
        )

        if not futures_info or futures_info.get('rt_cd') != '0':
            print(f" 선물 시세 조회 실패: {futures_info.get('msg1', '알 수 없는 오류') if futures_info else '응답 없음'}")
            return None

        print(" 선물 시세 조회 성공")

        # 데이터 추출
        result = self.extract_data(futures_info, futures_code)

        if result:
            self.display_results(result)

        return result

    def extract_data(self, futures_info: Dict, futures_code: str) -> Optional[Dict]:
        """API 응답에서 데이터 추출"""
        result = {
            'futures_code': futures_code,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'futures_price': None,
            'kospi200_index': None,
            'api_basis': None,
            'calculated_basis': None,
            'success': False
        }

        try:
            # output1에서 선물 가격 추출
            if 'output1' in futures_info and futures_info['output1']:
                futures_data = futures_info['output1']
                result['futures_price'] = float(futures_data.get('futs_prpr', 0))

                # API에서 제공하는 베이시스 (있으면)
                api_basis = futures_data.get('mrkt_basis') or futures_data.get('basis')
                if api_basis:
                    result['api_basis'] = float(api_basis)

                print(f" 선물 현재가: {result['futures_price']:.2f}")
                if result['api_basis'] is not None:
                    print(f" API 제공 베이시스: {result['api_basis']:.2f}")

            # output3에서 코스피200 지수 추출
            if 'output3' in futures_info and futures_info['output3']:
                kospi200_data = futures_info['output3']
                result['kospi200_index'] = float(kospi200_data.get('bstp_nmix_prpr', 0))
                print(f" 코스피200 현물지수: {result['kospi200_index']:.2f}")

            # 베이시스 계산
            if result['futures_price'] and result['kospi200_index']:
                result['calculated_basis'] = result['futures_price'] - result['kospi200_index']
                result['success'] = True
                print(f" 계산된 베이시스: {result['calculated_basis']:.2f}")

            return result

        except Exception as e:
            print(f" 데이터 추출 오류: {e}")
            return None

    def display_results(self, result: Dict):
        """결과 출력"""
        print(f"\n{'='*60}")
        print(" 베이시스 계산 결과")
        print(f"{'='*60}")

        print(f" 계산 시간: {result['timestamp']}")
        print(f" 선물 종목코드: {result['futures_code']}")
        print(f" 선물 현재가: {result['futures_price']:.2f}")
        print(f" 코스피200 지수: {result['kospi200_index']:.2f}")

        if result['calculated_basis'] is not None:
            basis = result['calculated_basis']
            print(f" 베이시스: {basis:.2f}")

            # 베이시스 해석
            if basis > 0:
                print(" 콘탱고 상태 (정상적인 시장)")
                print("   해석: 선물가격이 현물가격보다 높음")
            elif basis < 0:
                print(" 백워데이션 상태 (비정상적인 시장)")
                print("   해석: 선물가격이 현물가격보다 낮음")
            else:
                print("➡️ 완전 균형 상태")
                print("   해석: 선물가격과 현물가격이 동일")

            # 베이시스 크기 분석
            abs_basis = abs(basis)
            if abs_basis < 5:
                print(f" 베이시스 크기: 매우 작음 (±{abs_basis:.2f})")
            elif abs_basis < 20:
                print(f" 베이시스 크기: 보통 (±{abs_basis:.2f})")
            else:
                print(f" 베이시스 크기: 큼 (±{abs_basis:.2f})")

        if result['api_basis'] is not None:
            print(f" API 제공 베이시스: {result['api_basis']:.2f}")
            if result['calculated_basis'] is not None:
                diff = abs(result['calculated_basis'] - result['api_basis'])
                print(f" 계산 차이: {diff:.2f}")

    def test_multiple_codes(self):
        """여러 선물 종목코드 테스트"""
        print(f"\n{'='*60}")
        print(" 여러 선물 종목코드 테스트")
        print(f"{'='*60}")

        # 현재 거래되는 가능한 종목코드들
        test_codes = [
            "101W03",  # 3월물
            "101W06",  # 6월물
            "101W09",  # 9월물
            "101W12",  # 12월물
        ]

        results = []
        for code in test_codes:
            print(f"\n 테스트 종목코드: {code}")
            result = self.calculate_basis(code)
            if result and result['success']:
                results.append(result)
                print(f" {code} 테스트 성공")
            else:
                print(f" {code} 테스트 실패")

        # 결과 요약
        if results:
            print(f"\n{'='*60}")
            print(" 테스트 결과 요약")
            print(f"{'='*60}")

            for result in results:
                print(f"{result['futures_code']}: 베이시스 {result['calculated_basis']:.2f}")

        return results

    def run_comprehensive_test(self):
        """종합 테스트"""
        print(" 코스피200 베이시스 계산 종합 테스트 시작")
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 1. 현재 날짜 기준 자동 계산
        print("\n1️⃣ 현재 날짜 기준 자동 계산")
        auto_result = self.calculate_basis()

        # 2. 여러 종목코드 테스트
        print("\n2️⃣ 여러 종목코드 테스트")
        manual_results = self.test_multiple_codes()

        # 3. 최종 결과
        print(f"\n{'='*60}")
        print(" 최종 테스트 결과")
        print(f"{'='*60}")

        if auto_result and auto_result['success']:
            print(f" 자동 계산 성공: {auto_result['futures_code']} 베이시스 {auto_result['calculated_basis']:.2f}")
        else:
            print(" 자동 계산 실패")

        print(f" 수동 테스트 성공: {len(manual_results)}개 종목")

        print(f"완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """메인 함수"""
    tester = KospiBasisTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
