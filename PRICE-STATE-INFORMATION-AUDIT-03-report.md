## Executive summary (read this first)

Audit completed: **INCONCLUSIVE**. Exactly one next axis: **V5.1-CENTER-BIAS-AUDIT-04**, not executed. PRICE_FULL is the original parent PRICE_LOGISTIC, not a new candidate. All outcomes are already research-exposed. No independent OOS, alpha validation, submission, amplitude optimization or favorable subset is claimed.

## Direct answers to the audit questions

Q1: No. PRICE_FULL0.993183 is worse than training-majority/intercept0.989829 and structure0.991809. Incremental gains are negative: -0.003355 versus intercept, -0.001375 versus structure.

Q2: PRICE_FULL beats the5000-run global prevalence-matched random distribution (0/5000 random ratios as good; plus-one p0.000200) and has ranking/classification evidence against shuffled features (balanced p0.008996; Spearman p0.013493). But forecast-loss permutation p0.096452 does not pass the frozen0.05 gate; all three stale-price lags score slightly better than PRICE_FULL. This is not proof that price variables contain zero information. It is insufficient evidence of useful incremental CRPS information beyond simple bias/structure.

The parent single MATCHED_RANDOM was matched to SEP positive frequency75.73%, not PRICE_FULL54.77%. The two are different nulls. New controls correctly preserve PRICE_FULL counts. Fold-matched random median0.994566 is close to PRICE_FULL;1.78% of those5000 replications beat it. The inherited random result0.993609 is reproduced and reported, not substituted with a favorable null.

Q3: PRICE_FULL improves only2021/2022/2024, degrades2020/2023, and fold Spearman changes sign. Both assets and all horizons improve in aggregate, but this does not permit subset promotion. The largest year's gross positive gain share is62.96%; see the concentration audit. Stable coefficient signs alone (mean87.5% consistency) do not prove a stable score relation; earliest/latest coefficient cosine is0.430454.

Q4: Test targets are64.11% positive overall and each training fold has a positive majority. Constant-up/training-majority yields the same stronger improvement without prices. However test positive frequency varies49.0%,79.17%,88.89%,52.22%,46.34%, and raw mean center error reverses. The frozen persistent-bias criterion fails. Therefore do not declare a proven persistent baseline bias or NO_PRICE_SIGNAL; record INCONCLUSIVE and investigate baseline center bias separately.

Q5: Equal-origin PRICE_FULL ratio0.993450; equal-year0.993651. The small effect does not disappear merely under reweighting. Origin95% CI[0.988186,0.999769] supports a small baseline improvement, but year CI[0.988806,1.005643] spans no gain. PRICE_FULL-minus-intercept and minus-structure block intervals span zero. Only five years limit inference.

Q6: PIT C, not A/B. Publication lag checks do not bound historical revisions of the current-vintage H15 probe. A canonical broader ledger exists, but broader transfer is blocked by this PIT requirement before loading/scoring broader outcomes.

Q7: Exactly one next axis: V5.1-CENTER-BIAS-AUDIT-04. Stronger feature-free controls and unstable test bias are the central unresolved explanation; no new candidate or next experiment was run.

## Technical serialization clarification

After PRE, a necessary public-serialization fix suppressed oracle-derived direction probabilities from the public CSV. Private predictions, forecast losses, models, features, folds and interpretation gates did not change, and no such values were published remotely. Repair commit1ef7b0fe20349f1be1e5bf6c22a7548e4552cb3f and original/repaired hashes are recorded. A firewall regression test was added. This is the only post-PRE implementation change.

## Parent reproduction

Parent RESULT 929ca23e0a57a0529cc64d8a14d5a78b791892e6; parent PRE 2bdc6722fd5705887bee5f0695a09fe2319bf431; new PRE b1681d58ecc75e16760904086e672490d3cc20c6. Every parent model loss array is bitwise reproduced with the imported common v2.4.3 scorer; ratio tolerance1e-14. Saved fold scaler/coefficients reproduce saved probabilities within1e-14. Saved probabilities and original draws remain unchanged. Initial launch/import and Unicode Git-path protection errors were diagnosed before evaluation and corrected; no completed research was restarted.

## Main comparison

