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
    STOCK_TRADE = "H0STCNT0"       # 국내주식 실시간 체결가 (KRX)
    STOCK_ASK_BID = "H0STASP0"     # 국내주식 실시간 호가 (KRX)
    STOCK_EXPECTED = "H0UNANC0"    # 국내주식 실시간 예상체결 (통합)
    STOCK_NOTICE = "H0STCNI0"      # 국내주식 체결통보
    STOCK_NOTICE_AH = "H0STCNI9"   # 국내주식 시간외 체결통보

    # 국내주식 시간외 (KRX)
    OVERTIME_ASK_BID = "H0STOAA0"  # 시간외 단일가 호가
    OVERTIME_TRADE = "H0STOUP0"    # 시간외 단일가 체결
    OVERTIME_EXPECTED = "H0STOAC0" # 시간외 단일가 예상체결

    # 국내주식 실시간 (NXT)
    STOCK_TRADE_NXT = "H0NXCNT0"       # 국내주식 실시간 체결가 (NXT)
    STOCK_ASK_BID_NXT = "H0NXASP0"     # 국내주식 실시간 호가 (NXT)
    STOCK_EXPECTED_NXT = "H0NXANC0"    # 국내주식 실시간 예상체결 (NXT)
    PROGRAM_TRADE_NXT = "H0NXPGM0"     # 국내주식 실시간 프로그램매매 (NXT)
    MARKET_OPERATION_NXT = "H0NXMKO0"  # 국내주식 장운영정보 (NXT)
    MEMBER_TRADE_NXT = "H0NXMBC0"      # 국내주식 실시간 회원사 (NXT)

    # 지수 실시간
    INDEX = "H0UPCNT0"          # 국내지수 실시간 체결 (수정: H0IF1000 → H0UPCNT0)
    INDEX_EXPECTED = "H0UPANC0" # 지수 실시간 예상체결

    # 프로그램매매/회원사 (KRX)
    PROGRAM_TRADE = "H0STPGM0"  # 프로그램매매 실시간 (KRX)
    MEMBER_TRADE = "H0STMBC0"   # 회원사별 실시간 매매동향 (수정: H0MBCNT0 → H0STMBC0)

    # 지수선물/옵션
    INDEX_FUTURES_TRADE = "H0IFCNT0"    # 지수선물 실시간 체결
    INDEX_FUTURES_ASK_BID = "H0IFASP0" # 지수선물 실시간 호가
    INDEX_OPTION_TRADE = "H0IOCNT0"     # 지수옵션 실시간 체결 (수정: H0OPCNT0 → H0IOCNT0)
    INDEX_OPTION_ASK_BID = "H0IOASP0"  # 지수옵션 실시간 호가 (수정: H0OPASP0 → H0IOASP0)
    FUOPT_NOTICE = "H0IFCNI0"           # 선물옵션 체결통보

    # 상품선물 (KRX)
    COMMODITY_FUTURES_TRADE = "H0CFCNT0"    # 상품선물 실시간 체결
    COMMODITY_FUTURES_ASK_BID = "H0CFASP0" # 상품선물 실시간 호가

    # 주식선물/옵션
    STOCK_FUTURES_TRADE = "H0ZFCNT0"       # 주식선물 실시간 체결
    STOCK_FUTURES_ASK_BID = "H0ZFASP0"    # 주식선물 실시간 호가
    STOCK_FUTURES_EXPECTED = "H0ZFANC0"   # 주식선물 실시간 예상체결
    STOCK_OPTION_TRADE = "H0ZOCNT0"        # 주식옵션 실시간 체결
    STOCK_OPTION_ASK_BID = "H0ZOASP0"     # 주식옵션 실시간 호가
    STOCK_OPTION_EXPECTED = "H0ZOANC0"    # 주식옵션 실시간 예상체결

    # KRX 야간선물/옵션
    NIGHT_FUTURES_TRADE = "H0MFCNT0"       # 야간선물 체결
    NIGHT_FUTURES_ASK_BID = "H0MFASP0"    # 야간선물 호가
    NIGHT_FUTURES_NOTICE = "H0MFCNI0"     # 야간선물 체결통보
    NIGHT_OPTION_TRADE = "H0EUCNT0"        # 야간옵션 체결
    NIGHT_OPTION_ASK_BID = "H0EUASP0"     # 야간옵션 호가
    NIGHT_OPTION_EXPECTED = "H0EUANC0"    # 야간옵션 예상체결
    NIGHT_OPTION_NOTICE = "H0EUCNI0"      # 야간옵션 체결통보

    # 해외주식
    OVERSEAS_STOCK = "HDFSCNT0"             # 해외주식 실시간 체결
    OVERSEAS_STOCK_ASK_BID = "HDFSASP0"    # 해외주식 실시간 호가 (미국 1호가 무료)
    OVERSEAS_STOCK_ASK_BID_ASIA = "HDFSASP1"  # 해외주식 지연호가 (아시아)
    OVERSEAS_STOCK_NOTICE = "H0GSCNI0"     # 해외주식 체결통보
    OVERSEAS_STOCK_NOTICE_AH = "H0GSCNI9"  # 해외주식 시간외 체결통보

    # 해외선물옵션
    OVERSEAS_FUTURES = "HDFFF020"           # 해외선물옵션 실시간 체결
    OVERSEAS_FUTURES_ASK_BID = "HDFFF010"  # 해외선물옵션 실시간 호가
    OVERSEAS_FUTURES_NOTICE = "HDFFF2C0"   # 해외선물옵션 체결통보
    OVERSEAS_FUTURES_ORDER_NOTICE = "HDFFF1C0"  # 해외선물옵션 주문통보


@dataclass
class Subscription:
    """구독 정보"""

    sub_type: SubscriptionType
    key: str  # 종목코드 또는 지수코드
    handler: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
