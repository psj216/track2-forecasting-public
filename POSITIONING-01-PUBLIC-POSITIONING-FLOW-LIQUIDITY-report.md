## Executive summary (read this first)

POSITIONING01_RESULT = NO. FLOW_RESULT = NO, LIQUIDITY_RESULT = NO, COMBINED_RESULT = NO. POSITIONING_RESULT = SOURCE_GATE_FAIL: original positioning quantities were not evaluated, so this experiment does not establish that positioning has no forecasting information.

All 52 frozen crossfits and eight scoring chunks completed. The evaluation retains all 82,184 cells, 780 origins and 25 assets from 2010–2024. The best linear liquidity model L1 has active/full CRPS ratio 0.998539 (0.146% improvement), capture 0.002476 and only two improving folds. The single fixed nonlinear diagnostic has ratio 0.998429 (0.157% improvement), capture 0.002663 and three improving folds. Both miss the precommitted minimum effect/capture gates and have report/year confidence intervals crossing one. Neither qualifies as a signal. NEXT_RESEARCH_AXIS = CONTEXT-01; READY_FOR_ONE_SHOT_SUBMISSION = NO.

These are normalized marginal fair-CRPS research results, not official composite contest scores. No score-dependent source, asset, category, feature or architecture selection was performed.

## Frozen lineage and execution

- Branch: `track2/positioning-01-public-positioning-flow-liquidity`
- Parent SHA: `2ac22729875d48e59968edaa60cab927a02712d9`
- PRE_RESULT_POSITIONING01_SHA: `80933363f6c8fd273508c7ab30e35a43e03f37af`
- RESULT_SHA: the commit containing this completed report; exact remote SHA is recorded in the external completion receipt and final delivery, avoiding a self-referential commit hash.

The PRE commit was published, fetched and checked against its parent, tree and core file blobs before opening target scores. Four chronological outer folds retain the inherited 189-business-day purge and target-maturity checks in inner and outer splits. Ridge has no intercept, active-training-only scaling with `with_mean=False`, and alpha grid [0.01, 0.1, 1, 10, 100], chosen by chronological inner delta MSE. Each inactive row is exactly zero; all shifts are capped at ±10 original standard deviations. The one C2 HGB diagnostic fixes depth 3, learning rate 0.05, 200 iterations, L2 1, seed 19 and no early stopping. No HGB search occurred.

The 135,994-cell original training/evaluation ledger, target, original-draw SD and scale are unchanged. Original cache hashes for all 1,251 input files were verified. Imported common v2.4.3 fair CRPS is used. Every evaluated asset-origin checks pure-location geometry and reproduces baseline scores; no variance, scale, tail, ranks or copula change occurs. Predictions, fitted models, raw data and per-cell scores stay private.

## Source, publication, license and original-vintage audit


| Gate | Result |
| --- | --- |
| POSITIONING_SOURCE_GATE | FAIL |
| FLOW_SOURCE_GATE | PASS |
| LIQUIDITY_SOURCE_GATE | PASS |


Admissible: 2; partial: 1; rejected: 6. These classifications were fixed before results.


| Source | Class | Status | Reason / admitted measurement |
| --- | --- | --- | --- |
| TIC_FORM_S | F | ADMISSIBLE | Original ZIP by actual release date; most recent measurement month only. Historical rows revised within later releases are never used. End before replacement SLT. |
| FED_H41_RESERVES | L | ADMISSIBLE | Each dated release table, first data column; current DDP revisions excluded. Published2014corrections address table10collateral, not selectedtable1reserve balance. Preserve original selected field and ignore added later cover-note dates. |
| CFTC_LEGACY | P | REJECTED | Current FAQ no historical-update claim conflicts with official2010FX correction and2008backhistory revision. No complete historical actual release-date list; weekly URLs label observation date. No original corrected-week vintage and actual calendar sufficiently verified. |
| CFTC_TFF | P | REJECTED | 2006backfill first published December2010 cannot be assigned2006availability. Same historical publication/revision proof limitations; native categories not reconstructed from Legacy. |
| CFTC_DISAGG | P | REJECTED | Commodity categories lack direct contest commodity targets; cannot broadcast to FX/factors by indirect sensitivity. Same PIT verification gaps. |
| NYFED_PD_P | P | REJECTED | Provider states current data may reflect revisions since prior publication. Original release vintage panels across three eras not obtained. Historical observation dates plus routineThursday schedule do not prove individual original publications. |
| NYFED_PD_L | L | REJECTED | Same revised current history, no original vintage panel proved. Do not relabel revised dealer positions as admissible liquidity. |
| OFR_NYPD | L | REJECTED | Provider metadata says current vintage. API p/f/a means preliminary/final/as-of dataset type, not an original daily historical vintage panel. No source-date reconstruction from retrievaldate. |
| TIC_SLT | F | PARTIAL | Original2024sample ZIP verified and2023format break documented. Only one fixed outer era under native new definition; insufficient minimumthree eras. No splice with FormS historical flow. |