| model | CRPS_ratio | sign_accuracy | balanced_accuracy | Spearman |
| --- | --- | --- | --- | --- |
| V5.1 | 1.000000 | None | None | None |
| TRAINING_MAJORITY | 0.989829 | 0.641079 | 0.500000 | nan |
| INTERCEPT_ONLY | 0.989829 | 0.641079 | 0.500000 | -0.284346 |
| STRUCTURE_ONLY | 0.991809 | 0.616183 | 0.480583 | -0.373390 |
| PRICE_21BD | 0.996520 | 0.508299 | 0.502020 | 0.047329 |
| PRICE_FULL | 0.993183 | 0.595436 | 0.589062 | 0.153666 |
| MATCHED_RANDOM | 0.993609 | 0.597510 | 0.527078 | 0.060591 |
| CONSTANT_UP | 0.989829 | 0.641079 | 0.500000 | nan |
| CONSTANT_DOWN | 1.011269 | 0.358921 | 0.500000 | nan |
| PERFECT_LOCATION | 0.187266 | None | None | None |

## Incremental price information

{
  "vs_intercept": -0.0033545990021883743,
  "vs_structure": -0.0013746220040921076,
  "vs_inherited_random": 0.0004252778316505834,
  "vs_random_median": 0.006334301022453803
}

Feature-permutation Monte Carlo p (lower CRPS): 0.096452. The predeclared price-information gate requires ratio≤0.990, both null/structure increments≥0.003, direction evidence, stable years/blocks and usable PIT. All gates: {"Spearman_ge_010": true, "balanced_ge_055": true, "beats_majority": false, "beats_random_median": true, "four_years_nonworse": false, "increment_intercept_ge_0003": false, "increment_structure_ge_0003": false, "no_year_over_half_gross_gain": false, "origin_year_support": false, "permutation_support": false, "ratio_le_0990": false, "usable_PIT": false}.

## Training bias and nulls

{
  "executive_summary": "Descriptive training-only center bias inspected on unchanged heldout targets; no baseline recalibration.",
  "folds": [
    {
      "year": 2020,
      "train": {
        "cells": 380,
        "positive_fraction": 0.6368421052631579,
        "negative_fraction": 0.3631578947368421,
        "zero_fraction": 0.0,
        "mean_raw_center_error": 0.07301343114100771,
        "median_raw_center_error": 0.057318043045215816,
        "mean_standardized_error": 0.24965143592980416
      },
      "test": {
        "cells": 100,
        "positive_fraction": 0.49,
        "negative_fraction": 0.51,
        "zero_fraction": 0.0,
        "mean_raw_center_error": -0.11686545977492506,
        "median_raw_center_error": -0.006335013701042724,
        "mean_standardized_error": -0.3732081579592668
      },
      "same_material_majority": false,
      "same_mean_error_sign": false
    },
    {
      "year": 2021,
      "train": {
        "cells": 482,
        "positive_fraction": 0.5643153526970954,
        "negative_fraction": 0.43568464730290457,
        "zero_fraction": 0.0,
        "mean_raw_center_error": -0.03374760042439664,
        "median_raw_center_error": 0.027121276909708447,
        "mean_standardized_error": -0.005713448689905801
      },
      "test": {
        "cells": 120,
        "positive_fraction": 0.7916666666666666,
        "negative_fraction": 0.20833333333333334,
        "zero_fraction": 0.0,
        "mean_raw_center_error": 0.49388963784057194,
        "median_raw_center_error": 0.16880611707449267,
        "mean_standardized_error": 1.7022459202961833
      },
      "same_material_majority": true,
      "same_mean_error_sign": false
    },
    {
      "year": 2022,
      "train": {
        "cells": 598,
        "positive_fraction": 0.596989966555184,
        "negative_fraction": 0.40301003344481606,
        "zero_fraction": 0.0,
        "mean_raw_center_error": 0.0033961788546664983,
        "median_raw_center_error": 0.03555840968786377,
        "mean_standardized_error": 0.11594770789949724
      },
      "test": {
        "cells": 90,
        "positive_fraction": 0.8888888888888888,
        "negative_fraction": 0.1111111111111111,
        "zero_fraction": 0.0,
        "mean_raw_center_error": 0.7508282132901243,
        "median_raw_center_error": 0.6203149752707637,
        "mean_standardized_error": 1.9534436405779227
      },
      "same_material_majority": true,
      "same_mean_error_sign": true
    },
    {
      "year": 2023,
      "train": {
        "cells": 706,
        "positive_fraction": 0.6458923512747875,
        "negative_fraction": 0.35410764872521244,
        "zero_fraction": 0.0,
        "mean_raw_center_error": 0.15066998009889623,
        "median_raw_center_error": 0.06739256882776573,
        "mean_standardized_error": 0.533516727207552
      },
      "test": {
        "cells": 90,
        "positive_fraction": 0.5222222222222223,
        "negative_fraction": 0.4777777777777778,
        "zero_fraction": 0.0,
        "mean_raw_center_error": 0.006508670228169954,
        "median_raw_center_error": 0.03558307463962551,
        "mean_standardized_error": -0.20537780470043865
      },
      "same_material_majority": false,
      "same_mean_error_sign": true
    },
    {
      "year": 2024,
      "train": {
        "cells": 788,
        "positive_fraction": 0.6434010152284264,
        "negative_fraction": 0.3565989847715736,
        "zero_fraction": 0.0,
        "mean_raw_center_error": 0.15371024838385572,
        "median_raw_center_error": 0.0735026199318066,
        "mean_standardized_error": 0.47859454076081703
      },
      "test": {
        "cells": 82,
        "positive_fraction": 0.4634146341463415,
        "negative_fraction": 0.5365853658536586,
        "zero_fraction": 0.0,
        "mean_raw_center_error": -0.07961522315300225,
        "median_raw_center_error": -0.030737215326192224,
        "mean_standardized_error": -0.045953534425741856
      },
      "same_material_majority": false,
      "same_mean_error_sign": false
    }
  ],
  "test_positive_fraction": 0.6410788381742739,
  "persistent_center_bias": false,
  "criterion": "At least3/5 folds train/test same majority, both at least5pp from50%, same nonzero mean raw-error sign; training-majority CRPS<1."
}

