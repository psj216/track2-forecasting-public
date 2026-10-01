## Executive summary (read this first)

**NEXT_RESEARCH_AXIS = LOCATION.** The greatest measured mathematical headroom
is information about the future distribution's center. Perfect location reaches
0.489209 on the 24-card geometric research proxy and 0.386635 on the separate
59,052-cell marginal research universe. Rank-only joint improvement reaches
0.902435 overall; even the optimistic joint-zero bound is 0.849187.

**This does not establish a practical or official route to 0.5.** The 24-card
location result is 1.042291 under arithmetic sensitivity, due to joint damage
on some F1 cards. The restricted shared location correction worsens both
universes (1.246644 and 1.019000). Perfect location plus rank-only joint
optimization is more robust in the 24-card diagnostic: geometric 0.363948,
arithmetic sensitivity 0.462180. No predictive model or submission was built.

### Provenance and completion

- Branch: `track2/ceiling-01-score-headroom`.
- Parent: `31ab7cd70020d0c2d55df6e7e767fa91de98fffc`.
- PRE_RESULT_CEILING01_SHA: `0d396b84d361c752a921cf439f7f846637401cb0`.
- Scorer status: **RESEARCH_PROXY_ONLY**. See CEILING-01-SCORER-AUDIT.md.
- Oracle code, tests, methodology and data hashes were pushed and fetched
  at the exact pre-result SHA before evaluation. Result commit adds summaries
  and this report; oracle methodology is unchanged.
- Python 3.13.15, qfbench2-common 2.4.3, NumPy 2.5.3, pandas 3.0.6,
  SciPy 1.18.1. Runtime recovery used those same versions and frozen arrays.
- Before freeze: 415 repository tests passed, 2 integration tests skipped;
  16 CEILING contracts passed, including four bitwise CLI baseline reproductions.
  After runtime recovery: 415 passed, 2 skipped again.
- SURPRISE baseline exactly reproduces the archived 59,052 losses: maximum
  absolute error **0.0**; normalized mean CRPS **0.6132985094431782**.
- Per-card, cell, pair, origin losses and realized outcomes remain outside Git.
  Public manifest records hashes, counts and date ranges. No 2025 outcomes,
  independent OOS claim, official score extrapolation or CodaBench submission.

### Separate evaluation universes

| Universe | Scope | Cards / origins | Cells | Single / multi | Aggregation |
|---|---|---:|---:|---|---|
| V13_REVISED_PUBLIC_24 | First 6 alphabetically eligible daily public cards per family, revised-history reconstruction | 24 cards; 2003-08-12–2023-07-21 | 63 | 13 / 11 cards; 13 / 50 cells | Geometric mean of V5.1-normalized card composites |
| SURPRISE_EXPOSED_MARGINAL_ONLY | Preserved exposed 2017-01-06–2024-12-11 release cases | 376 market origins; 382 release events | 59,052 | Single marginal evaluations; no joint composite | Ratio of arithmetic mean volatility-normalized CRPS |

The 24 cards are the V13 reconstruction proxy, not the unavailable original
V12/V13 pseudo-origin archive. Original grouped reports, THESIS and ORIGIN
results were audited, but their missing detailed ledgers were not invented or
merged. Neither universe is the official scored roster. Repeated events and
long overlapping horizons are not independent observations.

### Oracle and component-bound matrix

All figures are ratios to the applicable V5.1 research baseline. The arithmetic
column is a sensitivity check on the same 24 ratios, not an official score.
The continuous universe scores marginal CRPS only; joint and tail-component
zero bounds are consequently inapplicable there. Its tail-warp row describes
CRPS after a tail transformation, not a scored tail component.

