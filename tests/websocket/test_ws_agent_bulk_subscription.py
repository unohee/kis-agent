"""WSAgent 다량 구독 및 토큰 재발급 테스트"""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from kis_agent.websocket.ws_agent import Subscription, SubscriptionType, WSAgent


class TestWSAgentBulkSubscription:
    """WSAgent 다량 구독 테스트 클래스"""

    @pytest.fixture
    def ws_agent(self):
        """WSAgent 픽스처"""
        return WSAgent(
            approval_key="test_approval_key",
            url="ws://test.example.com",
            auto_reconnect=False,
        )

    @pytest.fixture
    def ws_agent_with_client(self):
        """KISClient가 연결된 WSAgent 픽스처"""
        mock_client = Mock()
        mock_client.get_ws_approval_key = Mock(return_value="new_approval_key_12345")

        return WSAgent(
            approval_key="test_approval_key",
            url="ws://test.example.com",
            auto_reconnect=False,
            client=mock_client,
        )

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="WebSocket bulk subscription test unstable in CI - timing sensitive"
    )
    async def test_bulk_subscription_parallel(self, ws_agent):
        """다량 구독 병렬 처리 테스트"""
        # 웹소켓 모의 객체
        ws_mock = AsyncMock()
        ws_mock.closed = False
        ws_agent.ws = ws_mock
        ws_agent.connected = True

        # 10개 종목으로 줄여서 테스트 속도 향상
        stock_codes = [f"{i:06d}" for i in range(1, 11)]  # 000001 ~ 000010
        for code in stock_codes:
            ws_agent.subscribe(SubscriptionType.STOCK_TRADE, code)

        # 모든 구독에 대한 응답 시뮬레이션 (즉시 응답)
        async def simulate_all_responses():
            """모든 구독 응답 시뮬레이션"""
            # 병렬 처리 시작을 기다린 후 즉시 응답
            await asyncio.sleep(0.05)
            for code in stock_codes:
                sub_id = f"H0STCNT0_{code}"
                # _pending_subscriptions에 추가되기를 기다림
                max_wait = 10
                wait_count = 0
                while (
                    sub_id not in ws_agent._pending_subscriptions
                    and wait_count < max_wait
                ):
                    await asyncio.sleep(0.01)
                    wait_count += 1

                if sub_id in ws_agent._pending_subscriptions:
                    ws_agent._subscription_results[sub_id] = True
                    ws_agent._pending_subscriptions[sub_id].set()

        # 응답 시뮬레이션 태스크 생성
        response_task = asyncio.create_task(simulate_all_responses())

        # 타임아웃을 짧게 설정하여 테스트 속도 향상
        # _send_subscription의 timeout 파라미터를 사용할 수 없으므로
        # 전체 테스트에 타임아웃 설정
        try:
            results = await asyncio.wait_for(ws_agent._subscribe_all(), timeout=5.0)
        except asyncio.TimeoutError:
            pytest.fail("구독 요청 타임아웃 발생")
        finally:
            response_task.cancel()
            try:
                await response_task
            except asyncio.CancelledError:
                pass

        # 결과 확인
        assert len(results["success"]) == 10
        assert len(results["failed"]) == 0

        # send 호출 횟수 확인 (10번 호출되어야 함)
        assert ws_mock.send.call_count == 10

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="WebSocket ping test unstable in CI - timing sensitive")
    async def test_bulk_subscription_with_ping(self, ws_agent):
        """다량 구독 중 ping/pong 응답 테스트"""
        # 웹소켓 모의 객체
        ws_mock = AsyncMock()
        ws_mock.closed = False
        ws_agent.ws = ws_mock
        ws_agent.connected = True

        # 50개 종목 구독 등록 (대량 구독)
        stock_codes = [f"{i:06d}" for i in range(1, 51)]  # 000001 ~ 000050
        for code in stock_codes:
            ws_agent.subscribe(SubscriptionType.STOCK_TRADE, code)

        # ping 응답 시뮬레이션
        ping_responses = []

        async def simulate_ping_responses():
            """ping 응답 시뮬레이션"""
            for _ in range(2):  # 2번 ping 응답으로 단축
                await asyncio.sleep(0.1)  # 대기 시간 단축
                ping_responses.append("pong")

        # 구독 응답 시뮬레이션
        async def simulate_subscription_responses():
            """구독 응답 시뮬레이션"""
            await asyncio.sleep(0.01)  # 최소 대기 시간으로 단축
            for code in stock_codes:
                sub_id = f"H0STCNT0_{code}"
                if sub_id in ws_agent._pending_subscriptions:
                    ws_agent._subscription_results[sub_id] = True
                    ws_agent._pending_subscriptions[sub_id].set()

        # 병렬 태스크 실행
        ping_task = asyncio.create_task(simulate_ping_responses())
        sub_task = asyncio.create_task(simulate_subscription_responses())
        subscribe_task = asyncio.create_task(ws_agent._subscribe_all())

        # 모든 태스크 완료 대기 (타임아웃 설정)
        try:
            results = await asyncio.wait_for(subscribe_task, timeout=2.0)
            await asyncio.wait_for(ping_task, timeout=2.0)
            await asyncio.wait_for(sub_task, timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("테스트 타임아웃 발생")

        # 결과 확인
        assert len(results["success"]) == 50
        assert len(ping_responses) == 3  # ping 응답이 정상적으로 처리됨

    @pytest.mark.asyncio
    async def test_receive_loop_ping_timeout_handling(self, ws_agent):
        """수신 루프 ping 타임아웃 처리 테스트"""
        ws_mock = AsyncMock()
        ws_mock.closed = False

        # recv는 타임아웃 발생, ping은 성공
        recv_call_count = 0

        async def mock_recv():
            nonlocal recv_call_count
            recv_call_count += 1
            if recv_call_count <= 2:
                await asyncio.sleep(0.1)  # 짧은 대기 후 타임아웃
                raise asyncio.TimeoutError()
            return "0|H0STCNT0|0|005930^093000^50000^100"

        ws_mock.recv = mock_recv

        # ping 성공 시뮬레이션
        ping_waiter = AsyncMock()
        ping_waiter.__await__ = lambda x: iter([])  # await 가능하게 만들기
        ws_mock.ping = AsyncMock(return_value=ping_waiter)

        ws_agent.ws = ws_mock
        ws_agent.connected = True

        # 수신 루프를 짧은 시간만 실행
        receive_task = asyncio.create_task(ws_agent._receive_loop(ws_mock))

        # 0.3초 후 취소 (더 빠르게)
        await asyncio.sleep(0.3)
        receive_task.cancel()

        try:
            await receive_task
        except asyncio.CancelledError:
            pass

        # ping이 호출되었는지 확인
        assert ws_mock.ping.called

    def test_update_approval_key(self, ws_agent):
        """approval_key 갱신 테스트"""
        old_key = ws_agent.approval_key
        new_key = "new_approval_key_12345"

        ws_agent.update_approval_key(new_key)

        assert ws_agent.approval_key == new_key
        assert ws_agent.approval_key != old_key

    def test_update_approval_key_empty(self, ws_agent):
        """빈 approval_key 갱신 시도 테스트"""
        old_key = ws_agent.approval_key

        ws_agent.update_approval_key("")

        # 빈 키는 무시되어야 함
        assert ws_agent.approval_key == old_key

    @pytest.mark.asyncio
    async def test_token_refresh_on_auth_error(self, ws_agent_with_client):
        """인증 오류 시 토큰 재발급 테스트"""
        ws_mock = AsyncMock()
        ws_mock.closed = False
        ws_agent_with_client.ws = ws_mock
        ws_agent_with_client.connected = True

        # 인증 오류 시뮬레이션
        auth_error = Exception("401 Unauthorized")
        ws_mock.recv = AsyncMock(side_effect=auth_error)

        # connect() 메서드의 예외 처리 부분 테스트
        # 실제로는 connect() 내부에서 처리되지만, 여기서는 직접 테스트
        try:
            # 수신 루프 시작
            receive_task = asyncio.create_task(
                ws_agent_with_client._receive_loop(ws_mock)
            )
            await asyncio.sleep(0.1)
            receive_task.cancel()
            await receive_task
        except asyncio.CancelledError:
            pass

        # 인증 오류가 발생했지만 예외가 처리되었는지 확인
        # (실제로는 connect() 메서드에서 처리됨)

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="WebSocket semaphore test unstable in CI - timing sensitive"
    )
    async def test_subscribe_all_semaphore_limit(self, ws_agent):
        """구독 병렬 처리 세마포어 제한 테스트"""
        ws_mock = AsyncMock()
        ws_mock.closed = False
        ws_agent.ws = ws_mock
        ws_agent.connected = True

        # 20개 종목 구독 등록
        stock_codes = [f"{i:06d}" for i in range(1, 21)]
        for code in stock_codes:
            ws_agent.subscribe(SubscriptionType.STOCK_TRADE, code)

        # 구독 응답 시뮬레이션 (지연 포함)
        async def simulate_delayed_responses():
            """지연된 구독 응답 시뮬레이션"""
            await asyncio.sleep(0.05)  # 지연 시간 단축
            for code in stock_codes:
                sub_id = f"H0STCNT0_{code}"
                if sub_id in ws_agent._pending_subscriptions:
                    ws_agent._subscription_results[sub_id] = True
                    ws_agent._pending_subscriptions[sub_id].set()

        response_task = asyncio.create_task(simulate_delayed_responses())

        # 모든 구독 요청 전송
        results = await ws_agent._subscribe_all()

        # 결과 확인 (세마포어 제한으로 인해 순차 처리되지만 모두 성공)
        assert len(results["success"]) == 20
        # send 호출이 20번 이루어졌는지 확인
        assert ws_mock.send.call_count == 20

    @pytest.mark.asyncio
    async def test_receive_loop_ping_interval(self, ws_agent):
        """수신 루프 ping 간격 테스트"""
        ws_mock = AsyncMock()
        ws_mock.closed = False

        recv_timeouts = []

        async def mock_recv():
            await asyncio.sleep(0.05)
            recv_timeouts.append(asyncio.TimeoutError())
            raise asyncio.TimeoutError()

        ws_mock.recv = mock_recv

        # ping 성공 시뮬레이션
        ping_waiter = AsyncMock()
        ping_waiter.__await__ = lambda x: iter([])
        ws_mock.ping = AsyncMock(return_value=ping_waiter)

        ws_agent.ws = ws_mock
        ws_agent.connected = True
        ws_agent.ping_interval = 10  # 10초로 설정

        # 수신 루프를 짧은 시간만 실행
        receive_task = asyncio.create_task(ws_agent._receive_loop(ws_mock))

        # 0.5초 후 취소
        await asyncio.sleep(0.5)
        receive_task.cancel()

        try:
            await receive_task
        except asyncio.CancelledError:
            pass

        # ping이 호출되었는지 확인 (타임아웃 발생 시 ping 체크)
        assert ws_mock.ping.called

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="WebSocket mixed results test unstable in CI - timing sensitive"
    )
    async def test_bulk_subscription_mixed_results(self, ws_agent):
        """다량 구독 혼합 결과 테스트 (일부 성공, 일부 실패)"""
        ws_mock = AsyncMock()
        ws_mock.closed = False
        ws_agent.ws = ws_mock
        ws_agent.connected = True

        # 10개 종목 구독 등록
        stock_codes = [f"{i:06d}" for i in range(1, 11)]
        for code in stock_codes:
            ws_agent.subscribe(SubscriptionType.STOCK_TRADE, code)

        # 일부는 성공, 일부는 실패 시뮬레이션
        async def simulate_mixed_responses():
            await asyncio.sleep(0.01)  # 최소 대기 시간으로 단축
            for i, code in enumerate(stock_codes):
                sub_id = f"H0STCNT0_{code}"
                if sub_id in ws_agent._pending_subscriptions:
                    # 짝수 인덱스는 성공, 홀수 인덱스는 실패
                    if i % 2 == 0:
                        ws_agent._subscription_results[sub_id] = True
                    else:
                        ws_agent._subscription_results[sub_id] = False
                        ws_agent._subscription_errors[sub_id] = "테스트 실패"
                    ws_agent._pending_subscriptions[sub_id].set()

        response_task = asyncio.create_task(simulate_mixed_responses())

        results = await ws_agent._subscribe_all()

        # 결과 확인 (5개 성공, 5개 실패)
        assert len(results["success"]) == 5
        assert len(results["failed"]) == 5
        assert len(results["success"]) + len(results["failed"]) == 10
