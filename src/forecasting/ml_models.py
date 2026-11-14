"""Training-only preprocessing and traditional ML model interfaces."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from src.forecasting.validation import expanding_window_splits


def fit_ridge_model(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    *,
    alpha: float = 1.0,
) -> Pipeline:
    """Fit a scaled Ridge regressor using only the supplied training rows.

    Feature selection and missing-value handling are intentionally outside
    this function. Callers must construct each chronological training fold
    before calling it; the scaler is fitted as part of the pipeline on that
    fold alone.
    """
    _validate_training_data(x_train, y_train)
    if not np.isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be finite and greater than zero.")

    model = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=float(alpha))),
        ]
    )
    model.fit(x_train, y_train)
    return model


def build_regression_model(
    model_family: str,
    *,
    parameters: Mapping[str, object] | None = None,
    random_state: int = 42,
) -> Pipeline | RandomForestRegressor:
    """Build one pre-specified traditional regression estimator."""
    parameters = dict(parameters or {})
    if model_family == "ridge":
        alpha = parameters.pop("alpha", 1.0)
        if parameters:
            raise ValueError(f"Unsupported Ridge parameters: {sorted(parameters)}")
        return Pipeline(
            steps=[("scale", StandardScaler()), ("model", Ridge(alpha=float(alpha)))]
        )
    if model_family == "random_forest":
        allowed = {"n_estimators", "max_depth", "max_features", "min_samples_leaf"}
        unexpected = set(parameters).difference(allowed)
        if unexpected:
            raise ValueError(f"Unsupported Random Forest parameters: {sorted(unexpected)}")
        settings = {
            "n_estimators": 200, "max_depth": None, "max_features": 0.5,
            "min_samples_leaf": 20,
        }
        settings.update(parameters)
        return RandomForestRegressor(random_state=random_state, n_jobs=1, **settings)
    raise ValueError("model_family must be 'ridge' or 'random_forest'.")


def build_direction_classifier(
    *,
    parameters: Mapping[str, object] | None = None,
    random_state: int = 42,
) -> RandomForestClassifier:
    """Build a balanced Random Forest classifier for the existing -1/0/+1 labels."""
    parameters = dict(parameters or {})
    allowed = {"n_estimators", "max_depth", "max_features", "min_samples_leaf"}
    unexpected = set(parameters).difference(allowed)
    if unexpected:
        raise ValueError(f"Unsupported Random Forest classifier parameters: {sorted(unexpected)}")
    settings = {
        "n_estimators": 200, "max_depth": None, "max_features": 0.5,
        "min_samples_leaf": 20,
    }
    settings.update(parameters)
    return RandomForestClassifier(
        class_weight="balanced", random_state=random_state, n_jobs=1, **settings
    )


def predict_ridge(model: Pipeline, x_forecast: pd.DataFrame) -> pd.Series:
    """Predict complete rows and preserve the forecast index."""
    if not isinstance(x_forecast, pd.DataFrame):
        raise TypeError("x_forecast must be a pandas DataFrame.")
    if x_forecast.empty or x_forecast.shape[1] == 0:
        raise ValueError("x_forecast must contain at least one row and feature.")
    if not np.isfinite(x_forecast.to_numpy(dtype=float)).all():
        raise ValueError("x_forecast must contain only finite values.")
    if hasattr(model, "feature_names_in_") and list(model.feature_names_in_) != list(x_forecast.columns):
        raise ValueError("Forecast feature columns must match the fitted model in order.")
    values = np.asarray(model.predict(x_forecast), dtype=float)
    if values.ndim != 1 or len(values) != len(x_forecast):
        raise ValueError("The fitted model returned predictions with an invalid shape.")
    return pd.Series(values, index=x_forecast.index, name="ridge_forecast")


def ridge_walk_forward_predictions(
    x: pd.DataFrame,
    y: pd.Series,
    *,
    horizon: int,
    initial_train_size: int,
    validation_size: int,
    step_size: int | None = None,
    embargo: int = 0,
    alpha: float = 1.0,
) -> pd.DataFrame:
    """Generate expanding walk-forward Ridge predictions on acquired-row positions.

    Split boundaries and horizon purging are calculated on the complete input
    timeline before incomplete feature/target rows are excluded. This avoids
    compressing missing acquired rows and accidentally changing the horizon.
    """
    return regression_walk_forward_predictions(
        x,
        y,
        model_factory=lambda: build_regression_model("ridge", parameters={"alpha": alpha}),
        horizon=horizon,
        initial_train_size=initial_train_size,
        validation_size=validation_size,
        step_size=step_size,
        embargo=embargo,
    )


def regression_walk_forward_predictions(
    x: pd.DataFrame,
    y: pd.Series,
    *,
    model_factory,
    horizon: int,
    initial_train_size: int,
    validation_size: int,
    step_size: int | None = None,
    embargo: int = 0,
    on_fit=None,
) -> pd.DataFrame:
    """Evaluate a regression estimator on purged expanding walk-forward folds."""
    valid_features, valid_targets, splits = _prepare_walk_forward_inputs(
        x,
        y,
        horizon=horizon,
        initial_train_size=initial_train_size,
        validation_size=validation_size,
        step_size=step_size,
        embargo=embargo,
    )
    records: list[dict[str, object]] = []
    for fold_number, (train_positions, validation_positions) in enumerate(splits, start=1):
        train_positions = train_positions[valid_features[train_positions] & valid_targets[train_positions]]
        validation_positions = validation_positions[
            valid_features[validation_positions] & valid_targets[validation_positions]
        ]
        if train_positions.size < 2:
            raise ValueError(f"Fold {fold_number} has fewer than two complete training rows.")
        if validation_positions.size == 0:
            continue
        model = model_factory()
        model.fit(x.iloc[train_positions], y.iloc[train_positions])
        if on_fit is not None:
            on_fit(fold_number, model, x.iloc[train_positions], y.iloc[train_positions])
        predictions = np.asarray(model.predict(x.iloc[validation_positions]), dtype=float)
        for position, forecast in zip(validation_positions, predictions):
            records.append({"date": x.index[position], "fold": fold_number,
                            "actual": float(y.iloc[position]), "forecast": float(forecast)})
    if not records:
        raise ValueError("Walk-forward evaluation produced no complete validation predictions.")
    return pd.DataFrame.from_records(records).set_index("date")


def direction_walk_forward_predictions(
    x: pd.DataFrame,
    y: pd.Series,
    *,
    horizon: int,
    initial_train_size: int,
    validation_size: int,
    step_size: int | None = None,
    embargo: int = 0,
    parameters: Mapping[str, object] | None = None,
    random_state: int = 42,
    on_fit=None,
) -> pd.DataFrame:
    """Evaluate three-class Random Forest direction forecasts chronologically."""
    valid_features, valid_targets, splits = _prepare_walk_forward_inputs(
        x,
        y,
        horizon=horizon,
        initial_train_size=initial_train_size,
        validation_size=validation_size,
        step_size=step_size,
        embargo=embargo,
    )
    observed_labels = y[valid_targets].to_numpy(dtype=float)
    if not np.isin(observed_labels, (-1.0, 0.0, 1.0)).all():
        raise ValueError("Direction targets must use only the existing -1, 0 and +1 labels.")
    records: list[dict[str, object]] = []
    for fold_number, (train_positions, validation_positions) in enumerate(splits, start=1):
        train_positions = train_positions[valid_features[train_positions] & valid_targets[train_positions]]
        validation_positions = validation_positions[
            valid_features[validation_positions] & valid_targets[validation_positions]
        ]
        if train_positions.size < 2:
            raise ValueError(f"Fold {fold_number} has fewer than two complete training rows.")
        if validation_positions.size == 0:
            continue
        model = build_direction_classifier(parameters=parameters, random_state=random_state)
        model.fit(x.iloc[train_positions], y.iloc[train_positions].astype(int))
        if on_fit is not None:
            on_fit(fold_number, model, x.iloc[train_positions], y.iloc[train_positions])
        predictions = model.predict(x.iloc[validation_positions]).astype(int)
        probabilities = model.predict_proba(x.iloc[validation_positions])
        class_to_column = {int(label): i for i, label in enumerate(model.classes_)}
        if not set(class_to_column).issubset({-1, 0, 1}):
            raise ValueError("The fitted classifier returned unsupported direction classes.")
        for offset, position in enumerate(validation_positions):
            mapped_probabilities = np.array([
                probabilities[offset, class_to_column[label]] if label in class_to_column else 0.0
                for label in (-1, 0, 1)
            ])
            if not np.isfinite(mapped_probabilities).all() or not np.isclose(mapped_probabilities.sum(), 1.0):
                raise ValueError("Mapped direction probabilities must be finite and sum to one.")
            records.append({
                "date": x.index[position], "fold": fold_number,
                "actual": int(y.iloc[position]), "forecast": int(predictions[offset]),
                "probability_negative": float(mapped_probabilities[0]),
                "probability_neutral": float(mapped_probabilities[1]),
                "probability_positive": float(mapped_probabilities[2]),
            })
    if not records:
        raise ValueError("Walk-forward evaluation produced no complete validation predictions.")
    return pd.DataFrame.from_records(records).set_index("date")


def _prepare_walk_forward_inputs(
    x: pd.DataFrame,
    y: pd.Series,
    *,
    horizon: int,
    initial_train_size: int,
    validation_size: int,
    step_size: int | None,
    embargo: int,
):
    if not isinstance(x, pd.DataFrame) or not isinstance(y, pd.Series):
        raise TypeError("x must be a DataFrame and y must be a Series.")
    if not x.index.equals(y.index):
        raise ValueError("Feature and target indexes must be identical and ordered.")
    if not x.index.is_unique or not x.index.is_monotonic_increasing:
        raise ValueError("Input index must be unique and chronologically increasing.")
    if x.empty or x.shape[1] == 0:
        raise ValueError("Input data must contain rows and at least one feature.")
    feature_values = x.to_numpy(dtype=float, na_value=np.nan)
    target_values = y.to_numpy(dtype=float, na_value=np.nan)
    valid_features = np.isfinite(feature_values).all(axis=1)
    valid_targets = np.isfinite(target_values)
    splits = expanding_window_splits(
        len(x), initial_train_size=initial_train_size,
        validation_size=validation_size, step_size=step_size,
        horizon=horizon, embargo=embargo,
    )
    return valid_features, valid_targets, splits


def _validate_training_data(x_train: pd.DataFrame, y_train: pd.Series) -> None:
    if not isinstance(x_train, pd.DataFrame):
        raise TypeError("x_train must be a pandas DataFrame.")
    if not isinstance(y_train, pd.Series):
        raise TypeError("y_train must be a pandas Series.")
    if x_train.empty or x_train.shape[1] == 0:
        raise ValueError("x_train must contain at least one row and feature.")
    if len(x_train) != len(y_train) or not x_train.index.equals(y_train.index):
        raise ValueError("Training features and target must have identical indexes.")
    if not np.isfinite(x_train.to_numpy(dtype=float)).all():
        raise ValueError("x_train must contain only finite values; imputation is not performed.")
    if not np.isfinite(y_train.to_numpy(dtype=float)).all():
        raise ValueError("y_train must contain only finite values.")