TIC Form S uses the all-country/IRO US corporate-equity current-month purchase and sale fields in each actual dated Treasury ZIP. Net = purchases minus sales; the same-month gross transaction denominator is purchases plus sales, not assets under management. Only the newest measurement month, first seen at its real release, is retained; restated historical rows in subsequent ZIPs are ignored. The 2006-10-20 special ZIP lacks Form S and is the sole rejected original release. There is no splice into the changed 2023 SLT definition. Its 2024 sample is partial because it cannot cover three outer eras. Units are USD millions and no asset-size denominator is fabricated.

H.4.1 uses table 1, first numeric column, weekly-average Reserve balances with Federal Reserve Banks, in USD millions, from 1,304 dated releases. Six 2020 HTML timeouts were recovered once from the official contemporaneous H41.TXT format. Observation period, original file date and actual availability remain distinct. The delayed 2020-04-16 release is available conservatively on the verified 2020-04-17 announcement date.

**H.4.1 preservation limitation:** dated historical HTML is not immutable as a whole. A 2014 correction amended table 10 collateral on earlier release pages. The selected table 1 reserve-balance field is outside the announced correction scope. Admission is field-specific released-value provenance; it does not prove every historical HTML byte or every possible undocumented change is original. Current DDP/FRED revised history is excluded. This caveat limits liquidity inference.

For CFTC, an observation-date weekly URL and a routine Friday schedule do not prove historical publication. Correction notices and TFF backfills conflict with treating present history as originally available. Shutdown, holiday and ION delays are acknowledged; no guessed calendar or backdated TFF availability is used. New York Fed current revised primary-dealer data and OFR present-vintage API series do not establish a three-era original release-vintage panel. No positions or categories are synthesized.

The official Fed public-domain/source-attribution policy and Treasury original-file extraction/statistical provenance were audited; federal government statistical works are the provenance basis. Original files are preserved privately with URLs, retrieval times and SHA256. No commercial ETF dataset or restricted third-party quantity is used. Full per-source units, category definitions, correction evidence and hashes are in [source_manifest.json](backtesting/positioning01/results/source_manifest.json).

**Availability:** cutoff is the preceding Monday–Friday business day at 16:00 America/New_York. H.4.1 is normally after that close; Treasury individual intraday timestamps were not frozen. Both receive a conservative 23:59 ET publication-day upper bound. A release on the preceding business day therefore remains unavailable until the next eligible origin. Actual source dates are not inferred from observation dates. Max publication ages are F 30 and L 10 business days; absent P would be 10. The inherited Monday–Friday calendar is used, not a newly introduced exchange holiday calendar.

## Coverage and economic mapping


| Class | Original releases | Used reports | Years | Origins | Active cells | Full cells | Coverage | Outer eras |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P | 0 | 0 | 0 | 0 | 0 | 82184 | 0.0000% | 0 |
| F | 244 | 160 | 14 | 688 | 3440 | 82184 | 4.1857% | 4 |
| L | 1304 | 778 | 15 | 780 | 82184 | 82184 | 100.0000% | 4 |
| C | 1548 | 938 | 15 | 780 | 82184 | 82184 | 100.0000% | 4 |


F is active only on MKT, 2010–2023; source expiry after March 2023 leaves later rows at exact baseline. L and C cover all 15 evaluation years. Acquired releases and actually used evaluation snapshots are different counts.

