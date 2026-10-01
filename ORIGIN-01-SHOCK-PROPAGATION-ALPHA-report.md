## Executive summary (read this first)

ORIGIN-01 tests whether yesterday's unusually large source-market move
predicts a target market that has moved less than one historical standard
deviation today. This is a directed predictive test, not a causal claim.
The final 2024 scores will be appended only after this entire specification,
tests, private model hash, and evaluation code have a verified GitHub commit.

### Frozen specification before 2024 reveal

- Parent: THESIS-01 result `7e73f3623ec93e7efca852904ab6d656489d2b5c`.
- Universe: the existing 25 daily public-panel assets; no external data.
- Daily innovations: level difference or raw return/log-return increment.
- Volatility: prior 252 observations, minimum 200, clip standardized values to ±8.
- Source shock at t-1: signed excess above |z| ≥ 2.0.
- Target unreacted gate at t: |z| < 1.0; target self-shock excluded.
- Five-business-day anchored historical fit grid, labels fully mature by 2023-12-31.
- No-intercept ridge per target/horizon, λ = 0.1 × active fit row count; minimum 30 fit rows.
- Native location shift = gated predicted normalized movement × prior scale × √h.
- V5.1 numeric plus text-first-v5.1 with an empty frozen text corpus; 19 seed,
  500 draws for FX/rates and 1,000 for factor/equity. This is an explicit
  no-text historical ablation, not an official card result.
- Final 2024 grid: every 21 business days anchored on 2001-01-02; maturities
  no later than 2024-12-18; horizons 5, 21, 63, 126, 189.
- Controls: source event date permutation across 2024 grid origins; fixed
  peer-name reassignment at inference; synthetic future-row mutation.
  Consistent relabeling at both fit and evaluation would be algebraically
  invariant under isotropic ridge and is therefore not a useful placebo.
- Success: overall CRPS ratio < 1.00, intervention-only < 0.98, controls
  inferior, and intervention spread across assets. Low sample may be
  inconclusive. No specification changes after the final 2024 reveal.

Frozen artifact hashes and counts are in
`backtesting/origin01/frozen_inputs.json`. Individual target outcomes and
per-origin scores remain outside Git. The verified pre-final SHA precedes
the 2024 result below.

### Frozen 2024 one-shot result

The GitHub pre-final branch was verified at
`51b4e81f4aeff1811c0990bc1532f2259ef8779f` before constructing
any 2024 target labels. Its parent is
`7e73f3623ec93e7efca852904ab6d656489d2b5c`.
The final run used exactly that code and the three private inputs whose
SHA-256 values were committed in `frozen_inputs.json`. No coefficient,
threshold, gate, asset, or horizon was changed after reveal.

| Group | Cells | V5.1 normalized CRPS | ORIGIN normalized CRPS | Ratio |
| --- | ---: | ---: | ---: | ---: |
| Final overall | 570 | 0.484031 | 0.484004 | 0.999944 |
| Active only | 15 | 0.520874 | 0.519842 | 0.998019 |
| FX | 300 | 0.474604 | 0.474552 | 0.999891 |
| Rates | 204 | 0.496697 | 0.496697 | 1.000000 |
| Factor/Equity | 66 | 0.487732 | 0.487732 | 1.000000 |
| 5 business days | 164 | 0.595717 | 0.595680 | 0.999938 |
| 21 business days | 158 | 0.488860 | 0.488812 | 0.999902 |
| 63 business days | 124 | 0.462567 | 0.462552 | 0.999969 |
| 126 business days | 86 | 0.398781 | 0.398781 | 1.000000 |
| 189 business days | 38 (LOW SAMPLE) | 0.244916 | 0.244916 | 1.000000 |

There were 12 grid origins in 2024, one origin with a source shock, and
one source shock event. The mean active source count was 0.0833 per
origin. Only 15/570 cells were active (2.63%). All 15 interventions
have the same dominant source, `UST_2Y`, and are FX targets across
5, 21, and 63 business days. Their directional sign accuracy was
80.0%, Pearson IC 0.518, Spearman IC 0.586, and mean absolute shift
was only 0.00261 of V5.1's standard deviation. The 15 cells share
one shock event and must not be counted as 15 independent events.

The one observed source shock was in the 2–2.5 sigma bin; that bin's
active CRPS ratio was 0.998019. There were zero scored interventions
in the 2.5–3 and 3+ bins. The 3,000 directed-edge rows, event counts,
and two historical subperiod coefficients are stored in
`backtesting/origin01/results/edge_summary.csv`. Large individual
coefficients with small event counts are diagnostic only.

### Negative controls and decision

| Control | Total ratio | Active cells | Interpretation |
| --- | ---: | ---: | --- |
| Time-shuffled source dates | 1.000000 | 0 | Degenerate: one shuffled event produced no eligible intervention, so it cannot establish separation. |
| Peer source-name permutation | 1.000004 | 15 | No comparable improvement. |
| Future-row mutation | Passed | — | Synthetic test leaves origin-t signal and forecast identical. |

The minimum active-cell criterion of 0.98 was missed, and the result
depends entirely on one source shock at one grid origin. We therefore
record `READY_FOR_ORIGIN_02 = INCONCLUSIVE` and
`READY_FOR_ONE_SHOT_SUBMISSION = NO`. The fixed 21-business-day
grid gives insufficient shock-event coverage in 2024 to answer the
predictive question decisively. The negligible observed improvement
is not evidence for a usable price-only propagation alpha.

This historical evaluation uses revised public prefixes and an
origin-specific no-text V5.1 ablation. It is not an official or
point-in-time competition score. Private per-origin outcomes remain
outside Git; the public manifest holds only their hash, row count,
and date coverage.
