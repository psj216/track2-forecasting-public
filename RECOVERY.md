## Executive summary (read this first)

Independent M16 source recovery succeeded and transport was repaired. Execution stopped after two full-repository validation failures. Resume from the existing branch and evidence, not the old incomplete shared clone. Final remains ineligible.

# Recovery

Repository: psj216/track2-forecasting-public.
Branch: track2/moonshot-16-house-transport-repair.
Original PRE: ec36fbda44ca17c1c64b0b07da7d6adffbdb721b.
Original stopped RESULT: 74ebc30cbec728a4a739d58064e6f9e5772182b6.
Recovery checkpoint: 530b2c4b1eac215cd32535e3bb97d7e969f7f161.
Implementation checkpoint: 02b581199370be1071c7887907bb6df96742c544.
Frozen parent: 361018c14bab3cb7d8da101aa332066644921bac.

The source is a self-contained independent official git clone with no alternates. The full parent chain and fsck passed. Original PRE/RESULT remain ancestors. Current runtime differences are confined to the three permitted files.

Completed: transport 24, parser 54, fallback subset 125, integration subset 52, affected 130 and public comparisons 10. New unique M16 tests: 265 passes. Detailed synthetic receipts and frozen-source test fixtures are preserved. Do not rerun old research.

STOP point: full pytest first failed collection for missing sklearn; after installing sklearn, its one retry returned 11 failed, 1278 passed, 26 skipped. No third attempt. Unchanged historical tests require origin/main, private metadata variables, historical branch/path assumptions and yaml. Two new comparison-test lint issues remain. No assertion was changed to pass.

Next run: recover the latest verified branch independently; resolve new lint and concrete historical test prerequisites before any full retry; then container smoke if a Docker-capable environment exists. Keep failure evidence. Do not silently exclude old tests or infer alpha from mocks. Actual House/independent performance remain UNKNOWN.

Environment: Python 3.13.16, qfbench2-common v2.4.2 at dfa92d242908bba4a448218b9c10ae391238d10d, numpy 2.1.3, pandas 2.2.3, pyarrow 18.1.0, jsonschema 4.23.0, scikit-learn 1.6.1. Dependencies were installed before tests. No Docker/podman, image build or submission.

Existing V51-final-submission.zip stays solely with the user and was not requested or recreated.
