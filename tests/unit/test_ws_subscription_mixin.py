"""WSSubscriptionMixin 회귀 테스트.

`ws_agent.py`가 1500줄 LOC 게이트를 넘겨 편의 메서드 703줄을 믹스인으로 분리했다
(`ws_subscriptions.py`). 순수 이동이므로 **분리 전후로 공개 API가 동일해야** 한다.
이 테스트는 그 등가성을 고정한다 — 메서드가 사라지거나, 믹스인이 상속에서 빠지거나,
잘못된 SubscriptionType으로 위임하면 실패한다.
"""

import warnings

import pytest

from kis_agent.core.constants import WS_MOCK_URL, WS_REAL_URL
from kis_agent.websocket import WSAgent
from kis_agent.websocket.ws_subscriptions import WSSubscriptionMixin
from kis_agent.websocket.ws_types import SubscriptionType


@pytest.fixture
def agent():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return WSAgent(approval_key="key", url=WS_REAL_URL)


class TestMixinWiring:
    def test_ws_agent_inherits_mixin(self):
        assert issubclass(WSAgent, WSSubscriptionMixin)

    def test_mixin_only_depends_on_host_subscribe_api(self, agent):
        """믹스인은 호스트의 subscribe/unsubscribe/subscriptions만 써야 한다."""
        for attr in ("subscribe", "unsubscribe", "subscriptions"):
            assert hasattr(agent, attr)


class TestPublicApiPreserved:
    """분리 전 존재하던 편의 메서드가 전부 남아있어야 한다."""

    MOVED_METHODS = [
        "subscribe_stock",
        "subscribe_stocks",
        "subscribe_stock_nxt",
        "subscribe_stocks_nxt",
        "subscribe_market_operation_nxt",
        "subscribe_program_trading_nxt",
        "subscribe_member_trading_nxt",
        "subscribe_index",
        "subscribe_program_trading",
        "subscribe_member_trading",
        "subscribe_futures",
        "subscribe_options",
        "subscribe_stock_futures",
        "subscribe_stock_options",
        "subscribe_overtime",
        "subscribe_overseas_stock",
        "subscribe_overseas_futures",
        "unsubscribe_stock",
        "unsubscribe_stock_nxt",
        "unsubscribe_all",
    ]

    @pytest.mark.parametrize("name", MOVED_METHODS)
    def test_method_still_callable_on_agent(self, agent, name):
        assert callable(getattr(agent, name, None)), f"{name} 유실"


class TestDelegatesWithCorrectTrId:
    """편의 메서드가 올바른 SubscriptionType으로 위임하는지."""

    def test_subscribe_stock_uses_krx_trade_tr(self, agent):
        sub_ids = agent.subscribe_stock("005930", include_nxt=False)
        assert sub_ids == ["H0STCNT0_005930"]
        sub = agent.subscriptions["H0STCNT0_005930"]
        assert sub.sub_type is SubscriptionType.STOCK_TRADE
        assert sub.key == "005930"

    def test_subscribe_stock_nxt_uses_nxt_tr(self, agent):
        agent.subscribe_stock_nxt("005930")
        assert any(sid.startswith("H0NX") for sid in agent.subscriptions)

    def test_subscribe_index_uses_index_tr(self, agent):
        # codes는 리스트다 (문자열을 넘기면 문자 단위로 순회된다).
        agent.subscribe_index(["0001"])
        assert agent.subscriptions["H0UPCNT0_0001"].sub_type is SubscriptionType.INDEX

    def test_subscribe_futures_uses_futures_tr(self, agent):
        agent.subscribe_futures("101W09")
        assert (
            agent.subscriptions["H0IFCNT0_101W09"].sub_type
            is SubscriptionType.INDEX_FUTURES_TRADE
        )

    def test_unsubscribe_stock_removes_subscription(self, agent):
        agent.subscribe_stock("005930", include_nxt=False)
        agent.unsubscribe_stock("005930", include_nxt=False)
        assert "H0STCNT0_005930" not in agent.subscriptions

    def test_unsubscribe_all_clears_everything(self, agent):
        agent.subscribe_stock("005930")
        agent.subscribe_index(["0001"])
        assert agent.subscriptions
        agent.unsubscribe_all()
        assert agent.subscriptions == {}


class TestPaperTradingStillResolvesThroughMixin:
    """믹스인 경유 구독도 모의투자 TR 변환을 거쳐야 한다 (STO-1579 회귀)."""

    def test_paper_notice_tr_resolved(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            paper = WSAgent(approval_key="key", url=WS_MOCK_URL)
        assert paper.subscribe(SubscriptionType.STOCK_NOTICE, "12345678") == (
            "H0STCNI9_12345678"
        )

    def test_quote_subscription_via_mixin_unchanged_on_paper(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            paper = WSAgent(approval_key="key", url=WS_MOCK_URL)
        assert paper.subscribe_stock("005930", include_nxt=False) == [
            "H0STCNT0_005930"
        ]