| Oracle / bound | 24-card geometric | 24-card arithmetic sensitivity | 59,052-cell marginal |
|---|---:|---:|---:|
| BASELINE | 1.000000 | 1.000000 | 1.000000 |
| LOCATION_ORACLE | 0.489209 | 1.042291 | 0.386635 |
| SCALE_ORACLE_UNCONSTRAINED | 0.968602 | 1.508912 | 0.818504 |
| SCALE_ORACLE_BOUNDED | 1.196772 | 3.790618 | 0.865040 |
| LOCATION_SCALE_ORACLE_UNCONSTRAINED | 0.000000 | 0.000000 | 0.000000 |
| LOCATION_SCALE_ORACLE_BOUNDED | 0.199853 | 0.271866 | 0.193318 |
| TAIL_ORACLE | 0.990344 | 3.063369 | 0.821683 |
| JOINT_ORACLE | 0.902435 | 0.911271 | N/A |
| LOCATION_JOINT_ORACLE | 0.363948 | 0.462180 | N/A |
| MARGINAL_ZERO_LOSS | 0.369253 | 0.383929 | 0.000000 |
| JOINT_ZERO_LOSS | 0.849187 | 0.862500 | N/A |
| TAIL_ZERO_LOSS | 0.752368 | 0.753571 | N/A |
| MARGINAL_JOINT_ZERO_LOSS | 0.242625 | 0.246429 | N/A |
| MARGINAL_TAIL_ZERO_LOSS | 0.000000 | 0.137500 | N/A |
| JOINT_TAIL_ZERO_LOSS | 0.606562 | 0.616071 | N/A |
| ALL_ZERO_LOSS | 0.000000 | 0.000000 | 0.000000 |
| STRUCTURED_LOCATION_CROSSFIT | 1.246644 | 1.802021 | 1.019000 |
| STRUCTURED_SCALE_CROSSFIT | 1.341872 | 4.647777 | 1.010087 |

Unrestricted location+scale collapses draws to truth (a approximately zero),
so its zero is tautological mathematical headroom. The 24-card 1e-12 result
is the pre-existing geometric floor; the exact mathematical value is zero.
Bounded location+scale retains half the original spread and is reported
separately. The scale oracle minimizes marginal CRPS, not the full composite.

### What has to change to reach the requested targets?

Each percentage below is a uniform fraction of **each card's baseline component
loss**, replaced in the actual research arithmetic and inverted through the
geometric aggregator. It is not a linear approximation or an official forecast.
For joint/marginal and marginal/tail combinations, the same percentage applies
to both selected components. Actual oracle rows above also demonstrate
feasible truth-aware draw transformations.

| Target research ratio | Mathematically possible? | Marginal alone reduction | Marginal + joint reduction each | Marginal + tail reduction each | All three reduction each | Continuous marginal reduction |
|---|---|---:|---:|---:|---:|---:|
| 0.8 | YES | 32.34% | 26.53% | 23.10% | 20.00% | 20% |
| 0.7 | YES | 48.39% | 39.78% | 34.56% | 30.00% | 30% |
| 0.6 | YES | 64.30% | 53.02% | 45.93% | 40.00% | 40% |
| 0.5 | YES | 80.01% | 66.24% | 57.15% | 50.00% | 50% |

For **0.5**, marginal-only replacement requires **80.0051%** loss reduction
on every card. Joint+tail alone cannot reach it: their best zero-loss bound
is **0.606562**. Joint alone cannot even reach 0.8 (**0.849187** floor).
Tail alone can reach 0.8 under an optimistic 80.8586% loss replacement,
but its zero-loss floor **0.752368** prevents 0.7/0.6/0.5.

The continuous universe needs a 50% marginal loss reduction for ratio 0.5;
perfect location supplies 61.3365%. This is future-truth access, not a
forecastable signal. **Official absolute targets 0.8/0.7/0.6/0.5 remain
unverified**, because the sealed roster and reference scales are unavailable.

### Single-cell and multi-cell ceilings

| Diagnostic | 13 single-cell cards | 11 multi-cell cards |
|---|---:|---:|
| BASELINE | 1.000000 | 1.000000 |
| LOCATION_ORACLE | 0.293763 | 0.893850 |
| SCALE_ORACLE_UNCONSTRAINED | 0.851053 | 1.128628 |
| SCALE_ORACLE_BOUNDED | 0.884556 | 1.710675 |
| TAIL_ORACLE | 0.665412 | 1.584457 |
| LOCATION_SCALE_ORACLE_BOUNDED | 0.146881 | 0.287590 |
| JOINT_ORACLE | 1.000000 | 0.799330 |
| LOCATION_JOINT_ORACLE | 0.293763 | 0.468813 |
| MARGINAL_ZERO_LOSS | 0.285714 | 0.500000 |
| JOINT_ZERO_LOSS | 1.000000 | 0.700000 |
| TAIL_ZERO_LOSS | 0.714286 | 0.800000 |

