import numpy as np
import pandas as pd

from src.forecasting.ml_data import common_complete_mask, mask_features_to_common_dates


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
