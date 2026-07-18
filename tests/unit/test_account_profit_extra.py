"""AccountProfitAPI의 빈 응답과 오류 반환 경로 회귀 테스트."""

from unittest.mock import MagicMock

from kis_agent.account.profit_api import AccountProfitAPI


def _api():
    api = object.__new__(AccountProfitAPI)
    api.account = {"CANO": "12345678", "ACNT_PRDT_CD": "01"}
    api._make_request_dict = MagicMock()
    return api


def test_period_profit_methods_return_none_for_empty_and_failed_responses():
    api = _api()
    api._make_request_dict.return_value = None
    assert api.inquire_period_trade_profit("20250101", "20250131") is None
    assert api.inquire_period_profit("20250101", "20250131") is None
    assert api.inquire_period_rights("20250101", "20250131") is None

    api._make_request_dict.side_effect = RuntimeError("offline")
    assert api.inquire_period_trade_profit("20250101", "20250131") is None
    assert api.inquire_period_profit("20250101", "20250131") is None
    assert api.inquire_period_rights("20250101", "20250131") is None


def test_period_profit_methods_add_response_metadata_to_dataframes():
    api = _api()
    api._make_request_dict.return_value = {
        "rt_cd": "0", "msg_cd": "OK", "msg1": "success", "output1": [{"value": "1"}]
    }
    trade = api.inquire_period_trade_profit("20250101", "20250131")
    daily = api.inquire_period_profit("20250101", "20250131")
    rights = api.inquire_period_rights("20250101", "20250131")
    for frame in (trade, daily, rights):
        assert frame.loc[0, "msg1"] == "success"


def test_daily_ccld_pagination_returns_none_when_request_fails():
    api = _api()
    api.client = MagicMock()
    api.client.make_request.side_effect = RuntimeError("offline")
    assert api.inquire_daily_ccld("20250101", "20250131", pagination=True) is None


def test_daily_ccld_pagination_combines_pages_deduplicates_and_calls_callback():
    api = _api()
    first_page = [
        {
            "ord_dt": "20250102", "ord_tmd": f"09{index:04d}", "odno": str(index),
            "pdno": "005930", "ord_qty": "1", "tot_ccld_qty": "1", "tot_ccld_amt": "10",
        }
        for index in range(100)
    ]
    second_page = [first_page[0], {
        "ord_dt": "20250101", "ord_tmd": "090000", "odno": "new", "pdno": "000660",
        "ord_qty": "2", "tot_ccld_qty": "2", "tot_ccld_amt": "20",
    }]
    api.client = MagicMock()
    api.client.make_request.side_effect = [
        {"rt_cd": "0", "msg1": "조회가 계속됩니다", "output1": first_page, "ctx_area_fk100": "fk", "ctx_area_nk100": "nk"},
        {"rt_cd": "0", "msg1": "완료", "output1": second_page, "output2": {"prsm_tlex_smtl": "30"}},
    ]
    callback = MagicMock()

    result = api.inquire_daily_ccld(
        "20250101", "20250131", pagination=True, page_callback=callback
    )

    assert result["output2"] == {
        "tot_ord_qty": "102", "tot_ccld_qty": "102", "tot_ccld_amt": "1020.0",
        "page_count": 2, "total_count": 101, "prsm_tlex_smtl": "30",
    }
    assert len(result["output1"]) == 101
    assert callback.call_count == 2
    assert api.client.make_request.call_args_list[1].kwargs["headers"] == {"tr_cont": "N"}


def test_daily_ccld_single_request_and_profit_dict_wrappers():
    api = _api()
    api._make_request_dict.return_value = {"rt_cd": "0"}
    assert api.inquire_daily_ccld("20240101", "20240131", pdno="005930") == {"rt_cd": "0"}
    assert api._make_request_dict.call_args.kwargs["tr_id"] == "CTSC9215R"

    api._make_request_dict.return_value = {"output1": []}
    assert api.get_period_trade_profit("20250101", "20250131") == {"output1": []}
    assert api.get_period_profit("20250101", "20250131") == {"output1": []}


def test_pagination_handles_initial_error_empty_page_and_missing_keys():
    api = _api()
    api.client = MagicMock()
    api.client.make_request.return_value = {"rt_cd": "1", "msg1": "bad"}
    assert api.inquire_daily_ccld("20250101", "20250131", pagination=True) is None

    api.client.make_request.return_value = {"rt_cd": "0", "output1": []}
    empty = api.inquire_daily_ccld("20250101", "20250131", pagination=True)
    assert empty["msg_cd"] == "NO_DATA"

    api.client.make_request.return_value = {
        "rt_cd": "0", "msg1": "조회가 계속됩니다", "output1": [
            {"ord_dt": "20250101", "odno": "1", "pdno": "005930"}
        ],
    }
    result = api.inquire_daily_ccld("20250101", "20250131", pagination=True)
    assert result["output2"]["page_count"] == 1


def test_daily_ccld_exception_and_later_page_failure_return_expected_values():
    api = _api()
    api._make_request_dict.side_effect = RuntimeError("offline")
    assert api.inquire_daily_ccld("20250101", "20250131") is None

    api.client = MagicMock()
    page = [{"ord_dt": "20250101", "odno": str(index), "pdno": "005930"} for index in range(100)]
    api.client.make_request.side_effect = [
        {"rt_cd": "0", "msg1": "계속", "output1": page, "ctx_area_fk100": "fk"},
        {"rt_cd": "1", "msg1": "bad"},
    ]
    result = api.inquire_daily_ccld("20250101", "20250131", pagination=True)
    assert result["output2"]["page_count"] == 1


def test_pagination_short_page_and_extra_summary_fields():
    api = _api()
    api.client = MagicMock()
    api.client.make_request.return_value = {
        "rt_cd": "0", "msg1": "계속", "ctx_area_fk100": "fk", "output1": [
            {"ord_dt": "20250101", "odno": "1", "pdno": "005930"}
        ],
        "output2": {"pchs_avg_pric": "70000"},
    }
    result = api.inquire_daily_ccld("20250101", "20250131", pagination=True)
    assert result["output2"]["pchs_avg_pric"] == "70000"


def test_constructor_delegates_to_base_api():
    client = MagicMock()
    api = AccountProfitAPI(
        client, {"CANO": "12345678", "ACNT_PRDT_CD": "01"}, _from_agent=True
    )
    assert api.client is client
    assert api.account["CANO"] == "12345678"