## Feature permutation and random signs

2000 whole-price-vector train-origin permutations: {"executive_summary": "2000 train-origin vector permutations, all donors matured and known at fold cutoff; heldout features unchanged. No PRICE_FULL refit.", "replicates": 2000, "seed": 31803, "CRPS_ratio": {"mean": 0.9989155536897085, "q05": 0.9920361165680158, "q50": 0.998695207435176, "q95": 1.006450431296341}, "balanced_accuracy": {"mean": 0.46681463606262974, "q05": 0.3858128963465963, "q50": 0.466968778644518, "q95": 0.5509292515479732}, "Spearman": {"mean": -0.08503553708598732, "q05": -0.25861428164356803, "q50": -0.08633686916854597, "q95": 0.10172519215032406}, "Monte_Carlo_p_ratio": 0.09645177411294353, "Monte_Carlo_p_balanced_accuracy": 0.008995502248875561, "Monte_Carlo_p_Spearman": 0.013493253373313344}. Historical donors are all admitted and matured by the fold cutoff; they may move across earlier train origins, but never from test/future folds. This is a fold-conditional null, not a simulated tradable historical path. Test features and structural covariates are fixed.

| kind | mean | q05 | q50 | q95 | fraction_equal_or_better |
| --- | --- | --- | --- | --- | --- |
| A | 0.999507 | 0.997371 | 0.999518 | 1.001633 | 0.000000 |
| B | 0.999482 | 0.997329 | 0.999476 | 1.001641 | 0.000000 |
| C | 0.999170 | 0.997053 | 0.999185 | 1.001278 | 0.000000 |
| D | 0.994557 | 0.993496 | 0.994566 | 0.995617 | 0.017800 |

## Annual stability

