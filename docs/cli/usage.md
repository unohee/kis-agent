# CLI 사용법

`pip install kis-agent` 하면 `kis` 명령이 바로 설치됩니다. Node.js 불필요.

## 환경 변수

CLI는 `.env` 파일 또는 환경 변수에서 인증 정보를 읽습니다:

```bash
KIS_APP_KEY=...
KIS_SECRET=...        # 또는 KIS_APP_SECRET
KIS_ACCOUNT_NO=...
KIS_ACCOUNT_CODE=01
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
