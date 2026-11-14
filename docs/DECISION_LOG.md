# Decision Log
## AI Quantitative Trading & Strategy Optimisation System

**Document status:** Active
**Project phase:** Phase 8 — Machine Learning Experiments (implementation complete; owner review pending)
**Last updated:** 14 November 2026

---

## 1. Purpose

This document records confirmed architectural, technical, data governance and project-scope decisions.

It is intended to provide an auditable record of decisions that influence the system's design and implementation.

Historical decisions D01–D129 were approved during previous project discussions. Their complete individual descriptions are not reconstructed here because the full original decision records are not available in this document. The approved decisions remain part of the project's decision history.

---

## 2. Project Scope and Governance

### 2.1 Multi-Asset Architecture

**Decision:** The system must support multiple assets and providers from its initial architecture.

**Rationale:**
- Avoid an architecture tied exclusively to National Grid.
- Support future asset classes and instruments.
- Separate asset configuration from acquisition implementation.
- Allow independent provider connectors.

**Implementation principle:** National Grid (`NG.L`) is the initial pilot asset, not a hard-coded system dependency.

### 2.2 Initial Trading Scope

**Decision:** The initial research scope is daily-frequency, long-only swing trading, with GBP as the base currency and hypothetical starting capital of £1,000.

**Restrictions:**
- Research, backtesting and paper trading only.
- No live trading or broker integration.
- No leverage, derivatives or short selling without explicit approval.
- Paper trading is mandatory before any discussion of live trading.

### 2.3 FRED/ALFRED Usage Restriction

**Decision:** FRED/ALFRED data must not be used to train project models without written authorisation that expressly resolves the relevant restriction.

**Future review:** Reassess this decision at the end of the project, when the commercialisation question is evaluated.

---

## 3. Data Sources and Licensing

### 3.1 Yahoo Finance

**Decision:** Yahoo Finance is conditionally accepted for exploratory research and historical market-data acquisition.

**Restrictions and caveats:**
- It is accessed through an unofficial interface.
- No redistribution or commercial-use rights are assumed.
- Licensing and terms must be reviewed before any commercial use.
- Provider metadata and configured assumptions must not be represented as independently verified facts.

### 3.2 Source-Level Licensing

**Decision:** Licensing and permitted usage must be assessed at dataset/provider level.

The presence of an accessible API or downloadable dataset does not automatically establish permission for commercial use, redistribution or model training.

---

## 4. Data Acquisition Architecture

The following architectural decisions were approved for Phase 2.2.7.

### 4.1 Provider-Independent Design

- Use modular, provider-independent acquisition components.
- Implement independent provider connectors using an adapter pattern.
- Keep acquisition pipelines separate from downstream processing pipelines.
- Avoid provider-specific assumptions in shared acquisition logic.

### 4.2 Configuration Management

- Store asset and acquisition settings in external YAML configuration files.
- Validate configuration using Pydantic.
- Support global, asset, provider, dataset and environment-level configuration.
- Validate configuration before acquisition starts.
- Record the configuration version or hash in acquisition metadata.
- Store credentials in environment variables; never commit secrets.

### 4.3 Acquisition Modes

The architecture must support:
- Full historical acquisition.
- Fixed date-range acquisition.
- Incremental acquisition.

Incremental acquisition must use independent dataset watermarks. A watermark advances only after successful validation and commit.

### 4.4 Raw Data Immutability

**Decision:** Raw acquisitions are immutable.

- Never overwrite an existing Raw acquisition.
- Store each acquisition as a separately identifiable version.
- Use controlled reruns with an `acquisition_id`.
- Store files in temporary locations before validation and commit.
- Validate files and calculate SHA-256 checksums before atomic commit.
- Preserve revised source data as new versions.

### 4.5 Reliability and Failure Handling

- Classify errors as transient, permanent or investigation-required.
- Use configurable retries, exponential backoff and jitter.
- Respect provider rate limits and `Retry-After` instructions.
- Support provider-specific circuit breakers.
- Isolate provider failures so one provider does not automatically stop unrelated acquisitions.
- Use normalised acquisition statuses, including success, warnings, valid empty, incomplete and failed/rejected.

