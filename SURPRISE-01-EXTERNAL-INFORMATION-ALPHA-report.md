## Executive summary (read this first)

SURPRISE-01 tests whether first-release macro information adds directional or
future-dispersion information to the actual V5.1 no-text research baseline.
The frozen chronological research experiment has been executed. None of
the three heads improves marginal CRPS. No independent final holdout is claimed.

- Branch: `track2/surprise-01-external-information-alpha`.
- Remote parent: `809b2e192e36db0bcb25b9d62e19b7680a4f3e91`.
- Status at method freeze: not scored.
- Final status: `NO_INDEPENDENT_FINAL_HOLDOUT`. No 2025 labels or scores.
- Submission readiness: `NO`.

### Question and scope

Does newly released external information predict the future distribution
beyond the price-only V5.1 baseline? Direction and dispersion are separate
hypotheses. Neither a THESIS tension predictor nor an ORIGIN propagation
predictor enters this model. No text or same-day market reaction is predicted.

### Data legality and provenance

See `SURPRISE-01-DATA-PROVENANCE.md`. The official competition rules permit
lawful public data conditionally. Offline non-neural fitted artifacts are
permitted only with their true training cutoff and provenance. Runtime
internet cannot be used to fetch macro information. This branch is research
code, not an earlier-as-of competition submission.

Primary sources are dated BLS CPI and Employment Situation releases, Census
advance retail releases, and Board G.17 industrial production releases.
Original first estimates are extracted from the release itself. Later
revisions do not substitute for them. Scanned Census releases are OCR
(optical character recognition) acquisition cases, with their original scans
and extracted text retained privately. Unreadable archives are excluded
before scoring, with an explicit error ledger.

No reproducible pre-release historical consensus with verified reuse rights
was acquired. `TRUE_CONSENSUS_SURPRISE` events: **0**. All six families use
`RELEASE_INNOVATION`. This experiment cannot establish a consensus-surprise
claim.

### Exposure ledger and final feasibility

| Period | Status |
|---|---|
| 2001–2016 | Exposed development / chronological fitting |
| 2017–2023 | Exposed research validation; includes prior THESIS periods |
| 2024 | Exposed by ORIGIN-01, never reused as untouched final |
| 2025 | No independent final claimed; source-audit exposure incident |

A FRED export ignored a requested 2024 date limit and returned observations
through 2026. It was loaded during overlap auditing before method freeze.
No 2025 labels or scores were computed, but a strict independent-final claim
is not defensible. That export is excluded from accepted inputs. No 2025
extension is accepted and 2025 is not reassigned to validation or fitting.

The 25 historical asset definitions are inherited unchanged. FX H.10 uses a
noon observation, rates H.15 and French/AQR factors retain their prior level
or return units. EM source identifiers and factor-provider extension terms
are unverified; this is another obstacle to a faithful 25-asset 2025 final.
All accepted market inputs end on or before 2024-12-18.

### Frozen specification

1. Six families: CPI, Core CPI, Payrolls, Unemployment, Retail Sales,
   Industrial Production. No secondary family enters the experiment.
2. Expectation: previous valid **first-release** actual of the same family.
   Raw innovation is actual minus this prior release. No later revision or
   rolling model selection is used.
3. Scale: expanding same-family innovation sample standard deviation of
   strictly earlier events; minimum 24 prior errors; clip standardized
   innovation to [-5,5]. No threshold sweep.
4. Event origin: verified release before noon Eastern uses the first valid
   asset observation on that date. Noon respects the earliest H.10 market
   observation. Unknown/late release time uses the next valid business
   observation. At most three business days of observation lag are allowed.
5. LEVEL future label: endpoint level difference. RETURN label: sum of the
   next h daily increments. Daily returns are not differentiated again.
   Horizons: 5, 21, 63, 126, 189 business days. Sigma is 252 prior business
   observations, minimum 200, excluding the origin observation.
6. No-intercept ridge beta per family × asset × horizon. Fixed penalty .1*n,
   minimum 24 matured training events. Only labels ending strictly before
   the forecast origin enter its coefficients. Each event receives a new
   expanding historical fit; future labels in the private preparation file
   are never accessed by this coefficient query.
7. LOCATION: beta*S*sigma*sqrt(h) added identically to every V5.1 draw.
8. SCALE: ridge gamma of log(realized path scale / V5.1 draw SD) on abs(S).
   Realized path scale is sqrt(sum of future daily innovation squares), in
   native units. Deviations around the original draw median are multiplied
   by clip(exp(gamma*abs(S)), .75, 1.50). Location is unchanged.
