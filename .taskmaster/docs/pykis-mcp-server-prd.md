# PyKIS MCP Server - Product Requirements Document

## 1. Executive Summary

### 1.1 Project Overview
PyKIS MCP (Model Context Protocol) Server는 한국투자증권 OpenAPI Python 래퍼인 PyKIS를 MCP 프로토콜을 통해 Claude Desktop 및 기타 MCP 클라이언트에서 사용할 수 있도록 하는 서버 구현입니다.

### 1.2 Goals
- PyKIS의 모든 핵심 기능을 MCP Tools로 노출
- 실시간 시세, 계좌 정보, 주문 등 주요 API를 Claude가 직접 호출 가능하게 구현
- 한국 주식 시장 데이터 및 거래를 자연어로 제어 가능
- 타입 안정성 및 에러 처리 강화

### 1.3 Success Metrics
- 50개 이상의 MCP Tools 구현
- 모든 핵심 API 커버리지 100%
- 응답 시간 < 1초 (캐시 미적중 시)
- 에러 핸들링 100%

---

## 2. System Architecture

### 2.1 Current State (PyKIS)
```
PyKIS Package Structure:
├── pykis/
│   ├── core/
│   │   ├── agent.py          # Main Agent class (71 methods)
│   │   ├── client.py          # API client
│   │   ├── auth.py            # Authentication
│   │   ├── config.py          # Configuration
│   │   ├── rate_limiter.py    # Rate limiting
│   │   └── cache.py           # Caching
│   ├── account/
│   │   └── api.py             # Account API
│   ├── stock/
│   │   ├── api.py             # Stock API
│   │   ├── investor_api.py    # Investor API
│   │   ├── market_api.py      # Market API
│   │   └── price_api.py       # Price API
│   └── websocket/
│       └── client.py          # WebSocket client
```

### 2.2 Target State (MCP Server)
```
pykis-mcp-server/
├── src/
│   ├── server.py              # MCP server entry point
│   ├── tools/
│   │   ├── stock_tools.py     # Stock price, orderbook, etc.
│   │   ├── account_tools.py   # Balance, orders, etc.
│   │   ├── order_tools.py     # Buy, sell, cancel, etc.
│   │   ├── investor_tools.py  # Investor trends
│   │   ├── market_tools.py    # Market data
│   │   └── utility_tools.py   # Holidays, etc.
│   ├── resources/
│   │   └── account_resource.py # Real-time account data
│   └── config.py              # MCP server config
├── tests/
│   └── test_tools.py
├── pyproject.toml
└── README.md
```

### 2.3 Technology Stack
- **Protocol**: MCP (Model Context Protocol)
- **Language**: Python 3.8+
- **Core Library**: PyKIS 0.1.22+
- **MCP SDK**: `mcp` Python package
- **Transport**: stdio (standard input/output)

---

## 3. Functional Requirements

### 3.1 MCP Tools - ALL 50 Public Methods

**IMPORTANT**: 모든 공개 API 메서드를 MCP Tools로 노출합니다 (private 메서드 제외).

#### 3.1.1 Stock Price & Market Data Tools (15 tools)
1. `get_stock_price` - 주식 현재가 조회
2. `get_daily_price` - 일봉 데이터 조회
3. `get_minute_price` - 분봉 데이터 조회
4. `get_daily_minute_price` - 특정일 분봉 데이터
5. `get_orderbook_raw` - 호가 조회 (Raw)
6. `fetch_minute_data` - 4일간 분봉 데이터 수집
7. `calculate_support_resistance` - 지지/저항선 계산
8. `get_index_daily_price` - 지수 일봉
9. `get_volume_power` - 거래량 순위
10. `get_top_gainers` - 등락률 순위
11. `get_member` - 회원사 정보
12. `init_minute_db` - 분봉 DB 초기화
13. `migrate_minute_csv_to_db` - CSV to DB 마이그레이션
14. `get_kospi200_futures_code` - KOSPI200 선물코드 조회
15. `get_future_option_price` - 선물옵션 가격

#### 3.1.2 Account Management Tools (10 tools)
1. `get_account_balance` - 계좌 잔고 조회
2. `get_possible_order_amount` - 주문 가능 금액/수량
3. `get_account_order_quantity` - 계좌별 주문 가능 수량
4. `inquire_daily_ccld` - 일자별 체결 내역
5. `inquire_balance_rlz_pl` - 잔고 평가 및 실현 손익
6. `inquire_psbl_sell` - 매도 가능 수량
7. `inquire_period_trade_profit` - 기간별 매매 손익
8. `inquire_intgr_margin` - 증거금 조회
9. `inquire_credit_psamount` - 신용 가능 금액
10. `inquire_period_rights` - 기간별 권리 조회

#### 3.1.3 Order Execution Tools (12 tools)
1. `order_stock_cash` - 현금 주문 (매수/매도)
2. `order_stock_credit` - 신용 주문 (매수/매도)
3. `inquire_order_psbl` - 현금 주문 가능 조회
4. `inquire_credit_order_psbl` - 신용 주문 가능 조회
5. `order_cash` - 현금 매수
6. `order_cash_sor` - 시장가 매수
7. `order_credit_buy` - 신용 매수
8. `order_credit_sell` - 신용 매도
9. `order_rvsecncl` - 정정/취소
10. `order_resv` - 예약 주문
11. `order_resv_rvsecncl` - 예약 정정/취소
12. `order_resv_ccnl` - 예약 전체 취소
13. `inquire_psbl_rvsecncl` - 정정/취소 가능 조회

