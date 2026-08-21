# CLI 사용법

`pip install kis-agent` 하면 `kis` 명령이 바로 설치됩니다. Node.js 불필요.

## 환경 변수

CLI는 `.env` 파일 또는 환경 변수에서 인증 정보를 읽습니다:

```bash
KIS_APP_KEY=...
KIS_APP_SECRET=...
KIS_ACCOUNT_NO=...
KIS_ACCOUNT_CODE=01
KIS_PAPER=1           # 선택 — 모의투자로 실행
```

`KIS_PAPER=1`을 넣으면 모든 `kis` 명령이 모의투자 서버로 나갑니다. 모의투자 자격증명은 실전과 별도로 발급받아야 합니다 ([모의투자 가이드](../getting-started/paper-trading.md)).

```bash
KIS_PAPER=1 kis balance     # 일회성으로 모의투자 실행
```

---

## 서브커맨드 목록

### price — 국내 주식 현재가

```bash
kis price 005930                    # 삼성전자 현재가
kis price 삼성전자                   # 종목명으로도 검색 가능
kis price 005930 --daily            # 일별 시세 포함
kis price 005930 --daily --days 5   # 최근 5일
kis price 005930 --period W         # 주봉
kis price 005930 --pretty           # 사람 읽기용 포맷
```

| 옵션 | 설명 |
|:---|:---|
| `code` | 종목코드 또는 종목명 (필수) |
| `--daily` | 일별 시세 포함 |
| `--period` | 기간 구분: `D`(일), `W`(주), `M`(월) — 기본 `D` |
| `--days` | 조회 일수 — 기본 30 |
| `--pretty` | 사람 읽기용 포맷 |

### balance — 계좌 잔고

```bash
kis balance                         # 잔고 요약
kis balance --holdings              # 보유종목 상세 포함
kis balance --pretty
```

| 옵션 | 설명 |
|:---|:---|
| `--holdings` | 보유종목 상세 |
| `--pretty` | 사람 읽기용 포맷 |

### orderbook — 호가 조회

```bash
kis orderbook 005930                # 10호가 (매수/매도)
kis orderbook 삼성전자 --pretty
```

### overseas — 해외주식 시세

```bash
kis overseas NAS AAPL               # AAPL 현재가
kis overseas NAS AAPL --detail      # PER/PBR/52주 고저/시총 포함
kis overseas NAS TSLA --daily       # 일별 시세 포함
kis overseas NYS MSFT --daily --days 10
```

| 옵션 | 설명 |
|:---|:---|
| `excd` | 거래소 코드 (NAS, NYS, AMS, TSE, HKS 등) |
| `symb` | 종목 심볼 (AAPL, TSLA 등) |
| `--detail` | PER/PBR/시총 등 상세 정보 |
| `--daily` | 일별 시세 포함 |
| `--days` | 조회 일수 — 기본 30 |
| `--pretty` | 사람 읽기용 포맷 |

### futures — 선물옵션 시세

```bash
kis futures 101S03                  # 국내 선물 시세
kis futures CLM26 --overseas        # 해외 선물
kis futures ESH5 --overseas --orderbook  # 해외 선물 + 호가
kis futures OPT123 --overseas --option   # 해외 옵션 (그릭스 포함)
kis futures 101W09 --night          # 야간 선물 시세
kis futures 101W09 --night --balance    # 야간 잔고
kis futures 101W09 --night --ccnl       # 야간 체결내역
```

| 옵션 | 설명 |
|:---|:---|
| `code` | 종목코드 (필수) |
| `--overseas` | 해외선물 모드 |
| `--option` | 해외옵션 (그릭스 포함) |
| `--orderbook` | 호가 포함 (해외선물) |
| `--night` | 야간선물 모드 (18:00~05:00) |
| `--balance` | 야간 잔고 (`--night`와 함께) |
| `--ccnl` | 야간 체결내역 (`--night`와 함께) |
| `--pretty` | 사람 읽기용 포맷 |

### trades — 거래내역/체결/손익

```bash
kis trades                          # 당일 체결내역
kis trades --from 7d                # 최근 7일
kis trades --from 30d --sell        # 최근 30일 매도만
kis trades --from 7d --buy          # 매수만
kis trades --from 7d --filled       # 체결 완료건만
kis trades --from 7d --stock 005930 # 특정 종목만
kis trades --from 3m --profit       # 기간별 실현손익 (종목별)
kis trades --from 3m --profit --daily-profit  # 일별 손익 합산
kis trades --from 7d --limit 10     # 최대 10건
kis trades --from 7d --pretty       # 사람 읽기용
```

