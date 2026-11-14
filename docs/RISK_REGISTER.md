# Risk Register

**Project:** Quantitative Trading Strategy\
**Document status:** Active\
**Project phase:** Phase 8 --- Machine Learning Experiments (implementation complete; owner review pending)\
**Last updated:** 14 November 2026\
**Language:** British English

------------------------------------------------------------------------

## 1. Purpose

This register records material risks to the research, data, modelling,
validation, backtesting and paper-trading workstreams. It is intended to
support explicit risk ownership, mitigation, evidence tracking and
phase-gate decisions.

A risk is not considered closed merely because a mitigation has been
proposed or documented. Closure requires evidence that the mitigation
has been implemented and its effectiveness has been verified.

## 2. Rating methodology

The current entries retain the qualitative probability/likelihood and
impact assessments available in the project record. Where a historical
entry's original rating or full wording is not available in the current
working record, this is explicitly marked for reconciliation rather than
inferred.

  -----------------------------------------------------------------------
  Rating                              Meaning
  ----------------------------------- -----------------------------------
  Low                                 Limited effect on research validity
                                      or project delivery

  Medium                              Material issue requiring planned
                                      mitigation and monitoring

  High                                Could materially invalidate
                                      findings, trading results or
                                      operational controls
  -----------------------------------------------------------------------

The overall risk level is recorded as supplied by the project risk
assessment where available. No numerical probability is implied.

## 3. Risk register

### 3.1 Historical Phase 3 risks

The following identifiers were recorded as open in the project history.
The available record identifies them as outstanding currency/price-unit
verification risks. Their exact original descriptions and ratings should
be reconciled against the historical Phase 3 risk source if that source
is recovered.

  ----------------------------------------------------------------------------------
  Risk ID    Risk statement     Likelihood         Impact Status     Mitigation and
             / known scope                                           required
                                                                     evidence
  ---------- -------------- -------------- -------------- ---------- ---------------
  R-P3-006   Historical       To reconcile   To reconcile Open       Preserve Raw
             Phase 3 risk                                            acquisitions.
             concerning                                              Verify provider
             market                                                  quote currency
             currency /                                              and historical
             price-unit                                              price-series
             assumptions.                                            denomination
             Exact original                                          per instrument.
             wording is not                                          Record source
             available in                                            evidence and
             the current                                             validate any
             record.                                                 downstream
                                                                     conversion
                                                                     before closure.

  R-P3-007   Historical       To reconcile   To reconcile Open       Reconcile the
             Phase 3 risk                                            original risk
             concerning                                              statement to
             currency /                                              the Phase 3
             price-unit                                              source. Do not
             assumptions.                                            close until the
             Exact original                                          relevant unit
             wording is not                                          convention and
             available in                                            downstream
             the current                                             treatment have
             record.                                                 been
                                                                     independently
                                                                     verified.
  ----------------------------------------------------------------------------------

