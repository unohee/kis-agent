# Changelog

모든 주목할 만한 변경사항이 이 파일에 문서화됩니다.

## [1.1.0+] - 2025-09-21

### 🚀 성능 최적화
- **Rate Limiter 최적화**: 실측 기반으로 기본값 조정 (18 RPS / 900 RPM)
- **CI/CD 최적화**: Python 버전 테스트를 3개로 축소 (3.8/3.11/3.12)
- **캐시 성능**: 80-95% API 호출 감소 확인

### 🛠️ 시스템 개선
- **예외 처리 강화**: 통합 예외 처리 시스템 구축 (`pykis/core/exceptions.py`)
- **문서화 개선**: 모든 docstring 업데이트 및 README 전면 개선
- **테스트 안정성**: 232개 테스트 통과율 100% 달성

### 🔧 개발 환경
- **GitHub Actions**: CI/CD 파이프라인 최적화 및 보안 스캔 추가
- **보안 강화**: CodeQL 및 Trivy 보안 검사 통합
- **의존성 관리**: Dependabot 제거로 PR 노이즈 감소
- **코드 품질**: Black, isort, flake8, mypy 자동화

## [1.1.0] - 2025-01-12

###   
- **  API  **: /     
  - `order_stock_cash()`:  /  (, ,  )
  - `order_stock_credit()`:  /  (, ,  , )
  - `inquire_order_psbl()`:   / 
  - `inquire_credit_order_psbl()`:   / 

###     
- **TR ID **:   OpenAPI  
  - :  TTTC0012U,  TTTC0011U (: VTTC0012U, VTTC0011U)
  - :  TTTC0052U,  TTTC0051U
- **Rate Limiter **: 10 req/sec, 100ms   
- **  **:      
- ** Docstring**: NumPy      
- **  **:     

###   
- **246  **:   68  
- **52%  **: 8% 
- **  **: 
  - StockAPI    (13 )
  - Agent    (9 )
  - /   
  -      

###   
- **README.md**:   API   
- **  **: ,     
- ** **:     

###   
- **  **:     
- **  **:     
- ** **: ,     

## [1.0.0] - 2025-01-03 

###   :     

###  Breaking Changes
- **API   **:  `inquire_daily_ccld`  DataFrame  Dict    (pykis   )
- **  **: `pagination: bool = False`  / 

###   
- **  **: 
  - CTX_AREA_FK100/NK100    100  
  -  10,000   (100 × 100)
  -       
  -      
  
- **   **: 
  - `OrderExecutionItem`:    (27 )
  - `OrderExecutionSummary`:   
  - `OrderExecutionResponse`:  API  
  -  : `is_buy`, `is_sell`, `is_executed`, `execution_rate` 

- **   **:
  -    
  - NumPy   
  -   

###   
- ** **: Dict    
- ****:       
- ****:       
- ****:  ,       

###   
- **  **:  100 →  10,000  
- ** **:     
- ** **: (ord_dt, odno, pdno)    

###   
```python
#   ( )
result = agent.inquire_daily_ccld(start_date="20250101", end_date="20250131")

#  ()
result = agent.inquire_daily_ccld(
    start_date="20250101", 
    end_date="20250131",
    pagination=True,
    max_pages=50,
    page_callback=lambda page, data, ctx: print(f" {page}: {len(data)}")
)

#   
from pykis.account.models import OrderExecutionResponse
response = OrderExecutionResponse.from_api_response(result)
buy_orders = response.get_buy_orders()
executed_orders = response.get_executed_orders()
```

###   
- **94.4%  **:    
- **zero  **:   `pagination=False`   
- ** **:      

   pykis **   **    .

---

## [0.1.22] - 2025-08-27

###  NXT()   
- **  **:  API KOSPI/KOSDAQ/NXT  
  - `FID_COND_MRKT_DIV_CODE`  "J" "J" 
  - 29   (7  + 2  )
  -  KOSPI/KOSDAQ  100%  
  - NXT      

###         
- ** **: 232   (54 )
- ** **: 52%  (8% )
- **  **: 
  - `test_dataframe_helper.py`: DataFrame   16  (100% )
  - `test_investor_db.py`:  DB  16  (75% )
  - `test_websocket_client_basic.py`: WebSocket    15 

