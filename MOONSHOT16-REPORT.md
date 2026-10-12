## Executive summary (read this first)

Classification: TECHNICALLY_REPAIRED_BUT_UNPROVEN. Independent source recovery and the minimal House transport repair succeeded. All 265 new M16 tests passed, including A-E mock cases and original/repaired parquet comparisons. Full repository validation did not pass: after a dependency repair, its retry returned 1278 passed, 11 failed and 26 skipped. The requested two-failure STOP rule ended further execution. No Docker image or submission was created. Keep the existing V5.1 safe artifact as the preferred Final candidate.

# MOONSHOT16 recovery-resume report

## 1. Actual recovery method and history

A new self-contained clone was created directly from https://github.com/psj216/track2-forecasting-public.git using --no-checkout --single-branch for the existing M16 branch. It used neither --shared nor --reference. No old clone, object alternate or incomplete object store was reused.

git restore --source=HEAD --staged --worktree . materialized the current M16 HEAD. This was not a third retry of the old frozen checkout command. The restored HEAD, clean tree, commit/tree object existence, parent chain and git fsck --full passed. The frozen transport blob was fetched through the approved connector and matched local Git hash cec8fc3ebbaccc57e8121db4e7a526ebfe2409bb.

Verified resume HEAD: 74ebc30cbec728a4a739d58064e6f9e5772182b6.
Preserved original PRE: ec36fbda44ca17c1c64b0b07da7d6adffbdb721b.
Frozen parent: 361018c14bab3cb7d8da101aa332066644921bac.
Frozen tree: 9c7a78e3c23078bbe7f9c50f7eb50d65451869db.
Recovery checkpoint: 530b2c4b1eac215cd32535e3bb97d7e969f7f161.
Implementation checkpoint: 02b581199370be1071c7887907bb6df96742c544.
Final evidence SHA is reported in the handoff and remote branch; a file cannot embed its containing commit SHA without changing it.

The prior report/provenance/contract/recovery/status were read from the verified remote HEAD. Its unfinished phases were resumed. Existing historical evaluations were not restarted.

## 2. Modified files

Runtime changes are limited to moonshot15_engine/official_transport.py, engine.py request handling, and cli.py receipts. New tests are test_moonshot16_transport.py, test_moonshot16_runtime.py, test_moonshot16_comparison.py and their frozen-source fixture. Existing assertions were unchanged.

The config, prompts, context, entrypoint and all engine forecast/parser/transform functions except request remain identical to the frozen source. Protected SHA256 and AST checks passed. The test fixture preserves exact original sources for comparison; it is not a runtime forecaster and is not copied by the Dockerfile.

No main/M15 branch, V5.1 safe artifact, frozen image, existing image tag or forecasting parameter was changed.

## 3. Transport and metadata repair

The uppercase-only regression test was demonstrated to fail before repair. It passes after repair.

HTTP_PROXY/http_proxy and HTTPS_PROXY/https_proxy aliases are supported without changing their values. All nonempty grants must be equal; conflicting values fail before any request. An HTTPS_PROXY-only grant can supply the same explicit audited HTTP proxy. HTTPS proxy URL schemes remain unsupported and fail closed; the variable name does not mean the proxy URL itself uses HTTPS.

The injected HTTP origin uses absolute-form POST /v1/chat/completions via the explicit authenticated proxy. The injected HTTPS origin uses HTTP CONNECT and default TLS certificate/hostname verification. Proxy authorization is only on CONNECT for HTTPS, not forwarded to the House origin. Arbitrary endpoint overrides, non-origin paths, credentials/query/fragment, direct/NO_PROXY bypass, redirects and external fallback are rejected. There are no retries.

Safe failure categories distinguish missing endpoint/model/token/proxy, conflicting configuration, proxy authentication, HTTP status, timeout, TLS failure, malformed outer/model JSON, duplicate keys, schema rejection, truncation and output/runtime failures. No raw exception/server text, endpoint credential or actual token is saved.

Per-call receipt fields distinguish request_attempted, request_sent, response_received, response_validated and HTTP status. request_sent=true means the local request() completed; it is not a claim of organizer admission. An interrupted send is unknown. The CLI records adjustment_applied, fallback_used and location_shift_statistics separately from legacy reasoning_applied. E's second-call failure reverts the whole parquet atomically.

## 4. Tests and forecast comparisons

Counts below overlap; do not add them as a unique total.

