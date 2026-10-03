"""Executive summary: report the frozen primary result without selecting ablations."""
import argparse
import json
from pathlib import Path
import pandas as pd
from .source_acquisition import ROOT,OUT


def fmt(v,n=4):
    return '—' if v is None else f'{v:.{n}f}'


def table(rows,columns):
    return '\n'.join(['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']+['| '+' | '.join(str(r[c]) for c in columns)+' |' for r in rows])


def report(private):
    decision=json.loads((OUT/'final_decision.json').read_text());models=json.loads((OUT/'primary_score_summary.json').read_text())['models']
    boot=json.loads((OUT/'bootstrap_summary.json').read_text());controls=json.loads((OUT/'negative_controls.json').read_text())['controls']
    counts=json.loads((OUT/'effective_sample_summary.json').read_text());folds=pd.read_csv(OUT/'fold_manifest.csv');pre=json.loads((private/'pre_receipt.json').read_text())['PRE_RESULT_LOCATION02_SHA']
    mt=[{'Model':k,'CRPS ratio':fmt(v['crps_ratio']),'Oracle capture':fmt(v['oracle_capture']),
         'R²':fmt(v['r2']),'Spearman':fmt(v['spearman']),'Sign accuracy':fmt(v['sign_accuracy'])} for k,v in models.items()]
    year=pd.read_csv(OUT/'year_summary.csv');year=year.loc[year.model.eq('ECB_RIDGE_FULL5')]
    horizons=pd.read_csv(OUT/'horizon_summary.csv');horizons=horizons.loc[horizons.model.eq('ECB_RIDGE_FULL5')]
    yt=[{'Year':int(r.group),'Cells':int(r.cells),'Releases':int(r.releases),'CRPS ratio':fmt(r.crps_ratio),'Oracle capture':fmt(r.oracle_capture)} for r in year.itertuples()]
    ht=[{'Horizon (BD)':int(r.group),'Cells':int(r.cells),'Releases':int(r.releases),'CRPS ratio':fmt(r.crps_ratio),'Oracle capture':fmt(r.oracle_capture)} for r in horizons.itertuples()]
    ct=[{'Control':k,'Replicates':v.get('permutations',1),'Median/fixed ratio':fmt(v.get('median_ratio',v.get('crps_ratio'))),
         'Fraction ≤ primary':fmt(v.get('fraction_at_least_as_good'))} for k,v in controls.items()]
    ci=boot['blocks']['round_id'];yc=boot['blocks']['year'];p=models['ECB_RIDGE_FULL5']
    economic=json.loads((private/'economic_diagnostics.json').read_text())
    text=f'''# LOCATION-02 — ECB SPF consensus location alpha

## Executive summary

**Verdict: {decision['LOCATION02_RESULT']}.** The precommitted FULL5 model has CRPS ratio **{p['crps_ratio']:.6f}** versus original V5.1=1, with oracle capture **{p['oracle_capture']:.4%}**. All five annual folds deteriorate. This frozen test does not support ECB SPF predicting the EUR standardized location error. Do not tune this failure or substitute an ablation. Next axis: **{decision['NEXT']}**.

All observations are **RESEARCH-EXPOSED**. No result is independent out of sample, official validation or submission evidence. New architecture, scale, tail, covariance and rank models were not created. The experiment tests exactly five original-release consensus features against an existing forecast's location error.

## Source readiness and provenance

Gate A: **DATASET_READY=true**, before accessing forecasting outcomes. The actual dated official archive enumerated 40 releases, 2015Q1–2024Q4 (2015-01-23–2024-10-18), not an assumed quarter count. Original official PDFs supply 240 point-field rows: headline HICP and real GDP, explicit current/next/second-following calendar years. Matching HTML is additionally available for 26 rounds. Each raw document has an original URL and byte SHA256 receipt.

There are 39 usable same-target revision events / 78 variable revisions. 2015Q1 has no verified preceding 2014 original within the admitted universe and is inactive; its retrospective printed comparison was not a substitute feature. All 216 applicable following-round comparisons agree with preceding originals. No amendment notice was found in the complete original documents and matching HTML. This is **PIT B**, not immutable historical-vintage proof; absence of a notice does not prove that no unpublished replacement ever occurred. No current aggregate CSV, revised history, microdata or third-party backcast was used.

Publication uses actual official dates. For example 2020Q2 is **2020-05-04**, not a guessed April quarterly date. Date-only availability is 23:59:59 Europe/Berlin, compared with the prior repository weekday at 16:00 America/New_York. Response/deadline/PDF creation timestamps are never activation evidence. Ambiguous NY federal-holiday cutoff days are conservatively excluded. SOURCE_AGE uses unchanged repository weekday business days and expires strictly after 90, without tuning.

The archive and original URLs appear in `ecb_release_universe.csv`; each extraction locator, explicit target year and original hash appears in `ecb_field_ledger.csv`. A revision is current next-year minus the previous verified round for **that same target year**, including the preceding round's second-following year at Q1 rollover. Missing revisions are never imputed. Corrections are distinct availability events, not retrospective overwrite. Rights: ECB attribution, accurate reproduction and clearly labelled derivatives; raw originals are privately preserved for this research and are not publicly redistributed as a corpus.

Official source: https://www.ecb.europa.eu/stats/ecb_surveys/survey_of_professional_forecasters/html/all-releases.en.html

## Frozen experiment and maturity

Parent RESULT: `{decision.get('parent_result_sha','43a154ab419b6f3e3f4fc903db40d8c2e319f6bf')}`. PRE_RESULT_LOCATION02_SHA: `{pre}`. All source rows/hashes, parser, five features, timing, age90, EUR, horizons5/21/63/126/189, model, fold rules, scorer, controls and interpretation were committed and remotely verified before labels were materialized. The frozen parent ledger and original cached V5.1 draws were restored and byte-hash verified; no V5.1 model or distribution was regenerated.

Use first existing frozen baseline-ledger origin each month. Source-only calendar: 120 monthly candidates, 100 active after missing/expiry/holiday guards. Outcome eligibility leaves 95 origins / 462 cells across development and forward history. Evaluation has **{counts['forecast_origins']} origins / {counts['cells']} cells / {counts['unique_active_releases']} releases**, with 5 annual blocks. Original EUR level series ends 2024-10-31; no extension was synthesized. Every target matures no later than the user's 2024-12-18 ceiling and the existing series endpoint. EUR truth is the repository's absolute future level, not a reinterpreted log return.

Training starts 2015–2019 and expands for each annual 2020–2024 fold. Labels must mature strictly before the first test cutoff. The shared model additionally applies the parent's maximum189BD origin purge; horizon-specific target_end checks remain explicit. Train/test source release IDs do not overlap. One pooled Ridge has alpha=1.0, intercept and deterministic SVD. Train-only standardization and Ridge use weights1/(training rows in release), so each release has total weight1. No tuning, feature selection or threshold selection was performed.

Target: `(truth − median(original draws)) / original population SD`. Candidate: original draws plus `predicted_delta × original SD`. Draw count, centered geometry, ordering and original scale are preserved. Inactive origins have zero shift but are outside the active primary cohort. No later EUR/card transfer or joint/F1 claim follows from marginal scores.

## Primary scores and secondary ablations

CRPS imports the exact shared fair-ensemble scorer. Each cell is divided by its frozen past-only daily scale times sqrt(horizon); aggregate ratio is the ratio of sums over identical cells, exactly as in LOCATION-01. Lower is better. Oracle capture is `(1−candidate ratio)/(1−perfect-location ratio)`, without clipping.

{table(mt,['Model','CRPS ratio','Oracle capture','R²','Spearman','Sign accuracy'])}

Ablations are descriptive only. They do not replace the failed FULL5 result. Perfect location shifts each original distribution median to truth, changing no shape; it measures same-ledger location headroom, not achievable prediction. V5.1's zero-shift error predictor has undefined rank correlation; zero predictions count as a correct sign only for an exactly zero realized standardized error.

## Annual forward folds

{table(yt,['Year','Cells','Releases','CRPS ratio','Oracle capture'])}

No annual fold improves. Annual maturity/purge/release counts are in `fold_manifest.csv`; fold-specific scalers and coefficients are preserved privately. They are descriptive, not causal macro effects.

## Horizon breakdown

{table(ht,['Horizon (BD)','Cells','Releases','CRPS ratio','Oracle capture'])}

All five horizons are retained; no favorable horizon/year subset was selected. Late-2024 long-horizon labels are genuinely unavailable, explaining smaller counts.

## Repeated-release dependence and inference

The {counts['cells']} cells are not independent information events. They share only {counts['unique_active_releases']} source releases; this count is an **upper bound**, not a proven effective independent sample size. A source release can be reused by several monthly origins and horizons; quarterly persistence and overlapping targets can cause dependence beyond release blocks. Exact origins per release and releases per fold/horizon are preserved in the public summaries.

Release-block bootstrap: 5,000 replicates, ratio95% interval **{ci['crps_ratio_95ci']}**, delta-versus-V5.1 interval **{ci['delta_vs_v51_95ci']}**, capture interval **{ci['oracle_capture_95ci']}**. Year-block bootstrap: 5,000 replicates over only5 years, ratio95% interval **{yc['crps_ratio_95ci']}** and capture interval **{yc['oracle_capture_95ci']}**. Correlation intervals are in `bootstrap_summary.json`. Neither bootstrap creates independent validation.

## Negative controls and mutations

{table(ct,['Control','Replicates','Median/fixed ratio','Fraction ≤ primary'])}

Each stochastic family uses2,000 deterministic replicates, unchanged chronological maturity/purge and alpha1/scaler mechanics. Value/revision shuffles reassign training source vectors at release-block level within each historical training information set; held-out outcomes and future test values never enter fitting. Revision signs are fixed within each source block. Date permutations use randomly reassigned **nonnegative** publication delays0..20BD and never activate before actual publication. One-year lag is a single frozen diagnostic. Gaussian control has exactly5 dimensions and one vector per release. Null performance is never used to choose model settings.

Later ECB release mutation leaves all earlier source features and actual2020/2021 predictions bitwise unchanged. Outcome mutation cannot change the source calendar, whose construction has no outcome interface. Synthetic and real geometry checks preserve original population SD and weak within-distribution ordering. Actual FULL5 has two sorted-index positions affected by a newly rounded1ULP tie; centered geometry roundoff is at most2.22e-16 and no ordering inversion occurs. Strict argsort byte identity therefore does not hold. No numerical jitter, reranking or correction was introduced. The only post-PRE validation correction preserves original CSV-parsed bits for unchanged source events: rebuilding every input from JSON would introduce unrelated one-ULP serialization differences. This corrected diagnostic changes no primary feature, prediction, score, stochastic-control result or success gate; frozen primary implementation hashes remain exact. Individual standardized errors, truths, draws and cell losses remain private.

## Concentration and economic direction

Predeclared concentration diagnostics: `{decision['concentration']}`. These refer to shares of **gross positive local gains**, where present, not proof of a total improvement. FULL5 degrades in all five years, so there is no overall improvement whose breadth could support alpha. Removal of a bad year/release is not an authorized experiment.

Raw economic correlations are descriptive only: `{economic['raw_feature_correlations']}`. Forecast claims rely exclusively on crossfit predictions. Coefficient signs and these correlations are not causal evidence.

## Limitations and decision

Only EUR, only20 evaluated releases and five exposed annual folds; quarterly persistence and overlapping horizons limit inference. Source timing is dated official provenance at PIT B rather than an immutable archive. Weekday BDay is the repository convention, not a full exchange holiday calendar. The frozen draw cache cannot support new monthly dates, new scales or later market history; those were not invented. No official multi-card joint/tail score or prospective validation was run.

**Final verdict: {decision['LOCATION02_RESULT']}.** ECB SPF specifically failed this frozen location test. This does not imply every new information source fails. Preserve all results, leave ECB untuned, and proceed only in a separately frozen study to INFO-01's pre-ranked source#2, **Fed SLOOS**. Do not add SLOOS to this experiment and do not submit from this history.

## Tests, Git and recovery

Research-specific tests:20 passed before outcome access. Directly affected LOCATION-01 and INFO-01 tests:75 passed before PRE. Final research, affected, full repository and common-toolkit counts are recorded in `execution_audit.json` after execution. Main is protected against the recorded `e1b5cf3b3a87966e902332ef3cc5c0ed2dbffee8`; all178 frozen parent protected files are checked unchanged.

Branch: `track2/location-02-ecb-spf-alpha`. The result commit, remote critical-file verification, clean-tree proof and recovery archive hash are recorded in the external private verification receipt, avoiding a self-referential Git commit. Private recovery contains original source bytes/receipts, frozen baseline caches and ledger, source/parser/model/tests, predictions/losses, null distributions/bootstrap, report, stage status/logs, PRE/RESULT metadata and a Git bundle. ZIP CRC, per-file SHA256 and whole-archive SHA256 are verified before durable preservation.
'''
    (ROOT/'LOCATION-02-ECB-SPF-CONSENSUS-LOCATION-ALPHA-report.md').write_text(text)
    print('Report written, primary result remains '+decision['LOCATION02_RESULT'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private',type=Path,required=True);report(p.parse_args().private)
