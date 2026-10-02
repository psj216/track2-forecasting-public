## Executive summary (read this first)

EXPECTATION-01 is complete. All five frozen Ridge variants and the fixed nonlinear diagnostic fail the preregistered success gate. Genuine Philadelphia Fed survey expectations and first-release GDP surprises do not recover positive location headroom under this frozen design. The next axis is POSITIONING-01; no submission is ready or created.

The least harmful nonzero Ridge, A1, has active CRPS ratio 1.026548 and full-ledger ratio 1.012518. Its 95% event-block and year-block intervals are entirely above one. Nonlinear has active 1.011545 and full 1.005444, with intervals spanning one. These are research proxy marginal scores, not official composite scores or evidence that all possible expectation information is useless.

### Identity and freeze

| Item | Value |
| --- | --- |
| Branch | track2/expectation-01-true-market-expectation |
| Research parent | 2a110455c4d4640c8ea8a3b09dd62455104ab475 |
| Initial PRE_RESULT | c341ea5daa623e997483eb123c8f6fb7059289d9 |
| PRE_RESULT_EXPECTATION01_SHA | 5cf12e6380c43d272028a6def96ff9e47e1a3839 |
| PRE_RESULT immediate parent | c341ea5daa623e997483eb123c8f6fb7059289d9 |
| RESULT_SHA | The commit containing this report; recorded in the external preservation receipt to avoid a self-referential SHA. |

A pre-score execution correction dispatched the historical-surprise control to the already specified A5 model. Sources, features, folds, hyperparameters, controls and bootstrap were unchanged. That corrected commit was remotely published and fetched before final scoring. Resume verified 60 saved model/prediction chunks and eight complete scoring chunks, without retraining.

### Source gates and scope

TRUE_CONSENSUS_SOURCE_GATE = PASS. MARKET_IMPLIED_SOURCE_GATE = FAIL. One expectation provider supplies five admissible survey families. One separate BEA source supports first actuals. Three candidate sources were unused: one rejected and two partial.

| Source | Status | Scope or exclusion |
| --- | --- | --- |
| Philadelphia Fed SPF | ADMISSIBLE | 108 quarterly snapshots, 1,080 current/next-quarter values, 1998Q1–2024Q4; RGDP/CPI/UNEMP/TBILL/TBOND |
| BEA original GDP releases | ADMISSIBLE support | 107 original initial/advance releases, 1998Q1–2024Q3; actuals only |
| NY Fed dealer/participant surveys | PARTIAL, unused | Response date is not aggregate publication date; precise historical public snapshots not acquired |
| FRED/ALFRED breakevens | REJECTED, unused | Acquisition-time licensing audit found ML development/training restriction without written consent |
| Fed Board native H15 | PARTIAL, unused | Insufficient original PIT archive across three fixed outer eras |

Publication dates, rather than survey response dates, define point-in-time availability. Preceding-business-day cutoff is mandatory. GDP surprise uses the last matching pre-release quarterly SPF expectation and the original first-release actual; this is quarterly survey surprise, not an invented last-minute market consensus. Other families have expectation features but no fabricated actual-surprise series. Historical dispersion was excluded before results because its original publication timing was unproven. No Class B model was evaluated; that gate only describes the acquired candidates.

Source URLs, acquisition timestamps, legal/provenance notes and immutable hashes are retained in source_manifest.json. Raw reports and per-cell truth/predictions remain private. Excluded FRED numeric samples are not used or included in the durable research archive.

### Coverage and scoring

| Measure | Value |
| --- | --- |
| Underlying reused ledger | 135,994 cells / 1,250 origins / 25 assets |
| Fixed outer evaluation | 82,184 cells / 780 origins / 2010–2024 |
| Active cells / origins | 39,096 / 370 |
| Active coverage | 47.571% |
| Active original information events | 120: 60 survey publications + 60 GDP first releases |
| Unique release dates / years | 120 / 15 |
| Connected event-date blocks / year blocks | 60 / 15 |
| Active origins in folds 1–4 | 99 / 99 / 75 / 97 |

