#!/usr/bin/env python3
"""
일봉 데이터 조회 예제 - 페이지네이션 지원

PyKIS의 get_daily_price_all() 메서드를 사용하여
100건 제한 없이 장기간 일봉 데이터를 조회하는 방법을 보여줍니다.
"""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

from kis_agent import Agent

# 환경변수 로드
load_dotenv()


def example_basic():
    """기본 사용법: 2020년 전체 데이터 조회"""

    # Agent 초기화
    agent = Agent(
        app_key=os.getenv("KIS_APP_KEY"),
        app_secret=os.getenv("KIS_SECRET"),
        account_no=os.getenv("KIS_ACCOUNT_NO"),
        account_code=os.getenv("KIS_ACCOUNT_CODE", "01"),
    )

    print("=" * 80)
    print("예제 1: 2020년 전체 삼성전자 일봉 데이터 조회")
    print("=" * 80)

    # 2020년 전체 데이터 조회
    result = agent.get_daily_price_all(
        code="005930",  # 삼성전자
        start_date="20200102",
        end_date="20201230",
        period="D",  # 일봉
        org_adj_prc="1",  # 수정주가 사용
    )

    # 결과 출력
    pagination_info = result["_pagination_info"]
    print(f"✅ 총 {pagination_info['total_records']}건 수집")
    print(f"✅ API 호출 횟수: {pagination_info['total_calls']}회")
    print()

    # 최근 5일 데이터 출력
    print("최근 5일 데이터:")
    for day in result["output2"][:5]:
        print(
            f"  {day['stck_bsop_date']}: "
            f"종가 {day['stck_clpr']}원, "
            f"거래량 {day['acml_vol']}"
        )
    print()


def example_long_period():
    """장기 데이터 조회: 최근 3년"""

    agent = Agent(
        app_key=os.getenv("KIS_APP_KEY"),
        app_secret=os.getenv("KIS_SECRET"),
        account_no=os.getenv("KIS_ACCOUNT_NO"),
        account_code=os.getenv("KIS_ACCOUNT_CODE", "01"),
    )

    print("=" * 80)
    print("예제 2: 최근 3년 카카오 일봉 데이터 조회")
    print("=" * 80)

    # 날짜 계산
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3 * 365)

    # 3년치 데이터 조회
    result = agent.get_daily_price_all(
        code="035720",  # 카카오
        start_date=start_date.strftime("%Y%m%d"),
        end_date=end_date.strftime("%Y%m%d"),
    )

    pagination_info = result["_pagination_info"]
    print(f"✅ 총 {pagination_info['total_records']}건 수집")
    print(f"✅ API 호출 횟수: {pagination_info['total_calls']}회")
    print()

    # 통계 계산
    prices = [int(day["stck_clpr"]) for day in result["output2"]]
    print("통계 정보:")
    print(f"  최고가: {max(prices):,}원")
    print(f"  최저가: {min(prices):,}원")
    print(f"  평균가: {sum(prices) // len(prices):,}원")
    print()


def example_multiple_stocks():
    """여러 종목 동시 조회"""

    agent = Agent(
        app_key=os.getenv("KIS_APP_KEY"),
        app_secret=os.getenv("KIS_SECRET"),
        account_no=os.getenv("KIS_ACCOUNT_NO"),
        account_code=os.getenv("KIS_ACCOUNT_CODE", "01"),
    )

    print("=" * 80)
    print("예제 3: 여러 종목 2020년 데이터 동시 조회")
    print("=" * 80)

    stocks = {
        "005930": "삼성전자",
        "000660": "SK하이닉스",
        "035420": "NAVER",
    }

    results = {}

    for code, name in stocks.items():
        print(f"{name} ({code}) 조회 중...")

        result = agent.get_daily_price_all(
            code=code, start_date="20200102", end_date="20201230"
        )

        results[code] = result
        pagination_info = result["_pagination_info"]

        print(
            f"  ✅ {pagination_info['total_records']}건 수집 "
            f"({pagination_info['total_calls']}회 호출)"
        )

    print()
    print("수집 완료! 총 3종목 데이터")
    print()

    # 각 종목의 2020년 수익률 계산
    print("2020년 수익률:")
    for code, name in stocks.items():
        data = results[code]["output2"]
        # 역순이므로 첫 번째가 최신, 마지막이 가장 오래된
        latest_price = int(data[0]["stck_clpr"])
        earliest_price = int(data[-1]["stck_clpr"])
        returns = (latest_price - earliest_price) / earliest_price * 100

        print(f"  {name}: {returns:+.2f}%")
    print()


