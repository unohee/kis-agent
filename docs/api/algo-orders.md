# 알고리즘 주문 (TWAP / VWAP)

대량 주문을 한 번에 던지면 호가를 밀어 올려 체결가가 나빠진다. `kis-agent`의
알고리즘 주문은 부모 주문을 시간에 걸쳐 잘게 쪼개 집행한다.

## 빠른 시작

```python
from kis_agent import Agent

agent = Agent(app_key="...", app_secret="...", account_no="...", account_code="01")

# TWAP — 1,000주를 30분 동안 6회 균등 분할 매수
result = agent.twap_order("005930", "buy", quantity=1000, duration_minutes=30)
print(result.status, result.submitted_quantity)

# VWAP — 과거 5영업일 거래량 곡선에 비례해 2시간 동안 매수
result = agent.vwap_order(
    "005930", "buy", quantity=1000, duration_minutes=120, slices=12
)
print(result.notes[0])   # 거래량 프로파일: 5개 영업일 평균 (20260814~20260820)
```

!!! warning "블로킹 호출"
    `twap_order`/`vwap_order`는 `duration_minutes` 동안 **블로킹**된다.
    Ctrl+C로 중단하면 예외를 던지지 않고 그때까지 집행한 결과를 돌려준다.

## TWAP vs VWAP

|  | TWAP | VWAP |
|:---|:---|:---|
| 분할 기준 | 시간 균등 | 과거 거래량 비례 |
| 슬라이스 크기 | 모두 같음 | 거래 많은 시간대에 더 많이 |
| 사전 데이터 조회 | 없음 | 과거 N영업일 분봉 |
| 기본 집행시간 | 30분 | 60분 |

VWAP 프로파일은 **완료된 과거 세션**만 사용한다. 당일 부분 데이터는 아직 오지
않은 구간을 설명하지 못하고, 섞으면 스케줄이 오전으로 치우친다. 프로파일을
만들지 못하면 균등 분할로 내려가되 그 사유를 `result.notes`에 남긴다.

## 안전 가드

### 지정가 가드

```python
# 매수: 현재가가 70,000원을 넘는 슬라이스는 건너뛴다
result = agent.twap_order("005930", "buy", 1000, limit_price=70000)

# 벗어나면 아예 중단
result = agent.twap_order(
    "005930", "buy", 1000, limit_price=70000, on_price_breach="abort"
)
```

매도는 비교 방향이 반대다 — 현재가가 `limit_price` **미만**이면 스킵한다.
`limit_price`를 주면서 현재가 조회 경로가 없으면 `ValueError`로 즉시 거부한다.
살아 있는 주문에서 지정가가 조용히 무시되는 상황을 막기 위해서다.

### 정규장 제한

기본적으로 정규장(09:00–15:30, 평일) 밖 슬라이스는 스킵된다. 시간외 거래를
직접 다루려면 `restrict_to_session=False`.

### 연속 실패 중단

연속으로 `max_consecutive_failures`(기본 3)회 거부되면 남은 슬라이스를 취소하고
`status="aborted"`로 끝낸다. 중간에 한 번 성공하면 카운터는 리셋된다.

### dry-run

```python
result = agent.twap_order("005930", "buy", 1000, dry_run=True)
print(result.dry_run, result.status)   # True completed
```

`dry_run=True`는 주문 API를 **호출하지 않는다**. 스케줄 계산과 가드 평가는 그대로
수행하므로 집행 계획을 미리 볼 수 있다.

가드는 dry-run에서도 살아 있다. 장 마감 후에 돌리면 정규장 가드가 모든 슬라이스를
스킵해 `status`는 `completed`가 아니라 `partial`이 된다. 시간과 무관하게 분할
크기만 확인하려면 `restrict_to_session=False`를 함께 준다.

## 현금 / 신용 주문

```python
# 신용융자로 분할 매수 (기본 credit_type "21")
result = agent.twap_order("005930", "buy", 1000, funding="credit")

# 자기융자 + 대출일자 지정
result = agent.twap_order(
    "005930", "buy", 1000,
    funding="credit", credit_type="22", loan_dt="20260821",
)

# 신용이 거부되면 현금주문으로 폴백
result = agent.twap_order(
    "005930", "buy", 1000, funding="credit", credit_fallback_to_cash=True,
)
```

| 인자 | 기본값 | 설명 |
|:---|:---|:---|
| `funding` | `"cash"` | `"cash"` 현금주문 / `"credit"` 신용주문 |
| `credit_type` | 매수 `"21"`, 매도 `"11"` | 신용유형 코드 |
| `loan_dt` | `""` | 대출일자 (자기융자 `"22"` 매수용) |
| `credit_fallback_to_cash` | `False` | 신용 거부 시 현금 재시도 |

