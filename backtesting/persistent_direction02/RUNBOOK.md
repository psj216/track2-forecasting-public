## Executive summary (read this first)

Resume only the first incomplete stage in STATUS.json. Never read private outcomes before the remote PRE receipt exists. Private labels, draws and cell losses are never added to Git. Use Python3.13 and the pinned common v2.4.3 scorer. No submission or next experiment is executed.

Source acquisition: `python -m backtesting.persistent_direction02.audit_source PRIVATE --start A --stop B`. Existing original bytes are reused. Acquisition succeeded; original PDF extraction stage failed once, was diagnosed and corrected with deterministic Poppler layout and leading-decimal parsing. Corrected source verification succeeded. Do not repeat that work.

Source-only design: `calendar.build(PRIVATE)`. Synthetic/source tests: `pytest tests/test_persistent_direction02.py`. Freeze hashes/spec, commit, push and verify remote PRE. Preserve the private PRE receipt.

Evaluation commands, each bounded by timeout600: `python -m backtesting.persistent_direction02.evaluate prepare PRIVATE`; `fold PRIVATE --year YEAR` for2020–2024; `score PRIVATE`. Existing fold files are resumable; do not regenerate completed folds.

Controls: `control PRIVATE --kind STATE|DATE|RANDOM --start A --stop B`, chunks100–250 until2000 each. Bootstrap: `bootstrap PRIVATE --kind release|year|week --start A --stop B`, chunks1000 until5000 each. Each chunk writes a durable artifact and STATUS. Aggregate: `python -m backtesting.persistent_direction02.aggregate PRIVATE`.

Run research, actual affected package, full repository and common toolkit tests. Verify unchanged protected files/main. Commit/push results and compare remote critical blobs. Final external receipt binds PRE/RESULT to the CRC/member/full-SHA verified private recovery ZIP. Save the ZIP and receipt durably. If the same execution step fails twice, stop and preserve a verified checkpoint rather than loop.
