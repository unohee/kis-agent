"""Unit tests for historical intraday volume profiles."""

from datetime import datetime, timedelta

import pytest

from kis_agent.execution.volume_profile import (
    VolumeProfile,
    build_profile_from_bars,
    fetch_volume_profile,
)


def bar(hhmmss, volume):
    return {"stck_cntg_hour": hhmmss, "cntg_vol": volume}


class FakeStockAPI:
    """Minute-chart stub keyed by date, with optional per-date failures."""

    def __init__(self, by_date=None, failures=None):
        self.by_date = by_date or {}
        self.failures = failures or set()
        self.requested = []

    def get_daily_minute_price(self, code, date, market="J"):
        self.requested.append(date)
        if date in self.failures:
            raise RuntimeError("upstream 500")
        bars = self.by_date.get(date)
        if bars is None:
            return {"rt_cd": "0", "output2": []}
        return {"rt_cd": "0", "output2": bars}


class FakeAgent:
    def __init__(self, stock_api):
        self.stock_api = stock_api


class TestBuildProfileFromBars:
    def test_averages_across_contributing_sessions(self):
        profile = build_profile_from_bars(
            {
                "20260818": [bar("090000", "1000"), bar("140000", "3000")],
                "20260819": [bar("090000", "2000"), bar("140000", "1000")],
            }
        )
        assert profile.minute_volumes == {540: 1500.0, 840: 2000.0}
        assert profile.source_dates == ["20260818", "20260819"]
        assert profile.fallback_reason is None

    def test_blank_sessions_do_not_dilute_the_average(self):
        profile = build_profile_from_bars(
            {
                "20260818": [bar("090000", "1000")],
                "20260819": [],
                "20260820": [bar("090000", "3000")],
            }
        )
        # Divided by 2 contributing sessions, not 3 requested ones.
        assert profile.minute_volumes[540] == 2000.0
        assert "20260819" not in profile.source_dates

    def test_comma_separated_volumes_are_parsed(self):
        profile = build_profile_from_bars({"20260818": [bar("090000", "1,234")]})
        assert profile.minute_volumes[540] == 1234.0

    def test_malformed_bars_are_ignored(self):
        profile = build_profile_from_bars(
            {
                "20260818": [
                    bar("", "100"),
                    bar("xx0000", "100"),
                    bar("990000", "100"),
                    bar("090000", "abc"),
                    bar("090000", "500"),
                ]
            }
        )
        assert profile.minute_volumes == {540: 500.0}

    def test_no_usable_data_yields_an_explained_empty_profile(self):
        profile = build_profile_from_bars({"20260818": [], "20260819": []})
        assert profile.is_empty
        assert profile.fallback_reason
        assert profile.source_dates == []

    def test_seconds_within_a_minute_collapse_into_one_bucket(self):
        profile = build_profile_from_bars(
            {"20260818": [bar("090015", "100"), bar("090045", "200")]}
        )
        assert profile.minute_volumes == {540: 300.0}


class TestBucketWeights:
    def setup_method(self):
        self.profile = build_profile_from_bars(
            {
                "20260818": [
                    bar("090000", "100"),
                    bar("093000", "200"),
                    bar("140000", "700"),
                ]
            }
        )

    def test_weights_track_the_volume_curve(self):
        weights = self.profile.bucket_weights(
            datetime(2026, 8, 21, 9, 0), timedelta(hours=6), 6
        )
        assert weights == [300.0, 0.0, 0.0, 0.0, 0.0, 700.0]

    def test_buckets_are_half_open_so_no_minute_is_counted_twice(self):
        # 09:30 sits exactly on the boundary between two 30-minute buckets.
        weights = self.profile.bucket_weights(
            datetime(2026, 8, 21, 9, 0), timedelta(hours=1), 2
        )
        assert weights == [100.0, 200.0]
        assert sum(weights) == 300.0

    def test_empty_profile_returns_none_for_caller_fallback(self):
        empty = VolumeProfile(fallback_reason="no data")
        assert (
            empty.bucket_weights(datetime(2026, 8, 21, 9, 0), timedelta(hours=1), 4)
            is None
        )

    def test_window_covering_no_traded_minutes_returns_none(self):
        weights = self.profile.bucket_weights(
            datetime(2026, 8, 21, 22, 0), timedelta(hours=1), 4
        )
        assert weights is None

    @pytest.mark.parametrize(
        "buckets,duration", [(0, timedelta(hours=1)), (4, timedelta(0))]
    )
    def test_rejects_out_of_range_arguments(self, buckets, duration):
        with pytest.raises(ValueError):
            self.profile.bucket_weights(datetime(2026, 8, 21, 9, 0), duration, buckets)