### 4.6 Data Integrity and Idempotency

- Use dataset-specific logical keys and idempotency rules.
- Maintain temporal continuity checks appropriate to each dataset.
- Reconcile acquisitions deterministically.
- Keep historical backfills separately traceable.
- Record file sizes, checksums, record counts and acquisition metadata.

### 4.7 Logging, Audit and Lineage

- Use structured JSON logs.
- Maintain a central acquisition audit trail.
- Preserve lineage from provider through Raw, Interim and Processed datasets to downstream research artefacts.
- Keep operational monitoring separate from formal data quality assessment.
- Use append-only audit records with configurable retention.

### 4.8 Infrastructure Scope

**Decision:** Start with local acquisition monitoring and logging.

The initial implementation will not introduce Airflow, Prefect, Dagster, cloud monitoring services or external observability platforms unless a demonstrated requirement justifies them.

---

## 5. Data Storage and Temporal Principles

### 5.1 Storage Layers

The project uses the following logical layers:

- `data/raw/` — immutable provider acquisitions.
- `data/interim/` — standardised and typed data with source metadata.
- `data/processed/` — consolidated datasets prepared for subsequent assessment.

**Important:** Processed does not mean approved for modelling.

### 5.2 Temporal and Point-in-Time Controls

- Preserve source timestamps and original time-zone semantics.
- Use UTC internally while retaining relevant local-time information.
- Respect Europe/London GMT/BST transitions.
- Do not automatically forward-fill missing observations.
- Use publication timestamps and data vintages for macroeconomic point-in-time joins.
- Do not use macroeconomic information before it was publicly available.
- Do not use same-bar look-ahead execution: after-close signals execute no earlier than the next eligible trading session.

### 5.3 Dataset Metadata

Where applicable, retain:
- Provider and dataset identifier.
- Acquisition timestamp.
- Observation date.
- Publication date.
- Frequency.
- Currency and unit.
- Licence information.
- Data version.
- Adjustment convention.

---

## 6. Group A — Equities Acquisition Record

**Status:** Completed — acquisition and technical integrity verification.

The approved Group A instruments are:

| Instrument | Provider symbol | Role |
|---|---|---|
| National Grid | NG.L | Pilot / target asset |
| SSE plc | SSE.L | Sector peer |
| Severn Trent | SVT.L | Sector peer |
| FTSE 100 | ^FTSE | Market benchmark |

The initial NG.L acquisition was completed previously. The subsequent Group A acquisition covered SSE.L, SVT.L and ^FTSE.

The technical integrity verification confirmed:
- CSV and Parquet files exist.
- File sizes and SHA-256 checksums match their manifests.
- CSV and Parquet contents match after in-memory normalisation.
- Record counts, date ranges and columns are consistent with the manifests.

This record documents acquisition execution. It does not constitute formal financial data quality approval.

---

## 7. Decision Governance

Any material change to:
- project scope;
- data-provider usage or licensing;
- acquisition architecture;
- temporal or point-in-time policy;
- modelling methodology;
- strategy constraints;
- risk limits;
- backtesting or execution assumptions;

must be discussed and explicitly approved before implementation.

New decisions should be added with a unique identifier, date, status, rationale, consequences and links to relevant implementation evidence.


## 5. Phase 2 Closure Decisions

**Project phase:** Phase 2 — Multi-Asset Data Acquisition
**Decision date:** 5 November 2026

---

## D138 — ONS MM23 and QNA Semantic Validation

**Status:** APPROVED
**Date:** 5 November 2026

**Decision:** Approve the semantic validation of the five selected ONS series and the use of the MM23 and QNA source files for their respective logical datasets.

**Approved mappings:**

| Logical dataset ID | ONS series code | Description | Frequency |
|---|---|---|---|
| `UK_CPI` | `D7G7` | CPI Annual Rate — All Items | Monthly |
| `UK_CORE_CPI` | `DKO8` | CPI 12-month rate excluding energy, food, alcoholic beverages and tobacco | Monthly |
| `UK_CPIH` | `L55O` | CPIH Annual Rate — All Items | Monthly |
| `UK_REAL_GDP` | `ABMI` | GDP — Chained Volume Measures, Seasonally Adjusted | Quarterly |
| `UK_GDP_GROWTH` | `IHYQ` | GDP Quarter-on-Quarter Growth, CVM SA | Quarterly |

