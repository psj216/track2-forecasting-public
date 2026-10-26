## Executive summary (read this first)
Frozen historical examination of the exact FF03 image. No model tuning or Final score inference.
Meeting dates: 2022-06-15, 2023-03-22, 2024-09-18, 2025-09-17, 2026-09-16.
Each event origin is two US federal-holiday-adjusted business days before its meeting.
Controls: pseudo-event dates 15 and 10 such business days before each meeting; their origins are two days earlier. These windows do not include a scheduled FOMC decision. CPI, payroll and minutes days are not excluded or relabelled using outcomes.
Inputs: up to 504 earlier market observations per tenor. Treasury annual tables, FRED H15 series, or inherited official panels; never interpolate future data. All published nominal par curve maturities with finite origin value and >=120 past observations qualify; common aligned history must have >=120 rows. Newly introduced tenors without this history are excluded and logged.
Policies: the preceding FOMC statement and its minutes, only when published by the origin's New York close. Verified release times are 14:00 America/New_York; available_at is recorded from official publication notices; downloaded historical body vintage is not authenticated.
Sources without certified historical vintages are LIMITED_RECONSTRUCTION, never independent OOS. Historical research and October 2026 image construction make these retrospective results non-independent even with cutoff-safe runtime inputs.
Models: immutable FF03; FF03 text removed (same metadata, numeric inputs, seed); original V5.1 image if accessible and compatible; deterministic flat and zero-drift Gaussian random walk with 60-observation covariance, 10% diagonal shrinkage. No fitted hyperparameter selection.
Horizons: 1..4 business days; 2000 scenarios; seed 318. F3 joint UST card. No conversion to policy-decision probabilities.
Protocol: write predictions and SHA256, save per-origin checkpoints; finish all origins before opening evaluator truth. Model containers receive only the per-origin read-only input. Evaluator is a later stage, and checks hashes before scoring.
Metrics: directional accuracy excludes exactly unchanged truth; flat comparator ties abstain. Median MAE and paired improvement; official fair ensemble CRPS imported from toolkit v2.6.1; equal-tail 50/90% coverage and width; absolute origin-to-horizon move >=10bp probability and Brier score. bp comparisons use tolerance 1e-9. Report cell-weighted pooled and per-origin results; dependent cells are not independent trials.
Gaussian innovations share one path per scenario. Flat and Gaussian produce the same complete grid. Missing target dates exclude those cells, not silently shift the horizon. Report every exclusion and failure.
A/B: byte equality, ordered draw equality, max absolute difference and text-router ledger.
No outcome files or scores committed to public source. Full data, outputs and reports are outside the source tree.
No image rebuild/push, Team Key, packing or CodaBench access.
