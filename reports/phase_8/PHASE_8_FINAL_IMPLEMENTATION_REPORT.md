# Phase 8 — Machine Learning Experiments

**Project:** AI Quantitative Trading & Strategy Optimisation System  
**Report date:** 14 November 2026  
**Status:** IMPLEMENTED FOR RESEARCH — AWAITING PROJECT-OWNER REVIEW  
**Scope:** Traditional Machine Learning forecasting; development walk-forward evidence only.

## 1. Executive findings

Phase 8 implemented and executed Ridge regression, Random Forest regression and a Random Forest direction classifier for NG.L, SSE.L, SVT.L and FTSE 100. The study reused the Phase 6 targets and the Phase 7 B, BC and BCD feature groups. It did not change any Phase 7 result or use the previously inspected Phase 7 holdout as an independent Phase 8 test.

- No return model established consistent incremental value over the Phase 7 statistical references. Mean configuration-level out-of-sample R² relative to the fold-specific expanding-mean forecast was negative for Ridge (-0.014) and Random Forest (-0.040).
- Direction classification was weak. Mean accuracy was 0.487, below the training-majority reference accuracy of 0.543. Mean balanced accuracy was 0.376 and positive-versus-rest ROC-AUC was 0.510.
- Ridge and Random Forest produced lower walk-forward volatility MAE than several statistical references in many of the evaluated asset/horizon/group cases. These development results are a candidate for further confirmation, not a promotion decision: the final independent evaluation period is not yet available, intervals are unadjusted for the many comparisons, and known data risks remain open.
- No model is promoted as useful for trading or investment decisions. No profitability conclusion is made.

The notebook completed without cell errors. The full repository test suite passed **256 tests**. MLflow recorded 184 finished runs in the final experiment.

## 2. Research objectives and scope

The experiments compared traditional ML forecasts on the approved return, direction and cumulative realised-volatility targets. They assessed asset, horizon, chronological-fold and feature-group behaviour; logged model and dataset metadata; and compared outcomes with Phase 7 statistical references.

No trading signal, BUY/SELL/HOLD rule, position size, portfolio optimisation, risk engine, trading backtest, execution simulation, broker integration, live trading, deep learning, new data acquisition or macroeconomic feature use was introduced. Raw acquisitions were read-only.

## 3. Data, targets and features

The notebook reads exactly one local Parquet acquisition per configured asset and records the corresponding acquisition identifier:

| Asset | Acquisition identifier | Rows in Phase 7 inventory | Observation end |
|---|---|---:|---|
| NG.L | `20261103T000455Z_8b505769` | 7,890 | 2026-11-02 |
| SSE.L | `20261103T002507Z_de101edb` | 9,060 | 2026-11-02 |
| SVT.L | `20261103T002515Z_fdac38df` | 9,455 | 2026-11-02 |
| ^FTSE | `20261103T002524Z_9c7eb120` | 11,004 | 2026-11-02 |

The study uses the existing horizons of 5, 10 and 20 subsequent acquired rows and the existing target definitions without modification:

- Forward simple price return: `Close[t+h] / Close[t] - 1`.
- Direction: the existing sign label with the zero neutral band.
- Forward realised volatility: square root of summed squared one-row future log returns, unannualised.

These are acquired-row horizons, not independently verified exchange sessions. Close-based targets exclude dividends and are not total investment returns.

Feature groups exactly follow the small Phase 7 sets:

- **B:** five financial features: one-row return, 5- and 20-row momentum, 20-row realised volatility and 20-row drawdown.
- **BC:** Group B plus exact-date one-row returns for the other configured assets.
- **BCD:** Group BC plus the existing past-only trend and relative-volatility regime indicators.

For each asset/target comparison, model groups share common complete forecast dates. Missing acquired rows are retained in the timeline for horizon purging and are not compressed. No macroeconomic series, FRED or ALFRED data were used. No full-sample feature selection was performed.

## 4. Models and configurations

### Included

