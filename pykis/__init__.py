"""
pykis - 한국투자증권 OpenAPI Python Wrapper

이 모듈은 한국투자증권 OpenAPI를 통해 다음과 같은 기능을 제공합니다:
- 주식 시세 조회 (국내/해외)
- 계좌 정보 조회 (잔고, 주문 가능 금액 등)
- 시장 분석 (체결강도, 등락률 순위 등)
- 프로그램 매매 정보 조회
- 조건검색식 종목 조회 (통일된 API 방식)
- 휴장일 정보 조회
- 재무정보 (손익계산서, 재무비율 등)

✅ 주요 클래스:
- Agent: 모든 API 기능을 통합 제공하는 메인 클래스 (Facade 패턴)

🔗 기본 사용법:
```python
from pykis import Agent

# Agent 초기화
agent = Agent()

# 주식 현재가 조회
price = agent.get_stock_price("005930")  # 삼성전자

# 계좌 잔고 조회
balance = agent.get_balance()

# 조건검색 결과 조회 (v0.1.8에서 통일됨)
condition_stocks = agent.get_condition_stocks("unohee", 0, "N")

# 휴장일 정보 조회 (v0.1.8에서 새로 추가됨)
holiday_info = agent.get_holiday_info()
is_holiday = agent.is_holiday("20241225")
```

📊 최신 업데이트 (v0.1.8):
- 조건검색 API 통일 (tr_id="HHKST03900400")
- 휴장일 기능 추가 (get_holiday_info, is_holiday)
- Facade 패턴 일관성 강화
- 모든 기능을 Agent를 통해 접근하도록 아키텍처 개선
"""

# 메인 클래스 - 모든 기능을 통합 제공
from .core.agent import Agent

# 하위 호환성을 위한 기타 클래스들
from .core.client import KISClient
from .core.config import KISConfig
from .account import AccountAPI, AccountBalance
from .program import ProgramAPI, ProgramTrade
from .stock import StockAPI, ConditionAPI, MarketAPI

__version__ = "0.1.10"

# Agent를 메인 클래스로 강조
__all__ = [
    # Core
    "Agent",
    "KISClient",
    "KISConfig",
    
    # Account
    "AccountAPI",
    
    # Program
    "ProgramTrade",

    # Stock
    "StockAPI",
    "ConditionAPI", 
    "MarketAPI",
]
