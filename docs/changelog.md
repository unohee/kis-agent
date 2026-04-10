# Changelog

전체 변경 이력은 [GitHub Releases](https://github.com/unohee/kis-agent/releases)를 참고하세요.

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
