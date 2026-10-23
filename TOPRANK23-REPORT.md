# TOPRANK23 result
## Executive summary (read this first)
NO_IMPROVEMENT. A separate learned distribution model was implemented, trained and evaluated. Retain original FF03 for submission. No claim of winning probability or Final score.

One pooled ridge conditional log-return mean and conditional variance model, trained 2005-2023 using 36,175 asset-day observations. Student-t(df7) joint paths use trailing120 correlation with20% identity shrinkage. Parameters frozen before outcomes; no tuning or second candidate. Fixed seed17,1000 complete joint paths,1-4 business-day horizons. No FF03 draws used in candidate construction. Direct model has no text, monthly or UST integration and is not a deployable submission.

2025 exposed/current-vintage ECB data:100 forecasts,96 complete cards/48 origins,8 assets. Four incomplete exact label grids excluded equally, never imputed. Existing FF03 Docker forecasts reused with receipt hashes verified; own input bytes checked. FF03 score reproduced exactly. No independent OOS or authenticated vintage claim. Full-precision results and per-card component/subset scores saved; no target values exported.

|Measure|FF03|New candidate|
|---|---:|---:|
|Normalized composite|0.9418927387445168|0.9430214306043458|
|Normalized marginal|0.9304027015120374|0.9240281288454657|
|Normalized joint|0.9519596758097967|0.9754349826256927|
|Normalized tail|0.9555174262277956|0.9418843569695255|

Improvement=-0.001128691859829 (0.120% deterioration). Four-origin circular block diagnostic95% interval[-0.0235102,0.0249590],2000 replicates. Origins with missing labels compress the calendar; this diagnostic is not a formal independent significance claim. Removing best origin gives-0.00687194. Worst card deterioration0.3242543. Both EM and G10 aggregate worse. Quarters2/4 improve;1/3 deteriorate. Joint damage offsets marginal/tail improvement. No threshold achievement and no promotion.

Deterministic finite complete arrays:100/100 repeated. Post-asof extreme row perturbation leaves output unchanged on one G10 unit. Training cutoff<=2023-12-29, target shift drops terminal unlabeled observation. Training/forecast Python3.12.14 numpy2.3.5 pandas2.2.3; scorer Python3.13.16 with common2.6.1, official source3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56 and common03c50a0036aaf72675d353aef4c7c01ca86d1fcf. Published M0 formula reconstruction reused; not sealed evaluator identity. No official CLI or Docker gate claimed.

FF03 safety remote remains71c6ab1aa349a3cea01ca61e2b1a5f999c6b3006; executablec5b8bbbd6227888b7a3dc0bbd05dc414d2d7c3f6. Original image sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c. Original archive expected sha256:df232487177cb56cb0ae945b2613fbbebbb24eff702f21712662e589d04f636c (identity reused, not rehashed this experiment). No protected branch/image/archive modifications, tags, registry, keys, ZIP or submission operations.

NEXT ACTION: retain FF03 and proceed with its existing release preparation separately. No new model replacement. Winning competitiveness remains UNKNOWN without independent comparative leaderboard evidence.
