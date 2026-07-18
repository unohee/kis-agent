"""WebSocket 전략 핸들러의 파싱 및 라우팅 테스트."""

from kis_agent.websocket.message_handlers import (
    IndexHandler,
    MessageHandlerRegistry,
    OrderbookHandler,
    PingPongHandler,
    ProgramTradingHandler,
    TradeHandler,
)


class _BaseProbe(TradeHandler):
    """추상 기반 구현의 기본 반환값을 직접 검증하는 최소 서브클래스."""

    def can_handle(self, message):
        from kis_agent.websocket.message_handlers import MessageHandler

        return MessageHandler.can_handle(self, message)

    def handle(self, message):
        from kis_agent.websocket.message_handlers import MessageHandler

        return MessageHandler.handle(self, message)


def test_individual_handlers_parse_messages_and_empty_output():
    trade = TradeHandler()
    assert trade.can_handle({"header": {"tr_id": "H0STCNT0"}})
    assert not trade.can_handle({})
    assert trade.handle({"body": {}}) is None
    assert trade.handle({"body": {"output": {"stck_shrn_iscd": "005930", "stck_prpr": "10", "prdy_vrss": "1", "prdy_ctrt": "0.1", "acml_vol": "2", "acml_tr_pbmn": "20", "stck_cntg_hour": "090000"}}})["type"] == "trade"

    orderbook = OrderbookHandler()
    assert orderbook.can_handle({"tr_id": "H0STASP0"})
    assert orderbook.handle({"body": {}}) is None
    result = orderbook.handle({"body": {"output": {"stck_shrn_iscd": "005930", "askp1": "11", "askp_rsqn1": "2", "bidp1": "10"}}})
    assert result["asks"] == [{"price": 11, "volume": 2}]
    assert result["bids"] == [{"price": 10, "volume": 0}]

    index = IndexHandler()
    assert index.can_handle({"header": {"tr_id": "H0IF1000"}})
    assert index.handle({"body": {}}) is None
    result = index.handle({"header": {"tr_key": "0001"}, "body": {"output": {"bstp_nmix_prpr": "1", "bstp_nmix_prdy_vrss": "2", "prdy_vrss_sign": "3", "bstp_nmix_hgpr": "4", "bstp_nmix_lwpr": "0", "acml_vol": "5"}}})
    assert result["name"] == "KOSPI" and result["volume"] == 5

    program = ProgramTradingHandler()
    assert program.can_handle({"tr_id": "H0GSCNT0"})
    assert program.handle({"body": {}}) is None
    assert program.handle({"body": {"output": {"stck_shrn_iscd": "005930", "seln_pbmn": "1", "shnu_pbmn": "2", "ntby_pbmn": "3", "seln_vol": "4", "shnu_vol": "5", "ntby_vol": "6"}}})["net_volume"] == 6
    assert PingPongHandler().handle({"type": "PINGPONG"})["type"] == "PONG"


def test_registry_routes_default_and_unknown_messages():
    assert _BaseProbe().can_handle({}) is None
    assert _BaseProbe().handle({}) is None
    registry = MessageHandlerRegistry()
    assert len(registry.handlers) == 5
    assert registry.process({"tr_id": "H0STCNT0", "body": {"output": {"stck_prpr": "0"}}})["type"] == "trade"
    assert registry.process({"header": {"tr_id": "PINGPONG"}})["type"] == "PONG"
    assert registry.process({"tr_id": "unknown"}) is None
    registry.set_default_handler(lambda message: {"type": "default", "source": message["tr_id"]})
    assert registry.process({"tr_id": "unknown"}) == {"type": "default", "source": "unknown"}