### 3.2 Phase 5 risks

  -------------------------------------------------------------------------------------------------------
  Risk ID      Risk statement                 Likelihood         Impact Status     Mitigation / closure
                                                                                   criteria
  ------------ -------------------------- -------------- -------------- ---------- ----------------------
  RISK-05-01   Incorrect price                    Medium           High Open       Keep `Adj Close`
               adjustments could produce                                           distinct from
               misleading returns and                                              unadjusted OHLC
               financial results.                                                  fields. Document the
                                                                                   selected price series
                                                                                   and adjustment
                                                                                   semantics. Validate
                                                                                   corporate-action
                                                                                   treatment before
                                                                                   calculating returns.
                                                                                   Close only after
                                                                                   instrument-level
                                                                                   checks and
                                                                                   reproducible tests.

  RISK-05-02   GBP/GBp denomination               Medium           High Open       Apply the approved
               errors could create                                                 D140 convention only
               100-fold errors in prices,                                          downstream: LSE
               share quantities, cash                                              equities NG.L, SSE.L
               accounting, costs and P&L.                                          and SVT.L are
                                                                                   provider-quoted in
                                                                                   GBp, with a conversion
                                                                                   factor of 0.01 to GBP;
                                                                                   `^FTSE` is an index
                                                                                   measured in index
                                                                                   points and must not be
                                                                                   converted. Validate
                                                                                   historical
                                                                                   price-series
                                                                                   denomination before
                                                                                   transformation.
                                                                                   Preserve Raw data. Do
                                                                                   not convert dividend
                                                                                   action fields until
                                                                                   their units are
                                                                                   independently
                                                                                   verified. Close only
                                                                                   after implementation
                                                                                   and instrument-level
                                                                                   validation.

  RISK-05-03   Structural breaks may make           High           High Open       Inspect candidate
               historical statistical                                              series for regime
               relationships unstable or                                           changes and known
               non-representative of                                               methodology/economic
               future conditions.                                                  breaks. Report results
                                                                                   by relevant sub-period
                                                                                   where justified. Avoid
                                                                                   treating full-sample
                                                                                   estimates as stable
                                                                                   without evidence.

  RISK-05-04   Multiple testing may                 High           High Open       Pre-specify research
               increase false discoveries                                          questions and test
               and lead to spurious                                                families where
               research conclusions.                                               possible. Report the
                                                                                   number of tests,
                                                                                   distinguish
                                                                                   exploratory from
                                                                                   confirmatory analysis,
                                                                                   and apply suitable
                                                                                   multiple-testing
                                                                                   controls where
                                                                                   appropriate. Avoid
                                                                                   selecting findings
                                                                                   solely by statistical
                                                                                   significance.

  RISK-05-05   Macroeconomic observation            High           High Open       Do not use observation
               dates may be mistaken for                                           dates as publication
               publication/availability                                            timestamps. Record
               dates, causing look-ahead                                           release/availability
               bias.                                                               dates where validated.
                                                                                   Apply point-in-time or
                                                                                   conservative
                                                                                   release-lag rules
                                                                                   before any predictive
                                                                                   use.

  RISK-05-06   GDP data may not be                  High           High Open       Treat GDP as
               point-in-time safe because                                          `PIT_UNVALIDATED`. Do
               historical observations                                             not use it in
               can be revised and vintage                                          predictive modelling
               information may be                                                  until
               unavailable or                                                      vintage/release-time
               unvalidated.                                                        handling is validated.
                                                                                   Keep descriptive
                                                                                   analysis clearly
                                                                                   separated from
                                                                                   point-in-time
                                                                                   predictive claims.

  RISK-05-07   SONIA methodology changes          Medium         Medium Open       Document the
               may create discontinuities                                          methodology change
               or reduce comparability                                             dated 23 April 2018.
               across the historical                                               Inspect pre- and
               series.                                                             post-change behaviour
                                                                                   and assess
                                                                                   comparability before
                                                                                   interpreting long-run
                                                                                   relationships or using
                                                                                   the series as a model
                                                                                   feature.

  RISK-05-08   Missing observations and           Medium           High Open       Retain source
               inconsistent                                                        calendars and
               trading/economic calendars                                          missingness
               may cause misalignment,                                             information. Align
               unintended sample                                                   series explicitly by
               selection or invalid                                                date and frequency. Do
               statistical comparisons.                                            not interpolate or
                                                                                   impute by default.
                                                                                   Record the effective
                                                                                   sample for every
                                                                                   analysis.

  RISK-05-09   Correlations between                 High           High Open       Assess stationarity
               financial and                                                       and transformations
               macroeconomic series may                                            before interpreting
               be spurious due to trends,                                          relationships. Use
               non-stationarity, common                                            economically justified
               shocks, lags or structural                                          lags,
               breaks.                                                             rolling/sub-period
                                                                                   analysis and
                                                                                   appropriate
                                                                                   statistical tests.
                                                                                   Treat correlations as
                                                                                   associations, not
                                                                                   causal evidence.

  RISK-05-10   In-sample relationships              High           High Open       Separate explanatory
               may be mistaken for                                                 analysis from
               predictive value,                                                   forecasting
               resulting in features or                                            evaluation. Require
               hypotheses that fail out                                            chronological
               of sample.                                                          validation and
                                                                                   untouched holdout
                                                                                   evidence before
                                                                                   claiming predictive
                                                                                   value. Compare against
                                                                                   simple baselines and
                                                                                   retain only features
                                                                                   that demonstrate
                                                                                   robust incremental
                                                                                   value.
  -------------------------------------------------------------------------------------------------------

