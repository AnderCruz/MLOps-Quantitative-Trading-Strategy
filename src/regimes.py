"""Interpretable, past-only market regime indicators."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_regime_indicators(
    market_data: pd.DataFrame,
    *,
    price_column: str = "Close",
    volatility_window: int = 20,
    threshold_window: int = 252,
    volatility_quantiles: tuple[float, float] = (0.33, 0.67),
    trend_windows: tuple[int, int] = (50, 200),
) -> pd.DataFrame:
    """Return close-of-session trend and relative-volatility states.

    Volatility thresholds use only the prior ``threshold_window`` completed
    volatility observations. Every output at t uses price information no later
    than t; thresholds are lagged by one observation. Missing data are kept.
    """
    if not isinstance(market_data, pd.DataFrame):
        raise TypeError("market_data must be a pandas DataFrame.")
    if not market_data.index.is_monotonic_increasing:
        raise ValueError("market_data index must be chronological.")
    if market_data.index.has_duplicates:
        raise ValueError("market_data index must not contain duplicate observations.")
    if price_column not in market_data:
        raise ValueError(f"Missing required price column: {price_column}")
    for name, value in (("volatility_window", volatility_window), ("threshold_window", threshold_window)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 2:
            raise ValueError(f"{name} must be an integer of at least 2.")
    if (
        len(trend_windows) != 2
        or any(not isinstance(value, int) or isinstance(value, bool) or value < 2 for value in trend_windows)
        or trend_windows[0] >= trend_windows[1]
    ):
        raise ValueError("trend_windows must contain increasing integers of at least 2.")
    if (
        len(volatility_quantiles) != 2
        or not 0 < volatility_quantiles[0] < volatility_quantiles[1] < 1
    ):
        raise ValueError("volatility_quantiles must be two increasing values between 0 and 1.")

    prices = pd.to_numeric(market_data[price_column], errors="raise").astype("float64")
    observed = prices.dropna()
    if not np.isfinite(observed.to_numpy()).all() or (observed <= 0).any():
        raise ValueError("Prices must be finite and positive wherever observed.")

    log_returns = np.log(prices).diff()
    realised_volatility = np.sqrt(
        log_returns.pow(2).rolling(
            window=volatility_window,
            min_periods=volatility_window,
        ).sum()
    )

    prior_volatility = realised_volatility.shift(1).rolling(
        window=threshold_window,
        min_periods=threshold_window,
    )
    lower_threshold = prior_volatility.quantile(volatility_quantiles[0])
    upper_threshold = prior_volatility.quantile(volatility_quantiles[1])

    volatility_regime = pd.Series(pd.NA, index=prices.index, dtype="string")
    eligible = realised_volatility.notna() & lower_threshold.notna() & upper_threshold.notna()
    volatility_regime.loc[eligible & (realised_volatility <= lower_threshold)] = "low_volatility"
    volatility_regime.loc[eligible & (realised_volatility > upper_threshold)] = "high_volatility"
    middle = eligible & (realised_volatility > lower_threshold) & (realised_volatility <= upper_threshold)
    volatility_regime.loc[middle] = "typical_volatility"

    short_window, long_window = trend_windows
    short_average = prices.rolling(short_window, min_periods=short_window).mean()
    long_average = prices.rolling(long_window, min_periods=long_window).mean()
    trend_regime = pd.Series(pd.NA, index=prices.index, dtype="string")
    trend_eligible = prices.notna() & short_average.notna() & long_average.notna()
    uptrend = trend_eligible & (prices > short_average) & (short_average > long_average)
    downtrend = trend_eligible & (prices < short_average) & (short_average < long_average)
    trend_regime.loc[uptrend] = "uptrend"
    trend_regime.loc[downtrend] = "downtrend"
    trend_regime.loc[trend_eligible & ~uptrend & ~downtrend] = "mixed_trend"

    return pd.DataFrame(
        {
            f"realised_volatility_{volatility_window}": realised_volatility,
            "volatility_threshold_low": lower_threshold,
            "volatility_threshold_high": upper_threshold,
            "volatility_regime": volatility_regime,
            f"sma_{short_window}": short_average,
            f"sma_{long_window}": long_average,
            "trend_regime": trend_regime,
        },
        index=market_data.index,
    )
