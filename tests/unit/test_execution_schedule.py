"""Unit tests for deterministic order-slicing schedules."""

from datetime import datetime, timedelta

import pytest

from kis_agent.execution.schedule import (
    OrderSlice,
    build_twap_schedule,
    build_vwap_schedule,
    split_quantity,
    split_quantity_weighted,
)

START = datetime(2026, 8, 21, 10, 0)


class TestSplitQuantity:
    def test_even_split_sums_to_total(self):
        assert split_quantity(100, 4) == [25, 25, 25, 25]

    def test_remainder_goes_to_leading_chunks(self):
        chunks = split_quantity(10, 3)
        assert chunks == [4, 3, 3]
        assert sum(chunks) == 10

    def test_chunks_never_differ_by_more_than_one(self):
        chunks = split_quantity(997, 13)
        assert sum(chunks) == 997
        assert max(chunks) - min(chunks) <= 1

    def test_more_parts_than_shares_drops_parts_instead_of_padding_zeros(self):
        # A zero-share child order is not something the exchange accepts.
        assert split_quantity(2, 5) == [1, 1]

    @pytest.mark.parametrize("total,parts", [(0, 3), (-1, 3), (10, 0), (10, -2)])
    def test_rejects_non_positive_arguments(self, total, parts):
        with pytest.raises(ValueError):
            split_quantity(total, parts)


class TestSplitQuantityWeighted:
    def test_distributes_in_proportion_to_weights(self):
        assert split_quantity_weighted(100, [1.0, 3.0]) == [25, 75]

    def test_sum_is_exact_despite_rounding(self):
        weights = [0.7, 1.3, 2.9, 0.1, 5.0]
        chunks = split_quantity_weighted(1000, weights)
        assert sum(chunks) == 1000

    def test_zero_weight_profile_falls_back_to_even_split(self):
        assert split_quantity_weighted(10, [0.0, 0.0]) == [5, 5]

    def test_thin_buckets_receive_zero_rather_than_stealing_shares(self):
        chunks = split_quantity_weighted(3, [1, 5, 2, 9])
        assert sum(chunks) == 3
        # The two heaviest buckets absorb the shares; the thin ones get nothing.
        assert chunks[3] > 0 and chunks[1] > 0

    def test_ties_are_broken_deterministically(self):
        first = split_quantity_weighted(7, [1, 1, 1])
        second = split_quantity_weighted(7, [1, 1, 1])
        assert first == second == [3, 2, 2]

    def test_rejects_negative_weights(self):
        with pytest.raises(ValueError):
            split_quantity_weighted(10, [1.0, -1.0])

    def test_rejects_empty_weights(self):
        with pytest.raises(ValueError):
            split_quantity_weighted(10, [])


class TestBuildTwapSchedule:
    def test_slices_are_evenly_spaced_within_the_window(self):
        schedule = build_twap_schedule(100, 4, START, timedelta(minutes=20))
        assert [s.scheduled_at for s in schedule] == [
            datetime(2026, 8, 21, 10, 0),
            datetime(2026, 8, 21, 10, 5),
            datetime(2026, 8, 21, 10, 10),
            datetime(2026, 8, 21, 10, 15),
        ]

    def test_last_slice_lands_inside_the_duration(self):
        duration = timedelta(minutes=30)
        schedule = build_twap_schedule(60, 6, START, duration)
        assert schedule[-1].scheduled_at < START + duration

    def test_quantities_sum_to_total(self):
        schedule = build_twap_schedule(97, 7, START, timedelta(minutes=35))
        assert sum(s.quantity for s in schedule) == 97

    def test_slice_count_capped_by_share_count(self):
        schedule = build_twap_schedule(3, 10, START, timedelta(minutes=10))
        assert len(schedule) == 3
        assert all(s.quantity == 1 for s in schedule)

    def test_indices_are_sequential(self):
        schedule = build_twap_schedule(50, 5, START, timedelta(minutes=25))
        assert [s.index for s in schedule] == [0, 1, 2, 3, 4]

    def test_rejects_non_positive_duration(self):
        with pytest.raises(ValueError):
            build_twap_schedule(10, 2, START, timedelta(0))


class TestBuildVwapSchedule:
    def test_quantities_follow_weights(self):
        schedule = build_vwap_schedule(
            100, 2, START, timedelta(minutes=20), weights=[1.0, 3.0]
        )
        assert [s.quantity for s in schedule] == [25, 75]

    def test_timing_grid_matches_twap(self):
        vwap = build_vwap_schedule(
            100, 4, START, timedelta(minutes=20), weights=[1, 1, 1, 1]
        )
        twap = build_twap_schedule(100, 4, START, timedelta(minutes=20))
        assert [s.scheduled_at for s in vwap] == [s.scheduled_at for s in twap]

    def test_empty_buckets_are_dropped_and_reindexed(self):
        schedule = build_vwap_schedule(
            100, 4, START, timedelta(minutes=20), weights=[1, 0, 3, 0]
        )
        assert len(schedule) == 2
        assert [s.index for s in schedule] == [0, 1]
        assert [s.scheduled_at.minute for s in schedule] == [0, 10]
        assert sum(s.quantity for s in schedule) == 100

    def test_missing_weights_degrade_to_even_split(self):
        schedule = build_vwap_schedule(100, 4, START, timedelta(minutes=20))
        assert [s.quantity for s in schedule] == [25, 25, 25, 25]

    def test_weight_length_mismatch_is_rejected(self):
        with pytest.raises(ValueError, match="weights length"):
            build_vwap_schedule(100, 4, START, timedelta(minutes=20), weights=[1, 2])

    def test_normalized_weights_sum_to_one(self):
        schedule = build_vwap_schedule(
            1000, 3, START, timedelta(minutes=30), weights=[2, 3, 5]
        )
        assert sum(s.weight for s in schedule) == pytest.approx(1.0)

    @pytest.mark.parametrize(
        "qty,slices,duration",
        [(0, 3, timedelta(minutes=10)), (10, 0, timedelta(minutes=10)), (10, 3, timedelta(0))],
    )
    def test_rejects_out_of_range_arguments(self, qty, slices, duration):
        with pytest.raises(ValueError):
            build_vwap_schedule(qty, slices, START, duration, weights=None)


def test_order_slice_is_immutable():
    slice_ = OrderSlice(index=0, scheduled_at=START, quantity=10)
    with pytest.raises(Exception):
        slice_.quantity = 20


class TestWeightedSplitEdges:
    def test_rejects_non_positive_total(self):
        with pytest.raises(ValueError, match="total must be positive"):
            split_quantity_weighted(0, [1.0, 2.0])

    def test_all_zero_weights_normalise_to_an_even_share(self):
        # A flat profile has no information; every slice carries the same weight.
        schedule = build_vwap_schedule(
            100, 4, START, timedelta(minutes=20), weights=[0.0, 0.0, 0.0, 0.0]
        )
        assert [s.quantity for s in schedule] == [25, 25, 25, 25]
        assert [s.weight for s in schedule] == [0.25] * 4
