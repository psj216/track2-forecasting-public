## Executive summary (read this first)

**Verdict: NO.** The precommitted primary structure + text logistic router scores **1.007942** against B0=1. It fails to beat either structural baseline and worsens multi-card safety. The two-expert oracle scores **0.953566**, so expert selection has real descriptive headroom. The best fixed secondary text-only Ridge scores **0.957520**; that improvement is retained, but cannot replace a failed primary or establish a confirmed text signal without its own acceptance-level controls.

The answer to the primary question is: **incremental predictive routing information from card text beyond simple structural metadata was not established.** This is not evidence that every possible text router must fail. No architecture, expert, correction magnitude or new location alpha was created.

All 24 cards were previously exposed: 63 cells, 13 single and 11 multi, six cards in each of four existing families. No result is independent OOS or official validation. Nothing here justifies official submission. Any apparent gain requires future independent validation.

Parent RESULT: `d3618dcd9aae4ac118a5c12c0fe8f3709a72f296`. Parent PRE: `a57c11701ae2b9383882673b14680e16c8d9cdea`. This experiment PRE_RESULT: `16b4e6b216141a181d5bed73eb89c7232edb0da7`. Branch: `track2/text-route-audit-02`. The final RESULT SHA and remote/recovery completion proofs are recorded in the external completion receipt, avoiding a self-referential commit hash.

## Frozen expert and feature audit

E0 is the exact existing V5.1-text B0. E1 is the exact existing CONTEXT-01 R2 expert-average correction. No expert was fitted, recalibrated or modified. Parent baseline bytes, corrections, forecasts, text and per-card full component scores were verified. R2 reproduces the parent overall ratio 0.980115 and family/component summaries exactly.

The parent had not retained historical full R2 draw arrays or their original hashes. Its immutable baseline plus saved float64 correction uniquely reconstruct the arrays through the unchanged parent shift adapter. A second reconstruction through the original expert arrays and fixed router is bitwise identical; all parent full component scores match exactly. The reconstructed arrays were stored once, hashed and frozen before evaluation. Historical original R2-array hashes cannot be claimed to have been compared because they did not exist.

S0 has 13 pre-outcome structural columns. T0 has 36 inherited lexical/count columns. Parent topic flags that injected asset classes, metadata-derived temporal flags and forced joint flags were excluded from T0. Topic regexes are applied to frozen questions only; other frozen lexical counts use the original questions and dated corpus. ST0 has 49 columns. No new LLM annotations, embeddings, topics, outcome-aware labels or feature search were introduced. IDs, names, hashes, raw absolute dates, outcomes and scores never enter model features.

Fixed L2 logistic regression uses C=1, training-only StandardScaler, no class weighting and threshold 0.50. Fixed secondary Ridge uses alpha=1 on log(R2 loss / B0 loss) and selects R2 for predicted gain <0. No threshold search or post-result redesign was performed.

## 1. Routing oracle headroom

Whole-card oracle headroom is **4.64%**, selecting R2 on 5/24 cards. Single headroom is 7.70%; multi headroom is 0.90%. Maximum positive log-gain share is 61.05%; gains are concentrated in a small exposed sample. Oracle selection is outcome-derived and descriptive only. Multi cards always select one entire E0 or E1 forecast, including every joint draw.

|Family|Oracle composite|Oracle headroom|
|---|---:|---:|
|T2-F1|1.000000|0.00%|
|T2-F2|0.944104|5.59%|
|T2-F3|0.983585|1.64%|
|T2-F4|0.890373|10.96%|

## Forecast score comparison

Ratios below are geometric aggregates using the unchanged CONTEXT-01 scorer; lower is better. Marginal, joint and tail aggregates include only cards with an applicable nonzero B0 component. The artifact also reports arithmetic sensitivity and all classification/gain-regression metrics. Oracle capture is baseline-relative, is never clipped, and is descriptive.

