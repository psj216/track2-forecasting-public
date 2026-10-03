# LOCATION-02 — ECB SPF consensus location alpha

## Executive summary

**Verdict: NO.** The precommitted FULL5 model has CRPS ratio **1.562820** versus original V5.1=1, with oracle capture **-95.2418%**. All five annual folds deteriorate. This frozen test does not support ECB SPF predicting the EUR standardized location error. Do not tune this failure or substitute an ablation. Next axis: **FED-SLOOS-LOCATION-03; separate frozen branch, no ECB tuning**.

All observations are **RESEARCH-EXPOSED**. No result is independent out of sample, official validation or submission evidence. New architecture, scale, tail, covariance and rank models were not created. The experiment tests exactly five original-release consensus features against an existing forecast's location error.

## Source readiness and provenance

Gate A: **DATASET_READY=true**, before accessing forecasting outcomes. The actual dated official archive enumerated 40 releases, 2015Q1–2024Q4 (2015-01-23–2024-10-18), not an assumed quarter count. Original official PDFs supply 240 point-field rows: headline HICP and real GDP, explicit current/next/second-following calendar years. Matching HTML is additionally available for 26 rounds. Each raw document has an original URL and byte SHA256 receipt.

There are 39 usable same-target revision events / 78 variable revisions. 2015Q1 has no verified preceding 2014 original within the admitted universe and is inactive; its retrospective printed comparison was not a substitute feature. All 216 applicable following-round comparisons agree with preceding originals. No amendment notice was found in the complete original documents and matching HTML. This is **PIT B**, not immutable historical-vintage proof; absence of a notice does not prove that no unpublished replacement ever occurred. No current aggregate CSV, revised history, microdata or third-party backcast was used.

Publication uses actual official dates. For example 2020Q2 is **2020-05-04**, not a guessed April quarterly date. Date-only availability is 23:59:59 Europe/Berlin, compared with the prior repository weekday at 16:00 America/New_York. Response/deadline/PDF creation timestamps are never activation evidence. Ambiguous NY federal-holiday cutoff days are conservatively excluded. SOURCE_AGE uses unchanged repository weekday business days and expires strictly after 90, without tuning.

The archive and original URLs appear in `ecb_release_universe.csv`; each extraction locator, explicit target year and original hash appears in `ecb_field_ledger.csv`. A revision is current next-year minus the previous verified round for **that same target year**, including the preceding round's second-following year at Q1 rollover. Missing revisions are never imputed. Corrections are distinct availability events, not retrospective overwrite. Rights: ECB attribution, accurate reproduction and clearly labelled derivatives; raw originals are privately preserved for this research and are not publicly redistributed as a corpus.

Official source: https://www.ecb.europa.eu/stats/ecb_surveys/survey_of_professional_forecasters/html/all-releases.en.html

## Frozen experiment and maturity

Parent RESULT: `43a154ab419b6f3e3f4fc903db40d8c2e319f6bf`. PRE_RESULT_LOCATION02_SHA: `d83409f414498b0cadcc508d387252b54dfd1e98`. All source rows/hashes, parser, five features, timing, age90, EUR, horizons5/21/63/126/189, model, fold rules, scorer, controls and interpretation were committed and remotely verified before labels were materialized. The frozen parent ledger and original cached V5.1 draws were restored and byte-hash verified; no V5.1 model or distribution was regenerated.

Use first existing frozen baseline-ledger origin each month. Source-only calendar: 120 monthly candidates, 100 active after missing/expiry/holiday guards. Outcome eligibility leaves 95 origins / 462 cells across development and forward history. Evaluation has **48 origins / 227 cells / 20 releases**, with 5 annual blocks. Original EUR level series ends 2024-10-31; no extension was synthesized. Every target matures no later than the user's 2024-12-18 ceiling and the existing series endpoint. EUR truth is the repository's absolute future level, not a reinterpreted log return.

Training starts 2015–2019 and expands for each annual 2020–2024 fold. Labels must mature strictly before the first test cutoff. The shared model additionally applies the parent's maximum189BD origin purge; horizon-specific target_end checks remain explicit. Train/test source release IDs do not overlap. One pooled Ridge has alpha=1.0, intercept and deterministic SVD. Train-only standardization and Ridge use weights1/(training rows in release), so each release has total weight1. No tuning, feature selection or threshold selection was performed.