**Approved acquisition design:**
- Use one original MM23 CSV acquisition for the three inflation datasets.
- Use one original QNA CSV acquisition for the two GDP datasets.
- Preserve the downloaded source files without transformation during acquisition.
- Retain acquisition manifests, configuration hashes, file sizes and SHA-256 checksums.
- Keep the limitations concerning historical revisions and point-in-time availability explicit.

**Evidence:**
- ONS MM23 and QNA CSV files were fetched and inspected.
- All five approved series codes were found in the `CDID` row.
- Series titles, units, observation counts and date labels were inspected.
- The ONS connector's targeted tests and the full test suite passed at the time of implementation.

**Consequences and limitations:**
- Semantic identification is accepted for acquisition purposes.
- This decision does not constitute formal data quality approval or approval for modelling.
- The current ONS CSV release date is not the historical publication timestamp for every observation.
- Historical revisions and point-in-time vintages remain unresolved and must be assessed in the appropriate subsequent phase.
- Licensing and commercial-use permissions remain subject to dataset-level review.

---

## D139 — Phase 2 Closure

**Status:** APPROVED
**Date:** 5 November 2026

**Decision:** Approve the formal closure of Phase 2 — Multi-Asset Data Acquisition, with outstanding risks and limitations retained in the project records.

**Closure scope:**
- Group A — Equities.
- Group B — UK Interest Rates.
- Group C — UK Inflation and Macroeconomic Data.

**Closure evidence:**
- Approved acquisition configurations and provider connectors were implemented.
- The selected acquisitions were executed and recorded with acquisition identifiers and manifests.
- Raw file integrity checks were completed for the acquired datasets where specified in the group records.
- Group C ONS semantic validation was approved under D138.
- Group C ONS Raw file size, manifest status and SHA-256 checks passed.
- The relevant implementation and tests were committed to the repository.

**Explicit exclusions:**
- Phase 2 closure does not approve the datasets for modelling.
- Formal financial data quality assessment and temporal alignment are not included.
- Feature engineering, target construction, forecasting, strategy research and backtesting are not included.
- Source families not acquired in Groups A–C are not represented as acquired or validated by this closure.

**Outstanding risks:**
- Provider and dataset licensing, including commercial use and redistribution.
- Yahoo Finance's unofficial access interface and unresolved usage rights.
- Dataset-specific Bank of England reuse terms.
- ONS historical revisions and point-in-time vintage availability.
- Currency and adjustment assumptions requiring independent verification.
- Market calendar completeness, missing observations and cross-provider temporal alignment.
- The distinction between file integrity and financial data quality.
- FRED/ALFRED training restriction: no model training without written authorisation expressly resolving the relevant restriction.

**Consequences:**
- Phase 2 is recorded as completed.
- Phase 3 — Data Quality Assessment & Temporal Alignment remains not started and requires its own explicit approval.
- No change is made to the project's long-only, research/backtesting/paper-trading-only restrictions.


---

## D140 — Market Quote Currency and Price Unit Convention

**Status:** APPROVED — convention agreed; implementation and historical-data validation pending  
**Date:** 9 November 2026  
**Project phase:** Phase 5 — Financial Time Series and Macroeconomic Analysis

### Context

The original asset configurations declared `GBP` for NG.L, SSE.L, SVT.L and the FTSE 100. This configuration did not distinguish portfolio accounting currency, provider-reported quote currency and the unit in which an instrument is quoted.

The Yahoo Finance chart metadata endpoint was queried directly on 9 November 2026 for all four symbols. All four requests returned HTTP 200.

### Verified provider metadata

| Instrument | Symbol | `currency` | `instrumentType` | `exchangeName` | `fullExchangeName` |
|---|---|---|---|---|---|
| National Grid | `NG.L` | `GBp` | `EQUITY` | `LSE` | `LSE` |
| SSE plc | `SSE.L` | `GBp` | `EQUITY` | `LSE` | `LSE` |
| Severn Trent | `SVT.L` | `GBp` | `EQUITY` | `LSE` | `LSE` |
| FTSE 100 | `^FTSE` | `GBP` | `INDEX` | `FGI` | `FTSE Index` |

