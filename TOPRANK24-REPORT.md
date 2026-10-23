## Executive summary (read this first)
EXPLORATORY_GAIN_ONLY. One nonlinear whole-path forest was actually trained and evaluated. Goal0.5-0.7 NOT ACHIEVED. No replacement for frozen FF03, no new Docker build.

## What changed
Separate research source only. ExtraTrees256/minleaf64/maxfeatures0.7 learns state partitions from standardized whole four-business-day paths and final squared moves. A tree and leaf member are sampled, preserving the entire historical asset/horizon path; origin volatility and anchor map it to today's units. Fixed recipe, seed17 for1000 joint draws. No post-result parameter changes, score-based routing or favorable subset selection. This shares empirical path resampling ideas with FF03 but adds supervised state partitioning; it is not new external predictive information.

## Actual evidence
Training uses pre2024 data only: EM3597 origins2009-03-27..2023-12-18; G104627 origins2005-01-03..2023-12-18. Final target2023-12-22. Exact business-day target availability required. Gaps are not filled; feature windows count observed rows. Training forests include historical target paths, so binary remains outside public repository; reproducible source, recipe and hashes are saved. No2025 labels reach training or prediction.

100/100 input forecasts succeeded with finite complete1000-draw arrays, each repeated exactly. Four incomplete label grids excluded equally for both models, leaving96cards/48origins/8assets. Existing exact FF03 Docker outputs reused with file receipt hashes verified. Input bytes verified against frozen manifests. Postasof extreme row perturbation invariant on one G10 unit; post2023 training inputs rejected. These are host research tests, NOT official submission/Docker gates.

|Full cohort metric|FF03|Forest|
|---|---:|---:|
|Normalized composite|0.9418927387445168|0.9366880405931365|
|Normalized marginal|0.9304027015120374|0.9236094031278252|
|Normalized joint|0.9519596758097967|0.9515310546989107|
|Normalized tail|0.9555174262277956|0.947120113097753|

Absolute improvement0.00520469815138036; relative0.55257864694%. EM gain0.00467464556, G10gain0.00573475074. Four-origin circular block diagnostic95% interval[-0.01293635788,0.02680333861],2000replicates. Missing-label origins compress calendar; not a formal independent significance guarantee. Remove best origin gain0.001904548. Worst card deterioration0.166876732. Q1gain0.016216745,Q2gain0.038365901,Q3gain-0.022131463,Q4gain-0.008664369. Both later quarters deteriorate. Removing best quarter and asset/horizon diagnostics saved in falsification.json. Marginal/joint/tail aggregate improve slightly, but EM joint and G10tail worsen. This is not robust proof of predictive alpha.

## Interpretation and limits
2025 current-vintage ECB cohort already exposed through previous research, not independent OOS. PIT_AUTHENTICITY_LIMITED. Equal weighting and official loss code unchanged; M0 scales use previously validated published-formula reconstruction, not authenticated sealed Final scoring. Official source3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56,common03c50a0036aaf72675d353aef4c7c01ca86d1fcf. No new rules check or claim about current rankings. No extrapolation to Final score. Goal0.7 requires about25.7% improvement from this FF03 baseline, far beyond measured0.55%. Failure to reach target is not proof no better model can exist.

No UST/monthly/text adapter, official22-card validation, Docker or independent runner tests for this rejected research candidate. No inference of submission readiness. No automatic replacement after a small exposed gain.

## Preservation and next action
FF03 safety ref remains71c6ab1aa349a3cea01ca61e2b1a5f999c6b3006; executablec5b8bbbd6227888b7a3dc0bbd05dc414d2d7c3f6. Image sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c; archive recorded sha256:df232487177cb56cb0ae945b2613fbbebbb24eff702f21712662e589d04f636c (not rehashed here). No main/protected branch/image/archive/tag operations. No keys, registry, ZIP, submission. Preserve experiment; retain FF03 for release. A0.5-0.7 method has NOT been demonstrated.
