#!/usr/bin/env python3

"""
매물대 조회(get_pbar_tratio) 테스트 코드 - 시각화 포함

이 스크립트는 PyKIS의 get_pbar_tratio 메서드를 종합적으로 테스트하고,
매물대 분석을 시각화하여 지지/저항선을 직관적으로 파악합니다.

주요 기능:
1. 기본 API 호출 테스트
2. 응답 데이터 구조 검증
3. 매물대 데이터 분석
4. 현재가와 매물대 비교
5. 매물대 시각화 차트
6. 여러 종목 일괄 테스트

필요한 패키지:
    pip install matplotlib seaborn pandas

실행 방법:
    python examples/test_pbar_tratio_with_chart.py
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List

# 시각화 라이브러리
try:
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns
    VISUALIZATION_AVAILABLE = True
except ImportError:
    print(" 시각화 라이브러리가 설치되지 않았습니다.")
    print(" 설치 명령: pip install matplotlib seaborn pandas")
    VISUALIZATION_AVAILABLE = False

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import Agent


class PbarTratioVisualizer:
    """매물대 조회 테스트 및 시각화 클래스"""

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

        # 한글 폰트 설정 (시각화용)
        if VISUALIZATION_AVAILABLE:
            self.setup_korean_font()

    def setup_korean_font(self):
        """한글 폰트 설정"""
        try:
            # 한글 폰트 찾기
            font_candidates = [
                'Malgun Gothic',    # Windows
                'Apple Gothic',     # macOS
                'NanumGothic',      # Linux
                'DejaVu Sans'       # 기본값
            ]

            available_fonts = [f.name for f in fm.fontManager.ttflist]
            korean_font = None

            for font in font_candidates:
                if font in available_fonts:
                    korean_font = font
                    break

            if korean_font:
                plt.rcParams['font.family'] = korean_font
                print(f" 한글 폰트 설정: {korean_font}")
            else:
                print(" 한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")

            plt.rcParams['axes.unicode_minus'] = False

        except Exception as e:
            print(f" 폰트 설정 오류: {e}")

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
            processed_data = []
            for item in volume_profile:
                vol_str = item.get(volume_key, '0')
                volume = float(vol_str) if vol_str else 0.0
                price = int(item.get('stck_prpr', '0'))

                processed_item = {
                    'price': price,
                    'volume': volume,
                    'original_data': item
                }
                processed_data.append(processed_item)

            # 가격순 정렬
            processed_data.sort(key=lambda x: x['price'])

            # 최대 거래량 매물대 찾기
            max_volume_level = max(processed_data, key=lambda x: x['volume'])

            # 상위 5개 매물대 추출
            top_5_levels = sorted(processed_data, key=lambda x: x['volume'], reverse=True)[:5]

            analysis = {
                'max_volume_price': max_volume_level['price'],
                'max_volume': max_volume_level['volume'],
                'top_5_levels': top_5_levels,
                'all_levels': processed_data,
                'volume_key': volume_key,
                'total_levels': len(processed_data)
            }

            print(f" 최대 거래량 매물대: {max_volume_level['price']:,}원 (거래량: {max_volume_level['volume']:.2f})")
            print(" 상위 5개 매물대:")
            for i, level in enumerate(top_5_levels, 1):
                print(f"   {i}. {level['price']:,}원 - 거래량: {level['volume']:.2f}")

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
                              key=lambda x: abs(current_price - x['price']))

            print(f" 가장 가까운 매물대: {closest_level['price']:,}원 (거래량: {closest_level['volume']:.2f})")

            comparison = {
                'current_price': current_price,
                'max_volume_price': max_volume_price,
                'gap': gap,
                'gap_percentage': gap_percentage,
                'signal': signal,
                'closest_price': closest_level['price'],
                'closest_volume': closest_level['volume']
            }

            return comparison

        except Exception as e:
            print(f" 현재가 비교 오류: {e}")
            return None

    def create_volume_profile_chart(self, code: str, analysis: Dict, comparison: Dict) -> str:
        """매물대 시각화 차트 생성"""
        if not VISUALIZATION_AVAILABLE:
            print(" 시각화 라이브러리가 없어 차트를 생성할 수 없습니다.")
            return None

        try:
            print(f"\n 매물대 차트 생성: {code}")

            # 데이터 준비
            levels = analysis['all_levels']
            prices = [level['price'] for level in levels]
            volumes = [level['volume'] for level in levels]
            current_price = comparison['current_price']
            max_volume_price = analysis['max_volume_price']

            # 차트 생성
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

            # 1. 매물대 바 차트 (세로)
            ax1.barh(prices, volumes, alpha=0.7, color='skyblue', edgecolor='navy', linewidth=0.5)

            # 현재가 표시
            ax1.axhline(current_price, color='red', linestyle='-', linewidth=2, label=f'현재가: {current_price:,}원')

            # 최대 매물대 표시
            ax1.axhline(max_volume_price, color='orange', linestyle='--', linewidth=2,
                       label=f'최대 매물대: {max_volume_price:,}원')

            # 상위 5개 매물대 표시
            for _i, level in enumerate(analysis['top_5_levels'][:3]):  # 상위 3개만
                ax1.axhline(level['price'], color='green', linestyle=':', alpha=0.7, linewidth=1)

            ax1.set_xlabel('거래량')
            ax1.set_ylabel('가격 (원)')
            ax1.set_title(f'{code} 매물대 분포 (Volume Profile)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # 가격 포맷팅
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

            # 2. 가격대별 거래량 분포 (히스토그램 스타일)
            ax2.plot(volumes, prices, 'b-', linewidth=2, alpha=0.8)
            ax2.fill_betweenx(prices, volumes, alpha=0.3, color='lightblue')

            # 현재가와 최대 매물대 표시
            ax2.axhline(current_price, color='red', linestyle='-', linewidth=2, label=f'현재가: {current_price:,}원')
            ax2.axhline(max_volume_price, color='orange', linestyle='--', linewidth=2,
                       label=f'최대 매물대: {max_volume_price:,}원')

            # 신호에 따른 배경색
            if comparison['signal'] == 'SUPPORT':
                ax2.axhspan(min(prices), max_volume_price, alpha=0.1, color='green')
                ax2.text(max(volumes)*0.7, max_volume_price + (max(prices)-min(prices))*0.05,
                        '지지 구간', fontsize=12, color='green', fontweight='bold')
            elif comparison['signal'] == 'RESISTANCE':
                ax2.axhspan(max_volume_price, max(prices), alpha=0.1, color='red')
                ax2.text(max(volumes)*0.7, max_volume_price + (max(prices)-min(prices))*0.05,
                        '저항 구간', fontsize=12, color='red', fontweight='bold')

            ax2.set_xlabel('거래량')
            ax2.set_ylabel('가격 (원)')
            ax2.set_title(f'{code} 매물대 곡선 및 지지/저항 분석')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            # 가격 포맷팅
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

            # 차트 정보 텍스트 추가
            info_text = f"""
