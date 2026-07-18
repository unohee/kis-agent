"""
VKOSPICalculator 단위 테스트
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

import kis_agent.futures.vkospi as vkospi
from kis_agent.futures.vkospi import (
    VKOSPICalculator,
    VKOSPIResult,
    _calc_vega_weighted_iv,
    _is_otm,
    _parse_float,
    get_days_to_expiry,
    get_option_expiry_months,
    get_second_thursday,
    interpolation_weights,
)

# ── 헬퍼 ────────────────────────────────────────────────────────────────────

def otm_row(iv: str, vega: str = "1.0", vol: str = "100", cls: str = "OTM 콜") -> dict:
    return {"hts_ints_vltl": iv, "vega": vega, "acml_vol": vol, "atm_cls_name": cls}


def itm_row(iv: str = "15.0") -> dict:
    return {"hts_ints_vltl": iv, "vega": "1.0", "acml_vol": "100", "atm_cls_name": "ITM 콜"}


# ── get_second_thursday ──────────────────────────────────────────────────────

class TestGetSecondThursday:
    def test_2025_march(self):
        assert get_second_thursday(2025, 3) == date(2025, 3, 13)

    def test_2026_june(self):
        # 2026-06-01은 월요일 → 첫 목요일=06-04 → 두 번째=06-11
        assert get_second_thursday(2026, 6) == date(2026, 6, 11)

    def test_2026_july(self):
        # 2026-07-01은 수요일 → 첫 목요일=07-02 → 두 번째=07-09
        assert get_second_thursday(2026, 7) == date(2026, 7, 9)


# ── get_option_expiry_months ────────────────────────────────────────────────

class TestGetOptionExpiryMonths:
    def test_before_expiry_in_month(self):
        # 6월 13일 — 6월 만기(11일) 이후이므로 선근월=7월, 차근월=8월
        today = date(2026, 6, 13)
        near, far = get_option_expiry_months(today)
        assert near == (2026, 7)
        assert far == (2026, 8)

    def test_before_expiry_same_month(self):
        # 6월 5일 — 6월 만기(11일) 이전이므로 선근월=6월, 차근월=7월
        today = date(2026, 6, 5)
        near, far = get_option_expiry_months(today)
        assert near == (2026, 6)
        assert far == (2026, 7)

    def test_on_expiry_day(self):
        # 6월 11일(만기일 당일) — 이전으로 처리 → 6월, 7월
        today = date(2026, 6, 11)
        near, far = get_option_expiry_months(today)
        assert near == (2026, 6)
        assert far == (2026, 7)

    def test_december_rollover(self):
        # 12월 만기 후 → 1월, 2월
        today = date(2025, 12, 20)
        near, far = get_option_expiry_months(today)
        assert near == (2026, 1)
        assert far == (2026, 2)


# ── get_days_to_expiry ──────────────────────────────────────────────────────

class TestGetDaysToExpiry:
    def test_before_expiry(self):
        # 2026-07-09가 만기일, 오늘=2026-07-01 → 8일
        today = date(2026, 7, 1)
        days = get_days_to_expiry(2026, 7, today)
        assert days == 8

    def test_on_expiry(self):
        today = date(2026, 7, 9)
        assert get_days_to_expiry(2026, 7, today) == 0

    def test_after_expiry(self):
        today = date(2026, 7, 15)
        assert get_days_to_expiry(2026, 7, today) == 0


# ── interpolation_weights ───────────────────────────────────────────────────

class TestInterpolationWeights:
    def test_sum_to_one(self):
        w_near, w_far = interpolation_weights(20, 50)
        assert abs(w_near + w_far - 1.0) < 1e-9

    def test_30_days_near(self):
        # T1=30이면 near에 전부 가중
        w_near, w_far = interpolation_weights(30, 60)
        assert abs(w_near - 1.0) < 1e-9

    def test_30_days_far(self):
        # T2=30이면 far에 전부 가중
        w_near, w_far = interpolation_weights(10, 30)
        assert abs(w_far - 1.0) < 1e-9

    def test_clipping_below_t1(self):
        # 30 < T1 → w_near 클리핑
        w_near, w_far = interpolation_weights(35, 65)
        assert w_near == 1.0
        assert w_far == 0.0

    def test_equal_t1_t2(self):
        w_near, w_far = interpolation_weights(25, 25)
        assert w_near == 1.0
        assert w_far == 0.0


# ── _parse_float ────────────────────────────────────────────────────────────

class TestParseFloat:
    def test_normal(self):
        assert _parse_float("18.5") == 18.5

    def test_zero(self):
        assert _parse_float("0") is None
        assert _parse_float("0.0") is None

    def test_empty(self):
        assert _parse_float("") is None
        assert _parse_float("  ") is None
        assert _parse_float("-") is None

    def test_invalid(self):
        assert _parse_float("abc") is None


# ── _is_otm ─────────────────────────────────────────────────────────────────

class TestIsOtm:
    def test_otm_call(self):
        assert _is_otm({"atm_cls_name": "OTM 콜"})

    def test_otm_put(self):
        assert _is_otm({"atm_cls_name": "OTM 풋"})

    def test_itm(self):
        assert not _is_otm({"atm_cls_name": "ITM 콜"})

    def test_atm(self):
        assert not _is_otm({"atm_cls_name": "ATM"})

    def test_missing_key(self):
        assert not _is_otm({})


# ── _calc_vega_weighted_iv ──────────────────────────────────────────────────

class TestCalcVegaWeightedIV:
    def test_basic(self):
        rows = [
            otm_row("20.0", vega="1.0", vol="100"),
            otm_row("24.0", vega="3.0", vol="100"),
        ]
        iv = _calc_vega_weighted_iv(rows)
        # (20*1 + 24*3) / 4 = 92/4 = 23.0
        assert abs(iv - 23.0) < 1e-9

    def test_itm_excluded(self):
        rows = [
            otm_row("20.0", vega="1.0", vol="100"),
            itm_row("30.0"),  # ITM → 제외
        ]
        iv = _calc_vega_weighted_iv(rows)
        assert abs(iv - 20.0) < 1e-9

    def test_low_volume_excluded(self):
        rows = [
            otm_row("20.0", vega="1.0", vol="5"),   # vol < 10 → 제외
            otm_row("25.0", vega="1.0", vol="100"),
        ]
        iv = _calc_vega_weighted_iv(rows)
        assert abs(iv - 25.0) < 1e-9

    def test_zero_iv_excluded(self):
        rows = [
            otm_row("0", vega="1.0", vol="100"),    # iv=0 → 제외
            otm_row("18.0", vega="1.0", vol="100"),
        ]
        iv = _calc_vega_weighted_iv(rows)
        assert abs(iv - 18.0) < 1e-9

    def test_no_valid_rows(self):
        rows = [itm_row(), otm_row("0", vol="5")]
        assert _calc_vega_weighted_iv(rows) is None

    def test_no_vega_fallback_equal_weight(self):
        rows = [
            {"hts_ints_vltl": "20.0", "vega": "", "acml_vol": "100", "atm_cls_name": "OTM 콜"},
            {"hts_ints_vltl": "24.0", "vega": "0", "acml_vol": "100", "atm_cls_name": "OTM 풋"},
        ]
        iv = _calc_vega_weighted_iv(rows)
        assert abs(iv - 22.0) < 1e-9  # 동등 가중 (1.0, 1.0) → 평균


# ── VKOSPICalculator ─────────────────────────────────────────────────────────

class TestVKOSPICalculator:
    def _make_response(self, call_iv: str, put_iv: str) -> dict:
        return {
            "output1": [otm_row(call_iv, vol="100")],
            "output2": [otm_row(put_iv, vol="100", cls="OTM 풋")],
        }

    def test_basic_calculation(self):
        today = date(2026, 6, 13)  # T1=26, T2=61
        near_resp = self._make_response("18.0", "20.0")  # near_iv = (18+20)/2 = 19.0
        far_resp = self._make_response("22.0", "24.0")   # far_iv  = (22+24)/2 = 23.0
        # w_near = (61-30)/(61-26) = 31/35 ≈ 0.8857
        # result ≈ 0.8857*19 + 0.1143*23 ≈ 19.457

        calc = VKOSPICalculator()
        result = calc.calculate(near_resp, far_resp, today)

        assert result is not None
        assert isinstance(result, VKOSPIResult)
        assert 18.0 < result.value < 24.0
        assert result.near_sample_count == 2
        assert result.far_sample_count == 2
        assert result.near_days == 26
        assert result.far_days == 61

    def test_returns_none_when_near_empty(self):
        today = date(2026, 6, 13)
        near_resp = {"output1": [], "output2": []}
        far_resp = self._make_response("20.0", "22.0")

        result = VKOSPICalculator().calculate(near_resp, far_resp, today)
        assert result is None

    def test_returns_none_when_far_empty(self):
        today = date(2026, 6, 13)
        near_resp = self._make_response("18.0", "20.0")
        far_resp = {"output1": [], "output2": []}

        result = VKOSPICalculator().calculate(near_resp, far_resp, today)
        assert result is None

    def test_value_rounded_to_2dp(self):
        today = date(2026, 6, 13)
        near_resp = self._make_response("18.333333", "20.111111")
        far_resp = self._make_response("22.5", "24.5")

        result = VKOSPICalculator().calculate(near_resp, far_resp, today)
        assert result is not None
        # 소수점 2자리 반올림 확인
        assert result.value == round(result.value, 2)

    def test_weights_sum_to_one(self):
        today = date(2026, 6, 13)
        near_resp = self._make_response("18.0", "20.0")
        far_resp = self._make_response("22.0", "24.0")

        result = VKOSPICalculator().calculate(near_resp, far_resp, today)
        assert result is not None
        assert abs(result.w_near + result.w_far - 1.0) < 1e-6

    def test_calculate_from_single(self):
        resp = self._make_response("18.0", "22.0")
        calc = VKOSPICalculator()
        iv = calc.calculate_from_single(resp)
        assert iv is not None
        assert 18.0 <= iv <= 22.0


def test_default_dates_and_result_representation(monkeypatch):
    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 6, 5)

    monkeypatch.setattr(vkospi, "date", FixedDate)
    assert vkospi.get_option_expiry_months()[0] == (2026, 6)
    assert vkospi.get_days_to_expiry(2026, 6) == 6
    calc = VKOSPICalculator()
    response = {"output1": [otm_row("20", vol="100")], "output2": []}
    result = calc.calculate(response, response)
    assert "VKOSPIResult(value=" in repr(result)