### 3.3 Phase 6 implementation risks

The following risks were identified or confirmed during Phase 6 execution.
They remain open because their closure criteria require additional evidence
or owner review.

| Risk ID | Risk statement | Likelihood | Impact | Status | Mitigation / closure criteria |
|---|---|---:|---:|---|---|
| RISK-06-01 | Redundant candidate features may inflate complexity and encourage unstable selection. | High | High | Open | The executed Spearman screen found 51–54 pairs per asset above 0.95 absolute correlation. Treat the 48-column set as a candidate library; pre-specify a smaller set and perform selection only inside chronological training windows. |
| RISK-06-02 | Macro observations may be used before actual release or without vintage control. | High | High | Open | No macro series was joined to historical decisions. Validate per-observation availability, acquisition provenance and vintage semantics before any historical predictive use. Preserve PIT_UNVALIDATED exclusions. |
| RISK-06-03 | Overlapping target horizons and unapproved neutral thresholds may bias later evaluation or produce unstable classes. | High | High | Open | Keep targets separate; report horizon-specific class balance; decide thresholds before model evaluation; purge overlapping origins and document the validation-specific embargo. |
| RISK-06-04 | Relative regime labels may change materially with window and quantile choices and may be mistaken for stable economic states. | Medium | High | Open | Sensitivity runs show materially different state shares. Report transition/sub-period behaviour, avoid permanence claims, and re-evaluate only with pre-specified chronological evidence. |
| RISK-06-05 | Close-based targets exclude dividends, while adjusted-price and corporate-action semantics remain unvalidated. | Medium | High | Open | Label the current targets as price returns. Review Close versus Adjusted Close and corporate actions before interpreting them as investment returns; do not infer dividend units. |

### 3.4 Phase 7 baseline forecasting risks

| Risk ID | Risk statement | Likelihood | Impact | Status | Mitigation / closure criteria |
|---|---|---:|---:|---|---|
| RISK-07-01 | Small apparent return-forecast improvements may reflect model selection, overlapping labels or regime variation rather than stable predictive information. | High | High | Open | Retain naive benchmarks; keep the final holdout untouched; require consistent results across periods and pre-approved criteria before promoting a model. No feature group improved directional accuracy on the holdout. |
| RISK-07-02 | Adjacent validation outcomes remain dependent because forward targets overlap, even after purging training labels at split boundaries. | High | Medium | Open | Report period-level metrics and avoid treating fold observations as independent; any inferential comparison must account for overlap and serial dependence. |
| RISK-07-03 | GARCH(1,1) Gaussian QMLE may be sensitive to distributional assumptions, missing-row variance propagation and parameter instability. | Medium | High | Open | Keep GARCH as a benchmark only. Check convergence, residual distribution, parameter stability and performance across additional chronological windows before further use. |
| RISK-07-04 | OLS feature groups may remain unstable under candidate redundancy and data snooping across assets, horizons and feature families. | High | High | Open | Keep feature groups small and pre-specified; fit scaling within training folds; avoid broad searches and require out-of-sample incremental value over naive references. |

### 3.5 Phase 8 Machine Learning experiment risks