|Model|Composite|Marginal|Joint|Tail|Single|Multi|Oracle capture|R2 cards|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|S0_LOG|1.000000|1.000000|1.000000|1.000000|1.000000|1.000000|0.00%|2|
|T0_LOG|1.008135|1.004352|1.000000|1.016373|1.015071|1.000000|-17.52%|2|
|ST0_LOG|1.007942|1.009211|1.023181|1.000000|1.000000|1.017410|-17.10%|1|
|STF0_LOG|1.007942|1.009211|1.023181|1.000000|1.000000|1.017410|-17.10%|1|
|LENGTH_LOG|1.000000|1.000000|1.000000|1.000000|1.000000|1.000000|0.00%|0|
|ST_NO_FAMILY_LOG|1.000000|1.000000|1.000000|1.000000|1.000000|1.000000|0.00%|0|
|S0_RIDGE|0.993742|0.983324|1.000000|1.016373|0.988478|1.000000|13.48%|10|
|T0_RIDGE|0.957520|0.956325|1.000000|0.953807|0.922988|1.000000|91.49%|11|
|ST0_RIDGE|0.965310|0.960488|1.000000|0.969424|0.936898|1.000000|74.71%|11|
|MAJORITY|1.000000|1.000000|1.000000|1.000000|1.000000|1.000000|0.00%|0|
|B0|1.000000|1.000000|1.000000|1.000000|1.000000|1.000000|0.00%|0|
|R2|0.980115|0.979919|1.024588|0.968737|0.943992|1.024592|42.82%|24|
|STRUCTURAL_EXPOSED|0.969262|0.965539|1.000000|0.970412|0.943992|1.000000|66.20%|13|
|ORACLE_2WAY|0.953566|0.949192|0.998831|0.952161|0.922988|0.991013|100.00%|5|
|RANDOM_MATCHED|0.996018|0.993681|0.993506|1.000000|1.000000|0.991333|8.58%|1|

## 2. Structural routing

The exposed structural heuristic selects R2 for every single card and B0 for every multi card. It scores 0.969262, capturing 66.20% of oracle headroom. It uses a post-CONTEXT-01 pattern and is a diagnostic, not independent evidence. Learned S0 logistic scores 1.000000; primary ST0 logistic scores 1.007942. Its capture beyond the exposed structural heuristic is −246.44%. Removing explicit family labels makes ST0 logistic 1.000000 and does not establish a text increment. Length-only is also 1.000000.

## 3. Text-only routing

Text-only logistic scores 1.008135. The best precommitted secondary text-only Ridge scores 0.957520 and captures 91.49% of oracle headroom. It beats the exposed structural heuristic in this sample, with descriptive capture beyond structure of 74.81%. It uses a continuous gain label, unlike the primary binary winner classifier. This potentially informative secondary result is preserved and must not be called a confirmed null; it also must not be promoted to rescue the primary. Its label/text permutation controls were not part of the precommitted acceptance experiment. No confirmed incremental text-routing claim follows from it.

## 4. Structure + text routing

The sole primary ST0 logistic fails to improve B0 or either structural baseline. The predeclared family-label ablation also shows no incremental text evidence. The fixed secondary ST0 Ridge scores 0.965310 and remains descriptive. Neither secondary model replaces the primary.

## 5. Forecast-state diagnostic

STF0 adds five frozen forecast-state features. Its logistic score equals primary ST0 at 1.007942. Those features are not text and do not replace the primary question.

## 6. Single, multi and F1 safety

|Router|Routed multi|Improved multi|Marginal improved / composite worse|Multi composite|Multi joint|F1 composite|Safety failure|
|---|---:|---:|---:|---:|---:|---:|---|
|ST0_LOG|1|0|0|1.017410|1.023181|1.000000|True|
|T0_LOG|1|0|0|1.000000|1.000000|1.000000|False|
|T0_RIDGE|2|0|0|1.000000|1.000000|1.000000|False|
|ST0_RIDGE|3|0|0|1.000000|1.000000|1.000000|False|
|R2|11|2|0|1.024592|1.024588|1.029885|True|
|STRUCTURAL_EXPOSED|0|0|0|1.000000|1.000000|1.000000|False|
|ORACLE_2WAY|2|2|0|0.991013|0.998831|1.000000|False|

