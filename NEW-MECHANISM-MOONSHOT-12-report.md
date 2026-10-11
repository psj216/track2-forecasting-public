## Executive summary (read this first)

**Result: ANALOG_NOT_PREDICTIVE.** The frozen historical gate failed. No 24-card outcome was opened, no candidate was built and nothing was submitted.
The past-path library oracle reached 0.636035565, passing the 0.65 headroom gate. Actual PIT nearest-state retrieval with K=64 scored 1.040966086 against the exact same-cell V5.1 baseline. Equal-year ratio was 1.032292673. This does not meet the required 0.85/0.90 gates.

## Universe, provenance and target semantics

The original canonical ledger has 1,250 origins, 135,994 cells and 25 assets, 2001-01-02 through 2024-12-10. Evaluation uses all 467 canonical origins and 48,084 eligible cells in 2016–2024. All historical data are RESEARCH_EXPOSED; INDEPENDENT_OOS=false.
Original canonical ledger and preserved center ledger SHA256s matched exactly. Baseline cell CRPS was reused from the frozen center ledger; no original V5.1 draws were rebuilt. Its common CRPS source is byte-identical to the pinned validation scorer. Source panels are existing repository prefixes, not newly acquired data. Historical publication-vintage uncertainty beyond the inherited prefix convention remains.
Rate/FX levels use scaled historical endpoint changes rebased to the current observed level. Factors use the original accumulated daily return increments without scale normalization. Actual inherited business-day endpoints and gap rules are retained. Each complete analog path must have every requested endpoint strictly before the query origin. No per-cell retrieval or independently shuffled marginal occurs.
Eight own-asset fingerprint dimensions and two shared dimensions were fixed. Median/IQR normalization is fitted to prior state rows only. Distances use shared finite dimensions with 80% coverage. Uniform draws share one historical origin across all joint cells. Technical fallback requires at least 8 complete analogs. No text/PCA/new external source is used. Monthly macro assets are absent from the continuous universe; they were not dropped from an evaluated card set because no card phase occurred.

## Oracle and its limitation

Future-informed oracle marginal ratio: **0.636035565**. The full-card composite oracle is unavailable in the canonical marginal ledger and was not manufactured by opening card outcomes.
The diagnostic exhaustively finds the best single complete path and adds whole scenarios greedily up to 8 members. Final scores use 1000 complete draws and the inherited fair estimator. Greedy mixtures do not certify the optimum over every possible mixture. This headroom is hindsight, not evidence that market state can identify those scenarios.

## Historical-only K selection and forward test

K was chosen only on 2009–2015; 2016–2024 results and 24-card losses were excluded from selection. The four fixed choices were 8,16,32,64; ties prefer larger K.
| K | 2009–2015 ratio |
|---:|---:|
| 8 | 1.263832850 |
| 16 | 1.153248116 |
| 32 | 1.090869235 |
| 64 | 1.050677664 |

| Forward year | Primary CRPS ratio |
|---:|---:|
| 2016 | 0.980910642 |
| 2017 | 0.998021652 |
| 2018 | 1.090470408 |
| 2019 | 1.117175644 |
| 2020 | 0.991555222 |
| 2021 | 1.072188504 |
| 2022 | 1.062655837 |
| 2023 | 0.995107145 |
| 2024 | 0.982549002 |

Improved years: 5/9. Improved origins: 35.12%. Median origin ratio: 1.036102254. Fallback origins: 0.
Equal-origin 1.034748731; equal-year 1.032292673; asset-balanced 1.036351852; horizon-balanced 1.040268391. Balanced ratios are equal means of within-block ratios; primary is the ratio of all summed normalized cell losses.

## Controls and block uncertainty

| Control | Mean / ratio | Empirical lower-tail p |
|---|---:|---:|
| RANDOM_ANALOG | 1.021233978 | 1.0 |
| TIME_MATCHED_RANDOM | 1.020043919 | 1.0 |
| DISTANCE_SHUFFLE | 1.021293528 | 1.0 |
| REVERSED_SIMILARITY | 1.060159907 | — |
| CONSTANT_RECENT | 1.204718557 | — |

Stochastic controls each have 2000 replicates, seed 31812. The cheap null statistic scores the exact empirical K-path distribution with shared fair=False CRPS for BOTH primary and null. This integrates resampling noise and is kept separate from the main 1000-draw fair=True forecast ratio. Monte Carlo p-values use plus-one correction. Distance shuffle is uniform reassignment of the past eligible ranks and is distributionally equivalent to random K selection. Time matching uses fixed 5/10-year business-day age buckets. Every donor was already fully matured.
| Bootstrap block | Primary95% CI |
|---|---|
| origin (467 blocks) | [1.031669247, 1.050590184] |
| year (9 blocks) | [1.004618711, 1.073002205] |
| asset (22 blocks) | [1.018470066, 1.059078304] |

Each bootstrap has 5000 whole-block replicates, conditional on frozen retrieval. Origin blocks share overlapping future horizons; year and asset blocks provide complementary dependent-data views. No IID cell bootstrap or independent-OOS claim is made.
Largest-year share of gross gain: 15.04%; largest-asset share: 7.88%. All assets/horizons/years remain in the aggregate. These gross gains do not offset the total forecast degradation.

## Kill gate, card firewall and next action

The historical model worsens baseline and fails the frozen large-effect gates. Any statistical separation from random analog selection does not override that failure. No favorable year, asset, horizon, K or amplitude was substituted. The card PRE, card scoring, joint/tail/F1–F4 results, card/family bootstrap, inverse-distance card diagnostic and optional hybrid are NOT_RUN_GATE2_FAILED. No card result, submission candidate or 0.5-class signal exists.
**ZERO_POINT_FIVE_CLASS_SIGNAL=false. NEXT=V51-FINAL-SAFE-SUBMISSION-13.** No further forecasting research or actual submission is executed in this task.
The validated exact safe V5.1 image/source and common 2.4.2 remain unchanged. Historical Development 0.9541 remains a reference only; it was not re-estimated or multiplied by proxy ratios, and the actual historical uploaded-artifact identity remains unproven.

## Tests and release preservation

- research: 30 passed in 0.61s
- affected: 56 passed in 15.66s
- full: 981 passed, 25 skipped, 3 deselected, 2 warnings in 59.01s
- common: 250 passed in 1.28s

The three inherited immutable historical branch assertions are deselected under the already-documented branch-only exception. No test expectation/assertion was weakened. Other skips remain documented existing gated/integration tests.
Branch: `track2/new-mechanism-moonshot-12`. Parent: `126a7c628aa60783986450037309f5f59603276a`. Oracle/spec freeze: `30aa3227f36eaa4148b797a4bab605ae82b1bf71`. Historical implementation freeze: `23f211bec343d25fbc2b22d85b38e273743fab24`. Conditional card PRE: NOT_REACHED.
Final RESULT SHA, authoritative remote compare/file checks, protected-file verification, clean tree and new private recovery ZIP CRC/member/full hashes are recorded in the external final receipt after RESULT, avoiding self-reference.