| Model | Configuration | Rationale |
|---|---|---|
| Ridge regression | StandardScaler inside each training fold; `alpha=1.0`; seed 42 | Regularises redundant correlated financial inputs with low computational cost and stable fitting. |
| Random Forest Regressor | 200 trees; `max_features=0.5`; `min_samples_leaf=20`; seed 42; one worker | Provides a bounded non-linear tree comparison without scaling. Minimum leaf size limits very small local partitions. |
| Random Forest Classifier | Same tree settings; `class_weight="balanced"`; seed 42 | Tests direction classification while preserving the existing -1/0/+1 labels and the rare neutral class. |

Parameters were fixed before the main walk-forward run. A limited development-only sensitivity check on NG.L, Group B, horizon 10 compared Ridge alpha 0.1/1/10 and Random Forest minimum leaf sizes 10/20/40. It was not used to select a final model.

### Excluded

- Lasso and Elastic Net were deferred because the Phase 6/7 feature set already has substantial redundancy and an additional sparsity search could increase selection instability without a demonstrated need.
- XGBoost and LightGBM were excluded from this first controlled study because they were absent from the environment and would add separate dependencies and tuning complexity without established incremental value.
- Deep learning remains outside Phase 8 scope.

## 5. Temporal validation and holdout policy

Each asset timeline uses expanding walk-forward validation with a 70% initial training window and validation blocks of approximately 7.5% of the acquired rows. The existing split utility purges training origins whose target endpoint overlaps the first validation origin. No random split is used, and transformations are fitted only on training data. The same common complete dates are used for B, BC and BCD comparisons.

No extra embargo beyond horizon purging was used. Fold metrics are reported separately. Paired MAE uncertainty uses 500 block-bootstrap replications, block length equal to the target horizon in acquired-row positions, with blocks sampled separately within each fold. This respects gaps and avoids treating validation rows from different folds as one continuous block.

The Phase 7 final holdout was already inspected. It was not reused or relabelled as an independent Phase 8 test. Current results cover development walk-forward folds only. A genuinely independent final evaluation requires future observations collected after research choices are frozen, then evaluated once under a recorded protocol. That future data were not acquired in this phase.

The block-bootstrap intervals are **unadjusted** for multiple comparisons across models, assets, horizons, targets and feature groups. They are descriptive evidence and do not establish statistical significance.

## 6. Results

### 6.1 Aggregate development metrics

The following are unweighted means over 36 model/asset/horizon/feature-group configurations per model and target. They are descriptive summaries across different assets and targets.

| Target | Model | Mean MAE | Mean RMSE | Mean forecast bias | Mean OOS R² vs expanding mean |
|---|---|---:|---:|---:|---:|
| Return | Ridge | 0.0298 | 0.0399 | 0.0002 | -0.014 |
| Return | Random Forest | 0.0302 | 0.0404 | 0.0001 | -0.040 |
| Volatility | Ridge | 0.0125 | 0.0185 | 0.0015 | 0.215 |
| Volatility | Random Forest | 0.0127 | 0.0188 | 0.0014 | 0.197 |

Negative return OOS R² means the model had greater squared error than the expanding-mean reference on average. Volatility OOS R² is relative to the expanding-mean volatility forecast and does not itself establish reliable economic value.

### 6.2 Return comparisons against Phase 7 references

Across 36 configurations per model/benchmark comparison:

| Model | Benchmark | Lower MAE cases | Mean paired MAE difference (model − benchmark) |
|---|---|---:|---:|
| Ridge | Zero return | 14/36 | +0.00009 |
| Ridge | Expanding mean | 7/36 | +0.00023 |
| Ridge | Expanding median | 9/36 | +0.00020 |
| Ridge | Trailing 252-label mean | 26/36 | -0.00056 |
| Ridge | Adjacent-pair AR(1) | 8/36 | +0.00022 |
| Random Forest | Zero return | 2/36 | +0.00053 |
| Random Forest | Expanding mean | 0/36 | +0.00067 |
| Random Forest | Expanding median | 2/36 | +0.00065 |
| Random Forest | Trailing 252-label mean | 18/36 | -0.00012 |
| Random Forest | Adjacent-pair AR(1) | 0/36 | +0.00066 |

Ridge most often beat the trailing 252-label mean, but did not consistently beat the other references. The average MAE advantage over the trailing mean was small. Random Forest generally did not improve on the return references. This does not demonstrate stable incremental return-forecast value.