The source window is frozen at business days 1–21 after release; GDP surprise has 1/5/21-day features and an expanding scale from strictly earlier events with minimum 24 observations. Origins sharing overlapping survey/GDP events are unioned before event bootstrap; cells are not independent events. The 189-business-day target-maturity purge applies in both outer training and inner CV.

All candidates translate the original V5.1 draws by predicted standardized delta times original SD. Scoring imports common fair CRPS and original normalization. No variance, rank, tail, copula, draw count or sampling changes. Unavailable primary information forces exactly zero shift and baseline loss.

### Frozen primary Ridge results

Ratios below one improve on baseline. Capture is not clipped. Full capture below uses the requested active-only oracle on the full ledger.

| Model | Active ratio | Full ratio | Active capture | Full capture (active-only oracle) | Active R² | Active Spearman | Active sign accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A0 | 1.000000 | 1.000000 | 0.000% | 0.000% | -0.003835 | N/A | 0.000% |
| A1 | 1.026548 | 1.012518 | -4.528% | -4.528% | -0.044088 | 0.043817 | 51.069% |
| A2 | 1.066862 | 1.031528 | -11.405% | -11.405% | -0.154728 | 0.039977 | 50.721% |
| A3 | 1.114961 | 1.054208 | -19.610% | -19.610% | -0.318089 | 0.049104 | 51.606% |
| A4 | 1.284532 | 1.134166 | -48.534% | -48.534% | -0.839657 | 0.056072 | 51.993% |
| A5 | 1.285015 | 1.134394 | -48.617% | -48.617% | -0.851177 | 0.067073 | 52.568% |

A0 predicts zero shift; its sign accuracy is zero by the inherited exact sign-match convention, not a 0% market-direction classifier. A1 uses global E/S; A2 adds horizon interactions; A3 adds asset-group interactions; A4 adds asset interactions; A5 adds genuine same-target expectation revisions. No bare metadata or fitted intercept is allowed. Ridge scaling and alpha selection use active training data and purged delta-MSE CV, without score-based tuning.

| Model | Active delta MSE | Pearson | Calibration slope | Mean |shift|/SD | Cap hits |
| --- | --- | --- | --- | --- | --- |
| A0 | 1.031646 | N/A | N/A | 0.000000 | 0 |
| A1 | 1.073014 | 0.038320 | 0.170345 | 0.142790 | 0 |
| A2 | 1.186719 | 0.022166 | 0.055128 | 0.182944 | 0 |
| A3 | 1.354606 | 0.031122 | 0.053065 | 0.272090 | 0 |
| A4 | 1.890624 | 0.062749 | 0.064003 | 0.463419 | 164 |
| A5 | 1.902463 | 0.065593 | 0.066289 | 0.469686 | 167 |
| nonlinear | 1.065842 | 0.032044 | 0.155408 | 0.128016 | 0 |

A1 is the descriptive least harmful Ridge after all frozen variants are reported; it is not selected for deployment. Calibration slopes far below one show oversized predicted shifts. Larger interaction models substantially worsen errors, particularly in fold 3. No post-score shrinkage, feature removal, retuning or family selection was performed.

### Fixed nonlinear diagnostic

| Model | Active ratio | Full ratio | Active capture | Full capture (active-only oracle) | R² | Spearman | Sign accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A4 fixed HGB | 1.011545 | 1.005444 | -1.969% | -1.969% | -0.037109 | 0.049445 | 51.279% |

The precommitted depth-3, 200-iteration HGB is diagnostic only. Its two improving folds do not meet the three-fold condition, and pooled active/full ratios are both above one.

### Oracle headroom and reporting denominator audit

| Oracle | Ratio |
| --- | --- |
| Perfect location on active cells | 0.413752402 |
| Active-only oracle on full ledger | 0.723565295 |
| Perfect location on every full-ledger cell | 0.409983325 |

The frozen aggregator records full capture relative to a perfect oracle on every cell, even inactive cells. That denominator differs from the requested active-only oracle. Frozen outputs are preserved unchanged; metrics_reporting_audit.json separately supplies both denominators and the active-only year-bootstrap capture. For primary models inactive predictions and losses exactly match baseline, so the requested active-only full capture equals active capture. For example, A1 is −4.528% under the active-only denominator versus −2.122% in the frozen all-cell-oracle summary. This is a reporting clarification, not a change to scoring, model selection or success gates.

