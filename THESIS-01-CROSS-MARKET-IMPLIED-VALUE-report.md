## Executive summary (read this first)

**THESIS-01 failed its precommitted test.** A frozen, linear cross-market tension signal shifted the V5.1 no-text prior's location on 2018–2023 sparse public-panel origins. The one-business-day lag-safe final marginal CRPS ratio is **1.00622** (7,450 asset–horizon cells); contemporaneous is **1.00539**. Below 1 would be an improvement. The final lag-safe Spearman IC is **−0.0194**, and directional sign accuracy is **50.29%**. Both negative controls perform comparably. The validation ratio was already **1.00442**. Do not continue to THESIS-02 on this evidence; do not submit this research model.

## Provenance and precommitment

- Repository parent: V13-R2 remote commit `e263a37cfcbdb2fb0cbcdc0a624492d7fe0dcc47`. The THESIS-01 model/rules were committed **before** the final result was opened: remote commit `39b558f6bf565a6057cd419c0975255127aa1a80`. The final results commit only adds grouped research output, this report, and a diagnostics/min-fit-count reporting correction. No hyperparameter, model structure, asset or horizon changed after evaluation.
- Original V12 and V13 Git objects `123115f3a7f04450f6a525594f9e39b88aa0037b` and `253a0c733d77917599f1dbf21eae914cd136d69a` exist locally. GitHub refused direct archive refs for both (`422 Object does not exist`). The original SHAs have **not** been remotely archived. This did not block THESIS-01.
- The V12 R2 catalog, label semantics and horizon list supply public data rules only. No V12/V13 forecast, covariance, copula, or joint-world output enters the prediction. The V5.1 Numeric V3 and `text-first-v5.1` routing code produces the prior. Continuous research origins have **no frozen origin-specific text corpus**, so this is explicitly the **no-text V5.1 ablation**, not the complete text-enabled card forecast or an official score.

## Frozen specification

| Component | Rule fixed before the final score |
|---|---|
| Universe | 25 public daily assets: FX, UST rates, and daily factor returns; 22 eligible in final evaluation |
| Innovation | Level: `X_t − X_(t−1)`; daily return: `X_t` without another difference |
| Scale | Prior 252 business rows, at least 200 observations, sample SD; shifted one row, floor `1e−8`; standardized innovation clipped to `[−8, 8]` |
| Implied value | Linear leave-one-target-out conditional expectation, prior 504 rows and at least 252 observed target innovations, zero imputation for missing standardized increments; ridge `0.1 × trace(Cov(X))/p + 1e−4` |
| Signal | `T_i,t = Z_i,t − E[Z_i,t | other-market Z]`; same-day peers separately from lag-safe peers at `t−1` |
| Beta | Development-only signed slope from centered tension to normalized future target, ridge `0.1 × n`, minimum 24 mature training pairs; frozen throughout validation and final holdout, no sign restriction |
| Target | Level change or cumulative daily return over 5, 21, 63, 126, 189 business days; native value and `Q=Y/(sigma_t sqrt(h))` retained privately |
| Forecast | Actual V5.1 no-text draws plus identical `beta × T × sigma_t × sqrt(h)` in every draw. Dispersion, order, rank, and tail differences stay exactly as V5.1 emitted them |
| Randomness | Seed 19; 500 draws FX/rates, 1,000 factor draws. Controls use separate fixed seed 4101 |

Training uses historical rows strictly earlier than the origin. The current target value never appears among its own implied-value predictors. At an origin, the scale uses rows before it. V5.1 reads only its pre-origin series. The lag-safe model fits historical target-versus-prior-day-peer pairs and uses prior-day peers at inference. Future mutation, self-exclusion, seed and additive-only tests passed.

## Coverage and chronological protocol

The public prefixes cover 25 assets, with the combined business calendar from 2000-01-03 through 2024-12-18. Availability differs by asset; BRL and INR end in 2013, and the CNY prefix is too sparse for the fixed 252-row scale in final evaluation. The research origin grid starts 2001-01-02 and takes every 21st business day through 2023-12-12: **286 sparse origins**. The same and lag variants each produce **125,324 finite daily dense signal cells**; dense signals are only shape diagnostics.

- Development: 2001–2012 origins; a target is eligible for fitting only when its recorded end has matured by 2012-12-31. There are **115 fitted asset–horizon slopes** in each primary variant, with at least **69 mature training pairs** among fitted slopes.
- Validation: 2013–2017, strictly later than development. Coefficients remain frozen.
- Final one-shot holdout: 2018–2023, **22 assets, 7,450 eligible sparse asset–horizon cells**. No final outcome was read to choose a model or parameter.
- A 21-business-day grid still leaves overlap between long 189-day labels. Cell counts are descriptive, not independent sample counts or statistical significance claims.

