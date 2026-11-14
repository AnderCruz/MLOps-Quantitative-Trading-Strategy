"""Tests for causal, interpretable regime indicators."""

import numpy as np
import pandas as pd
import pytest

from src.regimes import build_regime_indicators


def _prices(count=20):
    return pd.DataFrame({"Close": np.linspace(100.0, 120.0, count)})


def test_regime_indicators_respect_warmup_and_classify_trend():
    result = build_regime_indicators(
        _prices(),
        volatility_window=3,
        threshold_window=4,
        trend_windows=(3, 6),
    )

    assert pd.isna(result.loc[5, "volatility_regime"])
    assert result.loc[7:, "volatility_regime"].notna().all()
    assert pd.isna(result.loc[4, "trend_regime"])
    assert result.loc[5, "trend_regime"] == "uptrend"


def test_volatility_thresholds_use_prior_observations_only():
    original = _prices(30)
    changed = original.copy()
    changed.loc[20, "Close"] = 500.0

    original_result = build_regime_indicators(
        original, volatility_window=3, threshold_window=5, trend_windows=(3, 6)
    )
    changed_result = build_regime_indicators(
        changed, volatility_window=3, threshold_window=5, trend_windows=(3, 6)
    )

    for column in ("volatility_threshold_low", "volatility_threshold_high"):
        assert changed_result.loc[20, column] == pytest.approx(original_result.loc[20, column])


def test_future_observations_do_not_change_prior_regime_outputs():
    original = _prices(30)
    extended = pd.concat([original, pd.DataFrame({"Close": [500.0]})], ignore_index=True)
    kwargs = {"volatility_window": 3, "threshold_window": 5, "trend_windows": (3, 6)}

    original_result = build_regime_indicators(original, **kwargs)
    extended_result = build_regime_indicators(extended, **kwargs).iloc[: len(original)]

    pd.testing.assert_frame_equal(original_result, extended_result)


def test_missing_prices_remain_missing_in_regime_calculations():
    prices = pd.DataFrame({"Close": [100.0, 101.0, 102.0, np.nan, 104.0, 105.0, 106.0, 107.0, 108.0]})
    result = build_regime_indicators(
        prices, volatility_window=2, threshold_window=2, trend_windows=(2, 3)
    )

    assert pd.isna(result.loc[4, "realised_volatility_2"])
    assert pd.isna(result.loc[4, "volatility_regime"])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"volatility_window": 1},
        {"threshold_window": 1},
        {"trend_windows": (20, 10)},
        {"volatility_quantiles": (0.8, 0.2)},
    ],
)
def test_invalid_regime_parameters_are_rejected(kwargs):
    with pytest.raises(ValueError):
        build_regime_indicators(_prices(), **kwargs)


def test_unsorted_duplicate_and_non_positive_prices_are_rejected():
    with pytest.raises(ValueError, match="chronological"):
        build_regime_indicators(pd.DataFrame({"Close": [10.0, 11.0]}, index=[2, 1]))
    with pytest.raises(ValueError, match="duplicate"):
        build_regime_indicators(pd.DataFrame({"Close": [10.0, 11.0]}, index=[1, 1]))
    with pytest.raises(ValueError, match="positive"):
        build_regime_indicators(pd.DataFrame({"Close": [10.0, 0.0]}))
