## Executive summary (read this first)

V13-A preserves the frozen V12 conditional marginal law and transplants the
V5.1 empirical rank copula. On 24 reused historical pseudo-origins its local
ratio is 0.893, versus V12's 0.933. The nine post-fit cases improve from
1.077 to 0.960, but post-fit joint loss remains 1.137. This is competition
research, not independent out-of-sample evidence. **READY_FOR_ONE_SHOT_SUBMISSION = NO.**

# V13-COPULA — Conditional Marginals + Empirical Joint Dependence

## Frozen controls and implementation

- Official V5.1 Development baseline: **0.9541**, untouched. The local ratios below cannot be multiplied by that score.
- Frozen V12 parent commit: `123115f`. Frozen V12 artifact SHA-256: `72fc4fab0457bee1caecd2eb8a4c80af7dc9469b403d0a1cf2e67f4c327d63d3`. Neither V12 code nor coefficients were modified.
- Branch: `track2/v13-copula`; no main merge or CodaBench submission.
- `marginal_adapter.py` explicitly samples V12's conditional state probabilities, frozen factor and idiosyncratic shock law, long-horizon adjustment, location reliability, and tail degrees of freedom for each asset independently. It does not call V12's joint world generator. No V11 directional head, stress sleeve, df search, or new marginal fit was introduced.
- A replaces V12's final parametric cross-asset and cross-horizon coupling with V5.1's whole-draw empirical rank ordering. Cellwise sorted V12-law samples are assigned in that order. This preserves empirical ranks exactly, including deterministic stable ties, but it does **not** preserve Pearson covariance exactly.
- B samples one complete origin from a 32-neighbor historical rank bank using 19 frozen current-state features. C samples whole rank sources with the precommitted 70% V5.1 / 30% bank probability. Every cell in a draw shares its source. No weights or neighbor count were searched.

The support manifest was committed before score access (`b812a266fceaeff975c833d7c09d4f222fd093a51d691a6143ed313f6628c99d`). It requires a daily target with at least 100 V12 fit target cells and a matching decoder asset/type. Any unsupported target triggers **exact whole-card V5.1** output. The 24-case run had 1 such card, 22 usable banks and 1 supported card whose historical bank fell back to V5.1 ranks. No family or unit identifier controls support. Final A runs offline without a bank artifact.

The private bank has 414 pre-2009 origins and 38,134 valid target cells across 25 assets and five canonical horizons. Every stored target end is no later than the V12 training cutoff. Retrieval uses only prefix features; runtime additionally requires the chosen prototype and the per-cell percentile reference outcomes to end **before the requested as-of**. The public `bank_manifest.json` stores its SHA-256; outcome-derived bank contents and individual-case diagnostics remain outside Git.

## Evaluation protocol and results

All models used the same fixed 24 generic pre-card pseudo-origins, 2,000 draws and the shared toolkit's CRPS and variogram primitives. Nine cases are labelled post-fit, but span only **two market years**. Fifteen earlier cases are train-period diagnostics: the V12 frozen artifact and its state normalization were trained through 2008, so these cases are not chronological out-of-sample tests. The histories are current/revised data, not verified point-in-time vintages. No official card future window or hidden outcome was read.

Ratios are against V5.1 on the same case. Overall is the geometric mean of paired case composite ratios; component figures are medians of paired ratios, so the columns need not algebraically combine. Lower is better.

| Model | Overall | Marginal | Joint | Tail | Post-fit 9 | Post-fit joint | F1 | F2 | F3 | F4 | Single | Multi | Worst decile | Win rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V5.1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | — |
| V11 | 1.073 | 1.041 | 1.022 | 1.075 | 1.308 | 1.997 | 1.311 | 0.955 | 1.014 | 1.044 | 1.016 | 1.144 | 1.356 | 37.5% |
| V12 | 0.933 | 0.903 | 1.151 | 0.829 | 1.077 | 1.520 | 1.041 | 0.832 | 0.892 | 0.980 | 0.900 | 0.973 | 1.275 | 54.2% |
| V13-A | **0.893** | **0.898** | **1.000** | **0.821** | **0.960** | **1.137** | **0.862** | 0.826 | 0.905 | 0.987 | 0.899 | **0.886** | 1.237 | 58.3% |
| V13-B | 0.978 | 0.898 | 1.186 | 0.821 | 0.925 | 0.951 | 1.231 | 0.826 | 0.910 | 0.987 | 0.899 | 1.080 | 1.232 | 58.3% |
| V13-C | 0.923 | 0.898 | 1.218 | 0.821 | 0.944 | 1.142 | 0.982 | 0.826 | 0.906 | 0.987 | 0.899 | 0.952 | 1.235 | 54.2% |

