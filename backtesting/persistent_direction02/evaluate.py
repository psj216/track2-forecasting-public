"""Executive summary: remotely frozen chronological evaluation, shared scorer, chunked controls."""
from pathlib import Path
import argparse,json,time,copy,warnings,subprocess
import numpy as np,pandas as pd
from scipy.stats import spearmanr,pearsonr
from sklearn.metrics import balanced_accuracy_score,brier_score_loss
from qfbench2_common.scoring.crps import crps_ensemble
from .source import *
from .model import *
PRIMARY='SEP_DIRECTION_FIXED005'
NAMES=['V5.1',PRIMARY,'5BD_DELAYED','21BD_STALE','PERSISTENCE','PRICE_21BD','PRICE_LOGISTIC','MATCHED_RANDOM','PERFECT_LOCATION']
def status(stage,artifact='',**extra):
 f=OUT.parent/'STATUS.json';v=json.loads(f.read_text());v.update(current_stage=stage,last_successful_artifact=artifact,**extra);save(f,v)
def verify(private):
 p=Path(private);receipt=json.loads((p/'pre_receipt.json').read_text());assert receipt['remote_verified'] and receipt['PRE_RESULT_PERSISTENT_DIRECTION02_SHA']
 assert json.loads((OUT/'source_readiness.json').read_text())['DATASET_READY']
 m=json.loads((OUT/'pre_result_manifest.json').read_text())
 for n,s in m['implementation_hashes'].items():assert digest(ROOT/n)==receipt.get('technical_repair_hashes',{}).get(n,s),n
 for n,s in m['private_input_hashes'].items():assert digest(p/n)==s,n
 return p
def prepare(private):
 p=verify(private);calendar=pd.read_parquet(p/'design_calendar.parquet');m=json.loads((ROOT/'backtesting/location01/results/ledger_manifest.json').read_text())
 ledger=p/'baseline-sealed/ledger.parquet';assert digest(ledger)==m['ledger_sha256']
 labels=pd.read_parquet(ledger);keys=['origin','asset','horizon'];labels=labels.loc[labels.asset.isin(ASSETS)&labels.horizon.isin(HORIZONS),keys+['truth','target_end','median','sd','scale','kind']]
 rows=calendar.merge(labels,on=keys,how='inner',validate='one_to_one');rows=rows.loc[(rows.target_end<='2024-12-18')&np.isfinite(rows[['truth','median','sd','scale']]).all(axis=1)&(rows.sd>0)&(rows.scale>0)].sort_values(keys).reset_index(drop=True)
 assert rows.kind.eq('level').all();draws=np.empty((500,len(rows)))
 for i,(o,g) in enumerate(rows.groupby('origin'),1):
  f=p/'baseline-sealed/origins'/(o+'.npz');assert digest(f)==m['baseline_cache_sha256'][f.name]
  with np.load(f,allow_pickle=False) as data:
   for idx,r in g.iterrows():draws[:,idx]=data[r.asset][:,HORIZONS.index(int(r.horizon))]
  if i%20==0:print('prepare',i,'/',rows.origin.nunique(),o,'output',p/'evaluation_ledger.parquet',flush=True)
 assert np.allclose(np.median(draws,axis=0),rows['median'],atol=1e-14,rtol=0)
 assert np.allclose(draws.std(axis=0),rows.sd,atol=1e-14,rtol=1e-13)
 rows['raw_center_error']=rows.truth-rows['median'];rows['y']=np.sign(rows.raw_center_error)
 rows.to_parquet(p/'evaluation_ledger.parquet',index=False);np.savez_compressed(p/'evaluation_draws.npz',draws=draws)
 save(OUT/'target_construction_audit.json',{'executive_summary':'Exact inherited targets/draw bytes; future labels first deserialized after remote PRE.','PRE':json.loads((p/'pre_receipt.json').read_text())['PRE_RESULT_PERSISTENT_DIRECTION02_SHA'],'origins':int(rows.origin.nunique()),'cells':len(rows),'original_draws_unchanged':True,'median_SD_match':True,'target_ties':int(rows.y.eq(0).sum()),'outcome_firewall':True})
 status('PREPARED','target_construction_audit.json')
