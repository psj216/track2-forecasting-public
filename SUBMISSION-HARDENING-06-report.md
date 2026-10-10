## Executive summary (read this first)

# SUBMISSION-HARDENING-06: V5.1 official reference delivery audit

**Verdict: NOT_READY_MISSING_PROVENANCE.** The evidence audit is complete. Delivery readiness is not established. The inherited historical V5.1 Development reference remains **0.9541**; this task did not reestimate that score or independently recover its official receipt.

Three historical V5.1 candidate builds were recovered from original GitHub Actions logs. An original submission-preparation ZIP identifies one of them. That ZIP explicitly states `official_submission = NOT_YET` and says it is not a CodaBench upload package. No available receipt connects the official 0.9541 result to a unique submitted ZIP, sealed descriptor, image digest or invocation. Selecting the preparation image as the official submission would be an unsupported inference.

The binding parent draft requires documenting this gap before any rebuild assumption. Gate A is **PROVENANCE_PARTIAL**; the official chain is missing. The equivalence-rebuild prerequisites also fail. No executable was recovered or built. Conditional runtime, determinism, output-equivalence and resource tests are **NOT_APPLICABLE / NOT_RUN**, never passing gates. A missing Docker engine is an additional execution limitation, not the reason for the provenance verdict.

## 1. Protected lineage and source

| Item | Verified identity |
|---|---|
| Repository | psj216/track2-forecasting-public |
| Branch | track2/submission-hardening-06 |
| Immutable parent RESULT | 8d06fcff48b9cc838d502f4c7b08fa2618015112 |
| Parent PRE | a80d1b431e4b9ff53d9abfd653b681b64fa006fa |
| This audit PRE | 9a8467493908d7295bbfc70077f72f0d33a353a7 |
| Protected main | e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8 |
| Inherited files protected | 2,450, SHA-256 and Git bytes verified |
| Original candidate package files | 26, all unchanged against candidate8b926cf source |

The preparation candidate's actual checked-out source is **47194f28d5188b87cdca1d591d86b9eeda86f7cf**, a PR merge commit. The workflow API `head_sha`8b926cf is not its actual checkout. Its Dockerfile, CLI and V5.1 interpreter were fetched from that exact merge commit and are byte-identical to the current protected files. Candidate45858fa and8b926cf differ only in their candidate workflow. The current research tree includes extra package modules; rebuilding the entire current tree would not recreate the historical build context.

The **official** submitted source SHA remains unknown. Source preservation is not output equivalence. No forecast/model/scorer logic, seeds, draw floors or family routing was changed.

## 2. Historical candidate and artifact inventory

| Actions run | Actual source SHA | Candidate tag | Image digest |
|---|---|---|---|
| 36173403535 | 45858fa41384b30d9a4233becba6de026c3bfa71 | v51-45858fa-36173403535-1 | sha256:7e4e954255a043750b09f07e93ea7548cdc000795e2b1fef8b3322c0acb00200 |
| 36173531198 | 8b926cfce029a604b6336ceef4e3bf3b39ec5246 | v51-8b926cf-36173531198-1 | sha256:f33b326076995274a22cc4c91d3e469723e491df3ce87fe3404bc0ebfde44997 |
| 36173543967 | 47194f28d5188b87cdca1d591d86b9eeda86f7cf | v51-47194f2-36173543967-1 | sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874 |

Registry: `docker.io/jotj216/track2-f4-approved`. These runs succeeded on September25. Linux/amd64 is supported by the x86_64 CI and container wheel records; no current registry manifest or image configuration was inspected. Historical anonymous-pull success is not a current availability attestation.

`V5.1_Text_First_Submission_Preparation.zip` is1,819bytes and passes ZIP CRC. SHA-256:
`b3d2ba6dcd05eddaa6b13e96658683d1ca11b1d36350baff6ac5873b6a48766c`.
It contains README, image reference, an unsealed descriptor draft and validation summary. Its digest matches run36173543967. It lacks an actual sealed descriptor/claim. Its historical local claims are103/103 smoke,49/49 frozen F2/F3 preservation and324/324 draw/seed stability; these are supporting historical evidence, not newly reproduced image outputs.

