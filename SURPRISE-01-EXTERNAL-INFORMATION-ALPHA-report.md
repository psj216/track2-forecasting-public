## Executive summary (read this first)

SURPRISE-01 tests whether first-release macro information adds directional or
future-dispersion information to the actual V5.1 no-text research baseline.
This commit freezes a chronological research experiment before scoring any
SURPRISE candidate. It does not claim an independent final holdout.

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
14. Research gate per head: ratio < .98, primary beats relevant controls,
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

### Results

Pending the remotely verified method/input freeze.
