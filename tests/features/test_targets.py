"""Tests for forward target definitions and temporal boundaries."""

import numpy as np
import pandas as pd
import pytest

from src.targets import build_forward_targets


def test_forward_return_direction_and_realised_volatility_definitions():
    prices = pd.DataFrame({"Close": [100.0, 110.0, 100.0, 105.0]})
    targets = build_forward_targets(prices, horizons=(2,), neutral_thresholds=(0.0,))

    assert targets.loc[0, "forward_return_2"] == pytest.approx(0.0)
    assert targets.loc[0, "direction_2_0bp"] == 0
    expected_volatility = np.sqrt(np.log(110.0 / 100.0) ** 2 + np.log(100.0 / 110.0) ** 2)
    assert targets.loc[0, "forward_realised_volatility_2"] == pytest.approx(expected_volatility)
    assert targets.loc[1, "direction_2_0bp"] == -1


def test_directional_neutral_threshold_is_inclusive_and_configurable():
    prices = pd.DataFrame({"Close": [100.0, 100.5, 101.0, 103.0]})
    targets = build_forward_targets(
        prices,
        horizons=(1,),
        neutral_thresholds=(0.0, 0.01),
    )

    assert targets.loc[0, "direction_1_0bp"] == 1
    assert targets.loc[0, "direction_1_100bp"] == 0
    assert targets.loc[2, "direction_1_100bp"] == 1


def test_target_tail_and_missing_intermediate_observations_remain_missing():
    prices = pd.DataFrame({"Close": [100.0, 101.0, np.nan, 103.0, 104.0]})
    targets = build_forward_targets(prices, horizons=(2,), neutral_thresholds=(0.0,))

    assert pd.isna(targets.loc[0, "forward_return_2"])
    assert pd.isna(targets.loc[0, "forward_realised_volatility_2"])
    assert pd.isna(targets.loc[1, "direction_2_0bp"])
    assert pd.isna(targets.loc[3, "forward_return_2"])


def test_future_price_changes_do_not_change_targets_before_their_origin():
    prices = pd.DataFrame({"Close": [100.0, 102.0, 101.0, 105.0, 107.0, 106.0]})
    changed = prices.copy()
    changed.loc[5, "Close"] = 50.0

    original_targets = build_forward_targets(prices, horizons=(2,), neutral_thresholds=(0.0,))
    changed_targets = build_forward_targets(changed, horizons=(2,), neutral_thresholds=(0.0,))

    pd.testing.assert_series_equal(
        original_targets.loc[:2, "forward_return_2"],
        changed_targets.loc[:2, "forward_return_2"],
    )
    assert original_targets.loc[3, "forward_return_2"] != changed_targets.loc[3, "forward_return_2"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"horizons": ()},
        {"horizons": (0,)},
        {"horizons": (1, 1)},
        {"neutral_thresholds": ()},
        {"neutral_thresholds": (-0.01,)},
        {"neutral_thresholds": (1.0,)},
    ],
)
def test_invalid_target_parameters_are_rejected(kwargs):
    with pytest.raises(ValueError):
        build_forward_targets(pd.DataFrame({"Close": [100.0, 101.0]}), **kwargs)


def test_unsorted_duplicate_non_positive_and_missing_prices_are_handled():
    with pytest.raises(ValueError, match="chronological"):
        build_forward_targets(pd.DataFrame({"Close": [100.0, 101.0]}, index=[2, 1]))
    with pytest.raises(ValueError, match="duplicate"):
        build_forward_targets(pd.DataFrame({"Close": [100.0, 101.0]}, index=[1, 1]))
    with pytest.raises(ValueError, match="positive"):
        build_forward_targets(pd.DataFrame({"Close": [100.0, 0.0]}))
    with pytest.raises(ValueError, match="Missing required price column"):
        build_forward_targets(pd.DataFrame({"Adj Close": [100.0, 101.0]}))
