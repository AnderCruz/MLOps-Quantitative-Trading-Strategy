"""Past-only financial feature calculations for daily market observations."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


DEFAULT_LOOKBACKS = (5, 10, 20, 50, 100)


def _validate_series(values: pd.Series, name: str, *, positive: bool = False) -> pd.Series:
    if not isinstance(values, pd.Series):
        raise TypeError(f"{name} must be a pandas Series.")
    if not values.index.is_monotonic_increasing:
        raise ValueError(f"{name} index must be chronological; input is not sorted.")
    if values.index.has_duplicates:
        raise ValueError(f"{name} index must not contain duplicate observations.")
    numeric = pd.to_numeric(values, errors="raise").astype("float64")
    observed = numeric.dropna()
    if not np.isfinite(observed.to_numpy()).all():
        raise ValueError(f"{name} must not contain infinite values.")
    if positive and (observed <= 0).any():
        raise ValueError(f"{name} must be positive wherever an observation is present.")
    return numeric


def _validate_lookbacks(lookbacks: Sequence[int]) -> tuple[int, ...]:
    windows = tuple(lookbacks)
    if not windows:
        raise ValueError("At least one lookback window is required.")
    if any(not isinstance(window, int) or isinstance(window, bool) or window < 1 for window in windows):
        raise ValueError("Lookback windows must be positive integers.")
    if len(set(windows)) != len(windows):
        raise ValueError("Lookback windows must be unique.")
    return windows


def simple_returns(prices: pd.Series) -> pd.Series:
    """Calculate one-observation simple returns without filling missing data."""
    prices = _validate_series(prices, "prices", positive=True)
    return prices.pct_change(fill_method=None).rename("simple_return_1")


def log_returns(prices: pd.Series) -> pd.Series:
    """Calculate one-observation log returns without filling missing data."""
    prices = _validate_series(prices, "prices", positive=True)
    return np.log(prices).diff().rename("log_return_1")


def build_financial_features(
    market_data: pd.DataFrame,
    *,
    price_column: str = "Close",
    volume_column: str = "Volume",
    lookbacks: Sequence[int] = DEFAULT_LOOKBACKS,
) -> pd.DataFrame:
    """Build past-only, close-of-session features from one asset's daily data.

    Rolling features require a complete window. Missing source observations are
    preserved; no interpolation, forward fill, or currency conversion occurs.
    The first observation without a prior price has missing return features.
    """
    if not isinstance(market_data, pd.DataFrame):
        raise TypeError("market_data must be a pandas DataFrame.")
    if not market_data.index.is_monotonic_increasing:
        raise ValueError("market_data index must be chronological; input is not sorted.")
    if market_data.index.has_duplicates:
        raise ValueError("market_data index must not contain duplicate observations.")
    if price_column not in market_data:
        raise ValueError(f"Missing required price column: {price_column}")

    windows = _validate_lookbacks(lookbacks)
    prices = _validate_series(market_data[price_column], price_column, positive=True)
    returns = simple_returns(prices)
    log_return = log_returns(prices)
    features = pd.DataFrame(index=market_data.index)
    features["simple_return_1"] = returns
    features["log_return_1"] = log_return

    for window in windows:
        rolling_mean = prices.rolling(window=window, min_periods=window).mean()
        features[f"momentum_{window}"] = prices.pct_change(
            periods=window, fill_method=None
        )
        features[f"sma_{window}"] = rolling_mean
        features[f"ema_{window}"] = prices.ewm(
            span=window, adjust=False, min_periods=window
        ).mean()
        features[f"price_to_sma_{window}"] = prices / rolling_mean - 1.0
        features[f"return_volatility_{window}"] = returns.rolling(
            window=window, min_periods=window
        ).std(ddof=1)
        features[f"realised_volatility_{window}"] = np.sqrt(
            log_return.pow(2).rolling(window=window, min_periods=window).sum()
        )
        downside_returns = returns.clip(upper=0.0)
        features[f"downside_volatility_{window}"] = np.sqrt(
            downside_returns.pow(2).rolling(window=window, min_periods=window).mean()
        )
        rolling_peak = prices.rolling(window=window, min_periods=window).max()
        features[f"drawdown_{window}"] = prices / rolling_peak - 1.0

    if volume_column in market_data:
        volume = _validate_series(market_data[volume_column], volume_column)
        if (volume.dropna() < 0).any():
            raise ValueError("volume must not be negative.")
        prior_volume = volume.shift(1)
        features["volume_change_1"] = (
            volume / prior_volume.where(prior_volume > 0) - 1.0
        )
        for window in windows:
            prior_average = volume.shift(1).rolling(
                window=window, min_periods=window
            ).mean()
            features[f"relative_volume_{window}"] = (
                volume / prior_average.where(prior_average > 0)
            )

    return features
