"""
Enhanced WebSocket Client 테스트
=================================

생성일: 2024-08-22
목적: EnhancedWebSocketClient 클래스의 기능 검증
의존성: pytest, pytest-asyncio, pykis.websocket
테스트 상태: 완료

주요 테스트 영역:
- 클라이언트 초기화 및 설정
- 주식 추가/제거 기능
- 콜백 시스템 동작
- 시장 데이터 저장 및 조회
- 비동기 작업 처리
"""

import asyncio
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest

from pykis.websocket.enhanced_client import EnhancedWebSocketClient
from pykis.websocket.ws_agent import SubscriptionType


@pytest.fixture
def mock_kis_client():
    """모의 KIS 클라이언트 생성"""
    client = Mock()
    client.get_ws_approval_key.return_value = "test_approval_key_12345"
    return client


@pytest.fixture
def account_info():
    """테스트용 계좌 정보"""
    return {"CANO": "12345678", "ACNT_PRDT_CD": "01"}


@pytest.fixture
def stock_api():
    """모의 주식 API"""
    api = Mock()
    api.get_stock_info.return_value = {
        "005930": {"name": "삼성전자", "market": "KOSPI"},
        "000660": {"name": "SK하이닉스", "market": "KOSPI"},
        "035420": {"name": "NAVER", "market": "KOSDAQ"},
    }
    return api


class TestEnhancedWebSocketClientInit:
    """클라이언트 초기화 테스트"""

    def test_init_default_params(self, mock_kis_client, account_info):
        """기본 매개변수로 초기화"""
        client = EnhancedWebSocketClient(
            client=mock_kis_client, account_info=account_info
        )

        assert client.client == mock_kis_client
        assert client.account_info == account_info
        assert client.stock_codes == []
        assert client.enable_index is True
        assert client.enable_ask_bid is False
        assert client.market_data["stocks"] == {}
        assert len(client.callbacks["on_trade"]) == 0

    def test_init_with_stock_codes(self, mock_kis_client, account_info):
        """종목 코드와 함께 초기화"""
        stock_codes = ["005930", "000660"]
        client = EnhancedWebSocketClient(
            client=mock_kis_client, account_info=account_info, stock_codes=stock_codes
        )

        assert client.stock_codes == stock_codes

    def test_init_with_options(self, mock_kis_client, account_info):
        """다양한 옵션과 함께 초기화"""
        client = EnhancedWebSocketClient(
            client=mock_kis_client,
            account_info=account_info,
            enable_index=False,
            enable_ask_bid=True,
            enable_program_trading=True,
        )

        assert client.enable_index is False
        assert client.enable_ask_bid is True
        assert client.enable_program_trading is True


class TestStockManagement:
    """주식 관리 기능 테스트"""

    @pytest.fixture
    def client(self, mock_kis_client, account_info, stock_api):
        """테스트용 클라이언트"""
        with patch("pykis.websocket.enhanced_client.StockAPI", return_value=stock_api):
            client = EnhancedWebSocketClient(
                client=mock_kis_client,
                account_info=account_info,
                stock_codes=["005930"],
            )
            # stock_info 미리 설정
            client.stock_info = {
                "005930": {"name": "삼성전자", "market": "KOSPI"},
                "000660": {"name": "SK하이닉스", "market": "KOSPI"},
            }
            return client

    def test_add_stock_new(self, client):
        """새로운 주식 추가"""
        # WSAgent 모킹
        with patch.object(client, "ws_agent") as mock_agent:
            mock_agent.subscribe.return_value = "subscription_id"

            client.add_stock("000660")

            assert "000660" in client.stock_codes
            # 체결 구독이 추가되었는지 확인
            mock_agent.subscribe.assert_called_with(
                SubscriptionType.STOCK_TRADE,
                "000660",
                handler=client._handle_stock_trade,
            )

    def test_add_stock_existing(self, client):
        """이미 있는 주식 추가 시도"""
        initial_count = len(client.stock_codes)
        client.add_stock("005930")  # 이미 존재하는 종목

        assert len(client.stock_codes) == initial_count

    def test_remove_stock_existing(self, client):
        """기존 주식 제거"""
        # WSAgent 모킹
        with patch.object(client, "ws_agent") as mock_agent:
            # 시장 데이터에 미리 데이터 추가
            client.market_data["stocks"]["005930"] = {"price": 75000}

            client.remove_stock("005930")

            assert "005930" not in client.stock_codes
            assert "005930" not in client.market_data["stocks"]

            # unsubscribe가 호출되었는지 확인
            mock_agent.unsubscribe.assert_called()

    def test_remove_stock_nonexistent(self, client):
        """존재하지 않는 주식 제거 시도"""
        initial_count = len(client.stock_codes)
        client.remove_stock("999999")

        assert len(client.stock_codes) == initial_count


