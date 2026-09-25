## Executive summary (read this first)

This experimental branch routes frozen Numeric V3 worlds through small F1,
F2, and F4 state gates. F3 worlds remain exact V3 bytes. The preliminary
chronological public selection did not clear the admission gate, so this is
not a submission image or an improvement claim. Detailed evaluation outputs
stay outside this public repository.

### Runtime

Use `FORECAST_MODE=integrated-v4` only for local experimentation. The default
config is `integrated-conservative`; the declared alternatives are
`integrated-moderate` and `integrated-strong`, selected through
`V4_INTEGRATED_CONFIG`. These are experimental choices, not trained weights.
`NUMERIC_VARIANT=v3` retains the exact existing bootstrap anchor.

- F1 level cells: a calm, low-momentum regime modestly contracts sample width;
  a persistent high-volatility regime modestly expands it. Horizon length
  changes the scale factor. Cell centers and draw ordering are preserved.
- F2: a recent, dated document must literally name a single target asset,
  assert one direction, and mention one clear event class in the same
  sentence. Recent panel momentum must agree. A small fraction of complete
  historical worlds is then selected through the existing world sampler.
  Multi-asset or ambiguous cases return V3 exactly. No House call occurs.
- F3: exact V3 draws, with the existing rank-based joint transmission.
- F4: calm periods can contract width. Persistent high volatility expands
  width and may inject a bounded number of historical extreme paths. Lack of
  separated historical stress windows leaves that sleeve empty.

The corpus reader applies the date cutoff before opening document content.
Malformed or absent evidence returns V3. No event-specific direction is
inferred from a generic macro statement.

### Historical evaluation

The evaluation deduplicates equivalent public inputs, creates four global
chronological folds, and purges earlier label intervals crossing fold
boundaries. The first two folds choose among the three declared configs at
500 draws. The last two are opened only if selection passes all gates. A
survivor then runs at 500 and 1,000 draws with three seeds. These public
histories were used in previous development; their later dates are not a
genuinely new holdout.

Require a geometric ratio at most 0.97 versus paired V3, controlled worst
decile, no material family or state degradation, improvement in every fold
and seed, and sufficient changed cases in F1/F2/F4. The dated text corpus
has little coverage at historical pseudo-as-of dates, so F2 cannot be
certified by numeric-only replay. The gate rejects models that merely return
V3 on most cases. The imported official score primitives are used; private
normalization and Development outcomes are not available.

```bash
python -m backtesting.integrated_v4_backtest --root . \
  --out /absolute/path/outside/public/repository/integrated-v4-run --cutoffs 6
```

No Docker image or CodaBench descriptor is generated when selection fails.
The preserved official baseline remains Numeric V3.
