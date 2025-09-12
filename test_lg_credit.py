#!/usr/bin/env python3
"""
LG(011070)  1  
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from pykis import Agent

# .env  
load_dotenv()

def test_lg_credit_order():
    """LG  """
    
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
            base_url="https://openapi.koreainvestment.com:9443"  # 
        )
        print(" Agent  ")
        
        # 1. LG  
        print("\n LG(011070)  ...")
        price_info = agent.get_stock_price("011070")
        if price_info and 'output' in price_info:
            current_price = price_info['output'].get('stck_prpr', '0')
            print(f"   : {current_price}")
        else:
            print("   ")
            current_price = "0"
        
        # 2.  
        print("\n  ...")
        if current_price != "0":
            credit_psbl = agent.inquire_credit_order_psbl(
                pdno="011070", 
                ord_unpr="0",  #  0
                ord_dvsn="03",  # 
                crdt_type="21",  # 
                cma_evlu_amt_icld_yn="N",
                ovrs_icld_yn="N"
            )
            if credit_psbl and credit_psbl.get('rt_cd') == '0':
                max_qty = credit_psbl.get('output', {}).get('max_buy_qty', '0')
                psbl_amt = credit_psbl.get('output', {}).get('crdt_buy_psbl_amt', '0')
                print(f"   : {max_qty}")
                print(f"   : {psbl_amt}")
            else:
                print(f"   : {credit_psbl}")
        
        # 3.   (, )
        print("\n   ...")
        print("   :  ( 1  )")
        
        #   (   )
        today = datetime.now().strftime("%Y%m%d")
        
        order_result = agent.order_stock_credit(
            ord_dv="buy",           # 
            pdno="011070",          # LG
            crdt_type="21",         # 
            ord_dvsn="03",          #  
            ord_qty="1",            # 1
            ord_unpr="0",           #   0
            loan_dt=today           #  
        )
        
        print("\n  :")
        if order_result:
            print(f"   : {order_result.get('rt_cd', 'N/A')}")
            print(f"   : {order_result.get('msg1', 'N/A')}")
            if 'output' in order_result:
                output = order_result['output']
                print(f"   : {output.get('odno', 'N/A')}")
                print(f"   : {output.get('ord_tmd', 'N/A')}")
            
            if order_result.get('rt_cd') == '0':
                print("  !    ")
            else:
                print("  ")
                print(f"    : {order_result}")
        else:
            print("  ")
            
    except Exception as e:
        print(f"  : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lg_credit_order()