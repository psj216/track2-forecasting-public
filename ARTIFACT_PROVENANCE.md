## Executive summary (read this first)

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
