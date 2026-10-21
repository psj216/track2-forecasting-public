## Executive summary (read this first)

Classification: **FF03_RETAINED_WITH_GAPS**. Both original V5.1 and the exact restored FF03 image passed all 22 official short-horizon practice cards and have identical paired output bytes and raw scores. No contract repair or forecast tuning was required. A shared numerical portability risk was discovered and preserved; macro and deployment gaps remain.

## Source and execution checkpoints

- Branch: `track2/final-fit-04-official-practice-replay`
- Parent: `71c6ab1aa349a3cea01ca61e2b1a5f999c6b3006`
- PRE: `62b289aa4b90bb398a68388aa528fa3bc95aee4f`
- INVENTORY / main executable: `e774e9bdea9a689995614a063efddce894e7b054`
- DOCKER checkpoint: `9a3eaf17ecce98cf5ea16dd579793cd45ae409b9`
- SCORE checkpoint: `0d74f30fbaef4b9d1553964e0bc77cc4faf7399d`
- Portability RED / executable: `9d7b2f29d62db94def796fd51cef12d52e1c1986`
- RESULT: this report’s Git commit; exact remote-verified SHA is returned with delivery. A file cannot name its own containing commit without a later checkpoint.

Official practice release `0ddb8896a942b9d44c64927f74755e7012c3e5f9`; current Track source `3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56`; toolkit v2.6.1/common `03c50a0036aaf72675d353aef4c7c01ca86d1fcf`, scorer3.1.0, contracts1.1.0, interface2.0. Cards/answers/scorer unchanged between release and current source. Newer documentation clarifies Final confidence-interval grouping. Final allows two uploads on different UTC days, later replaces earlier; deadline 2026-10-26 20:59 KST.

## Actual completion table

Every row: original Docker PASS, FF03 Docker PASS, all four official gates PASS, raw score paired difference zero, all three output files byte-identical. Inputs were unchanged; answers were mounted only in separate score processes.

| Card | Family | Assets | Horizons | Original | FF03 | Daily identity |
|---|---|---|---|---|---|---|
| t2-F1-curve-ust1y-001-ps1 | T2-F1 | UST_1Y | 2,3 | PASS | PASS | EXACT |
| t2-F1-curve-ust3m-002-ps1 | T2-F1 | UST_3M | 2,3 | PASS | PASS | EXACT |
| t2-F1-fx-eur-020-ps1 | T2-F1 | EUR | 1,4 | PASS | PASS | EXACT |
| t2-F1-fx-inr-010-ps1 | T2-F1 | INR | 1,4 | PASS | PASS | EXACT |
| t2-F1-fx-krw-011-ps1 | T2-F1 | KRW | 1,4 | PASS | PASS | EXACT |
| t2-F1-fx-zar-009-ps1 | T2-F1 | ZAR | 1,2 | PASS | PASS | EXACT |
| t2-F2-curve-ust1y-003-ps1 | T2-F2 | UST_1Y | 3,4 | PASS | PASS | EXACT |
| t2-F2-curve-ust6m-004-ps1 | T2-F2 | UST_6M | 1,4 | PASS | PASS | EXACT |
| t2-F2-fx-brl-012-ps1 | T2-F2 | BRL | 3,4 | PASS | PASS | EXACT |
| t2-F2-fx-eur-021-ps1 | T2-F2 | EUR | 2,4 | PASS | PASS | EXACT |
| t2-F2-fx-krw-015-ps1 | T2-F2 | KRW | 1,3 | PASS | PASS | EXACT |
| t2-F2-fx-mxn-013-ps1 | T2-F2 | MXN | 1,4 | PASS | PASS | EXACT |
| t2-F2-fx-zar-014-ps1 | T2-F2 | ZAR | 1,4 | PASS | PASS | EXACT |
| t2-F3-curve-ust3m-ust6m-ust1y-006-ps1 | T2-F3 | UST_3M,UST_6M,UST_1Y | 3 | PASS | PASS | EXACT |
| t2-F3-curve-ust3m-ust6m-ust1y-ust2y-005-ps1 | T2-F3 | UST_3M,UST_6M,UST_1Y,UST_2Y | 3 | PASS | PASS | EXACT |
| t2-F3-fx-eur-jpy-chf-022-ps1 | T2-F3 | EUR,JPY,CHF | 3 | PASS | PASS | EXACT |
| t2-F3-fx-krw-inr-zar-017-ps1 | T2-F3 | KRW,INR,ZAR | 4 | PASS | PASS | EXACT |
| t2-F3-fx-mxn-brl-zar-016-ps1 | T2-F3 | MXN,BRL,ZAR | 2,4 | PASS | PASS | EXACT |
| t2-F4-curve-ust3m-008-ps1 | T2-F4 | UST_3M | 1,3 | PASS | PASS | EXACT |
| t2-F4-curve-ust6m-007-ps1 | T2-F4 | UST_6M | 1,2 | PASS | PASS | EXACT |
| t2-F4-fx-brl-019-ps1 | T2-F4 | BRL | 3,4 | PASS | PASS | EXACT |
| t2-F4-fx-mxn-018-ps1 | T2-F4 | MXN | 1,4 | PASS | PASS | EXACT |

