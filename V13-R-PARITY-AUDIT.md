## Executive summary (read this first)

V13-R audits the reconstructed V13 against the V12/V13 reports and a new 24-card public-panel proxy. It identifies two implementation defects: daily return targets were represented as a difference of two daily returns, and raw asset units dominated the five-factor PCA and pooled long-horizon expert. The repaired A result is **1.655 overall** and **1.204 on 19 post-fit cards** under the corrected proxy. This is still far from the archived V13-A **0.893** on its *different, unrecoverable* pseudo-origin ledger. Marginal and tail calibration are not stable enough to begin V14. No parameter was selected against either evaluation.

## Scope and immutable comparisons

- Parent reconstructed V13 commit: `4f3cf96c30e216a5d8e66b4a4d0f4c59a2f620df`. Its artifact remains at `qfbench2_track_forecasting/v12/artifacts.json`. This audit creates a separate `artifacts_v13_r.json`; the V13 and V14 refs are not changed.
- Archived original V13-A: overall **0.893**, marginal median **0.898**, joint median **1.000**, tail median **0.821**, post-fit 9 overall **0.960** and joint median **1.137**. Original source and frozen coefficients are lost. The archive's nine post-fit cases are not the new proxy's 19.
- The previously published reconstructed 24-card proxy **1.741** used a defective return truth calculation. It subtracted one daily return from another. It must not be treated as the corrected proxy baseline.
- The same 24 selected public cards, 2,000 draws, seed 19, and paired V5.1 forecasts were used for the old and repaired artifacts in the corrected proxy. Its histories are revised and lack verified point-in-time vintages. These outcomes and individual-case scores remain outside Git.

## Target representation and cutoff

The V5.1 numeric path treats a `level` panel as a level to be differenced and a `log_return` panel as daily increments to be **summed** through the horizon. V12-R originally fit `after - before` for every target. The corrected V12-R training labels are level differences for level targets and sums of the next horizon's daily increments for return targets. Missing return observations within the synchronized horizon cause a masked label, rather than silently summing a partial path. The proxy evaluator now uses the corresponding cumulative return truth. These historical public panels and synchronization rules cannot prove parity to the lost original private target builder. The fit cell count falls from **31,377** to **26,945**, versus **38,134** in the archived V12 report. The dataset still has **950** synchronized observed origins and cutoff-matured target labels.

## Decoder, units, and cross-horizon differences

The previous PCA operated on rates in percentage points, FX in native quote units and factors in return units without scaling. Its five factors explained **99.44%** of raw covariance, versus **57.16%** reported by the original V12. The repaired PCA normalizes each asset using cutoff-safe fit-label standard deviation, computes factors in those units, and converts decoder loadings back to native units. Its five-factor explained share is **65.83%**. This is an implementation correction, not an attempt to target 57.16%.

The previous pooled long-horizon expert regressed raw residuals from different asset units and applied one raw coefficient vector to every asset. The repair fits the residual divided by each asset's training scale and converts predictions back to native units. This removed a large common-unit location bias in the audited FX long-horizon example. The repaired JPY residual standard deviation is **2.03** instead of **0.029**; its 63-day draw spread in the audited joint example moved closer to V5.1. The original V12 expert design and frozen coefficients cannot be recovered exactly.

Two audited long-horizon rate cards had extreme normalized variogram ratios, yet their draw-difference standard deviations were within an order of magnitude of V5.1. In both cases the V5.1 pairwise variogram contribution was about **0.0002**. Near-zero reference error magnifies a moderate absolute variogram difference into a very large ratio. The repaired model still has an inaccurate within-asset horizon difference distribution on those examples. This is a remaining joint issue, not evidence of a 75–218-fold unit conversion error.

The support rule remains daily target, matching decoder asset/type and at least 100 matured fit target cells. Unsupported whole cards retain exact V5.1 fallback. V13-A continues to preserve its repaired frozen one-dimensional sample values and V5.1 finite ranks. No runtime fit is introduced.

## Corrected revised-history proxy

Ratios below compare each candidate with V5.1 on the **same** selected card. Overall is a geometric mean of composite ratios; component figures are medians of individual component ratios.

| Artifact/candidate | 24-card overall | Marginal median | Joint median | Tail median | 19 post-fit overall | Post-fit marginal | Post-fit joint | Post-fit tail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Previous reconstruction A, corrected truth | 2.025 | 1.200 | 1.953 | 1.158 | 1.568 | 1.204 | 1.702 | 1.265 |
| V13-R A | **1.655** | 1.144 | 1.500 | 1.089 | **1.204** | 1.152 | 1.444 | 1.213 |
| V13-R B | 1.665 | 1.144 | 3.016 | 1.089 | 1.321 | 1.152 | 2.752 | 1.213 |
| V13-R C | 1.656 | 1.144 | 1.912 | 1.089 | 1.226 | 1.152 | 1.537 | 1.213 |

The A improvement under a fixed corrected protocol is a sanity result, not independent model validation. The original V13-A 0.893 is only an archived structural reference; different pseudo-origins and missing original coefficients prevent a score-parity assertion. In the corrected proxy, A's post-fit marginal **1.152** and tail **1.213** remain above V5.1. V14 is blocked.

## Attribution and remaining work

| Category | Finding |
|---|---|
| A. Implementation mismatch | Return target/truth representation; unnormalized PCA and pooled expert; corrected here. Horizon-difference behavior still differs. |
| B. Missing historical private artifact | The original V12 model coefficients, historical bank and pseudo-origin outcomes are unavailable. The V13-R bank is newly rebuilt from public revised panels and remains private. |
| C. Randomness/seed mismatch | No evidence that seed differences explain the structural failures; the paired diagnostic fixes seed 19 and 2,000 draws. |
| D. Irrecoverable original-model detail | Original normalization, expert fitting and exact target synchronization are described at design level, not sufficiently to restore original coefficients. |

Future work should audit synchronized target maturity and per-asset horizon semantics, then marginal and tail calibration without tuning to this exposed proxy. Start V14 only after a fresh parity check shows stable marginal and tail behavior with a residual joint issue.

## Reproduction

- Artifact: `qfbench2_track_forecasting/v12/artifacts_v13_r.json`. It was fit once from the public revised panels with the repaired code. Its SHA-256 is `4a0b50178ebb6dfd4be3e2760ec95471de70eeeae4eea6b84383194ccdd10e3d`.
- Public grouped output: `backtesting/v13_copula/parity_audit_24_grouped.json`. The private bank SHA and its artifact link are in `bank_manifest_v13_r.json`; bank outcomes and per-card diagnostic rows are excluded from Git.
- Run `python -m qfbench2_track_forecasting.v12.train --units units --out <artifact path>`, then `python -m backtesting.v13_copula.build_bank --units units --artifact <artifact path> --out <private bank path> --manifest <public manifest path>`. For the proxy run `python -m backtesting.v13_copula.evaluate_proxy --units units --artifact <artifact path> --bank <private bank path> --private-out <outside repo> --public-out <public grouped path> --draws 2000`.
- The archived `full_eval_final.json` is not a training target. No weight, neighbor count, support threshold or family-specific rule changed.
