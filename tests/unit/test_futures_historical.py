"""선물 월물 코드와 과거 분봉 페이지네이션 회귀 테스트."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from kis_agent.futures.historical import (
    FuturesContractCode,
    FuturesHistoricalAPI,
    generate_futures_code,
    get_futures_code,
)


def test_contract_code_generation_and_boundaries():
    assert FuturesContractCode.get_series_code(3) == "S"
    assert FuturesContractCode.get_expiry_date(2025, 3) == datetime(2025, 3, 13)
    assert FuturesContractCode.get_front_month_contract(datetime(2025, 3, 13)) == (2025, 3)
    assert FuturesContractCode.get_front_month_contract(datetime(2025, 3, 14)) == (2025, 6)
    assert FuturesContractCode.get_front_month_contract(datetime(2025, 12, 12)) == (2026, 3)
    assert FuturesContractCode.generate_code(2025, 6) == "101M06"
    assert FuturesContractCode.get_code_for_date(datetime(2025, 6, 1)) == "101M06"
    assert FuturesContractCode.get_previous_contract(2025, 3) == (2024, 12)
    assert FuturesContractCode.get_previous_contract(2025, 9) == (2025, 6)
    assert FuturesContractCode.parse_code("101Z12")[1] == 12
    assert get_futures_code(datetime(2025, 9, 1)) == "101U09"
    assert generate_futures_code(2025, 12) == "101Z12"
    for func, arg in ((FuturesContractCode.get_series_code, 1), (lambda _: FuturesContractCode.generate_code(2025, 1), None), (FuturesContractCode.parse_code, "bad"), (FuturesContractCode.parse_code, "101X03")):
        with pytest.raises(ValueError):
            func(arg)


def _api():
    return FuturesHistoricalAPI(MagicMock(), {"CANO": "1", "ACNT_PRDT_CD": "01"})


def test_fetch_page_normalizes_results_and_handles_errors():
    api = _api()
    api._make_request_dict = MagicMock(return_value=None)
    assert api._fetch_page("101S03", "20250102", "153000") == ([], None, None)
    api._make_request_dict.return_value = {"rt_cd": "0", "output2": []}
    assert api._fetch_page("101S03", "20250102", "153000") == ([], None, None)
    api._make_request_dict.return_value = {"rt_cd": "0", "output2": [{"stck_bsop_date": "20250102", "stck_cntg_hour": "090000", "fuop_prpr": "10"}]}
    bars, date, time = api._fetch_page("101S03", "20250102", "153000", include_past=False)
    assert bars[0]["contract"] == "101S03" and (date, time) == ("20250102", "085900")
    assert api._make_request_dict.call_args.kwargs["params"]["FID_PW_DATA_INCU_YN"] == "N"
    api._make_request_dict.return_value = {"rt_cd": "0", "output2": [{"stck_bsop_date": "bad", "stck_cntg_hour": "bad"}]}
    assert api._fetch_page("101S03", "20250102", "153000")[1:] == ("bad", "bad")


def test_history_paginates_filters_and_sorts(monkeypatch):
    api = _api()
    pages = iter([
        ([{"date": "20250103", "time": "100000"}, {"date": "20250102", "time": "150000"}], "20250102", "145900"),
        ([{"date": "20250101", "time": "090000"}], None, None),
    ])
    monkeypatch.setattr(api, "_fetch_page", lambda **kwargs: next(pages))
    bars = api.get_contract_history("101S03", "20250102", "20250103", max_bars=10)
    assert [(bar["date"], bar["time"]) for bar in bars] == [("20250102", "150000"), ("20250103", "100000")]

    pages = iter([([], None, None), ([], None, None), ([], None, None)])
    monkeypatch.setattr(api, "_fetch_page", lambda **kwargs: next(pages))
    assert api.get_minute_bars("20250102", "20250103") == []


def test_history_default_dates_and_page_transitions(monkeypatch):
    api = _api()
    pages = iter([
        ([{"date": "20250103", "time": "153000"}], "20250103", "152900"),
        ([{"date": "20250102", "time": "090000"}], None, None),
        ([], None, None),
    ])
    monkeypatch.setattr(api, "_fetch_page", lambda **kwargs: next(pages))
    bars = api.get_minute_bars("20250102", "20250103", max_bars=10)
    assert [bar["date"] for bar in bars] == ["20250102", "20250103"]

    api._fetch_page = MagicMock(return_value=([{"date": "20250101", "time": "090000"}], None, None))
    assert api.get_contract_history("101S03", "20250102", "20250103") == []
    api._fetch_page = MagicMock(return_value=([{"date": "20250103", "time": "090000"}], None, None))
    assert api.get_contract_history("101S03", "20250102", "20250103")


def test_default_end_dates_weekend_skip_and_empty_contract_page(monkeypatch):
    from kis_agent.futures import historical

    class FixedDateTime(datetime):
        @classmethod
        def now(cls):
            return cls(2025, 1, 6)

    monkeypatch.setattr(historical, "datetime", FixedDateTime)
    api = _api()
    api._fetch_page = MagicMock(return_value=([], None, None))
    assert api.get_minute_bars("20250103") == []
    assert api._fetch_page.call_args_list[0].kwargs["date"] == "20250106"
    assert api.get_contract_history("101S03", "20250101", "") == []

    pages = iter([([], None, None), ([], None, None), ([], None, None)])
    api._fetch_page = MagicMock(side_effect=lambda **kwargs: next(pages))
    assert api.get_minute_bars("20250102", "20250105") == []