Candidate mappings: DIRECT 8, GROUP_LEVEL 11, UNMAPPED 1, plus GLOBAL_MACRO 25. Primary admitted mappings: DIRECT 1 (TIC US equity → MKT), GLOBAL_MACRO 25 (bank reserves → all 25 assets under the predefined macro liquidity exception); zero group-level mappings enter primary fitting. Seven candidate direct currency mappings belong to failed CFTC sources and are unused. The all-maturity Treasury-flow and deliverable-futures basket candidates are group-level, not maturity-specific direct instruments, and are not evaluated. No commodity proxy is broadcast into contest assets. US corporate equities are broader than the exact MKT tradable basket; reserves measure global USD funding quantity, not dealer inventory or market microstructure.

F1/L1 have seven native features each and C1 concatenates fourteen. F2/L2 each add the five fixed horizon interactions to make 42 columns; C2 has 84. F features are level, one-release change, same-month net/gross share, 52-prior-release expanding z-score, four-release cumulative net flow and fixed publication/observation ages. L features are level, 1/4/13-release changes, 52-prior-release expanding z-score and publication/observation ages. Only strictly past releases enter historical normalization. Missing derived lags are zero; an admissible level/age may already be active. P columns are absent rather than invented all-zero P features.

## Primary scores and center-error diagnostics

Ratio = candidate summed normalized CRPS / baseline summed normalized CRPS; below one improves. Capture = (baseline − candidate)/(baseline − matching perfect-location oracle). The full oracle shifts **only the model's active cells**, leaving all other rows at baseline. Consequently active and full capture fractions match here, even though coverage changes full ratios. Negative capture remains untruncated. P0 is the all-zero baseline and is evaluated on C's full active scope. P1–P4 are NOT_EVALUATED because the P source gate failed.


| Model | Active ratio | Full ratio | Active capture | Full capture | active R² | active Spearman | active sign accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | -0.003931 | N/A | 0.000000 |
| P1 | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED |
| P2 | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED |
| P3 | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED |
| P4 | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED |
| F1 | 1.004988 | 1.000180 | -0.009101 | -0.009101 | -0.107967 | -0.107790 | 0.570058 |
| F2 | 1.033210 | 1.001200 | -0.060588 | -0.060588 | -0.162149 | -0.029700 | 0.565116 |
| L1 | 0.998539 | 0.998539 | 0.002476 | 0.002476 | 0.000008 | 0.067713 | 0.528120 |
| L2 | 1.006592 | 1.006592 | -0.011172 | -0.011172 | -0.012303 | 0.072738 | 0.526830 |
| C1 | 0.999792 | 0.999792 | 0.000352 | 0.000352 | -0.003396 | 0.064404 | 0.525054 |
| C2 | 1.009675 | 1.009675 | -0.016397 | -0.016397 | -0.018880 | 0.073735 | 0.524798 |
| nonlinear | 0.998429 | 0.998429 | 0.002663 | 0.002663 | 0.000354 | 0.070321 | 0.536297 |


Full-ledger R², Spearman and sign accuracy are separately reported below. Zero predictions count as a correct sign only for exactly zero truth, so low full sign accuracy for sparse F is a convention effect, not a tradable directional accuracy measure.


| Model | Full R² | Full Spearman | Full sign accuracy |
| --- | --- | --- | --- |
| P0 | -0.003931 | N/A | 0.000000 |
| F1 | -0.005481 | 0.013167 | 0.023861 |
| F2 | -0.007152 | 0.013357 | 0.023654 |
| L1 | 0.000008 | 0.067713 | 0.528120 |
| L2 | -0.012303 | 0.072738 | 0.526830 |
| C1 | -0.003396 | 0.064404 | 0.525054 |
| C2 | -0.018880 | 0.073735 | 0.524798 |
| nonlinear | 0.000354 | 0.070321 | 0.536297 |


Additional active diagnostics:


