## Executive summary (read this first)

**Execution stopped; research not complete. NEWINFO02_RESULT = NOT_EVALUATED.** The source-construction stage failed twice. The attached safe-long-work rule requires stopping rather than issuing a third attempt. Source selection, source-state persistence/alignment, price redundancy and the next experiment are not frozen results.

The exact parent is `16ef4d87f15151796b072e2a6f658ec076171bda`. The new branch is `track2/new-information-search-02`. Main is protected at `e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8`. No new forecasts, forecasting-model fits or CRPS calculations were made.

The outcome-free SPD state contains552 cells,59 origins and41 releases, retains both UST assets and every existing horizon, and matches the parent prediction-array hash `f3e542d86c31777c125f8020bd9df8646787dfa5215471d8d05ee99ca5ae795f`. Future yield, realized error, CRPS and oracle direction were not read as source-search inputs.

Official dated SEP and H.4.1 documents and source/version/rights documentation were acquired with URL and byte-hash receipts. The catalog covers17 source hypotheses. It is an inventory, **not a ranked Top3**. CME historical API returned401 without credentials. The actual Atlanta Fed downloadable history starts2023-03-29; its embedded license restricts use to personal and educational purposes. It cannot satisfy the required full2015/16-2024 history or automatically authorize contest/offline redistribution. CFTC report dates must not be mistaken for release dates;2023 delays require exact availability evidence. NY Fed dealer history explicitly allows revisions, while historic RRP records carry later `lastUpdated` fields. None of these limitations is a measured predictive failure.

The first construction failure came from treating the provider field `Rate: mean` as `Rate:mean`, leaving no selected rows. The second came from subtracting provider mean-rate strings before conversion. Both repairs and a focused regression test are saved. **The corrected constructor was not run a third time.** Source acquisition is preserved; no expensive download needs restarting.

No candidate has yet been shown to explain SPD better than the complete prior price-state representation. The exact old market cache was not recovered. A date-bounded official-yield proxy was prepared and labeled as a proxy; no redundancy analysis was executed. The FRED transport ignored requested date bounds, so rows were removed using date text before numerical parsing. This must not be presented as a clean prospective validation universe.

`persistence_summary.csv`, `spd_alignment_summary.csv`, `price_redundancy_summary.csv` and `source_scorecard.csv` are schema-only NOT_COMPUTED placeholders. `top3_sources.json` and `selected_primary_source.json` explicitly contain null selections. The next-experiment file is NOT_FROZEN/NOT_RUN. Do not promote any catalog entry into a model candidate.

All2020-2024 UST targets and prior cards remain research-exposed. Independent validation is NOT_AVAILABLE; this checkpoint does not justify an official submission.

Resume only at repaired source construction after acknowledging the mandatory stop. Then verify parsed source hashes, freeze/push the PRE implementation remotely, and run the already declared outcome-free diagnostics and deterministic ranking. Preserve all prior SPD predictions and all original source receipts. The recovery archive includes code, tests, logs, bounded source material, private SPD state and Git metadata.
