## Executive summary (read this first)

ALPHA-18 research diagnostics are separate from the unchanged V5.1 and FF03 runtimes. Public artifacts contain aggregate diagnostics and hashes, not raw future labels or forecast draws. PRE defines the bounded study and exposure constraints.

## Frozen identities and limits

- Research parent71c6ab1aa349a3cea01ca61e2b1a5f999c6b3006; retrieve the final research branch RESULT before resuming.
- Baseline47194f28d5188b87cdca1d591d86b9eeda86f7cf; archive into a separate `alpha18-baseline` directory. Never import the larger research branch as if it were this frozen production package.
- Official Track24582e957b0cbb9ea7268bec9636188a0e2c21fa; common tagv2.6.1 commit03c50a0036aaf72675d353aef4c7c01ca86d1fcf.
- Host Python3.13.16; numpy2.1.3,pandas2.2.3,pyarrow18.1.0,scipy1.18.1,jsonschema4.23.0,pytest8.4.2,ruff0.4.7. Full actual versions in environment.json. Common uses current authenticated2.6.1; image2.4.2 is a disclosed difference. The four-parquet host bridge must pass before new diagnostics.
- Maximum240seconds per evaluation command, batches saved; no full repository CI rerun is required. Inherited automatic branch CI is separate, not declared passed.

## Recover input data

Existing `input-manifest.json` freezes232 selected research inputs and source hashes. Original78 authored cards/text/panels come from pinned `alpha18-official/units`. Histories are research-projected to1/2/3/4BD, not relabeled as official short-horizon practice. The154 original ALFRED CSVs come from the authenticated R17 receipt `history/backtesting__research17__input-manifest.json`; its per-origin URL, vintage headers, size and SHA256 are preserved. Restore existing files first. If missing, re-fetch those exact historical URLs with a bounded client and verify every SHA256/header; if an upstream response differs, STOP rather than substituting revised/latest values. No token is needed. Do not rerun R17 fitting or scores.

Evaluation labels are derived solely from the two named later public panels in input-manifest.json and kept in `alpha18-private/labels-*.parquet`. No answer values, per-origin loss records or candidate draw arrays belong in this public Git branch. Original inputs and future evaluation tables are physically separate; generation code never opens labels.

## Reproduction commands

Run from a parent workspace containing this repo as `alpha18`, frozen source as `alpha18-baseline`, pinned official source as `alpha18-official`, authenticated common as `alpha18-common`, private artifacts as `alpha18-private`, original CSVs as `restored-vintages`. Install the toolkit from that pinned source with `uv pip install --link-mode copy --no-deps ./alpha18-common/common`; hardlinks are deliberately refused by its package-identity audit.

```bash
timeout 90 alpha18-env/bin/python alpha18/backtesting/alpha18/diagnostic.py bridge --repo alpha18 --baseline alpha18-baseline --official alpha18-official --work alpha18-private
timeout 90 alpha18-env/bin/python alpha18/backtesting/alpha18/diagnostic.py prepare --repo alpha18 --baseline alpha18-baseline --official alpha18-official --work alpha18-private --vintages restored-vintages
timeout 240 alpha18-env/bin/python alpha18/backtesting/alpha18/diagnostic.py forecast --repo alpha18 --baseline alpha18-baseline --official alpha18-official --work alpha18-private --start 0 --stop 78
timeout 240 alpha18-env/bin/python alpha18/backtesting/alpha18/diagnostic.py forecast --repo alpha18 --baseline alpha18-baseline --official alpha18-official --work alpha18-private --start 78 --stop 155
timeout 240 alpha18-env/bin/python alpha18/backtesting/alpha18/diagnostic.py forecast --repo alpha18 --baseline alpha18-baseline --official alpha18-official --work alpha18-private --start 155 --stop 232
timeout 90 alpha18-env/bin/python alpha18/backtesting/alpha18/diagnostic.py score --repo alpha18 --baseline alpha18-baseline --official alpha18-official --work alpha18-private
timeout 90 alpha18-env/bin/python alpha18/backtesting/alpha18/audit.py --repo alpha18 --baseline alpha18-baseline --official alpha18-official --common alpha18-common --work alpha18-private
timeout 60 alpha18-env/bin/python -m pytest -q -p no:cacheprovider alpha18/backtesting/alpha18/test_experiment.py
timeout 240 alpha18-env/bin/python alpha18/backtesting/alpha18/experiment.py generate --repo alpha18 --baseline alpha18-baseline --official alpha18-official --work alpha18-private --start 0 --stop 52
timeout 240 alpha18-env/bin/python alpha18/backtesting/alpha18/experiment.py generate --repo alpha18 --baseline alpha18-baseline --official alpha18-official --work alpha18-private --start 52 --stop 104
timeout 240 alpha18-env/bin/python alpha18/backtesting/alpha18/experiment.py generate --repo alpha18 --baseline alpha18-baseline --official alpha18-official --work alpha18-private --start 104 --stop 154
timeout 120 alpha18-env/bin/python alpha18/backtesting/alpha18/experiment.py evaluate --repo alpha18 --baseline alpha18-baseline --official alpha18-official --work alpha18-private
```

These commands are a recovery recipe, not instructions to repeat completed experiments. On resume, check successful private per-origin receipts and public hashes first. `forecast`/`generate` skip completed records; do not change seed, formula, roster, missing-target rule or fixed LOCK. Every generated array retains joint draw IDs; numerical key selection maps sampledsteps back to requested horizon positions without constructing a new model.

## Artifact interpretation

Baseline diagnostics use every observed cell and report blocked cells. Primary candidate comparison uses145 complete12-cell UST grids; separate marginal diagnostics use all1821 observed UST cells. Official metric functions are imported, but component ratios use matched empirical baseline means rather than M0 expected errors, so the proxy is not an official loss. Source input hashing, scorer tree hashing, fixture identity, PIT guards and repeated forecast checks remain separate evidence counts.

Generation batch artifacts publish a compact projection: per-origin gaps, run names, sampled steps, input/output hashes and counts. Full original command arrays remain in private per-origin receipts; their batch SHA256 and exact reconstruction code are public. Existing78 fresh-close outputs are preserved by reference, not78 new candidate executions. No new Docker run, image, registry publication, Final package or submission is part of ALPHA18.
