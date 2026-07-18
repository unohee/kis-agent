"""WSSubscriptionMixin의 남은 시장별 편의 구독 경로 테스트."""

from kis_agent.websocket.ws_subscriptions import WSSubscriptionMixin


class _Host(WSSubscriptionMixin):
    def __init__(self):
        self.subscriptions = {}
        self.calls = []

    def subscribe(self, sub_type, key, handler=None, **metadata):
        sub_id = f"{sub_type.value}_{key}"
        self.subscriptions[sub_id] = object()
        self.calls.append(sub_id)
        return sub_id

    def unsubscribe(self, sub_id):
        self.calls.append(f"unsub:{sub_id}")
        self.subscriptions.pop(sub_id, None)


def test_all_market_convenience_subscriptions_and_unsubscribe():
    host = _Host()
    assert len(host.subscribe_stock("005930", with_orderbook=True, with_expected=True, with_program=True, with_member=True)) == 5
    assert len(host.subscribe_stocks(["000660", "035420"], with_orderbook=True)) == 4
    assert len(host.subscribe_stock_nxt("005930", with_orderbook=True, with_expected=True, with_program=True, with_member=True)) == 5
    assert len(host.subscribe_stocks_nxt(["000660", "035420"], with_orderbook=True)) == 4
    host.subscribe_market_operation_nxt()
    assert len(host.subscribe_program_trading_nxt(["005930", "000660"])) == 2
    assert len(host.subscribe_member_trading_nxt(["005930", "000660"])) == 2
    assert len(host.subscribe_index(with_expected=True)) == 6
    assert len(host.subscribe_program_trading(["005930"])) == 1
    assert len(host.subscribe_member_trading(["005930"])) == 1
    assert len(host.subscribe_futures("101S03", with_orderbook=True)) == 2
    assert len(host.subscribe_options("201S340", with_orderbook=True)) == 2
    assert len(host.subscribe_stock_futures("111V06", with_orderbook=True, with_expected=True)) == 3
    assert len(host.subscribe_stock_options("211V05059", with_orderbook=True, with_expected=True)) == 3
    assert len(host.subscribe_overtime("005930", with_expected=True)) == 3
    assert len(host.subscribe_overseas_stock("AAPL", with_orderbook=True)) == 2
    assert len(host.subscribe_overseas_futures("ESM25", with_orderbook=True)) == 2
    host.unsubscribe_stock_nxt("005930")
    host.unsubscribe_stock("005930")
    host.unsubscribe_all()
    assert not host.subscriptions
