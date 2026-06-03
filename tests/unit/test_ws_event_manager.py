"""kis_agent.websocket.event_manager 단위 테스트.

Observer 패턴 EventManager의 동기/비동기 emit, 히스토리, 리스너 관리 커버.
"""

import asyncio

import pytest

from kis_agent.websocket.event_manager import (
    Event,
    EventManager,
    EventType,
)


class TestEventDataclass:
    def test_event_init_and_to_dict(self):
        ev = Event(EventType.TRADE_UPDATE, {"price": 100}, source="test")
        assert ev.type == EventType.TRADE_UPDATE
        assert ev.data == {"price": 100}
        assert ev.source == "test"
        assert ev.timestamp is not None

        d = ev.to_dict()
        assert d["type"] == "trade_update"
        assert d["data"] == {"price": 100}
        assert d["source"] == "test"
        assert "timestamp" in d


class TestEventManagerSync:
    def test_subscribe_and_unsubscribe(self):
        em = EventManager(async_mode=False)

        def listener(_event):
            pass

        em.subscribe(EventType.TRADE_UPDATE, listener)
        assert em.get_listener_count(EventType.TRADE_UPDATE) == 1
        assert em.get_listener_count() == 1

        # 중복 구독은 무시
        em.subscribe(EventType.TRADE_UPDATE, listener)
        assert em.get_listener_count(EventType.TRADE_UPDATE) == 1

        em.unsubscribe(EventType.TRADE_UPDATE, listener)
        assert em.get_listener_count(EventType.TRADE_UPDATE) == 0

    def test_unsubscribe_missing_is_noop(self):
        em = EventManager(async_mode=False)

        def listener(_event):
            pass

        # 구독 안 한 상태에서 해제해도 예외 없이 처리
        em.unsubscribe(EventType.ERROR, listener)
        assert em.get_listener_count(EventType.ERROR) == 0

    def test_emit_sync_dispatches(self):
        em = EventManager(async_mode=False)
        received = []

        def listener(event):
            received.append(event.data)

        em.subscribe(EventType.INDEX_UPDATE, listener)
        em.emit(EventType.INDEX_UPDATE, {"value": 2500})

        assert received == [{"value": 2500}]
        # 히스토리에도 기록됨
        assert len(em.get_history()) == 1
        assert em.get_history()[0].data == {"value": 2500}

    def test_emit_sync_listener_exception_propagates(self):
        em = EventManager(async_mode=False)

        def bad_listener(_event):
            raise RuntimeError("listener fail")

        em.subscribe(EventType.ERROR, bad_listener)
        with pytest.raises(RuntimeError, match="listener fail"):
            em.emit(EventType.ERROR, {"msg": "x"})

    def test_history_capped(self):
        em = EventManager(async_mode=False)
        em.max_history = 5
        for i in range(10):
            em.emit_sync(Event(EventType.MESSAGE_RECEIVED, i))
        assert len(em.event_history) == 5
        # 가장 최근 5개만 남음
        assert [e.data for e in em.event_history] == [5, 6, 7, 8, 9]

    def test_get_history_filtered_and_limit(self):
        em = EventManager(async_mode=False)
        for i in range(3):
            em.emit_sync(Event(EventType.TRADE_UPDATE, i))
        for i in range(2):
            em.emit_sync(Event(EventType.INDEX_UPDATE, i))

        all_hist = em.get_history(limit=100)
        assert len(all_hist) == 5

        trade_only = em.get_history(event_type=EventType.TRADE_UPDATE)
        assert len(trade_only) == 3
        assert all(e.type == EventType.TRADE_UPDATE for e in trade_only)

        # limit 적용
        last_two = em.get_history(limit=2)
        assert len(last_two) == 2

    def test_clear_history_and_listeners(self):
        em = EventManager(async_mode=False)
        em.subscribe(EventType.TRADE_UPDATE, lambda _e: None)
        em.subscribe(EventType.INDEX_UPDATE, lambda _e: None)
        em.emit_sync(Event(EventType.TRADE_UPDATE, 1))

        assert len(em.event_history) == 1
        em.clear_history()
        assert em.event_history == []

        assert em.get_listener_count() == 2
        em.clear_listeners(EventType.TRADE_UPDATE)
        assert em.get_listener_count(EventType.TRADE_UPDATE) == 0
        assert em.get_listener_count(EventType.INDEX_UPDATE) == 1

        em.clear_listeners()
        assert em.get_listener_count() == 0


class TestEventManagerAsync:
    @pytest.mark.asyncio
    async def test_emit_async_invokes_sync_listener(self):
        em = EventManager(async_mode=True)
        received = []

        def sync_listener(event):
            received.append(event.data)

        em.subscribe(EventType.MESSAGE_RECEIVED, sync_listener)
        await em.emit_async(Event(EventType.MESSAGE_RECEIVED, "payload"))
        # to_thread로 실행되므로 join 대기 필요 없음 (gather 이미 await됨)
        assert received == ["payload"]

    @pytest.mark.asyncio
    async def test_emit_async_invokes_async_listener(self):
        em = EventManager(async_mode=True)
        received = []

        async def async_listener(event):
            received.append(event.data)

        em.subscribe(EventType.TRADE_UPDATE, async_listener)
        await em.emit_async(Event(EventType.TRADE_UPDATE, 42))
        assert received == [42]

    @pytest.mark.asyncio
    async def test_emit_async_listener_exception_logged_but_gathered(self):
        em = EventManager(async_mode=True)

        async def bad(event):
            raise RuntimeError("boom")

        em.subscribe(EventType.ERROR, bad)
        # gather(return_exceptions=True)라 emit_async 자체는 raise하지 않음
        await em.emit_async(Event(EventType.ERROR, "x"))

    def test_emit_in_async_mode_without_running_loop_creates_task_safely(self):
        """async_mode=True일 때 emit()은 asyncio.create_task를 시도.

        실행 중인 루프가 없으면 RuntimeError가 발생하므로 그 자체를 검증.
        """
        em = EventManager(async_mode=True)
        em.subscribe(EventType.TRADE_UPDATE, lambda _e: None)
        # 루프가 없는 동기 컨텍스트에서 호출 시 RuntimeError
        with pytest.raises(RuntimeError):
            em.emit(EventType.TRADE_UPDATE, "x")

    @pytest.mark.asyncio
    async def test_emit_in_async_mode_with_loop_running(self):
        em = EventManager(async_mode=True)
        received = []

        async def listener(event):
            received.append(event.data)

        em.subscribe(EventType.SUBSCRIPTION_SUCCESS, listener)
        em.emit(EventType.SUBSCRIPTION_SUCCESS, "ok")
        # create_task로 백그라운드 실행되므로 이벤트 루프에 한 번 양보
        await asyncio.sleep(0.05)
        assert received == ["ok"]
