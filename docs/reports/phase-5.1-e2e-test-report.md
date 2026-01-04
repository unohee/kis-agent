# Phase 5.1 E2E 테스트 보고서

**작성일**: 2025-12-18
**최종 업데이트**: 2026-01-03
**관련 이슈**: INT-111 (PyKIS V2 업데이트), INT-139 (E2E 테스트), INT-359 (버그 수정 검증)
**상태**: ✅ 버그 수정 완료 (MCP 서버 재시작 후 최종 검증 필요)

---

## 1. 개요

MCP 서버의 통합 도구(Consolidated Tools)에 대한 E2E 테스트를 수행하여 실제 API 연동 상태를 검증했습니다.

## 2. 테스트 환경

```yaml
MCP Server: pykis-local (FastMCP 2.0 STDIO)
Agent: PyKIS Agent (account: 68867843)
Rate Limiter: 18 RPS / 900 RPM
Tools: 124개 (18 consolidated + 106 legacy)
테스트일: 2026-01-03 (주말 - 휴장)
```

## 3. E2E 테스트 결과

### 3.1 성공한 도구들 (12/13 테스트)

| 도구명 | 유형 | 테스트 케이스 | 결과 |
|--------|------|--------------|------|
| `stock_quote` | 통합 | detail (005930) | ✅ 성공 - 삼성전자 128,500원 (+7.17%) |
| `stock_chart` | 통합 | daily_30 (005930) | ✅ 성공 - 30일 일봉 데이터 |
| `investor_flow` | 통합 | stock (005930) | ✅ 성공 - 투자자별 매매동향 |
| `account_query` | 통합 | balance | ✅ 성공 - 22개 포지션 조회 |
| `index_data` | 통합 | current (KOSPI) | ✅ 성공 - KOSPI 지수 |
| `broker_trading` | 통합 | current (005930) | ✅ 성공 - 증권사별 매매동향 |
| `market_ranking` | 통합 | gainers | ✅ 성공 - 30개 종목 |
| `market_ranking` | 통합 | losers | ✅ 성공 - 13개 종목 |
| `market_ranking` | 통합 | fluctuation | ✅ 성공 - 30개 종목 |
| `market_ranking` | 통합 | volume_power | ✅ 성공 - 30개 종목 |
| `get_stock_price` | 레거시 | 005930 | ✅ 성공 |
| `get_market_rankings` | 레거시 | volume | ✅ 성공 |

### 3.2 수정 완료 (MCP 재시작 필요)

| 도구명 | 유형 | 이전 상태 | 수정 후 직접 호출 테스트 |
|--------|------|----------|------------------------|
| `market_ranking` | 통합 | volume 실패 | ✅ 30개 종목 (KODEX 200선물인버스2X 1위) |

## 4. 발견된 버그 및 수정 (2026-01-03 최종)

### 4.1 [버그 1] 에러 메시지에 rt_cd/msg_cd 미표시

**증상**: API 오류 시 "Unknown error"만 표시되어 디버깅 어려움

**원인**: `validate_api_response()`에서 `msg1`이 비어있을 때 fallback 메시지가 불친절함

**수정 (errors.py:171-180)**:
```python
# Before
error = APIError(f"{operation} failed: {msg1 or 'Unknown error'}", ...)

# After (2026-01-03 적용)
if msg1:
    error_message = msg1
else:
    error_message = f"rt_cd={rt_cd}, msg_cd={msg_cd}"
error = APIError(f"{operation} failed: {error_message}", ...)
```

**상태**: ✅ 코드 수정 완료

### 4.2 [버그 2] market_ranking volume 파라미터 케이스 불일치

**증상**: `market_ranking` 통합 도구에서 `ranking_type=volume` 호출 시 항상 실패

**근본 원인 분석**:
1. `consolidated_tools.py`에서 **lowercase** 파라미터 사용 (`fid_cond_mrkt_div_code`)
2. `/uapi/domestic-stock/v1/quotations/volume-rank` 엔드포인트는 **UPPERCASE** 파라미터 필요 (`FID_COND_MRKT_DIV_CODE`)
3. 잘못된 파라미터명 `fid_input_cnt_1` 사용 (올바른 값: `FID_INPUT_DATE_1`)

**수정 (consolidated_tools.py:232-249)**:
```python
# Before: 직접 _make_request_dict 호출 (lowercase params)
params = {
    "fid_cond_mrkt_div_code": "J",
    "fid_input_cnt_1": "50",  # 잘못된 파라미터
    ...
}
result = market_api._make_request_dict(...)

# After: price_api.volume_rank() 메서드 사용 (UPPERCASE params 자동 적용)
price_api = agent.stock_api.price_api
result = price_api.volume_rank(
    market="J",
    screen_code="20171",
    stock_code=input_iscd,
    div_cls="0",
    sort_cls="0",
    target_cls="111111111",
    exclude_cls="0000000000",
    price_from="",
    price_to="",
    volume=str(volume),
    date="",
)
```

**직접 호출 검증 결과**:
```
rt_cd: 0 (성공)
msg_cd: MCA00000
msg1: 정상처리 되었습니다.
Output count: 30개 종목
1위: KODEX 200선물인버스2X (거래량 835,730,042)
```

**상태**: ✅ 코드 수정 완료 (MCP 서버 재시작 후 반영)

## 5. 테스트 자동화 결과

```
pytest pykis-mcp-server/tests/test_consolidated_tools.py
================== 26 passed in 6.94s ===================
```

모든 단위 테스트 통과 확인.

## 6. 수정된 파일

| 파일 | 변경 내용 | 수정일 |
|------|----------|--------|
| `pykis-mcp-server/src/pykis_mcp_server/errors.py` | rt_cd/msg_cd 에러 메시지 표시 개선 | 2026-01-03 |
| `pykis-mcp-server/src/pykis_mcp_server/tools/consolidated_tools.py` | volume ranking을 `price_api.volume_rank()` 직접 호출로 변경 | 2026-01-03 |

## 7. 다음 단계

### 즉시 필요 작업
1. **MCP 서버 재시작** - 코드 변경사항 적용 필요
2. **volume ranking 최종 검증** - MCP 도구로 재테스트

### 후속 작업 (Phase 5.2, 5.3)
- [ ] IDE/Agent 호환성 테스트 (INT-360)
- [ ] CHANGELOG 및 마이그레이션 가이드 (INT-361)

## 8. 참고: PyKIS API 계층 구조 이슈

E2E 테스트 중 발견된 아키텍처 문제:

### /quotations/ vs /ranking/ 엔드포인트 차이

| 엔드포인트 | 파라미터 케이스 | 예시 |
|-----------|---------------|------|
| `/ranking/fluctuation` | lowercase 가능 | `fid_cond_mrkt_div_code` |
| `/ranking/volume-power` | lowercase 가능 | `fid_input_iscd` |
| `/quotations/volume-rank` | **UPPERCASE 필수** | `FID_COND_MRKT_DIV_CODE` |

**권장 사항**:
1. 가능하면 기존 API 메서드(`price_api.volume_rank()`) 사용
2. 직접 `_make_request_dict()` 호출 시 엔드포인트별 파라미터 케이스 확인 필수
3. 장기적으로 일관된 API 파라미터 케이스 정책 수립 필요

---

**작성자**: Claude Code
**검토자**: -
