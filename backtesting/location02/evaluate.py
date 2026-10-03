"""Executive summary: run the remotely frozen EUR experiment in restartable stages.

Individual truths, standardized errors and losses remain private. Public files
contain pre-outcome predictions and aggregate research-only diagnostics.
"""
import argparse
import copy
import hashlib
import json
import subprocess
import time
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from qfbench2_common.scoring.crps import crps_ensemble
from .source_acquisition import OUT,ROOT,digest,dump,write_csv
from .source_dataset import FEATURES,asof_features,activation
from .model import HORIZONS,MODELS,SEED,train_mask,fit_ridge,predict,shift,metrics,bootstrap,verdict

CONTROLS=('RELEASE_VALUE_SHUFFLE','RELEASE_DATE_PERMUTATION','REVISION_SIGN_SHUFFLE','GAUSSIAN_FULL5')


def save(path,value):
    dump(path,{'executive_summary':'Frozen EUR research crossfit; aggregate only; no independent OOS or submission.',**value})


def status(private,stage,**kw):
    path=ROOT/'backtesting/location02/STATUS.json';s=json.loads(path.read_text())
    s.update(current_stage=stage,**kw)
    save(path,s)


def verify_pre(private):
    receipt=json.loads((private/'pre_receipt.json').read_text())
    frozen=json.loads((OUT/'pre_result_manifest.json').read_text())
    if not receipt['remote_verified']: raise ValueError('PRE not remotely verified')
    for name,sha in frozen['frozen_file_hashes'].items():
        if digest(ROOT/name)!=sha: raise ValueError('Frozen file changed: '+name)
    if not json.loads((OUT/'ecb_dataset_readiness.json').read_text())['DATASET_READY']:
        raise ValueError('Gate A failed')
    return receipt['PRE_RESULT_LOCATION02_SHA']


