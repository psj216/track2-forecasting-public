## Executive summary (read this first)

# LOCATION-01 — Recovery, continuous crossfit results and frozen transfer blocker

**The complete continuous-ledger evaluation is preserved. The overall study is NOT complete: 13 of 24 transfer cards stop at the frozen geometry guard. No guard, feature, model, fold, alpha grid, hyperparameter, draw, or pre-result specification was changed.**

Best nonzero Ridge sequence M1 has marginal ratio 1.0057385846264797, worse than V5.1. Nonlinear M5 has ratio 0.999453240516707, capturing only 0.092668% of available oracle headroom. Neither meets the precommitted success gates.

READY_FOR_LOCATION_02 = **NO** (completed continuous evaluation). NEXT_RESEARCH_AXIS = **UNRESOLVED_TRANSFER_BLOCKED** (the frozen CONTEXT-01 transfer check cannot finish). READY_FOR_ONE_SHOT_SUBMISSION = **NO**.

All values are RESEARCH_PROXY_ONLY and research-exposed chronological crossfit, not official leaderboard scores or independent out-of-sample evidence.

## Commit lineage and recovery

Branch: `track2/location-01-predictable-oracle-shift`
PRE_RESULT_LOCATION01_SHA: `b05f73ace0d300968198f6563ca3eb4ba0d94257`
Frozen parent: `b24d2602fc70e4e004a6d4b5496f3b0be00948e2`
RESULT_SHA: the result commit containing this report; exact SHA is in the separate preservation receipt.

Remote branch and frozen commit were fetched. Local and remote HEAD both matched the pre-result freeze. The original runtime remained accessible. All requested files existed. Ledger and feature SHA-256, schema columns and all 1,251 baseline-cache hashes matched the frozen public manifest. There are 1,250 eligible ledger origins; the extra last cache has no eligible mature ledger cells.

All M1–M5 models in folds 1–4, nonlinear diagnostics and training controls were already complete. All 24 matched-as-of transfer model sets were also complete. No completed learning was rerun. Predictions contain finite values in every expected model/fold evaluation cell. Post-freeze prediction/model hashes were recorded as recovered evidence; the pre-result manifest did not contain expected prediction/model hashes.

Full ledger: 135,994 cells / 25 assets, 2001-01-02–2024-12-10. Evaluation ledger: 82,184 cells / 780 origins, 2010-01-05–2024-12-10.

## Runtime changes outside the frozen implementation

The original scoring loop was partitioned into thirteen disjoint origin chunks. Each chunk was saved immediately. The exact frozen aggregation, negative-control comparison and 2,000-replicate year bootstrap then ran on those stored arrays. Identical prediction matrices were loaded once instead of being repeatedly decompressed by lazy NPZ indexing. This was an I/O change only. Eight unfinished scoring attempts were stopped and resumed once; completed chunks were retained. Twelve origins spanning all folds were independently recomputed through the shared scorer: 36,480 candidate cell scores, plus matching baseline and oracle scores, were exactly equal.

## Frozen features and information boundary

M0 is zero shift. M1 contains metadata. M2 adds baseline forecast state. M3 adds own price history. M4 adds other markets at t-1 with self exclusion. M5 adds regime summaries. Training, chronological inner alpha selection, the 189-business-day purge and maturity boundary, numerical caps, original baseline draws and all feature windows remain frozen. Full protocol: `backtesting/location01/frozen_protocol.json` and `LOCATION-01-PRECOMMIT.md`.

## Oracle headroom

Perfect location ratio on the **matching evaluation ledger**: **0.409983325012**. Full training+evaluation ledger oracle ratio: **0.310345472962**. Capture is `(1 - candidate ratio) / (1 - matching oracle ratio)` and is not clipped. Negative capture is retained.

## Primary Ridge results

| Model | Ratio | Normalized CRPS | Capture fraction | Delta MSE | Delta R2 | Pearson | Spearman | Sign accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M0 | 1.000000 | 0.587221 | 0.000000 | 1.041529 | -0.003931 | — | — | 0.000000 |
| M1 | 1.005739 | 0.590591 | -0.009726 | 1.057051 | -0.018893 | -0.004986 | 0.003356 | 0.504721 |
| M2 | 1.023961 | 0.601291 | -0.040610 | 1.081748 | -0.042697 | 0.075552 | 0.101363 | 0.538730 |
| M3 | 1.031352 | 0.605632 | -0.053138 | 1.095484 | -0.055937 | 0.070324 | 0.092917 | 0.536163 |
| M4 | 1.042734 | 0.612315 | -0.072429 | 1.120476 | -0.080027 | 0.067276 | 0.090862 | 0.537343 |
| M5 | 1.047026 | 0.614835 | -0.079702 | 1.126193 | -0.085538 | 0.060535 | 0.084890 | 0.536795 |

