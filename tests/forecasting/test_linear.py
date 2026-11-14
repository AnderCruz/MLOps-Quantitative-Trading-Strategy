import numpy as np
import pandas as pd
import pytest

from src.forecasting.linear import fit_ols_forecast


def test_ols_scales_from_training_rows_and_predicts_in_requested_index():
    train_x = pd.DataFrame({"x": [0.0, 1.0, 2.0, 3.0]})
    train_y = pd.Series([1.0, 3.0, 5.0, 7.0])
    forecast_x = pd.DataFrame({"x": [4.0]}, index=["next"])
    result = fit_ols_forecast(train_x, train_y, forecast_x)
    assert result.loc["next"] == pytest.approx(9.0)


def test_future_forecast_rows_do_not_change_fitted_parameters_or_prior_predictions():
    train_x = pd.DataFrame({"x": [0.0, 1.0, 2.0, 3.0]})
    train_y = pd.Series([1.0, 3.0, 5.0, 7.0])
    first = pd.DataFrame({"x": [4.0]}, index=[4])
    extended = pd.DataFrame({"x": [4.0, 1000.0]}, index=[4, 5])
    expected = fit_ols_forecast(train_x, train_y, first)
    observed = fit_ols_forecast(train_x, train_y, extended).loc[[4]]
    pd.testing.assert_series_equal(expected, observed)


def test_ols_rejects_incomplete_or_misaligned_inputs():
    with pytest.raises(ValueError, match="finite"):
        fit_ols_forecast(
            pd.DataFrame({"x": [1.0, np.nan]}),
            pd.Series([1.0, 2.0]),
            pd.DataFrame({"x": [3.0]}),
        )
    with pytest.raises(ValueError, match="columns"):
        fit_ols_forecast(
            pd.DataFrame({"x": [1.0]}), pd.Series([1.0]), pd.DataFrame({"y": [3.0]})
        )
