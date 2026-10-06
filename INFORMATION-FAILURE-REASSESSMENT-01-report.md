## Executive summary (read this first)

# INFORMATION-FAILURE-REASSESSMENT-01 — Why did new information fail?

Central conclusion: **INCONCLUSIVE**. Exactly one future axis: **DIRECTION-TO-LOCATION-01**. All three prior primary verdicts remain **NO**. This study does not fit, tune, recalibrate or submit a forecasting model. It diagnoses immutable out-of-fold predictions.

## Frozen reconstruction and scope

Parent: `ca9b467d48b2fc145faa5bfe549975206c8a811f`. Diagnostic implementation PRE: `1a417f0522e04e2ecf1598c80e0bf0ebb1e7b5fe`. The PRE was pushed and remotely verified before any final diagnostic aggregation. All three primary ratios and original cell losses reproduce to 1e-12. The maximum ratio discrepancy is 2.44e-15. The scorer is the recovered pinned `qfbench2-common` v2.4.3 fair ensemble CRPS; per-cell loss retains the prior past-scale normalization. No scoring formula is reimplemented.

ECB: EUR, 227 cells, five 2020–2024 annual folds, original pooled-horizon model. SLOOS: all six originally admitted UST assets, 2,616 cells, eight 2017–2024 annual folds and separate asset/horizon models. SPD: original primary UST 2Y/5Y, 552 cells, five 2020–2024 folds. Every source keeps all five horizons. These are different ledgers, not a controlled source comparison. SLOOS's original documented read-only-mask compatibility amendment did not alter scientific specification; this diagnosis never executes the prior fitting code.

The realized outcomes and complete cell ledger remain in the private recovery archive. Aggregate diagnostics are public. Missing model states are reported rather than regenerated. See lineage, reproduction and unified manifests for all prior PRE/RESULT SHAs, input hashes and schemas.

## Cross-source failure matrix

| Source | Primary CRPS | Cell Spearman | Cell sign accuracy | Release sign accuracy | Release Spearman | Cell calibration slope | Release slope | Pred/true magnitude | Best diagnostic shrinkage | Best diagnostic sign | Worst year | Worst share positive annual damage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ECB | 1.5628 | 0.1379 | 0.5771 | 0.5434 | 0.0639 | 0.1368 | 0.1047 | 1.1619 | 0.9805 | 0.9711 | 2020.0000 | 0.4623 |
| SLOOS | 1.1485 | -0.0442 | 0.5134 | 0.4967 | -0.0535 | -0.1406 | -0.1457 | 0.4980 | 0.9999 | 1.0000 | 2021.0000 | 0.3316 |
| SPD | 1.4208 | 0.4044 | 0.6612 | 0.6639 | 0.3854 | 0.2328 | 0.2162 | 1.2529 | 0.9858 | 0.9553 | 2023.0000 | 0.8629 |

A sign score must be assessed with class balance and rank. A model that mostly predicts the more frequent sign can have high raw accuracy without discriminating directions. Release balancing gives each original release equal total mass; origin/year balancing are also reported. Weighted Spearman uses weighted mid-CDF ranks. No IID-cell significance is claimed. SLOOS keeps eight folds: the 4/5 and 3/5 descriptive rules scale to 7/8 and 5/8.

### ECB: direction and uncertainty

Direction label **WEAK**; positive release-balanced direction/rank in 2/5 original folds. Release accuracy 0.5434, balanced accuracy 0.5505, positive-truth share 0.5133, Spearman 0.0639. Release-block 95% accuracy CI [0.4308141025641026, 0.6516874999999998]; Spearman CI [-0.20875684904960462, 0.34068685201875265]. Year-block Spearman CI [-0.36184454700378743, 0.3403004329869436]. There are 20 release blocks and 5 year blocks, with 5,000 paired replicates each. These intervals describe an exposed fixed-prediction ledger, not refit uncertainty or independent validation.

### SLOOS: direction and uncertainty

