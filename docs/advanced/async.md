# 비동기 사용 (asyncio)

`Agent(...)`와 `KISClient(...)`는 생성자에서 **동기 HTTP로 토큰을 발급**합니다. asyncio 애플리케이션에서는 그 사이 이벤트 루프가 멈추므로, v1.8.0부터 토큰 발급만 비동기로 처리하는 팩토리를 제공합니다.

`aiohttp`가 필요합니다 (기본 의존성에 포함).

## Agent.create_async()

```python
import asyncio
from kis_agent import Agent


async def main():
    agent = await Agent.create_async(
        app_key=os.environ["KIS_APP_KEY"],
        app_secret=os.environ["KIS_APP_SECRET"],
        account_no=os.environ["KIS_ACCOUNT_NO"],
        account_code="01",
    )
    price = agent.get_stock_price("005930")
    print(price["output"]["stck_prpr"])


asyncio.run(main())
```

인자는 `Agent(...)`와 동일합니다 — `paper=True`, `enable_rate_limiter`, `rate_limiter_config` 모두 그대로 쓸 수 있습니다.

!!! note "비동기인 것은 인증뿐입니다"
    생성 이후의 API 호출(`get_stock_price` 등)은 **여전히 동기**입니다.
    `create_async`가 해결하는 것은 "Agent를 만드는 동안 이벤트 루프가 멈추는 것"
    한 가지입니다. 여러 계정을 동시에 인증하거나, 이미 asyncio로 돌아가는 앱
    (FastAPI, Discord 봇 등) 안에서 Agent를 만들 때 의미가 있습니다.

## 여러 계정 동시 인증

`create_async`의 실익이 가장 큰 경우입니다. 계정 수만큼 순차 대기하지 않습니다.

```python
agents = await asyncio.gather(*[
    Agent.create_async(
        app_key=acc["key"], app_secret=acc["secret"],
        account_no=acc["no"], account_code="01",
    )
    for acc in accounts
])
```

## 하위 레벨 API

### KISClient.create_async()

```python
from kis_agent.core.client import KISClient
from kis_agent.core.config import KISConfig

client = await KISClient.create_async(config=KISConfig(...))
```

### 토큰 강제 갱신

```python
await client.refresh_token_async()
```

캐시를 건너뛰고 새로 발급합니다 — 갱신을 요청했다는 건 기존 토큰을 믿지 못한다는 뜻이므로, 캐시를 재사용하면 의미가 없기 때문입니다.

### auth_async / reAuth_async

Agent나 Client 없이 토큰만 필요할 때 씁니다.

```python
from kis_agent.core.auth import auth_async, reAuth_async

token = await auth_async(config)            # 캐시가 있으면 재사용
token = await reAuth_async(config)          # 동일 (캐시 우선)
print(token["access_token"], token["access_token_token_expired"])
```

두 함수 모두 **유효한 캐시 토큰이 있으면 네트워크를 타지 않습니다.** KIS는 1일 1회 발급이 원칙이고, 만료 전 재발급을 요청하면 기존 토큰을 그대로 돌려주므로 호출만 낭비됩니다.

## 예외

| 예외 | 발생 조건 |
|---|---|
| `ImportError` | aiohttp 미설치 (`pip install aiohttp`) |
| `RuntimeError` | 토큰 발급 실패 (HTTP 200이 아닌 응답) |
| `ValueError` | 필수 매개변수 누락, 또는 `paper`/`base_url` 모순 |

토큰 발급 실패는 조용히 `None`을 반환하지 않고 예외를 던집니다. 인증 실패를 감추면 이후 모든 호출이 영문 모를 401로 실패하기 때문입니다.

전체 예제는 [`examples/async_auth_example.py`](https://github.com/unohee/kis-agent/blob/main/examples/async_auth_example.py)를 참고하세요.