| Risk ID | Risk statement | Likelihood | Impact | Status | Mitigation / closure criteria | Owner decision required |
|---|---|---:|---:|---|---|---|
| RISK-08-01 | Existing observations, including the Phase 7 holdout, have already been exposed to project analysis; retrospective Phase 8 walk-forward results could be overstated as independent final-test evidence. | High | High | Open | Label all current results development-only. Freeze research choices and evaluate once on genuinely future observations before any promotion claim. | Approve a frozen protocol and future evaluation period before any confirmatory run. |
| RISK-08-02 | Multiple models, assets, targets, feature groups and horizons create selection and multiple-testing risk; overlapping labels and serial dependence remain. | High | High | Open | Pre-specify configurations, retain fold-level results, use horizon-based purging and gap-aware block resampling, and treat current intervals as descriptive because no multiplicity correction was applied. | Select the primary hypothesis family and correction method before future evaluation. |
| RISK-08-03 | Apparent volatility forecast improvements may be asset-, period- or regime-specific and may not persist out of sample. | High | High | Open | Retain statistical benchmarks and require confirmation on a future evaluation period across assets and horizons before promotion. | Decide whether any model merits a separately governed confirmation study. |
| RISK-08-04 | The zero-band direction target has very few neutral observations, which can make classification metrics unstable and predictions insensitive to the neutral class. | High | Medium | Open | Preserve the approved target. The class note and per-asset/horizon/fold table show neutral labels in only 85 of 33,404 development origins, with no neutral cases in 18 of 48 folds. Retain balanced metrics and confusion matrices; do not alter the neutral band without a separate decision. | Any target-threshold change requires explicit approval and a newly pre-specified evaluation. |
| RISK-08-05 | A floating transitive dependency graph could drift between local and CI environments and compromise reproducibility. | Medium | Medium | Mitigated | Direct dependencies are explicitly pinned; pandas matches the tested environment; NumPy and pytest are explicit; a 107-package Python 3.12 lock was created from a clean installation. `pip check` and the full suite passed in that clean environment. Revalidate the lock on deliberate dependency updates. | Review dependency updates through normal project change review. |
| RISK-08-06 | Phase 7 AR(1) parameter fitting drops missing returns before constructing lag pairs, potentially treating non-adjacent acquired rows as consecutive. | Medium | High | Open | The Phase 8 return reference uses adjacent acquired-row pairs. The Phase 7 implementation and approved outputs remain untouched; a separate correction and comparison plan is documented. | Explicitly authorise or reject a separate Phase 7 correction after reviewing its impact. |
| RISK-08-07 | Yahoo Finance terms for commercial use and rights to train commercial models remain unresolved; macroeconomic point-in-time vintages and licensing are also unvalidated. | Medium | High | Open | Treat Yahoo data as research-only pending written rights confirmation. No macro series or FRED/ALFRED observations were added to Phase 8 training. Validate source licence, redistribution and point-in-time semantics before future use. | Obtain written licence/use determination before commercial use or adding macroeconomic training data. |

## 4. Currency and price-unit control --- D140

Decision D140 records the following provider metadata observed on 9
November 2026:

  -------------------------------------------------------------------------------
  Instrument     Instrument     Provider-reported   Price-unit     Conversion to
                 type           quote currency      treatment      GBP accounting
  -------------- -------------- ------------------- -------------- --------------
  NG.L           Equity         GBp                 Pence          0.01

  SSE.L          Equity         GBp                 Pence          0.01

  SVT.L          Equity         GBp                 Pence          0.01

  \^FTSE         Index          GBP metadata; index Index points   Not applicable
                                level is in index                  
                                points                             
  -------------------------------------------------------------------------------

The Yahoo Finance chart endpoint returned HTTP 200 for all four
instruments. The quote-currency metadata supports the current provider
convention, but does not, by itself, prove the denomination of every
historical observation or corporate-action field.

**Controls:** - Raw acquisitions remain immutable. - Conversion, if
required, is a downstream transformation. - Do not apply currency
conversion to volume or stock-split fields. - Do not infer dividend
units from the instrument's quote-currency metadata. - Historical
price-series denomination must be validated before conversion. - The
`^FTSE` index level is not a GBP-denominated equity price.

