# WebSocket 파사드 통일 작업 계획

## 개요
현재 pykis의 예제 파일들이 직접 `KISClient`, `StockAPI`, `WebSocketClient` 등을 사용하고 있어
파사드 패턴을 위반하고 있습니다. 모든 예제를 `Agent` (REST), `WSAgent` (WebSocket) 파사드를 통해
접근하도록 통일해야 합니다.

## 현재 상태 (2025-12-19)

### 완료된 작업
- ✅ 선물 호가창 API 구현 (`get_future_orderbook()`)
- ✅ 선물 호가창 예제 (`examples/future_orderbook_example.py`) - Agent 파사드 사용
- ✅ PR #21 생성 및 푸시 완료

### Stash에 보관된 파일들 (stash@{0})
다음 파일들은 Agent/WSAgent 파사드로 변환 작업이 진행 중이며 stash에 보관되어 있습니다:

1. **examples/daily_index_chart_price_example.py**
   - 변경: `KISClient() + StockAPI()` → `Agent()`
   - 메서드: `get_daily_index_chart_price()`
   - 상태: 변환 완료, 테스트 필요

2. **examples/future_option_price_example.py**
   - 변경: `stock_api.get_future_option_price()` → `agent.get_future_option_price()`
   - 베이시스 계산 로직 포함
   - 상태: 변환 완료, 테스트 필요

3. **examples/test_kospi200_basis.py**
   - 변경: 클래스 기반 테스터를 Agent 사용으로 전환
   - `self.client + self.stock_api` → `self.agent`
   - 상태: 변환 완료, 테스트 필요

4. **examples/refactored_websocket_example.py**
   - 변경: 완전히 새로 작성 (WSAgent 사용)
   - 기존: `WebSocketClientBuilder`, `WebSocketClientFactory`
   - 신규: `WSAgent` 파사드 패턴
   - 상태: 완전 재작성, 테스트 필요

5. **pykis-mcp-server/src/pykis_mcp_server/errors.py** (선택적)
   - 일반적인 에러 메시지 처리 개선
   - 선물 API와 무관한 변경
   - 상태: 별도 PR로 처리 권장

## 작업 계획

### Phase 1: REST API 예제 통일 (우선순위: 높음)
**목표**: 모든 REST API 예제가 Agent 파사드를 사용하도록 변경

#### 작업 항목
1. **examples/daily_index_chart_price_example.py**
   ```python
   # Before
   client = KISClient()
   stock_api = StockAPI(client, {})
   result = stock_api.get_daily_index_chart_price(...)

   # After
   agent = Agent()
   result = agent.get_daily_index_chart_price(...)
   ```

2. **examples/future_option_price_example.py**
   - Agent 파사드로 전환
   - 베이시스 계산 로직 유지
   - `get_kospi200_futures_code()` 헬퍼 사용 검증

3. **examples/test_kospi200_basis.py**
   - KospiBasisTester 클래스 리팩토링
   - Agent 파사드 사용으로 간소화

#### 테스트 계획
- [ ] 각 예제 파일 개별 실행 테스트
- [ ] API 응답 구조 변경 없음 확인
- [ ] 기존 기능 동작 검증

### Phase 2: WebSocket 예제 통일 (우선순위: 중간)
**목표**: WebSocket 관련 예제를 WSAgent 파사드로 통일

#### 작업 항목
1. **examples/refactored_websocket_example.py**
   - WSAgent 기반으로 완전 재작성
   - SubscriptionType enum 활용
   - 기존 Builder/Factory 패턴 제거

2. **examples/websocket_multi_subscribe.py** (미완성)
   - WSAgent로 다중 구독 예제 작성
   - 실시간 호가, 체결, 지수 동시 구독

#### 새로운 예제 구조
```python
from pykis import Agent

agent = Agent()
ws_agent = agent.websocket(
    stock_codes=['005930', '035420'],
    subscription_types=[
        SubscriptionType.QUOTE,
        SubscriptionType.EXECUTION,
        SubscriptionType.ORDERBOOK
    ]
)

async def on_data(event):
    print(f"Data: {event.data}")

ws_agent.on('data', on_data)
await ws_agent.start()
```

#### 테스트 계획
- [ ] 실시간 연결 테스트
- [ ] 다중 종목 구독 테스트
- [ ] 콜백 핸들러 동작 확인
- [ ] 메모리 누수 확인

### Phase 3: 문서화 및 가이드 업데이트 (우선순위: 낮음)

#### 작업 항목
1. **README.md 업데이트**
   - Agent/WSAgent 파사드 사용 가이드 추가
   - 직접 API 접근 방법 deprecated 표시

2. **CLAUDE.md 업데이트**
   - 파사드 패턴 사용 규칙 명시
   - 예제 작성 시 Agent/WSAgent 우선 사용 지침

3. **examples/README.md 생성**
   - 각 예제 파일 목적 및 사용법 설명
   - Agent vs. WSAgent 선택 가이드

## 기술 고려사항

### Agent 파사드의 장점
- 단일 진입점으로 API 접근 간소화
- 자동 인증 관리
- 통합된 에러 처리
- 향후 버전 업그레이드 시 하위 호환성 유지 용이

### WSAgent의 장점
- WebSocket 연결 생명주기 자동 관리
- 구독 타입별 추상화
- 재연결 로직 내장
- 메트릭 및 로깅 통합

### 하위 호환성 유지
- 기존 `KISClient`, `StockAPI` 등은 deprecated 처리하되 유지
- 점진적 마이그레이션 가이드 제공
- 주요 버전 업그레이드 시 제거 검토

## 예상 일정

- **Phase 1 (REST API)**: 1-2일
  - 파일별 변환: 0.5일
  - 테스트 및 검증: 0.5-1일

- **Phase 2 (WebSocket)**: 2-3일
  - WSAgent 예제 작성: 1일
  - 다중 구독 예제: 0.5일
  - 실시간 테스트: 1-1.5일

- **Phase 3 (문서화)**: 1일
  - README/CLAUDE.md: 0.5일
  - 예제 가이드: 0.5일

**총 예상 기간**: 4-6일

## 위험 요소 및 대응

### 위험 1: API 응답 구조 변경
- **대응**: 단위 테스트로 응답 구조 검증
- **완화**: TypedDict 응답 모델 활용

### 위험 2: WebSocket 연결 불안정
- **대응**: 재연결 로직 강화
- **완화**: 로깅 및 메트릭으로 모니터링

### 위험 3: 하위 호환성 문제
- **대응**: Deprecated 경고 추가, 마이그레이션 가이드 제공
- **완화**: 기존 API 최소 1년 유지

## 다음 단계

1. Stash 복구 및 Phase 1 작업 재개
   ```bash
   git stash pop stash@{0}
   # 또는 선택적 적용
   git checkout stash@{0} -- examples/daily_index_chart_price_example.py
   ```

2. 각 예제 파일 개별 테스트 후 커밋

3. Phase 1 완료 후 별도 PR 생성

4. Phase 2, 3 순차 진행

## 참고 자료

- PR #21: 선물 호가창 API 구현 (Agent 파사드 사용 예제 포함)
- `examples/future_orderbook_example.py`: Agent 파사드 베스트 프랙티스
- `CLAUDE.md`: 파사드 패턴 사용 지침

---

**작성일**: 2025-12-19
**작성자**: Claude Sonnet 4.5
**관련 이슈**: INT-111 (WebSocket 파사드 통일)
**Stash 참조**: stash@{0} "WIP: Agent/WSAgent facade pattern unification + futures orderbook"
