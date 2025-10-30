# Changelog

모든 주목할 만한 변경사항이 이 파일에 문서화됩니다.

## [1.3.1] - 2025-10-30

### 📚 API 응답 타입 완전 문서화

#### 🎯 주요 개선사항

**1. TypedDict 응답 모델 완전 문서화**
- **334개 API 엔드포인트** 응답 구조 추출 (`open-trading-api/examples_llm/` 분석)
- **106개 필드 추가** (기존 57개 → 163개 필드)
  - `StockPriceOutput`: 39 → **82 fields** (+43)
  - `DailyPriceItem`: 13 → **18 fields** (+5)
  - `StockInvestorOutput`: 13 → **27 fields** (+14)
  - `MinutePriceItem`: 8 → **14 fields** (+6)
  - `InquireBalanceRlzPlOutput`: 12 → **15 fields** (+3)
  - **NEW** `InquirePeriodTradeProfitOutput`: **35 fields** (신규 추가)

**2. 메서드 Docstring 완전 개선**
- **6개 주요 API** 메서드에 상세 응답 필드 문서 추가:
  - `get_stock_price()` - 주식 현재가 조회 (82개 필드 문서화)
  - `get_daily_price()` - 일별 시세 조회
  - `get_stock_investor()` - 투자자 매매 동향
  - `get_minute_price()` - 분봉 시세 조회
  - `inquire_balance_rlz_pl()` - 잔고 평가 및 실현 손익
  - `inquire_period_trade_profit()` - 기간별 매매 손익 (신규)

**3. 자동화 도구 개발**
- `extract_response_mappings.py` - 334개 예제 파일에서 COLUMN_MAPPING 추출
- `generate_complete_typeddict.py` - 완전한 TypedDict 모델 자동 생성
- `response_mappings.json` - 모든 API 응답 필드 매핑 (334 APIs, 288 categories)

**4. 개발자 경험 향상**
- IDE 자동완성 지원 강화 (163개 응답 필드)
- 타입 안전성 향상 (모든 필드에 한글 설명 포함)
- API 문서 접근성 개선 (docstring에 주요 필드 포함)

#### 📁 수정된 파일 (6개, +442줄)
- `pykis/responses/stock.py` - 향상된 stock 응답 타입
- `pykis/responses/account.py` - 향상된 account 응답 타입 + 신규 API
- `pykis/responses/__init__.py` - 새로운 응답 타입 export
- `pykis/stock/price_api.py` - 향상된 docstrings
- `pykis/stock/investor_api.py` - 향상된 docstrings
- `pykis/account/api.py` - 향상된 docstrings

#### 🐛 버그 수정
- `price_api.py:991` - 미사용 `retries` 파라미터 경고 해결 (`_retries`로 변경)

#### ✅ 검증 완료
- ✅ 248개 unit tests 통과 (breaking changes 없음)
- ✅ TypedDict `total=False` 일관성 유지
- ✅ 한국어 문서화 철학 유지 (API 필드명 1:1 매핑)

## [1.3.0] - 2025-10-24

### 🎯 파사드 패턴 완성 및 API 안정성 개선

#### 🔧 주요 수정사항

**1. 404 에러 API 처리**
- `inquire_index_price()` - 원본 KIS API 엔드포인트가 404를 반환하는 문제 해결
  - `inquire_index_timeprice()`로 내부 리다이렉트
  - **DeprecationWarning** 추가 (v2.0에서 제거 예정)
  - TODO 주석 명시

**2. TR_ID 수정**
- `get_index_timeprice()` - TR_ID를 `FHPUP02110200`로 수정
  - POSTMAN 테스트로 정상 작동 확인
  - KOSPI/KOSDAQ 시간별 지수 조회 정상화

**3. StockAPI Facade 완성 (31개 메서드 추가)**

Price API (21개):
- `inquire_index_price()`, `inquire_index_tickprice()`, `inquire_index_timeprice()`
- `inquire_index_category_price()`, `inquire_daily_overtimeprice()`, `inquire_elw_price()`
- `inquire_overtime_asking_price()`, `inquire_overtime_price()`, `inquire_vi_status()`
- `get_intraday_price()`, `get_stock_ccnl()`, `daily_credit_balance()`
- `disparity()`, `dividend_rate()`, `fluctuation()`, `foreign_institution_total()`
- `intstock_multprice()`, `market_cap()`, `market_time()`, `market_value()`
- `news_title()`, `profit_asset_index()`, `search_stock_info()`, `short_sale()`, `volume_rank()`

Market API (6개):
- `get_holiday_info()`, `is_holiday()`, `get_pbar_tratio()`
- `get_fluctuation_rank()`, `get_volume_power_rank()`, `get_volume_rank()`

**4. Agent 클래스 완성 (13개 메서드 추가)**

Price API (5개):
- `get_orderbook()` - 호가 정보 조회
- `inquire_price()` - 시세 조회 (추가 정보 포함)
- `get_stock_ccnl()` - 체결 조회
- `get_intraday_price()` - 당일 분봉 전체 데이터
- `get_index_minute_data()` - 업종 분봉 조회