### Outer folds

| Model | 2010–2013 | 2014–2017 | 2018–2020 | 2021–2024 |
| --- | --- | --- | --- | --- |
| A0 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| A1 | 1.035654 | 0.998879 | 1.070627 | 1.007485 |
| A2 | 1.044121 | 1.007672 | 1.213570 | 1.019345 |
| A3 | 1.062434 | 1.039311 | 1.336792 | 1.045596 |
| A4 | 1.232993 | 1.117319 | 1.662120 | 1.172160 |
| A5 | 1.237456 | 1.108179 | 1.666425 | 1.176019 |
| nonlinear | 0.998679 | 0.998523 | 1.001771 | 1.048565 |

### Asset groups and horizons

Below are A1 and nonlinear diagnostics. The CSVs retain every model, including controls and independent family fits.

| Model | group | Active ratio | Full ratio | Active cells |
| --- | --- | --- | --- | --- |
| A1 | FX | 1.029055 | 1.013584 | 17840 |
| A1 | Factor/Equity | 1.033442 | 1.015864 | 10450 |
| A1 | Rates | 1.016690 | 1.007926 | 10806 |
| nonlinear | FX | 1.014484 | 1.006772 | 17840 |
| nonlinear | Factor/Equity | 0.996430 | 0.998306 | 10450 |
| nonlinear | Rates | 1.020890 | 1.009920 | 10806 |

| Model | horizon | Active ratio | Full ratio | Active cells |
| --- | --- | --- | --- | --- |
| A1 | 5 | 1.028171 | 1.013723 | 7970 |
| A1 | 21 | 1.030660 | 1.014650 | 7934 |
| A1 | 63 | 1.030286 | 1.014042 | 7860 |
| A1 | 126 | 1.023897 | 1.011028 | 7732 |
| A1 | 189 | 1.020388 | 1.009562 | 7600 |
| nonlinear | 5 | 1.014889 | 1.007253 | 7970 |
| nonlinear | 21 | 1.013424 | 1.006414 | 7934 |
| nonlinear | 63 | 1.010584 | 1.004907 | 7860 |
| nonlinear | 126 | 1.008740 | 1.004033 | 7732 |
| nonlinear | 189 | 1.010269 | 1.004816 | 7600 |

### Independent family fits and conditional event families

All five preregistered families were retained. Each independent family-only A4 fit uses the same purge/grid. RGDP includes GDP surprise, so its activation extends beyond the common survey window; other families activate on survey releases only. These overlapping masks must not be summed as independent coverage.

| Family | Active cells | Coverage | Active ratio | Full ratio | Active capture | Fold 1 / 2 / 3 / 4 |
| --- | --- | --- | --- | --- | --- | --- |
| RGDP | 39096 | 47.571% | 1.180187 | 1.084964 | -30.736% | 1.066644 / 1.017738 / 1.656324 / 1.032187 |
| CPI | 26466 | 32.203% | 1.035224 | 1.011144 | -6.044% | 0.990555 / 1.047998 / 1.005241 / 1.094481 |
| UNEMP | 26466 | 32.203% | 1.102371 | 1.032389 | -17.566% | 1.226024 / 1.013631 / 1.193805 / 0.992901 |
| TBILL | 26466 | 32.203% | 1.014648 | 1.004634 | -2.513% | 1.025038 / 1.014835 / 1.000611 / 1.016423 |
| TBOND | 26466 | 32.203% | 1.027924 | 1.008835 | -4.791% | 1.075000 / 1.018828 / 1.013027 / 1.002968 |

Every independent family fit has pooled active and full ratio above one. Individual-source results and overlapping family-conditional aggregate results are retained in expectation_source_summary.csv and event_family_summary.csv. Source-family control comparisons are also reported; the controls are fixed A5 fits, not independently retuned family models.

### Negative controls and adversarial guards

