"""StockAPI 파사드의 직접 시세 호출 및 동적 위임 실패 회귀 테스트."""

from unittest.mock import MagicMock

import pytest

from kis_agent.stock.api_facade import StockAPI


def test_direct_index_chart_requests_and_missing_dynamic_attribute():
    api = object.__new__(StockAPI)
    api.price_api = MagicMock()
    api.market_api = MagicMock()
    api.investor_api = MagicMock()
    api._make_request_dict = MagicMock(return_value={"rt_cd": "0"})

    assert api.get_daily_index_chart_price("0007", "20250101", "20250131", "W") == api.price_api.get_daily_index_chart_price.return_value
    api.price_api.get_daily_index_chart_price.assert_called_once_with("0007", "20250101", "20250131", "W", "U")
    assert api.get_time_index_chart_price("0007", "5") == {"rt_cd": "0"}
    assert api._make_request_dict.call_args.kwargs["tr_id"] == "FHKUP03500200"
    assert api._make_request_dict.call_args.kwargs["params"] == {
        "FID_COND_MRKT_DIV_CODE": "U",
        "FID_ETC_CLS_CODE": "0",
        "FID_INPUT_ISCD": "0007",
        "FID_INPUT_HOUR_1": "900",
        "FID_PW_DATA_INCU_YN": "Y",
    }
    api.get_time_index_chart_price("0001", "3600")
    assert api._make_request_dict.call_args.kwargs["params"]["FID_INPUT_HOUR_1"] == "3600"

    api.price_api = object()
    api.market_api = object()
    api.investor_api = object()
    with pytest.raises(AttributeError, match="has no attribute"):
        _ = api.not_available