###   
- **Stock API **: `api.py`, `investor_api.py`, `price_api.py`, `market_api.py`, `condition.py`
- **Core **: `client.py` (  )
- **Program **: `trade.py` ( )
- ** **: `test_client.py`, `test_program_trade.py`

###    (2025-08-27 )
- **   **: API   J/UN   
- **investor_api.py**: / API J   (UN   )
  - `get_stock_investor()`, `get_stock_member()`, `get_member_transaction()` 
- ** API**:  / API UN   (NXT  )

###   
- **README.md**: NXT   ,  
- **NXT_SUPPORT_CHANGES.md**:   

## [0.1.21] - 2025-08-22

###   
- **  Excel  **:   Excel     
  - ** **: YYYYMMDD  / 
  - ** **:     
  - **  **:      
  - **  **:    
  - **98%  **:    

- **    **:    
  - **178   **: 2 , 1  
  - **Agent   **: env_path  
  - **   **:    
  - ** API  **: BaseAPI  

###  
- ** **: .env     
  - Agent  env_path  
  -      
- **  **: BaseAPI   account   
- **  **:       
- **  **:     

###    
- ** **: 44%
- **  **:
  - `trading_report.py`: 98% 
  - `program/trade.py`: 95%
  - `core/config.py`: 88%
  - `websocket/ws_agent.py`: 64%

###   
```python
#    Agent 
from pykis import Agent
agent = Agent(env_path=".env")  # env_path 

#  Excel 
from pykis.utils.trading_report import generate_trading_report
report_path = generate_trading_report(
    client=agent.client,
    account_info={'CANO': 'your_account', 'ACNT_PRDT_CD': '01'},
    start_date='20250101',
    end_date='20250131',
    output_path='trading_history.xlsx'
)

# 200   ( )
futures_price = agent.get_future_option_price()  # 9(101W09)
```

## [0.1.26] - 2025-01-08

### 
- **    API **
  - **/  API**:
    - `inquire_daily_ccld`:  (TTTC0081R)
    - `order_cash`: () - / (TTTC0011U/TTTC0012U)
    - `order_rvsecncl`: () (TTTC0013U)
    - `inquire_psbl_rvsecncl`:  (TTTC0084R)
  
  - **/  API**:
    - `inquire_period_trade_profit`:  (TTTC8715R)
    - `inquire_balance_rlz_pl`: _ (TTTC8494R)
  
  - **/  API**:
    - `inquire_psbl_sell`:  (TTTC8408R)
  
  - **  API**:
    - `order_resv`:  (CTSC0008U)
    - `order_resv_ccnl`:  (CTSC0004R)
    - `order_resv_rvsecncl`:  (CTSC0009U/CTSC0013U)
  
  - **  API**:
    - `inquire_credit_psamount`:  (TTTC8909R)
    - `order_credit_buy`: () (TTTC0052U)
    - `order_credit_sell`: () (TTTC0051U)
  
  - **/  API**:
    - `inquire_intgr_margin`:   (TTTC0869R)
    - `inquire_period_rights`:  (CTRGA011R)

### 
- **AccountAPI   **: 15     
- **Agent Facade  **:   API Agent    
- ** **:       

### 
- `testing/test_account_apis_250108.py`:   API    

=======
>>>>>>> a49c093ae6bced46934b90424a2ff3dac213c4ba
## [0.1.25] - 2025-07-15

### 
- **  API **
  - **`get_daily_minute_price(code, date, hour)`  **:
    -       ( 120)
    - TR ID: FHKST03010230 
    -        
    -  1    
  - **API  **: `INQUIRE_TIME_DAILYCHARTPRICE`
  - **StockAPI  Agent  **

### 
- **    **
  - **`fetch_minute_data`   **:
    -  30   →  4   
    -    (~480)  
    - 4  09:00, 11:00, 13:00, 15:30  
  - **   **:
    -  :   +    
    -  :   
  - **  **: `is_holiday` API    
  - **  **:    ,    

### 
- **    **
  - **`calculate_support_resistance(code, date)`  **:
    -    /  
    -     (Volume Profile)
    -     (R1~R3, S1~S3)
    - VWAP (   ) 
    -    (0-100) 
  - **5   **:
    -    
    -    / 
    -      
    -      
    -   /  