Direction label **NONE**; positive release-balanced direction/rank in 4/8 original folds. Release accuracy 0.4967, balanced accuracy 0.4708, positive-truth share 0.5557, Spearman -0.0535. Release-block 95% accuracy CI [0.42811447811447806, 0.5603226403226401]; Spearman CI [-0.23383181541959483, 0.11498401428326303]. Year-block Spearman CI [-0.2621018565743462, 0.16571880573278283]. There are 33 release blocks and 8 year blocks, with 5,000 paired replicates each. These intervals describe an exposed fixed-prediction ledger, not refit uncertainty or independent validation.

### SPD: direction and uncertainty

Direction label **STRONG**; positive release-balanced direction/rank in 4/5 original folds. Release accuracy 0.6639, balanced accuracy 0.6697, positive-truth share 0.5813, Spearman 0.3854. Release-block 95% accuracy CI [0.5824999999999999, 0.7452981029810298]; Spearman CI [0.2268032226402016, 0.5182298569547448]. Year-block Spearman CI [0.016223957388906446, 0.5488195238757868]. There are 41 release blocks and 5 year blocks, with 5,000 paired replicates each. These intervals describe an exposed fixed-prediction ledger, not refit uncertainty or independent validation.

## Sign-correct versus sign-wrong damage

| Source | Partition | Cell fraction | CRPS ratio | Harmed fraction | Overshoot fraction | Net damage share |
| --- | --- | --- | --- | --- | --- | --- |
| ECB | SIGN_CORRECT | 0.5771 | 1.1284 | 0.3435 | 0.4809 | 0.1467 |
| ECB | SIGN_WRONG | 0.4229 | 2.3457 | 1.0000 | 0.5208 | 0.8533 |
| ECB | ZERO_TIE | 0.0000 | N/A | N/A | N/A | 0.0000 |
| SLOOS | SIGN_CORRECT | 0.5134 | 0.8680 | 0.1854 | 0.2956 | -0.4383 |
| SLOOS | SIGN_WRONG | 0.4866 | 1.4210 | 1.0000 | 0.2797 | 1.4383 |
| SLOOS | ZERO_TIE | 0.0000 | N/A | N/A | N/A | 0.0000 |
| SPD | SIGN_CORRECT | 0.6612 | 1.0291 | 0.3370 | 0.4904 | 0.0594 |
| SPD | SIGN_WRONG | 0.3388 | 3.8210 | 1.0000 | 0.7112 | 0.9406 |
| SPD | ZERO_TIE | 0.0000 | N/A | N/A | N/A | 0.0000 |

The release-balanced, horizon and year partitions remain in sign_partition_summary.csv. Release fractions are nonexclusive: one release can contain both correct and wrong signs. A correct-direction pure translation cannot worsen convex location CRPS while it stays between the original median and truth. Sign-correct damage therefore implicates overshooting, rather than failure of the CRPS formula. No sign-defined subset becomes a primary result.

## Magnitude and fixed diagnostic translations

Post-hoc OLS and Theil-Sen calibration are descriptive only, never applied. The entire frozen prediction is multiplied by the universal grid; a separate curve uses only its sign and fixed SD units. Each point is **POST_HOC_DIAGNOSTIC_ONLY / INVALID_FOR_CONFIRMATORY_USE**. A favorable exposed minimum cannot rescue a prior NO. No interpolation or source-specific search occurs.

