"""A compact Gaussian QMLE GARCH(1,1) benchmark for return volatility."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit


def fit_garch11(log_return_history: pd.Series) -> dict[str, float]:
    """Fit a stationary GARCH(1,1) by Gaussian quasi-maximum likelihood.

    Returns parameters and the final filtered conditional variance. Missing
    return rows stay in the acquired timeline and are integrated using their
    conditional expected squared return. Infinite values are rejected. The fit
    uses training data and enforces alpha + beta < 1.
    """
    values = pd.to_numeric(log_return_history, errors="coerce").to_numpy(dtype=float)
    finite = np.isfinite(values)
    if values.ndim != 1 or values.size < 100 or np.isinf(values).any() or finite.sum() < 100:
        raise ValueError("GARCH(1,1) requires at least 100 finite acquired returns.")
    variance = float(np.var(values[finite], ddof=1))
    if not np.isfinite(variance) or variance <= 0:
        raise ValueError("GARCH(1,1) requires positive return variance.")

    def unpack(parameters: np.ndarray) -> tuple[float, float, float]:
        omega = float(np.exp(np.clip(parameters[0], -40, 10)))
        alpha = float(0.999 * expit(parameters[1]))
        beta = float((0.999 - alpha) * expit(parameters[2]))
        return omega, alpha, beta

    def objective(parameters: np.ndarray) -> float:
        omega, alpha, beta = unpack(parameters)
        conditional = np.empty(values.size, dtype=float)
        conditional[0] = variance
        for position in range(1, values.size):
            previous_square = values[position - 1] ** 2 if finite[position - 1] else conditional[position - 1]
            conditional[position] = omega + alpha * previous_square + beta * conditional[position - 1]
        if not np.isfinite(conditional).all() or np.any(conditional <= 0):
            return 1e100
        return float(0.5 * np.sum(np.log(conditional[finite]) + values[finite] ** 2 / conditional[finite]))

    initial = np.array([np.log(variance * 0.05), -2.9, 2.2], dtype=float)
    fitted = minimize(objective, initial, method="L-BFGS-B", options={"maxiter": 2_000, "ftol": 1e-10})
    if not fitted.success or not np.isfinite(fitted.fun):
        raise RuntimeError(f"GARCH(1,1) QMLE failed: {fitted.message}")
    omega, alpha, beta = unpack(fitted.x)
    conditional_last = variance
    for position in range(1, values.size):
        previous_square = values[position - 1] ** 2 if finite[position - 1] else conditional_last
        conditional_last = omega + alpha * previous_square + beta * conditional_last
    return {
        "omega": omega,
        "alpha": alpha,
        "beta": beta,
        "conditional_variance_last": float(conditional_last),
        "last_log_return": float(values[-1]) if finite[-1] else 0.0,
        "last_return_squared": float(values[-1] ** 2) if finite[-1] else float(conditional_last),
    }


def forecast_garch11_cumulative_volatility(parameters: dict[str, float], *, horizon: int) -> float:
    """Forecast cumulative h-row realised volatility from a fitted GARCH model."""
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError("horizon must be a positive integer.")
    omega = float(parameters["omega"])
    alpha = float(parameters["alpha"])
    beta = float(parameters["beta"])
    variance = float(parameters["conditional_variance_last"])
    last_return_squared = float(parameters.get("last_return_squared", parameters["last_log_return"] ** 2))
    if not all(np.isfinite(value) for value in (omega, alpha, beta, variance, last_return_squared)):
        raise ValueError("GARCH parameters must be finite.")
    if omega <= 0 or alpha < 0 or beta < 0 or alpha + beta >= 1 or variance <= 0:
        raise ValueError("GARCH parameters must satisfy positivity and covariance-stationarity constraints.")
    expected_variation = 0.0
    for step in range(horizon):
        variance = omega + alpha * last_return_squared + beta * variance
        expected_variation += variance
        last_return_squared = variance
    return float(np.sqrt(expected_variation))


def update_garch11_state(parameters: dict[str, float], observed_log_returns: pd.Series) -> dict[str, float]:
    """Advance a fitted GARCH filter through newly observed acquired rows."""
    updated = dict(parameters)
    omega = float(updated["omega"])
    alpha = float(updated["alpha"])
    beta = float(updated["beta"])
    variance = float(updated["conditional_variance_last"])
    last_return_squared = float(updated.get("last_return_squared", updated["last_log_return"] ** 2))
    values = pd.to_numeric(observed_log_returns, errors="coerce").to_numpy(dtype=float)
    if np.isinf(values).any():
        raise ValueError("Observed returns must not contain infinite values.")
    for value in values:
        variance = omega + alpha * last_return_squared + beta * variance
        last_return_squared = float(value**2) if np.isfinite(value) else variance
    updated["conditional_variance_last"] = variance
    updated["last_return_squared"] = last_return_squared
    return updated
