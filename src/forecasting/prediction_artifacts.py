"""Temporal identity checks for Phase 8 prediction outputs."""

from __future__ import annotations

import numpy as np
import pandas as pd


PREDICTION_KEY = ["date", "fold", "asset", "horizon", "target", "feature_group", "model"]


def attach_acquired_positions(
    predictions: pd.DataFrame,
    market_data: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Attach exact row positions from each asset's original acquired timeline."""
    required = {"date", "asset"}
    if missing := required.difference(predictions.columns):
        raise ValueError(f"Prediction data are missing identity columns: {sorted(missing)}.")
    result = predictions.copy()
    result["date"] = pd.to_datetime(result["date"])
    positions = np.empty(len(result), dtype=np.int64)
    for symbol, row_positions in result.groupby("asset", sort=False).indices.items():
        if symbol not in market_data:
            raise ValueError(f"No acquired timeline is available for asset {symbol}.")
        acquired_index = pd.DatetimeIndex(market_data[symbol].index)
        if acquired_index.has_duplicates or not acquired_index.is_monotonic_increasing:
            raise ValueError(f"Acquired timeline for {symbol} must be unique and chronological.")
        dates = pd.DatetimeIndex(result.iloc[row_positions]["date"])
        exact_positions = acquired_index.get_indexer(dates)
        if (exact_positions < 0).any():
            missing_dates = dates[exact_positions < 0].strftime("%Y-%m-%d").tolist()[:5]
            raise ValueError(f"Prediction dates for {symbol} are absent from its acquired timeline: {missing_dates}.")
        positions[row_positions] = exact_positions
    if "acquired_position" in result:
        existing = pd.to_numeric(result["acquired_position"], errors="coerce")
        mismatch = existing.notna() & (existing.to_numpy(dtype=float) != positions)
        if mismatch.any():
            raise ValueError("Existing acquired positions disagree with exact asset/date timeline matches.")
    result["acquired_position"] = positions
    return result


def validate_prediction_artifact(
    predictions: pd.DataFrame,
    market_data: dict[str, pd.DataFrame] | None = None,
) -> None:
    """Reject incomplete, duplicate, misordered or inconsistently paired predictions."""
    required = set(PREDICTION_KEY) | {
        "actual", "forecast", "acquired_position",
        "probability_negative", "probability_neutral", "probability_positive",
    }
    if missing := required.difference(predictions.columns):
        raise ValueError(f"Prediction artefact is missing columns: {sorted(missing)}.")
    identity = [column for column in PREDICTION_KEY if column != "date"] + ["date"]
    if predictions[identity].isna().any().any():
        raise ValueError("Prediction identity fields must not be missing.")
    if predictions["acquired_position"].isna().any():
        raise ValueError("Every prediction must have an acquired timeline position.")
    for column in ("actual", "forecast", "acquired_position"):
        values = pd.to_numeric(predictions[column], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"Prediction field {column} must contain finite values.")
    if predictions.duplicated(PREDICTION_KEY).any():
        raise ValueError("Prediction keys must be unique.")
    if (predictions["acquired_position"] < 0).any():
        raise ValueError("Acquired positions must be non-negative.")
    if not predictions["horizon"].isin((5, 10, 20)).all():
        raise ValueError("Prediction horizons must be one of the approved acquired-row horizons.")
    if not predictions["target"].isin(("return", "volatility", "direction")).all():
        raise ValueError("Prediction targets must be return, volatility or direction.")
    if not predictions["model"].isin(("ridge", "random_forest", "random_forest_classifier")).all():
        raise ValueError("Prediction model family is outside the approved Phase 8 scope.")
    valid_models = predictions["target"].eq("direction") == predictions["model"].eq("random_forest_classifier")
    if not valid_models.all():
        raise ValueError("Direction targets require the classifier and regression targets require regressors.")
    classifier = predictions["model"].eq("random_forest_classifier")
    probability_columns = ["probability_negative", "probability_neutral", "probability_positive"]
    probabilities = predictions.loc[classifier, probability_columns].to_numpy(dtype=float)
    if not predictions.loc[classifier, "forecast"].isin((-1, 0, 1)).all():
        raise ValueError("Direction forecasts must remain in the approved -1, 0 and +1 labels.")
    if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("Classifier probabilities must be finite and bounded between zero and one.")
    if len(probabilities) and not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-12, rtol=0.0):
        raise ValueError("Classifier probabilities must sum to one for every prediction.")

    if market_data is not None:
        dated = attach_acquired_positions(predictions, market_data)
        if not np.array_equal(dated["acquired_position"].to_numpy(), predictions["acquired_position"].to_numpy()):
            raise ValueError("Prediction date and acquired position do not identify the same source row.")

    if not predictions.groupby(["asset", "fold"], sort=False)["acquired_position"].apply(
        lambda values: values.is_monotonic_increasing
    ).all():
        raise ValueError("Predictions must be chronological within each asset and fold.")

    temporal = predictions.groupby(["asset", "horizon", "target", "date"], sort=False)
    if (temporal["fold"].nunique() > 1).any():
        raise ValueError("A forecast origin must retain the same fold across model and feature comparisons.")
    if (temporal["acquired_position"].nunique() > 1).any():
        raise ValueError("A forecast origin must retain one acquired position across comparisons.")
    actual_spread = temporal["actual"].agg(lambda values: values.max() - values.min())
    if not np.allclose(actual_spread.to_numpy(dtype=float), 0.0, atol=1e-12, rtol=0.0):
        raise ValueError("Actual target values disagree across models or feature groups on a common date.")

    feature_dates = predictions.groupby(
        ["asset", "horizon", "target", "model", "feature_group"], sort=False
    )["date"].apply(lambda values: frozenset(pd.to_datetime(values)))
    for _, group in feature_dates.groupby(level=["asset", "horizon", "target", "model"]):
        if group.nunique() != 1:
            raise ValueError("Feature groups expected to share dates have different forecast origins.")