def inputs(private):
 p=verify(private);return p,pd.read_parquet(p/'evaluation_ledger.parquet'),np.load(p/'evaluation_draws.npz')['draws']
def features(rows,source=None,price=False):
 structure=np.column_stack([rows.asset.eq('UST_5Y').astype(float),np.log(rows.horizon)])
 if price:return np.column_stack([rows[[c for c in rows if c.startswith('price_') and c not in ['price_direction','price_observation_date','price_available_at']]].to_numpy(float),structure])
 return np.column_stack([rows.SEP.to_numpy() if source is None else np.asarray(source,float),structure])
def folds(rows):
 for year in YEARS:
  test=np.flatnonzero(rows.year.eq(year).to_numpy())
  if not len(test):continue
  c=cutoff(rows.iloc[test].origin.min());train=np.flatnonzero(training_mask(rows,year,c,set(rows.iloc[test].release_id))&rows.y.ne(0).to_numpy())
  yield year,train,test,c
def fit_one(rows,x,train,test):
 good=np.isfinite(x).all(axis=1);tr=train[good[train]];te=test[good[test]];pred=np.full(len(test),.5)
 with warnings.catch_warnings():
  warnings.simplefilter('ignore',FutureWarning);f=fit(x[tr],(rows.y.to_numpy()[tr]>0).astype(int))
 if len(te):pred[np.flatnonzero(good[test])]=probability(f,x[te])
 return pred,f,tr,te
def fit_folds(private,year):
 p,rows,_=inputs(private);folder=p/'folds';folder.mkdir(exist_ok=True);dest=folder/(str(year)+'.npz')
 if dest.exists():print('resume completed fold',year,flush=True);return
 year,tr,te,c=next(x for x in folds(rows) if x[0]==year);pred={};audit=[]
 for name,src,price in [(PRIMARY,None,False),('5BD_DELAYED',rows.SEP5,False),('21BD_STALE',rows.SEP21,False),('PRICE_LOGISTIC',None,True)]:
  pp,f,train,test=fit_one(rows,features(rows,src,price),tr,te);pred[name]=pp
  audit.append({'model':name,'year':year,'train_cells':len(train),'test_cells':len(te),'predicted_cells':len(test),'train_unique_releases':int(rows.iloc[train].release_id.nunique()),'test_unique_releases':int(rows.iloc[te].release_id.nunique()),'first_test_cutoff':c.isoformat(),'maximum_train_target_end':rows.iloc[train].target_end.max(),'shared_release_count':len(set(rows.iloc[train].release_id)&set(rows.iloc[te].release_id)),'scaler_mean':f[0].mean_.tolist(),'scaler_scale':f[0].scale_.tolist(),'coefficients':f[1].coef_.tolist(),'intercept':f[1].intercept_.tolist(),'C':f[1].C,'class_weight':f[1].class_weight})
 np.savez_compressed(dest,indices=te,**pred);save(dest.with_suffix('.json'),audit);print('fold complete',year,'train',len(tr),'test',len(te),'output',dest,flush=True);status('FOLD_'+str(year),str(dest))
