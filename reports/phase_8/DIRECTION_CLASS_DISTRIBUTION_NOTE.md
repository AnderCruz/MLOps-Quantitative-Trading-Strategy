# Direction target class distribution — Phase 8

**Date:** 14 November 2026  
**Evidence type:** Existing development walk-forward predictions; not an independent test.

## Observed distribution

The corrected Phase 8 prediction file contains 33,404 unique direction forecast origins after deduplicating the three feature-group/model copies by asset, horizon, fold and date. The observed labels are:

| Label | Observations | Share |
|---|---:|---:|
| Negative (-1) | 15,158 | 45.38% |
| Neutral (0) | 85 | 0.25% |
| Positive (+1) | 18,161 | 54.37% |

The accompanying `development_results/class_distribution.csv` records counts and shares by asset, horizon and walk-forward fold (48 strata). Neutral labels are absent in 18 of 48 folds; the neutral share ranges from 0% to 0.986%. Fold-specific training sets can also lack one or more classes, so classifier probability columns are explicitly mapped to the approved `-1, 0, +1` labels, with absent classes assigned zero probability.

## Research interpretation and control

This confirms that the approved zero-neutral-band target produces a very sparse neutral class. Macro accuracy alone can conceal poor minority-class recognition; retain balanced accuracy, macro metrics, per-fold confusion matrices and class prevalence in future review. The implementation records this imbalance but does not change the target threshold, relabel observations, or claim improved model utility. Any threshold change requires separate owner approval and a newly pre-specified evaluation.

The counts are in-sample to the development experiment's walk-forward validation origins and should not be presented as population prevalence or independent confirmatory evidence.
