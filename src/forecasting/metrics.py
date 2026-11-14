"""Forecast metrics implemented without a new runtime dependency."""

from __future__ import annotations

import numpy as np


def regression_metrics(actual, forecast) -> dict[str, float]:
    """Return MAE, MSE, RMSE, bias and sample count for finite pairs."""
    y, prediction = _paired(actual, forecast)
    error = prediction - y
    return {
        "mae": float(np.mean(np.abs(error))),
        "mse": float(np.mean(error**2)),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "forecast_bias": float(np.mean(error)),
        "n_observations": int(y.size),
    }


def directional_metrics(actual, forecast) -> dict[str, float | int | list[list[int]]]:
    """Return sign accuracy and binary positive-class metrics with confusion counts."""
    y, prediction = _paired(actual, forecast)
    actual_sign = np.sign(y)
    forecast_sign = np.sign(prediction)
    tp = int(np.sum((actual_sign > 0) & (forecast_sign > 0)))
    tn = int(np.sum((actual_sign <= 0) & (forecast_sign <= 0)))
    fp = int(np.sum((actual_sign <= 0) & (forecast_sign > 0)))
    fn = int(np.sum((actual_sign > 0) & (forecast_sign <= 0)))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "directional_accuracy": float(np.mean(actual_sign == forecast_sign)),
        "precision_positive": precision,
        "recall_positive": recall,
        "f1_positive": f1,
        "confusion_matrix_negative_positive": [[tn, fp], [fn, tp]],
        "n_observations": int(y.size),
    }


def brier_score(actual_binary, probability) -> float:
    """Return the Brier score for binary outcomes and probabilities in [0, 1]."""
    y, p = _paired(actual_binary, probability)
    if np.any(~np.isin(y, [0, 1])) or np.any((p < 0) | (p > 1)):
        raise ValueError("Brier inputs require binary outcomes and probabilities in [0, 1].")
    return float(np.mean((p - y) ** 2))


def _paired(actual, forecast) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(actual, dtype=float)
    prediction = np.asarray(forecast, dtype=float)
    if y.shape != prediction.shape or y.ndim != 1:
        raise ValueError("actual and forecast must be one-dimensional arrays of equal length.")
    valid = np.isfinite(y) & np.isfinite(prediction)
    if not valid.any():
        raise ValueError("At least one finite actual/forecast pair is required.")
    return y[valid], prediction[valid]
