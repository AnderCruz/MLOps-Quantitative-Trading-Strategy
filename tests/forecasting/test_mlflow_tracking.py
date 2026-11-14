import os
import subprocess
import sys

import mlflow
from mlflow.tracking import MlflowClient

from src.forecasting.mlflow_tracking import configure_local_experiment


def test_local_mlflow_experiment_uses_sqlite_and_is_reused(tmp_path):
    first = configure_local_experiment(tmp_path, experiment_name="phase8_test")
    second = configure_local_experiment(tmp_path, experiment_name="phase8_test")
    assert first == second
    assert (tmp_path / "data" / "mlflow" / "mlflow.db").is_file()


def test_run_metadata_and_artifacts_persist_across_process_restart(tmp_path):
    experiment_id = configure_local_experiment(tmp_path, experiment_name="phase8_restart_test")
    with mlflow.start_run(experiment_id=experiment_id, run_name="traceable_run"):
        mlflow.log_param("feature_values_sha256", "a" * 64)
        mlflow.log_param("git_commit", "baseline-revision")
        mlflow.set_tag("git_worktree_dirty", "true")
        mlflow.log_metric("mae", 0.25)
        mlflow.log_text("local prediction record", "predictions.txt")
        run_id = mlflow.active_run().info.run_id

    project_root = os.fspath(tmp_path)
    code = """
from mlflow.tracking import MlflowClient
from src.forecasting.mlflow_tracking import configure_local_experiment
experiment_id = configure_local_experiment(ROOT, experiment_name='phase8_restart_test')
client = MlflowClient()
run = client.get_run(RUN_ID)
assert run.info.experiment_id == experiment_id
assert run.data.params['feature_values_sha256'] == 'a' * 64
assert run.data.tags['git_worktree_dirty'] == 'true'
assert run.data.metrics['mae'] == 0.25
assert 'predictions.txt' in client.list_artifacts(RUN_ID)[0].path
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        [os.fspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), environment.get("PYTHONPATH", "")]
    )
    environment["MLFLOW_TRACKING_URI"] = ""
    subprocess.run(
        [sys.executable, "-c", code.replace("ROOT", repr(project_root)).replace("RUN_ID", repr(run_id))],
        check=True, cwd=project_root, env=environment,
    )