### 
- **    **
  - **`examples/minute_candle_crawler.py` **:
    -   /  
    -      
    - 4     
    - `{}_candles.db` SQLite   
    -      
    -      
  - **  **:
    -  →   
    -     
    -     DB 
    -     

### 
- **    **:
  - (005930) 2024 12 20 361   
  -   +   722 (361+361)  
  -   0.00   
- **   **:
  -  5,  5  
  - VWAP     
  -     
  -     

###  
- **README.md **:
  -      
  -     
  -       
- **  **:
  - `get_daily_minute_price`  
  - `calculate_support_resistance`  
  -     

### 
- **   300% **: 30   → 4  
- **   **:        
- **   **:      
- **  **:    +     

## [0.1.24] - 2025-01-21

### 
- **     **
  - **`get_daily_credit_balance(code, date)`  **:
    -  (/)    
    - TR ID: FHPST04760000 
    - , ,     
    - ,   
    -  /   
  - **StockAPI  Agent  **:
    - `pykis/stock/api.py` StockAPI  
    - `pykis/core/agent.py` Agent  
    -    API  

### 
- **  API  **:
  - (005930)    
  - 30     
  -   0 () 
  -  0.13%,  842    

###  
- **PYKIS_API_METHODS.md **:
  -      
  -     (19/22  , 86.4%)
  -       
- **README.md **:
  -   " "  
  - API   `get_daily_credit_balance` 
- **CHANGELOG.md **:
  -      

### 
- **   **: /       
- **API  **: Postman    API  
- ** **:         

## [0.1.23] - 2025-07-10

### 
- **         **
  - **`fetch_minute_data`    **:
    - (09:00~15:30): 5  
    - : 30  
    -       
  - **   **:
    - : `{code}_minute_data.csv`
    - : `{code}_minute_data_{YYYYMMDD}.csv`
    -     
  - **  **:
    -       
    - API       
    -      

### 
- **     **
  - **`examples/portfolio_realtime_monitor.py`  **:
    -        
    -     
    - VWAP(  ) 60   
    - VWAP     
    -    
    -   5  
  - **`examples/README_portfolio_monitor.md`  **:
    -      
    -      
    -       
    -   (RSI, MACD,   )
  - **`examples/test_portfolio_monitor.py`  **:
    - Agent ,  ,    
    -  , VWAP ,    
    -       

### 
- **    **
  - **StockPosition  **:
    -  : , , , 
    -  : , , VWAP, 
    - : / ,  
    -  : ,   
  - **  **:
    - VWAP  -   
    -       
    -     

###  
- **  **:
  ```python
  #       
  balance = self.agent.get_account_balance()
  for position in balance['output1']:
      if int(position.get('hldg_qty', 0)) > 0:
          self.positions[code] = StockPosition(...)
  ```
- **VWAP  **:
  ```python
  # 60   VWAP 
  total_value = sum(price * volume for price, volume in valid_data)
  total_volume = sum(volume for _, volume in valid_data)
  vwap = total_value / total_volume
  ```
- ** **:
  ```
      
                  VWAP        
      75,000   70,000  +7.14%  74,500  +0.67%   +2.5%   1,234
  ```

### 
- **   **:
  -   : API   (420)
  -   :    ( )
  -       
- **   **:
  - 6      
  - Agent ,  ,    
  - VWAP        

### 
- ** **:        
- ** **:       
- **  **: VWAP     
- ** **:        
- ****:        

## [0.1.22] - 2025-07-07

### 
- ** pytest    **
  - **   **: 
    -         
    - `tests/test_token.py` /      
    -    `pykis/core/credit/KIS_Token.json` 
  - **  **:
    - `pykis/core/auth.py`, `pykis/core/config.py`   `.env`   
    -       `.env`  
    - `load_dotenv(dotenv_path=os.path.join(ROOT_DIR, '.env'), override=True)` 
  - **   **:
    - HTTP   5 → 2 
    -   1 → 0.5     
    - API        

### 
- **   99.2%  **
  - **  **: 127 , 2 , 1 xfail ( )
  - ** **:    5 → 30 90% 
  - ** **:         
  - **  **: `tests/websocket/test_client.py` → `test_websocket_client.py` 

