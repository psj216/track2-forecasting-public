## Executive summary (read this first)

# DIRECTION-TO-LOCATION-01 — Conservative directional location translation

Primary verdict: **NO**. Next axis: **NEW-INFORMATION-SEARCH-02**. Primary is exactly frozen SPD sign × **0.10** × original V5.1 SD. Secondary 0.05/0.20 and OOD3 do not select an amplitude or change this verdict. READY_FOR_SUBMISSION=false. No Development service was called and no submission was packaged.

## Frozen parent, direction and universe

Parent RESULT `fe62b9058ea6dc540f7548c6be96ccc4e8d04b92`. LOCATION04 RESULT `ca9b467d48b2fc145faa5bfe549975206c8a811f`, PRE `2e356b91dd98dae022b72494ea6d4c70a9a38ed7`. DTL PRE `e5058474ce1917f02fafab50e261f06f2fbf5bf2` was committed, pushed and remotely verified before any candidate CRPS. The original primary ratio, hashes and cell/release direction metrics reproduce within 1e-12. All original 552 cells, 59 forecast origins and 41 release IDs stay in scope: UST 2Y/5Y, five business-day horizons and original 2020–2024 folds. 2023 remains included.

All historical outcomes and the earlier fixed-sign curves were already exposed. 0.10 was specified by the user before this evaluation; 0.20 is not selected from the prior best curve. This is RESEARCH_EXPOSED, not independent OOS. Identical same-ledger fixed translations should reproduce earlier descriptive scores; this rerun is not new validation.

The original UST yield-level target, publication/PIT rules, 70-weekday expiry, past normalization scale, chronological purges and 2024-12-18 maturity cutoff remain unchanged. No SPD fit, V5.1 reconstruction, feature change, classifier or scale/tail/copula/rank change occurs. Draws and realized targets/cell losses are private.

## Overall primary and secondary scores

| Model | CRPS ratio | Oracle capture | Frozen source release direction | Frozen source release Spearman |
| --- | --- | --- | --- | --- |
| V5.1 | 1.000000 | 0.000000 | N/A | N/A |
| DTL_PRIMARY_010 | 0.975344 | 0.030996 | 0.663860 | 0.385438 |
| DTL_005 | 0.987093 | 0.016225 | 0.663860 | 0.385438 |
| DTL_020 | 0.955340 | 0.056143 | 0.663860 | 0.385438 |
| OOD3_DIAGNOSTIC | 0.980318 | 0.024743 | 0.663860 | 0.385438 |
| PERFECT_LOCATION_ORACLE | 0.204525 | 1.000000 | N/A | N/A |

The direction/rank columns describe the preserved continuous SPD prediction, not a newly fitted direction model. OOD3 uses that same source but abstains on extreme train-standardized states. The future-informed oracle has no predictive direction metric; its capture1 is mathematical by construction, not alpha. Baseline has no SPD direction shift. Scoring imports pinned qfbench2-common v2.4.3 fair CRPS and retains each original past-scale divisor; ratios use sums of cell losses. This is research marginal CRPS, not the official multi-card composite.

## Annual primary breakdown

| Year | Primary ratio | Capture | Cells | Releases |
| --- | --- | --- | --- | --- |
| 2020.000000 | 0.968747 | 0.050333 | 120.000000 | 9.000000 |
| 2021.000000 | 0.971828 | 0.032342 | 120.000000 | 9.000000 |
| 2022.000000 | 0.968234 | 0.037769 | 120.000000 | 9.000000 |
| 2023.000000 | 1.004076 | -0.006359 | 110.000000 | 9.000000 |
| 2024.000000 | 0.995520 | 0.006677 | 82.000000 | 9.000000 |

## Horizon and asset breakdown

| Business-day horizon | Primary ratio | Capture | Cells |
| --- | --- | --- | --- |
| 5.000000 | 0.987903 | 0.016282 | 118.000000 |
| 21.000000 | 0.984920 | 0.022069 | 116.000000 |
| 63.000000 | 0.971754 | 0.036763 | 112.000000 |
| 126.000000 | 0.965538 | 0.041807 | 106.000000 |
| 189.000000 | 0.974803 | 0.029066 | 100.000000 |

| Asset | Primary ratio | Capture | Cells |
| --- | --- | --- | --- |
| UST_2Y | 0.979078 | 0.024959 | 276.000000 |
| UST_5Y | 0.969265 | 0.042344 | 276.000000 |

