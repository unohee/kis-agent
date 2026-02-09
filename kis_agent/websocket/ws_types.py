"""
WebSocket 타입 정의

순환 참조 방지를 위해 공통 타입을 별도 모듈로 분리:
- SubscriptionType: 실시간 구독 타입 enum
- Subscription: 구독 정보 dataclass
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional


class SubscriptionType(Enum):
    """실시간 구독 타입: KRX(STOCK_*), NXT(*_NXT), 지수(INDEX*), 선물옵션, 해외"""

    # 국내주식 실시간 (KRX)
    STOCK_TRADE = "H0STCNT0"  # 국내주식 실시간 체결가 (KRX)
    STOCK_ASK_BID = "H0STASP0"  # 국내주식 실시간 호가 (KRX)
    STOCK_EXPECTED = "H0UNANC0"  # 국내주식 실시간 예상체결 (통합)
    STOCK_NOTICE = "H0STCNI0"  # 국내주식 체결통보
    STOCK_NOTICE_AH = "H0STCNI9"  # 국내주식 시간외 체결통보

    # 국내주식 실시간 (NXT)
    STOCK_TRADE_NXT = "H0NXCNT0"  # 국내주식 실시간 체결가 (NXT)
    STOCK_ASK_BID_NXT = "H0NXASP0"  # 국내주식 실시간 호가 (NXT)
    STOCK_EXPECTED_NXT = "H0NXANC0"  # 국내주식 실시간 예상체결 (NXT)
    PROGRAM_TRADE_NXT = "H0NXPGM0"  # 국내주식 실시간 프로그램매매 (NXT)
    MARKET_OPERATION_NXT = "H0NXMKO0"  # 국내주식 장운영정보 (NXT)
    MEMBER_TRADE_NXT = "H0NXMBC0"  # 국내주식 실시간 회원사 (NXT)

    # 지수 실시간
    INDEX = "H0IF1000"  # 지수 실시간
    INDEX_EXPECTED = "H0UPANC0"  # 지수 실시간 예상체결

    # 프로그램매매/회원사 (KRX)
    PROGRAM_TRADE = "H0STPGM0"  # 프로그램매매 실시간 (KRX)
    MEMBER_TRADE = "H0MBCNT0"  # 회원사별 실시간 매매동향

    # 선물/옵션
    FUTURES_TRADE = "H0CFCNT0"  # 선물 체결
    FUTURES_ASK_BID = "H0CFASP0"  # 선물 호가
    OPTION_TRADE = "H0OPCNT0"  # 옵션 체결
    OPTION_ASK_BID = "H0OPASP0"  # 옵션 호가

    # 해외
    OVERSEAS_STOCK = "HDFSCNT0"  # 해외주식 체결
    OVERSEAS_FUTURES = "HDFFF020"  # 해외선물 체결


@dataclass
class Subscription:
    """구독 정보"""

    sub_type: SubscriptionType
    key: str  # 종목코드 또는 지수코드
    handler: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