| Model | Mean absolute shift / SD | Calibration intercept | Calibration slope |
| --- | --- | --- | --- |
| M0 | 0.000000 | 0.063858 | — |
| M1 | 0.100069 | 0.064288 | -0.040803 |
| M2 | 0.225164 | 0.057619 | 0.258671 |
| M3 | 0.242787 | 0.059009 | 0.224277 |
| M4 | 0.280286 | 0.059124 | 0.189218 |
| M5 | 0.283715 | 0.058580 | 0.169341 |

## Secondary nonlinear diagnostic

| Model | Ratio | Normalized CRPS | Capture fraction | Delta MSE | Delta R2 | Pearson | Spearman | Sign accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M0 | 1.000000 | 0.587221 | 0.000000 | 1.041529 | -0.003931 | — | — | 0.000000 |
| M1 | 1.003003 | 0.588985 | -0.005090 | 1.052686 | -0.014684 | 0.005608 | 0.010528 | 0.505244 |
| M2 | 0.999737 | 0.587067 | 0.000446 | 1.049868 | -0.011968 | 0.102777 | 0.132650 | 0.551324 |
| M3 | 1.004371 | 0.589788 | -0.007408 | 1.065557 | -0.027091 | 0.078769 | 0.117049 | 0.544108 |
| M4 | 1.000620 | 0.587585 | -0.001051 | 1.052370 | -0.014380 | 0.097044 | 0.131653 | 0.550813 |
| M5 | 0.999453 | 0.586900 | 0.000927 | 1.049588 | -0.011699 | 0.102664 | 0.137445 | 0.552638 |

| Model | Mean absolute shift / SD | Calibration intercept | Calibration slope |
| --- | --- | --- | --- |
| M0 | 0.000000 | 0.063858 | — |
| M1 | 0.090984 | 0.063324 | 0.048665 |
| M2 | 0.165624 | 0.068167 | 0.438656 |
| M3 | 0.173401 | 0.067511 | 0.320701 |
| M4 | 0.178104 | 0.064079 | 0.408167 |
| M5 | 0.176582 | 0.064133 | 0.431942 |

M0 correlation and calibration slope are undefined. A zero prediction is counted directionally correct only when the true standardized location delta is exactly zero; M0 sign accuracy is not a coin-flip benchmark.

## Outer folds

ridge

| Model | 2010–2013 | 2014–2017 | 2018–2020 | 2021–2024 |
| --- | --- | --- | --- | --- |
| M0 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| M1 | 1.008265 | 1.005542 | 0.997817 | 1.010656 |
| M2 | 1.017003 | 1.032820 | 1.027623 | 1.017361 |
| M3 | 1.032971 | 1.040353 | 1.031418 | 1.019374 |
| M4 | 1.035711 | 1.041011 | 1.056550 | 1.039114 |
| M5 | 1.038979 | 1.051240 | 1.059392 | 1.038927 |

nonlinear

| Model | 2010–2013 | 2014–2017 | 2018–2020 | 2021–2024 |
| --- | --- | --- | --- | --- |
| M0 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| M1 | 1.002058 | 1.001416 | 0.997718 | 1.010555 |
| M2 | 0.979239 | 1.002058 | 1.010282 | 1.007775 |
| M3 | 0.996367 | 1.000582 | 1.009628 | 1.011856 |
| M4 | 0.978901 | 0.998321 | 1.020037 | 1.007110 |
| M5 | 0.975975 | 0.998555 | 1.019182 | 1.005794 |

Ridge M1 improves only one of four outer folds. Nonlinear M5 improves two of four. The success rule requires at least three, ratio <=0.97, capture >0.05 and clear separation from all three training controls.

## Negative controls

| Control | Best model | Ratio | Primary / control ratio 95% CI |
| --- | --- | --- | --- |
| A_label_time | M1 | 1.005739 | [0.9999999999999997, 1.0000000000000002] |
| B_wrong_feature_date | M1 | 1.005739 | [1.0, 1.0] |
| C_asset_label | M2 | 1.041221 | [0.9543320204847677, 0.9764786784256467] |

Control A permutes training labels in time within asset/horizon. B uses strictly earlier wrong feature dates. C rotates standardized training labels across assets. Ridge does not separate from A or B; the frozen all-controls gate is **False**. The future-mutation control D passes the recovered test suite. The full transfer geometry control E is **blocked**, not passed.

## Bootstrap intervals