Market API (7개):
- `get_market_fluctuation()` - 시장 변동성 정보
- `get_market_rankings()` - 거래량 기준 종목 순위
- `get_stock_info()` - 종목 기본 정보
- `get_fluctuation_rank()` - 등락률 순위
- `get_volume_power_rank()` - 체결강도 순위
- `get_volume_rank()` - 거래량 순위
- `get_pbar_tratio()` - PBR/PER 비율 순위

Investor API (1개):
- `get_frgnmem_pchs_trend()` - 외국인 매수 추이

### 📊 통계
- **StockAPI Facade**: 58개 메서드 (완성)
- **Agent Stock API**: 90개 메서드 (완성)
- **파사드 패턴**: 100% 구현 완료

### 🏗️ 아키텍처 개선
- Agent → StockAPI Facade → (StockPriceAPI | StockMarketAPI | StockInvestorAPI) 계층 구조 완성
- 모든 하위 API 메서드가 Facade와 Agent를 통해 접근 가능
- `__getattr__()` 동적 위임으로 향후 추가 메서드 자동 지원

### 🐛 버그 수정
- 404 에러 발생하는 `inquire_index_price()` 대체 메서드 제공
- `get_index_timeprice()` TR_ID 오류 수정
- StockAPI Facade에서 누락된 31개 메서드 추가
- Agent에서 누락된 13개 Stock API 메서드 추가

### ⚠️ Deprecation 경고
- `inquire_index_price()` - v2.0에서 제거 예정
  - 대안: `inquire_index_timeprice()` 또는 `get_index_timeprice()` 사용

---

## [1.2.0] - 2025-10-10

### 🚀 신규 API 추가 (31개)

#### 고우선순위 API (8개)
- **시간별 체결 조회**: `inquire_time_itemconclusion()` - 특정 시간 이후 체결 내역 조회
- **실시간 체결 조회**: `inquire_ccnl()` - 30건 체결 데이터 (체결강도 포함)
- **주식현재가 시세2**: `inquire_price_2()` - 상세 시세 정보
- **종목 기본정보**: `search_stock_info()` - 종목명, 시가총액, 상장주식수 등
- **뉴스 제목 조회**: `news_title()` - 종목 관련 뉴스
- **등락률 순위**: `fluctuation()` - 시장 등락률 상위 종목
- **거래량 순위**: `volume_rank()` - 거래량 상위 종목
- **시가총액 순위**: `market_cap()` - 시가총액 상위 종목

#### 중우선순위 API (5개)
- **외국인/기관 종합**: `foreign_institution_total()` - 매매동향 종합
- **신용잔고**: `daily_credit_balance()` - 일별 신용잔고 추이
- **공매도**: `short_sale()` - 공매도 상위 종목
- **ELW 현재가**: `inquire_elw_price()` - ELW 시세 조회
- **VI 발동 현황**: `inquire_vi_status()` - 변동성 완화장치 발동 현황

#### 시세조회 API (13개)
- **시간외 주가**: `inquire_daily_overtimeprice()`, `inquire_overtime_price()`, `inquire_overtime_asking_price()`
- **업종 지수**: `inquire_index_category_price()`, `inquire_index_tickprice()`, `inquire_index_timeprice()`
- **순위/지표**: `disparity()`, `dividend_rate()`, `profit_asset_index()`
- **복수종목**: `intstock_multprice()` - 한 번에 여러 종목 조회
- **서버 미지원 API**: `inquire_index_price()`, `market_time()`, `market_value()` - NotImplementedError 발생 및 대안 API 안내

#### 투자자동향 API (5개)
- **외국계 가집계**: `get_frgnmem_trade_estimate()` - 외국계 매매종목 가집계
- **회원사 동향**: `get_frgnmem_trade_trend()` - 실시간 매매동향
- **프로그램매매**: `get_investor_program_trade_today()` - 투자자별 프로그램매매
- **종목별 동향**: `get_investor_trade_by_stock_daily()` - 종목별 투자자 매매동향
- **추정가집계**: `get_investor_trend_estimate()` - 외국인/기관 추정가집계

### 🛠️ 시스템 개선
- **StockInvestorAPI 모듈 신규 생성**: 투자자 동향 API 분리 (`pykis/stock/investor_api.py`)
- **Agent 클래스 통합**: 모든 신규 API를 Agent에서 직접 호출 가능
- **명확한 에러 처리**: 서버 미지원 API는 NotImplementedError 발생 + 대안 API 제시
- **통합 테스트**: 실제 API 호출 테스트 20개 (100% 성공)

### 📋 테스트
- **유닛 테스트**: 31개 메서드 시그니처 검증 (100%)
- **통합 테스트**: 20개 실제 API 호출 테스트 (100%)
- **테스트 파일**:
  - `testing/test_all_new_apis_251010.py` - 메서드 존재 여부 검증
  - `tests/test_new_apis_integration_251010.py` - 실제 API 호출 검증

### 📊 API 통계
- **구현 완료**: 28개 API (실제 서버 지원)
- **서버 미지원**: 3개 API (명확한 에러 메시지 + 대안 제시)
- **성공률**: 100% (서버 미지원 API는 예상된 동작)

### 🔧 기술 부채 해소
- **보일러플레이트 자동화**: Task agent를 활용한 반복 작업 자동화
- **코드 품질**: 일관된 BaseAPI 패턴 적용
- **문서화**: 모든 메서드에 docstring 포함

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