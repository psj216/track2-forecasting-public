## Executive summary (read this first)
Frozen M0-HEDGE-10 research, NO_GO. All production code remains separate. No label files included.

m0.py reconstructs published distributions/scales and the fixed whole-row mixture. validate.py runs input-only checks. evaluate.py imports official losses and evaluates recovered Practice outputs; evaluate_ecb.py scores completed2025 Docker outputs. prepare_ecb.py truncates exact-hash public ECB history; run_ecb.py mounts one unit per archived FF03 container. falsify.py computes fixed origin-block checks. export_adapter.py is unpromoted and has an unresolved reused-output audit-file failure recorded in host-candidate-contract.json.

Use Python3.13, numpy2.1.3,pandas2.2.3,pyarrow18.1.0,scipy1.15.3,jsonschema4.23.0 and pinned common2.6.1. Put official3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56 and this directory on PYTHONPATH. Each command must have a timeout <=600sec. Exact execution commands are represented in workflow finalalpha19-ecb.yml and source argparse/main entrypoints. Recovered completed experiments must not be rerun merely to resume final reporting.

Results CSVs include all complete cards, raw/native-unit components, input-only scales, normalized components, scores and output/label hashes. Raw values are not pooled across units. Full group tables are in results/falsification.json; incomplete grids retained in results/ecb2025-summary.json. Labels and complete historical source files remain outside this repository. Synthetic research cards are not official Final metadata.