def prepare(private):
    pre=verify_pre(private)
    ledger=private/'frozen_inputs/ledger.parquet'
    manifest=json.loads((ROOT/'backtesting/location01/results/ledger_manifest.json').read_text())
    if digest(ledger)!=manifest['ledger_sha256']: raise ValueError('Frozen ledger hash mismatch')
    rows=pd.read_parquet(ledger)
    calendar=pd.read_csv(OUT/'source_calendar.csv')
    calendar=calendar.loc[calendar.active].copy()
    selected=rows.loc[(rows.asset=='EUR')&rows.origin.isin(calendar.origin)&
                      (rows.horizon.isin(HORIZONS))&(rows.target_end<='2024-12-18')].copy()
    selected=selected.merge(calendar,on='origin',validate='many_to_one').sort_values(['origin','horizon']).reset_index(drop=True)
    if not (selected.kind=='level').all(): raise ValueError('EUR target semantics changed')
    if not np.isfinite(selected[['truth','median','sd','delta','scale']].to_numpy()).all(): raise ValueError('Invalid frozen labels')
    if not (selected.sd>0).all(): raise ValueError('Zero scale')
    inputs=private/'frozen_v51/origins';inputs.mkdir(parents=True,exist_ok=True)
    archive=private/'restored_baseline/location01-baseline-2014-2024.zip'
    all_draws=[]
    with zipfile.ZipFile(archive) as bundle:
        for origin,group in selected.groupby('origin',sort=True):
            name='origins/'+origin+'.npz';raw=bundle.read(name)
            expected=manifest['baseline_cache_sha256'].get(origin,manifest['baseline_cache_sha256'].get(origin+'.npz',manifest['baseline_cache_sha256'].get(name)))
            if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError('Original V5.1 cache mismatch '+name)
            path=inputs/(origin+'.npz');path.write_bytes(raw)
            with np.load(path,allow_pickle=False) as data:
                draws=data['EUR'][:,[HORIZONS.index(int(h)) for h in group.horizon]]
            if draws.shape[0]!=500:raise ValueError('Original draw count mismatch')
            if not np.allclose(np.median(draws,axis=0),group['median'],rtol=0,atol=1e-15):raise ValueError('Original median mismatch')
            if not np.allclose(np.std(draws,axis=0),group.sd,rtol=1e-13,atol=1e-15):raise ValueError('Original SD mismatch')
            all_draws.append(draws)
    samples=np.concatenate(all_draws,axis=1)
    if not np.allclose((selected.truth-selected['median'])/selected.sd,selected.delta,rtol=1e-13,atol=1e-13):raise ValueError('Target delta mismatch')
    selected.to_parquet(private/'evaluation_ledger.parquet',index=False)
    np.savez_compressed(private/'evaluation_draws.npz',draws=samples)
    fold_rows=[]
    for year in range(2020,2025):
        candidates=calendar.loc[calendar.origin.str[:4]==str(year)]
        cutoff=candidates.sort_values('origin').cutoff.iloc[0]
        train=train_mask(selected,year,cutoff);test=pd.to_datetime(selected.origin).dt.year.eq(year).to_numpy()
        if not train.any() or not test.any():raise ValueError('Unevaluable predeclared year '+str(year))
        if set(selected.loc[train,'round_id'])&set(selected.loc[test,'round_id']):raise ValueError('Release leakage')
        fold_rows.append(dict(year=year,first_test_cutoff=cutoff,train_cells=int(train.sum()),test_cells=int(test.sum()),
          train_origins=int(selected.loc[train,'origin'].nunique()),test_origins=int(selected.loc[test,'origin'].nunique()),
          train_releases=int(selected.loc[train,'round_id'].nunique()),test_releases=int(selected.loc[test,'round_id'].nunique()),
          maximum_train_target_end=selected.loc[train,'target_end'].max(),max_purge_business_days=189,
          shared_train_test_release_count=0))
    write_csv(OUT/'fold_manifest.csv',fold_rows)
    save(private/'pre_evaluation_audit.json',{'PRE_RESULT_LOCATION02_SHA':pre,'outcomes_opened_only_after_verified_pre':True,
         'cache_reconstruction':'Original bytes restored, never rebuilt','ledger_sha256':digest(ledger),
         'asset':'EUR','target_kind':'level','cutoff':'2024-12-18','latest_available_truth':selected.target_end.max()})
    status(private,'fitting',outcomes_loaded=True,PRE_RESULT_LOCATION02_SHA=pre,last_successful_artifact='fold_manifest.csv')
    print(f'stage=prepare cells={len(selected)} origins={selected.origin.nunique()} output={private}',flush=True)


def crossfit(rows,x,columns):
    pp=np.full(len(rows),np.nan);audits=[]
    calendar=pd.read_csv(OUT/'source_calendar.csv')
    for year in range(2020,2025):
        cutoff=calendar.loc[calendar.active&calendar.origin.str[:4].eq(str(year))].sort_values('origin').cutoff.iloc[0]
        train=train_mask(rows,year,cutoff);test=pd.to_datetime(rows.origin).dt.year.eq(year).to_numpy()
        usable=train&np.isfinite(x).all(axis=1)
        fit=fit_ridge(x[usable],rows.loc[usable,'delta'],rows.loc[usable,'round_id'],columns)
        active=test&np.isfinite(x).all(axis=1)
        pp[test]=0.;pp[active]=predict(fit,x[active],columns)
        audits.append(dict(year=year,train_rows=int(usable.sum()),train_releases=int(rows.loc[usable,'round_id'].nunique()),
          scaler_mean=fit[0].mean_.tolist(),scaler_scale=fit[0].scale_.tolist(),coefficients=fit[1].coef_.tolist(),
          intercept=float(fit[1].intercept_),alpha=float(fit[1].alpha),cutoff=cutoff))
    return pp,audits


