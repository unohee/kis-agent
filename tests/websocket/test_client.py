import pytest
from unittest.mock import MagicMock, AsyncMock
from pykis import Agent
from pykis.websocket.client import KisWebSocket

@pytest.fixture
def agent():
    """Agent fixture"""
    return Agent()

def test_websocket_creation(agent):
    """
    Tests if the websocket client is created correctly.
    """
    ws_client = agent.websocket()
    assert ws_client is not None
    assert isinstance(ws_client, KisWebSocket)

@pytest.mark.asyncio
async def test_websocket_connect(agent):
    """
    Tests the websocket connect method.
    """
    ws_client = agent.websocket(stock_codes=["005930"])
    ws_client.ws = AsyncMock()
    ws_client.get_approval = MagicMock(return_value="test_approval_key")
    
    # Mock the websocket connection
    ws_client.ws.send = AsyncMock()
    
    await ws_client.connect()
    
    # Assert that the approval key was fetched
    ws_client.get_approval.assert_called_once()
    
    # Assert that the websocket send method was called
    ws_client.ws.send.assert_called()
