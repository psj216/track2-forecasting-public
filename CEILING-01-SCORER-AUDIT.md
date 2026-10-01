## Executive summary (read this first)

**RESEARCH_PROXY_ONLY.** The official scorer and historical research scorer do
not share their roster, normalization denominators, or aggregation. This study
reproduces the actual V13 reconstruction research scorer, plus the separate
SURPRISE marginal-only scorer. No number here is an official lower bound or an
official score prediction. The official 0.9541 score is not multiplied by ratios.

### Audited source and runtime

Parent commit: `31ab7cd70020d0c2d55df6e7e767fa91de98fffc`.
Python 3.13.15; qfbench2-common 2.4.3. Scoring primitives are imported,
never reimplemented. The existing canonical Track 2 `_composite` supplies
the raw component scores; the adapter supplies the already-existing research
normalization and aggregation from `backtesting/v13_copula/evaluate_proxy.py`.

Sources read: README, AGENTS, canonical scoring.py, tail.py, normalization.py,
aggregate.py, official.py, shared scoring/crps.py, numeric_v3.py,
text_first_v5.py, text_interpreter_v51.py, thesis01/v51_shift.py,
V12/V13 reports and reconstructed evaluation utilities, THESIS/ORIGIN/SURPRISE
reports, results, frozen manifests, available private SURPRISE cases and caches.
Original V12/V13 pseudo-origin outcomes are not available as a reconstructable
ledger. Their archived grouped metrics are not treated as a new evaluation.

### Exact metrics

- Marginal: toolkit `crps_marginal`, mean over flattened asset/horizon cells.
  Fair ensemble CRPS uses the finite-ensemble `n*(n-1)` spread denominator.
- Joint: toolkit `variogram_score(p=0.5)`, sum over all ordered cell pairs,
  including the structurally zero diagonal. No pair standardization is added.
  A cell-specific location shift can change this score. A common translation
  of all cells cannot. Canonical code also supports energy scoring; the fixed
  reconstructed research universe uses variogram throughout.
- Tail: existing Track 2 `tail_pinball`, mean over four quantile levels
  0.01/0.05/0.95/0.99 and cells. Quantiles use NumPy linear interpolation.
  The optional historical coverage arm differs and is not substituted for
  pinball. SURPRISE's old coverage diagnostic is not a composite component.
- Baseline normalization: each card component is divided by that card's
  **actual V5.1 loss**, floored at 1e-12, exactly as V13 research evaluation.
  These are not the official reference-forecast loss denominators.
- Multi-cell: component-relative composite uses weights 0.5/0.3/0.2.
- Single-cell: joint has no dependence information. Its weight becomes zero;
  marginal/tail weights become 5/7 and 2/7. Joint-zero substitution changes
  nothing on a single-cell card.
- Card aggregation: V13 research takes the geometric mean of per-card
  composite ratios, with every ratio floored at 1e-12 before logging.
  Original component summaries use medians, which cannot be summed to recover
  the overall geometric result. We retain per-card arithmetic internally.
- Horizon tables: a marginal+tail restricted-cell diagnostic, renormalized
  5/7 and 2/7, without inventing joint structure for the restricted slice.
  Joint cross-horizon effects are separately summarized by actual pair topology.
- SURPRISE universe: mean of per-cell CRPS / (prior sigma*sqrt(h)), and ratio
  of these means. It has no joint or scored tail component. It is not merged
  with the 24-card composite. Release-family repeated origins retain their
  original weights; cells are not independent sample counts.

### Official differences, missing cells, and fallback

Official `_score` consumes a committed C1 grid and private ref_scale. The
official `aggregate_submission` calls the Hub fixed-roster arithmetic
aggregation: scores are clipped to [0,4], participant failures remain in the
denominator with plan-defined penalties (documented default 4). Missing
reference/grid/normalization is an organizer failure, not a zero or dropped
card. Without those sealed references and plan, official equality is not
verifiable. No official component bound can be inferred from this proxy.

Research card selection reproduces the V13 reconstruction's first six
alphabetically eligible daily cards per family; missing history excludes
cards **before** scoring. The eligible universe itself is not the official
roster. Once frozen, every selected finite cell must be present; no silent
imputation or denominator shrinkage is allowed. Complete V5.1 text routing is
used on matched cards, and its exact numeric baseline is also retained.

V13-R2's existing whole-card support gate is audited for coverage. Unsupported
V13 cards return V5.1 exactly; this does not mean V5.1 is unsupported.
Missing/unsupported cards outside this universe have no measurable loss here.
Counts of such cards are descriptive, not a forecast of their score impact.

### Bounds and oracle interpretation frozen before results

Zero component substitutions call the same adapter arithmetic and geometric
aggregation. They need not correspond to a realizable joint forecast.
Any exactly-zero card creates a zero mathematical geometric mean; the
existing 1e-12 floor instead yields a positive numerical result. Coverage and
single/multi floors therefore also show arithmetic sensitivity. The latter
is a research sensitivity measure, not a substitute official score.

Perfect location plus unrestricted scale normally collapses all draws to the
outcome (a=0). This tautological zero is reported explicitly as degenerate.
Bounded [0.5,2] scale remains separate. The rank-only joint optimizer returns
a feasible construction, not a certified global optimum; joint-zero arithmetic
is the separate optimistic bound. Tail warp preserves central-50% interpolation
supports, median, draw count, and monotonic ordering but may worsen other terms.

Group/horizon corrections leave one calendar era out, reusing already exposed
outcomes. They are structured diagnostics, not independent OOS or evidence that
oracle parameters can be forecast. No predictive feature/model/submission is
created. Method, seed, proposal budget, universe, and tests are frozen and pushed
before oracle evaluation.
