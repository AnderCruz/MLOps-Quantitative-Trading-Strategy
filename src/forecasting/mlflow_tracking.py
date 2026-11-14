"""Local SQLite-backed MLflow configuration for Phase 8 research."""

from __future__ import annotations

from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient


def configure_local_experiment(
    project_root: str | Path,
    *,
    experiment_name: str = "phase_8_machine_learning_experiments_gap_aware",
) -> str:
    """Configure an experiment with local SQLite metadata and local artifacts."""
    root = Path(project_root).resolve()
    tracking_dir = root / "data" / "mlflow"
    artifact_dir = tracking_dir / "artifacts"
    tracking_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    database_path = tracking_dir / "mlflow.db"
    mlflow.set_tracking_uri(f"sqlite:///{database_path}")
    client = MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = client.create_experiment(
            experiment_name,
            artifact_location=artifact_dir.as_uri(),
        )
    else:
        experiment_id = experiment.experiment_id
    return str(experiment_id)