Actions artifacts are two-file image-reference/source-commit metadata ZIPs, not submitted ZIPs. Their IDs and archive hashes are in `historical_image_identity.json`. Two separately discovered tail descriptor drafts are excluded: they reference a different tail digest and are not original V5.1 receipts.

Search covered local Git history, protected reports, remote releases/tags, all accessible V5.1 candidate runs/jobs, PR evidence, project recovery manifests and the relevant121-item artifact folder. No official evaluation ID, upload timestamp, submitted ZIP hash or score receipt was found. This is a scoped negative finding, not proof that the platform has no such receipt.

## 3. Common, dependencies and base image

All three candidate Docker logs install **common2.4.2**. Its annotated tag object is e780dc4dc98293c6a126a2f182ca230b5fb25127 and peeled source commit is **dfa92d242908bba4a448218b9c10ae391238d10d**. The annotated tag must not be mistaken for a commit. Later research common2.4.3 peels to03fc89cc666354e999768381bb923e60be5c1cee and does not replace candidate2.4.2.

Static2.4.2→2.4.3 comparison finds unchanged common scoring, panel/runtime serialization and forecasting output schema bytes. Descriptor categories/schema remove byo-small/byo-large, documentation changes and package version advances. Runtime dependency constraints do not change. No dynamic cross-version equivalence run was performed. Current official packaging-tool documentation refers to2.6.0; that is not authority to upgrade the candidate's installed numerical runtime.

Recovered candidate container versions: numpy2.1.3; pandas2.2.3; pyarrow18.1.0; jsonschema4.23.0; scipy1.18.1; common2.4.2; attrs26.1.0; jsonschema-specifications2025.9.1; python-dateutil2.9.0.post0; pytz2026.4; referencing0.37.0; rpds-py2026.6.3; six1.17.0; tzdata2026.4. Python is3.13, but the exact container patch is unresolved. CI-host Python3.13.15 is not evidence of the container patch. The forecasting2.1.0 source was copied into `/opt`, not installed as a package distribution. Full container wheel hashes and system package closure are unavailable.

The Dockerfile's floating base tag risk is preserved. All three original build logs resolve:
`python:3.13-slim-bookworm@sha256:2325bb286ec344af3e5898cc224b5844e2707ac6e26b1632516fd3edc84a5e26`.
This recovered immutable reference is documented separately. The historical Dockerfile was not rewritten, and no official receipt links this base to the score.

Candidate build argument: `FORECAST_MODE=text-first-v5.1`. Source default seed0 and draws500; F4 floor1000, with the larger card minimum honored. Official invocation arguments remain unknown. Docker USER is runner UID1000; current harness UID65534 must be tested separately. CMD is `forecast --help`; the harness supplies the actual forecast arguments. Output files are forecast.parquet, forecast_meta.json and forecast_rationale.md.

## 4. Current policy and verified deadline

Authoritative documents were retrieved on October10 and hashed in the policy evidence manifest. Official Track2 documentation is pinned to30c8019d997f930eab9ba569d089d12298d86d8c; the official runtime document is pinned tobbc0d6089337d0337c20abc68297138ea6e5f1f4.

| Schedule | Exact value |
|---|---|
| Development/registration close | 2026-10-12 23:59 AoE =2026-10-13 11:59UTC =20:59KST |
| Last new Development run start | 2026-10-12 20:00UTC =2026-10-13 05:00KST |
| Maintenance | 2026-10-13 08:00–12:00UTC |
| Final+Verification close | 2026-10-25 23:59AoE =2026-10-26 11:59UTC =20:59KST |

An upload not started by the earlier run-start cutoff will not run. Upload timing is not a queue-start guarantee. No upload or score request occurred.

Development contract: linux/amd64, interface2.0, api category, sealed submission.json plus team-claim.json in a ZIP referencing an anonymously pullable immutable image. House calls are optional for permitted numerical operation; disclose fitted models if present. No participant vendor key route. A Team Key belongs only in the hidden local packer prompt/file and was never requested or copied here.

