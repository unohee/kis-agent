#!/usr/bin/env python3
"""
   
"""

import os
from dotenv import load_dotenv
from pykis import Agent

# .env  
load_dotenv()

def check_orders():
    """   """
    
    #  API  
    app_key = os.getenv('APP_KEY')
    app_secret = os.getenv('APP_SECRET') 
    account_no = os.getenv('CANO')
    account_code = os.getenv('ACNT_PRDT_CD', '01')
    
    if not all([app_key, app_secret, account_no]):
        print("   .")
        return
    
    try:
        # Agent  ()
        print(" Agent  ...")
        agent = Agent(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            account_code=account_code,
            base_url="https://openapi.koreainvestment.com:9443"
        )
        print(" Agent  ")
        
        #    
        print("\n    ...")
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        
        #    (AccountAPI )
        executions = agent.account_api.get_orders_filled()
        
        if executions and executions.get('rt_cd') == '0':
            output = executions.get('output', [])
            print(f"    {len(output)}  ")
            
            for i, execution in enumerate(output, 1):
                print(f"\n   [{i}] {execution.get('prdt_name', 'N/A')}")
                print(f"       : {execution.get('pdno', 'N/A')}")
                print(f"       : {execution.get('ord_dvsn_name', 'N/A')}")
                print(f"       : {execution.get('sll_buy_dvsn_cd_name', 'N/A')}")
                print(f"       : {execution.get('ccld_qty', 'N/A')}")
                print(f"       : {execution.get('ccld_unpr', 'N/A')}")
                print(f"       : {execution.get('ord_tmd', 'N/A')}")
        else:
            print(f"    : {executions}")
            
        #   
        print("\n   ...")
        pending_orders = agent.account_api.get_orders_pending()
        
        if pending_orders and pending_orders.get('rt_cd') == '0':
            output = pending_orders.get('output', [])
            print(f"    {len(output)}  ")
            
            for i, order in enumerate(output, 1):
                print(f"\n   [{i}] {order.get('prdt_name', 'N/A')}")
                print(f"       : {order.get('pdno', 'N/A')}")
                print(f"       : {order.get('ord_dvsn_name', 'N/A')}")
                print(f"       : {order.get('sll_buy_dvsn_cd_name', 'N/A')}")
                print(f"       : {order.get('ord_qty', 'N/A')}")
                print(f"       : {order.get('ord_unpr', 'N/A')}")
                print(f"       : {order.get('rmn_qty', 'N/A')}")
                print(f"       : {order.get('ord_tmd', 'N/A')}")
        else:
            print(f"    : {pending_orders}")
            
    except Exception as e:
        print(f"  : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_orders()