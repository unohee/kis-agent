#!/usr/bin/env python3

"""
매물대 조회(get_pbar_tratio) 간단 데모

이 스크립트는 PyKIS의 매물대 조회 기능을 간단하게 체험할 수 있는 데모입니다.
복잡한 테스트 없이 핵심 기능만 확인할 수 있습니다.

주요 기능:
1. 매물대 조회
2. 현재가와 매물대 비교
3. 지지/저항 신호 판단
4. 간단한 분석 결과 출력

실행 방법:
    python examples/pbar_tratio_demo.py
"""

import os
import sys
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import Agent


def analyze_stock_volume_profile(code: str):
    """종목의 매물대 분석"""
    print(f"\n{'='*60}")
    print(f" {code} 매물대 분석")
    print(f"{'='*60}")

    # Agent 초기화
    agent = Agent()

    try:
        # 1. 매물대 조회
        print(" 매물대 데이터 조회 중...")
        pbar_result = agent.get_pbar_tratio(code)

        if not pbar_result or pbar_result.get('rt_cd') != '0':
            print(f" 매물대 조회 실패: {pbar_result.get('msg1', '알 수 없는 오류') if pbar_result else '결과 없음'}")
            return

        print(" 매물대 데이터 조회 성공")

        # 2. 현재가 정보 (pbar_tratio API의 output1에서 가져오기)
        print(" 현재가 정보 확인 중...")

        if 'output1' in pbar_result:
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
            print(" 현재가 조회 중...")
            price_result = agent.get_stock_price(code)

            if not price_result or price_result.get('rt_cd') != '0':
                print(f" 현재가 조회 실패: {price_result.get('msg1', '알 수 없는 오류') if price_result else '결과 없음'}")
                return

            current_price = int(price_result['output']['stck_prpr'])
            print(f" 현재가: {current_price:,}원")

        # 3. 매물대 데이터 분석
        volume_profile = pbar_result.get('output2', [])
        if not volume_profile:
            print(" 매물대 데이터가 비어있습니다.")
            return

        print(f" 매물대 레벨: {len(volume_profile)}개")

        # 실제 API 응답 구조에 맞는 키 사용
        first_item = volume_profile[0]
        volume_key = 'cntg_vol'      # 거래량 데이터

        if volume_key not in first_item:
            print(f" 거래량 데이터 키 '{volume_key}'를 찾을 수 없습니다.")
            print(f" 사용 가능한 키: {list(first_item.keys())}")
            return

        # 4. 매물대 분석
        print("\n 매물대 분석 결과:")

        # 거래량 데이터 처리
        processed_levels = []
        for item in volume_profile:
            volume = float(item.get(volume_key, '0'))
            price = int(item.get('stck_prpr', '0'))
            processed_levels.append({
                'price': price,
                'volume': volume
            })

        # 거래량 순 정렬
        processed_levels.sort(key=lambda x: x['volume'], reverse=True)

        # 최대 매물대
        max_level = processed_levels[0]
        max_volume_price = max_level['price']
        max_volume = max_level['volume']

        print(f" 최대 거래량 매물대: {max_volume_price:,}원 (거래량: {max_volume:.2f})")

        # 상위 5개 매물대
        print("\n 상위 5개 매물대:")
        for i, level in enumerate(processed_levels[:5], 1):
            print(f"   {i}. {level['price']:,}원 - 거래량: {level['volume']:.2f}")

        # 5. 현재가와 비교 분석
        print("\n 현재가 vs 매물대 비교:")
        gap = current_price - max_volume_price
        gap_percentage = (gap / max_volume_price) * 100 if max_volume_price > 0 else 0

        print(f"   현재가: {current_price:,}원")
        print(f"   최대 매물대: {max_volume_price:,}원")
        print(f"   가격 이격: {gap:,}원 ({gap_percentage:+.2f}%)")

        # 6. 투자 신호 판단
        print("\n 투자 신호:")
        if gap > 0:
            print("    현재가가 최대 매물대 위에 있음")
            print("    해석: 매물대가 지지선으로 작용할 가능성")
            signal = "지지 (SUPPORT)"
        elif gap < 0:
            print("    현재가가 최대 매물대 아래에 있음")
            print("    해석: 매물대가 저항선으로 작용할 가능성")
            signal = "저항 (RESISTANCE)"
        else:
            print("   ➡️ 현재가가 최대 매물대와 일치")
            print("    해석: 중요한 가격대, 돌파 방향 주목")
            signal = "균형 (NEUTRAL)"

        # 가장 가까운 매물대 찾기
        closest_level = min(processed_levels[:10],
                          key=lambda x: abs(current_price - x['price']))

        print("\n 가장 가까운 주요 매물대:")
        print(f"   가격: {closest_level['price']:,}원")
        print(f"   거래량: {closest_level['volume']:.2f}")
        print(f"   현재가와 차이: {current_price - closest_level['price']:,}원")

        # 7. 요약
        print(f"\n{'='*60}")
        print(" 분석 요약")
        print(f"{'='*60}")
        print(f"  종목: {code}")
        print(f" 현재가: {current_price:,}원")
        print(f" 최대 매물대: {max_volume_price:,}원")
        print(f" 이격률: {gap_percentage:+.2f}%")
        print(f" 신호: {signal}")
        print(f" 분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return {
            'code': code,
            'current_price': current_price,
            'max_volume_price': max_volume_price,
            'gap_percentage': gap_percentage,
            'signal': signal,
            'success': True
        }

    except Exception as e:
        print(f" 분석 중 오류 발생: {e}")
        return {'code': code, 'success': False, 'error': str(e)}

def main():
    """메인 함수"""
    print(" PyKIS 매물대 조회 데모")
    print("=" * 60)

    # 기본 테스트 종목들
    default_stocks = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER

    print("\n 사용 방법:")
    print("1. 엔터: 기본 종목들(삼성전자, SK하이닉스, NAVER) 분석")
    print("2. 종목코드 입력: 특정 종목 분석 (예: 005930)")
    print("3. 'quit' 또는 'q': 종료")

    while True:
        try:
            print("\n" + "="*60)
            user_input = input(" 종목코드를 입력하세요 (엔터=기본종목, q=종료): ").strip()

            if user_input.lower() in ['quit', 'q', 'exit']:
                print(" 프로그램을 종료합니다.")
                break
            elif user_input == "":
                # 기본 종목들 분석
                print(f"\n 기본 종목들 분석 시작 ({', '.join(default_stocks)})")
                results = []
                for stock in default_stocks:
                    result = analyze_stock_volume_profile(stock)
                    if result:
                        results.append(result)

                # 간단한 비교 요약
                if len(results) > 1:
                    print(f"\n{'='*60}")
                    print(" 종목 비교 요약")
                    print(f"{'='*60}")

                    successful_results = [r for r in results if r.get('success')]
                    for result in successful_results:
                        print(f"   {result['code']}: {result['current_price']:,}원 "
                              f"({result['gap_percentage']:+.1f}%, {result['signal']})")

            elif len(user_input) == 6 and user_input.isdigit():
                # 특정 종목 분석
                analyze_stock_volume_profile(user_input)

            else:
                print(" 올바른 6자리 종목코드를 입력해주세요.")

        except KeyboardInterrupt:
            print("\n 프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f" 오류 발생: {e}")

if __name__ == "__main__":
    main()