Joint permutation has exactly no benefit on a single cell. Single-cell
marginal+tail weights are 5/7 and 2/7. Leaving all 13 single-cell cards at
baseline while making the other 11 zero gives **0.541667** under arithmetic
sensitivity, but **0.00000316228** under the floored geometric research metric
(exact mathematical geometric mean: zero). Thus there is no positive
single-cell floor in that geometric proxy. An arithmetic universe with this
same 13/24 share would require single-cell improvement to pass 0.5; this is
not evidence about the unknown official roster share.

### Family decomposition

Each family has six cards and baseline-relative loss 1.0. Raw losses in rates,
FX and returns have unlike units and are not pooled to invent family loss shares.
The table identifies family oracle limitations within the normalized proxy.

| Family | Location | Bounded scale | Tail warp | Joint | Location + joint | Bounded location+scale |
|---|---:|---:|---:|---:|---:|---:|
| T2-F1 | 1.706269 | 3.048227 | 2.772804 | 0.742972 | 0.643664 | 0.441729 |
| T2-F2 | 0.417239 | 0.865711 | 0.700226 | 1.000000 | 0.417239 | 0.208620 |
| T2-F3 | 0.450869 | 0.864724 | 0.799612 | 0.892672 | 0.366116 | 0.194031 |
| T2-F4 | 0.178441 | 0.898975 | 0.619593 | 1.000000 | 0.178441 | 0.089220 |

F1 is the bottleneck for a location-only transformation: **1.706269** even
with perfect cell medians. Fixed-rank cross-horizon draw differences can be
incompatible with the realized inter-horizon difference. Location+joint lowers
F1 to **0.643664**. F4 has the largest location headroom (**0.178441**).
This does not establish that its future location is predictable.

### Horizon decomposition

The card column uses marginal+tail restricted-cell ratios (5/7,2/7), excluding
joint; cross-horizon joint contributions are in the separate pair table below.
A dash means no such horizon in the fixed card universe. The actual 64/129-day
cards are retained, not silently relabeled to 63/126. All five requested
horizons exist in the continuous universe.

| Horizon BD | Card location | Card bounded scale | Card tail warp | Continuous location | Continuous bounded scale | Continuous tail warp |
|---|---:|---:|---:|---:|---:|---:|
| 5 | N/A | N/A | N/A | 0.386469 | 0.874381 | 0.825680 |
| 21 | 0.226913 | 0.913547 | 0.642690 | 0.409973 | 0.863954 | 0.829469 |
| 63 | 0.455070 | 0.774744 | 0.687147 | 0.397852 | 0.859831 | 0.826651 |
| 64 | 0.730320 | 0.859254 | 0.748822 | N/A | N/A | N/A |
| 126 | 0.884446 | 0.636883 | 0.717042 | 0.387132 | 0.859782 | 0.819987 |
| 129 | 0.712320 | 0.913494 | 0.751810 | N/A | N/A | N/A |
| 189 | 0.905375 | 0.627829 | 0.712991 | 0.354610 | 0.867384 | 0.807924 |

### Rank-only joint dependence and topology

All final joint-oracle arrays preserve every sorted marginal **bit for bit**.
The optimizer uses three frozen starts and 12,000 greedy swaps per start;
results are feasible oracle constructions, not certified global optima.
The final toolkit scorer independently recomputes every joint score. The
optimistic joint-zero bound is reported separately. Pair geometric ratios can
be dominated by nearly-zero losses, so arithmetic sensitivity is also shown.

| Pair topology | Pairs | Joint-only geometric | Joint-only arithmetic | Location+joint geometric | Location+joint arithmetic |
|---|---:|---:|---:|---:|---:|
| same_asset_different_horizon | 25 | 0.000540 | 0.236440 | 0.000043 | 0.036922 |
| different_asset_same_horizon | 52 | 0.419339 | 0.871626 | 0.000930 | 0.045619 |
| different_asset_different_horizon | 52 | 0.432518 | 0.693609 | 0.001617 | 0.055827 |