| Model | Delta MSE | Pearson | Calibration intercept | Calibration slope | Mean |shift|/SD | Cap hits |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | 1.041529 | N/A | 0.063858 | N/A | 0.000000 | 0 |
| F1 | 0.847140 | -0.095264 | 0.268682 | -0.398275 | 0.213324 | 0 |
| F2 | 0.888567 | -0.028535 | 0.221128 | -0.077614 | 0.245555 | 0 |
| L1 | 1.037443 | 0.067331 | -0.058773 | 0.927839 | 0.132168 | 0 |
| L2 | 1.050215 | 0.054365 | 0.018735 | 0.343014 | 0.141971 | 0 |
| C1 | 1.040975 | 0.052903 | -0.012919 | 0.575284 | 0.134387 | 0 |
| C2 | 1.057038 | 0.048623 | 0.027403 | 0.273862 | 0.145778 | 0 |
| nonlinear | 1.037084 | 0.076262 | -0.005067 | 0.591170 | 0.142411 | 0 |


The global perfect-location full ratio is 0.409983. The F-active perfect oracle has active ratio 0.451873 and full ratio 0.980188. The latter, not the global oracle, is the denominator for F full capture. This keeps sparse coverage from being credited with unattainable improvement.

## Outer folds, asset groups and horizons

All values below are active CRPS ratios. Training ends no later than 2009/2013/2017/2020, with test eras 2010–2013 / 2014–2017 / 2018–2020 / 2021–2024 respectively. Full and capture metrics, sample counts and all control models are in the corresponding CSVs.


| Model | 2010–13 | 2014–17 | 2018–20 | 2021–24 | Improving folds |
| --- | --- | --- | --- | --- | --- |
| P0 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0 |
| F1 | 1.019960 | 0.934637 | 1.033666 | 1.061227 | 1 |
| F2 | 1.051804 | 0.938587 | 1.065609 | 1.120801 | 1 |
| L1 | 1.009442 | 0.994468 | 1.003401 | 0.988010 | 2 |
| L2 | 1.046631 | 0.993157 | 1.004436 | 0.984352 | 2 |
| C1 | 1.010931 | 0.993959 | 1.004681 | 0.991026 | 2 |
| C2 | 1.050388 | 0.993928 | 1.007582 | 0.989362 | 2 |
| nonlinear | 1.004142 | 0.999604 | 0.999081 | 0.990839 | 3 |


| Model | FX | Factor/Equity | Rates |
| --- | --- | --- | --- |
| P0 | 1.000000 | 1.000000 | 1.000000 |
| F1 | NOT_ACTIVE | 1.004988 | NOT_ACTIVE |
| F2 | NOT_ACTIVE | 1.033210 | NOT_ACTIVE |
| L1 | 1.005736 | 0.985083 | 1.000046 |
| L2 | 1.015183 | 0.989557 | 1.009268 |
| C1 | 1.005434 | 0.990160 | 1.000149 |
| C2 | 1.015096 | 1.000721 | 1.009744 |
| nonlinear | 1.010390 | 0.991039 | 0.987429 |


| Model | 5 | 21 | 63 | 126 | 189 |
| --- | --- | --- | --- | --- | --- |
| P0 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| F1 | 1.036863 | 1.015965 | 1.019127 | 0.988068 | 0.965358 |
| F2 | 1.005735 | 1.006548 | 1.033406 | 1.068457 | 1.052755 |
| L1 | 1.009999 | 1.004401 | 0.999469 | 0.992648 | 0.987929 |
| L2 | 1.002406 | 1.000806 | 1.049261 | 0.996050 | 0.985839 |
| C1 | 1.012218 | 1.005936 | 1.001155 | 0.993703 | 0.987868 |
| C2 | 1.002640 | 1.001135 | 1.052832 | 1.001205 | 0.991466 |
| nonlinear | 1.004960 | 1.002669 | 0.998496 | 0.997089 | 0.990106 |


L1 improves in Factor/Equity (0.985083), while FX is worse (1.005736) and Rates is near one (1.000046). Longer horizons improve in L1, but the full frozen universe and minimum effect gates decide the result. These conditional patterns do not authorize a favorable subset, horizon, asset or category to become a new primary result. All 25 asset rows and every model are in [asset_summary.csv](backtesting/positioning01/results/asset_summary.csv).

## Sources, categories, ages, crowding and level versus change

