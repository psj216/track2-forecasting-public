## Executive summary (read this first)

Four fixed monthly assertions failed on the actual original image and passed unchanged on the isolated candidate. RED checkpoint: `696c938c7e5ca6dd831a3037c8eabbd40c32bdab`. Candidate checkpoint: `9108ba25737dc88fcdeb478d45c749dddc2bbcb0`.

| Finding | Original reproduction | Classification | Severity / Final scope |
|---|---|---|---|
| Explicit periods ignored | monthly-a versus monthly-b changes periods/steps but original parquet is identical | HORIZON_HANDLING | High for monthly cards requiring explicit metadata; actual new Final macro schema UNKNOWN |
| Monthly h1–h4 collapse | all four output cells have the same distribution despite requested steps 1–4 | HORIZON_HANDLING | Semantically wrong, although output grid/schema and exit 0 are valid |
| Missing mapping accepted | monthly-missing exits 0 | HORIZON_HANDLING | Silent unsupported assumption under current monthly contract |
| Conflicting mapping accepted | card versus forecast_spec conflict exits 0 | INPUT_SCHEMA_MISMATCH / HORIZON_HANDLING | Silent inconsistent input acceptance |
| Missing history | both original and candidate exit 1: insufficient overlapping rows | MISSING_HISTORY | Correct explicit refusal; no output/fallback fabricated |
| Sentinel validation error | initial validator checked /input directory basename instead of card identity | Audit tool error, not production DATE_OR_CUTOFF bug | Original parquet invariant; candidate probe validates filtering, still marks input cutoff invalid |
| First run setup | container UID-created folder not writable by Actions host; fixture task IDs lacked t2- prefix | DEPENDENCY_OR_CONTAINER / test INPUT_SCHEMA_MISMATCH | Tool-only fixes; first failure evidence preserved |

Root functions: original cli.main ignores forecast_spec; numeric_v1.forecast_numeric uses ceil(horizon / inferred observation period); text_first_v5 applies the same approximation. The new official helper requires observation-month gaps from the actual panel anchor, including publication lag. High confidence in this reproduced defect; no claim about CodaBench scores or future Final results.

The isolated adapter loads the unmodified official helper (Git blob 04650003bac311fd5c0cee7cb2c8d17484ddcbe6). It translates resolved monthly steps into the existing numeric/text sampling interfaces while retaining output keys, all model constants and daily behavior. It verifies actual numeric observation steps, writes a specific receipt and refuses conflicting/missing mappings. Mixed cadence or different per-asset monthly step grids are refused; they need separate validation. No original production file was edited.

Baseline source/image parity was checked again inside the candidate run. Repair is a read-only overlay executed in Docker, not a newly baked deployable image. No performance improvement follows from these tests.