| 옵션 | 설명 |
|:---|:---|
| `--from` | 시작일: `today`, `7d`, `30d`, `3m`, `1y`, `2026-03-01`, `20260301` |
| `--to` | 종료일 — 기본 오늘 |
| `--buy` | 매수만 필터 |
| `--sell` | 매도만 필터 |
| `--stock` | 종목코드 필터 |
| `--filled` | 체결 완료건만 |
| `--limit` | 최대 건수 (0=전체) |
| `--profit` | 기간별 실현손익 모드 |
| `--daily-profit` | 일별 손익 합산 (`--profit`과 함께) |
| `--pretty` | 사람 읽기용 포맷 |

### order — 주문 실행

#### 매수/매도

```bash
# 국내주식
kis order buy 005930 --qty 10 --price 70000          # 지정가 매수
kis order buy 005930 --qty 10 --type market           # 시장가 매수
kis order sell 005930 --qty 5 --price 78000           # 지정가 매도
kis order buy 005930 --qty 10 --exchange NXT          # NXT 거래소

# 해외주식
kis order buy AAPL --qty 10 --price 150 --overseas NAS   # AAPL 매수
kis order sell TSLA --qty 5 --price 200 --overseas NAS   # TSLA 매도
kis order sell MSFT --qty 10 --type moc --overseas NYS   # MOC 매도

# 확인 없이 즉시 실행
kis order buy 005930 --qty 10 --type market --yes
```

**국내 주문유형:**

| 코드 | 설명 |
|:---|:---|
| `limit` | 지정가 (기본) |
| `market` | 시장가 |
| `cond` | 조건부지정가 |
| `best` | 최유리지정가 |
| `pre` | 장전시간외 |
| `after` | 장후시간외 |
| `ioc` | IOC지정가 |
| `fok` | FOK지정가 |

**해외 주문유형:**

| 코드 | 설명 |
|:---|:---|
| `limit` | 지정가 (기본) |
| `moo` | 시장 개장시 시장가 (매도만) |
| `loo` | 시장 개장시 지정가 |
| `moc` | 시장 마감시 시장가 (매도만) |
| `loc` | 시장 마감시 지정가 |

#### TWAP / VWAP 분할주문

대량 주문을 한 번에 던지면 호가를 밀어 올려 체결가가 나빠진다. `twap`·`vwap`은
주문을 시간에 걸쳐 잘게 쪼개 집행한다.

```bash
# TWAP — 1,000주를 30분 동안 6회 균등 분할 매수
kis order twap 005930 --side buy --qty 1000 --duration 30 --slices 6

# VWAP — 1,000주를 2시간 동안 과거 거래량 곡선에 비례해 매수
kis order vwap 005930 --side buy --qty 1000 --duration 120 --slices 12

# 지정가 가드 — 70,000원을 넘는 구간은 건너뛴다
kis order twap 005930 --side buy --qty 1000 --limit-price 70000

# 지정가를 벗어나면 아예 중단
kis order twap 005930 --side buy --qty 1000 --limit-price 70000 --on-breach abort

# 신용융자로 분할 매수 (거부되면 현금주문으로 폴백)
kis order twap 005930 --side buy --qty 1000 --funding credit --credit-fallback

# 실제 주문 없이 스케줄만 확인
kis order twap 005930 --side buy --qty 1000 --dry-run --pretty
```

**TWAP vs VWAP**

| | TWAP | VWAP |
|:---|:---|:---|
| 분할 기준 | 시간 균등 | 과거 거래량 비례 |
| 슬라이스 크기 | 모두 같음 | 거래 많은 시간대에 더 많이 |
| 데이터 조회 | 없음 | 과거 N영업일 분봉 |
| 기본 집행시간 | 30분 | 60분 |

VWAP은 과거 **완료된** 영업일 분봉만 쓴다. 당일 부분 데이터는 아직 오지 않은
구간을 설명하지 못해 제외한다. 프로파일을 못 만들면 균등 분할로 내려가고, 그
사실을 응답 `notes`에 남긴다 — 조용히 바뀌지 않는다.

**옵션**

| 옵션 | 설명 |
|:---|:---|
| `--side` | `buy` / `sell` (필수) |
| `--qty` | 총 주문수량 (필수) |
| `--duration` | 집행 시간(분). TWAP 기본 30, VWAP 기본 60 |
| `--slices` | 분할 횟수 (기본 6) |
| `--type` | 주문유형 (기본 `best` 최유리지정가) |
| `--price` | 주문가격 (0=시장가) |
| `--exchange` | 거래소 (KRX, NXT, SOR) |
| `--funding` | `cash` 현금주문(기본) / `credit` 신용주문 |
| `--credit-type` | 신용유형. 매수 기본 `21`(신용융자), 매도 기본 `11`(융자상환매도) |
| `--loan-date` | 대출일자 YYYYMMDD (자기융자 `22` 매수용) |
| `--credit-fallback` | 신용 거부 시 현금주문으로 재시도 |
| `--limit-price` | 지정가 가드. 매수는 초과 시, 매도는 미만 시 스킵 |
| `--on-breach` | 지정가 이탈 시 `skip`(기본) / `abort` |
| `--max-failures` | 연속 주문 실패 허용 횟수 (기본 3) |
| `--no-session-guard` | 정규장(09:00-15:30) 제한 해제 |
| `--profile-days` | 거래량 프로파일 영업일 수 (VWAP 전용, 기본 5) |
| `--dry-run` | 주문을 전송하지 않고 스케줄만 시뮬레이션 |

