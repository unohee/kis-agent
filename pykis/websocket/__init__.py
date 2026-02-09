"""
WebSocket 모듈

실시간 데이터를 처리하는 WebSocket 클라이언트 모듈입니다.

권장 사용법::

    from pykis.websocket import WSAgent, WSAgentWithStore, SubscriptionType

    # 기본 사용
    ws = WSAgent(approval_key)
    ws.subscribe_stock("005930")
    await ws.connect()

    # 데이터 저장소 포함
    ws = WSAgentWithStore(approval_key, keep_history=True)
    ws.subscribe_stocks(["005930", "000660"])
    await ws.connect()

.. deprecated:: 1.3.0
    KisWebSocket, EnhancedWebSocketClient, RefactoredWebSocketClient,
    WebSocketClientFactory, WebSocketClientBuilder는 deprecated되었습니다.
    대신 WSAgent 또는 WSAgentWithStore를 사용하세요.
"""

# ============================================
# 권장 API (WSAgent 기반)
# ============================================
# ============================================
# Deprecated API (하위 호환성 유지)
# ============================================
from .client import KisWebSocket  # deprecated: use WSAgent

# ============================================
# 지원 모듈 (WSAgent 내부에서 사용)
# ============================================
from .connection import ConnectionManager
from .data_processor import DataProcessor
from .enhanced_client import EnhancedWebSocketClient  # deprecated: use WSAgentWithStore
from .event_manager import Event, EventManager, EventType
from .factory import (
    ClientType,
    WebSocketClientBuilder,
    WebSocketClientFactory,
)  # deprecated
from .message_handlers import (
    IndexHandler,
    MessageHandler,
    MessageHandlerRegistry,
    OrderbookHandler,
    ProgramTradingHandler,
    TradeHandler,
)
from .refactored_client import RefactoredWebSocketClient  # deprecated: use WSAgent
from .ws_agent import WSAgent
from .ws_helpers import RealtimeDataParser, RealtimeDataStore, WSAgentWithStore
from .ws_types import Subscription, SubscriptionType

__all__ = [
    # ============================================
    # 권장 API (WSAgent 기반) - Primary
    # ============================================
    "WSAgent",
    "WSAgentWithStore",
    "SubscriptionType",
    "Subscription",
    "RealtimeDataParser",
    "RealtimeDataStore",
    # ============================================
    # 지원 모듈
    # ============================================
    "ConnectionManager",
    "DataProcessor",
    "EventManager",
    "EventType",
    "Event",
    "MessageHandler",
    "TradeHandler",
    "OrderbookHandler",
    "IndexHandler",
    "ProgramTradingHandler",
    "MessageHandlerRegistry",
    # ============================================
    # Deprecated API (하위 호환성)
    # ============================================
    "KisWebSocket",  # deprecated
    "EnhancedWebSocketClient",  # deprecated
    "RefactoredWebSocketClient",  # deprecated
    "WebSocketClientFactory",  # deprecated
    "WebSocketClientBuilder",  # deprecated
    "ClientType",  # deprecated
]