| group | model | cells | CRPS_ratio | sign_accuracy | balanced_accuracy | Spearman |
| --- | --- | --- | --- | --- | --- | --- |
| 2020 | INTERCEPT_ONLY | 100 | 1.012791 | 0.490000 | 0.500000 | nan |
| 2020 | STRUCTURE_ONLY | 100 | 1.012791 | 0.490000 | 0.500000 | -0.282062 |
| 2020 | PRICE_FULL | 100 | 1.012791 | 0.490000 | 0.500000 | 0.363475 |
| 2020 | MATCHED_RANDOM | 100 | 1.002622 | 0.540000 | 0.545418 | 0.107903 |
| 2021 | INTERCEPT_ONLY | 120 | 0.984641 | 0.791667 | 0.500000 | nan |
| 2021 | STRUCTURE_ONLY | 120 | 0.989422 | 0.691667 | 0.436842 | -0.375060 |
| 2021 | PRICE_FULL | 120 | 0.987371 | 0.758333 | 0.641053 | 0.103368 |
| 2021 | MATCHED_RANDOM | 120 | 0.992882 | 0.633333 | 0.473684 | -0.049930 |
| 2022 | INTERCEPT_ONLY | 90 | 0.981246 | 0.888889 | 0.500000 | nan |
| 2022 | STRUCTURE_ONLY | 90 | 0.981246 | 0.888889 | 0.500000 | -0.049237 |
| 2022 | PRICE_FULL | 90 | 0.990760 | 0.666667 | 0.375000 | -0.161948 |
| 2022 | MATCHED_RANDOM | 90 | 0.988596 | 0.744444 | 0.506250 | 0.010036 |
| 2023 | INTERCEPT_ONLY | 90 | 1.000929 | 0.522222 | 0.500000 | nan |
| 2023 | STRUCTURE_ONLY | 90 | 1.000929 | 0.522222 | 0.500000 | -0.003872 |
| 2023 | PRICE_FULL | 90 | 1.001164 | 0.477778 | 0.500000 | 0.370321 |
| 2023 | MATCHED_RANDOM | 90 | 0.996543 | 0.544444 | 0.533152 | 0.077065 |
| 2024 | INTERCEPT_ONLY | 82 | 1.005222 | 0.463415 | 0.500000 | nan |
| 2024 | STRUCTURE_ONLY | 82 | 1.005222 | 0.463415 | 0.500000 | -0.161320 |
| 2024 | PRICE_FULL | 82 | 0.996770 | 0.536585 | 0.500000 | -0.128119 |
| 2024 | MATCHED_RANDOM | 82 | 1.000725 | 0.512195 | 0.525718 | 0.055119 |

## Asset stability

| group | cells | CRPS_ratio | sign_accuracy | balanced_accuracy | Spearman |
| --- | --- | --- | --- | --- | --- |
| UST_2Y | 241 | 0.994481 | 0.580913 | 0.572295 | 0.096766 |
| UST_5Y | 241 | 0.991005 | 0.609959 | 0.606536 | 0.207776 |

## Horizon stability

| group | cells | CRPS_ratio | sign_accuracy | balanced_accuracy | Spearman |
| --- | --- | --- | --- | --- | --- |
| 5 | 104 | 0.997483 | 0.509615 | 0.505303 | -0.016856 |
| 21 | 102 | 0.993746 | 0.568627 | 0.567963 | 0.104968 |
| 63 | 98 | 0.993261 | 0.591837 | 0.590993 | 0.176569 |
| 126 | 92 | 0.990661 | 0.630435 | 0.625874 | 0.163622 |
| 189 | 86 | 0.992832 | 0.697674 | 0.698485 | 0.435740 |

## Equal-origin/year evidence

| method | CRPS_ratio | sign_accuracy | balanced_accuracy | Spearman |
| --- | --- | --- | --- | --- |
| CELL_WEIGHTED | 0.993183 | 0.595436 | 0.589062 | 0.153666 |
| ORIGIN_BALANCED | 0.993450 | 0.599679 | 0.603773 | 0.162388 |
| YEAR_BALANCED | 0.993651 | 0.585873 | 0.588781 | 0.158738 |

## Paired block bootstrap

| block | PRICE_FULL_ratio | PRICE_FULL_minus_intercept | PRICE_FULL_minus_structure | PRICE_FULL_minus_random_median | balanced_accuracy | Spearman |
| --- | --- | --- | --- | --- | --- | --- |
| origin | [0.9881855516684542, 0.9997688439564011] | [-0.003287168455432884, 0.011221413183877647] | [-0.005244434299258999, 0.009280703823750338] | [-0.011335996302733173, 4.230881409674978e-05] | [0.4945947097320918, 0.6798299264791167] | [-0.042342196352371596, 0.3315480453832644] |
| year | [0.9888056342103676, 1.0056434314254488] | [-0.002952174995467738, 0.007246075594425694] | [-0.003868629558441472, 0.007246075594425694] | [-0.010104451242060164, 0.003908036536199422] | [0.463768115942029, 0.6806074542493054] | [-0.04485654965849245, 0.33868801186759434] |
| quarter | [0.9867953684694473, 1.0037093896097313] | [-0.005778595677317847, 0.015355042252782638] | [-0.007871599837290444, 0.013520357720839581] | [-0.012713139486258213, 0.0037264574529958364] | [0.4518644730294522, 0.7044283967541219] | [-0.10377355002766465, 0.36844588997921773] |