**동작 규칙**

- 명령은 `--duration` 만큼 **블로킹**된다. Ctrl+C로 중단하면 그때까지 집행된
  수량을 보고하고 정상 종료한다.
- 진행 상황은 stderr로, 최종 결과 JSON은 stdout으로 나간다. LLM 파싱 계약이
  깨지지 않는다.
- 스킵된 수량은 뒤 슬라이스로 이월하지 않는다. `unfilledQuantity`로 보고한다.
- 종료코드: 전량 집행 `0`, 부분 집행/중단 `2`, 인자 오류/예외 `1`.

**응답 예시**

```json
{
  "data": {
    "algoOrder": {
      "algorithm": "twap",
      "code": "005930",
      "side": "buy",
      "status": "completed",
      "dryRun": false,
      "totalQuantity": 100,
      "submittedQuantity": 100,
      "unfilledQuantity": 0,
      "sliceCount": 3,
      "notes": [],
      "slices": [
        {
          "index": 0,
          "scheduledAt": "2026-08-21T11:35:35",
          "submittedAt": "2026-08-21T11:35:35",
          "quantity": 34,
          "status": "filled",
          "reason": "",
          "orderNo": "0000123456",
          "referencePrice": null,
          "message": "정상처리 되었습니다"
        }
      ]
    }
  }
}
```

`status`는 `completed`(전량) / `partial`(일부 스킵·실패) / `aborted`(가드로
중단) / `cancelled`(Ctrl+C), 슬라이스 `reason`은 `price_limit`,
`outside_session`, `price_unavailable`, `order_rejected`, `interrupted`,
`upstream_abort` 중 하나다.

#### 주문 취소

```bash
kis order cancel 0000123456                      # 국내 전량 취소
kis order cancel 0000123456 --qty 5              # 부분 취소
kis order cancel 0000123456 --overseas NAS --code AAPL  # 해외 취소
```

#### 주문 정정

```bash
kis order modify 0000123456 --price 72000        # 가격 정정
kis order modify 0000123456 --qty 20 --price 72000  # 수량+가격 정정
kis order modify 0000123456 --overseas NAS --code AAPL --price 155  # 해외 정정
```

#### 미체결 주문 조회

```bash
kis order list                     # 국내 미체결 주문
kis order list --overseas NAS      # 해외 미체결 주문
```

!!! warning "주문 안전장치"
    `--yes` 옵션 없이 주문하면 stderr로 확인 프롬프트가 표시됩니다. LLM 에이전트 사용 시에만 `--yes`를 사용하세요.

### search — 종목 검색

```bash
kis search 삼성                    # 종목명 검색
kis search 005930                  # 종목코드 검색
kis search 카카오 --limit 5        # 최대 5건
```

### query — API 직접 호출

어떤 API 메서드든 직접 호출할 수 있습니다:

```bash
kis query stock get_stock_price code=005930
kis query account get_account_balance
kis query overseas get_price excd=NAS symb=AAPL
kis query futures get_price code=101S03
kis query agent get_stock_investor ticker=005930
```

**지원 도메인:** `stock`, `account`, `overseas`, `futures`, `overseas_futures`, `agent`

잘못된 메서드명을 입력하면 사용 가능한 메서드 목록이 출력됩니다.

### schema — 스키마 탐색

```bash
kis schema                         # 전체 스키마
kis schema Stock                   # Stock 관련 타입만
kis schema Account                 # Account 관련 타입만
kis schema --json                  # JSON으로 타입 목록 출력
```

---

## 출력 형식

기본 출력은 **JSON** 형식으로, LLM이 파싱하기 최적화되어 있습니다.

### 필드명 자동 변환

한투 API의 축약 필드명이 읽기 쉬운 이름으로 자동 변환됩니다:

| 원본 (한투 API) | 변환 후 |
|:---|:---|
| `stck_prpr` | `currentPrice` |
| `prdy_ctrt` | `changeRate` |
| `acml_vol` | `volume` |
| `stck_oprc` | `openPrice` |
| `stck_hgpr` | `highPrice` |
| `stck_lwpr` | `lowPrice` |

### 장외 시간 동작

- 휴장일/장외 시간에는 `_notice` 필드에 안내 메시지가 포함됩니다
- 장 시작 전 (09시 이전): `"장 시작 전 — 데이터는 전일 종가 기준"`
- 장 마감 후 (16시 이후): `"장 마감 후 — 데이터는 금일 종가 기준"`
- 휴장일: `"휴장일 — 데이터는 직전 영업일(YYYY-MM-DD) 기준"`
