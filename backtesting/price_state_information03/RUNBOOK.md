## Executive summary (read this first)

This audit preserves PRICE_FULL and all parent files. Controls are diagnostic only.
Set PRICE03_PRIVATE to the new private checkpoint directory and
PRICE03_PARENT_PRIVATE to the verified parent archive's private directory.
Use Python3.13.15, common v2.4.3 and the pinned parent numerical libraries.
OPENBLAS_NUM_THREADS=1 keeps repeated small fits deterministic and bounded.

Read STATUS.json and private chunk filenames before resuming. Never repeat a
complete chunk. Preserve failure logs; fix a diagnosed step once, then stop if
that same step fails again. Commands run from the repository root.

1. Verify parent Git lineage and archive CRC/member/full hashes. Run
   `core.exact_parent_reproduction()` once; never fit PRICE_FULL.
2. Freeze experiment_spec.json, implementation, tests, PIT manifests and broader
   all-origin specification. Commit, publish, verify remote tree and PRE SHA.
   Save private pre_receipt.json with implementation and parent input hashes.
3. `python -m backtesting.price_state_information03.run controls`
4. `python -m backtesting.price_state_information03.run permutation --start 0 --stop 100`
   Repeat only missing100-rep chunks through2000. Each is bounded and incremental.
5. `python -m backtesting.price_state_information03.run random --kind A --start 0 --stop 500`
   Use A/B/C/D and missing500-rep chunks through5000 each.
6. `python -m backtesting.price_state_information03.run bootstrap --kind origin --start 0 --stop 250`
   Use origin/year/quarter and missing250-rep chunks through5000 each.
7. `python -m backtesting.price_state_information03.aggregate`
8. Research tests, affected tests, full tests, common tests; record exact paths,
   counts, exclusions and commands. Verify all parent source hashes unchanged.
9. Publish report/results, verify RESULT and critical remote blobs, parent/main,
   clean local tree. Bind final RESULT in an external receipt; no self-reference.
10. Archive code/tests/public outputs/Git bundle/private required inputs/closed
    logs and receipt. Include per-file SHA manifest, verify CRC and full archive
    SHA. Save private recovery durably. Exclude active progress logs and venvs.