The adjacent-pair AR(1) comparison in Phase 8 uses only pairs adjacent on the acquired-row timeline; it does not compress missing observations. The potential `dropna()` gap-handling defect in the approved Phase 7 AR(1) implementation was reviewed and remains unmodified. Phase 7 results remain unchanged; any correction to that implementation requires separate owner review.

### 6.3 Volatility comparisons

Across 36 configurations per model/benchmark comparison, Ridge had lower MAE than GARCH in 34 cases and Random Forest in 31. Ridge and Random Forest also usually improved on rolling historical volatility and expanding mean, while their results versus the expanding median were less consistent. Mean paired MAE differences versus GARCH were -0.0018 for Ridge and -0.0016 for Random Forest.

This is a potentially useful development finding to verify prospectively. It differs in evaluation design from Phase 7's single final holdout, where GARCH had the lowest volatility MAE for FTSE 100 at all three horizons but not for the three individual equities. Neither result supersedes the other: the Phase 8 walk-forward outputs are development evidence, and a new independent period is required before promotion.

### 6.4 Direction classification

The average Random Forest results across 36 configurations were:

| Accuracy | Balanced accuracy | Macro F1 | Positive-vs-rest ROC-AUC | Positive-vs-rest PR-AUC |
|---:|---:|---:|---:|---:|
| 0.487 | 0.376 | 0.331 | 0.510 | 0.552 |

The training-majority baseline accuracy averaged 0.543. The zero-return forecast, interpreted as a neutral direction prediction, averaged 0.003 accuracy because the exact-zero neutral class was rare: its observed share was 0% for FTSE 100 and roughly 0.3–0.5% for the individual equities. The target was preserved unchanged; no class thresholds were modified. Fold results and 3×3 confusion matrices are retained in the metric outputs.

The classifier did not beat the majority baseline on average and did not establish useful directional classification value.

### 6.5 Feature groups, stability and importance

Return MAE averages were similar for B and BC under Ridge (0.02973 each) and slightly worse for BCD (0.02988). Random Forest return MAE averaged 0.03022 for B, 0.03017 for BC and 0.03029 for BCD. There is no stable cross-asset or regime-feature advantage for returns.

For volatility, BC had the lowest pooled mean MAE for both Ridge (0.01243) and Random Forest (0.01259), but differences among B, BC and BCD were modest and varied by asset and horizon. This does not establish a robust incremental cross-asset benefit.

Across chronological folds, metrics varied by period and asset. Direction fold balanced accuracy averaged 0.398; its asset-level means ranged from 0.339 for NG.L to 0.537 for FTSE 100. No single result is stable enough across assets, targets and horizons to justify promoting a model.

Random Forest impurity importance most often ranked the 20-row realised-volatility feature highly, followed by momentum and drawdown features. Cross-asset returns and regime variables had lower average importance in most target/group summaries. Impurity importance can be distorted by correlated predictors; it is descriptive only and was not used for selection.

### 6.6 Parameter sensitivity

In the NG.L Group B, 10-row return sensitivity check, Ridge MAE was 0.029739 for alpha 0.1 and 0.029738 for alpha 10. Random Forest MAE was 0.030861 for minimum leaf size 10 and 0.030269 for size 40; the primary size 20 result is in the main model table. This narrow comparison shows Ridge error was insensitive to these two regularisation settings in that case, while the tree result moved with leaf size. It is not a broad tuning study and was not used for final selection.

## 7. MLflow and reproducibility

The canonical experiment is **`phase_8_machine_learning_experiments_gap_aware`**, experiment ID **4** in the local tracking database. It contains **184 FINISHED runs**: 180 primary model configurations and four parameter-sensitivity configurations. Representative NG.L Group B, horizon 10 models retain model artifacts; all runs record fold predictions and metrics.

Tracking uses the local SQLite database at `data/mlflow/mlflow.db` and artifacts under `data/mlflow/artifacts/`. The directory is excluded from Git. No remote tracking service is used. The 180 primary runs record model family, asset, horizon, target, feature group, dataset identifier, available-data and validation dates, feature-column hash, parameters, seed, software versions, validation predictions and metrics. The four sensitivity runs record their pilot asset, horizon, target, feature group, parameters, seed, predictions and metrics. Models saved from a development fold are research artifacts, not deployable selected models.