Individual-source standalone fits are F1/F2 for TIC and L1/L2 for H.4.1; their primary scores above are the source-isolation results. Combined-model rows conditioned on TIC-active cells are overlapping exposure diagnostics, not an additive causal contribution or a source-specific full oracle. In the source/category CSVs, `full_ratio` is the whole model's unchanged full-ledger ratio, while `active_ratio` and `active_capture` describe the stated conditional mask.

There is one admitted aggregate category per source. No positioning category, crowding quintile or P level-versus-change model is evaluated; all Q1–Q5 are explicitly NOT_EVALUATED_SOURCE_GATE_FAIL. F1/C1 and F2/C2 comparisons add horizon interactions, not a score-selected position-level/change variant.



| model | source | category | active_ratio | active_capture | active_cells |
| --- | --- | --- | --- | --- | --- |
| F1 | TIC_FORM_S | foreign_transactions | 1.004988 | -0.009101 | 3440 |
| F2 | TIC_FORM_S | foreign_transactions | 1.033210 | -0.060588 | 3440 |
| L1 | FED_H41_RESERVES | depository_institutions | 0.998539 | 0.002476 | 82184 |
| L2 | FED_H41_RESERVES | depository_institutions | 1.006592 | -0.011172 | 82184 |
| C1 | TIC_FORM_S | foreign_transactions | 0.997601 | 0.004376 | 3440 |
| C1 | FED_H41_RESERVES | depository_institutions | 0.999792 | 0.000352 | 82184 |
| C2 | TIC_FORM_S | foreign_transactions | 1.042149 | -0.076896 | 3440 |
| C2 | FED_H41_RESERVES | depository_institutions | 1.009675 | -0.016397 | 82184 |
| nonlinear | TIC_FORM_S | foreign_transactions | 1.012895 | -0.023526 | 3440 |
| nonlinear | FED_H41_RESERVES | depository_institutions | 0.998429 | 0.002663 | 82184 |


| model | class_id | age_bin | active_ratio | active_cells |
| --- | --- | --- | --- | --- |
| F1 | F | 1-5BD | 1.000726 | 600 |
| F1 | F | 11-20BD | 1.003298 | 1575 |
| F1 | F | 21-30BD | 1.022375 | 485 |
| F1 | F | 6-10BD | 1.001084 | 780 |
| F2 | F | 1-5BD | 1.024943 | 600 |
| F2 | F | 11-20BD | 1.031360 | 1575 |
| F2 | F | 21-30BD | 1.048835 | 485 |
| F2 | F | 6-10BD | 1.033411 | 780 |
| L1 | L | 1-5BD | 0.998543 | 81964 |
| L1 | L | 6-10BD | 0.997167 | 220 |
| L2 | L | 1-5BD | 1.006626 | 81964 |
| L2 | L | 6-10BD | 0.996351 | 220 |
| C1 | F | 1-5BD | 1.004176 | 600 |
| C1 | F | 11-20BD | 0.992951 | 1575 |
| C1 | F | 21-30BD | 1.014904 | 485 |
| C1 | F | 6-10BD | 0.992037 | 780 |
| C1 | L | 1-5BD | 0.999778 | 81964 |
| C1 | L | 6-10BD | 1.004071 | 220 |
| C2 | F | 1-5BD | 1.040133 | 600 |
| C2 | F | 11-20BD | 1.037052 | 1575 |
| C2 | F | 21-30BD | 1.056868 | 485 |
| C2 | F | 6-10BD | 1.044895 | 780 |
| C2 | L | 1-5BD | 1.009692 | 81964 |
| C2 | L | 6-10BD | 1.004351 | 220 |
| nonlinear | F | 1-5BD | 1.011556 | 600 |
| nonlinear | F | 11-20BD | 1.008257 | 1575 |
| nonlinear | F | 21-30BD | 1.017726 | 485 |
| nonlinear | F | 6-10BD | 1.020051 | 780 |
| nonlinear | L | 1-5BD | 0.998435 | 81964 |
| nonlinear | L | 6-10BD | 0.996640 | 220 |


## Negative controls and guard results