def example_data_analysis():
    """데이터 분석 예제: 이동평균선 계산"""

    agent = Agent(
        app_key=os.getenv("KIS_APP_KEY"),
        app_secret=os.getenv("KIS_SECRET"),
        account_no=os.getenv("KIS_ACCOUNT_NO"),
        account_code=os.getenv("KIS_ACCOUNT_CODE", "01"),
    )

    print("=" * 80)
    print("예제 4: 데이터 분석 - 이동평균선")
    print("=" * 80)

    # 최근 200일 데이터 조회
    end_date = datetime.now()
    start_date = end_date - timedelta(days=300)  # 여유있게 300일

    result = agent.get_daily_price_all(
        code="005930",  # 삼성전자
        start_date=start_date.strftime("%Y%m%d"),
        end_date=end_date.strftime("%Y%m%d"),
    )

    # 종가 리스트 (역순이므로 뒤집기)
    close_prices = [int(day["stck_clpr"]) for day in reversed(result["output2"])]

    # 5일, 20일, 60일 이동평균 계산
    def calculate_ma(prices, period):
        """이동평균 계산"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period

    ma5 = calculate_ma(close_prices, 5)
    ma20 = calculate_ma(close_prices, 20)
    ma60 = calculate_ma(close_prices, 60)

    print("삼성전자 이동평균선:")
    print(f"  현재가: {close_prices[-1]:,}원")
    print(f"  MA5:   {ma5:,.0f}원" if ma5 else "  MA5:   계산 불가")
    print(f"  MA20:  {ma20:,.0f}원" if ma20 else "  MA20:  계산 불가")
    print(f"  MA60:  {ma60:,.0f}원" if ma60 else "  MA60:  계산 불가")
    print()


def example_weekly_data():
    """주봉 데이터 조회"""

    agent = Agent(
        app_key=os.getenv("KIS_APP_KEY"),
        app_secret=os.getenv("KIS_SECRET"),
        account_no=os.getenv("KIS_ACCOUNT_NO"),
        account_code=os.getenv("KIS_ACCOUNT_CODE", "01"),
    )

    print("=" * 80)
    print("예제 5: 주봉 데이터 조회 (최근 2년)")
    print("=" * 80)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=2 * 365)

    # 주봉 데이터 조회 (period="W")
    result = agent.get_daily_price_all(
        code="005930",
        start_date=start_date.strftime("%Y%m%d"),
        end_date=end_date.strftime("%Y%m%d"),
        period="W",  # 주봉
    )

    pagination_info = result["_pagination_info"]
    print(f"✅ 총 {pagination_info['total_records']}건 (주) 수집")
    print(f"✅ API 호출 횟수: {pagination_info['total_calls']}회")
    print()

    # 최근 10주 데이터 출력
    print("최근 10주 데이터:")
    for week in result["output2"][:10]:
        print(
            f"  {week['stck_bsop_date']}: "
            f"종가 {week['stck_clpr']}원, "
            f"거래량 {week['acml_vol']}"
        )
    print()


if __name__ == "__main__":
    # 환경변수 확인
    if not all([os.getenv("KIS_APP_KEY"), os.getenv("KIS_SECRET")]):
        print("❌ 환경변수 설정 필요: KIS_APP_KEY, KIS_SECRET")
        print("   .env 파일을 확인하세요.")
        exit(1)

    # 예제 실행
    try:
        example_basic()
        # example_long_period()  # 장기 데이터는 Rate Limit 고려
        # example_multiple_stocks()  # 여러 종목은 Rate Limit 고려
        # example_data_analysis()
        # example_weekly_data()

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()
