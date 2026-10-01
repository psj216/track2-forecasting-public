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
per-origin scores remain outside Git. Results below are pending the verified
pre-final remote SHA.
