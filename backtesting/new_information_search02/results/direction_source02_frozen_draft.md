## Executive summary (read this first)

CONDITIONAL FROZEN DRAFT ONLY — NOT_EXECUTED. Next: PERSISTENT-DIRECTION-STATE-02. Source focus: FOMC_SEP_POLICY_PATH. Selected source-audit PRIMARY: FOMC_SEP_POLICY_PATH. The draft cannot become a candidate until every source/PIT/access/rights gate passes and a new remote PRE is verified.

Exact source and fields: One source variable: released NCY-CY policy median spread at the release calendar year. Keep this state fixed until next original publication; age cap90BD. No new topics, magnitude target or calendar rollover relabeling.

Timing/roll rule: No contracts or expiry. Publication-date EOD activation, explicit target years, corrections inactive until original values recovered.

Asset universe: UST_2Y and UST_5Y only. Horizons5/21/63/126/189 in existing weekday semantics. SEP source age <=90BD, fixed before the next labels; no other source or contract family is included. Originals must span2016-2024; no current revised-history substitution. Bundling requires written lawful offline and contest-use rights.

Target: sign(truth - V5.1 median), binary positive versus negative; exact zeros excluded from classifier training only and retained as ties in reporting. Targets are constructed only after the next PRE. No standardized magnitude prediction. Fixed original V5.1 draws and SD remain unchanged.

One model: pooled L2 logistic regression, C=1.0, intercept, no class weights, no tuning, train-only numerical standardization. Source variables above plus fixed asset indicator and log(horizon) structural covariates. Threshold0.50; exact probability tie maps zero shift. No source-specific model selection or horizon subsets.

Development2016-2019; expanding forward folds2020/2021/2022/2023/2024. At each fold, only training targets matured by the first fold test cutoff. Apply exact horizon-specific maturity/purge, up to189BD, with the competition2024-12-18 target cutoff. No train/test overlapping future labels. These years remain exposed research, not independent OOS.

Primary translation: 0.05 * sign(probability-0.50) * frozen V5.1 SD. The cap is an independently declared one-twentieth-SD per-cell risk budget, not selected from SPD score curves. Never compare amplitudes to pick a winner. Preserve all draw geometry, ranks, scale and tails.

Timing controls: fixed5BD delayed mapping; fixed21BD stale mapping; previous source-state sign persistence; 2,000 date/block permutations with seed31802; matched random sign; fixed21BD own-price direction comparator and same logistic on the predeclared lagged price features. Every control uses only source states available before its origin and the same purged folds. No symmetric/future date remapping.

Success gate: primary marginal CRPS ratio <=0.98, positive improvement in at least4/5 evaluable folds, release/source-week and year block-bootstrap evidence supporting benefit, no dominant single year/update. Correct contemporary mapping must beat both fixed delayed/stale controls and the price-only/persistence comparators on the same ledger; a timing null equal or better makes verdictNO regardless of baseline gain. Adequate eligible unique updates must be checked before fit; daily origins do not create independent evidence.5,000 source-week/release and year bootstrap replicates. No production submission from exposed data.

Independent validation: NOT_AVAILABLE. Any future prospective universe requires separate preregistration before outcomes; do not relabel old cards or already exposed targets as clean. This draft does not execute data acquisition, forecasting fit, target-label construction or CRPS evaluation.
