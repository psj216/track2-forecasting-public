## Executive summary (read this first)

Numeric V3 is frozen at its known official baseline. This branch adds an opt-in,
F1-only center adjustment with no width, tail, text, F2, F3, or F4 changes. The
first public historical selection failed: all five predetermined shrinkage and
cap choices were worse than V3. No holdout, Docker submission image, or official
Development submission is authorized by this result.

### Experiment

The experiment takes twelve pseudo-as-of origins from each public card. It
deduplicates repeated histories, separates dates into fit, selection, and
holdout, and purges observations whose labels cross the next split. F1 level
forecasts only use the V3 sample median, observed later value, forecast spread,
business-day horizon band, and panel frequency. It clips each standardized
training error to [-1, 1], shrinks group averages by n / (n + 20), then checks
five predeclared strengths/caps on the middle period. Every applied change is a
constant shift of a V3 cell's draws; its dispersion and draw ordering remain.

The selected middle-period candidate must itself clear an F1 geometric ratio
below 0.98, at least 65 percent wins, and a worst decile at most 1.05. If it
does, one frozen parameter choice can be checked in the later period at 500
and 1,000 draws across three seeds. The historical labels and scoring results
are written outside the public repository. Scoring calls the shared official
metric primitives through the existing paired V3 comparator. Its local ratio
cannot be converted into an official leaderboard score.

### Result

The middle split has 64 independent F1 cases on 62 dates. The best of the five
predeclared candidates had a geometric ratio of 1.00055, win rate 35.9 percent,
and worst-decile ratio 1.00554. It failed the selection gate, so the latest
split was not evaluated and the decision is **retain Numeric V3**.

These public histories were examined during older experiments. Even a later
successful run over the same histories must not be called a fully untouched
holdout. An external truly unseen validation source is required to satisfy
that separate submission gate.

### Reproduce

```bash
python -m backtesting.f1_center_backtest --root . \
  --out /absolute/path/outside/the/public/repo/f1-center-run
```

The opt-in runtime setting is `FORECAST_MODE=f1-center` with a frozen
`F1_CENTER_PATH`. Without a valid config, an F1 forecast fails rather than
silently claiming calibration. F2/F3/F4 produce exactly the Numeric V3 Parquet
bytes for the same inputs and seed. This mode is experimental and must not be
used for a submission until all stated gates pass.
