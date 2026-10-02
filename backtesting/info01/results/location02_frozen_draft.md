# LOCATION-02 frozen draft: external pre-outcome information

## Executive summary

Specification only; **not executed**. Freeze ECB original euro-area SPF point expectations as the sole information source, EUR as the sole first asset, and a five-feature Ridge location experiment. This remains research crossfit on exposed history; there is no verified independent validation universe. Acquisition and row-level PIT/errata verification must finish before fitting. INFO01 does not authorize submission.

### 1. Source and original fields

Source ID: `ECB_SPF_ORIGINAL`. Accepted documentary history: 2015-01-23 through 2024-10-18. Earlier quarterly data exist, but publication-day evidence was not completed and they are excluded. Use original dated reports/press releases, not the current aggregate CSV or refreshed individual-forecaster panel. Obtain all 40 quarterly releases only in a later acquisition stage; no such full panel was built in INFO01.

Raw fields: originally released aggregate **HICP inflation point forecast** and **real GDP growth point forecast**, annual percentage changes, indexed by the exact forecast target calendar year. Retain the current/next/second-following target-year labels where necessary to identify a previous-round forecast of the same year. Do not use realized inflation/GDP, staff projections, Consensus Economics comparisons, unemployment forecasts, respondent identities, densities, new topic indicators or fitted expectation estimates.

Required schema: source ID, survey round, variable, target year, value in percent, survey-response window, actual publication date, publication-time evidence, timezone, conservative `available_at`, original URL, original bytes SHA256, representation, original-vs-amended status, amendment publication date, and field-specific extraction locator. Original downloadable PDF/HTML bytes are separate from extracted numerical rows. A hash computed now proves retrieval reproducibility, not historic immutability.

### 2. Publication and availability

Use the actual date listed in the official archive and release. Respondent deadline, quarter start, forecast target year and document creation time are not public availability. Default date-only upper bound: 23:59:59 **Europe/Berlin**, with actual daylight saving offset. Do not infer a fixed lag; the 2024Q4 survey closed October 3 but was published October 18.

Forecast cutoff is the parent convention: 16:00 **America/New_York** on the preceding repository business day. Keep the parent's business-day semantics; the helper's weekday predecessor is not a complete exchange holiday calendar. Reject ambiguous holiday/delay cutoffs rather than inventing them. A same-date date-only source may become usable before the New York cutoff if the Europe/Berlin end-of-day upper bound is already earlier; compare aware timestamps rather than enforcing a misleading blanket next-day rule.

At each origin take the latest proven field available at the cutoff. Never overwrite an old row with a subsequently corrected value. If a known correction lacks the initially released field, exclude that vintage, or activate the independently dated corrected version only after its publication; no retroactive correction. Unknown version/correction provenance blocks the affected row. No historical originals means no substitution with another source.

### 3. Exactly five inputs, no search

1. Next-calendar-year HICP aggregate point forecast, percent.
2. Next-calendar-year GDP aggregate point forecast, percent.
3. HICP revision versus the preceding available original round **for the same target year**, percentage points.
4. GDP revision versus that same preceding-round/target-year match, percentage points.
5. Source age in repository business days, capped only for eligibility, not optimized.

Maximum source age: 90 business days, fixed. No source-age imputation or backward fill. If the target-year match or any required field is absent, output zero correction at that origin; missingness never chooses a replacement model. Do not compare different target years across the January roll. Train-fold-only centering/scaling; zero-variance training columns become zero. No nonlinear expansion, embedding, parameter search, threshold search or feature redesign after results.

### 4. Asset and horizons

Eligible asset: **EUR only**, using its exact existing return convention. Europe expectations are directly associated with EUR's economic region; there is no assertion that rising expectations cause positive EUR returns. Do not broadcast to all FX, nominal US Treasury maturities, factors or the nonexistent commodity targets. Initial marginal experiment uses exact 5/21/63/126/189 **business-day** horizons. Public-card 64/65/127/128/etc. horizons are not relabeled.

### 5. Training and test universe

All historical targets remain **RESEARCH-EXPOSED**. No independent OOS claim. Potential future research dataset is the existing EUR continuous ledger, with only original source vintages from 2015 onward and labels whose maturity is no later than 2024-12-18. The 24 public cards are not an optimization or independent test cohort.

Use fixed monthly origins, the first existing repository business day of each month, reducing repeated copies of a quarterly release. Initial training years 2015-2019; forward annual test folds 2020, 2021, 2022, 2023, 2024. Each fold trains only on earlier origins whose labels have matured before the first test cutoff. Use the maximum 189-business-day maturity/purge rule for the shared dataset; no overlap leaking a future maturity into training. The 2024 fold excludes labels maturing beyond the frozen cutoff. No labels are acquired in INFO01; this is a future eligibility rule, not an implemented dataset.

A five-horizon shared Ridge uses the same five standardized inputs, alpha=1.0 and an intercept; horizon evaluation is reported separately. Avoid independent per-horizon searches or family customization. The first model pools standardized center-error targets with equal weight per original survey round, so repeated horizons/origins do not create false information depth. Training-only means/scales and preprocessing are frozen per fold. Baseline inactive/missing-source origins have exactly zero shift.

### 6. Target and candidate, future execution only

`delta = (truth - original V5.1 median) / original V5.1 predictive SD`.

`candidate_draw = original V5.1_draw + predicted_delta * original V5.1_SD`.

Use unchanged baseline model, draws and seeds. No scale, tail, covariance, copula, path or draw-rank adjustment. No R2 recalibration or T0 Ridge change. A marginal shift may affect full joint scoring, so no multi-card success claim follows from an EUR marginal result; any later transfer must recompute the entire frozen card with original scorer and predeclare safety gates.

### 7. Evaluation and blocking conditions

Before future execution, commit/push/verify the complete source acquisition manifest and this design's implementation PRE; validate original fields, timestamps, amendments, target-year matches, train-only preprocessing and maturity/purge. Stop when a source dependency is missing. Exact parent scorer, all five horizons, all eligible origins, and incremental information controls must be precommitted. Suggested fixed controls: structure/age-only, own-price-only parent baseline, and release-block shuffling with fixed seeds; they are future tests, not INFO01 results. Do not choose a winning horizon/year/subset.

Report the fixed marginal score and full applicable components, effect versus baseline, annual fold results and release/time-block uncertainty. Quarterly observations make effective N small. A bootstrap on exposed years does not establish independent evidence. Future independent validation requires a prospectively sealed cohort and frozen data/model/cutoff before labels are accessible.

Largest leakage risks: current-history overwrite, response-date activation, hindsight amendments, mixing forecast target years, training labels not matured by cutoff, and treating repeated quarterly values as independent samples. Practical limits: only EUR, less than ten years of accepted dated source history, sparse quarterly information and no verified independent universe. **No fitting or scoring has been performed.**