###    
- **   **:
  ```python
  #       
  backup_path = token_tmp + '.backup'
  if os.path.exists(token_tmp):
      shutil.copy2(token_tmp, backup_path)
  
  #       
  finally:
      if os.path.exists(backup_path):
          shutil.copy2(backup_path, token_tmp)
          os.remove(backup_path)
  ```
- **  **:
  ```python
  #    .env    
  ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
  load_dotenv(dotenv_path=os.path.join(ROOT_DIR, '.env'), override=True)
  ```

### 
- **        **
- **   128   127  **
- **CI/CD     **

## [0.1.21] - 2025-07-07

### 
- **  API     **
  - **`get_cash_available` API **: 
    - TR ID : `TTTC8901R` → `TTTC8908R` ()
    -   : `PDNO`     
    - : "005930" ()
  - **`get_total_asset` API **:
    - TR ID : `TTTC8522R` → `CTRP6548R` ()
    -   : `INQR_DVSN_1`, `BSPR_BF_DT_APLY_YN` 
    -  404   JSON     

- **   **
  - **`fetch_minute_data`  **: 
    -   `get_minute_chart`  `get_minute_price` 
    -      360     
  - **   **:  `get_minute_chart`  `get_minute_price` 

- **   **
  - **`pykis/websocket/client.py`   **:
    - 1245-1246 `if self.enable_ask_bid:`    
    - PyKIS  import      

### 
- **   100%  **
  - **  **: 127 , 2 , 1 xfail ( )
  - ** API   **: 
    - ""  → "_"  
    -  API     
    -  AccountAPI  16 
  - **API  **: 404 , JSON     API  

### 
- **   **
  - **`examples/test_helpers.py`  **:
    - `test_api_method`: API      
    - `setup_test_environment`: Agent       
    - `batch_test_methods`:    
    - `print_test_summary`:   
    - `reset_test_results`:   
    - `get_common_test_configs`:     
  - **  **:       

- **   v2.0  **
  - **Cell 1**:   import    
  - **Cell 2**:     ,     
  - **Cell 5**:    (  )
  - **Cell 6**:     ( )
  - **Cell 7**:      
  - **Cell 0**:  "v2.0 -    " 

### 
- ** RTX_ENV   **
  -     
  - PyKIS Agent  import/ 
  - API  100%  
  -      

### 
- **API **:        (360 )
- **API **:  API   404   
- ** **:      
- ** **:       
- ** **:       

## [0.1.20] - 2025-07-07

### 
- **      (H0IF1000)**
  - **, , 200**     
  - , ,   
  - `enable_index=True`    
  -    : 0001(KOSPI), 1001(KOSDAQ), 2001(KOSPI200)

- **      (H0GSCNT0)**
  - **   **   
  - , , ,   
  - `enable_program_trading=True`    
  -     

- **       (H0STASP0)**
  - **10   **  (    )
  -  5    
  - `enable_ask_bid=False`     (: )

- ** Agent   **
  - `agent.websocket()`    :
    - `enable_index`:      (: True)
    - `enable_program_trading`:      (: True)
    - `enable_ask_bid`:      (: False)

### 
- **     **
  - `handle_message()`   TR ID   
  -        
  -       
  -         

- **      **
  -      (KOSPI, KOSDAQ, KOSPI200)
  -      ( )
  -      (  )

- **KISClient     **
  - `get_ws_approval_key()`  
  -    : `KIS_SECRET_KEY` → `KIS_APP_SECRET`
  -        

### 
- **  **:   12% → 25%
- **  **: 6    
- **   **: , ,     

###  
```python
#    
agent = Agent()
ws_client = agent.websocket(
    stock_codes=["005930"],
    enable_index=True,           #    (, , 200)
    enable_program_trading=True, #   
    enable_ask_bid=False         #    ()
)
await ws_client.connect()
```

## [0.1.19] - 2025-07-07

### 
- **  **: `KIS_WS.py` `pykis.websocket`   `Agent`     `websocket()`  .
- ** **:    `README.md`, `PYKIS_API_METHODS.md`     .

