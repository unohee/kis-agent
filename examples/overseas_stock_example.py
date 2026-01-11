#!/usr/bin/env python3
"""
PyKIS 해외주식 거래 예제

해외주식 시세 조회, 주문, 잔고 조회 등 주요 기능을 시연합니다.
지원 거래소: 미국(NYSE, NASDAQ, AMEX), 일본, 중국, 홍콩, 베트남
"""

import os
import sys

# 상위 디렉토리의 Python 모듈 임포트
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import Agent


def create_agent():
    """환경변수에서 Agent 생성"""
    app_key = os.environ.get("KIS_APP_KEY")
    app_secret = os.environ.get("KIS_APP_SECRET")
    account_no = os.environ.get("KIS_ACCOUNT_NO")
    account_code = os.environ.get("KIS_ACCOUNT_CODE", "01")

    if not all([app_key, app_secret, account_no]):
        print("환경변수를 설정해주세요:")
        print("  export KIS_APP_KEY='your_app_key'")
        print("  export KIS_APP_SECRET='your_app_secret'")
        print("  export KIS_ACCOUNT_NO='your_account_no'")
        return None

    return Agent(
        app_key=app_key,
        app_secret=app_secret,
        account_no=account_no,
        account_code=account_code,
    )


def example_price_inquiry(agent):
    """시세 조회 예제"""
    print("\n" + "=" * 60)
    print("1. 해외주식 시세 조회")
    print("=" * 60)

    # 미국 주식 현재가 조회 (NASDAQ - Apple)
    print("\n[AAPL - Apple Inc.] 현재가 조회 (NASDAQ)")
    apple = agent.overseas.get_price(excd="NAS", symb="AAPL")
    if apple and apple.get("rt_cd") == "0":
        output = apple["output"]
        print(f"  현재가: ${output.get('last', 'N/A')}")
        print(
            f"  전일대비: ${output.get('diff', 'N/A')} ({output.get('rate', 'N/A')}%)"
        )
        print(f"  거래량: {output.get('tvol', 'N/A')}")

    # 미국 주식 상세 시세
    print("\n[TSLA - Tesla] 상세 시세 조회 (NASDAQ)")
    tesla = agent.overseas.get_price_detail(excd="NAS", symb="TSLA")
    if tesla and tesla.get("rt_cd") == "0":
        output = tesla["output"]
        print(f"  시가: ${output.get('open', 'N/A')}")
        print(f"  고가: ${output.get('high', 'N/A')}")
        print(f"  저가: ${output.get('low', 'N/A')}")
        print(f"  현재가: ${output.get('last', 'N/A')}")

    # 호가 조회
    print("\n[MSFT - Microsoft] 호가 조회 (NYSE)")
    orderbook = agent.overseas.get_orderbook(excd="NYS", symb="MSFT")
    if orderbook and orderbook.get("rt_cd") == "0":
        output = orderbook["output"]
        print(
            f"  매도1호가: ${output.get('askp1', 'N/A')} ({output.get('askp_rsqn1', 'N/A')})"
        )
        print(
            f"  매수1호가: ${output.get('bidp1', 'N/A')} ({output.get('bidp_rsqn1', 'N/A')})"
        )


def example_chart_data(agent):
    """차트 데이터 조회 예제"""
    print("\n" + "=" * 60)
    print("2. 차트 데이터 조회")
    print("=" * 60)

    # 일봉 조회
    print("\n[NVDA - NVIDIA] 일봉 차트 (최근 30일)")
    daily = agent.overseas.get_daily_price(
        excd="NAS",
        symb="NVDA",
        start="20240101",  # 시작일
        period="D",  # D:일봉, W:주봉, M:월봉
    )
    if daily and daily.get("rt_cd") == "0":
        candles = daily.get("output2", [])[:5]  # 최근 5일
        print(f"  총 {len(daily.get('output2', []))}개 봉 수신")
        for candle in candles:
            print(
                f"  {candle.get('xymd')}: "
                f"종가 ${candle.get('clos')}, "
                f"거래량 {candle.get('tvol')}"
            )

    # 분봉 조회
    print("\n[GOOGL - Google] 5분봉 차트")
    minute = agent.overseas.get_minute_price(
        excd="NAS", symb="GOOGL", interval=5  # 1, 5, 10, 15, 30, 60분
    )
    if minute and minute.get("rt_cd") == "0":
        candles = minute.get("output2", [])[:3]
        print(f"  총 {len(minute.get('output2', []))}개 봉 수신")
        for candle in candles:
            print(
                f"  {candle.get('xymd')} {candle.get('xhms')}: "
                f"종가 ${candle.get('clos')}"
            )