D140 is approved as a documented convention; implementation and
historical-data validation remain pending. Therefore, RISK-05-02 remains
**Open**.

## 5. Governance and review rules

1.  Review risks at each phase gate and whenever a material data,
    methodology or architecture decision changes.
2.  Record evidence, not just assertions, when changing a risk status.
3.  A mitigation marked as planned or approved does not constitute
    implementation.
4.  A risk may be closed only when its closure criteria are met and the
    supporting evidence is recorded.
5.  Retain historical risk identifiers. Do not renumber existing risks.
6.  Where historical source wording or ratings are unavailable, mark
    them for reconciliation; do not reconstruct them from assumptions.
7.  Risks affecting point-in-time integrity, leakage, accounting or
    execution realism must be resolved or explicitly accepted before the
    affected downstream phase is approved.

## 6. Current priority actions

  --------------------------------------------------------------------------------------
  Priority          Action                          Related risks     Required outcome
  ----------------- ------------------------------- ----------------- ------------------
  1                 Validate the historical price   R-P3-006,         Reproducible
                    denomination for the three LSE  R-P3-007,         instrument-level
                    equities and confirm the index  RISK-05-02        evidence; no Raw
                    treatment.                                        mutation

  2                 Confirm the price-adjustment    RISK-05-01        Documented and
                    semantics and corporate-action                    tested
                    treatment.                                        return-price
                                                                      convention

  3                 Establish                       RISK-05-05,       Explicit PIT
                    publication/availability-time   RISK-05-06        status and
                    controls for macroeconomic                        release-time rules
                    data.                                             

  4                 Assess SONIA methodology        RISK-05-07,       Documented
                    discontinuity and calendar      RISK-05-08        treatment and
                    alignment.                                        effective samples

  5                 Apply stationarity,             RISK-05-03,       Qualified
                    structural-break and            RISK-05-04,       statistical
                    multiple-testing safeguards     RISK-05-09        interpretation
                    before interpreting                               
                    relationships.                                    

  6                 Require chronological           RISK-05-10        Demonstrated
                    out-of-sample evidence before                     incremental value
                    promoting relationships to                        over baselines
                    predictive features.                              

  7                 Review the Phase 6              RISK-06-01 to     Completed 14 Nov
                    implementation report and      RISK-06-05        2026; owner approved
                    approve closure explicitly.                       Phase 6 closure.
                                                                      Residual risks remain
                                                                      open for later work.
  --------------------------------------------------------------------------------------

## 7. Change history

  -----------------------------------------------------------------------
  Date                                Change
  ----------------------------------- -----------------------------------
  9 November 2026                     Initial consolidated register
                                      created from the available project
                                      record. Historical Phase 3 risk
                                      identifiers retained; exact
                                      original wording and ratings
                                      flagged for reconciliation. Phase 5
                                      risks RISK-05-01 to RISK-05-10
                                      recorded. D140 currency/price-unit
                                      controls incorporated.

  14 November 2026                    Phase 6 execution findings
                                      recorded; five Phase 6 risks
                                      added and left open pending
                                      mitigation, owner review or
                                      later-phase evidence.

  14 November 2026                    Project owner approved Phase 6
                                      closure. Residual Phase 6 risks
                                      remain open and are carried into
                                      subsequent authorised work.

  14 November 2026                    Phase 7 baseline implementation
                                      and research findings recorded;
                                      four Phase 7 risks added and
                                      left open pending further
                                      evidence.

  14 November 2026                    Project owner approved Phase 7
                                      closure. Phase 7 risks and all
                                      carried data risks remain open.

  14 November 2026                    Phase 8 implementation findings
                                      recorded; six Phase 8 risks added
                                      and left open pending owner review,
                                      prospective evaluation or dependency
                                      reconciliation. Phase 8 closure is
                                      not yet approved.

  -----------------------------------------------------------------------
