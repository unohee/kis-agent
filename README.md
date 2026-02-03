# PyKIS

한국투자증권 OpenAPI Python 래퍼 - Korea Investment & Securities Trading API Client

**🚀 NEW: NXT(넥스트) 시장 완벽 지원!** - KOSPI/KOSDAQ과 함께 모든 국내 주식시장 커버
**🌏 NEW: 해외주식 거래 지원!** - 미국/일본/중국/홍콩/베트남 9개 거래소 완벽 지원

## ✨ 주요 특징

- **🏎️ 고성능**: 지능형 캐싱으로 API 호출 80-95% 감소
- **🛡️ 안정성**: 실측 기반 Rate Limiting (18 RPS / 900 RPM)
- **📊 실시간**: WebSocket을 통한 실시간 데이터 스트리밍
- **📈 국내시장**: KOSPI, KOSDAQ, NXT 시장 완벽 지원
- **🌏 해외시장**: 미국, 일본, 중국, 홍콩, 베트남 9개 거래소 지원
- **🔧 편의성**: Excel 거래 보고서 자동 생성
- **🤖 자동화**: CI/CD 파이프라인과 자동 테스트 (232개 테스트)
- **🎯 타입 안정성**: 57개 TypedDict 응답 모델, 176개 메서드 100% 타입힌팅
- **📚 명확한 문서**: 한국투자증권 API 공식 문서와 용어 일치 (디버깅 최적화)     

