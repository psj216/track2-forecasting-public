"""Executive summary: verified-PRE chronological extension, fixed shifts and chunked controls."""
from .core import *
import argparse, time, zipfile
from qfbench2_common.scoring.crps import crps_ensemble

def prepare_data():
 verify_pre();p=private();meta=pd.read_parquet(p/'eligibility.parquet')
 broad=pd.read_parquet(p/'canonical/ledger.parquet')
 rows=broad.iloc[meta.draw_row.to_numpy(int)].copy().reset_index(drop=True)
 assert rows[['origin','asset','horizon','target_end']].equals(meta[['origin','asset','horizon','target_end']])
 rows['year']=meta.year;rows['price_observation_date']=meta.price_observation_date
 rows['source_index']=meta.source_index;rows['y']=np.sign(rows.truth-rows['median']).astype(int)
 assert np.allclose(rows.delta,(rows.truth-rows['median'])/rows.sd,rtol=0,atol=1e-13)
 assets=tuple(json.loads((p/'assets.json').read_text()));px=np.load(p/'price_features.npy');x=np.column_stack([px,structure(rows,assets)])
 fold=np.zeros(len(rows),int);fold_records=[]
 for k,(_,start,end) in enumerate(FOLDS,1):
  tr=np.flatnonzero(purged_mask(rows,f'{start}-01-01')&rows.y.ne(0).to_numpy());te=np.flatnonzero(rows.year.between(start,end).to_numpy())
  if len(tr) and len(te):fold[te]=k;fold_records.append(dict(fold=k,train=tr.tolist(),test=te.tolist(),boundary=f'{start}-01-01'))
 rows['fold']=fold;rows.to_parquet(p/'u1_all.parquet',index=False);np.save(p/'u1_X.npy',x);save(p/'u1_folds.json',fold_records)
 # Existing own-price features are only read after the remotely verified expanded PRE.
 manifest=json.loads((ROOT/'backtesting/location01/results/ledger_manifest.json').read_text())
 with zipfile.ZipFile(p/'canonical-archives/location01-frozen-inputs.zip') as z:
  blob=z.read('features.npy');assert hashlib.sha256(blob).hexdigest()==manifest['feature_sha256'];(p/'canonical/features.npy').write_bytes(blob)
 cached=np.load(p/'canonical/features.npy',mmap_mode='r');schema=manifest['feature_schema'];groups=json.loads((OUT/'frozen_feature_spec.json').read_text())['secondary_groups']
 for name,columns in groups.items():
  xx=cached[rows.draw_row.to_numpy(int)][:,[schema.index(c) for c in columns]] if name in ('SELF_PRICE','VOL_STATE') else px[:,[NAMES.index(c) for c in columns]]
  np.save(p/f'u1_X_{name}.npy',np.column_stack([xx,structure(rows,assets)]))
 # Full rows remain private; every eligible source-covered cell is retained.
 te=np.flatnonzero(fold>0);ev=rows.iloc[te].reset_index(drop=True);ev.to_parquet(p/'u1_eval.parquet',index=False)
 folder=p/'scoring_chunks';folder.mkdir(exist_ok=True);origins=list(ev.origin.unique())
 for start in range(0,len(origins),25):
  selected=origins[start:start+25];dest=folder/f'{start:04d}.npz'
  if dest.exists():continue
  ii=np.flatnonzero(ev.origin.isin(selected));table=np.zeros((3,len(ii)));oracle=np.zeros(len(ii));local={int(v):j for j,v in enumerate(ii)}
  for origin in selected:
   with np.load(p/'canonical/origins'/f'{origin}.npz') as data:
    part=ev.index[ev.origin.eq(origin)]
    for asset in ev.loc[part,'asset'].unique():
     jj=part[ev.loc[part,'asset'].eq(asset)];draws=data[asset][:,[HORIZONS.index(int(h)) for h in ev.loc[jj,'horizon']]]
     a=ev.loc[jj];assert np.allclose(np.median(draws,axis=0),a['median'],rtol=0,atol=1e-13);assert np.allclose(draws.std(axis=0),a.sd,rtol=1e-13,atol=1e-13)
     truth=a.truth.to_numpy();sd=a.sd.to_numpy();scale=a.scale.to_numpy();kk=[local[int(v)] for v in jj]
     for s in [-1,0,1]:table[s+1,kk]=crps_ensemble(draws+AMPLITUDE*s*sd,truth)/scale
     oracle[kk]=crps_ensemble(draws+(truth-a['median'].to_numpy()),truth)/scale
  np.savez_compressed(dest,indices=ii,table=table,oracle=oracle)
  print('scoring',min(start+25,len(origins)),'/',len(origins),'origin',selected[-1],'output',dest,flush=True);status('SCORING_CHUNK',dest,scoring_completed_to=min(start+25,len(origins)))
 table=np.full((3,len(ev)),np.nan);oracle=np.full(len(ev),np.nan)
 for dest in sorted(folder.glob('*.npz')):
  d=np.load(dest);table[:,d['indices']]=d['table'];oracle[d['indices']]=d['oracle']
 assert np.isfinite(table).all() and np.isfinite(oracle).all();np.savez_compressed(p/'u1_table.npz',table=table,oracle=oracle)
 prepare_u0();status('DATA_PREPARED',p/'u1_eval.parquet')