### 
- `pykis/websocket/client.py`:  `KIS_WS.py`  `pykis`    ,    .
- `pykis/__init__.py`: `KisWebSocket`  `pykis`  .

## [0.1.18] - 2025-06-29

### 
- **  100%  **
  - `pykis/core/config.py`: `KISConfig`  `__init__`   
    - `all()`  `any()`        
    -       
    - `tests/unit/test_config.py::TestKISConfig::test_validate_config_missing_values`  
  - **  : 121 , 2 , 1 xfail ( )**
  - **PyKIS    100% **:   API    
    - `get_stock_price`, `get_daily_price`, `get_minute_price`  8  API  
    - Agent      
    -  API     

### 
- **  **: CI/CD     
- **   **:       
- **   61% **:    

## [0.1.17] - 2025-07-06

### 
- **   **
  - `tests/unit/test_config.py`: `KISConfig`       ,     `.env`    .   CI/CD              .
  - `tests/integration/test_agent_comprehensive.py`: `test_is_holiday`     .         ,       .

## [0.1.16] - 2025-01-29

### 
- ** KOSPI200    **
  - **`get_kospi200_futures_code`  **:          
    -     (3,6,9,12)      
    - KOSPI200     (: 101S12, 201S03 )
    - `get_future_option_price`    
  - ** API **:      KOSPI200    
    - :     (`101S09` )
    - :      

### 
- **    **: KOSPI200   
- ** **: PYKIS_API_METHODS.md    

###  
```python
#   (  )
futures_price = agent.get_future_option_price(
    market_div_code="F",      # 
    input_iscd="101S09"       #   
)

#   (  )
futures_price = agent.get_future_option_price()  #   KOSPI200  
```

## [0.1.15] - 2025-01-29

### 
- **   API **
  - **`get_future_option_price`  **:    
    - API : `/uapi/domestic-futureoption/v1/quotations/inquire-price` (TR: FHMIF10000000)
    - , , ,    
    - : F(), O(), JF(), JO()
    - :  6(: 101S03),  9(: 201S03370)
    - : (F), (101S09)

- ** **:
  ```python
  #    ()
  futures_price = agent.get_future_option_price()
  
  #    
  futures_price = agent.get_future_option_price(
      market_div_code="F",      # 
      input_iscd="101S03"       #   
  )
  
  #   
  option_price = agent.get_future_option_price(
      market_div_code="O",      # 
      input_iscd="201S03370"    #   (9)
  )
  ```

- **  **: `examples/future_option_price_example.py` -     
- ** **: PYKIS_API_METHODS.md     

## [0.1.14] - 2025-01-29

### 
- **   API **
  - **`get_daily_index_chart_price`  **:   
    - API : `/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice` (TR: FHKUP03500100)
    -     (, , , , KOSPI, KOSDAQ )
    -    (, , , )
    -  50  ,       
    -  : 0001(), 0002(), 0003(), 0004(), 0005(KOSPI), 0006(KOSDAQ), 0007(KOSPI200), 0008(KOSPI100), 0009(KOSPI50), 0010(KOSDAQ150)

- ** **:
  ```python
  #     
  sector_daily = agent.get_daily_index_chart_price(
      market_div_code="U",      # 
      input_iscd="0001",        # 
      start_date="20240601",
      end_date="20240630",
      period_div_code="D"       # 
  )
  
  #     
  large_cap_weekly = agent.get_daily_index_chart_price(
      market_div_code="U",      # 
      input_iscd="0002",        # 
      start_date="20240101",
      end_date="20241231",
      period_div_code="W"       # 
  )
  ```

- **  **: `examples/daily_index_chart_price_example.py` -     
- ** **: PYKIS_API_METHODS.md  API  

## [0.1.13] - 2025-01-29

### 
- **   API **
  - **`get_hourly_conclusion`  **:    
    - API : `/uapi/domestic-stock/v1/quotations/inquire-time-itemconclusion` (TR: FHPST01060000)
    -    (HHMMSS , : "115959")
    -  :  , , ,   30  
  
  - ** `get_stock_ccnl`  **:  (30)  - **   **
    - API : `/uapi/domestic-stock/v1/quotations/inquire-ccnl` (TR: FHKST01010300)
    - ** **:  (`tday_rltv`)      
    -  `get_volume_power`      
    -  :  30 , , , ,  
    -           

