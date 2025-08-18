import pytest
from pykis.stock.api import StockAPI
from pykis.core.client import KISClient
import os

@pytest.fixture
def stock_api():
    """Setup for the tests."""
    client = KISClient()
    account_info = {
        "CANO": os.environ.get("KIS_CANO"),
        "ACNT_PRDT_CD": os.environ.get("KIS_ACNT_PRDT_CD"),
    }
    return StockAPI(client, account_info)

@pytest.mark.xfail(reason="This test is expected to fail until the correct tr_id for KOSPI 200 index is found.")
def test_get_kospi200_index(stock_api):
    """Test fetching KOSPI 200 index."""
    # We need to provide a valid futures month to get the underlying KOSPI 200 index.
    # This might need to be updated periodically.
    futures_month = "202409"
    response = stock_api.get_kospi200_index(futures_month)
    assert response is not None
    assert response['rt_cd'] == '0'
    assert 'output2' in response
    assert 'bstp_nmix_prpr' in response['output2'] # Check for the index price field

def test_get_futures_price(stock_api):
    """Test fetching futures price."""
    # Note: The futures code might need to be updated depending on the current month.
    futures_code = "101S06" 
    response = stock_api.get_futures_price(futures_code)
    assert response is not None
    assert response['rt_cd'] == '0'
    assert 'output1' in response
    assert 'output2' in response
