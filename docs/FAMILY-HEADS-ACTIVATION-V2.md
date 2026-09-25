## Executive summary (read this first)

Activation v2 narrows F2/F4 text to four required JSON fields and validates
complete House transport and changed historical-world draws before any official
submission. F1 and F3 still use Numeric V3. This branch is an activation
experiment; no public Nemotron response has been observed in the Codex runner.

### Why identical scores were possible

The previous workflow ran every container with `--network=none`, then asserted
`family-heads == numeric` across every family. That was a valid fallback test
but could not prove any House-assisted forecast changed. The older router
required six exact JSON keys and its F2/F4 multi-asset decisions had no
`direction_asset` wire, so even a parsed multi-asset decision returned V3.
Identical official scores do not by themselves prove which failure occurred:
only per-unit runtime metadata or an actual endpoint replay establishes that.

### New input and safety gates

The model returns `regime`, `direction` (-1/0/+1 for the quoted asset),
`confidence` (0..1), and `evidence` (provided, pre-as-of document IDs). Optional
`tail_side` and `horizon` default from direction and the shortest horizon.
Multi-asset responses also require an explicit `direction_asset` equal to a
provided asset ID; ambiguity keeps the exact V3 worlds. Minor casing, signed
integer strings and numeric confidence strings are normalized. Unknown fields,
unknown evidence IDs, unsafe asset IDs, low confidence and continuation remain
closed. Python, not the LLM, sets shock sizes and the 15%/10% maximum sleeves.

### CI activation proof and its scope

A tiny localhost server responds with minimal, grounded JSON over the actual
HTTP transport. The CI container receives `MODEL_ENDPOINT`, `MODEL_NAME`, and
`MODEL_TOKEN` through environment forwarding, calls
`$MODEL_ENDPOINT/v1/chat/completions`, validates the returned document ID and
changes the forecast. `backtesting.activation_probe` compares the Parquet
forecasts with the same frozen-seed Numeric V3 and requires all six stages
`endpoint_configured`, `call_succeeded`, `parse_succeeded`,
`validation_succeeded`, `gate_passed`, and `samples_changed` to be true for both
F2 and F4. It also tests a multi-asset F2 and multi-asset F4 card. The existing
offline exact-parity test stays; F1/F3 remain frozen.

The localhost reply is synthetic. A passing CI proves the code can activate;
it does not prove the House service returns a compatible decision, nor that
forecast scores improve. Do not upload this branch to CodaBench on CI alone.

### Actual Nemotron check

The Codex runner has none of `MODEL_ENDPOINT`, `MODEL_NAME`, or `MODEL_TOKEN`,
and cannot access the per-submission House origin from outside its harness.
Use the organizer House route or an authorized public Nemotron-compatible
provider. Configure the three environment variables privately in your terminal,
never in a command line, Git commit, prompt, or output file. If using a public
provider, `MODEL_ENDPOINT` must be the API origin (or origin plus `/v1`),
`MODEL_NAME` that provider's served model, and `MODEL_TOKEN` the credential.
The proxy result proves behavior only for that provider; platform behavior must
still be checked from its per-unit metadata.

From this branch with Python 3.13 and the pinned dependencies installed:

```bash
python -m backtesting.activation_probe --mode live \
  --out /absolute/path/outside/repo/activation-live
```

The command exits nonzero unless one F2 and one F4 actually produce a changed
forecast and all six stages pass. `activation-results.json` stores stages and
reasons without credentials or raw model text. For Windows PowerShell, pass a
Windows absolute path to `--out` instead. A continuation decision or uncertain
evidence correctly fails this smoke check; it must not be misreported as a
transport failure. If no live endpoint is available, wait for endpoint access
rather than bypassing the activation gate.
