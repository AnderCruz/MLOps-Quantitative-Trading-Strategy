# Phase 8 Technical Remediation Report

**Report date:** 14 November 2026  
**Repository:** `/home/anderjcruz/projects/Quantitative-Trading-Strategy`  
**Branch:** `phase-7-baseline-forecasting`  
**Baseline commit:** `2e91c6c678d68ab4cb22b646360ac41c11e5e30a`  
**Status:** TECHNICAL REMEDIATION PARTIALLY COMPLETE — hosted CI run pending; Phase 8 owner approval not recorded.

## 1. Executive summary

The Phase 8 audit was completed against a clean working tree before changes. It verified 256 passing baseline tests, no existing CI workflow, a pandas pin mismatch, and 100,212 missing acquired-row positions in classifier predictions. Remediation added GitHub Actions CI, locked the Python 3.12 test environment, strengthened temporal and model checks, repaired the prediction artefact from the existing local acquisitions, and expanded MLflow provenance. The updated notebook was executed using the local data only. No Phase 6/7 source or approved output, original acquisition, strategy, broker integration or live-trading functionality was changed.

Local validation passes: **273 tests passed, 0 failed, 1 warning**; `pip check` is clean; all 501,060 predictions have complete temporal identity; all 368 runs in the canonical local MLflow experiment are finished and have traceability metadata. The GitHub Actions YAML and local equivalent steps were checked. A hosted workflow run could not be produced without pushing or dispatching to GitHub, and neither was authorised. That external CI result remains outstanding, so this report classifies remediation as partially complete. This is not a Phase 8 closure approval.

## 2. Baseline findings

See [`PHASE_8_REMEDIATION_BASELINE.md`](PHASE_8_REMEDIATION_BASELINE.md) for the full before-change record. The baseline was branch `phase-7-baseline-forecasting`, commit `2e91c6c678d68ab4cb22b646360ac41c11e5e30a`, with a clean Git status. The original suite passed 256 tests in 6.12 seconds, with one MLflow/SQLAlchemy `SADeprecationWarning`.

Verified gaps were: no workflow or development dependency file; declared pandas 3.1.0 versus installed 3.1.1; NumPy and pytest not explicitly represented in the direct dependency declaration; and missing `acquired_position` for every classifier prediction. The local MLflow SQLite store had 184 finished runs in experiment ID 4. Phase 8 results were already development evidence, not an independent holdout.

## 3. Changes implemented

### 3.1 GitHub Actions CI

Added `.github/workflows/phase-8-ci.yml`. It runs on pushes to `main`, `develop`, `phase-*` and `feature/**`, pull requests targeting `main`, and manual dispatch. It uses Python 3.12, pip caching, the exact development lock, `pip check`, the complete pytest suite and a GitHub job summary with passed/failed/error/skipped counts. Workflow permissions are limited to `contents: read`; no secrets or remote service are required. The workflow uses versioned `actions/checkout@v7` and `actions/setup-python@v7`.

The workflow file was parsed and its triggers, Python version, test step and summary step were inspected locally. The same clean-environment install, dependency check and complete suite succeeded locally. `actionlint` could not start because the available snap wrapper lacked the `cap_dac_override` capability; YAML parsing and structural checks succeeded with PyYAML. The GitHub-hosted workflow itself has not run because this task prohibited commits and pushes. The workflow and run instructions are documented in [`docs/PHASE_8_CI.md`](../../docs/PHASE_8_CI.md).

### 3.2 Dependency and environment reproducibility

- Aligned `pandas` in `requirements.txt` to 3.1.1.
- Added explicit `numpy==2.5.4`.
- Kept the compatible `mlflow==3.16.1` and `pyarrow==25.0.1` pair.
- Added `requirements-lock.txt`, a 107-package exact environment lock generated after installing the declared stack into a clean Python 3.12 virtual environment. `requirements-dev.txt` points to this lock, including `pytest==9.2.0`.
- Documented runtime versus locked test dependencies and setup commands in the README and CI guide.

A second new virtual environment installed `requirements-dev.txt` from scratch. It reported **Python 3.12.3**, NumPy 2.5.4, pandas 3.1.1, SciPy 1.18.1, statsmodels 0.15.0, scikit-learn 1.9.1, MLflow 3.16.1, PyArrow 25.0.1 and pytest 9.2.0. `pip check` reported no broken requirements.

### 3.3 Prediction artefact and temporal identity

The classifier branch previously bypassed the acquired-position assignment used by regressors. The experiment runner now attaches the exact original acquired-index position to every model prediction before metrics, MLflow logging or export. New `prediction_artifacts.py` checks required fields, unique keys, finite values, valid horizon/target/model combinations, chronological within-fold ordering, date-position correspondence, consistent fold and actual values, feature-group origin parity, and finite, bounded, unit-sum classifier probabilities.

`predictions.csv` was rebuilt from the existing local Parquet acquisitions and corrected implementation. No market data was fetched and no value was fabricated. Final validation found:

