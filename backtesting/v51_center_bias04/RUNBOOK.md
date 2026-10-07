## Executive summary (read this first)

Original forecasts and source bytes stay frozen. All location transformations are RESEARCH_DIAGNOSTIC_ONLY. No submission. Full-ledger bias uses all 2001–2024 cells; chronological score/capture uses the complete inherited 2010–2024 fold test universe.

Set BIAS04_PRIVATE to a verified private recovery directory, use Python3.13.15 and common v2.4.3. Run from the repository root. Only new files in this audit directory, its report and its tests may change. No features.npy, price, text or macro predictors are loaded.

1. `python -m backtesting.v51_center_bias04.setup`: outcome-free metadata/hash audit and fixed specification. Parent narrow reproduction must already match.
2. Run synthetic/source research tests. Commit implementation and specification, publish, verify PRE remotely. Save private pre_receipt.json with implementation/source hashes and verified PRE. No broader truth deserialization before this receipt.
3. `python -m backtesting.v51_center_bias04.run construct --start 0 --stop 250`: use consecutive 250-origin stages through1250, internally25-origin checkpoints. Never recompute completed chunks.
4. `python -m backtesting.v51_center_bias04.run merge`, then `chronological`: original draws/shared scorer, train-only historical signs and median. Four incremental folds.
5. `python -m backtesting.v51_center_bias04.run oracle --universe full --kind GLOBAL_ORACLE_BIAS`: each of five fixed oracle kinds for full and eval separately. Each group writes a checkpoint. Never transfer oracle values into predictive pipeline.
6. `python -m backtesting.v51_center_bias04.run controls --kind 0 --start 0 --stop 2000`: kinds0–3;100-replicate checkpoints. Training-year shuffle is within historical years, never a future-fit reassignment.
7. `python -m backtesting.v51_center_bias04.run bootstrap --kind origin --start 0 --stop 5000`: origin/year/asset;250-replicate checkpoints.
8. `python -m backtesting.v51_center_bias04.aggregate`: fixed gates, complete diagnostic tables. Then report script; no tuning or candidate creation.
9. Research→affected→full→common tests. Preserve any failure. Old tests asserting an earlier branch must be recorded as inapplicable, not edited. New tests protect current branch/main and all parent bytes.
10. Commit report/results, publish and verify remote tree/critical files/lineage/main/clean. Final RESULT binding lives in external receipt to avoid a self-referential hash.
11. Complete Git bundles must be clone-tested. Create private recovery containing canonical original draws/ledger, results, source hashes, code/tests/report, closed logs, CRC/member hashes and full archive SHA. Save durably and verify.

Every command has a finite 600–900second timeout. STATUS plus private chunk filenames identifies continuation. Preserve logs; one diagnosed fix allowed, stop if same step fails twice. No completed scientific work is restarted.
