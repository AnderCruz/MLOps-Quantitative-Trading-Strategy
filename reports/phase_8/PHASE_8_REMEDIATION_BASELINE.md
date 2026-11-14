# Phase 8 Technical Remediation — Baseline

**Inspection date:** 14 November 2026  
**Repository:** `/home/anderjcruz/projects/Quantitative-Trading-Strategy`  
**Branch:** `phase-7-baseline-forecasting`  
**HEAD:** `2e91c6c678d68ab4cb22b646360ac41c11e5e30a`

## Initial repository state

`git status --short --untracked-files=all` was empty. The working tree was clean before remediation. No files were changed or discarded during baseline inspection.

The repository contains the Phase 8 notebook, implementation report, forecasting modules, tests and development CSV outputs. No GitHub Actions workflow, `pyproject.toml`, `setup.cfg`, `tox.ini` or separate development requirements file was present. `requirements.txt` is the sole dependency declaration.

## Baseline tests

Command: `./.venv/bin/python -m pytest -q`  
Result: **256 passed, 0 failed, 1 warning in 6.12 seconds**.

The warning is an MLflow/SQLAlchemy `SADeprecationWarning` for the deprecated `noload` loader strategy, emitted by `tests/forecasting/test_mlflow_tracking.py` during mapper setup.

## Environment and dependencies

The active project environment reported Python 3.12.3 and:

| Package | Declared | Installed |
|---|---:|---:|
| NumPy | Not explicitly declared | 2.5.4 |
| pandas | 3.1.0 | 3.1.1 |
| SciPy | 1.18.1 | 1.18.1 |
| statsmodels | 0.15.0 | 0.15.0 |
| scikit-learn | 1.9.1 | 1.9.1 |
| MLflow | 3.16.1 | 3.16.1 |
| PyArrow | 25.0.1 | 25.0.1 |
| pytest | Not explicitly declared | 9.2.0 |

Thus the declared pandas pin does not match the environment used for the baseline test run, and NumPy/pytest are transitive or environment-only rather than explicitly declared. Clean-environment installation and `pip check` had not yet been recorded at baseline.

## Existing Phase 8 outputs and tracking

Under `reports/phase_8/development_results/` the repository contains `metrics.csv` (180 rows), `fold_metrics.csv` (720), `comparisons.csv` (792), `feature_importance.csv` (3,888) and `predictions.csv` (501,060). `predictions.csv` has 13 columns and the model counts are 200,424 Ridge, 200,424 Random Forest regression and 100,212 Random Forest classifier records. The classifier has **100,212 missing `acquired_position` values**; the regression records have none. The composite key `(date, fold, asset, horizon, target, feature_group, model)` had no duplicates in the initial file.

The local SQLite MLflow store at `data/mlflow/mlflow.db` contains active experiment `phase_8_machine_learning_experiments_gap_aware` (ID 4) with 184 runs. It is local tracking data and is not part of the remediation source changes.

## Known problems verified at baseline

1. No CI workflow exists.
2. The installed pandas version (3.1.1) differs from the declared 3.1.0; NumPy and pytest lack explicit project declarations.
3. Classifier prediction rows have missing acquired-timeline positions.
4. The existing Phase 8 report describes development evidence and unadjusted multiple comparisons; it does not establish an independent holdout or model promotion.
5. The baseline full test suite passes, but its MLflow deprecation warning remains.

This report records the state before remediation changes. It does not assert that any remediation acceptance criterion has been met.
