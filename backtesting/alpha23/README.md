## Executive summary (read this first)
ALPHA23 is complete: REGRESSION. Source, frozen weights, hashes, full paired scores and evidence are preserved. Do not retune or promote.

Runtime for training/evaluation: Python3.13.16,numpy2.1.3,pandas2.2.3,scipy1.18.1,pyarrow18.1.0,common2.6.1. Exact FF03 runner usesPython3.13.15/common2.4.2. Both FF03 and candidate forecasts use that same archived runtime; scoring is separate pinned official implementation. Dependencies listed here do not imply a new release image.

The engine combines conditional_mean,conditional_volatility and joint_generator in engine.py. Separate modules handle observable features, date-safe policy signals, dataset assembly, inference and evaluation. Reused m0.py/loss_helpers.py are byte-preserved ALPHA19 published-formula reconstruction/official loss import helpers; old hedge code is never called.

Reproduction from workspace root after restoring pinned official repository and source snapshots:
```bash
python alpha23/backtesting/alpha23/acquire.py
python alpha23/backtesting/alpha23/training_data.py official receipts/alpha23/raw receipts/alpha23/data
python alpha23/backtesting/alpha23/engine.py receipts/alpha23/data /tmp/reproduced-alpha23-weights
python alpha23/backtesting/alpha23/prepare_inputs.py receipts/alpha23/data receipts/alpha23/inputs
python alpha23/backtesting/alpha23/tests/check.py
```
Do not overwrite frozen weights to reproduce. Source fetches may change bytes; compare manifest hashes. Exact archived forecasts are in Actions40008576484 artifacts identified by ALPHA23-DOCKER-RECEIPT.json. Original panel pinned at official3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56, units/t2-F2-curve-ust6m-004-ps1/rates_daily.parquet. Treasury2023is missing, never filled. All historical inputs are truncated before forecasting. Training matrices and target values remain outside Git and outside forecast mounts.

Completed recovery/evaluation commands:
```bash
python alpha23/backtesting/alpha23/recover_inputs.py receipts/alpha23 receipts/alpha23/recovered
OPENBLAS_NUM_THREADS=2 PYTHONPATH=official python alpha23/backtesting/alpha23/evaluate.py receipts/alpha23/recovered receipts/alpha23/artifacts receipts/alpha23/experiment-recovered.json
```
Do not repeat already successful forecasts. Recovered metadata is byte-verified against each runner receipt and retains original numeric prices and policy signal values. An evaluation score is not a deployable adapter or an official Final result. Candidate production routing, monthly fallback and full22release tests are NOT_RUN because the improvement gate failed.