class TestFetchVolumeProfile:
    def test_collects_the_requested_number_of_sessions(self):
        api = FakeStockAPI(
            {
                "20260820": [bar("090000", "100")],
                "20260819": [bar("090000", "200")],
                "20260818": [bar("090000", "300")],
            }
        )
        profile = fetch_volume_profile(
            FakeAgent(api), "005930", days=3, end_date=datetime(2026, 8, 21)
        )
        assert sorted(profile.source_dates) == ["20260818", "20260819", "20260820"]
        assert profile.minute_volumes[540] == 200.0

    def test_weekends_are_skipped_without_an_api_call(self):
        # 2026-08-24 is a Monday; the walk back must skip Sat 22 and Sun 23.
        api = FakeStockAPI({"20260821": [bar("090000", "100")]})
        fetch_volume_profile(
            FakeAgent(api), "005930", days=1, end_date=datetime(2026, 8, 24)
        )
        assert "20260822" not in api.requested
        assert "20260823" not in api.requested
        assert "20260821" in api.requested

    def test_api_failures_degrade_to_an_explained_empty_profile(self):
        api = FakeStockAPI(failures={"20260820", "20260819", "20260818"})
        profile = fetch_volume_profile(
            FakeAgent(api), "005930", days=3, end_date=datetime(2026, 8, 21)
        )
        assert profile.is_empty
        assert "오류" in (profile.fallback_reason or "")

    def test_partial_failures_still_produce_a_profile(self):
        api = FakeStockAPI(
            {"20260819": [bar("090000", "500")]}, failures={"20260820"}
        )
        profile = fetch_volume_profile(
            FakeAgent(api), "005930", days=1, end_date=datetime(2026, 8, 21)
        )
        assert profile.source_dates == ["20260819"]

    def test_lookback_is_bounded_when_the_market_never_opens(self):
        api = FakeStockAPI({})
        profile = fetch_volume_profile(
            FakeAgent(api), "005930", days=5, end_date=datetime(2026, 8, 21)
        )
        assert profile.is_empty
        # Bounded walk: weekdays within a 45-calendar-day window, no more.
        assert len(api.requested) <= 45

    def test_today_is_never_included(self):
        api = FakeStockAPI({"20260821": [bar("090000", "100")]})
        fetch_volume_profile(
            FakeAgent(api), "005930", days=1, end_date=datetime(2026, 8, 21)
        )
        assert "20260821" not in api.requested

    def test_rejects_non_positive_days(self):
        with pytest.raises(ValueError):
            fetch_volume_profile(FakeAgent(FakeStockAPI()), "005930", days=0)


class TestNumericParsing:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            (None, 0.0),
            (1234, 1234.0),
            (12.5, 12.5),
            ("", 0.0),
            ("   ", 0.0),
            ("1,234", 1234.0),
            ("nope", 0.0),
        ],
    )
    def test_to_float_tolerates_kis_field_shapes(self, raw, expected):
        from kis_agent.execution.volume_profile import _to_float

        assert _to_float(raw) == expected

    def test_sub_minute_window_start_rounds_up_to_the_next_minute(self):
        # 09:00:30 must not pull in the 09:00 bar it already missed half of.
        profile = build_profile_from_bars(
            {"20260818": [bar("090000", "100"), bar("090100", "200")]}
        )
        weights = profile.bucket_weights(
            datetime(2026, 8, 21, 9, 0, 30), timedelta(minutes=2), 1
        )
        assert weights == [200.0]
