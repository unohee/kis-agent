# MCP 서버

kis-agent는 [MCP(Model Context Protocol)](https://modelcontextprotocol.io/) 서버를 제공하여 Claude Desktop 등의 AI 에이전트에서 한투 API를 직접 도구로 호출할 수 있습니다.

## 설치

```bash
cd pykis-mcp-server
pip install -e .
```

## Claude Desktop 설정

`claude_desktop_config.json`에 추가:

```json
{
  "mcpServers": {
    "kis-agent": {
      "command": "python",
      "args": ["-m", "pykis_mcp_server"],
      "env": {
        "KIS_APP_KEY": "...",
        "KIS_SECRET": "...",
        "KIS_ACCOUNT_NO": "...",
        "KIS_ACCOUNT_CODE": "01"
      }
    }
  }
}
```

## 통합 도구 (18개)

기존 개별 도구를 통합하여 컨텍스트 압박을 줄인 설계입니다. 각 도구는 `action` 파라미터로 세부 기능을 선택합니다.

### stock_quote — 주식 시세/호가/상세

종목 현재가, 호가, 상세정보 조회

### stock_chart — 주식 차트

일봉, 분봉, 기간별 차트 데이터

### index_data — 지수 데이터

KOSPI, KOSDAQ 등 업종 지수 조회

### market_ranking — 시장 순위

거래량, 등락률, 시총, 체결강도 등 순위

### investor_flow — 투자자 동향

투자자별/기관별/외국인 매매동향

### broker_trading — 외국계 거래

외국계 증권사 매매 분석

### program_trading — 프로그램 매매

프로그램매매 동향 분석

### account_query — 계좌/잔고/손익

계좌 잔고, 보유종목, 기간 손익, 주문가능금액 조회

### order_execute — 주문 실행

현금/신용 매수/매도 주문 실행

### order_manage — 주문 관리

정정, 취소, 미체결 조회, 예약주문

### stock_info — 종목 정보

종목 기본정보, 뉴스, 검색

### overtime_trading — 야간/시간외

시간외 체결, 호가, 야간 거래

### derivatives — 선물/옵션

국내/해외 선물옵션 시세, 전광판

### interest_stocks — 관심종목

관심종목 그룹 관리

### utility — 유틸리티

휴장일 확인, 섹터 코드, 거래시간 조회

### data_management — 데이터 관리

거래내역 내보내기, 종목 마스터

### rate_limiter — Rate Limiter

Rate Limiter 상태 조회/설정

### method_discovery — 메서드 탐색

사용 가능한 API 메서드 목록 조회