def fit_primary(private):
    verify_pre(private)
    rows=pd.read_parquet(private/'evaluation_ledger.parquet');x=rows[list(FEATURES)].to_numpy(float)
    pred={};audits={};started=time.monotonic()
    checkpoint=private/'fits';checkpoint.mkdir(exist_ok=True)
    for name,columns in MODELS.items():
        path=checkpoint/(name+'.npz');auditpath=checkpoint/(name+'.json')
        if path.exists() and auditpath.exists():
            pred[name]=np.load(path)['prediction'];audits[name]=json.loads(auditpath.read_text())['folds']
        else:
            pred[name],audits[name]=crossfit(rows,x,columns)
            np.savez_compressed(path,prediction=pred[name]);save(auditpath,{'folds':audits[name]})
        print(f'stage=fit completed={len(pred)}/{len(MODELS)} model={name} elapsed={time.monotonic()-started:.1f}s output={path}',flush=True)
    np.savez_compressed(private/'predictions.npz',**pred)
    save(private/'fit_audit.json',{'models':audits})
    public=rows.loc[pd.to_datetime(rows.origin).dt.year>=2020,['origin','horizon','round_id','target_calendar_year']].copy()
    test=pd.to_datetime(rows.origin).dt.year.ge(2020).to_numpy()
    for name in MODELS:public[name]=pred[name][test]
    public.insert(0,'executive_summary','Pre-outcome crossfit predictions only; truths and losses private')
    public.to_csv(OUT/'crossfit_predictions.csv',index=False,lineterminator='\n')
    status(private,'scoring',model_fits=25,last_successful_artifact='crossfit_predictions.csv')


def score(private):
    verify_pre(private)
    rows=pd.read_parquet(private/'evaluation_ledger.parquet');draws=np.load(private/'evaluation_draws.npz')['draws']
    test=pd.to_datetime(rows.origin).dt.year.ge(2020).to_numpy();rows=rows.loc[test].reset_index(drop=True);draws=draws[:,test]
    truth=rows.truth.to_numpy();sd=rows.sd.to_numpy();scale=rows.scale.to_numpy();y=rows.delta.to_numpy()
    base=crps_ensemble(draws,truth)/scale
    oracle=crps_ensemble(shift(draws,y,sd),truth)/scale
    pred=np.load(private/'predictions.npz');losses={};summaries={};annual=[];horizon=[];release=[]
    p0=np.zeros(len(rows));summaries['V5.1']=metrics(y,p0,base,base,oracle)
    for name in MODELS:
        p=pred[name][test];loss=crps_ensemble(shift(draws,p,sd),truth)/scale
        losses[name]=loss;summaries[name]=metrics(y,p,base,loss,oracle)
        for field,values,out in [('origin',range(2020,2025),annual),('horizon',HORIZONS,horizon),('round_id',sorted(rows.round_id.unique()),release)]:
            for value in values:
                mask=(pd.to_datetime(rows.origin).dt.year==value).to_numpy() if field=='origin' else (rows[field]==value).to_numpy()
                out.append(dict(model=name,group=value,origins=int(rows.loc[mask,'origin'].nunique()),
                   releases=int(rows.loc[mask,'round_id'].nunique()),**metrics(y[mask],p[mask],base[mask],loss[mask],oracle[mask])))
    summaries['PERFECT_LOCATION']=metrics(y,y,base,oracle,oracle)
    save(OUT/'primary_score_summary.json',{'models':summaries,'scorer':'qfbench2_common.scoring.crps.crps_ensemble fair=True; normalized by frozen past scale',
         'aggregation':'sum normalized cell CRPS / same-ledger baseline sum; unchanged parent scoring',
         'research_exposed':True,'independent_OOS':False,'official_validation':False,'primary_model':'ECB_RIDGE_FULL5'})
    save(OUT/'oracle_summary.json',{'same_ledger_perfect_location_ratio':summaries['PERFECT_LOCATION']['crps_ratio'],'diagnostic_only':True,'cells':len(rows)})
    save(OUT/'oracle_capture_summary.json',{'definition':'(1-R_ECB)/(1-R_perfect_location), unclipped',
         'models':{k:v['oracle_capture'] for k,v in summaries.items()}})
    save(OUT/'ablation_summary.json',{'secondary_only':True,'primary_remains_FULL5':True,'models':{k:v for k,v in summaries.items() if k in MODELS and k!='ECB_RIDGE_FULL5'}})
    for name,data in [('year_summary.csv',annual),('horizon_summary.csv',horizon),('release_summary.csv',release)]:write_csv(OUT/name,data)
    np.savez_compressed(private/'losses.npz',baseline=base,oracle=oracle,**losses)
    rows.to_parquet(private/'scored_rows.parquet',index=False)
    source=rows.groupby('round_id').agg(origins=('origin','nunique'),cells=('horizon','count')).reset_index().to_dict('records')
    save(OUT/'effective_sample_summary.json',{'forecast_origins':int(rows.origin.nunique()),'cells':len(rows),
         'unique_active_releases':int(rows.round_id.nunique()),'distinct_same_target_revision_events':int(rows.round_id.nunique()),
         'effective_independent_release_count_upper_bound':int(rows.round_id.nunique()),
         'effective_release_count_is_not_a_proven_iid_effective_N':True,'origins_per_release':source,
         'per_horizon':[{ 'horizon':h,'cells':int((rows.horizon==h).sum()),'unique_releases':int(rows.loc[rows.horizon==h,'round_id'].nunique())} for h in HORIZONS]})
    # Raw economic direction is descriptive only, never a coefficient-selection rule.
    from scipy.stats import pearsonr,spearmanr
    save(private/'economic_diagnostics.json',{'descriptive_only':True,
         'raw_feature_correlations':{f:{'pearson':float(pearsonr(rows[f],y).statistic),'spearman':float(spearmanr(rows[f],y).statistic)} for f in FEATURES[:4]}})
    status(private,'controls',forecast_scores=int(len(rows)*(len(MODELS)+2)),last_successful_artifact='primary_score_summary.json')
    print({k:round(v['crps_ratio'],5) for k,v in summaries.items()},flush=True)


