"""
WebSocket 모듈

실시간 데이터를 처리하는 WebSocket 클라이언트 모듈입니다.
리팩토링된 버전과 기존 버전 모두 제공합니다.
"""

# 기존 클라이언트 (하위 호환성)
from .client import KisWebSocket
from .ws_agent import WSAgent, SubscriptionType
from .enhanced_client import EnhancedWebSocketClient

# 리팩토링된 모듈
from .refactored_client import RefactoredWebSocketClient
from .connection import ConnectionManager
from .data_processor import DataProcessor
from .event_manager import EventManager, EventType, Event
from .message_handlers import (
    MessageHandler,
    TradeHandler,
    OrderbookHandler,
    IndexHandler,
    ProgramTradingHandler,
    MessageHandlerRegistry,
)
from .factory import WebSocketClientFactory, WebSocketClientBuilder, ClientType

__all__ = [
    # 기존 클라이언트
    "KisWebSocket",
    "WSAgent",
    "SubscriptionType",
    "EnhancedWebSocketClient",
    # 리팩토링된 모듈
    "RefactoredWebSocketClient",
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
    "WebSocketClientFactory",
    "WebSocketClientBuilder",
    "ClientType",
]