A replaces each report's content with a deterministic strictly past donor, preserving real timing/ages; B uses one genuine report older with its own expiry. Each class has separate stage-2 crossfits (FA/FB, LA/LB, CA/CB). A's very poor L/C first-era behavior and cap hits show that it is a strong disturbance, not by itself evidence of alpha. All main fits have zero cap hits; LA has 506 and CA 570.


| Control | Active ratio | Full ratio | Capture | Cap hits |
| --- | --- | --- | --- | --- |
| FA | 1.020750 | 1.000750 | -0.037857 | 0 |
| FB | 1.015068 | 1.000545 | -0.027489 | 0 |
| LA | 1.720753 | 1.720753 | -1.221580 | 506 |
| LB | 1.006633 | 1.006633 | -0.011242 | 0 |
| CA | 1.724717 | 1.724717 | -1.228300 | 570 |
| CB | 1.008477 | 1.008477 | -0.014368 | 0 |


A primary clears a control only if both paired report-active and full-year upper 95% ratio bounds are below one. Comparisons use each primary class mask, including baseline retention when the older control expires.


| Primary | Control | Report paired 95% | Year paired 95% | Clear |
| --- | --- | --- | --- | --- |
| F1 | FA | 0.942223 / 1.021030 | 0.997767 / 1.000956 | False |
| F1 | FB | 0.972063 / 1.008822 | 0.998568 / 1.000545 | False |
| F2 | FA | 0.968215 / 1.051886 | 0.998409 / 1.002273 | False |
| F2 | FB | 0.993970 / 1.042327 | 0.999028 / 1.002011 | False |
| L1 | LA | 0.519152 / 0.656617 | 0.385983 / 0.938393 | True |
| L1 | LB | 0.989928 / 0.993931 | 0.981645 / 0.999698 | True |
| L2 | LA | 0.523848 / 0.661048 | 0.392586 / 0.939487 | True |
| L2 | LB | 0.999441 / 1.000476 | 0.999042 / 1.001063 | False |
| C1 | CA | 0.493981 / 0.688888 | 0.385170 / 0.938816 | True |
| C1 | CB | 0.987889 / 0.994694 | 0.981371 / 0.998869 | True |
| C2 | CA | 0.499279 / 0.694285 | 0.392426 / 0.941494 | True |
| C2 | CB | 0.999794 / 1.002602 | 0.998864 / 1.003366 | False |
| nonlinear | CA | 0.493645 / 0.686635 | 0.384265 / 0.937990 | True |
| nonlinear | CB | 0.985085 / 0.994620 | 0.977905 / 0.999679 | True |


C instrument mapping rotation and D category rotation are **NOT_IDENTIFIABLE**, precommitted before scores: one real directly mapped F instrument and one real global L instrument, with one aggregate category each, cannot yield an informative permutation. Tested generic rotation utilities are not an informative executed control. No synthetic categories, arbitrary global-L swaps or fake pass labels are asserted. This restricts source-specific interpretations. L1, C1 and nonlinear clear applicable A/B; F1/F2, L2 and C2 do not clear both.

E actual-publication/after-close exclusion, F future-report exclusion, G future-OI rejection, H original-hash/revision rejection and I pure-shift geometry guards pass their pre-result adversarial tests. G is a generic synthetic guard because no real P/OI series is admitted. H verifies selected-original-file provenance and immutable stored hashes; it does not erase the H.4.1 field-specific archive limitation. I also runs on every scored asset-origin.

## Report-block and calendar-year bootstrap

Each uses 2,000 paired draws; report bootstrap seed 1903. Entire groups of origins, assets and horizons sharing latest published snapshots or coincident release dates remain together. C unions both F/L snapshot IDs and dates. Past lags and expanding normalization are deterministic snapshot content and do not count as extra independent report events. Dependencies from historical features can extend across these blocks; full calendar-year blocks provide an additional sensitivity check. There is no cell bootstrap.


| Class | Used reports | Report weeks | Release dates | Years | Instruments | Categories | Connected blocks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F | 160 | 160 | 160 | 14 | 1 | 1 | 160 |
| L | 778 | 778 | 778 | 15 | 1 | 1 | 778 |
| C | 938 | 779 | 918 | 15 | 2 | 2 | 246 |


