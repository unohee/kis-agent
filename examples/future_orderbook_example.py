#!/usr/bin/env python3
"""
선물옵션 호가창 조회 예제

이 예제는 Pykis를 사용하여 선물옵션 호가창을 조회하고 분석하는 방법을 보여줍니다.
현물/선물 포지션 분석을 위한 호가 분포와 미결제약정 정보를 확인할 수 있습니다.
"""

import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kis_agent import Agent


def print_orderbook_analysis(orderbook_data, title="호가창 분석"):
    """호가창 데이터를 분석하여 출력"""
    print(f"\n{title}")
    print("=" * 70)

    if not orderbook_data or orderbook_data.get("rt_cd") != "0":
        print(
            f"조회 실패: {orderbook_data.get('msg1', '알 수 없는 오류') if orderbook_data else '응답 없음'}"
        )
        return

    output1 = orderbook_data.get("output1", {})
    output2 = orderbook_data.get("output2", {})

    # 기본 정보 출력
    print("\n[기본 정보]")
    print(f"종목명: {output1.get('fuop_name', 'N/A')}")
    print(f"현재가: {output1.get('futs_prpr', 'N/A')}")
    print(
        f"전일대비: {output1.get('prdy_vrss', 'N/A')} ({output1.get('prdy_ctrt', 'N/A')}%)"
    )
    print(f"미결제약정: {output1.get('optn_opni_qty', 'N/A')} 계약")
    print(f"미결제약정 전일대비: {output1.get('optn_opni_prdy_dfrn', 'N/A')}")

    # 호가창 10단계 출력
    print("\n[호가창 - 10단계]")
    print(
        f"{'단계':<4} {'매도잔량':>12} {'매도호가':>12} | {'매수호가':>12} {'매수잔량':>12}"
    )
    print("-" * 70)

    total_ask_volume = 0
    total_bid_volume = 0

    for i in range(1, 11):
        ask_price = output2.get(f"askp{i}", "-")
        bid_price = output2.get(f"bidp{i}", "-")
        ask_volume = output2.get(f"askp_rsqn{i}", "0")
        bid_volume = output2.get(f"bidp_rsqn{i}", "0")

        # 누적 잔량 계산
        try:
            total_ask_volume += int(ask_volume) if ask_volume != "-" else 0
            total_bid_volume += int(bid_volume) if bid_volume != "-" else 0
        except ValueError:
            pass

        print(
            f"{i:>2}단  {ask_volume:>12} {ask_price:>12} | {bid_price:>12} {bid_volume:>12}"
        )

    print("-" * 70)
    print(f"합계  {total_ask_volume:>12} {'':>12} | {'':>12} {total_bid_volume:>12}")

    # 호가 불균형 분석
    print("\n[호가 불균형 분석]")
    if total_ask_volume > 0 and total_bid_volume > 0:
        imbalance_ratio = (total_bid_volume / total_ask_volume) * 100
        print(f"총 매수잔량: {total_bid_volume:,} 계약")
        print(f"총 매도잔량: {total_ask_volume:,} 계약")
        print(f"매수/매도 비율: {imbalance_ratio:.2f}%")

        if imbalance_ratio > 120:
            print("→ 매수세가 강함 (상승 압력)")
        elif imbalance_ratio < 80:
            print("→ 매도세가 강함 (하락 압력)")
        else:
            print("→ 균형 상태")
    else:
        print("호가 데이터 부족")


