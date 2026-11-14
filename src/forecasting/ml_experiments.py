"""Phase 8 walk-forward experiment orchestration and local tracking."""

from __future__ import annotations

import hashlib
import json
import math
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd

from src.forecasting.garch import fit_garch11, forecast_garch11_cumulative_volatility, update_garch11_state
from src.forecasting.ml_data import FEATURE_GROUPS, common_complete_mask, mask_features_to_common_dates
from src.forecasting.ml_metrics import (
    block_bootstrap_mae_difference,
    direction_metrics,
    fold_direction_metrics,
    fold_regression_metrics,
)
from src.forecasting.ml_models import (
    build_direction_classifier,
    build_regression_model,
    direction_walk_forward_predictions,
    regression_walk_forward_predictions,
)
from src.forecasting.metrics import regression_metrics
from src.forecasting.mlflow_tracking import configure_local_experiment
from src.forecasting.validation import expanding_window_splits


SEED = 42
STUDY_ITERATION = "phase8_gap_aware_final"
INITIAL_TRAIN_FRACTION = 0.70
VALIDATION_FRACTION = 0.075
RF_PARAMETERS = {"n_estimators": 200, "max_features": 0.5, "min_samples_leaf": 20}
RIDGE_PARAMETERS = {"alpha": 1.0}


def _finite_target(target: pd.Series) -> np.ndarray:
    return np.isfinite(pd.to_numeric(target, errors="coerce").to_numpy(dtype=float, na_value=np.nan))


def _ar1_origin_forecast(log_returns: np.ndarray, train_end: int, origin: int, horizon: int) -> float:
    """AR(1) forecast using only adjacent acquired-row pairs; gaps are not compressed."""
    fit_end = min(train_end, len(log_returns) - 1)
    pair_positions = np.arange(1, fit_end + 1)
    valid = np.isfinite(log_returns[pair_positions]) & np.isfinite(log_returns[pair_positions - 1])
    pair_positions = pair_positions[valid]
    if len(pair_positions) < 30 or origin >= len(log_returns) or not np.isfinite(log_returns[origin]):
        return np.nan
    design = np.column_stack((np.ones(len(pair_positions)), log_returns[pair_positions - 1]))
    intercept, coefficient = np.linalg.lstsq(design, log_returns[pair_positions], rcond=None)[0]
    previous = float(log_returns[origin])
    total = 0.0
    for _ in range(horizon):
        previous = float(intercept + coefficient * previous)
        total += previous
    return float(np.expm1(total))


def _regression_baselines(
    target: pd.Series,
    eligibility: pd.Series,
    *,
    horizon: int,
    initial_train_size: int,
    validation_size: int,
    close: pd.Series,
    target_kind: str,
) -> pd.DataFrame:
    splits = expanding_window_splits(
        len(target), initial_train_size=initial_train_size,
        validation_size=validation_size, horizon=horizon,
    )
    target_values = target.to_numpy(dtype=float, na_value=np.nan)
    eligible = eligibility.to_numpy(dtype=bool) & np.isfinite(target_values)
    log_returns = np.log(close.astype(float)).diff().to_numpy(dtype=float)
    records: list[dict[str, object]] = []
    for fold_number, (train_pos, validation_pos) in enumerate(splits, start=1):
        train_pos = train_pos[eligible[train_pos]]
        validation_pos = validation_pos[eligible[validation_pos]]
        if len(train_pos) < 2:
            continue
        history = target_values[train_pos]
        train_end = int(train_pos[-1])
        garch_parameters = None
        if target_kind == "volatility":
            try:
                garch_parameters = fit_garch11(pd.Series(log_returns[: train_end + 1]))
            except (ValueError, RuntimeError, FloatingPointError):
                garch_parameters = None
        for position in validation_pos:
            row: dict[str, object] = {
                "date": target.index[position], "fold": fold_number,
                "actual": float(target_values[position]),
            }
            row["zero_return"] = 0.0 if target_kind == "return" else np.nan
            row["expanding_mean"] = float(np.mean(history))
            row["expanding_median"] = float(np.median(history))
            row["trailing_252_mean"] = float(np.mean(history[-252:]))
            if target_kind == "return":
                row["AR1_adjacent_pairs"] = _ar1_origin_forecast(
                    log_returns, train_end, int(position), horizon
                )
            else:
                row["AR1_adjacent_pairs"] = np.nan
            if target_kind == "volatility":
                recent = log_returns[max(0, int(position) - 251): int(position) + 1]
                row["rolling_historical_volatility"] = (
                    float(np.std(recent, ddof=1) * np.sqrt(horizon))
                    if len(recent) >= 2 and np.isfinite(recent).all() else np.nan
                )
                if garch_parameters is not None:
                    updated = update_garch11_state(
                        garch_parameters,
                        pd.Series(log_returns[train_end + 1: int(position) + 1]),
                    )
                    row["GARCH11"] = forecast_garch11_cumulative_volatility(
                        updated, horizon=horizon
                    )
                else:
                    row["GARCH11"] = np.nan
            records.append(row)
    if not records:
        return pd.DataFrame(columns=["fold", "actual"])
    return pd.DataFrame.from_records(records).set_index("date")


