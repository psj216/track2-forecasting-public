"""## Executive summary (read this first)

Write complete grouped results without exposing individual labels or answers.
"""
import argparse
import json
from pathlib import Path
import pandas as pd
from .build_location_ledger import dump,digest

def number(value):
    return '—' if value is None else f'{value:.6f}'

def table(rows,columns):
    lines=['| '+' | '.join(c[0] for c in columns)+' |',
           '| '+' | '.join('---' for _ in columns)+' |']
    for row in rows:
        lines.append('| '+' | '.join(str(row.get(c[1],'—')) if c[2]=='s' else number(row.get(c[1])) for c in columns)+' |')
    return '\n'.join(lines)

def write(root,private,pre_result_sha):
    result=root/'backtesting/location01/results'
    def read(name):return json.loads((result/name).read_text())
    ledger=read('ledger_manifest.json');main=read('crossfit_summary.json')
    single=read('single_cell_transfer.json');multi=read('multi_cell_transfer.json')
    folds=pd.read_csv(result/'fold_summary.csv');groups=pd.read_csv(result/'group_summary.csv')
    horizons=pd.read_csv(result/'horizon_summary.csv');families=pd.read_csv(result/'family_transfer.csv')
    best=main['best_precommitted_ridge'];gate=main['READY_FOR_LOCATION_02']
    signal=gate not in ('NO','NONLINEAR_ONLY_SIGNAL')
    joint=multi['models'][best]['joint_ratio'];f1=multi['F1'][best]
    joint_damage=joint>1.10 or f1['joint_ratio']>1.10
    if signal:axis='PATH-01' if joint_damage else 'LOCATION-02'
    elif gate=='NONLINEAR_ONLY_SIGNAL':axis='LOCATION-02'
    elif single['models'][best]['ratio']<=.97:axis='CONTEXT-01'
    else:axis='NEW_INFORMATION_REQUIRED'
    main['NEXT_RESEARCH_AXIS']=axis
    main['F1_SAFETY_VERDICT']=('LOCATION SIGNAL MAY EXIST, BUT PATH MODEL REQUIRED'
        if f1['marginal_ratio']<1 and f1['joint_ratio']>1.10 else 'NO_MARGINAL_GAIN_WITH_MAJOR_JOINT_DAMAGE_PATTERN')
    dump(result/'crossfit_summary.json',main)
    audit=read('crossfit_fit_audit.json');totalpurge=sum(v['purged_rows'] for v in audit)
    parts=['## Executive summary (read this first)',
        '# LOCATION-01 — Predictable Oracle Shift Decomposition',
        f'Best precommitted Ridge channel: **{best}**. Cross-fitted ratio **{main["models"]["ridge"][best]["ratio"]:.6f}**, oracle-headroom capture **{main["models"]["ridge"][best]["oracle_capture_fraction"]:.2%}**.',
        f'**READY_FOR_LOCATION_02 = {gate}**. **NEXT_RESEARCH_AXIS = {axis}**. **READY_FOR_ONE_SHOT_SUBMISSION = NO**.',
        'All results are RESEARCH_PROXY_ONLY and research-exposed chronological cross-fit. They are not independent OOS evidence or official leaderboard scores. No submission candidate was built.',
        '## Preservation and frozen protocol',
        'Branch: `track2/location-01-predictable-oracle-shift`  \nParent: `b24d2602fc70e4e004a6d4b5496f3b0be00948e2`  \n'+f'PRE_RESULT_LOCATION01_SHA: `{pre_result_sha}`  \nRESULT_SHA: the result commit containing this report (recorded separately in the preservation receipt).',
        'All method, schema, folds, parameters, alpha grid, controls, tests and input hashes were remotely frozen before final cross-fitted scoring or card-transfer outcomes were opened. Full definitions: `frozen_protocol.json` and `LOCATION-01-PRECOMMIT.md`.',
        '## Ledger and information boundary',
        f'General origins: **{ledger["origins"]}**; eligible cells: **{ledger["cells"]}**; assets: **{len(ledger["assets"])}**; dates: **{ledger["date_range"][0]} — {ledger["date_range"][1]}**. Grid anchor2001-01-02, stride5 BDays; horizons5/21/63/126/189. Unequal prefix coverage is retained, with no result-dependent filtering.',
        f'Cross-fit scoring: **{main["evaluation_origins"]} origins / {main["evaluation_cells"]} cells**, {main["evaluation_date_range"][0]} — {main["evaluation_date_range"][1]}. Earlier origins train models. Purged rows summed across overlapping outer training pools: **{totalpurge}** (not a unique-row count).',
        table(audit,[('Fold','fold','s'),('Train cells','train_rows','s'),('Test cells','test_rows','s'),('Purged','purged_rows','s'),('Latest train origin','latest_training_origin','s'),('Latest train maturity','max_training_maturity','s')]),
        'The full maximum189-BDay origin exclusion and explicit maturity check apply to outer, inner and transfer fitting. Inner scaler/imputer are fit only on the inner training portion. Labels are future truth-minus-baseline median divided by max(baseline SD,1e-8). They never enter features. Levels use the verified endpoint change plus origin anchor; daily returns sum next increments through the verified business-horizon endpoint.',
        'Baseline is the actual V5.1 empty-text runtime; no historical card text is invented. FX/Rates use500 original draws; Factor/Equity uses1000; seed19. Native CRPS is normalized by ex-ante daily innovation SD×sqrt(h). Baseline and candidates share exactly the same scored cells and denominators.',
        f'Same **cross-fit evaluation ledger** perfect-location ratio: **{main["same_ledger_perfect_location_ratio"]:.6f}**. Full training+evaluation ledger perfect-location ratio: **{main["full_ledger_headroom"]["perfect_location_ratio"]:.6f}**. Capture uses the matching evaluation ratio, never the CEILING or full-training ratio.',
        '## Frozen channel sequence and models',
        'M0 zero shift; M1 metadata; M2 adds baseline forecast state; M3 adds own history; M4 adds lag-safe other markets; M5 adds regime summaries. Own windows1/5/21/63/126/252; peers1/5/21/63 at t-1 with self columns zero; regime5/21/63. Raw-unit forecast values are centered and scaled ex ante. All channel sequences remain in the report.',
        'Primary Ridge alpha grid.01/.1/1/10/100 is chosen by chronological inner delta-MSE. Secondary HGB uses depth3, learning rate.05,200 iterations,L2=1,seed19 and early_stopping=False; it is not tuned or selected as a submission. Primary predictions have only the fixed±10 numerical safety cap.',
        '## Ridge results']
    cols=[('Model','model','s'),('CRPS ratio','ratio','n'),('Oracle capture','oracle_capture_fraction','n'),('R²','delta_r2','n'),('Spearman','spearman','n'),('Sign accuracy','sign_accuracy','n')]
    for estimator in ('ridge','nonlinear'):
        if estimator=='nonlinear':parts.append('## SECONDARY_NONLINEAR_DIAGNOSTIC')
        parts.append(table([{'model':m,**v} for m,v in main['models'][estimator].items()],cols))
        parts.append(table([{'model':m,**v} for m,v in main['models'][estimator].items()],
            [('Model','model','s'),('Normalized CRPS','normalized_crps','n'),('Delta MSE','delta_mse','n'),('Pearson','pearson','n'),('Mean |shift|/SD','mean_abs_shift_over_sd','n'),('Calibration intercept','calibration_intercept','n'),('Calibration slope','calibration_slope','n')]))
    parts.extend(['M0 correlation and slope are undefined because its prediction is constant. Zero-shift sign accuracy is zero unless truth delta is exactly zero; it is not interpreted as a coin-flip forecast.',
        '## Incremental channel information',json.dumps(read('channel_increment_summary.json'),indent=2),
        'Negative gains remain; no channel was removed or retrained after inspecting scores.'])
    for estimator in ('ridge','nonlinear'):
        parts.append(f'## {estimator} outer-fold, group and horizon breakdown')
        for title,frame,field in (('Fold',folds,'fold'),('Group',groups,'group'),('Horizon',horizons,'horizon')):
            subset=frame[frame.estimator==estimator]
            parts.append(table(subset.to_dict('records'),[(title,field,'s'),('Model','model','s'),('Ratio','ratio','n'),('Perfect ratio','perfect_location_ratio','n'),('Oracle capture','oracle_capture_fraction','n')]))
    parts.extend(['## TRANSFER_DIAGNOSTIC — thirteen single-cell cards',
        table([{'model':m,**v} for m,v in single['models'].items()],[('Model','model','s'),('Baseline composite','baseline_composite','n'),('Predicted composite','ratio','n'),('Perfect composite','perfect_location_composite','n'),('Oracle capture','oracle_capture_fraction','n')]),
        'All24 cards have matched continuous-history as-of feature/model snapshots. Models train on continuous ledger labels mature before each card origin, with the full189-BDay exclusion. No card outcome is used for fitting, alpha selection or model choice. All five sequences are frozen before scoring. The transfer baseline retains original CEILING card text, so this probes transport from a no-text historical ledger into a text-conditioned baseline. The sample is too small and exposed to establish independent evidence.',
        '## TRANSFER_DIAGNOSTIC — eleven multi-cell cards',
        table([{'model':m,**v} for m,v in multi['models'].items()],[('Model','model','s'),('Marginal ratio','marginal_ratio','n'),('Joint ratio','joint_ratio','n'),('Tail ratio','tail_ratio','n'),('Composite ratio','ratio','n'),('Oracle capture','oracle_capture_fraction','n')]),
        'Components are recomputed by the existing scorer for every card after shifting. Composite ratios use the original V13 geometric card aggregation; component ratios are geometric means of applicable baseline-relative components. Centered draw geometry and pairing remain unchanged, but joint score can change when centers differ.',
        '## F1 safety and family transfer',
        table(families.to_dict('records'),[('Family','family','s'),('Model','model','s'),('Baseline','baseline_composite','n'),('Predicted','ratio','n'),('Perfect','perfect_location_composite','n'),('Marginal ratio','marginal_ratio','n'),('Joint before mean','joint_baseline_mean','n'),('Joint after mean','joint_candidate_mean','n'),('Joint ratio','joint_ratio','n')]),
        f'F1 safety for {best}: **{main["F1_SAFETY_VERDICT"]}**. The precommitted major joint-damage threshold is1.10. Each family has six cards; no broad OOS claim is made.',
        '## Negative controls and uncertainty',
        'A permutes delta times within asset/horizon using training-only donors. B permutes strictly previous-year numeric feature dates, retaining metadata. C rotates standardized labels across assets within training origin/horizon. D future-market mutations leave features and actual V5.1 forecasts identical. E additive updates preserve centered differences, variance and ranks; every transferred model/card passed.',
        table([{'control':k,**v} for k,v in main['control_comparisons'].items()],
              [('Control','control','s'),('Best sequence','control_best_model','s'),('CRPS ratio','ratio','n'),('Primary/control 95% interval','primary_over_control_ratio_95_interval','s')]),
        f'Negative controls clearly beaten under the frozen paired-block rule: **{main["negative_controls_clear"]}**.',
        table([{'model':f'{e} {m}',**v['bootstrap']} for e,vv in main['models'].items() for m,v in vv.items()],
              [('Model','model','s'),('Ratio 95% interval','ratio_95_interval','s'),('Capture 95% interval','capture_95_interval','s')]),
        'Intervals use2000 calendar-year block draws preserving every origin/asset/horizon in a sampled year. Overlapping long horizons remain dependent across adjacent years; these exposed-research intervals are descriptive, not a formal generalization proof.',
        '## Numerical safety and tests',
        'Outer caps by fold/model/estimator are in `crossfit_fit_audit.json`; transfer caps are in `single_cell_transfer.json`. The cap remains±10 regardless of score.',
        json.dumps(read('test_summary.json'),indent=2),
        '## Decision',
        f'READY_FOR_LOCATION_02 = **{gate}**  \nNEXT_RESEARCH_AXIS = **{axis}**  \nREADY_FOR_ONE_SHOT_SUBMISSION = **NO**',
        'A failure here means the specified observable feature universe and frozen models do not demonstrate enough location information under these gates. It does not prove mathematical impossibility, or prove that all other observable data contain no information. No scale, tail, copula, macro-surprise model or architecture search was performed.'])
    report=root/'LOCATION-01-PREDICTABLE-ORACLE-SHIFT-report.md'
    report.write_text('\n\n'.join(parts)+'\n')
    files=sorted(result.glob('*'))
    manifest={'pre_result_sha':pre_result_sha,'scorer_status':'RESEARCH_PROXY_ONLY',
        'files':{str(p.relative_to(root)):digest(p) for p in files if p.name!='artifact_manifest.json'},
        'report_sha256':digest(report),'private_ledger':{'sha256':digest(private/'ledger.parquet'),
            'rows':ledger['cells'],'date_range':ledger['date_range'],'schema':ledger['schema']},
        'private_predictions_sha256':digest(private/'predictions.npz'),
        'private_losses_sha256':digest(private/'losses.npz'),
        'private_transfer_models_sha256':digest(private/'transfer_models.pkl')}
    dump(result/'artifact_manifest.json',manifest)
    return main

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd())
    p.add_argument('--private',type=Path,required=True);p.add_argument('--pre-result-sha',required=True)
    a=p.parse_args();write(a.root,a.private,a.pre_result_sha)
