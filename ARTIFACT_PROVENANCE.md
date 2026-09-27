## Executive summary (read this first)

V7 extends the opt-in V5.1 baseline with a static, dated Fed/BLS/ECB event
catalog. Its records contain release text or bounded excerpts, observable event
features, source links and checksums. They contain **no response paths or price
series**. The F2 engine reconstructs matured event responses from the unit's
mounted panel at runtime and uses a small reliability-weighted empirical sleeve.
F1/F3/F4 retain their V5.1 forecast. This is an experimental research mode,
not a claimed leaderboard improvement or automatic submission.

V7's builder is `tools/build_v7_catalog.py`. BLS CPI and Employment Situation
vintages come from the official news-release archive indexes; ECB policy
decisions come from the official older index and the year-specific HTML listing
fragments. Fed statements and separately released minutes reuse the checksum-
bound V6 input. BLS publication dates are cross-checked with their release
mastheads. The `data/v7/catalog_manifest.json` records the catalog version,
parser and schema versions, index hashes, event counts and source exclusions.
`data/v7/index.json` holds only dates, record paths and checksums; future record
contents are not opened at inference. Each historical response's final panel
observation must precede the forecast cutoff. CPI and payroll release changes
are **not** labeled as forecast surprises without an as-of consensus source.
Historical source fetches happen at build time only; inference runs offline.

V6 packages an external historical event library containing official Federal Reserve
Board text, publication dates, deterministic semantic features and source checksums.
There are no prices, forecast outcomes, Development scores, unit-specific rules,
pretrained neural weights or fitted forecasting parameters in this library.

Source policy: Track 2 ARTIFACT-POLICY.md revision 2026-09-21.1 permits static
retrieval assets subject to each task's cutoff and the no-answer-lookup rule.
Official source: https://www.federalreserve.gov/monetarypolicy/fomc_historical.htm
Usage basis: United States federal government work, Federal Reserve Board publications.

Each record in data/v6 has the source URL, raw source SHA-256, extracted-text SHA-256,
retrieval timestamp, explicit publication date, document type and meeting episode.
The index binds every record to a feature-file SHA-256. The deterministic builder is
versioned with this code; it downloads only statements and publicly released minutes.
Meeting dates are never substituted for the later publication dates of minutes.
Transcripts and delayed archival staff materials are excluded.

At runtime the catalog loader checks the date-only index before opening a record.
Its returned subset contains only documents published by the task's as-of. Candidate
responses and pre-event volatility are calculated exclusively from the current unit's
mounted panel. Every full historical response must end before its prediction cutoff.
The pseudo-asof replay repeats these cutoffs, and chronologically disjoint events
separate candidate selection from validation. All scoring calls delegate to the
pinned common toolkit; paired local ratios are not official normalized scores.

The current catalog covers Federal Reserve communications, not a comprehensive global
shock archive. Unknown issuers, sparse events and failed validation can return the
exact V5.1 baseline. A large document count does not establish independent support.
The build report records coverage and any sources rejected during collection.

V6's numerical selection is performed within the unit at runtime on its pre-cutoff
panel. No globally fitted forecasting weights are bundled. Pure code and static
retrieval assets are disclosed here; any future fitted artifact needs its own
training/selection cutoff and models[] entry. No official submission is automated.

Frozen catalog build: 456 discovered URLs, 455 downloaded documents, 353 retained
feature records and 102 documents without a qualifying fingerprint. One source with
conflicting release-date metadata was excluded. Both construction and runtime use
the same bounded text excerpt. Rebuilding requires beautifulsoup4==4.12.3; inference
does not need Beautiful Soup or network access.
