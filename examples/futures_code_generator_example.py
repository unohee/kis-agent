"""
선물옵션 종목코드 자동 생성 예시

Created: 2026-01-20
Purpose: FuturesCodeGenerator 사용법 시연

자동 종목코드 생성을 통해 API 호출을 간소화합니다.
"""

from pykis.futures import (
    FuturesCodeGenerator,
    generate_call_option,
    generate_current_futures,
    generate_next_futures,
    generate_put_option,
)


def example_1_basic_futures_code():
    """기본 선물 종목코드 생성"""
    print("=" * 60)
    print("예시 1: 기본 선물 종목코드 생성")
    print("=" * 60)

    # 현재 월물 자동 생성 (2026년 1월 → 3월물)
    current_code = generate_current_futures()
    print(f"현재 월물: {current_code}")  # '101S03'

    # 차근월물 생성
    next_code = generate_next_futures()
    print(f"차근월물: {next_code}")  # '101M06'

    # 특정 월물 생성
    june_code = FuturesCodeGenerator.generate_futures_code(expiry_month=6)
    print(f"6월물: {june_code}")  # '101M06'

    # 시리즈로 생성
    series_code = FuturesCodeGenerator.generate_futures_code(series="Z")
    print(f"Z 시리즈 (12월물): {series_code}")  # '101Z12'
    print()


def example_2_option_code():
    """옵션 종목코드 생성"""
    print("=" * 60)
    print("예시 2: 옵션 종목코드 생성")
    print("=" * 60)

    # 현재 월물 콜옵션 340.0
    call_code = generate_call_option(340.0)
    print(f"콜옵션 340.0: {call_code}")  # '201SC340'

    # 현재 월물 풋옵션 340.0
    put_code = generate_put_option(340.0)
    print(f"풋옵션 340.0: {put_code}")  # '301SP340'

    # 6월물 콜옵션 342.5
    june_call = FuturesCodeGenerator.generate_option_code("CALL", 342.5, expiry_month=6)
    print(f"6월물 콜옵션 342.5: {june_call}")  # '201MC342' (소수점 절사)

    # 소수점 행사가는 자동으로 정수로 변환됨
    decimal_strike = FuturesCodeGenerator.generate_option_code(
        "PUT", 337.5, expiry_month=3
    )
    print(f"풋옵션 337.5: {decimal_strike}")  # '301SP337'
    print()


def example_3_atm_options():
    """ATM 옵션 코드 일괄 생성"""
    print("=" * 60)
    print("예시 3: ATM 옵션 코드 일괄 생성")
    print("=" * 60)

    # KOSPI200 현재가 340.25 기준
    current_price = 340.25

    atm_codes = FuturesCodeGenerator.generate_atm_option_codes(
        current_price, expiry_month=3, range_count=3
    )

    print(f"현재가: {current_price}")
    print(f"ATM 행사가: {atm_codes['atm_strike']}")  # 340.0 (2.5 단위 반올림)
    print()

    print("콜옵션 종목코드:")
    for code in atm_codes["call"]:
        parsed = FuturesCodeGenerator.parse_option_code(code)
        print(f"  {code} - 행사가 {parsed['strike_price']}")

    print()
    print("풋옵션 종목코드:")
    for code in atm_codes["put"]:
        parsed = FuturesCodeGenerator.parse_option_code(code)
        print(f"  {code} - 행사가 {parsed['strike_price']}")
    print()


def example_4_parse_code():
    """종목코드 파싱"""
    print("=" * 60)
    print("예시 4: 종목코드 파싱")
    print("=" * 60)

    # 선물 코드 파싱
    futures_info = FuturesCodeGenerator.parse_futures_code("101S03")
    print("선물 코드 '101S03' 파싱:")
    print(f"  상품: {futures_info['product']}")
    print(f"  시리즈: {futures_info['series']}")
    print(f"  만기월: {futures_info['expiry_month']}월")
    print()

    # 옵션 코드 파싱
    option_info = FuturesCodeGenerator.parse_option_code("201SC340")
    print("옵션 코드 '201SC340' 파싱:")
    print(f"  상품: {option_info['product']}")
    print(f"  옵션 타입: {option_info['option_type']}")
    print(f"  시리즈: {option_info['series']}")
    print(f"  행사가: {option_info['strike_price']}")
    print()