def prepare_u0():
 from backtesting.persistent_direction02.evaluate import features, folds
 p=private();old=p/'u0-parent';rows=pd.read_parquet(old/'evaluation_ledger.parquet');scores=np.load(old/'scores.npz');ev=pd.read_parquet(old/'scored_rows.parquet')
 rows['delta']=(rows.truth-rows['median'])/rows.sd;ev['delta']=(ev.truth-ev['median'])/ev.sd
 x=features(rows,price=True);assert x.shape[1]==16;rows.to_parquet(p/'u0_all.parquet',index=False);np.save(p/'u0_X.npy',x)
 folds0=[dict(fold=int(year),train=tr.tolist(),test=te.tolist(),boundary=str(cut)) for year,tr,te,cut in folds(rows)]
 save(p/'u0_folds.json',folds0)
 # No original price model is refitted. All probabilities and tables preserve parent bytes.
 te=np.concatenate([np.asarray(f['test'],int) for f in folds0]);assert rows.iloc[te][['origin','asset','horizon']].reset_index(drop=True).equals(ev[['origin','asset','horizon']])
 ev['fold']=ev.year;ev.to_parquet(p/'u0_eval.parquet',index=False);np.savez_compressed(p/'u0_table.npz',table=scores['table'],oracle=scores['oracle'])
 assert hashlib.sha256(np.ascontiguousarray(scores['prob_PRICE_LOGISTIC']).tobytes()).hexdigest()=='a4690d8f3ef4c4935d34747d9a679171abf1335ecb9f30184f6cfc5fc1bbca51'
 np.savez_compressed(p/'u0_predictions.npz',PRICE_LOGISTIC=scores['prob_PRICE_LOGISTIC'],MAJORITY=np.array([float((rows.iloc[np.asarray(f['train'])].y>0).mean()>.5) for f in folds0 for _ in f['test']]),ZERO=np.full(len(ev),.5))

def fit_fold(fold_id):
 verify_pre();p=private();rows=pd.read_parquet(p/'u1_all.parquet');folds=json.loads((p/'u1_folds.json').read_text());f=next(f for f in folds if f['fold']==fold_id);tr=np.asarray(f['train']);te=np.asarray(f['test']);y=(rows.y.to_numpy()>0).astype(int)
 dest=p/'fits'/f'{fold_id}.npz';dest.parent.mkdir(exist_ok=True)
 if dest.exists():print('resume fitted fold',fold_id,flush=True);return
 names=['PRICE_LOGISTIC','MAJORITY','STRUCTURE_ONLY']+list(json.loads((OUT/'frozen_feature_spec.json').read_text())['secondary_groups']);pred={};audit=[]
 for name in names:
  if name=='MAJORITY':pred[name]=np.full(len(te),float(y[tr].mean()>.5) if y[tr].mean()!=.5 else .5);continue
  x=np.load(p/('u1_X.npy' if name in ['PRICE_LOGISTIC','STRUCTURE_ONLY'] else f'u1_X_{name}.npy'))
  if name=='STRUCTURE_ONLY':x=x[:,14:]
  a,b,fill=impute_training(x[tr],x[te]);fit=numeric_fit(a,y[tr]);pred[name]=predict(fit,b)
  audit.append(dict(model=name,train_cells=len(tr),test_cells=len(te),scaler_mean=fit[0].mean_.tolist(),scaler_scale=fit[0].scale_.tolist(),coefficients=fit[1].coef_.tolist() if fit[1] is not None else None,intercept=fit[1].intercept_.tolist() if fit[1] is not None else fit[2],imputation=fill.tolist(),max_train_target_end=rows.iloc[tr].target_end.max(),max_train_origin=rows.iloc[tr].origin.max(),C=1.,class_weight=None,no_test_fit=True))
  print('fold',fold_id,name,'train',len(tr),'test',len(te),'output',dest,flush=True)
 np.savez_compressed(dest,indices=te,**pred);save(dest.with_suffix('.json'),audit);status('FIT_FOLD_'+str(fold_id),dest)