Report intervals below are active; year intervals are full, with 15 whole calendar-year blocks and the corresponding active-only full oracle.


| Model | Report ratio 95% | Report capture 95% | Year ratio 95% | Year capture 95% |
| --- | --- | --- | --- | --- |
| P0 | 1.000000 / 1.000000 | 0.000000 / 0.000000 | 1.000000 / 1.000000 | 0.000000 / 0.000000 |
| F1 | 0.980471 / 1.028414 | -0.052165 / 0.035592 | 0.998513 / 1.001567 | -0.078898 / 0.077166 |
| F2 | 1.001913 / 1.063503 | -0.115389 / -0.003438 | 0.998879 / 1.003126 | -0.154768 / 0.056003 |
| L1 | 0.995869 / 1.001058 | -0.001821 / 0.007005 | 0.991901 / 1.006085 | -0.010625 / 0.013685 |
| L2 | 1.002938 / 1.010379 | -0.017658 / -0.004971 | 0.993803 / 1.021739 | -0.038745 / 0.010094 |
| C1 | 0.995309 / 1.004575 | -0.007804 / 0.007837 | 0.992978 / 1.007182 | -0.012444 / 0.011941 |
| C2 | 1.002940 / 1.017127 | -0.029388 / -0.004946 | 0.996434 / 1.025076 | -0.044506 / 0.005848 |
| nonlinear | 0.993481 / 1.003893 | -0.006574 / 0.010992 | 0.990364 / 1.006813 | -0.011832 / 0.016177 |


## Decision and validation

The minimum WEAK_YES gates are active ratio ≤0.97, full ratio <1, at least three improving outer folds, capture >0.05 and clear applicable controls, with at least three covered eras. Higher verdicts retain all minimum gates. F1/F2 worsen on aggregate. L1/C1 have small improvements and only two improving folds; L2/C2 worsen. Nonlinear has three improving folds but misses both minimum active-ratio and capture gates. All seven evaluated main/diagnostic models are NO. P's source failure leaves the central positioning question unanswered; no negative P performance claim is justified.

POSITIONING01_RESULT = NO; POSITIONING_RESULT = SOURCE_GATE_FAIL; FLOW_RESULT = NO; LIQUIDITY_RESULT = NO; COMBINED_RESULT = NO; NEXT_RESEARCH_AXIS = CONTEXT-01; READY_FOR_ONE_SHOT_SUBMISSION = NO. F/L source acquisition succeeded, so the all-source-acquisition-failed route is not triggered. The next axis is the frozen routing decision, not a new executed experiment.

Validation: source-specific 24 passed; repository 498 passed, 2 skipped (existing Docker/Coda requirements); imported common 250 passed; public unit firewall PASS. Saved fits/chunks and original inputs are hash-checked. No completed evaluation was repeated after UI interruption. Scientific code is unchanged from PRE. Results/report and public aggregate artifact hashes are added only after scoring.

## Artifacts and recovery

All required source, mapping, publication, coverage, fitting, source/category/crowding/age, fold/group/horizon/asset, control, both bootstrap, decision and validation artifacts are in [backtesting/positioning01/results](backtesting/positioning01/results). [artifact_manifest.json](backtesting/positioning01/results/artifact_manifest.json) lists their hashes. Implementation and tests are in the branch. The completed private recovery package includes all fitted models, per-fold predictions, source data, features, scoring chunks, logs, unchanged LOCATION ledger/draws, Git bundle and remote verification receipt. Original TIC ZIPs reside in five separately preserved archives with exact hashes/receipts in that package; they are not redistributed publicly.

Official evidence: [Treasury dated release archive](https://home.treasury.gov/archives-of-tic-monthly-data-releases), [Fed H.4.1](https://www.federalreserve.gov/releases/h41/), [Fed correction history](https://www.federalreserve.gov/releases/h41/revisions.htm), [Fed announcements](https://www.federalreserve.gov/releases/h41/announcements.htm), [CFTC reports](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm), [New York Fed primary dealer statistics](https://www.newyorkfed.org/markets/counterparties/primary-dealers-statistics). Exact audited URLs, retrieved bytes, documents and hashes are preserved with the source manifest.
