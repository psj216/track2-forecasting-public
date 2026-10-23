## Executive summary (read this first)
REGRESSION. A real independent conditional UST forecasting engine was implemented, trained, container-executed and evaluated. It failed to improve FF03. Preserve FF03 for submission.

Training: one official9-tenor history2000-2022 plus nonoverlapping current-vintage Treasury2024-2026for evaluation inputs.2023not available in this acquisition; no fill. Actual train origins4545:4138fit(2001-2020),407inner validation(2021-2022). Four-business-day target purge at split boundary. Final refit4545; last origin2022-12-06,last target2022-12-12. Nominal model guard2023-12-31is conservative eligibility, not a claim of2023training observations. Full125features,25policy-related.198total policy docs;160active by historical panel end,138by2020end. Future docs filtered at eachorigin. Original vintage/source-selection risk remains.

Model: direct36-cell conditional mean+risk+joint Student-t distribution. Curve par-forward proxies are not futures/OIS expected policy paths. Lexical policy changes are not market-consensus surprises. Policy relationships learned, not fixed hawkish/dovish yield offsets. Schedule availability starts2024and cannot estimate historical schedule effect. No verified genuine policy-surprise alpha claim.

Evaluation:91fixed weekly origins requested;10missing origin observations;81original FF03/full/ablation container executions;7incomplete target grids excluded equally;74scored.9tenors,1..4BD,1000draws,seed17. Official M0 reference uses500draw convention. Price panel/text bytes identical;78metadata hash mismatches from refetchedHTML IDs were recovered to exact runner bytes before scoring. No assertions weakened. No forecasts rerun. Current-vintage2025/26evaluation is exploratory; prior exposure and revision status prevent independent OOS claims. Official loss imported, M0 expected-error scale from previously verified published-formula reconstruction. No authenticated Final score.

|Normalized metric|FF03|ALPHA23|Policy-free|M0|
|---|---:|---:|---:|---:|
|Composite|0.907399286943|0.957133510806|0.939654463056|0.914299245262|
|Marginal|0.864351470184|0.889960060387|0.881179275919|0.875642827406|
|Joint|0.928416058347|1.004897919144|0.986245507819|0.940924337213|
|Tail|0.983493671737|1.053420524347|1.015955863755|0.971002651976|

Overall loss worsens5.4810%. Policy addition worsens0.017479047750. Full beats FF03 only in3Mtenor subgroup; all horizon subgroups worse.2025and2026both worse. Direction0.505255vsFF030.475225,but centerRMSE0.059005vs0.057783. A direction hit does not establish distribution quality. All overall threshold goals missed.

Actual Docker research:Actions40008576484 all4chunksPASS. ArchiveSHA256df232487177cb56cb0ae945b2613fbbebbb24eff702f21712662e589d04f636c checked before restore. Original image sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c. New source/weights mounted read-only into identical original runtime to compare; no claim of a new image. Nonroot1000,networknone,readonlyroot/input,2CPU/4GB. No peakRSS measurement. No separate candidate release image,G0-G3/full22/monthly/concurrent release checks because performance gate failed. Research concurrent jobs are not proof of complete Final concurrency readiness.

PREa85ed6b852f72e29bac1527b42a2fb996d6235fa. SOURCEc190da62afe6bc1489cdece3229a7422c30ef9d2. Evaluator lock4e5eb664403724290a2013ab3d9995c7be389421. Official scoring3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56,common03c50a0036aaf72675d353aef4c7c01ca86d1fcf. Repository-wide CI is separate and not claimed green; PRE already failed CI. No broad-CI cleanup attempted.

FF03 safety71c6ab1aa349a3cea01ca61e2b1a5f999c6b3006; executablec5b8bbbd6227888b7a3dc0bbd05dc414d2d7c3f6. Protected branches/images/tags unchanged. No Registry, keys,ZIP,CodaBench. NEXT ACTION: stop ALPHA23promotion; resume existing FF03release preparation separately. No automatic deployment or new follow-on research.