| Source | Lambda | Diagnostic CRPS | Leave-one-block gain robust |
| --- | --- | --- | --- |
| ECB | 0.0000 | 1.0000 | 0.0000 |
| ECB | 0.0200 | 0.9950 | 0.0000 |
| ECB | 0.0500 | 0.9888 | 0.0000 |
| ECB | 0.1000 | 0.9816 | 0.0000 |
| ECB | 0.2000 | 0.9805 | 0.0000 |
| ECB | 0.3000 | 0.9990 | 0.0000 |
| ECB | 0.5000 | 1.0921 | 0.0000 |
| ECB | 0.7500 | 1.2958 | 0.0000 |
| ECB | 1.0000 | 1.5628 | 0.0000 |
| SLOOS | 0.0000 | 1.0000 | 0.0000 |
| SLOOS | 0.0200 | 0.9999 | 0.0000 |
| SLOOS | 0.0500 | 0.9999 | 0.0000 |
| SLOOS | 0.1000 | 1.0007 | 0.0000 |
| SLOOS | 0.2000 | 1.0049 | 0.0000 |
| SLOOS | 0.3000 | 1.0127 | 0.0000 |
| SLOOS | 0.5000 | 1.0384 | 0.0000 |
| SLOOS | 0.7500 | 1.0867 | 0.0000 |
| SLOOS | 1.0000 | 1.1485 | 0.0000 |
| SPD | 0.0000 | 1.0000 | 0.0000 |
| SPD | 0.0200 | 0.9949 | 1.0000 |
| SPD | 0.0500 | 0.9894 | 1.0000 |
| SPD | 0.1000 | 0.9858 | 1.0000 |
| SPD | 0.2000 | 0.9964 | 0.0000 |
| SPD | 0.3000 | 1.0238 | 0.0000 |
| SPD | 0.5000 | 1.1082 | 0.0000 |
| SPD | 0.7500 | 1.2499 | 0.0000 |
| SPD | 1.0000 | 1.4208 | 0.0000 |

| Source | Fixed sign SD shift | Diagnostic CRPS | Correct-sign diagnostic ratio | Gain not one block |
| --- | --- | --- | --- | --- |
| ECB | 0.0200 | 0.9953 | 0.9822 | 0.0000 |
| ECB | 0.0500 | 0.9889 | 0.9561 | 0.0000 |
| ECB | 0.1000 | 0.9804 | 0.9147 | 0.0000 |
| ECB | 0.2000 | 0.9711 | 0.8391 | 0.0000 |
| SLOOS | 0.0200 | 1.0000 | 0.9850 | 0.0000 |
| SLOOS | 0.0500 | 1.0006 | 0.9631 | 0.0000 |
| SLOOS | 0.1000 | 1.0029 | 0.9282 | 0.0000 |
| SLOOS | 0.2000 | 1.0130 | 0.8641 | 0.0000 |
| SPD | 0.0200 | 0.9947 | 0.9907 | 1.0000 |
| SPD | 0.0500 | 0.9871 | 0.9770 | 1.0000 |
| SPD | 0.1000 | 0.9753 | 0.9548 | 1.0000 |
| SPD | 0.2000 | 0.9553 | 0.9130 | 1.0000 |

| Source | Top absolute-shift fraction | Net damage share | Gross damage share |
| --- | --- | --- | --- |
| ECB | 0.0100 | 0.0519 | 0.0463 |
| ECB | 0.0500 | 0.2249 | 0.1855 |
| ECB | 0.1000 | 0.4793 | 0.3901 |
| ECB | 0.2000 | 0.8516 | 0.7199 |
| SLOOS | 0.0100 | 0.1284 | 0.0747 |
| SLOOS | 0.0500 | 0.4350 | 0.2752 |
| SLOOS | 0.1000 | 0.6030 | 0.4162 |
| SLOOS | 0.2000 | 0.8321 | 0.6137 |
| SPD | 0.0100 | 0.1726 | 0.1082 |
| SPD | 0.0500 | 0.6491 | 0.4068 |
| SPD | 0.1000 | 0.9780 | 0.6131 |
| SPD | 0.2000 | 1.2247 | 0.7898 |

All rows stay in the main ledger. Sensitivity omits one existing block only to diagnose concentration, never to produce a new model or favorable main result. A diagnostic gain is called nonconcentrated only if every leave-one-release and leave-one-year ratio remains below 1 and no one block contributes more than half of gross positive block gains.

## SPD 2023 retained: failure mechanism

