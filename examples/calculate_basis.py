# Created: 2026-07-17
# Purpose: Compute the KOSPI 200 futures basis (선물가 - 현물지수).
# Dependencies: kis_agent, python-dotenv
# Test Status: Verified against a mocked transport; live run needs KIS credentials.

"""KOSPI 200 선물 베이시스 계산 예제.

베이시스 = 선물가격 - 현물지수. 양수면 콘탱고, 음수면 백워데이션이다.

실행:
    python examples/calculate_basis.py

`.env`에 `KIS_APP_KEY` / `KIS_APP_SECRET` / `KIS_ACCOUNT_NO`가 필요하다.
선물옵션 시세는 모의투자도 지원하므로 `KIS_PAPER=1`로도 돌릴 수 있다.
"""

import os

from dotenv import load_dotenv

from kis_agent import Agent

load_dotenv()


def main():
    agent = Agent(
        app_key=os.environ["KIS_APP_KEY"],
        app_secret=os.environ["KIS_APP_SECRET"],
        account_no=os.environ["KIS_ACCOUNT_NO"],
        account_code=os.environ.get("KIS_ACCOUNT_CODE", "01"),
    )

    # 근월물 종목코드는 만기마다 바뀐다. 마스터에서 자동 해석해 주는 편의 메서드 사용.
    futures = agent.futures.get_current_futures_price()
    if not futures or futures.get("rt_cd") != "0":
        msg = futures.get("msg1") if futures else "응답 없음"
        print(f"선물 시세 조회 실패: {msg}")
        return

    output = futures.get("output", {})
    futures_price = float(output.get("futs_prpr", 0))

    # 현물 지수 (KOSPI200)
    index = agent.inquire_index_price("0007")
    if not index or index.get("rt_cd") != "0":
        msg = index.get("msg1") if index else "응답 없음"
        print(f"KOSPI200 지수 조회 실패: {msg}")
        return

    spot = float(index.get("output", {}).get("bstp_nmix_prpr", 0))
    basis = futures_price - spot

    print(f"선물가격:      {futures_price:>10.2f}")
    print(f"KOSPI200 지수: {spot:>10.2f}")
    print(f"베이시스:      {basis:>+10.2f}  ({'콘탱고' if basis > 0 else '백워데이션'})")


if __name__ == "__main__":
    main()
