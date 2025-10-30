"""
PyKIS Response Types Package

한국투자증권 OpenAPI의 응답 구조를 TypedDict로 정의한 타입 힌팅 전용 패키지

이 패키지는 런타임 동작에 영향을 주지 않으며, 순수하게 타입 체크 및 IDE 자동완성을 위한 용도입니다.

주요 모듈:
- common: BaseResponse 등 공통 응답 구조
- stock: 주식 시세, 호가, 분봉 등 Stock API 응답
- account: 계좌 잔고, 체결내역 등 Account API 응답
- order: 주문 실행, 정정/취소 등 Order API 응답

사용 예시:
    from pykis.responses.stock import StockPriceResponse

    def get_stock_price(code: str) -> StockPriceResponse:
        # API 호출 로직
        return response
"""

# Common types
from .common import BaseResponse, OutputField

# Stock-related responses
from .stock import (
    DailyPriceItem,
    DailyPriceResponse,
    InquireCcnlItem,
    InquireCcnlResponse,
    InquireTimeItemconclusionOutput1,
    InquireTimeItemconclusionOutput2,
    InquireTimeItemconclusionResponse,
    MinutePriceItem,
    MinutePriceResponse,
    OrderbookOutput,
    OrderbookResponse,
    SearchStockInfoOutput,
    SearchStockInfoResponse,
    StockInvestorOutput,
    StockInvestorResponse,
    StockPriceOutput,
    StockPriceResponse,
)

# Account-related responses
from .account import (
    AccountBalanceOutput1Item,
    AccountBalanceOutput2,
    AccountBalanceResponse,
    GetTotalAssetOutput1,
    GetTotalAssetOutput2,
    GetTotalAssetResponse,
    InquireBalanceRlzPlOutput1Item,
    InquireBalanceRlzPlResponse,
    InquireDailyCcldOutput1Item,
    InquireDailyCcldOutput2,
    InquireDailyCcldResponse,
    InquirePeriodTradeProfitOutput1Item,
    InquirePeriodTradeProfitOutput2,
    InquirePeriodTradeProfitResponse,
    InquirePsblSellOutput,
    InquirePsblSellResponse,
    PossibleOrderOutput,
    PossibleOrderResponse,
)

# Order-related responses
from .order import (
    InquirePsblRvsecnclItem,
    InquirePsblRvsecnclResponse,
    OrderCashOutput,
    OrderCashResponse,
    OrderCreditBuyOutput,
    OrderCreditBuyResponse,
    OrderCreditSellOutput,
    OrderCreditSellResponse,
    OrderResvCcnlItem,
    OrderResvCcnlResponse,
    OrderResvOutput,
    OrderResvResponse,
    OrderResvRvsecnclOutput,
    OrderResvRvsecnclResponse,
    OrderRvsecnclOutput,
    OrderRvsecnclResponse,
)

__all__ = [
    # Common
    "BaseResponse",
    "OutputField",
    # Stock
    "StockPriceResponse",
    "StockPriceOutput",
    "DailyPriceResponse",
    "DailyPriceItem",
    "OrderbookResponse",
    "OrderbookOutput",
    "MinutePriceResponse",
    "MinutePriceItem",
    "StockInvestorResponse",
    "StockInvestorOutput",
    "InquireTimeItemconclusionResponse",
    "InquireTimeItemconclusionOutput1",
    "InquireTimeItemconclusionOutput2",
    "InquireCcnlResponse",
    "InquireCcnlItem",
    "SearchStockInfoResponse",
    "SearchStockInfoOutput",
    # Account
    "AccountBalanceResponse",
    "AccountBalanceOutput1Item",
    "AccountBalanceOutput2",
    "PossibleOrderResponse",
    "PossibleOrderOutput",
    "InquireDailyCcldResponse",
    "InquireDailyCcldOutput1Item",
    "InquireDailyCcldOutput2",
    "InquirePsblSellResponse",
    "InquirePsblSellOutput",
    "GetTotalAssetResponse",
    "GetTotalAssetOutput1",
    "GetTotalAssetOutput2",
    "InquireBalanceRlzPlResponse",
    "InquireBalanceRlzPlOutput1Item",
    "InquirePeriodTradeProfitResponse",
    "InquirePeriodTradeProfitOutput1Item",
    "InquirePeriodTradeProfitOutput2",
    # Order
    "OrderCashResponse",
    "OrderCashOutput",
    "OrderCreditBuyResponse",
    "OrderCreditBuyOutput",
    "OrderCreditSellResponse",
    "OrderCreditSellOutput",
    "OrderRvsecnclResponse",
    "OrderRvsecnclOutput",
    "InquirePsblRvsecnclResponse",
    "InquirePsblRvsecnclItem",
    "OrderResvResponse",
    "OrderResvOutput",
    "OrderResvRvsecnclResponse",
    "OrderResvRvsecnclOutput",
    "OrderResvCcnlResponse",
    "OrderResvCcnlItem",
]

__version__ = "1.3.0"
