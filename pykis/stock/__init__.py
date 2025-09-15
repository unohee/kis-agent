"""
Stock API 패키지 - 주식 관련 API 모음

구조적 리팩토링으로 단일 책임 원칙(SRP)을 적용하여 분리:
- StockAPI: Facade 패턴으로 통합 인터페이스 제공 (하위 호환성 유지)
- StockPriceAPI: 시세 조회 전담
- StockMarketAPI: 시장 정보 전담  
- StockInvestorAPI: 투자자 정보 전담
- ConditionAPI: 조건검색 전담
"""

# 새로운 구조화된 API들 (Strategy Pattern 적용)
from .api_facade import StockAPI
from .price_api import StockPriceAPI
from .market_api import StockMarketAPI  
from .investor_api import StockInvestorAPI

# 기존 기능들 (하위 호환성 유지)
from .condition import ConditionAPI
from .investor import InvestorPositionAnalyzer

__all__ = [
    'StockAPI',           # 메인 Facade (Strategy Pattern으로 구현)
    'StockPriceAPI',      # 시세 전담 (SRP 적용)
    'StockMarketAPI',     # 시장 정보 전담 (SRP 적용)
    'StockInvestorAPI',   # 투자자 정보 전담 (SRP 적용)
    'ConditionAPI',       # 조건검색 (BaseAPI 상속)
    'InvestorPositionAnalyzer',  # 기존 유틸리티
]

# 하위 호환 별칭 제거: 레거시 사용 중단 정책
