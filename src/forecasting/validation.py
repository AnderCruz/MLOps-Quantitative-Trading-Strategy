"""Chronological splits and overlap controls for forward financial labels."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def chronological_holdout(
    n_observations: int,
    *,
    holdout_fraction: float = 0.2,
    horizon: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Return development and final-holdout positions, purging boundary labels.

    Positions are row offsets in one asset's chronological acquired series.
    The holdout starts at ``floor(n * (1 - fraction))``. Development origins
    whose labels extend into the holdout are removed.
    """
    if not isinstance(n_observations, int) or isinstance(n_observations, bool) or n_observations < 2:
        raise ValueError("n_observations must be an integer of at least 2.")
    if not 0 < holdout_fraction < 1:
        raise ValueError("holdout_fraction must be between 0 and 1.")
    _validate_horizon(horizon)
    boundary = int(np.floor(n_observations * (1 - holdout_fraction)))
    if boundary <= horizon or boundary >= n_observations:
        raise ValueError("The requested holdout leaves too few development or test rows.")
    holdout = np.arange(boundary, n_observations, dtype=int)
    development = purge_overlapping_origins(np.arange(boundary, dtype=int), holdout, horizon=horizon)
    return development, holdout


def purge_overlapping_origins(
    training_positions: Sequence[int],
    evaluation_positions: Sequence[int],
    *,
    horizon: int,
) -> np.ndarray:
    """Remove training origins whose ``horizon``-row labels overlap evaluation.

    A label at origin ``i`` covers acquired rows ``i+1`` through ``i+h``.
    The evaluation interval is based on the earliest evaluation origin. This
    supports both a final holdout and walk-forward validation blocks.
    """
    _validate_horizon(horizon)
    train = np.asarray(training_positions, dtype=int)
    evaluation = np.asarray(evaluation_positions, dtype=int)
    if train.ndim != 1 or evaluation.ndim != 1:
        raise ValueError("Positions must be one-dimensional.")
    if train.size == 0 or evaluation.size == 0:
        raise ValueError("Training and evaluation positions must be non-empty.")
    if np.any(train < 0) or np.any(evaluation < 0):
        raise ValueError("Positions must be non-negative.")
    if np.any(np.diff(train) <= 0) or np.any(np.diff(evaluation) <= 0):
        raise ValueError("Positions must be strictly increasing and unique.")
    first_evaluation = int(evaluation[0])
    return train[(train + horizon) <= first_evaluation]


def expanding_window_splits(
    n_observations: int,
    *,
    initial_train_size: int,
    validation_size: int,
    horizon: int,
    step_size: int | None = None,
    embargo: int = 0,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Create expanding walk-forward folds, with purged training boundaries.

    Only observations before each validation block may enter training, so a
    post-validation embargo is unnecessary for this expanding-only design.
    ``embargo`` additionally removes the requested number of acquired rows
    immediately before the validation block after horizon purging.
    """
    if not isinstance(n_observations, int) or isinstance(n_observations, bool) or n_observations < 1:
        raise ValueError("n_observations must be a positive integer.")
    for name, value in (("initial_train_size", initial_train_size), ("validation_size", validation_size)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"{name} must be a positive integer.")
    if step_size is None:
        step_size = validation_size
    if not isinstance(step_size, int) or isinstance(step_size, bool) or step_size < 1:
        raise ValueError("step_size must be a positive integer.")
    if not isinstance(embargo, int) or isinstance(embargo, bool) or embargo < 0:
        raise ValueError("embargo must be a non-negative integer.")
    _validate_horizon(horizon)
    if initial_train_size <= horizon:
        raise ValueError("initial_train_size must exceed horizon.")

    folds: list[tuple[np.ndarray, np.ndarray]] = []
    validation_start = initial_train_size
    all_positions = np.arange(n_observations, dtype=int)
    while validation_start < n_observations:
        validation_end = min(validation_start + validation_size, n_observations)
        validation = np.arange(validation_start, validation_end, dtype=int)
        training = all_positions[:validation_start]
        training = purge_overlapping_origins(training, validation, horizon=horizon)
        if embargo:
            training = training[training < validation_start - embargo]
        if training.size:
            folds.append((training, validation))
        validation_start += step_size
    if not folds:
        raise ValueError("No valid folds; increase n_observations or reduce split sizes.")
    return folds


def _validate_horizon(horizon: int) -> None:
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError("horizon must be a positive integer.")
