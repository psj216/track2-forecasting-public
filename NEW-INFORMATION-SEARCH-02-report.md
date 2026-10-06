## Executive summary (read this first)

Completed source-discovery audit. **NEWINFO02_RESULT = PERSISTENT_REGIME_PROXY**. No future UST labels, forecasting fit, candidate CRPS or official submission was used in this audit.

Selected audit PRIMARY source: `FOMC_SEP_POLICY_PATH`. Exactly one audit/acquisition focus: `FOMC_SEP_POLICY_PATH`. Next action: `PERSISTENT-DIRECTION-STATE-02`. The selected audit source still requires a complete source-readiness gate before any forecasting experiment.

Original research parent: `16ef4d87f15151796b072e2a6f658ec076171bda`. Resumed checkpoint: `5ff1ba0664c159bd06705c7cbfbeadb9bf8769fe`. PRE: `8f4ae57eebb33b6d5a60f6fd0c351df29b5f65ea`.

The prior parser stop was operational, not scientific. The corrected implementation reused the saved downloads. The old stopped-execution artifact remains as recovery history. Source ranking was run only after the PRE commit was pushed and remotely verified. The original experiment_spec.json and catalog SPEC were preserved byte-for-byte.

The explanand is the exact frozen SPD prediction/sign state: 552 cells, 59 origins, 41 SPD releases, UST_2Y and UST_5Y, all five existing horizons. No realized Treasury outcome, center error, return, CRPS or oracle direction entered features or ranking.

## Quality shortlist

| Source | Family | PIT | Timing | Novelty | Lag5 persistence | Release-balanced SPD agreement / rank | Access | Score | Gates |
|---|---|---|---|---|---|---|---|---|---|
| FOMC_SEP_POLICY_PATH | C | B | LOW | MEDIUM | 0.9857 | 0.5756 / 0.5299 | ACCESSIBLE_PUBLIC | 16/20 | True |
| H41_RESERVES | E | B | MEDIUM | HIGH | 0.8046 | 0.4433 / -0.0372 | ACCESSIBLE_PUBLIC | 15/20 | False |
| NYFED_ONRRP | E | C | MEDIUM | MEDIUM | 0.7660 | 0.4023 / -0.3447 | ACCESSIBLE_WITH_LIMITATIONS | 11/20 | False |

A score is source quality, not forecasting performance. SPD alignment contributes at most 2/20. Missing state access receives no invented alignment or novelty benefit. Inclusion in the shortlist never overrides hard PIT, rights, history or novelty gates.

## Same/as-of frozen SPD alignment

| Source | Cells | Origins | SPD releases | Candidate states | Agreement | Balanced agreement | Weighted Spearman |
|---|---|---|---|---|---|---|---|
| FOMC_SEP_POLICY_PATH | 532 | 57 | 39 | 19 | 0.5756 | 0.5687 | 0.5299 |
| H41_RESERVES | 552 | 59 | 41 | 59 | 0.4433 | 0.4429 | -0.0372 |
| NYFED_ONRRP | 552 | 59 | 41 | 59 | 0.4023 | 0.4021 | -0.3447 |
| ATLANTA_MPT_SOFR | 162 | 20 | 15 | 20 | 0.9867 | 0.5000 | -0.3587 |

The 19 SEP candidate states are repeated across 57 origins and 39 SPD releases. Release-balanced metrics above weight SPD release IDs, not 532 independent observations. No significance or independent alpha claim follows.

Fixed 21BD price-state proxy: release-balanced agreement 0.5730, rank correlation 0.1470. The 5BD and 63BD comparisons are reported separately; no best lag was selected.

SEP sign agreement (57.56%) is almost the same as the fixed price comparator (57.30%), while its rank relation is stronger (0.530 versus 0.147). The source/price coverage differs slightly and the original full price cache is absent; no incremental forecasting superiority is established. MPT raw agreement (98.67%) is a majority-sign effect: balanced agreement 0.50 and negative rank relation -0.359 prevent an alignment pass.

These statistics describe agreement with the exposed SPD model, not agreement with future yields. PIT-C series are exploratory current-vintage diagnostics, not admissible primary evidence. All joins enforce availability <= the parent cutoff: previous weekday 16:00 America/New_York, with DST. Original dated releases activate conservatively at publication-date EOD; MPT at next-weekday EOD. No lead values or optimized lags were used.

## Source persistence and price redundancy

| Source | Observed days | Lag1 | Lag5 | Lag21 | Sign-run BD | Direction unchanged | Source-on-price R2 | Novelty |
|---|---|---|---|---|---|---|---|---|
| FOMC_SEP_POLICY_PATH | 2112 | 0.9970 | 0.9857 | 0.9401 | 352.0000 | 0.9981 | 0.7650 | MEDIUM |
| H41_RESERVES | 1310 | 0.9650 | 0.8046 | 0.2626 | 15.0575 | 0.9415 | 0.3645 | HIGH |
| NYFED_ONRRP | 2209 | 0.9089 | 0.7660 | 0.2719 | 4.3145 | 0.8081 | 0.4027 | MEDIUM |
| ATLANTA_MPT_SOFR | 436 | 0.9817 | 0.9233 | 0.6949 | 18.9565 | 0.9833 | 0.9485 | LOW |

Persistence measures describe source states only. Missing or inactive publication events interrupt daily expansion; unacquired weekly updates are never filled as unchanged. The half-life is an AR(1) descriptive proxy, not a causal decay estimate. NY Fed current-version metadata and MPT current-model history retain PIT-C tags.