The returned `regularMarketPrice` values were metadata observations at query time and are not adopted as historical prices or backtest inputs.

### Decision

1. `GBP` is the portfolio accounting currency.
2. Yahoo Finance reports `GBp` as the quote currency for NG.L, SSE.L and SVT.L. Their quoted price unit is therefore pence sterling.
3. The conversion factor from pence sterling to pounds sterling is `0.01 GBP per GBp`.
4. Price values used in GBP-denominated portfolio accounting and valuation must be converted consistently from GBp to GBP in a downstream processing layer.
5. The original Raw acquisitions must remain immutable. No in-place conversion or modification of Raw files is permitted.
6. The FTSE 100 is an index. Its observations are expressed in index points (`index_points`), not in GBP or GBp price units. No currency conversion is to be applied to index levels.
7. Asset metadata and configuration must distinguish:
   - `accounting_currency`;
   - `provider_quote_currency`;
   - `price_unit`;
   - `conversion_to_accounting_currency`, where applicable.
8. Volume and stock-split fields must not be subjected to currency conversion.
9. Dividend action values must not be converted until their unit convention has been independently verified. The chart metadata `currency` field alone is not sufficient evidence of the units used in the dividend action records.
10. The approved convention does not authorise immediate changes to asset YAML files, manifests, Raw data or Notebook 09. Those implementation changes require a controlled follow-up step.

### Proposed asset metadata convention

For the three LSE equities:

| Field | Approved value |
|---|---|
| `accounting_currency` | `GBP` |
| `provider_quote_currency` | `GBp` |
| `price_unit` | `pence` |
| `conversion_to_accounting_currency` | `0.01` |

For the FTSE 100:

| Field | Approved value |
|---|---|
| `instrument_type` | `index` |
| `provider_quote_currency` | `GBP` (provider metadata) |
| `price_unit` | `index_points` |
| `conversion_to_accounting_currency` | `null` |

The `provider_quote_currency` value reported for the index must not be interpreted as meaning that index levels are monetary prices.

### Evidence and provenance

- Provider: Yahoo Finance.
- Endpoint: `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}`.
- Query date: 9 November 2026.
- Symbols queried: `NG.L`, `SSE.L`, `SVT.L` and `^FTSE`.
- HTTP response: 200 for all four symbols.
- Fields inspected: `symbol`, `currency`, `instrumentType`, `exchangeName`, `fullExchangeName`, `priceHint` and `regularMarketPrice`.
- The terminal output from the query is retained in the project conversation as implementation evidence.

### Validation still required

- Verify the denomination of historical price columns in the existing Raw acquisitions against the provider-reported convention before applying any transformation.
- Independently establish the unit convention for dividend action values.
- Implement and test downstream conversion without changing Raw acquisitions.
- Verify that portfolio accounting, position sizing, cash, fees and P&L use GBP consistently.
- Preserve index levels as index points.
- Update asset configurations and relevant manifests only through a separately controlled implementation step.

### Consequences

- The previous single `currency: GBP` configuration is insufficient to describe all four instruments.
- The asset configuration schema requires a controlled revision.
- Processed equity prices used for GBP accounting will use GBP after validated conversion.
- The FTSE 100 remains in index points.
- This decision approves the unit convention; it does not constitute formal approval of the historical datasets for modelling or formal data-quality closure.
- Raw acquisitions remain unchanged and immutable.

## D141 — Phase 6 Implementation Methodology and Evidence

**Status:** IMPLEMENTED FOR RESEARCH — ACCEPTED WITH DOCUMENTED LIMITATIONS
**Date:** 14 November 2026
**Project phase:** Phase 6 — Feature Engineering and Market Regime Detection

### Context

The approved four-notebook Phase 6 structure has been implemented and executed against existing local market acquisitions. The project owner approved Phase 6 closure on 14 November 2026, accepting these research conventions and the residual limitations. This entry does not approve the features, labels or regimes for forecasting, trading, or Phase 7.

