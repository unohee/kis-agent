# 모의투자

실제 돈 없이 한국투자증권 모의투자 서버로 주문·조회를 테스트합니다. v1.8.0부터 지원합니다.

## 시작하기

모의투자는 **실전과 별도의 APP KEY / APP SECRET / 계좌번호**가 필요합니다. [KIS API 포털](https://apiportal.koreainvestment.com)에서 모의투자용으로 따로 신청하세요. 실전 키로는 모의투자 서버에 접속할 수 없습니다.

`.env`에 모의투자 자격증명과 `KIS_PAPER=1`을 넣습니다:

```bash
KIS_PAPER=1
KIS_APP_KEY=모의투자_앱키
KIS_APP_SECRET=모의투자_시크릿
KIS_ACCOUNT_NO=모의투자_계좌번호
KIS_ACCOUNT_CODE=01
```

이것만으로 CLI와 Python 양쪽 모두 모의투자로 동작합니다.

=== "CLI"

    ```bash
    kis balance
    kis price 005930
    ```

=== "Python"

    ```python
    from kis_agent import Agent

    agent = Agent(
        app_key=os.environ["KIS_APP_KEY"],
        app_secret=os.environ["KIS_APP_SECRET"],
        account_no=os.environ["KIS_ACCOUNT_NO"],
        account_code="01",
        paper=True,          # .env에 KIS_PAPER=1이 있으면 생략 가능
    )
    print(agent.is_real)     # False
    ```

`paper=True`는 모의투자 URL과 **모의투자 전용 TR_ID**를 함께 적용합니다. 둘 중 하나만 맞으면 서버가 요청을 거절하므로 한 번에 처리됩니다.

전체 예제는 [`examples/paper_trading.py`](https://github.com/unohee/kis-agent/blob/main/examples/paper_trading.py)를 참고하세요.

## 모의투자에서 쓸 수 없는 API

!!! warning "KIS는 전체 336개 API 중 43개만 모의투자로 제공합니다"

    라이브러리 제약이 아니라 **한국투자증권 서버의 제약**입니다. 아래는 모의투자에서 사용할 수 없습니다:

    - 해외선물옵션 **전량**
    - 장내채권 **전량**
    - 순위분석 / 투자자매매동향 / 프로그램매매 **전량**
    - 재무·실적, 예탁원정보, ELW(현재가 시세 제외)
    - 국내휴장일 조회, 조건검색, 관심종목
    - 선물옵션 **야간** 세션 (주간 주문만 지원)
    - 해외주식 미체결내역, 기간손익, 예약주문 조회

미지원 API를 모의투자로 호출하면 네트워크 요청 없이 즉시 예외가 발생합니다:

```python
from kis_agent.core.tr_mapping import PaperTradingNotSupportedError

try:
    agent.overseas_futures.get_balance()   # 해외선물옵션 — 모의 미지원
except PaperTradingNotSupportedError as e:
    print(e.tr_id)  # 'OTFM3116R'
```

지원 목록의 진실의 출처는 [`kis_agent/core/tr_mapping.py`](https://github.com/unohee/kis-agent/blob/main/kis_agent/core/tr_mapping.py)의 `REAL_TO_PAPER_TR`입니다. 특정 API의 지원 여부는 코드로 확인할 수 있습니다:

```python
from kis_agent.core.tr_mapping import is_paper_supported

is_paper_supported("TTTC8434R")   # True  — 주식잔고조회
is_paper_supported("OTFM3116R")   # False — 해외선물옵션
```

## 실시간 (WebSocket)

모의투자는 WebSocket 서버와 체결통보 TR_ID가 실전과 다릅니다. `get_ws_url()`로 URL을 고르면 나머지는 자동 처리됩니다:

```python
from kis_agent.core.constants import get_ws_url
from kis_agent.websocket import WSAgent, SubscriptionType

ws = WSAgent(approval_key, url=get_ws_url(is_real=False))
ws.subscribe(SubscriptionType.STOCK_NOTICE, account_no)  # H0STCNI9로 자동 변환
```

시세 구독(체결가·호가)은 실전과 모의가 동일한 TR_ID를 쓰므로 그대로 동작합니다.

## 동작 방식

모의투자는 URL만 바꿔서는 동작하지 않습니다. KIS는 모의투자에 **별도의 TR_ID**를 요구합니다:

| 조회 | 실전 | 모의 |
|---|---|---|
| 주식잔고조회 | `TTTC8434R` | `VTTC8434R` |
| 주식주문(현금) 매수 | `TTTC0012U` | `VTTC0012U` |
| 해외주식 미국 매도 | `TTTT1006U` | `VTTT1001U` |
| 국내주식 체결통보 | `H0STCNI0` | `H0STCNI9` |
| 주식현재가 시세 | `FHKST01010100` | `FHKST01010100` (동일) |

변환은 모든 API가 거치는 단일 지점에서 처리되므로 사용자가 신경 쓸 일은 없습니다. 규칙이 일정하지 않다는 점만 알아두면 됩니다 — 시세는 양쪽이 같고, 미국 매도는 앞글자뿐 아니라 숫자까지 바뀌며, 체결통보는 끝자리가 바뀝니다.

## 자주 겪는 문제

**`모의투자 TR 이 아닙니다` (HTTP 500)**

v1.7.0 이하에서 `base_url`만 모의투자로 지정했을 때 발생합니다. v1.8.0으로 올리고 `paper=True` 또는 `KIS_PAPER=1`을 쓰세요. ([#44](https://github.com/unohee/kis-agent/issues/44))

**`paper=True 와 base_url=... 이 서로 모순됩니다` (ValueError)**

`paper=True`와 실전 `base_url`을 함께 넘긴 경우입니다. 잘못된 환경으로 주문이 나가는 것을 막기 위해 의도적으로 실패합니다. 둘 중 하나만 지정하세요 — `paper`를 쓰면 `base_url`은 생략하면 됩니다.

**`'dict' object can't be awaited`**

`get_account_balance()`는 동기 메서드입니다. `await`를 빼세요.

```python
balance = agent.get_account_balance()   # await 불필요
```

**모의투자인데 인증이 실패한다**

실전 APP KEY를 쓰고 있지 않은지 확인하세요. 모의투자 자격증명은 별도로 발급받아야 합니다.