## Scoring and exposure

The 22 cards contain 53 target cells, cover historical as-ofs 2009-08-10 to 2022-12-12, and use 1,000 draws per cell with seed17. There are no official single-cell cards in this set. Family counts are F1=6, F2=7, F3=5, F4=4. Eight Treasury-bill, eleven ECB EM and three H.10 G10 cards all pass. Failed/unscored cards: 0.

The canonical official scorer was called 44 times with published answers, giving `raw_unrankable` and `rankable=false`. Every per-card CRPS, variogram, tail pinball and raw composite is exactly equal between candidates. `FINALFIT04-SCORE-COMPARISON.md` provides all values. There is no cross-card raw average, normalized leaderboard claim or comparison to Development0.9541. No authenticated M0 scale bundle was supplied; reconstructing the published M0 generator was not undertaken. This is EXPOSED_PRACTICE_DIAGNOSTIC, not independent OOS.

## Runtime and regression

57 actual Docker forecast processes exited zero: 44 main, six same-runner FF03 repeats, two resource probes and five portability diagnostic forecasts. These process counts are not independent performance observations. The 44 main forecasts and 44 separate official scoring calls pass. All six locked same-runner FF03 repeats match exact bytes. New host verification ran 37 unchanged current official tail/monthly pytest cases, all passed, zero skips. New FF04 code passes syntax and Ruff E/F/I at0.4.7. Prior FF03’s120 checks are reused, not counted as new execution. No original assertions were edited.

Maximum main forecast wall time was2.241566 seconds including Docker startup; maximum output size35907bytes. Representative forecast-child maxrss was199184KiB original /199692KiB FF03, under2CPU/4GiB limits. These are child RSS observations, not cgroup peak or all-card peak. Entire sealed Final batch runtime remains UNKNOWN.

## Preserved portability RED

The resource runner produced different daily parquet/rationale for one representative card compared with the main runner, for both images. Main-versus-resource difference:13/2000values, maximum0.06308603200308704percentagepoints. One fixed diagnostic reproduced a CPU-feature-sensitive matched-start ordering: same456pool members,39positions differ;8/2000values change. Original and FF03 remain equal within every controlled environment. Same-runner normal original repeat also matches the main batch. The exact earlier resource-run CPU cause is not fully established. See FINALFIT04-PORTABILITY-FORENSICS.md. This is why cross-runner byte stability is not passed and no new forecast implementation is silently introduced.

## Remaining release risks

- MACRO_FINAL_SCHEMA_UNVERIFIED: no new macro practice; GDP/claims and new release vintages unknown. FF03’s existing explicit monthly helper and image are unchanged.
- Ranked G10 uses ECB-derived inputs while these three G10 practice cards use H.10; unseen bytes/contracts remain unexecuted.
- Inherited whole-repository CI remains red:2288lint errors and61collection errors from missing sklearn/requests/bs4; same counts as parent. Scoped image success does not make whole-repository CI pass.
- FF03 is an authenticated local image archive/config ID, not a published registry manifest. No registry push, packing, secret use or submission occurred.
- Public practice is exposed; independent alpha and unseen Final forecast quality remain UNKNOWN.

## Decision and next action

Retain FF03 as preferred technical direction with the above gaps, and preserve the original safe image/Windows ZIP. There is no FF04 runtime candidate because no new-card contract repair was necessary. Further numerical hardening would change legacy draw ordering and needs a separate candidate with explicit regression evidence. Deployment needs a fresh immutable public image reference, anonymous-pull verification and official secret-safe descriptor/claim checks; these remain unperformed as instructed. Full decision and gates are in FINALFIT04-CANDIDATE-DECISION.md and FINALFIT04-RELEASE-GATE.json.
