# PyKIS v1.4.0 마이그레이션 가이드

이 문서는 PyKIS v1.3.x에서 v1.4.0으로 업그레이드하는 사용자를 위한 가이드입니다.

## 개요

v1.4.0의 주요 변경사항:
1. **MCP 도구 통합**: 110+ 개별 도구 → 18개 통합 도구
2. **LOC 게이트**: 모든 소스 파일 1500줄 미만
3. **버그 수정**: MCP 도구 안정성 개선

> **Breaking Changes 없음**: 기존 Python API는 100% 하위 호환됩니다.

---

## MCP 도구 마이그레이션

### 기존 도구 → 통합 도구 매핑

#### 주식 시세 관련

| 기존 도구 | 통합 도구 | 파라미터 |
|----------|----------|---------|
| `get_stock_price` | `stock_quote` | `query_type="price"` |
| `get_stock_detail` | `stock_quote` | `query_type="detail"` |
| `get_orderbook` | `stock_quote` | `query_type="orderbook"` |
| `get_execution_info` | `stock_quote` | `query_type="execution"` |
| `get_time_execution` | `stock_quote` | `query_type="time_execution", hour="HHMMSS"` |

```python
# 기존
result = await stock_quote.call(code="005930")

# v1.4.0
result = await stock_quote.call(code="005930", query_type="price")
```

#### 차트 데이터

| 기존 도구 | 통합 도구 | 파라미터 |
|----------|----------|---------|
| `get_minute_chart` | `stock_chart` | `timeframe="minute"` |
| `get_daily_chart` | `stock_chart` | `timeframe="daily"` |
| `get_daily_30` | `stock_chart` | `timeframe="daily_30"` |
| `get_weekly_chart` | `stock_chart` | `timeframe="weekly"` |
| `get_monthly_chart` | `stock_chart` | `timeframe="monthly"` |

```python
# 기존
result = await get_daily_chart.call(code="005930", start_date="20250101")

# v1.4.0
result = await stock_chart.call(
    code="005930",
    timeframe="daily",
    start_date="20250101"
)
```

#### 지수 데이터

| 기존 도구 | 통합 도구 | 파라미터 |
|----------|----------|---------|
| `get_index_current` | `index_data` | `data_type="current"` |
| `get_index_daily` | `index_data` | `data_type="daily"` |
| `get_index_tick` | `index_data` | `data_type="tick"` |
| `get_index_time` | `index_data` | `data_type="time"` |
| `get_index_minute` | `index_data` | `data_type="minute"` |
| `get_sector_index` | `index_data` | `data_type="category", category="CODE"` |

```python
# 기존
result = await get_index_current.call(index_code="0001")

# v1.4.0
result = await index_data.call(index_code="0001", data_type="current")
```

#### 시장 순위

| 기존 도구 | 통합 도구 | 파라미터 |
|----------|----------|---------|
| `get_volume_rank` | `market_ranking` | `ranking_type="volume"` |
| `get_gainers_rank` | `market_ranking` | `ranking_type="gainers"` |
| `get_losers_rank` | `market_ranking` | `ranking_type="losers"` |
| `get_fluctuation_rank` | `market_ranking` | `ranking_type="fluctuation", sign="1/2/3"` |
| `get_volume_power_rank` | `market_ranking` | `ranking_type="volume_power"` |
| `get_market_status` | `market_ranking` | `ranking_type="market_status"` |

```python
# 기존
result = await get_volume_rank.call(market="KOSPI")

# v1.4.0
result = await market_ranking.call(ranking_type="volume", market="1")
```

#### 투자자 동향

| 기존 도구 | 통합 도구 | 파라미터 |
|----------|----------|---------|
| `get_stock_investor` | `investor_flow` | `query_type="stock", code="CODE"` |
| `get_market_investor_daily` | `investor_flow` | `query_type="market_daily"` |
| `get_market_investor_time` | `investor_flow` | `query_type="market_time"` |
| `get_foreign_trend` | `investor_flow` | `query_type="foreign_trend"` |
| `get_foreign_estimate` | `investor_flow` | `query_type="foreign_estimate"` |
| `get_foreign_trading` | `investor_flow` | `query_type="foreign_trading"` |

```python
# 기존
result = await get_stock_investor.call(code="005930")

# v1.4.0
result = await investor_flow.call(query_type="stock", code="005930")
```

#### 계좌 조회

