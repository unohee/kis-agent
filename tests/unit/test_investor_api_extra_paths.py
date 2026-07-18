"""StockInvestorAPI의 남은 예외 및 일별 거래원 조회 경로 테스트."""

from unittest.mock import MagicMock

from kis_agent.stock.investor_api import StockInvestorAPI


def test_current_foreign_broker_parse_error_returns_none():
    api = StockInvestorAPI(client=MagicMock(), enable_cache=False)
    api.get_stock_member = MagicMock(return_value={"output": object()})

    assert api._get_foreign_broker_current("005930") is None


def test_member_trading_daily_forwards_all_parameters():
    api = StockInvestorAPI(client=MagicMock(), enable_cache=False)
    api._make_request_dict = MagicMock(return_value={"rt_cd": "0"})

    result = api.get_member_trading_daily(
        "005930", "20250101", "20250131", "001", "NX", "A"
    )

    assert result == {"rt_cd": "0"}
    assert api._make_request_dict.call_args.kwargs["params"] == {
        "FID_COND_MRKT_DIV_CODE": "NX",
        "FID_INPUT_ISCD": "005930",
        "FID_INPUT_ISCD_2": "001",
        "FID_INPUT_DATE_1": "20250101",
        "FID_INPUT_DATE_2": "20250131",
        "FID_SCTN_CLS_CODE": "A",
    }
