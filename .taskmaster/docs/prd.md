# PRD: PyKIS MCP Server Enhancement

## 1. 개요

### 1.1 목적
PyKIS 라이브러리의 모든 API 엔드포인트를 MCP(Model Context Protocol) 서버를 통해 LLM 모델이 사용할 수 있도록 완전히 노출하는 것

### 1.2 배경
- PyKIS Agent에 70+ API 메서드 구현 완료
- 현재 MCP 서버에 58개 도구 구현됨
- 최근 API 리팩토링으로 새로운 엔드포인트 추가됨 (inquire_daily_price, inquire_daily_itemchartprice 등)
- 일부 엔드포인트 MCP 미노출 상태

### 1.3 범위
- 모든 Agent 메서드를 MCP 도구로 노출
- 기존 MCP 도구 API 시그니처 업데이트
- 도구 분류 체계 정리
- 테스트 및 문서화

## 2. 기능적 요구사항

### 2.1 Stock Price Tools (주식 시세)
- [ ] FR-001: get_stock_price - 주식 현재가 조회
- [ ] FR-002: inquire_daily_price - 최근 30일 일봉 조회 (신규)
- [ ] FR-003: inquire_daily_itemchartprice - 기간별 일봉 조회 (신규)
- [ ] FR-004: get_orderbook - 호가 조회
- [ ] FR-005: get_minute_price - 당일 분봉 조회
- [ ] FR-006: get_daily_minute_price - 특정일 분봉 조회
- [ ] FR-007: get_intraday_price - 전체 당일 분봉
- [ ] FR-008: inquire_price - 현재가 상세
- [ ] FR-009: inquire_price_2 - 현재가 상세 2
- [ ] FR-010: inquire_ccnl - 체결 정보
- [ ] FR-011: get_stock_ccnl - 주식 체결
- [ ] FR-012: inquire_time_itemconclusion - 시간별 체결

### 2.2 Market Data Tools (시장 데이터)
- [ ] FR-013: get_market_fluctuation - 시장 등락
- [ ] FR-014: get_market_rankings - 시장 순위
- [ ] FR-015: get_fluctuation_rank - 등락률 순위
- [ ] FR-016: get_volume_rank - 거래량 순위
- [ ] FR-017: get_volume_power_rank - 체결강도 순위
- [ ] FR-018: get_top_gainers - 상승률 상위
- [ ] FR-019: inquire_daily_overtimeprice - 시간외 일봉
- [ ] FR-020: inquire_overtime_price - 시간외 현재가
- [ ] FR-021: inquire_overtime_asking_price - 시간외 호가

### 2.3 Index & Derivatives Tools (지수/파생)
- [ ] FR-022: inquire_index_price - 지수 현재가
- [ ] FR-023: inquire_index_category_price - 업종별 지수
- [ ] FR-024: inquire_index_tickprice - 지수 틱
- [ ] FR-025: inquire_index_timeprice - 지수 시간별
- [ ] FR-026: get_index_daily_price - 지수 일봉
- [ ] FR-027: get_index_minute_data - 지수 분봉
- [ ] FR-028: inquire_elw_price - ELW 시세
- [ ] FR-029: get_future_option_price - 선물옵션 시세

### 2.4 Investor Analysis Tools (투자자 분석)
- [ ] FR-030: get_stock_investor - 종목별 투자자 동향
- [ ] FR-031: get_member - 증권사별 동향
- [ ] FR-032: get_stock_member - 종목 증권사 동향
- [ ] FR-033: get_member_transaction - 증권사 기간 거래
- [ ] FR-034: get_foreign_broker_net_buy - 외국계 순매수
- [ ] FR-035: get_frgnmem_pchs_trend - 외국인 매수 추세
- [ ] FR-036: get_frgnmem_trade_estimate - 외국인 추정
- [ ] FR-037: get_frgnmem_trade_trend - 외국인 추세
- [ ] FR-038: get_investor_trade_by_stock_daily - 일별 투자자
- [ ] FR-039: get_investor_trend_estimate - 투자자 추정

### 2.5 Program Trading Tools (프로그램 매매)
- [ ] FR-040: get_program_trade_by_stock - 종목별 프로그램
- [ ] FR-041: get_program_trade_hourly_trend - 시간대별 추세
- [ ] FR-042: get_program_trade_daily_summary - 일별 요약
- [ ] FR-043: get_program_trade_period_detail - 기간별 상세
- [ ] FR-044: get_program_trade_market_daily - 시장별 일별
- [ ] FR-045: get_investor_program_trade_today - 당일 투자자 프로그램

### 2.6 Account Tools (계좌)
- [ ] FR-046: get_account_balance - 계좌 잔고
- [ ] FR-047: get_total_asset - 총자산
- [ ] FR-048: get_possible_order_amount - 주문가능수량
- [ ] FR-049: inquire_psbl_order - 주문가능조회
- [ ] FR-050: get_account_order_quantity - 계좌 주문수량
- [ ] FR-051: inquire_daily_ccld - 일별 체결내역
- [ ] FR-052: inquire_period_trade_profit - 기간별 매매손익
- [ ] FR-053: inquire_balance_rlz_pl - 잔고평가손익
- [ ] FR-054: inquire_psbl_sell - 매도가능수량
- [ ] FR-055: inquire_credit_psamount - 신용가능금액
- [ ] FR-056: inquire_order_psbl - 주문가능조회
- [ ] FR-057: inquire_credit_order_psbl - 신용주문가능
- [ ] FR-058: inquire_intgr_margin - 통합증거금
- [ ] FR-059: inquire_psbl_rvsecncl - 정정취소가능