Track2 Development grants16CPU quota,128GiB,1,800seconds per unit and43,200seconds ingestion stage. UID65534/non-root, read-only root, `/input` read-only, writable `/output`,64MiB noexec/nosuid/nodev `/tmp`,64MiB output tree,256PIDs,1,024file descriptors,256nproc and no swap. House limits are25calls/unit and4,000output tokens/request. Development quotas do not certify Final resources. Minimum200draws and any larger card floor remain mandatory.

Track2 Development allows5uploads/day and20total; held/cancelled uploads count, platform Failed uploads do not. Final allows one submission per track. Policy permits reproducible source/image packaging subject to its rules, but supplies no blanket grandfathering or equivalence attestation for an unidentified historical image.

## 5. Gate disposition and chain of custody

| Link or gate | Status |
|---|---|
| Official0.9541 receipt → submitted artifact | MISSING |
| Submitted artifact → historical image/source | MISSING |
| Preparation ZIP → run36173543967 image | VERIFIED |
| That candidate image → actual source47194f28 | VERIFIED |
| Candidate source → common/dependency versions | SUPPORTED; immutable closure incomplete |
| Dependencies → currently recovered executable | MISSING |
| Executable → three repeated offline outputs | MISSING / NOT_RUN |
| Repeated outputs → historical protected outputs | MISSING / NOT_RUN |
| Equivalent outputs → valid sealed package | MISSING |

Original image recovered: **no**. Rebuild performed: **no**. Run1/run2/run3 output hashes: **not available**. Byte determinism and historical output equivalence: **not established**. Schema/runtime/as-of/resource gates: **not run**. Actual package and image-layer security audit: **not run**. A pattern scan of newly produced audit text found no credentials; that does not certify an absent image or submission package.

Stop reason: the official receipt/package/unique source/config and immutable rebuild closure do not satisfy the frozen prerequisites. Do not select the latest Actions digest, substitute the tail draft, rebuild the current research tree, use a default seed as an official invocation, or label source parity as output parity.

## 6. Tests and operational completion

| Suite | Receipt |
|---|---|
| research | 39 passed in 0.13s |
| affected | 137 passed, 2 skipped in 2.96s |
| full | 897 passed, 25 skipped, 3 deselected, 5 warnings in 27.55s |
| common | 250 passed in 0.85s |

Audit-only tests check fail-closed provenance, unchanged inherited bytes, source/dependency identities, rejection of unmeasured or mismatched output evidence, independent repeat count, required runtime fields, card draw floors, unsafe package paths and absence of fitting/scoring/submission calls. Synthetic evidence tests validate gate logic; they are not container executions. Existing V5.1/schema tests run in the audit environment, not the original container.

Three historical immutable branch/private-path assertions retain the exact exclusions documented by parent RESET05. No historical test was edited or weakened. The full test environment uses existing private source-artifact dependencies only for inherited test validation; no Development hidden answer access or new candidate scoring occurs. Those dependencies are not included in the public audit or final recovery archive.

PRE9a846749... was pushed and its remote branch and critical files checked byte-for-byte before conditional-stage disposition. RESULT and final recovery identities live in the external completion receipt to avoid self-referential commit/archive hashes. Finalization verifies parent/PRE/RESULT lineage, remote critical bytes, unchanged main and all2,450 parent files, then a clean tree. The final non-secret recovery preserves the audit, historical source references, preparation ZIP, test logs, branch metadata and hashes. ZIP CRC, member SHA-256 and complete archive SHA-256 are checked.

## 7. Continuation required

Recover the actual official0.9541 receipt and the sealed submitted ZIP/descriptor so a unique image/source/invocation can be identified. Recover its immutable runtime and protected fixture outputs. Then continue the already frozen hardening gates. This is evidence recovery, not permission to redesign forecasts or execute another research study.

No new model, forecast logic, candidate score, leaderboard tuning or submission was performed. V5.1 remains the historical safe reference, with delivery readiness explicitly unresolved.
