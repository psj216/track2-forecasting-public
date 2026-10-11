# V51-DELIVERY-EMERGENCY-11

## Executive summary

**SAFE_CANDIDATE_READY_EXACT_IMAGE.** The exact frozen V5.1 preparation image was pulled anonymously on a branch-push GitHub Actions runner, with no rebuild. Five public raw-fixture cards passed schema, cutoff and historical route checks. Four family representatives ran three times each; forecast arrays, draw ordering, parquet bytes, normalized metadata and rationale were identical. There were 18 forecast container runs in total. No new model, forecast logic, score, leaderboard tuning or submission was performed.

Historical Development **0.9541** remains a reference. This validated candidate is **not proven** to be the artifact historically uploaded for that result.

## Frozen identity and Git chain

| Item | Identity |
|---|---|
| Branch | `track2/v51-delivery-emergency-11` |
| Parent RESULT | `d37c1a922b9dac750309e41e1569851bf7060db2` |
| Inherited scientific parent | `6903eb83c7c84c5c6dc581c1c76820a24bbc89e6` |
| PRE, remotely verified before workflow addition | `a592b20223cc6225af70658ec696737f9c1c6d09` |
| Workflow trigger / Actions checkout | `66a07d47e4ad5a738f0b3ec613b8f8a4a1c8af5a` |
| Image | `docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874` |
| Image ID | `sha256:1d6835db45dec0dd419b135441540b9e27e1b1218f37c051f1e13a0c2072eb74` |
| Source | `47194f28d5188b87cdca1d591d86b9eeda86f7cf` |
| Platform / user | linux/amd64 / `runner`, non-root |
| Common | 2.4.2, source `dfa92d242908bba4a448218b9c10ae391238d10d` |
| Protected main | `e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8` |

The package files inside the container match the exact source checkout by SHA-256. Image dependencies are Python 3.13.15, numpy 2.1.3, pandas 2.2.3, pyarrow 18.1.0, jsonschema 4.23.0 and qfbench2-common 2.4.2. No candidate files, mode, dependencies, seed or draws were modified.

## Push workflow and remote evidence

Workflow: `.github/workflows/v51-delivery-emergency11.yml`, push only to the named branch, `contents: read`, no login, secrets, image publication, rebuild or submission. A paths filter prevents report/result-only pushes from repeating validation. The older manual workflow and main were untouched.

