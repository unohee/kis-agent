# 설치 및 설정

## 사전 준비

### 1. 한국투자증권 OpenAPI 가입

1. [한국투자증권 API 포털](https://apiportal.koreainvestment.com/)에서 회원가입
2. API 서비스 신청 및 승인
3. 앱 등록 후 **App Key**와 **App Secret** 발급
4. 계좌번호(CANO)와 계좌상품코드(ACNT_PRDT_CD) 확인

### 2. Python 환경

- **Python 3.8 이상** 필수
- 가상환경 사용 권장

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

## 설치

### PyPI (권장)

```bash
pip install kis-agent
```

WebSocket, aiohttp, openpyxl은 기본 의존성에 포함되어 별도 설치가 불필요합니다.

### 개발 버전

```bash
git clone https://github.com/unohee/kis-agent.git
cd kis-agent
pip install -e ".[dev]"
```

## 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다:

```bash
KIS_APP_KEY=발급받은_앱키
KIS_APP_SECRET=발급받은_시크릿
KIS_ACCOUNT_NO=계좌번호
KIS_ACCOUNT_CODE=01              # 선택 (기본 "01" = 주식, "03" = 선물옵션)
KIS_PAPER=                       # 선택 (1이면 모의투자)
```

인식하는 변수는 `KIS_*` prefix 전용입니다.

| 변수 | 필수 | 설명 |
|---|---|---|
| `KIS_APP_KEY` | ✅ | APP KEY |
| `KIS_APP_SECRET` | ✅ | APP SECRET |
| `KIS_ACCOUNT_NO` | ✅ | 종합계좌번호 (앞 8자리) |
| `KIS_ACCOUNT_CODE` | | 계좌 상품코드 (기본 `01`) |
| `KIS_PAPER` | | `1`/`true`/`yes`/`on`이면 모의투자 |
| `KIS_BASE_URL` | | 직접 지정 (`KIS_PAPER` 사용 시 불필요) |
| `KIS_TOKEN_PATH` | | 토큰 캐시 경로 |

!!! warning "v1.8.0 Breaking change"
    Legacy 별칭(`MY_APP`, `MY_SEC`, **`KIS_SECRET`**, `MY_ACCT_STOCK`, `MY_PROD`,
    `PROD_URL`, `VPS_URL`, `MY_AGENT`)은 더 이상 인식되지 않습니다.
    특히 `KIS_SECRET`은 `KIS_APP_SECRET`으로 바꿔야 합니다.

!!! warning "보안 주의"
    `.env` 파일을 절대 Git에 커밋하지 마세요. `.gitignore`에 `.env`가 포함되어 있는지 확인하세요.

### 환경 변수 확인

```python
import os
from dotenv import load_dotenv

load_dotenv()
print("App Key:", os.getenv('KIS_APP_KEY')[:10] + "...")
print("Account:", os.getenv('KIS_ACCOUNT_NO'))
```

## 실전투자 vs 모의투자

`Agent` 초기화 시 `paper` 파라미터로 전환합니다 (v1.8.0+):

```python
from kis_agent import Agent

# 실전투자 (기본값)
agent = Agent(
    app_key=os.environ['KIS_APP_KEY'],
    app_secret=os.environ['KIS_APP_SECRET'],
    account_no=os.environ['KIS_ACCOUNT_NO'],
    account_code=os.environ.get('KIS_ACCOUNT_CODE', '01'),
)

# 모의투자 — URL과 모의투자 전용 TR_ID가 함께 적용됩니다
agent = Agent(
    app_key=os.environ['KIS_APP_KEY'],
    app_secret=os.environ['KIS_APP_SECRET'],
    account_no=os.environ['KIS_ACCOUNT_NO'],
    account_code=os.environ.get('KIS_ACCOUNT_CODE', '01'),
    paper=True,
)
```

`.env`에 `KIS_PAPER=1`을 넣으면 `paper` 인자를 생략할 수 있고, CLI에도 동일하게 적용됩니다.

!!! note "모의투자 먼저"
    처음에는 반드시 모의투자로 테스트한 후 실전투자로 전환하세요.
    모의투자는 **실전과 별도의 APP KEY / SECRET / 계좌번호**가 필요하고,
    KIS가 모의로 제공하지 않는 API도 있습니다 — [모의투자 가이드](paper-trading.md) 참고.

!!! warning "v1.7.0 이하에서 올라오는 경우"
    이전에는 `base_url`만 모의투자로 지정했지만, 그 방식은 URL만 바꿀 뿐
    모의투자 TR_ID를 적용하지 않아 모든 호출이 `모의투자 TR 이 아닙니다`로
    실패했습니다 ([#44](https://github.com/unohee/kis-agent/issues/44)).
    `paper=True`를 사용하세요. `base_url` 인자도 계속 동작합니다.
