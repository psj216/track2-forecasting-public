## Executive summary (read this first)

Preserve submitted commit `31224eff97f9f06808dd52b7f2ee5457594cb387` and compare
small numeric changes independently. The default runtime remains Numeric V3;
V4 variants are opt-in, numeric-only experiments. Main is not changed.
No leaderboard score or rank is predicted by this experiment.

## Frozen experiment

- A: six causal features, weighted historical analogues, and independent
  fragility/persistence/analogue-quality routing.
- B: blocks standardized by lagged 60-observation EWM root-mean-square volatility,
  restored with a fixed blend of current 20/120-observation variance.
- C: single-cell monotone tail scaling; lower/upper factors independently selected
  from `0.85, 1.00, 1.15` on the fit split only.
- F3: exact Numeric V3 output for every variant, including tail and ensemble routes.
- An A+B combination is eligible only if A and B independently pass selection.
- Only eligible candidates receive a fixed 70% V3 / 30% candidate draw mixture.
  Whole asset/horizon worlds are mixed; point predictions are never averaged.

Changing normalized shocks changes the volatility-clustering process. It is not
claimed to preserve the original clustering exactly. Shared historical block starts
preserve contemporaneous shock alignment, and horizons use one accumulated path.
The fixed five-observation block length, drift and uncertainty multiplier are retained
to avoid combining unrelated interventions in this first experiment.

## Dates and leakage

The default experiment uses six pseudo-cutoffs per public card, 1,000 draws, and two
fixed RNG salts. Equivalent target inputs and outcomes are deduplicated across cards.
All unique dates are split globally at 40% and 70%. Cases whose full label interval
extends into the next partition are purged. The oldest split fits C, the middle
split selects candidates, and the newest split evaluates the frozen selection once.
At least 40 eligible singleton fit cases are needed for a non-identity C transform.

Each forecaster receives a prefix ending at its cutoff. Analogue features precede
their sampled block. Historical volatility is lagged, so a shock cannot shrink
itself by inflating its own denominator. Text is absent from all numeric ablations.

This protects cutoff and partition boundaries, not data provenance unavailable to us.
Public macro panels can contain later revisions; these histories have also been used
in previous development. The newest split is held out for THIS frozen experiment,
not claimed to be globally unseen or a substitute for prospective evaluation.
Nearby or overlapping forecasts within a partition are correlated. Seeds are averaged
within a case and never counted as additional independent observations.

## Metrics and admission

Use existing official component functions and the Track-2 selectable-tail composite.
For a single cell the weights are `5/7, 0, 2/7`. Private normalization is unavailable;
normalize only against our same-case Numeric V3 for diagnostics. This is not a copy
of, approximation to, or forecast of the private leaderboard score.

The admission gate excludes F3, whose output is frozen, so unchanged F3 cases do not
dilute failures. Require at least 30 active cases and 10 dates, geometric ratio <1,
median <=1.02, win rate >=0.50, 90th-percentile ratio <=1.10, marginal ratio <=1.03,
tail ratio <=1.05, every seed geometric ratio <=1.01, and every family ratio <=1.03.
These conservative thresholds can reject an average improvement. They are fixed
before outcomes, not relaxed when a candidate is disappointing.

All candidate results are reported for transparency. Only the candidate frozen on
selection can be admitted on holdout. A rejected winner cannot be replaced by a
different holdout winner. A subsequent revision needs a new evaluation plan.

## Run locally

Use Python 3.13 and toolkit v2.4.2, matching the submitted runtime.
Keep outputs OUTSIDE this public repository:

```bash
python -m backtesting.v4_ablation --root . --out ../private-v4-run --cutoffs 6 --draws 1000
FORECAST_MODE=numeric NUMERIC_VARIANT=v4-a forecast --panels /input \
  --text /input/text --asof YYYY-MM-DD --out /output/forecast.parquet
```

Supported runtime variants are `v3` (default), `v4-a`, `v4-b`, and `v4-ab`.
Tail fit parameters remain development artifacts; they are not silently deployed.
The run writes protocol, fit, frozen-selection, ratio tables and summary once.
An existing output directory is refused. Results never enter the image or public git.

## Numeric control and later stages

The dedicated workflow builds Numeric-only from the frozen submitted commit, with
the same 500-draw default and all numerical settings. It checks offline parity with
f4-only, publishes a distinct Docker Hub tag, verifies anonymous pull by digest, and
produces a descriptor draft. Team authentication and submission quota remain separate.
The control declares the House model for the API-category ablation but performs no
model calls. It must be evaluated under the same organizer roster and scoring version
as the existing result before attributing the difference to reasoning.

Adaptive blocks, extra draws and a text-driven router are later independent studies.
Increasing draw count reduces sampling error, not model bias, and costs runtime.
Routing text into a numeric variant is deliberately refused until the numeric choices
have passed calibration and organizer-endpoint behavior has been evaluated.