**Exposure limitation:** this is a revised-history public-panel experiment, not verified point-in-time data. About **31.5% of development label cells** and **94.16% of scored final cells** fall after that asset's first public card date. They are kept in an outside-repository private ledger. This limits claims about an unexposed benchmark and bars extrapolation to the official 0.9541 score.

## Marginal CRPS results

Each CRPS is divided by that cell's ex-ante `sigma_t sqrt(h)` before grouping. The displayed group CRPS is the mean of those unitless cell scores; the ratio is the thesis mean divided by the V5.1 mean on **the same cells and draws**. Overall combines validation and final. No official composite or joint score is inferred from these values.

| Lag-safe subset | Cells | V5.1 CRPS | THESIS CRPS | Ratio |
|---|---:|---:|---:|---:|
| Overall OOS, 2013–2023 | 14,070 | 0.622112 | 0.625484 | **1.005419** |
| Validation, 2013–2017 | 6,620 | 0.588483 | 0.591083 | **1.004419** |
| Final, 2018–2023 | 7,450 | 0.651995 | 0.656051 | **1.006221** |
| Final FX | 3,300 | 0.590847 | 0.595886 | **1.008528** |
| Final rates | 2,040 | 0.815337 | 0.814957 | **0.999534** |
| Final factor/equity | 2,110 | 0.589708 | 0.596516 | **1.011543** |
| Final horizon 5 | 1,496 | 0.631742 | 0.634947 | **1.005073** |
| Final horizon 21 | 1,496 | 0.572508 | 0.574091 | **1.002765** |
| Final horizon 63 | 1,496 | 0.620462 | 0.623228 | **1.004457** |
| Final horizon 126 | 1,490 | 0.675694 | 0.679240 | **1.005249** |
| Final horizon 189 | 1,472 | 0.761421 | 0.770683 | **1.012163** |

The same-day diagnostic gives **1.005389** on the same 7,450 final cells. Its apparent advantage of about 0.00083 in ratio is too small and not a model-selection rule; neither variant beats the prior. The mean absolute lag-safe location shift is **6.13% of the V5.1 draw SD** in final cells. Its final sign accuracy is **50.29%**, close to chance. Pooled final lag-safe tension-versus-normalized-target Pearson is **0.0270** and Spearman is **−0.0194**. The per-asset/horizon slopes, IC, sign accuracy, CRPS and shifts are in the grouped `asset_horizon_summary.csv`, never per origin in Git.

## Negative controls and era stability

| Final signal | Marginal CRPS ratio | Interpretation |
|---|---:|---|
| Lag-safe primary | **1.006221** | Worsens V5.1 |
| Time-shuffled tension, refitted beta | 1.000931 | Nearly unchanged prior; primary is worse |
| Permuted peer-to-coefficient mapping, refitted beta | 1.005020 | Comparable to primary |

The peer control permutes inference-time other-market values across the frozen fitted coefficient mapping, excluding the current target. Merely renaming regression columns and refitting would leave a linear prediction unchanged and would be a meaningless control.

| Era | Lag-safe sparse IC | OOS CRPS ratio | Status |
|---|---:|---:|---|
| Pre-GFC | 0.0031 | — | Development signal diagnostic only |
| GFC / aftermath | 0.0778 | — | Development signal diagnostic only |
| Post-GFC low-rate | 0.0493 | 1.004923 | Validation/final origins in this era |
| COVID | −0.0201 | 1.007342 | Final |
| Inflation / hiking | 0.0178 | 1.005113 | Final |

The development episodes do not have independent OOS V5.1 CRPS in this run. All scored eras worsen the prior. The sign and IC do not establish a durable effect. A small rates subgroup improvement of 0.05% does not rescue the precommitted all-market hypothesis; selecting only that subgroup now would be outcome-driven selection.

## Verification and disposition

- Full repository test run: **370 passed, 2 skipped**, after installing the missing `jsonschema` execution dependency. Ten focused THESIS-01 tests cover return/level units, prior-only scale, leave-one-target-out, unit invariance, stable seed, lag-safe peers, location-only draws, future mutation and negative-control effectiveness.
- The private signal/label panel and one-shot per-origin outcome ledger remain outside Git. Their SHA-256 digests and draw settings are in `artifact_manifest.json`; public JSON and CSV contain only grouped results.
- This is a **negative result for the exact simple linear tension hypothesis tested**, not a proof that all possible cross-market alpha is impossible. It supplies no warrant for leader detection, scenario mixture, path generation, V14, or official submission.

**READY_FOR_THESIS_02 = NO**

**READY_FOR_ONE_SHOT_SUBMISSION = NO**
