# Phase 7 — Baseline Forecasting Models

**Project:** AI Quantitative Trading & Strategy Optimisation System  
**Branch:** `phase-7-baseline-forecasting`  
**Report date:** 14 November 2026  
**Status:** COMPLETE AND APPROVED by the project owner on 14 November 2026.

## 1. Scope and evidence

Phase 7 established simple return, direction and volatility forecasting references using the existing approved Phase 6 targets. It did not create trading rules, BUY/SELL signals, position sizing, portfolio optimisation, backtests, broker connections or live trading. No new market or macroeconomic data were downloaded. Raw acquisitions were read without modification.

The executed notebook and outputs are retained in `notebooks/14_baseline_forecasting.ipynb`. Reusable utilities are in `src/forecasting/`. The full repository suite passed: **246 tests passed**. The notebook was executed with Jupyter and saved with outputs; no notebook cell errors remained.

## 2. Inputs and target definitions

The study used the locally acquired Yahoo Finance market data for:

| Asset | Rows | Date range | Missing `Close` | Unit note |
|---|---:|---|---:|---|
| NG.L | 7,890 | 1995-12-11 to 2026-11-02 | 1 | GBp configured; historical denomination validation pending |
| SSE.L | 9,060 | 1991-06-17 to 2026-11-02 | 1 | GBp configured; historical denomination validation pending |
| SVT.L | 9,455 | 1989-12-11 to 2026-11-02 | 1 | GBp configured; historical denomination validation pending |
| FTSE 100 (`^FTSE`) | 11,004 | 1984-01-03 to 2026-11-02 | 184 | Index points |

The notebook calls the existing Phase 6 target builder without changing it:

- Forward simple price return: `Close[t+h] / Close[t] - 1`.
- Direction: the sign of that return with the existing zero neutral band.
- Forward realised volatility: the square root of summed squared one-row future log returns over the horizon, unannualised.

Horizons are 5, 10 and 20 subsequent acquired rows, not verified exchange sessions. Missing values on a target path keep the label missing. Price targets exclude dividends; adjustment and corporate-action semantics remain unvalidated. Targets are not investment total returns.

## 3. Forecast methods

Return references were zero return, expanding training mean, expanding training median, trailing 252 complete training labels, and AR(1) on one-row log returns. For a price-level interpretation, zero return is the no-change price forecast; no separate price-level target was evaluated. AR(1) coefficients are fitted inside the training fold; observed returns at later validation origins update the state without refitting coefficients.

Three pre-specified ordinary least-squares feature groups were evaluated:

- **B — Financial:** one-row return, 5- and 20-row momentum, 20-row realised volatility and 20-row drawdown.
- **BC — Cross-asset:** Group B plus exact-date one-row returns for the other configured assets.
- **BCD — Regime:** Group BC plus one-hot, past-only trend and relative-volatility states.

Features are not selected from full-sample correlations. OLS scaling is estimated inside each training fold; no imputation is performed. Macro features were excluded because historical availability timestamps, vintages and licensing remain unvalidated. FRED/ALFRED data were not used.

For volatility, references were training mean and median of the Phase 6 target, rolling historical volatility scaled to the forecast horizon, and a Gaussian QMLE GARCH(1,1) model. GARCH constrains `alpha + beta < 1`; missing acquired return rows remain in the timeline and are integrated using conditional expected variance.

SciPy 1.18.1 and Statsmodels 0.15.0 were already installed in `.venv` and were added to `requirements.txt` for the reproducible GARCH fit and formal diagnostics. No package was installed during this work.

## 4. Temporal validation and diagnostics

For each asset, the final 20% of acquired rows formed one chronological holdout. Development used expanding walk-forward folds over the first 80%. Each training origin was retained only when its target interval ended no later than the first validation origin. This purges training labels whose future-return path overlaps the validation period. The expanding design never uses post-validation training observations; the additional configurable embargo is available in the split utility but was set to zero beyond horizon purging.

The same complete validation dates were used for return benchmarks and all three feature groups. OLS estimates were fitted separately within each fold. The feature group with lowest pooled development MAE was selected by asset and horizon, then evaluated once on the untouched holdout. Return baselines and the selected group share holdout dates. Volatility methods likewise share dates after requiring a complete recent history for the rolling estimator.

On the initial training prefixes, ADF rejected the unit-root null at `p < 0.001` for all four one-row return series; KPSS did not reject its stationarity null at the 10% reported upper bound. These tests are consistent with stationary returns in those prefixes, but are not proof that the process is stable across all periods. Ljung–Box residual autocorrelation was significant at 10 lags for FTSE and NG.L, but not for SSE.L and SVT.L. ARCH-LM rejected no conditional heteroskedasticity at `p < 0.001` for all four assets, motivating the GARCH benchmark.

Metrics include MAE, MSE, RMSE, forecast bias and directional accuracy, positive-class precision/recall/F1. Confusion matrices and fold-level metrics are saved in the notebook. No probability forecast was generated, so Brier score, log loss and calibration are not applicable.

