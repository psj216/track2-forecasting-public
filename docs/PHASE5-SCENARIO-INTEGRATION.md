## Executive summary (read this first)

Phase 5 connects validated text evidence to Numeric v3 through one sampled economic world per
Monte Carlo draw.  The integration is family-specific and bounded.  F1 receives only a small
context adjustment.  F2 receives a regime mixture.  F3 changes joint pairing without changing a
single marginal value.  F4 receives an asymmetric shock branch.  The `TEXT_INTEGRATION=off` kill
switch restores Numeric v3 exactly.

No empirical score improvement is claimed yet.  The current environment has no organizer model
endpoint, so model-generated evidence cannot be replayed across historical pseudo-as-of cases.
Phase 6 must calibrate or reject each family route before final submission.

## One draw is one economic world

Python samples one scenario label and one positive severity for each draw.  That scenario is
shared by all assets and all horizons in the draw.  An inflation world cannot simultaneously be a
growth world merely because two asset loops sampled independently.

For an asset \(a\), horizon \(h\), and draw \(d\), the bounded value routes use the pattern:

\[
X'_{d,a,h}=X_{d,a,h}+\sigma_{a,h}\sqrt{h/H}\,B_{f,d,a}
\]

Here, \(H\) is the longest requested business-day horizon.  The family-specific adjustment
\(B\) comes from scenario direction, activation, severity, and optional tail shock.  Every change
is capped in units of the Numeric v3 forecast standard deviation.

## Family router

| Family | Mean cap mechanism | Volatility | Shock branch | Joint behavior |
|---|---:|---:|---:|---|
| T2-F1 | 0.05 standard-deviation coefficient | up to +3% | none | Numeric v3 retained |
| T2-F2 | 0.25 standard-deviation coefficient | up to +12% | up to 3% of draws | Shared regime world |
| T2-F3 | none | unchanged | none | 15% rank blend; exact marginals |
| T2-F4 | 0.10 standard-deviation coefficient | up to +10% | up to 7% of draws | Shared shock world |

The absolute per-cell change caps are 0.15 standard deviations for F1, 1.5 for F2, and 3.5 for
F4.  These are conservative engineering bounds, not calibrated optima.

## Evidence-to-world mapping

Each scenario cites Phase-4 evidence identifiers.  Python combines only those cited items.
Direction is calculated in the target's native quote convention.  Support, confidence, and
relevance determine scenario activation.  Contradicting evidence reduces the exposure.  Missing
asset directions remain zero; Python does not invent an exposure for an unmentioned asset.

Scenario probabilities come from the Phase-4 Python ledger.  The language model never supplies a
probability field.  The sampled scenario count is recorded in `forecast_meta.json` so the realized
mixture is auditable.

## F3 marginal-preserving route

F3 uses the scenario world only as a rank signal.  For every asset and horizon, Python sorts the
existing Numeric v3 marginal values and reassigns them to draw identifiers.  Therefore the mean,
variance, skew, quantiles, marginal CRPS contribution, and tail contribution are unchanged by
construction.  Only which asset outcomes occur together changes.

## F4 shock route

F4 selects at most seven percent of draws with the strongest supported tail exposure.  Those draws
receive a directional Student-t shock.  The same scenario and severity propagate through all
assets and grow with the square root of the horizon ratio.  The final per-cell change is capped at
3.5 Numeric v3 standard deviations.

This is intentionally a candidate, not a victory lap.  Too much tail mass can improve one crisis
card and damage ten ordinary cards.  Phase 6 must tune the fraction and magnitude with paired
pseudo-as-of tests.

## Failure and rollback

Integration is skipped when evidence is absent, rejected, directionless, or the family is not
supported.  `forecast_meta.json` records the reason.  Setting `TEXT_INTEGRATION=off` bypasses all
scenario transformations after evidence interpretation and returns the exact Numeric v3 draws.
