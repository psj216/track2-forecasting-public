## Executive summary (read this first)

A shared numerical portability defect is reproducible in both frozen images. It does not overturn the exact paired 22-card score equality on the original execution. It prevents a claim of byte-exact reproducibility across all x86_64 runner environments. No production repair was made.

## Observations

The main 22-card replay completed 44 forecasts and six same-runner FF03 repeats with exact byte identity. A separate resource job replayed `t2-F4-curve-ust3m-008-ps1` using the same official input commit, image IDs, seed 17 and 1,000 draws. Both candidates remained byte-identical to one another, but 13 of 2,000 numeric values differed from the main run (maximum absolute difference 0.06308603200308704 percentage points). Metadata was unchanged; parquet and rationale changed.

One bounded follow-up on a single AMD EPYC 7763 runner ran the original twice and FF03 once normally. All three exactly matched the main batch. Disabling AVX512F, AVX2 and FMA3 for diagnostic processes changed both candidates' output identically. Eight of 2,000 values changed, with the same maximum absolute difference. No score was used to choose either environment, and neither environment override is added to a release image.

Numeric fingerprints show 456 state-matched block starts with identical pool members but a different order. The source uses `np.argsort(distance.to_numpy(dtype=float))` without specifying stable tie ordering. Changing CPU feature dispatch on one runner reproduces the ordering change and fixed-seed draw change. This is sufficient evidence of a common numerical portability risk. It is not proof of the complete cause on the earlier resource runner: that runner's CPU features were not captured, and its numeric values are not exactly reproduced by this one toggle.

## Release consequences

- Same-runner repeat determinism: demonstrated in the tested cases.
- Original versus FF03 under the same environment: exact in all tested comparisons.
- Universal cross-runner byte determinism: FALSE for the observed resource replay.
- FF03-only regression or asset routing defect: not found.
- Practice A/B raw score table: still describes its frozen execution, not all possible machine implementations.
- Remediation would require an explicit canonical tie-break, its RED test and a separate release candidate. It could change legacy daily draws, so it cannot be silently called byte-preserving. This task preserves both immutable candidates and does not change forecasting semantics after seeing scores.

Receipts: main run 39552405145, resource run 39552900342, portability run 39553274096. Full commands, runtime fingerprints, hashes and retained RED evidence are in the corresponding results JSON and Actions artifacts.
