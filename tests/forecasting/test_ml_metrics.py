import numpy as np
import pandas as pd
import pytest

from src.forecasting.ml_metrics import (
    block_bootstrap_mae_difference,
    direction_metrics,
    fold_direction_metrics,
)


def test_three_class_direction_metrics_retain_neutral_class_and_binary_auc():
    predictions = pd.DataFrame(
        {
            "actual": [-1, 0, 1, 1, -1, 0],
            "forecast": [-1, 0, 0, 1, 1, 0],
            "probability_positive": [0.1, 0.2, 0.4, 0.8, 0.7, 0.1],
        }
    )
    metrics = direction_metrics(predictions)
    assert metrics["n_observations"] == 6
    assert len(metrics["confusion_matrix"]) == 3
    assert np.isfinite(metrics["roc_auc_positive_vs_rest"])
    predictions["fold"] = [1, 1, 1, 2, 2, 2]
    assert fold_direction_metrics(predictions).shape[0] == 2


def test_block_bootstrap_mae_difference_is_seed_reproducible_and_paired():
    dates = pd.date_range("2024-01-01", periods=30, freq="B")
    predictions = pd.DataFrame(
        {"fold": np.repeat([1, 2], 15), "actual": np.zeros(30), "forecast": np.ones(30)},
        index=dates,
    )
    benchmark = pd.Series(0.5, index=dates)
    first = block_bootstrap_mae_difference(predictions, benchmark, horizon=5, replications=200)
    second = block_bootstrap_mae_difference(predictions, benchmark, horizon=5, replications=200)
    assert first == second
    assert first["mae_difference_model_minus_benchmark"] == pytest.approx(0.5)
    assert first["n_paired"] == 30


def test_block_bootstrap_excludes_non_finite_pairs_consistently():
    dates = pd.date_range("2024-01-01", periods=5, freq="B")
    predictions = pd.DataFrame(
        {"fold": [1] * 5, "acquired_position": range(5),
         "actual": [0.0, 0.0, np.inf, 0.0, 0.0],
         "forecast": [1.0] * 5}, index=dates,
    )
    benchmark = pd.Series([0.5] * 5, index=dates)
    result = block_bootstrap_mae_difference(predictions, benchmark, horizon=2, replications=100)
    assert result["n_paired"] == 4


def test_block_bootstrap_rejects_duplicate_benchmark_dates_and_missing_folds():
    dates = pd.date_range("2024-01-01", periods=3, freq="B")
    predictions = pd.DataFrame(
        {"fold": [1, 1, 1], "actual": [0.0] * 3, "forecast": [1.0] * 3}, index=dates
    )
    with pytest.raises(ValueError, match="Benchmark dates must be unique"):
        block_bootstrap_mae_difference(
            predictions, pd.Series([0.0, 1.0], index=[dates[0], dates[0]]),
            horizon=1, replications=100,
        )
    predictions.loc[dates[0], "fold"] = np.nan
    with pytest.raises(ValueError, match="Fold identifiers must be complete"):
        block_bootstrap_mae_difference(
            predictions, pd.Series(0.0, index=dates), horizon=1, replications=100
        )


def test_direction_metrics_reject_non_finite_probability():
    predictions = pd.DataFrame({
        "actual": [-1, 1], "forecast": [-1, 1],
        "probability_positive": [0.1, np.inf],
    })
    with pytest.raises(ValueError, match="probabilities must be finite"):
        direction_metrics(predictions)