def score(private):
 p,allrows,alldraws=inputs(private);mask=allrows.year.isin(YEARS).to_numpy();rows=allrows.loc[mask].reset_index(drop=True);draws=alldraws[:,mask];prob={}
 for name in [PRIMARY,'5BD_DELAYED','21BD_STALE','PRICE_LOGISTIC']:
  arr=np.full(len(allrows),np.nan)
  for year in YEARS:
   f=np.load(p/'folds'/(str(year)+'.npz'));arr[f['indices']]=f[name]
  assert np.isfinite(arr[mask]).all();prob[name]=arr[mask]
 prob['PERSISTENCE']=(rows.persistence_direction.to_numpy()+1)/2;prob['PRICE_21BD']=(rows.price_direction.to_numpy()+1)/2
 rng=np.random.default_rng(np.random.SeedSequence([SEED,3,0]));prob['MATCHED_RANDOM']=rng.permutation(direction(prob[PRIMARY]))/2+.5
 raw=rows.raw_center_error.to_numpy();sd=rows.sd.to_numpy();scale=rows.scale.to_numpy();truth=rows.truth.to_numpy()
 base=crps_ensemble(draws,truth)/scale;oracle=crps_ensemble(translate(draws,raw),truth)/scale
 table=np.array([crps_ensemble(translate(draws,shift(sd,d)),truth)/scale for d in [-1,0,1]])
 losses=[base]+[table[direction(prob[n]).astype(int)+1,np.arange(len(rows))] for n in NAMES[1:-1]]+[oracle]
 np.savez_compressed(p/'scores.npz',names=NAMES,losses=losses,base=base,oracle=oracle,table=table,**{'prob_'+n:v for n,v in prob.items()})
 rows.to_parquet(p/'scored_rows.parquet',index=False)
 public=rows[['origin','asset','horizon','year','release_id','release_date','source_age','SEP']].copy()
 for n,v in prob.items():public[n+'_probability']=v;public[n+'_direction']=direction(v)
 public.to_csv(OUT/'crossfit_predictions.csv',index=False)
 audit=[]
 for year in YEARS:audit.extend(json.loads((p/'folds'/(str(year)+'.json')).read_text()))
 csv(OUT/'fold_manifest.csv',audit)
 geom={'max_SD_difference':0.,'max_center_shift_error':0.,'ranks_unchanged':True}
 shifted=translate(draws,shift(sd,direction(prob[PRIMARY])));geom['max_SD_difference']=float(np.max(abs(shifted.std(axis=0)-sd)));geom['max_center_shift_error']=float(np.max(abs(shifted-draws-shift(sd,direction(prob[PRIMARY])))))
 order=np.argsort(draws,axis=0,kind='stable');ordered=np.take_along_axis(shifted,order,axis=0);original_ordered=np.take_along_axis(draws,order,axis=0);gaps=np.diff(ordered,axis=0);original_gaps=np.diff(original_ordered,axis=0);collapsed=(gaps==0)&(original_gaps>0)
 geom['strict_order_inversions']=int((gaps<0).sum());geom['float64_tie_coalescences']=int(collapsed.sum());geom['maximum_coalesced_gap']=float(original_gaps[collapsed].max()) if collapsed.any() else 0.;geom['ranks_unchanged']=bool(geom['strict_order_inversions']==0);geom['rank_semantics']='Monotone location translation; ties can coalesce at float64 ULP. No strict ordering inversions.'
 assert geom['max_SD_difference']<1e-12 and geom['ranks_unchanged'] and geom['maximum_coalesced_gap']<=2*np.spacing(abs(draws).max())
 save(OUT/'draw_geometry_audit.json',{'executive_summary':'Pure0.05SD translation; original draws, ranks and SD retained.','amplitude':AMPLITUDE,**geom});status('SCORED','scores.npz')
def null_source(states,kind,rep):
 rng=np.random.default_rng(np.random.SeedSequence([SEED,{'STATE':1,'DATE':2}[kind],rep]));s=copy.deepcopy(states)
 if kind=='STATE':
  for i,r in enumerate(s):r['value']=states[int(rng.integers(i+1))]['value']
 else:
  delays=rng.permutation(np.resize(np.array([0,5,21,42,63]),len(s)))
  for r,d in zip(s,delays):r['available_at']=(pd.Timestamp(r['available_at'])+pd.offsets.BDay(int(d))).isoformat()
 return s
def source_values(states,rows):
 # Original release-only nulls: availability changes never select a future release.
 ordered=sorted(states,key=lambda r:r['release_date']);available=np.array([pd.Timestamp(r['available_at']).tz_convert('UTC').to_datetime64() for r in ordered]);dates=np.array([r['release_date'] for r in ordered],dtype='datetime64[D]');values=np.array([r['value'] if r.get('active',True) else np.nan for r in ordered]);lookup={}
 for origin in rows.origin.unique():
  c=cutoff(origin);eligible=np.flatnonzero(available<=c.tz_convert('UTC').to_datetime64())
  j=eligible[-1] if len(eligible) else -1
  lookup[origin]=values[j] if j>=0 and np.busday_count(dates[j],np.datetime64(str(c.date()),'D'))<=90 else np.nan
 return np.array([lookup[o] for o in rows.origin])
