# FINAL-ALPHA-21 — PRE-FROZEN PREQUENTIAL RISK CALIBRATION

## Executive summary
One bounded candidate mechanism only: causally backtested, per-card adaptive spread calibration centered on the **FF03 conditional forecast center**, never on the last observed market level. This is a research specification, not an implemented model or proven performance gain. The original FF03 safety image/branch, MOONSHOT20, main, registry tags and submission artifacts must remain unchanged.

## Provenance
Parent: 79983b1343e98088c51889600503329edf757557 (FINAL-ALPHA-19 result, research only).
Safe FF03 source: c5b8bbbd6227888b7a3dc0bbd05dc414d2d7c3f6.
Safe FF03 local image: sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c.
Candidate branch: track2/final-alpha-21-prequential-risk-calibration.

## Hypothesis
FF03 numeric-only daily forecasts may have transient predictable dispersion mismatch, detectable by performance of as-of-lagged pseudo-forecasts on past observations within each *input panel*. If the mismatch is robust on a held-back pre-as-of slice, modest spread correction can improve proper-score components without destroying forecast center or dependence.

## Inference-time mechanism
Eligibility: daily level target, complete continuous dated history with 24 matured pseudo-origin windows, maximum horizon <=4 business days, nonmissing labels prior to actual as-of, no active FF03 text adjustment, no transfer-gap condition, exact unit metadata, finite FF03 output. Otherwise return FF03 byte-identical. Monthly, nonlevel and unknown inputs always return FF03 unchanged.

Choose 24 nonoverlapping matured pseudo-origins, ordered chronologically and spaced at least 5 business days, selected by a deterministic as-of-only rule, no data after current as-of. At each pseudo-origin, truncate ALL data including future text, numeric observations, revision-sensitive metadata and target labels before running the frozen FF03 numeric prediction, and score it only after forecast completes using outcomes already matured before the current as-of. Historical publication vintage authenticity must be evaluated; no future final answers.

For each complete original joint draw X and cell, let mu be the sample mean of that cell's original frozen FF03 draws. Predeclared scale choices are {0.85, 1.00, 1.15}; produce X_s = mu + s*(X-mu), using **one common scale for the entire joint grid**. Do not move mu toward observed anchor. Keep all draw IDs, cell order and horizons. Text-active forecasts bypass.

Training first 16 pseudo-origins: choose scale minimizing mean per-origin *official M0-normalized composite* if independently reproduced M0 scale and grader are available; otherwise no adaptation. Ties prefer 1.00. Latest 8 pseudo-origins are a strict gate, not for refitting. Deploy selected non-identity scale at this card only if: (a) fit mean gain >=0.010 absolute normalized loss, (b) validation mean gain >=0.005, (c) worst validation per-origin loss increase <=0.05 absolute, (d) no mean CRPS/tail damage exceeding 1% on validation, and (e) no missing/invalid grids. Otherwise fall back to FF03 exactly. Never relax these after results. These thresholds and scales are fixed before any new evaluation.

A prequential diagnostic is not independent evidence of alpha or of actual availability of original historical vintages. Pseudo-origin scores must not enter the final 2025 evaluation except through the frozen inference algorithm. Do not precompute favorable per-card gates against published truth. Adapter output folder must contain only required forecast files.

## Research protocol
Review historical family-calibration, V8/V9, ALPHA-19 and FF05 reports before work; stop if equivalent already fully failed. Build one reusable adapter, not family-specific fitted coefficients. Verify cutoff firewall by perturbing or removing observations strictly after pseudo-origin and checking output invariance. Verify that all reference values used for selection mature BEFORE current as-of. Reconstruct exact M0 normalization without hidden scales; if formula reproduction not verifiable, label BLOCKED, no official score claim.

Evaluate precommitted cohorts chronologically and report (a) official exposed 22 practice (diagnostics only), (b) inherited 2025 ECB research 96 (PIT_AUTHENTICITY_LIMITED and already exposed), and (c) genuine untouched forward periods only when provenance actually verifies them. Do not use any evaluation cohort to alter gates/thresholds. Include per-origin paired loss, year/quarter/asset, component tradeoffs, uncertainty intervals from dependence-aware origins, leave-largest-origin-out and worst-card harm. No parameter sweep or second candidate.

Safety: at least one complete Daily and Monthly Docker gate before promotion, then all relevant 22-card official practice contracts for new runtime; separate candidate image only if promotion passes; unknown final Macro/ranked ECB metadata remain unknown. Retain original FF03, do not alter existing tags.

## Decision and stop
GO only with positive robust improvement on independently defensible holdout plus operational gate. If evaluation data are exposed/PIT-limited, classification EXPLORATORY_GAIN_ONLY at best. If effects are flat, weak or unsafe, NO_GO and close research. Never assert 0.7–0.6 without a genuinely measured, comparable official normalized evaluation. Finish without blocking preparation of original FF03 Registry/public digest/ZIP submission. No Team Key, Registry push, packing or CodaBench submission in this research task.

## Milestones
PRE -> one adapter and test -> temporal firewall -> one paired evaluation -> robustness/decision -> optional separate Docker -> RESULT. Record exact parent, source, artifact hashes and remote RESULT SHA. One decisive review; avoid repetitive checks.
