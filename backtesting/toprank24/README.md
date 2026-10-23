## Executive summary (read this first)
Completed exploratory conditional path forest: small exposed gain, target missed; not a submission adapter. Preserve FF03.

Training is deterministic with Python3.12.14, sklearn1.8.0, numpy2.3.5 and pandas2.2.3. Scoring uses Python3.13.16/common2.6.1 and pinned official source from report. Raw ECB source SHA checked by inherited prepare_ecb.load; use original ALPHA19 archive, not a silently updated download. The inherited input manifest lists all100 exact input units.

Completed commands from workspace root:
```bash
PYTHONPATH=audit-deps:toprank24/backtesting/toprank23/reused python toprank24/backtesting/toprank23/prepare_training.py receipts/alpha19-newdata/ecb /tmp/toprank23-training.parquet
PYTHONPATH=audit-deps timeout 120 python toprank24/backtesting/toprank24/model.py train /tmp/toprank23-training.parquet /tmp/toprank24-model.pkl toprank24/backtesting/toprank24/training-receipt.json
PYTHONPATH=audit-deps timeout 60 python toprank24/backtesting/toprank24/check.py
PYTHONPATH=audit-deps timeout 240 python toprank24/backtesting/toprank24/model.py forecast receipts/alpha19-newdata /tmp/toprank24-model.pkl receipts/toprank24-forecasts
PYTHONPATH=official:toprank24/backtesting/toprank23/reused timeout 300 /tmp/toprank23-env/bin/python toprank24/backtesting/toprank24/score.py receipts/toprank24-forecasts receipts/toprank24-experiment.json
```
Training parquet was reused byte-for-byte from TOPRANK23; its materialization command is shown for reproduction, not claimed rerun in TOPRANK24. Model.py never reads labels or previous FF03 forecasts. Scoring reads labels only after100 forecasts are completed. Model pickle contains historical training paths and is not uploaded to public GitHub or packaged into an image. Future deployment would require a distinct design/contract review, not merely placing this research pickle into a container. No additional trained candidate or post-result tuning was run.
