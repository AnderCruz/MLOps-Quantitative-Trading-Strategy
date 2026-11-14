"""Local Phase 8 input loading using the approved Phase 6/7 definitions."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.features.cross_asset import build_cross_asset_return_panel
from src.features.financial import build_financial_features
from src.regimes import build_regime_indicators
from src.targets import DEFAULT_HORIZONS, build_forward_targets


FEATURE_GROUPS = ("B_financial", "BC_cross_asset", "BCD_regime")


def load_local_market_data(project_root: str | Path) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Read the single configured local Parquet acquisition for each asset."""
    root = Path(project_root).resolve()
    market_data: dict[str, pd.DataFrame] = {}
    inventory: list[dict[str, object]] = []
    for config_path in sorted((root / "configs" / "assets").glob("*.yaml")):
        with config_path.open(encoding="utf-8") as stream:
            config = yaml.safe_load(stream)
        symbol = config["provider"]["symbol"]
        candidates = sorted(
            (root / "data" / "raw" / "market" / "yahoo_finance" / symbol)
            .glob(f"acquisition_*/{symbol}.parquet")
        )
        if len(candidates) != 1:
            raise RuntimeError(
                f"Expected exactly one local Parquet acquisition for {symbol}; found {len(candidates)}."
            )
        path = candidates[0]
        frame = pd.read_parquet(path)
        if "Date" in frame.columns:
            frame = frame.set_index("Date")
        frame.index = pd.to_datetime(frame.index)
        frame.index.name = "forecast_origin_observation_date"
        if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
            raise ValueError(f"Dates for {symbol} must be unique and chronological.")
        if "Close" not in frame:
            raise ValueError(f"Close is absent for {symbol}.")
        manifest_path = path.parent / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        market_data[symbol] = frame
        inventory.append(
            {
                "symbol": symbol,
                "dataset_id": manifest.get("dataset_id", manifest.get("acquisition_id", path.parent.name)),
                "source_file": path.relative_to(root).as_posix(),
                "price_unit": config["asset"].get("price_unit", "not configured"),
                "unit_validation": config["asset"].get("price_unit_validation_status", "not recorded"),
                "rows": len(frame),
                "first_date": frame.index.min(),
                "last_date": frame.index.max(),
                "missing_close": int(frame["Close"].isna().sum()),
            }
        )
    return market_data, pd.DataFrame(inventory).sort_values("symbol").reset_index(drop=True)


def build_phase8_features_and_targets(
    market_data: dict[str, pd.DataFrame],
) -> tuple[dict[str, dict[str, pd.DataFrame]], dict[str, pd.DataFrame]]:
    """Reuse the exact small B/BC/BCD sets and Phase 6 zero-band targets."""
    prices = {symbol: frame["Close"].astype(float) for symbol, frame in market_data.items()}
    cross_asset = build_cross_asset_return_panel(prices, lookbacks=(1,))
    features: dict[str, dict[str, pd.DataFrame]] = {}
    targets: dict[str, pd.DataFrame] = {}
    for symbol, frame in market_data.items():
        financial = build_financial_features(frame, lookbacks=(5, 20))[
            ["simple_return_1", "momentum_5", "momentum_20", "realised_volatility_20", "drawdown_20"]
        ].copy()
        peers = [
            column for column in cross_asset.columns
            if column.endswith("__return_1") and not column.startswith(f"{symbol}__")
        ]
        group_b = financial.rename(
            columns={
                "simple_return_1": "asset_return_1",
                "momentum_5": "asset_momentum_5",
                "momentum_20": "asset_momentum_20",
                "realised_volatility_20": "asset_realised_volatility_20",
                "drawdown_20": "asset_drawdown_20",
            }
        )
        group_bc = group_b.join(cross_asset[peers], how="left")
        regimes = build_regime_indicators(
            frame, volatility_window=20, threshold_window=252, trend_windows=(50, 200)
        )
        regime_categories = pd.DataFrame(index=frame.index)
        for column, allowed in (
            ("volatility_regime", ["low_volatility", "typical_volatility", "high_volatility"]),
            ("trend_regime", ["downtrend", "mixed_trend", "uptrend"]),
        ):
            categorical = pd.Categorical(regimes[column], categories=allowed)
            encoded = pd.get_dummies(categorical, prefix=column, dtype=float)
            encoded.index = frame.index
            regime_categories = regime_categories.join(encoded)
        group_bcd = group_bc.join(regime_categories, how="left")
        features[symbol] = {
            "B_financial": group_b,
            "BC_cross_asset": group_bc,
            "BCD_regime": group_bcd,
        }
        targets[symbol] = build_forward_targets(
            frame, horizons=DEFAULT_HORIZONS, neutral_thresholds=(0.0,)
        )
    return features, targets


def common_complete_mask(
    feature_groups: dict[str, pd.DataFrame], target: pd.Series
) -> pd.Series:
    """Mark rows complete for every group so model comparisons share dates."""
    mask = target.notna().copy()
    for frame in feature_groups.values():
        values = frame.to_numpy(dtype=float, na_value=np.nan)
        mask &= pd.Series(np.isfinite(values).all(axis=1), index=frame.index)
    return mask


def mask_features_to_common_dates(
    feature_groups: dict[str, pd.DataFrame], mask: pd.Series
) -> dict[str, pd.DataFrame]:
    """Keep the acquired timeline intact while excluding non-common rows from all groups."""
    return {name: frame.where(mask, axis=0) for name, frame in feature_groups.items()}
