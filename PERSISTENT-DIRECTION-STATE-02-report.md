## Executive summary (read this first)


PERSISTENT-DIRECTION-STATE-02 completed: **NO**. DATASET_READY=true. Primary same-ledger CRPS ratio 1.00334288. Next exactly one axis: **PRICE-STATE-INFORMATION-AUDIT-03**, not executed. Contemporary SEP policy direction is tested against frozen V5.1, stale state, persistence and observable prices. No model, amplitude, threshold or favorable subset was tuned.


## Source readiness and provenance


Official release universe2016–2024: 35; admitted 33; source-only state changes 22. Original dated PDFs and header-resolved accessible HTML agree on CY/NCY policy medians. Earlier td-row tables were recovered deterministically. Two corrected-document rounds fail closed. March2020 had no SEP. Release-date EOD New York activation; age90 weekdays. Fields retain release-year CY/NCY targets across January. Public Fed information with attribution; offline research feasible under organizer rules. PIT B does not prove immutable originals or absence of undisclosed replacement. No official submission rights/approval or readiness claim.


## Binding draft and pre-outcome clarifications


Parent RESULT 6653df8c61042c4642be3e2ed37b52daeea16de7; PRE 2bdc6722fd5705887bee5f0695a09fe2319bf431. `experiment_spec.json` records every clarification before labels: inherited monthly cache grid, conservative delayed-control refits, missing-control zero shifts, strict maturity purge, original-price vintage limits, chronology-safe one-sided date and historical-donor state controls, and quantified concentration gate. No substantive source/feature/model/amplitude/fold gate conflict. Public outputs are predictions and aggregates only; private labels, draws, losses and perfect-location cell results remain outside Git.


## Primary comparison

| model | CRPS_ratio | sign_accuracy | oracle_capture | balanced_accuracy | Brier |
| --- | --- | --- | --- | --- | --- |
| V5.1 | 1.000000 | 0.000000 | 0.000000 | 0.500000 | 0.250000 |
| SEP_DIRECTION_FIXED005 | 1.003343 | 0.460581 | -0.004113 | 0.378304 | 0.265114 |
| 5BD_DELAYED | 1.003343 | 0.460581 | -0.004113 | 0.378304 | 0.265114 |
| 21BD_STALE | 1.002367 | 0.437759 | -0.002913 | 0.440971 | 0.261637 |
| PERSISTENCE | 0.992817 | 0.315353 | 0.008838 | 0.640075 | 0.248963 |
| PRICE_21BD | 0.996520 | 0.508299 | 0.004282 | 0.528032 | 0.460581 |
| PRICE_LOGISTIC | 0.993183 | 0.595436 | 0.008387 | 0.589062 | 0.322034 |
| MATCHED_RANDOM | 0.993609 | 0.597510 | 0.007864 | 0.527078 | 0.402490 |
| PERFECT_LOCATION | 0.187266 | 1.000000 | 1.000000 | 1.000000 | 0.000000 |


## Annual folds

| year | cells | releases | SEP_DIRECTION_FIXED005_ratio | PRICE_LOGISTIC_ratio | 5BD_DELAYED_ratio | 21BD_STALE_ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 2020 | 100 | 3 | 1.012791 | 1.012791 | 1.012791 | 1.011728 |
| 2021 | 120 | 4 | 1.013256 | 0.987371 | 1.013256 | 1.015111 |
| 2022 | 90 | 3 | 0.981246 | 0.990760 | 0.981246 | 0.981246 |
| 2023 | 90 | 3 | 1.019146 | 1.001164 | 1.019146 | 1.001320 |
| 2024 | 82 | 4 | 1.005222 | 0.996770 | 1.005222 | 1.005222 |


## Horizons

