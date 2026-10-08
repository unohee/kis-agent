# ETF/ETN API

ETF/ETN 시세는 `agent.stock`으로 호출합니다 (`StockAPI`가 `StockEtfAPI`로 자동 위임). 모의투자는 지원하지 않습니다.

| 메서드 | 설명 |
|:---|:---|
| `agent.stock.get_etf_component_stock_price(code)` | ETF 구성종목시세 [국내주식-073] |
| `agent.stock.get_etf_nav_comparison_daily_trend(code)` | NAV 비교추이(일) [v1_국내주식-071] |
| `agent.stock.get_etf_nav_comparison_time_trend(code)` | NAV 비교추이(분) [v1_국내주식-070] |
| `agent.stock.get_etf_nav_comparison_trend(code)` | NAV 비교추이(종목) [v1_국내주식-069] |
| `agent.stock.get_etf_price(code)` | ETF/ETN 현재가 [v1_국내주식-068] |

```python
etf = agent.stock.get_etf_price("069500")
components = agent.stock.get_etf_component_stock_price("069500")
nav_daily = agent.stock.get_etf_nav_comparison_daily_trend("069500")
```

실시간 NAV 추이는 웹소켓으로 받습니다.

```python
ws.subscribe_etf_nav("069500")   # H0STNAV0
```
