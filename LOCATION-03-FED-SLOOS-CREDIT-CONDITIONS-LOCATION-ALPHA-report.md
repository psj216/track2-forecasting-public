## Executive summary (read this first)

LOCATION-03 is complete. **DATASET_READY = true; LOCATION03_RESULT = NO.** The precommitted release-balanced SLOOS FULL5 model worsens normalized marginal continuous ranked probability score (CRPS, lower is better) by **14.85%** versus the exact frozen V5.1 forecasts. Release-block and year-block confidence intervals both remain above 1. No secondary ablation improves on V5.1. Close SLOOS for this frozen test and move to INFO-01's previously ranked third source, **NY Fed Survey of Primary Dealers**, in a separate pre-outcome frozen study.

This tests original-publication bank credit information predicting an existing forecast's standardized center error. It creates no forecasting architecture. The dataset is research exposed; no independent out-of-sample (OOS) or official-submission claim follows.

## Source readiness and original-release provenance

The official [Fed SLOOS archive](https://www.federalreserve.gov/data/sloos.htm) contains 115 enumerated archive entries for 1997–2024. The post-break 2013–2024 universe has 49 entries: **48 regular releases**, plus September 2020's supplementary Main Street survey excluded because it lacks the four fixed C&I fields. All 48 regular releases have original official provenance, verified publication dates and agreement of the four response-count vectors between official HTML and original PDFs. There are **47 complete change-feature releases** because the first admitted release has no predecessor. Admitted publication period: **2013-02-04 through 2024-11-12**.

PIT means point in time: information activates only when public. Without exact intraday evidence, a dated release activates at 23:59:59 America/New_York. Forecast feature lookup uses the previous repository business day's 16:00 New York cutoff. [October 2024's original release](https://www.federalreserve.gov/data/sloos/sloos-202410.htm) is dated **November 12, 2024** and is never activated in October. Source age expires after the fixed **100 business days**, without tuning.

The [official panel documentation](https://www.federalreserve.gov/data/sloos/about.htm) describes 2012 expansion. The admitted start is 2013, before outcome inspection. Later large-bank asset-threshold changes concern subgroup columns; the fixed ALL domestic-bank columns remain the primary extraction. Excluded household, CRE and supplementary questions do not enter the model. The official announcement/errata audit finds no admitted core C&I correction requiring historical rewriting.

The April 2024 Table 1 PDF link points to the wrong January PDF. That linked document was rejected for April. April HTML counts instead agree with the [official full April report](https://www.federalreserve.gov/data/documents/sloos-202404.pdf). Difficult original PDF fonts required OCR and five visually verified first-column digit corrections before outcomes. Private receipts preserve those checks. No current revised history, FRED series, third-party mirror or backcast was substituted. Undocumented silent edits cannot be proven absent; original archived material plus official errata is the evidence basis.

## Exact fields, denominators and five features

A count example illustrates the rule: applicable responses [2, 8, 45, 5, 0] give 100×(2+8−5−0)/60 = 8.3333 net percentage points. A bank answering “did not originate” is excluded from the five-category denominator. Never divide by the full survey panel.

The four fields are domestic all-bank C&I standards and demand for large/middle-market and small firms. Standards net positive means tightening; demand net positive means strengthening. Average the two firm groups equally for each level. Changes subtract the preceding verified regular release's same semantic level.

The primary features are exactly CREDIT_STANDARDS, CREDIT_DEMAND, DELTA_CREDIT_STANDARDS, DELTA_CREDIT_DEMAND and SOURCE_AGE_BUSINESS_DAYS. First-change missing values are not imputed. The frozen source ledgers document URL, publication proof, hashes, counts, applicable denominators, signs, amendments and exclusions.

## Universe, target and frozen model

Assets are exactly **UST_2Y, UST_5Y, UST_7Y, UST_10Y, UST_20Y and UST_30Y**; no other asset was added. Horizons are **5, 21, 63, 126 and 189** repository business days. Original monthly cache-ledger origins are used, not newly generated V5.1 forecasts. There are 144 source-calendar origins, 137 with active source, and 134 with a valid original UST ledger. Three source-active dates absent from that ledger (2017-07-04, 2019-01-01, 2023-07-04) are excluded without replacement. The ledger has 3,906 training/evaluation cells; **2,616 cells at 91 forward-evaluation origins** survive the frozen maturity rules. All target maturities are no later than **2024-12-18**.

For each cell, delta = (truth − median(V5.1 draws)) / SD(V5.1 draws), using the exact original draws and population SD. Separate asset/horizon models use Ridge alpha **1.0**, intercept, train-only weighted standardization and no model selection. Each training release has total weight 1: an origin's weight is 1 divided by that release's training-origin count. Both scaler and regression use these same weights. A prediction shifts every original draw by delta_hat×original_SD; shape, rank and scale are preserved to floating-point tolerance.

Development history is 2013–2016. Expanding annual research folds run **2017–2024**, with horizon-specific purge and target availability before the first test cutoff. All held-out-year release IDs are excluded from training. The fixed minimum is 12 unique training releases. **All 240 asset×horizon×year folds are valid**, with a minimum of 12 unique training releases. Unweighted FULL5 and the four fixed ablations are secondary descriptions and cannot replace the primary.

CRPS is the exact **qfbench2_common v2.4.3 fair ensemble scorer**. Each cell's CRPS is divided by its frozen past scale; the ratio is summed candidate normalized CRPS over summed V5.1 normalized CRPS on the same cells. Ratios are not averages of asset or year ratios.

## Primary and predeclared secondary results

| Model | CRPS ratio | Oracle capture | R² | Spearman | Sign accuracy |
| --- | --- | --- | --- | --- | --- |
| V5.1 | 1.0000 | 0.00% | -0.0316 | N/A | N/A (zero forecast) |
| SLOOS FULL5 release-balanced | 1.1485 | -21.43% | -0.3384 | -0.0442 | 51.34% |
| SLOOS FULL5 unweighted | 1.1707 | -24.64% | -0.3746 | -0.0510 | 50.54% |
| Levels-only | 1.0906 | -13.08% | -0.2208 | -0.1191 | 50.65% |
| Changes-only | 1.0637 | -9.20% | -0.1187 | 0.0096 | 50.27% |
| Standards-only | 1.1025 | -14.80% | -0.2429 | 0.0112 | 54.17% |
| Demand-only | 1.0723 | -10.44% | -0.1521 | -0.1843 | 48.81% |
| Perfect location oracle | 0.3072 | 100.00% | 1.0000 | 1.0000 | 100.00% |

V5.1 has a zero delta prediction; its sign accuracy is uninformative and is displayed N/A (the implementation's strict sign-agreement count is 0). Constant predictions have undefined correlations. The perfect-location row uses realized outcomes diagnostically and is not a feasible forecast.

FULL5 delta MSE is **2.477955**, versus V5.1 **1.909855**. Pearson is **-0.072241**; calibration slope **-0.140595**. Mean predicted absolute shift is **0.489023 original SD**, versus mean realized |delta| **0.981954**.

## Same-ledger oracle headroom

The perfect-location oracle shifts each original distribution median to truth, preserving shape. Its ratio is **0.307150933**, establishing **69.2849%** descriptive location headroom. Oracle capture = (1 − candidate ratio)/(1 − oracle ratio), without clipping. FULL5 captures **−21.4267%**: the failure is predictive, not a lack of descriptive headroom.

## Per-asset, horizon and annual folds

| Asset | Cells | Unique active releases | CRPS ratio | Oracle capture |
| --- | --- | --- | --- | --- |
| UST_2Y | 436 | 33 | 1.1263 | -15.59% |
| UST_5Y | 436 | 33 | 1.1443 | -20.75% |
| UST_7Y | 436 | 33 | 1.1573 | -23.66% |
| UST_10Y | 436 | 33 | 1.1613 | -24.75% |
| UST_20Y | 436 | 33 | 1.1659 | -26.34% |
| UST_30Y | 436 | 33 | 1.1524 | -24.79% |

| Horizon | Cells | Unique active releases | CRPS ratio | Oracle capture |
| --- | --- | --- | --- | --- |
| 5 | 546 | 33 | 1.0598 | -9.22% |
| 21 | 540 | 32 | 1.0602 | -9.91% |
| 63 | 528 | 32 | 1.0948 | -14.07% |
| 126 | 510 | 31 | 1.1969 | -27.34% |
| 189 | 492 | 30 | 1.2611 | -34.07% |

| Year | Cells | Unique active releases | CRPS ratio | Oracle capture |
| --- | --- | --- | --- | --- |
| 2017 | 330 | 5 | 0.9133 | 15.38% |
| 2018 | 300 | 4 | 0.9948 | 0.86% |
| 2019 | 330 | 6 | 1.3061 | -44.69% |
| 2020 | 360 | 5 | 1.3239 | -52.52% |
| 2021 | 360 | 5 | 1.2502 | -31.12% |
| 2022 | 360 | 5 | 1.0880 | -11.18% |
| 2023 | 330 | 5 | 1.1058 | -17.32% |
| 2024 | 246 | 5 | 1.0376 | -6.20% |

All six assets and all five horizons worsen. Only **2/8 annual folds** improve; the 2018 gain is small. Long horizons show the greatest degradation. Annual counts of active releases overlap across years and cannot be summed into independent events.

## Repeated-release dependence and block inference

There are **33 unique evaluated releases/change events**, an upper bound on distinct information events, not a demonstrated independent sample size. Each asset uses those same releases. Horizons use 33/32/32/31/30 releases respectively. Origins sharing a release are not treated as independent information observations. `effective_sample_summary.json` and `release_summary.csv` provide origins/cells per release.

Paired bootstrap uses **5,000 release-block** and **5,000 year-block** resamples; it does not refit models and never uses a primary cell-IID bootstrap.

| Resampling | Blocks | CRPS ratio 95% interval | Delta vs V5.1 95% interval | Oracle capture 95% interval |
| --- | --- | --- | --- | --- |
| Release | 33 | 1.06598–1.23761 | +0.06598–+0.23761 | −35.1745%–−9.6076% |
| Year | 8 | 1.04425–1.23631 | +0.04425–+0.23631 | -34.0893%–-6.8813% |

Release-block Pearson interval is −0.29978–0.12698; Spearman interval is −0.23667–0.13876. Bootstrapping this exposed historical universe does not create independent OOS evidence.

## Negative controls and mutation tests

| Control | Replicates | Median CRPS ratio | Fraction at least as good as primary |
| --- | --- | --- | --- |
| RELEASE_VALUE_SHUFFLE | 2000 | 1.1286 | 70.90% |
| RELEASE_DATE_PERMUTATION | 2000 | 1.1477 | 55.20% |
| STANDARDS_SIGN_SHUFFLE | 2000 | 1.1580 | 37.00% |
| DEMAND_SIGN_SHUFFLE | 2000 | 1.1352 | 74.70% |
| GAUSSIAN_FULL5 | 2000 | 1.0707 | 99.35% |
| FEATURE_YEAR_SHIFT | 1 | 1.0322 | 100.00% |

Each stochastic control has exactly **2,000 non-overlapping deterministic replicates**, seed **2026100303**. All controls use the same chronology, minimum-release rule, train-only scaler, release weights, purge and scorer. Value shuffle exchanges four economic vectors among training releases while retaining age and actual test values. Standards/demand sign controls apply a balanced shuffled sign jointly to a training release's level and change. Gaussian controls use five reproducible per-release values.

Date permutation uses permuted **0–20 business-day nonnegative activation delays**, never early disclosure, with source states and weights rebuilt. If a perturbed state is unavailable, its test forecast gets zero shift on the fixed common ledger. Feature-year shift uses a fixed one-calendar-year lag. These nulls are not substitute information sources.

The original primary fails to outperform the controls: 70.9% of value-shuffle and 99.35% of Gaussian trials score at least as well. Future-source mutation leaves earlier feature vectors and fixed-model predictions **bitwise identical**; outcome-side mutation leaves source features identical. Changing training labels is not claimed to leave a refitted model unchanged.

## Concentration and economic direction

Overall net normalized gain is negative (**−286.198853**). Removing any one release leaves the ratio between **1.129996 and 1.165795**; removing any one year leaves **1.121625–1.173869**. Therefore the degradation cannot be blamed on one release or year. The formal improvement-concentration flag is false because no net improvement exists. Isolated positive gains are concentrated: top-three positive-gain releases represent 78.19% of positive release gains; 2017 contributes 93.96% of positive annual gains. These favorable subsets do not rescue the experiment.

| Feature | Raw Pearson vs delta | Raw Spearman vs delta |
| --- | --- | --- |
| CREDIT_STANDARDS | -0.1158 | -0.1345 |
| CREDIT_DEMAND | 0.1618 | 0.1613 |
| DELTA_CREDIT_STANDARDS | -0.0568 | -0.0406 |
| DELTA_CREDIT_DEMAND | 0.0426 | -0.0025 |

Raw relationships are descriptive only. They are not causal evidence or crossfit forecast claims; the actual crossfit score and correlations above determine the verdict.

## Freeze, execution deviation and tests

Immediate parent: **6a9bf9a3507b3dd5b2ef2b8b687b4bfedf89e267** (LOCATION-02 NO). INFO-01 selection parent: **43a154ab419b6f3e3f4fc903db40d8c2e319f6bf**. Branch: **track2/location-03-sloos-alpha**.

**PRE_RESULT_LOCATION03_SHA: 57e9d1b5c44d3b196755e00524e778e56f220049**, remotely verified before new error labels were accessed.

One disclosed technical amendment occurred **after labels were loaded, before any model fit, prediction or score completed**. Pandas 3 returned a read-only Boolean mask; `to_numpy(copy=True)` replaces `to_numpy()` solely to permit mask intersection. All **240 masks were bitwise identical** to the original PRE behavior. No scientific feature, Ridge setting, fold, purge, scoring or decision rule changed. Amendment commit **fe29b985a838261b78d207fb207519fb23f13b37** preserves the original PRE; it is not falsely described as a second pre-outcome freeze. Both original and executed code hashes are retained.

Final verification: research **39 passed**; affected **51 passed**; full repository **653 passed, 2 skipped**; shared toolkit **250 passed**. Two existing integration gaps are skipped: Docker scoring-image parity (image/registry prerequisites) and live CodaBench wrapper parity (staging instance required). Initial affected/full commands hit their bounded timeout under competing BLAS threads; their partial logs were kept. The completed suites use one BLAS thread. No completed model fit, score, control or bootstrap was rerun for this test-only recovery.

All parent-tracked bytes are protected and unchanged. The public result commit contains source provenance, aggregate scores and outcome-free prediction provenance; original market truths and per-cell realized scores remain in the private recovery archive. Final RESULT SHA, remote blob verification, unchanged main SHA, clean tree and CRC/per-member/archive hashes are recorded in the external completion receipts to avoid self-referential Git hashes.

## Limitations and final decision

**LOCATION03_RESULT = NO.** SLOOS specifically fails this frozen release-balanced location test. Neither favorable annual subsets nor secondary ablations replace that result. The source passed its readiness gate; passing provenance does not imply predictive alpha. No independent alpha was validated and no official submission is authorized by this research.

The effective information count is small, rate assets share macro events, release/year blocks are dependent, publication timing is conservative date-only, and the historical universe is exposed. This does not show all external information fails. ECB remains closed after LOCATION-02; SLOOS now closes after LOCATION-03. Recommended next: **NY Fed SPD, INFO-01's pre-ranked source #3, under a new separately frozen research branch**. Do not tune SLOOS, expand model complexity, or test SPD within LOCATION-03.
