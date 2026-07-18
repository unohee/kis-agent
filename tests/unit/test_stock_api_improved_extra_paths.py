"""개선된 StockAPI의 기본값과 비정상 응답 경로 회귀 테스트."""

from unittest.mock import MagicMock, patch

import pytest

from kis_agent.core.exceptions import APIException, ValidationException
from kis_agent.stock import api_improved
from kis_agent.stock.api_improved import StockAPI


def _api():
    api = object.__new__(StockAPI)
    api._make_request_dict = MagicMock()
    api._exception_logger = MagicMock()
    return api


def test_dataframe_unexpected_output_and_daily_validation():
    api = _api()
    api._make_request_dict.return_value = {"output": "bad"}
    with pytest.raises(APIException):
        api._make_request_dataframe("endpoint", "tr", {})
    with pytest.raises(ValidationException):
        api.get_daily_price("short")


def test_foreign_net_buy_empty_and_populated_defaults_and_holidays():
    api = _api()
    api._make_request_dict.return_value = {"output": []}
    assert api.get_foreign_net_buy("005930")[0] == 0

    api._make_request_dict.return_value = {
        "output": {"frgn_ntby_qty": "3", "frgn_hldn_rate": "1.2"}
    }
    assert api.get_foreign_net_buy("005930", "20250101")[0] == 3
    assert (
        api._make_request_dict.call_args.kwargs["endpoint"]
        == api_improved.API_ENDPOINTS["INQUIRE_INVESTOR"]
    )
    assert api._make_request_dict.call_args.kwargs["tr_id"] == "FHKST01010900"

    api._make_request_dataframe = MagicMock(return_value="holidays")
    assert api.get_holidays() == "holidays"
    assert (
        api._make_request_dataframe.call_args.kwargs["endpoint"]
        == api_improved.API_ENDPOINTS["CHK_HOLIDAY"]
    )
    assert api._make_request_dataframe.call_args.kwargs["tr_id"] == "CTCA0903R"
    with pytest.raises(ValidationException):
        api.get_foreign_net_buy("005930", "bad")


def test_stock_member_raises_when_every_response_is_empty():
    api = _api()
    api.client = MagicMock()
    api.client.make_request.return_value = None
    with pytest.raises(APIException, match="회원사 정보 조회 실패"):
        api.get_stock_member("005930", retries=2)


@pytest.mark.parametrize(
    ("price_error", "foreign_error", "expected"),
    [
        (None, None, "삼성전자 현재가"),
        (ValidationException("bad input"), None, "입력 오류"),
        (APIException("bad api"), None, "API 오류"),
        (RuntimeError("bad runtime"), APIException("bad foreign"), "예상치 못한 오류"),
    ],
)
def test_example_usage_handles_each_documented_error(
    price_error, foreign_error, expected, capsys
):
    with patch("kis_agent.core.client.KISClient") as client, patch.object(
        api_improved, "StockAPI"
    ) as stock_api:
        instance = stock_api.return_value
        instance.get_stock_price.side_effect = price_error
        instance.get_foreign_net_buy.side_effect = foreign_error
        if foreign_error is None:
            instance.get_foreign_net_buy.return_value = (10, {"code": "005930"})
        api_improved.example_usage()

    assert client.called
    output = capsys.readouterr().out
    assert expected in output
    if foreign_error:
        assert "조회 실패" in output