def control_chunk(private,kind,start,stop):
 p,allrows,_=inputs(private);rows=pd.read_parquet(p/'scored_rows.parquet');data=np.load(p/'scores.npz');folder=p/'controls';folder.mkdir(exist_ok=True);dest=folder/f'{kind}-{start:04d}-{stop:04d}.npz'
 if dest.exists():print('resume completed',dest,flush=True);return
 states=json.loads((p/'source_states.json').read_text());groups=list(folds(allrows));ratios=[];begun=time.monotonic()
 for rep in range(start,stop):
  if kind=='RANDOM':
   rng=np.random.default_rng(np.random.SeedSequence([SEED,3,rep]));signs=rng.permutation(direction(data['prob_'+PRIMARY]))
  else:
   mutated=null_source(states,kind,rep);vals=source_values(mutated,allrows);x=features(allrows,vals);pred=np.full(len(allrows),.5)
   for year,tr,te,c in groups:pred[te]=fit_one(allrows,x,tr,te)[0]
   signs=direction(pred[allrows.year.isin(YEARS)])
  loss=data['table'][signs.astype(int)+1,np.arange(len(rows))];ratios.append(float(loss.sum()/data['base'].sum()))
  if (rep-start+1)%25==0:print('control',kind,rep+1,'/2000 elapsed',round(time.monotonic()-begun,1),'output',dest,flush=True)
 np.savez_compressed(dest,ratios=ratios);status('CONTROL_'+kind,str(dest),control_completed_to=stop)
def bootstrap_chunk(private,block,start,stop):
 p=verify(private);rows=pd.read_parquet(p/'scored_rows.parquet');data=np.load(p/'scores.npz');keys=rows[{'release':'release_id','year':'year','week':'source_week'}[block]] if block!='week' else pd.to_datetime(rows.origin).dt.to_period('W-FRI').astype(str)
 groups=[np.flatnonzero(np.asarray(keys)==g) for g in sorted(set(keys))];matrix=np.array([data['losses'][:,ii].sum(axis=1) for ii in groups]);oracle=np.array([data['oracle'][ii].sum() for ii in groups]);folder=p/'bootstrap';folder.mkdir(exist_ok=True);dest=folder/f'{block}-{start:04d}-{stop:04d}.npz'
 if dest.exists():return
 ratios=[];captures=[];differences=[]
 for rep in range(start,stop):
  rng=np.random.default_rng(np.random.SeedSequence([SEED,{'release':10,'year':11,'week':12}[block],rep]));ii=rng.integers(len(groups),size=len(groups));tot=matrix[ii].sum(axis=0);rr=tot/tot[0];ro=oracle[ii].sum()/tot[0]
  ratios.append(rr);captures.append((1-rr)/(1-ro));differences.append([rr[1]-rr[k] for k in [0,2,3,4,5,6]])
 np.savez_compressed(dest,ratios=ratios,capture=captures,differences=differences);print('bootstrap',block,start,'-',stop,'output',dest,flush=True);status('BOOTSTRAP_'+block,str(dest),bootstrap_completed_to=stop)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('stage',choices=['prepare','fold','score','control','bootstrap']);a.add_argument('private');a.add_argument('--year',type=int);a.add_argument('--kind');a.add_argument('--start',type=int,default=0);a.add_argument('--stop',type=int,default=250);q=a.parse_args()
 if q.stage=='prepare':prepare(q.private)
 elif q.stage=='fold':fit_folds(q.private,q.year)
 elif q.stage=='score':score(q.private)
 elif q.stage=='control':control_chunk(q.private,q.kind,q.start,q.stop)
 else:bootstrap_chunk(q.private,q.kind,q.start,q.stop)