def collect():
 verify_pre();p=private();rows=pd.read_parquet(p/'u1_all.parquet');ev=pd.read_parquet(p/'u1_eval.parquet');allprobs={}
 for dest in sorted((p/'fits').glob('*.npz')):
  data=np.load(dest)
  for name in data.files:
   if name=='indices':continue
   if name not in allprobs:allprobs[name]=np.full(len(rows),np.nan)
   allprobs[name][data['indices']]=data[name]
 mask=rows.fold.ne(0).to_numpy();probs={name:v[mask] for name,v in allprobs.items()};assert all(np.isfinite(v).all() for v in probs.values());probs['ZERO']=np.full(len(ev),.5)
 np.savez_compressed(p/'u1_predictions.npz',**probs)
 for u in ['u0','u1']:
  a=pd.read_parquet(p/f'{u}_eval.parquet');pp=np.load(p/f'{u}_predictions.npz');public=a[['origin','asset','horizon','year','fold','price_observation_date']].copy()
  for name in pp.files:public[name+'_probability']=pp[name]
  public.to_csv(OUT/f'{u}_predictions.csv',index=False)
 status('PREDICTIONS_COLLECTED',OUT/'u1_predictions.csv')

def null_chunk(universe,kind,start,stop):
 verify_pre();p=private();folder=p/'nulls'/universe;folder.mkdir(parents=True,exist_ok=True);dest=folder/f'{kind}-{start:04d}-{stop:04d}.npz'
 completed=[];previous=[]
 if dest.exists():
  with np.load(dest) as saved:completed=saved['replicates'].tolist();previous=saved['metrics'].tolist()
  if completed and completed[-1]==stop-1:print('resume completed null',dest,flush=True);return
  assert completed==list(range(start,start+len(completed)))
 rows=pd.read_parquet(p/f'{universe}_all.parquet');ev=pd.read_parquet(p/f'{universe}_eval.parquet');x=np.load(p/f'{universe}_X.npy');folds=json.loads((p/f'{universe}_folds.json').read_text());table=np.load(p/f'{universe}_table.npz')['table'];primary=np.load(p/f'{universe}_predictions.npz')['PRICE_LOGISTIC'];records=[];begun=time.monotonic()
 records=previous;keys=['Balanced_Accuracy','Direction_Accuracy','AUC','Spearman','Spearman_direction','Brier','FIXED005_CRPS']
 is_random=kind in ['N0','FOLD_RANDOM','BALANCED_RANDOM'] or kind.startswith('FAMILY_')
 if kind.startswith('FAMILY_'):primary=np.load(p/f'{universe}_predictions.npz')[kind.removeprefix('FAMILY_')]
 if kind=='N4':
  frame=source_frame();complete=frame.loc[np.isfinite(frame.to_numpy()).all(axis=1)];dates=pd.to_datetime(rows.price_observation_date);source_indices=complete.index.searchsorted(dates,side='right')-1;assert (source_indices>=0).all()
 y=(rows.y.to_numpy()>0).astype(int)
 for rep in range(start+len(completed),stop):
  rng=np.random.default_rng(np.random.SeedSequence([SEED,30,rep,0 if universe=='u0' else 1]))
  if is_random:
   if kind=='N0' or kind.startswith('FAMILY_'):prob=rng.permutation(primary)
   elif kind=='FOLD_RANDOM':
    prob=primary.copy()
    for g in sorted(ev.fold.unique()):
     ii=np.flatnonzero(ev.fold.eq(g));prob[ii]=rng.permutation(primary[ii])
   else:
    prob=np.r_[np.zeros(len(ev)//2),np.ones(len(ev)//2),[.5] if len(ev)%2 else []];prob=rng.permutation(prob)
  else:
   full=np.full(len(rows),np.nan)
   for f in folds:
    tr=np.asarray(f['train']);te=np.asarray(f['test']);xx=x;yy=y[tr]
    if kind in ['N1','N2','N3']:yy=null_labels(rows.iloc[tr].reset_index(drop=True),yy,kind,rep,f['fold'])
    if kind=='N4':
     unique=np.unique(source_indices);donor=historical_donors(unique,rep,f['fold']);mapping=dict(zip(unique,donor));jj=np.array([mapping[j] for j in source_indices]);xx=x.copy();xx[:,:14]=complete.iloc[jj].to_numpy(float)
     assert (complete.index[jj]<=dates).all()
    if kind=='N5':
     unique,inv=np.unique(rows.origin,return_inverse=True);rr=np.random.default_rng(np.random.SeedSequence([SEED,15,rep,f['fold'],0 if universe=='u0' else 1]));xx=np.column_stack([rr.normal(size=(len(unique),14))[inv],x[:,14:]])
    fit=numeric_fit(xx[tr],yy);full[te]=predict(fit,xx[te])
   ii=np.concatenate([np.asarray(f['test']) for f in folds]);prob=full[ii];assert np.isfinite(prob).all()
  metric=metrics(prob,ev,table);records.append([metric[k] for k in keys])
  # Each replicate is persisted, so a timeout resumes exactly after the last completed rep.
  atomic_npz(dest,replicates=np.arange(start,rep+1),keys=keys,metrics=np.array(records,float))
  if (rep-start+1)%5==0:print('null',universe,kind,rep+1,'/',RANDOM_REPS if is_random else NULL_REPS,'elapsed',round(time.monotonic()-begun,1),'fold',f['fold'] if not is_random else 'matched','output',dest,flush=True)
 status('NULL_CHUNK',dest,universe=universe,null_kind=kind,completed_to=stop)

def bootstrap_chunk(universe,block,start,stop):
 verify_pre();p=private();dest=p/'bootstrap'/universe/f'{block}-{start:04d}-{stop:04d}.npz';dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():return
 rows=pd.read_parquet(p/f'{universe}_eval.parquet');table=np.load(p/f'{universe}_table.npz');probs=np.load(p/f'{universe}_predictions.npz');prob=probs['PRICE_LOGISTIC'];base=table['table'][1];loss=table['table'][direction(prob)+1,np.arange(len(rows))];oracle=table['oracle'];majority=table['table'][direction(probs['MAJORITY'])+1,np.arange(len(rows))]
 keys=rows[block].astype(str).to_numpy() if block!='quarter' else pd.to_datetime(rows.origin).dt.to_period('Q').astype(str).to_numpy();unique,inv=np.unique(keys,return_inverse=True)
 sums=np.array([np.bincount(inv,weights=v,minlength=len(unique)) for v in [base,loss,oracle,majority]])
 vals=[]
 for rep in range(start,stop):
  rng=np.random.default_rng(np.random.SeedSequence([SEED,40,rep,['origin','year','quarter','asset'].index(block),0 if universe=='u0' else 1]));sample=rng.integers(len(unique),size=len(unique));counts=np.bincount(sample,minlength=len(unique));tot=sums@counts;ratio=tot[1]/tot[0];ro=tot[2]/tot[0]
  # Block-weighted classification: fixed crossfit predictions; resampled blocks, no refit.
  wm=counts[inv].astype(float);positive=rows.y.to_numpy()>0;valid=rows.y.to_numpy()!=0;d=direction(prob)
  bal=np.mean([np.average(d[positive&valid]==1,weights=wm[positive&valid]),np.average(d[~positive&valid]==-1,weights=wm[~positive&valid])]) if wm[positive&valid].sum()>0 and wm[~positive&valid].sum()>0 else np.nan
  vals.append([ratio,ratio-1,(tot[1]-tot[3])/tot[0],(1-ratio)/(1-ro),bal])
 np.savez_compressed(dest,values=vals,keys=['CRPS_ratio','delta_V51','delta_majority','oracle_capture','balanced_accuracy']);print('bootstrap',universe,block,start,stop,'blocks',len(unique),'output',dest,flush=True);status('BOOTSTRAP_CHUNK',dest,universe=universe,block=block,completed_to=stop)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('stage',choices=['prepare','fold','collect','null','bootstrap']);a.add_argument('--fold',type=int);a.add_argument('--universe',default='u1');a.add_argument('--kind');a.add_argument('--start',type=int,default=0);a.add_argument('--stop',type=int,default=20);q=a.parse_args()
 if q.stage=='prepare':prepare_data()
 elif q.stage=='fold':fit_fold(q.fold)
 elif q.stage=='collect':collect()
 elif q.stage=='null':null_chunk(q.universe,q.kind,q.start,q.stop)
 else:bootstrap_chunk(q.universe,q.kind,q.start,q.stop)
