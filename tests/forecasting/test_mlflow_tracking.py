from src.forecasting.mlflow_tracking import configure_local_experiment


def test_local_mlflow_experiment_uses_sqlite_and_is_reused(tmp_path):
    first = configure_local_experiment(tmp_path, experiment_name="phase8_test")
    second = configure_local_experiment(tmp_path, experiment_name="phase8_test")
    assert first == second
    assert (tmp_path / "data" / "mlflow" / "mlflow.db").is_file()
