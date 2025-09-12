#!/usr/bin/env python3
"""
   - (009470)  1  ( )
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from pykis import Agent

# .env  
load_dotenv()

def test_cash_order():
    """  """
    
    #  API  
    app_key = os.getenv('APP_KEY')
    app_secret = os.getenv('APP_SECRET') 
    account_no = os.getenv('CANO')
    account_code = os.getenv('ACNT_PRDT_CD', '01')
    
    if not all([app_key, app_secret, account_no]):
        print("   :")
        print("   .env     :")
        print("   APP_KEY=your_app_key")
        print("   APP_SECRET=your_app_secret")
        print("   CANO=your_account_no")
        print("   ACNT_PRDT_CD=01")
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
        
        # 1.    
        print("\n (009470)  ...")
        price_info = agent.get_stock_price("009470")
        if price_info and 'output' in price_info:
            current_price = price_info['output'].get('stck_prpr', '0')
            print(f"   : {current_price}")
        else:
            print("   ")
            current_price = "30000"  # 
        
        # 2.  
        print("\n  ...")
        if current_price != "0":
            cash_psbl = agent.inquire_order_psbl(
                pdno="009470",
                ord_unpr=current_price
            )
            if cash_psbl and cash_psbl.get('rt_cd') == '0':
                max_qty = cash_psbl.get('output', {}).get('ord_psbl_qty', '0')
                psbl_amt = cash_psbl.get('output', {}).get('ord_psbl_amt', '0')
                print(f"   : {max_qty}")
                print(f"   : {psbl_amt}")
            else:
                print(f"   : {cash_psbl}")
        else:
            print("      ")
        
        # 3.     ( )
        print("\n   ...")
        
        #     ( ,  )
        current_price_int = int(current_price)
        high_price_int = current_price_int + 500  # 500 
        
        #   (30,000  50 )
        if high_price_int >= 30000:
            high_price_int = (high_price_int // 50) * 50
        
        high_price = str(high_price_int)
        print(f"   : {high_price} (  +{high_price_int - current_price_int})")
        
        order_result = agent.order_stock_cash(
            ord_dv="buy",           # 
            pdno="009470",          # 
            ord_dvsn="00",          # 
            ord_qty="1",            # 1
            ord_unpr=high_price     #  
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
                print("  !")
                print("         .")
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
    test_cash_order()