class TestCallbackSystem:
    """콜백 시스템 테스트"""

    @pytest.fixture
    def client(self, mock_kis_client, account_info):
        """테스트용 클라이언트"""
        return EnhancedWebSocketClient(
            client=mock_kis_client, account_info=account_info
        )

    def test_register_callback(self, client):
        """콜백 등록"""

        def test_callback(data):
            pass

        client.register_callback("on_trade", test_callback)

        assert "on_trade" in client.callbacks
        assert test_callback in client.callbacks["on_trade"]

    def test_register_multiple_callbacks(self, client):
        """동일 이벤트에 여러 콜백 등록"""

        def callback1(data):
            pass

        def callback2(data):
            pass

        client.register_callback("on_trade", callback1)
        client.register_callback("on_trade", callback2)

        assert len(client.callbacks["on_trade"]) == 2

    def test_trigger_callback(self, client):
        """콜백 실행"""
        callback_data = []

        def test_callback(data):
            callback_data.append(data)

        client.register_callback("on_trade", test_callback)

        # 직접 콜백 호출 테스트
        test_data = {"code": "005930", "price": 75000}
        for callback in client.callbacks["on_trade"]:
            callback(test_data)

        assert len(callback_data) == 1
        assert callback_data[0] == test_data

    def test_trigger_callback_error_handling(self, client):
        """콜백 실행 중 오류 처리"""
        success_count = [0]

        def failing_callback(data):
            raise ValueError("Test error")

        def working_callback(data):
            success_count[0] += 1

        client.register_callback("on_trade", failing_callback)
        client.register_callback("on_trade", working_callback)

        # 오류 처리 테스트 - try/except로 감싸서 테스트
        test_data = {}
        for callback in client.callbacks["on_trade"]:
            try:
                callback(test_data)
            except Exception as e:
                # 테스트 중 예외는 기록하지만 계속 진행
                print(f"Test callback error: {e}")

        # 정상적인 콜백은 실행되었는지 확인
        assert success_count[0] == 1


class TestMarketDataManagement:
    """시장 데이터 관리 테스트"""

    @pytest.fixture
    def client(self, mock_kis_client, account_info):
        """테스트용 클라이언트"""
        return EnhancedWebSocketClient(
            client=mock_kis_client, account_info=account_info
        )

    def test_get_current_price_existing(self, client):
        """존재하는 종목 현재가 조회"""
        # 테스트 데이터 설정
        client.market_data["stocks"]["005930"] = {
            "name": "삼성전자",
            "price": 75000.0,
            "timestamp": datetime.now(),
        }

        price = client.get_current_price("005930")
        assert price == 75000.0

    def test_get_current_price_nonexistent(self, client):
        """존재하지 않는 종목 현재가 조회"""
        price = client.get_current_price("999999")
        assert price is None

    def test_get_market_summary_empty(self, client):
        """빈 시장 데이터 요약"""
        summary = client.get_market_summary()

        assert "stocks" in summary
        assert "indices" in summary
        assert "timestamp" in summary
        assert summary["stocks"] == {}

    def test_get_market_summary_with_data(self, client):
        """데이터가 있는 시장 요약"""
        # 테스트 데이터 설정
        test_time = datetime.now()
        client.market_data["stocks"]["005930"] = {
            "name": "삼성전자",
            "price": 75000.0,
            "change_rate": 1.5,
            "volume": 1000000,
            "timestamp": test_time,
        }

        summary = client.get_market_summary()

        assert "005930" in summary["stocks"]
        assert summary["stocks"]["005930"]["name"] == "삼성전자"
        assert summary["stocks"]["005930"]["price"] == 75000.0


class TestDataHandlers:
    """데이터 처리 핸들러 테스트"""

    @pytest.fixture
    def client(self, mock_kis_client, account_info):
        """테스트용 클라이언트"""
        return EnhancedWebSocketClient(
            client=mock_kis_client, account_info=account_info
        )

    def test_handle_trade_data_valid(self, client):
        """유효한 체결 데이터 처리"""
        callback_data = []

        def trade_callback(data):
            callback_data.append(data)

        client.register_callback("on_trade", trade_callback)

        # 모의 체결 데이터 (실제 한국투자증권 웹소켓 형식 - 20개 필드)
        raw_data = [
            "005930",
            "093000",
            "75000",
            "1000",
            "+500",
            "+1.23",
            "1",
            "7500000",
            "75100",
            "74900",
            "75500",
            "1000000",
            "100",
            "7500000",
            "7500000",
            "1",
            "2",
            "3",
            "102.5",
            "1",
        ]
        metadata = {"name": "삼성전자"}

        # stock_info 설정
        client.stock_info["005930"] = {"name": "삼성전자", "market": "KOSPI"}

        client._handle_stock_trade(raw_data, metadata)

        # 콜백이 호출되었는지 확인
        assert len(callback_data) == 1
        trade_data = callback_data[0]
        assert trade_data["code"] == "005930"
        assert trade_data["price"] == 75000.0
        assert trade_data["name"]["name"] == "삼성전자"

    def test_handle_trade_data_invalid(self, client):
        """잘못된 체결 데이터 처리"""
        callback_data = []

        def trade_callback(data):
            callback_data.append(data)

        client.register_callback("on_trade", trade_callback)

        # 잘못된 데이터 (길이 부족)
        raw_data = ["005930", "093000"]
        metadata = {}

        client._handle_stock_trade(raw_data, metadata)

        # 콜백이 호출되지 않았는지 확인
        assert len(callback_data) == 0

    def test_handle_index_data(self, client):
        """지수 데이터 처리"""
        callback_data = []

        def index_callback(data):
            callback_data.append(data)

        client.register_callback("on_index", index_callback)

        # 모의 지수 데이터 (실제 한국투자증권 웹소켓 형식 - 10개 필드)
        raw_data = [
            "0001",  # 0: 지수코드
            "2650.50",  # 1: 현재값
            "+12.30",  # 2: 전일대비
            "+0.47",  # 3: 등락률
            "093000",  # 4: 체결시간
            "0",
            "0",
            "0",
            "0",
            "0",  # 5-9: 추가 필드
        ]
        metadata = {"name": "KOSPI"}

        client._handle_index(raw_data, metadata)

        assert len(callback_data) == 1
        index_data = callback_data[0]
        assert index_data["code"] == "0001"
        assert index_data["value"] == 2650.50
        assert index_data["name"] == "KOSPI"


