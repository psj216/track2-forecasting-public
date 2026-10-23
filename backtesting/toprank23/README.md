## Executive summary (read this first)
Completed negative research result. Do not tune or deploy. Original FF03 remains selected.

`reused/` contains byte-for-byte ALPHA19 helpers from commit79983b1343e98088c51889600503329edf757557. Only reconstruction/scoring/loader functions are used. Old hedge functions are NOT invoked. No new scoring formula was written. Official package must be pinned as recorded in TOPRANK23-REPORT.md.

Commands from workspace root (paths may be relocated):
```bash
PYTHONPATH=backtesting/toprank23/reused python backtesting/toprank23/prepare_training.py PATH_TO_ECB_ZIP /tmp/train.parquet
python backtesting/toprank23/model.py train /tmp/train.parquet backtesting/toprank23/weights.json
python backtesting/toprank23/model.py forecast PATH_TO_INPUT_ROOT backtesting/toprank23/weights.json /tmp/forecasts
```
The completed run used Python3.12.14 for training/generation, and Python3.13.16/common2.6.1 for scoring. Exact versions and input hashes are preserved. Do not overwrite frozen coefficients on recovery. Scoring script expects separate receipts folders documented by source; labels are never read by model.py. No output Docker adapter or monthly contract was developed because the performance gate failed.
