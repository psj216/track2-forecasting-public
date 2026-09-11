## Executive summary (read this first)

This experiment asks one narrow question: does Phase-5 F4 text integration beat Numeric v3 on a
public historical holdout when evidence is extracted by a public Nemotron proxy?  It is not an
official organizer-endpoint test.  The structure is complete, but no external model has been
called and no performance decision exists yet.  Until a credentialed proxy replay clears every
frozen guard below, F4 remains unapproved and submission behavior does not change.

## Experiment identity

The result name is **Public-Nemotron proxy calibration**.  The expected development model is
`nvidia/nemotron-3.5-lightning-30b-a3b`, supplied through
`CALIBRATION_MODEL_NAME`.  The provider URL is supplied through
`CALIBRATION_MODEL_ENDPOINT`.  An optional bearer token is read from
`CALIBRATION_MODEL_API_KEY` and is never written to replay or report files.

The official runtime continues to use `MODEL_ENDPOINT` and `MODEL_NAME`.  The forecast command
does not read any `CALIBRATION_MODEL_*` variable.  A positive proxy result therefore means only:
"Public-Nemotron proxy historical holdout improved."  It still requires organizer-endpoint
validation.

## Frozen protocol

| Item | Frozen value |
|---|---|
| Family | `T2-F4` only |
| Replay cases | 24 public F4 units, one cutoff-safe case per unit |
| Candidate-selection split | Oldest 60%, with same-date cases grouped |
| Untouched holdout | Newest 40%, with same-date cases grouped |
| Expected grouped counts | 14 training cases and 10 holdout cases |
| Candidate multipliers | `0.50`, `0.75`, `1.00` |
| Final draws | 1,000 |
| Prompt version | `1.0.3` |
| Evidence schema version | `1.0.0` |
| Replay format version | `2.0.0` |
| Seed inputs | unit id, cutoff, family, draw count, fixed salt |

The 24 opportunities were counted from the current repository.  Each F4 unit contributes its
latest cutoff-safe point among the five predeclared pseudo-asof candidates.  This avoids treating
many adjacent days from one episode as independent evidence.  The grouped chronological split
places 14 cases through 2018-10-31 in candidate selection and 10 cases from 2020-01-15 onward in
the untouched holdout.

## Replay and calibration commands

Set secrets only in the process environment:

```bash
export CALIBRATION_MODEL_ENDPOINT="https://provider.example/v1"
export CALIBRATION_MODEL_NAME="nvidia/nemotron-3.5-lightning-30b-a3b"
export CALIBRATION_MODEL_API_KEY="..."  # omit for local vLLM

python -m backtesting.build_evidence_replay \
  --root . \
  --output calibration_outputs/f4-public-nemotron.evidence-replay.jsonl \
  --cutoffs 5 \
  --n-draws 1000 \
  --family T2-F4

python -m backtesting.scenario_backtest \
  --root . \
  --replay calibration_outputs/f4-public-nemotron.evidence-replay.jsonl \
  --output-dir calibration_outputs/f4-public-nemotron \
  --n-draws 1000
```

The builder writes atomically only after validated responses are available.  Missing settings,
network failures, malformed JSON, unknown citations, future citations, stale prompt/schema/model
provenance, or a failed F4 case stop approval.  Historical outcomes never enter the model prompt.

## Approval gate

The candidate selected on the older 60% is approved only if the newer holdout meets every rule:

- geometric-mean paired composite ratio is below `1.00`;
- median paired ratio is at most `1.02`;
- win rate is at least `50%`;
- worst-decile paired ratio is at most `1.10`;
- marginal component ratio is at most `1.03`;
- tail component ratio is at most `1.05`.

Numeric v3 is always `1.00`.  F1-F3 cannot be approved by this experiment.  Adding candidates
after viewing the holdout converts that holdout into training data and requires a new untouched
window.

## Current result

| Field | Result |
|---|---|
| Replay generated | No |
| External calls made | 0 |
| Candidate selected | Not available |
| Holdout metrics | Not available |
| Decision | **REJECT / NOT EVALUATED** |
| Deployment changed | No |

The limitation is blunt: structural tests can prove leakage controls and reproducibility, but
they cannot prove text uplift.  Model access is the remaining dependency.