def main():
    """선물옵션 호가창 조회 예제"""

    # Agent 초기화 (환경변수에서 자동으로 API 키 로드)
    agent = Agent()

    print("선물옵션 호가창 조회 및 분석")
    print("=" * 70)

    # 1. KOSPI200 지수선물 호가창 조회 (기본값)
    print("\n1. KOSPI200 지수선물 호가창 조회")
    print("-" * 70)

    # 실제 거래되는 종목코드 (2025년 9월물)
    futures_code = "101W09"
    print(f"조회 종목: {futures_code} (KOSPI200 2025년 9월물)")

    orderbook = agent.get_future_orderbook(futures_code)
    print_orderbook_analysis(orderbook, "KOSPI200 선물 호가창")

    # 2. KOSPI200 옵션 호가창 조회
    print("\n2. KOSPI200 콜옵션 호가창 조회")
    print("-" * 70)

    option_code = "201W09370"  # 2025년 9월물 콜옵션 행사가 370
    print(f"조회 종목: {option_code} (KOSPI200 C 202509 370)")

    option_orderbook = agent.get_future_orderbook(
        code=option_code, market_div_code="O"  # 옵션
    )
    print_orderbook_analysis(option_orderbook, "KOSPI200 옵션 호가창")

    # 3. 주식선물 호가창 조회
    print("\n3. 주식선물 호가창 조회")
    print("-" * 70)

    stock_futures_code = "005930F09"  # 삼성전자 2025년 9월물
    print(f"조회 종목: {stock_futures_code} (삼성전자 F 202509)")

    stock_futures_orderbook = agent.get_future_orderbook(
        code=stock_futures_code, market_div_code="JF"  # 주식선물
    )
    print_orderbook_analysis(stock_futures_orderbook, "주식선물 호가창")

    # 4. 시장분류코드 정보
    print("\n4. 시장분류코드 정보")
    print("-" * 70)
    market_codes = {
        "F": "지수선물 (KOSPI200 선물)",
        "O": "지수옵션 (KOSPI200 옵션)",
        "JF": "주식선물 (개별종목 선물)",
        "JO": "주식옵션 (개별종목 옵션)",
    }

    print("사용 가능한 시장분류코드:")
    for code, name in market_codes.items():
        print(f"  {code}: {name}")

    # 5. 종목코드 형식 안내
    print("\n5. 종목코드 형식 안내")
    print("-" * 70)
    print("지수선물 종목코드: 6자리")
    print("  - 형식: 101[월코드][연도]")
    print("  - 예시: 101W09 (2025년 9월물), 101Z12 (2025년 12월물)")
    print("  - 월코드: F(1월), G(2월), H(3월), J(4월), K(5월), M(6월)")
    print("           N(7월), Q(8월), U(9월), V(10월), X(11월), Z(12월)")

    print("\n옵션 종목코드: 9자리")
    print("  - 형식: 2[01/02][월코드][연도][행사가]")
    print("  - 예시: 201W09370 (콜옵션 2025년 9월물 행사가 370)")
    print("         202W09370 (풋옵션 2025년 9월물 행사가 370)")

    print("\n주식선물 종목코드: 종목코드 + F + 월코드 + 연도")
    print("  - 예시: 005930F09 (삼성전자 2025년 9월물)")

    # 6. 현물/선물 포지션 분석 활용 예시
    print("\n6. 현물/선물 포지션 분석 활용 예시")
    print("-" * 70)
    print("이 예제는 다음과 같은 분석에 활용할 수 있습니다:")
    print("")
    print("1. 호가 불균형을 통한 단기 방향성 예측")
    print("   - 매수잔량 > 매도잔량: 상승 압력")
    print("   - 매수잔량 < 매도잔량: 하락 압력")
    print("")
    print("2. 미결제약정 변화를 통한 포지션 분석")
    print("   - 미결제약정 증가 + 가격 상승: 롱 포지션 증가")
    print("   - 미결제약정 증가 + 가격 하락: 숏 포지션 증가")
    print("   - 미결제약정 감소: 포지션 청산 (이익 실현 또는 손절)")
    print("")
    print("3. 선물 베이시스와 호가창을 결합한 차익거래 분석")
    print("   - 베이시스 확대 + 선물 매수잔량 증가: 롱 포지션 선호")
    print("   - 베이시스 축소 + 선물 매도잔량 증가: 숏 포지션 선호")
    print("")
    print("※ 주의: 이 예제는 교육 목적으로만 사용하세요.")
    print("   실제 투자 결정은 다양한 요인을 종합적으로 고려해야 합니다.")


if __name__ == "__main__":
    main()
