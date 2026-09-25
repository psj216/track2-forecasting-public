## Executive summary (read this first)

This opt-in candidate keeps Numeric V3 as its anchor and routes grounded House
text into bounded historical-world mixtures for F2/F4. F1 calibration is available
but inactive unless an earlier, admitted fitted configuration is explicitly
provided. F3 is unchanged. This is an experimental A/B candidate, not a proven
score improvement or a confirmed repair of a live House failure.

### Runtime

Build with `docker build --build-arg FORECAST_MODE=family-heads .` or set
`FORECAST_MODE=family-heads` locally. Default draws remain 500 for a clean comparison.
`TEXT_INTEGRATION=off` restores the exact numeric anchor. Legacy modes remain
unchanged. F1 may use `F1_CALIBRATION_PATH`; fitted labels must end before the
forecast as-of. No fitted parameters are baked into this candidate.

The House caller uses only MODEL_ENDPOINT, MODEL_NAME and MODEL_TOKEN. The
injected origin is extended to /v1/chat/completions, with Bearer authentication.
One bounded request asks for regime, direction, confidence, tail_side, horizon,
and eligible evidence document IDs. Direction refers to the actual quoted target,
not generic currency strength. The model does not supply numerical forecasts.

### Historical worlds

F2 selects complete past paths whose target change has the requested direction.
F4 selects complete past paths in the requested empirical 5% tail. These are
numerical direction/tail labels; no claim is made that an unlabeled historical
block was caused by the same policy or inflation event described in the text.
Confidence must be at least 0.65. Allocation rises linearly from zero at 0.65 to
15% for F2 or 10% for F4 at confidence one. These caps are conservative experimental
constants, not fitted or validated optimal weights. The remaining draws are V3.
Keeping V3 in the mixture does not guarantee a score floor.

Only histories dated through as-of are eligible. All assets/horizons in a replaced
draw share one actual contiguous historical trajectory, with current level anchor
or summed log-return as appropriate. Sparse support, missing evidence, unsupported
target types, ambiguous multiasset direction, continuation and low confidence keep
V3 exactly. Multiasset cards are intentionally not changed by this first router.

### Diagnostics and limits

forecast_meta.json stores `family_heads.router`: endpoint_configured,
call_attempted, call_succeeded, parse_succeeded, validation_succeeded, gate_passed,
samples_changed, reason, HTTP status, finish reason and token counts. Standard
output emits the same safe ledger. Never log credentials or response bodies.

A successful parse is distinct from an applied forecast change. Synthetic tests
verify transport shape and a real historical sampler through the CLI; offline
Docker tests verify official gates and exact numeric fallback. Neither proves
live House availability or predictive alpha. Obtain the official result together
with this ledger before deciding whether the text specialist is useful.