9. COMBINED: the independent location and scale updates together. All three
   heads are reported separately. No best-head deployment claim.
10. Exact existing `v51_no_text_prior` research runner, Numeric V3 plus actual
    V5.1 routing, empty corpus, seed 19. FX/rates 500 draws; factors 1000.
    Baseline calls are per asset as in THESIS/ORIGIN. Worker parallelism
    changes only execution order, never seeds or the model.
11. Small/medium/large bins are abs(S) tertiles from events through 2016.
    Boundaries are frozen before evaluation; tail diagnostics do not fit a
    tail head or change degrees of freedom.
12. Controls: fixed event sign flips; within-family date permutation; fixed
    family cycle. Sign shuffle is algebraically invariant for the abs(S)
    scale head and is not interpreted as a scale falsification test.
13. Uncertainty: 2,000 bootstrap draws of whole release-date clusters,
    retaining all families/assets/horizons. Overlapping long targets leave
    serial dependence across release dates; this is a stated limitation.
14. Research gate per head: ratio < .98, each relevant control captures less than half the primary CRPS gain,
    and paired event-bootstrap primary/control CI upper bound is below 1,
    at least two groups have ratio <1.10, at least ten gaining events with
    no one event >50% of positive gain, cluster CI upper bound <1. No final
    independent gate can be passed by this exposed-data experiment.

### Reproduction

Use Python 3.13 and the shared `qfbench2-common` scorer. Source and optional
PDF/OCR acquisition dependencies are requests, BeautifulSoup, pypdf,
fontTools, Poppler and Tesseract. No internet/PDF tooling is needed by the
runtime `surprise01.engine` update.

```bash
python -m backtesting.surprise01.source_audit --private-root PRIVATE --public-manifest backtesting/surprise01/results/source_manifest.json
python -m backtesting.surprise01.build_event_ledger --raw-manifest PRIVATE/archive_manifest.json --private-out PRIVATE/events.json --audit-out PRIVATE/parse_errors.json
python -m backtesting.surprise01.fit_response --root . --ledger PRIVATE/events.json --private-root PRIVATE
python -m pytest
# Freeze all inputs, commit and push, verify the remote SHA and core files.
python -m backtesting.surprise01.validation_eval --private-root PRIVATE --pre-final-sha VERIFIED_SHA
```

Private raw archives, per-origin future labels, baseline draws and detailed
scored outcomes remain outside Git. Public manifests contain identifiers,
hashes, row counts and date coverage; public score outputs are aggregates.
An official score is not inferred by multiplying a local research ratio.

### Executed research results

PRE_FINAL_SURPRISE01_SHA: `bada39e0bc9cd4b084e7c745f5689f0a59467648`.

Status: **EXPOSED_CHRONOLOGICAL_RESEARCH_ONLY**. **NO_INDEPENDENT_FINAL_HOLDOUT**. No 2025 label or score was generated.

Source ledger: 1,901 family records, 1998-01-09 to 2024-12-17; 41 documented pre-score exclusions. TRUE_CONSENSUS_SURPRISE count: 0. All signals are RELEASE_INNOVATION.

| Head | V5.1 normalized CRPS | Candidate | Ratio | Cells | Events | Active cells |
|---|---:|---:|---:|---:|---:|---:|
| location | 0.613299 | 0.615074 | 1.002894 | 59052 | 382 | 51370 |
| scale | 0.613299 | 0.614320 | 1.001666 | 59052 | 382 | 51370 |
| combined | 0.613299 | 0.616274 | 1.004852 | 59052 | 382 | 51370 |

The three heads are separate precommitted hypotheses. These are research ratios, not official competition scores.

### Direction and dispersion

| Head | Sign accuracy | Pearson IC | Spearman IC | Mean absolute shift / baseline SD | Mean scale multiplier |
|---|---:|---:|---:|---:|---:|
| location | 0.497138 | -0.017051 | -0.004637 | 0.027610 | 1.000000 |
| scale | N/A | 0.076093 | 0.093241 | 0.000000 | 0.943722 |
| combined | 0.497138 | -0.017051 | -0.004637 | 0.027610 | 0.943722 |

Scale-head IC concerns future log path scale / V5.1 SD; it is not directional IC. Directional accuracy concerns nonzero intervention cells.

### Target groups

| Partition | Location ratio | Scale ratio | Combined ratio | Cells | Events |
|---|---:|---:|---:|---:|---:|
| FX | 1.004084 | 0.999574 | 1.004005 | 27120 | 376 |
| Factor/Equity | 1.004093 | 1.003550 | 1.008088 | 15348 | 356 |
| Rates | 1.000498 | 1.002908 | 1.003518 | 16584 | 382 |

