# LOCATION-01R transfer guard recovery

**Executive summary.** The old exact argsort-index guard rejected valid uniform translations because floating-point rounding created ties. All 13 recorded first failures were reproduced exactly. The repaired, pre-frozen numerical guard passes all 24 cards and 144 model-card pairs without changing forecasts or refitting. The fixed primary M1 transfer is mixed: single composite ratio 1.076213221, multi composite ratio 0.987752716. Continuous primary remains NO; NEXT_RESEARCH_AXIS is NEW_INFORMATION_REQUIRED; one-shot submission readiness is NO.

## Frozen lineage and scope

- Repository: `psj216/track2-forecasting-public`.
- Recovery branch: `track2/location-01r-transfer-guard`.
- Parent partial result: `4c35ef22e9b1bafe2d9fc009e6b3151e09afb723`.
- Original PRE_RESULT_LOCATION01_SHA: `b05f73ace0d300968198f6563ca3eb4ba0d94257`.
- PRE_RESULT_LOCATION01R_SHA: `7554bb851658306172654864c10fd40d41e4edb2`, published and independently fetched before transfer scoring.
- This report belongs to the subsequent RESULT commit; its SHA is supplied by the remote preservation receipt to avoid a self-referential commit identifier.

Ledger, feature schema, features, predictions, losses, models, alpha, folds, purge, labels, baselines, deltas, shifts, seeds, card universe, scorer, marginal/joint/tail formulas and continuous success gates are unchanged. Only the existing geometry_guard delegates to the repaired validator. New recovery modules snapshot, validate, score and aggregate existing artifacts. No continuous evaluation or model fitting was rerun. Original LOCATION-01 sources/results and the old branch are preserved.

## Recovery and old blocker reproduction

Existing private runtime inputs survived. SHA-256 values match frozen manifests/preservation receipts; all 1,251 origin cache hashes were checked. Card inputs also match the preserved recovery archive byte-for-byte. Schema and all audit files were recovered. Each frozen card prediction/candidate was snapshotted before transfer aggregation.

| Artifact | SHA-256 |
| --- | --- |
| ledger.parquet | 5a421fa5c10745c69469c683797bf42f4abf54288e8082984bcf39fda76968a6 |
| features.npy | bfd4a3bbe34e4237575e0bbfd801ae8151fb611ac8b7b678f2762c816fdd9665 |
| predictions.npz | 135ef536f2378211a1ec5187ee8eae784f73ee86481ebe193acd2acc0b0e1c62 |
| losses.npz | d71b2fa7f60cd3f288df5776e4602af255353a1cbb254a89d5e7994977ab4c39 |
| transfer_models.pkl | a2c882a669b9a00ea8427d409faea0f0b112f4882d97b82dab370a4d7164efdc |

Before repair, all 13 blocked first card/model failures reproduced exactly: 94 previously distinct adjacent draws rounded to ties, zero strict reversals, and maximum centered error / shift nonuniformity 8.881784197001252e-16. Exact argsort index identity is not a mathematical invariant after rounded uniform addition. This was a validation false rejection, not an observed forecast geometry violation.

## Numerical invariant frozen before scoring

For each float64 cell, tau = 32 * eps * max(1, maxabs(baseline), maxabs(candidate), abs(median(candidate-baseline))). The validator requires equal nonempty shapes, finite inputs/intermediates, a uniform cell shift and unchanged median-centered geometry within tau (rtol=0). It stably sorts baseline indices only for checking; an adjacent baseline gap greater than tau must not become a candidate gap below -tau. Ties are permitted; meaningful strict reversals are rejected.

Variance and centered second moments are auxiliary checks. Their frozen bound is 4*tau*max(1,centered_magnitude) + tau^2 + 8*gamma_n*max(1,both_variances,both_second_moments), with gamma_n=n*eps/(1-n*eps). The fixed multiplier and moment rule were justified by roundoff propagation and frozen before transfer aggregates. The guard does not mutate, reorder, jitter, quantize or round the forecast. No tolerance depends on scores or card identity.

Four bounded six-card evaluation commands saved each card immediately. All 24/24 cards, all 144/144 model-card checks pass, with zero true violations and zero strict reversals. Across all checks, maximum shift residual is 1.4210854715202004e-14 and maximum centered residual is 4.263256414560601e-14. Candidate reconstruction matches each immutable snapshot exactly. The previous 11 completed cards have 66 model-card baseline/candidate/oracle component dictionaries exactly unchanged.

Validation: 14 new adversarial tests; the two synthetic old-guard tie failures were demonstrated before repair. Tests cover ordinary/large translations, rounded ties, reversals, nonuniform shifts, scaling, variance, reorder, NaN/Inf, deterministic behavior and nonmutation. LOCATION-related tests: 30 passed. Full repository: 445 passed / 2 skipped. Public-safe validation: all 104 units pass.

## Transfer scoring and aggregation

