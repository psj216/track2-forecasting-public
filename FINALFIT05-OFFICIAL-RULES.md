## Executive summary (read this first)

Official repository HEAD observed on 2026-10-22 remains 3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56. v2.6.1 toolkit resolves to 03c50a0036aaf72675d353aef4c7c01ca86d1fcf. The ranked announcement is issue 4 comment 6301021850, created/updated 2026-10-20T20:41:50Z.

## Final contract

Deadline: 2026-10-26 11:59 UTC = 20:59 KST. At most two uploads, on different UTC dates. Later upload replaces earlier. Each upload gets an unranked sealed check; ranked runs occur after closing. As-of 2026-10-26; at most 48 cards in three seeded balanced sets of at most 16. Same image per entry. Each run: 43,200 seconds including image pull. Each card: 1,800 seconds. Runs may be sequential or concurrent. Missed/unanswered card counts 8.0. Keep anonymous digest pull available through results publication. No separate participant verification submission.

UST/FX forecast 1-4 business days, targets 27-30 October. UST uses Treasury par yields; Final FX uses ECB reference-rate USD crosses, including G10. EM currency per USD. Release cards forecast October observation figures first published 27-30 October. Unreleased by 30 October: dropped. Announcement names inflation, economic sentiment, unemployment as examples, not executable target IDs or complete schemas.

## Numerical verification

SUBMISSION_CLI.md lines 193-194 says T2/T3/T4 statistical bootstrap confidence interval overlap on rerun. Lines 263-266 describe fresh seeds/resamples. Universal cross-CPU parquet byte identity is not stated as the T2 criterion. This is not a guarantee the organizer accepts arbitrary distribution changes.

## Monthly periods and gaps

Current MONTHLY-HORIZONS.md and horizons.py are authoritative over stale starter-pack prose that calls horizons panel rows. Preserve authored business-day keys. Monthly transitions come from explicit observation-period mapping and each asset's last valid pre-asof observation. Target dates denote observation months, not release dates. Vintage convention remains separately authored. Missing/conflicting mappings refuse. A public helper is not proof that all sealed cards carry required metadata.

Ranked card IDs/metadata and new release templates were not found in this official tree/announcement. Published monthly CPI/NFP are historical Practice scope, not all-Final compatibility evidence. Ranked ECB G10 actual schema remains unverified; H.10 G10 Practice is a different fixing source.

Sources: https://github.com/Agenthon-2026/track2-forecasting-public/tree/3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56 ; https://github.com/Agenthon-2026/track2-forecasting-public/issues/4#issuecomment-6301021850 ; common v2.6.1 SUBMISSION-DESCRIPTOR.md, TEAM-CLAIM.md, schemas/submission.schema.json, contracts/descriptor.py, team_claim.py. File hashes: backtesting/finalfit05/results/official-files.json.