| Stage | Result |
|---|---|
| Unmodified uppercase regression control | 1 expected failure |
| Transport unit | 24 passed |
| House parser | 54 passed |
| Failure/fallback integration subset | 125 passed |
| Success/E-atomic/repeat/frozen-semantics subset | 52 passed |
| Existing affected package | 130 passed |
| Public original/repaired/baseline comparison | 10 passed |
| New M16 unique tests | 265 passed, 0 failed, 0 skipped |
| Full repository first attempt | 56 collection errors: sklearn missing |
| Full repository retry after sklearn installation | 1278 passed, 11 failed, 26 skipped |
| Existing regression_suite/run_regression.py | ALL REGRESSION CHECKS PASSED |
| Unit stdlib checks | 104 units passed; manifest/public-safety not included |
| Container smoke | Not run: no Docker or podman |

166 detailed mock cases cover the previous 76 conditions and additional errors. Failure outputs exactly match V5.1 parquet bytes. Successful fixed responses change the parquet and preserve draw/grid/finite checks. Three repeated normal runs produce identical parquet, metadata and rationale bytes. These tests use local synthetic credentials and mock services only.

Ten public-input comparisons cover A-E on a single-target and a joint card. With a functioning lowercase proxy, frozen M15 and repaired M15 parquet are byte-identical, including cross-asset/horizon distributions and geometry. With uppercase-only proxy, original M15 falls back without a House request; repaired M15 applies the same nominal correction. This proves repair behavior, not forecast accuracy.

The production timeout remains 60 seconds. Matrix timeout faults use a disclosed test-only 0.1-second deadline. No actual House/CodaBench connection, Team Key or score evaluation was used.

## 5. Full regression failures and STOP

The entire repository failed twice, so no third full execution or post-STOP code repair was attempted. The 11 failures are in unchanged historical tests. Recorded causes include missing origin/main in a single-branch clone, historical private metadata environment variables, an old expected branch/ancestor snapshot, a hardcoded old-workspace toolkit import path, and missing yaml. They are not silently skipped or rewritten.

The failed test list and results are in MOONSHOT16-TEST-RECEIPT.json. A fresh frozen-suite A/B reproduction of these 11 failures was not performed, so this report does not claim all full-suite failures have been causally excluded as regressions.

Two lint errors remain in the new comparison test (I001 ordering and F811 fixture import/parameter redefinition). Its behavioral tests pass. These lint errors were discovered before the STOP and remain explicitly unresolved. Earlier transport and first two test-file lint checks passed. Existing global CI was already failing, and no green-CI claim is made.

## 6. Gate and Final recommendation

| State | Result |
|---|---|
| SOURCE_RECOVERED | TRUE |
| TRANSPORT_FIXED | TRUE |
| M16_SPECIFIC_TESTS_PASSED | TRUE |
| TESTS_PASSED / REGRESSION_PASS | FALSE |
| FALLBACK_EXACT | TRUE for tested mocks |
| PROVENANCE_VERIFIED | TRUE |
| IMAGE_BUILD_READY | UNKNOWN |
| LIVE_HOUSE_VERIFIED | UNKNOWN |
| INDEPENDENT_ALPHA_VERIFIED | UNKNOWN |
| FINAL_ELIGIBLE | FALSE |

Classification: TECHNICALLY_REPAIRED_BUT_UNPROVEN.
Prefer the user's existing V51-final-submission.zip. Do not request, recreate, modify or submit it.
The old CodaBench root cause remains unconfirmed. Mock repair is not evidence of independent score improvement.

## 7. Exact next work

In a separately resumed run, begin with the preserved independently recovered branch. Fix the two new comparison-test lint issues without changing assertions. Establish the historical-test environment/ref/metadata requirements and handle fixed old-branch/path assumptions through an isolated compatible test environment, not assertion weakening. Recheck full regression only after those prerequisites are concrete. Then perform a real container smoke in a Docker-capable environment with an isolated authenticated mock network, preserving all existing images.

Live House success and independent PIT-safe quality evidence remain separate missing gates. Do not infer them from mocks or use Development scores for tuning. No Final submission is authorized here.

Evidence: MOONSHOT16-TEST-RECEIPT.json, MOONSHOT16-FALLBACK-MATRIX.json, MOONSHOT16-PROVENANCE.json, MOONSHOT16-FINAL-GATE.json, backtesting/moonshot16/results/full_mock_receipts.json.gz and forecast_comparison.json.
