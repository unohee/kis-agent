# PyKIS MCP Server

한국투자증권 OpenAPI Python 래퍼 PyKIS를 MCP (Model Context Protocol) 서버로 제공합니다.

## Features

- **58개 MCP Tools**: PyKIS의 모든 공개 API를 MCP Tools로 노출
- **실시간 데이터**: 주식 시세, 계좌 정보, 투자자 동향 실시간 조회
- **주문 실행**: 매수/매도, 정정/취소, 예약 주문 지원
- **Rate Limiting**: 18 RPS / 900 RPM 자동 관리
- **캐싱**: 지능형 캐싱으로 API 호출 최소화

## Installation

```bash
pip install pykis-mcp-server
```

## Configuration

MCP 클라이언트 설정:

```json
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

## Available Tools

### Stock Price & Market Data (16 tools)
- `get_stock_price` - 주식 현재가 조회
- `get_daily_price` - 일봉 데이터
- `inquire_minute_price` - 분봉시세조회 (일별분봉 우선, **권장**)
- `get_minute_price` - 당일 분봉 데이터
- `get_orderbook_raw` - 호가 조회
- ... 및 11개 더

### Account Management (10 tools)
- `get_account_balance` - 계좌 잔고
- `inquire_daily_ccld` - 일자별 체결
- `inquire_balance_rlz_pl` - 손익 조회
- ... 및 7개 더

### Order Execution (13 tools)
- `order_stock_cash` - 현금 주문
- `order_stock_credit` - 신용 주문
- `order_rvsecncl` - 정정/취소
- ... 및 10개 더

### Investor & Program Trading (11 tools)
- `get_stock_investor` - 투자자 매매동향
- `get_program_trade_by_stock` - 프로그램 매매
- ... 및 9개 더

### Utility & Helper (7 tools)
- `get_holiday_info` - 휴장일 정보
- `search_methods` - 메서드 검색
- ... 및 5개 더

### Rate Limiter & Configuration (4 tools)
- `get_rate_limiter_status` - Rate Limiter 상태
- `set_rate_limits` - Rate Limit 설정
- ... 및 2개 더

## Usage Examples

### 주식 현재가 조회
```
User: 삼성전자 현재가 알려줘
AI: (calls get_stock_price with code="005930")
    삼성전자 현재가는 70,000원입니다.
```

### 계좌 잔고 조회
```
User: 내 계좌 잔고 보여줘
AI: (calls get_account_balance)
    총 자산: 10,000,000원
    예수금: 5,000,000원
    보유 종목: ...
```

### 일봉 데이터 분석
```
User: 삼성전자 최근 30일 일봉 데이터로 추세 분석해줘
AI: (calls get_daily_price with code="005930")
    최근 30일간 상승 추세를 보이고 있습니다...
```

### 투자자 매매 동향
```
User: 삼성전자의 외국인 매매 동향 알려줘
AI: (calls get_stock_investor with code="005930")
    외국인은 최근 순매수 중입니다...
```

### Rate Limiter 관리
```
User: API Rate Limiter 상태 확인해줘
AI: (calls get_rate_limiter_status)
    초당 요청: 5/18
    분당 요청: 120/900
    ...
```

## Troubleshooting

### 환경 변수가 로드되지 않음
**증상**: `ConfigurationError: Missing required configuration`

**해결**:
- MCP 클라이언트 설정 파일의 `env` 필드 확인
- 환경 변수 이름이 정확한지 확인 (`KIS_APP_KEY`, `KIS_SECRET`, etc.)

### Rate Limit 에러
**증상**: `EGW00201` 또는 `EGW00202` 에러

**해결**:
- `get_rate_limiter_status`로 현재 상태 확인
- `set_rate_limits`로 제한 값 조정
- Rate Limiter가 활성화되어 있는지 확인

### API 호출 실패
**증상**: 특정 도구 호출 시 에러

**해결**:
- API 키가 유효한지 확인
- 시장 개장 시간인지 확인
- `is_holiday`로 휴장일 여부 확인

### 서버 연결 실패
**증상**: MCP 서버가 클라이언트에 연결되지 않음

**해결**:
- 클라이언트 로그 확인
- Python 경로가 올바른지 확인
- 패키지 설치 확인: `python -m pykis_mcp_server --version`

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format src tests
```

## License

MIT License

## Links

- [PyKIS](https://github.com/unohee/pykis)
- [MCP Protocol](https://modelcontextprotocol.io)
- [한국투자증권 OpenAPI](https://apiportal.koreainvestment.com)