### Implemented research conventions

1. Notebooks 10–13 use the configured market `Close` field. Returns and ratios are scale-invariant; moving-average price levels retain their configured source unit. No GBp-to-GBP conversion is applied. Price returns exclude dividends.
2. Notebook 10 calculates simple and log returns, 5/10/20/50/100-observation momentum, SMA/EMA relationships, rolling return and realised volatility, downside volatility, drawdown, and volume changes/relative volume. The resulting 48-column set is a candidate library, not a selected model feature set.
3. Notebook 11 aligns daily cross-asset returns by exact observation date on an outer calendar union. It does not forward-fill, interpolate, or create synthetic market observations. It does not join macroeconomic observations to decision timestamps where availability/vintage evidence is absent.
4. Notebook 12 defines relative-volatility states using 20-observation realised volatility and lagged quantiles of the preceding 252 completed volatility observations (33rd/67th percentile baseline), and trend states using Close/SMA50/SMA200. Parameter alternatives are sensitivity scenarios, not optimised settings.
5. Notebook 13 defines forward price returns, direction labels and unannualised forward realised volatility over 5, 10 and 20 subsequent acquired rows. Direction neutral bands of 0%, 0.5% and 1.0% are comparison scenarios; none is selected as optimal.
6. All close-based observations at date t are available only after that session close. No same-session execution assumption is introduced. Future shifts occur only in target construction and targets remain in separate output frames.

### Evidence recorded

- The four notebooks executed successfully on 14 November 2026 against the existing local market acquisitions. Outputs are stored in the notebooks.
- The complete repository test suite passed: 224 tests.
- The full-sample descriptive Spearman screen found 51–54 feature pairs per asset with absolute correlation above 0.95 (minimum 252 paired rows). This is redundancy evidence only, not predictive feature selection.
- Regime proportions varied materially across candidate quantiles and estimation windows. No permanent regime interpretation is adopted.
- Directional class balance varied with the neutral band. No threshold is approved by this implementation record.
- No Raw data were modified; no new data were acquired; no FRED/ALFRED data were used.

### Review and limitations

- Historical GBp denomination and corporate-action/adjustment semantics remain unvalidated; RISK-05-01 and RISK-05-02 remain open.
- Macroeconomic availability timestamps, historical vintages and licensing remain incomplete or unvalidated. PIT_UNVALIDATED series are not eligible for strict historical use.
- Incremental predictive value, chronological feature selection and target/regime usefulness have not been tested. Forecasting-model evaluation remains outside Phase 6.
- The project owner accepted these research methods for Phase 6 closure; they are not promoted as forecasting or trading decisions.

## D142 — Phase 6 Closure Approval

**Status:** APPROVED
**Date:** 14 November 2026
**Project phase:** Phase 6 — Feature Engineering and Market Regime Detection

### Decision

The project owner explicitly approves Phase 6 closure after reviewing the executed notebooks and `reports/phase_6/PHASE_6_FINAL_IMPLEMENTATION_REPORT.md`.

The approval accepts the documented research methods and limitations for Phase 6. It does not close the residual risks recorded in `docs/RISK_REGISTER.md`, validate macroeconomic PIT availability or historical price denomination, select an optimal target threshold, approve features for model training, or start Phase 7.

### Consequence

Phase 6 is complete and approved. Phase 7 has not started and requires a separate explicit instruction from the project owner.

## Phase 7 Baseline Forecasting Implementation Record

**Status:** IMPLEMENTED FOR RESEARCH — APPROVED AT PHASE CLOSURE\
**Date:** 14 November 2026\
**Project phase:** Phase 7 — Baseline Forecasting Models

### Scope and implementation

