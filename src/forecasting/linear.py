"""Small ordinary least-squares interface for pre-specified feature groups."""

from __future__ import annotations

import numpy as np
import pandas as pd


def fit_ols_forecast(x_train: pd.DataFrame, y_train: pd.Series, x_forecast: pd.DataFrame) -> pd.Series:
    """Fit OLS with training-only scaling and predict complete forecast rows.

    The function deliberately performs no feature selection or imputation.
    Callers must define a small feature set before evaluation and provide only
    complete rows. Rank deficiency is handled by least squares and reported by
    callers as a limitation when interpreting coefficients.
    """
    if not isinstance(x_train, pd.DataFrame) or not isinstance(x_forecast, pd.DataFrame):
        raise TypeError("x_train and x_forecast must be pandas DataFrames.")
    if not isinstance(y_train, pd.Series):
        raise TypeError("y_train must be a pandas Series.")
    if x_train.empty or x_train.shape[1] == 0:
        raise ValueError("x_train must contain at least one row and feature.")
    if list(x_train.columns) != list(x_forecast.columns):
        raise ValueError("Training and forecast feature columns must match in order.")
    if len(x_train) != len(y_train) or x_forecast.empty:
        raise ValueError("Training features/target must align and forecast rows must be non-empty.")
    train_x = x_train.to_numpy(dtype=float)
    forecast_x = x_forecast.to_numpy(dtype=float)
    train_y = y_train.to_numpy(dtype=float)
    if not (np.isfinite(train_x).all() and np.isfinite(forecast_x).all() and np.isfinite(train_y).all()):
        raise ValueError("OLS inputs must be complete and finite; imputation is not performed.")

    means = train_x.mean(axis=0)
    scales = train_x.std(axis=0, ddof=0)
    scales[scales == 0] = 1.0
    scaled_train = (train_x - means) / scales
    scaled_forecast = (forecast_x - means) / scales
    design = np.column_stack((np.ones(len(x_train)), scaled_train))
    forecast_design = np.column_stack((np.ones(len(x_forecast)), scaled_forecast))
    coefficients, *_ = np.linalg.lstsq(design, train_y, rcond=None)
    return pd.Series(forecast_design @ coefficients, index=x_forecast.index, name="forecast")