Primary ST0 sends one multi card to R2, improves none, and worsens both its marginal and joint components. Its aggregate multi composite is 1.017410; aggregate joint is 1.023181. F1 remains 1.000000. The predeclared safety threshold is breached. The requested marginal-improved/composite-worsened count is zero because this card also worsens marginal. Joint damage contribution uses the unchanged original composite weights and is recorded in multi_safety_summary.json. Pairwise/path effects are measured by the original full joint variogram; no additional path metric was introduced.

Secondary text-only Ridge sends two multi cards to R2; both choices are no-ops relative to B0, so multi/F1 remain 1.000000. Its gain comes from singles. Every real held-out route was recomputed with the exact full frozen forecast and original scorer, matching the selected parent component scores.

## 7. Family-group holdout

Whole-card LOCO holds out each of 24 cards. Family holdout has four folds of 18 training and six held-out cards. No cells from a card cross folds; preprocessing uses training folds only. Majority uses only training winner labels. No test-card outcomes influence features, thresholds or baselines.

|Model|F1 heldout|F2 heldout|F3 heldout|F4 heldout|
|---|---:|---:|---:|---:|
|S0_LOG|1.000000|1.000000|1.000000|1.049960|
|T0_LOG|1.000000|1.000000|1.000000|1.049960|
|ST0_LOG|1.000000|1.000000|1.000000|1.049960|
|STF0_LOG|1.000000|1.000000|1.000000|0.934857|
|LENGTH_LOG|1.000000|1.000000|1.000000|1.000000|
|ST_NO_FAMILY_LOG|1.000000|1.000000|1.000000|1.049960|
|S0_RIDGE|1.000000|0.944104|1.031538|0.934857|
|T0_RIDGE|1.000000|0.944104|1.000000|0.934857|
|ST0_RIDGE|1.000000|0.944104|1.000000|0.934857|
|MAJORITY|1.000000|1.000000|1.000000|1.000000|

Primary family holdout fails to improve any family and worsens F4. Secondary Ridge gains occur in F2 and F4; F1/F3 remain baseline. This is not broad independent validation.

## 8. Negative controls

The precommitted primary receives 2,000 label-shuffle, 2,000 text-shuffle and 2,000 exactly application-rate-matched random comparisons. Label shuffle permutes only training-card labels inside each fold, excluding held-out outcomes. Text shuffle permutes T0 rows while keeping S0 intact. All seeds are fixed in the artifacts. Smaller lower-tail p values would favor the real router.

|Primary control|Replicates|Mean composite|Lower-tail p|Primary beats null 5% quantile|
|---|---:|---:|---:|---|
|LABEL_SHUFFLE|2000|1.002043|0.771114|False|
|TEXT_SHUFFLE|2000|1.002519|0.760120|False|
|RANDOM_MATCHED|2000|0.999311|0.965517|False|

All nine fixed predictive routers also have their own 2,000 exactly matched-rate random comparisons. This requested reporting supplement uses already frozen choices; it performs no fitting, tuning or primary promotion.

|Router|R2 cards|Random mean composite|Lower-tail p|
|---|---:|---:|---:|
|S0_LOG|2|0.998429|0.662169|
|T0_LOG|2|0.998429|0.968516|
|ST0_LOG|1|0.999311|0.965517|
|STF0_LOG|1|0.999311|0.965517|
|LENGTH_LOG|0|1.000000|1.000000|
|ST_NO_FAMILY_LOG|0|1.000000|1.000000|
|S0_RIDGE|10|0.992082|0.491754|
|T0_RIDGE|11|0.991806|0.007496|
|ST0_RIDGE|11|0.991806|0.065967|

