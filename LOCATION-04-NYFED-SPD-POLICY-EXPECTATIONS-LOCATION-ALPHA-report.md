Executive summary: LOCATION-04 = NO. The frozen original-release SPD FULL5 model worsened primary UST 2Y+5Y CRPS by 42.08%; no feature, horizon, source, weight or model was redesigned after evaluation. Next: INFORMATION-FAILURE-REASSESSMENT-01.

# LOCATION-04 — NY Fed SPD policy-expectations location alpha

## Source readiness and provenance

DATASET_READY = true. Enumerated 112 SPD rounds and 224 original questionnaire/results PDFs for 2011–2024. There are 69 usable FULL5 releases over 2016–2024 and three predeclared policy eras. Canonical representation begins with March 2016; complete source state first activates on 2016-05-19 and ends on 2024-11-27. Earlier separate top/bottom range medians were excluded before outcomes, rather than averaged. Probability bins and appendices are excluded. The May 2023 questionnaire cover was visually verified from the original PDF. Eighteen recent original modal tables were visually checked after OCR extraction.

Canonical statistic: **DIRECT_PUBLISHED_MEDIAN_OF_DEALER_MODAL_TARGET_RATE_OR_RANGE_MIDPOINT_PERCENT**. This is the published median of individual dealers' modal target rates/range midpoints, in percent; it is not an implied expectation from probability bins. Exact target-event dates are in the frozen field ledger.

PIT grade B: activation uses original official results dates where available and conservative one-business-day-after-actual-FOMC-minutes reconstruction from contemporaneous official policy otherwise. End-of-publication-day New York activation and previous-business-day 16:00 New York origin cutoff are conservative. Distribution/deadline dates never activate results. Tested traps: December 2011→2012-01-04, January 2018→2018-02-22, September 2024→2024-10-10. Unresolved early 2011 dates are inactive. December 2024 results after the competition cutoff are inactive. Known corrected appendices do not replace original admitted modal fields; missing unrecoverable original affected fields would be inactive. This audit is not proof of immutable historical bytes at every publication.