Release-balanced versions and all release aggregates remain in the CSV artifacts. No favorable subgroup replaces the complete primary ledger.

## 2023 safety audit, fully retained

2023 primary ratio 1.004076; original full-magnitude SPD ratio 5.880883. Cell direction accuracy 0.509091, release accuracy 0.472222. Cells 110, releases 9; OOD fraction 1.000000. Mean raw shift -0.057639, mean absolute raw shift 0.059239. Its normalized total score delta is 0.221530 and signed share of overall delta -0.016115. Positive damage can coexist with net overall improvement; that share is not a positive-gain concentration measure. No 2023-excluded score is promoted or produced.

## Paired release and year block bootstrap

release: 41 blocks, 5000 replicates. Primary CRPS 95% CI `[0.9682914716493022, 0.9832879514692893]`; ratio delta vs V5.1 `[-0.03170852835069777, -0.01671204853071068]`; mean normalized CRPS delta `[-0.03698573700989331, -0.013504711313749094]`; oracle capture `[0.021773948833125802, 0.04090243592859956]`.

year: 5 blocks, 5000 replicates. Primary CRPS 95% CI `[0.9694603555869593, 0.9926564921560543]`; ratio delta vs V5.1 `[-0.03053964441304069, -0.0073435078439456625]`; mean normalized CRPS delta `[-0.04266029800467568, -0.003764887579082317]`; oracle capture `[0.011362244904291252, 0.038682888975756585]`.

All original assets/horizons of each sampled block stay together. Predictions are fixed; bootstrap does not refit direction. There is no naive IID-cell bootstrap. Five years and 41 related releases remain a small exposed information sample. Resampling does not create independent data.

## Negative controls

RELEASE_SIGN_SHUFFLE: `{'replicates': 2000, 'median_ratio': 0.9982505100719559, 'ratio_95_range': [0.9859884219335905, 1.010436588730883], 'mean_ratio': 0.9981991337676032, 'fraction_at_least_as_good': 0.0, 'add_one_p': 0.0004997501249375312, 'release_balanced_median_ratio': 0.9980643089848986, 'mean_direction_coverage': 1.0, 'min_direction_coverage': 1.0, 'primary_552_cell_denominator_unchanged': True, 'positive_fraction_range': [0.4365942028985507, 0.6086956521739131]}`.

DATE_PERMUTED_DIRECTION: `{'replicates': 2000, 'median_ratio': 0.9748626760046549, 'ratio_95_range': [0.9731812591608551, 0.9757154976098723], 'mean_ratio': 0.9745752793603031, 'fraction_at_least_as_good': 0.8325, 'add_one_p': 0.8325837081459271, 'release_balanced_median_ratio': 0.9750890411403064, 'mean_direction_coverage': 1.0, 'min_direction_coverage': 1.0, 'primary_552_cell_denominator_unchanged': True, 'positive_fraction_range': [0.5344202898550725, 0.5670289855072463]}`.

RANDOM_SIGN: `{'replicates': 2000, 'median_ratio': 1.0007454421051452, 'ratio_95_range': [0.995520102524588, 1.0058013202757816], 'mean_ratio': 1.0007485863915913, 'fraction_at_least_as_good': 0.0, 'add_one_p': 0.0004997501249375312, 'release_balanced_median_ratio': 1.001197751927592, 'mean_direction_coverage': 1.0, 'min_direction_coverage': 1.0, 'primary_552_cell_denominator_unchanged': True, 'positive_fraction_range': [0.5398550724637681, 0.5398550724637681]}`.

ONE_YEAR_SHIFT: `{'crps_ratio': 0.9807873498631394, 'coverage_cells': 422, 'coverage_fraction': 0.7644927536231884, 'unmatched_zero_shift': True, 'full_universe_used': True}`.

