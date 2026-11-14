"""Tests for past-only financial feature calculations."""

import numpy as np
import pandas as pd
import pytest

from src.features.financial import (
    build_financial_features,
    log_returns,
    simple_returns,
)


def test_simple_and_log_returns_match_definitions():
    prices = pd.Series([100.0, 110.0, 99.0])

    np.testing.assert_allclose(simple_returns(prices).iloc[1:], [0.1, -0.1])
    np.testing.assert_allclose(log_returns(prices).iloc[1:], np.log([1.1, 0.9]))
    assert pd.isna(simple_returns(prices).iloc[0])


def test_momentum_and_rolling_features_use_only_current_and_past_values():
    frame = pd.DataFrame({"Close": [10.0, 11.0, 12.0, 13.0]})
    features = build_financial_features(frame, lookbacks=(2,))

    assert features.loc[3, "momentum_2"] == pytest.approx(13.0 / 11.0 - 1.0)
    assert features.loc[3, "sma_2"] == pytest.approx(12.5)
    assert features.loc[3, "price_to_sma_2"] == pytest.approx(13.0 / 12.5 - 1.0)
    assert features.loc[2, "drawdown_2"] == pytest.approx(0.0)
    assert features.loc[3, "drawdown_2"] == pytest.approx(0.0)


def test_ema_volatility_and_drawdown_formulas():
    prices = pd.Series([10.0, 12.0, 9.0, 10.0])
    features = build_financial_features(
        pd.DataFrame({"Close": prices}), lookbacks=(2,)
    )
    returns = prices.pct_change(fill_method=None)
    expected_ema = prices.ewm(span=2, adjust=False, min_periods=2).mean()

    assert features.loc[3, "ema_2"] == pytest.approx(expected_ema.loc[3])
    assert features.loc[3, "return_volatility_2"] == pytest.approx(
        returns.iloc[2:4].std(ddof=1)
    )
    assert features.loc[2, "drawdown_2"] == pytest.approx(9.0 / 12.0 - 1.0)


def test_future_observations_do_not_change_prior_feature_values():
    original = pd.DataFrame({"Close": [10.0, 12.0, 11.0, 13.0]})
    extended = pd.DataFrame({"Close": [10.0, 12.0, 11.0, 13.0, 500.0]})

    original_features = build_financial_features(original, lookbacks=(2,))
    extended_features = build_financial_features(extended, lookbacks=(2,))
    pd.testing.assert_frame_equal(
        original_features,
        extended_features.iloc[: len(original)],
    )


def test_price_features_are_invariant_to_quote_scale():
    prices = pd.Series([100.0, 102.0, 99.0, 104.0, 105.0])
    gbp = build_financial_features(pd.DataFrame({"Close": prices}), lookbacks=(2,))
    gbp_scaled = build_financial_features(
        pd.DataFrame({"Close": prices * 0.01}), lookbacks=(2,)
    )

    relative_columns = [
        "simple_return_1", "log_return_1", "momentum_2", "price_to_sma_2",
        "return_volatility_2", "realised_volatility_2", "downside_volatility_2",
        "drawdown_2",
    ]
    pd.testing.assert_frame_equal(gbp[relative_columns], gbp_scaled[relative_columns])


def test_missing_prices_are_not_filled_or_skipped_inside_windows():
    frame = pd.DataFrame({"Close": [10.0, np.nan, 12.0, 13.0]})
    features = build_financial_features(frame, lookbacks=(2,))

    assert pd.isna(features.loc[2, "simple_return_1"])
    assert pd.isna(features.loc[3, "momentum_2"])
    assert pd.isna(features.loc[3, "return_volatility_2"])


def test_volume_relative_to_previous_window_excludes_current_volume():
    frame = pd.DataFrame({"Close": [10.0, 11.0, 12.0], "Volume": [100.0, 200.0, 300.0]})
    features = build_financial_features(frame, lookbacks=(2,))

    assert pd.isna(features.loc[1, "relative_volume_2"])
    assert features.loc[2, "relative_volume_2"] == pytest.approx(300.0 / 150.0)
    extended = pd.DataFrame({"Close": [10.0, 11.0, 12.0, 13.0], "Volume": [100.0, 200.0, 300.0, 400.0]})
    extended_features = build_financial_features(extended, lookbacks=(2,))
    assert extended_features.loc[3, "relative_volume_2"] == pytest.approx(400.0 / 250.0)
    assert extended_features.loc[3, "volume_change_1"] == pytest.approx(400.0 / 300.0 - 1.0)


@pytest.mark.parametrize("bad_prices", [[10.0, 0.0], [10.0, -1.0]])
def test_non_positive_prices_are_rejected(bad_prices):
    with pytest.raises(ValueError, match="must be positive"):
        simple_returns(pd.Series(bad_prices))


def test_unsorted_or_duplicate_observations_are_rejected():
    unsorted = pd.DataFrame({"Close": [10.0, 11.0]}, index=[2, 1])
    duplicated = pd.DataFrame({"Close": [10.0, 11.0]}, index=[1, 1])

    with pytest.raises(ValueError, match="chronological"):
        build_financial_features(unsorted, lookbacks=(1,))
    with pytest.raises(ValueError, match="duplicate"):
        build_financial_features(duplicated, lookbacks=(1,))


def test_invalid_volume_and_missing_price_column_are_rejected():
    with pytest.raises(ValueError, match="negative"):
        build_financial_features(
            pd.DataFrame({"Close": [10.0, 11.0], "Volume": [1.0, -1.0]},),
            lookbacks=(1,),
        )
    with pytest.raises(ValueError, match="Missing required price column"):
        build_financial_features(pd.DataFrame({"Adj Close": [10.0]}))


def test_zero_volume_denominators_produce_missing_ratios_not_infinity():
    frame = pd.DataFrame({
        "Close": [10.0, 11.0, 12.0, 13.0],
        "Volume": [0.0, 0.0, 10.0, 20.0],
    })
    features = build_financial_features(frame, lookbacks=(2,))

    assert pd.isna(features.loc[1, "volume_change_1"])
    assert pd.isna(features.loc[2, "relative_volume_2"])
    assert not np.isinf(features["volume_change_1"].to_numpy()).any()
    assert not np.isinf(features["relative_volume_2"].to_numpy()).any()
