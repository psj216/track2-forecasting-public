## Executive summary (read this first)

Current official Final rules and descriptor identifiers are verified. **The user-held ZIP and actual numeric CodaBench Final destination are not verified.** Keep the existing ZIP unchanged and hold submission. No package is produced or uploaded by this audit.

# Official Final readiness

## Freshly verified official rules

| Item | Current requirement |
|---|---|
| Upload window |13October2026 12:00UTC /21:00KST through26October11:59UTC /20:59KST (25October23:59AoE) |
| Attempt limit |One Final upload per team per track. Failed does not consume it; held/cancelled/scored does. Local checks do not upload |
| Window run |Unranked sealed-card check; status visible, per-card outputs/logs hidden |
| Ranked run |After upload close, fresh cards from data up to23October; all cards share23October asof; UST/G10FX only;2–12BD targets27October–10November |
| Image availability |Anonymous exact digest must stay pullable through results on13November; no intraday publication time given |
| Runtime |1,800s per unit;86,400s shared run allowance, queue excluded and pull included;16CPU,128GiB RAM,GPU;256PIDs;64MiB per output file and total |
| Image contract |linux/amd64, qfbench2.interface_version2.0, no Docker VOLUME, forecast CLI and three required outputs |
| Network/model |House optional for numerical api entry; if used only audited House route,25 admitted requests/unit,4,000output tokens/request |
| Descriptor identifiers |`competition_id=agenthon2026-forecasting-final`, `phase=final`, `track=forecasting`, `category=api`, interface2.0 |
| Claim |Official2.0 team-claim bound to exact descriptor bytes; correct derived alias/account. No key in ZIP |

The11October Track2 notice explicitly supersedes README/CodaBench/older notices about ranked data and verification timing. The12October clarification confirms common23October asof and no monthly/factor/EMFX targets; whether panels contain23October's own close was still pending there. This unresolved detail is not guessed. The10October run-limit notice supplies resource/attempt rules; Track2's later notice extends pullability through13November.

## Readiness gates

| Gate | V5.1 | M16 |
|---|---|---|
| Source identity |VERIFIED safe image/source26 files |VERIFIED frozen mechanisms plus repaired transport |
| Actual image evidence |VERIFIED prior immutable public image,18 forecast processes and later anonymous recheck |VERIFIED test images,5jobs/110processes; no published repaired registry digest |
| Current output schema |Static validation keywords same as runtime2.4.2; old fixture receipts reused |Same static schema boundary and prior container output checks |
| Image currently/future pullable |Known successful prior pulls; not freshly pulled in this audit; keep until13November |No deployed repaired reference identified |
| Actual Final descriptor/claim |UNKNOWN, user-held ZIP unseen |NOT_CREATED / NOT_RECOVERED |
| Actual ZIP CRC/hash/member binding |NOT_RUN, ZIP_BYTES_VERIFIED=false |NOT_CREATED |
| Numeric CodaBench Final competition/phase |UNKNOWN |UNKNOWN |
| Full release gate |Image technical proof present; package gate BLOCKED |BLOCKED regression and lack of deployable Final artifact |
| Live House |Not required for exact safe mode |UNKNOWN |
| Independent performance improvement |UNKNOWN |UNKNOWN |
| READY_TO_SUBMIT |BLOCKED |FALSE |

The actual public Development page17766 could not be read by the retrieval service, and focused search recovered no authoritative platform phase mapping. No signed-in session or account was probed. The Final descriptor string is authenticated by the official C5 fixture/guide; it does not establish the numeric platform competition or phase ID. Those are distinct identifiers.

## Official validator boundary

Pinned packaging toolkit2.6.0 (`bd01548e34d21fd660d88fd06157078fb25ece4e`, contract set1.1.0) is distinct from immutable image runtime common2.4.2. Existing Secure14 fixtures/toolkit execution is reused; no positive fixtures rerun here. Current schema/parser source was read from shared HEAD `6181b9c9f45c93ee526a6692406367a4042da7ad`. `SubmissionDescriptor.from_mapping` checks structure and descriptor_digest; `matches_plan` checks exact final track/competition/phase. Schema alone misses those plan matches and actual alias ownership. Official `qfbench2 submission pack` is a sealing/packaging command, not a read-only ZIP verifier, and must **not** be rerun against the existing safe ZIP in this audit.

Fresh static validation of the old public delivery11 template shows missingteam_id/descriptor_digest and wrong dev identifiers for Final. These findings concern that validation-only template, not the unseen user's sealed file. Old/current forecast schemas differ only in a prose description, with identical validation keywords; this helps interpret prior schema receipts but does not establish a new runtime smoke result.

## Precise local-only next check

For the **already existing** `V51-final-submission.zip`, a read-only local check should compute whole-ZIP SHA256/size and CRC; require exactlysubmission.json plusteam-claim.json; validate closed descriptor fields and canonical self-digest with the official parser; match final/forecasting/agenthon2026-forecasting-final; require the exact safe immutable image and intended model-free declaration; check2.0 claim structure and its descriptor_sha256 against the exact descriptor bytes. Do not print proof, alias, key, token or password. Produce only sanitized pass/fail/hash/version evidence if a future task is authorized.

Those structural checks need no Team Key. Independent HMAC/linked-account authentication is organizer-side or depends on existing trustworthy official-pack evidence; it remains BLOCKED_LOCAL_SECRET_DEPENDENCY without that evidence. Never request the key here. The user should also confirm the official Final upload page/phase when the window opens, without uploading during this task. No existing ZIP changes or repacking are prescribed.

Sources: [Track2 Final notice](https://github.com/Agenthon-2026/track2-forecasting-public/issues/4#issuecomment-6103652999), [asof/asset clarification](https://github.com/Agenthon-2026/track2-forecasting-public/issues/4#issuecomment-6116227449), [Final limits](https://github.com/Agenthon-2026/Agenthon2026-public/issues/2#issuecomment-6099955125), [official Final fixture](https://github.com/Agenthon-2026/Agenthon2026-public/blob/6181b9c9f45c93ee526a6692406367a4042da7ad/common/qfbench2_common/contracts/fixtures/c5/forecasting_final.json), [team claim](https://github.com/Agenthon-2026/Agenthon2026-public/blob/6181b9c9f45c93ee526a6692406367a4042da7ad/starter-packs/track2/TEAM-CLAIM.md).