Structure-only, length-only and explicit-family ablation are separately reported. Mutation and card-ID tests pass. Rebuilding all frozen features after adding/shuffling outcome-side fields is bitwise invariant, and 432 real saved-model held-out predictions remain bitwise identical without refitting. Refitting after changing training labels is a deliberately different label-shuffle null, not a feature-leakage mutation test.

## 9. Bootstrap

Each router has 5,000 whole-card and 5,000 whole-family-block replicates. Four six-card families are resampled as complete blocks. Intervals measure exposed-sample sensitivity and do not create independent OOS evidence.

|Router / bootstrap|Composite 95% interval|Delta vs exposed structure 95%|Oracle capture 95%|
|---|---|---|---|
|ST0_LOG / whole_card|[1.000000, 1.024016]|[-0.013065, 0.106858]|[-2.169603, 0.000000]|
|ST0_LOG / family_block|[1.000000, 1.024016]|[0.014277, 0.060531]|[-1.935047, 0.000000]|
|T0_RIDGE / whole_card|[0.893753, 1.000000]|[-0.030124, 0.000000]|[0.000000, 1.000000]|
|T0_RIDGE / family_block|[0.916598, 1.000000]|[-0.034135, 0.000000]|[0.000000, 1.000000]|

The primary interval offers no support for improvement against B0. Negative capture is retained. Tiny or nonpositive capture denominators are marked unstable and excluded from capture intervals with replicate counts reported. Delta vs B0, delta vs learned S0 and capture beyond exposed structure are also included for every model.

## 10. Limitations

Twenty-four previously exposed cards are a tiny research sample. The single/multi pattern, parent expert behavior and family composition are already known. Oracle uses realized outcomes only as a diagnostic. Router winner/gain targets use outcomes only as training labels within crossfit. Secondary apparent gains are not acceptance-confirmed; no new annotations, feature fishing, card-specific rules, threshold tuning, expert refits or favorable-subset selection occurred. Existing frozen R2 inherits the parent's research exposure and cannot be treated as an independent production expert validation.

Public per-card ledgers and prediction CSVs contain explicit metadata/hash redactions. Complete requested per-card losses, predictions, component scores, frozen arrays, original outcome dependencies and fold models are preserved in the private recovery archive. Ledger B0_card_loss, R2_card_loss and routed_card_loss are normalized composite losses relative to that card's B0=1, consistent with the unchanged parent scorer. Their marginal/joint/tail columns are raw original component losses.

## 11. Final verdict and next research axis

**NO. ROUTING_HEADROOM=REAL; primary TEXT_ROUTING_SIGNAL=NO.** Text's incremental contribution beyond structure is not established by the precommitted primary. Controls fail and multi safety worsens. The favorable secondary Ridge is a descriptive lead, not a substitute success. Preserve it without opening TEXT-ROUTE-03 or claiming validation.

Recommended next axis: **NEW_INFORMATION_REQUIRED**. Seek genuinely new, independently dated pre-outcome information and an independent evaluation universe before any further routing claim. No official submission and no one-shot readiness.

## 12. Tests, Git and recovery

Research-specific tests: 20 passed. Directly affected CONTEXT-01 tests: 22 passed. Full repository: 540 passed, two skipped; three pandas deprecation warnings. Common toolkit: 250 passed. The common public manifest firewall passes all 104 public units. Frozen PRE source/feature hashes, all private ledger hashes and result artifact hashes pass. No scoring math was reimplemented.

Results are committed only to track2/text-route-audit-02, descending from the exact parent RESULT and verified PRE. Main remains untouched. Remote RESULT SHA, parent links, every critical remote file and the clean working tree are verified in the external completion receipt. The private recovery includes branch metadata, PRE/RESULT, report, source, tests, STATUS, all results, fold models, controls and manifests, with CRC and SHA-256 verification.
