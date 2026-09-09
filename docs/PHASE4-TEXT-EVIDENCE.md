## Executive summary (read this first)

Phase 4 adds a cutoff-safe text interpreter on top of Numeric v3.  The language model identifies
evidence, contradictions, causal shocks, competing views, and asset directions.  It never emits a
forecast value or a scenario probability.  Python validates citations and computes a probability
ledger.  The ledger remains in shadow mode until Phase 5 backtesting proves that a particular
distribution adjustment improves the numeric baseline.

## Boundary between the model and Python

| Language model may produce | Language model may not produce |
|---|---|
| Evidence claim tied to a `doc_id` | Price or return forecast |
| Support and contradiction strength | Basis-point drift |
| Evidence confidence and relevance | Volatility multiplier |
| Shock label and causal direction | Monte Carlo draws |
| Asset direction in its native quote | Scenario probability |
| Tail direction and volatility impact | Final scenario weight |

The distinction is not cosmetic.  A model can interpret language, but an unconstrained numeric
answer is neither calibrated nor reproducible.  The deterministic probability engine can be
backtested, capped, routed by family, and removed when it hurts.

## Competing-view schema

Every accepted interpretation contains three intentionally partisan views:

1. `long` gives the strongest upside or continuation case.
2. `short` gives the strongest downside or reversal case.
3. `outlier` gives a structural outcome that both conventional sides may miss.

The `skeptic` then names a shared assumption and the observation that would break it.  No scenario
is deleted.  Python assigns every scenario at least one percent before Phase 5 calibration.

## Cutoff and grounding controls

The interpreter opens only files listed in `corpus_index.json`.  Each public timestamp must be no
later than `--asof`.  A path must resolve inside the supplied text directory, have a `.txt` suffix,
and fit the input-size limit.  Duplicate identifiers, invalid dates, path traversal, missing files,
and oversized documents are rejected before a model sees them.

Model JSON is also fail-closed.  It must use the exact schema.  Scores must be finite and between
zero and one.  Every evidence item must cite a supplied document.  Every view must cite accepted
evidence.  Unknown assets, shocks, scenarios, documents, and non-finite values reject the entire
interpretation.  A rejected interpretation is labelled in `forecast_meta.json`; Numeric v3 remains
the forecast.

## Scenario probability ledger

The model supplies scenario support, contradiction, confidence, and relevance.  Python applies:

\[
L_s = \log(\pi_s) + 2\lambda_f(S_s-C_s)Q_sR_s
\]

Here, \(\pi_s\) is a fixed prior and \(\lambda_f\) is the family router strength.  F1 receives a
small text update.  F2 and F4 receive larger updates because their task definitions make text the
leading indicator.  A softmax converts the logits into relative weights.  Python then reserves a
one-percent floor for each scenario and renormalizes the remaining mass.

These are shadow probabilities in Phase 4.  They are recorded for inspection but do not alter
`forecast.parquet`.

## Failure behavior

If the endpoint is absent, the request fails, or the reply violates the schema, the program still
writes an admissible Numeric v3 submission.  It sets `reasoning_applied` to false and records the
specific reason.  Silent fallback is prohibited because it makes later text-ablation results
meaningless.

## Phase 5 promotion gate

Phase 5 may transform draws only after paired pseudo-as-of backtests compare:

- Numeric v3 with no text adjustment;
- the same draws with the proposed text adjustment;
- the same seeds, cutoffs, assets, and horizons.

Promotion should be family-specific.  F1 must remain close to the numeric anchor.  F2 may shift
regime weights.  F3 may change joint world pairing.  F4 may add directional tail mass.  Any route
that fails to improve its protected diagnostic remains in shadow mode.