| horizon | cells | SEP_DIRECTION_FIXED005_ratio | PRICE_LOGISTIC_ratio | 5BD_DELAYED_ratio | 21BD_STALE_ratio |
| --- | --- | --- | --- | --- | --- |
| 5 | 104 | 0.994987 | 0.997483 | 0.994987 | 0.995902 |
| 21 | 102 | 1.005264 | 0.993746 | 1.005264 | 1.002710 |
| 63 | 98 | 1.006003 | 0.993261 | 1.006003 | 1.002553 |
| 126 | 92 | 1.004457 | 0.990661 | 1.004457 | 1.003493 |
| 189 | 86 | 1.003950 | 0.992832 | 1.003950 | 1.004280 |


## Assets

| asset | cells | SEP_DIRECTION_FIXED005_ratio | PRICE_LOGISTIC_ratio |
| --- | --- | --- | --- |
| UST_2Y | 241 | 1.002462 | 0.994481 |
| UST_5Y | 241 | 1.004821 | 0.991005 |


## Block bootstrap


Negative differences favor SEP. No IID cell bootstrap. Only five evaluation years constrain year inference.
| block | replicates | blocks | primary_ratio | primary_minus_price_logistic | primary_minus_5BD | primary_minus_21BD | oracle_capture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| release | 5000 | 17 | [0.9929954002483282, 1.0133485753345508] | [-0.0030255833605539405, 0.021225452525342813] | [0.0, 0.0] | [-0.002719266281298588, 0.00554958851533339] | [-0.01726217801659554, 0.00879437379477358] |
| year | 5000 | 5 | [0.9872882473467545, 1.0150808136807823] | [-0.006331013530846863, 0.023442517618709524] | [0.0, 0.0] | [-0.0014151588909634416, 0.007414249758397329] | [-0.02084203781678902, 0.015353281936907118] |
| week | 5000 | 52 | [0.9969043945558278, 1.009584897035788] | [0.0013788185003332902, 0.017838402816448207] | [0.0, 0.0] | [-0.0016889700022157395, 0.004043104036574608] | [-0.012154417399840807, 0.003771867858892914] |


## Negative controls

| kind | replicates | mean | q05 | q95 | Monte_Carlo_p_plus_one |
| --- | --- | --- | --- | --- | --- |
| STATE | 2000 | 0.997062 | 0.990444 | 1.004523 | 0.922039 |
| DATE | 2000 | 1.000859 | 0.997234 | 1.004313 | 0.878561 |
| RANDOM | 2000 | 0.995067 | 0.993268 | 0.996943 | 1.000000 |


## Dependence and timing identification


52 evaluation origins; 482 target cells; only 17 unique evaluation releases. The release count is an upper bound on independent information events. Model probabilities repeat source state and differ only by asset/horizon/fold. Source-week bootstrap uses origin calendar week because this inherited ledger is monthly; it does not manufacture intramonth publication event identification. Contemporary SEP must beat both5BD delayed and21BD stale controls and previous-state persistence. Gates: {"CRPS_le_098": false, "PIT_integrity": true, "annual_4_of_5": false, "beats_persistence": false, "beats_price": false, "beats_timing": false, "concentration_safe": false, "negative_controls_inferior": false, "release_CI_support": false, "week_CI_support": false, "year_CI_support": false}.


## Price redundancy and concentration


Dominant explanation: PRICE_REDUNDANT. `primary_score_summary.json` records fraction of gross positive gain in the largest release/year; all years including2023 and all five horizons remain in the primary. Price logistic uses exactly the inherited fixed14 H15 columns and asset/log horizon on identical origins and purged folds. The H15 current-vintage bounded probe has PIT C, a limit to strong incremental-information claims. Neither small baseline improvement nor source persistence proves new-release alpha.


## Limitations and baseline preservation


All2020–2024 outcomes were previously research-exposed. PRE prevents this experiment’s within-fold leakage, not prior exposure. No independent OOS, official score gain or causal relation is established. Monthly inherited cache gaps, source corrections inactive, current-vintage price control and five years constrain interpretation. V5.1 forecasts and protected parent/submission source files remain unchanged; official verified reference score0.9541 is not remeasured. Existing binary Docker package is not reconstructed or overwritten; byte-level preservation evidence is reported separately. No submission or next experiment is executed.


