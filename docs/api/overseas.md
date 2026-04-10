# 해외 주식 API

`agent.overseas` 네임스페이스를 통해 접근합니다. 내부적으로 `OverseasStockAPI` Facade가 `OverseasPriceAPI`, `OverseasAccountAPI`, `OverseasOrderAPI`, `OverseasRankingAPI`에 위임합니다.

## 지원 거래소

| 코드 | 거래소 | 국가 | 통화 |
|:---|:---|:---|:---|
| `NAS` | NASDAQ | 미국 | USD |
| `NYS` | NYSE | 미국 | USD |
| `AMS` | AMEX | 미국 | USD |
| `TSE` | 도쿄증권거래소 | 일본 | JPY |
| `SHS` | 상해증권거래소 | 중국 | CNY |
| `SZS` | 심천증권거래소 | 중국 | CNY |
| `HKS` | 홍콩증권거래소 | 홍콩 | HKD |
| `HSX` | 호치민증권거래소 | 베트남 | VND |
| `HNX` | 하노이증권거래소 | 베트남 | VND |

## 시세 조회

```python
# 현재가
price = agent.overseas.get_price(excd="NAS", symb="AAPL")

# 상세 정보 (52주 최고/최저, PER, EPS 등)
detail = agent.overseas.get_price_detail(excd="NAS", symb="AAPL")

# 일봉 (gubn: "0"=일, "1"=주, "2"=월)
daily = agent.overseas.get_daily_price(excd="NAS", symb="TSLA", gubn="0")

# 분봉 (nmin: "1"=1분, "5"=5분, "30"=30분, "60"=60분)
minute = agent.overseas.get_minute_price(excd="NAS", symb="AAPL", nmin="5")

# 호가
orderbook = agent.overseas.get_orderbook(excd="NAS", symb="AAPL")

# 체결정보
ccnl = agent.overseas.get_ccnl(excd="NAS", symb="AAPL")

# 종목 기본정보 (prdt_type_cd: 512=미국, 513=홍콩, 514=상해, 515=심천, 516=일본, 517=베트남)
info = agent.overseas.get_stock_info(prdt_type_cd="512", pdno="NAS.AAPL")

# 종목 검색
results = agent.overseas.search_symbol(excd="NAS", symb="APPL")

# 업종/테마
theme = agent.overseas.get_industry_theme(excd="NAS")

# 뉴스
news = agent.overseas.get_news_title(excd="NAS", symb="AAPL")

# 휴장일 확인
holiday = agent.overseas.get_holiday(trad_dt="20260410")
```

## 계좌 조회

```python
# 잔고 (거래소별/통화별 필터 가능)
balance = agent.overseas.get_balance()
balance = agent.overseas.get_balance(ovrs_excg_cd="NASD")

# 체결기준 현재잔고
present = agent.overseas.get_present_balance(wcrc_frcr_dvsn_cd="02")

# 주문체결내역
history = agent.overseas.get_order_history()

# 미체결 주문
unfilled = agent.overseas.get_unfilled_orders()

# 매수가능금액
buyable = agent.overseas.get_buyable_amount(ovrs_excg_cd="NASD", item_cd="AAPL")

# 기간손익
profit = agent.overseas.get_period_profit(
    inqr_strt_dt="20260101", inqr_end_dt="20260331"
)

# 예약주문 내역
reserve = agent.overseas.get_reserve_order_list()

# 외화증거금
margin = agent.overseas.get_foreign_margin(crcy_cd="USD")
```

## 주문

```python
# 매수 (ord_dvsn: "00"=지정가, "31"=MOO, "32"=LOO, "33"=MOC, "34"=LOC)
result = agent.overseas.buy_order(
    ovrs_excg_cd="NASD", pdno="AAPL", qty=10, price=150.00
)

# 매도
result = agent.overseas.sell_order(
    ovrs_excg_cd="NYSE", pdno="MSFT", qty=20, price=350.00
)

# 정정
agent.overseas.modify_order(
    ovrs_excg_cd="NASD", pdno="AAPL",
    orgn_odno="0001234567", qty=15, price=155.00
)

# 취소
agent.overseas.cancel_order(
    ovrs_excg_cd="NASD", pdno="AAPL",
    orgn_odno="0001234567", qty=10
)

# 예약주문
agent.overseas.reserve_order(
    ovrs_excg_cd="NASD", pdno="AAPL",
    sll_buy_dvsn_cd="02", qty=10, price=150.00
)

# 예약주문 정정/취소
agent.overseas.modify_reserve_order(rsvn_ord_seq="001", qty=15, price=155.00)
agent.overseas.cancel_reserve_order(rsvn_ord_seq="001")
```

