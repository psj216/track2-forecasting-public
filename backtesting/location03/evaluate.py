"""Executive summary: remotely frozen, restartable US-rate location-only evaluation.

Private labels and cell scores never enter public artifacts. All CRPS math is
imported from the pinned shared toolkit. No primary feature or model selection.
"""
import argparse,json,hashlib,zipfile,subprocess,time,copy
from pathlib import Path
import numpy as np
import pandas as pd
from qfbench2_common.scoring.crps import crps_ensemble
from .source_dataset import FEATURES,save,write_csv,digest,asof_features,cutoff,activation
from .model import *
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'backtesting/location03/results'
CONTROLS=('RELEASE_VALUE_SHUFFLE','RELEASE_DATE_PERMUTATION','STANDARDS_SIGN_SHUFFLE','DEMAND_SIGN_SHUFFLE','GAUSSIAN_FULL5')

def status(stage,**kw):
 path=ROOT/'backtesting/location03/STATUS.json';s=json.loads(path.read_text());s.update(current_stage=stage,**kw);s['stages'][stage]='complete';save(path,s)

def verify_pre(private):
 r=json.loads((private/'pre_receipt.json').read_text());m=json.loads((OUT/'pre_result_manifest.json').read_text())
 if not r['remote_verified'] or not json.loads((OUT/'sloos_dataset_readiness.json').read_text())['DATASET_READY']:raise ValueError('PRE/Gate A not verified')
 for name,sha in m['frozen_file_hashes'].items():
  if digest(ROOT/name)!=sha:raise ValueError('Frozen implementation changed: '+name)
 for doc in json.loads((OUT/'sloos_document_manifest.json').read_text())['documents']:
  if digest(private/'source'/doc['path'])!=doc['sha256']:raise ValueError('Original source bytes changed: '+doc['path'])
 return r['PRE_RESULT_LOCATION03_SHA']

def prepare(private):
 pre=verify_pre(private);manifest=json.loads((ROOT/'backtesting/location01/results/ledger_manifest.json').read_text())
 path=private/'frozen_inputs/ledger.parquet';path.parent.mkdir(exist_ok=True)
 if not path.exists():
  with zipfile.ZipFile(private/'restored/LOCATION02-private-recovery.zip') as z:path.write_bytes(z.read('private/frozen_inputs/ledger.parquet'))
 if digest(path)!=manifest['ledger_sha256']:raise ValueError('Frozen continuous ledger changed')
 rows=pd.read_parquet(path);cal=pd.read_csv(OUT/'source_calendar.csv',float_precision='round_trip');cal=cal.loc[cal.active]
 rows=rows.loc[rows.asset.isin(ASSETS)&rows.horizon.isin(HORIZONS)&rows.origin.isin(cal.origin)&(rows.target_end<='2024-12-18')].merge(cal,on='origin',validate='many_to_one').sort_values(['origin','asset','horizon']).reset_index(drop=True)
 if not (rows.kind=='level').all() or not np.isfinite(rows[['truth','median','sd','delta','scale']].to_numpy()).all() or not (rows.sd>0).all():raise ValueError('Invalid frozen UST level target')
 archives={k:zipfile.ZipFile(private/'restored_baseline'/name) for k,name in [(0,'location01-baseline-2001-2013.zip'),(1,'location01-baseline-2014-2024.zip')]};draws=np.empty((500,len(rows)));cachedir=private/'frozen_v51/origins';cachedir.mkdir(parents=True,exist_ok=True)
 for i,(origin,g) in enumerate(rows.groupby('origin'),1):
  raw=archives[int(origin[:4])>=2014].read('origins/'+origin+'.npz');key=origin+'.npz';expected=manifest['baseline_cache_sha256'].get(key,manifest['baseline_cache_sha256'].get(origin))
  if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('V5.1 bytes changed '+origin)
  p=cachedir/key;p.write_bytes(raw)
  with np.load(p,allow_pickle=False) as data:
   for ii,row in g.iterrows():draws[:,ii]=data[row.asset][:,HORIZONS.index(int(row.horizon))]
  if i%20==0:print(f'PREPARE {i}/{rows.origin.nunique()} origin={origin} output={cachedir}',flush=True)
 for z in archives.values():z.close()
 if not np.allclose(np.median(draws,axis=0),rows['median'],atol=1e-14,rtol=0) or not np.allclose(np.std(draws,axis=0),rows.sd,atol=1e-14,rtol=1e-13):raise ValueError('Frozen draw geometry inconsistent with ledger')
 if not np.allclose((rows.truth-rows['median'])/rows.sd,rows.delta,atol=1e-12,rtol=1e-12):raise ValueError('Frozen target mismatch')
 rows.to_parquet(private/'evaluation_ledger.parquet',index=False);np.savez_compressed(private/'evaluation_draws.npz',draws=draws)
 save(private/'pre_evaluation_audit.json',{'PRE_RESULT_LOCATION03_SHA':pre,'new_outcomes_opened_only_after_remote_pre':True,'ledger_sha256':digest(path),'draws_loaded_exact_original_bytes':True,'cells':len(rows),'origins':int(rows.origin.nunique())})
 status('prepare',new_outcomes_accessed=True,PRE_RESULT_LOCATION03_SHA=pre)