## Reproducibility


Use Python3.13, pinned common v2.4.3 scorer and original private input hashes. Stage commands are documented in RUNBOOK.md. Final Git RESULT is bound by the external verified recovery receipt to avoid a self-referential commit SHA. Full test/Git/recovery evidence is stored in execution_audit.json and the final receipt.

## Failure detail and technical execution disclosure

SEP improves only2022, not the other four annual folds. Its cell direction accuracy46.06%, release-balanced46.26%, balanced accuracy37.83% and probability/direction Spearman−0.20474 do not establish a useful future-direction signal.5BD delayed predictions and losses equal contemporary predictions bitwise;21BD stale is slightly better. Previous-state persistence and price logistic outperform SEP on aggregate. This is compatible with a persistent policy-state proxy, not validated new-release information. The label PRICE_REDUNDANT means the incremental SEP gate failed; it does not prove causal redundancy. Price logistic improves only0.68%, and the point matched-random comparator is similar. Random controls all outperform SEP; no independently validated price alpha follows. Exactly one next axis is PRICE-STATE-INFORMATION-AUDIT-03 under the frozen decision tree, not executed.

There were two corrected operational issues: original PDF column/cover-page layout extraction and a float64 geometry assertion. The latter occurred after PRE:85 gaps at most4.44e−16 coalesced, with zero strict ordering inversions and SD change2.22e−16. The technical checkpoint cd97b1ea0ebad052aaf1f81ba6152267014bc05e is remotely verified; no fold was refit, no score formula changed, and the complete scores.npz SHA stayed identical. Original PRE remains2bdc6722fd5705887bee5f0695a09fe2319bf431. This exception is disclosed, not treated as an untouched implementation.

For heuristic controls, encoded probabilities0/.5/1 are descriptive; probability tie means zero shift. Sign accuracy counts no-action predictions as not correct against nonzero targets, so persistence's low unconditional accuracy includes280 abstentions. Binary balanced_accuracy uses the conventional probability>.5 class rule; it is distinct from three-way sign accuracy. V5.1 is an unshifted distribution, not a binary classifier: its direction accuracy is N/A for interpretation. Exact target ties were zero in this ledger. All target outcomes remain private.

## Final tests and preservation evidence

{
  "research": {
    "exit_code": 0,
    "passed": 34,
    "skipped": 0,
    "deselected": 0,
    "log_SHA256": "b21dee9fdba98799d4675157acb1ca201e67b5f0aa462adaaa1cf5d5069c79a5"
  },
  "affected": {
    "exit_code": 0,
    "passed": 74,
    "skipped": 0,
    "deselected": 1,
    "log_SHA256": "06deb7cb2c10302ebaf2912055762678ab07ccfa6ff727576c1300c3777fdc13"
  },
  "full": {
    "exit_code": 0,
    "passed": 782,
    "skipped": 17,
    "deselected": 1,
    "log_SHA256": "94d48740a9089198b6fde8a21592321bcabaee3a22b4316bb8f88f46a8798f80"
  },
  "common": {
    "exit_code": 0,
    "passed": 250,
    "skipped": 0,
    "deselected": 0,
    "log_SHA256": "db754842640fa05d301792fa96dd2fda32175f06c8c70dcfb759b20848c0c312"
  }
}

17 inherited tests require older private studies or Docker/live-CodaBench and remain skipped;1 prior-branch-name-only test is explicitly deselected. Current branch/main/parent protection is tested. All2261 protected parent files and original V5.1 draws retain hashes. Primary and baseline CRPS reproduce bitwise without refitting. Current binary Docker image is not materialized, so no fresh binary-image verification is claimed. Neither submission package nor reference model is overwritten.