### 2.7 Stock Info Tools (종목 정보)
- [ ] FR-060: get_stock_info - 종목 기본정보
- [ ] FR-061: get_stock_basic - 종목 기본
- [ ] FR-062: get_stock_financial - 종목 재무
- [ ] FR-063: get_daily_credit_balance - 신용잔고
- [ ] FR-064: get_pbar_tratio - 매수매도비율
- [ ] FR-065: get_asking_price_exp_ccn - 호가예상체결
- [ ] FR-066: get_volume_power - 체결강도

### 2.8 Utility Tools (유틸리티)
- [ ] FR-067: calculate_support_resistance - 지지/저항선 계산
- [ ] FR-068: get_holiday_info - 휴장일 정보
- [ ] FR-069: is_holiday - 휴장일 여부
- [ ] FR-070: get_condition_stocks - 조건검색 종목
- [ ] FR-071: get_rate_limiter_status - Rate Limiter 상태
- [ ] FR-072: inquire_vi_status - VI 발동 상태
- [ ] FR-073: inquire_period_rights - 기간별 권리

### 2.9 Interest Stock Tools (관심종목)
- [ ] FR-074: get_interest_group_list - 관심그룹 목록
- [ ] FR-075: get_interest_stock_list - 관심종목 목록

## 3. 비기능적 요구사항

### 3.1 성능
- [ ] NFR-001: API 응답시간 < 500ms (캐시 hit 시 < 50ms)
- [ ] NFR-002: Rate Limiting 준수 (18 RPS / 900 RPM)
- [ ] NFR-003: 동시 요청 처리 지원

### 3.2 안정성
- [ ] NFR-004: 모든 도구에 에러 핸들링 구현
- [ ] NFR-005: 입력값 검증 (종목코드 6자리, 날짜 형식 등)
- [ ] NFR-006: API 실패 시 명확한 에러 메시지 반환

### 3.3 문서화
- [ ] NFR-007: 모든 도구에 한글 docstring
- [ ] NFR-008: Args, Returns 명세
- [ ] NFR-009: 사용 예시 포함

### 3.4 테스트
- [ ] NFR-010: 각 도구별 단위 테스트
- [ ] NFR-011: 모킹 기반 테스트 (실제 API 호출 없이)
- [ ] NFR-012: 커버리지 70% 이상

## 4. 기술 설계

### 4.1 디렉토리 구조
```
pykis-mcp-server/
├── src/pykis_mcp_server/
│   ├── tools/
│   │   ├── stock_tools.py      # 주식 시세
│   │   ├── market_tools.py     # 시장 데이터
│   │   ├── index_tools.py      # 지수/파생
│   │   ├── investor_tools.py   # 투자자 분석
│   │   ├── program_tools.py    # 프로그램 매매
│   │   ├── account_tools.py    # 계좌
│   │   ├── info_tools.py       # 종목 정보
│   │   └── utility_tools.py    # 유틸리티
│   ├── server.py
│   └── errors.py
└── tests/
```

### 4.2 도구 구현 패턴
```python
@server.tool()
async def tool_name(param: str) -> Dict[str, Any]:
    """한글 설명

    Args:
        param: 파라미터 설명

    Returns:
        Dict: 응답 설명
    """
    # 입력값 검증
    if not param:
        raise InvalidParameterError("param", "설명")

    agent = get_agent()
    result = agent.method_name(param)
    return validate_api_response(result, "기능명")
```

## 5. 마일스톤

### Phase 1: 기존 도구 업데이트 (FR-001 ~ FR-012)
- 최근 리팩토링된 API 시그니처 반영
- inquire_daily_price, inquire_daily_itemchartprice 추가

### Phase 2: 시장/지수 도구 (FR-013 ~ FR-029)
- 시장 데이터 도구 완성
- 지수/파생 도구 추가

### Phase 3: 분석 도구 (FR-030 ~ FR-045)
- 투자자 분석 도구
- 프로그램 매매 도구

### Phase 4: 계좌/유틸리티 (FR-046 ~ FR-075)
- 계좌 관련 도구
- 유틸리티 및 관심종목 도구

### Phase 5: 테스트 및 문서화
- 단위 테스트 작성
- 문서화 완료
- CI/CD 통합

## 6. 의존성

- pykis >= 1.3.1
- mcp >= 0.1.0
- Python >= 3.8

## 7. 승인 기준

- [ ] 모든 FR 구현 완료
- [ ] 모든 NFR 충족
- [ ] 테스트 통과 (pytest)
- [ ] 기존 58개 도구 하위호환성 유지

---
최종 수정: 2025-11-19 | 상태: Draft