All 24 historically exposed cards are included: 13 single-cell, 11 multi-cell, six per F1–F4. These are research proxy diagnostics, not independent OOS or official hidden scores. The existing LOCATION-01 recompute/scorer and geometric aggregation are reused unchanged. Baseline composite is normalized to 1. Ratios below 1 improve. Primary transfer model M1 was fixed from the prior continuous best nonzero Ridge; all models are reported and no transfer-best model is selected. Component ratios use the matching applicable cards; single-cell joint is not applicable. Raw arithmetic component means are separate descriptive quantities and their ratios need not equal geometric card ratios.

| Model | Single composite | Single capture | Multi composite | Multi capture |
| --- | --- | --- | --- | --- |
| M0 | 1.000000000 | 0.000000% | 1.000000000 | 0.000000% |
| M1 | 1.076213221 | -10.791444% | 0.987752716 | 11.537765% |
| M2 | 1.154182237 | -21.831500% | 1.047516529 | -44.763765% |
| M3 | 1.151885821 | -21.506338% | 1.052739667 | -49.684313% |
| M4 | 1.128099666 | -18.138327% | 1.077753633 | -73.249151% |
| M5 | 1.153537435 | -21.740199% | 1.093984975 | -88.540167% |

Primary M1:

| Group/component | Candidate ratio | Perfect-location ratio | Oracle capture |
| --- | --- | --- | --- |
| Single composite | 1.076213221 | 0.293762526 | -10.791444% |
| Multi marginal | 0.993494627 | 0.591900948 | 1.594067% |
| Multi joint | 0.963304626 | 0.504953467 | 7.412510% |
| Multi tail | 1.001645982 | 0.797223446 | -0.811722% |
| Multi composite | 0.987752716 | 0.893850465 | 11.537765% |

Oracle capture is (1-candidate_ratio)/(1-oracle_ratio); it is not clipped. The perfect-location oracle optimizes marginal center location, not joint or composite score. Capture is undefined when oracle ratio equals 1, and negative-denominator captures should not be treated as conventional positive headroom.

## Family transfer and F1 safety

| Family | Marginal ratio | Joint ratio | Tail ratio | Composite ratio | Oracle composite | Composite capture |
| --- | --- | --- | --- | --- | --- | --- |
| T2-F1 | 0.994520939 | 0.913802683 | 1.000000000 | 0.978122994 | 1.706268702 | -3.097547% |
| T2-F2 | 1.139301273 | N/A | 1.044802800 | 1.116147222 | 0.417239345 | -19.930519% |
| T2-F3 | 0.994741587 | 1.006598611 | 1.003019703 | 1.000385303 | 0.450869282 | -0.070166% |
| T2-F4 | 1.043224052 | N/A | 1.061026739 | 1.049588844 | 0.178440921 | -6.035944% |

F1 raw arithmetic means (six cards for marginal/tail; joint has five applicable cards):

| Component | Baseline mean | M1 candidate mean | Geometric ratio |
| --- | --- | --- | --- |
| marginal | 0.105351256 | 0.099171718 | 0.994520939 |
| joint | 0.002751492 | 0.002719735 | 0.913802683 |
| tail | 0.018263807 | 0.018263807 | 1.000000000 |

F1 composite ratio = 0.9781229935676898. F1_SAFETY_VERDICT = CARD_LOCATION_TRANSFER_POSITIVE. Marginal improves, joint remains safely below the frozen 1.10 damage threshold and composite improves. This does not support the PATH_REQUIRED pattern. The F1 perfect-location composite is 1.706268702471187, above baseline: marginal-perfect shifts are not composite-optimal, and existing baseline component normalization can magnify joint loss. Therefore its composite capture of -3.097547% has a negative headroom denominator and is not evidence that the improving M1 composite worsened.

Multi-cell geometric joint ratio improves to 0.963304626 while its arithmetic joint mean rises from 0.941363860 to 0.972798830. This reflects heterogeneous per-card losses and the unchanged geometric aggregation; no scoring formula was adjusted to resolve that difference.

## Continuous result preserved, not recomputed

Original ledger: 1,250 origins / 135,994 cells / 25 assets, 2001-01-02 through 2024-12-10. Continuous evaluation: 780 origins / 82,184 cells, 2010-01-05 through 2024-12-10. Same-ledger perfect-location normalized CRPS ratio = 0.4099833250124908. Continuous scores, controls and intervals below are copied from the prior frozen result.

| Model | Ridge ratio | Nonlinear ratio | Ridge capture | Nonlinear capture |
| --- | --- | --- | --- | --- |
| M0 | 1.000000000 | 1.000000000 | 0.000000% | 0.000000% |
| M1 | 1.005738585 | 1.003003292 | -0.972614% | -0.509018% |
| M2 | 1.023960765 | 0.999736895 | -4.061032% | 0.044593% |
| M3 | 1.031352352 | 1.004370719 | -5.313808% | -0.740779% |
| M4 | 1.042734090 | 1.000620239 | -7.242861% | -0.105122% |
| M5 | 1.047025569 | 0.999453241 | -7.970210% | 0.092668% |