2023 accounts for 0.8629 of positive annual net damage and 1.1305 of total net damage. Its release-balanced CRPS ratio is 6.5105, sign accuracy 0.4722, Spearman -0.0897, and calibration slope -0.0384. Sign-correct harmed fraction 0.7321, sign-correct overshoot fraction 0.7679.

Held-out source extremeness is measured against each preserved original train scaler: mean max absolute z 4.7164, p95 5.3847, max 5.3847; fraction above 3 is 1.0000. Mean absolute predicted raw shift 3.1151, actual raw error 0.4226, baseline SD 0.5924. The five mean absolute linear feature contributions are [2.5966333526449064, 1.7781532823872253, 0.27222791560240733, 0.11594100245204234, 0.06509410426726728], in the frozen SPD feature order. This separates direction, amplitude and source extrapolation; it is not evidence that a newly invented 2023 regime should be excluded.

## Source age and horizon alignment

| Source | Horizon | Release CRPS | Sign accuracy | Spearman | Calibration slope | Pred |delta| | True |delta| |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ECB | 5.0000 | 1.6957 | 0.4458 | -0.0695 | 0.0255 | 0.8860 | 0.8403 |
| ECB | 21.0000 | 1.8232 | 0.4500 | -0.1321 | 0.0253 | 0.8860 | 0.7130 |
| ECB | 63.0000 | 1.5659 | 0.6535 | 0.1640 | 0.1307 | 0.9314 | 0.7469 |
| ECB | 126.0000 | 1.5320 | 0.6053 | 0.1696 | 0.1605 | 0.9323 | 0.7494 |
| ECB | 189.0000 | 1.5267 | 0.5880 | 0.1755 | 0.1909 | 0.9807 | 0.8108 |
| SLOOS | 5.0000 | 1.0605 | 0.6048 | 0.0837 | 0.0718 | 0.4554 | 0.8100 |
| SLOOS | 21.0000 | 1.0752 | 0.5061 | 0.0881 | 0.2419 | 0.3443 | 0.7941 |
| SLOOS | 63.0000 | 1.1157 | 0.5026 | -0.0713 | -0.1040 | 0.3786 | 0.9512 |
| SLOOS | 126.0000 | 1.2105 | 0.4462 | -0.1426 | -0.2653 | 0.5880 | 1.0417 |
| SLOOS | 189.0000 | 1.2733 | 0.4394 | -0.2321 | -0.3180 | 0.7005 | 1.2168 |
| SPD | 5.0000 | 1.0729 | 0.5488 | 0.0848 | 0.2356 | 0.5551 | 0.9181 |
| SPD | 21.0000 | 1.3871 | 0.5813 | 0.1759 | 0.1842 | 0.9538 | 0.8888 |
| SPD | 63.0000 | 1.4948 | 0.6346 | 0.2651 | 0.2499 | 1.5754 | 1.2642 |
| SPD | 126.0000 | 1.4883 | 0.7635 | 0.4577 | 0.2416 | 2.1221 | 1.4161 |
| SPD | 189.0000 | 1.6997 | 0.8000 | 0.6317 | 0.2811 | 3.0622 | 1.6866 |

| Source | Business-day age | Cells | Releases | Release CRPS | Sign accuracy | Spearman |
| --- | --- | --- | --- | --- | --- | --- |
| ECB | 0-20 | 86.0000 | 18.0000 | 1.7847 | 0.5444 | 0.0784 |
| ECB | 21-40 | 57.0000 | 12.0000 | 1.8141 | 0.4694 | -0.1453 |
| ECB | 41-60 | 69.0000 | 15.0000 | 1.3065 | 0.6200 | 0.3297 |
| ECB | 61-90 | 15.0000 | 3.0000 | 0.8152 | 0.8667 | 0.6614 |
| ECB | >90 | 0.0000 | 0.0000 | N/A | N/A | N/A |
| SLOOS | 0-20 | 798.0000 | 28.0000 | 1.2034 | 0.4925 | -0.0765 |
| SLOOS | 21-40 | 564.0000 | 20.0000 | 1.0819 | 0.5207 | -0.0411 |
| SLOOS | 41-60 | 630.0000 | 21.0000 | 1.1548 | 0.5444 | -0.0429 |
| SLOOS | 61-90 | 624.0000 | 22.0000 | 1.1119 | 0.5025 | 0.0654 |
| SLOOS | >90 | 0.0000 | 0.0000 | N/A | N/A | N/A |
| SPD | 0-20 | 348.0000 | 37.0000 | 1.4557 | 0.6707 | 0.4299 |
| SPD | 21-40 | 204.0000 | 22.0000 | 1.3383 | 0.6439 | 0.3225 |
| SPD | 41-60 | 0.0000 | 0.0000 | N/A | N/A | N/A |
| SPD | 61-90 | 0.0000 | 0.0000 | N/A | N/A | N/A |
| SPD | >90 | 0.0000 | 0.0000 | N/A | N/A | N/A |

