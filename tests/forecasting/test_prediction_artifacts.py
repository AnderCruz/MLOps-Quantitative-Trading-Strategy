import pandas as pd
import pytest

from src.forecasting.prediction_artifacts import (
    attach_acquired_positions,
    validate_prediction_artifact,
)


@pytest.fixture
def sample_predictions():
    rows = []
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    for model, forecast in (("ridge", 0.1), ("random_forest", 0.2)):
        for position, date in enumerate(dates[1:], start=1):
            rows.append({
                "date": date, "fold": 1, "actual": 0.05, "forecast": forecast,
                "acquired_position": position, "asset": "TEST", "horizon": 5,
                "target": "return", "feature_group": "B_financial", "model": model,
                "probability_negative": float("nan"), "probability_neutral": float("nan"),
                "probability_positive": float("nan"),
            })
    return pd.DataFrame(rows).sort_values(["asset", "fold", "acquired_position"])


def test_positions_are_mapped_by_exact_asset_date(sample_predictions):
    market = {"TEST": pd.DataFrame(index=pd.date_range("2024-01-01", periods=3, freq="D"))}
    missing_position = sample_predictions.drop(columns="acquired_position")
    attached = attach_acquired_positions(missing_position, market)
    assert attached.acquired_position.tolist() == [1, 1, 2, 2]
    validate_prediction_artifact(attached, market)


def test_missing_position_is_rejected(sample_predictions):
    sample_predictions.loc[0, "acquired_position"] = float("nan")
    with pytest.raises(ValueError, match="timeline position"):
        validate_prediction_artifact(sample_predictions)


def test_duplicate_prediction_key_is_rejected(sample_predictions):
    duplicated = pd.concat([sample_predictions, sample_predictions.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="keys must be unique"):
        validate_prediction_artifact(duplicated)


def test_position_must_match_source_date(sample_predictions):
    market = {"TEST": pd.DataFrame(index=pd.date_range("2024-01-01", periods=3, freq="D"))}
    sample_predictions.loc[0, "acquired_position"] = 2
    with pytest.raises(ValueError, match="disagree"):
        attach_acquired_positions(sample_predictions, market)


def test_common_actuals_must_match(sample_predictions):
    sample_predictions.loc[2, "actual"] = 0.06
    with pytest.raises(ValueError, match="Actual target values disagree"):
        validate_prediction_artifact(sample_predictions)
