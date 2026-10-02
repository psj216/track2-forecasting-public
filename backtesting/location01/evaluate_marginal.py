"""## Executive summary (read this first)

Open frozen cross-fitted scores once, on the same general historical ledger.
Import fair CRPS from the shared toolkit, rather than duplicating its formula.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from qfbench2_common.scoring.crps import crps_ensemble
from qfbench2_track_forecasting.location01.oracle_target import HORIZONS
from .build_location_ledger import dump,digest
from .negative_controls import CONTROLS
from .diagnostics import metrics,success
from .bootstrap import year_bootstrap

def evaluate(root,private,pre_result_sha):
    rows=pd.read_parquet(private/'ledger.parquet');pred=np.load(private/'predictions.npz')
    fold=pred['fold'];valid=fold>0;selected=rows.loc[valid].reset_index(drop=True)
    keys=('ridge','nonlinear',*CONTROLS)
    losses={k:np.zeros((6,int(valid.sum()))) for k in keys}
    base=np.zeros(int(valid.sum()));oracle=base.copy()
    fullbase=np.zeros(len(rows));fulloracle=fullbase.copy()
    original_to_test=np.full(len(rows),-1,int);original_to_test[valid]=np.arange(valid.sum())
    # Evaluate real original draw counts, never duplicated or resampled draws.
    for oi,(origin,indices) in enumerate(rows.groupby('origin',sort=True).groups.items()):
        archive=np.load(private/'origins'/f'{origin}.npz')
        for asset,asset_indices in rows.loc[list(indices)].groupby('asset').groups.items():
            asset_indices=np.asarray(asset_indices)
            hh=[HORIZONS.index(int(h)) for h in rows.loc[asset_indices,'horizon']]
            draws=archive[asset][:,hh];truth=rows.loc[asset_indices,'truth'].to_numpy()
            median=rows.loc[asset_indices,'median'].to_numpy();sd=rows.loc[asset_indices,'sd'].to_numpy()
            scale=rows.loc[asset_indices,'scale'].to_numpy()
            fullbase[asset_indices]=crps_ensemble(draws,truth)/scale
            fulloracle[asset_indices]=crps_ensemble(draws+(truth-median),truth)/scale
            keep=valid[asset_indices]
            if not keep.any():continue
            asset_indices=asset_indices[keep];destination=original_to_test[asset_indices]
            draws=draws[:,keep];truth=truth[keep];sd=sd[keep];scale=scale[keep]
            base[destination]=fullbase[asset_indices];oracle[destination]=fulloracle[asset_indices]
            for key in keys:
                for m in range(6):
                    shifted=draws+pred[key][m,asset_indices]*sd
                    losses[key][m,destination]=crps_ensemble(shifted,truth)/scale
        archive.close()
        if oi%100==0:print(f'scoring origin {oi+1} {origin}',flush=True)
    years=pd.to_datetime(selected.origin).dt.year.to_numpy()
    y=selected.delta.to_numpy();out={'pre_result_sha':pre_result_sha,
        'status':'RESEARCH_EXPOSED_LEAKAGE_FREE_CROSS_FIT','scorer_status':'RESEARCH_PROXY_ONLY',
        'evaluation_cells':len(selected),'evaluation_origins':int(selected.origin.nunique()),
        'evaluation_date_range':[selected.origin.min(),selected.origin.max()],
        'same_ledger_perfect_location_ratio':float(oracle.sum()/base.sum()),'models':{}}
    out['full_ledger_headroom']={'cells':len(rows),'origins':int(rows.origin.nunique()),
        'perfect_location_ratio':float(fulloracle.sum()/fullbase.sum()),
        'note':'includes 2001-2009 training origins; capture uses exactly matching cross-fit evaluation cells only'}
    boot={};fold_table=[];group_table=[];horizon_table=[];negative={}
    testfold=fold[valid]
    for key in keys:
        summaries={}
        for m in range(6):
            pp=pred[key][m,valid];cc=losses[key][m]
            result=metrics(y,pp,base,cc,oracle)
            result['fold_ratios']=[]
            for f in range(1,5):
                mask=testfold==f;v=metrics(y[mask],pp[mask],base[mask],cc[mask],oracle[mask])
                result['fold_ratios'].append(v['ratio'])
                fold_table.append({'estimator':key,'model':f'M{m}','fold':f,**v})
            for group in ('FX','Rates','Factor/Equity'):
                mask=(selected.group==group).to_numpy()
                group_table.append({'estimator':key,'model':f'M{m}','group':group,
                    **metrics(y[mask],pp[mask],base[mask],cc[mask],oracle[mask])})
            for h in HORIZONS:
                mask=(selected.horizon==h).to_numpy()
                horizon_table.append({'estimator':key,'model':f'M{m}','horizon':h,
                    **metrics(y[mask],pp[mask],base[mask],cc[mask],oracle[mask])})
            result['bootstrap']=year_bootstrap(years,base,cc,oracle)
            summaries[f'M{m}']=result;boot[f'{key}_M{m}']=result['bootstrap']
        if key in CONTROLS:negative[key]=summaries
        else:out['models'][key]=summaries
    ridge_best=min(range(1,6),key=lambda m:out['models']['ridge'][f'M{m}']['ratio'])
    nonlinear_best=min(range(1,6),key=lambda m:out['models']['nonlinear'][f'M{m}']['ratio'])
    comparisons={}; clear=True
    for control in CONTROLS:
        best=min(range(1,6),key=lambda m:negative[control][f'M{m}']['ratio'])
        interval=year_bootstrap(years,losses[control][best],losses['ridge'][ridge_best])
        comparisons[control]={'control_best_model':f'M{best}',
            'ratio':negative[control][f'M{best}']['ratio'],
            'primary_over_control_ratio_95_interval':interval['ratio_95_interval']}
        clear=clear and interval['ratio_95_interval'][1]<1.
    best_metric=out['models']['ridge'][f'M{ridge_best}']
    gate=success(best_metric,best_metric['fold_ratios'],clear)
    if gate=='NO':
        # The same primary controls are a conservative descriptive comparison;
        # nonlinear-only success remains diagnostic, never a submission choice.
        nm=out['models']['nonlinear'][f'M{nonlinear_best}']; nclear=True
        for control,info in comparisons.items():
            cm=int(info['control_best_model'][1:])
            ci=year_bootstrap(years,losses[control][cm],losses['nonlinear'][nonlinear_best])
            nclear=nclear and ci['ratio_95_interval'][1]<1.
        if success(nm,nm['fold_ratios'],nclear)!='NO':gate='NONLINEAR_ONLY_SIGNAL'
    out.update(best_precommitted_ridge=f'M{ridge_best}',best_nonlinear_diagnostic=f'M{nonlinear_best}',
        negative_controls_clear=bool(clear),control_comparisons=comparisons,
        READY_FOR_LOCATION_02=gate,READY_FOR_ONE_SHOT_SUBMISSION='NO')
    results=root/'backtesting/location01/results'
    dump(results/'crossfit_summary.json',out)
    dump(results/'negative_controls.json',{'training_controls':negative,'comparisons':comparisons,
         'D_future_mutation':'tested: as-of features and real V5.1 draws unchanged',
         'E_draw_geometry':'tested and checked for every transferred model/card',
         'separation_gate':'paired year-bootstrap primary/control upper 95% ratio <1 for every control, comparing each control best M1-M5'})
    dump(results/'bootstrap_summary.json',{'method':'2000 paired calendar-year block replicates; no cell resampling',
         'interpretation':'research-exposed cross-fit uncertainty; not independent generalization proof','models':boot})
    dump(results/'oracle_capture_summary.json',{
         'definition':'(1-candidate_ratio)/(1-perfect_location_ratio), not clipped',
         'same_ledger_perfect_location_ratio':out['same_ledger_perfect_location_ratio'],
         'models':{k:{m:{f:v[f] for f in ('ratio','perfect_location_ratio','oracle_capture_fraction')}
                     for m,v in vv.items()} for k,vv in out['models'].items()}})
    dump(results/'channel_increment_summary.json',{k:{
        name: vv[f'M{a}']['ratio']-vv[f'M{b}']['ratio']
        for name,a,b in (('Gain_F',1,2),('Gain_O',2,3),('Gain_X',3,4),('Gain_R',4,5))}
        for k,vv in out['models'].items()})
    pd.DataFrame(fold_table).to_csv(results/'fold_summary.csv',index=False)
    pd.DataFrame(group_table).to_csv(results/'group_summary.csv',index=False)
    pd.DataFrame(horizon_table).to_csv(results/'horizon_summary.csv',index=False)
    np.savez_compressed(private/'losses.npz',baseline=base,oracle=oracle,years=years,
                        row_index=np.flatnonzero(valid),**losses)
    dump(results/'crossfit_fit_audit.json',json.loads((private/'crossfit_audit.json').read_text()))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd())
    p.add_argument('--private',type=Path,required=True);p.add_argument('--pre-result-sha',required=True)
    a=p.parse_args();evaluate(a.root,a.private,a.pre_result_sha)
