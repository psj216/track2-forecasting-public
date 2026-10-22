## Executive summary (read this first)
Exploratory gains do not support promotion. All frozen coefficients and seed17 remain unchanged. Positive improvement means FF03 loss minus candidate loss.

| Test | Exposed Practice22 | Current-vintage ECB2025 |
|---|---:|---:|
| Complete cards/origins |22/22|96/48|
| Improvement |0.01094125|0.00296234|
| Four-origin block95% interval |[0.00457225,0.03041124]|[-0.00024799,0.00643078]|
| Remove largest-gain origin |0.00509358|0.00171985|
| Remove largest-gain quarter |0.00509358|0.00158538|
| Selection salt18 improvement |0.00457100|0.00224350|
| Selection salt19 improvement |0.00188698|0.00092135|
| Improved/worsened cards |13/9|49/47|
| Worst card loss increase |0.05085377|0.03399269|

Blocks resample complete origins with their correlated cards. These conditional intervals do not erase exposure, selection history, missing labels or vintage uncertainty. Practice is an irregular historical event sample, not a continuous independent holdout.

Practice group improvements: UST−0.00438638, G10+0.01663780, ECB EM+0.02053501; F1−0.00255576, F2+0.00935602, F3+0.00261422, F4+0.04436968. Removing F4 leaves0.00351271. All leave-year-out practice means improve, but remain exposed. The largest gain is BRL F4 at2016-11-07.

New2025: ECB EM improves0.00512841; ECB G100.00079626. Q1/Q2/Q4 improve, Q3 worsens0.00285656. All four horizon subgrids improve; five of eight asset subgrids worsen. MXN worsens0.01040165 across48 origins, exceeding the frozen subgroup harm threshold. BRL, CHF, EUR and INR also worsen. Subgrids recompute their own scales; they are not original-card contributions. Full group/removal/component tables: backtesting/finalalpha19/results/falsification.json.

All-card mean normalized CRPS, joint and tail improve slightly on both cohorts. Different-unit raw losses are never averaged together. Both cohorts contain only multi-cell cards and no text-active forecasts. Empirical single-cell and F1/F4 text-active harm checks are NOT_AVAILABLE. Family membership does not imply text activation, so this cannot identify text's causal contribution. New data cover only2025 and F3; removing that year/family leaves no sample, UNKNOWN.

All100 requested new forecasts succeeded. Four lack complete exact-date labels (both groups at2025-04-14 and2025-04-28, Easter/May1). Missing grids remain in the roster and are never imputed or called forecast failures. Performance covers96 complete grids only; no full100-card score is asserted.

Controls: source SHA locked before scores;100 runner manifests equal local regenerated inputs; each Docker forecast sees only one truncated input and writable output, network none. Full history and labels are not mounted. M0 future-input mutation leaves predictions unchanged. Labels are materialized after all baseline forecasts. Original publication vintages are unauthenticated and early exposure records incomplete: PIT_AUTHENTICITY_LIMITED, independent OOS UNKNOWN.

Host candidate export failed g0 because adapter-receipt.json was inside the strict three-file output directory. The writer was moved outside, but a reused output again contained an extra receipt. Seven cards passed before the second failure; repeated file presence was not fully isolated. That path stopped under the user's repeated-error rule. No assertion was weakened and no third retry occurred. Candidate22/22 and candidate Docker PASS are not claimed. This is additional to decisive magnitude/statistical failures.
