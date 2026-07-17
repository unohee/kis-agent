# KIS-Agent

한국투자증권 OpenAPI Python 래퍼 - Korea Investment & Securities Trading API Client

```bash
pip install kis-agent
```

[![PyPI version](https://badge.fury.io/py/kis-agent.svg)](https://pypi.org/project/kis-agent/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/kis-agent.svg)](https://pypi.org/project/kis-agent/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-526CFE?logo=materialformkdocs)](https://unohee.github.io/kis-agent/)

**📖 공식 문서:** **[unohee.github.io/kis-agent](https://unohee.github.io/kis-agent/)** — 설치, 빠른 시작, CLI · Python API 레퍼런스, LLM Agent · MCP 연동, 아키텍처 가이드.

## CLI

`pip install kis-agent` 하면 `kis` 명령이 바로 설치됩니다.

```bash
kis price 005930                    # 삼성전자 현재가
kis price 005930 --daily --days 5   # 일별 시세 5일

kis overseas NAS AAPL               # AAPL 시세
kis overseas NAS AAPL --detail      # PER/PBR/시총 포함

kis balance --holdings              # 계좌 잔고 + 보유종목
kis orderbook 005930                # 호가 10호가
kis futures 101S03                  # 선물 시세

kis trades                          # 당일 체결내역
kis trades --from 7d --pretty       # 최근 7일 (사람 읽기용)
kis trades --from 30d --sell        # 최근 30일 매도만
kis trades --from 3m --profit       # 기간별 실현손익

kis query stock get_stock_price code=005930  # API 직접 호출
kis schema Stock                    # 타입 스키마 (LLM introspection)
```

- JSON 출력 (LLM 파싱 최적화), `--pretty`로 사람 읽기용
- 한투 필드명 자동 변환: `stck_prpr` → `currentPrice`, `prdy_ctrt` → `changeRate`
- 휴장일/장외 시간 자동 감지 — 직전 영업일 기준 데이터 안내

## 주요 특징

- **CLI 도구**: 설치 즉시 터미널에서 시세 조회
- **LLM Agent 연동**: JSON 출력 + 스키마 탐색으로 AI 에이전트 도구로 활용
- **고성능**: 지능형 캐싱으로 API 호출 80-95% 감소
- **안정성**: 실측 기반 Rate Limiting (18 RPS / 900 RPM)
- **실시간**: WebSocket을 통한 실시간 데이터 스트리밍
- **국내시장**: KOSPI, KOSDAQ, NXT(넥스트) 시장 지원
- **해외시장**: 미국, 일본, 중국, 홍콩, 베트남 9개 거래소 지원
- **선물옵션**: 국내/해외 선물옵션 거래 지원
- **타입 안정성**: 96개 TypedDict 응답 모델, 100% 타입힌팅

## 설치

```bash
pip install kis-agent
```

WebSocket, aiohttp, openpyxl은 기본 의존성에 포함되어 별도 설치가 불필요합니다.

## 사전 준비

1. [한국투자증권 API 포털](https://apiportal.koreainvestment.com)에서 API 신청
2. APP_KEY와 APP_SECRET 발급
3. 계좌번호(CANO)와 계좌상품코드(ACNT_PRDT_CD) 확인
4. `.env` 파일 설정 (`.env.example`를 복사하여 사용):

```bash
KIS_APP_KEY=발급받은_앱키
KIS_APP_SECRET=발급받은_시크릿
KIS_ACCOUNT_NO=계좌번호
KIS_ACCOUNT_CODE=01                # 선택 (기본 "01" = 주식, "03" = 선물옵션)
KIS_PAPER=                          # 선택 (1이면 모의투자 — URL·TR_ID 자동 적용)
KIS_BASE_URL=                       # 선택 (KIS_PAPER=1이면 불필요)
```

### 모의투자

`paper=True`로 Agent를 만들면 모의투자 URL과 모의투자 전용 TR_ID가 자동 적용됩니다.
모의투자 APP KEY/SECRET/계좌번호는 실전과 별도로 발급받아야 합니다.

```python
agent = Agent(
    app_key=os.environ["KIS_APP_KEY"],
    app_secret=os.environ["KIS_APP_SECRET"],
    account_no=os.environ["KIS_ACCOUNT_NO"],
    account_code="01",
    paper=True,          # 또는 .env에 KIS_PAPER=1
)
```

CLI는 `.env`의 `KIS_PAPER=1`만 설정하면 됩니다:

```bash
KIS_PAPER=1 kis balance
```

> **모의투자 미지원 API**: KIS는 전체 336개 API 중 43개만 모의투자로 제공합니다.
> 해외선물옵션·장내채권·순위/투자자동향·재무 등은 모의투자에서 쓸 수 없습니다.
> 미지원 API를 모의투자로 호출하면 `PaperTradingNotSupportedError`가 발생합니다.
> 지원 목록은 `kis_agent/core/tr_mapping.py`의 `REAL_TO_PAPER_TR`를 참고하세요.

> **v1.8.0 Breaking change**: 환경변수 이름이 `KIS_*` prefix로 통일되었습니다.
> 이전 별칭(`MY_APP`, `MY_SEC`, `KIS_SECRET`, `MY_ACCT_STOCK`, `MY_PROD`, `PROD_URL`,
> `VPS_URL`, `MY_AGENT`)은 더 이상 인식되지 않습니다. 사용 중인 `.env`를
> 다음과 같이 마이그레이션하세요:
>
> | 이전 이름 | 새 이름 |
> | --- | --- |
> | `MY_APP` | `KIS_APP_KEY` |
> | `MY_SEC` / `KIS_SECRET` | `KIS_APP_SECRET` |
> | `MY_ACCT_STOCK` | `KIS_ACCOUNT_NO` |
> | `MY_PROD` | `KIS_ACCOUNT_CODE` |
> | `PROD_URL` | `KIS_BASE_URL` |
> | `VPS_URL` | `KIS_VPS_URL` |
> | `MY_AGENT` | `KIS_USER_AGENT` |

## Python API

### 빠른 시작

```python
from kis_agent import Agent
import os

agent = Agent(
    app_key=os.environ['KIS_APP_KEY'],
    app_secret=os.environ['KIS_APP_SECRET'],
    account_no=os.environ['KIS_ACCOUNT_NO'],
    account_code=os.environ.get('KIS_ACCOUNT_CODE', '01'),
)

# 주식 현재가 조회
price = agent.get_stock_price("005930")  # 삼성전자
print(f"현재가: {price['output']['stck_prpr']}원")

# 계좌 잔고 조회
balance = agent.get_account_balance()

# 일봉 데이터 조회
daily = agent.inquire_daily_itemchartprice(
    "005930",
    start_date="20250101",
    end_date="20251231"
)
```

### 국내 주식 거래

```python
# 현금 매수 (지정가)
result = agent.order_stock_cash("buy", "005930", "00", "1", "70000")

# 현금 매수 (시장가)
result = agent.order_stock_cash("buy", "005930", "03", "1", "0")

# 주문 가능 수량 조회
inquiry = agent.inquire_order_psbl("005930", "70000")
print(f"주문가능수량: {inquiry['output']['max_buy_qty']}")

# 주문 정정/취소
result = agent.order_rvsecncl(org_order_no, qty, price, order_type, cncl_type)
```

### 해외 주식 거래

```python
# 시세 조회
apple = agent.overseas.get_price(excd="NAS", symb="AAPL")
print(f"AAPL 현재가: ${apple['output']['last']}")

# 일봉/분봉
tesla_daily = agent.overseas.get_daily_price(excd="NAS", symb="TSLA")
tesla_minute = agent.overseas.get_minute_price(excd="NYS", symb="TSLA", interval=5)

# 매수/매도 주문
result = agent.overseas.buy_order(excd="NAS", symb="AAPL", qty="10", price="150.00")
result = agent.overseas.sell_order(excd="NYS", symb="MSFT", qty="20", price="350.00")

# 정정/취소
agent.overseas.modify_order(excd="NAS", order_no="...", qty="15", price="155.00")
agent.overseas.cancel_order(excd="NAS", order_no="...")
```

**지원 거래소:** NAS (NASDAQ), NYS (NYSE), AMS (AMEX), TSE (도쿄), SHS (상해), SZS (심천), HKS (홍콩), HSX (호치민), HNX (하노이)

### 선물/옵션 거래

```python
# 국내 선물
futures_price = agent.futures.get_price("101S03")
result = agent.futures.buy_order(code="101S03", qty=1, price=350.00)

# 해외 선물
overseas_futures = agent.overseas_futures.get_price(excd="CME", symb="ESH5")

# 잔고
futures_balance = agent.futures.get_balance()
```

### 실시간 데이터 (WebSocket)

```python
ws_client = agent.websocket(
    stock_codes=["005930", "035420"],
    enable_index=True,
    enable_program_trading=True,
    enable_ask_bid=True
)

import asyncio
asyncio.run(ws_client.start())
```

### 분석 기능

```python
investor_trend = agent.get_stock_investor("005930")     # 투자자별 매매동향
program_trade = agent.get_program_trade_by_stock("005930", "20250101")  # 프로그램 매매
member_trade = agent.get_stock_member("005930")          # 증권사별 매매동향
support_resistance = agent.calculate_support_resistance("005930")       # 지지/저항선
```

### 장기 데이터 조회

API의 100건 제한을 자동으로 우회하여 전체 기간 데이터 수집:

```python
result = agent.get_daily_price_all(
    code="005930",
    start_date="20200102",
    end_date="20201230",
    period="D",
    org_adj_prc="1"
)
print(f"총 {len(result['output2'])}건 수집")  # 248건 (100건 제한 우회!)
print(f"API 호출: {result['_pagination_info']['total_calls']}회")
```

## 성능

- **캐시 적중률**: 80-95% (API 호출 대폭 감소)
- **Rate Limiting**: 18 RPS / 900 RPM (실측 안정 기준)
- **응답 시간**: 평균 50ms 이하 (캐시 적중 시)
- **동시 연결**: 멀티스레드 안전성 보장

## 개발

```bash
# 개발 의존성 설치
pip install -e ".[dev]"

# 린팅
ruff check kis_agent tests
ruff format kis_agent tests

# 테스트
pytest tests/ -v --cov=kis_agent
```

## API 레퍼런스

### 계좌
- `get_account_balance()` / `inquire_order_psbl()` / `inquire_credit_order_psbl()`

### 주문
- `order_stock_cash()` / `order_stock_credit()` / `order_rvsecncl()` / `inquire_psbl_rvsecncl()`

### 시세
- `get_stock_price()` / `get_daily_price()` / `get_minute_price()` / `get_orderbook()`

### 분석
- `get_stock_investor()` / `get_stock_member()` / `get_program_trade_by_stock()` / `calculate_support_resistance()`

### 해외주식 (`agent.overseas.*`)
- `get_price()` / `get_daily_price()` / `get_balance()` / `buy_order()` / `sell_order()`

### 선물옵션 (`agent.futures.*`)
- `get_price()` / `get_balance()` / `buy_order()` / `sell_order()`

### CLI (`kis`)
- `kis price <code>` / `kis balance` / `kis orderbook <code>` / `kis overseas <excd> <symb>` / `kis futures <code>` / `kis query <domain> <method>` / `kis schema [type]`

## 라이센스

MIT License

## 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다.

## 링크

- [PyPI Package](https://pypi.org/project/kis-agent/)
- [한국투자증권 API 포털](https://apiportal.koreainvestment.com)
- [GitHub Issues](https://github.com/Intrect-io/kis-agent/issues)
