# PR: WebSocket 단일화 + 승인키 Fail‑Fast + 레거시 정리 (v1.1.1)

## 개요
- 공식 WebSocket 진입점을 `WebSocketClient`로 단일화하고, `Agent.websocket()`을 표준 클라이언트로 전환했습니다.
- 승인키 발급은 Agent/KISClient 경로와 완전히 일치하며, 실패 시 즉시 예외를 발생시키는 fail‑fast 정책을 적용했습니다.
- 레거시 `pykis.stock.api.StockAPI` 구현을 제거하고 Facade(`api_facade.StockAPI`)로 재노출, 주문/가능조회/휴장일/지수·선물 관련 메서드를 이관했습니다.

## 주요 변경
- refactor(websocket): Agent.websocket → WebSocketClient 반환, 루트 공개 엔트리 `WebSocketClient`만 유지
- feat(stock): 레거시 StockAPI 메서드 Facade로 이관 (order_cash, order_credit, inquire_psbl_order, inquire_credit_psamount, get_possible_order, get_holiday_info, get_kospi200_index, get_futures_price)
- fix(investor_api): dict 경로에서 `retries` 전달 문제 제거
- docs: WebSocketClient 공식화 및 승인키 fail‑fast 정책 명시
- tests: WebSocket 테스트를 WebSocketClient 기준으로 업데이트, 승인키 발급 mock 추가

## 동작/검증
- 테스트 결과: 340 passed, 33 skipped, 1 xfailed
- 승인키 실패 시: 한국어 로깅 + traceback 포함, 즉시 예외 발생

## 마이그레이션 노트
- WebSocket: `from pykis import WebSocketClient` 또는 `agent.websocket()` 사용
- 레거시 `KisWebSocket`: deprecated, 신규 코드에서 사용 금지
- 레거시 `pykis.stock.api.StockAPI`: 구현 제거, `from pykis.stock.api import StockAPI`는 Facade를 로드하므로 인터페이스는 유지되나 내부는 Facade입니다.

## 체크리스트
- [x] 테스트 통과 (로컬)
- [x] 문서 업데이트(README, docs/api, guides)
- [x] 버전 bump(1.1.1) + CHANGELOG 추가

## 스크린샷/로그 (선택)
- N/A