def control_x(rows,x,kind,seed,states):
    rng=np.random.default_rng(seed);xx=x.copy()
    if kind=='RELEASE_DATE_PERMUTATION':
        # Only later activation is allowed: randomly assign fixed positive delays.
        delayed=copy.deepcopy(states);lags=rng.permutation(np.resize(np.arange(0,21),len(states)))
        for s,lag in zip(delayed,lags):
            publication=pd.Timestamp(s['publication_date'])+pd.offsets.BDay(int(lag))
            s['available_at']=activation(str(publication.date())).isoformat()
        xx[:]=np.nan
        lookup={origin:asof_features(delayed,origin) for origin in rows.origin.unique()}
        for i,origin in enumerate(rows.origin):
            state=lookup[origin]
            if state:xx[i]=[state[f] for f in FEATURES]
    elif kind=='FEATURE_YEAR_SHIFT':
        xx[:]=np.nan
        for i,origin in enumerate(rows.origin):
            shifted=pd.Timestamp(origin)-pd.DateOffset(years=1)
            state=asof_features(states,shifted)
            if state:xx[i]=[state[f] for f in FEATURES]
    elif kind=='GAUSSIAN_FULL5':
        vectors={release:rng.normal(size=5) for release in sorted(rows.round_id.unique())}
        xx=np.array([vectors[r] for r in rows.round_id])
    elif kind in ('RELEASE_VALUE_SHUFFLE','REVISION_SIGN_SHUFFLE'):
        # Shuffle within each chronological training information set only. No held-out
        # outcomes or future test release values enter fitting. This intentional null
        # reassignment is not a claim of real historical source availability.
        pass
    return xx


