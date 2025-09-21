# PyKIS API Reference Guide

## 목차
1. [개요](#개요)
2. [설치 및 초기 설정](#설치-및-초기-설정)
3. [주요 클래스](#주요-클래스)
4. [API 메서드 레퍼런스](#api-메서드-레퍼런스)
5. [사용 예시](#사용-예시)
6. [에러 처리](#에러-처리)

---

## 개요

PyKIS는 한국투자증권 OpenAPI를 Python에서 쉽게 사용할 수 있도록 만든 라이브러리입니다. 실시간 시세 조회, 주문 처리, 계좌 관리, 프로그램 매매 등 다양한 기능을 제공합니다.

### 주요 특징
- 통합된 Agent 인터페이스
- 자동 토큰 관리
- Rate Limiting 지원
- 실시간 WebSocket 지원
- DataFrame 변환 지원
- 캐싱 기능

### 프로젝트 구조
```
pykis/
├── core/           # 핵심 모듈 (Agent, Client, Auth, Config)
├── stock/          # 주식 관련 API
├── account/        # 계좌 관련 API
├── program/        # 프로그램 매매 API
├── websocket/      # 실시간 WebSocket
└── utils/          # 유틸리티 함수
```

---

## 설치 및 초기 설정

### 설치
```bash
pip install pykis
```

### 환경 변수 설정 (.env 파일)
```env
# 한국투자증권 API 인증 정보
APP_KEY=your_app_key
APP_SECRET=your_app_secret
ACCOUNT_NO=your_account_number
ACCOUNT_CODE=01  # 계좌 상품코드

# API URL (실전/모의 선택)
BASE_URL=https://openapi.koreainvestment.com:9443  # 실전투자
# BASE_URL=https://openapivts.koreainvestment.com:29443  # 모의투자
```

---

## 주요 클래스

### Agent 클래스
모든 API 기능을 통합 제공하는 메인 인터페이스

#### 초기화
```python
from pykis import Agent

# 방법 1: 환경 변수 파일 사용
agent = Agent(env_path=".env")

# 방법 2: 직접 인증 정보 전달
agent = Agent(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    account_no="12345678",
    account_code="01",
    base_url="https://openapi.koreainvestment.com:9443"  # 실전
)

# 방법 3: Rate Limiter 설정과 함께 초기화
agent = Agent(
    app_key="YOUR_APP_KEY",
    app_secret="YOUR_APP_SECRET",
    account_no="12345678",
    account_code="01",
    enable_rate_limiter=True,
    rate_limiter_config={
        'requests_per_second': 20,
        'requests_per_minute': 1000,
        'min_interval_ms': 10,
        'burst_size': 15,
        'enable_adaptive': True
    }
)
```

### KisWebSocket 클래스
실시간 시세 데이터 수신을 위한 WebSocket 클라이언트

```python
# WebSocket 생성
ws = agent.websocket(
    stock_codes=["005930", "000660"],  # 구독할 종목
    purchase_prices={
        "005930": (70000, 100),  # 삼성전자: (매수가격, 수량)
        "000660": (150000, 50)   # SK하이닉스: (매수가격, 수량)
    },
    enable_index=True,            # 지수 실시간 구독
    enable_program_trading=True,  # 프로그램매매 구독
    enable_ask_bid=False          # 호가 실시간 구독
)

# WebSocket 실행
ws.run()
```

---

## API 메서드 레퍼런스

### 시세 조회 API

#### get_stock_price(code: str) -> Optional[Dict]
현재가 시세 조회

**Parameters:**
- `code` (str): 종목코드 (6자리)

**Returns:**
- Dict: 현재가 정보 (rt_cd, output 포함)
- None: 실패 시

**Example:**
```python
result = agent.get_stock_price("005930")
if result and result.get('rt_cd') == '0':
    price = result['output']['stck_prpr']
    print(f"현재가: {price:,}원")
```

#### get_daily_price(code: str, period: str = "D", org_adj_prc: str = "1") -> Optional[Dict]
일별 시세 조회

**Parameters:**
- `code` (str): 종목코드
- `period` (str): 기간구분 (D: 일, W: 주, M: 월, Y: 년)
- `org_adj_prc` (str): 수정주가 사용 여부 (0: 미사용, 1: 사용)

**Example:**
```python
daily = agent.get_daily_price("005930", period="D")
if daily and daily.get('rt_cd') == '0':
    for day in daily['output'][:5]:  # 최근 5일
        print(f"{day['stck_bsop_date']}: {day['stck_clpr']:,}원")
```

#### get_minute_price(code: str, hour: str = "153000") -> Optional[Dict]
당일 분봉 조회

**Parameters:**
- `code` (str): 종목코드
- `hour` (str): 조회 시간 (HHMMSS 형식)

**Example:**
```python
minutes = agent.get_minute_price("005930", "150000")
for minute in minutes['output'][:10]:  # 최근 10개 분봉
    print(f"{minute['stck_cntg_hour']}: {minute['stck_prpr']:,}원")
```

#### get_daily_minute_price(code: str, date: str, hour: str = "153000") -> Optional[Dict]
과거 일자 분봉 조회

**Parameters:**
- `code` (str): 종목코드
- `date` (str): 조회 날짜 (YYYYMMDD)
- `hour` (str): 조회 시간 (HHMMSS)

**Example:**
```python
past_minutes = agent.get_daily_minute_price("005930", "20240101", "150000")
```

#### get_orderbook_raw(code: str) -> Optional[Dict]
호가 정보 조회

**Parameters:**
- `code` (str): 종목코드

**Example:**
```python
orderbook = agent.get_orderbook_raw("005930")
if orderbook:
    print(f"매도호가1: {orderbook['output']['askp1']:,}원")
    print(f"매수호가1: {orderbook['output']['bidp1']:,}원")
```

### 거래원 및 투자자 정보

#### get_member(code: str) -> Optional[Dict]
거래원별 매매 현황

**Parameters:**
- `code` (str): 종목코드

**Example:**
```python
members = agent.get_member("005930")
if members and members.get('rt_cd') == '0':
    for member in members['output'][:5]:  # 상위 5개 거래원
        print(f"{member['mbcr_name']}: 매수 {member['seln_mbcr_rlim_val']:,}")
```

#### get_foreign_broker_net_buy(code: str, foreign_brokers=None, date: str = None) -> Optional[Dict]
외국계 증권사 순매수 현황

**Parameters:**
- `code` (str): 종목코드
- `foreign_brokers` (list, optional): 외국계 증권사 목록
- `date` (str, optional): 조회 날짜 (YYYYMMDD)

**Example:**
```python
foreign = agent.get_foreign_broker_net_buy("005930")
if foreign:
    print(f"외국계 순매수량: {foreign['net_buy_volume']:,}주")
```

#### get_stock_investor(code: str) -> Optional[Dict]
투자자별 매매 동향

**Parameters:**
- `code` (str): 종목코드

**Example:**
```python
investors = agent.get_stock_investor("005930")
if investors:
    print(f"외국인 순매수: {investors['output']['frgn_ntby_qty']:,}주")
    print(f"기관 순매수: {investors['output']['orgn_ntby_qty']:,}주")
```

### 프로그램 매매

#### get_program_trade_by_stock(code: str) -> Optional[Dict]
종목별 프로그램매매 추이

**Parameters:**
- `code` (str): 종목코드

**Example:**
```python
program = agent.get_program_trade_by_stock("005930")
if program and program.get('rt_cd') == '0':
    output = program['output']
    print(f"프로그램 매수: {output['program_buy_vol']:,}주")
    print(f"프로그램 매도: {output['program_sell_vol']:,}주")
```

#### get_program_trade_hourly_trend(code: str) -> Optional[Dict]
시간대별 프로그램매매 추이

**Example:**
```python
hourly = agent.get_program_trade_hourly_trend("005930")
for hour in hourly['output']:
    print(f"{hour['time']}: 순매수 {hour['net_buy']:,}")
```

### 계좌 관련 API

#### get_account_balance() -> Optional[Dict]
계좌 잔고 조회

**Returns:**
- Dict: 계좌 잔고 정보 (보유종목 목록 포함)

**Example:**
```python
balance = agent.get_account_balance()
if balance and balance.get('rt_cd') == '0':
    for stock in balance['output']:
        print(f"{stock['prdt_name']}: {stock['hldg_qty']}주")
        print(f"  평균단가: {stock['pchs_avg_pric']:,}원")
        print(f"  현재가: {stock['prpr']:,}원")
        print(f"  수익률: {stock['evlu_pfls_rt']}%")
```

#### get_possible_order_amount(code: str, price: str, order_type: str = "01") -> Optional[Dict]
주문 가능 금액/수량 조회

**Parameters:**
- `code` (str): 종목코드
- `price` (str): 주문 가격
- `order_type` (str): 주문 유형 (01: 현금매수, 02: 현금매도)

**Example:**
```python
possible = agent.get_possible_order_amount("005930", "70000", "01")
if possible:
    print(f"주문 가능 수량: {possible['output']['ord_psbl_qty']}주")
```

#### inquire_balance_rlz_pl() -> Optional[pd.DataFrame]
평가손익 조회 (DataFrame 반환)

**Example:**
```python
df = agent.inquire_balance_rlz_pl()
if df is not None:
    print(df[['종목명', '보유수량', '평가손익', '수익률']])
```

### 주문 관련 API

#### order_cash(pdno: str, qty: str, unpr: str, side: str, ord_dvsn: str = "01") -> Optional[Dict]
현금 주문 (매수/매도)

**Parameters:**
- `pdno` (str): 종목코드
- `qty` (str): 주문 수량
- `unpr` (str): 주문 단가
- `side` (str): 매수/매도 구분 (buy/sell)
- `ord_dvsn` (str): 주문 구분 (01: 시장가, 00: 지정가)

**Example:**
```python
# 지정가 매수
result = agent.order_cash("005930", "10", "70000", "buy", "00")
if result and result.get('rt_cd') == '0':
    print(f"주문번호: {result['output']['ODNO']}")

# 시장가 매도
result = agent.order_cash("005930", "5", "0", "sell", "01")
```

#### order_stock_cash(code: str, quantity: int, price: int = 0, order_type: str = "BUY", price_type: str = "LIMIT") -> Optional[Dict]
통합 현금 주문 메서드

**Parameters:**
- `code` (str): 종목코드
- `quantity` (int): 주문 수량
- `price` (int): 주문 가격 (시장가는 0)
- `order_type` (str): BUY(매수) / SELL(매도)
- `price_type` (str): LIMIT(지정가) / MARKET(시장가)

**Example:**
```python
# 지정가 매수
result = agent.order_stock_cash("005930", 10, 70000, "BUY", "LIMIT")

# 시장가 매도
result = agent.order_stock_cash("005930", 5, 0, "SELL", "MARKET")
```

#### order_rvsecncl(odno: str, orgn_odno: str, qty: str, side: str) -> Optional[Dict]
주문 정정/취소

**Parameters:**
- `odno` (str): 주문번호 (취소 시 원주문번호와 동일)
- `orgn_odno` (str): 원주문번호
- `qty` (str): 정정/취소 수량 (전량 취소 시 "0")
- `side` (str): 매수/매도 구분 (buy/sell)

**Example:**
```python
# 주문 취소 (전량)
result = agent.order_rvsecncl("12345678", "12345678", "0", "buy")

# 주문 정정 (수량 변경)
result = agent.order_rvsecncl("12345679", "12345678", "5", "buy")
```

#### order_credit_buy(pdno: str, qty: str, unpr: str, ord_dvsn: str = "01") -> Optional[Dict]
신용 매수

**Parameters:**
- `pdno` (str): 종목코드
- `qty` (str): 주문 수량
- `unpr` (str): 주문 단가
- `ord_dvsn` (str): 주문 구분 (01: 시장가, 00: 지정가)

**Example:**
```python
result = agent.order_credit_buy("005930", "10", "70000", "00")
```

#### order_credit_sell(pdno: str, qty: str, unpr: str, ord_dvsn: str = "01") -> Optional[Dict]
신용 매도

**Example:**
```python
result = agent.order_credit_sell("005930", "10", "75000", "00")
```

### 조건검색 및 시장 정보

#### get_condition_stocks(condition_nm: str = "", sort_by: str = "volume") -> Optional[List[Dict]]
조건검색식 종목 조회

**Parameters:**
- `condition_nm` (str): 조건명 필터
- `sort_by` (str): 정렬 기준 (volume, rate, price)

**Example:**
```python
stocks = agent.get_condition_stocks(condition_nm="급등", sort_by="rate")
if stocks:
    for stock in stocks[:10]:  # 상위 10개
        print(f"{stock['name']} ({stock['code']}): {stock['rate']:+.2f}%")
```

#### get_top_gainers() -> Optional[List[Dict]]
상승률 상위 종목

**Example:**
```python
gainers = agent.get_top_gainers()
if gainers:
    for stock in gainers[:5]:
        print(f"{stock['hts_kor_isnm']}: {stock['prdy_rate']:+.2f}%")
```

#### get_volume_power(volume: int = 0) -> Optional[Dict]
거래량 급증 종목

**Parameters:**
- `volume` (int): 최소 거래량 필터

**Example:**
```python
volume_stocks = agent.get_volume_power(volume=1000000)
for stock in volume_stocks['output']:
    print(f"{stock['hts_kor_isnm']}: 거래량 {stock['acml_vol']:,}")
```

#### get_holiday_info() -> Optional[Dict]
휴장일 정보 조회

**Example:**
```python
holidays = agent.get_holiday_info()
if holidays:
    for day in holidays['output']:
        print(f"{day['bass_dt']}: {day['wday_dvsn_nm']}")
```

#### is_holiday(date: str) -> Optional[bool]
특정일 휴장 여부 확인

**Parameters:**
- `date` (str): 확인할 날짜 (YYYYMMDD)

**Example:**
```python
if agent.is_holiday("20240101"):
    print("휴장일입니다")
else:
    print("개장일입니다")
```

### 분봉 데이터 및 기술적 분석

#### fetch_minute_data(code: str, date: Optional[str] = None, cache_dir: str = "cache") -> pd.DataFrame
분봉 데이터 수집 (캐시 지원)

**Parameters:**
- `code` (str): 종목코드
- `date` (str, optional): 조회 날짜
- `cache_dir` (str): 캐시 디렉토리

**Example:**
```python
df = agent.fetch_minute_data("005930", "20240101")
print(df.head())
```

#### calculate_support_resistance(code: str, date: str = None, period_days: int = 5) -> Optional[Dict]
지지/저항선 계산

**Parameters:**
- `code` (str): 종목코드
- `date` (str, optional): 기준 날짜
- `period_days` (int): 분석 기간 (일)

**Returns:**
- Dict: 지지선, 저항선, VWAP, 피봇 포인트 등

**Example:**
```python
levels = agent.calculate_support_resistance("005930", period_days=5)
if levels:
    print(f"주요 지지선: {levels['support_levels'][:3]}")
    print(f"주요 저항선: {levels['resistance_levels'][:3]}")
    print(f"VWAP: {levels['vwap']:,.0f}")
```

### Rate Limiter 관리

#### get_rate_limiter_status() -> Optional[Dict]
Rate Limiter 상태 조회

**Example:**
```python
status = agent.get_rate_limiter_status()
if status:
    print(f"현재 상태: {status['status']}")
    print(f"초당 요청: {status['current_rps']}/{status['max_rps']}")
```

#### set_rate_limits(requests_per_second: int = None, ...) -> bool
Rate Limit 설정 변경

**Parameters:**
- `requests_per_second` (int): 초당 최대 요청 수
- `requests_per_minute` (int): 분당 최대 요청 수
- `min_interval_ms` (int): 최소 요청 간격
- `burst_size` (int): 버스트 크기

**Example:**
```python
agent.set_rate_limits(
    requests_per_second=10,
    requests_per_minute=500,
    min_interval_ms=50
)
```

#### reset_rate_limiter()
Rate Limiter 초기화

**Example:**
```python
agent.reset_rate_limiter()
```

### 유틸리티 메서드

#### get_all_methods(show_details: bool = False, category: str = None) -> Dict
사용 가능한 모든 메서드 조회

**Parameters:**
- `show_details` (bool): 상세 정보 표시 여부
- `category` (str): 카테고리 필터 (stock, account, program, utility)

**Example:**
```python
# 모든 메서드 조회
methods = agent.get_all_methods()
for category, method_list in methods.items():
    print(f"{category}: {len(method_list)}개")

# 특정 카테고리만
stock_methods = agent.get_all_methods(category="stock")
```

#### search_methods(keyword: str) -> List[Dict]
메서드 검색

**Parameters:**
- `keyword` (str): 검색 키워드

**Example:**
```python
results = agent.search_methods("order")
for method in results:
    print(f"{method['name']}: {method['description']}")
```

#### show_method_usage(method_name: str) -> None
메서드 사용법 출력

**Parameters:**
- `method_name` (str): 메서드명

**Example:**
```python
agent.show_method_usage("get_stock_price")
```

---

## 사용 예시

### 예시 1: 기본 시세 조회 및 주문
```python
from pykis import Agent

# Agent 초기화
agent = Agent(env_path=".env")

# 1. 현재가 조회
price_info = agent.get_stock_price("005930")
current_price = int(price_info['output']['stck_prpr'])
print(f"삼성전자 현재가: {current_price:,}원")

# 2. 주문 가능 수량 확인
possible = agent.get_possible_order_amount("005930", str(current_price))
possible_qty = int(possible['output']['ord_psbl_qty'])
print(f"주문 가능 수량: {possible_qty}주")

# 3. 매수 주문 (지정가)
if possible_qty > 0:
    order_result = agent.order_stock_cash(
        code="005930",
        quantity=1,
        price=current_price,
        order_type="BUY",
        price_type="LIMIT"
    )
    if order_result and order_result.get('rt_cd') == '0':
        print(f"주문 성공! 주문번호: {order_result['output']['ODNO']}")

# 4. 계좌 잔고 확인
balance = agent.get_account_balance()
if balance:
    for stock in balance['output']:
        if stock['pdno'] == "005930":
            print(f"보유수량: {stock['hldg_qty']}주")
            print(f"평가손익: {stock['evlu_pfls_amt']:,}원")
```

### 예시 2: 조건검색 종목 매매
```python
# 급등주 조회
hot_stocks = agent.get_condition_stocks(condition_nm="급등", sort_by="rate")

for stock in hot_stocks[:3]:  # 상위 3개 종목
    code = stock['code']
    name = stock['name']
    rate = stock['rate']

    print(f"\n{name} ({code}): {rate:+.2f}%")

    # 상세 시세 조회
    detail = agent.get_stock_price(code)
    if detail:
        price = int(detail['output']['stck_prpr'])
        volume = int(detail['output']['acml_vol'])

        # 거래량이 100만주 이상이면 매수 검토
        if volume > 1000000:
            print(f"  현재가: {price:,}원, 거래량: {volume:,}주")

            # 외국인 매매 동향 확인
            investor = agent.get_stock_investor(code)
            if investor:
                foreign_net = int(investor['output']['frgn_ntby_qty'])
                if foreign_net > 0:
                    print(f"  외국인 순매수: {foreign_net:,}주")
```

### 예시 3: 실시간 WebSocket 모니터링
```python
# 관심 종목 실시간 모니터링
ws = agent.websocket(
    stock_codes=["005930", "000660", "035720"],
    purchase_prices={
        "005930": (70000, 100),   # 삼성전자
        "000660": (150000, 50),    # SK하이닉스
        "035720": (500000, 10)     # 카카오
    },
    enable_index=True,
    enable_program_trading=True
)

# 콜백 함수 설정 (선택사항)
def on_price_update(data):
    print(f"가격 업데이트: {data}")

ws.on_message = on_price_update

# WebSocket 실행
try:
    ws.run()
except KeyboardInterrupt:
    print("실시간 모니터링 종료")
```

### 예시 4: 기술적 분석 기반 자동매매
```python
import time
from datetime import datetime

def auto_trading_strategy(agent, code, target_profit=3.0):
    """
    지지/저항선 기반 자동매매 전략

    Args:
        agent: PyKIS Agent 객체
        code: 종목코드
        target_profit: 목표 수익률 (%)
    """

    # 지지/저항선 계산
    levels = agent.calculate_support_resistance(code, period_days=5)
    if not levels:
        print("기술적 분석 실패")
        return

    support = levels['support_levels'][0] if levels['support_levels'] else 0
    resistance = levels['resistance_levels'][0] if levels['resistance_levels'] else 0
    vwap = levels['vwap']

    print(f"지지선: {support:,.0f}, 저항선: {resistance:,.0f}, VWAP: {vwap:,.0f}")

    # 현재가 조회
    price_info = agent.get_stock_price(code)
    current_price = int(price_info['output']['stck_prpr'])

    # 매수 조건: 현재가가 지지선 근처이고 VWAP보다 낮을 때
    if support > 0 and current_price <= support * 1.01 and current_price < vwap:
        print(f"매수 신호 발생! 현재가: {current_price:,}")

        # 매수 주문
        result = agent.order_stock_cash(
            code=code,
            quantity=10,
            price=current_price,
            order_type="BUY",
            price_type="LIMIT"
        )

        if result and result.get('rt_cd') == '0':
            buy_price = current_price
            order_no = result['output']['ODNO']
            print(f"매수 완료! 주문번호: {order_no}")

            # 목표가 및 손절가 설정
            target_price = int(buy_price * (1 + target_profit/100))
            stop_loss = int(buy_price * 0.97)  # -3% 손절

            # 매도 모니터링
            while True:
                time.sleep(5)  # 5초마다 체크

                price_info = agent.get_stock_price(code)
                current_price = int(price_info['output']['stck_prpr'])
                profit_rate = (current_price - buy_price) / buy_price * 100

                print(f"현재가: {current_price:,} (수익률: {profit_rate:+.2f}%)")

                # 익절 또는 손절 조건
                if current_price >= target_price or current_price <= stop_loss:
                    result = agent.order_stock_cash(
                        code=code,
                        quantity=10,
                        price=0,
                        order_type="SELL",
                        price_type="MARKET"
                    )

                    if result and result.get('rt_cd') == '0':
                        print(f"매도 완료! 최종 수익률: {profit_rate:+.2f}%")
                    break

# 전략 실행
auto_trading_strategy(agent, "005930", target_profit=2.0)
```

### 예시 5: 포트폴리오 분석 및 리밸런싱
```python
def portfolio_analysis(agent):
    """포트폴리오 분석 및 리밸런싱 제안"""

    # 계좌 잔고 조회
    balance = agent.get_account_balance()
    if not balance or balance.get('rt_cd') != '0':
        print("잔고 조회 실패")
        return

    portfolio = []
    total_value = 0

    # 포트폴리오 구성
    for stock in balance['output']:
        if int(stock['hldg_qty']) > 0:
            code = stock['pdno']
            name = stock['prdt_name']
            qty = int(stock['hldg_qty'])
            current_price = int(stock['prpr'])
            avg_price = float(stock['pchs_avg_pric'])
            value = qty * current_price
            profit_rate = float(stock['evlu_pfls_rt'])

            portfolio.append({
                'code': code,
                'name': name,
                'qty': qty,
                'current_price': current_price,
                'avg_price': avg_price,
                'value': value,
                'profit_rate': profit_rate
            })
            total_value += value

    # 포트폴리오 분석 출력
    print("=" * 60)
    print("포트폴리오 분석 보고서")
    print("=" * 60)
    print(f"총 평가금액: {total_value:,}원")
    print(f"보유 종목수: {len(portfolio)}개\n")

    # 종목별 비중 및 성과
    for stock in sorted(portfolio, key=lambda x: x['value'], reverse=True):
        weight = stock['value'] / total_value * 100
        print(f"{stock['name']}")
        print(f"  비중: {weight:.1f}%")
        print(f"  수익률: {stock['profit_rate']:+.2f}%")
        print(f"  평가금액: {stock['value']:,}원")

        # 리밸런싱 제안
        if weight > 30:
            print(f"  ⚠️ 비중 과다 - 일부 매도 권장")
        elif stock['profit_rate'] < -10:
            print(f"  ⚠️ 손실 과다 - 손절 검토")
        elif stock['profit_rate'] > 20:
            print(f"  ✅ 목표 수익 달성 - 일부 익절 검토")
        print()

    # 섹터별 분산 분석 (예시)
    print("\n리밸런싱 제안:")
    print("1. 단일 종목 비중이 30%를 넘지 않도록 조정")
    print("2. -10% 이상 손실 종목은 손절 검토")
    print("3. +20% 이상 수익 종목은 일부 익절로 현금 확보")

# 포트폴리오 분석 실행
portfolio_analysis(agent)
```

---

## 에러 처리

### 일반적인 에러 코드
```python
def handle_api_response(response):
    """API 응답 처리 헬퍼 함수"""
    if response is None:
        print("API 호출 실패: 응답 없음")
        return False

    rt_cd = response.get('rt_cd')
    msg1 = response.get('msg1', '')

    if rt_cd == '0':
        return True  # 성공
    else:
        error_messages = {
            '1': '시스템 점검',
            '2': '인증 실패',
            '3': '요청 한도 초과',
            '4': '잘못된 파라미터',
            '5': '권한 없음'
        }

        error_type = error_messages.get(rt_cd, '알 수 없는 오류')
        print(f"API 오류 [{rt_cd}]: {error_type} - {msg1}")
        return False

# 사용 예시
result = agent.get_stock_price("005930")
if handle_api_response(result):
    # 정상 처리
    price = result['output']['stck_prpr']
    print(f"현재가: {price}")
```

### Rate Limit 처리
```python
try:
    # 대량 API 호출
    for code in stock_list:
        result = agent.get_stock_price(code)
        # 처리...

except Exception as e:
    if "rate limit" in str(e).lower():
        print("API 호출 한도 초과. 잠시 후 재시도...")
        time.sleep(1)
        # 재시도 로직
```

### 토큰 만료 처리
```python
# Agent는 자동으로 토큰을 갱신하지만, 수동 처리가 필요한 경우:
from pykis.core.auth import auth, read_token

def ensure_valid_token(config):
    """토큰 유효성 확인 및 갱신"""
    token = read_token()

    if token is None or token.get('expires_at', 0) < time.time():
        print("토큰 갱신 중...")
        auth(config=config)
        return read_token()

    return token
```

---

## 주의사항

1. **API 호출 제한**
   - 초당 20회, 분당 1000회 제한
   - Rate Limiter를 활용하여 자동 조절

2. **토큰 관리**
   - 토큰은 24시간 유효
   - Agent가 자동으로 갱신 처리

3. **주문 관련**
   - 실전/모의 구분 필수
   - 시장가 주문 시 price는 "0" 설정
   - 주문 수량과 가격은 문자열로 전달

4. **데이터 타입**
   - API 응답은 기본적으로 Dict 형태
   - 일부 메서드는 DataFrame 반환 (inquire_balance_rlz_pl 등)
   - 금액/수량 필드는 문자열로 반환되므로 int() 변환 필요

5. **에러 처리**
   - None 반환 시 실패로 간주
   - rt_cd == '0'일 때만 성공
   - msg1 필드에 상세 오류 메시지 포함

---

## 추가 리소스

- [한국투자증권 OpenAPI 공식 문서](https://apiportal.koreainvestment.com)
- [PyKIS GitHub Repository](https://github.com/your-repo/pykis)
- [문의 및 지원](mailto:support@example.com)

---

*본 문서는 PyKIS v0.1.22 기준으로 작성되었습니다.*