def folds(rows,x=None,release_override=None):
 for asset in ASSETS:
  for horizon in HORIZONS:
   ii=np.flatnonzero((rows.asset==asset)&(rows.horizon==horizon));g=rows.iloc[ii].copy().reset_index(drop=True)
   if release_override is not None:g['release_id']=release_override[ii]
   for year in YEARS:
    test=(pd.to_datetime(g.origin).dt.year==year).to_numpy()
    if not test.any():continue
    c=g.loc[test].sort_values('origin').cutoff.iloc[0];train=train_mask(g,year,c)
    if x is not None:train&=np.isfinite(x[ii]).all(axis=1)&g.release_id.notna().to_numpy()
    if g.loc[train,'release_id'].nunique()<MIN_RELEASES:yield asset,horizon,year,ii[train],ii[test],c,False
    else:yield asset,horizon,year,ii[train],ii[test],c,True

def fit(private):
 verify_pre(private);rows=pd.read_parquet(private/'evaluation_ledger.parquet');x=rows[list(FEATURES)].to_numpy();folder=private/'fits';folder.mkdir(exist_ok=True);pred={};audit=[];primary_mask=np.zeros(len(rows),bool)
 for name,cols in MODELS.items():
  p=np.full(len(rows),np.nan)
  for asset,horizon,year,train,test,c,valid in folds(rows,x):
   path=folder/f'{name}-{asset}-{horizon}-{year}.npz'
   if not valid:
    if name==next(iter(MODELS)):audit.append(dict(asset=asset,horizon=horizon,year=year,valid=False,train_rows=len(train),train_releases=int(rows.iloc[train].release_id.nunique()),test_rows=len(test),first_test_cutoff=c,maximum_train_target_end=rows.iloc[train].target_end.max() if len(train) else '',shared_release_count=0))
    continue
   if path.exists():p[test]=np.load(path)['prediction']
   else:
    f=fit_ridge(x[train],rows.delta.to_numpy()[train],rows.release_id.to_numpy()[train],cols,name!='SLOOS_FULL5_UNWEIGHTED');pp=predict(f,x[test],cols);p[test]=pp;np.savez_compressed(path,prediction=pp)
    save(path.with_suffix('.json'),{'asset':asset,'horizon':horizon,'year':year,'alpha':f[1].alpha,'scaler_mean':f[0].mean_.tolist(),'scaler_scale':f[0].scale_.tolist(),'coefficient':f[1].coef_.tolist(),'intercept':float(f[1].intercept_)})
   if name==next(iter(MODELS)):
    primary_mask[test]=True;shared=len(set(rows.iloc[train].release_id)&set(rows.iloc[test].release_id));assert shared==0
    audit.append(dict(asset=asset,horizon=horizon,year=year,valid=True,train_rows=len(train),train_releases=int(rows.iloc[train].release_id.nunique()),test_rows=len(test),first_test_cutoff=c,maximum_train_target_end=rows.iloc[train].target_end.max(),shared_release_count=shared))
  pred[name]=p;print(f'FIT {name} completed asset-horizon annual folds output={folder}',flush=True)
 np.savez_compressed(private/'predictions.npz',**pred,eval_mask=primary_mask);write_csv(OUT/'fold_manifest.csv',audit)
 pub=rows.loc[primary_mask,['origin','asset','horizon','release_id']].copy()
 for name in MODELS:pub[name]=pred[name][primary_mask]
 pub.insert(0,'executive_summary','Crossfit predictions only; private labels and cell losses omitted');pub.to_csv(OUT/'crossfit_predictions.csv',index=False)
 status('fit',fitted_models=len(MODELS),valid_cells=int(primary_mask.sum()))

