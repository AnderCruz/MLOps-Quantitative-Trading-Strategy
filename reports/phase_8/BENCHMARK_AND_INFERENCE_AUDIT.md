# Phase 8 benchmark and inference audit

**Date:** 14 November 2026  
**Scope:** Phase 8 comparison pipeline and review of the Phase 7 AR(1) caveat.

## Pairing and forecast construction

Phase 8 benchmark comparisons join the model and reference predictions by forecast-origin date, then calculate paired differences on common non-missing observations. Direction comparisons use the same forecast dates and retain the existing three-class labels. The corrected prediction validator checks that model copies have the same actual target, fold and acquired position for each common asset/horizon/date, and that B/BC/BCD groups use the same origins. The comparison file retains paired counts and dates.

Return references use zero, expanding mean/median, trailing training mean and Phase 8's adjacent-acquired-pair AR(1) calculation. The AR(1) reference only forms lag pairs when the two return values belong to adjacent acquired rows. No change was made to the previously approved Phase 7 implementation or results.

Volatility references forecast a cumulative, unannualised horizon target. The expanding location forecasts are based on prior forward volatility labels. Rolling historical volatility uses recent one-row log returns and scales their sample standard deviation by the square root of the horizon. GARCH(1,1) is fitted using the training prefix, then its state is updated with observed returns through each forecast origin. These methods have different distributional and state-update assumptions; their MAE comparisons are forecast-error comparisons on paired targets, not evidence of economic superiority.

## Phase 7 AR(1) issue requiring separate review

`src/forecasting/benchmarks.py` applies `dropna()` before forming AR(1) lag pairs in its general-purpose fitting helpers. If acquired returns contain a missing row, values on either side can become adjacent in the compacted array even though they were not adjacent acquired observations. This can change the estimated lag relationship and recursive forecast. Phase 7 reports the benchmark as an AR(1) on one-row log returns; the Phase 7 code, notebook outputs and approved findings are intentionally unchanged in this remediation.

The Phase 8 reference uses explicit acquired positions and adjacent finite pairs. A separate, owner-approved Phase 7 correction should preserve missing positions when forming lags, re-run only the affected benchmark calculations against the existing local acquisition, compare the results to the approved outputs, and record any disposition without silently replacing the approved report.

## Statistical interpretation

The development output contains **792 comparison rows**. The 500-replication bootstrap uses blocks of length equal to each forecast horizon and resamples separately within each validation fold. It is reproducible with a fixed seed and does not carry blocks across folds. Paired inputs now reject duplicate dates and incomplete fold/position identity and exclude any non-finite actual/model/reference triplet consistently.

Intervals remain unadjusted across the many model, asset, target, feature-group and horizon comparisons. They are descriptive; no confirmatory significance or model-selection claim is warranted from repeated inspection of these outputs. Future confirmatory work should freeze a small set of primary hypotheses before evaluation, define a genuinely future one-time evaluation period, and use an appropriate family-wise (for example Holm) or false-discovery adjustment for any secondary test family. Existing outputs remain available for descriptive comparison; no multiplicity correction was retrospectively used to select a model.