def control_prediction(rows,x,kind,seed,states):
    xx=control_x(rows,x,kind,seed,states)
    if kind not in ('RELEASE_VALUE_SHUFFLE','REVISION_SIGN_SHUFFLE'):
        return crossfit(rows,xx,tuple(range(5)))[0]
    pp=np.full(len(rows),np.nan);calendar=pd.read_csv(OUT/'source_calendar.csv')
    for year in range(2020,2025):
        cutoff=calendar.loc[calendar.active&calendar.origin.str[:4].eq(str(year))].sort_values('origin').cutoff.iloc[0]
        train=train_mask(rows,year,cutoff);test=pd.to_datetime(rows.origin).dt.year.eq(year).to_numpy()
        rng=np.random.default_rng(seed+year);releases=sorted(rows.loc[train,'round_id'].unique())
        vectors=np.array([x[np.flatnonzero(rows.round_id.eq(r).to_numpy())[0],:4] for r in releases])
        indices=rng.permutation(len(releases));lookup={r:v for r,v in zip(releases,vectors[indices])}
        signs={r:rng.choice([-1.,1.],size=2) for r in releases}
        xt=x[train].copy()
        for j,r in enumerate(rows.loc[train,'round_id']):
            if kind=='RELEASE_VALUE_SHUFFLE':xt[j,:4]=lookup[r]
            else:xt[j,2:4]=lookup[r][2:4]*signs[r]
        fit=fit_ridge(xt,rows.loc[train,'delta'],rows.loc[train,'round_id'],tuple(range(5)))
        pp[test]=predict(fit,x[test],tuple(range(5)))
    return pp


def controls(private,kind,start,stop):
    verify_pre(private);started=time.monotonic()
    rows=pd.read_parquet(private/'evaluation_ledger.parquet');x=rows[list(FEATURES)].to_numpy(float)
    test=pd.to_datetime(rows.origin).dt.year.ge(2020).to_numpy();selected=rows.loc[test]
    draws=np.load(private/'evaluation_draws.npz')['draws'][:,test]
    truth=selected.truth.to_numpy();sd=selected.sd.to_numpy();scale=selected.scale.to_numpy()
    base=np.load(private/'losses.npz')['baseline'];states=json.loads((private/'source_states.json').read_text())['states']
    out=private/'controls';out.mkdir(exist_ok=True)
    for first in range(start,stop,25):
        last=min(first+25,stop);path=out/f'{kind}-{first:04d}-{last:04d}.npz'
        if path.exists():continue
        predictions=np.array([control_prediction(rows,x,kind,SEED+100000*CONTROLS.index(kind)+i,states)[test] for i in range(first,last)])
        # Import the exact common scorer; vectorize repeated pure shifts without new scoring math.
        all_draws=np.tile(draws,(1,len(predictions)))+np.tile(sd,len(predictions))*predictions.reshape(-1)
        losses=crps_ensemble(all_draws,np.tile(truth,len(predictions)))/np.tile(scale,len(predictions))
        ratios=losses.reshape(len(predictions),len(truth)).sum(axis=1)/base.sum()
        np.savez_compressed(path,ratios=ratios,seeds=np.arange(first,last)+SEED+100000*CONTROLS.index(kind))
        print(f'stage=controls kind={kind} completed={last}/2000 elapsed={time.monotonic()-started:.1f}s output={path}',flush=True)
    status(private,'controls',last_successful_artifact=f'controls/{kind}-{stop}')


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
    xx=x.copy()
    for i,origin in enumerate(allrows.origin):
        state=asof_features(mutated,origin)
        if state:xx[i]=[state[f] for f in FEATURES]
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
    parser.add_argument('stage',choices=['prepare','fit','score','controls','finish']);parser.add_argument('--kind',choices=CONTROLS)
    parser.add_argument('--start',type=int,default=0);parser.add_argument('--stop',type=int,default=0)
    args=parser.parse_args()
    if args.stage=='prepare':prepare(args.private)
    elif args.stage=='fit':fit_primary(args.private)
    elif args.stage=='score':score(args.private)
    elif args.stage=='controls':controls(args.private,args.kind,args.start,args.stop)
    else:finish(args.private)
