# PyKIS

한국투자증권 OpenAPI Python 래퍼 - Korea Investment & Securities Trading API Client

**🚀 NEW: NXT(넥스트) 시장 완벽 지원!** - KOSPI/KOSDAQ과 함께 모든 국내 주식시장 커버

## ✨ 주요 특징

- **🏎️ 고성능**: 지능형 캐싱으로 API 호출 80-95% 감소
- **🛡️ 안정성**: 실측 기반 Rate Limiting (18 RPS / 900 RPM)
- **📊 실시간**: WebSocket을 통한 실시간 데이터 스트리밍
- **📈 완전성**: KOSPI, KOSDAQ, NXT 시장 완벽 지원
- **🔧 편의성**: Excel 거래 보고서 자동 생성
- **🤖 자동화**: CI/CD 파이프라인과 자동 테스트 (232개 테스트)     

[![Tests](https://img.shields.io/badge/tests-232%20passed-brightgreen)](https://github.com/unohee/pykis)
[![Coverage](https://img.shields.io/badge/coverage-52%25-orange)](https://github.com/unohee/pykis)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![NXT](https://img.shields.io/badge/NXT--green)](https://www.nextrade.co.kr/)
[![Rate Limiting](https://img.shields.io/badge/rate%20limiting-18%20RPS%2F900%20RPM-blue)](https://github.com/unohee/pykis)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-green)](https://github.com/unohee/pykis/actions)

## 📦 설치

```bash
pip install pykis
```

## 🔧 사전 준비

한국투자증권 API 사용을 위한 준비사항:
- [한국투자증권 API 포털](https://apiportal.koreainvestment.com)에서 API 신청
- APP_KEY와 APP_SECRET 발급
- 계좌번호(CANO)와 계좌상품코드(ACNT_PRDT_CD) 확인

## ⚡ 성능 최적화

PyKIS는 실제 운영 환경에서 검증된 성능 최적화를 제공합니다:

- **캐시 적중률**: 80-95% (API 호출 대폭 감소)
- **Rate Limiting**: 18 RPS / 900 RPM (실측 안정 기준)
- **응답 시간**: 평균 50ms 이하 (캐시 적중 시)
- **동시 연결**: 멀티스레드 안전성 보장 

## 🚀 빠른 시작

```python
from pykis import Agent
import os

# 환경변수에서 API 키 로드 (권장 방식)
app_key = os.environ.get('KIS_APP_KEY')
app_secret = os.environ.get('KIS_APP_SECRET')
account_no = os.environ.get('KIS_ACCOUNT_NO')
account_code = os.environ.get('KIS_ACCOUNT_CODE', '01')

# Agent 인스턴스 생성 (실전투자)
agent = Agent(
    app_key=app_key,
    app_secret=app_secret,
    account_no=account_no,
    account_code=account_code,
    # 기본값: 실전투자 URL
)

# 모의투자 Agent 생성
agent_mock = Agent(
    app_key=app_key,
    app_secret=app_secret,
    account_no=account_no,
    account_code=account_code,
    base_url="https://openapivts.koreainvestment.com:29443"  # 모의투자
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

## 📋 테스트 현황 (v0.1.22)

### 🧪 테스트 커버리지
- **232개 테스트 통과** (모든 핵심 기능 검증)
- **52% 코드 커버리지** (지속적 개선 중)
- **CI/CD 자동화**: GitHub Actions으로 Python 3.8/3.11/3.12 테스트

###  NXT()   
- **  **:  API KOSPI/KOSDAQ/NXT  
  - `FID_COND_MRKT_DIV_CODE`  "J" "J" 
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