Official evidence: [NY Fed archive](https://www.newyorkfed.org/markets/market-intelligence/survey-of-market-expectations), [December 2011 results announcement](https://www.newyorkfed.org/newsevents/events/regional_outreach/2012/0104_2012.html), [September 2024 publication announcement](https://www.newyorkfed.org/markets/opolicy/operating_policy_241010), plus the URL/hash receipts and official FOMC calendars in the private recovery archive. SPD and SMP are kept separate with no fallback; current revised exports are not retroactive primary evidence.

## Frozen design and outcome access

Immediate scientific parent: `938abb88db0dc985d8468950e169098b88ed50b9`. Remote PRE: `2e356b91dd98dae022b72494ea6d4c70a9a38ed7`. Tree hash was verified before any LOCATION-04 future-error labels were deserialized. All frozen hashes and all 2087 protected parent files remain unchanged.

Primary assets: **UST_2Y + UST_5Y**. Horizons: **5, 21, 63, 126, 189 repository business days**, all retained. Development 2016–2019; expanding annual evaluation 2020–2024. Source-only coverage determined these folds before labels. Every asset/horizon fit uses at least 20 unique training releases, strict horizon maturity purge, no held-out release sharing, and maturity no later than 2024-12-18.

Five features only: POLICY_NEAR, POLICY_FAR, POLICY_PATH_SLOPE, POLICY_REVISION_SAME_TARGET, SOURCE_AGE_BUSINESS_DAYS. Near/far targets are explicit future events at publication; far is distinct and at most 180 calendar days out. Revision requires the identical target date/event and statistic in the immediately previous public SPD round. Missing revisions are not imputed. Latest incomplete states are inactive; there is no older-state fallback. The age cap is fixed at 70 business days. Near/far are frozen at release and are not reselected between origins.

Ridge alpha=1, intercept, train-only standardized features. Each release has total training weight one, in both scaler and Ridge. The original frozen V5.1 draws are shifted uniformly by predicted standardized error × original SD. Distribution shape, draw geometry/ranks, scale, tails and cross-draw structure are preserved. Fair CRPS is imported from qfbench2-common v2.4.3; the primary ratio is the sum of CRPS normalized by the frozen past scale divided by the exact same-ledger V5.1 sum. The oracle moves each median to truth without changing shape. Capture is `(1-R_candidate)/(1-R_oracle)`, never clipped.

## Primary results

| Model | CRPS ratio | Oracle capture | R² | Spearman | Sign accuracy |
| --- | --- | --- | --- | --- | --- |
| V5.1 | 1.0000 | 0.0000 | -0.0929 | — | — |
| SPD FULL5 release-balanced | 1.4208 | -0.5290 | -1.1805 | 0.4044 | 0.6612 |
| SPD FULL5 unweighted (secondary) | 1.4013 | -0.5044 | -1.1270 | 0.4109 | 0.6594 |
| Path levels (secondary) | 1.4536 | -0.5702 | -1.2991 | 0.3982 | 0.6612 |
| Revision only (secondary) | 1.0611 | -0.0768 | -0.1740 | -0.2466 | 0.5000 |
| Near only (secondary) | 1.3579 | -0.4499 | -0.9388 | 0.3746 | 0.6286 |
| Slope only (secondary) | 1.1110 | -0.1395 | -0.2772 | -0.1692 | 0.5018 |
| Perfect location oracle (descriptive) | 0.2045 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |


V5.1 predicts zero standardized center correction, so its correlation and sign-direction metrics are undefined and displayed as —. Its descriptive target R² remains computable against the evaluation target mean. Oracle values are descriptive, not predictions.

There are 552 primary cells, 59 forecast origins and 41 unique active releases. The effective independent release count is **at most 41**, not 552 independent cells. Releases are not established IID observations. Repeated source states are release-balanced and inference is blocked.

## Primary assets

| asset | Cells | Releases | CRPS ratio | Oracle capture | R² | Spearman | Sign accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UST_2Y | 276 | 41 | 1.3839 | -0.4580 | -1.0561 | 0.4191 | 0.6594 |
| UST_5Y | 276 | 41 | 1.4809 | -0.6625 | -1.5177 | 0.3876 | 0.6630 |


## Horizons

| horizon | Cells | Releases | CRPS ratio | Oracle capture | R² | Spearman | Sign accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 118 | 41 | 1.0584 | -0.0786 | -0.0684 | 0.0828 | 0.5339 |
| 21 | 116 | 40 | 1.3185 | -0.4661 | -0.5076 | 0.1934 | 0.5690 |
| 63 | 112 | 39 | 1.4449 | -0.5791 | -0.8736 | 0.2966 | 0.6607 |
| 126 | 106 | 37 | 1.4438 | -0.5383 | -1.5769 | 0.4472 | 0.7642 |
| 189 | 100 | 35 | 1.6136 | -0.7078 | -2.0810 | 0.6282 | 0.8100 |


No horizon was dropped. Better long-horizon directional association does not establish a useful location shift: all five horizons worsen CRPS.

## Annual folds

| year | Cells | Releases | CRPS ratio | Oracle capture | R² | Spearman | Sign accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 120 | 9 | 1.3333 | -0.5368 | -0.5135 | 0.5714 | 0.6583 |
| 2021 | 120 | 9 | 0.7635 | 0.2716 | 0.0387 | 0.4602 | 0.7667 |
| 2022 | 120 | 9 | 0.8832 | 0.1388 | -0.1776 | 0.4478 | 0.7833 |
| 2023 | 110 | 9 | 5.8809 | -7.6137 | -17.0326 | -0.0920 | 0.5091 |
| 2024 | 82 | 9 | 1.4894 | -0.7294 | -1.1626 | 0.1696 | 0.5366 |


Only two of five annual folds improve. Full5 mean predicted absolute shift is 1.5553 V5.1 SD, versus actual mean absolute error 1.2413 SD. Crossfit calibration slope is 0.2328. Positive rank association coexists with poor error magnitude/calibration; no recalibration is permitted in this experiment.

## Negative controls and invariance

| Control | Replicates | Median CRPS ratio | Fraction as good as primary |
| --- | --- | --- | --- |
| RELEASE_VALUE_SHUFFLE | 2000 | 1.1707 | 1.0000 |
| RELEASE_DATE_PERMUTATION | 2000 | 1.4009 | 0.7020 |
| POLICY_REVISION_SIGN_SHUFFLE | 2000 | 1.4680 | 0.0005 |
| POLICY_PATH_ORIENTATION_SHUFFLE | 2000 | 1.1404 | 1.0000 |
| GAUSSIAN_FULL5 | 2000 | 1.0953 | 1.0000 |
| FEATURE_YEAR_SHIFT | 1 | 1.1042 | 1.0000 |
| ONE_RELEASE_LAG | 1 | 1.3839 | 1.0000 |


Each stochastic control uses 2,000 fixed-seed replicates with the same chronological model mechanics, weights and purge; seed 2026100404. Economic vectors/signs are permuted across training release blocks, not independent origins. Date permutation uses nonnegative 0–20-business-day activation delays and never releases data early. Missing altered states produce zero shift on the frozen common primary ledger. Year shift and one-release lag are one fixed descriptive control each. Gaussian features have five coordinates and are assigned by release. SMP contamination, future-source features/predictions and outcome-side feature mutation all pass bitwise invariance. Outcome-label changes are not claimed to leave refitted models invariant.

## Block bootstrap

5,000 paired release-block and 5,000 paired year-block resamples of crossfit forecast losses, without model refitting; no naive cell-IID bootstrap.

| Block | Blocks | CRPS ratio 95% CI | Oracle capture 95% CI | Spearman 95% CI |
| --- | --- | --- | --- | --- |
| release | 41 | [1.0741, 1.9975] | [-1.3727, -0.088] | [0.2536, 0.5262] |
| year | 5 | [0.8481, 3.299] | [-3.5571, 0.1792] | [0.0317, 0.5454] |


Release-level uncertainty supports deterioration. The five-year interval is much wider and crosses one; it does not rescue the poor primary ratio and negative capture. Bootstrap does not create independent OOS validation.

## Concentration

The failure is dominated by 2023: 86.29% of summed negative annual contributions. Removing 2023 without refitting gives ratio 0.9391, purely descriptive. This exclusion is forbidden as a primary result. Year/release leave-one-block sensitivities and top-one/top-three positive gain shares are in concentration_audit.json; the full universe is preserved. There is no broad stable improvement to declare robust.

## SECONDARY broad curve

7Y/10Y/20Y/30Y aggregate CRPS ratio 1.5120; capture -0.7610. These assets cannot replace the failed 2Y+5Y primary result.

| Secondary asset | CRPS ratio | Oracle capture |
| --- | --- | --- |
| UST_10Y | 1.5265 | -0.7773 |
| UST_20Y | 1.5122 | -0.7692 |
| UST_30Y | 1.5232 | -0.8043 |
| UST_7Y | 1.4884 | -0.7038 |


All fixed ablations and the unweighted sensitivity also worsen aggregate CRPS. They cannot rescue the primary. Raw economic correlations are descriptive and coefficient signs are not causal evidence.

## Limitations and verdict

LOCATION04_RESULT = **NO**. This frozen SPD formulation failed. All results are research-exposed, with no independent OOS claim, no validated alpha and no official submission justification. No new architecture was created; only an external-information location shift was tested. This does not prove every SPD formulation, all information sources or future prospective survey signals fail. It also establishes no causal Fed mechanism, generalization to all rates/assets, official score gain or score 0.5.

ECB, SLOOS and SPD remain closed under their frozen tests. Next research axis: **INFORMATION-FAILURE-REASSESSMENT-01**. Do not tune SPD, cycle mechanically to source #4, or start that reassessment inside LOCATION-04.

## Verification and recovery

Research tests 39 passed; directly affected tests 72 passed; full repository tests 692 passed and 2 pre-existing skips; common toolkit tests 250 passed. The full suite emitted only existing pandas Copy-on-Write deprecation warnings. Commands/log hashes, mutation results and source reconstruction receipts are retained. Remote final commit/file verification and final clean-tree/main checks are recorded in the private completion receipt, whose exact RESULT SHA is also returned to the user. This avoids self-referential Git hashes.

Branch: `track2/location-04-nyfed-spd-alpha`. A pre-evaluation private recovery ZIP was already saved, CRC and per-file hashes verified; final private ZIP includes code/tests, original permitted source PDFs and provenance, exact V5.1 inputs, fold fits/predictions, private labels/losses, control chunks, bootstrap, report, STATUS, logs and Git bundle. Original NY Fed/Fed material retains its source rights and is not relicensed as MIT. No private market truth, exact per-cell loss or baseline draws are committed to the public branch.