[![CI/CD](https://github.com/Intrect-io/pykis/workflows/PyKIS%20CI/CD%20Pipeline/badge.svg)](https://github.com/Intrect-io/pykis/actions)
[![Tests](https://img.shields.io/badge/tests-232%20passed-brightgreen)](https://github.com/Intrect-io/pykis)
[![Coverage](https://img.shields.io/badge/coverage-52%25-orange)](https://github.com/Intrect-io/pykis)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![NXT](https://img.shields.io/badge/NXT--green)](https://www.nextrade.co.kr/)
[![Rate Limiting](https://img.shields.io/badge/rate%20limiting-18%20RPS%2F900%20RPM-blue)](https://github.com/Intrect-io/pykis)

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
daily = agent.inquire_daily_itemchartprice("035720", start_date="20250101", end_date="20251231")  # 일봉 (최대 100건)
orderbook = agent.get_orderbook("NXT")   # NXT

# 📊 장기 일봉 데이터 조회 (100건 제한 자동 우회) - NEW!
# 페이지네이션 자동 처리로 전체 기간 데이터 수집
result = agent.get_daily_price_all(
    code="005930",          # 삼성전자
    start_date="20200102",  # 2020년 1월 2일
    end_date="20201230",    # 2020년 12월 30일
    period="D",             # 일봉 (W:주봉, M:월봉도 가능)
    org_adj_prc="1"         # 수정주가 사용
)
print(f"총 {len(result['output2'])}건 수집")  # 248건 (100건 제한 우회!)
print(f"API 호출: {result['_pagination_info']['total_calls']}회")  # 3회

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

## 🌏 해외주식 거래

```python
# 해외주식 시세 조회 (미국, 일본, 중국, 홍콩, 베트남)
apple = agent.overseas.get_price(excd="NAS", symb="AAPL")
print(f"AAPL 현재가: ${apple['output']['last']}")

# 차트 데이터 조회
tesla_daily = agent.overseas.get_daily_price(excd="NAS", symb="TSLA", start="20240101")
tesla_minute = agent.overseas.get_minute_price(excd="NYS", symb="TSLA", interval=5)

# 호가 조회
orderbook = agent.overseas.get_orderbook(excd="NYS", symb="MSFT")

# 해외주식 잔고 조회
balance = agent.overseas.get_balance()
usd_balance = agent.overseas.get_balance(excd="NAS")  # 특정 거래소만

# 매수 주문 (지정가)
result = agent.overseas.buy_order(
    excd="NAS",      # 거래소: NASDAQ
    symb="AAPL",     # 종목: Apple
    qty="10",        # 수량
    price="150.00"   # 가격
)

# 매수 주문 (시장가)
result = agent.overseas.buy_order(
    excd="NAS", symb="TSLA",
    qty="5", price="0",  # 시장가
    order_type="34"      # 시장가 주문
)

# 매도 주문
result = agent.overseas.sell_order(
    excd="NYS", symb="MSFT",
    qty="20", price="350.00"
)

# 주문 정정
modify_result = agent.overseas.modify_order(
    excd="NAS",
    order_no="original_order_number",
    qty="15",        # 변경 수량
    price="155.00"   # 변경 가격
)

# 주문 취소
cancel_result = agent.overseas.cancel_order(
    excd="NAS",
    order_no="order_to_cancel"
)

# 시장 순위 조회
volume_ranking = agent.overseas.get_volume_ranking(excd="NAS")  # 거래량 상위
price_ranking = agent.overseas.get_price_change_ranking(excd="NYS", sort_type="상승")

# 지원 거래소 목록
exchanges = agent.overseas.get_supported_exchanges()
# ['NAS', 'NYS', 'AMS', 'HKS', 'TSE', 'SHS', 'SZS', 'HSX', 'HNX']
```

**지원 거래소:**
- 🇺🇸 미국: NAS (NASDAQ), NYS (NYSE), AMS (AMEX)
- 🇯🇵 일본: TSE (도쿄증권거래소)
- 🇨🇳 중국: SHS (상해), SZS (심천)
- 🇭🇰 홍콩: HKS (홍콩거래소)
- 🇻🇳 베트남: HSX (호치민), HNX (하노이)

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

## 🛠️ 개발 도구 및 코드 품질

PyKIS는 현대적인 Python 개발 도구를 사용하여 높은 코드 품질을 유지합니다:

### 린팅 및 포맷팅
- **Ruff**: 초고속 통합 린터 및 포맷터 (Black, Flake8, isort 통합)
- **Black**: 코드 스타일 포맷터
- **isort**: import 정렬
- **Flake8**: 코드 스타일 체커
- **MyPy**: 타입 체커

### CI/CD 파이프라인
- **GitHub Actions**: 자동화된 테스트 및 배포
- **Python 3.8-3.12**: 5개 버전 동시 테스트
- **자동 보안 스캔**: Trivy 보안 취약점 검사
- **자동 배포**: PyPI 패키지 자동 배포

### 로컬 개발 환경 설정
```bash
# 개발 의존성 설치
pip install -e ".[dev]"

# 코드 린팅 및 포맷팅
ruff check pykis tests
ruff format pykis tests
black pykis tests
isort pykis tests

# 타입 체크
mypy pykis

# 테스트 실행
pytest tests/ -v --cov=pykis
```

## 🎯 타입 안정성 및 문서화 철학

### TypedDict 응답 모델

PyKIS는 모든 API 응답에 대한 명시적 타입 정의를 제공합니다:

```python
from pykis.responses.stock import StockPriceResponse
from pykis.responses.account import AccountBalanceResponse

def get_stock_price(code: str) -> Optional[StockPriceResponse]:
    """주식 현재가 조회

    Args:
        code: 종목코드 6자리 (예: "005930")

    Returns:
        StockPriceResponse: 현재가 정보
            - output.stck_prpr: 주식 현재가
            - output.prdy_vrss: 전일 대비
            - output.acml_vol: 누적 거래량
    """
    ...
```

**제공되는 응답 타입** (57개):
- **주식 시세**: `StockPriceResponse`, `OrderbookResponse`, `DailyPriceResponse` 등 20개
- **계좌 정보**: `AccountBalanceResponse`, `PossibleOrderResponse` 등 18개
- **주문 처리**: `OrderCashResponse`, `OrderRvsecnclResponse` 등 19개

### 한국어 Docstring 철학

**PyKIS는 의도적으로 한국어 docstring을 사용합니다.**

#### 이유:
1. **API 공식 문서와 용어 일치**
   ```python
   # 한국투자증권 API 응답 필드
   {
       "stck_prpr": "70000",   # 주식 현재가
       "prdy_vrss": "1000",    # 전일 대비
       "prdy_ctrt": "1.45"     # 전일 대비율
   }

   # PyKIS docstring - 공식 문서 용어 그대로 사용
   """
   Returns:
       - output.stck_prpr: 주식 현재가  ← API 문서 그대로!
       - output.prdy_vrss: 전일 대비   ← 직접 매칭 가능
   """
   ```

2. **디버깅 효율성**
   - API 에러 메시지: 한글 (`"주문가능수량이 부족합니다"`)
   - PyKIS docstring: 한글 → **즉시 매칭 가능**
   - 공식 문서 대조 시간 단축

3. **주 사용자층 최적화**
   - 타겟 유저: 한국 개발자
   - 한국투자증권 API: 국내 전용
   - 실용성 > 국제 표준

#### 국제화 정책:
> 영문 번역이 필요하다면 커뮤니티 기여를 환영합니다.
> 오픈소스로 공개 시 i18n은 커뮤니티가 자연스럽게 해결할 것으로 기대합니다.

### IDE 자동완성 지원

타입힌팅 덕분에 모든 주요 IDE에서 완벽한 자동완성을 지원합니다:

```python
# VS Code, PyCharm, Cursor 등에서 자동완성
response = agent.get_stock_price("005930")
if response:
    price = response['output']['stck_prpr']  # ← 자동완성!
    #                           ^
    #                           |- stck_prpr
    #                           |- prdy_vrss
    #                           |- prdy_ctrt
    #                           |- acml_vol
    #                           |- ...
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