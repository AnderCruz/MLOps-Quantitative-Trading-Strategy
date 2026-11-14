import numpy as np
import pandas as pd
import pytest

from src.forecasting.ml_models import fit_ridge_model, predict_ridge


def test_ridge_pipeline_fits_scaler_on_training_rows_and_preserves_prediction_index():
    x_train = pd.DataFrame({"x": [0.0, 1.0, 2.0, 3.0]}, index=[1, 2, 3, 4])
    y_train = pd.Series([0.0, 0.1, 0.2, 0.3], index=x_train.index)
    x_forecast = pd.DataFrame({"x": [4.0, 5.0]}, index=["next", "later"])

    model = fit_ridge_model(x_train, y_train, alpha=0.1)
    prediction = predict_ridge(model, x_forecast)

    assert model.named_steps["scale"].mean_[0] == pytest.approx(1.5)
    assert prediction.index.tolist() == ["next", "later"]
    assert np.isfinite(prediction.to_numpy()).all()


def test_ridge_training_rejects_unaligned_indexes_and_non_finite_values():
    x_train = pd.DataFrame({"x": [1.0, np.nan]}, index=[0, 1])
    y_train = pd.Series([0.0, 1.0], index=[0, 1])
    with pytest.raises(ValueError, match="finite"):
        fit_ridge_model(x_train, y_train)

    clean_x = pd.DataFrame({"x": [1.0, 2.0]}, index=[0, 1])
    misaligned_y = pd.Series([0.0, 1.0], index=[1, 2])
    with pytest.raises(ValueError, match="identical indexes"):
        fit_ridge_model(clean_x, misaligned_y)


def test_ridge_rejects_invalid_alpha_and_forecast_schema():
    x_train = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
    y_train = pd.Series([0.1, 0.2, 0.3])
    with pytest.raises(ValueError, match="alpha"):
        fit_ridge_model(x_train, y_train, alpha=0.0)

    model = fit_ridge_model(x_train, y_train)
    with pytest.raises(ValueError, match="columns"):
        predict_ridge(model, pd.DataFrame({"other": [4.0]}))
