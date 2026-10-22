## Executive summary (read this first)

Freeze FINAL-FIT-05 before new Docker execution. Preserve Original, FF03, FF04 and ALPHA18. No production patch unless the frozen severity gate establishes A or material B. Existing 22-card FF04 evidence is inherited, not rerun without a patch.

## Identity and boundaries

Parent: c6fcb0eec71e0442ed6d73a70c7cb958c221374b.
Branch: track2/final-fit-05-numerical-release-readiness.
Original source: 47194f28d5188b87cdca1d591d86b9eeda86f7cf.
Original immutable reference: docker.io/jotj216/track2-f4-approved@sha256:0b9b08d8a6b59eca262d77778d2b2a9b33bb938ab68c4db8f71538302f3bf874.
FF03 executable source: c5b8bbbd6227888b7a3dc0bbd05dc414d2d7c3f6.
FF03 local image ID: sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c.
FF03 archive SHA256: df232487177cb56cb0ae945b2613fbbebbb24eff702f21712662e589d04f636c.
Official source observed: 3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56.
Protected references are snapshotted from ls-remote. No existing branch, image, archive or Windows ZIP is modified. No secrets, registry push, team-key access, package packing or submission.

## Numerical reproduction

Restore the exact archived image on two independent GitHub-hosted runner jobs. Original and FF03 run representative t2-F4-curve-ust3m-008-ps1, seed 17, 1000 draws, identical official input hashes, container flags and package versions. Compare default dispatch, repeated default dispatch and NPY_DISABLE_CPU_FEATURES=AVX512F,AVX2,FMA3. Trace locals of the existing numeric function in a separate diagnostic process; do not overlay forecasting code. Record distances, exact tie groups, near ties, default and stable sort, pool membership/order, bootstrap selection and RNG states where observable. Production forecasts remain standalone.

## Frozen severity rules

A: crash, nonfinite/missing output, current official gate failure, contract-mandated determinism violation, or gross distribution distortion.
B: valid output but mean/median shift >= 1% of baseline IQR, any tested quantile (1,5,50,95,99%) shift >= 5% of IQR, RMS paired-draw shift >= 5% of IQR, or absolute raw-score relative change >= 1% (only diagnostic, never optimization). Also classify B if substantive instability cannot be bounded. Zero IQR with a nonzero change is B.
C: valid output, same-runner deterministic, no A/B trigger; observed CPU difference is a nonblocking residual. IQR means interquartile range. Paired-draw difference and marginal distribution change are reported separately. Two runners do not establish universal CPU coverage.

## Patch acceptance and no-patch criteria

Only actual A/material B permits a separate FF05 hardened image. Fix only demonstrated distance/order dispatch effects. No weights, volatility, drift, tails, architecture or monthly semantics changes. No epsilon/bucket search against scores. Require RED then official full 22-card replay plus monthly/output regression, independent runner and CPU-feature tests. Any legacy draw change is INTENTIONAL_NUMERICAL_BEHAVIOR_CHANGE. Severity C means NO_PATCH, FF03 exact identity retained, FF04 22/22 reused. If evidence is incomplete, report INCONCLUSIVE rather than fabricate a pass.

## Regression and final release gates

Exercise exact FF03 Docker on published CPI/NFP and a small explicit-period boundary matrix. Synthetic fixtures remain labelled synthetic. Missing Final metadata means BLOCKED for unseen schema, not universal macro approval. Test 16-card sequential existing public inputs, concurrent containers, repeat isolation, read-only/no-network/nonroot and child RSS. Inspect image and layers for unexpected files/secrets without reading credentials. Restore archive, never rebuild unchanged FF03. Build reproducibility may remain NOT_RUN; archive restoration is distinct.

Verify current v2.6.1 descriptor schema and CLI without packing. Registry digest stays null until separately authorized publication. Technical candidate approval is distinct from upload readiness. No independent alpha claim from exposed practice.

## Checkpoints and execution limits

PRE -> PORTABILITY -> DECISION -> REGRESSION -> RELEASE -> RESULT. Commit/push each; verify remote final SHA. Shell step timeout <=600 seconds. Progress every 1-3 minutes. One retry maximum for the same failure. No whole-repository lint or unnecessary 120-test/22-card rerun. Independent normal clone; no alternates.
