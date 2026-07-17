---
title: KIS-Agent — 한국투자증권 OpenAPI Python SDK & CLI
description: 한국투자증권 OpenAPI를 위한 Python 래퍼 라이브러리. CLI·Python SDK·LLM Agent·MCP 서버를 통해 국내/해외 주식, 선물옵션, 실시간 WebSocket 시세와 자동매매를 지원합니다.
keywords: 한국투자증권, KIS OpenAPI, Python, SDK, CLI, kis-agent, 주식 API, 자동매매, 트레이딩, WebSocket, LLM Agent, MCP, pykis, 국내주식, 해외주식, 선물옵션
---

# KIS-Agent — 한국투자증권 OpenAPI Python 래퍼

**CLI와 Python SDK로 쉽게 쓰는 한국투자증권 OpenAPI** — 국내·해외 주식, 선물옵션, 실시간 WebSocket, LLM Agent 연동까지.

[![PyPI version](https://badge.fury.io/py/kis-agent.svg)](https://pypi.org/project/kis-agent/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/kis-agent.svg)](https://pypi.org/project/kis-agent/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 주요 특징

- **CLI 도구** — `pip install kis-agent` 하면 `kis` 명령이 바로 설치됩니다
- **LLM Agent 연동** — JSON 출력 + 스키마 탐색으로 AI 에이전트 도구로 활용
- **모의투자** — `paper=True` 하나로 URL과 모의투자 TR_ID를 함께 전환
- **고성능** — 지능형 캐싱으로 API 호출 80-95% 감소
- **실시간** — WebSocket을 통한 실시간 데이터 스트리밍
- **국내시장** — KOSPI, KOSDAQ, NXT(넥스트) 시장 지원
- **해외시장** — 미국, 일본, 중국, 홍콩, 베트남 9개 거래소 지원
- **선물옵션** — 국내/해외 선물옵션 거래 지원
- **타입 안정성** — 96개 TypedDict 응답 모델, 100% 타입힌팅

## 빠른 설치

```bash
pip install kis-agent
```

## 30초 만에 시작하기

### CLI

```bash
kis price 005930                    # 삼성전자 현재가
kis balance --holdings              # 계좌 잔고 + 보유종목
kis overseas NAS AAPL               # AAPL 시세
kis futures 101S03                  # 선물 시세
```

### Python

```python
from kis_agent import Agent
import os

agent = Agent(
    app_key=os.environ['KIS_APP_KEY'],
    app_secret=os.environ['KIS_APP_SECRET'],
    account_no=os.environ['KIS_ACCOUNT_NO'],
    account_code=os.environ.get('KIS_ACCOUNT_CODE', '01'),
)

price = agent.get_stock_price("005930")
print(f"삼성전자 현재가: {price['output']['stck_prpr']}원")
```

## 다음 단계

- [설치 및 설정](getting-started/installation.md) — API 키 발급부터 환경 설정까지
- [빠른 시작](getting-started/quickstart.md) — 주요 기능을 코드 예제로 살펴보기
- [CLI 사용법](cli/usage.md) — 터미널에서 바로 사용하는 방법
