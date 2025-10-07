#!/usr/bin/env python3

"""
매물대 조회(get_pbar_tratio) 테스트 코드

이 스크립트는 PyKIS의 get_pbar_tratio 메서드를 종합적으로 테스트하고,
매물대 분석을 통한 지지/저항선 파악 기능을 검증합니다.

주요 기능:
1. 기본 API 호출 테스트
2. 응답 데이터 구조 검증
3. 매물대 데이터 분석
4. 현재가와 매물대 비교
5. 여러 종목 일괄 테스트
6. 매물대 시각화 (선택사항)

실행 방법:
    python examples/test_pbar_tratio.py
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import Agent


class PbarTratioTester:
    """매물대 조회 테스트 클래스"""

    def __init__(self):
        """테스트 환경 초기화"""
        self.agent = Agent()
        self.test_results = []
        self.test_stocks = [
            "005930",  # 삼성전자
            "000660",  # SK하이닉스
            "035420",  # NAVER
            "051910",  # LG화학
            "028260",  # 삼성물산
        ]

    def test_basic_api_call(self, code: str) -> Dict:
        """기본 API 호출 테스트"""
        print(f"\n{'='*60}")
        print(f" 매물대 조회 테스트: {code}")
        print(f"{'='*60}")

        try:
            start_time = time.time()
            result = self.agent.get_pbar_tratio(code)
            elapsed_time = time.time() - start_time

            if result is None:
                print(f" API 호출 실패: {code}")
                return None

            if result.get('rt_cd') != '0':
                print(f" API 오류: {result.get('msg1', '알 수 없는 오류')}")
                return None

            print(f" API 호출 성공 (응답시간: {elapsed_time:.3f}초)")
            print(f" 응답 키: {list(result.keys())}")

            # 응답 구조 검증
            if 'output1' in result:
                print(f" output1 타입: {type(result['output1'])}")

            if 'output2' in result:
                output2 = result['output2']
                if isinstance(output2, list):
                    print(f" output2 데이터 수: {len(output2)}개")
                    if len(output2) > 0:
                        print(f" 첫 번째 항목 키: {list(output2[0].keys())}")

            return result

        except Exception as e:
            print(f" 예외 발생: {e}")
            return None

    def analyze_volume_profile(self, result: Dict, code: str) -> Dict:
        """매물대 데이터 분석"""
        print(f"\n 매물대 분석: {code}")

        if not result or 'output2' not in result:
            print(" 매물대 데이터 없음")
            return None

        volume_profile = result['output2']
        if not isinstance(volume_profile, list) or len(volume_profile) == 0:
            print(" 매물대 데이터 형식 오류")
            return None

        print(f" 매물대 레벨 수: {len(volume_profile)}개")

        # 거래량 기준 키 확인
        first_item = volume_profile[0]
        volume_keys = [key for key in first_item if 'vol' in key.lower()]
        print(f" 거래량 관련 키: {volume_keys}")

        # 실제 API 응답 구조에 맞는 키 사용
        volume_key = 'cntg_vol'  # 거래량 데이터

        if volume_key not in first_item:
            print(f" 거래량 데이터 키 '{volume_key}'를 찾을 수 없음")
            print(f" 사용 가능한 키: {list(first_item.keys())}")
            return None

        print(f" 사용할 거래량 키: {volume_key}")

        # 거래량 데이터 처리
        try:
            for item in volume_profile:
                vol_str = item.get(volume_key, '0')
                item[volume_key] = float(vol_str) if vol_str else 0.0

            # 최대 거래량 매물대 찾기
            max_volume_level = max(volume_profile, key=lambda x: x.get(volume_key, 0))
            max_volume_price = int(max_volume_level.get('stck_prpr', '0'))
            max_volume = max_volume_level.get(volume_key, 0)

            # 상위 5개 매물대 추출
            top_5_levels = sorted(volume_profile,
                                key=lambda x: x.get(volume_key, 0),
                                reverse=True)[:5]

            analysis = {
                'max_volume_price': max_volume_price,
                'max_volume': max_volume,
                'top_5_levels': top_5_levels,
                'volume_key': volume_key,
                'total_levels': len(volume_profile)
            }

            print(f" 최대 거래량 매물대: {max_volume_price:,}원 (거래량: {max_volume:.2f})")
            print(" 상위 5개 매물대:")
            for i, level in enumerate(top_5_levels, 1):
                price = int(level.get('stck_prpr', '0'))
                volume = level.get(volume_key, 0)
                print(f"   {i}. {price:,}원 - 거래량: {volume:.2f}")

            return analysis

        except Exception as e:
            print(f" 매물대 분석 오류: {e}")
            return None

    def compare_with_current_price(self, code: str, analysis: Dict, pbar_result: Dict = None) -> Dict:
        """현재가와 매물대 비교 분석"""
        print(f"\n 현재가 vs 매물대 비교: {code}")

        if not analysis:
            print(" 매물대 분석 결과 없음")
            return None

        # pbar_tratio API의 output1에서 현재가 정보 가져오기
        try:
            if pbar_result and 'output1' in pbar_result:
                current_price_info = pbar_result['output1']
                current_price = int(current_price_info.get('stck_prpr', '0'))
                stock_name = current_price_info.get('hts_kor_isnm', code)
                prdy_vrss = current_price_info.get('prdy_vrss', '0')
                prdy_ctrt = current_price_info.get('prdy_ctrt', '0')
                acml_vol = current_price_info.get('acml_vol', '0')

                print(f" 종목명: {stock_name}")
                print(f" 현재가: {current_price:,}원")
                print(f" 전일 대비: {prdy_vrss}원 ({prdy_ctrt}%)")
                print(f" 누적 거래량: {acml_vol}")
            else:
                # 기존 방식 (fallback)
                price_result = self.agent.get_stock_price(code)
                if not price_result or price_result.get('rt_cd') != '0':
                    print(" 현재가 조회 실패")
                    return None

                current_price = int(price_result['output']['stck_prpr'])
                print(f" 현재가: {current_price:,}원")

            # 최대 매물대와 비교
            max_volume_price = analysis['max_volume_price']
            gap = current_price - max_volume_price
            gap_percentage = (gap / max_volume_price) * 100 if max_volume_price > 0 else 0

            print(f" 최대 매물대: {max_volume_price:,}원")
            print(f"↕️ 가격 이격: {gap:,}원 ({gap_percentage:+.2f}%)")

            # 지지/저항 분석
            if gap > 0:
                print(" 현재가 > 최대 매물대: 지지선으로 작용 가능")
                signal = "SUPPORT"
            elif gap < 0:
                print(" 현재가 < 최대 매물대: 저항선으로 작용 가능")
                signal = "RESISTANCE"
            else:
                print("➡️ 현재가 = 최대 매물대: 균형 상태")
                signal = "NEUTRAL"

            # 가장 가까운 매물대 찾기
            closest_level = min(analysis['top_5_levels'],
                              key=lambda x: abs(current_price - int(x.get('stck_prpr', '0'))))
            closest_price = int(closest_level.get('stck_prpr', '0'))
            closest_volume = closest_level.get(analysis['volume_key'], 0)

            print(f" 가장 가까운 매물대: {closest_price:,}원 (거래량: {closest_volume:.2f})")

            comparison = {
                'current_price': current_price,
                'max_volume_price': max_volume_price,
                'gap': gap,
                'gap_percentage': gap_percentage,
                'signal': signal,
                'closest_price': closest_price,
                'closest_volume': closest_volume
            }

            return comparison

        except Exception as e:
            print(f" 현재가 비교 오류: {e}")
            return None

    def test_single_stock(self, code: str) -> Dict:
        """단일 종목 종합 테스트"""
        print(f"\n{'='*80}")
        print(f" 종합 테스트: {code}")
        print(f"{'='*80}")

        # 1. 기본 API 호출
        result = self.test_basic_api_call(code)
        if not result:
            return {'code': code, 'success': False, 'error': 'API 호출 실패'}

        # 2. 매물대 분석
        analysis = self.analyze_volume_profile(result, code)
        if not analysis:
            return {'code': code, 'success': False, 'error': '매물대 분석 실패'}

        # 3. 현재가 비교
        comparison = self.compare_with_current_price(code, analysis, result)
        if not comparison:
            return {'code': code, 'success': False, 'error': '현재가 비교 실패'}

        # 4. 결과 요약
        summary = {
            'code': code,
            'success': True,
            'analysis': analysis,
            'comparison': comparison,
            'timestamp': datetime.now().isoformat()
        }

        print("\n 테스트 결과 요약:")
        print(f"    종목: {code}")
        print(f"    매물대 레벨: {analysis['total_levels']}개")
        print(f"    최대 매물대: {analysis['max_volume_price']:,}원")
        print(f"    현재가: {comparison['current_price']:,}원")
        print(f"    신호: {comparison['signal']}")

        return summary

    def test_multiple_stocks(self) -> List[Dict]:
        """여러 종목 일괄 테스트"""
        print(f"\n{'='*80}")
        print(" 여러 종목 일괄 테스트")
        print(f"{'='*80}")

        results = []

        for i, code in enumerate(self.test_stocks, 1):
            print(f"\n[{i}/{len(self.test_stocks)}] 테스트 진행 중...")

            result = self.test_single_stock(code)
            results.append(result)

            # API 호출 간격 유지
            if i < len(self.test_stocks):
                time.sleep(0.2)

        return results

    def print_final_summary(self, results: List[Dict]):
        """최종 결과 요약"""
        print(f"\n{'='*80}")
        print(" 최종 테스트 결과 요약")
        print(f"{'='*80}")

        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]

        print(f" 총 테스트 수: {len(results)}개")
        print(f" 성공: {len(successful)}개 ({len(successful)/len(results)*100:.1f}%)")
        print(f" 실패: {len(failed)}개")

        if failed:
            print("\n 실패한 종목:")
            for result in failed:
                print(f"   • {result['code']}: {result.get('error', '알 수 없는 오류')}")

        if successful:
            print("\n 성공한 종목들의 매물대 분석:")
            for result in successful:
                comparison = result.get('comparison', {})
                analysis = result.get('analysis', {})

                print(f"   • {result['code']}: "
                      f"현재가 {comparison.get('current_price', 0):,}원, "
                      f"매물대 {analysis.get('max_volume_price', 0):,}원, "
                      f"신호: {comparison.get('signal', 'N/A')}")

        # 신호별 분류
        if successful:
            signals = {}
            for result in successful:
                signal = result.get('comparison', {}).get('signal', 'N/A')
                if signal not in signals:
                    signals[signal] = []
                signals[signal].append(result['code'])

            print("\n 신호별 분류:")
            for signal, codes in signals.items():
                print(f"   • {signal}: {', '.join(codes)}")

    def run_all_tests(self):
        """모든 테스트 실행"""
        print(f"{'='*80}")
        print(" 매물대 조회(get_pbar_tratio) 종합 테스트")
        print(f"{'='*80}")
        print(f" 테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # 여러 종목 일괄 테스트
            results = self.test_multiple_stocks()

            # 최종 결과 요약
            self.print_final_summary(results)

            # 결과 저장 (선택사항)
            self.save_results(results)

        except Exception as e:
            print(f" 테스트 실행 중 오류 발생: {e}")

        print(f"\n 테스트 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def save_results(self, results: List[Dict]):
        """테스트 결과 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"pbar_tratio_test_results_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"\n 테스트 결과 저장: {filename}")

        except Exception as e:
            print(f" 결과 저장 실패: {e}")

def main():
    """메인 함수"""
    tester = PbarTratioTester()

    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 테스트가 중단되었습니다.")
    except Exception as e:
        print(f" 예상치 못한 오류: {e}")

if __name__ == "__main__":
    main()
