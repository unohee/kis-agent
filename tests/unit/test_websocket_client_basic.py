"""
WebSocket 클라이언트 기본 기능 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import json
import os
import tempfile

from pykis.websocket.client import KisWebSocket
from pykis.core.client import KISClient


class TestKisWebSocketBasic:
    """KisWebSocket 기본 기능 테스트"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock KISClient 픽스처"""
        client = Mock(spec=KISClient)
        client.token = "test_token"
        client.app_key = "test_app_key"
        client.secret_key = "test_secret_key"
        return client
    
    @pytest.fixture
    def account_info(self):
        """테스트 계좌 정보"""
        return {
            "CANO": "12345678",
            "ACNT_PRDT_CD": "01"
        }
    
    @pytest.fixture
    def temp_log_dir(self):
        """임시 로그 디렉토리"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_websocket_init_basic(self, mock_client, account_info):
        """기본 초기화 테스트"""
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info
        )
        
        assert ws_client.client == mock_client
        assert ws_client.account_info == account_info
        assert ws_client.stock_codes == []
        assert ws_client.url == 'ws://ops.koreainvestment.com:21000'
        assert ws_client.enable_index is True
        assert ws_client.enable_program_trading is True
        assert ws_client.enable_ask_bid is False

    def test_websocket_init_with_stock_codes(self, mock_client, account_info):
        """종목코드와 함께 초기화"""
        stock_codes = ['005930', '000660']
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info,
            stock_codes=stock_codes
        )
        
        assert ws_client.stock_codes == stock_codes
        assert len(ws_client.latest_trade) == 2
        assert len(ws_client.trade_history) == 2
        assert '005930' in ws_client.latest_trade
        assert '000660' in ws_client.trade_history

    def test_websocket_init_with_purchase_prices(self, mock_client, account_info):
        """매수 정보와 함께 초기화"""
        purchase_prices = {
            '005930': (70000, 10),
            '000660': (120000, 5)
        }
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info,
            purchase_prices=purchase_prices
        )
        
        assert ws_client.purchase_prices == purchase_prices

    def test_websocket_init_with_options(self, mock_client, account_info):
        """옵션과 함께 초기화"""
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info,
            enable_index=False,
            enable_program_trading=False,
            enable_ask_bid=True
        )
        
        assert ws_client.enable_index is False
        assert ws_client.enable_program_trading is False
        assert ws_client.enable_ask_bid is True

    @patch('os.makedirs')
    def test_log_directory_creation(self, mock_makedirs, mock_client, account_info):
        """로그 디렉토리 생성 테스트"""
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info
        )
        
        mock_makedirs.assert_called_with('logs/websocket', exist_ok=True)
        assert ws_client.log_dir == 'logs/websocket'
        assert 'trade_history_' in ws_client.trade_log_file
        assert ws_client.trade_log_file.endswith('.jsonl')

    def test_data_structures_initialization(self, mock_client, account_info):
        """데이터 구조 초기화 테스트"""
        stock_codes = ['005930', '000660', '035720']
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info,
            stock_codes=stock_codes
        )
        
        # 각 종목별 데이터 구조 확인
        for code in stock_codes:
            assert code in ws_client.latest_trade
            assert ws_client.latest_trade[code] is None
            assert code in ws_client.trade_history
            assert ws_client.trade_history[code] == []
            assert code in ws_client.prev_indicators
            assert ws_client.prev_indicators[code] == (None, None)
        
        # 전역 데이터 구조 확인
        assert isinstance(ws_client.latest_index, dict)
        assert isinstance(ws_client.latest_program_trading, dict)
        assert isinstance(ws_client.latest_ask_bid, dict)
        assert isinstance(ws_client.stock_names, dict)
        assert isinstance(ws_client.open_prices, dict)
        assert isinstance(ws_client.subscribed_stocks, set)

    def test_add_stock_code(self, mock_client, account_info):
        """종목코드 동적 추가 테스트"""
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info,
            stock_codes=['005930']
        )
        
        # 새 종목 추가
        new_code = '000660'
        ws_client.stock_codes.append(new_code)
        ws_client.latest_trade[new_code] = None
        ws_client.trade_history[new_code] = []
        ws_client.prev_indicators[new_code] = (None, None)
        ws_client.subscribed_stocks.add(new_code)
        
        assert new_code in ws_client.stock_codes
        assert new_code in ws_client.latest_trade
        assert new_code in ws_client.trade_history
        assert new_code in ws_client.prev_indicators
        assert new_code in ws_client.subscribed_stocks

    def test_remove_stock_code(self, mock_client, account_info):
        """종목코드 제거 테스트"""
        stock_codes = ['005930', '000660']
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info,
            stock_codes=stock_codes
        )
        
        # 종목 제거
        remove_code = '000660'
        ws_client.stock_codes.remove(remove_code)
        del ws_client.latest_trade[remove_code]
        del ws_client.trade_history[remove_code]
        del ws_client.prev_indicators[remove_code]
        ws_client.subscribed_stocks.discard(remove_code)
        
        assert remove_code not in ws_client.stock_codes
        assert remove_code not in ws_client.latest_trade
        assert remove_code not in ws_client.trade_history
        assert remove_code not in ws_client.prev_indicators
        assert remove_code not in ws_client.subscribed_stocks

    def test_approval_key_initialization(self, mock_client, account_info):
        """승인키 초기화 상태 확인"""
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info
        )
        
        assert ws_client.approval_key is None
        assert ws_client.aes_key is None
        assert ws_client.aes_iv is None

    @patch('pykis.websocket.client.StockAPI')
    def test_stock_api_initialization(self, mock_stock_api, mock_client, account_info):
        """StockAPI 초기화 테스트"""
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info
        )
        
        mock_stock_api.assert_called_once_with(client=mock_client, account_info=account_info)
        assert ws_client.stock_api is not None

    def test_empty_stock_codes_handling(self, mock_client, account_info):
        """빈 종목코드 리스트 처리"""
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info,
            stock_codes=[]
        )
        
        assert ws_client.stock_codes == []
        assert ws_client.latest_trade == {}
        assert ws_client.trade_history == {}
        assert ws_client.prev_indicators == {}
        assert len(ws_client.subscribed_stocks) == 0

    def test_none_stock_codes_handling(self, mock_client, account_info):
        """None 종목코드 처리"""
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info,
            stock_codes=None
        )
        
        assert ws_client.stock_codes == []

    def test_purchase_prices_default(self, mock_client, account_info):
        """매수가 기본값 처리"""
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info,
            purchase_prices=None
        )
        
        assert ws_client.purchase_prices == {}

    def test_large_stock_codes_list(self, mock_client, account_info):
        """대용량 종목코드 리스트 처리"""
        # 100개 종목 생성
        stock_codes = [f"{str(i).zfill(6)}" for i in range(100)]
        
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info,
            stock_codes=stock_codes
        )
        
        assert len(ws_client.stock_codes) == 100
        assert len(ws_client.latest_trade) == 100
        assert len(ws_client.trade_history) == 100
        assert len(ws_client.prev_indicators) == 100
        assert len(ws_client.subscribed_stocks) == 100

    def test_duplicate_stock_codes(self, mock_client, account_info):
        """중복 종목코드 처리"""
        stock_codes = ['005930', '000660', '005930']  # 중복 포함
        
        ws_client = KisWebSocket(
            client=mock_client,
            account_info=account_info,
            stock_codes=stock_codes
        )
        
        # 중복이 그대로 유지됨 (필터링하지 않음)
        assert len(ws_client.stock_codes) == 3
        assert '005930' in ws_client.latest_trade
        assert len(ws_client.subscribed_stocks) == 2  # set이므로 중복 제거됨