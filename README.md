# KIS_AGENT

한국투자증권 API를 Python으로 쉽게 사용할 수 있는 래퍼 라이브러리입니다.

## 설치 방법

```bash
pip install kis-agent
```

## 주요 기능

- 계좌 잔고 조회
- 주식 시세 조회
- 프로그램 매매 정보 조회
- 조건검색식 종목 조회
- 실시간 시세 조회

## 사용 예시

```python
from kis.agent import KIS_Agent

# KIS_Agent 초기화
agent = KIS_Agent(account_info={
    'CANO': '계좌번호',
    'ACNT_PRDT_CD': '계좌상품코드'
})

# 주식 가격 조회
price = agent.get_stock_price("005930")  # 삼성전자

# 계좌 잔고 조회
balance = agent.get_account_balance()
```

## 개발 환경 설정

1. 저장소 클론
```bash
git clone https://github.com/your-username/kis-agent.git
cd kis-agent
```

2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. API 인증 정보 설정
- `credit/kis_devlp.yaml` 파일에 API 인증 정보를 설정합니다.

## 테스트 실행

```bash
pytest tests/
```