| Model | Rows |
|---|---:|
| Ridge | 200,424 |
| Random Forest regression | 200,424 |
| Random Forest classifier | 100,212 |
| **Total** | **501,060** |

All 501,060 rows have an acquired position. Composite prediction keys are unique. Every recorded date maps to the exact row on that asset's acquired timeline. Paired actual targets, folds and common forecast origins agree across models and feature groups. The final schema retains the date, fold, target, model, feature group, asset, horizon and forecast/probability fields.

### 3.4 Temporal validation and leakage checks

The approved chronological expanding windows, horizon purge and zero neutral-band target definitions are unchanged. Added coverage for multiple purge horizons and inclusive boundaries, missing acquired-row positions without timeline compression, and a future-price mutation check showing that Phase 8 B/BC/BCD features at earlier dates remain unchanged. Existing feature and regime tests also verify future-data invariance; target tests cover forward return, direction, future realised volatility, missing paths, invalid prices, duplicate dates and non-chronological indexes. Walk-forward inputs retain the full acquired index before incomplete rows are filtered.

Training-only preprocessing remains inside the fold-specific estimator pipeline. A Ridge helper defect that returned the same estimator object for every fold was corrected so each fold gets a newly built estimator. A dedicated test checks distinct fold estimators.

### 3.5 Model implementation

Ridge standardisation stays within each training fold. Random Forest configurations and seed 42 remain unchanged. Classifier targets are restricted to the approved `-1, 0, +1` labels. Probabilities are mapped by the fitted model's actual class labels; absent classes receive zero rather than shifting probability columns. The mapped probability vector is checked for finite values and a unit sum. A one-class training-fold test confirms the mapping.

### 3.6 Direction class distribution

Added [`DIRECTION_CLASS_DISTRIBUTION_NOTE.md`](DIRECTION_CLASS_DISTRIBUTION_NOTE.md) and `development_results/class_distribution.csv`, with counts and shares for each asset/horizon/fold. Among 33,404 unique development forecast origins, 15,158 labels are negative (45.38%), 85 neutral (0.25%), and 18,161 positive (54.37%). Neutral labels are absent from 18 of 48 asset/horizon/fold strata. The zero neutral band is preserved; the note explains why per-fold class prevalence, balanced metrics and confusion matrices remain necessary.

### 3.7 Benchmarks and statistical inference

Added [`BENCHMARK_AND_INFERENCE_AUDIT.md`](BENCHMARK_AND_INFERENCE_AUDIT.md). Phase 8 paired comparisons are date-aligned and use common actuals, folds and feature-group origins. The Phase 8 AR(1) reference forms lag pairs only from adjacent finite acquired observations.

The separate Phase 7 benchmark helper still applies `dropna()` before forming lag pairs. With missing observations this can pair non-adjacent acquired rows. That issue and a separately approved correction/review procedure are documented; no Phase 7 code, notebook or approved result was modified.

Metric validation now rejects duplicate benchmark dates and incomplete fold/acquired-position identity, and consistently excludes non-finite paired triples. The existing 500-replication, horizon-length block bootstrap continues to sample separately by fold with a fixed seed. The output contains 792 comparison rows. Intervals remain unadjusted for the large comparison family and are explicitly descriptive, not confirmatory significance. Future confirmation should pre-specify primary hypotheses and consider Holm or false-discovery adjustment on a genuinely future one-time evaluation.

### 3.8 MLflow traceability

Local SQLite and local artifact storage are retained; no remote tracker or sensitive upload was added. Each canonical run now records, where applicable, model and seed, asset/horizon/target/feature group, dataset identifier and date range, training and validation date ranges per fold, feature names and value hashes, Git revision and working-tree state, Python and dependency versions, metrics, predictions and existing model artifacts.

The notebook rerun added 184 runs to experiment ID 4. The earlier 184 runs were reconciled with provenance metadata using the same local feature/target construction and their saved prediction dates; no model was retrained for that metadata reconciliation. A separate process-restart test verifies recovery of the experiment and persistence of parameters, a metric and an artifact. Final audit found **368/368 runs FINISHED**, with no missing checked commit, feature-value hash, dataset ID, horizon, target definition, Python/NumPy/pandas tags, dirty-state tag or `fold_periods.json` artifact.

### 3.9 Data and licensing governance

Added `RISK-08-07` to the risk register. Yahoo Finance historical equity licensing and commercial model-training rights remain unverified. Historical GBp, corporate-action and price-adjustment semantics remain open. No macroeconomic features were introduced; FRED/ALFRED training restrictions remain in force. Macroeconomic point-in-time availability, vintages, publication delays and licensing remain unresolved.

## 4. Notebook execution evidence

