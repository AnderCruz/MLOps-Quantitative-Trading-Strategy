import numpy as np
import pytest

from src.forecasting.validation import (
    chronological_holdout,
    expanding_window_splits,
    purge_overlapping_origins,
)


def test_holdout_is_chronological_and_purges_labels_crossing_boundary():
    development, holdout = chronological_holdout(100, holdout_fraction=0.2, horizon=5)
    assert development[0] == 0
    assert development[-1] == 75
    assert holdout[0] == 80
    assert development[-1] + 5 <= holdout[0]


def test_purge_removes_only_training_labels_overlapping_validation():
    kept = purge_overlapping_origins([0, 1, 2, 3, 4, 5], [8, 9], horizon=3)
    np.testing.assert_array_equal(kept, [0, 1, 2, 3, 4, 5])
    kept = purge_overlapping_origins([0, 1, 2, 3, 4, 5, 6, 7], [8, 9], horizon=3)
    np.testing.assert_array_equal(kept, [0, 1, 2, 3, 4, 5])


def test_expanding_folds_are_ordered_purged_and_do_not_train_on_future_rows():
    folds = expanding_window_splits(
        40, initial_train_size=20, validation_size=5, horizon=3, embargo=1
    )
    assert len(folds) == 4
    for train, validation in folds:
        assert train.max() < validation.min()
        assert train.max() + 3 <= validation.min()
        assert train.max() < validation.min() - 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_observations": 1},
        {"n_observations": 10, "holdout_fraction": 0},
        {"n_observations": 10, "horizon": 0},
    ],
)
def test_invalid_holdout_parameters_raise(kwargs):
    with pytest.raises(ValueError):
        chronological_holdout(**kwargs)


def test_future_rows_do_not_change_existing_walk_forward_splits():
    original = expanding_window_splits(
        50, initial_train_size=20, validation_size=5, horizon=3
    )
    extended = expanding_window_splits(
        60, initial_train_size=20, validation_size=5, horizon=3
    )
    for (train_a, validation_a), (train_b, validation_b) in zip(original, extended):
        np.testing.assert_array_equal(train_a, train_b)
        np.testing.assert_array_equal(validation_a, validation_b)


@pytest.mark.parametrize("horizon", [1, 5, 10, 20])
def test_purging_respects_acquired_positions_and_boundary_for_each_horizon(horizon):
    evaluation = np.array([100, 101, 102])
    training = np.array([0, 50, 100 - horizon - 1, 100 - horizon, 100 - horizon + 1])
    kept = purge_overlapping_origins(training, evaluation, horizon=horizon)
    assert np.all(kept + horizon <= evaluation[0])
    assert (100 - horizon) in kept
    assert (100 - horizon + 1) not in kept


def test_missing_acquired_positions_are_not_compressed_for_horizon_purging():
    # Positions 96–98 may be missing labels, but remain part of the acquired time axis.
    observed_training = np.array([90, 94, 95, 99])
    evaluation = np.array([100, 102])
    kept = purge_overlapping_origins(observed_training, evaluation, horizon=5)
    np.testing.assert_array_equal(kept, [90, 94, 95])
