# Changelog

전체 변경 이력은 [GitHub Releases](https://github.com/unohee/kis-agent/releases)를 참고하세요.

## Unreleased

### 비동기 인증 (NEW)
- **feat(async)**: `Agent.create_async()` / `KISClient.create_async()` / `client.refresh_token_async()` / `auth_async()` / `reAuth_async()`. 생성자의 동기 토큰 발급이 이벤트 루프를 막던 문제 해결. [가이드](advanced/async.md)
  - 테스트는 있었으나(`test_auth_async.py`) 구현이 없어 21개 전부 skip 상태였습니다. 이제 19개가 실제로 실행됩니다.

### 기능 추가
- **feat(stock)**: `get_daily_index_chart_price()` — 국내주식업종기간별시세(일/주/월/년). 엔드포인트 상수만 있고 메서드가 없던 것을 구현.
- **fix(agent)**: `investor_api` / `interest_api`가 `Agent.__getattr__` 위임 목록에서 빠져 있어 `agent.get_interest_group_list()` 등 8개 메서드를 Agent로 호출할 수 없던 문제.

### 문서
- **docs**: 동작하지 않던 예제 정리 — 미구현 기능 시연, 제거된 `KIS_SECRET`, 개명 전 `from pykis import`, 정의되지 않은 이름 등.

## v1.8.0 (2026-07-17)

!!! warning "Breaking change — 환경변수 이름 통일"
    Legacy 별칭(`MY_APP`, `MY_SEC`, `KIS_SECRET`, `MY_ACCT_STOCK`, `MY_PROD`,
    `PROD_URL`, `VPS_URL`, `MY_AGENT`)이 제거되고 `KIS_*` prefix로 통일됐습니다.
    v1.7.0으로 예정됐다가 출시되지 않은 채 남아있던 변경이라, v1.6.1에서
    올라오신다면 `.env`를 확인하세요. `.env` 자동 로드도 현재 디렉터리만
    검색합니다(부모 디렉터리 검색 제거).

### 모의투자 지원 (NEW)
- **feat(paper)**: `Agent(paper=True)` / `KIS_PAPER=1` — URL과 모의투자 TR_ID를 함께 전환. [가이드](getting-started/paper-trading.md)
- **fix(paper)**: `base_url`만 모의로 지정하면 모든 호출이 `모의투자 TR 이 아닙니다`로 실패하던 문제 ([#44](https://github.com/unohee/kis-agent/issues/44)). 원인은 URL이 아니라 TR_ID였습니다
- **feat(paper)**: `PaperTradingNotSupportedError` — KIS는 전체 336개 API 중 43개만 모의로 제공합니다. 미지원 API 호출 시 네트워크 왕복 없이 즉시 알림
- **feat(ws)**: 모의투자 체결통보(`H0STCNI9`) 및 모의 WebSocket 지원

### 수정
- **fix(futures)**: 선물옵션 주문이 존재하지 않는 TR_ID(`TTTO1102U`/`TTTO1104U`)를 전송하던 버그 — **실전에서도 실패**하던 문제. 매수/매도는 `TTTO1101U`, 정정/취소는 `TTTO1103U` 하나를 쓰고 구분은 본문 필드로 합니다
- **fix(ws)**: `SubscriptionType.STOCK_NOTICE_AH`가 "시간외"로 오라벨돼 있던 문제 → `STOCK_NOTICE_PAPER`(기존 이름은 별칭으로 유지)
- **fix(core)**: `except: pass`로 예외를 삼켜 실패 원인이 추적되지 않던 문제
- **fix(rate_limiter)**: 공식 KIS 한도 준수, lock-free sleep, 안전한 기본값
- **perf(ws)**: 구독 속도 최적화, 동기 핸들러 격리, task 누수 수정

### 기능 추가
- **feat(futures)**: VKOSPI 프록시 계산기
- **feat(constants)**: `get_ws_url(is_real=...)` 헬퍼

### 내부
- **fix(ci)**: CI가 존재하지 않는 `pykis/`를 검사하며 lint·LOC·커버리지가 전부 무효였던 문제 수정
- **refactor(ws)**: `ws_agent.py`(1831줄) 편의 메서드를 `WSSubscriptionMixin`으로 분리 (1130줄)

## v1.6.1 (2026-04-07)

### 선물 기능 강화
- **feat(futures)**: 야간세션 REST 엔드포인트에 `market` 파라미터(CM/EU) 추가
- **feat(futures)**: `futures_master` 기반 종목코드 자동 해석
- **feat(ws,master)**: KRX 야간 선물/옵션 실시간 WebSocket 및 선물 마스터 데이터 추가

### 안정성 및 CLI 개선
- **fix(websocket)**: 무한 재연결 루프 방지, 백오프 및 실패 제한 추가
- **perf(core)**: 토큰 캐시 우선 초기화, CLI 로그 정리, API 응답 TTL
- **feat(cli)**: `trades` 서브커맨드 추가 — 거래 내역, 손익, 날짜 필터링
- **feat(cli)**: 해외선물 지원 추가 (`kis futures CLM26 --overseas`)
- **feat(cli,mcp)**: 종목명 표시 및 이름/코드 검색 기능 추가

### 수정
- **fix(test)**: websockets v16 호환성 테스트 업데이트

## v1.5.0 (2026-03-21)

- CLI for LLM Agents — `kis` 명령 추가
- JSON 출력, 필드명 자동 변환, 스키마 탐색
- 일봉 데이터 페이지네이션 지원

## v1.3.5 (2025-12-12)

- NXT WebSocket 지원
