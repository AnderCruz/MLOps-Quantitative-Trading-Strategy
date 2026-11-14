# AI Quantitative Trading Strategy

Multi-Asset Quantitative Trading Research and Strategy Optimisation System.

## Project Overview

A research-oriented quantitative trading system designed to investigate
multi-asset forecasting, trading strategies, risk management and systematic
strategy evaluation.

The initial pilot asset is National Grid (NG.L), within a multi-asset
architecture.

## Project Scope

- Multi-asset quantitative research.
- Daily market and macroeconomic data.
- Forecasting and uncertainty estimation.
- Strategy research and backtesting.
- Risk management and portfolio accounting.
- Paper trading.

The project is research-only. No live trading or broker integration is
authorised.

## Retrospective Notebook Reconstruction

Notebooks 01–05 have been retrospectively reconstructed to improve the
documentation and traceability of the completed data-related phases.

The five notebooks are documentary records, not original execution records.

Files:

1. `01_data_sources_investigation.ipynb`
2. `02_financial_data_acquisition.ipynb`
3. `03_macroeconomic_data_acquisition.ipynb`
4. `04_data_quality_assessment.ipynb`
5. `05_temporal_data_alignment.ipynb`

Important notes:

- All five notebooks are Markdown-only documentary records.
- Illustrative code is explicitly identified as not executed.
- Historical evidence, retrospective reconstruction and unavailable
  evidence are distinguished.
- Raw data remains unchanged.
- Phase 2 acquisition results and Phase 3 findings are report-derived.
- Later repository observations are distinguished from historical
  phase evidence.
- Equity PIT labels are not invented where the Phase 3 report does not
  assign them.
- The FRED/ALFRED training restriction remains in force pending written
  authorisation expressly resolving it.

## Project Documentation

- `MASTER_PROJECT_SPECIFICATION_TRADING_FINAL.md`
- `reports/acquisition/PHASE_3_FINAL_DATA_QUALITY_ASSESSMENT_REPORT.md`
- `reports/phase_6/PHASE_6_FINAL_IMPLEMENTATION_REPORT.md`
- `reports/phase_7/PHASE_7_FINAL_IMPLEMENTATION_REPORT.md`
- `reports/phase_8/PHASE_8_FINAL_IMPLEMENTATION_REPORT.md`
- `notebooks/15_machine_learning_experiments.ipynb`

## Phase 6 — Feature Engineering and Market Regime Detection

The approved Phase 6 notebooks are implemented and were executed against the
existing local market acquisitions on 14 November 2026. Their outputs are
retained in the notebooks:

- `notebooks/10_financial_feature_engineering.ipynb`
- `notebooks/11_cross_asset_and_macroeconomic_feature_engineering.ipynb`
- `notebooks/12_market_regime_detection.ipynb`
- `notebooks/13_target_engineering.ipynb`

The implementation includes reusable calculation modules and tests. The full
repository test suite passed (224 tests). Macroeconomic observations were not
joined to historical daily decisions because point-in-time availability and
vintages remain incomplete or unvalidated. Historical GBp denomination,
corporate-action treatment, feature redundancy, regime sensitivity and target
thresholds remain documented review items.

## Phase 7 — Baseline Forecasting Models

The baseline forecasting research is implemented and executed in
`notebooks/14_baseline_forecasting.ipynb`. It evaluates naive, AR(1), small
financial/cross-asset/regime OLS groups, and historical/GARCH volatility
benchmarks on NG.L, SSE.L, SVT.L and the FTSE 100. Validation is chronological,
uses horizon-based purging, and reserves a final holdout. No macroeconomic
features were used because point-in-time availability and licensing remain
unvalidated.

The selected feature group reduced holdout return MAE in 4 of 12
asset/horizon comparisons, while direction accuracy was lower than the best
naive/AR reference in all 12. GARCH(1,1) had the lowest holdout volatility MAE
for the FTSE 100 across the three horizons, but not for the other assets. These
are baseline research results, not trading or profitability evidence. The
Phase 7 report records the methods, outputs, limitations and tests. The project
owner approved Phase 7 closure on 14 November 2026. Phase 8 development
experiments are implemented and reported; owner review and formal closure are
pending. The previously inspected Phase 7 holdout is not an independent Phase 8
test, and no model is promoted.

## Status

Phases 0–7 are complete and approved. Phase 8 implementation is complete for
research and awaits owner review. Phase 9 is not authorised.