Outer fold ratios:

| Estimator/model | Fold 1 | Fold 2 | Fold 3 | Fold 4 |
| --- | --- | --- | --- | --- |
| ridge/M1 | 1.008264767 | 1.005542314 | 0.997817096 | 1.010655943 |
| ridge/M2 | 1.017003288 | 1.032820297 | 1.027622912 | 1.017361342 |
| ridge/M3 | 1.032971403 | 1.040353348 | 1.031418239 | 1.019373526 |
| ridge/M4 | 1.035710654 | 1.041011193 | 1.056549563 | 1.039114023 |
| ridge/M5 | 1.038979057 | 1.051240209 | 1.059391845 | 1.038926538 |
| nonlinear/M1 | 1.002058103 | 1.001416006 | 0.997718373 | 1.010554852 |
| nonlinear/M2 | 0.979238868 | 1.002058213 | 1.010281874 | 1.007775281 |
| nonlinear/M3 | 0.996367066 | 1.000582132 | 1.009628023 | 1.011856499 |
| nonlinear/M4 | 0.978900938 | 0.998321242 | 1.020036891 | 1.007109537 |
| nonlinear/M5 | 0.975974604 | 0.998555112 | 1.019181720 | 1.005793544 |

Prior 2,000-replicate calendar-year block bootstrap (15 years, all asset/horizon cells resampled together):

| Estimator/model | Ratio 95% CI | Capture 95% CI |
| --- | --- | --- |
| ridge/M1 | [1.000442137, 1.011018903] | [-1.879567%, -0.077300%] |
| ridge/M2 | [1.004226825, 1.043266571] | [-7.144472%, -0.728252%] |
| ridge/M3 | [1.009705676, 1.053209573] | [-8.850828%, -1.692198%] |
| ridge/M4 | [1.018714699, 1.064121584] | [-10.663844%, -3.333816%] |
| ridge/M5 | [1.022770005, 1.069042009] | [-11.511881%, -3.962126%] |
| nonlinear/M1 | [0.997581586, 1.007882481] | [-1.308737%, 0.411236%] |
| nonlinear/M2 | [0.983773053, 1.014173521] | [-2.306902%, 2.853489%] |
| nonlinear/M3 | [0.990428943, 1.017581720] | [-2.886131%, 1.683537%] |
| nonlinear/M4 | [0.982865687, 1.017118934] | [-2.828411%, 3.009312%] |
| nonlinear/M5 | [0.981637629, 1.016138195] | [-2.652779%, 3.280393%] |

Best nonzero Ridge M1 ratio 1.005738585; best nonlinear diagnostic M5 ratio 0.999453241, capture 0.092668%. Neither establishes the precommitted continuous success gate.

| Negative control | Best control | Control ratio | Primary/control ratio 95% CI |
| --- | --- | --- | --- |
| A_label_time | M1 | 1.005738585 | [1.000000000, 1.000000000] |
| B_wrong_feature_date | M1 | 1.005738585 | [1.000000000, 1.000000000] |
| C_asset_label | M2 | 1.041221496 | [0.954332020, 0.976478678] |

A and B do not separate from primary M1; C separates. The joint success requirement to beat every control is not met. D future mutation retains as-of features and real V5.1 draws. The old public E control record remains historically blocked; the additional LOCATION-01R immutable-candidate and complete numerical guard audits now establish the requested translation geometry checks on all cards. No original controls file is rewritten.

## Final decision

| Field | Value |
| --- | --- |
| CONTINUOUS_LOCATION_GATE | NO |
| TRANSFER_DIAGNOSTIC | MIXED |
| F1_SAFETY_VERDICT | CARD_LOCATION_TRANSFER_POSITIVE |
| READY_FOR_LOCATION_02 | NO |
| NEXT_RESEARCH_AXIS | NEW_INFORMATION_REQUIRED |
| READY_FOR_ONE_SHOT_SUBMISSION | NO |

The frozen M1 single-cell result worsens substantially; multi-cell and F1 have modest local improvement, while F2/F4 worsen and F3 is nearly neutral. There is no coherent strong single/multi transfer. The existing numeric observable information universe has not extracted enough oracle location headroom; NEW_INFORMATION_REQUIRED is the descriptive next research axis. No card/text causal ablation was run, and these exposed-card diagnostics do not establish a new information channel or submission readiness.

## Preservation boundary

Public outputs contain full-group aggregate scores and geometry metadata/hashes. Individual card outcomes/components/ratios remain outside Git in the private recovery artifacts. The public transfer_card_summary.csv contains guard flags, shape-independent metadata and immutable candidate hashes, while the private CSV contains components and ratios. The public artifact_manifest.json records public file hashes and private artifact hash/counts. Final remote fetch verification and durable private archive receipt are saved separately after the RESULT commit.