Mutation checks: `{'FUTURE_MUTATION': {'passed': True, 'origins_checked': 59, 'features_bitwise_invariant': True, 'frozen_shifts_bitwise_invariant': True}, 'OUTCOME_MUTATION': {'passed': True, 'all_primary_and_secondary_construction_bitwise_invariant': True, 'no_refit_claim': True}}`. Each stochastic control has exactly 2,000 fixed-seed replicates and the same 0.10 SD nonzero magnitude. Release packets are shuffled inside asset/horizon coverage strata, with nearest pre-outcome age matching; the release-shuffle null intentionally destroys historical association and is not a deployable PIT forecast. The date control permutes nonnegative activation delays and reuses only earlier frozen directions; it never backdates publication. It is a **safe delayed-mapping null**, not a literal unrestricted date permutation. Missing dated/prior-year donors receive zero shift on the unchanged full ledger, and coverage is reported. Random sign preserves exact cellular sign prevalence. These definitions were frozen before DTL scoring and are not selected after the outcome.

## Concentration and repeated information

NONCONCENTRATED=True.

release_id: leave-one-block ratio range [0.97431252664929, 0.9767567591339499]; largest gross positive block gain share 0.107017; every deletion stays <1: True.

year: leave-one-block ratio range [0.9722404189588277, 0.9786409789667245]; largest gross positive block gain share 0.444703; every deletion stays <1: True.

asset: leave-one-block ratio range [0.9692647776220313, 0.9790783089696288]; largest gross positive block gain share 0.525608; every deletion stays <1: True.

horizon: leave-one-block ratio range [0.9731864315748818, 0.9783626183202077]; largest gross positive block gain share 0.329022; every deletion stays <1: True.

41 release IDs, not 552 independent information events. Share of cells in releases repeated across origins 0.619565. Origins/release `{'count': 41.0, 'mean': 1.4390243902439024, 'std': 0.5024331043932554, 'min': 1.0, '25%': 1.0, '50%': 1.0, '75%': 2.0, 'max': 2.0}`; cells/release `{'count': 41.0, 'mean': 13.463414634146341, 'std': 5.495896473622887, 'min': 2.0, '25%': 10.0, '50%': 10.0, '75%': 20.0, 'max': 20.0}`. Original releases are not proven IID. No influential release, asset, horizon or year is removed from the primary.

## Frozen primary gates and next axis

Decision gate evidence: `{'primary_ratio': 0.9753436089359536, 'primary_oracle_capture': 0.03099581697885401, 'annual_folds_improved': 4, 'annual_folds_total': 5, 'controls_inferior': False, 'controls_clearly_inferior': False, 'release_upper_CI_below_one': True, 'year_upper_CI_at_most_one': True, 'release_direction_retained': True, 'nonconcentrated': True, 'secondary_used_to_decide': False}`. Secondary lead status: `['SECONDARY_SENSITIVITY_ONLY']`. Exactly one next axis: **NEW-INFORMATION-SEARCH-02**, not executed here. The full gate specification is experiment_spec.json. There is no analyst override, amplitude optimization, primary replacement or post-score scientific redesign. If the primary fails, no favorable secondary rescues it.

A positive result means only that frozen SPD direction with the user-fixed small translation improves V5.1 on this exposed ledger. It does not validate the old SPD magnitude model, independent alpha, an official score, or a submission.

## Verification and recovery

Research-specific, affected, full repository and pinned common-toolkit tests, protected parent file hashes, PRE/RESULT lineage, remote critical files, unchanged main and clean tree are recorded in execution_audit.json and the external completion receipt. The private recovery ZIP includes frozen inputs, candidate shifts/cell scores, null/bootstrap chunks, code/tests, report, STATUS and Git metadata, with CRC, member SHA256 and full archive SHA256 verification. The external receipt avoids circular commit/archive hashes.

## Control interpretation and completed tests

The primary score improves, including both paired block confidence intervals. The strict precommitted NO is specifically triggered by the delayed date-mapping control: its median is slightly better than the primary and 83.25% of replicates are at least as good. This control retains much of the frozen directional signal; it is a timing robustness/specificity challenge and does not establish that SPD information is useless. It is not an unrestricted date/packet permutation. The release-packet permutation and prevalence-matched random sign controls are clearly worse. Do not replace or remove the timing control after observing it, override the primary gate, or claim independent alpha.

Research-specific: **24 passed**. Affected: **79 passed, 5 historical private-fixture checks skipped**. Full repository: **728 passed, 7 skipped, 3 warnings**. Common toolkit: **250 passed**. Five skips belong to the old private recovery fixture/branch; the new tests verify actual frozen inputs, original scalers and protected parent hashes on this branch. Two integration skips require a published Docker scorer and a live CodaBench instance. Public unit firewall passed all 104 units; all 2188 protected parent file hashes remain identical.
