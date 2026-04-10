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
KIS_SECRET=발급받은_시크릿      # 또는 KIS_APP_SECRET
KIS_ACCOUNT_NO=계좌번호
KIS_ACCOUNT_CODE=01
```

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

`Agent` 초기화 시 `base_url` 파라미터로 전환합니다:

```python
from kis_agent import Agent

# 실전투자 (기본값)
agent = Agent(
    app_key=os.environ['KIS_APP_KEY'],
    app_secret=os.environ['KIS_APP_SECRET'],
    account_no=os.environ['KIS_ACCOUNT_NO'],
    account_code=os.environ.get('KIS_ACCOUNT_CODE', '01'),
)

# 모의투자
agent = Agent(
    app_key=os.environ['KIS_APP_KEY'],
    app_secret=os.environ['KIS_APP_SECRET'],
    account_no=os.environ['KIS_ACCOUNT_NO'],
    account_code=os.environ.get('KIS_ACCOUNT_CODE', '01'),
    base_url="https://openapivts.koreainvestment.com:29443",
)
```

!!! note "모의투자 먼저"
    처음에는 반드시 모의투자(`base_url` 변경)로 테스트한 후 실전투자로 전환하세요.
