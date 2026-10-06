# DIRECTION-TO-LOCATION-01

Executive summary: use only the exact frozen SPD cross-fit sign to translate the
original V5.1 distributions by 0.10 of their original SD. No refitting, new
source, outcome-dependent feature generation, threshold search or submission.

The source universe is immutable: 552 cells, 59 origins, 41 releases,
UST_2Y/UST_5Y, five original horizons and all five years including 2023.
`results/experiment_spec.json` freezes every scientific decision before scoring.
Individual outcomes, draws, predictions and loss arrays remain private.

## Restart procedure

Use the recovered pinned Python environment and set `DTL01_PRIVATE` to the
private recovery directory. Run the audit and research tests first. Commit and
remotely verify PRE before creating `PRE-receipt.json`; evaluation rejects an
absent receipt or changed implementation/input hash.

Run `python -m backtesting.direction_to_location01.evaluate --private PATH
--stage primary`, then `secondary`. Run each control kind in 500-replicate chunks
using `--stage control_chunk --kind KIND --start N --stop N+500`, then
`control_summary`. Run both release/year bootstrap types in 1000-replicate chunks
using `--stage bootstrap_chunk --block TYPE --start N --stop N+1000`, then
`bootstrap_summary`. Completed private chunks are reused, not recomputed.

Run `finalize` and `report` modules with `--private PATH`. Check STATUS and
preserve logs after every stage. Each execution is bounded to ten minutes.
Stop after a repeated failure; never change a scientific rule to rescue a score.
Run research, affected, full repository and common toolkit tests in that order.
Verify remote RESULT, parent lineage, main and clean working tree. Create and
CRC/SHA-256 verify a private recovery archive with per-file hashes.

The date null is deliberately a safe delayed date-mapping control; its
coverage and exact definition are reported. It never silently introduces a
refitted SPD forecast. Secondary 0.05/0.20 and OOD3 are diagnostics and cannot
replace the primary or override a failed control gate.