| Model | Ratio 95% CI | Capture 95% CI |
| --- | --- | --- |
| ridge M0 | [1.0, 1.0] | [0.0, 0.0] |
| ridge M1 | [1.0004421367961054, 1.0110189025892546] | [-0.018795671428712406, -0.0007730039452163633] |
| ridge M2 | [1.004226824931861, 1.043266570886858] | [-0.071444718035413, -0.007282517159039768] |
| ridge M3 | [1.0097056759830199, 1.0532095733552336] | [-0.08850828079255113, -0.01692197903801118] |
| ridge M4 | [1.018714698831407, 1.064121583966423] | [-0.10663843556728887, -0.0333381639853977] |
| ridge M5 | [1.022770005234745, 1.0690420093261919] | [-0.11511881425971329, -0.039621264166425425] |
| nonlinear M0 | [1.0, 1.0] | [0.0, 0.0] |
| nonlinear M1 | [0.9975815864127393, 1.0078824806462514] | [-0.013087372026406172, 0.004112361462361152] |
| nonlinear M2 | [0.9837730531786733, 1.0141735207682094] | [-0.02306902348868102, 0.028534887864818583] |
| nonlinear M3 | [0.9904289425750195, 1.017581720458899] | [-0.028861308558651166, 0.01683536901456781] |
| nonlinear M4 | [0.9828656865596576, 1.01711893377353] | [-0.02828410609090532, 0.030093121834919776] |
| nonlinear M5 | [0.9816376287283864, 1.016138194991437] | [-0.026527789786428172, 0.032803926530077306] |

All intervals use 2,000 paired calendar-year block replicates with seed 1903. Cells are not bootstrapped independently. Overlapping long horizons still create dependence across adjacent years. These are exposed-research descriptive intervals, not independent generalization proof.

## Single/multi-cell and family transfer — blocked

All 24 frozen transfer model sets are available; no card label was used for training. Each transfer was attempted under the unchanged guard. Eleven complete card records are retained privately; thirteen cards fail. Single-cell completion is 5/13 and multi-cell completion is 6/11. No aggregate single/multi-cell score, family score, F1 safety verdict or best-card subset score is released because coverage is incomplete.

| Family | Required cards | Complete cards | Blocked cards | Aggregate status |
| --- | --- | --- | --- | --- |
| T2-F1 | 6 | 4 | 2 | NOT_COMPUTED_INCOMPLETE_COVERAGE |
| T2-F2 | 6 | 3 | 3 | NOT_COMPUTED_INCOMPLETE_COVERAGE |
| T2-F3 | 6 | 2 | 4 | NOT_COMPUTED_INCOMPLETE_COVERAGE |
| T2-F4 | 6 | 2 | 4 | NOT_COMPUTED_INCOMPLETE_COVERAGE |

## Exact transfer blocker

The frozen `geometry_guard` requires exact equality of default `np.argsort` indices before and after a uniform location shift. At floating-point precision, some originally distinct neighboring draws round to the same value after addition. Their sorting indices can differ even though no strict-order reversal occurs. For all thirteen first failures, centered differences satisfy the frozen tolerance. The maximum centered difference error is 8.881784197001252e-16; strict-order reversals total zero; originally distinct adjacent values rounded to ties total 94.

The frozen guard still returns False. No tolerance was relaxed, no tie jitter was added, no sort algorithm was replaced, no candidate was changed and no card was dropped. The default report writer would incorrectly imply complete guard success, so it was not run. This blocker report preserves only established evidence. Failure card IDs and models appear in `transfer_blocker_audit.json`; individual card outcomes and scores remain private.

## Validation and preserved outputs

LOCATION-specific tests rerun in recovery: **16 passed**. Frozen full-repository log SHA-256 verified: **431 passed / 2 skipped**. Frozen shared-toolkit log SHA-256 verified: **250 passed**. No implementation or frozen protocol change occurred. Group and horizon metrics for all models are in `group_summary.csv` and `horizon_summary.csv`; complete control metrics and bootstrap outputs are in the associated JSON files.

## Decision and exact continuation

READY_FOR_LOCATION_02 = **NO**
NEXT_RESEARCH_AXIS = **UNRESOLVED_TRANSFER_BLOCKED**
READY_FOR_ONE_SHOT_SUBMISSION = **NO**

The specified historical observable feature universe and frozen models do not demonstrate the required predictable location signal on the continuous ledger. This does not establish impossibility for all information sources. The final axis cannot yet be chosen under the frozen protocol because CONTEXT-01 depends on the complete card-transfer ratio.

Continue from the numerical transfer guard blocker. Reuse the verified ledger, features, predictions, continuous losses and all 24 frozen transfer models. Any guard repair must be explicitly documented and authorized separately; do not silently alter this pre-result freeze or treat these transfer results as complete. No model retraining or architecture search is needed for recovery.
