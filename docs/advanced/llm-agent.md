# LLM Agent 연동

kis-agent는 LLM 에이전트(Claude, GPT 등)가 도구로 사용하기에 최적화되어 있습니다.

## CLI를 도구로 사용

### JSON 출력

CLI의 기본 출력은 JSON으로, LLM이 바로 파싱할 수 있습니다:

```bash
kis price 005930
# {"currentPrice": "71800", "changeRate": "-1.37", "volume": "12345678", ...}
```

### 필드명 자동 변환

한투 API의 축약 필드명이 LLM이 이해할 수 있는 이름으로 자동 변환됩니다:

- `stck_prpr` → `currentPrice`
- `prdy_ctrt` → `changeRate`
- `acml_vol` → `volume`

### 스키마 탐색 (Introspection)

LLM이 사용 가능한 타입과 필드를 탐색할 수 있습니다:

```bash
kis schema              # 전체 타입 목록
kis schema Stock        # Stock 관련 스키마
kis schema Stock --json # JSON 형식
```

## MCP 서버로 활용

kis-agent를 MCP(Model Context Protocol) 서버로 구성하면 Claude Desktop 등에서 직접 호출할 수 있습니다.

## Python API를 도구로 사용

```python
from kis_agent import Agent

agent = Agent(
    app_key=os.environ['KIS_APP_KEY'],
    app_secret=os.environ['KIS_APP_SECRET'],
    account_no=os.environ['KIS_ACCOUNT_NO'],
    account_code=os.environ.get('KIS_ACCOUNT_CODE', '01'),
)

# LLM 에이전트의 도구 함수로 등록
def get_stock_price(code: str) -> dict:
    """주식 현재가를 조회합니다."""
    return agent.get_stock_price(code)

def get_balance() -> dict:
    """계좌 잔고를 조회합니다."""
    return agent.get_account_balance()
```

## CLI Bridge

`kis-bridge` 명령을 통해 표준 입출력 기반 메시지 프로토콜을 사용할 수 있습니다:

```bash
kis-bridge
```