#### 3.1.4 Investor & Program Trading Tools (10 tools)
1. `get_stock_investor` - 종목별 투자자 매매동향
2. `get_investor_daily_by_market` - 시장별 투자자 일별 동향
3. `get_investor_time_by_market` - 시장별 투자자 시간대별 동향
4. `get_foreign_broker_net_buy` - 외국인/기관 순매수
5. `get_stock_member` - 증권사별 매매동향
6. `get_member_transaction` - 증권사 기간별 거래
7. `get_program_trade_by_stock` - 종목별 프로그램 매매
8. `get_program_trade_daily_summary` - 프로그램 매매 일별 요약
9. `get_program_trade_market_daily` - 시장 프로그램 매매
10. `get_program_trade_hourly_trend` - 프로그램 매매 시간대별 추세
11. `get_program_trade_period_detail` - 프로그램 매매 기간 상세

#### 3.1.5 Utility & Helper Tools (7 tools)
1. `get_holiday_info` - 휴장일 정보
2. `is_holiday` - 특정일 휴장일 여부
3. `get_daily_credit_balance` - 일별 신용잔고
4. `get_condition_stocks` - 조건검색식 종목 조회
5. `search_methods` - Agent 메서드 검색
6. `get_all_methods` - 모든 메서드 목록
7. `show_method_usage` - 메서드 사용법 표시

#### 3.1.6 Rate Limiter & Configuration Tools (4 tools)
1. `get_rate_limiter_status` - Rate Limiter 상태 조회
2. `reset_rate_limiter` - Rate Limiter 리셋
3. `set_rate_limits` - Rate Limit 설정
4. `enable_adaptive_rate_limiting` - 적응형 Rate Limiting 활성화

**Total: 58 MCP Tools** (모든 공개 메서드 커버)

### 3.2 MCP Resources

#### 3.2.1 Account Resource
- URI: `account://balance`
- Description: 실시간 계좌 잔고 정보
- Update Frequency: 1초 캐시

#### 3.2.2 Watchlist Resource
- URI: `watchlist://stocks`
- Description: 관심종목 리스트
- Update Frequency: 실시간

---

## 4. Technical Specifications

### 4.1 Tool Definition Example

```python
@server.tool()
async def get_stock_price(code: str) -> Dict[str, Any]:
    """주식 현재가 조회

    Args:
        code: 종목코드 (예: "005930" - 삼성전자)

    Returns:
        Dict: 현재가 정보
            - output.stck_prpr: 주식 현재가
            - output.prdy_vrss: 전일 대비
            - output.prdy_ctrt: 전일 대비율
    """
    agent = get_agent()
    result = agent.get_stock_price(code)

    if not result or result.get('rt_cd') != '0':
        raise McpError(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to get stock price: {result.get('msg1')}"
        )

    return result
```

### 4.2 Error Handling

```python
class PyKISMCPError(Exception):
    """PyKIS MCP Server 에러"""
    pass

ERROR_MAPPINGS = {
    "40": ErrorCode.INVALID_REQUEST,  # 잘못된 요청
    "50": ErrorCode.INTERNAL_ERROR,   # 서버 오류
    "99": ErrorCode.METHOD_NOT_FOUND, # API 미지원
}
```

### 4.3 Configuration

```python
# config.py
class MCPServerConfig:
    # PyKIS Agent 설정
    APP_KEY: str = os.getenv("KIS_APP_KEY")
    APP_SECRET: str = os.getenv("KIS_SECRET")
    ACCOUNT_NO: str = os.getenv("KIS_ACCOUNT_NO")
    ACCOUNT_CODE: str = os.getenv("KIS_ACCOUNT_CODE", "01")

    # MCP Server 설정
    SERVER_NAME: str = "pykis-mcp-server"
    SERVER_VERSION: str = "0.1.0"

    # Rate Limiting
    ENABLE_RATE_LIMITER: bool = True
    REQUESTS_PER_SECOND: int = 18
    REQUESTS_PER_MINUTE: int = 900

    # Cache
    ENABLE_CACHE: bool = True
    DEFAULT_CACHE_TTL: int = 5
```

### 4.4 Server Initialization

