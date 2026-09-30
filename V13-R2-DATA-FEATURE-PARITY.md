## Executive summary (read this first)

V13-R2 audits the reconstructed training data and return-feature semantics without changing the copula or model architecture. Its 25 assets, 950 accepted origins, 414 fit origins, 38,134 fit cells and 52,453 total cells match the verified V12 source exactly. The new 24-card proxy yields V13-R2 A **1.669 overall**, **1.175 post-fit**, with post-fit marginal **1.143** and tail **1.207**. This does not establish the archived original V13-A 0.893 or satisfy the prerequisite for V14.

## Newly recovered source and provenance

The local Git object `123115f3a7f04450f6a525594f9e39b88aa0037b` contains the original V12 dataset builder and artifact. The artifact SHA-256 is `72fc4fab0457bee1caecd2eb8a4c80af7dc9469b403d0a1cf2e67f4c327d63d3`, exactly the V12 report's hash. The local Git object `253a0c733d77917599f1dbf21eae914cd136d69a` contains the original V13 source; its final evaluation JSON SHA-256 is `776666c14ba145e7d0e7ba0456c386131589fcaec480923ec495a6697c62b0cb`, exactly the attached archive. Their `units/` tree is identical to the current checkout. These objects were found in local Git refs, not in a missing workspace. This supersedes the earlier claim that the original implementation details were irrecoverable. This R2 experiment stays on its own branch and does not replace the reconstructed V13 or V14 refs.

## Exact structural audit

| Measure | R1 reconstruction | V13-R2 and original V12 |
|---|---:|---:|
| Assets | 23 | **25** |
| Accepted origins | 950 | **950** |
| Fit-origin definition | 366 origins with at least 3 mature 21BD cells | **414 accepted fit dates** |
| Fit cells | 26,945 | **38,134** |
| Total target cells | not comparable under the R1 selected dates | **52,453** |
| First / last accepted date | 2001-01-01 / 2019-03-11 | **2001-01-02 / 2020-02-18** |
| Five-factor explained share | 65.83% | **66.07%** in reconstructed R2; original **57.16%** |

The missing assets were **BAB** (1,636 fit cells) and **UST_20Y** (586 fit cells). They exist in public daily panels but the previous loader admitted only explicit card target assets. The original catalog also includes sufficiently long context assets, using their first panel cutoff as a conservative label boundary if they never appear as a target.

The original calendar starts 2001-01-02, takes every fifth business day, purges 2009-01-01 through 2009-09-30, and retains a date only with at least three valid cells across at least two assets. The R1 loader started from a global union-panel date, took every fifth such row, and kept the first 950 regardless of purge/validity. The two fit-date sets have **zero exact shared dates**. Its `fit_origins=366` also counted a different event: at least three mature 21BD cells. On the corrected dataset that same PCA eligibility rule yields **407** dates, while the accepted fit-date count is **414**. Both values are now recorded separately.

For the original 38,134 fit cells, applying R1 label rules at those *same* dates leaves 30,011:

| Exclusive exclusion reason | Cells |
|---|---:|
| Two assets filtered out | 2,222 |
| Return path incorrectly required every global-panel date to be populated | 4,813 |
| Global-index horizon endpoint absent | 1,088 |

The remaining difference from 30,011 to the actual R1 26,945 is a **net 3,066 cells from shifting the origin grid**. This is an arithmetic counterfactual decomposition, not 3,066 individually matchable original cells: no original fit date equals an R1 fit date. The private 51,750-row fit-cell ledger records origin date, asset, horizon, actual target end, first-target boundary, counterfactual R1 endpoint, and exclusion reason. It is excluded from Git.

The R2 builder reconstructs the original dates, asset universe, target maturity, first-target boundaries, and availability masks from public prefixes. We regenerated the reference dataset from commit `123115f`: asset order, all 950 origin dates, every mask bit and every present target-end date match the R2 builder. Dividing R2 native labels by the original as-of daily scale and `sqrt(horizon)`, with the original clip, reproduces every original masked label within floating-point tolerance. R2 keeps **native-unit labels** for its existing reconstructed decoder; it does not load the original model coefficients.

## Return features and one frozen refit

The previous extractor applied `np.diff` to daily factor returns. R2 instead uses those daily observations as increments. Momentum and trend derive from cumulative returns; volatility and higher moments use the increments. Global cross-asset movement features treat return columns as increments while level columns are differenced. Level assets keep their previous local feature semantics. Both offline training and runtime use the same asset-kind mapping. Future-panel mutation tests check the as-of boundary.

After these source-driven corrections, the V12-R2 artifact was fit **once**, before reading the new proxy scores. The V13 copula, 32-neighbor count, 70/30 mixture and support gate were not tuned. The public artifact is `qfbench2_track_forecasting/v12/artifacts_v13_r2.json`, SHA-256 `1c321d6681747cd322f42bf4b60edf5c43107ab7faa1917f8311bea7fcc538d0`. The private rank bank was rebuilt from its 414 fit origins and 38,134 cells; the public manifest carries the bank SHA. V13 runtime performs no fit.

## Corrected revised-history proxy

The same fixed 24 public cards, V5.1 baseline draws, 2,000 draws per card, seed 19 and corrected cumulative-return truth were used. It is a revised-history research diagnostic; the original archived 24 pseudo-origins differ and cannot be treated as the same test. Ratios are relative to V5.1 on the same card. Overall is the geometric mean of case composite ratios, while component columns are medians.

| Candidate | Overall | Marginal | Joint | Tail | Post-fit 19 | Post-fit marginal | Post-fit joint | Post-fit tail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R1 A | 1.655 | 1.144 | 1.500 | 1.089 | 1.204 | 1.152 | 1.444 | 1.213 |
| R2 A | **1.669** | 1.105 | 1.659 | 1.112 | **1.175** | 1.143 | 1.397 | 1.207 |
| R2 B | 1.629 | 1.105 | 1.986 | 1.112 | 1.194 | 1.143 | 1.588 | 1.207 |
| R2 C | 1.651 | 1.105 | 2.440 | 1.112 | 1.174 | 1.143 | 1.797 | 1.207 |

R2 A's overall proxy is slightly worse even though its post-fit aggregate improves. The five-factor explained share is still **66.07%**, not the original **57.16%**: the reconstructed model consumes native labels and has different normalization, covariance and fitting details. Structural dataset identity cannot be mistaken for model identity. The exposed proxy did not determine a new candidate or parameter. Post-fit marginal/tail are still above V5.1, so V14 remains blocked.

## Verification and limits

- 362 collected tests: **360 passed, 2 skipped**. F1/F2/F3/F4 offline runtime smoke produced finite, correctly shaped output with marginal identity across A/B/C. The original V12 target tensor audit and deterministic rerun are separate checks.
- The R2 artifact and grouped evaluation are public. Private per-origin masks, target values, case-level outcomes and the historical bank remain outside Git.
- The local original V12/V13 Git objects are stronger evidence than the reports. Their GitHub preservation must be verified separately; the R2 reconstruction branch is not their original commit lineage.
- No official submission, V14 implementation, tuning to 0.893, or claim of point-in-time vintage certification was made.
