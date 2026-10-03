"""Executive summary: finish frozen diagnostics while preserving the actual CSV feature representation.

Post-PRE validation-only correction: unchanged earlier source events reuse their
original CSV-parsed input bits. Reconstructing all rows from JSON would create
one-ULP serialization changes unrelated to future mutation. Primary fitting,
features, draws, scores, controls and interpretation remain the frozen code.
"""
import argparse
import copy
import json
from pathlib import Path
import numpy as np
import pandas as pd
from qfbench2_common.scoring.crps import crps_ensemble
from .source_acquisition import OUT, digest
from .source_dataset import FEATURES, asof_features
from .model import SEED, shift, bootstrap, verdict
from .evaluate import (CONTROLS,verify_pre,save,status,control_prediction,crossfit)

def mutated_feature_rows(rows, x, states, mutated):
    """Reuse original parsed bits for unchanged events; change future events only."""
    xx=x.copy()
    for i,origin in enumerate(rows.origin):
        state=asof_features(mutated,origin)
        if state != asof_features(states,origin) and state is not None:
            xx[i]=[state[f] for f in FEATURES]
    return xx


def finish(private):
    verify_pre(private)
    rows=pd.read_parquet(private/'scored_rows.parquet');allrows=pd.read_parquet(private/'evaluation_ledger.parquet')
    test=pd.to_datetime(allrows.origin).dt.year.ge(2020).to_numpy()
    pred=np.load(private/'predictions.npz')['ECB_RIDGE_FULL5'][test];y=rows.delta.to_numpy()
    loss=np.load(private/'losses.npz');base=loss['baseline'];candidate=loss['ECB_RIDGE_FULL5'];oracle=loss['oracle']
    primary=json.loads((OUT/'primary_score_summary.json').read_text())['models']['ECB_RIDGE_FULL5']
    negative={};raw={}
    for kind in CONTROLS:
        parts=sorted((private/'controls').glob(kind+'-*.npz'))
        values=np.concatenate([np.load(p)['ratios'] for p in parts])
        if len(values)!=2000:raise ValueError('Incomplete controls '+kind)
        raw[kind]=values
        negative[kind]=dict(permutations=len(values),median_ratio=float(np.median(values)),
             ratio_95_interval=np.quantile(values,[.025,.975]).tolist(),fraction_at_least_as_good=float(np.mean(values<=primary['crps_ratio'])))
    states=json.loads((private/'source_states.json').read_text())['states'];x=allrows[list(FEATURES)].to_numpy(float)
    lag=control_prediction(allrows,x,'FEATURE_YEAR_SHIFT',SEED,states)[test]
    draws=np.load(private/'evaluation_draws.npz')['draws'][:,test]
    lag_loss=crps_ensemble(shift(draws,lag,rows.sd.to_numpy()),rows.truth.to_numpy())/rows.scale.to_numpy()
    negative['FEATURE_YEAR_SHIFT']={'crps_ratio':float(lag_loss.sum()/base.sum()),'fixed_one_year_lag':True}
    earlier='2021-02-02';before=asof_features(states,earlier);mutated=copy.deepcopy(states)
    for s in mutated:
        if pd.Timestamp(s['available_at'])>pd.Timestamp('2022-01-01',tz='UTC'):
            for f in FEATURES[:4]:s[f]+=999.
    if asof_features(mutated,earlier)!=before:raise ValueError('Future source mutation changed earlier state')
    # At a past fitting cutoff, future ECB rows cannot enter any earlier source state.
    for origin in allrows.loc[allrows.origin<'2022-01-01','origin'].unique():
        if asof_features(mutated,origin)!=asof_features(states,origin):raise ValueError('Future mutation violated asof')
    xx=mutated_feature_rows(allrows,x,states,mutated)
    past=(pd.to_datetime(allrows.origin).dt.year>=2020)&(allrows.origin<'2022-01-01')
    changed_prediction=crossfit(allrows,xx,tuple(range(5)))[0]
    original_prediction=np.load(private/'predictions.npz')['ECB_RIDGE_FULL5']
    if not np.array_equal(changed_prediction[past],original_prediction[past]):raise ValueError('Future mutation changed actual earlier predictions')
    source_hash=digest(OUT/'source_calendar.csv');fake_y=y.copy();fake_y[:]=999.
    if digest(OUT/'source_calendar.csv')!=source_hash:raise ValueError('Outcome mutation changed source bytes')
    save(OUT/'negative_controls.json',{'controls':negative,'fixed_seed':SEED,
        'future_mutation':'All pre-2022 source inputs and actual 2020/2021 crossfit predictions bitwise identical after later-release mutation',
        'outcome_mutation':'Source module has no outcome interface; source calendar hash unchanged',
        'date_control':'Nonnegative publication delays randomly reassigned, never activate earlier than real publication',
        'value_revision_controls':'Within chronological training release blocks; held-out covariates and outcomes never shuffled into training'})
    boots={}
    for group in ['round_id','year']:
        bootrows=rows.copy();bootrows['year']=pd.to_datetime(rows.origin).dt.year
        boots[group]=bootstrap(bootrows,base,candidate,oracle,y,pred,group)
        print(f'stage=bootstrap completed={len(boots)}/2 block={group} output={OUT}',flush=True)
    save(OUT/'bootstrap_summary.json',{'replicates':5000,'primary':'release-block','secondary':'year-block','blocks':boots,'independent_OOS':False})
    gain=base-candidate
    release_gains={str(k):float(gain[ii].sum()) for k,ii in rows.groupby('round_id').groups.items()}
    year_values=pd.to_datetime(rows.origin).dt.year
    year_gains={str(k):float(gain[np.asarray(year_values==k)].sum()) for k in sorted(year_values.unique())}
    positive=sum(max(v,0) for v in release_gains.values());positive_year=sum(max(v,0) for v in year_gains.values())
    concentration={'largest_release_positive_gain_share':max(max(v,0) for v in release_gains.values())/positive if positive else None,
                   'largest_year_positive_gain_share':max(max(v,0) for v in year_gains.values())/positive_year if positive_year else None}
    concentration['dominated_by_one_release_or_year']=any(v is not None and v>.50 for v in concentration.values())
    annual=[r for r in pd.read_csv(OUT/'year_summary.csv').to_dict('records') if r['model']=='ECB_RIDGE_FULL5']
    decision=verdict(primary,annual,negative,boots['round_id'],concentration)
    next_axis={'NO':'FED-SLOOS-LOCATION-03; separate frozen branch, no ECB tuning','WEAK_YES':'ECB-SPF-ROBUSTNESS-03',
      'YES':'ECB-SPF-TRANSFER-03','STRONG_YES':'ECB-SPF-TRANSFER-03','INCONCLUSIVE':'Assess prospective EUR release count feasibility; no complexity increase'}[decision]
    save(OUT/'final_decision.json',{'LOCATION02_RESULT':decision,'DATASET_READY':True,'PRIMARY_MODEL':'ECB_RIDGE_FULL5',
       'primary':primary,'concentration':concentration,'NEXT':next_axis,'READY_FOR_SUBMISSION':False,
       'RESEARCH_EXPOSED':True,'INDEPENDENT_OOS':False,'no_secondary_ablation_rescue':True})
    np.savez_compressed(private/'control_distributions.npz',**raw)
    status(private,'report_tests',completed_stages=['environment','parent_recovery','source_acquisition','PIT_errata','dataset_readiness','implementation','research_tests','PRE_RESULT','evaluation','controls_bootstrap'],last_successful_artifact='final_decision.json')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private',type=Path,required=True)
    finish(parser.parse_args().private)
