"""
KOSPI 200 선물 베이시스 계산 예제

Note: 이 예제는 레거시 StockAPI를 사용합니다. 새 코드에서는 Agent 사용을 권장합니다.
"""

import os

from pykis.core.client import KISClient
from pykis.stock import LegacyStockAPI as StockAPI

# Set up the KISClient and StockAPI
client = KISClient()
account_info = {
    "CANO": os.environ.get("KIS_CANO"),
    "ACNT_PRDT_CD": os.environ.get("KIS_ACNT_PRDT_CD"),
}
stock_api = StockAPI(client, account_info)

# Fetch the KOSPI 200 index
# Note: This method is currently not working and is marked as xfail in the tests.
# We will use a placeholder value for the KOSPI 200 index.
kospi200_index_response = stock_api.get_kospi200_index()
kospi200_index = 350.00

# Fetch the futures price
# Note: The futures code might need to be updated depending on the current month.
futures_code = "101S06"
futures_response = stock_api.get_futures_price(futures_code)

if futures_response and futures_response["rt_cd"] == "0":
    futures_price = float(futures_response["output"]["stck_prpr"])

    if kospi200_index_response and kospi200_index_response["rt_cd"] == "0":
        kospi200_index = float(kospi200_index_response["output2"]["bstp_nmix_prpr"])
        basis = futures_price - kospi200_index
        print(f"KOSPI 200 Index: {kospi200_index}")
    else:
        basis = futures_price - kospi200_index
        print(f"KOSPI 200 Index: {kospi200_index} (Placeholder)")

    print(f"Futures Price ({futures_code}): {futures_price}")
    print(f"KOSPI Basis: {basis:.2f}")
else:
    print("Failed to fetch futures price.")
    if futures_response:
        print(f"Error: {futures_response.get('msg1')}")

if kospi200_index_response and kospi200_index_response["rt_cd"] != "0":
    print("\nFailed to fetch KOSPI 200 index.")
    print(f"Error: {kospi200_index_response.get('msg1')}")