!!! note "거래소 코드 주의"
    주문 시에는 조회용 코드(NAS)가 아닌 주문용 코드(NASD)를 사용해야 합니다. 매핑: NAS→NASD, NYS→NYSE, AMS→AMEX, HKS→SEHK, TSE→TKSE

## 랭킹 조회

```python
# 거래량 순위
vol = agent.overseas.trade_volume_ranking(excd="NAS")

# 거래대금 순위
amt = agent.overseas.trade_amount_ranking(excd="NAS")

# 거래증가율 순위
growth = agent.overseas.trade_growth_ranking(excd="NAS")

# 거래회전율 순위
turnover = agent.overseas.trade_turnover_ranking(excd="NAS")

# 시가총액 순위
mktcap = agent.overseas.market_cap_ranking(excd="NAS")

# 상승률/하락률 순위 (gubn: "1"=상승, "2"=하락)
change = agent.overseas.price_change_ranking(excd="NAS", gubn="1")

# 가격급등락
surge = agent.overseas.price_fluctuation_ranking(excd="NAS", gubn="0")

# 신고가/신저가 (gubn: "0"=신저, "1"=신고)
hl = agent.overseas.new_high_low_ranking(excd="NAS", gubn="1")

# 매수체결강도 상위
power = agent.overseas.volume_power_ranking(excd="NAS")

# 거래량급증
vol_surge = agent.overseas.volume_surge_ranking(excd="NAS")
```

## 유틸리티

```python
# 지원 거래소 목록
exchanges = agent.overseas.get_supported_exchanges()

# 거래소 코드 유효성
valid = agent.overseas.is_valid_exchange("NAS")  # True

# 거래소 정보
info = agent.overseas.get_exchange_info("NAS")
# {"name": "NASDAQ", "country": "미국", "currency": "USD"}
```

## API 메서드 요약

### 시세

| 메서드 | 설명 |
|:---|:---|
| `get_price(excd, symb)` | 현재가 |
| `get_price_detail(excd, symb)` | 상세 (PER/EPS/52주) |
| `get_daily_price(excd, symb, gubn)` | 일/주/월봉 |
| `get_minute_price(excd, symb, nmin)` | 분봉 |
| `get_orderbook(excd, symb)` | 호가 |
| `get_ccnl(excd, symb)` | 체결정보 |
| `get_stock_info(prdt_type_cd, pdno)` | 종목정보 |
| `search_symbol(excd, symb)` | 종목 검색 |
| `get_news_title(excd, symb)` | 뉴스 |
| `get_holiday(trad_dt)` | 휴장일 |

### 계좌

| 메서드 | 설명 |
|:---|:---|
| `get_balance()` | 잔고 |
| `get_present_balance()` | 체결기준 잔고 |
| `get_order_history()` | 주문체결내역 |
| `get_unfilled_orders()` | 미체결 주문 |
| `get_buyable_amount(excd)` | 매수가능금액 |
| `get_period_profit(...)` | 기간손익 |
| `get_reserve_order_list()` | 예약주문 내역 |
| `get_foreign_margin(crcy_cd)` | 외화증거금 |

### 주문

| 메서드 | 설명 |
|:---|:---|
| `buy_order(excd, pdno, qty, price)` | 매수 |
| `sell_order(excd, pdno, qty, price)` | 매도 |
| `modify_order(excd, pdno, orgn_odno, qty, price)` | 정정 |
| `cancel_order(excd, pdno, orgn_odno, qty)` | 취소 |
| `reserve_order(...)` | 예약주문 |

### 랭킹

| 메서드 | 설명 |
|:---|:---|
| `trade_volume_ranking(excd)` | 거래량 순위 |
| `trade_amount_ranking(excd)` | 거래대금 순위 |
| `market_cap_ranking(excd)` | 시가총액 순위 |
| `price_change_ranking(excd, gubn)` | 상승/하락률 순위 |
| `new_high_low_ranking(excd, gubn)` | 신고/신저가 |
| `volume_surge_ranking(excd)` | 거래량 급증 |