## 5. Results

### 5.1 Return forecasts on the final holdout

The table reports the percent change in MAE of the development-selected feature group relative to the best naive/AR benchmark on the same holdout dates. Negative values mean lower feature-group MAE.

| Asset | Horizon | Selected group | MAE change vs best naive | Direction accuracy change vs best naive |
|---|---:|---|---:|---:|
| FTSE 100 | 5 | B | -0.28% | -2.49 pp |
| FTSE 100 | 10 | B | -1.65% | -1.39 pp |
| FTSE 100 | 20 | B | -2.36% | -2.52 pp |
| NG.L | 5 | BC | +0.60% | -1.85 pp |
| NG.L | 10 | B | +1.18% | -4.73 pp |
| NG.L | 20 | B | +0.07% | -1.74 pp |
| SSE.L | 5 | B | +1.55% | -5.38 pp |
| SSE.L | 10 | B | +3.60% | -9.73 pp |
| SSE.L | 20 | B | +3.42% | -10.51 pp |
| SVT.L | 5 | B | approximately 0.00% lower | -1.38 pp |
| SVT.L | 10 | B | +1.07% | -4.69 pp |
| SVT.L | 20 | B | +0.46% | -1.77 pp |

The selected feature group reduced holdout MAE in 4 of 12 asset/horizon cases, with small changes for FTSE and SVT.L at five rows. It had higher MAE in the other eight cases. Its directional accuracy was below the best naive/AR benchmark in all 12 cases. Group B was selected in 11 cases and BC once; BCD was never selected. Cross-asset and regime inputs therefore showed no stable incremental benefit in this experiment.

### 5.2 Volatility forecasts on the final holdout

The lowest-MAE volatility reference by asset/horizon was:

| Asset | 5 rows | 10 rows | 20 rows |
|---|---|---|---|
| NG.L | Training median | Training median | Training median |
| SSE.L | Training mean | Training mean | Training mean |
| SVT.L | Training median | Training median | Training median |
| FTSE 100 | GARCH(1,1) | GARCH(1,1) | GARCH(1,1) |

GARCH did not beat the simple mean/median references for NG.L, SSE.L or SVT.L. It had the lowest MAE for FTSE 100 at all three horizons. This asset-specific result is a candidate for further diagnostic research, not evidence of stable or economic value.

### 5.3 Stability and limits of inference

Walk-forward MAE and directional metrics varied between chronological folds. No feature family was a consistent improvement over simple references across assets and horizons. Target overlap still makes adjacent validation errors dependent even after boundary purging. The notebook does not estimate uncertainty intervals or correct for the number of model comparisons; small apparent differences should not be treated as statistically established.

## 6. Limitations and risks carried forward

1. Historical GBp denomination for NG.L, SSE.L and SVT.L remains unvalidated; no conversion was applied.
2. Close-based targets exclude dividends and corporate-action/adjustment semantics remain unresolved.
3. Yahoo Finance remains an exploratory source; commercial-use and redistribution rights are not assumed.
4. Macroeconomic point-in-time availability, vintages and licensing remain unresolved; macro variables were excluded.
5. Feature redundancy and market-regime sensitivity remain relevant. No full-sample feature selection was performed.
6. The sample and fold outcomes span changing market conditions and calendar gaps. No exchange-calendar repair was performed.
7. GARCH is a Gaussian QMLE benchmark with constraints and simple missing-row variance propagation. Distributional adequacy, parameter stability and inferential uncertainty were not established.
8. No economic profitability, strategy performance or trading suitability was assessed.

## 7. Repository changes and quality assurance

- Created `notebooks/14_baseline_forecasting.ipynb` with saved outputs and British English research documentation.
- Created `src/forecasting/validation.py`, `benchmarks.py`, `linear.py`, `metrics.py` and `garch.py`.
- Added 22 tests in `tests/forecasting/` covering split boundaries, purging, embargo, future-data invariance, forecast calculations, metric behaviour, OLS scaling and GARCH constraints/gaps.
- Added SciPy and Statsmodels pins to `requirements.txt`; no installation was run.
- Updated the README, current project status, decision log and risk register.
- No Phase 6 implementation files were edited. No Raw data were changed. No commit, merge or push was made.
- Complete test suite: **246 passed**.

## 8. Recommendation and phase gate

Do not promote the feature-based return models as useful forecasting candidates based on this evidence. Retain zero, historical location and AR(1) returns as reference benchmarks. Retain GARCH(1,1) as an additional volatility reference for FTSE 100 while checking its stability in a separately approved follow-up.

The project owner approved Phase 7 closure on 14 November 2026. No Phase 8 work has started. Any ML/DL phase requires a separate explicit instruction, should pre-register an evaluation criterion, retain the temporal holdout protocol, address the unresolved data risks, and require consistent out-of-sample improvement over these baselines. No profitability threshold is proposed.
