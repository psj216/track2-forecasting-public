## Executive summary (read this first)

The organizers published 22 short-horizon cards and their answers. Final accepts two uploads on different UTC dates; the later upload replaces the first. This task makes no upload or registry push.

Verified on 2026-10-21 from actual GitHub sources:

- Official Track HEAD: `3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56`.
- Practice release: `0ddb8896a942b9d44c64927f74755e7012c3e5f9`. The units, answer files and scorer are unchanged between that commit and current HEAD. The newer commit changes only confidence-interval documentation and its changelog.
- Official announcement: https://github.com/Agenthon-2026/track2-forecasting-public/issues/4#issuecomment-6252030411
- Shared common HEAD/version: `03c50a0036aaf72675d353aef4c7c01ca86d1fcf`, v2.6.1; contracts 1.1.0, interface 2.0; Track scorer 3.1.0.
- Deadline: 2026-10-26 11:59 UTC / 20:59 KST. Ranked as-of October 26, market targets October 27–30, one to four business days. Monthly official statistics are additional targets, with their own period and vintage contracts.
- Two uploads maximum, at most one per UTC day; later replaces earlier. Each has an unranked sealed-card check. This is not the former one-upload rule.
- Linux/amd64, interface 2.0, no inherited or declared VOLUME, public anonymous pull, 1,800 seconds per unit and 43,200 seconds for ingestion.
- Ranked Final confidence intervals group by pre-fixed event/card kind and resample cards within those groups. Development grouping remains by as-of. This documentation correction does not change per-card scoring.

## Data and scoring

Practice has eight Treasury bill cards, eleven ECB-derived EM currency cards and three historical H.10 G10 cards. Each authored card retains its own assets, horizon grid, units, text and draw floor. EM is already converted by the organizers to currency units per USD. No new conversion is applied to those input values. Ranked G10 uses ECB-derived crosses; the three historical practice cards retain H.10. Passing these cards does not prove every unseen Final panel identifier.

`scoring/scoring.py score --card ... --forecast ... --realized ...` calls the canonical Track verifier and toolkit metrics. With no organizer reference scales it reports `raw_unrankable`, `rankable=false`. Raw composite values have card-specific units; no cross-card raw composite average or comparison to historical Development 0.9541 is admissible. M0's procedure and expected-error formulas are public in `docs/M0-BASELINE.md`, but the generator and authenticated scale bundles are not shipped. This task reports official raw per-card scores and paired equality, not a claimed official normalized leaderboard score.

## Data firewall

Forecast Docker mounts only one unmodified official unit at `/input:ro` and its empty output at `/output:rw`; root is read-only, network is none, process is non-root. There is no repository root, answer directory or audit Python overlay mounted during forecasting. Container inspect receipts preserve the actual mounts and network configuration. The scoring container is a distinct process, created after forecasts and output hashes are complete; only that process sees official answers. Neither image is rebuilt with answers or card-specific predictions.

## Monthly and macro boundary

The current official monthly helper Git blob is `04650003bac311fd5c0cee7cb2c8d17484ddcbe6`, unchanged from FF03. The published monthly document distinguishes observation month, publication date, final available anchor, authored horizon key and release vintage. The 22 new cards are daily market cards, so their replay does not validate GDP, jobless claims or sealed monthly schemas. Existing FF03 monthly receipts remain historical evidence, not newly executed tests.
