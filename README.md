# PyKIS

 OpenAPI Python      .

** NEW: NXT()  !** - KOSPI/KOSDAQ     

[![Tests](https://img.shields.io/badge/tests-232%20passed-brightgreen)](https://github.com/your-repo/pykis)
[![Coverage](https://img.shields.io/badge/coverage-52%25-orange)](https://github.com/your-repo/pykis)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![NXT](https://img.shields.io/badge/NXT--green)](https://www.nextrade.co.kr/)

##   

```bash
pip install pykis
```

##  API  

  API  :
- [](https://apiportal.koreainvestment.com)   API 
- APP_KEY APP_SECRET 
- (CANO) (ACNT_PRDT_CD) 

##   

```python
from pykis import Agent
import os

#  API   ( )
app_key = os.environ.get('KIS_APP_KEY')
app_secret = os.environ.get('KIS_APP_SECRET')
account_no = os.environ.get('KIS_ACCOUNT_NO')
account_code = os.environ.get('KIS_ACCOUNT_CODE', '01')

# Agent   ()
agent = Agent(
    app_key=app_key,
    app_secret=app_secret,
    account_no=account_no,
    account_code=account_code,
    # base_url="https://openapi.koreainvestment.com:9443"  #  ()
)

#  Agent 
agent_mock = Agent(
    app_key=app_key,
    app_secret=app_secret,
    account_no=account_no,
    account_code=account_code,
    base_url="https://openapivts.koreainvestment.com:29443"  # 
)
```

###  

```python
try:
    agent = Agent(
        app_key=app_key,
        app_secret=app_secret,
        account_no=account_no,
        account_code=account_code
    )
except ValueError as e:
    print(f"  : {e}")
except RuntimeError as e:
    print(f"  : {e}")
```

#    
balance = agent.get_account_balance()  #  

# Note: get_cash_available get_total_asset     :
if balance and balance.get('rt_cd') == '0':
    #     balance['output2'] 
    total_info = balance['output2'][0] if balance.get('output2') else None
    if total_info:
        total_asset = total_info.get('tot_evlu_amt')  #  
        available_cash = total_info.get('nass_amt')   # 

#    (NEW )
#  1 70000   ()
result = agent.order_stock_cash("buy", "005930", "00", "1", "70000")

#  1   ( )
result = agent.order_stock_cash("buy", "005930", "03", "1", "0")

#  1   (, )
from datetime import datetime
today = datetime.now().strftime("%Y%m%d")
result = agent.order_stock_credit("buy", "009470", "21", "00", "1", "12000", loan_dt=today)

#   / 
inquiry = agent.inquire_order_psbl("005930", "70000")
print(f": {inquiry['output']['max_buy_qty']}")

#   / 
credit_inquiry = agent.inquire_credit_order_psbl("005930", "70000", crdt_type="21")
print(f": {credit_inquiry['output']['crdt_psbl_qty']}")

#     (KOSPI/KOSDAQ/NXT  )
price = agent.get_stock_price("005930")      #   (KOSPI)
daily = agent.get_daily_price("035720")      #   (KOSDAQ)
orderbook = agent.get_orderbook("NXT")   # NXT     

#    
minute_data = agent.get_minute_price("005930", "093000")  #   
daily_minute = agent.get_daily_minute_price("005930", "20250715", "153000")  #  

#     (4    )
minute_data = agent.fetch_minute_data("005930", "20250715")  # 
recent_data = agent.fetch_minute_data("005930")             #  

#    (/, VWAP, )
support_resistance = agent.calculate_support_resistance("005930")

#   &  
condition_stocks = agent.get_condition_stocks("user_id", 0, "N")
investor_trend = agent.get_stock_investor("005930")  #  

#   &  
is_holiday = agent.is_holiday("20250101")  #  
holiday_info = agent.get_holiday_info()    #  

#  200   ( )
futures_price = agent.get_future_option_price()  # 9(101W09)  

#   Excel 
from pykis.utils.trading_report import generate_trading_report
report_path = generate_trading_report(
    agent.client, 
    {'CANO': 'your_account', 'ACNT_PRDT_CD': '01'},
    '20250101', '20250131',
    output_path='trading_history.xlsx'
)
```

##    

공식 웹소켓 진입점은 `WebSocketClient`입니다.

```python
from pykis import WebSocketClient
# 혹은 agent.websocket()으로 생성
ws_client = agent.websocket(stock_codes=["005930"], enable_index=True)
```

`KisWebSocket`은 deprecated이며 테스트/내부 호환만 유지됩니다.

```python
#    
ws_client = agent.websocket(
    stock_codes=["005930", "035420"],  # , 
    enable_index=True,                 #  
    enable_program_trading=True,       #  
    enable_ask_bid=True               #  
)

#  
import asyncio
asyncio.run(ws_client.start())

# 주의: 승인키 발급 정책 (fail-fast)
# - agent.websocket()은 내부 KISClient에서 approval_key를 발급해 주입합니다.
# - 승인키 발급 실패 시 즉시 예외를 발생시키고(traceback 포함) 로깅합니다.
# - 네트워크/자격 증명 문제를 먼저 해결한 뒤 재시도하세요.
```

##   Excel 

```python
from pykis.utils.trading_report import generate_trading_report

#   Excel 
report_path = generate_trading_report(
    client=agent.client,
    account_info={'CANO': 'your_account', 'ACNT_PRDT_CD': '01'},
    start_date='20250101',
    end_date='20250131', 
    output_path='trading_history.xlsx',
    tickers=['005930', '035420'],  #   ()
    only_executed=True             #  
)
print(f" : {report_path}")
```

##    

   SQLite  :

```bash
cd examples  
python minute_candle_crawler.py
```

### 
- ** **: /    
- **  **:  API    
- ** **: 4      
- **SQLite **: `{}_candles.db`   
- **  **:      

###  
```
   
========================================
    : 
  :  (005930)

   
 (YYYYMMDD): 20240101
 (YYYYMMDD): 20240131

  : (005930)
 : 20240101 ~ 20240131
  : 22
  : 005930_candles.db
============================================================
[  1/22] 20240102  ...   (361)
[  2/22] 20240103  ...   (361)
...
============================================================
  !
 : 22/22 
  : 005930_candles.db

   :
     : 7,942
    : 22
    : 361.0
```

##   

-  **246  ** ()
-  **52%  ** () 
-  **  **:
  - `trading_report.py`: 98%
  - `program/trade.py`: 95% 
  - `core/config.py`: 88%
  - `websocket/ws_agent.py`: 64%

```bash
#  
pytest tests/ -v --cov=pykis
```

##   

###  
- `get_account_balance()`:   
- `get_cash_available()`:    
- `get_total_asset()`:   
- `get_possible_order_amount(code, price)`:    

###    (NEW)
- `order_stock_cash(ord_dv, pdno, ord_dvsn, ord_qty, ord_unpr)`:   (/)
- `order_stock_credit(ord_dv, pdno, crdt_type, ord_dvsn, ord_qty, ord_unpr)`:   (/, )
- `inquire_order_psbl(pdno, ord_unpr)`:   / 
- `inquire_credit_order_psbl(pdno, ord_unpr)`:   / 
- `order_credit(code, qty, price, order_type)`:   ()
- `order_rvsecncl(org_order_no, qty, price, order_type, cncl_type)`:  /
- `inquire_psbl_rvsecncl()`: /   
- `order_resv(code, qty, price, order_type)`:  
- `order_resv_rvsecncl(seq, qty, price, order_type)`:   /
- `order_resv_ccnl()`:   

###   (KOSPI/KOSDAQ/NXT  )
- `get_stock_price(code)`:   
- `get_daily_price(code)`:     
- `get_orderbook(code)`:   
- `get_minute_price(code, time)`:     
- `get_daily_minute_price(code, date, hour)`:     ( 120)
- `fetch_minute_data(code, date, cache_dir)`:    (4   )
- `calculate_support_resistance(code, date)`:   (/, VWAP, )

###    
- `get_future_option_price()`: 200   ( )
- `get_futures_price(code)`:    
- `get_kospi200_futures_code()`:    

### 
- `generate_trading_report()`:  Excel  

###  
- `get_stock_investor(ticker)`:    
- `get_foreign_broker_net_buy(code, foreign_brokers, date)`:    
- `get_volume_power(code)`:  
- `get_stock_ccnl(code)`:  (30)  -   

###  
- `get_stock_member(code)`:   
- `get_member_transaction(code, start_date, end_date)`:   

### 
- `get_condition_stocks(user_id, seq, div_code)`:   

### 
- `get_program_trade_by_stock(code, date)`:   
- `get_program_trade_daily_summary(code, date)`:   
- `get_program_trade_market_daily(start_date, end_date)`:  

### 
- `get_holiday_info()`:   
- `is_holiday(date)`:    
- `get_daily_credit_balance(code, date)`:    

##    (v0.1.21)

###   
- **  Excel **:   Excel    
  - ,   
  -    
  - 98%   
- **    **: 178    
  - Agent   env_path    
  -       
  -  API  

###  
- ** **: .env     
- ** **: BaseAPI   account   
- ** **:       

##   (v0.1.20)

##    (v0.1.22)

###  NXT()   
- **  **:  API KOSPI/KOSDAQ/NXT  
  - `FID_COND_MRKT_DIV_CODE`  "J" "UN" 
  -  KOSPI/KOSDAQ  100%  
  - NXT      
- ** **:  , / ,  ,   ,       API

###      
- ** **: 232   ( 178 54 )
- ** **: 52%  ( 44% )
- **  **: DataFrame ,  DB, WebSocket     

###   
- **    **:       `WSAgent`  
  -  , , ,    
  -       
  -      

###  
- **  **: `KIS_WS.py` `pykis.websocket`  
- **Agent **: `agent.websocket()`    

##   (v0.1.18)

###    100%  
- **  **: 121 , 2 , 1 xfail ( )
- **PyKIS    100% **:   API    

###  
- **  **: CI/CD     
- **   **: `KISConfig`        

##   (v0.1.16)

###   
- ** KOSPI200    **:  API     
  - `get_kospi200_futures_code` :         (3,6,9,12)       
  - `get_future_option_price`  :      KOSPI200    

## 

MIT License

## 

 ,  ,   !

## 

-  : [GitHub Issues](https://github.com/your-repo/pykis/issues)
- : [PyKIS ](https://your-docs-url.com)
