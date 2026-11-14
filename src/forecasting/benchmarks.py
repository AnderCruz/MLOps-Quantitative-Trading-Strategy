"""Univariate baselines for return, price and volatility forecasts."""

from __future__ import annotations

import numpy as np
import pandas as pd


def constant_return_forecast(history: pd.Series, *, statistic: str = "zero") -> float:
    """Forecast a constant future simple return from training labels only."""
    if statistic not in {"zero", "mean", "median"}:
        raise ValueError("statistic must be 'zero', 'mean' or 'median'.")
    if statistic == "zero":
        return 0.0
    values = pd.to_numeric(history, errors="coerce").dropna().to_numpy(dtype=float)
    if values.size == 0:
        raise ValueError("history must contain at least one finite return.")
    if not np.isfinite(values).all():
        raise ValueError("history must contain only finite returns.")
    return float(np.mean(values) if statistic == "mean" else np.median(values))


def no_change_price_forecast(last_price: float) -> float:
    """Return the last known price as a no-change price forecast."""
    if not np.isfinite(last_price) or last_price <= 0:
        raise ValueError("last_price must be finite and positive.")
    return float(last_price)


def moving_average_return_forecast(history: pd.Series, *, window: int) -> float:
    """Use the mean of the most recent training returns as a simple forecast."""
    if not isinstance(window, int) or isinstance(window, bool) or window < 1:
        raise ValueError("window must be a positive integer.")
    values = pd.to_numeric(history, errors="coerce").dropna().to_numpy(dtype=float)
    if values.size == 0 or not np.isfinite(values).all():
        raise ValueError("history must contain finite returns.")
    return float(np.mean(values[-window:]))


def autoregressive_one_step_forecast(history: pd.Series) -> float:
    """Fit an intercept and AR(1) by least squares to a training return series."""
    values = pd.to_numeric(history, errors="coerce").dropna().to_numpy(dtype=float)
    if values.size < 3 or not np.isfinite(values).all():
        raise ValueError("AR(1) history must contain at least three finite returns.")
    design = np.column_stack((np.ones(values.size - 1), values[:-1]))
    coefficients, *_ = np.linalg.lstsq(design, values[1:], rcond=None)
    return float(coefficients[0] + coefficients[1] * values[-1])


def fit_ar1_parameters(history: pd.Series) -> tuple[float, float]:
    """Estimate AR(1) intercept and lag coefficient from a training series."""
    values = pd.to_numeric(history, errors="coerce").dropna().to_numpy(dtype=float)
    if values.size < 3 or not np.isfinite(values).all():
        raise ValueError("AR(1) history must contain at least three finite returns.")
    design = np.column_stack((np.ones(values.size - 1), values[:-1]))
    intercept, coefficient = np.linalg.lstsq(design, values[1:], rcond=None)[0]
    return float(intercept), float(coefficient)


def autoregressive_horizon_return_forecast(
    log_return_history: pd.Series,
    *,
    horizon: int,
    parameters: tuple[float, float] | None = None,
) -> float:
    """Recursively forecast an h-row simple return with an AR(1) log-return model."""
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError("horizon must be a positive integer.")
    values = pd.to_numeric(log_return_history, errors="coerce").dropna().to_numpy(dtype=float)
    if values.size < 3 or not np.isfinite(values).all():
        raise ValueError("AR(1) history must contain at least three finite returns.")
    if parameters is None:
        intercept, coefficient = fit_ar1_parameters(pd.Series(values))
    else:
        intercept, coefficient = parameters
        if not np.isfinite(intercept) or not np.isfinite(coefficient):
            raise ValueError("AR(1) parameters must be finite.")
    previous = float(values[-1])
    cumulative_log_return = 0.0
    for _ in range(horizon):
        previous = float(intercept + coefficient * previous)
        cumulative_log_return += previous
    return float(np.expm1(cumulative_log_return))


def historical_volatility_forecast(
    history: pd.Series, *, window: int, horizon: int | None = None
) -> float:
    """Forecast cumulative h-step realised volatility from recent returns.

    ``window`` is the count of one-row log returns used to estimate volatility;
    ``horizon`` is the forecast horizon in acquired rows (defaults to ``window``).
    The result is scaled to the Phase 6 cumulative target and is not annualised.
    """
    if not isinstance(window, int) or isinstance(window, bool) or window < 1:
        raise ValueError("window must be a positive integer.")
    if horizon is None:
        horizon = window
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError("horizon must be a positive integer.")
    values = pd.to_numeric(history, errors="coerce").to_numpy(dtype=float)
    if values.size < window:
        raise ValueError("history must contain at least window acquired rows.")
    values = values[-window:]
    if not np.isfinite(values).all():
        raise ValueError("the most recent window must contain only finite returns.")
    one_step_volatility = float(np.std(values[-window:], ddof=1)) if window > 1 else abs(float(values[-1]))
    return one_step_volatility * np.sqrt(horizon)