`credit_fallback_to_cash`는 기본이 꺼져 있다. 포지션의 자금 조달 방식을 말없이
바꾸는 것은 하면 안 되는 종류의 일이다. 폴백이 실제로 일어나면 해당 슬라이스
`message`에 신용 거부 사유와 함께 기록된다.

## 집행 원장 — 죽어도 남는 기록

자식 주문은 거래소가 접수를 확인한 **즉시** JSONL 원장에 기록되고 fsync됩니다.
프로세스가 어떻게 죽든(SIGKILL·절전·OOM·에이전트 타임아웃) 이미 나간 주문은
파일에 남습니다.

```python
result = agent.twap_order("005930", "buy", 1000)
print(result.run_id)        # 20260821-133000-005930-buy-3f9a2c
print(result.journal_path)  # ~/.kis-agent/executions/20260821/....jsonl
```

```bash
$ cat ~/.kis-agent/executions/20260821/20260821-133000-005930-buy-3f9a2c.jsonl
{"ts": "...", "runId": "...", "event": "start", "code": "005930", "totalQuantity": 1000, ...}
{"ts": "...", "runId": "...", "event": "slice", "index": 0, "quantity": 167, "status": "filled", "orderNo": "0000123456"}
{"ts": "...", "runId": "...", "event": "slice", "index": 1, "quantity": 167, "status": "filled", "orderNo": "0000123457"}
...
{"ts": "...", "runId": "...", "event": "end", "status": "completed", "submittedQuantity": 1000, ...}
```

| 인자 | 기본값 | 설명 |
|:---|:---|:---|
| `journal_dir` | `~/.kis-agent/executions` | 원장 위치. `KIS_EXECUTION_JOURNAL_DIR`로도 지정 |
| `journal_enabled` | `True` | 끄지 말 것 — 죽으면 주문번호 복구 경로가 사라진다 |

### 미완료 집행 가드

`end` 레코드가 없는 원장은 **주문이 이미 나간 채로 프로세스가 죽었다**는 서명입니다.
같은 종목에 그런 기록이 있으면 CLI는 새 집행을 거부합니다:

```bash
$ kis order twap 005930 --side buy --qty 1000 --yes
{
  "error": "005930에 완료되지 않은 집행 기록이 1건 있습니다. 이미 나간 주문을 확인한 뒤 진행하세요 (강행하려면 --ignore-incomplete).",
  "code": "IncompleteExecutionFound",
  "data": {"incompleteRuns": [{"runId": "...", "orderNumbers": ["0000123456"], "submittedQuantity": 167, "totalQuantity": 1000, ...}]}
}
```

이걸 보지 않고 같은 부모 주문을 다시 내는 것이 포지션이 조용히 두 배가 되는 경로입니다.
확인 후 강행하려면 `--ignore-incomplete`. dry-run은 거래소에 닿지 않으므로 가드 대상이 아닙니다.

Python API도 같은 보호를 받습니다 — CLI만 막고 문서화된 API를 열어두면 의미가 없습니다:

```python
from kis_agent.execution import IncompleteExecutionError, find_incomplete_runs

try:
    agent.twap_order("005930", "buy", 1000)
except IncompleteExecutionError as e:
    for run in e.runs:
        print(run.describe())   # 20260821-...: 005930 buy 167/1000주 접수 (주문번호 0000123456)
    # 대사한 뒤에만 끈다
    agent.twap_order("005930", "buy", 833, check_incomplete=False)
```

`find_incomplete_runs(code)`로 직접 조회할 수도 있습니다.

가드는 **당일** 원장만 봅니다. 정상 완료와 Ctrl+C는 원장을 닫으므로 걸리지 않고,
처리되지 않은 즉사만 걸립니다. 어제 죽은 실행은 오늘을 막지 않는데, KRX 당일 주문은
장 마감을 넘기지 못하는 데다 한 번의 크래시가 그 종목을 영구히 막으면 안 되기
때문입니다. 다만 **부분 체결된 포지션은 남으므로**, 크래시 이후에는 잔고를 확인하고
다음 주문 수량을 조정하세요.

원장 기록 실패는 주문을 중단시키지 않습니다 — 디스크가 찼다고 절반 집행된 부모 주문을
버리는 것이 더 나쁩니다. 그래서 진행 출력(stderr)에도 주문번호를 함께 싣습니다.

## 주문은 재전송되지 않는다

`KISClient`는 GET이 아닌 요청을 **절대 재시도하지 않습니다**. 타임아웃은 *응답*에
걸린 것이지 *동작*에 걸린 것이 아니라, 접수된 주문의 응답만 유실됐는데 같은 본문을
다시 보내면 중복 주문이 되기 때문입니다.