The redundancy regression has the SOURCE state as its dependent variable, not any future target. It uses 14 lagged spot-yield level/change/curve features. It is a small-N in-sample descriptive projection, with 59 or fewer origins, and does not validate novel predictive information. The exact original price-state cache is unavailable; a strictly date-bounded official DGS proxy is used with a conservative next-weekday EOD availability assumption. Thus superiority to the complete original price representation is NOT_ESTABLISHED. Spot slopes and fitted spot forwards remain price-derived by construction. Distinct Fed Funds/OIS contract expectations could be novel, but that claim has not been empirically verified here.

## PIT, access and historical coverage

The selected SEP extraction spans 2016-09-21 through 2024-12-18. Six earlier original pages were not extracted by the frozen median-table parser and remain inactive; this is not proof that policy information was unavailable. A future complete source-readiness gate must resolve supported field semantics/originals before forecasting.

Parsed SEP rows: 33; H.4.1 rows: 294; eligible current-version RRP rows: 2476; MPT state rows: 436. Explicit parser/timing inactivations are recorded in source_dataset_manifest.json.

SEP originals are quarterly appropriate-policy projections, not daily market-implied probabilities. Release-year NCY minus CY remains fixed until the next eligible publication; no outcome-based direction flip or January target retuning is permitted. H.4.1 uses Wednesday reserve balances, not weekly averages. Corrections or known release/DDP timing ambiguities are inactive until field-specific original recovery. The H.4.1 archive universe is enumerated, but the downloaded source sample is not claimed to be a complete usable 2015-2024 field dataset.

CME ZQ monthly contracts encode calendar-month average effective Fed Funds rates via 100 minus settlement. No authenticated CME historical settlement access was present; the actual API probe returned 401. Original settlement timestamps, correction vintages, expiry/roll rules and written offline/contest-use rights are needed before a market-implied source can become primary. SOFR alone starts in 2018, so it cannot satisfy the required 2015/16 start without a separately justified source protocol. OIS/options vendor curves were not acquired; commercial existence is not access.

The Atlanta Fed MPT public file actually begins 2023-03-29 and lacks 2015-2022. It is a current model-produced history. Its embedded license permits personal and educational use only; no contest or offline redistribution authorization was inferred. Original post-2024 transport rows are quarantined in the private recovery and excluded from numeric construction.

CFTC report dates are not publication dates. The 2023 catch-up schedule makes generic Tuesday-plus-three-days activation unsafe. NY Fed dealer history explicitly may reflect later revisions. Historic RRP records carry lastUpdated later than observation dates; the audit uses conservative version availability and prevents a late old record from displacing a newer economic observation. Those restrictions reduce access to trustworthy PIT data; they are not evidence of absent alpha.

Provider links, per-document hashes, retrieval receipts, machine readability, authentication, rights and largest risks are recorded in the inventory and documentation manifest. Board/CFTC public-domain provisions and NY Fed attribution terms are source-specific; provider rights never imply automatic contest eligibility. Runtime network remains restricted, so any later eligible source must be lawfully bundled offline.

## Decision questions and next study

- Q1_beats_original_price_state: NOT_ESTABLISHED: no exact prior market cache and no full original price-model replication
- Q2_resolves_timing: NOT_ESTABLISHED unless selected source has higher frequency; daily derivatives require license
- Q3_persistence: Source-state autocorrelation is descriptive; does not establish that SPD timing generated alpha
- Q4_real_update_vs_regime: No identified source has yet passed a future timing-specific forecast test
- Q5_historical_asof_acquisition: Original SEP/H41 samples available; licensed contract history not acquired
- Q6_new_information: Distinct policy-path contracts potentially novel, not empirically verified; spot-yield derivatives are price history

Selected source-audit PRIMARY count: 1. Single focus: FOMC_SEP_POLICY_PATH. No source is forced into primary merely to produce a winner. When every candidate fails the frozen substantive gates, the primary is null and a single acquisition target is selected instead. This preserves the original no-forced-winner specification.

SEP is quarterly and has fewer update events than the meeting-level SPD survey. It does not offer higher-frequency timing resolution. Its 21BD autocorrelation 0.940 and 99.81% unchanged-direction fraction make the delayed-SPD result compatible with a persistent policy state, but do not causally identify that state.

The conditional next-study draft is saved separately. It specifies one low-capacity directional model, lawful original SEP fields, explicit target-year semantics, chronological folds, a small fixed risk-budget shift and contemporaneous-versus-delayed/stale/persistence/price controls. It was not executed. A source readiness gate and another remote PRE are required before any future labels are constructed.

## Firewall, limitations and validation

Outcome-mutation tests add fake future return, truth, CRPS and oracle columns; rankings and selection remain bitwise identical. The frozen SPD hash is preserved. This proves pipeline input independence, not provider vintage immutability. All 2020-2024 UST targets and old cards are already exposed. INDEPENDENT_VALIDATION = NOT_AVAILABLE. No result here is independent OOS and nothing justifies official submission. Source selection against a previously exposed SPD direction can itself overfit its proxy state; prospective validation is still required.

No forecasting architecture was created, no SPD retraining occurred, no amplitude or directional threshold was optimized, and no new forecasting candidate or CRPS score was computed. Access failure is not a predictive rejection of the inaccessible information family.

## Verification

Tests, remote PRE verification, input hashes, final execution/Git audit and private recovery verification are recorded in the corresponding manifests and completion receipt. The immutable RESULT SHA is supplied in the external completion receipt to avoid a self-referential commit hash. Main remains protected.

Final required tests: research **31 passed**; affected **92 passed**; full repository **749 passed, 17 skipped**; common toolkit **250 passed**. Skips are existing private-input and external Docker/CodaBench prerequisites. All 806 PRE input hashes and 2220 protected prior-research file hashes were preserved. No completed source acquisition or source-analysis stage was restarted.
