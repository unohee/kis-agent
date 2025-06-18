"""
pyKis - 한국투자증권 OpenAPI Python Wrapper

이 모듈은 한국투자증권 OpenAPI를 통해 다음과 같은 기능을 제공합니다:
- 주식 시세 조회
- 계좌 정보 조회
- 프로그램 매매 분석
- 전략 실행
- 조건검색식 종목 조회
- 시장 정보 조회

✅ 주요 클래스:
- Agent: 모든 API 기능을 통합 제공하는 메인 클래스

🔗 사용법:
from pykis import Agent
agent = Agent()

# 주식 시세 조회
price = agent.get_stock_price("005930")

# 계좌 잔고 조회
balance = agent.get_account_balance()

# 프로그램 매매 정보 조회
program_info = agent.get_program_trade_summary("005930")

# 조건검색식 종목 조회
condition_stocks = agent.get_condition_stocks()
"""

# 메인 클래스 - 모든 기능을 통합 제공
from .core.agent import Agent

# 하위 호환성을 위한 기타 클래스들
from .core.client import KISClient
from .core.config import KISConfig
from .account import AccountAPI, AccountBalance
from .program import ProgramAPI, ProgramTrade
from .stock import StockData, StockAPI, ConditionAPI, MarketAPI, ProgramTradeAPI

__version__ = "0.1.0"

# Agent를 메인 클래스로 강조
__all__ = [
    "Agent",  # 메인 클래스
    # 하위 호환성을 위한 기타 클래스들
    "KISClient",
    "KISConfig",
    "AccountAPI",
    "AccountBalance",
    "ProgramAPI",
    "ProgramTrade",
    "StockData",
    "StockAPI",
    "ConditionAPI",
    "MarketAPI",
    "ProgramTradeAPI"
]
