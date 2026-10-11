"""Executive summary: preserve failed historical gates; never open blocked card outcomes.

This finalizer only reports frozen diagnostics and stages that were actually run.
It cannot change the mechanism, select a new K, or promote a diagnostic forecast.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from .core import PARENT, MAIN, BRANCH, digest, save, gate1, gate2
from .run import OUT, ROOT, private, status, verify


def finalize():
    receipt=verify();p=private()
    oracle=json.loads((OUT/'candidate_path_oracle.json').read_text())
    historical=json.loads((OUT/'historical_summary.json').read_text())
    assert gate1(oracle['marginal_ratio'])
    assert not gate2(historical),'A passed historical gate needs the separately frozen card phase, not this stopped-stage finalizer.'
    assert historical['card_outcomes_opened'] is False
    controls=json.loads((OUT/'negative_controls.json').read_text())
    boot=json.loads((OUT/'historical_bootstrap.json').read_text())
    selection=json.loads((OUT/'historical_k_selection.json').read_text())
    data=json.loads((OUT/'analog_data_manifest.json').read_text())
    tests=json.loads((p/'final_test_results.json').read_text())
    assert all(x['exit_code']==0 for x in tests.values())
    decision=dict(executive_summary='Frozen nearest-path mechanism failed the historical moonshot gate; card outcomes remain unopened.',
        NEW_MECHANISM_MOONSHOT12_RESULT='ANALOG_NOT_PREDICTIVE',ZERO_POINT_FIVE_CLASS_SIGNAL=False,
        oracle_gate_passed=True,historical_gate_passed=False,oracle_marginal=oracle['marginal_ratio'],
        historical_ratio=historical['ratio'],equal_year_ratio=historical['equal_year_ratio'],
        selected_K=selection['selected_K'],no_posthoc_redesign=True,card_outcomes_opened=False,
        no_submission=True,independent_OOS=False,official_score_reestimated=False,
        biggest_failure='The compact state fingerprint cannot reproduce hindsight path selection strongly enough; nearest-path distribution worsens the preserved V5.1 baseline.',
        mechanism='Hindsight coherent scenario selection generates library headroom. Actual PIT similarity retrieval does not generate a moonshot forecast gain.',
        NEXT='V51-FINAL-SAFE-SUBMISSION-13',next_axis_executed=False)
    save(OUT/'final_decision.json',decision)
    save(OUT/'next_axis_decision.json',dict(executive_summary='Stop forecasting research after the frozen historical failure; next action is separately authorized safe delivery.',NEXT=decision['NEXT'],executed=False,submission_executed=False))
    save(OUT/'pre_result_manifest.json',dict(executive_summary='Remote oracle and implementation freezes exist; the conditional PRE before cards was correctly never reached.',
        parent=PARENT,PRE_ORACLE_SPEC_SHA=receipt['PRE_ORACLE_SPEC_SHA'],HISTORICAL_IMPLEMENTATION_SHA=receipt['historical_implementation_SHA'],
        PRE_RESULT_MOONSHOT12_SHA=None,status='CARD_PRE_NOT_REACHED_GATE2_FAILED',card_outcomes_opened=False,
        frozen_files=receipt['frozen_files'],remote_verified=True))
    skip=dict(executive_summary='Correctly not run because historical kill gate failed.',status='NOT_RUN_GATE2_FAILED',card_outcomes_opened=False)
    for name in ['card_score_summary.json','single_multi_summary.json','joint_safety.json','card_bootstrap.json']:
        save(OUT/name,skip)
    for name,cols in [('card_results.csv',['executive_summary','card_id','status']),('family_summary.csv',['executive_summary','family','status'])]:
        pd.DataFrame([['Not evaluated; no card outcome opened','ALL','NOT_RUN_GATE2_FAILED']],columns=cols).to_csv(OUT/name,index=False)
    folds=[]
    for phase,years in [('K_SELECTION',range(2009,2016)),('FORWARD_EVALUATION',range(2016,2025))]:
        dest='selection' if phase=='K_SELECTION' else 'evaluation'
        for year in years:
            files=sorted((p/dest/str(year)).glob('*.npz'))
            folds.append(dict(executive_summary='Every donor path matured strictly before its own query origin; no yearly fit uses future labels.',phase=phase,year=year,origins=len(files),historical_origin_start='2001-01-02',training_rule='Strict per-origin whole-path maturity purge; feature normalization on prior state rows only.',selected_K=selection['selected_K'] if phase=='FORWARD_EVALUATION' else '8/16/32/64'))
    pd.DataFrame(folds).to_csv(OUT/'historical_fold_manifest.csv',index=False)
    save(OUT/'execution_audit.json',dict(executive_summary='Frozen path oracle, historical retrieval, all required historical controls and block inference completed; conditional card stage blocked honestly.',
        parent=PARENT,oracle_PRE=receipt['PRE_ORACLE_SPEC_SHA'],historical_freeze=receipt['historical_implementation_SHA'],
        tests=tests,card_outcomes_opened=False,hidden_development_labels_used=False,
        scientific_redesign=False,main=MAIN,safe_V51_unchanged=True,safe_delivery_artifacts_unchanged=True,
        operational_notes=['The scratch .venv interpreter target was absent; reused already-restored explicit host dependencies and common source path. No package installation or historical source repair.',
                           'Host Python3.12 audit only. Safe V5.1 container Python3.13/common2.4.2 remains untouched. Common CRPS source hash matches the canonical scorer byte-for-byte.'],
        completed_controls={k:v.get('reps',1) for k,v in controls['controls'].items()},bootstrap_reps=5000,
        historical_OUTCOME_exposure='RESEARCH_EXPOSED, no independent OOS',
        git_RESULT_and_recovery='Recorded after commit by external final receipt; no self-referential RESULT/archive hash.'))
    years=[(x['year'],x['ratio']) for x in historical['years']]
    text=['## Executive summary (read this first)','',
          '**Result: ANALOG_NOT_PREDICTIVE.** The frozen historical gate failed. No 24-card outcome was opened, no candidate was built and nothing was submitted.',
          f"The past-path library oracle reached {oracle['marginal_ratio']:.9f}, passing the 0.65 headroom gate. Actual PIT nearest-state retrieval with K={selection['selected_K']} scored {historical['ratio']:.9f} against the exact same-cell V5.1 baseline. Equal-year ratio was {historical['equal_year_ratio']:.9f}. This does not meet the required 0.85/0.90 gates.",'',
          '## Universe, provenance and target semantics','',
          f"The original canonical ledger has {data['origins']:,} origins, {data['cells']:,} cells and {len(data['assets'])} assets, {data['date_range'][0]} through {data['date_range'][1]}. Evaluation uses all {historical['origins']} canonical origins and {historical['cells']:,} eligible cells in 2016–2024. All historical data are RESEARCH_EXPOSED; INDEPENDENT_OOS=false.",
          'Original canonical ledger and preserved center ledger SHA256s matched exactly. Baseline cell CRPS was reused from the frozen center ledger; no original V5.1 draws were rebuilt. Its common CRPS source is byte-identical to the pinned validation scorer. Source panels are existing repository prefixes, not newly acquired data. Historical publication-vintage uncertainty beyond the inherited prefix convention remains.',
          'Rate/FX levels use scaled historical endpoint changes rebased to the current observed level. Factors use the original accumulated daily return increments without scale normalization. Actual inherited business-day endpoints and gap rules are retained. Each complete analog path must have every requested endpoint strictly before the query origin. No per-cell retrieval or independently shuffled marginal occurs.',
          'Eight own-asset fingerprint dimensions and two shared dimensions were fixed. Median/IQR normalization is fitted to prior state rows only. Distances use shared finite dimensions with80% coverage. Uniform draws share one historical origin across all joint cells. Technical fallback requires at least8 complete analogs. No text/PCA/new external source is used. Monthly macro assets are absent from the continuous universe; they were not dropped from an evaluated card set because no card phase occurred.','',
          '## Oracle and its limitation','',
          f"Future-informed oracle marginal ratio: **{oracle['marginal_ratio']:.9f}**. The full-card composite oracle is unavailable in the canonical marginal ledger and was not manufactured by opening card outcomes.",
          'The diagnostic exhaustively finds the best single complete path and adds whole scenarios greedily up to8 members. Final scores use1000 complete draws and the inherited fair estimator. Greedy mixtures do not certify the optimum over every possible mixture. This headroom is hindsight, not evidence that market state can identify those scenarios.','',
          '## Historical-only K selection and forward test','',
          'K was chosen only on2009–2015;2016–2024 results and24-card losses were excluded from selection. The four fixed choices were8,16,32,64; ties prefer larger K.',
          '| K | 2009–2015 ratio |','|---:|---:|',
          *[f"| {k} | {v:.9f} |" for k,v in selection['ratios'].items()], '',
          '| Forward year | Primary CRPS ratio |','|---:|---:|',
          *[f'| {y} | {v:.9f} |' for y,v in years], '',
          f"Improved years: {historical['improved_years']}/9. Improved origins: {historical['fraction_origins_improved']:.2%}. Median origin ratio: {historical['median_origin_ratio']:.9f}. Fallback origins: {historical['fallback_origins']}.",
          f"Equal-origin {historical['equal_origin_ratio']:.9f}; equal-year {historical['equal_year_ratio']:.9f}; asset-balanced {historical['asset_balanced_ratio']:.9f}; horizon-balanced {historical['horizon_balanced_ratio']:.9f}. Balanced ratios are equal means of within-block ratios; primary is the ratio of all summed normalized cell losses.",'',
          '## Controls and block uncertainty','',
          '| Control | Mean / ratio | Empirical lower-tail p |','|---|---:|---:|',
          *[f"| {name} | {item.get('mean',item.get('ratio')):.9f} | {item.get('MC_p','—')} |" for name,item in controls['controls'].items()], '',
          'Stochastic controls each have2000 replicates, seed31812. The cheap null statistic scores the exact empirical K-path distribution with shared fair=False CRPS for BOTH primary and null. This integrates resampling noise and is kept separate from the main1000-draw fair=True forecast ratio. Monte Carlo p-values use plus-one correction. Distance shuffle is uniform reassignment of the past eligible ranks and is distributionally equivalent to random K selection. Time matching uses fixed5/10-year business-day age buckets. Every donor was already fully matured.',
          '| Bootstrap block | Primary95% CI |','|---|---|',
          *[f"| {name} ({item['blocks']} blocks) | [{item['CI95'][0]:.9f}, {item['CI95'][1]:.9f}] |" for name,item in boot['blocks'].items()], '',
          'Each bootstrap has5000 whole-block replicates, conditional on frozen retrieval. Origin blocks share overlapping future horizons; year and asset blocks provide complementary dependent-data views. No IID cell bootstrap or independent-OOS claim is made.',
          f"Largest-year share of gross gain: {historical['max_year_gross_share']:.2%}; largest-asset share: {historical['max_asset_gross_share']:.2%}. All assets/horizons/years remain in the aggregate. These gross gains do not offset the total forecast degradation.",'',
          '## Kill gate, card firewall and next action','',
          'The historical model worsens baseline and fails the frozen large-effect gates. Any statistical separation from random analog selection does not override that failure. No favorable year, asset, horizon, K or amplitude was substituted. The card PRE, card scoring, joint/tail/F1–F4 results, card/family bootstrap, inverse-distance card diagnostic and optional hybrid are NOT_RUN_GATE2_FAILED. No card result, submission candidate or0.5-class signal exists.',
          '**ZERO_POINT_FIVE_CLASS_SIGNAL=false. NEXT=V51-FINAL-SAFE-SUBMISSION-13.** No further forecasting research or actual submission is executed in this task.',
          'The validated exact safe V5.1 image/source and common2.4.2 remain unchanged. Historical Development0.9541 remains a reference only; it was not re-estimated or multiplied by proxy ratios, and the actual historical uploaded-artifact identity remains unproven.','',
          '## Tests and release preservation','',
          *[f"- {name}: {item['summary']}" for name,item in tests.items()], '',
          'The three inherited immutable historical branch assertions are deselected under the already-documented branch-only exception. No test expectation/assertion was weakened. Other skips remain documented existing gated/integration tests.',
          f"Branch: `{BRANCH}`. Parent: `{PARENT}`. Oracle/spec freeze: `{receipt['PRE_ORACLE_SPEC_SHA']}`. Historical implementation freeze: `{receipt['historical_implementation_SHA']}`. Conditional card PRE: NOT_REACHED.",
          'Final RESULT SHA, authoritative remote compare/file checks, protected-file verification, clean tree and new private recovery ZIP CRC/member/full hashes are recorded in the external final receipt after RESULT, avoiding self-reference.']
    (ROOT/'NEW-MECHANISM-MOONSHOT-12-report.md').write_text('\n'.join(text)+'\n')
    status('scientific_delivery_complete',True,state='RESULT_READY',classification=decision['NEW_MECHANISM_MOONSHOT12_RESULT'],
           NEXT=decision['NEXT'],PRE_ORACLE_SPEC_SHA=receipt['PRE_ORACLE_SPEC_SHA'],
           card_PRE_and_evaluation='NOT_RUN_GATE2_FAILED',pending_stages=['RESULT_commit_push_verify','final_recovery'])
    save(OUT/'artifact_manifest.json',dict(executive_summary='All public results are aggregate-only; private labels/path bank remain outside Git.',
        parent=PARENT,files={str(f.relative_to(ROOT)):digest(f) for f in sorted(OUT.glob('*')) if f.is_file() and f.name!='artifact_manifest.json'},
        report_SHA256=digest(ROOT/'NEW-MECHANISM-MOONSHOT-12-report.md'),
        private_state='Original canonical/center hashes, original feature/scale caches, path bank, per-origin selection/oracle/evaluation, all control chunks and bootstrap arrays are retained in private recovery.'))


if __name__=='__main__':finalize()
