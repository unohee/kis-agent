"""WebSocket 헬퍼의 미노출 파서·저장소 경로 테스트."""

from kis_agent.websocket.ws_helpers import RealtimeDataParser, RealtimeDataStore, WSAgentWithStore
from kis_agent.websocket.ws_types import SubscriptionType


def test_parser_empty_and_orderbook_wrapper():
    assert RealtimeDataParser._convert_value("", "stck_prpr") is None
    assert RealtimeDataParser.parse_stock_orderbook(["005930", "090000", "0", "70000"])["askp1"] == 70000


def test_store_empty_history_and_auto_store_handlers():
    store = RealtimeDataStore(max_history=1)
    assert store.get_history("missing", SubscriptionType.STOCK_TRADE) == []
    agent = WSAgentWithStore("approval", keep_history=True, url="ws://example", auto_reconnect=False)
    handler = agent._base_agent.type_handlers[SubscriptionType.STOCK_TRADE][0]
    handler(["005930", "090000", "70000"], {})
    handler({"stck_prpr": 71000}, {"tr_key": "005930"})
    handler("raw", {"tr_key": "000660"})
    assert agent.store.get_trade("005930")["stck_prpr"] == 71000
    assert agent.store.get( "000660", SubscriptionType.STOCK_TRADE)["raw"] == "raw"