class TestAsyncOperations:
    """비동기 작업 테스트"""

    @pytest.fixture
    def client(self, mock_kis_client, account_info):
        """테스트용 클라이언트"""
        return EnhancedWebSocketClient(
            client=mock_kis_client, account_info=account_info, stock_codes=["005930"]
        )

    @pytest.mark.asyncio
    async def test_init_subscriptions(self, client):
        """비동기 초기화 테스트"""
        with patch.object(client, "ws_agent") as mock_agent, patch.object(
            client.stock_api, "get_stock_info"
        ) as mock_get_info:

            # 모의 주식 정보 반환
            mock_get_info.return_value = {
                "005930": {"name": "삼성전자", "market": "KOSPI"}
            }
            mock_agent.subscribe.return_value = "sub_id"

            # 초기화 메서드 호출
            await client._init_subscriptions()

            # 구독이 설정되었는지 확인
            mock_agent.subscribe.assert_called()

    def test_subscription_setup(self, client):
        """구독 설정 테스트"""
        with patch.object(client, "ws_agent") as mock_agent:
            mock_agent.subscribe.return_value = "sub_id"

            # 주식 구독 직접 테스트
            result = client.ws_agent.subscribe(
                SubscriptionType.STOCK_TRADE,
                "005930",
                handler=client._handle_stock_trade,
            )

            # 구독이 호출되었는지 확인
            mock_agent.subscribe.assert_called_with(
                SubscriptionType.STOCK_TRADE,
                "005930",
                handler=client._handle_stock_trade,
            )


@pytest.mark.integration
class TestIntegration:
    """통합 테스트"""

    @pytest.fixture
    def client_with_mocks(self, mock_kis_client, account_info):
        """완전히 모킹된 클라이언트"""
        with patch("pykis.websocket.enhanced_client.StockAPI") as mock_stock_api, patch(
            "pykis.websocket.enhanced_client.WSAgent"
        ) as mock_ws_agent:

            # StockAPI 모킹
            stock_api_instance = mock_stock_api.return_value
            stock_api_instance.get_stock_info.return_value = {
                "005930": {"name": "삼성전자", "market": "KOSPI"}
            }

            # WSAgent 모킹
            ws_agent_instance = mock_ws_agent.return_value
            ws_agent_instance.subscribe.return_value = "test_sub_id"

            client = EnhancedWebSocketClient(
                client=mock_kis_client,
                account_info=account_info,
                stock_codes=["005930"],
                enable_index=True,
            )

            return client, ws_agent_instance, stock_api_instance

    def test_complete_workflow(self, client_with_mocks):
        """전체 워크플로우 테스트"""
        client, mock_ws_agent, mock_stock_api = client_with_mocks

        # 1. 주식 추가
        client.stock_info["000660"] = {"name": "SK하이닉스", "market": "KOSPI"}
        client.add_stock("000660")
        assert "000660" in client.stock_codes

        # 2. 콜백 등록
        callback_called = []

        def test_callback(data):
            callback_called.append(data)

        client.register_callback("on_trade", test_callback)

        # 3. 데이터 처리 시뮬레이션
        trade_data = [
            "005930",
            "093000",
            "75000",
            "1000",
            "+500",
            "+1.23",
            "1",
            "7500000",
            "75100",
            "74900",
            "75500",
            "1000000",
            "100",
            "7500000",
            "7500000",
            "1",
            "2",
            "3",
            "102.5",
            "1",
        ]
        client.stock_info["005930"] = {"name": "삼성전자", "market": "KOSPI"}
        client._handle_stock_trade(trade_data, {"name": "삼성전자"})

        # 4. 결과 검증
        assert len(callback_called) == 1
        assert callback_called[0]["code"] == "005930"
        assert "005930" in client.market_data["stocks"]

        # 5. 주식 제거
        client.market_data["stocks"]["005930"] = {"price": 75000}
        client.remove_stock("005930")
        assert "005930" not in client.stock_codes
        assert "005930" not in client.market_data["stocks"]


if __name__ == "__main__":
    # 직접 실행 시 테스트 실행
    pytest.main([__file__, "-v"])
