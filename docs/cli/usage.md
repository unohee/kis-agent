# CLI 사용법

`pip install kis-agent` 하면 `kis` 명령이 바로 설치됩니다. Node.js 불필요.

## 기본 사용법

### 국내 주식 시세

```bash
kis price 005930                    # 삼성전자 현재가
kis price 005930 --daily --days 5   # 일별 시세 5일
kis price 005930 --pretty           # 사람 읽기용 포맷
```

### 호가 조회

```bash
kis orderbook 005930                # 10호가
```

### 해외 주식 시세

```bash
kis overseas NAS AAPL               # AAPL 시세
kis overseas NAS AAPL --detail      # PER/PBR/시총 포함
```

### 선물 시세

```bash
kis futures 101S03                  # 국내 선물 시세
kis futures CLM26 --overseas        # 해외 선물 시세
```

### 계좌 관리

```bash
kis balance                         # 계좌 잔고
kis balance --holdings              # 잔고 + 보유종목
```

### 거래 내역

```bash
kis trades                          # 당일 체결내역
kis trades --from 7d --pretty       # 최근 7일 (사람 읽기용)
kis trades --from 30d --sell        # 최근 30일 매도만
kis trades --from 3m --profit       # 기간별 실현손익
```

### API 직접 호출

```bash
kis query stock get_stock_price code=005930
```

### 스키마 탐색

```bash
kis schema Stock                    # Stock 타입 스키마
kis schema                          # 전체 스키마 목록
kis schema Stock --json             # JSON 형식 출력
```

## 출력 형식

기본 출력은 **JSON** 형식으로, LLM이 파싱하기 최적화되어 있습니다.

```bash
kis price 005930
# {"currentPrice": "71800", "changeRate": "-1.37", ...}

kis price 005930 --pretty
# 삼성전자 (005930)
# 현재가: 71,800원 (-1.37%)
```

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

## 장외 시간 동작

휴장일이나 장외 시간에는 직전 영업일 기준 데이터를 자동으로 안내합니다.

## 환경 변수

CLI는 `.env` 파일 또는 환경 변수에서 인증 정보를 읽습니다:

```bash
KIS_APP_KEY=...
KIS_SECRET=...        # 또는 KIS_APP_SECRET
KIS_ACCOUNT_NO=...
KIS_ACCOUNT_CODE=01
```