The full `notebooks/15_machine_learning_experiments.ipynb` run used Python 3.12.3, JupyterLab 4.6.5 and nbclient 0.11.0. It ran against the four configured local Parquet acquisitions and completed all 13 code cells with **zero cell errors**, regenerated the development CSVs, and produced the tables and figures. An original notebook copy was retained at `/tmp/phase8-notebook-before-remediation.ipynb` before the run.

After the full run, only the sensitivity cell's MLflow metadata logging was expanded. That exact current cell was executed separately with its local import/data-preparation cells and an isolated temporary SQLite store; it completed without errors and its outputs were saved back to the notebook. This avoided a second full model sweep while verifying the updated sensitivity logging. The cell's metrics and modelling configuration were not changed.

## 5. Test and validation results

Baseline: **256 passed, 0 failed, 1 warning**.  
Final clean locked environment: **273 passed, 0 failed, 1 warning in 8.03 seconds**.  
`pip check`: **No broken requirements found**.  
Workflow YAML: parsed; expected event filters and test job confirmed.  
Prediction artefact: **501,060 rows; 0 missing positions; 0 duplicate keys**.  
MLflow: **368 finished runs; 0 checked runs missing required traceability fields/artifacts**.  
Notebook full run: **13 code cells; 0 cell errors**. The updated sensitivity cell's isolated run also completed with 0 errors.

The single remaining test warning is MLflow/SQLAlchemy's `SADeprecationWarning` for SQLAlchemy's deprecated `noload` loader during MLflow mapper setup. It does not fail a test and originates in MLflow's tracking internals.

The hosted Actions workflow could not be run without a GitHub-side dispatch or push. No push, commit, merge or remote action was performed.

## 6. Files changed

Created:

- `.github/workflows/phase-8-ci.yml`
- `docs/PHASE_8_CI.md`
- `requirements-dev.txt`, `requirements-lock.txt`
- `src/forecasting/prediction_artifacts.py`
- `tests/forecasting/test_prediction_artifacts.py`
- `reports/phase_8/PHASE_8_REMEDIATION_BASELINE.md`
- `reports/phase_8/PHASE_8_TECHNICAL_REMEDIATION_REPORT.md`
- `reports/phase_8/DIRECTION_CLASS_DISTRIBUTION_NOTE.md`
- `reports/phase_8/BENCHMARK_AND_INFERENCE_AUDIT.md`
- `reports/phase_8/development_results/class_distribution.csv`

Modified:

- `requirements.txt`, `README.md`, `docs/DECISION_LOG.md`, `docs/RISK_REGISTER.md`
- `src/forecasting/ml_experiments.py`, `src/forecasting/ml_models.py`, `src/forecasting/ml_metrics.py`
- `tests/forecasting/test_ml_data.py`, `test_ml_metrics.py`, `test_ml_walk_forward.py`, `test_mlflow_tracking.py`, `test_validation.py`
- `reports/phase_8/PHASE_8_FINAL_IMPLEMENTATION_REPORT.md`
- `reports/phase_8/development_results/predictions.csv`
- `notebooks/15_machine_learning_experiments.ipynb`

Deliberately not modified: `src/targets.py`, `src/forecasting/validation.py` implementation, Phase 6/7 code and approved outputs, original Raw acquisitions, FRED/ALFRED data, model families/configurations, target threshold, trading strategy/execution code and Phase 9 scope.

## 7. Remaining risks and decisions

- Obtain a hosted GitHub Actions run after the project owner chooses an authorised GitHub-side dispatch or push. No commit or push was made during remediation.
- Preserve Phase 8 as development evidence; no independent evaluation period exists. Do not reuse the inspected Phase 7 holdout.
- Keep unadjusted bootstrap intervals descriptive. Pre-register a small primary hypothesis family and multiplicity treatment before future confirmation.
- Resolve Yahoo Finance commercial-use rights and point-in-time macro-data/licensing questions before expanding the research data set.
- Review the Phase 7 AR(1) missing-row issue separately; an owner decision is required before changing approved Phase 7 code or findings.
- The MLflow SQLAlchemy deprecation warning remains upstream of project code.
- Formal Phase 8 owner approval and closure remain outstanding.

## 8. Future independent evaluation protocol

Before acquiring or inspecting a final evaluation period, freeze and record the feature set, Phase 6 target definitions and thresholds, model families and parameters, walk-forward/purge methodology, primary metrics, benchmark set, missing-data policy, primary hypotheses and multiple-comparison treatment. Define a future period not previously inspected, evaluate it once, retain the run and predictions with source/data hashes, and prohibit tuning against its outcomes. If the result prompts a model change, that period becomes development evidence and a later untouched evaluation period is required.

## 9. Recommendation

The code, local environment, prediction traceability, notebook and research documentation are technically remediated and pass local checks. Keep the project classified as **TECHNICAL REMEDIATION PARTIALLY COMPLETE** until the GitHub-hosted workflow has a successful run. Do not declare Phase 8 formally approved or closed; obtain explicit owner review and approval after the hosted CI result is available. Phase 9 remains unauthorised.
