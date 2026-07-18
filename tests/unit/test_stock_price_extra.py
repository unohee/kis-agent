"""회원사 재시도와 전체 일봉 페이지네이션 회귀 테스트."""

from unittest.mock import MagicMock

from kis_agent.stock.price_api import StockPriceAPI


def _api():
    return StockPriceAPI(MagicMock(), {"CANO": "1", "ACNT_PRDT_CD": "01"})


def test_member_retries_success_error_none_exception_and_alias():
    api = _api()
    api._make_request_dict = MagicMock(side_effect=[{"rt_cd": "1", "msg1": "retry"}, {"rt_cd": "0", "output": []}])
    assert api.get_stock_member("005930", retries=2)["rt_cd"] == "0"
    api._make_request_dict.side_effect = [{"rt_cd": "1"}]
    assert api.get_stock_member("005930", retries=1)["rt_cd"] == "1"
    api._make_request_dict.side_effect = [None]
    assert api.get_stock_member("005930", retries=1) is None
    api._make_request_dict.side_effect = [None, None]
    assert api.get_stock_member("005930", retries=2) is None
    api._make_request_dict.side_effect = RuntimeError("offline")
    assert api.get_stock_member("005930", retries=1) is None
    api._make_request_dict.side_effect = [RuntimeError("offline"), RuntimeError("offline")]
    assert api.get_stock_member("005930", retries=2) is None
    assert api.get_stock_member("005930", retries=0) is None
    api.get_stock_member = MagicMock(return_value="alias")
    assert api.get_member("005930", 3, "NX") == "alias"


def test_daily_price_all_paginates_deduplicates_and_stops_safely():
    api = _api()
    page1 = [{"stck_bsop_date": "20250103"}] * 100
    page1[-1] = {"stck_bsop_date": "20250102"}
    page2 = [{"stck_bsop_date": "20250102"}, {"stck_bsop_date": "20250101"}]
    api.inquire_daily_itemchartprice = MagicMock(side_effect=[{"rt_cd": "0", "output1": {"name": "x"}, "output2": page1}, {"rt_cd": "0", "output2": page2}])
    result = api.get_daily_price_all("005930", "20250101", "20250103")
    assert result["_pagination_info"]["total_calls"] == 2
    assert [row["stck_bsop_date"] for row in result["output2"]] == ["20250103", "20250102", "20250101"]
    api.inquire_daily_itemchartprice.side_effect = [{"rt_cd": "0", "output2": []}]
    assert api.get_daily_price_all("005930", "20250101", "20250103")["output2"] == []
    api.inquire_daily_itemchartprice.side_effect = [{"rt_cd": "1", "msg1": "bad"}]
    assert api.get_daily_price_all("005930", "20250101", "20250103")["_pagination_info"]["total_calls"] == 1
    api.inquire_daily_itemchartprice.side_effect = [{"rt_cd": "0", "output2": [{"stck_bsop_date": ""}] * 100}]
    assert api.get_daily_price_all("005930", "20250101", "20250103")["_pagination_info"]["total_calls"] == 1
    api.inquire_daily_itemchartprice.side_effect = [{"rt_cd": "0", "output2": [{"stck_bsop_date": "bad"}] * 100}]
    assert api.get_daily_price_all("005930", "20250101", "20250103")["_pagination_info"]["total_calls"] == 1
    api.inquire_daily_itemchartprice.side_effect = [{"rt_cd": "0", "output2": [{"stck_bsop_date": "20250101"}] * 100}]
    assert api.get_daily_price_all("005930", "20250101", "20250103")["_pagination_info"]["total_calls"] == 1


def test_index_financial_and_basic_requests_delegate_to_client():
    api = _api()
    api._make_request_dict = MagicMock(return_value={"rt_cd": "0"})
    assert api.get_daily_index_chart_price("0007", "20250101", "20250102") == {"rt_cd": "0"}
    assert api.get_stock_financial("005930") == {"rt_cd": "0"}
    assert api.get_stock_basic("005930") == {"rt_cd": "0"}
