# Created: 2026-07-16
# Purpose: Demonstrate paper trading (모의투자) — account balance, buyable cash,
#          and the error raised when an API has no paper-trading counterpart.
# Dependencies: kis_agent, python-dotenv
# Test Status: Requires live paper-trading credentials (KIS_PAPER=1 in .env)

"""모의투자 사용 예제.

모의투자는 실전과 **별도의** APP KEY / APP SECRET / 계좌번호가 필요하다.
한국투자증권 API 포털에서 모의투자용으로 따로 발급받아 `.env`에 넣어야 한다.

    KIS_PAPER=1
    KIS_APP_KEY=모의투자_앱키
    KIS_APP_SECRET=모의투자_시크릿
    KIS_ACCOUNT_NO=모의투자_계좌번호

실행:
    python examples/paper_trading.py
"""

import os

from dotenv import load_dotenv

from kis_agent import Agent
from kis_agent.core.tr_mapping import PaperTradingNotSupportedError

load_dotenv()


def main():
    # paper=True 하나로 모의투자 URL과 모의투자 TR_ID가 모두 적용된다.
    # .env에 KIS_PAPER=1 을 넣었다면 paper 인자는 생략해도 된다.
    agent = Agent(
        app_key=os.environ["KIS_APP_KEY"],
        app_secret=os.environ["KIS_APP_SECRET"],
        account_no=os.environ["KIS_ACCOUNT_NO"],
        account_code=os.environ.get("KIS_ACCOUNT_CODE", "01"),
        paper=True,
    )
    print(f"모의투자 모드: {not agent.is_real}\n")

    print("=== 1. 모의투자 계좌 잔고 ===")
    balance = agent.get_account_balance()
    holdings = balance.get("output1", []) or []
    summary = (balance.get("output2") or [{}])[0]
    print(f"총평가금액: {summary.get('tot_evlu_amt', 'N/A')} 원")
    print(f"예수금:     {summary.get('dnca_tot_amt', 'N/A')} 원")
    print(f"보유 종목:  {len(holdings)}개")
    for item in holdings[:5]:
        print(f"  - {item.get('prdt_name')} {item.get('hldg_qty')}주")

    print("\n=== 2. 매수가능 조회 (삼성전자 70,000원 기준) ===")
    psbl = agent.inquire_psbl_order(price=70000, pdno="005930")
    if psbl:
        print(f"주문가능현금: {psbl.get('ord_psbl_cash', 'N/A')} 원")
        print(f"최대매수수량: {psbl.get('max_buy_qty', 'N/A')} 주")

    print("\n=== 3. 모의투자 미지원 API를 호출하면? ===")
    # KIS는 전체 336개 API 중 43개만 모의투자로 제공한다.
    # 미지원 API는 네트워크 왕복 없이 즉시 예외로 실패한다.
    try:
        agent.client.make_request(
            endpoint="/uapi/overseas-futureoption/v1/trading/inquire-ccnl",
            tr_id="OTFM3116R",  # 해외선물옵션 — 모의투자 전량 미지원
            params={},
        )
    except PaperTradingNotSupportedError as e:
        print(f"예상된 예외: {e}")


if __name__ == "__main__":
    main()