응답이 유실되면 슬라이스는 `failed` / `order_rejected`로 기록됩니다. **접수됐는데
실패로 보일 수 있다**는 뜻이므로, 그런 슬라이스가 있으면 `kis order list`나
`kis trades`로 실제 접수 여부를 확인하세요. 조회 API의 재시도는 그대로입니다.

## 결과 읽기

```python
result = agent.twap_order("005930", "buy", 1000)

result.status              # completed / partial / aborted / cancelled
result.submitted_quantity  # 실제 집행된 수량
result.unfilled_quantity   # 스킵·실패로 집행되지 못한 수량
result.notes               # 프로파일 출처, 중단 사유 등
result.to_dict()           # JSON 직렬화 가능한 dict

for s in result.slices:
    print(s.index, s.quantity, s.status, s.reason, s.order_no)
```

| `status` | 의미 |
|:---|:---|
| `completed` | 모든 슬라이스가 집행(또는 시뮬레이션)됨 |
| `partial` | 일부 슬라이스가 스킵되거나 실패 |
| `aborted` | 가드에 걸려 스케줄 도중 중단 |
| `cancelled` | 운영자가 Ctrl+C로 중단 |

| 슬라이스 `reason` | 의미 |
|:---|:---|
| `price_limit` | 지정가 가드 위반 |
| `outside_session` | 정규장 시간 밖 |
| `price_unavailable` | 가드 확인용 현재가 조회 실패 |
| `order_rejected` | 주문 API 거부 또는 예외 |
| `interrupted` | Ctrl+C |
| `upstream_abort` | 선행 슬라이스 문제로 미실행 |

스킵된 수량은 **뒤 슬라이스로 이월하지 않는다**. 이월하면 마지막 슬라이스가
비대해져 알고리즘의 존재 이유인 시장충격 완화가 무너지기 때문이다. 남은 수량은
`unfilled_quantity`로 보고하니 필요하면 다시 집행하면 된다.

## 진행 상황 관찰

```python
def on_slice(s):
    print(f"{s.index + 1}: {s.quantity}주 → {s.status}")

agent.twap_order("005930", "buy", 1000, progress=on_slice)
```

## 저수준 구성 요소

스케줄만 미리 계산하거나, 자체 주문 콜러블로 루프를 돌리고 싶다면:

```python
from datetime import datetime, timedelta
from kis_agent.execution import (
    AlgoExecutor,
    build_twap_schedule,
    build_vwap_schedule,
    fetch_volume_profile,
)

# 집행하지 않고 스케줄만 확인
schedule = build_twap_schedule(
    total_quantity=1000, slices=6,
    start=datetime.now(), duration=timedelta(minutes=30),
)
for s in schedule:
    print(s.scheduled_at, s.quantity)

# 거래량 프로파일 직접 조회
profile = fetch_volume_profile(agent, "005930", days=20)
print(profile.source_dates, profile.fallback_reason)

# 자체 주문 콜러블로 집행
executor = AlgoExecutor(order_func=my_order_func, price_func=my_price_func)
result = executor.run(schedule, code="005930", side="buy")
```

| 함수 | 역할 |
|:---|:---|
| `split_quantity(total, parts)` | 최대잔여법 균등 분할 (합계 보존) |
| `split_quantity_weighted(total, weights)` | 가중 분할 (합계 보존) |
| `build_twap_schedule(...)` | 시간 균등 스케줄 |
| `build_vwap_schedule(...)` | 거래량 가중 스케줄 |
| `fetch_volume_profile(agent, code, days)` | 과거 분봉 → 시간대별 거래량 |
| `AlgoExecutor.run(...)` | 스케줄 집행 + 가드 |

## 타이밍 정확도

슬라이스 대기는 벽시계를 반복해서 읽는 대신 **모노토닉 시계 기준 오프셋**으로
계산한다. 덕분에

- 집행 도중 NTP 보정이 들어와도 남은 슬라이스 간격이 늘거나 줄지 않고,
- 한 슬라이스의 주문 지연이 뒤 슬라이스로 누적되지 않는다.

실측(실계좌 dry-run, 20초 간격 3슬라이스)에서 예정 시각 대비 실제 제출 오차는
1.5~10ms였다.

## 주의사항

- 미체결 정정·취소는 하지 않는다. 기본 주문유형이 최유리지정가(`"03"`)인 이유다.
- VWAP 프로파일 조회는 영업일당 분봉 API를 4회 호출한다
  (`profile_days=5`면 20회).
- 국내주식 대상이다. 해외주식·선물옵션은 이번 범위에 없다.