def score(private):
 verify_pre(private);allrows=pd.read_parquet(private/'evaluation_ledger.parquet');pred=np.load(private/'predictions.npz');test=pred['eval_mask'];rows=allrows.loc[test].reset_index(drop=True);draws=np.load(private/'evaluation_draws.npz')['draws'][:,test];truth=rows.truth.to_numpy();sd=rows.sd.to_numpy();scale=rows.scale.to_numpy();y=rows.delta.to_numpy();base=crps_ensemble(draws,truth)/scale;oracle=crps_ensemble(shift(draws,y,sd),truth)/scale;losses={};summaries={'V5.1':metrics(y,np.zeros(len(y)),base,base,oracle)};tables={f:[] for f in ['asset','horizon','year','release_id']};rows['year']=pd.to_datetime(rows.origin).dt.year
 for name in MODELS:
  p=pred[name][test];loss=crps_ensemble(shift(draws,p,sd),truth)/scale;losses[name]=loss;summaries[name]=metrics(y,p,base,loss,oracle)
  for field,data in tables.items():
   for value,g in rows.groupby(field):
    ii=g.index.to_numpy();data.append(dict(model=name,group=value,origins=int(g.origin.nunique()),releases=int(g.release_id.nunique()),**metrics(y[ii],p[ii],base[ii],loss[ii],oracle[ii])))
 summaries['PERFECT_LOCATION']=metrics(y,y,base,oracle,oracle)
 save(OUT/'primary_score_summary.json',{'models':summaries,'primary_model':next(iter(MODELS)),'scorer':'qfbench2_common v2.4.3 fair CRPS; sum(CRPS/frozen past scale) candidate / same-ledger V5.1 sum','research_exposed':True,'independent_OOS':False,'official_submission':False})
 save(OUT/'oracle_summary.json',{'perfect_location_CRPS_ratio':summaries['PERFECT_LOCATION']['crps_ratio'],'diagnostic_only':True,'same_ledger':True})
 save(OUT/'oracle_capture_summary.json',{'definition':'(1-R_SLOOS)/(1-R_perfect_location); unclipped','models':{k:v['oracle_capture'] for k,v in summaries.items()}})
 save(OUT/'ablation_summary.json',{'secondary_only':True,'models':{k:summaries[k] for k in ['LEVELS_ONLY','CHANGES_ONLY','STANDARDS_ONLY','DEMAND_ONLY']}})
 save(OUT/'unweighted_sensitivity.json',{'secondary_only':True,'model':summaries['SLOOS_FULL5_UNWEIGHTED'],'cannot_replace_primary':True})
 for f,data in tables.items():write_csv(OUT/({'release_id':'release'}.get(f,f)+'_summary.csv'),data)
 rows.to_parquet(private/'scored_rows.parquet',index=False);np.savez_compressed(private/'scored_draws.npz',draws=draws);np.savez_compressed(private/'losses.npz',baseline=base,oracle=oracle,**losses)
 save(OUT/'effective_sample_summary.json',{'forecast_origins':int(rows.origin.nunique()),'evaluated_cells':len(rows),'unique_active_releases':int(rows.release_id.nunique()),'unique_change_events':int(rows.release_id.nunique()),'effective_independent_release_count_upper_bound':int(rows.release_id.nunique()),'release_blocks_are_not_proven_iid_N':True,'origins_per_release':[dict(release_id=r,origins=int(g.origin.nunique()),cells=len(g)) for r,g in rows.groupby('release_id')],'per_asset':[dict(asset=r,releases=int(g.release_id.nunique()),origins=int(g.origin.nunique())) for r,g in rows.groupby('asset')],'per_horizon':[dict(horizon=int(r),releases=int(g.release_id.nunique()),origins=int(g.origin.nunique())) for r,g in rows.groupby('horizon')]})
 status('score');print({k:round(v['crps_ratio'],6) for k,v in summaries.items()},flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--private',type=Path,required=True);ap.add_argument('--stage',choices=['prepare','fit','score'],required=True);a=ap.parse_args();globals()[a.stage](a.private)