- Implemented and executed `notebooks/14_baseline_forecasting.ipynb` against the existing local acquisitions for NG.L, SSE.L, SVT.L and FTSE 100. Raw acquisitions were not modified and no data were downloaded.
- Preserved Phase 6 targets at 5, 10 and 20 acquired rows: forward `Close` price return, zero-band direction and cumulative unannualised realised volatility. No target formula, threshold or missing-value rule was changed.
- Compared zero, historical mean/median, trailing 252-label mean, AR(1) returns, pre-specified B/BC/BCD OLS feature groups, historical volatility and GARCH(1,1).
- Used an 80/20 chronological development/holdout partition and expanding walk-forward development folds. Purged training origins whose target endpoint would overlap the next validation origin. No random split was used.
- Computed ADF/KPSS, AR residual Ljung–Box and ARCH-LM diagnostics on initial training prefixes. ARCH-LM rejected no conditional heteroskedasticity at p < 0.001 for each asset; a GARCH(1,1) benchmark was therefore investigated.
- Added `src/forecasting/` utilities, 22 tests in `tests/forecasting/`, and SciPy/Statsmodels pins to `requirements.txt`. Both packages were already present in the project environment; no package installation was run.

### Research findings

- A development-selected feature group reduced holdout return MAE in 4 of 12 asset/horizon cases and had higher MAE in the other 8. Holdout directional accuracy was below the best naive/AR reference in all 12 cases.
- Group B financial features were selected in 11 cases, Group BC cross-asset features in one, and Group BCD with regimes in none. No stable incremental value was established for cross-asset or regime information.
- Historical mean/median forecasts were strongest for volatility on NG.L, SSE.L and SVT.L. GARCH(1,1) had the lowest holdout MAE at all three horizons for FTSE 100 only.
- Complete repository tests passed: 246 tests. The executed notebook retains its outputs. Full methods, metrics and limitations are recorded in `reports/phase_7/PHASE_7_FINAL_IMPLEMENTATION_REPORT.md`.

### Status and limits

This record documents the implementation evidence reviewed by the owner at Phase 7 closure. It does not close the open Phase 5/6 data risks or support a profitability, strategy or trading conclusion. Phase 8 has not started.

## D143 — Phase 7 Closure Approval

**Status:** APPROVED\
**Date:** 14 November 2026\
**Project phase:** Phase 7 — Baseline Forecasting Models

### Decision

The project owner approves Phase 7 closure after reviewing the implementation report, executed notebook outputs, results, tests and documented limitations.

### Consequences and limits

- Phase 7 is complete and approved.
- Its negative and mixed forecasting results are accepted as research findings; no feature-based return model is promoted as useful.
- The residual risks in `docs/RISK_REGISTER.md`, including data provenance, historical price denomination, corporate-action semantics, target overlap and model stability, remain open.
- This approval does not authorise Phase 8. Phase 8 has not started and requires a separate instruction.

## Phase 8 Machine Learning Implementation Record — Owner Review Pending

**Status:** IMPLEMENTED FOR RESEARCH — NOT YET APPROVED FOR PHASE CLOSURE  
**Date:** 14 November 2026  
**Project phase:** Phase 8 — Machine Learning Experiments

### Implementation evidence

- Added `notebooks/15_machine_learning_experiments.ipynb` and reusable modules under `src/forecasting/` for ML models, data preparation, metrics, walk-forward experiments and local MLflow configuration.
- Evaluated Ridge, Random Forest regression and Random Forest direction classification against the unchanged Phase 6 targets and Phase 7 B/BC/BCD groups for NG.L, SSE.L, SVT.L and FTSE 100.
- Used expanding walk-forward folds with horizon-based purging. No random split was used. The previously evaluated Phase 7 holdout was not treated as an independent Phase 8 test.
- The executed notebook and detailed results are retained in `reports/phase_8/`.
- The full test suite passed 256 tests. No Phase 7 implementation or findings were changed.

### Research findings and limits

- No return model showed consistent incremental value over statistical references; direction classification did not beat the training-majority accuracy on average.
- Ridge and Random Forest volatility forecasts had lower development walk-forward MAE than several references in many cases. These results are development evidence only and require a genuinely future evaluation period before any model promotion.
- Block-bootstrap intervals are unadjusted for multiple comparisons. Existing data provenance, price-unit, corporate-action, licensing and serial-dependence risks remain open.
- The potential Phase 7 AR(1) gap-handling issue was documented and reviewed but not changed.

This implementation record does not constitute a Phase 8 closure decision. Owner review and explicit closure approval remain pending. Phase 9 is not authorised.