| Control (fixed A5) | Active ratio | Full ratio | A5 / control event CI | A5 / control year CI |
| --- | --- | --- | --- | --- |
| A_historical_surprise | 1.275181 | 1.129760 | [0.997471, 1.018394] | [0.999549, 1.008835] |
| B_sign_shuffle | 1.300110 | 1.141511 | [0.970046, 1.005405] | [0.980833, 1.005522] |
| C_older_snapshot | 1.094179 | 1.044357 | [1.027926, 1.436812] | [1.011186, 1.200472] |
| D_event_dates | 1.283116 | 1.133498 | [0.996705, 1.005678] | [0.999028, 1.002852] |

A = strictly historical same-family surprise donor. B = surprise sign shuffle. C = strictly older matching survey snapshot. D = conservative delayed event-date permutation within family/year. A/B/D retain genuine expectation state. Comparisons use the primary-active mask and preserve entire event/year blocks.

A5 is not clearly better than every control. A1 and nonlinear beat the more complex A5 controls under the frozen paired rule, but they still fail baseline, capture and fold gates. This complexity mismatch cannot establish surprise-specific alpha. E pre-release injection, F revised-actual substitution and H post-release snapshot mutation are rejected; G future-source mutation and inherited cached-baseline immutability pass. There is no admissible Class B market input, so a Class B future-market experiment is not claimed.

### Uncertainty

Event uncertainty uses 2,000 paired connected event-date resamples with 60 blocks. Full-ledger uncertainty uses 2,000 calendar-year resamples with 15 blocks. Every related origin, asset and horizon stays together. Seeds and frozen bootstrap functions are unchanged.

| Model | Active event-block ratio 95% CI | Full year-block ratio 95% CI |
| --- | --- | --- |
| A0 | [1.000000, 1.000000] | [1.000000, 1.000000] |
| A1 | [1.004154, 1.063228] | [1.001169, 1.029855] |
| A2 | [1.012599, 1.170068] | [1.003188, 1.082674] |
| A3 | [1.029670, 1.272891] | [1.011099, 1.131287] |
| A4 | [1.120060, 1.584115] | [1.046134, 1.283223] |
| A5 | [1.118135, 1.587182] | [1.046310, 1.284941] |
| nonlinear | [0.998131, 1.024776] | [0.997601, 1.013007] |

### Event-level GDP diagnostic

| Metric | Value |
| --- | --- |
| Original GDP events / dates | 60 / 60 |
| Surprise → mean standardized delta slope | -0.018484 |
| Event Spearman | -0.247680 |
| Direction agreement | 43.333% |
| Mean delta for positive / negative surprise | -0.015917 / 0.098333 |

This descriptive pooled event statistic mixes assets and horizons. It is not a deployable asset-specific direction rule or a reason to flip economic sign after seeing results. Individual event values remain private.

### Validation and preservation

Source and processed input hashes, 1,251 inherited origin-cache hashes, 60 prediction chunks and eight score chunks verified. Zero-shift baseline is reproduced through the imported common CRPS. All methodological code and frozen protocol match PRE_RESULT. Research tests pass (29); pre-result directly affected tests pass (59); the recorded full suite passes (474, 2 skipped), and resume verification logs are preserved. No main-branch edits, architecture changes, submission artifacts or new evaluation-time source fetches were made.

The complete private recovery archive contains saved predictions/models, scoring chunks, 80 individually saved frozen bootstrap calls, losses, per-event diagnostic rows, audits and execution logs. Earlier source and frozen-matrix archives are separately preserved and referenced in the preservation receipt. Public artifact_manifest.json lists hashes, byte counts and provenance, without raw realized outcomes.

### Final decision

```text
EXPECTATION01_RESULT = NO
NEXT_RESEARCH_AXIS = POSITIONING-01
READY_FOR_ONE_SHOT_SUBMISSION = NO
```

The actual tested survey-state / first-release-surprise design does not capture the location headroom despite 47.57% cell coverage and four active eras. This excludes the tested design as a justified submission improvement. It does not rule out release-immediate reactions, unavailable intraday consensus, other expectation archives, or a future separately preregistered design. Further tuning of these exposed folds would not be independent validation.
