import numpy as np
import pandas as pd
import pytest

from src.forecasting.ml_models import (
    build_regression_model,
    direction_walk_forward_predictions,
    regression_walk_forward_predictions,
    ridge_walk_forward_predictions,
)


def test_ridge_walk_forward_preserves_timeline_and_skips_incomplete_rows():
    index = pd.date_range("2024-01-01", periods=40, freq="B")
    x = pd.DataFrame({"feature": np.arange(40, dtype=float)}, index=index)
    y = pd.Series(np.linspace(-0.02, 0.03, 40), index=index)
    x.loc[index[21], "feature"] = np.nan
    y.loc[index[23]] = np.nan

    predictions = ridge_walk_forward_predictions(
        x,
        y,
        horizon=5,
        initial_train_size=20,
        validation_size=5,
        alpha=0.5,
    )

    assert index[20] in predictions.index
    assert index[21] not in predictions.index
    assert index[23] not in predictions.index
    assert predictions["fold"].min() == 1
    assert np.isfinite(predictions[["actual", "forecast"]].to_numpy()).all()


def test_ridge_walk_forward_requires_identical_chronological_indexes():
    x = pd.DataFrame({"feature": [1.0, 2.0, 3.0, 4.0, 5.0]}, index=[1, 2, 3, 4, 5])
    y = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0], index=[1, 2, 3, 4, 6])
    with pytest.raises(ValueError, match="indexes must be identical"):
        ridge_walk_forward_predictions(
            x,
            y,
            horizon=1,
            initial_train_size=3,
            validation_size=1,
        )


def test_random_forest_regression_and_direction_keep_fold_dates_and_classes():
    index = pd.date_range("2024-01-01", periods=90, freq="B")
    values = np.arange(90, dtype=float)
    x = pd.DataFrame({"feature": values, "cycle": np.sin(values)}, index=index)
    y = pd.Series(np.where(values % 3 == 0, 1, np.where(values % 3 == 1, 0, -1)), index=index)
    reg_y = pd.Series(values / 1000.0, index=index)
    options = {"horizon": 5, "initial_train_size": 45, "validation_size": 15}

    reg = regression_walk_forward_predictions(
        x,
        reg_y,
        model_factory=lambda: build_regression_model(
            "random_forest", parameters={"n_estimators": 8, "min_samples_leaf": 2}
        ),
        **options,
    )
    classification = direction_walk_forward_predictions(
        x,
        y,
        parameters={"n_estimators": 8, "min_samples_leaf": 2},
        **options,
    )
    assert reg.index.equals(classification.index)
    assert set(classification["forecast"].unique()).issubset({-1, 0, 1})
    assert np.allclose(
        classification[["probability_negative", "probability_neutral", "probability_positive"]].sum(axis=1),
        1.0,
    )


def test_one_class_training_fold_maps_missing_class_probabilities_to_zero():
    index = pd.date_range("2024-01-01", periods=50, freq="B")
    x = pd.DataFrame({"feature": np.arange(50, dtype=float)}, index=index)
    labels = np.array([-1] * 25 + [0, 1] * 12 + [-1])
    y = pd.Series(labels, index=index)
    fitted = []
    predictions = direction_walk_forward_predictions(
        x, y, horizon=5, initial_train_size=20, validation_size=10,
        parameters={"n_estimators": 8, "min_samples_leaf": 2},
        on_fit=lambda fold, model, train_x, train_y: fitted.append((fold, model, train_y.copy())),
    )
    first_fold = predictions.loc[predictions.fold == 1]
    assert fitted[0][0] == 1
    assert set(fitted[0][2].unique()) == {-1}
    assert (first_fold.probability_negative == 1.0).all()
    assert (first_fold.probability_neutral == 0.0).all()
    assert (first_fold.probability_positive == 0.0).all()


def test_each_walk_forward_fold_fits_a_fresh_ridge_estimator():
    index = pd.date_range("2024-01-01", periods=50, freq="B")
    x = pd.DataFrame({"feature": np.arange(50, dtype=float)}, index=index)
    y = pd.Series(np.arange(50, dtype=float) / 100.0, index=index)
    fitted = []
    predictions = regression_walk_forward_predictions(
        x, y,
        model_factory=lambda: build_regression_model("ridge", parameters={"alpha": 1.0}),
        horizon=3, initial_train_size=20, validation_size=5,
        on_fit=lambda fold, model, train_x, train_y: fitted.append(model),
    )
    assert len(predictions)
    assert len({id(model) for model in fitted}) == len(fitted)
