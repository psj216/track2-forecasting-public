## Executive summary (read this first)

This study asks how much of V5.1's oracle center error is predictable from
observable market history. It creates no forecast architecture or submission.
The machine-readable protocol is `backtesting/location01/frozen_protocol.json`.
The complete public feature schema and private-ledger hashes are frozen before
opening final cross-fitted CRPS or card-transfer scores.

For example, a baseline ratio of 1, perfect location ratio of .40 and predicted
location ratio of .94 imply 10% oracle-headroom capture. Negative capture is
retained. A center shift adds one identical value to all baseline draws.

All 25 original daily assets remain. The public prefixes have unequal end dates.
Every eligible mature asset/horizon cell enters; there is no balanced-panel or
favorable-asset restriction. The 2001-2009 ledger portion supplies training.
The exact same 2010-2024 mature cells supply baseline, perfect oracle and
cross-fitted candidate metrics. No independent-OOS claim is made.

Target endpoint and return-sum acceptance call the original V13-R2 helper.
No future rows enter features, sigma or V5.1 inputs. Numeric missing values
are imputed from training only. Categorical vocabularies are deterministic.
The full 189-business-day origin exclusion plus maturity check applies to
outer fitting, inner validation and matched card-as-of fitting.

Old 24-card examples precede the first 2009 outer model. For safe transfer,
freeze all M1-M5 continuous-ledger models at each card's historical cutoff,
using only earlier mature labels, before any card score is opened. This is
an explicit matched-asof implementation of transfer, not card-label refitting.
Card transfer uses the original CEILING V5.1 text-conditioned baseline arrays,
while continuous training is the explicitly labeled no-text ablation.

Three supervised negative controls are fit with the same alpha protocol.
Inner-control permutations stay within that inner training split. Complete
calendar years are bootstrap units, not cells. The bootstrap compares each
control's best fixed channel sequence conservatively with the Ridge best.

Ridge and fixed HGB are reported separately. HGB has no random early-stopping
validation. No result-dependent feature selection, scale, tail, joint model,
copula modification or one-shot submission is authorized by this study.
