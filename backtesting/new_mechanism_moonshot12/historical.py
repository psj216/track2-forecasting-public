"""Executive summary: select K on 2009–2015 only; test frozen retrieval on 2016–2024.

Cheap nulls compare exact empirical K-path distributions using the common
population CRPS on BOTH the primary and controls. The separate 1000-draw
forecast score uses the inherited fair estimator. No card outcome is opened.
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd

from .core import (DRAW_COUNT, KS, MIN_ANALOGS, SEED, YEARS, crps_ensemble,
                   digest, gate2, joint_draws, save)
from .run import OUT, private, query, status, verify

CONTROL_NAMES=('RANDOM_ANALOG','TIME_MATCHED_RANDOM','DISTANCE_SHUFFLE','REVERSED_SIMILARITY','CONSTANT_RECENT')


def load():
    p=private()
    return (np.load(p/'path_bank.npz',allow_pickle=False),json.loads((p/'bank_keys.json').read_text()),pd.read_parquet(p/'fingerprints.parquet'))


def selection_indices(distance, donors, k, kind='PRIMARY'):
    k=min(k,len(donors))
    if kind=='PRIMARY':return np.argsort(distance,kind='stable')[:k]
    if kind=='REVERSED_SIMILARITY':return np.argsort(-distance,kind='stable')[:k]
    if kind=='CONSTANT_RECENT':return np.argsort(-np.asarray(donors),kind='stable')[:k]
    raise ValueError(kind)


def fit_k_year(year):
    verify();data,keys,feat=load();p=private();dest=p/'selection'/str(year);dest.mkdir(parents=True,exist_ok=True)
    origins=data['origins'];ii=np.flatnonzero(pd.DatetimeIndex(origins).year==year);beg=time.monotonic()
    for done,oi in enumerate(ii,1):
        file=dest/f'{oi:04d}.npz'
        if file.exists():continue
        cols,donors,paths,dist,coverage=query(data,keys,feat,oi)
        losses={}
        for k in KS:
            if len(donors)<MIN_ANALOGS:loss=data['base'][oi,cols].copy()
            else:
                idx=selection_indices(dist,donors,k);draws,_=joint_draws(paths,idx,oi)
                loss=crps_ensemble(draws,data['truth'][oi,cols])/data['scale'][oi,cols]
            losses[f'K{k}']=loss
        np.savez_compressed(file,cols=cols,base=data['base'][oi,cols],donors=len(donors),**losses)
        if done%10==0 or done==len(ii):
            print(json.dumps(dict(stage='historical_K_selection',year=year,completed=done,total=len(ii),elapsed=round(time.monotonic()-beg,1),output=str(file))),flush=True)
    save(dest/'COMPLETE.json',dict(year=year,origins=len(ii)))


def select_k():
    verify();p=private();scores={k:[0.,0.] for k in KS};years=[]
    for year in range(2009,2016):
        dest=p/'selection'/str(year);assert (dest/'COMPLETE.json').exists()
        sums={k:0. for k in KS};base=0.;n=0
        for f in dest.glob('*.npz'):
            d=np.load(f);base+=float(d['base'].sum());n+=1
            for k in KS:sums[k]+=float(d[f'K{k}'].sum())
        for k in KS:scores[k][0]+=sums[k];scores[k][1]+=base
        years.append(dict(year=year,origins=n,ratios={k:sums[k]/base for k in KS}))
    ratios={k:x[0]/x[1] for k,x in scores.items()}
    chosen=min(KS,key=lambda k:(ratios[k],-k))
    result=dict(executive_summary='One K chosen on chronological 2009–2015 history only; no 2016–2024 or card loss in selection.',
        selected_K=chosen,ratios=ratios,selection_years=list(range(2009,2016)),test_years=list(YEARS),tie_break='larger K',years=years,card_outcomes_opened=False)
    save(OUT/'historical_k_selection.json',result);status('historical_K_selection',True,selected_K=chosen)
    print(json.dumps(result),flush=True)


def evaluate(year):
    verify();p=private();k=json.loads((OUT/'historical_k_selection.json').read_text())['selected_K']
    data,keys,feat=load();dest=p/'evaluation'/str(year);dest.mkdir(parents=True,exist_ok=True)
    origins=data['origins'];ii=np.flatnonzero(pd.DatetimeIndex(origins).year==year);beg=time.monotonic()
    for done,oi in enumerate(ii,1):
        file=dest/f'{oi:04d}.npz'
        if file.exists():continue
        cols,donors,paths,dist,coverage=query(data,keys,feat,oi)
        truth=data['truth'][oi,cols];scale=data['scale'][oi,cols];base=data['base'][oi,cols]
        model={};selected=np.array([],int)
        for kind in ['PRIMARY','REVERSED_SIMILARITY','CONSTANT_RECENT']:
            if len(donors)<MIN_ANALOGS:
                model[kind]=base.copy();model[kind+'_population']=base.copy();continue
            idx=selection_indices(dist,donors,k,kind);draws,sampled=joint_draws(paths,idx,oi)
            model[kind]=crps_ensemble(draws,truth)/scale
            model[kind+'_population']=crps_ensemble(paths[idx],truth,fair=False)/scale
            if kind=='PRIMARY':selected=idx
        # Private query cache: complete paths only; no new training predictors.
        np.savez_compressed(file,cols=cols,base=base,truth=truth,scale=scale,paths=paths,donors=donors,distance=dist,selected=selected,
                            origin=origins[oi],fallback=len(donors)<MIN_ANALOGS,**model)
        if done%10==0 or done==len(ii):
            print(json.dumps(dict(stage='historical_validation',year=year,completed=done,total=len(ii),elapsed=round(time.monotonic()-beg,1),output=str(file))),flush=True)
    save(dest/'COMPLETE.json',dict(year=year,origins=len(ii),K=k));status('historical_validation',year=year,completed_origins=len(ii))


def random_indices(n,k,donors,selected,kind,rng,current_origin_index):
    k=min(k,n)
    if kind=='RANDOM_ANALOG':return rng.choice(n,size=k,replace=False)
    if kind=='DISTANCE_SHUFFLE':return rng.permutation(n)[:k]  # Exactly a shuffled fingerprint/rank assignment on eligible past rows.
    if kind=='TIME_MATCHED_RANDOM':
        # Canonical origins are 5BD apart. Fixed age buckets in BUSINESS days:
        # <1260 (~5y), 1260–2520, >=2520. Match primary donor-age composition.
        ages=(current_origin_index-np.asarray(donors))*5
        buckets=np.digitize(ages,[1260,2520]);out=[]
        for b in range(3):
            count=int(np.sum(buckets[selected]==b));pool=np.flatnonzero(buckets==b)
            out.extend(rng.choice(pool,size=count,replace=False).tolist())
        return np.asarray(out,int)
    raise ValueError(kind)


def controls(year,kind,start,stop):
    verify();p=private();k=json.loads((OUT/'historical_k_selection.json').read_text())['selected_K']
    dest=p/'controls'/kind/str(year);dest.mkdir(parents=True,exist_ok=True);file=dest/f'{start:04d}-{stop:04d}.npz'
    if file.exists():return
    sums=np.zeros(stop-start);base=0.;primary=0.;beg=time.monotonic()
    for done,f in enumerate(sorted((p/'evaluation'/str(year)).glob('*.npz')),1):
        d=np.load(f);oi=int(f.stem);n=len(d['donors']);base+=float(d['base'].sum());primary+=float(d['PRIMARY_population'].sum())
        if bool(d['fallback']):sums+=d['base'].sum();continue
        indices=np.array([random_indices(n,k,d['donors'],d['selected'],kind,np.random.default_rng(np.random.SeedSequence([SEED,CONTROL_NAMES.index(kind)+1,rep,oi])),oi) for rep in range(start,stop)])
        # Common estimator evaluates all replicates simultaneously; no custom CRPS math.
        m=indices.shape[1];batch=d['paths'][indices].transpose(1,0,2);truth=np.tile(d['truth'],len(indices));scales=np.tile(d['scale'],len(indices))
        loss=crps_ensemble(batch.reshape(m,-1),truth,fair=False)/scales
        sums+=loss.reshape(len(indices),-1).sum(axis=1)
        if done%10==0:
            print(json.dumps(dict(stage='controls',kind=kind,year=year,reps=[start,stop],origins=done,elapsed=round(time.monotonic()-beg,1),output=str(file))),flush=True)
    np.savez_compressed(file,loss=sums,base=base,primary_population=primary,start=start,stop=stop,year=year)


def aggregation():
    verify();p=private();data,keys,feat=load();records=[];origin_rows=[]
    for year in YEARS:
        assert (p/'evaluation'/str(year)/'COMPLETE.json').exists()
        for f in sorted((p/'evaluation'/str(year)).glob('*.npz')):
            d=np.load(f);oi=int(f.stem);base=float(d['base'].sum());loss=float(d['PRIMARY'].sum())
            origin_rows.append(dict(origin_index=oi,origin=str(d['origin'])[:10],year=year,cells=len(d['cols']),base=base,loss=loss,ratio=loss/base,fallback=bool(d['fallback'])))
            for j,c in enumerate(d['cols']):
                a,h=keys['keys'][c]
                records.append(dict(origin=str(d['origin'])[:10],year=year,asset=a,horizon=h,kind=keys['kinds'][c],base=float(d['base'][j]),loss=float(d['PRIMARY'][j]),population=float(d['PRIMARY_population'][j]),reversed=float(d['REVERSED_SIMILARITY'][j]),recent=float(d['CONSTANT_RECENT'][j])))
    rows=pd.DataFrame(records);orig=pd.DataFrame(origin_rows);rows.to_parquet(p/'historical_cell_scores.parquet',index=False);orig.to_parquet(p/'historical_origin_scores.parquet',index=False)
    base=float(rows.base.sum());ratio=float(rows.loss.sum()/base);yr=rows.groupby('year')[['base','loss']].sum();yr['ratio']=yr.loss/yr.base
    equal={}
    for k in ['origin','year','asset','horizon']:equal[k]=float(np.mean([g.loss.sum()/g.base.sum() for _,g in rows.groupby(k)]))
    gains=rows.assign(gain=(rows.base-rows.loss).clip(lower=0));total=float(gains.gain.sum());year_gain=gains.groupby('year').gain.sum();asset_gain=gains.groupby('asset').gain.sum()
    controls={};primary_pop=float(rows.population.sum()/base)
    for name in CONTROL_NAMES[:3]:
        values=np.zeros(2000);count=np.zeros(2000,int)
        for y in YEARS:
            for f in sorted((p/'controls'/name/str(y)).glob('*.npz')):
                d=np.load(f);start=int(d['start']);stop=int(d['stop']);values[start:stop]+=d['loss'];count[start:stop]+=1
        assert (count==len(YEARS)).all(),(name,np.unique(count))
        ratios=values/base;p_value=float((1+np.sum(ratios<=primary_pop))/(len(ratios)+1))
        np.save(p/f'null_{name}.npy',ratios)
        controls[name]=dict(reps=2000,mean=float(ratios.mean()),quantiles=np.quantile(ratios,[.025,.05,.5,.95,.975]).tolist(),primary_population_ratio=primary_pop,MC_p=p_value,scoring='Same K empirical-measure CRPS fair=False on primary and null; separate actual1000-draw primary score fair=True.')
    for name,col in [('REVERSED_SIMILARITY','reversed'),('CONSTANT_RECENT','recent')]:controls[name]=dict(ratio=float(rows[col].sum()/base),reps=1,deterministic=True)
    save(OUT/'negative_controls.json',dict(executive_summary='Same complete-path eligible pools, no future donors; exact empirical population endpoint for cheap stochastic nulls.',seed=SEED,controls=controls,card_outcomes_opened=False))
    bootstrap={};rng=np.random.default_rng(SEED)
    for block in ['origin','year','asset']:
        g=rows.groupby(block)[['base','loss']].sum().to_numpy();result=[]
        for start in range(0,5000,250):
            idx=rng.integers(0,len(g),size=(250,len(g)));z=g[idx].sum(axis=1);result.extend((z[:,1]/z[:,0]).tolist())
        result=np.asarray(result);np.save(p/f'bootstrap_{block}.npy',result)
        bootstrap[block]=dict(reps=5000,blocks=len(g),CI95=np.quantile(result,[.025,.975]).tolist(),conditional_on_frozen_retrieval=True)
    save(OUT/'historical_bootstrap.json',dict(executive_summary='Whole origin/year/asset blocks; historical research remains exposed.',seed=SEED,blocks=bootstrap))
    summary=dict(executive_summary='Untuned nearest joint historical scenarios; 2016–2024 held forward of K selection.',
        selected_K=json.loads((OUT/'historical_k_selection.json').read_text())['selected_K'],ratio=ratio,
        equal_origin_ratio=equal['origin'],equal_year_ratio=equal['year'],asset_balanced_ratio=equal['asset'],horizon_balanced_ratio=equal['horizon'],
        median_origin_ratio=float(orig.ratio.median()),fraction_origins_improved=float((orig.ratio<1).mean()),
        origins=len(orig),cells=len(rows),assets=int(rows.asset.nunique()),fallback_origins=int(orig.fallback.sum()),
        improved_years=int((yr.ratio<1).sum()),years=yr.reset_index()[['year','ratio']].to_dict('records'),
        max_year_gross_share=float(year_gain.max()/total) if total else 0.,max_asset_gross_share=float(asset_gain.max()/total) if total else 0.,
        origin_upper95=bootstrap['origin']['CI95'][1],random_p=controls['RANDOM_ANALOG']['MC_p'],population_ratio=primary_pop,
        card_outcomes_opened=False,independent_OOS=False)
    passed=gate2(summary);summary['gate2_passed']=passed
    save(OUT/'historical_summary.json',summary)
    yr.reset_index()[['year','ratio']].to_csv(OUT/'historical_results.csv',index=False)
    for dim in ['asset','horizon','kind']:
        groups=rows.groupby(dim)[['base','loss']].sum();groups['ratio']=groups.loss/groups.base
        groups['cells']=rows.groupby(dim).size();groups.reset_index().drop(columns=['base','loss']).to_csv(OUT/f'historical_{dim}_results.csv',index=False)
    save(OUT/'concentration_summary.json',dict(executive_summary='All historical cells retained; gross gains are baseline-minus-loss positive parts.',year_share=(year_gain/total).to_dict() if total else {},asset_share=(asset_gain/total).to_dict() if total else {}))
    status('historical_kill_gate',True,gate2_passed=passed,card_evaluation_permitted=passed,selected_K=summary['selected_K'])
    print(json.dumps(summary),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['selection_year','select_k','evaluate','controls','aggregation']);p.add_argument('--year',type=int);p.add_argument('--kind');p.add_argument('--start',type=int);p.add_argument('--stop',type=int);a=p.parse_args()
    if a.stage=='selection_year':fit_k_year(a.year)
    elif a.stage=='select_k':select_k()
    elif a.stage=='evaluate':evaluate(a.year)
    elif a.stage=='controls':controls(a.year,a.kind,a.start,a.stop)
    else:aggregation()


if __name__=='__main__':main()