## Timing, feature groups and coefficients

Timing-specific information: NOT_ESTABLISHED. Fixed5/21/63 weekday lags and LEVEL/CHANGE/CURVE controls are all reported in artifacts; no best lag/group becomes a candidate. Mean coefficient sign consistency 0.875000; full standardized coefficients, fold cosine similarities, concentration and scaler drift are in coefficient_stability.json. Coefficient size alone does not validate information.

## Price point-in-time integrity and broader transfer

PIT remains C. The archived bounded FRED/H15 probe is current-vintage. Official observation dates plus one weekday EOD and previous-weekday16:00NY cutoff prevent same-day premature activation, but cannot recover unknown later revisions. FRED represents latest vintage; ALFRED has dated vintage semantics. No original contemporaneous price vintage was acquired or revisions bounded. Therefore validated price alpha is unavailable. Exact raw source hash and all14 transformations are in price_feature_manifest.csv and price_pit_audit.json. Public Federal Reserve rates require attribution; offline reconstruction is feasible only after a separate PIT acquisition audit. Broader canonical LOCATION01 ledger exists, but PRICE_DATA_PIT is insufficient, so BROAD_TRANSFER_READY=false. Its canonical all-origin specification was frozen before diagnostics; no broader outcomes were evaluated or substitute favorable origins invented.

## Concentration and limitations

Largest positive gross gain shares by year/origin/horizon: {"year": 0.6295841712672955, "origin": 0.07995543166534141, "horizon": 0.3244820593060368}. Parent ledger has52 origins and482 cells, monthly gaps, only five years, quarterly SEP eligibility conditioning and repeated cells per origin. No IID cell bootstrap. Ties receive zero directional credit; V5.1 and perfect-location oracle directional metrics are not predictive metrics. Same-ledger oracle is mathematical headroom. PIT and dependence prevent independent claims. All years, assets and horizons remain in the main result.

## Verdict and next axis

**INCONCLUSIVE**. **V5.1-CENTER-BIAS-AUDIT-04** is the only selected future axis. Quantitative attribution: {"PRICE_SPECIFIC_INFORMATION": "NOT_ESTABLISHED", "TIMING_SPECIFIC_PRICE_INFORMATION": "NOT_ESTABLISHED", "central_conclusion": "INCONCLUSIVE", "concentration": {"horizon": 0.3244820593060368, "origin": 0.07995543166534141, "year": 0.6295841712672955}, "evidence": {"materially_price_specific": false, "negligible_increment": true, "random_frequently_beats": false, "similar_null": true}, "executive_summary": "Exposed forensic attribution only; quantitative null/bias conditions frozen before diagnostics.", "gates": {"Spearman_ge_010": true, "balanced_ge_055": true, "beats_majority": false, "beats_random_median": true, "four_years_nonworse": false, "increment_intercept_ge_0003": false, "increment_structure_ge_0003": false, "no_year_over_half_gross_gain": false, "origin_year_support": false, "permutation_support": false, "ratio_le_0990": false, "usable_PIT": false}, "incremental_gain": {"vs_inherited_random": 0.0004252778316505834, "vs_intercept": -0.0033545990021883743, "vs_random_median": 0.006334301022453803, "vs_structure": -0.0013746220040921076}, "persistent_center_bias": false}. No next experiment is executed.

## Baseline, tests and recovery

All parent tracked files, main, V5.1 source and submission files are hash-protected and unchanged. Official previously verified V5.1 Development reference0.9541 is not remeasured. No Docker package is overwritten; existing binary-package byte verification remains limited by the preserved evidence. Research, affected, full repository and common tests are recorded in execution_audit.json. PRE is remotely verified before new diagnostic labels; final RESULT/remote files/main/tree and private recovery CRC/member SHA/archive SHA are bound by an external completion receipt to avoid self-reference. RUNBOOK.md documents stages and exact continuation points.