Target: `(truth − median(original draws)) / original population SD`. Candidate: original draws plus `predicted_delta × original SD`. Draw count, centered geometry, ordering and original scale are preserved. Inactive origins have zero shift but are outside the active primary cohort. No later EUR/card transfer or joint/F1 claim follows from marginal scores.

## Primary scores and secondary ablations

CRPS imports the exact shared fair-ensemble scorer. Each cell is divided by its frozen past-only daily scale times sqrt(horizon); aggregate ratio is the ratio of sums over identical cells, exactly as in LOCATION-01. Lower is better. Oracle capture is `(1−candidate ratio)/(1−perfect-location ratio)`, without clipping.

| Model | CRPS ratio | Oracle capture | R² | Spearman | Sign accuracy |
| --- | --- | --- | --- | --- | --- |
| V5.1 | 1.0000 | 0.0000 | -0.0000 | — | 0.0000 |
| ECB_RIDGE_FULL5 | 1.5628 | -0.9524 | -1.4317 | 0.1379 | 0.5771 |
| LEVELS_ONLY | 1.1227 | -0.2076 | -0.3426 | 0.1245 | 0.5595 |
| REVISIONS_ONLY | 1.4146 | -0.7016 | -0.7901 | -0.0705 | 0.4185 |
| HICP_ONLY | 1.1389 | -0.2351 | -0.3548 | -0.0308 | 0.5154 |
| GDP_ONLY | 1.2853 | -0.4827 | -0.7591 | 0.3018 | 0.5947 |
| PERFECT_LOCATION | 0.4091 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

Ablations are descriptive only. They do not replace the failed FULL5 result. Perfect location shifts each original distribution median to truth, changing no shape; it measures same-ledger location headroom, not achievable prediction. V5.1's zero-shift error predictor has undefined rank correlation; zero predictions count as a correct sign only for an exactly zero realized standardized error.

## Annual forward folds

| Year | Cells | Releases | CRPS ratio | Oracle capture |
| --- | --- | --- | --- | --- |
| 2020 | 60 | 5 | 1.8244 | -1.4236 |
| 2021 | 45 | 5 | 1.3163 | -0.5381 |
| 2022 | 50 | 5 | 1.6124 | -0.8806 |
| 2023 | 45 | 4 | 1.4971 | -1.0573 |
| 2024 | 27 | 3 | 1.0120 | -0.0276 |

No annual fold improves. Annual maturity/purge/release counts are in `fold_manifest.csv`; fold-specific scalers and coefficients are preserved privately. They are descriptive, not causal macro effects.

## Horizon breakdown

| Horizon (BD) | Cells | Releases | CRPS ratio | Oracle capture |
| --- | --- | --- | --- | --- |
| 5 | 48 | 20 | 1.6820 | -1.0922 |
| 21 | 48 | 20 | 1.7520 | -1.3959 |
| 63 | 46 | 19 | 1.5161 | -0.9276 |
| 126 | 44 | 19 | 1.4544 | -0.7565 |
| 189 | 41 | 18 | 1.4135 | -0.6603 |

All five horizons are retained; no favorable horizon/year subset was selected. Late-2024 long-horizon labels are genuinely unavailable, explaining smaller counts.

## Repeated-release dependence and inference

The 227 cells are not independent information events. They share only 20 source releases; this count is an **upper bound**, not a proven effective independent sample size. A source release can be reused by several monthly origins and horizons; quarterly persistence and overlapping targets can cause dependence beyond release blocks. Exact origins per release and releases per fold/horizon are preserved in the public summaries.

Release-block bootstrap: 5,000 replicates, ratio95% interval **[1.1547135348440911, 2.1097404167556473]**, delta-versus-V5.1 interval **[0.15471353484409106, 1.1097404167556473]**, capture interval **[-1.9535843877029808, -0.25781317637508594]**. Year-block bootstrap: 5,000 replicates over only5 years, ratio95% interval **[1.2794966312193918, 1.730224581053736]** and capture interval **[-1.2604727304035326, -0.5264943774217224]**. Correlation intervals are in `bootstrap_summary.json`. Neither bootstrap creates independent validation.

## Negative controls and mutations

