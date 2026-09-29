# V12/V13 reconstructed implementation audit

## Identity and provenance

This is a **RECONSTRUCTED IMPLEMENTATION** based on the recovery pack. It is not the lost V12/V13 executable, coefficient artifact or private historical bank. The V5.1 base is remote commit `8b926cfce029a604b6336ceef4e3bf3b39ec5246`. The root `V12-JOINT-NATIVE-report.md` and `V13-COPULA-report.md` are unaltered historical design references. The archived `backtesting/v13_copula/archive/full_eval_final.json` is read-only evidence, not an optimization target.

## Reconstructed structure

V12 builds one synchronized date row with `X[origin,asset,19]`, `G[origin,21]`, five-horizon masked `Y` and target-end dates. Training purges cells crossing the cutoff and excludes monthly macro panels without point-in-time vintages. Five masked PCA axes, five ordinal future states, state-conditioned PSD covariance, a common long-horizon expert and Student-t radial shocks drive a whole-world runtime. Fitting is offline. The runtime loads frozen JSON and reads only panel rows at or before as-of. The archived negative directional-location reliability is frozen at zero; it was not refit on outcomes in this reconstruction.

V13 samples those frozen conditional marginals independently of V12's joint generator. Candidate A applies V5.1 whole-draw stable empirical ranks. B selects a whole origin from a 32-neighbor bank, recomputing every percentile reference only from target cells matured before the requested as-of. C chooses 70% V5.1 percentiles and 30% bank percentiles per whole draw. B/C sampled duplicate prototypes are converted to stable finite rank permutations before inverse assignment, preserving every cell's finite marginal values exactly. Daily targets require at least 100 fit target cells and matching decoder asset/type. Unsupported targets return the entire V5.1 tensor unchanged.

## Dataset and artifact divergence

| Quantity | Historical report | New public-panel reconstruction |
|---|---:|---:|
| Origin cap | 950 | 950 |
| Usable V12 fit origins | 414 | 368 |
| Fit target cells | 38,134 | 31,377 |
| Trained daily decoder assets | 25 | 23 |
| New bank origins | Original 414 | 416 |

The public panels and the report do not reconstruct the original 25-asset training tensor or coefficients. The new bank uses revised public prefixes and has a different SHA. Monthly NFP, CPI_ALL and UNRATE have no trained decoder. The old private case and pair ledgers were not included in the recovery pack. These are substantive model and evidence differences, not rounding noise.

## Verification and archived comparison

Eleven focused tests cover masked target dates, PSD, whole-world shape, deterministic seeds, future-panel invariance, finite marginal permutations, V5.1 rank preservation, stable ties, whole-card fallback, cutoff-local bank references, support gates and runtime no-fit. The actual V5.1 CLI and reconstructed V13 generated 2,000 draws for one public F1, F2, F3 and F4 structure. F3 had two horizons and four assets. All output cells were finite and A/B/C had identical per-cell sorted values. A separate bank-free F3 run produced identical parquet hashes with the same seed.

| Model | Archived 24 pseudo-origin ratio | New, different 24 public-card proxy ratio |
|---|---:|---:|
| V12 | 0.933 | Not evaluated |
| V13-A | 0.893 | 1.741 |
| V13-B | 0.978 | 1.659 |
| V13-C | 0.923 | 1.716 |

The archived evaluation has 24 cases, 2,000 draws, four family groups and **nine** post-fit cases. Its old ratios are preserved under `archive/`. The exact 24 pseudo-origin definitions and outcome ledger are missing. We therefore fixed a new selection before reading its scores: the first six alphabetical public cards per family with revised-history future observations. This proxy has **19** post-fit cards, overlapping market histories and no verified historical vintages. Its A overall ratio is 1.741, marginal median 1.166, joint median 1.934 and win rate 5/24. This is adverse evidence for the reconstruction, but the different case set makes the archived 0.893 and new 1.741 unpaired. No parameter, weight, threshold or neighbor count was changed after viewing it. The four-card checks are output and contract smokes, not the 24-card scores.

Mismatch classes: **A implementation mismatch** (new training tensor/code), **B missing historical private artifact** (bank and case ledger), **C randomness/seed mismatch unassessable**, and **D irrecoverable original-model detail** (coefficients and precise case definitions). Nothing was tuned to the archived ratios. No official submission or Docker image was made.

**READY_FOR_ONE_SHOT_SUBMISSION = NO.**