Actions run [38124740551](https://github.com/psj216/track2-forecasting-public/actions/runs/38124740551) concluded **success**; job ID 114426656915, Ubuntu 24.04.5. First anonymous digest pull succeeded; no retry was needed. The recorded RepoDigest matches exactly. Validation took 53.298s after setup.

Artifact ID 11696333929, 90 evidence files, downloaded ZIP SHA-256 `1c0751f363697061f7445030bebe3905db71e35e4e84f06acc359a26f61908db`. Downloaded bytes, CRC, runner receipt and Actions SHA were checked rather than relying on the green UI. The exact receipts and redacted command logs are retained in `results/actions_evidence/`.

## Runtime and schema matrix

| Unit | Exact cutoff | Assets | Horizons | Draws | Wall time | Schema/cutoff/exit |
|---|---|---|---|---:|---:|---|
| t2-F1-patient-dropped-2015 | 2015-03-18 | UST_2Y | [129] | 500 | 2.061s | PASS |
| t2-F2-eur-parity-2022 | 2022-06-30 | EUR | [64] | 500 | 1.993s | PASS |
| t2-F3-brexit-joint-2016 | 2016-06-17 | GBP, EUR, CHF, JPY | [21, 63] | 500 | 2.040s | PASS |
| t2-F4-funding-stress-2y-2008 | 2008-09-12 | UST_2Y | [63] | 1000 | 2.069s | PASS |
| t2-F4-covid-nfp-2020 | 2020-03-31 | NFP | [21] | 1000 | 1.810s | PASS |

Isolation: exact digest, `--network=none`, read-only root and input, tmpfs `/tmp`, writable `/output`, image non-root user, 2 CPU/8 GiB/pids 256. Each card ran both historical numeric and text-first-v5.1 modes. No scoring utility or outcome file was invoked. The public grid, bounded parquet parser, common 2.4.2 JSON Schema, metadata binding and text-corpus cutoff utilities were used directly. All arrays were finite with complete draw×asset×horizon coverage. Input panel timestamps and text publication cutoffs were checked.

All five cards produced nonempty `forecast_rationale.md`, alongside `forecast.parquet` and `forecast_meta.json`. No sidecar packaging repair was required.

## Historical route invariants and determinism

F2 EUR and F3 Brexit numeric/text parquet bytes were identical. F1 patient and both F4 cards activated the established text route, produced a changed forecast, and passed reasoning/adjustment, currentness, last-world-date, evidence ID/excerpt, direction and sleeve `(0, 0.20]` checks. Both F4 outputs contained 1,000 draws.

| Representative | Parquet SHA-256 | Three runs |
|---|---|---|
| t2-F1-patient-dropped-2015 | `384c59406afe5aca5bbbc6cdeb9a283f9249866a2b38896ba2a430e719330bd7` | identical ×3 |
| t2-F2-eur-parity-2022 | `8c47d3b7adfc39c0e3d48566a3c530cd9f1292abada7755a9c7102209387b33e` | identical ×3 |
| t2-F3-brexit-joint-2016 | `56303276d6b3078c655a632b180e5e9b8ff913f013fb4caba9da32a9cff7ca95` | identical ×3 |
| t2-F4-funding-stress-2y-2008 | `b169a58aef562d43b66bad3dc1c12fa1995896e3240ae6fa0c1e76175c74383a` | identical ×3 |

All parsed numeric arrays and draw ordering were bitwise identical. Parquet, metadata and rationale bytes were also identical in all repeated runs. Full per-file and parsed-array hashes are in `determinism_audit.json`.

## Security and resources

Security passed: 16,650 filesystem entries inventoried, 58 bounded application/work/home/root files scanned, no secret-signature, credential-path, hidden-label or private-truth findings. Pattern-based inspection cannot prove absence of every possible secret encoding. No credentials or hidden outcomes appear in the validation package.

Image size: 538,357,294 bytes. Maximum observed container wall time: 2.110s; maximum output size: 48,571 bytes. All executions fit the conservative 8 GiB/2 CPU cap and repository parser output limits. Peak memory was not separately sampled. This verifies these five fixtures, not all unseen competition tasks.

## Current contract and validation-only descriptor

Current official `SUBMISSION_CLI.md` was read at track commit `a2c93e7b66b8c6a6c429fda81d6bc7873b7c5dec`; descriptor guidance/schema at common commit `c817c36780aba74e9caeb8d86167103b66b779f1`. The candidate has the required interface 2.0 label, forecast verb, linux/amd64 architecture, no Docker VOLUME, offline operation and required rationale sidecar.

These public raw fixtures have parquet panels at `/input`; the frozen historical invocation therefore uses `--panels /input`. Official staged bundles use `/input/panels/`. No image change was made to resolve fixture layout.

`submission.json` is deliberately a **validation-only template** pointing to the immutable digest. No verified derived team alias was available, so `team_id` and `descriptor_digest` are absent. The current schema confirms the other fields and reports exactly those two missing required fields. Full upload-descriptor validation/sealing is therefore **not claimed**. No example team identity was copied, no Team Key accessed and no team-claim generated. The delivery evidence package is not a CodaBench submission ZIP.

## Local tests and inherited CI limitations

| Suite | Result |
|---|---|
| Emergency11-specific | 12 passed |
| Affected | 91 passed |
| Full repository | 951 passed, 25 skipped, 3 deselected, 2 warnings |
| Common 2.4.2 toolkit | 250 passed |

All ran only after Actions evidence retrieval, using the restored absolute common path `/workspace/scratch/935b41f252e9/safe09-common242/common`, repository `/workspace/scratch/935b41f252e9/v51-delivery-emergency11` and test dependencies `/workspace/scratch/935b41f252e9/repair10-test-deps`. Original private historical test artifacts were restored with their original hashes; origin/main was restored as a tracking ref.

The three inherited immutable branch-only exclusions remain documented in execution_audit.json; no historical assertions were changed. One affected-suite invocation named a nonexistent `test_parse_limits.py` and executed zero tests; the discovered `test_limits.py` path corrected the command, which then passed. No expectation was relaxed.

The unrelated inherited Track 2 CI run 38124740585 remains red: 61 historical collection errors and 2,245 historical lint findings. It is distinct from the successful Docker validation workflow and the repaired local full suite. No historical tests/source were modified to mask those existing CI problems.

## Delivery, protection and next step

Validation package SHA-256: `56a5fe04ac301e0d0b7ac56f569cbd47dda4cde951a80bc939955d835e85a55c`; CRC and every listed member hash verified. The final recovery archive is created after remote RESULT verification; its RESULT binding and full archive hash are external receipts to avoid a self-referential Git/ZIP hash.

All 2,571 parent blobs, including 129 V5.1 package blobs, are unchanged. Main remained unchanged. RESULT remote HEAD, parent/PRE/trigger lineage, critical files and clean working tree are verified in the final external receipt.

**NEXT: NEW-MECHANISM-MOONSHOT-12.** Not executed in this task.