def _direction_baselines(
    target: pd.Series,
    eligibility: pd.Series,
    *,
    horizon: int,
    initial_train_size: int,
    validation_size: int,
) -> pd.DataFrame:
    splits = expanding_window_splits(
        len(target), initial_train_size=initial_train_size,
        validation_size=validation_size, horizon=horizon,
    )
    values = target.to_numpy(dtype=float, na_value=np.nan)
    eligible = eligibility.to_numpy(dtype=bool) & np.isfinite(values)
    rows = []
    for fold_number, (train_pos, valid_pos) in enumerate(splits, start=1):
        train_pos = train_pos[eligible[train_pos]]
        valid_pos = valid_pos[eligible[valid_pos]]
        if len(train_pos) < 2:
            continue
        train_labels = values[train_pos].astype(int)
        majority = int(pd.Series(train_labels).mode().iloc[0])
        positive_probability = float(np.mean(train_labels == 1))
        for position in valid_pos:
            rows.append({
                "date": target.index[position], "fold": fold_number,
                "actual": int(values[position]),
                "zero_direction": 0,
                "majority_class": majority,
                "probability_positive": positive_probability,
            })
    return pd.DataFrame.from_records(rows).set_index("date")


def _software_versions() -> dict[str, str]:
    names = ("pandas", "numpy", "scipy", "statsmodels", "scikit-learn", "mlflow", "pyarrow")
    versions = {}
    for name in names:
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            versions[name] = "not installed"
    return versions