| Control | Replicates | Median/fixed ratio | Fraction ≤ primary |
| --- | --- | --- | --- |
| RELEASE_VALUE_SHUFFLE | 2000 | 1.7528 | 0.3340 |
| RELEASE_DATE_PERMUTATION | 2000 | 1.8708 | 0.0845 |
| REVISION_SIGN_SHUFFLE | 2000 | 1.4657 | 0.5945 |
| GAUSSIAN_FULL5 | 2000 | 1.0431 | 1.0000 |
| FEATURE_YEAR_SHIFT | 1 | 1.1287 | — |

Each stochastic family uses2,000 deterministic replicates, unchanged chronological maturity/purge and alpha1/scaler mechanics. Value/revision shuffles reassign training source vectors at release-block level within each historical training information set; held-out outcomes and future test values never enter fitting. Revision signs are fixed within each source block. Date permutations use randomly reassigned **nonnegative** publication delays0..20BD and never activate before actual publication. One-year lag is a single frozen diagnostic. Gaussian control has exactly5 dimensions and one vector per release. Null performance is never used to choose model settings.

Later ECB release mutation leaves all earlier source features and actual2020/2021 predictions bitwise unchanged. Outcome mutation cannot change the source calendar, whose construction has no outcome interface. Synthetic and real geometry checks preserve original population SD and weak within-distribution ordering. Actual FULL5 has two sorted-index positions affected by a newly rounded1ULP tie; centered geometry roundoff is at most2.22e-16 and no ordering inversion occurs. Strict argsort byte identity therefore does not hold. No numerical jitter, reranking or correction was introduced. The only post-PRE validation correction preserves original CSV-parsed bits for unchanged source events: rebuilding every input from JSON would introduce unrelated one-ULP serialization differences. This corrected diagnostic changes no primary feature, prediction, score, stochastic-control result or success gate; frozen primary implementation hashes remain exact. Individual standardized errors, truths, draws and cell losses remain private.

## Concentration and economic direction

Predeclared concentration diagnostics: `{'largest_release_positive_gain_share': 0.40052806739205754, 'largest_year_positive_gain_share': None, 'dominated_by_one_release_or_year': False}`. These refer to shares of **gross positive local gains**, where present, not proof of a total improvement. FULL5 degrades in all five years, so there is no overall improvement whose breadth could support alpha. Removal of a bad year/release is not an authorized experiment.

Raw economic correlations are descriptive only: `{'HICP_NCY': {'pearson': 0.16054563528306673, 'spearman': 0.10047371842815427}, 'GDP_NCY': {'pearson': -0.28835596172182976, 'spearman': -0.3217412131431107}, 'HICP_NCY_REV_SAME_TARGET': {'pearson': 0.05851473302072573, 'spearman': -0.15923099972765126}, 'GDP_NCY_REV_SAME_TARGET': {'pearson': -0.0033838130299118667, 'spearman': -0.13322181680208517}}`. Forecast claims rely exclusively on crossfit predictions. Coefficient signs and these correlations are not causal evidence.

## Limitations and decision

Only EUR, only20 evaluated releases and five exposed annual folds; quarterly persistence and overlapping horizons limit inference. Source timing is dated official provenance at PIT B rather than an immutable archive. Weekday BDay is the repository convention, not a full exchange holiday calendar. The frozen draw cache cannot support new monthly dates, new scales or later market history; those were not invented. No official multi-card joint/tail score or prospective validation was run.

**Final verdict: NO.** ECB SPF specifically failed this frozen location test. This does not imply every new information source fails. Preserve all results, leave ECB untuned, and proceed only in a separately frozen study to INFO-01's pre-ranked source#2, **Fed SLOOS**. Do not add SLOOS to this experiment and do not submit from this history.

## Tests, Git and recovery

Research-specific tests:20 passed before outcome access. Directly affected LOCATION-01 and INFO-01 tests:75 passed before PRE. Final research, affected, full repository and common-toolkit counts are recorded in `execution_audit.json` after execution. Main is protected against the recorded `e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8`; all178 frozen parent protected files are checked unchanged.

Branch: `track2/location-02-ecb-spf-alpha`. The result commit, remote critical-file verification, clean-tree proof and recovery archive hash are recorded in the external private verification receipt, avoiding a self-referential Git commit. Private recovery contains original source bytes/receipts, frozen baseline caches and ledger, source/parser/model/tests, predictions/losses, null distributions/bootstrap, report, stage status/logs, PRE/RESULT metadata and a Git bundle. ZIP CRC, per-file SHA256 and whole-archive SHA256 are verified before durable preservation.
