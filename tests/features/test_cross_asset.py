"""Tests for exact-date cross-asset alignment and PIT controls."""

import pandas as pd
import pytest

from src.features.cross_asset import (
    build_cross_asset_return_panel,
    point_in_time_eligibility,
)


def test_cross_asset_returns_use_exact_dates_and_keep_calendar_gaps():
    target = pd.Series([100.0, 110.0, 121.0], index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-04"]))
    peer = pd.Series([50.0, 55.0], index=pd.to_datetime(["2024-01-01", "2024-01-03"]))

    panel = build_cross_asset_return_panel({"target": target, "peer": peer}, lookbacks=(1,))

    assert list(panel.index) == list(pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]))
    assert pd.isna(panel.loc["2024-01-02", "peer__return_1"])
    assert pd.isna(panel.loc["2024-01-03", "target__return_1"])
    assert panel.loc["2024-01-02", "target__return_1"] == pytest.approx(0.1)


def test_cross_asset_return_lookback_does_not_fill_missing_values():
    price = pd.Series([10.0, None, 12.0, 13.0])
    panel = build_cross_asset_return_panel({"asset": price}, lookbacks=(1, 2))

    assert panel.loc[3, "asset__return_1"] == pytest.approx(13.0 / 12.0 - 1.0)
    assert pd.isna(panel.loc[3, "asset__return_2"])


def test_point_in_time_check_requires_both_times_before_decision():
    observations = pd.DataFrame({
        "availability_timestamp": pd.to_datetime(["2024-01-02T09:00:00Z", "2024-01-03T09:00:00Z"]),
        "acquisition_timestamp": pd.to_datetime(["2024-01-02T09:05:00Z", "2024-01-02T09:05:00Z"]),
    })
    decisions = pd.to_datetime(["2024-01-02T10:00:00Z", "2024-01-02T10:00:00Z"])

    assert point_in_time_eligibility(observations, decisions).tolist() == [True, False]


def test_point_in_time_check_fails_closed_for_missing_or_naive_timestamps():
    observations = pd.DataFrame({
        "availability_timestamp": [pd.NaT, pd.Timestamp("2024-01-02 09:00")],
        "acquisition_timestamp": [pd.Timestamp("2024-01-02T09:00:00Z"), pd.Timestamp("2024-01-02T09:00:00Z")],
    })
    decisions = [pd.Timestamp("2024-01-02T10:00:00Z")] * 2

    assert point_in_time_eligibility(observations, decisions).tolist() == [False, False]


def test_point_in_time_check_rejects_missing_schema_or_mismatched_decisions():
    with pytest.raises(ValueError, match="Missing PIT timestamp columns"):
        point_in_time_eligibility(pd.DataFrame({"value": [1]}), [pd.Timestamp("2024-01-02T10:00:00Z")])
    complete = pd.DataFrame({"availability_timestamp": [pd.Timestamp("2024-01-02T09:00:00Z")], "acquisition_timestamp": [pd.Timestamp("2024-01-02T09:00:00Z")]})
    with pytest.raises(ValueError, match="one decision timestamp"):
        point_in_time_eligibility(complete, [])
