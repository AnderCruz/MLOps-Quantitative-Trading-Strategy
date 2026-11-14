"""Forward target definitions for later forecasting research."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


DEFAULT_HORIZONS = (5, 10, 20)


def _validate_horizons(horizons: Sequence[int]) -> tuple[int, ...]:
    values = tuple(horizons)
    if not values:
        raise ValueError("At least one forecast horizon is required.")
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 1 for value in values):
        raise ValueError("Forecast horizons must be positive integers.")
    if len(set(values)) != len(values):
        raise ValueError("Forecast horizons must be unique.")
    return values


def _validate_thresholds(thresholds: Sequence[float]) -> tuple[float, ...]:
    values = tuple(thresholds)
    if not values:
        raise ValueError("At least one neutral threshold is required.")
    if any(not isinstance(value, (int, float)) or isinstance(value, bool) for value in values):
        raise ValueError("Neutral thresholds must be numeric fractions.")
    if any(not np.isfinite(value) or value < 0 or value >= 1 for value in values):
        raise ValueError("Neutral thresholds must be finite fractions in [0, 1).")
    if len(set(values)) != len(values):
        raise ValueError("Neutral thresholds must be unique.")
    return values


def build_forward_targets(
    market_data: pd.DataFrame,
    *,
    price_column: str = "Close",
    horizons: Sequence[int] = DEFAULT_HORIZONS,
    neutral_thresholds: Sequence[float] = (0.0,),
) -> pd.DataFrame:
    """Build forward simple-return, direction and realised-volatility targets.

    Rows are indexed by forecast-origin session t. Return targets span Close[t]
    to Close[t+h]. Future realised volatility uses the h one-session log returns
    from t+1 through t+h. A missing observation anywhere in the horizon makes
    that target missing. The negative shifts are intentional target construction;
    outputs must never be joined to explanatory features as input columns.
    """
    if not isinstance(market_data, pd.DataFrame):
        raise TypeError("market_data must be a pandas DataFrame.")
    if not market_data.index.is_monotonic_increasing:
        raise ValueError("market_data index must be chronological.")
    if market_data.index.has_duplicates:
        raise ValueError("market_data index must not contain duplicate observations.")
    if price_column not in market_data:
        raise ValueError(f"Missing required price column: {price_column}")

    windows = _validate_horizons(horizons)
    thresholds = _validate_thresholds(neutral_thresholds)
    prices = pd.to_numeric(market_data[price_column], errors="raise").astype("float64")
    observed = prices.dropna()
    if not np.isfinite(observed.to_numpy()).all() or (observed <= 0).any():
        raise ValueError("Prices must be finite and positive wherever observed.")

    log_returns = np.log(prices).diff()
    targets = pd.DataFrame(index=market_data.index)
    for horizon in windows:
        future_prices = pd.concat(
            [prices.shift(-step).rename(step) for step in range(horizon + 1)],
            axis=1,
        )
        complete_price_path = future_prices.notna().all(axis=1)
        forward_return = (prices.shift(-horizon) / prices - 1.0).where(complete_price_path)
        targets[f"forward_return_{horizon}"] = forward_return

        for threshold in thresholds:
            direction = pd.Series(pd.NA, index=prices.index, dtype="Int8")
            complete_return = forward_return.notna()
            direction.loc[complete_return & (forward_return > threshold)] = 1
            direction.loc[complete_return & (forward_return < -threshold)] = -1
            direction.loc[
                complete_return & (forward_return >= -threshold) & (forward_return <= threshold)
            ] = 0
            threshold_basis_points = int(round(threshold * 10_000))
            targets[f"direction_{horizon}_{threshold_basis_points}bp"] = direction

        future_log_returns = pd.concat(
            [log_returns.shift(-step).rename(step) for step in range(1, horizon + 1)],
            axis=1,
        )
        complete_return_path = future_log_returns.notna().all(axis=1)
        future_volatility = np.sqrt(
            future_log_returns.pow(2).sum(axis=1, min_count=horizon)
        ).where(complete_return_path)
        targets[f"forward_realised_volatility_{horizon}"] = future_volatility

    return targets
