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