The principal reproducible files are:

- `notebooks/15_machine_learning_experiments.ipynb` — executed notebook with saved outputs and no cell errors.
- The notebook includes summary scorecards plus figures for horizon-level MAE, chronological fold stability and asset-level direction confusion matrices.
- `reports/phase_8/development_results/metrics.csv` — pooled metrics and MLflow run IDs.
- `reports/phase_8/development_results/fold_metrics.csv` — per-fold regression and direction metrics.
- `reports/phase_8/development_results/comparisons.csv` — paired reference comparisons and block-bootstrap intervals.
- `reports/phase_8/development_results/feature_importance.csv` — fold-level Random Forest importance.
- `reports/phase_8/development_results/predictions.csv` — fold-level predictions (approximately 50 MB).

The local `.venv` versions at execution were Python 3.12.3, pandas 3.1.1, NumPy 2.5.4, SciPy 1.18.1, Statsmodels 0.15.0, scikit-learn 1.9.1, MLflow 3.16.1, PyArrow 25.0.1, pytest 9.2.0 and JupyterLab 4.6.5. `requirements.txt` pins pandas 3.1.0 while the existing environment has 3.1.1; this pre-existing environment/pin mismatch remains visible and was not resolved by an automatic upgrade.

MLflow 3.16.1 requires PyArrow below 26, so the project pin was changed from 26.0.0 to 25.0.1 to make the declared environment coherent. This compatible local version passed the complete test suite. scikit-learn 1.9.1 and MLflow 3.16.1 were added as direct pins. MLflow emits one SQLAlchemy deprecation warning during its tracking test; no test failed.

Earlier implementation attempts are retained in separate local MLflow experiment names for audit. Only the `..._gap_aware` experiment is the final corrected run used by this report.

## 8. Tests and quality assurance

The complete repository test suite passed: **256 passed, 1 warning**. This includes the existing tests and ten new Phase 8 forecasting tests for Ridge validation, walk-forward chronology, Random Forest regression/classification, common-date masks, metrics, block-bootstrap reproducibility and local MLflow configuration.

The Phase 8 notebook executed successfully with no cell errors. `pip check` reported no broken installed requirements. No new market data were downloaded, no Raw files were modified and no approved Phase 7 code or results were changed.

## 9. Open risks and limitations

- A genuinely independent future evaluation period remains unavailable; do not treat the Phase 7 holdout or these development folds as a final Phase 8 test.
- The nominal 95% block-bootstrap intervals are not corrected for multiple testing. They should not be treated as confirmatory significance tests.
- Adjacent validation forecast errors can remain dependent. Block resampling accounts for horizon overlap approximately but does not remove all serial dependence or regime effects.
- Equity historical GBp denomination, corporate-action and price-adjustment semantics remain unvalidated. FTSE 100 is an index in points.
- Close-based price returns omit dividends. Yahoo Finance licensing and commercial-use restrictions remain open.
- Feature redundancy and regime sensitivity remain open; impurity importance is not causal or a selection rule.
- Macro point-in-time availability, historical vintages and licensing remain unresolved. FRED/ALFRED restrictions remain in force.
- The Phase 7 AR(1) missing-observation handling issue remains open for owner review; the Phase 7 source was not modified.
- The current pandas environment version differs from the declared requirements pin.

No risk is closed by this report.

## 10. Research conclusion and recommendation

The current evidence does not justify promoting ML return or direction models. Ridge and Random Forest volatility forecasts show a stronger development signal relative to several Phase 7 references, but this remains provisional and is not a trading result. Keep the Phase 7 findings intact and retain all Phase 8 outputs as development evidence.

Before any model promotion, freeze the evaluation protocol and obtain a genuinely future evaluation period. Review the AR(1) gap issue separately before changing Phase 7. No Phase 9 work is authorised by this report; it requires separate explicit owner approval.

**Phase 8 implementation status:** complete for research and awaiting project-owner review. **Phase 8 closure approval:** not recorded here.
