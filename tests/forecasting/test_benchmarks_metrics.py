import numpy as np
import pandas as pd
import pytest

from src.forecasting.benchmarks import (
    autoregressive_horizon_return_forecast,
    autoregressive_one_step_forecast,
    fit_ar1_parameters,
    constant_return_forecast,
    historical_volatility_forecast,
    moving_average_return_forecast,
    no_change_price_forecast,
)
from src.forecasting.metrics import brier_score, directional_metrics, regression_metrics
from src.forecasting.garch import fit_garch11, forecast_garch11_cumulative_volatility


def test_naive_return_and_price_benchmarks():
    history = pd.Series([0.1, -0.2, 0.3])
    assert constant_return_forecast(history) == 0
    assert constant_return_forecast(history, statistic="mean") == pytest.approx(0.2 / 3)
    assert constant_return_forecast(history, statistic="median") == pytest.approx(0.1)
    assert no_change_price_forecast(42) == 42
    assert moving_average_return_forecast(history, window=2) == pytest.approx(0.05)


def test_ar1_and_historical_volatility_are_finite_and_causal():
    returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
    forecast = autoregressive_one_step_forecast(returns)
    volatility = historical_volatility_forecast(returns, window=3, horizon=5)
    changed_future = pd.concat([returns, pd.Series([100.0])], ignore_index=True)
    assert np.isfinite(forecast)
    parameters = fit_ar1_parameters(returns)
    conditional_forecast = autoregressive_horizon_return_forecast(
        returns, horizon=2, parameters=parameters
    )
    assert np.isfinite(conditional_forecast)
    assert volatility == pytest.approx(
        historical_volatility_forecast(changed_future.iloc[:5], window=3, horizon=5)
    )


def test_garch11_fit_is_stationary_and_forecasts_positive_cumulative_volatility():
    rng = np.random.default_rng(41)
    returns = pd.Series(rng.normal(0.0, 0.01, 300))
    fitted = fit_garch11(returns)
    assert fitted["omega"] > 0
    assert fitted["alpha"] >= 0
    assert fitted["beta"] >= 0
    assert fitted["alpha"] + fitted["beta"] < 1
    assert forecast_garch11_cumulative_volatility(fitted, horizon=10) > 0


def test_garch11_retains_gaps_and_rejects_invalid_forecast_constraints():
    rng = np.random.default_rng(42)
    gapped = pd.Series(rng.normal(0.0, 0.01, 250))
    gapped.iloc[100] = np.nan
    assert fit_garch11(gapped)["conditional_variance_last"] > 0
    with pytest.raises(ValueError, match="finite acquired"):
        fit_garch11(pd.Series([0.01, np.nan] * 60))
    with pytest.raises(ValueError, match="stationarity"):
        forecast_garch11_cumulative_volatility(
            {"omega": 0.1, "alpha": 0.7, "beta": 0.4,
             "conditional_variance_last": 0.2, "last_log_return": 0.1},
            horizon=5,
        )


def test_regression_directional_and_probability_metrics():
    assert regression_metrics([1, 2, 3], [1, 1, 4])["mae"] == pytest.approx(2 / 3)
    results = directional_metrics([-1, 1, 1, -1], [-0.1, 0.1, -0.2, 0.3])
    assert results["directional_accuracy"] == pytest.approx(0.5)
    assert results["confusion_matrix_negative_positive"] == [[1, 1], [1, 1]]
    assert brier_score([0, 1], [0.2, 0.8]) == pytest.approx(0.04)


@pytest.mark.parametrize(
    "call",
    [
        lambda: constant_return_forecast(pd.Series([1]), statistic="mode"),
        lambda: no_change_price_forecast(0),
        lambda: moving_average_return_forecast(pd.Series([1]), window=0),
        lambda: autoregressive_one_step_forecast(pd.Series([1, 2])),
        lambda: historical_volatility_forecast(pd.Series([1]), window=2),
        lambda: regression_metrics([1, 2], [1]),
        lambda: brier_score([2], [0.5]),
    ],
)
def test_invalid_benchmark_and_metric_inputs_raise(call):
    with pytest.raises(ValueError):
        call()