Age and short/long-horizon criteria are frozen in experiment_spec.json. They are hypotheses, not tuned cutoffs or proposed favorable subsets. Sparse and inactive bins remain visible.

## Repeated releases, coefficients and target geometry

ECB: 227 cells, 48 origins, 20 unique releases; 93.4% of cells share a release across multiple origins. Adjacent original standardized coefficient cosine mean 0.9500. Lowest within-asset/horizon SD quintile gross positive damage share 0.0933; raw vs standardized release Spearman 0.1666 vs 0.0639.

SLOOS: 2616 cells, 91 origins, 33 unique releases; 98.6% of cells share a release across multiple origins. Adjacent original standardized coefficient cosine mean 0.8286. Lowest within-asset/horizon SD quintile gross positive damage share 0.2727; raw vs standardized release Spearman -0.1095 vs -0.0535.

SPD: 552 cells, 59 origins, 41 unique releases; 62.0% of cells share a release across multiple origins. Adjacent original standardized coefficient cosine mean 0.9435. Lowest within-asset/horizon SD quintile gross positive damage share 0.0322; raw vs standardized release Spearman 0.4105 vs 0.3854.

The full SD-quintile table and held-out scaler diagnostics are preserved. Positive SD makes raw and standardized direction exactly identical. For a fixed standardized prediction, a smaller baseline SD makes the raw shift smaller, not larger. Small SD may inflate original normalized training targets; these diagnostics cannot establish that causal training mechanism without a separately frozen study. The past normalization scale in CRPS is a different quantity. Annual coefficients can be unstable without proving a pre-outcome regime rule. No pre-existing regime variables sufficient for AXIS D were recovered.

## Interpretation review and disclosed protocol deviation

The frozen automatic aggregator returned **INCONCLUSIVE / NEW-INFORMATION-SEARCH-02**. Its implementation imposed an additional **original-full-shift-only** requirement on the sign-correct gate. SPD fails that stricter gate: original sign-correct CRPS ratio is 1.0291. This failure is preserved in frozen_aggregation_decision.json and frozen_next_axis_decision.json; it is never relabeled as a pass.

However, the user-defined AXIS E requires direction/rank and small fixed shifts to lose their useful evidence. SPD contradicts that requirement: release-balanced direction/rank survive, four original folds are positive, and every predeclared fixed-sign whole-ledger curve improves without one release/year driving the gain. Thus the automated fallback E is not an eligible substantive conclusion.

The final **post-hoc interpretive recommendation** is exactly **DIRECTION-TO-LOCATION-01**, applying the directional sign-correct condition to the predeclared fixed-magnitude diagnostics: at 0.05/0.10/0.20 SD, SPD sign-correct ratios are 0.9770/0.9548/0.9130, with whole-ledger and block-concentration checks passing. No future constant is chosen. This is an explicitly disclosed interpretation deviation, **not a passed precommitted automatic gate**, new candidate, prior-NO rescue, or independent evidence. A later experiment must freeze its own mapping before seeing new outcomes. The central cross-source conclusion remains INCONCLUSIVE: SPD supplies direction-with-bad-magnitude evidence; SLOOS does not; ECB is weak and unstable.