- **Agent   **:    Agent     
  ```python
  #   
  hourly = agent.get_hourly_conclusion("005930", "143000")
  
  #    
  ccnl = agent.get_stock_ccnl("005930")
  strength = ccnl['output'][0]['tday_rltv']  # 123.50
  ```

### 
- **   **:      
- ** **: README.md, PYKIS_API_METHODS.md    

## [0.1.12] - 2025-06-29

### 
- **`get_pbar_tratio`  **
  - `get_pbar_tratio`  docstring, `tr_id`,   "/ "    .

## [0.1.11] - 2025-06-29

### 
- **  API   **
  - `Agent`   `get_program_trade_hourly_trend`  `ProgramTradeAPI`    .
  - `ProgramTradeAPI` `get_program_trade_hourly_trend`    `get_program_trade_by_stock`  .
  -       .

## [0.1.10] - 2025-06-29

### 
- **`is_holiday`   **: (, )    .   API          .

## [0.1.9] - 2025-06-29

### 
- **  **: `kis_devlp.yaml`    `.env`    .
  - `python-dotenv`   `.env`  API     .
  -   `pyyaml`   .

### 
- **`.env.example` **:       `.env.example`  .
- ** **: `.env`    `FileNotFoundError`     .

### 
- **YAML  **: `pykis/core/config.py`    YAML    .
- **`load_account_info` **: `pykis/stock/api.py`     `load_account_info`  .

## [0.1.8] - 2025-06-29

### 
- `pykis/program/api.py`:     deprecated  .

## [0.1.7] - 2025-06-29

### 
- **API    **
  -  API         .
  - `pykis/stock/program_trade.py`  deprecated  .
  - `pykis/stock/data.py`      .
- **  **
  -      .
  -     (`tests/unit/test_stock_data.py`, `tests/unit/test_stock_market.py`) .
- **`API_ENDPOINTS` **
  - `pykis/core/client.py` `API_ENDPOINTS` (alias)     .
- **Facade  **
  - `Agent`    API    .
  - `pykis/__init__.py`  `Agent`     Facade   .

### 
- **    **
  -     API   .
- ** **
  -           .

## [0.1.6] - 2025-06-28

### 
- **      **
  - `tests/test_agent_usage.py`: `get_market_rankings()` -> `get_price_rank()`, `get_stock_info()` -> `get_stock_opinion()`  . DataFrame    .
  - `tests/integration/test_agent_comprehensive.py`: `validate_api_response`  `output1`, `output2`    /   .
  - `tests/unit/test_auth.py`: `read_token`  `save_token`    mock  .
  - `tests/unit/test_client.py`: `test_make_request_daily_price` `tr_id` . `test_refresh_token` `requests.post` mock .
  - `tests/unit/test_program_trade.py`: `datetime` import       `pytest.raises` .

- **`pykis/core/agent.py` **
  - `StockMarketAPI` `Agent`   `__getattr__`    .

### 
- **    **
  -        .
  - mock     API  .

## [0.1.5] - 2025-06-26

### 
- **datetime import  **
  - `pykis/core/agent.py`: `import datetime` `from datetime import timedelta`  import  
  - `pykis/stock/api.py`: `import datetime` `from datetime import datetime` , `datetime.datetime.now()` → `datetime.now()` 
  - `pykis/stock/data.py`:  datetime import 
  -    import (`from datetime import datetime, timedelta`)  

- ** API        **
  -  API   : `FID_ETC_CLS_CODE=""` , `FID_COND_SCR_DIV_CODE` 
  - `get_minute_price`  API_ENDPOINTS  `MINUTE_CHART` → `MINUTE_PRICE` 
  - `fetch_minute_data`     : `output` → `output2`  
  -   "0900" → "090000" (HHMMSS) 
  - API       (`rt_cd == '0'`)
  -      : 8  240    

-  API   
  -    `condition.py`  (`tr_id="HHKST03900400"`)  
  - `pykis/stock/api.py` `get_condition_stocks`   `tr_id` 
  - `pykis/core/agent.py` `get_condition_stocks_dict`   `ConditionAPI` 
  - `examples/list_interest_groups.py` Agent   
  -    `user_id="unohee"`   
  - `rt_cd='1'` ("  ")    

