## Executive summary (read this first)

Reproduce the locked 22-card actual Docker comparison without modifying any forecast implementation. Use the source and artifact IDs frozen in spec.json. Forecasts see only the selected official unit, never the answer directory. Official scoring happens in a separate container afterwards.

## Reproduction

1. Check out this branch's executable e774e9bdea9a689995614a063efddce894e7b054, official Track 3b51e16b3f7c0fa0e56bcba323c2bb5e81b8bd56 and common 03c50a0036aaf72675d353aef4c7c01ca86d1fcf in independent directories.
2. Download FF03 artifact 12003002655 from run 38798442114. Authenticate candidate-image.tar.gz with SHA-256 df232487177cb56cb0ae945b2613fbbebbb24eff702f21712662e589d04f636c. Load it with `timeout 120 docker load -i candidate-image.tar` after decompression. Image ID must be sha256:23f226ced859978d7a3f16a23c6d1515a1a3bdb14338297f4818d114bcfa2c1c. This is a config/image ID, not a published registry manifest digest.
3. Anonymous-pull the exact original immutable digest in spec.json with `timeout 150 docker pull --platform=linux/amd64 IMAGE`.
4. Each completed batch has immutable receipts. Resume an interrupted batch with the same output directory; the runner checks input hashes and image identity before reusing receipts. Do not rerun completed batches merely to recreate numbers.

```bash
timeout 360 python3 backtesting/finalfit04/replay.py --official official-current --common common-current --out /tmp/ff04-batch-0 --batch 0
timeout 120 python3 backtesting/finalfit04/score.py --official official-current --common common-current --out /tmp/ff04-batch-0
```

Batches are 0–5, partitioning the frozen roster by stride six. The Actions workflow handles restoration and uploads full forecasts, inspect output and per-process stdout/stderr. The raw practice answers stay solely in the separate official checkout and are mounted only in scorer containers.

After authenticating and extracting all six evidence ZIPs under an external EVIDENCE directory, run with Python 3.13 and pinned NumPy2.1.3/pandas2.2.3/pyarrow18.1.0/common2.6.1:

```bash
timeout 120 python backtesting/finalfit04/aggregate.py --evidence EVIDENCE --official official-current --out .
```

This post-processing calls official metric functions; no duplicated scoring math or training is used. It verifies the official CLI component values before emitting asset/horizon slices. It never edits forecasts. Extra resource and portability workflows are separate from the original locked 22-card score table; their results do not replace it.

## Preserved boundaries

No protected source/image changed, no registry push, no credentials requested, no ZIP generation and no CodaBench submission. Public raw scores are not normalized leaderboard scores. The historical score 0.9541 is not attributable to the safe image without additional evidence. ALPHA18 is not imported.