def example_account_inquiry(agent):
    """계좌 조회 예제"""
    print("\n" + "=" * 60)
    print("3. 해외주식 계좌 조회")
    print("=" * 60)

    # 전체 잔고 조회
    print("\n[전체 잔고 조회]")
    balance = agent.overseas.get_balance()
    if balance and balance.get("rt_cd") == "0":
        holdings = balance.get("output1", [])
        print(f"  보유 종목 수: {len(holdings)}개")
        for holding in holdings[:3]:  # 최대 3개만 출력
            print(
                f"  - {holding.get('ovrs_item_name')}: "
                f"{holding.get('ovrs_cblc_qty')}주, "
                f"평가액 ${holding.get('ovrs_stck_evlu_amt')}"
            )

    # 특정 거래소 잔고 조회
    print("\n[미국 주식 잔고만 조회 (NASDAQ)]")
    us_balance = agent.overseas.get_balance(excd="NAS")
    if us_balance and us_balance.get("rt_cd") == "0":
        print(f"  NASDAQ 보유 종목: {len(us_balance.get('output1', []))}개")

    # 주문 가능 금액 조회
    print("\n[AAPL 매수 가능 금액 조회]")
    buyable = agent.overseas.get_buyable_amount(excd="NAS", symb="AAPL", price="150.00")
    if buyable and buyable.get("rt_cd") == "0":
        output = buyable["output"]
        print(f"  매수 가능 금액: ${output.get('max_ord_amt', 'N/A')}")
        print(f"  매수 가능 수량: {output.get('max_ord_qty', 'N/A')}주")


def example_order_execution(agent):
    """주문 실행 예제 (실제 주문 안 함 - 주석 처리)"""
    print("\n" + "=" * 60)
    print("4. 주문 실행 예제 (코드만 표시 - 실행 안 함)")
    print("=" * 60)

    print(
        """
# 매수 주문 (지정가)
result = agent.overseas.buy_order(
    excd="NAS",      # NASDAQ
    symb="AAPL",     # Apple
    qty="10",        # 10주
    price="150.00"   # $150
)

# 매수 주문 (시장가)
result = agent.overseas.buy_order(
    excd="NAS",
    symb="TSLA",
    qty="5",
    price="0",       # 시장가는 0
    order_type="34"  # 34: 시장가
)

# 매도 주문
result = agent.overseas.sell_order(
    excd="NYS",
    symb="MSFT",
    qty="20",
    price="350.00"
)

# 주문 정정
modify = agent.overseas.modify_order(
    excd="NAS",
    order_no="original_order_number",
    qty="15",
    price="155.00"
)

# 주문 취소
cancel = agent.overseas.cancel_order(
    excd="NAS",
    order_no="order_to_cancel"
)
"""
    )


def example_market_ranking(agent):
    """시장 순위 조회 예제"""
    print("\n" + "=" * 60)
    print("5. 시장 순위 조회")
    print("=" * 60)

    # 거래량 상위
    print("\n[NASDAQ 거래량 상위 종목]")
    volume_ranking = agent.overseas.get_volume_ranking(excd="NAS")
    if volume_ranking and volume_ranking.get("rt_cd") == "0":
        stocks = volume_ranking.get("output", [])[:5]
        for idx, stock in enumerate(stocks, 1):
            print(
                f"  {idx}. {stock.get('symb')}: "
                f"거래량 {stock.get('tvol')}, "
                f"${stock.get('last')}"
            )

    # 등락률 상위
    print("\n[NYSE 상승률 상위 종목]")
    price_ranking = agent.overseas.get_price_change_ranking(
        excd="NYS", sort_type="상승"  # "상승" 또는 "하락"
    )
    if price_ranking and price_ranking.get("rt_cd") == "0":
        stocks = price_ranking.get("output", [])[:5]
        for idx, stock in enumerate(stocks, 1):
            print(
                f"  {idx}. {stock.get('symb')}: "
                f"{stock.get('rate')}%, "
                f"${stock.get('last')}"
            )


def example_utilities(agent):
    """유틸리티 기능 예제"""
    print("\n" + "=" * 60)
    print("6. 유틸리티 기능")
    print("=" * 60)

    # 지원 거래소 목록
    print("\n[지원 거래소 목록]")
    exchanges = agent.overseas.get_supported_exchanges()
    print(f"  {len(exchanges)}개 거래소: {', '.join(exchanges)}")

    # 거래소 정보
    print("\n[거래소 상세 정보]")
    for excd in ["NAS", "NYS", "HKS", "TSE"]:
        info = agent.overseas.get_exchange_info(excd)
        if info:
            print(f"  {excd}: {info['name']} ({info['country']}, {info['currency']})")

    # 종목 검색
    print("\n[종목 검색 - 'APP' 검색]")
    search = agent.overseas.search_symbol(excd="NAS", keyword="APP")
    if search and search.get("rt_cd") == "0":
        results = search.get("output", [])[:3]
        for stock in results:
            print(f"  {stock.get('symb')}: {stock.get('name')}")


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("PyKIS 해외주식 거래 예제")
    print("=" * 60)

    # Agent 생성
    agent = create_agent()
    if not agent:
        return

    print("\n✅ Agent 생성 완료 (실전투자)")

    # 각 예제 실행
    try:
        example_price_inquiry(agent)
        example_chart_data(agent)
        example_account_inquiry(agent)
        example_order_execution(agent)  # 주문은 실행 안 함
        example_market_ranking(agent)
        example_utilities(agent)

        print("\n" + "=" * 60)
        print("예제 실행 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
