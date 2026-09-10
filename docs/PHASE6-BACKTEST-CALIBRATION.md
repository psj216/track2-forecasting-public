## Executive summary (read this first)

Phase 6 tests whether Phase-5 text integration beats Numeric v3 on historical public cutoffs.  It
does not assume that reasoning helps.  Evidence is generated once, validated again at replay time,
and evaluated with older cases for candidate selection and newer cases for approval.  A family
that lacks data or fails any risk guard remains rejected.

No Phase-5 family is approved by this document.  The current execution environment has no model
endpoint credential, so it cannot produce the real evidence replay required for a defensible
decision.  Synthetic tests validate the machinery, not forecast skill.  The follow-on
Public-Nemotron experiment is documented in `PUBLIC-NEMOTRON-F4-CALIBRATION.md` and must not be
described as an organizer-endpoint result.

## Evaluation flow

1. Choose historical cutoffs with later public panel observations.
2. Keep only cutoffs that already had at least one frozen text document.
3. Ask an explicitly configured OpenAI-compatible calibration model for the strict Phase-4
   evidence schema.
4. Store the validated response in a local JSONL replay.
5. Revalidate every citation and cutoff when loading the replay.
6. Generate one Numeric-v3 sample tensor per case.
7. Apply every predeclared family candidate to the same tensor.
8. Select a candidate on the oldest 60 percent of cases.
9. Approve or reject it on the newest 40 percent.

The comparison imports marginal CRPS and variogram primitives from `qfbench2-common` and the
existing public tail diagnostic.  It does not reproduce the private normalized scorer.  Reported
ratios are therefore model-selection diagnostics, not an official leaderboard score.

## Commands

With a development-only calibration endpoint configured, build an F4 replay:

```bash
export CALIBRATION_MODEL_ENDPOINT="https://provider.example/v1"
export CALIBRATION_MODEL_NAME="nvidia/nemotron-3.5-lightning-30b-a3b"
python -m backtesting.build_evidence_replay \
  --root . \
  --output calibration_outputs/f4-public.evidence-replay.jsonl \
  --cutoffs 5 \
  --n-draws 1000 \
  --family T2-F4
```

Then run calibration with enough draws to represent the F4 tail:

```bash
python -m backtesting.scenario_backtest \
  --root . \
  --replay calibration_outputs/f4-public.evidence-replay.jsonl \
  --output-dir calibration_outputs/f4-public \
  --n-draws 1000
```

The replay and results are ignored by Git.  They are reproducible calibration artifacts, not
submission inputs.  Deployment requires a separate reviewed code change after the holdout result.
The replay pins prompt version `1.0.0`, interpreter schema version `1.0.0`, and replay format
version `2.0.0`.  Loading rejects mixed model names.  A prompt, schema, model, or replay-format
change therefore requires a fresh replay.

## Candidate grid

Candidate strength multipliers are declared before evaluation:

| Family | Multipliers | Protected behavior |
|---|---|---|
| T2-F1 | 0.50, 1.00 | Adjustment remains inside the conservative cap |
| T2-F2 | 0.50, 0.75, 1.00 | Shared regime world remains bounded |
| T2-F3 | 0.33, 0.67, 1.00, 1.33 | Every marginal and tail value remains exact |
| T2-F4 | 0.50, 0.75, 1.00 | Shock mass never exceeds the Phase-5 candidate |

No parameter is fitted to the holdout.  Adding a candidate after seeing holdout performance makes
that holdout training data and requires a new untouched evaluation window.

## Approval gates

A family needs at least four training cases and four newer holdout cases.  The selected candidate is
approved only if all conditions hold:

- geometric-mean paired composite ratio is below 1.00;
- median ratio is at most 1.02;
- at least half of holdout cases beat Numeric v3;
- the holdout worst decile is at most 1.10;
- marginal degradation is at most 3 percent;
- tail degradation is at most 5 percent;
- F3 marginal and tail components remain unchanged to numerical tolerance.

These are initial risk controls, not laws of nature.  They may be tightened after more cases are
available.  Loosening them after a failure would be metric shopping and should trigger a new
holdout.

## Current data limitation

On the current public snapshot, five evenly spaced candidate cutoffs produce 30 cutoff-safe text
replay opportunities: 24 F4, three F2, two F3, and one F1.  This is enough to begin F4 evaluation
but not enough to approve F1 through F3 under the minimum-case rule.  More historical text or an
additional organizer-provided practice units are needed for those families.  External market data
is not an acceptable substitute under the competition contract.
