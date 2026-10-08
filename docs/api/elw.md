# ELW API

`agent.elw` 네임스페이스로 ELW(주식워런트증권) 시세·순위를 조회합니다. 내부적으로 `ElwAPI` Facade가
`ElwPriceAPI`(시세·추이)와 `ElwRankingAPI`(순위)에 위임합니다.

!!! warning "실전투자 전용"
    ELW API는 모의투자를 지원하지 않습니다. 모의투자 환경에서 호출하면 HTTP 요청 전에
    `PaperTradingNotSupportedError`가 발생합니다.

## 빠른 예제

```python
from kis_agent import Agent

agent = Agent()

# 기초자산별 ELW 시세
price = agent.elw.get_elw_udrl_asset_price("005930")

# 민감도(델타·감마 등) 추이 — 일별
greeks = agent.elw.get_elw_sensitivity_trend_daily("57LA24")

# 거래량 순위
rank = agent.elw.get_elw_volume_rank()
```

CLI에서는 `kis query elw <메서드> [인자]`로 같은 메서드를 직접 호출할 수 있습니다.

```bash
kis query elw get_elw_volume_rank
```

## 시세·추이 (`elw/v1/quotations/*`)

| 메서드 | 설명 |
|:---|:---|
| `agent.elw.get_elw_compare_stocks(code)` | ELW 비교대상종목조회 [국내주식-183] |
| `agent.elw.get_elw_cond_search()` | ELW 종목검색 [국내주식-166] |
| `agent.elw.get_elw_expiration_stocks()` | ELW 만기예정/만기종목 [국내주식-184] |
| `agent.elw.get_elw_indicator_trend_ccnl(code)` | ELW 투자지표추이(체결) [국내주식-172] |
| `agent.elw.get_elw_indicator_trend_daily(code)` | ELW 투자지표추이(일별) [국내주식-173] |
| `agent.elw.get_elw_indicator_trend_minute(code)` | ELW 투자지표추이(분별) [국내주식-174] |
| `agent.elw.get_elw_lp_trade_trend(code)` | ELW LP매매추이 [국내주식-182] |
| `agent.elw.get_elw_newly_listed()` | ELW 신규상장종목 [국내주식-181] |
| `agent.elw.get_elw_sensitivity_trend_ccnl(code)` | ELW 민감도 추이(체결) [국내주식-175] |
| `agent.elw.get_elw_sensitivity_trend_daily(code)` | ELW 민감도 추이(일별) [국내주식-176] |
| `agent.elw.get_elw_udrl_asset_list()` | ELW 기초자산 목록조회 [국내주식-185] |
| `agent.elw.get_elw_udrl_asset_price(underlying)` | ELW 기초자산별 종목시세 [국내주식-186] |
| `agent.elw.get_elw_volatility_trend_ccnl(code)` | ELW 변동성추이(체결) [국내주식-177] |
| `agent.elw.get_elw_volatility_trend_daily(code)` | ELW 변동성 추이(일별) [국내주식-178] |
| `agent.elw.get_elw_volatility_trend_minute(code)` | ELW 변동성 추이(분별) [국내주식-179] |
| `agent.elw.get_elw_volatility_trend_tick(code)` | ELW 변동성 추이(틱) [국내주식-180] |

## 순위 (`elw/v1/ranking/*`)

| 메서드 | 설명 |
|:---|:---|
| `agent.elw.get_elw_indicator_rank()` | ELW 지표순위 [국내주식-169] |
| `agent.elw.get_elw_quick_change_rank()` | ELW 당일급변종목 [국내주식-171] |
| `agent.elw.get_elw_sensitivity_rank()` | ELW 민감도 순위 [국내주식-170] |
| `agent.elw.get_elw_updown_rate_rank()` | ELW 상승률순위 [국내주식-167] |
| `agent.elw.get_elw_volume_rank()` | ELW 거래량순위 [국내주식-168] |

## 실시간

ELW 체결·호가·예상체결은 웹소켓으로 구독합니다 (실전 전용).

```python
ws.subscribe_elw("57LA24", with_orderbook=True, with_expected=True)
# ['H0EWCNT0_57LA24', 'H0EWASP0_57LA24', 'H0EWANC0_57LA24']
```

`agent.stock.inquire_elw_price(code)`(ELW 현재가, `domestic-stock` 경로)는 기존대로 `agent.stock`에 있습니다.