```python
# server.py
import asyncio
from mcp.server import Server
from mcp.types import Tool, Resource
from pykis import Agent

server = Server("pykis-mcp-server")
_agent: Optional[Agent] = None

def get_agent() -> Agent:
    """싱글턴 Agent 인스턴스 반환"""
    global _agent
    if _agent is None:
        _agent = Agent(
            app_key=MCPServerConfig.APP_KEY,
            app_secret=MCPServerConfig.APP_SECRET,
            account_no=MCPServerConfig.ACCOUNT_NO,
            account_code=MCPServerConfig.ACCOUNT_CODE,
            enable_rate_limiter=MCPServerConfig.ENABLE_RATE_LIMITER,
        )
    return _agent

async def main():
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5. Implementation Plan

### 5.1 Phase 1: Core Infrastructure (Week 1)
- MCP server 기본 구조 생성
- Agent 싱글턴 관리
- 에러 핸들링 구현
- 설정 관리 구현

### 5.2 Phase 2: Stock Tools (Week 2)
- 8개 주식 시세 조회 Tools 구현
- 테스트 코드 작성
- 문서화

### 5.3 Phase 3: Account & Order Tools (Week 3)
- 6개 계좌 조회 Tools 구현
- 10개 주문 관련 Tools 구현
- 통합 테스트

### 5.4 Phase 4: Market & Utility Tools (Week 4)
- 12개 투자자/시장 Tools 구현
- 6개 유틸리티 Tools 구현
- 리소스 구현

### 5.5 Phase 5: Testing & Documentation (Week 5)
- 전체 통합 테스트
- Claude Desktop 연동 테스트
- README 및 사용 가이드 작성
- 배포 준비

---

## 6. Testing Strategy

### 6.1 Unit Tests
- 각 Tool 별 단위 테스트
- Mock을 사용한 Agent API 호출 테스트
- 에러 케이스 테스트

### 6.2 Integration Tests
- 실제 Agent와 연동 테스트
- 모의투자 API 사용
- 전체 워크플로우 테스트

### 6.3 Claude Desktop Tests
- .mcp.json 설정 테스트
- 실제 Claude와 대화 테스트
- 사용자 시나리오 테스트

---

## 7. Deployment

### 7.1 Package Structure
```bash
pykis-mcp-server/
├── pyproject.toml
├── README.md
├── LICENSE
├── .env.example
└── src/
    └── pykis_mcp_server/
        ├── __init__.py
        ├── server.py
        └── tools/
```

### 7.2 Installation
```bash
# PyPI 배포
pip install pykis-mcp-server

# Claude Desktop 설정
# .claude/config.json
{
  "mcpServers": {
    "pykis": {
      "command": "python",
      "args": ["-m", "pykis_mcp_server"],
      "env": {
        "KIS_APP_KEY": "your_app_key",
        "KIS_SECRET": "your_secret",
        "KIS_ACCOUNT_NO": "your_account",
        "KIS_ACCOUNT_CODE": "01"
      }
    }
  }
}
```

---

## 8. Risk & Mitigation

### 8.1 Risks
1. **Rate Limiting 초과**: 18 RPS / 900 RPM 제한
   - Mitigation: PyKIS 내장 Rate Limiter 활용

2. **API 응답 지연**: 네트워크 지연으로 응답 시간 증가
   - Mitigation: 캐시 활용, 타임아웃 설정

3. **인증 토큰 만료**: 24시간 후 토큰 만료
   - Mitigation: 자동 재발급 로직 구현

4. **보안**: API 키 노출 위험
   - Mitigation: 환경변수 사용, .env 파일 .gitignore 추가

### 8.2 Monitoring
- 에러 로그 수집
- API 호출 통계
- 응답 시간 모니터링

---

## 9. Success Criteria

### 9.1 Functional
- ✅ 50개 이상 Tools 구현
- ✅ 모든 핵심 API 커버
- ✅ Claude Desktop 정상 연동

### 9.2 Non-Functional
- ✅ 응답 시간 < 1초 (95 percentile)
- ✅ 에러율 < 1%
- ✅ 테스트 커버리지 > 80%

### 9.3 Documentation
- ✅ README with examples
- ✅ API reference
- ✅ Troubleshooting guide

---

## 10. Future Enhancements

### 10.1 Phase 2 Features
- WebSocket 실시간 데이터 스트리밍
- 차트 이미지 생성 및 반환
- 백테스팅 도구
- 포트폴리오 분석

### 10.2 Community
- GitHub 오픈소스 공개
- 사용자 피드백 수집
- 커뮤니티 기여 독려

---

## Appendix

### A. PyKIS Agent Methods (71 total)
```
Core Methods (20):
- get_stock_price, get_daily_price, get_minute_price
- get_orderbook_raw, get_account_balance
- order_stock_cash, order_stock_credit
- get_stock_investor, get_foreign_broker_net_buy
- get_program_trade_by_stock, etc.

Account Methods (12):
- inquire_daily_ccld, inquire_balance_rlz_pl
- inquire_psbl_sell, inquire_order_psbl
- inquire_credit_order_psbl, etc.

Order Methods (10):
- order_cash, order_cash_sor
- order_credit_buy, order_credit_sell
- order_rvsecncl, order_resv, etc.

Utility Methods (8):
- get_holiday_info, is_holiday
- get_condition_stocks, search_methods
- get_all_methods, etc.

Internal Methods (21):
- _init_apis, _ensure_valid_token
- _calculate_support_resistance, etc.
```

### B. References
- [PyKIS GitHub](https://github.com/unohee/pykis)
- [MCP Protocol Spec](https://modelcontextprotocol.io)
- [한국투자증권 OpenAPI](https://apiportal.koreainvestment.com)
