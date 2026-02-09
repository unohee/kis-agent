#!/usr/bin/env python3
"""
PyKIS

 API      .
API      .
"""

import os
import sys

#    Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykis import Agent


def create_agent_from_env():
    """API    Agent"""
    print("=" * 60)
    print("API    Agent ")
    print("=" * 60)

    #
    #     !
    app_key = os.environ.get("KIS_APP_KEY")
    app_secret = os.environ.get("KIS_APP_SECRET")
    account_no = os.environ.get("KIS_ACCOUNT_NO")
    account_code = os.environ.get("KIS_ACCOUNT_CODE", "01")

    if not all([app_key, app_secret, account_no]):
        print(" :")
        print("  export KIS_APP_KEY='your_app_key'")
        print("  export KIS_APP_SECRET='your_app_secret'")
        print("  export KIS_ACCOUNT_NO='your_account_no'")
        print("  export KIS_ACCOUNT_CODE='01'  # ,  01")
        return None

    try:
        # Agent  ()
        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code,
            # base_url   URL
        )
        print(" Agent   ()")

        #  Agent
        # agent_mock = Agent(
        #     app_key=app_key,
        #     app_secret=app_secret,
        #     account_no=account_no,
        #     account_code=account_code,
        #     base_url="https://openapivts.koreainvestment.com:29443"
        # )

        return agent

    except ValueError as e:
        print(f"   : {e}")
        return None
    except RuntimeError as e:
        print(f"   : {e}")
        return None


def demonstrate_basic_features(agent: Agent):
    """ """
    if not agent:
        return

    print("\n" + "=" * 60)
    print("  ")
    print("=" * 60)

    # 1.
    print("\n1.   ")
    try:
        balance = agent.get_account_balance()
        if balance and balance.get("rt_cd") == "0":
            print("    ")

            #
            holdings = balance.get("output1", [])
            if holdings:
                print(f"     : {len(holdings)}")
                for stock in holdings[:3]:  #  3
                    print(
                        f"   - {stock.get('prdt_name', 'N/A')}: {stock.get('hldg_qty', 0)}"
                    )

            #
            summary = balance.get("output2", [{}])[0]
            if summary:
                total_asset = summary.get("tot_evlu_amt", 0)
                print(f"    : {int(total_asset):,}")
        else:
            print("    ")
    except Exception as e:
        print(f"  : {e}")

    # 2.
    print("\n2.    ()")
    try:
        price_info = agent.get_stock_price("005930")
        if price_info and price_info.get("rt_cd") == "0":
            output = price_info.get("output", {})
            current_price = output.get("stck_prpr", "N/A")
            change_rate = output.get("prdy_ctrt", "N/A")
            print(f" : {current_price}")
            print(f"   : {change_rate}%")
        else:
            print("    ")
    except Exception as e:
        print(f"  : {e}")

    # 3.
    print("\n3.    ()")
    try:
        daily_price = agent.get_daily_price("035720", period="D")
        if daily_price and daily_price.get("rt_cd") == "0":
            output = daily_price.get("output2", [])
            if output:
                recent = output[0]  #
                print(f" : {recent.get('stck_bsop_date', 'N/A')}")
                print(f"   : {recent.get('stck_clpr', 'N/A')}")
                print(f"   : {int(recent.get('acml_vol', 0)):,}")
        else:
            print("    ")
    except Exception as e:
        print(f"  : {e}")

    # 4. Rate Limiter
    print("\n4. Rate Limiter ")
    try:
        status = agent.get_rate_limiter_status()
        if status:
            print(" Rate Limiter ")
            print(f"    : {status.get('requests_per_second', 0)}/")
            print(f"     : {status.get('total_requests', 0)}")
        else:
            print("ℹ Rate Limiter  ")
    except Exception as e:
        print(f"  : {e}")


def main():
    """ """
    print("\n" + " PyKIS   " + "\n")

    # Agent
    agent = create_agent_from_env()

    #
    if agent:
        demonstrate_basic_features(agent)
    else:
        print("\n Agent  . API  .")

    print("\n" + "=" * 60)
    print(" ")
    print("=" * 60)


if __name__ == "__main__":
    main()
