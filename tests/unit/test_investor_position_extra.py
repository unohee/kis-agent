"""InvestorPositionAnalyzer의 DataFrame 해석 및 종합 경로 테스트."""

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pandas as pd

from kis_agent.stock.investor import InvestorPositionAnalyzer


def _analyzer():
    return InvestorPositionAnalyzer(MagicMock(), {"CANO": "1"})


def test_daily_cumulative_and_market_wide_analysis():
    analyzer = _analyzer()
    frame = pd.DataFrame([{
        "frgn_shnu_vol": "10", "frgn_seln_vol": "2", "frgn_ntby_qty": "8", "frgn_shnu_tr_pbmn": "100", "frgn_seln_tr_pbmn": "20", "frgn_ntby_tr_pbmn": "80",
        "inst_shnu_vol": "9", "inst_seln_vol": "1", "inst_ntby_qty": "8", "inst_shnu_tr_pbmn": "90", "inst_seln_tr_pbmn": "10", "inst_ntby_tr_pbmn": "80",
        "prsn_shnu_vol": "1", "prsn_seln_vol": "9", "prsn_ntby_qty": "-8", "prsn_shnu_tr_pbmn": "10", "prsn_seln_tr_pbmn": "90", "prsn_ntby_tr_pbmn": "-80",
        "stck_prpr": "70000", "acml_vol": "123",
    }])
    analyzer.get_stock_investor_data = MagicMock(return_value=frame)
    daily = analyzer.analyze_daily_position("005930", "20250101")
    assert daily["foreign"]["net_amount"] == 80
    analyzer.analyze_daily_position = MagicMock(return_value=daily)
    cumulative = analyzer.get_30day_cumulative_analysis("005930")
    assert cumulative["institution"]["daily_data"] == [daily["institution"]]
    analyzer.get_daily_market_trends = MagicMock(return_value=frame)
    analyzer.get_foreign_institution_aggregate = MagicMock(return_value=frame)
    result = analyzer.get_market_wide_trends("20250101")
    assert result["date"] == "20250101" and "KOSPI" in result["summary"]


def test_context_variant_comprehensive_and_failure():
    analyzer = _analyzer()
    daily = {"foreign": {"net_amount": 1}, "institution": {"net_amount": 1}, "individual": {"net_amount": -1}}
    cumulative = {"foreign": {"net_amount": -1}, "institution": {"net_amount": -1}, "individual": {"net_amount": 0}}
    assert "패턴 변화" in analyzer.interpret_position_context(daily, cumulative)
    analyzer.analyze_daily_position = MagicMock(return_value=daily)
    analyzer.get_30day_cumulative_analysis = MagicMock(return_value=cumulative)
    result = analyzer.analyze_comprehensive_position("005930")
    assert result.stock_code == "005930"
    analyzer.analyze_daily_position = MagicMock(side_effect=RuntimeError("offline"))
    assert analyzer.analyze_comprehensive_position("005930").score == 0.0


def test_import_success_and_remaining_interpretations(monkeypatch):
    analyzer = _analyzer()
    modules = {
        "domestic_stock.foreign_institution_total.foreign_institution_total": "foreign_institution_total",
        "domestic_stock.inquire_investor.inquire_investor": "inquire_investor",
        "domestic_stock.inquire_investor_daily_by_market.inquire_investor_daily_by_market": "inquire_investor_daily_by_market",
        "domestic_stock.inquire_investor_time_by_market.inquire_investor_time_by_market": "inquire_investor_time_by_market",
    }
    for module_name, function_name in modules.items():
        fake = ModuleType(module_name)
        setattr(fake, function_name, lambda: None)
        monkeypatch.setitem(sys.modules, module_name, fake)
    assert set(analyzer._import_investor_apis()) == set(modules.values())

    daily = {"foreign": {"net_amount": 1}, "institution": {"net_amount": -1}, "individual": {"net_amount": -1}}
    cumulative = {"foreign": {"net_amount": 1}, "institution": {"net_amount": 1}, "individual": {"net_amount": 1}}
    text = analyzer.interpret_position_context(daily, cumulative)
    assert "일시적 매도" in text and "개인: 당일 순매도" in text
    text = analyzer.interpret_position_context({"foreign": {"net_amount": 1}}, {"foreign": {"net_amount": 1}, "institution": {"net_amount": -1}})
    assert "일부가 30일간" in text