def run_phase8_experiments(
    project_root: str | Path,
    market_data: dict[str, pd.DataFrame],
    inventory: pd.DataFrame,
    feature_data: dict[str, dict[str, pd.DataFrame]],
    target_data: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Run pre-specified, development-only walk-forward model comparisons."""
    root = Path(project_root).resolve()
    experiment_id = configure_local_experiment(root)
    dataset_ids = inventory.set_index("symbol")["dataset_id"].to_dict()
    software = _software_versions()
    metric_rows: list[dict[str, object]] = []
    fold_rows: list[dict[str, object]] = []
    comparison_rows: list[dict[str, object]] = []
    importance_rows: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []

    for symbol, frame in market_data.items():
        for horizon in (5, 10, 20):
            for target_kind, target_column in (
                ("return", f"forward_return_{horizon}"),
                ("volatility", f"forward_realised_volatility_{horizon}"),
                ("direction", f"direction_{horizon}_0bp"),
            ):
                target = target_data[symbol][target_column]
                mask = common_complete_mask(feature_data[symbol], target)
                masked_features = mask_features_to_common_dates(feature_data[symbol], mask)
                masked_target = target.where(mask)
                n_rows = len(frame)
                initial_train_size = max(horizon + 2, int(math.floor(n_rows * INITIAL_TRAIN_FRACTION)))
                validation_size = max(horizon + 1, int(math.ceil(n_rows * VALIDATION_FRACTION)))
                if initial_train_size + validation_size >= n_rows:
                    raise ValueError(f"Insufficient rows for walk-forward folds for {symbol}, h={horizon}.")

                if target_kind == "direction":
                    baselines = _direction_baselines(
                        masked_target, mask, horizon=horizon,
                        initial_train_size=initial_train_size,
                        validation_size=validation_size,
                    )
                    model_specs = [("random_forest_classifier", None)]
                else:
                    baselines = _regression_baselines(
                        masked_target, mask, horizon=horizon,
                        initial_train_size=initial_train_size,
                        validation_size=validation_size,
                        close=frame["Close"], target_kind=target_kind,
                    )
                    model_specs = [
                        ("ridge", RIDGE_PARAMETERS),
                        ("random_forest", RF_PARAMETERS),
                    ]

                for feature_group in FEATURE_GROUPS:
                    x = masked_features[feature_group]
                    for model_family, parameters in model_specs:
                        fit_capture: dict[str, object] = {}
                        training_ranges: list[dict[str, object]] = []

                        def capture_fit(fold, fitted, train_x, train_y):
                            fit_capture["model"] = fitted
                            fit_capture["fold"] = fold
                            training_ranges.append({
                                "fold": int(fold),
                                "training_start": str(train_x.index.min().date()),
                                "training_end": str(train_x.index.max().date()),
                            })
                            if hasattr(fitted, "feature_importances_"):
                                for feature, importance in zip(train_x.columns, fitted.feature_importances_):
                                    importance_rows.append({
                                        "asset": symbol, "horizon": horizon,
                                        "target": target_kind, "feature_group": feature_group,
                                        "model": model_family, "fold": fold,
                                        "feature": feature, "importance": float(importance),
                                    })

                        if target_kind == "direction":
                            predictions = direction_walk_forward_predictions(
                                x, masked_target, horizon=horizon,
                                initial_train_size=initial_train_size,
                                validation_size=validation_size,
                                parameters=RF_PARAMETERS, random_state=SEED,
                                on_fit=capture_fit,
                            )
                            model_metrics = direction_metrics(predictions)
                            for row in fold_direction_metrics(predictions).to_dict(orient="records"):
                                fold_rows.append({
                                    "asset": symbol, "horizon": horizon, "target": target_kind,
                                    "feature_group": feature_group, "model": model_family, **row,
                                })
                        else:
                            factory = lambda family=model_family, params=parameters: build_regression_model(
                                family, parameters=params, random_state=SEED
                            )
                            predictions = regression_walk_forward_predictions(
                                x, masked_target, model_factory=factory,
                                horizon=horizon, initial_train_size=initial_train_size,
                                validation_size=validation_size, on_fit=capture_fit,
                            )
                            predictions["acquired_position"] = frame.index.get_indexer(predictions.index)
                            model_metrics = regression_metrics(predictions["actual"], predictions["forecast"])
                            model_metrics["oos_r2_vs_expanding_mean"] = _oos_r2_vs_benchmark(
                                predictions, baselines["expanding_mean"]
                            )
                            fold_metrics = fold_regression_metrics(predictions)
                            for row in fold_metrics.to_dict(orient="records"):
                                fold_rows.append({
                                    "asset": symbol, "horizon": horizon, "target": target_kind,
                                    "feature_group": feature_group, "model": model_family, **row,
                                })

                        run_name = f"{symbol}_h{horizon}_{target_kind}_{feature_group}_{model_family}"
                        with mlflow.start_run(experiment_id=experiment_id, run_name=run_name):
                            mlflow.set_tags({
                                "phase": "8", "evaluation_role": "development_walk_forward",
                                "study_iteration": STUDY_ITERATION,
                                "asset": symbol, "target": target_kind,
                                "feature_group": feature_group, "model_family": model_family,
                            })
                            params_to_log = {
                                "asset": symbol, "horizon_acquired_rows": horizon,
                                "target_definition": target_column, "feature_group": feature_group,
                                "model_family": model_family,
                                "model_parameters": json.dumps(parameters or RF_PARAMETERS, sort_keys=True),
                                "available_data_start": str(frame.index.min().date()),
                                "available_data_end": str(frame.index.max().date()),
                                "development_validation_start": str(predictions.index.min().date()),
                                "development_validation_end": str(predictions.index.max().date()),
                                "initial_train_fraction": INITIAL_TRAIN_FRACTION,
                                "validation_fraction": VALIDATION_FRACTION,
                                "random_seed": SEED, "dataset_id": dataset_ids[symbol],
                                "feature_columns_sha256": hashlib.sha256(
                                    json.dumps(list(x.columns)).encode("utf-8")
                                ).hexdigest(),
                            }
                            mlflow.log_params(params_to_log)
                            mlflow.log_dict(training_ranges, "fold_training_ranges.json")
                            for package_name, package_version in software.items():
                                mlflow.set_tag(f"software.{package_name}", package_version)
                            for name, value in model_metrics.items():
                                if isinstance(value, (int, float, np.number)) and np.isfinite(value):
                                    mlflow.log_metric(name, float(value))
                            mlflow.log_text(predictions.to_csv(), "walk_forward_predictions.csv")
                            if target_kind == "direction":
                                mlflow.log_dict(
                                    {key: value for key, value in model_metrics.items()
                                     if key == "confusion_matrix"},
                                    "direction_metrics.json",
                                )
                            save_representative_model = (
                                symbol == "NG.L" and horizon == 10
                                and feature_group == "B_financial"
                            )
                            if fit_capture.get("model") is not None and save_representative_model:
                                mlflow.sklearn.log_model(
                                    fit_capture["model"],
                                    name="last_development_fold_model",
                                    skops_trusted_types=["sklearn.tree._tree.Tree"],
                                )
                                mlflow.set_tag("model_artifact_role", "representative_development_fold_fit")
                            else:
                                mlflow.set_tag("model_artifact_role", "predictions_and_metrics_only")
                            run_id = mlflow.active_run().info.run_id

                        metric_rows.append({
                            "asset": symbol, "horizon": horizon, "target": target_kind,
                            "feature_group": feature_group, "model": model_family,
                            "run_id": run_id, **model_metrics,
                        })
                        tagged_predictions = predictions.copy()
                        tagged_predictions["asset"] = symbol
                        tagged_predictions["horizon"] = horizon
                        tagged_predictions["target"] = target_kind
                        tagged_predictions["feature_group"] = feature_group
                        tagged_predictions["model"] = model_family
                        prediction_frames.append(tagged_predictions)

                        if target_kind == "direction":
                            for baseline_name, forecast_column in (
                                ("zero_direction", "zero_direction"),
                                ("majority_class", "majority_class"),
                            ):
                                paired = predictions.join(baselines[[forecast_column, "actual"]].rename(
                                    columns={"actual": "baseline_actual"}
                                ), how="inner")
                                comparison_rows.append({
                                    "asset": symbol, "horizon": horizon, "target": target_kind,
                                    "feature_group": feature_group, "model": model_family,
                                    "benchmark": baseline_name,
                                    "paired_dates": int(len(paired)),
                                    "accuracy_vs_benchmark": float(np.mean(
                                        paired["actual"].to_numpy() == paired[forecast_column].to_numpy()
                                    )),
                                })
                        else:
                            for benchmark_name in baselines.columns.difference(["actual", "fold"]):
                                benchmark = baselines[benchmark_name]
                                paired = predictions.join(benchmark.rename("benchmark"), how="inner").dropna(
                                    subset=["actual", "forecast", "benchmark"]
                                )
                                if paired.empty:
                                    continue
                                uncertainty = block_bootstrap_mae_difference(
                                    predictions, benchmark, horizon=horizon,
                                    replications=500, random_state=SEED,
                                )
                                comparison_rows.append({
                                    "asset": symbol, "horizon": horizon, "target": target_kind,
                                    "feature_group": feature_group, "model": model_family,
                                    "benchmark": benchmark_name,
                                    **uncertainty,
                                })

    results = {
        "metrics": pd.DataFrame(metric_rows),
        "fold_metrics": pd.DataFrame(fold_rows),
        "comparisons": pd.DataFrame(comparison_rows),
        "feature_importance": pd.DataFrame(importance_rows),
        "predictions": pd.concat(prediction_frames).sort_index() if prediction_frames else pd.DataFrame(),
    }
    return results


def _oos_r2_vs_benchmark(predictions: pd.DataFrame, benchmark: pd.Series) -> float:
    paired = predictions.join(benchmark.rename("benchmark"), how="inner").dropna(
        subset=["actual", "forecast", "benchmark"]
    )
    if paired.empty:
        return float("nan")
    model_sse = float(np.sum((paired["actual"] - paired["forecast"]) ** 2))
    benchmark_sse = float(np.sum((paired["actual"] - paired["benchmark"]) ** 2))
    return float(1.0 - model_sse / benchmark_sse) if benchmark_sse > 0 else float("nan")