## Failure attribution, headroom and one next axis

ECB: **F2_MAGNITUDE_OVERSHOOT**. Quantitative evidence: `{'release_sign_accuracy': 0.5433974358974358, 'release_spearman': 0.06388432992175727, 'release_calibration_slope': 0.10474092952193245, 'original_sign_correct_ratio': 1.1284034407609889, 'sign_correct_harmed_fraction': 0.3435114503816794, 'best_nonzero_shrinkage_ratio': 0.9805362439175243, 'best_fixed_sign_ratio': 0.9711250498105508, 'fold_calibration_slopes': [0.09886361503767424, 0.28401072107602954, -0.8727182540986879, -7.308188157281533, 2.487341067870965]}`. Secondary contributors: ['Attenuated post-hoc release-balanced calibration slope', 'Annual calibration-sign instability; not an identified pre-outcome regime']. Attribution is descriptive rather than causal.

SLOOS: **F7_REPEATED_RELEASE_ARTIFACT**. Quantitative evidence: `{'release_sign_accuracy': 0.496695896695897, 'release_spearman': -0.053456654285663194, 'release_calibration_slope': -0.14572513731829256, 'original_sign_correct_ratio': 0.8679633117326615, 'sign_correct_harmed_fraction': 0.18540580789277736, 'best_nonzero_shrinkage_ratio': 0.9998621760404794, 'best_fixed_sign_ratio': 1.0000104095966678, 'fold_calibration_slopes': [0.052413958066160185, 1.091177953705132, -0.5678501388037477, 0.26285302032513985, -0.4747560175003056, -2.0647683954152405, -0.0497063101087153, 0.15152536231586788]}`. Secondary contributors: ['Annual calibration-sign instability; not an identified pre-outcome regime']. Attribution is descriptive rather than causal.

SPD: **F2_MAGNITUDE_OVERSHOOT**. Quantitative evidence: `{'release_sign_accuracy': 0.6638598528842431, 'release_spearman': 0.3854381509674189, 'release_calibration_slope': 0.21615654867254708, 'original_sign_correct_ratio': 1.0290879175597214, 'sign_correct_harmed_fraction': 0.336986301369863, 'best_nonzero_shrinkage_ratio': 0.9857595008612428, 'best_fixed_sign_ratio': 0.9553398418675999, 'fold_calibration_slopes': [0.9435325459596855, 2.5000090859629425, 0.647167283601841, -0.038441517805793794, 0.25116429023288356]}`. Secondary contributors: ['Attenuated post-hoc release-balanced calibration slope', 'Annual calibration-sign instability; not an identified pre-outcome regime']. Attribution is descriptive rather than causal.

**INCONCLUSIVE**. SPD direction/ranking survives release/year balancing and four annual folds; three predeclared fixed-sign diagnostics improve original sign-correct CRPS materially and whole-ledger gains survive all leave-one-release/year checks. Full frozen magnitude still fails. The original stricter automated gate and its inconsistency with fallback E are disclosed in interpretation_review.json. Next: **DIRECTION-TO-LOCATION-01**, and nothing else is selected or executed. Gate-by-gate evidence is in next_axis_decision.json. Large perfect-location oracle headroom is mathematical possibility, not evidence that source information predicts that error.

## Limits and verification

All outcomes were previously exposed. No independent OOS claim, new alpha, new official score or submission follows. Diagnostic minimum selection and many descriptive comparisons are outcome-exposed and can overfit. Different source assets/origin counts prevent causal cross-source ranking. Release and annual blocks are few and correlated; 5,000 resamples do not create new information events. Source states can repeat across many cells; source_age changes within a packet. Bootstrap holds predictions fixed. No prior model is retrained. Every prior prediction file, draw array and input hash is checked before aggregation. 2023 stays in all primary SPD diagnostics. Research-specific, affected, full repository and common-toolkit test receipts, Git lineage, protected main SHA and recovery verification are recorded in execution_audit.json and the private completion receipt.
