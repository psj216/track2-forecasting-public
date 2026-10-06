## Executive summary (read this first)

Frozen-prediction diagnosis only. No source model is retrained. Whole-cell outcome ledgers and draws stay in a private recovery directory; public files contain aggregate evidence. Read experiment_spec.json before interpreting anything.

Run the source audit separately for ECB, SLOOS, SPD, then ASSEMBLE. The audit requires exact recovered private archives and uses the original common-toolkit scorer. Commit and remotely verify all code, tests, specification and source hash manifests before running diagnose. The private PRE-receipt.json must contain `remote_verified`, `PRE_RESULT_INFO_FAILURE_SHA` and `frozen_implementation_hashes`; every diagnostic stage verifies that receipt and all original inputs.

For each source, run `python -m backtesting.information_failure01.diagnose --private PRIVATE --source SOURCE --stage STAGE`, with STAGE `metrics`, `curves`, `geometry`, `coefficients`. Each command writes one incremental partial and STATUS. Then use STAGE `bootstrap` with `--block release` or `--block year`, and five disjoint `--start` / `--stop` chunks 0:1000 through 4000:5000. Chunks are deterministic and existing completed chunks are reused. Finish with `bootstrap_summary`. Do not run a command longer than 10–15 minutes: wrap each invocation with timeout 600. Record any failure; stop if the same step fails twice.

After all source stages complete, `python -m backtesting.information_failure01.aggregate --private PRIVATE` publishes diagnostic summaries and exactly one next hypothesis. `python -m backtesting.information_failure01.report --private PRIVATE` renders the standalone report. No next experiment is executed. Every shrinkage or sign-only score is POST_HOC_DIAGNOSTIC_ONLY and INVALID_FOR_CONFIRMATORY_USE.

Tests live in tests/test_information_failure01.py. Set INFORMATION_FAILURE_PRIVATE to the recovered private directory to run the immutable-input checks. Discover and run affected legacy tests, full repository tests and pinned common-toolkit tests. Preserve logs and SHA metadata in the private archive. The public artifact manifest points to the private parquet by hash, never by publishing realized truth.
