"""WSAgent 테스트"""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from kis_agent.websocket.ws_agent import Subscription, SubscriptionType, WSAgent


class TestWSAgent:
    """WSAgent 테스트 클래스"""

    @pytest.fixture
    def ws_agent(self):
        """WSAgent 픽스처"""
        return WSAgent(
            approval_key="test_approval_key",
            url="ws://test.example.com",
            auto_reconnect=False,
        )

    def test_init(self, ws_agent):
        """초기화 테스트"""
        assert ws_agent.approval_key == "test_approval_key"
        assert ws_agent.url == "ws://test.example.com"
        assert ws_agent.auto_reconnect == False
        assert ws_agent.connected == False
        assert len(ws_agent.subscriptions) == 0

    def test_subscribe(self, ws_agent):
        """구독 추가 테스트"""
        # 구독 추가
        sub_id = ws_agent.subscribe(
            SubscriptionType.STOCK_TRADE, "005930", test_meta="test_value"
        )

        assert sub_id == "H0STCNT0_005930"
        assert sub_id in ws_agent.subscriptions

        subscription = ws_agent.subscriptions[sub_id]
        assert subscription.sub_type == SubscriptionType.STOCK_TRADE
        assert subscription.key == "005930"
        assert subscription.metadata["test_meta"] == "test_value"

    def test_duplicate_subscribe(self, ws_agent):
        """중복 구독 테스트"""
        # 첫 번째 구독
        sub_id1 = ws_agent.subscribe(SubscriptionType.STOCK_TRADE, "005930")

        # 중복 구독 시도
        sub_id2 = ws_agent.subscribe(SubscriptionType.STOCK_TRADE, "005930")

        assert sub_id1 == sub_id2
        assert len(ws_agent.subscriptions) == 1

    def test_unsubscribe(self, ws_agent):
        """구독 해제 테스트"""
        # 구독 추가
        sub_id = ws_agent.subscribe(SubscriptionType.STOCK_TRADE, "005930")
        assert sub_id in ws_agent.subscriptions

        # 구독 해제
        ws_agent.unsubscribe(sub_id)
        assert sub_id not in ws_agent.subscriptions

    def test_register_handler(self, ws_agent):
        """핸들러 등록 테스트"""
        handler = Mock()

        ws_agent.register_handler(SubscriptionType.STOCK_TRADE, handler)

        assert SubscriptionType.STOCK_TRADE in ws_agent.type_handlers
        assert handler in ws_agent.type_handlers[SubscriptionType.STOCK_TRADE]

    def test_parse_json_message(self, ws_agent):
        """JSON 메시지 파싱 테스트"""
        message = json.dumps(
            {
                "header": {"tr_id": "H0STCNT0", "tr_key": "005930"},
                "body": {"msg1": "test message"},
            }
        )

        tr_id, tr_key, data = ws_agent._parse_message(message)

        assert tr_id == "H0STCNT0"
        assert tr_key == "005930"
        assert data["body"]["msg1"] == "test message"

    def test_parse_binary_message(self, ws_agent):
        """바이너리 메시지 파싱 테스트"""
        message = "0|H0STCNT0|0|005930^100^200^300"

        tr_id, tr_key, data = ws_agent._parse_message(message)

        assert tr_id == "H0STCNT0"
        assert tr_key == "005930"
        assert data == ["005930", "100", "200", "300"]

    def test_aes_key_storage(self, ws_agent):
        """AES 키 저장 테스트"""
        message = json.dumps(
            {
                "header": {"tr_id": "H0STCNI0", "tr_key": "test"},
                "body": {"output": {"key": "test_key_123", "iv": "test_iv_456"}},
            }
        )

        tr_id, tr_key, data = ws_agent._parse_message(message)

        assert "H0STCNI0" in ws_agent.aes_keys
        assert ws_agent.aes_keys["H0STCNI0"] == ("test_key_123", "test_iv_456")

    @pytest.mark.asyncio
    async def test_handle_message_with_handler(self, ws_agent):
        """핸들러를 통한 메시지 처리 테스트"""
        # 핸들러 모의 객체
        handler = AsyncMock()

        # 구독 및 핸들러 등록
        ws_agent.subscribe(SubscriptionType.STOCK_TRADE, "005930", handler=handler)

        # 메시지 처리
        message = "0|H0STCNT0|0|005930^093000^50000^100"
        await ws_agent._handle_message(message)

        # 핸들러 호출 확인
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_pingpong(self, ws_agent):
        """PINGPONG 메시지 처리 테스트"""
        message = json.dumps({"header": {"tr_id": "PINGPONG"}, "body": {}})

        # PINGPONG은 무시되어야 함
        await ws_agent._handle_message(message)

        assert ws_agent.stats["messages_received"] == 1
        assert ws_agent.stats["messages_processed"] == 0

    def test_get_stats(self, ws_agent):
        """통계 정보 테스트"""
        stats = ws_agent.get_stats()

        assert "messages_received" in stats
        assert "messages_processed" in stats
        assert "errors" in stats
        assert "reconnects" in stats

    @pytest.mark.asyncio
    async def test_send_subscription(self, ws_agent):
        """구독 요청 전송 테스트"""
        # 웹소켓 모의 객체
        ws_mock = AsyncMock()
        ws_mock.close_code = None  # websockets v16+ 호환
        ws_agent.ws = ws_mock

        subscription = Subscription(sub_type=SubscriptionType.STOCK_TRADE, key="005930")

        # 응답 시뮬레이션 (타임아웃 방지)
        async def simulate_response():
            await asyncio.sleep(0.1)
            sub_id = "H0STCNT0_005930"
            if sub_id in ws_agent._pending_subscriptions:
                ws_agent._subscription_results[sub_id] = True
                ws_agent._pending_subscriptions[sub_id].set()

        asyncio.create_task(simulate_response())

        result = await ws_agent._send_subscription(subscription)

        # send 호출 확인
        ws_mock.send.assert_called_once()

        # 전송된 메시지 확인
        sent_message = json.loads(ws_mock.send.call_args[0][0])
        assert sent_message["body"]["input"]["tr_id"] == "H0STCNT0"
        assert sent_message["body"]["input"]["tr_key"] == "005930"
        assert result is True

    @pytest.mark.asyncio
    async def test_send_unsubscription(self, ws_agent):
        """구독 해제 요청 전송 테스트"""
        # 웹소켓 모의 객체
        ws_mock = AsyncMock()
        ws_agent.ws = ws_mock

        subscription = Subscription(sub_type=SubscriptionType.STOCK_TRADE, key="005930")

        await ws_agent._send_unsubscription(subscription)

        # send 호출 확인
        ws_mock.send.assert_called_once()

        # 전송된 메시지 확인
        sent_message = json.loads(ws_mock.send.call_args[0][0])
        assert sent_message["header"]["tr_type"] == "2"  # 구독 해제

    def test_multiple_subscriptions(self, ws_agent):
        """다중 구독 테스트"""
        # 여러 종목 구독
        stocks = ["005930", "000660", "035420"]
        sub_ids = []

        for stock in stocks:
            sub_id = ws_agent.subscribe(SubscriptionType.STOCK_TRADE, stock)
            sub_ids.append(sub_id)

        # 모든 구독 확인
        assert len(ws_agent.subscriptions) == 3
        for sub_id in sub_ids:
            assert sub_id in ws_agent.subscriptions

    def test_mixed_subscription_types(self, ws_agent):
        """다양한 구독 타입 테스트"""
        # 주식 체결
        sub1 = ws_agent.subscribe(SubscriptionType.STOCK_TRADE, "005930")

        # 주식 호가
        sub2 = ws_agent.subscribe(SubscriptionType.STOCK_ASK_BID, "005930")

        # 지수
        sub3 = ws_agent.subscribe(SubscriptionType.INDEX, "0001")

        # 선물
        sub4 = ws_agent.subscribe(SubscriptionType.FUTURES_TRADE, "101S6000")

        assert len(ws_agent.subscriptions) == 4
        assert all(sub in ws_agent.subscriptions for sub in [sub1, sub2, sub3, sub4])

    # === 새로운 기능 테스트 ===

    def test_handle_subscription_response_success(self, ws_agent):
        """구독 응답 처리 테스트 - 성공"""
        sub_id = "H0STCNT0_005930"

        # 대기 중인 구독 설정
        ws_agent._pending_subscriptions[sub_id] = asyncio.Event()
        ws_agent._subscription_results[sub_id] = False
        ws_agent._subscription_errors[sub_id] = ""

        # 성공 응답 메시지
        json_data = {
            "header": {"tr_id": "H0STCNT0", "tr_key": "005930"},
            "body": {"msg1": "SUBSCRIBE SUCCESS", "rt_cd": "0"},
        }

        result = ws_agent._handle_subscription_response(json_data)

        assert result is True
        assert ws_agent._subscription_results[sub_id] is True
        assert ws_agent._pending_subscriptions[sub_id].is_set()

    def test_handle_subscription_response_failure(self, ws_agent):
        """구독 응답 처리 테스트 - 실패"""
        sub_id = "H0STCNT0_005930"

        # 대기 중인 구독 설정
        ws_agent._pending_subscriptions[sub_id] = asyncio.Event()
        ws_agent._subscription_results[sub_id] = False
        ws_agent._subscription_errors[sub_id] = ""

        # 실패 응답 메시지
        json_data = {
            "header": {"tr_id": "H0STCNT0", "tr_key": "005930"},
            "body": {"msg1": "구독 실패: 유효하지 않은 종목코드", "rt_cd": "1"},
        }

        result = ws_agent._handle_subscription_response(json_data)

        assert result is True
        assert ws_agent._subscription_results[sub_id] is False
        assert "유효하지 않은 종목코드" in ws_agent._subscription_errors[sub_id]

    def test_handle_subscription_response_no_pending(self, ws_agent):
        """구독 응답 처리 테스트 - 대기 중인 구독 없음"""
        # 대기 중인 구독 없이 성공 응답
        json_data = {
            "header": {"tr_id": "H0STCNT0", "tr_key": "005930"},
            "body": {"msg1": "SUBSCRIBE SUCCESS"},
        }

        result = ws_agent._handle_subscription_response(json_data)

        # 대기 중인 구독은 없지만 로그만 남기고 True 반환
        assert result is True

    def test_handle_subscription_response_no_msg(self, ws_agent):
        """구독 응답 처리 테스트 - msg1 없음"""
        json_data = {
            "header": {"tr_id": "H0STCNT0", "tr_key": "005930"},
            "body": {"output": {"some": "data"}},
        }

        result = ws_agent._handle_subscription_response(json_data)

        # msg1이 없으면 False 반환 (일반 데이터 메시지)
        assert result is False

    @pytest.mark.asyncio
    async def test_subscribe_async_success(self, ws_agent):
        """비동기 구독 테스트 - 성공"""
        # 웹소켓 모의 객체 설정
        ws_mock = AsyncMock()
        ws_mock.close_code = None
        ws_agent.ws = ws_mock
        ws_agent.connected = True

        async def simulate_response():
            """구독 응답 시뮬레이션"""
            await asyncio.sleep(0.1)
            sub_id = "H0STCNT0_005930"
            if sub_id in ws_agent._pending_subscriptions:
                ws_agent._subscription_results[sub_id] = True
                ws_agent._pending_subscriptions[sub_id].set()

        # 응답 시뮬레이션 태스크 생성
        asyncio.create_task(simulate_response())

        # 비동기 구독 호출
        sub_id, success = await ws_agent.subscribe_async(
            SubscriptionType.STOCK_TRADE, "005930"
        )

        assert sub_id == "H0STCNT0_005930"
        assert success is True
        assert sub_id in ws_agent.subscriptions
        assert sub_id in ws_agent.active_subscriptions

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="WebSocket timeout test unstable in CI - requires real connection timing"
    )
    async def test_subscribe_async_timeout(self, ws_agent):
        """비동기 구독 테스트 - 타임아웃"""
        # 웹소켓 모의 객체 설정
        ws_mock = AsyncMock()
        ws_mock.close_code = None
        ws_agent.ws = ws_mock
        ws_agent.connected = True

        # 응답 없이 타임아웃 발생
        sub_id, success = await ws_agent.subscribe_async(
            SubscriptionType.STOCK_TRADE, "005930"
        )

        # 3회 재시도 후 실패
        assert sub_id == "H0STCNT0_005930"
        assert success is False
        # 실패 시 구독 목록에서 제거됨
        assert sub_id not in ws_agent.subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_async_not_connected(self, ws_agent):
        """비동기 구독 테스트 - 연결 안됨"""
        ws_agent.connected = False
        ws_agent.ws = None

        sub_id, success = await ws_agent.subscribe_async(
            SubscriptionType.STOCK_TRADE, "005930"
        )

        assert sub_id == "H0STCNT0_005930"
        assert success is False

    @pytest.mark.asyncio
    async def test_send_subscription_ws_closed(self, ws_agent):
        """구독 요청 테스트 - 웹소켓 연결 종료됨"""
        # 웹소켓 모의 객체 - 닫힌 상태
        ws_mock = AsyncMock()
        ws_mock.close_code = 1000  # 정상 종료 코드 = closed
        ws_agent.ws = ws_mock

        subscription = Subscription(sub_type=SubscriptionType.STOCK_TRADE, key="005930")

        result = await ws_agent._send_subscription(subscription)

        assert result is False
        ws_mock.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_subscription_no_ws(self, ws_agent):
        """구독 요청 테스트 - 웹소켓 없음"""
        ws_agent.ws = None

        subscription = Subscription(sub_type=SubscriptionType.STOCK_TRADE, key="005930")

        result = await ws_agent._send_subscription(subscription)

        assert result is False

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="WebSocket bulk subscription test unstable in CI - timing sensitive"
    )
    async def test_subscribe_all_results(self, ws_agent):
        """모든 구독 요청 결과 테스트"""
        # 웹소켓 모의 객체
        ws_mock = AsyncMock()
        ws_mock.close_code = None
        ws_agent.ws = ws_mock
        ws_agent.connected = True

        # 여러 종목 구독 등록 (연결 전)
        ws_agent.connected = False
        ws_agent.subscribe(SubscriptionType.STOCK_TRADE, "005930")
        ws_agent.subscribe(SubscriptionType.STOCK_TRADE, "000660")
        ws_agent.connected = True

        async def simulate_responses():
            """구독 응답 시뮬레이션"""
            await asyncio.sleep(0.05)
            for sub_id in list(ws_agent._pending_subscriptions.keys()):
                # 첫 번째는 성공, 두 번째는 실패
                if "005930" in sub_id:
                    ws_agent._subscription_results[sub_id] = True
                else:
                    ws_agent._subscription_results[sub_id] = False
                    ws_agent._subscription_errors[sub_id] = "테스트 실패"
                ws_agent._pending_subscriptions[sub_id].set()

        # 응답 시뮬레이션
        asyncio.create_task(simulate_responses())

        results = await ws_agent._subscribe_all()

        assert "success" in results
        assert "failed" in results
        assert len(results["success"]) + len(results["failed"]) == 2

    def test_pending_subscription_tracking(self, ws_agent):
        """대기 중인 구독 추적 테스트"""
        # 초기화 상태 확인
        assert len(ws_agent._pending_subscriptions) == 0
        assert len(ws_agent._subscription_results) == 0
        assert len(ws_agent._subscription_errors) == 0

    def test_on_subscription_task_done_success(self, ws_agent):
        """구독 태스크 완료 콜백 테스트 - 성공"""
        # 성공 태스크 모의
        task_mock = Mock()
        task_mock.result.return_value = True

        # 예외 없이 완료
        ws_agent._on_subscription_task_done(task_mock, "H0STCNT0_005930")

    def test_on_subscription_task_done_failure(self, ws_agent):
        """구독 태스크 완료 콜백 테스트 - 실패"""
        # 실패 태스크 모의
        task_mock = Mock()
        task_mock.result.return_value = False

        # 경고 로그 발생 (예외 없음)
        ws_agent._on_subscription_task_done(task_mock, "H0STCNT0_005930")

    def test_on_subscription_task_done_exception(self, ws_agent):
        """구독 태스크 완료 콜백 테스트 - 예외"""
        # 예외 발생 태스크 모의
        task_mock = Mock()
        task_mock.result.side_effect = Exception("테스트 예외")

        # 예외 처리됨 (프로그램 중단 없음)
        ws_agent._on_subscription_task_done(task_mock, "H0STCNT0_005930")