신호: {comparison['signal']}
이격률: {comparison['gap_percentage']:+.2f}%
매물대 레벨: {analysis['total_levels']}개
            """.strip()

            ax2.text(0.02, 0.98, info_text, transform=ax2.transAxes,
                    verticalalignment='top', bbox={"boxstyle": 'round', "facecolor": 'wheat', "alpha": 0.8})

            plt.tight_layout()

            # 파일 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'pbar_chart_{code}_{timestamp}.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()

            print(f" 차트 저장: {filename}")
            return filename

        except Exception as e:
            print(f" 차트 생성 오류: {e}")
            return None

    def test_single_stock_with_chart(self, code: str) -> Dict:
        """단일 종목 종합 테스트 (차트 포함)"""
        print(f"\n{'='*80}")
        print(f" 종합 테스트 (차트 포함): {code}")
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

        # 4. 차트 생성
        chart_filename = None
        if VISUALIZATION_AVAILABLE:
            chart_filename = self.create_volume_profile_chart(code, analysis, comparison)

        # 5. 결과 요약
        summary = {
            'code': code,
            'success': True,
            'analysis': analysis,
            'comparison': comparison,
            'chart_filename': chart_filename,
            'timestamp': datetime.now().isoformat()
        }

        print("\n 테스트 결과 요약:")
        print(f"    종목: {code}")
        print(f"    매물대 레벨: {analysis['total_levels']}개")
        print(f"    최대 매물대: {analysis['max_volume_price']:,}원")
        print(f"    현재가: {comparison['current_price']:,}원")
        print(f"    신호: {comparison['signal']}")
        if chart_filename:
            print(f"    차트: {chart_filename}")

        return summary

    def test_multiple_stocks_with_charts(self) -> List[Dict]:
        """여러 종목 일괄 테스트 (차트 포함)"""
        print(f"\n{'='*80}")
        print(" 여러 종목 일괄 테스트 (차트 포함)")
        print(f"{'='*80}")

        results = []

        for i, code in enumerate(self.test_stocks, 1):
            print(f"\n[{i}/{len(self.test_stocks)}] 테스트 진행 중...")

            result = self.test_single_stock_with_chart(code)
            results.append(result)

            # API 호출 간격 유지
            if i < len(self.test_stocks):
                time.sleep(0.3)

        return results

    def create_summary_chart(self, results: List[Dict]):
        """종합 비교 차트 생성"""
        if not VISUALIZATION_AVAILABLE:
            return None

        try:
            successful_results = [r for r in results if r.get('success')]
            if len(successful_results) < 2:
                return None

            print("\n 종합 비교 차트 생성")

            # 데이터 준비
            codes = []
            current_prices = []
            max_volume_prices = []
            gap_percentages = []
            signals = []

            for result in successful_results:
                codes.append(result['code'])
                comparison = result['comparison']
                analysis = result['analysis']

                current_prices.append(comparison['current_price'])
                max_volume_prices.append(analysis['max_volume_price'])
                gap_percentages.append(comparison['gap_percentage'])
                signals.append(comparison['signal'])

            # 차트 생성
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

            # 1. 현재가 vs 최대 매물대 비교
            x_pos = np.arange(len(codes))
            width = 0.35

            ax1.bar(x_pos - width/2, current_prices, width, label='현재가', alpha=0.7, color='blue')
            ax1.bar(x_pos + width/2, max_volume_prices, width, label='최대 매물대', alpha=0.7, color='orange')

            ax1.set_xlabel('종목')
            ax1.set_ylabel('가격 (원)')
            ax1.set_title('현재가 vs 최대 매물대 비교')
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels(codes)
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # 가격 포맷팅
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000):,}K'))

            # 2. 이격률 바 차트
            colors = ['green' if gap > 0 else 'red' for gap in gap_percentages]
            ax2.bar(codes, gap_percentages, color=colors, alpha=0.7)
            ax2.axhline(0, color='black', linestyle='-', linewidth=1)
            ax2.set_xlabel('종목')
            ax2.set_ylabel('이격률 (%)')
            ax2.set_title('현재가 vs 최대 매물대 이격률')
            ax2.grid(True, alpha=0.3)

            # 3. 신호 분포 파이 차트
            signal_counts = {}
            for signal in signals:
                signal_counts[signal] = signal_counts.get(signal, 0) + 1

            colors_pie = {'SUPPORT': 'green', 'RESISTANCE': 'red', 'NEUTRAL': 'gray'}
            pie_colors = [colors_pie.get(signal, 'blue') for signal in signal_counts]

            ax3.pie(signal_counts.values(), labels=signal_counts.keys(), autopct='%1.1f%%',
                   colors=pie_colors, startangle=90)
            ax3.set_title('매물대 신호 분포')

            # 4. 종목별 상세 정보 테이블
            ax4.axis('tight')
            ax4.axis('off')

            table_data = []
            for result in successful_results:
                code = result['code']
                comparison = result['comparison']
                analysis = result['analysis']

                table_data.append([
                    code,
                    f"{comparison['current_price']:,}",
                    f"{analysis['max_volume_price']:,}",
                    f"{comparison['gap_percentage']:+.1f}%",
                    comparison['signal']
                ])

            table = ax4.table(cellText=table_data,
                            colLabels=['종목', '현재가', '최대매물대', '이격률', '신호'],
                            cellLoc='center',
                            loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.5)

            ax4.set_title('종목별 상세 정보', pad=20)

            plt.tight_layout()

            # 파일 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'pbar_summary_{timestamp}.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()

            print(f" 종합 차트 저장: {filename}")
            return filename

        except Exception as e:
            print(f" 종합 차트 생성 오류: {e}")
            return None

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

        # 차트 파일 목록
        chart_files = [r.get('chart_filename') for r in successful if r.get('chart_filename')]
        if chart_files:
            print("\n 생성된 차트 파일:")
            for filename in chart_files:
                print(f"   • {filename}")

    def run_all_tests(self):
        """모든 테스트 실행"""
        print(f"{'='*80}")
        print(" 매물대 조회(get_pbar_tratio) 종합 테스트 - 시각화 포함")
        print(f"{'='*80}")
        print(f" 테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if not VISUALIZATION_AVAILABLE:
            print(" 시각화 기능을 사용할 수 없습니다. 기본 테스트만 실행됩니다.")

        try:
            # 여러 종목 일괄 테스트 (차트 포함)
            results = self.test_multiple_stocks_with_charts()

            # 종합 비교 차트 생성
            if VISUALIZATION_AVAILABLE:
                summary_chart = self.create_summary_chart(results)
                if summary_chart:
                    print(f"\n 종합 비교 차트 생성: {summary_chart}")

            # 최종 결과 요약
            self.print_final_summary(results)

            # 결과 저장
            self.save_results(results)

        except Exception as e:
            print(f" 테스트 실행 중 오류 발생: {e}")

        print(f"\n 테스트 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def save_results(self, results: List[Dict]):
        """테스트 결과 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"pbar_tratio_test_results_{timestamp}.json"

            # JSON 직렬화를 위해 차트 파일명만 저장
            save_results = []
            for result in results:
                save_result = result.copy()
                if 'analysis' in save_result and 'all_levels' in save_result['analysis']:
                    # 큰 데이터는 제거하고 요약만 저장
                    del save_result['analysis']['all_levels']
                save_results.append(save_result)

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_results, f, ensure_ascii=False, indent=2)

            print(f"\n 테스트 결과 저장: {filename}")

        except Exception as e:
            print(f" 결과 저장 실패: {e}")

def main():
    """메인 함수"""
    visualizer = PbarTratioVisualizer()

    try:
        visualizer.run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 테스트가 중단되었습니다.")
    except Exception as e:
        print(f" 예상치 못한 오류: {e}")

if __name__ == "__main__":
    main()
