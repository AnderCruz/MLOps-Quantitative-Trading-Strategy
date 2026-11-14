import numpy as np
import pandas as pd

from src.forecasting.ml_data import (
    build_phase8_features_and_targets,
    common_complete_mask,
    mask_features_to_common_dates,
)


def test_feature_groups_share_dates_without_compressing_acquired_timeline():
    index = pd.date_range("2024-01-01", periods=5, freq="B")
    target = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5], index=index)
    groups = {
        "B_financial": pd.DataFrame({"b": [1.0, 2.0, np.nan, 4.0, 5.0]}, index=index),
        "BC_cross_asset": pd.DataFrame({"bc": [1.0, 2.0, 3.0, np.nan, 5.0]}, index=index),
        "BCD_regime": pd.DataFrame({"bcd": [1.0, 2.0, 3.0, 4.0, 5.0]}, index=index),
    }

    mask = common_complete_mask(groups, target)
    masked = mask_features_to_common_dates(groups, mask)

    assert len(mask) == 5
    assert mask.tolist() == [True, True, False, False, True]
    assert masked["B_financial"].index.equals(index)
    assert pd.isna(masked["BCD_regime"].loc[index[2], "bcd"])


def test_future_price_changes_do_not_change_earlier_phase8_features():
    index = pd.date_range("2020-01-01", periods=320, freq="B")
    close = 100.0 * np.exp(np.cumsum(np.sin(np.arange(320) / 17.0) * 0.002 + 0.0001))
    original = pd.DataFrame({"Close": close}, index=index)
    changed = original.copy()
    changed.iloc[280:, changed.columns.get_loc("Close")] *= 1.5

    original_features, original_targets = build_phase8_features_and_targets({"TEST": original})
    changed_features, _ = build_phase8_features_and_targets({"TEST": changed})
    cutoff = index[279]
    for group in original_features["TEST"]:
        pd.testing.assert_frame_equal(
            original_features["TEST"][group].loc[:cutoff],
            changed_features["TEST"][group].loc[:cutoff],
        )
        assert not any(
            column.startswith(("forward_", "direction_"))
            for column in original_features["TEST"][group].columns
        )
    assert "forward_return_5" in original_targets["TEST"]