def example_5_with_agent():
    """Agent와 함께 사용 (실제 API 호출 시뮬레이션)"""
    print("=" * 60)
    print("예시 5: Agent와 함께 사용")
    print("=" * 60)

    print("# 실제 사용 예시 (Agent 초기화 필요):")
    print(
        """
from pykis import Agent

agent = Agent(
    app_key="...",
    app_secret="...",
    account_no="12345678",
    account_code="03"  # 선물옵션 계좌
)

# 방법 1: 종목코드 직접 입력
price = agent.futures.get_price("101S03")

# 방법 2: 현재 월물 자동 조회 (종목코드 생성 불필요!)
price = agent.futures.get_current_futures_price()
print(price['output']['fuop_prpr'])

# 방법 3: 옵션 자동 조회
call_price = agent.futures.get_call_option_price(340.0)
put_price = agent.futures.get_put_option_price(340.0, expiry_month=6)

# 방법 4: 현재 월물 차트 조회
chart = agent.futures.get_current_futures_chart("20260101", "20260131")

# 방법 5: 종목코드 생성기 직접 사용
code = agent.futures.code.generate_futures_code(expiry_month=6)
price = agent.futures.get_price(code)

# 방법 6: ATM 옵션 일괄 조회
atm_codes = agent.futures.code.generate_atm_option_codes(340.25)
for call_code in atm_codes['call']:
    price = agent.futures.get_price(call_code)
    print(f"{call_code}: {price['output']['fuop_prpr']}")
    """
    )


def example_6_trading():
    """자동 주문 예시"""
    print("=" * 60)
    print("예시 6: 자동 주문")
    print("=" * 60)

    print("# 실제 주문 예시 (Agent 초기화 필요):")
    print(
        """
# 현재 월물 선물 시장가 매수
result = agent.futures.order_current_futures(
    order_type="02",  # 매수
    qty="1",
    price="0"  # 시장가
)

# 콜옵션 340.0 시장가 매수
result = agent.futures.order_option(
    option_type="CALL",
    strike_price=340.0,
    order_type="02",  # 매수
    qty="1",
    price="0"  # 시장가
)

# 풋옵션 342.5 지정가 매도
result = agent.futures.order_option(
    option_type="PUT",
    strike_price=342.5,
    order_type="01",  # 매도
    qty="1",
    price="5.50"  # 지정가
)

print(f"주문번호: {result['output']['odno']}")
    """
    )


def main():
    """모든 예시 실행"""
    example_1_basic_futures_code()
    example_2_option_code()
    example_3_atm_options()
    example_4_parse_code()
    example_5_with_agent()
    example_6_trading()

    print("=" * 60)
    print("🎉 종목코드 자동 생성 기능 사용 완료!")
    print("=" * 60)
    print()
    print("주요 기능:")
    print("  ✅ 현재/차근월물 선물 코드 자동 생성")
    print("  ✅ 콜/풋 옵션 코드 자동 생성")
    print("  ✅ ATM 기준 옵션 일괄 생성")
    print("  ✅ 종목코드 파싱 및 분석")
    print("  ✅ Agent 편의 메서드 (자동 조회/주문)")
    print()
    print("장점:")
    print("  🚀 종목코드 수동 입력 불필요")
    print("  🚀 월물 변경 시 자동 대응")
    print("  🚀 ATM 옵션 찾기 간편")
    print("  🚀 코드 가독성 향상")


if __name__ == "__main__":
    main()