V13-A meets the local overall, marginal, tail, post-fit and F1 targets. Its overall joint median equals V5.1, while post-fit joint remains above 1.10. B improves the post-fit joint median but has a severe F1 train-period failure (single-case ratio 7.54) and worse overall and multi-cell scores. Correctly implemented C does not beat A. The worst A case is a one-cell F4 train-period diagnostic at 1.531; its worst post-fit F1 two-cell case is 1.273. These reused cases do not establish the tail risk of a future submission.

## Marginal and pairwise checks

For every supported cell in every evaluated case, sorting the A/B/C finite draw values gives exactly the same values. A's per-cell draw ranks equal V5.1's ranks. A frozen-V12 versus adapter simulation at 5 and 21 business days used 5,000 independent draws: tested 5%, 50%, and 95% quantiles agreed within 0.12 V12 standard deviations and standard deviations within 10%. This is sampling equivalence to the frozen one-dimensional law, not equality of independently generated finite V12 tensors. Unsupported whole-card arrays equal V5.1 bit for bit.

The private pair ledger contains 116 pairs: 24 same-asset/different-horizon, 46 different-asset/same-horizon, and 46 different-asset/different-horizon. Every private row records cell indices, assets, horizons, the V5.1 and V12 toolkit variogram contributions, all V13 contributions, rank and Pearson correlations, and draw difference scales. Public grouped medians are in `backtesting/v13_copula/failure_analysis.json`.

| Pair group | V12 median variogram ratio | A median ratio | B median ratio | C median ratio | A median rank correlation change vs V5.1 | A median difference-scale ratio vs V5.1 |
|---|---:|---:|---:|---:|---:|---:|
| Same asset, different horizon | 1.667 | 1.376 | 1.046 | 1.245 | 0.000 | 0.763 |
| Different asset, same horizon | 0.919 | 0.943 | 0.938 | 0.939 | 0.000 | 1.001 |
| Different asset, different horizon | 1.041 | 1.070 | 0.957 | 1.060 | 0.000 | 1.000 |

A retains the V5.1 rank copula. Pearson correlation changes slightly under marginal transformation. Its residual joint weakness concentrates in **within-asset cross-horizon difference scale**, whose median is 0.763 of V5.1 despite identical ranks. This supports a relative marginal-scale/temporal-difference diagnosis; it does not justify changing the frozen V12 marginal in V13. Cross-asset pairs are close to the V5.1 reference in median, though F3 as a family remains 0.905 overall versus V12's 0.892.

## Two targeted repairs and audit trail

1. **Cutoff-local percentile reference.** The first run filtered bank prototype rows by as-of but had computed their percentiles against all pre-2009 outcomes. For train-period pseudo-asofs that indirectly used later outcomes. The bank now stores private standardized outcomes and computes reference ranks using only matured cells before each as-of. A future-value mutation test leaves the forecast unchanged. The first run is invalid for selection.
2. **Copula source scale alignment.** The first two runs mixed raw V5.1 forecast values with bank percentiles in C. This encoded source identity as a false common factor. C now mixes V5.1 **percentiles** with bank percentiles, preserving the frozen 70/30 probability. Its initially attractive post-fit joint figure was an implementation artifact; only `full_eval_final.json` is selection-valid.

No third repair, family rule, mixture sweep, k sweep, or marginal parameter change was made. The pre-repair aggregate JSON files are retained as an explicit invalidated audit trail; their numbers must not be used for candidate choice.

## Verification and limitations

- Seven V13 contract tests passed: exact finite marginals and ranks, whole-draw alignment, stable ties, cutoff-local bank ranks, support gate and exact fallback, V12 marginal statistical comparison, no future-panel access, determinism, and no V12 joint generator call. Two additional V12 leakage/runtime tests passed.
- CLI smoke completed on supported F1, F2, F3 and F4 structures at 500 draws, with correct finite output shapes. A second offline F3 run with the same seed produced the identical 4,000-row forecast without a bank path. Runtime fits no model and makes no network call.
- The original V10 ledger found insufficient independent historical validation and no verified strict point-in-time source for this task. The present 24 cases reuse market episodes; the post-fit subset spans two years. Local proxy selection has now been exposed to these outcomes. The local ratios do not predict an official score.
- Only public aggregates, source/configuration hashes and code were committed. Private bank and per-case/pair diagnostics are outside Git. The SHA values in the public manifests and final evaluation allow verification if those private artifacts are preserved in the authorized research store.

**Final research candidate: V13-A. READY_FOR_ONE_SHOT_SUBMISSION = NO.** Its post-fit joint ratio 1.137 is above the 1.10 concern threshold, and independent point-in-time validation remains insufficient. No Docker submission image was built and no CodaBench submission was made.
