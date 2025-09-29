"""WSAgent 테스트"""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from pykis.websocket.ws_agent import Subscription, SubscriptionType, WSAgent


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
        ws_agent.ws = ws_mock

        subscription = Subscription(sub_type=SubscriptionType.STOCK_TRADE, key="005930")

        await ws_agent._send_subscription(subscription)

        # send 호출 확인
        ws_mock.send.assert_called_once()

        # 전송된 메시지 확인
        sent_message = json.loads(ws_mock.send.call_args[0][0])
        assert sent_message["body"]["input"]["tr_id"] == "H0STCNT0"
        assert sent_message["body"]["input"]["tr_key"] == "005930"

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
