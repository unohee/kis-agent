"""
Stock API 패키지 - 주식 관련 API 모음

구조적 리팩토링으로 단일 책임 원칙(SRP)을 적용하여 분리:
- StockAPI: Facade 패턴으로 통합 인터페이스 제공 (하위 호환성 유지)
- StockPriceAPI: 시세 조회 전담 (StockIndexAPI 상속)
- StockIndexAPI: 지수/선물 시세 조회 전담
- StockMarketAPI: 시장 정보 전담
- StockInvestorAPI: 투자자 정보 전담
- ConditionAPI: 조건검색 전담
- InterestStockAPI: 관심종목 전담
"""

# 새로운 구조화된 API들 (Strategy Pattern 적용)
from .analysis_api import StockAnalysisAPI
from .api_facade import StockAPI
from .chart_api import StockChartAPI

# 기존 기능들 (하위 호환성 유지)
from .condition import ConditionAPI
from .etf_api import StockEtfAPI
from .finance_api import StockFinanceAPI
from .index_api import StockIndexAPI
from .interest import InterestStockAPI
from .investor import InvestorPositionAnalyzer
from .investor_api import StockInvestorAPI
from .ksdinfo_api import StockKsdInfoAPI
from .market_api import StockMarketAPI
from .price_api import StockPriceAPI
from .ranking_api import StockRankingAPI

# 기존 import (필요시 접근)
try:
    from .api import StockAPI as LegacyStockAPI
    from .api import get_kospi200_futures_code  # 유틸리티 함수
except ImportError:
    LegacyStockAPI = None  # 레거시 클래스가 없을 경우
    get_kospi200_futures_code = None

# 하위 호환성을 위한 별칭
MarketAPI = StockAPI  # 기존 별칭 유지

__all__ = [
    "StockAPI",  # 메인 Facade (Strategy Pattern으로 구현)
    "StockPriceAPI",  # 시세 전담 (SRP 적용, StockIndexAPI 상속)
    "StockIndexAPI",  # 지수/선물 시세 전담 (SRP 적용)
    "StockMarketAPI",  # 시장 정보 전담 (SRP 적용)
    "StockInvestorAPI",  # 투자자 정보 전담 (SRP 적용)
    "StockRankingAPI",  # 순위분석
    "StockAnalysisAPI",  # 시세분석
    "StockFinanceAPI",  # 종목정보·재무
    "StockKsdInfoAPI",  # 예탁원 일정
    "StockEtfAPI",  # ETF/ETN
    "StockChartAPI",  # 분봉·시간외
    "ConditionAPI",  # 조건검색 (BaseAPI 상속)
    "InterestStockAPI",  # 관심종목 (BaseAPI 상속)
    "MarketAPI",  # 기존 별칭 (하위 호환성)
    "InvestorPositionAnalyzer",  # 기존 유틸리티
    "get_kospi200_futures_code",  # 유틸리티 함수
]

# 레거시 지원
if LegacyStockAPI:
    __all__.append("LegacyStockAPI")
