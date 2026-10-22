## Executive summary (read this first)

FF03_RETAINED_WITH_NONBLOCKING_RISKS. Existing FF03 remains the single selected technical candidate. No production code/model/parameter change, no FF05 image, no push to a registry, no Team Key access, no ZIP packing, no CodaBench upload. Cross-CPU RED is reproduced and bounded in the observed representative case; new Macro/ECB G10 sealed metadata remains unknown.

## Checkpoints

Branch: track2/final-fit-05-numerical-release-readiness.
Parent: c6fcb0eec71e0442ed6d73a70c7cb958c221374b.
PRE: e2d6105b83af836ac34a49bf3885da029e42c900.
PORTABILITY execution freeze: 258a09ef9978344937cca31d8b1832db6e210ac1.
PORTABILITY evidence: 8f6731a44170508dddacadd4f1043b49ae84e731.
DECISION: 6b7f5019f63d8eaa5c1f22a1a9f0efe64caaf12d.
REGRESSION: 2e3d24228e0c0ac773fb4a11ada396b5b02256de.
RELEASE: 0a0b63de65a4b2dbf764958a3d7485aa2cfc3045.
RESULT: the commit containing this report, resolved from the remote branch; do not confuse an earlier checkpoint with RESULT.
Official rules source: 3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56; toolkit v2.6.1: 03c50a0036aaf72675d353aef4c7c01ca86d1fcf.

## Numerical finding

Two different AMD CPUs, EPYC 7763 and 9V74, exactly reproduce FF04's 13/2000 changed values and maximum 0.06308603200308704 percentage points. Same input hashes, frozen package versions and Docker flags, seed 17 and 1000 draws. Original and FF03 match within each environment. All ten standalone forecasts and official gate checks pass. Both same-runner FF03 repeats are byte-identical. Universal cross-runner byte identity is false.

Default NumPy argsort changes exact-tie order even when all distance bits are identical. One CPU-feature probe also changes one distance by 1.11e-16. Observed stable full orders match, but that does not prove every future near tie is safe. RNG states/random sequences match; selected blocks differ. Cross-runner means shift less than 0.000095 percentage points; tested 1/5/50/95/99 quantiles and medians match. Max empirical Wasserstein-1 movement 0.2971% of IQR; max paired RMS 5.5990% of IQR. Default cross-runner raw-score sensitivity is -0.06472%, and feature-toggle sensitivity -0.04925%/+0.01548%. These are raw exposed Practice diagnostics, not independent alpha or Final score forecasts.

Severity B is preserved because the frozen paired-RMS screening threshold was crossed. Reviewed as nonblocking: no meaningful observed marginal/output degradation, so NO_PATCH, HARDENING_RESULT=NOT_APPLICABLE. Avoid broad replacement of legacy fixed-seed draw ordering for unproven practical benefit.

## Monthly and execution results

Actions release regression succeeds. Four current published CPI/NFP/UNRATE cards plus seven accepted synthetic boundaries pass official gates; seven synthetic outputs also match the unchanged kernel at explicit monthly steps. Five malformed/unsupported cases safely refuse without forecast files. Target observation month, release date, vintage, as-of, per-asset last observation, output key and sampling transitions are documented separately in the macro matrix. Current official helper SHA256 matches FF03's embedded helper exactly.

Sixteen public short-horizon cards complete sequentially in 27.668s. After-batch repeat output matches. Four simultaneous containers, including the largest published grid, complete in 3.791s and repeated parallel outputs match. Max measured card wall time 3.782s, max output 211735 bytes. Forecast child peak RSS max 203712 KiB; this is not container/cgroup peak. First fresh forecast after restoration 1.792s and next 1.737s, including container startup/inference, excluding image restoration and without clearing OS caches. Three similar 16-card sets would linearly estimate 83.005s excluding pull; actual 48 ranked cards are not available, so no whole-Final runtime guarantee.

Image linux/amd64, interface 2.0, USER 1000, no VOLUME, no ENTRYPOINT (forecast verb resolved from PATH), read-only root/input, writable isolated outputs, tmpfs and network=none tested. All 26 production files and 2 wrappers match frozen source. Exact archive restored, no source rebuild. Byte-reproducible rebuilding remains NOT_RUN/UNPROVEN. All 12 layers / 14256 file entries enumerated; filename checks and bounded <=2MB text/config credential-pattern checks find none. This is stated scan coverage, not proof against arbitrary hidden credentials.

## Reuse and known failures

Full FF04 22-card A/B and exact score equality reused, not rerun. New 16-card sequence is runtime/isolation scope, not a new full A/B. No prior 120-check rerun. Numerical evidence workflow ends FAILURE only at the auxiliary final analysis write: parent directory permission. Forecasts, official gates and raw trace outputs were complete and archived. The same failing step was stopped; exact artifacts analyzed offline without rerunning forecasts or weakening assertions. Release workflow and full-layer workflow both succeed.

Whole-repository CI: firewall and unit/manifests pass; lint 2288 errors and 61 test-collection errors from missing sklearn/requests/bs4 remain inherited. No broad lint cleanup attempted. All seven inherited protected heads and FF04 separately are verified unchanged.

## Release/package status and exact next action

FF03 executable source c5b8bbbd6227888b7a3dc0bbd05dc414d2d7c3f6.
Local image ID sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c.
Archive SHA256 df232487177cb56cb0ae945b2613fbbebbb24eff702f21712662e589d04f636c.
Registry manifest digest NULL. Proposed fresh repository/tag and post-push anonymous verification commands are prepared; no publication performed. Official descriptor controls pass, actual null-filled draft is intentionally invalid. No team identity is guessed. Actual competition numeric URL is not in reviewed public sources; operator must use the registered team's verified Track 2 Final page.

Remaining unknowns: sealed Macro/ECB G10 schemas, full Final runtime/statistical rerun, source rebuild reproducibility, independent alpha, exact 0.9541 provenance. Publication/real descriptor/package/upload are pending separate authorization. Exact NEXT ACTION: authorize publication of the existing verified FF03 archive to the proposed fresh registry reference; then verify anonymous pull by the newly observed manifest digest before any descriptor sealing or packing.

## Evidence links

- Numerical RED (raw evidence complete, auxiliary analyzer-write failure): https://github.com/psj216/track2-forecasting-public/actions/runs/39732916469 ; artifacts 12405747784 / 12406420225.
- Monthly/runtime/descriptor PASS: https://github.com/psj216/track2-forecasting-public/actions/runs/39733727450 ; artifact 12406416612.
- All archive layers PASS: https://github.com/psj216/track2-forecasting-public/actions/runs/39734270566 ; artifact 12406307364.
- Inherited FF04 replay: https://github.com/psj216/track2-forecasting-public/actions/runs/39552405145 .
- Official ranked announcement: https://github.com/Agenthon-2026/track2-forecasting-public/issues/4#issuecomment-6301021850 .