For same-asset/different-horizon pairs, location-only arithmetic pair ratios
reach a mean **897.0646**, despite a geometric mean **0.693456**. Very small
baseline variogram denominators make some temporal losses explode; the
overall composite and arithmetic sensitivity must be inspected together.

### Scale, tail, coverage and channel audit

The 63-cell unconstrained scale median is **0.760509**, range
**0.013152–8.745283**. The practical oracle hits 0.5 for **38.0952%** of cells
and 2.0 for **23.8095%**. After perfect location all bounded scales are 0.5.
These fitted-on-one-outcome values do not estimate forecasting capability.

Bounded scale reduces geometric marginal loss to **0.824364**, but increases
geometric multi-card joint ratio to **2.351097**, making overall composite
**1.196772**. Tail warp preserves the median and central-50% interpolation
supports, count and monotonicity. It improves single-cell composite to
**0.665412**, but multi-cell composite worsens to **1.584457**. Therefore
changing one component's draw geometry can spoil another component.

In the scored 24 cards, V5.1 and the existing V13-R2 support gate both cover
24/24, with no fallback. Making fallback perfect gives **1.0**, so no measured
fallback headroom exists in this selected universe. Across all 103 practice
cards, the gate supports 99 and rejects 4 non-daily cards. Those four have no
paired outcomes in this study, so their score ceiling is **unmeasured**, not zero.

Text audit is **OBSERVED_CHANNEL_CONTRIBUTION**, using matching card, outcome,
Numeric V3 base draws, draw count and seed. Four of 24 cards change under
existing V5.1 text/context routing. Numeric-only ratio is **1.008696** versus
text-enabled **1.000000**: text/numeric ratio **0.991379**, roughly 0.8621%
relative improvement on this exposed sample. F1 numeric-only is 0.989325,
so text slightly worsens it; F4 numeric-only is 1.046411, so text improves it.
F2/F3 are identical by the existing route. No historical text contribution
is inferred for continuous origins without a frozen corpus.

### Mathematical versus structured headroom

| Exposed diagnostic | 24-card composite | Continuous marginal |
|---|---:|---:|
| Perfect cell location | 0.489209 | 0.386635 |
| Family/group × horizon location, leave one era out | 1.246644 | 1.019000 |
| Group × horizon bounded scale, leave one era out | 1.341872 | 1.010087 |

Eras are fixed: <=2016, 2017–2019, 2020–2021, 2022–2024. The held era's
outcomes are excluded from its correction, but other exposed eras can lie
later in calendar time and overlapping horizons remain. This is **not
independent OOS**. Shared corrections are medians of standardized location
errors and bounded oracle scales, with fixed fallback on insufficient groups.
No feature, ridge, threshold, macro/neural model or submission candidate is tuned.

### Decision and limits

**NEXT_RESEARCH_AXIS = LOCATION.** Measured perfect-location reduction is
51.0791% in the card geometric proxy and 61.3365% in continuous marginal CRPS.
Rank-only joint reduces the card proxy only 9.7565%, and its optimistic
zero-loss bound reduces it only 15.0813%. Scale alone is substantially smaller
in the continuous universe (bounded: 13.4960%). Coverage contributes zero
measured headroom on supported cards, and observed text uplift is 0.8621%.

The next axis means seeking usable information about future location, with
joint/path compatibility checked on multi-cell cards. This report provides
no such predictive information: structured corrections fail. No next model
has been implemented. The answer to the core question is that **0.5 is
mathematically possible on these research proxies**, chiefly through major
marginal/location improvement, while **official feasibility and practical
predictability remain unestablished**.

### Reproduction

```bash
python -m backtesting.ceiling01.build_baseline_ledger --private /absolute/private-ceiling --surprise /absolute/private-surprise
python -m pytest
# Commit, push and verify the method/input freeze before scoring.
python -m backtesting.ceiling01.diagnostics --private /absolute/private-ceiling --surprise /absolute/private-surprise --pre-result-sha 0d396b84d361c752a921cf439f7f846637401cb0
```

Private inputs must be outside the repository and must match the frozen
hashes. Public artifacts include all requested matrices, bounds, family,
horizon, single/multi, coverage, text and target-feasibility summaries.

