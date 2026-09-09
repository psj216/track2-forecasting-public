## Executive summary (read this first)

The Development leaderboard is the only public environment that injects the organizer's model
endpoint.  This repository therefore builds three images from one commit: a true Numeric-v3
control, an F4-only text candidate, and the full Phase-5 candidate.  The modes differ only in
whether the evidence interpreter is allowed to run.  Numeric parameters, seeds, output schema,
and Docker dependencies remain identical.

The current official reasoning example records a real run against
`nvidia/nemotron-3.5-lightning-30b-a3b`.  Runtime code must still use the injected `MODEL_NAME`
rather than hardcoding that string, because the organizer owns the final pin.

## Why three images

| Mode | Endpoint calls | Text adjustment | Purpose |
|---|---|---|---|
| `numeric` | none | none | Clean Numeric-v3 control |
| `f4-only` | T2-F4 only | T2-F4 only | Isolate the best-supported tail hypothesis |
| `full` | all families with usable text | all supported families | Test total reasoning uplift |

`TEXT_INTEGRATION=off` is still available as an emergency runtime kill switch, but it is not the
primary ablation.  It runs the interpreter before discarding the adjustment and therefore wastes
model budget.  `FORECAST_MODE=numeric` bypasses text reading and endpoint access entirely.

## Reproducible builds

```bash
docker build --build-arg FORECAST_MODE=numeric -t t2-dev:numeric .
docker build --build-arg FORECAST_MODE=f4-only -t t2-dev:f4-only .
docker build --build-arg FORECAST_MODE=full -t t2-dev:full .
```

Each mode is stored in both the image label `qfbench2.forecast_mode` and
`forecast_meta.json.forecast_mode`.  A score without its immutable image digest and mode is not a
usable experiment.

## Submission order

1. Submit `numeric` once and record its digest, submission identifier, aggregate score, and
   per-card scores.
2. Submit `f4-only` from the same commit and seed policy.
3. Compare F4 cards pairwise.  Keep the candidate only if the improvement is broad rather than one
   extreme card carrying the mean.
4. Submit `full` only after the F4 result is known or if the Development submission budget permits
   one predeclared broader test.
5. Use the per-card family breakdown to decide which routes enter a later deployment policy.

Do not alter prompts or coefficients between steps 1 and 3.  Doing so destroys attribution.  Do
not repeatedly probe one card or infer its sealed outcome from score movements.  Development is a
model comparison surface, not an answer oracle.

## Decision rules

The first Development pass uses conservative rules:

- F4-only must improve the F4 median and aggregate family score.
- Its F4 worst decile may not deteriorate by more than 10 percent.
- Failed or skipped reasoning calls are counted and reported; a score from mostly Numeric fallback
  does not validate text reasoning.
- Full mode must beat Numeric overall and must not erase a confirmed F4 gain.
- A family with no clear improvement remains Numeric v3 in the final router.

The public leaderboard reports per-card scores and text uplift.  Those are the appropriate
Development diagnostics.  They are not substitutes for the chronological replay gate in Phase 6;
they are the first real endpoint-backed evidence available to us.

## Local Nemotron option

Running the same public model through vLLM remains a secondary path.  A 30B-class mixture-of-experts
model is not realistic on the user's 8-12 GB Oracle VM, and a different quantization or serving
template may not reproduce the organizer endpoint closely enough for fine calibration.  Use a GPU
cloud only after the Development A/B result proves that more replay capacity is worth buying.

## Current blocker

The public repository specifies only the final step: submit an image digest to the leaderboard
portal.  It does not publish the portal URL, registry namespace, authentication method, or
submission quota.  Those values must come from the registered team's starter package or portal.
No registry target should be guessed.