### Business-day horizons

| Partition | Location ratio | Scale ratio | Combined ratio | Cells | Events |
|---|---:|---:|---:|---:|---:|
| 5 | 1.004741 | 1.001907 | 1.007153 | 12288 | 382 |
| 21 | 1.003653 | 1.000303 | 1.004328 | 12168 | 380 |
| 63 | 1.002661 | 1.000881 | 1.003805 | 11924 | 372 |
| 126 | 1.002051 | 1.001438 | 1.003762 | 11528 | 360 |
| 189 | 1.001542 | 1.003634 | 1.005250 | 11144 | 348 |

### Release families

| Partition | Location ratio | Scale ratio | Combined ratio | Cells | Events |
|---|---:|---:|---:|---:|---:|
| CPI | 1.001456 | 1.001845 | 1.003348 | 9832 | 96 |
| Core CPI | 1.003602 | 1.004065 | 1.008006 | 9832 | 96 |
| Industrial Production | 1.002071 | 1.001238 | 1.003564 | 9826 | 95 |
| Payrolls | 1.002383 | 1.001206 | 1.003756 | 9868 | 96 |
| Retail Sales | 1.006471 | 1.000564 | 1.007864 | 9826 | 95 |
| Unemployment | 1.001497 | 1.001084 | 1.002715 | 9868 | 96 |

### Negative controls and event uncertainty

| Head | Primary | Sign shuffle | Date permutation | Family permutation | Primary event-bootstrap 95% interval |
|---|---:|---:|---:|---:|---|
| location | 1.002894 | 1.002358 | 1.001510 | 1.002132 | [1.001222, 1.004857] |
| scale | 1.001666 | 1.001666 | 1.001557 | 1.001626 | [1.000369, 1.002835] |
| combined | 1.004852 | 1.004243 | 1.003234 | 1.003940 | [1.002274, 1.007750] |

Resampling unit: entire release date, all families/assets/horizons together; 2,000 replicates, seed 1902. Long overlapping targets retain serial dependence between dates. Cell counts are not independent sample counts.

Scale sign shuffle is algebraically invariant and cannot establish a scale edge. Relevant date/family controls must capture less than half the primary gain, with paired bootstrap upper ratio below one. See negative_controls.json for all paired intervals.

Future-market mutation and later-revision mutation tests passed before scoring.

### Decisions

- location: `NO`.
- scale: `NO`.
- combined: `NO`.

READY_FOR_SURPRISE_02 = **NO**.

READY_FOR_ONE_SHOT_SUBMISSION = **NO**.

This fixed release-innovation specification does not meet its precommitted incremental-information gate. It does not establish absence of information in unavailable true pre-release consensus. No event, asset, horizon, penalty, clip or scale bound was changed after scoring.

### Preservation and private-data firewall

Private scored outcomes: 59,052 rows, SHA-256 `3019eed25a90d8b5389b13ade8301f847754a54dcb2b53f24b9c73875834704c`. Individual outcomes and baseline draws remain outside Git. Public result files contain only aggregate scores, source identifiers, hashes, counts and coverage.

Tests before freeze: repository 399 passed / 2 skipped; SURPRISE-specific 19 passed. Remote result commit and exact-SHA file fetch are verified separately.

### Interpretation and recovery verification

Location does not establish directional information: sign accuracy is 49.7138%,
Pearson IC -0.017051 and Spearman IC -0.004637. Scale has weak positive
dispersion IC (Pearson 0.076093, Spearman 0.093241), but fails to improve CRPS.
This specification establishes neither usable direction nor dispersion improvement.
It does not test unavailable true historical consensus surprises.

Automated workspace maintenance removed the completed local result files before
the result commit. All frozen private cases and 3,111 baseline caches were
recovered from persistent archives. Computational replay used unchanged
PRE_FINAL code, the same case/cache hashes and toolkit v2.4.3. All three
ratios agree with the initially completed run within 1e-13. No retraining,
parameter change or 2025 evaluation occurred. This is recovery of an exposed
research result, not a second independent experiment.

### Actual asset coverage

The inherited universe contains 25 assets. Scored 2017–2024 cases cover
22 assets: ten H.10 FX, six rates and six factors. BRL, INR and CNY
produce no eligible matured evaluation cells under the frozen coverage,
prior-volatility and target-maturity rules. They were not removed after
scoring; the private case hash was fixed before evaluation. EM source
identifiers remain unverified. The 25-asset universe must not be confused
with 25 scored assets.
