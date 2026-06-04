"""WSAgent 최적화 검증.

PR perf/ws-agent-optimizations에서 도입된 4가지 변경 검증:
1. _subscribe_all에서 구독 간 0.5초 sleep 제거 (응답 대기로 자연 직렬화)
2. _call_handler가 sync 핸들러를 asyncio.to_thread()로 격리
3. fire-and-forget 백그라운드 태스크가 _background_tasks에 추적되어 GC 회피
4. _send_subscription의 결과 dict 누수 fix
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from kis_agent.websocket.ws_agent import WSAgent
from kis_agent.websocket.ws_types import Subscription, SubscriptionType


@pytest.fixture
def agent():
    """기본 WSAgent 인스턴스 (실제 연결 없음)."""
    return WSAgent(approval_key="test_key")


class TestSubscribeAllNoExtraSleep:
    @pytest.mark.asyncio
    async def test_subscribe_all_does_not_sleep_between_subs(self, agent):
        """_subscribe_all 자체에는 sub 간 추가 sleep이 없다.

        실제 KIS 응답 대기는 _send_subscription에서 처리되므로 mocking으로 즉시
        성공시키면 N개 구독이 거의 즉시 완료되어야 한다 (이전 구현은 0.5s/sub).
        """
        # 5개 구독 등록 (실제 send는 mock)
        for code in ("005930", "000660", "035420", "035720", "051910"):
            sub = Subscription(
                sub_type=SubscriptionType.STOCK_TRADE,
                key=code,
                handler=None,
                metadata={},
            )
            agent.subscriptions[f"H0STCNT0_{code}"] = sub

        # 연결 시뮬레이션
        agent.ws = MagicMock()
        agent.ws.close_code = None
        agent.connected = True

        # _send_subscription을 즉시 성공으로 mock
        async def fake_send(subscription, max_retries=3, timeout=60.0):
            await asyncio.sleep(0)  # 단순 yield
            return True

        agent._send_subscription = fake_send

        start = time.monotonic()
        result = await agent._subscribe_all()
        elapsed = time.monotonic() - start

        assert len(result["success"]) == 5
        # 이전 구현은 5개 = 4×0.5s = 2초+ 소비
        assert elapsed < 0.3, f"sub 간 sleep이 남아있는 듯: {elapsed:.3f}s"


class TestSyncHandlerIsolation:
    @pytest.mark.asyncio
    async def test_sync_handler_runs_in_thread(self, agent):
        """동기 핸들러가 asyncio.to_thread()로 격리되어 이벤트 루프를 블록하지 않는다."""
        main_loop_thread_id = None
        handler_thread_id = None

        # 이벤트 루프 스레드 ID 기록 (단순히 현재 스레드)
        import threading

        main_loop_thread_id = threading.get_ident()

        def sync_handler(data, metadata):
            nonlocal handler_thread_id
            handler_thread_id = threading.get_ident()

        await agent._call_handler(sync_handler, {"price": 100}, {})

        assert handler_thread_id is not None
        # to_thread로 실행되면 메인 스레드와 다른 스레드에서 실행됨
        assert handler_thread_id != main_loop_thread_id, (
            "sync 핸들러가 메인 이벤트 루프 스레드에서 실행됨 — 격리 안 됨"
        )

    @pytest.mark.asyncio
    async def test_async_handler_runs_in_loop(self, agent):
        """async 핸들러는 이벤트 루프에서 직접 await된다 (to_thread 사용 안 함)."""
        received = []

        async def async_handler(data, metadata):
            received.append(data)

        await agent._call_handler(async_handler, {"price": 200}, {"meta": "x"})
        assert received == [{"price": 200}]

    @pytest.mark.asyncio
    async def test_handler_exception_caught_and_counted(self, agent):
        """핸들러가 예외를 발생시켜도 _call_handler가 잡고 stats["errors"] 증가."""
        initial_errors = agent.stats["errors"]

        def bad_handler(data, metadata):
            raise RuntimeError("intentional")

        # 예외가 전파되지 않아야 함
        await agent._call_handler(bad_handler, {}, {})
        assert agent.stats["errors"] == initial_errors + 1


class TestBackgroundTaskTracking:
    @pytest.mark.asyncio
    async def test_track_task_keeps_reference(self, agent):
        """_track_task가 task를 set에 추가하고 완료 시 자동 제거한다."""

        async def quick():
            return 42

        task = agent._track_task(asyncio.create_task(quick()))
        assert task in agent._background_tasks

        await task
        # done_callback이 즉시 동기 실행되지 않을 수 있어 한 번 양보
        await asyncio.sleep(0)
        assert task not in agent._background_tasks

    @pytest.mark.asyncio
    async def test_disconnect_cancels_pending_background_tasks(self, agent):
        """disconnect 시 미완료 백그라운드 태스크가 모두 cancel된다."""

        async def long_task():
            await asyncio.sleep(10)

        # 백그라운드 태스크 3개 시작
        for _ in range(3):
            agent._track_task(asyncio.create_task(long_task()))

        assert len(agent._background_tasks) == 3
        snapshot = list(agent._background_tasks)

        await agent.disconnect()

        # 모두 cancel된 상태
        for t in snapshot:
            assert t.done()
            assert t.cancelled()


class TestSubscriptionStateCleanup:
    @pytest.mark.asyncio
    async def test_send_subscription_clears_all_state_after_failure(self, agent):
        """_send_subscription 실패 후 pending/results/errors 모두 정리된다."""
        sub = Subscription(
            sub_type=SubscriptionType.STOCK_TRADE,
            key="005930",
            handler=None,
            metadata={},
        )
        sub_id = "H0STCNT0_005930"

        # ws mock — send는 호출되지만 응답은 안 옴 → timeout
        agent.ws = MagicMock()
        agent.ws.close_code = None
        agent.ws.send = AsyncMock()

        # 짧은 timeout으로 즉시 실패
        result = await agent._send_subscription(sub, max_retries=1, timeout=0.05)
        assert result is False

        # 모든 상태 정리 확인
        assert sub_id not in agent._pending_subscriptions
        assert sub_id not in agent._subscription_results
        assert sub_id not in agent._subscription_errors


class TestJSONDoubleParsingAvoided:
    def test_parse_message_accepts_preparsed_json(self, agent):
        """이미 파싱한 json_data를 넘기면 _parse_message가 다시 파싱하지 않는다."""
        raw = '{"header": {"tr_id": "H0STCNT0", "tr_key": "005930"}, "body": {"output": {}}}'
        preparsed = {
            "header": {"tr_id": "H0STCNT0", "tr_key": "005930"},
            "body": {"output": {}},
        }
        tr_id, tr_key, data = agent._parse_message(raw, json_data=preparsed)
        assert tr_id == "H0STCNT0"
        assert tr_key == "005930"
        # 동일 객체 사용 검증 (이중 파싱이면 새 dict)
        assert data is preparsed

    def test_parse_message_parses_when_no_preparsed(self, agent):
        """json_data가 없으면 _parse_message가 자체적으로 파싱한다 (역호환)."""
        raw = '{"header": {"tr_id": "H0STCNT0", "tr_key": "005930"}, "body": {}}'
        tr_id, tr_key, data = agent._parse_message(raw)
        assert tr_id == "H0STCNT0"
        assert tr_key == "005930"
        assert isinstance(data, dict)
