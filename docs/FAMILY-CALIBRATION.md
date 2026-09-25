## Executive summary (read this first)

This experimental F1 head preserves V3 sampled worlds and changes their center and
width with one coefficient set shared across the family. F3, F2 and F4 remain
exactly unchanged. No fitted parameter is active by default. Backtest outcomes and
fitted parameters must remain outside the public repository.

For example, persistence-50 shifts each marginal center halfway from the V3 sample
mean toward the last observed level. Residual worlds retain their ranks. This
preserves their sampled rank dependence, but does not preserve exact accumulated
shock paths across horizons.

### Declared experiment

Twelve configurations include identity, persistence, mean reversion toward the
past 252-observation mean, bounded 60-observation trend, constant width changes,
and mild horizon width tilts. The width multiplier is scale times
(horizon / 21) ** tilt, clipped to [0.70, 1.30]. Horizons are business days.
The trend uses actual business-day elapsed time, including lower-frequency panels.
Only F1 level targets with at least 60 prior observations are transformed.

The executable uses six historical origins per public card and two 1,000-draw
seeds. It removes duplicate target histories. Global chronological boundaries
assign fit/select/holdout partitions and purge any earlier label interval reaching
the next partition. Fold one chooses only on fit, then evaluates select. Fold two
chooses on fit plus select, then evaluates holdout. Each choice is frozen before
that fold's later observations are scored. Two seeds are averaged within cases;
they are not treated as independent observations.

Candidate admission uses the existing V4 safety gates including at least 30 cases,
10 dates, geometric loss ratio below one, median at most 1.02, win rate at least
50 percent, worst decile at most 1.10, marginal at most 1.03 and tail at most 1.05.
Both later fold results must pass before considering an official A/B submission.
Failure retains V3. The selected configuration can differ between folds because
only the later fold has the additional earlier labels available.

All CRPS, variogram and tail calculations delegate to the existing official
scorer imports. Component-normalized ratios compare against this model's V3 draws,
not the organizer reference baseline, and are not leaderboard scores. These public
histories have been examined in earlier experiments; calling the latest partition
an untouched new holdout would be incorrect. Revised historical data vintages and
repeated model development remain limitations.

### Run and runtime interface

```bash
python -m backtesting.family_calibration_backtest --root . \
  --out /absolute/path/outside/repository/f1-calibration
```

`FamilyCalibration` serializes with `dataclasses.asdict`. Runtime loading through
`load_family_calibration(Path)` requires `trained_through`, the last training-label
date. `apply_family_calibration` rejects an affected forecast whose as-of is on or
before that date. Such old cards must retain V3; applying coefficients fitted on
later history would leak information. No coefficients fitted to official card
outcomes are used. Newer as-of forecasts can use only admitted coefficients after
an explicit experiment configuration is supplied.

F1-only evidence is smaller than the previous all-family V4 report. The fixed
minimum remains 30 independent cases in a fold; a smaller fold is explicitly
insufficient and does not receive a lowered threshold. Identity is always the
safe fallback even though it cannot pass a strict-improvement gate. Unselected
configuration results on select are exploratory diagnostics only; the frozen
fold-one result is the only out-of-training result for that choice.
