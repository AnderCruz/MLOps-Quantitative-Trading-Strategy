"""Cross-asset return alignment and strict point-in-time checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd


def build_cross_asset_return_panel(
    asset_prices: Mapping[str, pd.Series],
    *,
    lookbacks: Sequence[int] = (1, 5, 20),
) -> pd.DataFrame:
    """Calculate return features and align them on the union of exact dates.

    No calendar is synthesised and no value is forward-filled. Dates absent
    from an instrument remain missing in that instrument's columns.
    """
    if not asset_prices:
        raise ValueError("At least one asset price series is required.")
    windows = tuple(lookbacks)
    if not windows or any(
        not isinstance(window, int) or isinstance(window, bool) or window < 1
        for window in windows
    ):
        raise ValueError("Lookback windows must be positive integers.")
    if len(set(windows)) != len(windows):
        raise ValueError("Lookback windows must be unique.")

    features: dict[str, pd.Series] = {}
    for asset, prices in asset_prices.items():
        if not isinstance(asset, str) or not asset.strip():
            raise ValueError("Asset identifiers must be non-empty strings.")
        if not isinstance(prices, pd.Series):
            raise TypeError(f"Prices for {asset} must be a pandas Series.")
        if not prices.index.is_monotonic_increasing:
            raise ValueError(f"Dates for {asset} must be chronological.")
        if prices.index.has_duplicates:
            raise ValueError(f"Dates for {asset} must be unique.")
        numeric = pd.to_numeric(prices, errors="raise").astype("float64")
        observed = numeric.dropna()
        if not np.isfinite(observed.to_numpy()).all() or (observed <= 0).any():
            raise ValueError(f"Prices for {asset} must be finite and positive when present.")

        for window in windows:
            returns = numeric.pct_change(periods=window, fill_method=None)
            features[f"{asset}__return_{window}"] = returns

    # Outer exact-index alignment keeps non-overlapping sessions visible as NaN.
    return pd.concat(features, axis=1, join="outer", sort=False).sort_index()


def point_in_time_eligibility(
    observations: pd.DataFrame,
    decision_timestamps: Sequence[object],
    *,
    availability_column: str = "availability_timestamp",
    acquisition_column: str = "acquisition_timestamp",
) -> pd.Series:
    """Return strict row eligibility using documented availability and acquisition times.

    Missing, unparseable or timezone-naive timestamps fail closed. This check
    does not establish that a source's availability policy is itself valid.
    """
    required = {availability_column, acquisition_column}
    absent = required.difference(observations.columns)
    if absent:
        raise ValueError(f"Missing PIT timestamp columns: {sorted(absent)}")
    if len(observations) != len(decision_timestamps):
        raise ValueError("Each observation must have one decision timestamp.")

    eligible: list[bool] = []
    for availability, acquisition, decision in zip(
        observations[availability_column],
        observations[acquisition_column],
        decision_timestamps,
    ):
        timestamps = (availability, acquisition, decision)
        if any(pd.isna(value) for value in timestamps):
            eligible.append(False)
            continue
        try:
            parsed = tuple(pd.Timestamp(value) for value in timestamps)
        except (TypeError, ValueError, OverflowError):
            eligible.append(False)
            continue
        if any(timestamp.tzinfo is None for timestamp in parsed):
            eligible.append(False)
            continue
        available_at, acquired_at, decision_at = (timestamp.tz_convert("UTC") for timestamp in parsed)
        eligible.append(available_at <= decision_at and acquired_at <= decision_at)

    return pd.Series(eligible, index=observations.index, name="pit_eligible", dtype=bool)
