"""Tests for Yahoo Finance market acquisition configuration and metadata."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from scripts.acquire_market_data import (
    PROJECT_ROOT,
    AssetConfiguration,
    build_manifest,
    calculate_sha256,
    load_asset_config,
    normalise_columns,
    validate_market_data,
)


ASSET_CONFIGS = [
    "configs/assets/ng_l.yaml",
    "configs/assets/sse_l.yaml",
    "configs/assets/svt_l.yaml",
    "configs/assets/ftse_100.yaml",
]


@pytest.mark.parametrize("filename", ASSET_CONFIGS)
def test_load_asset_configurations(filename):
    """Load and validate all approved market asset configurations."""

    config_path = PROJECT_ROOT / filename

    config, config_hash = load_asset_config(config_path)

    assert config.asset.ticker == config.provider.symbol
    assert config.asset.accounting_currency == "GBP"
    assert len(config_hash) == 64


@pytest.mark.parametrize(
    ("filename", "ticker"),
    [
        ("ng_l.yaml", "NG.L"),
        ("sse_l.yaml", "SSE.L"),
        ("svt_l.yaml", "SVT.L"),
    ],
)
def test_equity_price_unit_metadata(filename, ticker):
    """Validate price-unit metadata for LSE equity instruments."""

    config_path = PROJECT_ROOT / "configs/assets" / filename

    config, _ = load_asset_config(config_path)

    assert config.asset.ticker == ticker
    assert config.asset.instrument_type == "equity"
    assert config.asset.provider_quote_currency == "GBp"
    assert config.asset.price_unit == "GBp"
    assert config.asset.conversion_to_accounting_currency == 0.01
    assert config.asset.price_unit_validation_status == "pending"


def test_ftse_index_price_unit_metadata():
    """Validate FTSE 100 index price-unit metadata."""

    config_path = PROJECT_ROOT / "configs/assets/ftse_100.yaml"

    config, _ = load_asset_config(config_path)

    assert config.asset.instrument_type == "index"
    assert config.asset.price_unit == "index_points"
    assert config.asset.conversion_to_accounting_currency is None
    assert config.asset.price_unit_validation_status == "not_applicable"


def test_equity_configuration_rejects_missing_conversion_factor():
    """Reject equity configurations without a conversion factor."""

    config_path = PROJECT_ROOT / "configs/assets/ng_l.yaml"

    config, _ = load_asset_config(config_path)
    config_data = config.asset.model_dump()

    config_data["conversion_to_accounting_currency"] = None

    with pytest.raises(
        ValidationError,
        match="require a conversion factor",
    ):
        AssetConfiguration.model_validate(config_data)


@pytest.mark.parametrize("factor", [0, -0.01])
def test_equity_configuration_rejects_non_positive_conversion(factor):
    """Reject zero or negative equity conversion factors."""

    config_path = PROJECT_ROOT / "configs/assets/ng_l.yaml"

    config, _ = load_asset_config(config_path)
    config_data = config.asset.model_dump()

    config_data["conversion_to_accounting_currency"] = factor

    with pytest.raises(ValidationError):
        AssetConfiguration.model_validate(config_data)


def test_equity_configuration_rejects_index_points():
    """Reject index-point units for equity instruments."""

    config_path = PROJECT_ROOT / "configs/assets/ng_l.yaml"

    config, _ = load_asset_config(config_path)
    config_data = config.asset.model_dump()

    config_data["price_unit"] = "index_points"

    with pytest.raises(
        ValidationError,
        match="cannot use index_points",
    ):
        AssetConfiguration.model_validate(config_data)


def test_index_configuration_rejects_currency_conversion():
    """Reject currency conversion factors for index instruments."""

    config_path = PROJECT_ROOT / "configs/assets/ftse_100.yaml"

    config, _ = load_asset_config(config_path)
    config_data = config.asset.model_dump()

    config_data["conversion_to_accounting_currency"] = 0.01

    with pytest.raises(
        ValidationError,
        match="cannot have a currency conversion factor",
    ):
        AssetConfiguration.model_validate(config_data)


def test_manifest_contains_new_financial_metadata():
    """Verify financial denomination metadata in the manifest."""

    config_path = PROJECT_ROOT / "configs/assets/ng_l.yaml"

    config, config_hash = load_asset_config(config_path)

    data = pd.DataFrame(
        {"Close": [100.0, 101.0]},
        index=pd.to_datetime(
            ["2026-11-06", "2026-11-09"]
        ),
    )

    manifest = build_manifest(
        data=data,
        config=config,
        config_path=config_path,
        config_hash=config_hash,
        acquisition_id="TEST_ONLY",
        retrieved_at=datetime(
            2026, 11, 9, tzinfo=timezone.utc
        ),
        files={},
        warnings=[],
    )

    assert manifest["accounting_currency"] == "GBP"
    assert manifest["provider_quote_currency"] == "GBp"
    assert manifest["price_unit"] == "GBp"
    assert manifest["conversion_to_accounting_currency"] == 0.01
    assert manifest["price_unit_validation_status"] == "pending"


def test_manifest_preserves_legacy_metadata():
    """Preserve existing manifest metadata fields."""

    config_path = PROJECT_ROOT / "configs/assets/ng_l.yaml"

    config, config_hash = load_asset_config(config_path)

    data = pd.DataFrame(
        {"Close": [100.0]},
        index=pd.to_datetime(["2026-11-09"]),
    )

    manifest = build_manifest(
        data=data,
        config=config,
        config_path=config_path,
        config_hash=config_hash,
        acquisition_id="TEST_ONLY",
        retrieved_at=datetime(
            2026, 11, 9, tzinfo=timezone.utc
        ),
        files={},
        warnings=[],
    )

    assert manifest["currency"] == "GBP"
    assert manifest["currency_status"] == "configured_assumption"
    assert manifest["instrument_type"] == "equity"
    assert manifest["exchange"] == "LSE"
    assert manifest["market_timezone"] == "Europe/London"


def test_market_data_values_are_not_currency_converted():
    """Verify market data values remain unchanged during normalisation."""

    original = pd.DataFrame(
        {
            "Open": [1250.0, 1260.0],
            "High": [1270.0, 1280.0],
            "Low": [1240.0, 1250.0],
            "Close": [1255.0, 1270.0],
            "Volume": [1000000, 1200000],
        },
        index=pd.to_datetime(
            ["2026-11-06", "2026-11-09"]
        ),
    )

    expected = original.copy(deep=True)

    result = normalise_columns(
        original.copy(deep=True),
        "NG.L",
    )

    validate_market_data(result, "equity")

    pd.testing.assert_frame_equal(result, expected)


@pytest.mark.parametrize("filename", ASSET_CONFIGS)
def test_asset_configuration_sha256(filename):
    """Verify asset configuration SHA-256 integrity."""

    config_path = PROJECT_ROOT / filename

    _, config_hash = load_asset_config(config_path)

    assert config_hash == calculate_sha256(config_path)
    assert len(config_hash) == 64