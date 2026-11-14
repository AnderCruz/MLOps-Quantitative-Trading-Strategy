"""Fold-aware machine-learning forecast metrics and dependence-aware intervals."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.forecasting.metrics import regression_metrics


DIRECTION_CLASSES = (-1, 0, 1)


def direction_metrics(predictions: pd.DataFrame) -> dict[str, object]:
    """Score existing three-class direction labels and positive-vs-rest probabilities."""
    required = {"actual", "forecast", "probability_positive"}
    missing = required.difference(predictions.columns)
    if missing:
        raise ValueError(f"Missing direction prediction columns: {sorted(missing)}")
    actual = predictions["actual"].astype(int).to_numpy()
    forecast = predictions["forecast"].astype(int).to_numpy()
    probability = predictions["probability_positive"].astype(float).to_numpy()
    if not np.isin(actual, DIRECTION_CLASSES).all() or not np.isin(forecast, DIRECTION_CLASSES).all():
        raise ValueError("Direction labels must remain in the approved classes -1, 0 and +1.")
    binary_actual = (actual == 1).astype(int)
    binary_forecast = (forecast == 1).astype(int)
    both_binary_classes = np.unique(binary_actual).size == 2
    return {
        "accuracy": float(accuracy_score(actual, forecast)),
        "balanced_accuracy": float(balanced_accuracy_score(actual, forecast)),
        "precision_macro": float(precision_score(actual, forecast, labels=DIRECTION_CLASSES, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(actual, forecast, labels=DIRECTION_CLASSES, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(actual, forecast, labels=DIRECTION_CLASSES, average="macro", zero_division=0)),
        "precision_positive": float(precision_score(binary_actual, binary_forecast, zero_division=0)),
        "recall_positive": float(recall_score(binary_actual, binary_forecast, zero_division=0)),
        "f1_positive": float(f1_score(binary_actual, binary_forecast, zero_division=0)),
        "roc_auc_positive_vs_rest": float(roc_auc_score(binary_actual, probability)) if both_binary_classes else np.nan,
        "pr_auc_positive_vs_rest": float(average_precision_score(binary_actual, probability)) if both_binary_classes else np.nan,
        "confusion_matrix": confusion_matrix(actual, forecast, labels=DIRECTION_CLASSES).tolist(),
        "n_observations": int(len(actual)),
    }


def fold_direction_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    """Return the approved direction metrics separately for each validation fold."""
    if "fold" not in predictions:
        raise ValueError("Direction predictions must include a fold column.")
    rows = []
    for fold, frame in predictions.groupby("fold", sort=True):
        rows.append({"fold": int(fold), **direction_metrics(frame)})
    return pd.DataFrame(rows)


def block_bootstrap_mae_difference(
    predictions: pd.DataFrame,
    benchmark_forecast: pd.Series,
    *,
    horizon: int,
    replications: int = 1000,
    random_state: int = 42,
) -> dict[str, float]:
    """Estimate paired model-minus-benchmark MAE with horizon-sized time blocks.

    The interval is descriptive and does not correct for the number of model
    comparisons. Resampling is performed separately within each walk-forward
    fold so blocks do not cross validation boundaries.
    """
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError("horizon must be a positive integer.")
    if not isinstance(replications, int) or replications < 100:
        raise ValueError("replications must be an integer of at least 100.")
    if not predictions.index.is_unique:
        raise ValueError("Prediction dates must be unique for paired comparison.")
    aligned = predictions.join(benchmark_forecast.rename("benchmark"), how="inner").dropna(
        subset=["actual", "forecast", "benchmark"]
    )
    if aligned.empty:
        raise ValueError("No paired forecast dates are available.")
    model_error = np.abs(aligned["forecast"].to_numpy() - aligned["actual"].to_numpy())
    benchmark_error = np.abs(aligned["benchmark"].to_numpy() - aligned["actual"].to_numpy())
    difference = model_error - benchmark_error
    fold_values = aligned["fold"].to_numpy() if "fold" in aligned else np.zeros(len(aligned))
    acquired_positions = (
        aligned["acquired_position"].to_numpy(dtype=int)
        if "acquired_position" in aligned else np.arange(len(aligned), dtype=int)
    )
    fold_blocks: list[np.ndarray] = []
    for fold in pd.unique(fold_values):
        positions = np.flatnonzero(fold_values == fold)
        order = np.argsort(acquired_positions[positions])
        positions = positions[order]
        acquired = acquired_positions[positions]
        block_id = (acquired - acquired[0]) // horizon
        unique_blocks = np.unique(block_id)
        matrix = np.full((len(unique_blocks), horizon), -1, dtype=int)
        block_lookup = {value: row for row, value in enumerate(unique_blocks)}
        rows = np.fromiter((block_lookup[value] for value in block_id), dtype=int, count=len(block_id))
        offsets = (acquired - acquired[0]) % horizon
        matrix[rows, offsets] = positions
        fold_blocks.append(matrix)
    generator = np.random.default_rng(random_state)
    draws = np.empty(replications, dtype=float)
    for replication in range(replications):
        sampled: list[int] = []
        for matrix in fold_blocks:
            choices = generator.integers(0, len(matrix), size=len(matrix))
            fold_sample = matrix[choices].reshape(-1)
            sampled.extend(fold_sample[fold_sample >= 0].tolist())
        draws[replication] = float(np.mean(difference[np.asarray(sampled, dtype=int)]))
    return {
        "mae_difference_model_minus_benchmark": float(np.mean(difference)),
        "block_bootstrap_ci_2_5": float(np.quantile(draws, 0.025)),
        "block_bootstrap_ci_97_5": float(np.quantile(draws, 0.975)),
        "n_paired": int(len(difference)),
        "block_length": int(horizon),
        "replications": int(replications),
    }


def fold_regression_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    """Return one regression-metric row per chronological validation fold."""
    if not {"actual", "forecast", "fold"}.issubset(predictions.columns):
        raise ValueError("Predictions must include actual, forecast and fold columns.")
    rows = []
    for fold, frame in predictions.groupby("fold", sort=True):
        rows.append({"fold": int(fold), **regression_metrics(frame["actual"], frame["forecast"])})
    return pd.DataFrame(rows)