| 기존 도구 | 통합 도구 | 파라미터 |
|----------|----------|---------|
| `get_balance` | `account_query` | `query_type="balance"` |
| `get_order_ability` | `account_query` | `query_type="order_ability", code, price` |
| `get_trades` | `account_query` | `query_type="trades", date` |
| `get_profit_loss` | `account_query` | `query_type="profit_loss"` |
| `get_period_profit` | `account_query` | `query_type="period_profit", start_date, end_date` |

```python
# 기존
result = await get_balance.call()

# v1.4.0
result = await account_query.call(query_type="balance")
```

#### 주문 실행/관리

| 기존 도구 | 통합 도구 | 파라미터 |
|----------|----------|---------|
| `buy_stock` | `order_execute` | `action="buy"` |
| `sell_stock` | `order_execute` | `action="sell"` |
| `modify_order` | `order_manage` | `action="modify"` |
| `cancel_order` | `order_manage` | `action="cancel"` |
| `reserve_order` | `order_manage` | `action="reserve"` |

```python
# 기존
result = await buy_stock.call(code="005930", quantity=10, price=70000)

# v1.4.0
result = await order_execute.call(
    action="buy",
    code="005930",
    quantity="10",
    price="70000"
)
```

---

## 응답 형식

모든 통합 도구는 일관된 응답 형식을 반환합니다:

```python
{
    "rt_cd": "0",           # 성공: "0", 실패: "1" 이상
    "msg_cd": "MCA00000",   # 메시지 코드
    "msg1": "정상 처리되었습니다", # 메시지 내용
    "output": { ... },      # 단일 결과
    # 또는
    "output1": [ ... ],     # 목록 결과 (헤더)
    "output2": [ ... ],     # 목록 결과 (데이터)
}
```

### 에러 처리

```python
result = await stock_quote.call(code="INVALID")

if result["rt_cd"] != "0":
    # 에러 메시지 확인
    error_msg = result.get("msg1") or f"rt_cd={result['rt_cd']}, msg_cd={result.get('msg_cd', '')}"
    print(f"Error: {error_msg}")
```

---

## Python API (변경 없음)

Python API는 하위 호환성을 유지합니다. 기존 코드 그대로 사용 가능:

```python
from pykis import Agent

agent = Agent()

# 이전과 동일하게 작동
price = agent.get_stock_price("005930")
balance = agent.get_account_balance()
```

---

## 새로운 도구 활용

### rate_limiter - Rate Limiter 관리

```python
# 상태 조회
status = await rate_limiter.call(action="status")

# 초기화
await rate_limiter.call(action="reset")

# 제한 설정
await rate_limiter.call(
    action="set_limits",
    requests_per_second=15,
    requests_per_minute=800
)

# 적응형 활성화/비활성화
await rate_limiter.call(action="set_adaptive", enable_adaptive=True)
```

### method_discovery - 메서드 탐색

```python
# 키워드 검색
methods = await method_discovery.call(action="search", query="investor")

# 전체 메서드 목록
all_methods = await method_discovery.call(action="list_all")

# 특정 메서드 사용법
usage = await method_discovery.call(action="usage", method_name="get_stock_price")
```

### data_management - 데이터 관리

```python
# 4일간 분봉 수집
await data_management.call(action="fetch_minute", code="005930")

# 지지/저항선 계산
levels = await data_management.call(
    action="support_resistance",
    code="005930",
    date="20260103"
)
```

---

## FAQ

### Q: 기존 MCP 설정을 그대로 사용할 수 있나요?

A: 네, 서버 설정은 동일합니다. `.mcp.json` 변경 없이 업그레이드 가능합니다.

### Q: 이전 도구 이름으로 호출하면 어떻게 되나요?

A: 이전 도구는 더 이상 존재하지 않습니다. 위의 매핑 테이블을 참조하여 통합 도구로 변경해주세요.

### Q: 파라미터 형식이 변경되었나요?

A: 대부분의 파라미터는 동일합니다. 추가된 `query_type`, `action`, `timeframe` 등의 선택 파라미터가 있습니다.

### Q: 성능 차이가 있나요?

A: 내부 구현은 동일하므로 성능 차이는 없습니다. 오히려 도구 선택 오버헤드가 감소합니다.

---

## 지원

문제가 발생하면:
1. GitHub Issues: https://github.com/unohee/pykis/issues
2. CHANGELOG.md: 상세 변경 내역 확인