-      
  - `StockAPI`  `get_holiday_info()`  `is_holiday()`  
  - Agent    :  API (`get_holiday_info`) +  (`is_holiday`)
  -     API    
  -    :        
  -   10     

### 
- **     **
  - `fetch_minute_data`  8 (09:00~15:30)    
  - SQLite DB      
  -  240     
  - : `stck_bsop_date`, `stck_cntg_hour`, `stck_prpr`, `stck_oprc`, `stck_hgpr`, `stck_lwpr`, `cntg_vol`, `acml_tr_pbmn`, `code`, `date`

- Facade   
  -  `ConditionAPI`    
  - Agent  `get_condition_stocks`  (`user_id`, `seq`, `tr_cont`) 
  -   Agent      API  
  -  Agent    

-   
  - `examples/pykis.ipynb`     
  -     API    (   )
  -      
  -      
  -      

### 
-  API  
  - `/uapi/domestic-stock/v1/quotations/chk-holiday`  
  - `tr_id="CTCA0903R"`    
  -  (`opnd_yn`)  
  -      

## [0.1.4] - 2024-06-22

### 
-   API   
  - `get_volume_power`     
  -  API   TR   (`/uapi/domestic-stock/v1/ranking/volume-power`, `FHPST01680000`)
  -  : " " → "" 
  -      (  API)

-   API 
  -        API 
  - `get_program_trade_daily_summary`:   
  - `get_program_trade_market_daily`:    API 
  -   

-   API 
  - `get_market_fluctuation`      API 
  - : `/uapi/domestic-stock/v1/ranking/fluctuation`, TR: `FHPST01700000`

-  API 
  -   
  - `client.py` `INQUIRE_PSBL_ORDER`  
  -   `get_total_evaluation`  

### 
-   
  - `get_pgm_trade`  `examples/program_trade_analysis.py` 
  - `ProgramTradeAnalyzer`    
  - API    

-    
  - `logger`   : `logger` → `logging` 
  -     : `get_condition_stocks_dict`  API  

- Strategy   
  - deprecated strategy  import    
  - `pykis/core/agent.py` strategy   
  - `tests/integration/test_strategy.py`  

### 
-    
  - 50      
  - , , ,  ,     
  -       
  -     

### 
-  `get_volume_power`  
-     API   
- Strategy      
-    API  

## [0.1.3] - 2024-06-19

### 
- ProgramTradeAPI     
  - `pykis/program/api.py`, `pykis/program/trade.py`, `pykis/stock/program_trade.py`   
  -  import `pykis.program.trade` 
  - deprecated    

### 
-  
  - `get_program_trade_summary` → `get_program_trade_by_stock` 
  -     
- `get_program_trade_by_stock`  API   
  - () API  
  -    

### 
- README.md 
  -      
  -       

## [0.1.2] - 2024-06-16

### 
-  `kis-agent` `pykis` 
-   
  - `src`  
  -   `pykis` 
-  
  - `KIS_Agent` → `Agent`
  - `KISClient` → `Client`

## [0.1.1] - 2024-06-15

### 
- Postman    
  - : , , ,  
  - :  ( ) API     
  - : , ,  
  - :  
  -  : //  

### 
-   
  -  API     
  -   
  -   
-     ,     ( / API           )

### 
- `market.py`  
  -  
  -    
  -   

### 
-  API   docstring 
  - , ,  
  -   
  -    

## [0.1.0] - 2025-06-11

### 
-  OpenAPI      
  - `core`: API , ,  
  - `account`:     
  - `stock`:     
  - `program`:    
  - `strategy`:    

### 
-      docstring 
  -  : , , ,  ,  
  -  : , ,  
  -  : , , , ,  

### 
- `program_trade.py`  
  - `get_program_trade_detail` → `get_program_trade_period_detail`
  - `get_program_trade_ratio` → `get_pgm_trade`

### 
- `scripts/convert_yaml_to_env.py`:    

### 
- API        
-     .gitignore 

### 
-   README.md  
- API     
-     

###  
- `program_trade.py`   `get_program_trade_summary`   
-  API     
-       